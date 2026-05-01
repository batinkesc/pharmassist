"""
RAGAS değerlendirme pipeline'ı — Final metrik seti.

Standart (varsayılan — her değerlendirmede):
  - faithfulness:         Cevap yalnızca context'e mi dayanıyor? Model uyduruyor mu?
                          GT gerektirmez — (answer perspective, hallucination check)
  - context_utilization:  Getirilen chunk'lar cevap için gerçekten kullanıldı mı?
                          GT gerektirmez — (retrieval→answer alignment, GT-free context_precision)
  - context_recall:       Context, ground truth'u kapsıyor mu? Retrieval eksiksiz mi?
                          GT gerektirir — (retrieval completeness, benchmark karşılaştırması)

Alternatif (--mode ac):
  - answer_correctness:   Cevap klinik olarak ground truth ile ne kadar örtüşüyor?
                          GT gerektirir — (semantic + factual overlap vs GT)
  - context_utilization:  (aynı)
  - context_recall:       (aynı)

Devre dışı:
  - coherence, clinical_safety: Binary (0/1) — çalışan sistemde hep 1.0, iyileştirme sinyali yok
  - answer_relevancy, context_precision: Embedding modeli gerektirir
  - nv_context_relevance, nv_response_groundedness: NV proprietary, test edilmedi

Değerlendirici LLM:
  - Varsayılan: RAGAS_MODEL env var (Together AI Qwen3-235B)
  - Alternatif: Claude Haiku (--evaluator haiku)
"""

import os
import re
import numpy as np
from loguru import logger
from dotenv import load_dotenv

from src.core.content_policy import POLICY

from datasets import Dataset
from ragas import evaluate
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import (
        faithfulness,
        context_recall,
    )
    from ragas.metrics._answer_correctness import AnswerCorrectness
    from ragas.metrics._context_precision import ContextUtilization
    from ragas.embeddings import HuggingFaceEmbeddings as RagasHFEmbeddings
from ragas.run_config import RunConfig
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

load_dotenv(override=True)

# Standart 3'lü metrik seti — FF + CU + CR
# faithfulness + context_utilization: GT-free
# context_recall: GT gerektirir (eval dosyalarında ground_truth şart)
_METRICS_DEFAULT = [faithfulness, ContextUtilization(), context_recall]

# Alternatif metrik seti — AC + CU + CR (FF yerine Answer Correctness)
# multilingual-e5-base: zaten sistemde yüklü, embedding için dış API gerektirmez
_ac_embeddings = RagasHFEmbeddings(model="intfloat/multilingual-e5-base")
_answer_correctness_factual = AnswerCorrectness(weights=[0.75, 0.25])
_METRICS_AC = [_answer_correctness_factual, ContextUtilization(), context_recall]

# ContentPolicy'den gelir — rag_engine ile aynı değerler → drift engeli
_MAX_CONTEXTS    = POLICY.eval_max_contexts
_MAX_CHUNK_CHARS = POLICY.eval_max_chunk_chars


def _get_llm(provider: str | None = None):
    """RAGAS için değerlendirici LLM döner."""
    if provider is None:
        provider = os.environ.get("RAGAS_PROVIDER", "local")

    if provider == "haiku":
        logger.info("Değerlendirici: Claude Haiku (Anthropic API)")
        return ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            temperature=0,
            max_tokens=4096,
        )

    lm_studio_url = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")
    model_name = (
        os.environ.get("RAGAS_MODEL")
        or os.environ.get("LOCAL_MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.3")
    )
    api_key = os.environ.get("LM_STUDIO_API_KEY") or "lm-studio"
    logger.info(f"Değerlendirici: {model_name} @ {lm_studio_url}")
    return ChatOpenAI(
        base_url=lm_studio_url,
        api_key=api_key,
        model=model_name,
        temperature=0,
        max_tokens=4096,
        timeout=600,
    )


def _truncate_contexts(contexts: list[str]) -> list[str]:
    """RAGAS prompt'unun LLM context limitini aşmaması için kırpar."""
    truncated = []
    for ctx in contexts[:_MAX_CONTEXTS]:
        truncated.append(ctx[:_MAX_CHUNK_CHARS] + ("…" if len(ctx) > _MAX_CHUNK_CHARS else ""))
    return truncated


# Citation bracket pattern: [İlaç | Madde X.X], [Graf], [CYP450], [Kümülatif...]
_CITATION_RE = re.compile(
    r'\[[^\]]*\|[^\]]*\]'          # [İlaç | Madde X.X]
    r'|\[Graf\]'                    # [Graf]
    r'|\[CYP450\]'                  # [CYP450]
    r'|\[Kümülatif[^\]]*\]'        # [Kümülatif Risk Analizi]
    r'|\*\*\[KÜB Aktarımı\]\*\*'   # **[KÜB Aktarımı]**
    r'|\*\*\[Sistem Tespitleri\]\*\*'
    r'|\*\*\[Değerlendirme\]\*\*',
)

def _strip_citations_for_ac(text: str) -> str:
    """AC modu için citation bracket'larını ve JSON-problematic karakterleri temizler.

    Üç sorun çözülür:
    1. [İlaç | Madde X.X] formatındaki bracket'lar Qwen3 JSON parser'ını şaşırtıyor.
    2. < karakteri (CrCL <30 gibi) JSON string içinde parser hatası yaratıyor.
    3. " çift tırnak (KÜB alıntıları) JSON string içinde nested quote hatası yaratıyor.

    Sadece AC (answer_correctness) değerlendirmesinde kullanılır.
    FF/CU/CR modunda orijinal metin korunur.
    """
    cleaned = _CITATION_RE.sub("", text)
    cleaned = cleaned.replace("<", "≤")                # CrCL <30 → CrCL ≤30
    cleaned = cleaned.replace('"', "‘’")     # " → '' (Türkçe alıntı çiftli)
    return cleaned.strip()


def build_ragas_dataset(
    eval_records: list[dict],
    include_gt: bool = False,
    strip_citations: bool = False,
) -> Dataset:
    """
    RAGAS Dataset formatına çevirir.

    include_gt=False (varsayılan): GT-free metrikler için — ground_truth alanı dahil edilmez.
    include_gt=True: context_recall gibi GT gerektiren metrikler için.
    strip_citations=True: AC modu — [İlaç | Madde] bracket'larını temizler (Qwen3 parse fix).
    """
    def _prep(answer: str) -> str:
        ans = answer[:1500]
        if strip_citations:
            ans = _strip_citations_for_ac(ans)
        return ans

    data = {
        "question": [r["question"] for r in eval_records],
        "answer":   [_prep(r["answer"]) for r in eval_records],
        "contexts": [_truncate_contexts(r["contexts"]) for r in eval_records],
    }
    if include_gt:
        data["ground_truth"] = [r.get("ground_truth", "") for r in eval_records]
    return Dataset.from_dict(data)


def run_ragas_evaluation(
    eval_records: list[dict],
    evaluator_provider: str | None = None,
    mode: str = "default",
) -> dict:
    """
    RAGAS metrikleri hesaplar.

    Args:
        eval_records:       [{"question", "answer", "contexts", "ground_truth"}, ...]
                            ground_truth context_recall için zorunlu.
        evaluator_provider: "haiku" veya "local" (varsayılan: RAGAS_PROVIDER env)
        mode:               "default" → FF+CU+CR  |  "ac" → AC+CU+CR

    Returns:
        {
            "scores":       {"faithfulness"|"answer_correctness": float,
                             "context_utilization": float, "context_recall": float},
            "per_question": [{"question_id": int, ...metriker...: float}, ...]
        }
    """
    logger.info(f"RAGAS değerlendirmesi başlıyor: {len(eval_records)} soru  [mode={mode}]")

    metrics = list(_METRICS_AC if mode == "ac" else _METRICS_DEFAULT)
    # AC modu: citation bracket'ları temizle — Qwen3 JSON parse hatası önlenir
    dataset  = build_ragas_dataset(eval_records, include_gt=True,
                                   strip_citations=(mode == "ac"))
    llm      = _get_llm(evaluator_provider)
    logger.info(f"Metrikler: {[m.name for m in metrics]}")

    # AC modu: multilingual-e5-base embeddings — dış API gerektirmez
    embeddings_kwarg = {"embeddings": _ac_embeddings} if mode == "ac" else {}

    # AC modu: max_workers=1 — Qwen3 paralel yükte parse hatası yapıyor
    # Default modu: max_workers=3 tutuldu (FF/CU/CR'da sorun yok)
    workers = 1 if mode == "ac" else 3
    retries = 5 if mode == "ac" else 3

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=llm,
        run_config=RunConfig(
            max_workers=workers,
            timeout=900,
            max_retries=retries,
            seed=42,
        ),
        raise_exceptions=False,
        **embeddings_kwarg,
    )

    # Metrik anahtarları
    metric_keys = [m.name for m in metrics]

    def _mean(key: str) -> float:
        vals = result[key]
        if isinstance(vals, list):
            clean = [v for v in vals if v is not None and not (isinstance(v, float) and np.isnan(v))]
            return float(np.mean(clean)) if clean else float("nan")
        return float(vals)

    def _clean(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        return round(float(v), 4)

    # NaN log
    for key in metric_keys:
        vals = result[key]
        if isinstance(vals, list):
            nan_idx = [i for i, v in enumerate(vals)
                       if v is None or (isinstance(v, float) and np.isnan(v))]
            if nan_idx:
                nan_qs = [eval_records[i]["question"][:55] for i in nan_idx]
                logger.warning(f"[NaN] {key}: {len(nan_idx)} soru — {nan_qs}")

    scores = {k: round(_mean(k), 4) for k in metric_keys}

    # Per-question
    per_question = []
    raw_vals = {k: (result[k] if isinstance(result[k], list) else [result[k]])
                for k in metric_keys}

    for i, record in enumerate(eval_records):
        entry = {
            "question_id":    i + 1,
            "question":       record["question"],
            "answer_length":  len(record["answer"]),
            "n_contexts":     len(record["contexts"]),
        }
        for k in metric_keys:
            vals = raw_vals[k]
            entry[k] = _clean(vals[i]) if i < len(vals) else None
        per_question.append(entry)

    logger.info(f"RAGAS sonuçları: {scores}")
    return {"scores": scores, "per_question": per_question}


def print_ragas_report(scores: dict, per_question: list[dict] | None = None) -> None:
    """Sonuçları formatlı olarak yazdırır."""
    metric_labels = {
        "faithfulness":        "Faithfulness        (sadakat) ",
        "answer_correctness":  "Answer Correctness  (doğruluk)",
        "context_utilization": "Context Utilization (kullanım)",
        "context_recall":      "Context Recall      (kapsam)  ",
    }

    print("\n" + "=" * 60)
    print("RAGAS DEĞERLENDİRME RAPORU")
    print("=" * 60)

    valid_vals = []
    for k, label in metric_labels.items():
        if k in scores:
            v = scores[k]
            v_str = f"{v:.4f}" if not (isinstance(v, float) and np.isnan(v)) else "  NaN "
            print(f"  {label}: {v_str} / 1.0")
            if not (isinstance(v, float) and np.isnan(v)):
                valid_vals.append(v)

    ortalama = sum(valid_vals) / len(valid_vals) if valid_vals else float("nan")
    print(f"\n  Genel Ortalama : {ortalama:.4f} / 1.0")

    if not np.isnan(ortalama):
        if ortalama >= 0.75:
            print("  Değerlendirme  : ✓ KABUL EDILEBILIR (>=0.75)")
        elif ortalama >= 0.60:
            print("  Değerlendirme  : ~ GELIŞTIRILEBILİR (0.60-0.75)")
        else:
            print("  Değerlendirme  : ✗ YETERSIZ (<0.60)")

    if per_question:
        metric_keys = [k for k in metric_labels if k in scores]
        low = [q for q in per_question
               if any(q.get(k) is not None and q[k] < 0.5 for k in metric_keys)]
        if low:
            print(f"\n  Düşük skorlu sorular ({len(low)}):")
            for q in low:
                scores_str = "  ".join(
                    f"{k[:2].upper()}={q[k]:.2f}" if q.get(k) is not None else f"{k[:2].upper()}=NaN"
                    for k in metric_keys
                )
                print(f"    [{scores_str}] {q['question'][:55]}")

    print("=" * 60)
