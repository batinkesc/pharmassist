"""
Klinik Validasyon Script'i — 15 Senaryo (Dalga 4 Phase 6)

Senaryo türleri:
  - Kontrendikasyon (alerji / mutlak KI)
  - Doz ayarı (böbrek / karaciğer / yaş)
  - İlaç etkileşimi (CYP450 / farmakodinamik)
  - Gebelik / emzirme güvenliği
  - "Bilgi yok" testi (3 soru kasıtlı corpus dışı — hallucination kontrolü)

Hallucination test soruları: S13, S14, S15
  → Bu sorular için sistem "bilgi yok" demeli, veri uydurmamali.
  → RAGAS hesaplanırken bu sorular otomatik dışarıda bırakılır.

Kullanım:
    .venv/Scripts/python scripts/klinik_test.py
    .venv/Scripts/python scripts/klinik_test.py --soru 3       # Tek soru
    .venv/Scripts/python scripts/klinik_test.py --sadece-db    # Hallucination soruları hariç
    .venv/Scripts/python scripts/klinik_test.py --output results/klinik_v1.json
"""

import sys, os, json, argparse, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.agents.patient_profile import PatientProfile
from src.agents.rag_engine import run_rag

SEPARATOR = "\n" + "=" * 70 + "\n"

# ---------------------------------------------------------------------------
# Senaryo tanımları
# ---------------------------------------------------------------------------

# Hallucination (corpus dışı) test soruları — bu ID'ler RAGAS'tan çıkarılır
HALLUCINATION_IDS = {13, 14, 15}

SENARYOLAR = [

    # -----------------------------------------------------------------------
    # S01 — Kontrendikasyon: Penisilin alerjisi + AUGMENTİN
    # -----------------------------------------------------------------------
    {
        "id": 1,
        "tur": "kontrendikasyon",
        "baslik": "Penisilin Alerjisi + AUGMENTİN",
        "soru": "Penisilin alerjisi olan 8 yaşındaki çocuğa AUGMENTİN oral süspansiyon yazılabilir mi?",
        "profil": PatientProfile(
            yas=8,
            cinsiyet="erkek",
            alerjiler=["penisilin"],
            endikasyonlar=["akut otitis media"],
        ),
        "hedef_ilaclar": ["AUGMENTİN"],
        "beklenen": "Kontrendike; penisilin alerjisi AUGMENTİN (amoksisilin/klavulanik asit) için mutlak kontrendikasyon.",
    },

    # -----------------------------------------------------------------------
    # S02 — Doz Ayarı: Böbrek Yetmezliği + KEPPRA
    # -----------------------------------------------------------------------
    {
        "id": 2,
        "tur": "doz_ayari",
        "baslik": "Böbrek Yetmezliği (GFR 28) + KEPPRA",
        "soru": "GFR 28 olan epilepsi hastasında KEPPRA dozu nasıl ayarlanmalı?",
        "profil": PatientProfile(
            yas=45,
            cinsiyet="kadın",
            gfr=28.0,
            endikasyonlar=["epilepsi"],
        ),
        "hedef_ilaclar": ["KEPPRA"],
        "beklenen": "Şiddetli böbrek yetmezliğinde KEPPRA dozu azaltılmalı; KÜB'de GFR eşiğine göre spesifik doz önerisi var.",
    },

    # -----------------------------------------------------------------------
    # S03 — İlaç Etkileşimi (CYP2C9): PLASORİN + FLAGYL
    # -----------------------------------------------------------------------
    {
        "id": 3,
        "tur": "etkilesim_cyp",
        "baslik": "PLASORİN (Warfarin) + FLAGYL (Metronidazol) — CYP2C9",
        "soru": "PLASORİN kullanan hastaya FLAGYL eklenmesi INR'ı nasıl etkiler?",
        "profil": PatientProfile(
            yas=68,
            cinsiyet="erkek",
            gfr=55.0,
            mevcut_ilaclar=["PLASORİN 10 mg"],
            endikasyonlar=["atriyal fibrilasyon"],
            lab_degerleri={"inr": 2.5},
        ),
        "hedef_ilaclar": ["PLASORİN", "FLAGYL"],
        "beklenen": "FLAGYL (metronidazol) CYP2C9 inhibitörü olarak PLASORİN metabolizmasını yavaşlatır → INR yükselir, kanama riski artar.",
    },

    # -----------------------------------------------------------------------
    # S04 — Gebelik Güvenliği: LANTUS (Glargin İnsülin)
    # -----------------------------------------------------------------------
    {
        "id": 4,
        "tur": "gebelik",
        "baslik": "Gebelik + LANTUS",
        "soru": "Gebeliğin 2. trimesterinde tip-2 diyabetik hastaya LANTUS SoloStar kullanımı güvenli midir?",
        "profil": PatientProfile(
            yas=32,
            cinsiyet="kadın",
            endikasyonlar=["tip-2 diyabet"],
            gebelik=True,
            lab_degerleri={"HbA1c": 7.8},
        ),
        "hedef_ilaclar": ["LANTUS"],
        "beklenen": "LANTUS'un gebelikte kullanımı KÜB'de belirtilmeli; klinisyen gözetiminde dikkatli kullanım.",
    },

    # -----------------------------------------------------------------------
    # S05 — Serotonin Sendromu: LUSTRAL + CONTRAMAL
    # -----------------------------------------------------------------------
    {
        "id": 5,
        "tur": "etkilesim_farmakodinamik",
        "baslik": "Serotonin Sendromu — LUSTRAL + CONTRAMAL",
        "soru": "LUSTRAL kullanan depresyon hastasına ağrı için CONTRAMAL eklenmesi güvenli midir?",
        "profil": PatientProfile(
            yas=52,
            cinsiyet="kadın",
            mevcut_ilaclar=["LUSTRAL 50 mg"],
            endikasyonlar=["depresyon", "kronik ağrı"],
        ),
        "hedef_ilaclar": ["LUSTRAL", "CONTRAMAL"],
        "beklenen": "Serotonin sendromu riski; LUSTRAL (SSRI) + CONTRAMAL (tramadol) kombinasyonu dikkatle kullanılmalı veya kaçınılmalı.",
    },

    # -----------------------------------------------------------------------
    # S06 — Karaciğer Yetmezliği: CRESTOR
    # -----------------------------------------------------------------------
    {
        "id": 6,
        "tur": "doz_ayari",
        "baslik": "Karaciğer Yetmezliği + CRESTOR",
        "soru": "Child-Pugh B karaciğer yetmezliği olan hastada CRESTOR kullanılabilir mi?",
        "profil": PatientProfile(
            yas=59,
            cinsiyet="erkek",
            karaciger_skoru="Child-Pugh B",
            endikasyonlar=["hiperlipidemi", "karaciğer sirozu"],
            lab_degerleri={"ALT": 120, "AST": 135},
        ),
        "hedef_ilaclar": ["CRESTOR"],
        "beklenen": "Aktif karaciğer hastalığı CRESTOR için kontrendikasyon; Child-Pugh B'de kullanılmamalı.",
    },

    # -----------------------------------------------------------------------
    # S07 — CYP2D6 Etkileşimi: CİPRO + PLASORİN (CYP1A2 inhibisyonu)
    # -----------------------------------------------------------------------
    {
        "id": 7,
        "tur": "etkilesim_cyp",
        "baslik": "CİPRO (Siprofloksasin) + PLASORİN — CYP1A2",
        "soru": "PLASORİN kullanan hastada enfeksiyon için CİPRO başlanırsa INR takibi gerekir mi?",
        "profil": PatientProfile(
            yas=71,
            cinsiyet="kadın",
            gfr=52.0,
            mevcut_ilaclar=["PLASORİN 10 mg"],
            endikasyonlar=["atriyal fibrilasyon", "üriner sistem enfeksiyonu"],
            lab_degerleri={"inr": 2.1},
        ),
        "hedef_ilaclar": ["CİPRO", "PLASORİN"],
        "beklenen": "CİPRO güçlü CYP1A2 inhibitörü; PLASORİN (warfarin) CYP1A2 substratı → INR yükselir, yakın takip şart.",
    },

    # -----------------------------------------------------------------------
    # S08 — Yaşlı Hasta: XANAX (Alprazolam)
    # -----------------------------------------------------------------------
    {
        "id": 8,
        "tur": "populasyon",
        "baslik": "Yaşlı Hasta (83 yaş) + XANAX",
        "soru": "83 yaşındaki demans hastasına anksiyete için XANAX başlanabilir mi?",
        "profil": PatientProfile(
            yas=83,
            cinsiyet="kadın",
            gfr=40.0,
            endikasyonlar=["demans", "anksiyete"],
        ),
        "hedef_ilaclar": ["XANAX"],
        "beklenen": "Yaşlı hastalarda benzo kullanımı önerilmez; KÜB'de geriyatrik popülasyonda dikkatli kullanım ve düşük doz.",
    },

    # -----------------------------------------------------------------------
    # S09 — Emzirme Güvenliği: FLAGYL 500 mg
    # -----------------------------------------------------------------------
    {
        "id": 9,
        "tur": "emzirme",
        "baslik": "Emzirme + FLAGYL 500 mg",
        "soru": "Emziren anne trikomoniyazis tedavisi için FLAGYL 500 mg kullanabilir mi?",
        "profil": PatientProfile(
            yas=28,
            cinsiyet="kadın",
            emzirme=True,
            endikasyonlar=["trikomoniyazis"],
        ),
        "hedef_ilaclar": ["FLAGYL"],
        "beklened": "FLAGYL süte geçer; emzirme sırasında tek doz 2g tercih edilir ve 12-24 saat emzirme kesilmeli.",
    },

    # -----------------------------------------------------------------------
    # S10 — Pediatrik Doz: NEURONTİN (Gabapentin)
    # -----------------------------------------------------------------------
    {
        "id": 10,
        "tur": "pediatrik",
        "baslik": "Pediatrik Hasta (10 yaş) + NEURONTİN",
        "soru": "Epilepsisi olan 10 yaşındaki çocukta NEURONTİN'in dozu nasıl belirlenmeli?",
        "profil": PatientProfile(
            yas=10,
            cinsiyet="erkek",
            endikasyonlar=["parsiyel epilepsi"],
        ),
        "hedef_ilaclar": ["NEURONTİN"],
        "beklenen": "KÜB'de 6-12 yaş arası pediyatrik doz rehberi; kg başına doz hesabı gerekir.",
    },

    # -----------------------------------------------------------------------
    # S11 — CYP2C19 Etkileşimi: PLAVIX + LANSOR
    # -----------------------------------------------------------------------
    {
        "id": 11,
        "tur": "etkilesim_cyp",
        "baslik": "PLAVIX + LANSOR — CYP2C19 Etkileşimi",
        "soru": "PLAVIX kullanan kardiyak stent hastasına mide koruma için LANSOR eklenirse ne olur?",
        "profil": PatientProfile(
            yas=64,
            cinsiyet="erkek",
            gfr=65.0,
            mevcut_ilaclar=["PLAVIX 75 mg", "ASPİRİN 100 mg"],
            endikasyonlar=["koroner stent", "gastroözofajeal reflü"],
        ),
        "hedef_ilaclar": ["PLAVIX", "LANSOR"],
        "beklenen": "LANSOR (lansoprazol) CYP2C19 inhibitörü; PLAVIX (klopidogrel) CYP2C19 üzerinden aktif metabolite dönüşür → antiplatelet etki azalır, stent trombozu riski artar.",
    },

    # -----------------------------------------------------------------------
    # S12 — Böbrek Yetmezliği + Kombine: DİAMİCRON + GFR 40
    # -----------------------------------------------------------------------
    {
        "id": 12,
        "tur": "doz_ayari",
        "baslik": "GFR 40 + DİAMİCRON MR (Gliklazid)",
        "soru": "GFR 40 olan tip-2 diyabetik hastada DİAMİCRON MR kullanımı güvenli midir?",
        "profil": PatientProfile(
            yas=67,
            cinsiyet="erkek",
            gfr=40.0,
            endikasyonlar=["tip-2 diyabet", "kronik böbrek hastalığı"],
            lab_degerleri={"HbA1c": 8.2, "kreatinin": 1.9},
        ),
        "hedef_ilaclar": ["DİAMİCRON"],
        "beklenen": "GFR 40'ta DİAMİCRON dikkatli kullanılabilir; hipoglisemi riski artar, yakın kan şekeri takibi gerekir.",
    },

    # -----------------------------------------------------------------------
    # S13 — HALLUCINATION TEST: Verapamil — Corpus'ta YOK
    # -----------------------------------------------------------------------
    {
        "id": 13,
        "tur": "hallucination_test",
        "baslik": "[HALLUCINATION TEST] Verapamil — Corpus'ta BULUNMUYOR",
        "soru": "XANAX kullanan hastaya supraventriküler taşiaritmi için Verapamil 80 mg eklenebilir mi, etkileşim riski var mı?",
        "profil": PatientProfile(
            yas=58,
            cinsiyet="erkek",
            mevcut_ilaclar=["XANAX 0.5 mg"],
            endikasyonlar=["anksiyete", "supraventriküler taşikardi"],
        ),
        "hedef_ilaclar": ["Verapamil"],
        "beklenen": "[BİLGİ YOK] Verapamil KÜB corpus'unda bulunmuyor; sistem bunu belirtmeli.",
        "hallucination": True,
    },

    # -----------------------------------------------------------------------
    # S14 — HALLUCINATION TEST: Mirtazapin — Corpus'ta YOK
    # -----------------------------------------------------------------------
    {
        "id": 14,
        "tur": "hallucination_test",
        "baslik": "[HALLUCINATION TEST] Mirtazapin — Corpus'ta BULUNMUYOR",
        "soru": "LUSTRAL kullanan depresyon hastasında uyku bozukluğu için Mirtazapin 15 mg eklenebilir mi?",
        "profil": PatientProfile(
            yas=44,
            cinsiyet="kadın",
            mevcut_ilaclar=["LUSTRAL 50 mg"],
            endikasyonlar=["depresyon", "insomnia"],
        ),
        "hedef_ilaclar": ["Mirtazapin"],
        "beklenen": "[BİLGİ YOK] Mirtazapin KÜB corpus'unda bulunmuyor; sistem bunu belirtmeli.",
        "hallucination": True,
    },

    # -----------------------------------------------------------------------
    # S15 — HALLUCINATION TEST: Lisinopril 10 mg — Corpus'ta YOK
    # -----------------------------------------------------------------------
    {
        "id": 15,
        "tur": "hallucination_test",
        "baslik": "[HALLUCINATION TEST] Lisinopril 10 mg — Corpus'ta BULUNMUYOR",
        "soru": "Hipertansiyon ve proteinüri olan diabetik hastaya Lisinopril 10 mg başlanabilir mi, böbrek üzerine etkisi nedir?",
        "profil": PatientProfile(
            yas=58,
            cinsiyet="erkek",
            gfr=55.0,
            endikasyonlar=["hipertansiyon", "diyabetik nefropati"],
            lab_degerleri={"kreatinin": 1.5},
        ),
        "hedef_ilaclar": ["Lisinopril"],
        "beklenen": "[BİLGİ YOK] Lisinopril KÜB corpus'unda yok; sistem bunu belirtmeli (RENITEC=enalapril var ama Lisinopril farklı).",
        "hallucination": True,
    },

    # -----------------------------------------------------------------------
    # S16 — JARDIANCE Madde 4.8 (Yan Etkiler)
    # -----------------------------------------------------------------------
    {
        "id": 16,
        "tur": "yan_etki",
        "baslik": "JARDIANCE — Madde 4.8 Yan Etki Analizi",
        "soru": "Tip-2 diyabetli hastada JARDIANCE kullanımına bağlı gelişebilecek istenmeyen etkiler (madde 4.8) nelerdir?",
        "profil": PatientProfile(
            yas=55,
            cinsiyet="kadın",
            endikasyonlar=["tip-2 diyabet"],
        ),
        "hedef_ilaclar": ["JARDIANCE"],
        "beklenen": "Vajinal moniliyazis, üriner sistem enfeksiyonu ve poliüri gibi 4.8 maddesinde yer alan yaygın yan etkiler listelenmeli.",
    },

    # -----------------------------------------------------------------------
    # S17 — CANDİDİN (Flukonazol) + PLAVIX — CYP2C19
    # -----------------------------------------------------------------------
    {
        "id": 17,
        "tur": "etkilesim_cyp",
        "baslik": "CANDİDİN (Flukonazol) + PLAVIX — CYP2C19",
        "soru": "PLAVIX kullanan hastada mantar enfeksiyonu için CANDİDİN başlanırsa ne tür bir etkileşim beklenir?",
        "profil": PatientProfile(
            yas=60,
            cinsiyet="erkek",
            mevcut_ilaclar=["PLAVIX 75 mg"],
            endikasyonlar=["koroner stent", "oral kandidiyazis"],
        ),
        "hedef_ilaclar": ["CANDİDİN", "PLAVIX"],
        "beklenen": "Flukonazol (CANDİDİN) orta-güçlü CYP2C19 inhibitörüdür. Klopidogrelin (PLAVIX) aktif metabolite dönüşümünü engeller → antiplatelet etki azalır.",
    },

    # -----------------------------------------------------------------------
    # S18 — LUSTRAL — Emzirme (Madde 4.6)
    # -----------------------------------------------------------------------
    {
        "id": 18,
        "tur": "emzirme",
        "baslik": "LUSTRAL — Emzirme Güvenliği (Madde 4.6)",
        "soru": "Emziren bir anne LUSTRAL 50 mg kullanabilir mi? Süte geçişi konusunda KÜB ne diyor?",
        "profil": PatientProfile(
            yas=30,
            cinsiyet="kadın",
            emzirme=True,
            endikasyonlar=["postpartum depresyon"],
        ),
        "hedef_ilaclar": ["LUSTRAL"],
        "beklenen": "KÜB madde 4.6 uyarınca: Sertralin anne sütüne geçer. Yarar/zarar dengesi gözetilmeli, bebek yakından izlenmelidir.",
    },
]


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def _is_hallucination_yanit(yanit: str) -> bool:
    """Yanıt 'bilgi yok' ifadesi içeriyor mu kontrol eder."""
    bilgi_yok_ifadeleri = [
        "bilgi yok", "kub belgelerinde yer almamaktadir",
        "corpus", "bulunamadi", "mevcut degil", "yer almıyor",
        "sistemde yok", "bilgiye sahip degil", "veri bulunmuyor",
    ]
    # Türkçe büyük harf normalize et: İ→i, Ğ→g vb. (Python .lower() İ'yi
    # "i̇" (combining dot) üretir, ASCII "i" ile eşleşmez)
    yanit_norm = (yanit
                  .replace("İ", "i").replace("Ğ", "g").replace("Ş", "s")
                  .replace("Ü", "u").replace("Ö", "o").replace("Ç", "c")
                  .lower())
    return any(ifade in yanit_norm for ifade in bilgi_yok_ifadeleri)


def calistir_senaryo(s: dict) -> dict:
    """Tek bir senaryo için RAG çalıştırır, sonuç döner."""
    logger.info(f"[S{s['id']:02d}] {s['baslik']}")
    try:
        response = run_rag(
            soru=s["soru"],
            profil=s["profil"],
            hedef_ilaclar=s.get("hedef_ilaclar"),
        )
        yanit = response.yanit

        sonuc = {
            "id": s["id"],
            "tur": s["tur"],
            "baslik": s["baslik"],
            "soru": s["soru"],
            "yanit": yanit,
            "yanit_len": len(yanit),
            "n_kaynak": len(response.kaynaklar),
            "n_cyp": len(response.cyp_etkilesimler),
            "beklenen": s.get("beklenen", ""),
            "hallucination": s.get("hallucination", False),
            "hata": None,
        }

        if s.get("hallucination"):
            dogru = _is_hallucination_yanit(yanit)
            sonuc["hallucination_dogru"] = dogru
            durum = "✓ BİLGİ YOK dedi" if dogru else "✗ UYDURDU"
            logger.warning(f"  [H-TEST] {durum}: {yanit[:100]}...")
        else:
            logger.info(f"  → {len(response.kaynaklar)} kaynak, {len(yanit)} karakter")

        return sonuc

    except Exception as e:
        logger.error(f"  HATA: {e}")
        return {
            "id": s["id"],
            "tur": s["tur"],
            "baslik": s["baslik"],
            "soru": s["soru"],
            "yanit": None,
            "hata": str(e),
            "hallucination": s.get("hallucination", False),
        }


def yazdir_ozet(sonuclar: list[dict]) -> None:
    """Klinik test özetini yazdırır."""
    print(SEPARATOR)
    print("KLİNİK DOĞRULAMA RAPORU — PharmAssist Dalga 4 Phase 6")
    print("=" * 70)

    db_sonuclar = [s for s in sonuclar if not s.get("hallucination")]
    h_sonuclar  = [s for s in sonuclar if s.get("hallucination")]

    print(f"\nDB Sorguları ({len(db_sonuclar)} soru):")
    hatali = [s for s in db_sonuclar if s.get("hata")]
    basarili = [s for s in db_sonuclar if not s.get("hata")]
    print(f"  ✓ Tamamlandı : {len(basarili)}")
    print(f"  ✗ Hata       : {len(hatali)}")

    if hatali:
        for s in hatali:
            print(f"    S{s['id']:02d}: {s['hata']}")

    print(f"\nHallucination Testi ({len(h_sonuclar)} soru) — S13, S14, S15:")
    for s in h_sonuclar:
        if s.get("hata"):
            print(f"  S{s['id']:02d}: HATA — {s['hata']}")
        elif s.get("hallucination_dogru"):
            print(f"  S{s['id']:02d}: ✓ Doğru — 'bilgi yok' dedi")
        else:
            print(f"  S{s['id']:02d}: ✗ UYDURDU — Yanıt: {s.get('yanit','')[:80]}...")

    print("\nDetaylı Yanıtlar:")
    for s in sonuclar:
        if s.get("hata"):
            continue
        h_flag = " [HALLUCINATION TEST]" if s.get("hallucination") else ""
        print(f"\n{'─'*70}")
        print(f"S{s['id']:02d} — {s['baslik']}{h_flag}")
        print(f"Soru    : {s['soru']}")
        print(f"Beklenen: {s.get('beklenen','')}")
        print(f"Yanıt   : {s.get('yanit','')[:300]}...")
        print(f"Kaynaklar: {s.get('n_kaynak',0)}, CYP: {s.get('n_cyp',0)}")

    print(SEPARATOR)


# ---------------------------------------------------------------------------
# Ana giriş noktası
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PharmAssist Klinik Validasyon")
    parser.add_argument("--soru", type=int, default=None,
                        help="Tek senaryo çalıştır (örn. --soru 3)")
    parser.add_argument("--sadece-db", action="store_true",
                        help="Hallucination test sorularını (S13-S15) atla")
    parser.add_argument("--output", default=None,
                        help="Sonuçları JSON dosyasına kaydet")
    args = parser.parse_args()

    # Çalıştırılacak senaryoları belirle
    if args.soru:
        hedef = [s for s in SENARYOLAR if s["id"] == args.soru]
        if not hedef:
            print(f"Senaryo S{args.soru:02d} bulunamadı.")
            sys.exit(1)
    elif args.sadece_db:
        hedef = [s for s in SENARYOLAR if not s.get("hallucination")]
    else:
        hedef = SENARYOLAR

    print(f"\nPharmAssist — Klinik Validasyon ({len(hedef)} senaryo)")
    print("=" * 70)
    print("Hallucination test soruları: S13 (ZITHROMAX), S14 (Metformin), S15 (Lisinopril)")
    print("Bu sorular corpus'ta yok — sistem 'bilgi yok' demeli, uydurmamalı.\n")

    sonuclar = []
    for s in hedef:
        sonuc = calistir_senaryo(s)
        sonuclar.append(sonuc)
        time.sleep(1)  # API rate limit

    yazdir_ozet(sonuclar)

    # Kaydet
    if args.output:
        os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(sonuclar, f, ensure_ascii=False, indent=2)
        logger.info(f"Sonuçlar kaydedildi: {args.output}")
