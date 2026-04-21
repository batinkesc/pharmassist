"""
RAGAS değerlendirme pipeline'ı.

Metrikler (LLM tabanlı — embedding gerektirmez):
  - faithfulness:   Yanıt yalnızca context'teki bilgilere mi dayanıyor?
  - context_recall: Ground truth'u karşılamak için yeterli chunk var mı?

Değerlendirici LLM:
  - Varsayılan: LM Studio / Mistral (RAGAS_PROVIDER=local, API maliyeti sıfır)
  - Alternatif: Claude Haiku (--evaluator haiku) — çok katı, production için önerilmez

Not (v10 bulgusu): Turkish patch (Haiku için prompt öneki) Context Recall'u
iyileştirmedi; kaldırıldı. Haiku'nun R=0.2 kalıcı sorunu prompt kaynaklı değil,
değerlendirici semantik katılığından kaynaklanıyor.
"""

import os
import numpy as np
from loguru import logger
from dotenv import load_dotenv

from src.core.content_policy import POLICY

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, context_recall
from ragas.run_config import RunConfig
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

load_dotenv()



def _get_llm(provider: str | None = None):
    """
    RAGAS için değerlendirici LLM döner.
    provider argümanı verilmezse env var'a bakar.
    """
    if provider is None:
        provider = os.environ.get("RAGAS_PROVIDER", "local")

    if provider == "haiku":
        logger.info("Değerlendirici: Claude Haiku (Anthropic API)")
        return ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            temperature=0,
            max_tokens=2048,
        )

    lm_studio_url = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")
    model_name = os.environ.get("LOCAL_MODEL_NAME", "mistralai/mistral-7b-instruct-v0.3")
    logger.info(f"Değerlendirici: {model_name} (LM Studio)")
    return ChatOpenAI(
        base_url=lm_studio_url,
        api_key="lm-studio",
        model=model_name,
        temperature=0,
        max_tokens=2048,
        timeout=600,
    )


# ContentPolicy'den gelir — rag_engine ile aynı değerler → drift engeli
_MAX_CONTEXTS    = POLICY.eval_max_contexts
_MAX_CHUNK_CHARS = POLICY.eval_max_chunk_chars


def _truncate_contexts(contexts: list[str]) -> list[str]:
    """RAGAS prompt'unun LLM context limitini aşmaması için kırpar."""
    truncated = []
    for ctx in contexts[:_MAX_CONTEXTS]:
        truncated.append(ctx[:_MAX_CHUNK_CHARS] + ("…" if len(ctx) > _MAX_CHUNK_CHARS else ""))
    return truncated


def build_ragas_dataset(eval_records: list[dict]) -> Dataset:
    """
    RAGAS Dataset formatına çevirir.

    Her kayıt:
      question:    str
      answer:      str   (RAG çıktısı)
      contexts:    list[str]  (retrieved chunk içerikleri)
      ground_truth: str  (beklenen doğru cevap)
    """
    return Dataset.from_dict({
        "question":    [r["question"] for r in eval_records],
        "answer":      [r["answer"][:1500] for r in eval_records],  # yanıt da kırp (NaN prevention)
        "contexts":    [_truncate_contexts(r["contexts"]) for r in eval_records],
        "ground_truth": [r["ground_truth"] for r in eval_records],
    })


def run_ragas_evaluation(eval_records: list[dict], evaluator_provider: str | None = None) -> dict:
    """
    RAGAS metrikleri hesaplar (LLM tabanlı).

    Args:
        eval_records: [{"question", "answer", "contexts", "ground_truth"}, ...]
        evaluator_provider: "haiku" (Anthropic API) veya "local" (LM Studio)

    Returns:
        {
            "scores": {"faithfulness": float, "context_recall": float},
            "per_question": [{"question_id": int, "faithfulness": float, "context_recall": float, ...}, ...]
        }
    """
    logger.info(f"RAGAS değerlendirmesi başlıyor: {len(eval_records)} soru")

    dataset = build_ragas_dataset(eval_records)
    llm = _get_llm(evaluator_provider)
    provider = evaluator_provider or os.environ.get("RAGAS_PROVIDER", "local")

    if provider == "haiku":
        logger.info("Değerlendirici LLM: claude-haiku-4-5-20251001 (Anthropic API)")
    else:
        logger.info(f"Değerlendirici LLM: {os.environ.get('LOCAL_MODEL_NAME', 'meta-llama-3.1-8b-instruct')} (LM Studio)")

    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, context_recall],
        llm=llm,
        run_config=RunConfig(max_workers=1, timeout=600),
        raise_exceptions=False,
    )

    def _mean(key: str) -> float:
        vals = result[key]
        if isinstance(vals, list):
            clean = [v for v in vals if v is not None and not (isinstance(v, float) and np.isnan(v))]
            return float(np.mean(clean)) if clean else float("nan")
        return float(vals)

    # Sorun #7: NaN olan soruları logla — kötü yanıtları maskelememek için
    for metric_key in ("faithfulness", "context_recall"):
        vals = result[metric_key]
        if isinstance(vals, list):
            nan_indices = [
                i for i, v in enumerate(vals)
                if v is None or (isinstance(v, float) and np.isnan(v))
            ]
            if nan_indices:
                nan_questions = [eval_records[i]["question"][:60] for i in nan_indices]
                logger.warning(
                    f"[NaN] {metric_key}: {len(nan_indices)} soru NaN "
                    f"(indeksler: {nan_indices}). Sorular: {nan_questions}"
                )

    scores = {
        "faithfulness":  round(_mean("faithfulness"), 4),
        "context_recall": round(_mean("context_recall"), 4),
    }

    # Per-question detayları topla
    per_question = []
    faith_vals = result["faithfulness"] if isinstance(result["faithfulness"], list) else [result["faithfulness"]]
    recall_vals = result["context_recall"] if isinstance(result["context_recall"], list) else [result["context_recall"]]

    for i, record in enumerate(eval_records):
        f_score = faith_vals[i] if i < len(faith_vals) else None
        r_score = recall_vals[i] if i < len(recall_vals) else None

        # NaN'ları float veya None'a dönüştür
        if isinstance(f_score, float) and np.isnan(f_score):
            f_score = None
        if isinstance(r_score, float) and np.isnan(r_score):
            r_score = None

        per_question.append({
            "question_id": i + 1,
            "question": record["question"],
            "faithfulness": round(f_score, 4) if f_score is not None else None,
            "context_recall": round(r_score, 4) if r_score is not None else None,
            "answer_length": len(record["answer"]),
            "n_contexts": len(record["contexts"]),
        })

    logger.info(f"RAGAS sonuçları: {scores}")
    return {
        "scores": scores,
        "per_question": per_question,
    }


def print_ragas_report(scores: dict, per_question: list[dict] | None = None) -> None:
    """Sonuçları formatlı olarak yazdırır."""
    print("\n" + "="*60)
    print("RAGAS DEĞERLENDİRME RAPORU")
    print("="*60)
    print(f"  Faithfulness   (sadakat) : {scores['faithfulness']:.4f} / 1.0")
    print(f"  Context Recall (kapsam)  : {scores['context_recall']:.4f} / 1.0")

    valid = [v for v in scores.values() if not (isinstance(v, float) and np.isnan(v))]
    ortalama = sum(valid) / len(valid) if valid else float("nan")
    print(f"\n  Genel Ortalama: {ortalama:.4f} / 1.0")

    if not np.isnan(ortalama):
        if ortalama >= 0.75:
            print("  Değerlendirme: KABUL EDILEBILIR (>=0.75)")
        elif ortalama >= 0.60:
            print("  Değerlendirme: GELISTIRILEBILIR (0.60-0.75)")
        else:
            print("  Değerlendirme: YETERSIZ (<0.60)")

    if per_question:
        print("\n" + "-"*60)
        print("SORU BAZLI SONUÇLAR:")
        for i, q in enumerate(per_question, 1):
            print(f"\n  Soru {i}: {q['question'][:60]}...")
            for metric, val in q.get("scores", {}).items():
                print(f"    {metric}: {val:.4f}")

    print("="*60)
