#!/usr/bin/env python3
"""
Mini Run 20 — 6 soru, yeni 3-katman format testi.
Seçim kriteri:
  - R18'de düşük F: q10(0.25), q22(0.17), q03(0.50), q26(0.30)
  - R18'de yüksek F (kontrol): q09(1.0), q28(1.0)
"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.rag_engine import run_rag
from src.agents.patient_profile import PatientProfile

HEDEF_IDS = {"v3_q10", "v3_q22", "v3_q03", "v3_q26", "v3_q09", "v3_q28"}

sorular = json.load(open("data/eval/ragas_v3_questions.json", encoding="utf-8"))
secilen = [q for q in sorular if q["id"] in HEDEF_IDS]

print(f"Mini test: {len(secilen)} soru\n")
print("=" * 70)

for q in secilen:
    h = q.get("hasta", {})
    profil = PatientProfile(
        yas=h.get("yas", 0),
        cinsiyet=h.get("cinsiyet", "belirtilmemiş"),
        gfr=h.get("gfr"),
        karaciger_skoru=h.get("karaciger_skoru"),
        mevcut_ilaclar=h.get("mevcut_ilaclar", []),
        alerjiler=h.get("alerjiler", []),
        endikasyonlar=h.get("endikasyonlar", []),
        gebelik=h.get("gebelik", False),
        emzirme=h.get("emzirme", False),
        lab_degerleri=h.get("lab_degerleri", {}),
    )
    resp = run_rag(soru=q["soru"], profil=profil, hedef_ilaclar=q.get("hedef_ilaclar"))

    yanit = resp.yanit
    has_kub_aktarim  = "[KÜB Aktarımı]" in yanit or "**[KÜB Aktarımı]**" in yanit
    has_sistem       = "[Sistem Tespitleri]" in yanit or "**[Sistem Tespitleri]**" in yanit
    has_degerlendirme= "[Değerlendirme]" in yanit or "**[Değerlendirme]**" in yanit
    dogru_count      = yanit.count("[DOĞRULANAMADI]") + yanit.count("[DOĞRULANAMADI-")

    sonuc_start = yanit.find("## SONUÇ")
    uyari_start = yanit.find("## UYARI")
    sonuc_text  = yanit[sonuc_start:uyari_start].strip() if uyari_start > 0 else yanit[sonuc_start:sonuc_start+600]

    print(f"[{q['id']}] {q['soru'][:65]}")
    print(f"  GT: {q['ground_truth'][:100]}")
    print(f"  Format: KÜB={'✓' if has_kub_aktarim else '✗'}  Sistem={'✓' if has_sistem else '-'}  Değ={'✓' if has_degerlendirme else '✗'}  DOĞRULANAMADI:{dogru_count}")
    print(f"  SONUÇ ({len(sonuc_text)}c):")
    print("  " + sonuc_text[:400].replace("\n", "\n  "))
    print()
