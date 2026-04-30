#!/usr/bin/env python3
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

r19 = json.load(open("data/eval/ragas_run19_results.json", encoding="utf-8"))
r18 = json.load(open("data/eval/ragas_run18_results.json", encoding="utf-8"))
r19m = {q["soru_id"]: q for q in r19["per_question"]}
r18m = {q["soru_id"]: q for q in r18["per_question"]}

print("=== REGRESYON: R18->R19 ===")
for sid in ["v3_q09", "v3_q06", "v3_q15", "v3_q10"]:
    q18 = r18m.get(sid)
    q19 = r19m.get(sid)
    if not q18 or not q19:
        continue
    f18 = q18["faithfulness"]
    f19 = q19["faithfulness"]
    l18 = q18["answer_length"]
    l19 = q19["answer_length"]
    print(f"[{sid}] F: {f18} -> {f19}  len: {l18} -> {l19}")
    ra18 = (q18.get("ragas_answer") or q18["answer"] or "")[:220].replace("\n", " ")
    ra19 = (q19.get("ragas_answer") or q19["answer"] or "")[:220].replace("\n", " ")
    print(f"  R18: {ra18}")
    print(f"  R19: {ra19}")
    print()

print()
print("=== IYILESEN: q16, q22, q03 ===")
for sid in ["v3_q16", "v3_q22", "v3_q03"]:
    q18 = r18m.get(sid)
    q19 = r19m.get(sid)
    if not q18 or not q19:
        continue
    f18 = q18["faithfulness"]
    f19 = q19["faithfulness"]
    l18 = q18["answer_length"]
    l19 = q19["answer_length"]
    print(f"[{sid}] F: {f18} -> {f19}  len: {l18} -> {l19}")
    ra19 = (q19.get("ragas_answer") or q19["answer"] or "")[:250].replace("\n", " ")
    print(f"  R19: {ra19}")
    print()

# Uzunluk dagilimi
print("=== UZUNLUK vs F R19 ===")
short = [q for q in r19["per_question"] if q["answer_length"] <= 700]
long_ = [q for q in r19["per_question"] if q["answer_length"] > 700]
avg_f_short = sum(q["faithfulness"] or 0 for q in short) / max(len(short), 1)
avg_f_long  = sum(q["faithfulness"] or 0 for q in long_) / max(len(long_), 1)
print(f"  <=700 chars ({len(short)} soru): ort F={avg_f_short:.3f}")
print(f"  >700  chars ({len(long_)} soru): ort F={avg_f_long:.3f}")
