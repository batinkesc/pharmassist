"""
ProfileExtractor — serbest metinden hasta profili çıkarır (kural tabanlı, LLM gerektirmez).

Yaklaşım:
  1. Regex ile demografik bilgi + lab değerleri çıkar
  2. ChromaDB ilaç listesi ile kelime eşleştirme → mevcut ilaçlar + hedef ilaç
  3. Soru ifadesini tespit et → hedef ilacı belirle

Örnek:
  "68 yaşında erkek, böbrek yetmezliği (eGFR 35), warfarin kullanıyor.
   Klaritromisin yazabilir miyim?"
  →  yas=68, cinsiyet=erkek, gfr=35, bobrek_yetmezligi=True
     mevcut_ilaclar=["warfarin"], hedef_ilaclar=["klaritromisin"]
"""

import re
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Regex kalıpları
# ---------------------------------------------------------------------------

_YAS = re.compile(r'(\d{1,3})\s*yaş', re.IGNORECASE)
_GFR = re.compile(r'e?g[fF][rR]\s*[=:;]?\s*(\d{1,3}(?:\.\d+)?)', re.IGNORECASE)

# Özel durum
_BOBREK    = re.compile(
    r'böbrek\s+yetmezli[gğ]i|renal\s+yetmezlik|kronik\s+böbrek|'
    r'\bKBH\b|\bCKD\b|hemodiyaliz|periton\s+diyalizi|\bdiyaliz\b|'
    r'böbrek\s+nakli|renal\s+transplant',
    re.IGNORECASE,
)
_KARACIGER = re.compile(
    r'karaci[gğ]er\s+yetmezli[gğ]i|hepatik\s+yetmezlik|'
    r'siroz|karaci[gğ]er\s+sirozlu|'
    r'hepatit\s*[ABC]|kronik\s+hepatit|'
    r'non.alkolik\s+ya[gğ]l[ıi]\s+karaci[gğ]er|NASH|'
    r'karaci[gğ]er\s+nakli|hepatik\s+ensefalopati',
    re.IGNORECASE,
)
_CHILD     = re.compile(r'child[-\s]pugh\s+([abc])', re.IGNORECASE)
_GEBELIK   = re.compile(r'gebe[ck]|hamile|gebelik|\bG[123]\b', re.IGNORECASE)
_EMZIRME   = re.compile(r'emzir', re.IGNORECASE)
_PEDIYATRIK= re.compile(r'pediatrik|pediyatrik|çocuk\s+hasta|bebek|\bneonatal\b', re.IGNORECASE)
_GERIYATRIK= re.compile(r'geriyatrik|geriatrik|yaşlı\s+hasta', re.IGNORECASE)

# Lab değerleri: "ALT: 45" / "ALT=45" / "ALT 45 U/L"
_LAB_PATTERNS: dict[str, re.Pattern] = {
    "ALT":        re.compile(r'ALT\s*[=:;]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    "AST":        re.compile(r'AST\s*[=:;]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    "INR":        re.compile(r'INR\s*[=:;]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    "K":          re.compile(r'\bK\+?\s*[=:;]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    "Na":         re.compile(r'\bNa\+?\s*[=:;]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    "Kreatinin":  re.compile(r'kreatinin\s*[=:;]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    "HbA1c":      re.compile(r'HbA1c\s*[=:;]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    "Hemoglobin": re.compile(r'hemoglobin\s*[=:;]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    "Bilirubin":  re.compile(r'bilirubin\s*[=:;]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
    "Trombosit":  re.compile(r'trombosit\s*[=:;]?\s*(\d+(?:\.\d+)?)', re.IGNORECASE),
}

# Soru / niyet ifadeleri — önünde gelen kelime hedef ilaç olabilir
_SORU_IFADESI = re.compile(
    r'(?:yazabilir\s+m[ıi]|verilebilir\s+m[ıi]|kullan[ıi]labilir\s+m[ıi]|ba[sş]lanabilir\s+m[ıi]'
    r'|uygun\s+m[ıi]|kontrendike\s+m[ıi]|yazmal[ıi]\s+m[ıi]|verilmeli\s+m[ıi]'
    r'|reçete\s+edebilir\s+m[ıi]|nas[ıi]l\s+etkiler|ne\s+olur|etkile[sş]im\s+var\s+m[ıi]'
    r'|eklemek\s+istiyorum|ekleyebilir\s+m[ıi]'
    r'|ba[sş]lamay[ıi]\s+d[uü][sş][uü]n[uü]yorum|vermeyi\s+d[uü][sş][uü]n[uü]yorum'
    r'|yazmay[ıi]\s+d[uü][sş][uü]n[uü]yorum|yazmak\s+istiyorum|vermek\s+istiyorum'
    r'|ba[sş]lamak\s+istiyorum|önerir\s+misiniz|önerebilir\s+m[ıi]'
    r'|sordu|soruldu|istedi|talep\s+etti|ba[sş]vurdu)',
    re.IGNORECASE,
)

# Cümle yapısından hedef ilaç: "[ilaç] yazabilir miyim / eklemek istiyorum?" → ilaç
_HEDEF_ILAC = re.compile(
    r'\b([\wçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\-]{2,}(?:\s+[\wçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\-]{2,})?)'
    r'\s+(?:yazabilir|verilebilir|kullan[ıi]labilir|ba[sş]lanabilir|verilmeli|'
    r'kontrendike|uygun\s+mu|yaz[ıi]labilir|'
    r'eklemek\s+istiyorum|ekleyebilir|'
    r'ba[sş]lamay[ıi]\s+d[uü][sş][uü]n[uü]yorum|'
    r'vermeyi\s+d[uü][sş][uü]n[uü]yorum|yazmay[ıi]\s+d[uü][sş][uü]n[uü]yorum|'
    r'yazmak\s+istiyorum|vermek\s+istiyorum|ba[sş]lamak\s+istiyorum|'
    r'sordu|soruldu|istedi|talep\s+etti|ba[sş]vurdu)',
    re.IGNORECASE,
)

# "X için Y [eklemek/yazmak/sordu/...]" → endikasyon=X, hedef=Y
_ICIN_HEDEF = re.compile(
    r'\b([\wçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\-]{2,}(?:\s+[\wçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\-]{2,})?)'
    r'\s+için\s+'
    r'([\wçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\-]{2,}(?:\s+[\wçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\-]{2,})?)'
    r'\s+(?:eklemek|yazmak|vermek|ba[sş]lamak|reçete|öner(?:mek)?|'
    r'sordu|istedi|talep|ba[sş]vurdu|istiyorum|isteniyor)',
    re.IGNORECASE,
)

# "mevcut ilaçları: X, Y, Z" liste formatı
_ILAC_LISTESI = re.compile(
    r'(?:mevcut\s+ilaçlar[ıi]?|kulland[ıi][gğ][ıi]\s+ilaçlar[ıi]?|'
    r'düzenli\s+ilaçlar[ıi]?|kronik\s+ilaçlar[ıi]?|ilaç\s+listesi)'
    r'\s*[:\-–]?\s*'
    r'([^.!?\n]{3,150})',
    re.IGNORECASE,
)

# Mevcut ilaç tespiti — daha geniş fiil yelpazesi
_MEVCUT_ILAC = re.compile(
    r'\b([\wçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\-]{3,}(?:\s+[\wçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\-]{2,})?)'
    r'\s+(?:kullan[ıi]yor|al[ıi]yor|kullan[ıi]mda|tedavisinde|kullan[ıi]lmakta|'
    r'kullanmakta|almakta|kullanmaktad[ıi]r|almaktad[ıi]r|'
    r'kulland[ıi][gğ][ıi]|ald[ıi][gğ][ıi]|'
    r'kullan[ıi]yor\s+olup|al[ıi]yor\s+olup|'
    r'kullan[ıi]m[ıi]nda|tedavisindeyken)',
    re.IGNORECASE,
)

# Alerji tespiti
_ALERJI = re.compile(
    r'\b([\wçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\-]{2,}(?:\s+[\wçğıöşüÇĞİÖŞÜ][\wçğıöşüÇĞİÖŞÜ\-]{2,})?)'
    r'(?:[\'e\'a\'ye\'ya]|\s+)'
    r'(?:alerjisi\s+(?:var|olan|mevcut|bulunuyor)|'
    r'karş[ıi]\s+alerjik|alerjik|'
    r'aş[ıi]r[ıi]\s+duyarl[ıi]l[ıi][gğ][ıi]|hipersensitivitesi)',
    re.IGNORECASE | re.UNICODE,
)

# Başına gelebilecek ilaç olmayan kelimeler ("hastaya X" → sadece X)
_ILAC_OLMAYAN = {
    'hastaya', 'buna', 'ona', 'bu', 'o', 'birlikte', 'ile', 'hasta',
    'yani', 'sadece', 'birde', 'ayrıca', 'ayrica', 'yeni', 'hemen',
    'gunluk', 'günlük', 'doz', 'sabah', 'aksam', 'akşam', 'gece',
    'için', 'icin', 'ile', 'veya', 'ya', 'de', 'da', 've',
    'tedavi', 'tedavisi', 'nedeni', 'sebebi', 'amacı', 'amaci',
}

# Cinsiyet
_ERKEK  = re.compile(r'\berkek\b', re.IGNORECASE)
_KADIN  = re.compile(r'\bkad[ıi]n\b|\bbayan\b', re.IGNORECASE)

# Kilo
_KILO   = re.compile(r'(\d{2,3}(?:\.\d+)?)\s*kg', re.IGNORECASE)

# ---------------------------------------------------------------------------
# Tanı / Endikasyon çıkarımı
# ---------------------------------------------------------------------------

# Bilinen klinik tanılar — (pattern, kanonik_ad)
_BILINEN_TANILAR: list[tuple[re.Pattern, str]] = [
    (re.compile(r'akut\s+miyokard\s+enfarktüsü|akut\s+mi\b|STEMI|NSTEMI|kalp\s+krizi|miyokard\s+enfarktüsü', re.IGNORECASE), "Akut miyokard enfarktüsü"),
    (re.compile(r'atriyal\s+fibrilasyon|\bAF\b', re.IGNORECASE), "Atriyal fibrilasyon"),
    (re.compile(r'tip\s*[12]\s*diyabet|diyabet(?:es)?|\bDM\b|diabetes\s+mellitus', re.IGNORECASE), "Diyabet"),
    (re.compile(r'hipertansiyon|\bHT\b|hipertansif|yüksek\s+tansiyon', re.IGNORECASE), "Hipertansiyon"),
    (re.compile(r'kalp\s+yetmezli[gğ]i|konjestif\s+kalp|kardiyak\s+yetmezlik', re.IGNORECASE), "Kalp yetmezliği"),
    (re.compile(r'romatoid\s+artrit|\bRA\b', re.IGNORECASE), "Romatoid artrit"),
    (re.compile(r'\bepileps[iy]\b|n[oö]bet\s+hastal', re.IGNORECASE), "Epilepsi"),
    (re.compile(r'\bmigren\b', re.IGNORECASE), "Migren"),
    (re.compile(r'\bKOAH\b|kronik\s+obstrüktif\s+akci[gğ]er', re.IGNORECASE), "KOAH"),
    (re.compile(r'hipotiroid[iy]|hipertiroid[iy]|tiroid\s+hastal', re.IGNORECASE), "Tiroid hastalığı"),
    (re.compile(r'koroner\s+arter\s+hastal|\bKAH\b', re.IGNORECASE), "Koroner arter hastalığı"),
    (re.compile(r'\bosteoporoz\b', re.IGNORECASE), "Osteoporoz"),
    (re.compile(r'\bdepresyon\b|major\s+depresif', re.IGNORECASE), "Depresyon"),
    (re.compile(r'\banksiyete\b|anksiyete\s+bozuklu', re.IGNORECASE), "Anksiyete"),
    (re.compile(r'\bParkinson\b', re.IGNORECASE), "Parkinson hastalığı"),
    (re.compile(r'\bAlzheimer\b|\bdemans\b', re.IGNORECASE), "Demans"),
    (re.compile(r'\bastım\b', re.IGNORECASE), "Astım"),
    (re.compile(r'ülseratif\s+kolit|\bCrohn\b', re.IGNORECASE), "İnflamatuvar bağırsak hastalığı"),
    (re.compile(r'\bgut\s+(?:artriti?|hastal)|\bgut\b(?=\s+(?:tanı|hasta|nedeniy))', re.IGNORECASE), "Gut"),
    (re.compile(r'erektil\s+disfonksiyon|\bED\b(?=\s+(?:tanı|için|nedeniy))', re.IGNORECASE), "Erektil disfonksiyon"),
    (re.compile(r'kronik\s+böbrek\s+hastal|\bKBH\b|\bCKD\b', re.IGNORECASE), "Kronik böbrek hastalığı"),
    (re.compile(r'\bhiperlipidemi\b|\bdislipidemi\b|\byüksek\s+kolesterol\b', re.IGNORECASE), "Hiperlipidemi"),
    (re.compile(r'\bstent\b|\bkoroner\s+stent\b|\bbypass\b', re.IGNORECASE), "Koroner revaskülarizasyon öyküsü"),
    (re.compile(r'\binme\b|\bSVO\b|\biskemik\s+inme\b|\bstroke\b', re.IGNORECASE), "İnme öyküsü"),
    (re.compile(r'\bpulmoner\s+emboli\b|\bPE\b(?=\s+(?:tanı|öykü|geçir))', re.IGNORECASE), "Pulmoner emboli"),
    (re.compile(r'derin\s+ven\s+trombozu|\bDVT\b', re.IGNORECASE), "Derin ven trombozu"),
    (re.compile(r'\bpnömoni\b|\bzatürre\b', re.IGNORECASE), "Pnömoni"),
    (re.compile(r'\bsepsis\b', re.IGNORECASE), "Sepsis"),
]

# Tetikleyici kalıplar — önünde koşul olan kelime/ifade
_ENDIKASYON_TRIGGER = re.compile(
    r'((?:[\wçğıöşüÇĞİÖŞÜ\-]+\s+){1,6})'
    r'(?:tanısı\s+(?:var|mevcut|olan|konulan)|tanılı|geçirmiş|'
    r'geçiren|geçirdi|nedeniyle|sebebiyle|hastal[ıi][gğ][ıi]\s+(?:var|olan))',
    re.IGNORECASE | re.UNICODE,
)

# Tetikleyici çıktısından ilaç / gereksiz kelime filtresi
_TANI_FILTRE = {
    'hasta', 'hastaya', 'yaşında', 'erkek', 'kadın', 'bayan', 'yaklaşık',
    'günce', 'önce', 'sonra', 'taburcu', 'yatan', 'gün', 'hafta', 'ay', 'yıl',
    'şu', 'bu', 'o', 've', 'ile', 'için',
}


# ---------------------------------------------------------------------------
# Veri yapısı
# ---------------------------------------------------------------------------

@dataclass
class ExtractedContext:
    """Serbest metinden çıkarılan hasta bağlamı. Session'da birikimli tutulur."""

    yas: Optional[int] = None
    cinsiyet: Optional[str] = None
    gfr: Optional[float] = None
    kilo: Optional[float] = None
    bobrek_yetmezligi: bool = False
    karaciger_yetmezligi: bool = False
    karaciger_skoru: Optional[str] = None
    gebelik: bool = False
    emzirme: bool = False
    pediyatrik: bool = False
    geriyatrik: bool = False
    mevcut_ilaclar: list = field(default_factory=list)
    alerjiler: list = field(default_factory=list)
    endikasyonlar: list = field(default_factory=list)
    hedef_ilaclar: list = field(default_factory=list)
    temizlenmis_soru: str = ""
    lab_degerleri: dict = field(default_factory=dict)

    def merge(self, other: "ExtractedContext") -> "ExtractedContext":
        """Mevcut bağlamla yeni bağlamı birleştirir. None gelen alanlar eskiyi korur."""
        return ExtractedContext(
            yas=other.yas if other.yas is not None else self.yas,
            cinsiyet=other.cinsiyet or self.cinsiyet,
            gfr=other.gfr if other.gfr is not None else self.gfr,
            kilo=other.kilo if other.kilo is not None else self.kilo,
            bobrek_yetmezligi=other.bobrek_yetmezligi or self.bobrek_yetmezligi,
            karaciger_yetmezligi=other.karaciger_yetmezligi or self.karaciger_yetmezligi,
            karaciger_skoru=other.karaciger_skoru or self.karaciger_skoru,
            gebelik=other.gebelik or self.gebelik,
            emzirme=other.emzirme or self.emzirme,
            pediyatrik=other.pediyatrik or self.pediyatrik,
            geriyatrik=other.geriyatrik or self.geriyatrik,
            mevcut_ilaclar=_merge_lists(self.mevcut_ilaclar, other.mevcut_ilaclar),
            alerjiler=_merge_lists(self.alerjiler, other.alerjiler),
            endikasyonlar=_merge_lists(self.endikasyonlar, other.endikasyonlar),
            hedef_ilaclar=other.hedef_ilaclar if other.hedef_ilaclar else self.hedef_ilaclar,
            temizlenmis_soru=other.temizlenmis_soru or self.temizlenmis_soru,
            lab_degerleri={**self.lab_degerleri, **other.lab_degerleri},
        )

    @property
    def dolu_mu(self) -> bool:
        return any([
            self.yas, self.cinsiyet, self.gfr,
            self.mevcut_ilaclar, self.hedef_ilaclar,
            self.bobrek_yetmezligi, self.karaciger_yetmezligi,
            self.lab_degerleri,
        ])


def _merge_lists(a: list, b: list) -> list:
    seen, result = set(), []
    for item in a + b:
        key = item.lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Ana çıkarım fonksiyonu (kural tabanlı)
# ---------------------------------------------------------------------------

def extract_context(text: str, ilac_listesi: list[str] | None = None) -> "ExtractedContext":
    """
    Türkçe klinik sorgudan hasta bağlamını çıkarır.
    LLM çağrısı yapmaz — regex + ilaç listesi eşleştirmesi kullanır.

    Args:
        text:          Doktorun yazdığı ham metin
        ilac_listesi:  ChromaDB'den gelen bilinen ilaç adları (None ise ilaç tespiti atlanır)

    Returns:
        ExtractedContext
    """
    # ── Yaş ──
    yas = None
    m = _YAS.search(text)
    if m:
        v = int(m.group(1))
        yas = v if 0 < v < 120 else None

    # ── Cinsiyet ──
    cinsiyet = None
    if _ERKEK.search(text):
        cinsiyet = "erkek"
    elif _KADIN.search(text):
        cinsiyet = "kadın"

    # ── Kilo ──
    kilo = None
    m = _KILO.search(text)
    if m:
        v = float(m.group(1))
        kilo = v if 10 < v < 300 else None

    # ── GFR ──
    gfr = None
    m = _GFR.search(text)
    if m:
        gfr = float(m.group(1))

    # ── Klinik durumlar ──
    bobrek      = bool(_BOBREK.search(text))
    if gfr and gfr < 60:
        bobrek = True
    karaciger   = bool(_KARACIGER.search(text))
    gebelik     = bool(_GEBELIK.search(text))
    emzirme     = bool(_EMZIRME.search(text))
    pediyatrik  = bool(_PEDIYATRIK.search(text))
    geriyatrik  = bool(_GERIYATRIK.search(text))
    if yas and yas >= 65:
        geriyatrik = True
    if yas and yas < 18:
        pediyatrik = True

    # ── Child-Pugh ──
    kc_skoru = None
    m = _CHILD.search(text)
    if m:
        kc_skoru = m.group(1).upper()

    # ── Alerjiler ──
    alerjiler: list[str] = []
    for m in _ALERJI.finditer(text):
        madde = _filtrele_ilac_adi(m.group(1).strip())
        if madde and len(madde) > 2 and madde not in alerjiler:
            alerjiler.append(madde)

    # ── Lab değerleri ──
    lab_degerleri: dict[str, float] = {}
    for param, pat in _LAB_PATTERNS.items():
        m = pat.search(text)
        if m:
            lab_degerleri[param] = float(m.group(1))

    # ── Tanı / Endikasyon ──
    endikasyonlar: list[str] = []
    # 1. Bilinen tanı listesinde ara (yüksek güven)
    for pat, kanon in _BILINEN_TANILAR:
        if pat.search(text) and kanon not in endikasyonlar:
            endikasyonlar.append(kanon)
    # 2. Tetikleyici kalıpla çıkar ("X geçirmiş", "X tanısı var" …)
    for m in _ENDIKASYON_TRIGGER.finditer(text):
        ham = m.group(1).strip()
        # Çok kısa veya sadece filtre kelimeleriyse atla
        kelimeler = [k for k in ham.split() if k.lower() not in _TANI_FILTRE and len(k) > 2]
        if len(kelimeler) < 2:
            continue
        tani = " ".join(kelimeler).strip().rstrip(",.")
        # Zaten bilinen tanı olarak eklenmediyse ve ilaç adı gibi görünmüyorsa ekle
        if not any(tani.lower() in e.lower() or e.lower() in tani.lower()
                   for e in endikasyonlar):
            endikasyonlar.append(tani)

    # ── İlaç eşleştirme ──
    mevcut_ilaclar: list[str] = []
    hedef_ilaclar:  list[str] = []

    # 1. Cümle yapısından hedef ilaç: "X yazabilir miyim / eklemek istiyorum?" → X
    hedef_ham: str | None = None
    m = _HEDEF_ILAC.search(text)
    if m:
        hedef_ham = _filtrele_ilac_adi(m.group(1).strip())

    # 1b. "X için Y eklemek" kalıbı — hem endikasyon hem hedef ilaç
    #     _HEDEF_ILAC'tan daha güvenilir: "X için" → X=endikasyon, Y=hedef
    icin_m = _ICIN_HEDEF.search(text)
    if icin_m:
        endikasyon_ham = icin_m.group(1).strip().rstrip(',.')
        hedef_icin     = _filtrele_ilac_adi(icin_m.group(2).strip())
        if hedef_icin:
            hedef_ham = hedef_icin   # _HEDEF_ILAC sonucunu geçersiz kıl
        # Endikasyon olarak ekle (bilinen listede yoksa)
        if endikasyon_ham and len(endikasyon_ham) > 2:
            if not any(endikasyon_ham.lower() in e.lower() or e.lower() in endikasyon_ham.lower()
                       for e in endikasyonlar):
                endikasyonlar.append(endikasyon_ham.capitalize())

    # 2. Cümle yapısından mevcut ilaçlar: "warfarin kullanıyor" → warfarin
    mevcut_ham: list[str] = []
    for m in _MEVCUT_ILAC.finditer(text):
        ad = _filtrele_ilac_adi(m.group(1).strip())
        if ad and (not hedef_ham or ad.lower() != hedef_ham.lower()):
            mevcut_ham.append(ad)

    # 2b. Liste formatı: "mevcut ilaçları: X, Y, Z" → her birini ayır
    liste_m = _ILAC_LISTESI.search(text)
    if liste_m:
        for parca in re.split(r',|\bve\b', liste_m.group(1)):
            ad = _filtrele_ilac_adi(parca.strip().rstrip('.,'))
            if ad and len(ad) > 2 and (not hedef_ham or ad.lower() != hedef_ham.lower()):
                if ad.lower() not in {x.lower() for x in mevcut_ham}:
                    mevcut_ham.append(ad)

    if ilac_listesi:
        mevcut_ilaclar, hedef_ilaclar = _eslestir_ilaclar(
            text, ilac_listesi, hedef_ham, mevcut_ham
        )
    else:
        hedef_ilaclar = [hedef_ham] if hedef_ham else []
        mevcut_ilaclar = mevcut_ham

    # ── Temizlenmiş soru ──
    # Soru işareti içeren cümleleri yakala
    cumle_re = re.compile(r'[^.!?]*\?')
    sorular = cumle_re.findall(text)
    temizlenmis_soru = " ".join(sorular).strip() if sorular else text

    return ExtractedContext(
        yas=yas,
        cinsiyet=cinsiyet,
        gfr=gfr,
        kilo=kilo,
        bobrek_yetmezligi=bobrek,
        karaciger_yetmezligi=karaciger,
        karaciger_skoru=kc_skoru,
        gebelik=gebelik,
        emzirme=emzirme,
        pediyatrik=pediyatrik,
        geriyatrik=geriyatrik,
        mevcut_ilaclar=mevcut_ilaclar,
        alerjiler=alerjiler,
        endikasyonlar=endikasyonlar,
        hedef_ilaclar=hedef_ilaclar,
        temizlenmis_soru=temizlenmis_soru or text,
        lab_degerleri=lab_degerleri,
    )


# ---------------------------------------------------------------------------
# İlaç eşleştirme
# ---------------------------------------------------------------------------

def _filtrele_ilac_adi(s: str) -> str | None:
    """
    Başındaki ilaç-olmayan kelimeleri atar.
    "hastaya klaritromisin" → "klaritromisin"
    "bu NORODOL" → "NORODOL"
    """
    kelimeler = s.split()
    while kelimeler and kelimeler[0].lower() in _ILAC_OLMAYAN:
        kelimeler = kelimeler[1:]
    return " ".join(kelimeler) if kelimeler else None


def _tr_norm(s: str) -> str:
    """Türkçe karakter farkından bağımsız büyük-harf karşılaştırma için normalize eder."""
    return (s.upper()
            .replace('İ', 'I').replace('Ğ', 'G')
            .replace('Ş', 'S').replace('Ç', 'C')
            .replace('Ü', 'U').replace('Ö', 'O'))


def _eslestir_ilaclar(
    text: str,
    ilac_listesi: list[str],
    hedef_ham: str | None = None,
    mevcut_ham: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    """
    Metindeki ilaç adlarını ChromaDB listesiyle eşleştirir.

    Strateji:
      1. hedef_ham varsa (cümle yapısından çıkarıldıysa) önce onu ChromaDB'de ara
      2. Kalan ilaçlar için marka/INN kelime eşleştirmesi yap (mevcut ilaçlar)
      3. Tüm karşılaştırmalar Türkçe normalize edilmiş (İ=I, Ş=S...)
    """
    text_norm = _tr_norm(text)

    # ChromaDB adlarını normalize et: norm → [orijinal_ad]
    norm_to_tam: dict[str, list[str]] = {}
    for tam in ilac_listesi:
        kelimeler = tam.split()
        # Her kelimeyi ayrı ayrı indeksle (marka veya INN olabilir)
        for kelime in kelimeler[:3]:  # sadece ilk 3 kelime (doz/form kelimeleri pas)
            k_norm = _tr_norm(kelime)
            if len(k_norm) >= 4 and not kelime[0].isdigit():
                norm_to_tam.setdefault(k_norm, []).append(tam)

    def _bul_chromadb(aday: str) -> list[str]:
        """Aday ilaç adını ChromaDB listesinde bul (normalize karşılaştırma)."""
        aday_norm = _tr_norm(aday)
        # 1. Tam kelime eşleşmesi
        if aday_norm in norm_to_tam:
            return list(dict.fromkeys(norm_to_tam[aday_norm]))[:2]
        # 2. Substring eşleşmesi: aday, herhangi bir ilaç adı içinde geçiyor mu?
        eslesme = [
            tam for tam in ilac_listesi
            if aday_norm in _tr_norm(tam)
        ]
        return list(dict.fromkeys(eslesme))[:2]

    # ── Hedef ilaç (cümle yapısından geldiyse öncelikli) ──
    hedef_tam: list[str] = []
    if hedef_ham:
        hedef_tam = _bul_chromadb(hedef_ham)
        if not hedef_tam:
            hedef_tam = [hedef_ham]  # ChromaDB'de yoksa ham ismi kullan

    # ── Mevcut ilaçlar: metinde geçen diğer ilaçlar ──
    bulunan: list[tuple[int, str]] = []
    for anahtar, tam_adlar in norm_to_tam.items():
        if len(anahtar) < 5:
            continue
        pat = re.compile(r'\b' + re.escape(anahtar) + r'\b')
        m = pat.search(text_norm)
        if m:
            for ta in tam_adlar:
                if not any(x[1] == ta for x in bulunan):
                    bulunan.append((m.start(), ta))

    # Mevcut_ham listesini de ChromaDB ile eşleştir
    mevcut_eslesik: list[str] = []
    if mevcut_ham:
        for mh in mevcut_ham:
            eslesme = _bul_chromadb(mh)
            if eslesme:
                mevcut_eslesik.extend(eslesme)
            else:
                mevcut_eslesik.append(mh)  # ChromaDB'de yoksa ham ismi kullan
        mevcut_eslesik = list(dict.fromkeys(mevcut_eslesik))

    # hedef_tam zaten belirlendiyse: kalan ilaçlar mevcut, hedef sabit
    if hedef_tam:
        hedef_tam_norm = {_tr_norm(h.split()[0]) for h in hedef_tam}
        # bulunan + mevcut_eslesik birleştir, hedef olanları çıkar
        tum_mevcut = list(dict.fromkeys(
            [ad for _, ad in bulunan if _tr_norm(ad.split()[0]) not in hedef_tam_norm]
            + [ad for ad in mevcut_eslesik if _tr_norm(ad.split()[0]) not in hedef_tam_norm]
        ))
        return tum_mevcut, hedef_tam

    if not bulunan:
        return [], []

    # hedef_ham yoksa: soru ifadesine en yakın ilaç → hedef
    soru_m = _SORU_IFADESI.search(text)
    soru_pos = soru_m.start() if soru_m else len(text)

    onceki = [(pos, ad) for pos, ad in bulunan if pos < soru_pos]
    sonraki = [(pos, ad) for pos, ad in bulunan if pos >= soru_pos]

    if onceki:
        hedef_pos, hedef = max(onceki, key=lambda x: x[0])
        mevcut = [ad for pos, ad in bulunan if ad != hedef]
    elif sonraki:
        hedef_pos, hedef = min(sonraki, key=lambda x: x[0])
        mevcut = [ad for pos, ad in bulunan if ad != hedef]
    else:
        return [ad for _, ad in bulunan], []

    return mevcut, [hedef]
