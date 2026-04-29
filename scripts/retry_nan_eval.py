"""
Run 15 NaN soruları için RAGAS retry scripti.
RAG pipeline yeniden çalıştırılmaz — mevcut answers + contexts kullanılır.
Sadece RAGAS evaluator yeniden çağrılır.

Kullanım:
    .venv/Scripts/python scripts/retry_nan_eval.py \
        --run15 data/eval/ragas_run15_results.json \
        --output data/eval/ragas_run15_merged.json
"""

import sys, os, json, math, argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.evaluation.ragas_eval import run_ragas_evaluation, print_ragas_report
import numpy as np


def is_nan(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def load_results(path: str) -> dict:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run15", default="data/eval/ragas_run15_results.json")
    parser.add_argument("--output", default="data/eval/ragas_run15_merged.json")
    args = parser.parse_args()

    data = load_results(args.run15)
    per_q = data["per_question"]

    # NaN olan soruları tespit et
    nan_indices = []
    for i, r in enumerate(per_q):
        if is_nan(r.get("faithfulness")) or is_nan(r.get("context_utilization")) or is_nan(r.get("context_recall")):
            nan_indices.append(i)

    logger.info(f"Toplam NaN soru: {len(nan_indices)} / {len(per_q)}")
    for i in nan_indices:
        r = per_q[i]
        logger.info(f"  [{i}] {r.get('soru_id','?')} — F={r.get('faithfulness')} CU={r.get('context_utilization')} CR={r.get('context_recall')}")

    if not nan_indices:
        logger.info("NaN yok, çıkılıyor.")
        sys.exit(0)

    # Retry için eval_records oluştur (mevcut RAG cevaplarından)
    retry_records = []
    for i in nan_indices:
        r = per_q[i]
        retry_records.append({
            "question":     r["question"],
            "answer":       r.get("ragas_answer") or r.get("answer", ""),
            "contexts":     r.get("contexts", []),
            "ground_truth": r.get("ground_truth", ""),
            "soru_id":      r.get("soru_id", ""),
        })

    logger.info(f"{len(retry_records)} soru için RAGAS evaluator yeniden çalıştırılıyor...")
    result = run_ragas_evaluation(retry_records)
    retry_per_q = result["per_question"]

    # Sonuçları orijinal per_q'ya merge et
    merged_per_q = list(per_q)
    for j, orig_idx in enumerate(nan_indices):
        new_scores = retry_per_q[j]
        old = merged_per_q[orig_idx]
        for key in ["faithfulness", "context_utilization", "context_recall"]:
            new_val = new_scores.get(key)
            old_val = old.get(key)
            if not is_nan(new_val):
                merged_per_q[orig_idx][key] = new_val
                if is_nan(old_val):
                    logger.info(f"  {old.get('soru_id','?')} {key}: NaN → {new_val:.4f}")
            else:
                logger.warning(f"  {old.get('soru_id','?')} {key}: hâlâ NaN")

    # Global skorları yeniden hesapla
    def recompute_mean(key):
        vals = [r.get(key) for r in merged_per_q]
        clean = [v for v in vals if not is_nan(v)]
        return round(float(np.mean(clean)), 4) if clean else float("nan")

    merged_scores = {
        "faithfulness":        recompute_mean("faithfulness"),
        "context_utilization": recompute_mean("context_utilization"),
        "context_recall":      recompute_mean("context_recall"),
    }

    print_ragas_report(merged_scores)

    output = {
        **data,
        "scores":      merged_scores,
        "per_question": merged_per_q,
        "_note": "Run 15 + NaN retry merged",
    }
    os.makedirs("data/eval", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logger.info(f"Merge edilmiş sonuçlar: {args.output}")
