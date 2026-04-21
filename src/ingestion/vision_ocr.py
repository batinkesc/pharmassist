"""
Claude Vision OCR — Resim Bazlı KÜB PDF Okuyucu — DISABLED

⚠️  THIS MODULE USES CLAUDE HAIKU AND COSTS MONEY. DISABLED BY DEFAULT.
Set ENABLE_VISION_OCR=true in .env to enable (NOT RECOMMENDED).

Resim bazlı (tarayıcıdan oluşturulmuş) TİTCK PDF'lerini Claude Haiku Vision ile
metin çıkarma yapar. Sonuç, mevcut pdf_parser.py pipeline'ına doğrudan verilir.

Özellikler:
  - Her sayfa PNG olarak render edilir
  - Claude Haiku Vision her sayfayı okur
  - Tablolar markdown formatında çıkarılır
  - Rate limit için exponential backoff (tenacity)
  - Paralel sayfa işleme (ThreadPoolExecutor)

Kullanım:
    from src.ingestion.vision_ocr import ocr_pdf_to_text
    full_text, page_offsets = ocr_pdf_to_text(pdf_path)
"""

import base64
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
import pymupdf
from loguru import logger

# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------

_MODEL = "claude-haiku-4-5-20251001"
_MAX_WORKERS = 5          # Paralel sayfa işleme (rate limit dostu)
_RETRY_MAX   = 3          # Max retry sayısı
_RETRY_WAIT  = 2.0        # İlk bekleme (saniye) — her seferinde 2x artar
_DPI         = 150        # PNG render çözünürlüğü — 150 tıp metni için yeterli
_JPEG_QUALITY = 85        # Sıkıştırma (boyut/kalite dengesi)

_SYSTEM_PROMPT = """Sen bir Türk tıbbi belge OCR uzmanısın.
TİTCK KÜB (Kısa Ürün Bilgisi) belgelerini eksiksiz ve doğru şekilde metin olarak çıkarırsın."""

_PAGE_PROMPT = """Bu, bir Türk ilaç KÜB (Kısa Ürün Bilgisi) belgesinin taranmış sayfasıdır.

Sayfadaki TÜM içeriği aşağıdaki kurallara göre çıkar:

1. Metni orijinal sırasıyla ve tam olarak yaz
2. Bölüm başlıklarını koru — örnek: "4.3 Kontrendikasyonlar", "4.5. Diğer tıbbi ürünler ile etkileşimler"
3. Tabloları GitHub Markdown formatında yaz:
   | Sütun 1 | Sütun 2 |
   | --- | --- |
   | veri | veri |
4. Madde işaretlerini koru (•, -, ▪, ►)
5. Sayfa numaralarını ve "güvenli elektronik imza" / "Belge Doğrulama Kodu" satırlarını YAZMA
6. Sadece belge metnini döndür — açıklama, yorum veya "İşte metin:" gibi giriş ekleme"""


# ---------------------------------------------------------------------------
# İstemci
# ---------------------------------------------------------------------------

def _get_client() -> anthropic.Anthropic:
    # CRITICAL SECURITY: This function uses Claude Haiku API = MONEY
    # Only allow if EXPLICITLY enabled via env var
    if os.environ.get("ENABLE_VISION_OCR", "").lower() != "true":
        raise RuntimeError(
            "❌ Vision OCR is DISABLED to prevent unexpected API charges.\n"
            "   This module uses Claude Haiku ($) for every PDF page.\n"
            "   Set ENABLE_VISION_OCR=true in .env if you REALLY want to use it."
        )

    # .env yüklenmemişse proje kökünden yükle
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        from pathlib import Path as _P
        env_path = _P(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    os.environ["ANTHROPIC_API_KEY"] = api_key
                    break
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY bulunamadı — .env dosyasını kontrol edin.")
    return anthropic.Anthropic(api_key=api_key)


# ---------------------------------------------------------------------------
# Sayfa → PNG → Base64
# ---------------------------------------------------------------------------

def _render_page(page: pymupdf.Page, dpi: int = _DPI) -> bytes:
    """
    PDF sayfasını PNG olarak render eder.
    DPI 150 → tıp metni için yeterli kalite, makul dosya boyutu.
    """
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
    return pix.tobytes("png")


def _page_to_b64(page: pymupdf.Page) -> str:
    """Sayfa PNG → base64 string."""
    png_bytes = _render_page(page)
    return base64.standard_b64encode(png_bytes).decode("utf-8")


# ---------------------------------------------------------------------------
# Tek Sayfa OCR
# ---------------------------------------------------------------------------

def _ocr_single_page(
    client: anthropic.Anthropic,
    page_b64: str,
    page_num: int,
) -> str:
    """
    Tek bir sayfayı Claude Vision ile okur.
    Başarısız olursa exponential backoff ile retry yapar.
    """
    for attempt in range(_RETRY_MAX):
        try:
            response = client.messages.create(
                model=_MODEL,
                max_tokens=4096,
                system=_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": page_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": _PAGE_PROMPT,
                            },
                        ],
                    }
                ],
            )
            text = response.content[0].text.strip()
            logger.debug(f"  Sayfa {page_num}: {len(text)} char çıkarıldı")
            return text

        except anthropic.RateLimitError:
            wait = _RETRY_WAIT * (2 ** attempt)
            logger.warning(f"  Rate limit — {wait:.0f}s bekleniyor (sayfa {page_num}, deneme {attempt+1})")
            time.sleep(wait)

        except anthropic.APIError as e:
            wait = _RETRY_WAIT * (2 ** attempt)
            logger.warning(f"  API hatası ({e}) — {wait:.0f}s (sayfa {page_num}, deneme {attempt+1})")
            time.sleep(wait)

    logger.error(f"  Sayfa {page_num} {_RETRY_MAX} denemeden sonra başarısız — boş döndürülüyor")
    return ""


# ---------------------------------------------------------------------------
# OCR Sonrası Temizleme
# ---------------------------------------------------------------------------

def _strip_markdown_bold(text: str) -> str:
    """
    Claude'un OCR çıktısındaki markdown bold/italic işaretlerini kaldırır.
    KÜB section tespiti regex'leri düz metin bekler.

    **4.3 Kontrendikasyonlar** → 4.3 Kontrendikasyonlar
    *not*                      → not
    """
    import re
    # Bold: **text** veya __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    # İtalik: *text* veya _text_ (sadece tek yıldız/alt çizgi)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', text)
    return text


# ---------------------------------------------------------------------------
# Ana Fonksiyon
# ---------------------------------------------------------------------------

def ocr_pdf_to_text(
    pdf_path: str | Path,
    max_workers: int = _MAX_WORKERS,
) -> tuple[str, list[int]]:
    """
    Resim bazlı PDF'i Claude Vision ile metne çevirir.

    Args:
        pdf_path:    PDF dosya yolu
        max_workers: Paralel sayfa işleme limiti

    Returns:
        (full_text, page_offsets)
        full_text:    Tüm sayfaların birleşik metni
        page_offsets: Her sayfanın full_text'teki başlangıç pozisyonu
    """
    pdf_path = Path(pdf_path)
    logger.info(f"[Vision OCR] {pdf_path.name} — Claude Haiku Vision ile okunuyor")

    client = _get_client()
    doc = pymupdf.open(str(pdf_path))
    total_pages = len(doc)

    logger.info(f"  {total_pages} sayfa render ediliyor (DPI={_DPI})...")

    # Sayfaları render et (paralel safe — sadece okuma)
    page_b64s: list[tuple[int, str]] = []
    for i, page in enumerate(doc):
        b64 = _page_to_b64(page)
        page_b64s.append((i + 1, b64))
    doc.close()

    logger.info(f"  Claude Vision ile {total_pages} sayfa işleniyor ({max_workers} paralel)...")

    # Paralel OCR
    page_texts: dict[int, str] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_ocr_single_page, client, b64, pnum): pnum
            for pnum, b64 in page_b64s
        }
        for future in as_completed(futures):
            pnum = futures[future]
            try:
                page_texts[pnum] = future.result()
            except Exception as e:
                logger.error(f"  Sayfa {pnum} işlenemedi: {e}")
                page_texts[pnum] = ""

    # Sayfa sırasına göre birleştir + markdown bold temizle
    full_text = ""
    page_offsets: list[int] = []

    for pnum in range(1, total_pages + 1):
        page_offsets.append(len(full_text))
        text = page_texts.get(pnum, "")
        text = _strip_markdown_bold(text)
        full_text += text + "\n"

    total_chars = len(full_text.strip())
    logger.info(
        f"  [Vision OCR] Tamamlandı: {total_pages} sayfa → {total_chars} karakter"
    )

    if total_chars < 100:
        logger.warning(
            f"  [Vision OCR] Çok az karakter çıkarıldı ({total_chars}). "
            f"PDF kalitesi düşük olabilir."
        )

    return full_text, page_offsets
