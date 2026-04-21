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
