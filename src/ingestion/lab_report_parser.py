"""
Web UI için lab raporu parser — e-Nabız ve benzeri Türk hastane formatları.

Tablo bazlı PDF'lerden TÜM parametreleri çıkarır (40+), ardından
PharmAssist PatientProfile'ına eşlenebilenleri ayrıca döndürür.

Kullanım:
    result = parse_lab_report(file_bytes, "rapor.pdf")
    result.all_values       # {display_name: value}  — tüm parametreler
    result.profile_values   # {canonical_key: value} — PatientProfile'a gidenler

NOT: Bu modül yalnızca web UI içindir (app.py).
     KÜB ingestion pipeline'ı (pdf_parser.py) ile ilgisi yoktur.
"""

import re
from dataclasses import dataclass, field
from loguru import logger

# ---------------------------------------------------------------------------
# e-Nabız tablo satır formatı:
#   [Parametre adı]   [≥2 boşluk]   [sayısal değer]   [boşluk/satırsonu]
# ---------------------------------------------------------------------------
_ROW_RE = re.compile(
    r"^"
    r"(.+?)"                                     # parametre adı (non-greedy)
    r"\s{2,}"                                    # sütun ayırıcı (≥2 boşluk)
    r"(\d{1,5}[.,]\d{1,4}|\d{1,5})"             # sayısal değer (TR virgül destekli)
    r"(?:\s|$)",                                 # boşluk veya satır sonu
    re.UNICODE,
)

# Parantez içi kısaltma: "Alanin aminotransferaz (ALT)" → "ALT"
# Küçük harf de dahil: Na, Ca, Mg, eGFR, HbA1c
_ABBREV_RE = re.compile(r"\(([A-Za-z][A-Za-z0-9#%]*)\)\s*$")

# Başlık / footer satırları — atlanacak
_SKIP_RE = re.compile(
    r"^("
    r"T\.C\.|Sağlık|Tarih\s|Adı|Doğum|Cinsiyet|Sağlık Tesisi"
    r"|Sonuç\s|Referans|Birimi|Değeri"
    r"|enabiz|0 850|Sayfa\s"
    r"|\d{1,2}\.\d{2}\.\d{4}"  # tarih: 25.06.2025
    r"|\d{2}:\d{2}"            # saat: 11:48
    r"|TAM KAN|HEMOGRAM"
    r")",
    re.IGNORECASE | re.UNICODE,
)

# ---------------------------------------------------------------------------
# PatientProfile kanonik anahtar eşlemeleri
# display_name → canonical_key
# ---------------------------------------------------------------------------
_PROFILE_MAP: dict[str, str] = {
    # Kısaltmalar (parentez içinden çıkarılan)
    "ALT":    "ALT",
    "AST":    "AST",
    "HGB":    "Hemoglobin",
    "HB":     "Hemoglobin",
    "PLT":    "Trombosit",
    "K":      "K",
    "Na":     "Na",
    "INR":    "INR",
    "GFR":    "GFR",
    "eGFR":   "GFR",
    "HbA1c":  "HbA1c",
    "HgbA1c": "HbA1c",
    "Bil":    "Bilirubin",
    # Tam isimle eşleşenler (kısaltma yoksa)
    "Hemoglobin":  "Hemoglobin",
    "Trombosit":   "Trombosit",
    "Kreatinin":   "Kreatinin",
    "Creatinine":  "Kreatinin",
    "Bilirubin":   "Bilirubin",
    "Potasyum (K)": "K",    # fallback: tam ad
    "Sodyum (Na)":  "Na",   # fallback: tam ad
}

# Sanity check — yalnızca PatientProfile parametreleri için
_PROFILE_RANGES: dict[str, tuple[float, float]] = {
    "ALT":        (1,   2000),
    "AST":        (1,   2000),
    "Hemoglobin": (1,   25),
    "Trombosit":  (1,   2000),
    "K":          (1.0, 10.0),
    "Na":         (100, 200),
    "INR":        (0.5, 20),
    "GFR":        (1,   200),
    "HbA1c":      (3,   20),
    "Kreatinin":  (0.1, 30),
    "Bilirubin":  (0.1, 50),
}


# ---------------------------------------------------------------------------
# Sonuç veri sınıfı
# ---------------------------------------------------------------------------

@dataclass
class LabReportResult:
    all_values: dict[str, float] = field(default_factory=dict)
    """Rapordaki TÜM parametreler → display_name: value"""

    profile_values: dict[str, float] = field(default_factory=dict)
    """PatientProfile'a eşlenenler → canonical_key: value"""


# ---------------------------------------------------------------------------
# Çekirdek parser
# ---------------------------------------------------------------------------

def _display_name(raw: str) -> str:
    """'Alanin aminotransferaz (ALT)' → 'ALT', 'HGB' → 'HGB', 'Serbest T3' → 'Serbest T3'"""
    m = _ABBREV_RE.search(raw)
    return m.group(1) if m else raw.strip()


def _parse_lines(lines: list[str]) -> LabReportResult:
    result = LabReportResult()

    for line in lines:
        s = line.strip()
        if not s or _SKIP_RE.match(s):
            continue

        m = _ROW_RE.match(s)
        if not m:
            continue

        raw_name = m.group(1).strip()
        raw_val  = m.group(2).replace(",", ".")
        try:
            val = float(raw_val)
        except ValueError:
            continue

        disp = _display_name(raw_name)
        result.all_values[disp] = val
        logger.debug(f"Lab: {disp} = {val}  (raw: '{raw_name}')")

        # PatientProfile'a ekle — kanonik isim varsa kullan, yoksa display_name ile ekle
        canonical = _PROFILE_MAP.get(disp) or _PROFILE_MAP.get(raw_name)
        profile_key = canonical if canonical else disp
        # Bilinen parametreler için sanity check; bilinmeyenler doğrudan eklenir
        lo, hi = _PROFILE_RANGES.get(profile_key, (0, float("inf")))
        if lo <= val <= hi:
            result.profile_values[profile_key] = val

    logger.info(
        f"Lab raporu parse: {len(result.all_values)} parametre, "
        f"{len(result.profile_values)} profil değeri"
    )
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_lab_report_pdf(file_bytes: bytes) -> LabReportResult:
    """PDF byte'larından lab değerlerini çıkarır (PyMuPDF)."""
    import fitz

    lines: list[str] = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page in doc:
        # sort=True: bloklari koordinata gore sirala → tablo sütunları karışmaz
        lines += page.get_text("text", sort=True).splitlines()
    doc.close()

    logger.debug(f"Lab PDF: {len(lines)} satır çıkarıldı")
    if sum(len(l.strip()) for l in lines) < 50:
        logger.warning("Lab PDF: çok az metin — taranmış (image-based) PDF olabilir")

    return _parse_lines(lines)


def parse_lab_report_image(file_bytes: bytes) -> LabReportResult:
    """Görüntü dosyasından lab değerlerini çıkarır (pytesseract)."""
    try:
        import pytesseract
        from PIL import Image
        import io
    except ImportError as exc:
        raise ImportError(
            "Görüntü parse için 'pytesseract' ve 'Pillow' gereklidir."
        ) from exc

    img = Image.open(io.BytesIO(file_bytes))
    try:
        text = pytesseract.image_to_string(img, lang="tur+eng")
    except pytesseract.TesseractError:
        text = pytesseract.image_to_string(img, lang="eng")

    return _parse_lines(text.splitlines())


def parse_lab_report(file_bytes: bytes, filename: str) -> LabReportResult:
    """Dosya uzantısına göre uygun parser'ı seçer."""
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return parse_lab_report_pdf(file_bytes)
    elif ext in ("png", "jpg", "jpeg", "tiff", "bmp", "webp"):
        return parse_lab_report_image(file_bytes)
    else:
        raise ValueError(
            f"Desteklenmeyen format: {filename}. PDF, PNG veya JPG yükleyin."
        )
