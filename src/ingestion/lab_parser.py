"""
Lab raporu parser — PDF ve görüntü formatından lab değerlerini çıkarır.

Desteklenen parametreler: ALT, AST, Kreatinin, K, Na, INR, HbA1c,
Bilirubin, Hemoglobin, Trombosit, GFR
"""
import re
from loguru import logger

# ---------------------------------------------------------------------------
# Parametre → regex pattern eşlemeleri (geniş eşleşme, hastaneden hastaneye
# farklı format)
# ---------------------------------------------------------------------------

_LAB_PATTERNS: dict[str, list[str]] = {
    "ALT": [
        r"\bALT\b",
        r"\bSGPT\b",
        r"Alanin[\s\-]?[Aa]minotransferaz",
        r"Alanin[\s\-]?[Tt]ransaminaz",
        r"Alanine\s+[Aa]minotransferase",
    ],
    "AST": [
        r"\bAST\b",
        r"\bSGOT\b",
        r"Aspartat[\s\-]?[Aa]minotransferaz",
        r"Aspartat[\s\-]?[Tt]ransaminaz",
        r"Aspartate\s+[Aa]minotransferase",
    ],
    "Kreatinin": [
        r"\bKreatinin\b",
        r"\bCreatinine?\b",
        r"\bKREA\b",
        r"\bCrea\b",
    ],
    "K": [
        r"\bPotasyum\b",
        r"\bPotassium\b",
        r"\bKalium\b",
        # Tek 'K' harfi — sadece satır başında veya iki nokta/boşluktan sonra
        r"(?:^|[\s:;|])\bK\b(?:\+)?(?=\s*[:=\s]\s*\d)",
    ],
    "Na": [
        r"\bSodyum\b",
        r"\bSodium\b",
        r"\bNatrium\b",
        r"(?:^|[\s:;|])\bNa\b(?:\+)?(?=\s*[:=\s]\s*\d)",
    ],
    "INR": [
        r"\bINR\b",
        r"International\s+Normalized\s+Ratio",
        r"Uluslararas[iı]\s+Normalize",
    ],
    "HbA1c": [
        r"\bHbA1[cC]\b",
        r"\bHgbA1[cC]\b",
        r"Hemoglobin\s+A1[cC]",
        r"Glikozile\s+Hemoglobin",
        r"Glikolize\s+Hemoglobin",
    ],
    "Bilirubin": [
        r"Total\s+Bilirubin",
        r"Toplam\s+Bilirubin",
        r"\bBilirubin[\s,]",
        r"\bBilirubin$",
        r"\bT\.?\s*[Bb]il\b",
    ],
    "Hemoglobin": [
        r"\bHemoglobin\b",
        r"\bHgb\b",
        # Hb — HbA1c ile çakışmaması için negatif lookahead
        r"\bHb\b(?!A1)",
    ],
    "Trombosit": [
        r"\bTrombosit\b",
        r"\bThrombocyte\b",
        r"\bPlatelet\b",
        r"\bPLT\b",
    ],
    "GFR": [
        r"\beGFR\b",
        r"\bGFR\b",
        r"Glomerüler\s+[Ff]iltrasyon",
        r"CKD[-\s]?EPI",
        r"Tahmini\s+GFR",
    ],
}

# Ondalık nokta veya Türkçe virgülü destekleyen sayı regex
_NUMBER_RE = re.compile(r"(\d{1,4}[.,]\d{1,3}|\d{1,4})")


# ---------------------------------------------------------------------------
# Metin → dict
# ---------------------------------------------------------------------------

def _parse_text(text: str) -> dict[str, float]:
    """Ham metinden lab değerlerini çıkarır. Döndürür: {param: value, ...}

    e-Nabız gibi tablo-bazlı PDF'lerde PyMuPDF parametre adını ve değerini
    farklı satırlara bölüyor olabilir. Bu nedenle:
    - Önce aynı satırda sayı aranır.
    - Bulunamazsa sonraki 2 satır da kontrol edilir (lookahead).
    - Tarihlerin (ör. 25.06.2025) yanlış eşleşmesini önlemek için
      4+ basamaklı sayılar yıl kalıplarıyla elenir.
    """
    results: dict[str, float] = {}
    lines = text.splitlines()

    # Tarih/yıl sayılarını yanlışlıkla değer olarak almamak için
    _DATE_YEAR_RE = re.compile(r"^\d{4}$|^20\d{2}$|^\d{1,2}\.\d{1,2}\.\d{4}$")

    def _first_valid_number(search_lines: list[str]) -> float | None:
        """Verilen satırlardan ilk geçerli sayıyı döner (tarih sayıları hariç)."""
        for sl in search_lines:
            nums = _NUMBER_RE.findall(sl)
            for raw in nums:
                if _DATE_YEAR_RE.match(raw.replace(",", ".")):
                    continue
                try:
                    return float(raw.replace(",", "."))
                except ValueError:
                    continue
        return None

    for param, patterns in _LAB_PATTERNS.items():
        for pattern in patterns:
            for i, line in enumerate(lines):
                if re.search(pattern, line, re.IGNORECASE):
                    # 1) Aynı satırda ara, 2) bulamazsan sonraki 2 satırda ara
                    candidate_lines = [line] + lines[i + 1: i + 3]
                    val = _first_valid_number(candidate_lines)
                    if val is not None and _sanity_check(param, val):
                        results[param] = val
                        logger.debug(f"Lab parse: {param} = {val} ('{line.strip()}')")
                    break  # Pattern eşleşti, bir sonraki pattern'e geç
            if param in results:
                break  # Bu param bulundu, diğer pattern'lere bakma

    return results


def _sanity_check(param: str, val: float) -> bool:
    """Makul değer aralığı kontrolü — açıkça saçma sayıları filtreler."""
    _RANGES = {
        "ALT":        (1, 2000),
        "AST":        (1, 2000),
        "Kreatinin":  (0.1, 30),
        "K":          (1.0, 10.0),
        "Na":         (100, 200),
        "INR":        (0.5, 20),
        "HbA1c":      (3, 20),
        "Bilirubin":  (0.1, 50),
        "Hemoglobin": (1, 25),
        "Trombosit":  (1, 2000),
        "GFR":        (1, 200),
    }
    lo, hi = _RANGES.get(param, (0, float("inf")))
    return lo <= val <= hi


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_lab_pdf(file_bytes: bytes) -> dict[str, float]:
    """PDF byte'larından lab değerlerini çıkarır. PyMuPDF kullanır.

    sort=True: Metin bloklarını koordinata göre sıralar — e-Nabız gibi
    tablo PDF'lerinde sütunların karışmasını önler.
    """
    import fitz  # PyMuPDF

    text_parts: list[str] = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page in doc:
        text_parts.append(page.get_text("text", sort=True))
    doc.close()

    full_text = "\n".join(text_parts)
    logger.debug(f"Lab PDF parse: {len(full_text)} karakter çıkarıldı")
    if len(full_text.strip()) < 50:
        logger.warning("Lab PDF: çok az metin çıkarıldı — taranmış (image-based) PDF olabilir")
    return _parse_text(full_text)


def parse_lab_image(file_bytes: bytes) -> dict[str, float]:
    """Görüntü byte'larından lab değerlerini çıkarır. pytesseract kullanır (opsiyonel)."""
    try:
        import pytesseract
        from PIL import Image
        import io as _io
    except ImportError as exc:
        raise ImportError(
            "Görüntü parse için 'pytesseract' ve 'Pillow' kütüphaneleri gereklidir. "
            "pip install pytesseract Pillow"
        ) from exc

    image = Image.open(_io.BytesIO(file_bytes))
    # Önce Türkçe, yoksa İngilizce
    try:
        text = pytesseract.image_to_string(image, lang="tur+eng")
    except pytesseract.TesseractError:
        text = pytesseract.image_to_string(image, lang="eng")

    logger.debug(f"Lab görüntü OCR: {len(text)} karakter çıkarıldı")
    return _parse_text(text)


def parse_lab_file(file_bytes: bytes, filename: str) -> dict[str, float]:
    """Dosya adına göre uygun parser'ı seçer ve lab değerlerini döndürür."""
    fname_lower = filename.lower()
    if fname_lower.endswith(".pdf"):
        return parse_lab_pdf(file_bytes)
    elif fname_lower.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp")):
        return parse_lab_image(file_bytes)
    else:
        raise ValueError(f"Desteklenmeyen dosya formatı: {filename}. PDF, PNG veya JPG yükleyin.")
