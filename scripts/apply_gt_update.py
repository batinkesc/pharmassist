#!/usr/bin/env python3
"""
Gemini GT revizyonunu uygula:
 - Gemini dosyasını temel al (kısa GT + ® temizliği + q34)
 - q01: karbamazepin substrat/indükleyici bilgisini koru
 - data/eval/ragas_v3_questions.json üzerine yaz
"""
import json, sys, shutil
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
HEDEF = ROOT / "data" / "eval" / "ragas_v3_questions.json"
GEMINI = Path(r"C:\Users\kesic\Downloads\gemini-code-1777482964796.json")
YEDEK  = ROOT / "data" / "eval" / "ragas_v3_questions_backup_pre_gemini.json"

# ── 1. Mevcut dosyayı yedekle ────────────────────────────────────────────
shutil.copy(HEDEF, YEDEK)
print(f"Yedek: {YEDEK.name}")

# ── 2. Gemini dosyasını yükle ────────────────────────────────────────────
sorular = json.load(open(GEMINI, encoding="utf-8"))

# ── 3. Manuel düzeltmeler ────────────────────────────────────────────────

# q01: Karbamazepin hem CYP3A4 substratı hem de indükleyicidir — bu çift
# rol önemli klinik bilgi; Gemini'nin kısa versiyonu bunu gizliyor.
for q in sorular:
    if q["id"] == "v3_q01":
        q["ground_truth"] = (
            "Karbamazepin (TEGRETOL) güçlü bir CYP3A4 indükleyicisidir; "
            "aynı zamanda kendisi de CYP3A4 substratıdır. "
            "CYP3A4 substratı olan amiodaronun (SANORONE) plazma düzeyini düşürebilir. "
            "Birlikte kullanımda kontrendike değildir ancak etkileşim nedeniyle dikkatli olunmalıdır."
        )
        print(f"[q01] GT güncellendi (substrat/indükleyici not korundu)")

# q05: Gemini'nin iyileştirmesi zaten doğru — "koagülopati ile ilişkili
# klinik olarak anlamlı kanama riski taşıyan" KÜB metnine daha yakın.
# Değişiklik gerekmez.

# ── 4. Kaydet ────────────────────────────────────────────────────────────
with open(HEDEF, "w", encoding="utf-8") as f:
    json.dump(sorular, f, ensure_ascii=False, indent=2)

print(f"\nKaydedildi: {HEDEF.name}")
print(f"  Toplam soru : {len(sorular)}")
print(f"  Yeni soru   : v3_q34 (negatif_bilgi_yok) dahil")

# ── 5. Hızlı doğrulama ───────────────────────────────────────────────────
print("\n=== DOGRULAMA (ilk 5 GT) ===")
for q in sorular[:5]:
    print(f"  [{q['id']}] {len(q['ground_truth'])}c | {q['ground_truth'][:80]}...")

print("\n=== HEDEF ILACLAR (® kalmadi mi?) ===")
toplam_ilac = 0
ring_kalan = 0
for q in sorular:
    for h in q["hedef_ilaclar"]:
        toplam_ilac += 1
        if "®" in h:
            ring_kalan += 1
            print(f"  [!] {q['id']}: {h}")
if ring_kalan == 0:
    print(f"  Tum {toplam_ilac} hedef ilacta ® simgesi yok. OK")
