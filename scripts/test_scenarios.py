"""
Kapsamlı senaryo testi — 5 farklı klinik soru türü.
Çalıştır: .venv/Scripts/python scripts/test_scenarios.py
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.agents.patient_profile import PatientProfile
from src.agents.rag_engine import run_rag

SEPARATOR = "\n" + "="*70 + "\n"

SENARYOLAR = [
    {
        "id": 1,
        "baslik": "Kontrendikasyon — Penisilin Alerjisi + Augmentin",
        "soru": "Penisilin alerjisi olan bu çocuğa Augmentin yazılabilir mi?",
        "profil": PatientProfile(
            yas=7,
            cinsiyet="erkek",
            gfr=None,
            alerjiler=["penisilin"],
            endikasyonlar=["Sinüzit"],
        ),
        "hedef_ilaclar": None,
    },
    {
        "id": 2,
        "baslik": "Doz Ayarı — Böbrek Yetmezliği + Augmentin",
        "soru": "Böbrek yetmezliği olan hastada Augmentin dozu nasıl ayarlanmalı?",
        "profil": PatientProfile(
            yas=55,
            cinsiyet="kadın",
            gfr=25,
            endikasyonlar=["İdrar yolu enfeksiyonu"],
        ),
        "hedef_ilaclar": None,
    },
    {
        "id": 3,
        "baslik": "İlaç Etkileşimi — Varfarin + Parasetamol",
        "soru": "Varfarin kullanan hastaya parasetamol verilebilir mi, etkileşim riski var mı?",
        "profil": PatientProfile(
            yas=72,
            cinsiyet="erkek",
            gfr=55,
            mevcut_ilaclar=["Varfarin 5 mg"],
            endikasyonlar=["Atriyal fibrilasyon"],
        ),
        "hedef_ilaclar": None,
    },
    {
        "id": 4,
        "baslik": "Gebelik — Onaxan (Essitalopram) Güvenliği",
        "soru": "Gebeliğin ilk trimesterinde Onaxan kullanımı güvenli midir?",
        "profil": PatientProfile(
            yas=29,
            cinsiyet="kadın",
            gfr=None,
            gebelik=True,
            endikasyonlar=["Major Depresyon"],
        ),
        "hedef_ilaclar": None,
    },
    {
        "id": 5,
        "baslik": "Yan Etki — Plasorin (Atorvastatin) Kas Ağrısı",
        "soru": "Plasorin kullanan hastada kas ağrısı ve güçsüzlük başladı, bu ilaca bağlı olabilir mi?",
        "profil": PatientProfile(
            yas=61,
            cinsiyet="erkek",
            gfr=70,
            mevcut_ilaclar=["PLASORİN 10 mg tablet"],
            endikasyonlar=["Hiperlipidemi"],
        ),
        "hedef_ilaclar": None,
    },
]


def test_senaryo(s: dict) -> None:
    print(SEPARATOR)
    print(f"SENARYO {s['id']}: {s['baslik']}")
    print(f"Soru: {s['soru']}")
    print(f"Hasta: {s['profil'].yas}y, GFR={s['profil'].gfr}, Flags={s['profil'].aktif_flags}")
    print("-"*70)

    response = run_rag(
        soru=s["soru"],
        profil=s["profil"],
        hedef_ilaclar=s.get("hedef_ilaclar"),
    )

    print("YANIT:")
    print(response.yanit)
    print(f"\nKullanılan kaynaklar ({len(response.kaynaklar)} chunk):")
    for k in response.kaynaklar:
        alt = f"[{k.alt_madde}]" if k.alt_madde else ""
        print(f"  [{k.score:.3f}] {k.ilac_adi} | {k.madde_no}{alt} | s.{k.sayfa}")
    print(f"\nToken: {response.prompt_token_sayisi} giriş / {response.yanit_token_sayisi} çıkış")


if __name__ == "__main__":
    print("PharmAssist — Kapsamlı Senaryo Testi")
    print(f"Provider: {os.environ.get('LLM_PROVIDER', 'claude')}")

    for s in SENARYOLAR:
        try:
            test_senaryo(s)
        except Exception as e:
            print(f"HATA — Senaryo {s['id']}: {e}")

    print(SEPARATOR)
    print("Tüm senaryolar tamamlandı.")
