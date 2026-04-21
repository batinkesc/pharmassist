"""
CYP450 Ontoloji Mapping Modülü — Senaryo 3

KÜB Madde 4.5 metnindeki "CYP3A4 inhibitörü", "CYP2C9 substratı" gibi
sınıf ifadelerini tespit ederek hastanın mevcut ilaçlarıyla eşleştirir.

Mantık:
  1. Sorgu edilen ilacın KÜB 4.5 metninden CYP ifadelerini parse et
  2. Hastanın mevcut ilaçlarının CYP profillerini mapping tablosundan al
  3. Çakışan CYP rolleri → etkileşim uyarısı üret

Roller:
  - inhibitör: Bu enzimi baskılar → diğer ilaçların metabolizmasını yavaşlatır
  - indükleyici: Bu enzimi uyarır → diğer ilaçların metabolizmasını hızlandırır
  - substrat: Bu enzim tarafından metabolize edilir

Çakışma mantığı:
  İlaç A CYP3A4 substratı + İlaç B CYP3A4 inhibitörü
  → İlaç A'nın kan düzeyi artar → toksisite riski
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from src.analysis.cyp450_extractor import extract_cyp_profile_from_text


# ---------------------------------------------------------------------------
# CYP enzim tespiti için regex
# ---------------------------------------------------------------------------

CYP_PATTERN = re.compile(
    r"CYP\s*(\d[A-Z]\d+)\s*"
    r"(inhibitör[ü]?|indükleyici|substrat|inhibitor|inducer|substrate)",
    re.IGNORECASE,
)

CYP_SINIF_PATTERN = re.compile(
    r"(güçlü|orta|zayıf|strong|moderate|weak)?\s*"
    r"CYP\s*(\d[A-Z]\d+)\s*"
    r"(inhibitör[ü]?|indükleyici|substrat|inhibitor|inducer|substrate)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# ⚠️  DONDURULDU — 2026-04-15
# Bu listeye manuel ekleme yapma.
# Yeni ilaçlar AŞAMA 2'de otomatik extraction ile eklenecek.
# Son manuel güncelleme: CANDÍDIN, CANDIMAX eklendi (Dalga 6)
# ---------------------------------------------------------------------------
# Statik ilaç → CYP profil mapping tablosu
# (Sık CYP etkileşimi olan ilaçlar — KÜB 4.5 metinden çıkarılamayan vakaları kapsar)
# ---------------------------------------------------------------------------

ILAC_CYP_PROFILI: dict[str, dict[str, list[str]]] = {
    # ONAXAN (Rivaroksaban)
    "ONAXAN": {
        "substrat":    ["CYP3A4", "CYP2J2"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "ONAXAN® 20 MG FILM KAPLI TABLET": {
        "substrat":    ["CYP3A4", "CYP2J2"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # PLASORİN (Varfarin)
    "PLASORIN": {
        "substrat":    ["CYP2C9", "CYP3A4", "CYP1A2"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "PLASORIN 10 MG TABLET": {
        "substrat":    ["CYP2C9", "CYP3A4", "CYP1A2"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # AUGMENTİN (Amoksisilin/Klavulanik Asit) — CYP etkileşimi minimal
    "AUGMENTIN": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    # A-FERİN (Parasetamol + Psödoefedrin)
    "A-FERIN": {
        "substrat":    ["CYP2E1", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "A-FERİN® 1 MG+160 MG/5 ML PEDİYATRİK ŞURUP": {
        "substrat":    ["CYP2E1", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # Yaygın kullanılan ilaçlar (hasta profili mevcut ilaçlar için)
    "Warfarin": {
        "substrat":    ["CYP2C9", "CYP3A4", "CYP1A2"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "Aspirin": {
        "substrat":    [],
        "inhibitor":   ["CYP2C19"],
        "induktor":    [],
    },
    "Metformin": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    "Atorvastatin": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "Amlodipin": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "Ramipril": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    "Omeprazol": {
        "substrat":    ["CYP2C19", "CYP3A4"],
        "inhibitor":   ["CYP2C19"],
        "induktor":    [],
    },
    "Flukonazol": {
        "substrat":    ["CYP2C9", "CYP3A4"],
        "inhibitor":   ["CYP2C9", "CYP3A4", "CYP2C19"],
        "induktor":    [],
    },
    # CANDİDİN / CANDİMAX (Flukonazol ticari adları)
    "CANDİDİN": {
        "substrat":    ["CYP2C9", "CYP3A4"],
        "inhibitor":   ["CYP2C9", "CYP3A4", "CYP2C19"],
        "induktor":    [],
    },
    "CANDİMAX": {
        "substrat":    ["CYP2C9", "CYP3A4"],
        "inhibitor":   ["CYP2C9", "CYP3A4", "CYP2C19"],
        "induktor":    [],
    },
    "Rifampisin": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    ["CYP3A4", "CYP2C9", "CYP2C19", "CYP1A2"],
    },
    "Karbamazepin": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    ["CYP3A4", "CYP2C9", "CYP1A2"],
    },
    "Fenitoin": {
        "substrat":    ["CYP2C9", "CYP2C19"],
        "inhibitor":   [],
        "induktor":    ["CYP3A4", "CYP2C9"],
    },
    "Klaritromisin": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   ["CYP3A4"],
        "induktor":    [],
    },
    "Eritromisin": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   ["CYP3A4"],
        "induktor":    [],
    },
    # RAGAS v2 corpus ilaçları — Faz sonrası ekleme (Problem #2 fix)
    # PLAVIX (Klopidogrel) — CYP2C19 üzerinden aktive olan prodrug; CYP3A4 de substrate
    "Klopidogrel": {
        "substrat":    ["CYP2C19", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "PLAVIX": {
        "substrat":    ["CYP2C19", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "PLAVIX® 75 mg film kaplı tablet": {
        "substrat":    ["CYP2C19", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # ELİQUİS (Apiksaban) — CYP3A4 ve P-gp substrate
    "Apiksaban": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "ELİQUİS": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # XANAX (Alprazolam) — CYP3A4 substrate
    "Alprazolam": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "XANAX": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # CONTRAMAL (Tramadol) — CYP2D6 ve CYP3A4 substrate
    "Tramadol": {
        "substrat":    ["CYP2D6", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "CONTRAMAL": {
        "substrat":    ["CYP2D6", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # LUSTRAL (Sertralin) — CYP2C19 substrate; zayıf CYP2D6 inhibitörü
    "Sertralin": {
        "substrat":    ["CYP2C19", "CYP3A4"],
        "inhibitor":   ["CYP2D6"],
        "induktor":    [],
    },
    "LUSTRAL": {
        "substrat":    ["CYP2C19", "CYP3A4"],
        "inhibitor":   ["CYP2D6"],
        "induktor":    [],
    },
    # Essitalopram — CYP2C19 substrate; zayıf CYP2D6 inhibitörü
    "Essitalopram": {
        "substrat":    ["CYP2C19", "CYP3A4"],
        "inhibitor":   ["CYP2D6"],
        "induktor":    [],
    },
    # Amiodaron — güçlü çok enzim inhibitörü
    "Amiodaron": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   ["CYP2C9", "CYP2D6", "CYP3A4"],
        "induktor":    [],
    },
    # FLAGYL (Metronidazol) — CYP2C9 ve CYP3A4 inhibitörü
    "Metronidazol": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   ["CYP2C9", "CYP3A4"],
        "induktor":    [],
    },
    "FLAGYL": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   ["CYP2C9", "CYP3A4"],
        "induktor":    [],
    },
    # COZAAR (Losartan) — CYP2C9 substrate (aktif metabolite dönüşüm)
    "Losartan": {
        "substrat":    ["CYP2C9", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "COZAAR": {
        "substrat":    ["CYP2C9", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # VOLTAREN (Diklofenak) — CYP2C9 substrate
    "Diklofenak": {
        "substrat":    ["CYP2C9"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "VOLTAREN": {
        "substrat":    ["CYP2C9"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # CİPRO (Siprofloksasin) — güçlü CYP1A2 inhibitörü
    "Siprofloksasin": {
        "substrat":    [],
        "inhibitor":   ["CYP1A2"],
        "induktor":    [],
    },
    "CİPRO": {
        "substrat":    [],
        "inhibitor":   ["CYP1A2"],
        "induktor":    [],
    },
    # Metoprolol — CYP2D6 substrate
    "Metoprolol": {
        "substrat":    ["CYP2D6"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # PANTPAS (Pantoprazol) — CYP2C19 substrate (Omeprazol gibi ama daha az CYP2C19 inhibisyonu)
    "Pantoprazol": {
        "substrat":    ["CYP2C19", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "PANTPAS": {
        "substrat":    ["CYP2C19", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # İbuprofen — CYP2C9 substrate
    "İbuprofen": {
        "substrat":    ["CYP2C9"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # ZOFRAN (Ondansetron) — CYP3A4, CYP1A2, CYP2D6 substrate
    "Ondansetron": {
        "substrat":    ["CYP3A4", "CYP1A2", "CYP2D6"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "ZOFRAN": {
        "substrat":    ["CYP3A4", "CYP1A2", "CYP2D6"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # COLCHICUM DISPERT (Kolşisin) — CYP3A4 substrate
    "Kolşisin": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "COLCHICUM": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # CONCOR (Bisoprolol) — CYP2D6 substrate (minor klinik etki)
    "Bisoprolol": {
        "substrat":    ["CYP2D6", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "CONCOR": {
        "substrat":    ["CYP2D6", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # CRESTOR (Rosuvastatin) — CYP2C9 substrate (minor); OATP1B1/B3 ağırlıklı
    "Rosuvastatin": {
        "substrat":    ["CYP2C9"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "CRESTOR": {
        "substrat":    ["CYP2C9"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # Klaritromisin — Klaritromisin 500 mg için tam ad eşleşmesi
    "Klaritromisin 500 mg": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   ["CYP3A4"],
        "induktor":    [],
    },
    # JANUVIA (Sitagliptin) — CYP3A4 minor substrate
    "Sitagliptin": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "JANUVIA": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # JARDIANCE (Empagliflozin) — minimal CYP etkileşimi
    "Empagliflozin": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    "JARDIANCE": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    # DİAMİCRON (Gliklazid) — CYP2C9 substrate
    "Gliklazid": {
        "substrat":    ["CYP2C9"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "DİAMİCRON": {
        "substrat":    ["CYP2C9"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # DELTACORTRİL (Prednizolon) — CYP3A4 substrate
    "Prednizolon": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "DELTACORTRİL": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # ALDACTONE (Spironolakton) — CYP3A4 substrate
    "Spironolakton": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "ALDACTONE": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # LANSOR (Lansoprazol) — CYP2C19, CYP3A4 substrate (Omeprazol gibi)
    "Lansoprazol": {
        "substrat":    ["CYP2C19", "CYP3A4"],
        "inhibitor":   ["CYP2C19"],
        "induktor":    [],
    },
    "LANSOR": {
        "substrat":    ["CYP2C19", "CYP3A4"],
        "inhibitor":   ["CYP2C19"],
        "induktor":    [],
    },
    # NAPROSYN (Naproksen) — CYP2C9 substrate
    "Naproksen": {
        "substrat":    ["CYP2C9"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "NAPROSYN": {
        "substrat":    ["CYP2C9"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # ÜRİKOLİZ (Allopürinol) — zayıf CYP inhibitör (CYP2C9, xanthine oxidase pathway)
    "Allopürinol": {
        "substrat":    [],
        "inhibitor":   ["CYP2C9"],
        "induktor":    [],
    },
    "ÜRİKOLİZ": {
        "substrat":    [],
        "inhibitor":   ["CYP2C9"],
        "induktor":    [],
    },
    # NEURONTİN (Gabapentin) — CYP ile metabolize edilmez
    "Gabapentin": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    "NEURONTİN": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    # KEPPRA (Levetirasetam) — CYP ile metabolize edilmez
    "Levetirasetam": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    "KEPPRA": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    # LİPİTOR (Atorvastatin) — CYP3A4 substrate (Atorvastatin zaten var, marka ekle)
    "LİPİTOR": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # ZİTOREL / Azitromisin — CYP3A4 minor substrate, zayıf CYP3A4 inhibitörü
    "Azitromisin": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   ["CYP3A4"],
        "induktor":    [],
    },
    "ZİTOREL": {
        "substrat":    ["CYP3A4"],
        "inhibitor":   ["CYP3A4"],
        "induktor":    [],
    },
    # METAFORMAL / Metformin — CYP ile metabolize edilmez
    "Metformin": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    "METAFORMAL": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    # BELOC ZOK (Metoprolol süksinat) — CYP2D6 substrate (Metoprolol zaten var)
    "BELOC ZOK": {
        "substrat":    ["CYP2D6"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # PLASORİN 5 mg — aynı profil
    "PLASORİN 5 MG TABLET": {
        "substrat":    ["CYP2C9", "CYP3A4", "CYP1A2"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # PLASORİN (Varfarin) tam ad eşleşmesi
    "PLASORİN": {
        "substrat":    ["CYP2C9", "CYP3A4", "CYP1A2"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # Aspirin 100 mg için tam ad eşleşmesi
    "Aspirin 100 mg": {
        "substrat":    [],
        "inhibitor":   ["CYP2C19"],
        "induktor":    [],
    },
    # Metformin — CYP450 ile metabolize edilmez
    "Metformin 1000 mg": {
        "substrat":    [],
        "inhibitor":   [],
        "induktor":    [],
    },
    # Warfarin tam ad eşleşmesi
    "Warfarin 5 mg": {
        "substrat":    ["CYP2C9", "CYP3A4", "CYP1A2"],
        "inhibitor":   [],
        "induktor":    [],
    },
    # Verapamil (ISOPTIN) — CYP3A4 substrat + inhibitör, CYP1A2 inhibitör
    "Verapamil": {
        "substrat":    ["CYP3A4", "CYP1A2"],
        "inhibitor":   ["CYP3A4", "CYP1A2"],
        "induktor":    [],
    },
    "ISOPTIN": {
        "substrat":    ["CYP3A4", "CYP1A2"],
        "inhibitor":   ["CYP3A4", "CYP1A2"],
        "induktor":    [],
    },
    # Risperidon (PERILIFE) — CYP2D6 ve CYP3A4 substrat
    "Risperidon": {
        "substrat":    ["CYP2D6", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
    "PERILIFE": {
        "substrat":    ["CYP2D6", "CYP3A4"],
        "inhibitor":   [],
        "induktor":    [],
    },
}


# ---------------------------------------------------------------------------
# Veri yapıları
# ---------------------------------------------------------------------------

@dataclass
class CYPEtkilesim:
    """Tek bir CYP bazlı etkileşim bulgusu."""
    enzim: str              # "CYP3A4"
    sorgu_ilac: str         # Sorgulanan ilaç (substrat)
    etkilesen_ilac: str     # Hastanın mevcut ilacı (inhibitör/indükleyici)
    rol: str                # "inhibitor" | "induktor"
    sonuc: str              # Klinik sonuç açıklaması
    siddet: str             # "kritik" | "dikkat"


@dataclass
class CYP450Sonucu:
    """Tüm CYP analizi çıktısı."""
    etkilesimler: list[CYPEtkilesim] = field(default_factory=list)
    kub_cyp_ifadeleri: list[str] = field(default_factory=list)  # KÜB'den tespit edilenler
    ozet_metin: str = ""
    source: str = "static_table"  # "static_table" | "llm_extraction" | "unavailable"

    @property
    def etkilesim_yok(self) -> bool:
        return len(self.etkilesimler) == 0


# ---------------------------------------------------------------------------
# Yardımcı: İlaç adından CYP profilini bul
# ---------------------------------------------------------------------------

def _ilac_cyp_profili_bul(ilac_adi: str) -> dict[str, list[str]]:
    """
    İlaç adını ILAC_CYP_PROFILI tablosunda arar.
    Tam eşleşme yoksa kısmi eşleşme dener.
    """
    # None safety
    if not ilac_adi:
        return {"substrat": [], "inhibitor": [], "induktor": []}

    # Tam eşleşme
    if ilac_adi in ILAC_CYP_PROFILI:
        return ILAC_CYP_PROFILI[ilac_adi]

    # Büyük harf normalize
    ilac_upper = ilac_adi.upper()
    for key, val in ILAC_CYP_PROFILI.items():
        if key.upper() in ilac_upper or ilac_upper in key.upper():
            return val

    # İlk kelime ile eşleşme (örn: "Warfarin 5 mg" → "Warfarin")
    ilk_kelime = ilac_adi.split()[0] if ilac_adi.split() else ilac_adi
    for key, val in ILAC_CYP_PROFILI.items():
        if key.lower().startswith(ilk_kelime.lower()):
            return val

    return {"substrat": [], "inhibitor": [], "induktor": []}


# ---------------------------------------------------------------------------
# KÜB metninden CYP ifadelerini çıkar
# ---------------------------------------------------------------------------

def _kub_cyp_parse(icerik: str) -> list[str]:
    """Madde 4.5 metninden CYP ifadelerini tespit eder."""
    bulunanlar = []
    for m in CYP_SINIF_PATTERN.finditer(icerik):
        guc = m.group(1) or ""
        enzim = m.group(2)
        rol = m.group(3)
        ifade = f"CYP{enzim} {rol.lower()}"
        if guc:
            ifade = f"{guc.lower()} {ifade}"
        if ifade not in bulunanlar:
            bulunanlar.append(ifade)
    return bulunanlar


# ---------------------------------------------------------------------------
# Ana analiz fonksiyonu
# ---------------------------------------------------------------------------

def analiz_et(
    chunklar: list,
    hasta_ilaclar: list[str],
    sorgu_ilaclar: list[str] | None = None,
) -> CYP450Sonucu:
    """
    CYP450 bazlı ilaç etkileşim analizi yapar.

    Args:
        chunklar:      RAG engine'den gelen RetrievedChunk listesi
        hasta_ilaclar: Hastanın mevcut ilaçları
        sorgu_ilaclar: Sorgulanan ilaçlar (None ise chunk'lardan çıkar)

    Returns:
        CYP450Sonucu
    """
    # 1. Metin içeriğini ilaç bazlı grupla (Extraction için)
    ilac_45_metinleri: dict[str, str] = {}
    for chunk in chunklar:
        d_adi = getattr(chunk, "ilac_adi", "")
        m_no = getattr(chunk, "madde_no", "")
        icerik = getattr(chunk, "icerik", "")
        if d_adi and m_no == "4.5" and icerik:
            ilac_45_metinleri[d_adi] = ilac_45_metinleri.get(d_adi, "") + "\n" + icerik

    # 2. Sorgu ilaçlarını belirle
    if not sorgu_ilaclar:
        sorgu_ilaclar = list({
            getattr(c, "ilac_adi", "") for c in chunklar
            if getattr(c, "ilac_adi", "")
        })

    # 3. KÜB 4.5 chunk'larından CYP ifadelerini topla (Regex bazlı - hızlı gösterim için)
    kub_cyp_ifadeleri: list[str] = []
    for icerik in ilac_45_metinleri.values():
        ifadeler = _kub_cyp_parse(icerik)
        kub_cyp_ifadeleri.extend(ifadeler)

    # 4. Etkileşim analizi
    etkilesimler: list[CYPEtkilesim] = []

    # Kaynak takibi
    llm_used = False
    static_used = False

    # Profil bulma yardımcısı (Static + LLM Fallback)
    def _get_profil(ilac: str) -> dict:
        nonlocal llm_used, static_used
        # Önce statik liste (frozen)
        p = _ilac_cyp_profili_bul(ilac)
        if p.get("substrat") or p.get("inhibitor") or p.get("induktor"):
            static_used = True
            return p

        # Statik listede yoksa LLM ile extract et
        metin = ilac_45_metinleri.get(ilac, "")
        if metin:
            from loguru import logger
            logger.info(f"CYP450: {ilac} için otomatik extraction yapılıyor...")
            extracted = extract_cyp_profile_from_text(metin, ilac)
            if extracted.get("substrat") or extracted.get("inhibitor") or extracted.get("induktor"):
                llm_used = True
            return extracted

        return p  # Boş döner

    for sorgu_ilac in sorgu_ilaclar:
        sorgu_profil = _get_profil(sorgu_ilac)
        sorgu_substratlar = set(sorgu_profil.get("substrat", []))

        for hasta_ilac in hasta_ilaclar:
            # Kendisiyle etkileşimi atla
            if sorgu_ilac == hasta_ilac:
                continue
                
            hasta_profil = _get_profil(hasta_ilac)

            # Senaryo 1: Hasta ilacı inhibitör, sorgu ilacı aynı enzimin substratı
            for enzim in hasta_profil.get("inhibitor", []):
                if enzim in sorgu_substratlar:
                    etkilesimler.append(CYPEtkilesim(
                        enzim=enzim,
                        sorgu_ilac=sorgu_ilac,
                        etkilesen_ilac=hasta_ilac,
                        rol="inhibitor",
                        sonuc=(
                            f"{hasta_ilac} {enzim} inhibitörüdür — "
                            f"{sorgu_ilac} kan düzeyi artabilir, toksisite riski"
                        ),
                        siddet="kritik",
                    ))

            # Senaryo 2: Hasta ilacı indükleyici, sorgu ilacı aynı enzimin substratı
            for enzim in hasta_profil.get("induktor", []):
                if enzim in sorgu_substratlar:
                    etkilesimler.append(CYPEtkilesim(
                        enzim=enzim,
                        sorgu_ilac=sorgu_ilac,
                        etkilesen_ilac=hasta_ilac,
                        rol="induktor",
                        sonuc=(
                            f"{hasta_ilac} {enzim} indükleyicisidir — "
                            f"{sorgu_ilac} etkinliği azalabilir"
                        ),
                        siddet="dikkat",
                    ))

            # Senaryo 3: İki ilaç aynı enzimin substratı → kompetitif inhibisyon
            hasta_substratlar = set(hasta_profil.get("substrat", []))
            paylasilan = sorgu_substratlar & hasta_substratlar
            for enzim in paylasilan:
                if sorgu_ilac != hasta_ilac:
                    etkilesimler.append(CYPEtkilesim(
                        enzim=enzim,
                        sorgu_ilac=sorgu_ilac,
                        etkilesen_ilac=hasta_ilac,
                        rol="kompetitif",
                        sonuc=(
                            f"Her ikisi de {enzim} substratı — "
                            f"rekabet sonucu kan düzeyleri değişebilir"
                        ),
                        siddet="dikkat",
                    ))

    # Tekrarları temizle
    tekil: list[CYPEtkilesim] = []
    seen: set[str] = set()
    for e in etkilesimler:
        key = f"{e.enzim}|{e.sorgu_ilac}|{e.etkilesen_ilac}|{e.rol}"
        if key not in seen:
            seen.add(key)
            tekil.append(e)

    # Şiddete göre sırala
    tekil.sort(key=lambda e: 0 if e.siddet == "kritik" else 1)

    if llm_used:
        source = "llm_extraction"
    elif static_used:
        source = "static_table"
    else:
        source = "unavailable"
        tekil = []

    ozet = _format_ozet(tekil, kub_cyp_ifadeleri)

    return CYP450Sonucu(
        etkilesimler=tekil,
        kub_cyp_ifadeleri=list(set(kub_cyp_ifadeleri)),
        ozet_metin=ozet,
        source=source,
    )


def _format_ozet(etkilesimler: list[CYPEtkilesim], kub_ifadeler: list[str]) -> str:
    """CYP bulgularını prompt için formatlı metne çevirir."""
    parcalar = []

    if kub_ifadeler:
        parcalar.append(
            "**CYP450 İfadeleri (KÜB Madde 4.5'ten):** " +
            ", ".join(kub_ifadeler[:6])
        )

    if etkilesimler:
        satirlar = ["**CYP450 Bazlı Etkileşim Analizi:**"]
        for e in etkilesimler:
            sembol = "🔴" if e.siddet == "kritik" else "🟡"
            satirlar.append(f"  {sembol} {e.sonuc} [{e.enzim}]")
        parcalar.append("\n".join(satirlar))

    return "\n\n".join(parcalar)
