#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Dogrulama Testi - fix/validate-pipeline branch
5 fix'in etkisini hedefli 6 sorgu ile dogrular.
Calistirma: .venv/Scripts/python.exe scripts/fix_validation_test.py
"""
import sys
import os
import re
import time
from pathlib import Path
from dataclasses import dataclass

# Windows console UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    os.environ["PYTHONIOENCODING"] = "utf-8"

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.patient_profile import PatientProfile
from src.agents.rag_engine import run_rag, RAGResponse

# ── ANSI renk ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RST    = "\033[0m"

def _pass(msg): print(f"  {GREEN}✓ {msg}{RST}")
def _fail(msg): print(f"  {RED}✗ {msg}{RST}")
def _warn(msg): print(f"  {YELLOW}⚠ {msg}{RST}")
def _info(msg): print(f"  {CYAN}  {msg}{RST}")


@dataclass
class TestCase:
    id: str
    fix_hedef: str
    aciklama: str
    soru: str
    profil: PatientProfile
    hedef_ilaclar: list[str]
    beklenen_icermemeli: list[str]   # yanıtta OLMAMALI
    beklenen_icermeli: list[str]     # yanıtta OLMALI (en az biri)
    kontrendikasyon_max: int | None = None  # graph'tan gelen kontra sayısı ≤ bu değer


# ── PROFIL YARDIMCI ────────────────────────────────────────────────────────
def profil(**kw) -> PatientProfile:
    defaults = dict(
        yas=0, cinsiyet="belirtilmemiş", gfr=None, karaciger_skoru=None,
        mevcut_ilaclar=[], alerjiler=[], endikasyonlar=[],
        gebelik=False, emzirme=False, notlar="",
        lab_degerleri={}, kilo=None,
    )
    defaults.update(kw)
    return PatientProfile(**defaults)


# ==============================================================================
# TEST SENARYOLARI
# ==============================================================================
TESTLER: list[TestCase] = [

    # ── TEST 1: Fix #1+4 — YANLIŞ POZİTİF önlenmiş mi? ───────────────────
    # CO-DİOVAN'ın "10 yaş altı çocuklar" kontrendikasyonu
    # 65 yaşlı yetişkin hastaya KONTREDİKE çıkmamalı.
    TestCase(
        id="T1",
        fix_hedef="Fix #1 + Fix #4",
        aciklama="CO-DİOVAN: 65 yaş yetişkin → pediyatrik kontra FALSE POSITIVE olmamalı",
        soru="65 yaşında erkek hasta, hipertansiyon ve tip 2 diyabet. CO-DİOVAN başlanabilir mi?",
        profil=profil(yas=65, cinsiyet="erkek", endikasyonlar=["hipertansiyon", "tip 2 diyabet"]),
        hedef_ilaclar=["CO-DİOVAN"],
        # kontrendike kelimesi yalnızca [AŞIRI YORUM:...] etiket içinde kabul edilir
        # Büyük harf verdict veya bağımsız cümle olmamalı
        beklenen_icermemeli=["KONTREDİKE\n", "KONTREDİKE ", "Bu hasta kontrendike", "mutlak kontrendike"],
        beklenen_icermeli=["AŞIRI YORUM",   # VALIDATE pipeline overstatement yakaladı
                           "dikkatli", "diyabet", "izlenmelidir"],
        kontrendikasyon_max=10,
    ),

    # ── TEST 2: Fix #1+4 — GERÇEK POZİTİF korunmuş mu? ──────────────────
    # Sildenafil + AMI = gerçek kontrendikasyon (Fix korunmuş mu kontrol)
    TestCase(
        id="T2",
        fix_hedef="Fix #1 + Fix #4 (true-positive korunuyor mu?)",
        aciklama="Sildenafil + AMI: gerçek KONTREDİKE korunmalı",
        soru="Akut miyokard enfarktüsü geçirmiş, 3 gün önce taburcu olan 60 yaşında erkek hasta. "
             "Erektil disfonksiyon için sildenafil sordu.",
        profil=profil(
            yas=60, cinsiyet="erkek",
            endikasyonlar=["akut miyokard enfarktüsü", "erektil disfonksiyon"],
        ),
        hedef_ilaclar=["VİAGRA", "SİLDENAFİL"],
        beklenen_icermemeli=[],
        beklenen_icermeli=["kontrendike", "KONTREDİKE", "kullanılmamalı", "önerilmez",
                           "kardiyak", "nitrat", "miyokard"],
        kontrendikasyon_max=None,
    ),

    # ── TEST 3: Fix #3 — Türkçe virgül ondalık DOĞRULANAMADI azaldı mı? ──
    # ARLEC 6,25 mg → KÜB'de virgüllü doz; yanıtta [DOĞRULANAMADI] azalmalı
    TestCase(
        id="T3",
        fix_hedef="Fix #3 (ondalık virgül/nokta)",
        aciklama="ARLEC 6,25 mg: [DOĞRULANAMADI] etiketi görünmemeli",
        soru="Astım olmayan, kalp yetmezliği tanılı 52 yaşında kadın hastada ARLEC 6,25 mg "
             "başlangıç dozu uygun mudur?",
        profil=profil(
            yas=52, cinsiyet="kadın",
            endikasyonlar=["kalp yetmezliği"],
        ),
        hedef_ilaclar=["ARLEC"],
        beklenen_icermemeli=["[DOĞRULANAMADI]"],
        beklenen_icermeli=["6,25", "başlangıç", "doz", "titrasy", "mg"],
        kontrendikasyon_max=None,
    ),

    # ── TEST 4: Fix #4 (graf filtresi) + Fix #1 — Astım + ARLEC ─────────
    # Gerçek kontrendikasyon → hasta astımlı → KONTREDİKE çıkmalı
    # Aynı zamanda çocuk kontrendikasyonları listede olmamalı
    TestCase(
        id="T4",
        fix_hedef="Fix #4 (graf filtresi) — doğru kontrendikasyon",
        aciklama="ARLEC + astım hastası: KONTREDİKE çıkmalı, pediyatrik filtre çalışmalı",
        soru="52 yaşında astım tanılı kadın hastada kalp yetmezliği için ARLEC başlanabilir mi?",
        profil=profil(
            yas=52, cinsiyet="kadın",
            endikasyonlar=["kalp yetmezliği", "astım"],
        ),
        hedef_ilaclar=["ARLEC"],
        beklenen_icermemeli=[],
        beklenen_icermeli=["kontrendike", "KONTREDİKE", "bronkospazm", "astım",
                           "kullanılmamalı", "önerilmez"],
        kontrendikasyon_max=10,
    ),

    # ── TEST 5: Fix #5 — Çoklu anormal lab → query'e TEK terim ───────────
    # Böbrek + karaciğer + INR hepsi anormal; soru etkileşim türünde
    # Fix #5: yalnızca doz/kontrendikasyon sorularında lab terimi eklenmeli
    # Bu etkileşim sorusunda lab terimleri query'ye EKLENMEMELİ
    TestCase(
        id="T5",
        fix_hedef="Fix #5 (lab query izolasyonu)",
        aciklama="Çoklu anormal lab değerleri + etkileşim sorusu → query'de gürültü olmamalı",
        soru="Warfarin kullanan hastaya PLAVIX eklenebilir mi? Etkileşimi nedir?",
        profil=profil(
            yas=68, cinsiyet="erkek",
            mevcut_ilaclar=["warfarin"],
            endikasyonlar=["atriyal fibrilasyon"],
            lab_degerleri={
                "Kreatinin": 1.9,   # mg/dL — yüksek (float olmalı)
                "ALT": 110.0,       # U/L — yüksek
                "INR": 2.8,         # yüksek
                "HbA1c": 8.5,       # % — yüksek
            },
        ),
        hedef_ilaclar=["PLAVIX"],
        beklenen_icermemeli=[],
        beklenen_icermeli=["kanama", "etkileşim", "warfarin", "antikoagülan",
                           "dikkat", "risk", "birlikte"],
        kontrendikasyon_max=None,
    ),

    # ── TEST 6: Fix #2 (CC) + CYP yön doğruluğu ─────────────────────────
    # SPORANOX (itrakonazol) → CYP3A4 inhibitörü
    # CORDARONE (amiodaron) → CYP3A4 substratı
    # Beklenen: amiodaron düzeyi ARTAR
    TestCase(
        id="T6",
        fix_hedef="Fix #2 (context compression) + CYP yön doğruluğu",
        aciklama="SPORANOX+CORDARONE: itrakonazol CYP3A4 inhibitörü → amiodaron düzeyi ARTMALI",
        soru="SPORANOX kullanan hastada CORDARONE kan düzeyi nasıl etkilenir?",
        profil=profil(
            yas=64, cinsiyet="kadın",
            mevcut_ilaclar=["CORDARONE 200 mg"],
            endikasyonlar=["atriyal fibrilasyon", "fungal enfeksiyon"],
        ),
        hedef_ilaclar=["SPORANOX", "CORDARONE"],
        beklenen_icermemeli=["düzeyi azalır", "konsantrasyonu düşer", "etkinliği azal"],
        beklenen_icermeli=["artar", "yükselir", "artış", "inhib", "CYP3A4",
                           "toksisite", "QT"],
        kontrendikasyon_max=None,
    ),
]


# ==============================================================================
# ÇALIŞTIRICI
# ==============================================================================

def calistir_test(tc: TestCase, idx: int, toplam: int) -> dict:
    print(f"\n{'='*70}")
    print(f"{BOLD}[{idx}/{toplam}] {tc.id} — {tc.fix_hedef}{RST}")
    print(f"  Senaryo  : {tc.aciklama}")
    print(f"  Soru     : {tc.soru[:90]}{'...' if len(tc.soru)>90 else ''}")
    print(f"  Hedef    : {tc.hedef_ilaclar}")

    t0 = time.time()
    try:
        sonuc: RAGResponse = run_rag(
            soru=tc.soru,
            profil=tc.profil,
            hedef_ilaclar=tc.hedef_ilaclar,
        )
        sure = time.time() - t0
        yanit: str = sonuc.yanit
        verdict: str = ""  # run_rag'dan verdict alanı yok, yanıtta aranır
        graph_ctx: str = sonuc.graf_baglami

        # Graf kontrendikasyon sayısını log'dan değil yanıt uzunluğundan tahmin et
        # (graph_ctx'e erişemiyorsak basit proxy)
        # Yanıttaki verdict kelimesini tespit et
        v_match = re.search(r'\b(KONTREDİKE|DİKKATLİ_KULLANIM|GÜVENLE_KULLANILABİLİR)\b', yanit)
        verdict = v_match.group(0) if v_match else "—"
        print(f"\n  {BOLD}Yanıt ({sure:.1f}s | verdict={verdict}):{RST}")
        # İlk 500 karakter
        preview = yanit[:500].replace('\n', ' ')
        print(f"  {preview}{'...' if len(yanit)>500 else ''}")

        # VALIDATE etiketleri
        validate_tags = re.findall(
            r'\[(DOĞRULANAMADI[^\]]*|AŞIRI YORUM[^\]]*|ONAYLANDI[^\]]*)\]', yanit
        )
        if validate_tags:
            print(f"\n  VALIDATE etiketleri: {validate_tags}")

        # ── KONTROLLER ──────────────────────────────────────────────────
        gecti = 0
        toplam_kontrol = len(tc.beklenen_icermemeli) + (1 if tc.beklenen_icermeli else 0)

        # Olmamaması gerekenler
        for ifade in tc.beklenen_icermemeli:
            if ifade.lower() in yanit.lower():
                _fail(f"'{ifade}' yanıtta VAR — olmamalıydı")
            else:
                _pass(f"'{ifade}' yanıtta yok ✓")
                gecti += 1

        # Olması gerekenler (en az biri)
        if tc.beklenen_icermeli:
            bulunan = [t for t in tc.beklenen_icermeli if t.lower() in yanit.lower()]
            if bulunan:
                _pass(f"Beklenen ifadeler bulundu: {bulunan[:3]}")
                gecti += 1
            else:
                _fail(f"Beklenen ifadelerden hiçbiri yok: {tc.beklenen_icermeli}")

        # Kontrendikasyon max kontrolü (graph_ctx içindeyse)
        if tc.kontrendikasyon_max is not None and graph_ctx:
            # "- X → Y ile birlikte kontrendike" satırlarını say
            kontra_sayisi = len(re.findall(r'kontrendike', graph_ctx, re.IGNORECASE))
            if kontra_sayisi <= tc.kontrendikasyon_max:
                _pass(f"Graf kontrendikasyon ≤ {tc.kontrendikasyon_max} (bulunan: ~{kontra_sayisi})")
                gecti += 1; toplam_kontrol += 1
            else:
                _warn(f"Graf kontrendikasyon ~{kontra_sayisi} > {tc.kontrendikasyon_max}")
                toplam_kontrol += 1

        durum = "GEÇTİ" if gecti == toplam_kontrol else ("KISMEN" if gecti > 0 else "BAŞARISIZ")
        renk = GREEN if durum == "GEÇTİ" else (YELLOW if durum == "KISMEN" else RED)
        print(f"\n  {renk}{BOLD}→ {durum} ({gecti}/{toplam_kontrol}){RST}")

        return {"id": tc.id, "durum": durum, "gecti": gecti, "toplam": toplam_kontrol,
                "sure": sure, "hata": None}

    except Exception as e:
        sure = time.time() - t0
        import traceback
        _fail(f"HATA: {e}")
        traceback.print_exc()
        return {"id": tc.id, "durum": "HATA", "gecti": 0, "toplam": 0,
                "sure": sure, "hata": str(e)}


def main():
    print(f"\n{BOLD}{'='*70}{RST}")
    print(f"{BOLD}  PharmAssist — Fix Doğrulama Testi (fix/validate-pipeline){RST}")
    print(f"{BOLD}{'='*70}{RST}")
    print(f"  Toplam: {len(TESTLER)} senaryo\n")

    sonuclar = []
    for i, tc in enumerate(TESTLER, 1):
        s = calistir_test(tc, i, len(TESTLER))
        sonuclar.append(s)

    # ── ÖZET ────────────────────────────────────────────────────────────────
    print(f"\n\n{'='*70}")
    print(f"{BOLD}  ÖZET{RST}")
    print(f"{'='*70}")
    gecenler = sum(1 for s in sonuclar if s["durum"] == "GEÇTİ")
    kismen   = sum(1 for s in sonuclar if s["durum"] == "KISMEN")
    hatalar  = sum(1 for s in sonuclar if s["durum"] in ("BAŞARISIZ", "HATA"))

    for s in sonuclar:
        renk = GREEN if s["durum"] == "GEÇTİ" else (YELLOW if s["durum"] == "KISMEN" else RED)
        hata_str = f" [{s['hata'][:40]}]" if s["hata"] else ""
        print(f"  {renk}{s['id']}: {s['durum']} ({s['gecti']}/{s['toplam']}) "
              f"— {s['sure']:.1f}s{hata_str}{RST}")

    print(f"\n  {GREEN}Geçti : {gecenler}{RST}  "
          f"{YELLOW}Kısmen: {kismen}{RST}  "
          f"{RED}Hata  : {hatalar}{RST}")

    toplam_sure = sum(s["sure"] for s in sonuclar)
    print(f"  Toplam süre: {toplam_sure:.1f}s")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
