"""
RAGAS değerlendirme pipeline'ı — Final metrik seti (3'lü).

Standart (varsayılan — her değerlendirmede):
  - faithfulness:        Cevap yalnızca context'e mi dayanıyor? Model uyduruyor mu?
                         GT gerektirmez — (answer perspective, hallucination check)
  - context_utilization: Getirilen chunk'lar cevap için gerçekten kullanıldı mı?
                         GT gerektirmez — (retrieval→answer alignment, GT-free context_precision)
  - context_recall:      Context, ground truth'u kapsıyor mu? Retrieval eksiksiz mi?
                         GT gerektirir — (retrieval completeness, benchmark karşılaştırması)

Devre dışı:
  - coherence, clinical_safety: Binary (0/1) — çalışan sistemde hep 1.0, iyileştirme sinyali yok
  - answer_relevancy, context_precision: Embedding modeli gerektirir
  - nv_context_relevance, nv_response_groundedness: NV proprietary, test edilmedi

Değerlendirici LLM:
  - Varsayılan: RAGAS_MODEL env var (Together AI Qwen3-235B)
  - Alternatif: Claude Haiku (--evaluator haiku)
"""

import os
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
    from ragas.metrics._context_precision import ContextUtilization
from ragas.run_config import RunConfig
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

load_dotenv(override=True)

# Standart 3'lü metrik seti — her değerlendirmede kullanılır
# faithfulness + context_utilization: GT-free
# context_recall: GT gerektirir (eval dosyalarında ground_truth şart)
_METRICS_DEFAULT = [faithfulness, ContextUtilization(), context_recall]

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


def build_ragas_dataset(eval_records: list[dict], include_gt: bool = False) -> Dataset:
    """
    RAGAS Dataset formatına çevirir.

    include_gt=False (varsayılan): GT-free metrikler için — ground_truth alanı dahil edilmez.
    include_gt=True: context_recall gibi GT gerektiren metrikler için.
    """
    data = {
        "question": [r["question"] for r in eval_records],
        "answer":   [r["answer"][:1500] for r in eval_records],
        "contexts": [_truncate_contexts(r["contexts"]) for r in eval_records],
    }
    if include_gt:
        data["ground_truth"] = [r.get("ground_truth", "") for r in eval_records]
    return Dataset.from_dict(data)


def run_ragas_evaluation(
    eval_records: list[dict],
    evaluator_provider: str | None = None,
) -> dict:
    """
    RAGAS metrikleri hesaplar — faithfulness + context_utilization + context_recall.

    Args:
        eval_records:       [{"question", "answer", "contexts", "ground_truth"}, ...]
                            ground_truth context_recall için zorunlu.
        evaluator_provider: "haiku" veya "local" (varsayılan: RAGAS_PROVIDER env)

    Returns:
        {
            "scores":       {"faithfulness": float, "context_utilization": float,
                             "context_recall": float},
            "per_question": [{"question_id": int, "faithfulness": float,
                              "context_utilization": float, "context_recall": float}, ...]
        }
    """
    logger.info(f"RAGAS değerlendirmesi başlıyor: {len(eval_records)} soru")

    metrics = list(_METRICS_DEFAULT)
    dataset  = build_ragas_dataset(eval_records, include_gt=True)
    llm      = _get_llm(evaluator_provider)
    logger.info(f"Metrikler: {[m.name for m in metrics]}")

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=llm,
        run_config=RunConfig(
            max_workers=3,
            timeout=900,
            max_retries=3,
            seed=42,
        ),
        raise_exceptions=False,
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
        "faithfulness":        "Faithfulness       (sadakat)  ",
        "context_utilization": "Context Utilization (kullanım)",
        "context_recall":      "Context Recall     (kapsam)   ",
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
