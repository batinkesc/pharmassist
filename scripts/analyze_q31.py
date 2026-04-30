#!/usr/bin/env python3
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = json.load(open("data/eval/ragas_run18_results.json", encoding="utf-8"))
pq = data["per_question"]

# F=1.0 olan uzun cevaplar vs dusuk F uzun cevaplar
print("=== F=1.0 olan sorular (tum) ===")
perfect = [q for q in pq if (q["faithfulness"] or 0) >= 0.99]
for q in sorted(perfect, key=lambda x: x["answer_length"], reverse=True):
    sid = q["soru_id"]
    print(f"  [{sid}] F:1.0  len:{q['answer_length']}  n_ctx:{q['n_contexts']}")
    ans = (q["ragas_answer"] or q["answer"] or "")[:150].replace("\n", " ")
    print(f"    ragas_ans: {ans}")
    print()

print()
print("=== q31 tam ragas_answer ===")
for q in pq:
    if q["soru_id"] == "v3_q31":
        print("  Soru:", q["question"])
        print("  GT  :", q["ground_truth"])
        print("  n_ctx:", q["n_contexts"])
        print()
        print("  ragas_answer:")
        print(q.get("ragas_answer") or q["answer"])

print()
print("=== Uzun (>700) F>=0.80 olanlar - neden iyi? ===")
for q in pq:
    if q["answer_length"] > 700 and (q["faithfulness"] or 0) >= 0.80:
        sid = q["soru_id"]
        f = q["faithfulness"]
        print(f"  [{sid}] F:{f:.3f}  len:{q['answer_length']}  n_ctx:{q['n_contexts']}")
        ans = (q["ragas_answer"] or q["answer"] or "")[:200].replace("\n"," ")
        print(f"    {ans}")
        print()
