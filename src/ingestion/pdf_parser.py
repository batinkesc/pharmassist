"""
KÜB PDF Parsing Pipeline — v2.2 (Standart İsimlendirme + Duplicate Kontrolü)

Yapılan iyileştirmeler:
  P0.1 — Metin bloklarını Y koordinatına göre sıralama (kutu/tablo sırası düzeltildi)
  P0.2 — find_tables() ile tablo tespiti ve markdown formatına çevirme
  P0.3 — Madde 1 öncesi özel uyarı bloğu (kara kutu) tespiti ve ayrı chunk olarak kaydı
  P0.4 — Resim bazlı PDF tespiti → ImageBasedPDFError → karantina (Vision OCR DISABLED)
  P0.5 — Section 1'den alınan isim anında normalize edilir (trademark, Türkçe char, uppercase)
  P0.6 — Normalize isim üzerinden duplicate kontrolü (aynı isim = tekrar işleme)

Standart:
  - İlaç adı her zaman Section 1'den gelir ("1. BEŞERİ TIBBİ ÜRÜNÜN ADI")
  - Normalize edilir: trademark kaldır, Türkçe→ASCII, uppercase, whitespace temizle
  - JSON çıktı dosyası normalize isme göre isimlendirilir
  - Aynı normalize isim daha önce işlendiyse → duplicate, atla
"""

import re
import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger
import pymupdf

from .kub_sections import (
    KUB_SECTION_TITLES,
    CRITICAL_SECTIONS,
    IMPORTANT_SECTIONS,
    SECTION_RISK_LEVEL,
)
from .subsection_parser import extract_42_subchunks, extract_44_subchunks
from src.data.normalization import normalize_drug_name


# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------

# Tablo için minimum hücre sayısı — çok küçük "tablolar" atlanır
_MIN_TABLE_CELLS = 4
# Sayfa başına minimum karakter eşiği — altındaysa resim bazlı PDF
_MIN_CHARS_PER_PAGE = 50


# ---------------------------------------------------------------------------
# P0.4 — Resim Bazlı PDF Tespiti
# ---------------------------------------------------------------------------

class ImageBasedPDFError(Exception):
    """PDF metin içermiyor; OCR gerekli."""
    pass


def _check_image_based(doc: pymupdf.Document) -> bool:
    """
    PDF'in tarayıcıdan oluşturulmuş (resim bazlı) olup olmadığını kontrol eder.

    Returns:
        True  → resim bazlı, Vision OCR gerekli
        False → normal metin PDF
    """
    toplam = sum(len(page.get_text().strip()) for page in doc)
    sayfa_basi = toplam / max(len(doc), 1)
    return sayfa_basi < _MIN_CHARS_PER_PAGE


# ---------------------------------------------------------------------------
# P0.1 — Y-Sıralı Metin Okuma
# ---------------------------------------------------------------------------

def _page_text_sorted(page: pymupdf.Page) -> str:
    """
    Sayfadaki metin bloklarını Y koordinatına göre sıralayarak birleştirir.

    Sorun: get_text() metin akışı sırasını kullanır; kare kutular ve
    floating box'lar görsel konumlarından farklı yere düşer.
    Çözüm: 'blocks' modunda koordinatları alıp Y'ye göre sıralamak.
    """
    blocks = page.get_text("blocks")
    # block = (x0, y0, x1, y1, text, block_no, block_type)
    # block_type 0=metin, 1=resim
    text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]
    # Y'yi 5px hassasiyetle yuvarla (aynı satırdaki blokları gruplandrır), sonra X'e göre sırala
    sorted_blocks = sorted(text_blocks, key=lambda b: (round(b[1] / 5) * 5, b[0]))
    return "\n".join(b[4] for b in sorted_blocks)


# ---------------------------------------------------------------------------
# P0.2 — Tablo Tespiti ve Markdown Çevirimi
# ---------------------------------------------------------------------------

def _table_to_markdown(tbl) -> str:
    """
    pymupdf tablo nesnesini GitHub Flavored Markdown tablosuna çevirir.
    Boş veya çok küçük tablolar için boş string döner.
    """
    try:
        data = tbl.extract()
        if not data or tbl.row_count * tbl.col_count < _MIN_TABLE_CELLS:
            return ""

        rows_md = []
        for i, row in enumerate(data):
            cells = [str(c or "").strip().replace("\n", " ") for c in row]
            rows_md.append("| " + " | ".join(cells) + " |")
            if i == 0:
                rows_md.append("|" + "|".join([" --- "] * len(cells)) + "|")

        return "\n".join(rows_md)
    except Exception as e:
        logger.debug(f"Tablo markdown çevirimi başarısız: {e}")
        return ""


def _extract_page_text_with_tables(page: pymupdf.Page) -> str:
    """
    Bir sayfanın metnini Y-sıralı olarak okur; tabloları tespit edip
    markdown formatında yerleştirir.

    Algoritma:
    1. find_tables() ile tablo bounding box'larını ve markdown içeriklerini hazırla
    2. Metin bloklarını Y'ye göre sırala
    3. Tablo bbox'ı içinde kalan metin bloklarını atla (markdown ile zaten temsil ediliyor)
    4. Tablo markdown'ını doğru Y konumuna (ilk tablo bloğunun konumuna) ekle
    """
    # --- Tabloları bul ---
    table_regions: list[dict] = []
    try:
        tab_finder = page.find_tables()
        for tbl in tab_finder.tables:
            md = _table_to_markdown(tbl)
            if md:
                table_regions.append({
                    "bbox": tbl.bbox,       # (x0, y0, x1, y1)
                    "markdown": md,
                    "y_top": tbl.bbox[1],
                })
    except Exception as e:
        logger.debug(f"find_tables başarısız (sayfa atlanıyor): {e}")

    if not table_regions:
        # Tablo yoksa sadece Y-sıralı metin döndür
        return _page_text_sorted(page)

    # --- Metin bloklarını al ---
    blocks = page.get_text("blocks")
    text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]
    sorted_blocks = sorted(text_blocks, key=lambda b: (round(b[1] / 5) * 5, b[0]))

    # --- Hangi bloklar tablo alanında? ---
    def _in_table(bx0: float, by0: float, bx1: float, by1: float) -> Optional[dict]:
        for tr in table_regions:
            tx0, ty0, tx1, ty1 = tr["bbox"]
            # Basit overlap: bloğun merkezi tablo bbox'ı içindeyse
            bcy = (by0 + by1) / 2
            bcx = (bx0 + bx1) / 2
            if ty0 <= bcy <= ty1 and tx0 <= bcx <= tx1:
                return tr
        return None

    # --- Metin + tablo markdown'larını Y sırasına göre birleştir ---
    parts: list[tuple[float, str]] = []   # (y_pos, içerik)
    inserted_tables: set[int] = set()

    for bx0, by0, bx1, by1, text, *_ in sorted_blocks:
        tr = _in_table(bx0, by0, bx1, by1)
        if tr:
            tid = id(tr)
            if tid not in inserted_tables:
                # Tabloyu ilk eşleşen blok konumuna yerleştir
                parts.append((tr["y_top"], tr["markdown"]))
                inserted_tables.add(tid)
            # Bu metin bloğunu atla (tablo markdown'ına dahil)
        else:
            parts.append((by0, text.strip()))

    # Y'ye göre son sıralama
    parts.sort(key=lambda x: x[0])
    return "\n".join(p for _, p in parts if p)


# ---------------------------------------------------------------------------
# Yardımcı Fonksiyonlar
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """Fazla boşlukları ve satır sonlarını temizler."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _clean_chunk_text(text: str) -> str:
    """
    Chunk metninden TİTCK e-imza metadata satırlarını temizler.
    Ayrıca sayfa numarası artefaktlarını (ör: "2/17 \\n") kaldırır.
    """
    # TİTCK e-imza satırları
    text = re.sub(r"Belge\s+Do[ğg]rulama\s+Kodu\s*:\s*\S+", "", text)
    text = re.sub(
        r"Bu\s+belge\s*,?\s*g[üu]venli\s+elektronik\s+imza\s+ile\s+imzalanm[ıi][şs]t[ıi]r\.?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"Belge\s+Tarihi\s*:\s*[\d./]+", "", text)
    text = re.sub(r"Belge\s+Takip\s+Adresi\s*:.*?(?=\n|$)", "", text)
    # Sayfa numarası artefaktları: "2/17" veya "1| 15" gibi
    text = re.sub(r"^\s*\d{1,3}\s*/\s*\d{1,3}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d{1,3}\s*\|\s*\d{1,3}\s*$", "", text, flags=re.MULTILINE)
    # Ardışık boş satırları tek satıra indir
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_etken_madde(full_text: str) -> str:
    """
    KÜB Madde 2'den etkin madde bilgisini çıkarır.

    TİTCK KÜB'lerinde Madde 2 formatı:
      "Etkin madde: <içerik>"   — tek satırlı veya çok satırlı
      "Etkin maddeler: ..."     — kombinasyon ilaçlar

    "Yardımcı maddeler" başlığına kadar olan içerik alınır.
    """
    m = re.search(
        r"etkin\s+madde\w*\s*:?\s*(.{1,600}?)"
        r"(?:yard[ıi]mc[ıi]\s+madde|3\s*\.\s*[A-ZÇĞİÖŞÜ])",
        full_text,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return ""

    raw = m.group(1)
    raw = re.sub(r"\.{3,}", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    if len(raw) < 3:
        return ""
    return raw[:300]


def _extract_drug_name(first_page_text: str) -> str:
    """
    KÜB'ün 1. maddesinden ilaç adını çıkarır.

    Desteklenen formatlar:
      Format 1: "1. BEŞERİ TIBBİ ÜRÜNÜN ADI"   (noktalı, standart TİTCK)
      Format 2: "1\\nBEŞERİ TIBBİ ÜRÜNÜN ADI"  (sayı ayrı satırda — ör: CIPRALEX)
    """
    patterns = [
        re.compile(
            r"1\.\s*BE[ŞS]ER[İI]\s+TIBB[İI]\s+[ÜU]R[ÜU]N[ÜU]N\s+ADI\s*\n+(.+?)(?:\n|$)",
            re.IGNORECASE,
        ),
        re.compile(
            r"^1\s*\n\s*BE[ŞS]ER[İI]\s+TIBB[İI]\s+[ÜU]R[ÜU]N[ÜU]N\s+ADI\s*\n+(.+?)(?:\n|$)",
            re.IGNORECASE | re.MULTILINE,
        ),
    ]
    for pattern in patterns:
        m = pattern.search(first_page_text)
        if m:
            name = m.group(1).strip().split("\n")[0].strip()
            return name[:120]
    return "Bilinmeyen İlaç"


# ---------------------------------------------------------------------------
# P0.3 — Özel Uyarı Bloğu (Kara Kutu) Tespiti
# ---------------------------------------------------------------------------

def _extract_ozel_uyari(
    full_text: str, drug_name: str, source_file: str, total_pages: int,
    kub_parse_date: str = "", kub_pdf_hash: str = ""
) -> Optional[dict]:
    """
    Madde 1'den önce gelen özel uyarı bloğunu tespit eder.

    TİTCK KÜB'lerinde iki tip uyarı görülüyor:
      Tip A — Kare kutu (CONTRAMAL): madde 1 öncesi, çerçeve içinde bullet'lar
      Tip B — UYARI: başlığı (CİPRO): büyük harfli, madde 1 öncesi veya 3-4 arası
      Tip C — ▼ simgesi (ONAXAN): "ek izlemeye tabidir" notu

    Sonuç chunk: madde_no="ozel_uyari", risk_seviyesi="critical"
    """
    # Madde 1'in konumunu bul
    m1 = re.search(
        r"1[\.\s]*\n?\s*BE[ŞS]ER[İI]\s+TIBB[İI]\s+[ÜU]R[ÜU]N[ÜU]N\s+ADI",
        full_text,
        re.IGNORECASE,
    )
    if not m1:
        return None

    onceki = full_text[: m1.start()].strip()

    # "KISA ÜRÜN BİLGİSİ" başlığını çıkar
    onceki = re.sub(
        r"KISA\s+[ÜU]R[ÜU]N\s+B[İI]LG[İI]S[İI]", "", onceki, flags=re.IGNORECASE
    )
    onceki = _clean_chunk_text(onceki)
    onceki = _normalize_text(onceki)

    if len(onceki) < 30:
        return None

    # Uyarı niteliği taşıyor mu?
    uyari_re = re.compile(
        r"(UYARI|DİKKAT|▼|kontrendike|kullanılmamalı|şiddetlenme|ciddi advers)",
        re.IGNORECASE,
    )
    if not uyari_re.search(onceki):
        return None

    chunk_id_raw = f"{drug_name}_ozel_uyari_{source_file}"
    chunk_id = (
        f"{_slugify(drug_name)}_ozel_uyari_"
        f"{hashlib.md5(chunk_id_raw.encode()).hexdigest()[:8]}"
    )

    logger.info(f"  [P0.3] Özel uyarı bloğu bulundu: {len(onceki)} char")
    return {
        "chunk_id": chunk_id,
        "ilac_adi": drug_name,
        "madde_no": "ozel_uyari",
        "madde_baslik": "Özel Uyarılar (Kara Kutu / Ek İzleme)",
        "icerik": onceki,
        "sayfa": 1,
        "kaynak_dosya": source_file,
        "risk_seviyesi": "critical",
        "oncelik": "critical",
        "toplam_sayfa": total_pages,
        "parse_tarihi": datetime.now().isoformat(),
        "kub_parse_date": kub_parse_date,
        "kub_pdf_hash": kub_pdf_hash,
    }


# ---------------------------------------------------------------------------
# P0.1 — Bölüm Tespiti
# ---------------------------------------------------------------------------

def _detect_sections(full_text: str) -> list[dict]:
    """
    KÜB metninden bölüm başlıklarını ve konumlarını tespit eder.

    TİTCK PDF'lerinde karşılaşılan format varyantları:
      1. "4.3 Kontrendikasyonlar"          — standart, tek satır
      2. "4.3. Kontrendikasyonlar"         — noktalı versiyon
      3. "     4.3 Kontrendikasyonlar"     — girintili versiyon
      4. "4.1 \\nTerapötik endikasyonlar"  — başlık sonraki satırda

    Bölüm bütünlüğü: Aynı section_no bir kez kabul edilir.
    Yanlış pozitif filtreleri: referanslar, dozaj sayıları, kısa/sayısal başlıklar.
    """
    patterns = [
        re.compile(
            r"^\s{0,8}(4\.[1-9](?:\.[0-9])?)\s*\.?\s{0,6}([A-ZÇĞİÖŞÜ][^\n]{4,90}?)\s*$",
            re.MULTILINE,
        ),
        re.compile(
            r"^\s{0,4}(4\.[1-9](?:\.[0-9])?)\s*\.?\s*\n\s*([A-ZÇĞİÖŞÜ][^\n]{4,80}?)\s*$",
            re.MULTILINE,
        ),
        re.compile(
            r"^\s{0,4}(5|6|7|8|9|10)\.\s{1,6}([A-ZÇĞİÖŞÜ][^\n]{4,70}?)\s*$",
            re.MULTILINE,
        ),
        re.compile(
            r"^\s{0,4}(5|6|7|8|9|10)\.\s*\n\s*([A-ZÇĞİÖŞÜ][^\n]{4,70}?)\s*$",
            re.MULTILINE,
        ),
        # Tablo hücresi formatı: "| 4.3 Kontrendikasyonlar |" veya "| 4.5. Diğer... |"
        re.compile(
            r"^\|\s*(4\.[1-9](?:\.[0-9])?)\s*\.?\s{0,6}([A-ZÇĞİÖŞÜ][^\n]{4,90}?)\s*\|?\s*$",
            re.MULTILINE,
        ),
        re.compile(
            r"^\|\s*(5|6|7|8|9|10)\.\s{1,6}([A-ZÇĞİÖŞÜ][^\n]{4,70}?)\s*\|?\s*$",
            re.MULTILINE,
        ),
        # Bare section number only (title filled from canonical dict)
        re.compile(
            r"^\s{0,8}(4\.[1-9](?:\.[0-9])?)\s*\.\s*$",
            re.MULTILINE,
        ),
        # OCR artefakt: "4,5." (virgülle hatalı taranmış nokta)
        re.compile(
            r"^\s{0,8}(4,[1-9](?:,[0-9])?)\s*\.?\s{0,6}([A-ZÇĞİÖŞÜ][^\n]{4,90}?)\s*$",
            re.MULTILINE,
        ),
    ]

    found: list[dict] = []
    seen_positions: set[int] = set()

    for pattern in patterns:
        for m in pattern.finditer(full_text):
            pos = m.start()

            if any(abs(pos - p) < 50 for p in seen_positions):
                continue

            section_no = m.group(1).strip().rstrip(".").replace(",", ".")
            title_raw = m.group(2).strip() if len(m.groups()) >= 2 and m.group(2) else ""

            # Referans filtresi: "bkz. 4.3" gibi ifadeleri atla
            surrounding = full_text[max(0, pos - 60) : pos + 5]
            last_nl = surrounding.rfind("\n")
            same_line_ctx = surrounding[last_nl + 1 :] if last_nl >= 0 else surrounding
            _sec_esc = re.escape(section_no)
            _ref_pat = re.compile(
                rf"(bkz|bakınız|see|Bölüm|Madde|Section)\s*\.?\s*{_sec_esc}([^0-9]|$)",
                re.IGNORECASE,
            )
            if _ref_pat.search(same_line_ctx):
                continue

            # Dozaj sayısı filtresi
            if re.match(r"^\d[\d\.,]+\s*(mg|ml|mcg|iu|%|kg)", title_raw, re.IGNORECASE):
                continue

            # Çok kısa veya sayısal başlık — ama canonical varsa geç
            canonical_title = KUB_SECTION_TITLES.get(section_no, title_raw)
            if not title_raw and not canonical_title:
                continue
            if title_raw and (len(title_raw) < 5 or title_raw.isdigit()):
                continue

            # Parantez filtresi (referans metni)
            if ")" in title_raw:
                continue
            found.append({
                "section_no": section_no,
                "title": canonical_title,
                "title_raw": title_raw,
                "start": pos,
            })
            seen_positions.add(pos)

    # Konuma göre sırala, section_no tekrarlarını kaldır (ilk geçen kazanır)
    found.sort(key=lambda x: x["start"])
    seen_nos: set[str] = set()
    deduped: list[dict] = []
    for item in found:
        if item["section_no"] not in seen_nos:
            seen_nos.add(item["section_no"])
            deduped.append(item)

    return deduped


# ---------------------------------------------------------------------------
# Chunk Üretimi
# ---------------------------------------------------------------------------

def _split_into_chunks(
    full_text: str,
    sections: list[dict],
    drug_name: str,
    source_file: str,
    total_pages: int,
    page_offsets: list[int],
    kub_parse_date: str = "",
    kub_pdf_hash: str = "",
) -> list[dict]:
    """
    Tespit edilen bölümlere göre metni chunk'lara böler.

    P0.1 notu: Bu aşamada full_text zaten Y-sıralı ve tablo-markdown'lı
    şekilde gelmiş olmalıdır (_extract_page_text_with_tables ile oluşturulmuş).
    """
    chunks = []

    for i, sec in enumerate(sections):
        start = sec["start"]
        end = sections[i + 1]["start"] if i + 1 < len(sections) else len(full_text)
        content = full_text[start:end]
        content = _normalize_text(content)
        content = _clean_chunk_text(content)

        if len(content) < 20:
            continue

        section_no = sec["section_no"]

        # Sayfa numarasını tahmin et
        page_num = 1
        for p_idx, offset in enumerate(page_offsets):
            if offset <= start:
                page_num = p_idx + 1
            else:
                break

        raw_id = f"{drug_name}_{section_no}_{source_file}"
        chunk_id = hashlib.md5(raw_id.encode()).hexdigest()[:12]
        chunk_id = f"{_slugify(drug_name)}_{section_no.replace('.', '_')}_{chunk_id}"

        chunk = {
            "chunk_id": chunk_id,
            "ilac_adi": drug_name,
            "madde_no": section_no,
            "madde_baslik": sec["title"],
            "icerik": content,
            "sayfa": page_num,
            "kaynak_dosya": source_file,
            "risk_seviyesi": SECTION_RISK_LEVEL.get(section_no, "info"),
            "oncelik": (
                "critical"
                if section_no in CRITICAL_SECTIONS
                else "important"
                if section_no in IMPORTANT_SECTIONS
                else "normal"
            ),
            "toplam_sayfa": total_pages,
            "parse_tarihi": datetime.now().isoformat(),
            "kub_parse_date": kub_parse_date,
            "kub_pdf_hash": kub_pdf_hash,
        }
        chunks.append(chunk)

    return chunks


def _slugify(text: str) -> str:
    """İlaç adını dosya/ID uyumlu formata çevirir."""
    text = text.upper()
    tr_map = str.maketrans("ÇĞİÖŞÜçğışöü", "CGIOSCGIISOU")
    text = text.translate(tr_map)
    text = re.sub(r"[^A-Z0-9]", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:30]


# ---------------------------------------------------------------------------
# Ana Parser Sınıfı
# ---------------------------------------------------------------------------

class KUBParser:
    """
    TİTCK KÜB PDF'lerini parse ederek madde bazlı chunk'lar üretir.

    v2.0 yenilikleri:
      - Metin Y-koordinat sıralaması (kutu/tablo sırası düzeltildi)
      - Tablo → Markdown çevirimi (find_tables)
      - Özel uyarı bloğu (kara kutu) tespiti
      - Resim bazlı PDF tespiti ve ImageBasedPDFError
    """

    def __init__(
        self,
        target_sections: Optional[list[str]] = None,
        use_vision_ocr: bool = False,  # DISABLED: image PDFs go to quarantine, no API calls
    ):
        self.target_sections = target_sections
        self.use_vision_ocr = use_vision_ocr

    def parse(self, pdf_path: str | Path) -> dict:
        """
        Tek bir KÜB PDF'ini parse eder.

        Resim bazlı PDF tespitinde:
          use_vision_ocr=False (default) → ImageBasedPDFError → karantina
          use_vision_ocr=True → Vision OCR (DISABLED, API para harcar)
        """
        pdf_path = Path(pdf_path)
        logger.info(f"Parsing: {pdf_path.name}")

        doc = pymupdf.open(str(pdf_path))
        total_pages = len(doc)

        # --- Task 1: KÜB Versioning Metadata ---
        try:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            kub_pdf_hash = hashlib.sha1(pdf_bytes).hexdigest()[:16]
        except Exception as e:
            logger.error(f"PDF hash hesaplanamadı: {e}")
            kub_pdf_hash = "unknown"

        kub_parse_date = ""
        meta = doc.metadata or {}
        date_str = meta.get("modDate") or meta.get("creationDate") or ""
        if date_str.startswith("D:") and len(date_str) >= 10:
            try:
                year = date_str[2:6]
                month = date_str[6:8]
                day = date_str[8:10]
                kub_parse_date = f"{year}-{month}-{day}"
            except Exception:
                pass
        
        if not kub_parse_date:
            try:
                mtime = os.path.getmtime(pdf_path)
                kub_parse_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            except Exception:
                kub_parse_date = datetime.now().strftime("%Y-%m-%d")

        # P0.4 — Resim bazlı PDF kontrolü
        is_image_based = _check_image_based(doc)

        if is_image_based:
            if not self.use_vision_ocr:
                doc.close()
                raise ImageBasedPDFError(
                    f"PDF resim bazlı ({pdf_path.name}). "
                    f"use_vision_ocr=True ile tekrar deneyin."
                )
            # Vision OCR yolu
            doc.close()
            logger.info(f"  [P0.4] Resim bazlı PDF — Claude Vision OCR devreye giriyor")
            from .vision_ocr import ocr_pdf_to_text
            full_text, page_offsets = ocr_pdf_to_text(pdf_path)

            # OCR sonrası hâlâ boşsa karantinaya al
            if len(full_text.strip()) < 100:
                raise ImageBasedPDFError(
                    f"Vision OCR sonrası yeterli metin çıkarılamadı ({pdf_path.name}). "
                    f"PDF kalitesi çok düşük olabilir."
                )

            # Doc bilgilerini yeniden al (total_pages için)
            doc2 = pymupdf.open(str(pdf_path))
            total_pages = len(doc2)
            doc2.close()

        else:
            # P0.1 + P0.2 — Y-sıralı ve tablo-markdown'lı metin oluştur
            full_text = ""
            page_offsets = []

            for page in doc:
                page_offsets.append(len(full_text))
                page_text = _extract_page_text_with_tables(page)
                full_text += page_text + "\n"

            doc.close()

        # İlaç adı — Section 1'den al, anında normalize et
        drug_name_raw = _extract_drug_name(full_text[:3000])
        etken_madde = _extract_etken_madde(full_text[:5000])
        if drug_name_raw == "Bilinmeyen İlaç":
            drug_name_raw = pdf_path.stem.replace("_", " ")[:50]

        # P0.5: Normalize et (trademark, Türkçe char, uppercase)
        drug_name = normalize_drug_name(drug_name_raw)
        if drug_name != drug_name_raw:
            logger.info(f"İlaç adı normalize edildi: '{drug_name_raw}' → '{drug_name}'")
        else:
            logger.info(f"İlaç adı: {drug_name}")

        # P0.6: Duplicate kontrolü pipeline katmanında (canonical_id + ChromaDB) yapılır.
        # Parser burada kontrol etmez — crash-restart döngülerinde stale JSON'lardan
        # yanlış "duplicate" tespiti yapıyor ve gerçek ilaçları karantinaya düşürüyor.

        # Bölümleri tespit et
        sections = _detect_sections(full_text)
        detected_nos = {s["section_no"] for s in sections}
        logger.info(f"Tespit edilen bölümler: {sorted(detected_nos)}")

        # Fallback: kritik bölümler eksikse _page_text_sorted ile yeniden dene
        if not ({"4.3", "4.5"} <= detected_nos):
            logger.info("  Kritik bölüm eksik — _page_text_sorted fallback deneniyor")
            doc2 = pymupdf.open(str(pdf_path))
            fallback_text = ""
            fallback_offsets: list[int] = []
            for page2 in doc2:
                fallback_offsets.append(len(fallback_text))
                fallback_text += _page_text_sorted(page2) + "\n"
            doc2.close()
            fallback_sections = _detect_sections(fallback_text)
            fallback_nos = {s["section_no"] for s in fallback_sections}
            if len(fallback_nos) > len(detected_nos) or ({"4.3", "4.5"} <= fallback_nos):
                logger.info(f"  Fallback başarılı: {sorted(fallback_nos)}")
                full_text = fallback_text
                page_offsets = fallback_offsets
                sections = fallback_sections
                detected_nos = fallback_nos
            else:
                logger.debug(f"  Fallback fark yaratmadı, orijinal metin kullanılıyor")

        if self.target_sections:
            sections = [s for s in sections if s["section_no"] in self.target_sections]

        # Chunk'lara böl
        chunks = _split_into_chunks(
            full_text, sections, drug_name, pdf_path.name, total_pages, page_offsets,
            kub_parse_date, kub_pdf_hash
        )

        # P0.3 — Özel uyarı bloğunu ekle (varsa)
        ozel_uyari = _extract_ozel_uyari(full_text, drug_name, pdf_path.name, total_pages, kub_parse_date, kub_pdf_hash)
        if ozel_uyari:
            chunks.insert(0, ozel_uyari)

        # 4.2 sub-chunk'ları
        chunk_42 = next((c for c in chunks if c["madde_no"] == "4.2"), None)
        if chunk_42:
            sub_chunks = extract_42_subchunks(chunk_42)
            chunks.extend(sub_chunks)
            if sub_chunks:
                logger.info(f"  + 4.2 sub-chunk: {[s['alt_madde'] for s in sub_chunks]}")

        # 4.4 sub-chunk'ları — büyük Özel Uyarılar bölümlerini parçala
        chunk_44 = next((c for c in chunks if c["madde_no"] == "4.4"), None)
        if chunk_44:
            sub_chunks_44 = extract_44_subchunks(chunk_44)
            chunks.extend(sub_chunks_44)
            if sub_chunks_44:
                logger.info(f"  + 4.4 sub-chunk: {len(sub_chunks_44)} bölüm "
                            f"(orijinal {len(chunk_44['icerik'])} karakter)")

        ozel_uyari_var = any(c["madde_no"] == "ozel_uyari" for c in chunks)
        result = {
            "ilac_adi": drug_name,
            "etken_madde": etken_madde,
            "kaynak_dosya": pdf_path.name,
            "toplam_sayfa": total_pages,
            "chunks": chunks,
            "parse_tarihi": datetime.now().isoformat(),
            "ozet": {
                "toplam_chunk": len(chunks),
                "sub_chunk_sayisi": len([c for c in chunks if "alt_madde" in c]),
                "ozel_uyari_var": ozel_uyari_var,
                "kritik_bolumler": [c["madde_no"] for c in chunks if c["oncelik"] == "critical"],
                "tespit_edilen_bolumler": [s["section_no"] for s in sections],
            },
        }

        logger.info(
            f"✓ {drug_name}: {len(chunks)} chunk "
            f"({'⚠ uyarı bloğu + ' if ozel_uyari_var else ''}"
            f"{result['ozet']['sub_chunk_sayisi']} sub-chunk)"
        )
        return result

    def save_json(self, result: dict, output_path: str | Path) -> None:
        """Parse sonucunu JSON olarak kaydeder."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"Kaydedildi: {output_path}")

    def parse_directory(self, pdf_dir: str | Path, output_dir: str | Path) -> list[dict]:
        """Bir klasördeki tüm KÜB PDF'lerini parse eder."""
        pdf_dir = Path(pdf_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        pdf_files = list(pdf_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning(f"PDF bulunamadı: {pdf_dir}")
            return results

        for pdf_path in pdf_files:
            try:
                result = self.parse(pdf_path)
                slug = _slugify(result["ilac_adi"])
                out_file = output_dir / f"{slug}.json"
                self.save_json(result, out_file)
                results.append(result)
            except ImageBasedPDFError as e:
                logger.warning(f"OCR başarısız / resim kalitesi düşük ({pdf_path.name}): {e}")
            except Exception as e:
                logger.error(f"Hata ({pdf_path.name}): {e}")

        logger.info(f"\n{'='*50}")
        logger.info(f"Toplam {len(results)}/{len(pdf_files)} PDF parse edildi.")
        total_chunks = sum(r["ozet"]["toplam_chunk"] for r in results)
        logger.info(f"Toplam chunk: {total_chunks}")
        return results
