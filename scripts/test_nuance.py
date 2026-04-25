"""Kontrendikasyon nüansı testi — model ne kadar detay veriyor?"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from src.agents.patient_profile import PatientProfile
from src.agents.rag_engine import run_rag

cases = [
    {
        "soru": "Child-Pugh A karaciğer yetmezliği olan hastada LİPİTOR dozu nasıl ayarlanmalı?",
        "profil": PatientProfile(yas=58, cinsiyet="erkek", karaciger_skoru="Child-Pugh A"),
        "beklenen": "Child-Pugh A hafif — kontrendike değil, ama doz/izlem bilgisi vermeli",
    },
    {
        "soru": "GFR 35 olan hastada JANUMET kullanılabilir mi?",
        "profil": PatientProfile(yas=62, cinsiyet="kadin", gfr=35),
        "beklenen": "GFR 35 borderline — sadece kontrendike demek değil, eşik ve alternatif vermeli",
    },
    {
        "soru": "GFR 15 olan hastada METAFORMAL kullanılabilir mi?",
        "profil": PatientProfile(yas=70, cinsiyet="erkek", gfr=15),
        "beklenen": "GFR 15 gerçekten kontrendike — ama neden + alternatif vermeli",
    },
]

for case in cases:
    print("=" * 60)
    print(f"SORU: {case['soru']}")
    print(f"BEKLENEN DAVRANIŞ: {case['beklenen']}")
    print("-" * 60)
    resp = run_rag(soru=case["soru"], profil=case["profil"])
    # Sadece SONUÇ bölümünü göster
    yanit = resp.yanit
    if "## SONUÇ" in yanit:
        sonuc_end = yanit.find("## KAYNAKLAR") if "## KAYNAKLAR" in yanit else yanit.find("## UYARI")
        sonuc = yanit[yanit.find("## SONUÇ"):sonuc_end].strip() if sonuc_end > 0 else yanit[yanit.find("## SONUÇ"):]
        print(sonuc[:600])
    print()
