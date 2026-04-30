#!/usr/bin/env python3
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = json.load(open("data/eval/ragas_run18_results.json", encoding="utf-8"))
pq = data["per_question"]

low_f = [q for q in pq if (q["faithfulness"] or 0) < 0.65]
low_f.sort(key=lambda x: x["faithfulness"] or 0)

print(f"Dusuk F (<0.65) soru sayisi: {len(low_f)}\n")
for q in low_f:
    f = q["faithfulness"]
    cu = q["context_utilization"]
    cr = q["context_recall"]
    sid = q["soru_id"]
    soru = q["question"][:80]
    ans_len = q["answer_length"]
    n_ctx = q["n_contexts"]
    ans = (q["answer"] or "")[:300].replace("\n", " ")
    gt = (q["ground_truth"] or "")[:150].replace("\n", " ")
    print(f"[{sid}]  F:{f}  CU:{cu:.3f}  CR:{cr:.3f}")
    print(f"  Soru   : {soru}")
    print(f"  AnsLen : {ans_len}  n_ctx: {n_ctx}")
    print(f"  Cevap  : {ans}")
    print(f"  GT     : {gt}")
    print()
