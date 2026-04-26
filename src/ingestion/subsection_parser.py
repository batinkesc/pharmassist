"""
4.2 Pozoloji bölümü için additive sub-chunk üretici.

Strateji:
  - Base 4.2 chunk'ına DOKUNMAZ, sadece ekstra chunk'lar üretir.
  - Her sub-chunk = [4.2 giriş metni] + [alt bölüm içeriği]
  - Böylece RAG hem genel hem de hedefe özel içeriği getirebilir.

Tespit edilen kalıplar (tüm TİTCK PDF varyantları):
  Böbrek yetmezliği        → alt_madde = "bobrek"
  Böbrek/Karaciğer ...     → alt_madde = "bobrek_karaciger"
  Karaciğer yetmezliği     → alt_madde = "karaciger"
  Pediyatrik popülasyon    → alt_madde = "pediyatrik"
  Geriyatrik popülasyon    → alt_madde = "geriyatrik"
"""

import re
import hashlib
from loguru import logger

# ---------------------------------------------------------------------------
# Alt bölüm kalıpları — öncelik sırasına göre (birleşik önce gelir)
# ---------------------------------------------------------------------------
SUBHEADING_PATTERNS = [
    # Birleşik böbrek/karaciğer (A-FERİN gibi PDF'ler)
    {
        "key": "bobrek_karaciger",
        "label": "Böbrek / Karaciğer Yetmezliği",
        "patient_flags": ["renal", "hepatic"],
        "regex": re.compile(
            r"B[oö]brek\s*/\s*Karaci[gğ]er\s+yetmezli[gğ]i",
            re.IGNORECASE,
        ),
    },
    # Böbrek yetmezliği (tek başına)
    {
        "key": "bobrek",
        "label": "Böbrek Yetmezliği",
        "patient_flags": ["renal"],
        "regex": re.compile(
            r"B[oö]brek\s+yetmezli[gğ]i",
            re.IGNORECASE,
        ),
    },
    # Karaciğer yetmezliği
    {
        "key": "karaciger",
        "label": "Karaciğer Yetmezliği",
        "patient_flags": ["hepatic"],
        "regex": re.compile(
            r"Karaci[gğ]er\s+yetmezli[gğ]i",
            re.IGNORECASE,
        ),
    },
    # Pediyatrik
    {
        "key": "pediyatrik",
        "label": "Pediyatrik Popülasyon",
        "patient_flags": ["pediatric"],
        "regex": re.compile(
            r"Pediyatrik\s+pop[uü]lasyon",
            re.IGNORECASE,
        ),
    },
    # Geriyatrik
    {
        "key": "geriyatrik",
        "label": "Geriyatrik Popülasyon",
        "patient_flags": ["geriatric"],
        "regex": re.compile(
            r"Geriyatrik\s+pop[uü]lasyon",
            re.IGNORECASE,
        ),
    },
]

# "Özel popülasyonlar" ara başlığını bul — buraya kadar olan metin = giriş
OZEL_POP_REGEX = re.compile(
    r"[Öo]zel\s+pop[uü]lasyonlara?\s+ili[sş]kin\s+ek\s+bilgiler",
    re.IGNORECASE,
)


def _make_chunk_id(drug_name: str, sub_key: str, source_file: str) -> str:
    raw = f"{drug_name}_4.2_{sub_key}_{source_file}"
    h = hashlib.md5(raw.encode()).hexdigest()[:10]
    slug = re.sub(r"[^A-Z0-9]", "_", drug_name.upper())[:25]
    return f"{slug}_4_2_{sub_key}_{h}"


def _make_44_chunk_id(drug_name: str, part_idx: int, source_file: str) -> str:
    raw = f"{drug_name}_4.4_part{part_idx}_{source_file}"
    h = hashlib.md5(raw.encode()).hexdigest()[:10]
    slug = re.sub(r"[^A-Z0-9]", "_", drug_name.upper())[:25]
    return f"{slug}_4_4_part{part_idx}_{h}"


def extract_42_subchunks(base_chunk: dict) -> list[dict]:
    """
    4.2 base chunk'ından alt popülasyon chunk'larını üretir.

    Args:
        base_chunk: pdf_parser tarafından üretilen 4.2 chunk dict'i

    Returns:
        Ek chunk listesi (base_chunk dahil DEĞİL — sadece ekstralar)
    """
    text = base_chunk["icerik"]
    drug_name = base_chunk["ilac_adi"]
    source_file = base_chunk["kaynak_dosya"]
    base_page = base_chunk["sayfa"]

    # 1. Giriş metnini belirle
    #    "Özel popülasyonlar" ifadesinden önce gelen kısım = genel dozaj girişi
    ozel_match = OZEL_POP_REGEX.search(text)
    if ozel_match:
        intro_text = text[: ozel_match.start()].strip()
        search_text = text[ozel_match.start():]
    else:
        # "Özel popülasyonlar" başlığı yoksa, ilk sub-heading'e kadar giriş
        intro_text = ""
        search_text = text

    # 2. Alt başlık konumlarını bul
    hits: list[dict] = []
    for pat in SUBHEADING_PATTERNS:
        m = pat["regex"].search(search_text)
        if m:
            hits.append({
                "key": pat["key"],
                "label": pat["label"],
                "patient_flags": pat["patient_flags"],
                "pos": m.start(),
                "heading_end": m.end(),
            })

    if not hits:
        logger.debug(f"{drug_name}: 4.2 alt bölüm bulunamadı.")
        return []

    # Konuma göre sırala
    hits.sort(key=lambda x: x["pos"])

    # Birleşik (bobrek_karaciger) varsa ve ayrı böbrek/karaciğer de varsa,
    # ayrıları kaldır (çakışma önleme)
    combined_keys = {h["key"] for h in hits if "_" in h["key"]}
    if "bobrek_karaciger" in combined_keys:
        hits = [h for h in hits if h["key"] not in ("bobrek", "karaciger")]

    # 3. Her hit için sub-chunk üret
    sub_chunks = []
    for i, hit in enumerate(hits):
        start = hit["pos"]
        end = hits[i + 1]["pos"] if i + 1 < len(hits) else len(search_text)
        sub_content = search_text[start:end].strip()

        if len(sub_content) < 30:
            logger.debug(f"  Atlandı (çok kısa): {hit['key']}")
            continue

        # Giriş + sub içerik birleştir
        if intro_text:
            full_content = (
                f"[{base_chunk['madde_baslik']} — {hit['label']}]\n\n"
                f"{intro_text}\n\n"
                f"--- {hit['label']} ---\n"
                f"{sub_content}"
            )
        else:
            full_content = (
                f"[{base_chunk['madde_baslik']} — {hit['label']}]\n\n"
                f"--- {hit['label']} ---\n"
                f"{sub_content}"
            )

        chunk = {
            "chunk_id": _make_chunk_id(drug_name, hit["key"], source_file),
            "ilac_adi": drug_name,
            "madde_no": "4.2",
            "alt_madde": hit["key"],
            "alt_madde_etiketi": hit["label"],
            "madde_baslik": f"Pozoloji ve Uygulama Şekli — {hit['label']}",
            "patient_flags": hit["patient_flags"],
            "icerik": full_content,
            "sayfa": base_page,
            "kaynak_dosya": source_file,
            "risk_seviyesi": "warning",
            "oncelik": "important",
            "toplam_sayfa": base_chunk["toplam_sayfa"],
            "parse_tarihi": base_chunk["parse_tarihi"],
            "ust_chunk_id": base_chunk["chunk_id"],  # base'e referans
        }
        sub_chunks.append(chunk)
        logger.debug(f"  + Sub-chunk: {hit['key']} ({len(sub_content)} karakter)")

    return sub_chunks


# ---------------------------------------------------------------------------
# 4.4 Sub-chunking — paragraf tabanlı bölme
# ---------------------------------------------------------------------------

# 4.4 bölümü bu uzunluğun altındaysa bölmeye gerek yok
_44_SPLIT_THRESHOLD = 2500
# Her sub-chunk'ın hedef maksimum karakter sayısı
_44_MAX_SUB_CHARS = 2200
# Her sub-chunk başına eklenecek bağlam prefix (ilk N karakter)
_44_INTRO_CHARS = 280


def extract_44_subchunks(base_chunk: dict) -> list[dict]:
    """
    4.4 Özel kullanım uyarıları bölümü için paragraf-tabanlı sub-chunk üretici.

    Strateji:
    - 4.4 chunk _44_SPLIT_THRESHOLD karakterden kısaysa bölme — zaten yönetilebilir.
    - Büyük 4.4 chunk'larını paragrafa göre _44_MAX_SUB_CHARS boyutunda parçalara böl.
    - Her sub-chunk'a kısa bağlam prefix (madde girişi) eklenir.
    - Sadece ek sub-chunk'lar döner; base chunk DEĞİŞTİRİLMEZ.

    Neden gerekli?
    - Bazı ilaçlar için 4.4 = 7000–23000 karakter tek monolitik chunk.
    - "Feokromasitoma" gibi nadir klinik durumlar chunk sonunda gömülüyor →
      embedding diğer içeriği temsil ediyor → retrieval başarısız (CR=0).
    - Küçük sub-chunk'lar spesifik koşulların embedding'de öne çıkmasını sağlar.
    """
    from datetime import datetime

    text = base_chunk.get("icerik", "")
    drug_name = base_chunk.get("ilac_adi", "")
    source_file = base_chunk.get("kaynak_dosya", "")
    base_page = base_chunk.get("sayfa", 0)
    madde_baslik = base_chunk.get("madde_baslik", "Özel kullanım uyarıları ve önlemleri")
    toplam_sayfa = base_chunk.get("toplam_sayfa", 0)
    parse_tarihi = base_chunk.get("parse_tarihi", datetime.now().isoformat())
    base_chunk_id = base_chunk.get("chunk_id", "")

    if len(text) <= _44_SPLIT_THRESHOLD:
        logger.debug(f"{drug_name}: 4.4 kısa ({len(text)} karakter) — bölme atlandı.")
        return []

    # ── Intro prefix ────────────────────────────────────────────────────────
    # İlk paragrafı veya ilk _44_INTRO_CHARS karakteri intro olarak al
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    if not paragraphs:
        return []

    # Intro: ilk paragraf ya da ilk _44_INTRO_CHARS karakter
    intro_text = paragraphs[0][:_44_INTRO_CHARS]
    content_paragraphs = paragraphs[1:] if len(paragraphs) > 1 else paragraphs

    # ── Paragrafları gruplara böl ───────────────────────────────────────────
    groups: list[list[str]] = []
    current: list[str] = []
    current_size = 0

    for para in content_paragraphs:
        para_len = len(para)
        if current_size + para_len > _44_MAX_SUB_CHARS and current:
            groups.append(current)
            current = [para]
            current_size = para_len
        else:
            current.append(para)
            current_size += para_len

    if current:
        groups.append(current)

    if len(groups) <= 1:
        logger.debug(f"{drug_name}: 4.4 bölme sonucu tek grup — atlandı.")
        return []

    # ── Sub-chunk üret ──────────────────────────────────────────────────────
    sub_chunks: list[dict] = []
    total = len(groups)

    for idx, group in enumerate(groups, 1):
        content = "\n\n".join(group).strip()
        if len(content) < 50:
            logger.debug(f"  Atlandı (çok kısa): part{idx}")
            continue

        full_content = (
            f"[{madde_baslik} — Bölüm {idx}/{total}]\n\n"
            f"[Bağlam — Madde 4.4 girişi]: {intro_text}\n\n"
            f"--- Devam (Bölüm {idx}/{total}) ---\n"
            f"{content}"
        )

        chunk = {
            "chunk_id":          _make_44_chunk_id(drug_name, idx, source_file),
            "ilac_adi":          drug_name,
            "madde_no":          "4.4",
            "alt_madde":         f"part{idx}",
            "alt_madde_etiketi": f"Özel Uyarılar — Bölüm {idx}/{total}",
            "madde_baslik":      f"{madde_baslik} — Bölüm {idx}/{total}",
            "patient_flags":     [],
            "icerik":            full_content,
            "sayfa":             base_page,
            "kaynak_dosya":      source_file,
            "risk_seviyesi":     "warning",
            "oncelik":           "important",
            "toplam_sayfa":      toplam_sayfa,
            "parse_tarihi":      parse_tarihi,
            "ust_chunk_id":      base_chunk_id,
        }
        sub_chunks.append(chunk)
        logger.debug(f"  + 4.4 sub-chunk: part{idx} ({len(content)} karakter)")

    if sub_chunks:
        logger.info(f"{drug_name}: 4.4 bölündü → {len(sub_chunks)} sub-chunk "
                    f"(orijinal: {len(text)} karakter)")
    return sub_chunks
