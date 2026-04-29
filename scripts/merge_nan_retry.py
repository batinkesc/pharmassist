"""
merge_nan_retry.py — Run 14 NaN retry sonuçlarını ana sonuçlarla birleştirir.

NaN olan sorular retry'dan gelen değerlerle doldurulur.
Kullanım:
    python scripts/merge_nan_retry.py \
        --base data/eval/ragas_v9_run14_results.json \
        --retry data/eval/ragas_run14_nan_retry_results.json \
        --output data/eval/ragas_v9_run14_merged.json
"""
import json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base",   required=True, help="Run 14 ana sonuç dosyası")
    parser.add_argument("--retry",  required=True, help="NaN retry sonuç dosyası")
    parser.add_argument("--output", required=True, help="Birleştirilmiş çıktı")
    args = parser.parse_args()

    with open(args.base,  encoding="utf-8") as f: base  = json.load(f)
    with open(args.retry, encoding="utf-8") as f: retry = json.load(f)

    metrics = ["faithfulness", "context_utilization", "context_recall"]

    # retry sonuçlarını id ile indeksle
    retry_by_id = {r["id"]: r for r in retry.get("results", [])}

    replaced = {m: 0 for m in metrics}
    for row in base.get("results", []):
        rid = row.get("id")
        if rid in retry_by_id:
            rr = retry_by_id[rid]
            for m in metrics:
                base_val  = row.get(m)
                retry_val = rr.get(m)
                is_nan = (base_val is None) or (isinstance(base_val, float) and base_val != base_val)
                has_val = (retry_val is not None) and not (isinstance(retry_val, float) and retry_val != retry_val)
                if is_nan and has_val:
                    row[m] = retry_val
                    replaced[m] += 1
                    print(f"  ✅ [{rid}] {m}: NaN → {retry_val:.4f}")

    # Ortalamaları yeniden hesapla (NaN'ları atla)
    summary = {}
    for m in metrics:
        vals = [r[m] for r in base["results"] if r.get(m) is not None and not (isinstance(r[m], float) and r[m] != r[m])]
        summary[m] = round(sum(vals) / len(vals), 4) if vals else None
        nan_count = sum(1 for r in base["results"] if r.get(m) is None or (isinstance(r[m], float) and r[m] != r[m]))
        print(f"  {m}: {summary[m]:.4f}  ({nan_count} NaN kaldı)")

    base["summary"] = summary
    base["avg"] = round(sum(v for v in summary.values() if v) / len(metrics), 4)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"  Faithfulness       : {summary.get('faithfulness', 'N/A')}")
    print(f"  Context Utilization: {summary.get('context_utilization', 'N/A')}")
    print(f"  Context Recall     : {summary.get('context_recall', 'N/A')}")
    print(f"  Genel Ortalama     : {base['avg']}")
    print(f"{'='*50}")
    print(f"\nKaydedildi: {args.output}")
    for m, n in replaced.items():
        print(f"  {m}: {n} NaN dolduruldu")

if __name__ == "__main__":
    main()
