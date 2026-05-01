import json
import numpy as np

with open("data/eval/cross_eval_agreement.json", "r", encoding="utf-8") as f:
    data = json.load(f)

high_disagreement = []
for q in data["per_question"]:
    q_id = q["soru_id"]
    for m in ["faithfulness", "context_utilization", "context_recall"]:
        va = q.get(f"{m}_a")
        vb = q.get(f"{m}_b")
        
        a_nan = va is None or np.isnan(va) if va is not None else True
        b_nan = vb is None or np.isnan(vb) if vb is not None else True
        
        if a_nan and not b_nan:
            high_disagreement.append({
                "soru_id": q_id,
                "metric": m,
                "score_a": "NaN",
                "score_b": vb,
                "delta": "NaN (A failed)"
            })
        elif b_nan and not a_nan:
            high_disagreement.append({
                "soru_id": q_id,
                "metric": m,
                "score_a": va,
                "score_b": "NaN",
                "delta": "NaN (B failed)"
            })
        elif not a_nan and not b_nan:
            delta = abs(va - vb)
            if delta > 0.25:
                high_disagreement.append({
                    "soru_id": q_id,
                    "metric": m,
                    "score_a": va,
                    "score_b": vb,
                    "delta": round(delta, 4)
                })

data["high_disagreement"] = high_disagreement

with open("data/eval/cross_eval_agreement.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

with open("data/eval/cross_eval_agreement_report.md", "w", encoding="utf-8") as f:
    f.write("# Cross-Evaluator Agreement Raporu\n")
    f.write(f"Tarih: {data['date']}  |  Evaluator A: {data['evaluator_a']}  |  Evaluator B: {data['evaluator_b']}\n\n")
    
    f.write("## Özet\n")
    f.write("| Metrik | Pearson r | Mean |Δ| | A NaN | B NaN |\n")
    f.write("|---|---|---|---|---|\n")
    for m in ["faithfulness", "context_utilization", "context_recall"]:
        stat = data["per_metric"][m]
        r = stat["pearson_r"]
        d = stat["mean_abs_delta"]
        r_str = f"{r:.2f}" if r is not None else "N/A"
        d_str = f"{d:.2f}" if d is not None else "N/A"
        f.write(f"| {m} | {r_str} | {d_str} | {stat['n_nan_a']} | {stat['n_nan_b']} |\n")
        
    f.write("\n## Yüksek Disagreement (|Δ| > 0.25 veya NaN vs Skor)\n")
    f.write("| Soru ID | Metrik | Skor A | Skor B | Δ |\n")
    f.write("|---|---|---|---|---|\n")
    for hd in high_disagreement:
        sa = f"{hd['score_a']:.2f}" if isinstance(hd['score_a'], float) else hd['score_a']
        sb = f"{hd['score_b']:.2f}" if isinstance(hd['score_b'], float) else hd['score_b']
        delta = f"{hd['delta']:.2f}" if isinstance(hd['delta'], float) else hd['delta']
        f.write(f"| {hd['soru_id']} | {hd['metric']} | {sa} | {sb} | {delta} |\n")
        
    f.write("\n## Yorum\n")
    f.write("- Korelasyon yorumu (0.7+ = acceptable, 0.5-0.7 = moderate, <0.5 = low)\n")
    f.write("- NaN vs valid skor durumları en ciddi disagreement olarak rapora eklendi.\n")
