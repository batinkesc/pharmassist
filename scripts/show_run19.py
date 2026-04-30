#!/usr/bin/env python3
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

r19 = json.load(open("data/eval/ragas_run19_results.json", encoding="utf-8"))
s = r19["scores"]
f, cu, cr = s["faithfulness"], s["context_utilization"], s["context_recall"]
ort = (f + cu + cr) / 3

print("=== RUN 19 SONUCLARI ===")
print(f"Faithfulness     : {f:.4f}")
print(f"Context Util     : {cu:.4f}")
print(f"Context Recall   : {cr:.4f}")
print(f"Ortalama         : {ort:.4f}")
print(f"n_questions      : {r19['n_questions']}")
print()
print("vs Run 18 (F:0.7127 CU:0.7516 CR:0.9343 Ort:0.7995):")
print(f"  F  delta: {f-0.7127:+.4f}")
print(f"  CU delta: {cu-0.7516:+.4f}")
print(f"  CR delta: {cr-0.9343:+.4f}")
print(f"  Ort delta: {ort-0.7995:+.4f}")

print()
print("=== PER-QUESTION (F sirasiyla) ===")
pq = r19["per_question"]
items = [(q["soru_id"], q["faithfulness"] or 0, q["context_utilization"] or 0,
          q["context_recall"] or 0, q["answer_length"]) for q in pq]
items.sort(key=lambda x: x[1])
print("Dusuk F (<0.65):")
for sid, f2, cu2, cr2, l in items:
    if f2 < 0.65:
        print(f"  [{sid}] F:{f2:.3f}  CU:{cu2:.3f}  CR:{cr2:.3f}  len:{l}")

print()
print("Yuксek F (>=0.85):")
for sid, f2, cu2, cr2, l in sorted(items, key=lambda x:-x[1]):
    if f2 >= 0.85:
        print(f"  [{sid}] F:{f2:.3f}  CU:{cu2:.3f}  CR:{cr2:.3f}  len:{l}")

# R18 vs R19 per question karsilastirma
print()
print("=== R18 vs R19 PER QUESTION DEGISIMLER ===")
r18 = json.load(open("data/eval/ragas_run18_results.json", encoding="utf-8"))
r18_map = {q["soru_id"]: q for q in r18["per_question"]}
r19_map = {q["soru_id"]: q for q in pq}
degisimler = []
for sid in r19_map:
    if sid in r18_map:
        f18 = r18_map[sid]["faithfulness"] or 0
        f19 = r19_map[sid]["faithfulness"] or 0
        delta = f19 - f18
        l18 = r18_map[sid]["answer_length"]
        l19 = r19_map[sid]["answer_length"]
        degisimler.append((sid, f18, f19, delta, l18, l19))

degisimler.sort(key=lambda x: x[3])
print("En cok dusen (F):")
for sid, f18, f19, d, l18, l19 in degisimler[:5]:
    print(f"  [{sid}] {f18:.3f}->{f19:.3f} ({d:+.3f})  len:{l18}->{l19}")
print("En cok yukselen (F):")
for sid, f18, f19, d, l18, l19 in degisimler[-5:]:
    print(f"  [{sid}] {f18:.3f}->{f19:.3f} ({d:+.3f})  len:{l18}->{l19}")
print()
# Answer uzunluk degisimi
avg_len_18 = sum(q["answer_length"] for q in r18["per_question"]) / len(r18["per_question"])
avg_len_19 = sum(q["answer_length"] for q in pq) / len(pq)
print(f"Ort cevap uzunlugu: R18={avg_len_18:.0f} -> R19={avg_len_19:.0f} ({avg_len_19-avg_len_18:+.0f})")
