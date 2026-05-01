"""
Cross-Evaluator Agreement — Run 20 yanıtlarını B evaluator ile yeniden skorla.

Kullanım:
  python scripts/cross_eval_agreement.py
  python scripts/cross_eval_agreement.py --run data/eval/ragas_run20_results.json

Çıktı:
  data/eval/cross_eval_agreement.json
  data/eval/cross_eval_agreement_report.md
"""

import os
import json
import argparse
from datetime import datetime
import numpy as np
import scipy.stats

from src.evaluation.ragas_eval import run_ragas_evaluation

def load_run20(filepath: str) -> dict:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"{filepath} bulunamadı.")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def build_records(run20: dict) -> list[dict]:
    records = []
    for pq in run20.get("per_question", []):
        records.append({
            "question": pq["question"],
            "answer": pq.get("ragas_answer", pq.get("answer", "")),
            "contexts": pq.get("contexts", []),
            "ground_truth": pq.get("ground_truth", ""),
        })
    return records

def compute_stats(scores_a: list[float], scores_b: list[float]) -> dict:
    valid_a = []
    valid_b = []
    n_nan_a = 0
    n_nan_b = 0

    for a, b in zip(scores_a, scores_b):
        a_is_nan = a is None or np.isnan(a)
        b_is_nan = b is None or np.isnan(b)
        
        if a_is_nan: n_nan_a += 1
        if b_is_nan: n_nan_b += 1
        
        if not a_is_nan and not b_is_nan:
            valid_a.append(a)
            valid_b.append(b)
            
    if len(valid_a) > 1:
        pearson_r, _ = scipy.stats.pearsonr(valid_a, valid_b)
        mean_abs_delta = float(np.mean([abs(a - b) for a, b in zip(valid_a, valid_b)]))
    else:
        pearson_r = float("nan")
        mean_abs_delta = float("nan")
        
    return {
        "pearson_r": round(float(pearson_r), 4) if not np.isnan(pearson_r) else None,
        "mean_abs_delta": round(float(mean_abs_delta), 4) if not np.isnan(mean_abs_delta) else None,
        "n_nan_a": n_nan_a,
        "n_nan_b": n_nan_b
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=str, default="data/eval/ragas_run20_results.json")
    args = parser.parse_args()

    print(f"[{datetime.now().time()}] Loading run 20 data from {args.run}")
    run20 = load_run20(args.run)
    records = build_records(run20)
    
    print(f"[{datetime.now().time()}] Running evaluator B for {len(records)} records")
    result_b = run_ragas_evaluation(records, evaluator_provider="model_b")
    
    evaluator_a = run20.get("model", "Qwen/Qwen3-235B-A22B-Instruct-2507-tput")
    evaluator_b = os.environ.get("RAGAS_MODEL_2", "deepseek-ai/DeepSeek-V3-1")
    
    metrics = ["faithfulness", "context_utilization", "context_recall"]
    
    per_metric = {}
    high_disagreement = []
    per_question = []
    
    pq_a = run20.get("per_question", [])
    pq_b = result_b.get("per_question", [])
    
    for m in metrics:
        scores_a = [q.get(m) for q in pq_a]
        scores_b = [q.get(m) for q in pq_b]
        per_metric[m] = compute_stats(scores_a, scores_b)
        
    for i in range(len(records)):
        question_id = f"Q{i+1:02d}"
        q_entry = {"soru_id": question_id}
        qa = pq_a[i] if i < len(pq_a) else {}
        qb = pq_b[i] if i < len(pq_b) else {}

        for m in metrics:
            va = qa.get(m)
            vb = qb.get(m)
            q_entry[f"{m}_a"] = va
            q_entry[f"{m}_b"] = vb

            a_nan = va is None or (isinstance(va, float) and np.isnan(va))
            b_nan = vb is None or (isinstance(vb, float) and np.isnan(vb))

            # En bilgilendirici disagreement: bir evaluator NaN, diğeri valid
            if a_nan and not b_nan:
                high_disagreement.append({
                    "soru_id": question_id,
                    "metric": m,
                    "score_a": "NaN",
                    "score_b": vb,
                    "delta": "NaN (A failed)",
                })
            elif b_nan and not a_nan:
                high_disagreement.append({
                    "soru_id": question_id,
                    "metric": m,
                    "score_a": va,
                    "score_b": "NaN",
                    "delta": "NaN (B failed)",
                })
            elif not a_nan and not b_nan:
                delta = abs(va - vb)
                if delta > 0.25:
                    high_disagreement.append({
                        "soru_id": question_id,
                        "metric": m,
                        "score_a": va,
                        "score_b": vb,
                        "delta": round(delta, 4),
                    })

        per_question.append(q_entry)
        
    output = {
        "run_a": os.path.basename(args.run),
        "evaluator_a": evaluator_a,
        "evaluator_b": evaluator_b,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "per_metric": per_metric,
        "high_disagreement": high_disagreement,
        "per_question": per_question
    }
    
    out_json = "data/eval/cross_eval_agreement.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        
    out_md = "data/eval/cross_eval_agreement_report.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Cross-Evaluator Agreement Raporu\n")
        f.write(f"Tarih: {output['date']}  |  Evaluator A: {evaluator_a}  |  Evaluator B: {evaluator_b}\n\n")
        
        f.write("## Özet\n")
        f.write("| Metrik | Pearson r | Mean |Δ| | A NaN | B NaN |\n")
        f.write("|---|---|---|---|---|\n")
        for m in metrics:
            stat = per_metric[m]
            r = stat["pearson_r"]
            d = stat["mean_abs_delta"]
            r_str = f"{r:.2f}" if r is not None else "N/A"
            d_str = f"{d:.2f}" if d is not None else "N/A"
            f.write(f"| {m} | {r_str} | {d_str} | {stat['n_nan_a']} | {stat['n_nan_b']} |\n")
            
        f.write("\n## Yüksek Disagreement (|Δ| > 0.25 veya NaN vs valid skor)\n")
        f.write("| Soru ID | Metrik | Skor A | Skor B | Δ |\n")
        f.write("|---|---|---|---|---|\n")
        for hd in high_disagreement:
            sa = f"{hd['score_a']:.2f}" if isinstance(hd['score_a'], float) else hd['score_a']
            sb = f"{hd['score_b']:.2f}" if isinstance(hd['score_b'], float) else hd['score_b']
            d = f"{hd['delta']:.2f}" if isinstance(hd['delta'], float) else hd['delta']
            f.write(f"| {hd['soru_id']} | {hd['metric']} | {sa} | {sb} | {d} |\n")

        # En çok anlaşmazlık olan metrik (en düşük r veya en yüksek delta)
        valid_metrics = [(m, per_metric[m]) for m in metrics if per_metric[m]["pearson_r"] is not None]
        if valid_metrics:
            worst = min(valid_metrics, key=lambda x: x[1]["pearson_r"])
            best = max(valid_metrics, key=lambda x: x[1]["pearson_r"])
            worst_str = f"{worst[0]} (r={worst[1]['pearson_r']:.2f})"
            best_str = f"{best[0]} (r={best[1]['pearson_r']:.2f})"
        else:
            worst_str = "N/A"
            best_str = "N/A"

        f.write("\n## Yorum\n")
        f.write("- **Korelasyon eşikleri:** 0.7+ = acceptable, 0.5–0.7 = moderate, <0.5 = low\n")
        f.write(f"- **En yüksek anlaşma:** {best_str}\n")
        f.write(f"- **En düşük anlaşma:** {worst_str}\n")
        f.write(f"- **Toplam high-disagreement vakası:** {len(high_disagreement)} (33 soru × 3 metrik = 99 değerlendirmeden)\n")
        
    print(f"[{datetime.now().time()}] Done! Wrote to {out_json} and {out_md}")

if __name__ == "__main__":
    main()
