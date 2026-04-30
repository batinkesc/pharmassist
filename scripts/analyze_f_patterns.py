#!/usr/bin/env python3
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = json.load(open("data/eval/ragas_run18_results.json", encoding="utf-8"))
pq = data["per_question"]

print("=== CYP iceren cevaplarda F ===")
for q in pq:
    ans = q["answer"] or ""
    if "[CYP450]" in ans:
        sid = q["soru_id"]
        f = q["faithfulness"] or 0
        print(f"  [{sid}] F:{f:.3f}  ansLen:{q['answer_length']}")

print()
print("=== Cevap uzunlugu vs F ===")
items = [(q["soru_id"], q["faithfulness"] or 0, q["answer_length"]) for q in pq]
long_low  = [(s,f,l) for s,f,l in items if l > 700 and f < 0.70]
long_high = [(s,f,l) for s,f,l in items if l > 700 and f >= 0.70]
short_avg = sum(f for _,f,l in items if l <= 500) / max(1, len([x for x in items if x[2] <= 500]))
long_avg  = sum(f for _,f,l in items if l > 700)  / max(1, len([x for x in items if x[2] > 700]))
print(f"  Kisa (<=500) ort F : {short_avg:.3f}")
print(f"  Uzun (>700)  ort F : {long_avg:.3f}")
print(f"  Uzun + Dusuk F (<0.70): {len(long_low)}")
for s,f,l in sorted(long_low, key=lambda x:x[1]):
    print(f"    [{s}] F:{f:.3f} len:{l}")

print()
print("=== DOGRULANAMADI veya BILGI YOK iceren cevaplar ===")
for q in pq:
    ans = q["answer"] or ""
    sid = q["soru_id"]
    f = q["faithfulness"] or 0
    if "DOGRULANAMADI" in ans.upper() or "DOĞRULANAMADI" in ans or "BILGI YOK" in ans.upper() or "BİLGİ YOK" in ans:
        print(f"  [{sid}] F:{f:.3f} ansLen:{q['answer_length']}")

print()
print("=== q16 detay ===")
for q in pq:
    if q["soru_id"] == "v3_q16":
        print("  soru_id:", q["soru_id"])
        print("  faithfulness:", q["faithfulness"])
        print("  answer[:300]:", (q["answer"] or "")[:300].replace("\n"," "))
        print("  ragas_answer:", (q.get("ragas_answer") or "")[:200].replace("\n"," "))
