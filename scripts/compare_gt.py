#!/usr/bin/env python3
import json, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

eskiler = json.load(open("data/eval/ragas_v3_questions.json", encoding="utf-8"))
yeniler = json.load(open(r"C:\Users\kesic\Downloads\gemini-code-1777482964796.json", encoding="utf-8"))

eski_map = {q["id"]: q for q in eskiler}
yeni_map = {q["id"]: q for q in yeniler}

ortak = sorted(set(eski_map) & set(yeni_map))
yeni_eklenen = sorted(set(yeni_map) - set(eski_map))
silinen = sorted(set(eski_map) - set(yeni_map))

print(f"Mevcut soru sayisi : {len(eskiler)}")
print(f"Gemini dosyasi     : {len(yeniler)}")
print(f"Ortak ID           : {len(ortak)}")
print(f"Yeni eklenen       : {yeni_eklenen}")
print(f"Silinen/eksik      : {silinen}")
print()

# GT uzunluk karşılaştırması
toplam_eski_len = sum(len(q["ground_truth"]) for q in eskiler if q["id"] in yeni_map)
toplam_yeni_len = sum(len(yeni_map[q["id"]]["ground_truth"]) for q in eskiler if q["id"] in yeni_map)
print(f"GT ortalama uzunluk (ortak {len(ortak)} soru):")
print(f"  Eski: {toplam_eski_len // len(ortak)} karakter")
print(f"  Yeni: {toplam_yeni_len // len(ortak)} karakter")
print()

# Değişen GT'ler
print("=" * 70)
print("DEGISEN GROUND TRUTH lar (ortak soru)")
print("=" * 70)
degisen = 0
for qid in ortak:
    eski_gt = eski_map[qid]["ground_truth"]
    yeni_gt = yeni_map[qid]["ground_truth"]
    eski_h  = eski_map[qid]["hedef_ilaclar"]
    yeni_h  = yeni_map[qid]["hedef_ilaclar"]
    gt_degisti   = eski_gt != yeni_gt
    hedef_degisti = eski_h != yeni_h
    if gt_degisti or hedef_degisti:
        degisen += 1
        soru = eski_map[qid]["soru"][:65]
        print(f"\n[{qid}] {soru}")
        if gt_degisti:
            print(f"  GT ESKI ({len(eski_gt)}c): {eski_gt[:150]}")
            print(f"  GT YENI ({len(yeni_gt)}c): {yeni_gt[:150]}")
        if hedef_degisti:
            print(f"  HEDEF DEGISTI:")
            for h in eski_h:
                print(f"    ESKI: {h}")
            for h in yeni_h:
                print(f"    YENI: {h}")

print(f"\n  Toplam degisen: {degisen}/{len(ortak)}")
print()

# Yeni sorular özeti
print("=" * 70)
print(f"YENI EKLENEN {len(yeni_eklenen)} SORU")
print("=" * 70)
for qid in yeni_eklenen:
    q = yeni_map[qid]
    print(f"  [{qid}] [{q['kategori']}] {q['soru'][:70]}")
    print(f"    GT: {q['ground_truth'][:100]}")
    print(f"    Hedef: {q['hedef_ilaclar']}")
    print()
