"""
KÜB JSON → Neo4j graf yükleyici.

Her ilaç JSON dosyasından:
  - Drug node oluşturur
  - Her KÜB bölümü için Section node oluşturur + HAS_SECTION ilişkisi
  - 4.3 (kontrendikasyon) bölümünden Condition node + CONTRAINDICATED_FOR ilişkisi çıkarır
  - 4.5 (etkileşim) bölümünden Drug-INTERACTS_WITH-Drug ilişkisi çıkarır
  - 4.4 (uyarı) bölümünden Warning node + HAS_WARNING ilişkisi çıkarır
"""

import json
import re
from pathlib import Path
from loguru import logger

from src.graph.neo4j_client import run_query


# ---------------------------------------------------------------------------
# Severity çıkarma — KÜB 4.5 metin bağlamına göre
# ---------------------------------------------------------------------------

# Anahtar kelime → severity seviyesi (öncelik sırasıyla kontrol edilir)
_SEVERITY_RULES: list[tuple[str, list[str]]] = [
    ("contraindicated", [
        "kontrendike", "kontrendikedir", "kullanılmamalıdır", "verilmemelidir",
        "kullanılması önerilmez", "kesinlikle önerilmez", "birlikte kullanımından kaçınılmalıdır",
        "birlikte kullanılmamalıdır", "birlikte verilmemelidir",
    ]),
    ("severe", [
        "ciddi etkileşim", "hayatı tehdit", "ölümcül", "tehlikeli kombinasyon",
        "şiddetli", "yoğun bakım", "kardiyak arrest", "serotonin sendromu",
        "kanama riski önemli ölçüde artar", "ciddi kanama",
    ]),
    ("moderate", [
        "dikkatli olunmalıdır", "dikkatli kullanılmalıdır", "dikkatle kullanılmalıdır",
        "yakın izlem", "yakından izlenmelidir", "doz ayarı gerekebilir",
        "doz azaltılmalıdır", "doz düzenlemesi", "yakın takip",
        "kan düzeyi izlenmelidir", "düzeyi artabilir", "düzeyi azalabilir",
        "etkisi artabilir", "etkisi azalabilir", "etkisi güçlenebilir",
        "etkisi potansiyalize", "biyoyararlanımı artar", "biyoyararlanımı azalır",
        "konsantrasyonu artabilir", "konsantrasyonu azalabilir",
    ]),
    ("mild", [
        "klinik önemi sınırlı", "klinik açıdan önemsiz", "minimal etkileşim",
        "önemsiz etkileşim", "hafif düzeyde", "hafif artış",
        "klinik önemi bilinmemektedir",
    ]),
]


def _extract_severity(text: str, mention: str, window_size: int = 1500) -> str:
    """
    KÜB 4.5 metninde mention (ilaç adı / INN) çevresindeki ±window_size karakterlik
    pencereye bakarak etkileşim şiddetini çıkarır.

    Dönüş: 'contraindicated' | 'severe' | 'moderate' | 'mild' | 'unknown'
    """
    if not text or not mention:
        return "unknown"

    # mention etrafında ±window_size karakter pencere al (lowercase)
    lower_text = text.lower()
    lower_mention = mention.lower()
    idx = lower_text.find(lower_mention)
    if idx == -1:
        # Mention bulunamadı — tüm metni tara
        window = lower_text
    else:
        start = max(0, idx - window_size)
        end = min(len(lower_text), idx + len(lower_mention) + window_size)
        window = lower_text[start:end]

    for severity, keywords in _SEVERITY_RULES:
        if any(kw in window for kw in keywords):
            return severity

    return "unknown"


# ---------------------------------------------------------------------------
# İlaç etkileşimi çıkarma için basit regex'ler
# ---------------------------------------------------------------------------

# İlaç adı gibi görünen büyük harfle başlayan kelimeleri yakala (≥5 karakter).
# Lookahead: "ile", "birlikte" vb. AYRI KELİME olarak (boşluk zorunlu — "Chamom"+"ile" tuzağı önlenir).
DRUG_MENTION_RE = re.compile(
    r"\b([A-ZÇĞİÖŞÜ][a-zA-ZçğışöüÇĞİÖŞÜ]{4,}(?:[\s-][A-Za-zçğışöüÇĞİÖŞÜ]{5,})?)"
    r"(?=\s+(?:ile|birlikte|etkileşim|inhibitör|antagonist)\b)",
)

# Bu terimler ilaç adı değil — eşleşse de DrugMention oluşturma
_DRUG_MENTION_STOPWORDS = {
    "etkileşim", "etkileşimler", "etkileşimde", "etkileşimi",
    "inhibisyonu", "inhibisyon", "indüksiyonu", "indüksiyon",
    "bitkisel", "enzim", "mekanizma", "mekanizmayla",
    "tıbbi", "ürünler", "yoluyla",
    "potansiyel", "klinik", "sistemik", "metabolizma",
    "plazma", "konsantrasyon", "biyoyararlanım", "absorbsiyon",
    # Türkçe fiil/isim ekleri alan kelimeler — asla ilaç adı değil
    "birlikte", "kullanımı", "kullanımda", "kullanılması",
    "uygulanması", "uygulanırken", "tedavisinde", "tedavisinde",
    "hastalarda", "hastalarda", "kombinasyonu", "kombinasyonunda",
    "eşzamanlı", "önerilmez", "önerilmemektedir", "bildirilmiştir",
    "artırabilir", "azaltabilir", "değiştirebilir", "etkileyebilir",
}

# Kontrendikasyon için durum/koşul çıkarma
CONDITION_RE = re.compile(
    r"(böbrek\s+yetmezli[gğ]i|karaci[gğ]er\s+yetmezli[gğ]i|gebelik|laktasyon"
    r"|penisilin\s+alerjisi|hipersensitivite|hipertansiyon|diyabet"
    r"|pediyatrik|geriyatrik|[a-zçğışöüA-Z]+\s+alerjisi)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Ana yükleme fonksiyonları
# ---------------------------------------------------------------------------

def load_drug_from_json(json_path: Path) -> tuple[str, str, str, list[dict]]:
    """JSON dosyasını yükler. (ilac_adi, kaynak_dosya, etken_madde, chunks) döner."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    ilac_adi     = data.get("ilac_adi", json_path.stem)
    kaynak_dosya = data.get("kaynak_dosya", json_path.name)
    etken_madde  = data.get("etken_madde", "")
    chunks       = data.get("chunks", [])
    return ilac_adi, kaynak_dosya, etken_madde, chunks


def upsert_drug_node(
    ilac_adi: str,
    kaynak_dosya: str,
    etken_madde: str = "",
    canonical_id: str = "",
) -> None:
    """
    Drug node oluşturur veya günceller.
    canonical_id: DrugIdentity'den gelir — tüm depolarda aynı birincil anahtar.
    """
    run_query(
        """
        MERGE (d:Drug {name: $name})
        ON CREATE SET d.kaynak_dosya  = $kaynak_dosya,
                      d.etken_madde   = $etken_madde,
                      d.canonical_id  = $canonical_id,
                      d.created_at    = timestamp()
        ON MATCH  SET d.kaynak_dosya  = $kaynak_dosya,
                      d.etken_madde   = $etken_madde,
                      d.canonical_id  = $canonical_id
        """,
        {
            "name": ilac_adi,
            "kaynak_dosya": kaynak_dosya,
            "etken_madde": etken_madde,
            "canonical_id": canonical_id,
        },
    )


def upsert_section_node(ilac_adi: str, chunk: dict) -> None:
    """Section node ve Drug→Section ilişkisi oluşturur."""
    section_id = chunk["chunk_id"]
    run_query(
        """
        MERGE (s:Section {section_id: $section_id})
        ON CREATE SET s.madde_no     = $madde_no,
                      s.madde_baslik = $madde_baslik,
                      s.alt_madde   = $alt_madde,
                      s.icerik      = $icerik,
                      s.sayfa       = $sayfa,
                      s.risk_seviyesi = $risk_seviyesi
        ON MATCH  SET s.icerik = $icerik

        WITH s
        MATCH (d:Drug {name: $ilac_adi})
        MERGE (d)-[:HAS_SECTION]->(s)
        """,
        {
            "section_id": section_id,
            "madde_no":   chunk.get("madde_no", ""),
            "madde_baslik": chunk.get("madde_baslik", ""),
            "alt_madde":  chunk.get("alt_madde", ""),
            "icerik":     chunk.get("icerik", ""),  # Tam içerik — ContentPolicy kırpma yok
            "sayfa":      chunk.get("sayfa", 0),
            "risk_seviyesi": chunk.get("risk_seviyesi", "standard"),
            "ilac_adi":   ilac_adi,
        },
    )


def extract_contraindications(ilac_adi: str, chunk: dict) -> None:
    """4.3 bölümünden kontrendikasyon condition'larını çıkarır."""
    icerik = chunk.get("icerik", "")
    kosullar = CONDITION_RE.findall(icerik)

    for kosul in set(kosullar):
        kosul = kosul.strip().lower()
        if len(kosul) < 4:
            continue
        run_query(
            """
            MERGE (c:Condition {name: $kosul})
            WITH c
            MATCH (d:Drug {name: $ilac_adi})
            MERGE (d)-[r:CONTRAINDICATED_FOR]->(c)
            ON CREATE SET r.kaynak_madde = '4.3',
                          r.kaynak_chunk = $chunk_id
            """,
            {"kosul": kosul, "ilac_adi": ilac_adi, "chunk_id": chunk["chunk_id"]},
        )

    if kosullar:
        logger.debug(f"  {ilac_adi} 4.3 → {len(set(kosullar))} kontrendikasyon condition")


def extract_interactions(ilac_adi: str, chunk: dict) -> None:
    """4.5 bölümünden büyük harfli marka adı eşleşmeleriyle INTERACTS_WITH oluşturur.

    Jenerik (küçük harfli) INN eşleşmeleri build_interacts_with_from_sections() tarafından
    toplu cross-reference yöntemiyle işlenir — bu fonksiyon yalnızca DRUG_MENTION_RE kapsamını üstlenir.
    """
    icerik = chunk.get("icerik", "")
    anlasilan_ilaclar = DRUG_MENTION_RE.findall(icerik)

    ilac_kisa = ilac_adi.split()[0].lower() if ilac_adi else ""

    anlasilan_ilaclar = [
        i.strip() for i in anlasilan_ilaclar
        if len(i.strip()) > 4
        and i.strip().lower() not in ilac_adi.lower()
        and ilac_kisa not in i.strip().lower()
        and not i.strip().lower().endswith(" ile")
        and i.strip().lower() not in _DRUG_MENTION_STOPWORDS
        and len(i.strip().split()[-1]) >= 4
    ]

    for diger_ilac in set(anlasilan_ilaclar[:10]):
        severity = _extract_severity(icerik, diger_ilac)
        run_query(
            """
            MATCH (d:Drug {name: $ilac_adi})

            OPTIONAL MATCH (real:Drug)
            WHERE (
                toLower(coalesce(real.etken_madde, '')) CONTAINS toLower($diger_ilac)
                OR toLower(real.name) CONTAINS toLower($diger_ilac)
            )
            AND real.name <> $ilac_adi

            WITH d, real, $diger_ilac AS mention_name, $chunk_id AS cid, $severity AS sev

            FOREACH (_ IN CASE WHEN real IS NOT NULL THEN [1] ELSE [] END |
                MERGE (d)-[r:INTERACTS_WITH]->(real)
                ON CREATE SET r.kaynak_madde = '4.5',
                              r.kaynak_chunk = cid,
                              r.severity     = sev
                ON MATCH  SET r.severity     = CASE WHEN r.severity = 'unknown' THEN sev ELSE r.severity END
            )

            FOREACH (_ IN CASE WHEN real IS NULL THEN [1] ELSE [] END |
                MERGE (m:DrugMention {name: mention_name})
                MERGE (d)-[r2:MENTIONS_INTERACTION]->(m)
                ON CREATE SET r2.kaynak_madde = '4.5',
                              r2.kaynak_chunk = cid
            )
            """,
            {
                "ilac_adi":   ilac_adi,
                "diger_ilac": diger_ilac,
                "chunk_id":   chunk["chunk_id"],
                "severity":   severity,
            },
        )

    if anlasilan_ilaclar:
        logger.debug(f"  {ilac_adi} 4.5 → {len(set(anlasilan_ilaclar))} etkileşim ilaç")


def extract_warnings(ilac_adi: str, chunk: dict) -> None:
    """4.4 bölümünden Warning node'ları oluşturur."""
    icerik = chunk.get("icerik", "")
    # 4.4'ün ilk 300 karakterini uyarı özeti olarak sakla
    ozet = icerik[:300].strip()
    if not ozet:
        return

    run_query(
        """
        MERGE (w:Warning {chunk_id: $chunk_id})
        ON CREATE SET w.ozet     = $ozet,
                      w.ilac_adi = $ilac_adi
        WITH w
        MATCH (d:Drug {name: $ilac_adi})
        MERGE (d)-[:HAS_WARNING]->(w)
        """,
        {"chunk_id": chunk["chunk_id"], "ozet": ozet, "ilac_adi": ilac_adi},
    )


# ---------------------------------------------------------------------------
# INN cross-reference — jenerik etken madde eşleşmesi
# ---------------------------------------------------------------------------

# etken_madde metninde ilaç adı OLMAYAN kelimeler (kimyasal form / birim / Türkçe dolgu)
_INN_SKIP = {
    # Kimyasal tuz/form ekleri
    "dihidrat", "monohidrat", "trihidrat", "seskihidrat",
    "sodyum", "potasyum", "kalsiyum", "magnezyum",
    "maleat", "tartarat", "hidroklorür", "hidroklorid", "fosfat", "sitrat",
    "besilat", "fumarat", "sülfat", "oksalat", "glukonat", "hidrojen",
    "nitrat", "asetat", "laktat", "bromir", "klorür",
    # Doz birimleri ve sayı kalıpları
    "milligram", "mikrogram", "miligram", "millilitre",
    # Türkçe dolgu kelimeler
    "eşdeğer", "içerir", "içinde", "içindeki", "içeren", "içerisinde",
    "içermektedir", "içermekte", "içeriğind", "içeriğinde",
    "olarak", "kaynakl", "katkı", "üretilen", "üretilmiş",
    "kullanıma", "kullanım",
    "maddesi", "tablette", "tabletinde", "kapsülde",
    "çözelti", "çözeltinin", "süspansiyon", "enjeksiyon", "enjeksiyonluk",
    "kullanılmaktadır", "kullanılmakta", "kullanılma", "kullanılm",
    "birlikte", "kullanımı", "tedavisi", "kombinasyonu",
    "üretiminde", "hammadde", "sütünden", "elde", "edilen",
    "miktarda", "edilmektedir", "mukozasından",
    # Biyolojik üretim süreçleri
    "intestinal", "türetilen", "alkalin", "depolimerizasyonu",
    "rekombinant", "teknolojisi",
    # İngilizce / Latince
    "equivalent", "anhydrous", "hydrate", "sodium", "calcium", "escherichi",
}


def _inn_tokens(etken_madde: str) -> list[str]:
    """
    Etken madde metninden INN bazlı eşleşme tokenları çıkarır.

    Strateji:
      - Sadece harf karakterlerinden oluşan, ≥ 7 karakter kelimeleri al
      - Kimyasal form / birim / dolgu kelimelerini atla
      - Her kelime için Türkçe çekim eki soyulmuş (-1 char) versiyonu da ekle
        ("klopidogrele" → "klopidogrel" — bu 4.5 metninde geçen base formdur)
      - Prefix deduplication: uzun varsa kısa olanı tut

    Örnek:
      "klopidogrele eşdeğer klopidogrel hidrojen sülfat" → ["klopidogrel"]
      "varfarin sodyum 10 mg"                           → ["varfarin"]
      "Parasetamol 500 mg Klorfeniramin maleat 4 mg"    → ["parasetamol", "klorfeniramin"]
    """
    if not etken_madde:
        return []

    _TURKISH_VOWELS = set("aeıioöuüAEIİOÖUÜ")
    # İlk 120 karakter: INN adı her zaman ilk cümlede — kaynak/üretim gürültüsü kesilir
    etken_madde = etken_madde[:120]
    # Minimum 8 karakter: kısa Türkçe kelimelerin yanlış eşleşmesini önler
    raw_words = re.findall(r'[a-zA-ZçğışöüÇĞİÖŞÜ]{8,}', etken_madde)
    pool: set[str] = set()

    for w in raw_words:
        w_lower = w.lower()
        if w_lower in _INN_SKIP:
            continue
        pool.add(w_lower)
        # Sadece ünlü ile biten kelimelerde Türkçe çekim eki soy:
        #   klopidogrele (-e dative eki) → klopidogrel  ✓
        #   varfarin      (-n, ek değil) → atla          ✓
        if w_lower[-1] in _TURKISH_VOWELS:
            stripped = w_lower[:-1]
            if len(stripped) >= 8:
                pool.add(stripped)

    # Prefix deduplication: uzun form kısa formla başlıyorsa uzunu çıkar.
    # {"klopidogrele", "klopidogrel"} → {"klopidogrel"}
    result = [tok for tok in pool
              if not any(other != tok and tok.startswith(other) for other in pool)]

    result.sort(key=len)
    return result[:5]


def build_interacts_with_from_sections(parsed_dir: str = "data/parsed_json") -> None:
    """
    Post-processing: JSON 4.5 metinleri × etken_madde cross-reference.

    Her Drug A'nın 4.5 bölümünde Drug B'nin INN tokenlarından herhangi biri
    geçiyorsa INTERACTS_WITH ilişkisi oluşturur.

    Bu fonksiyon extract_interactions() ile tamamlayıcıdır:
      - extract_interactions: büyük harfli marka adı eşleşmeleri
      - bu fonksiyon:         küçük harfli jenerik INN eşleşmeleri
    """
    json_files = list(Path(parsed_dir).glob("*.json"))

    # İlaç adı → INN tokenlar
    drug_tokens: dict[str, list[str]] = {}
    # İlaç adı → 4.5 metni (lowercase)
    drug_45_texts: dict[str, str] = {}

    for jf in json_files:
        data = json.loads(jf.read_text(encoding="utf-8"))
        ilac = data.get("ilac_adi", "")
        etken = data.get("etken_madde", "")

        tokens = _inn_tokens(etken)
        if tokens:
            drug_tokens[ilac] = tokens

        for chunk in data.get("chunks", []):
            if chunk.get("madde_no") == "4.5":
                drug_45_texts[ilac] = chunk.get("icerik", "").lower()
                break

    logger.info(
        f"INN cross-reference: {len(drug_45_texts)} 4.5 metin "
        f"× {len(drug_tokens)} etken madde token seti"
    )

    created = 0
    for drug_a, text_a in drug_45_texts.items():
        for drug_b, tokens_b in drug_tokens.items():
            if drug_a == drug_b:
                continue
            # Eşleşen token'lardan ilkini severity tespiti için kullan
            matched_tok = next((tok for tok in tokens_b if tok in text_a), None)
            if matched_tok is None:
                continue
            severity = _extract_severity(text_a, matched_tok)
            run_query(
                """
                MATCH (a:Drug {name: $drug_a})
                MATCH (b:Drug {name: $drug_b})
                MERGE (a)-[r:INTERACTS_WITH]->(b)
                ON CREATE SET r.kaynak_madde = '4.5',
                              r.severity     = $severity,
                              r.kaynak       = 'inn_xref'
                ON MATCH  SET r.severity     = CASE WHEN r.severity = 'unknown' THEN $severity ELSE r.severity END
                """,
                {"drug_a": drug_a, "drug_b": drug_b, "severity": severity},
            )
            created += 1

    logger.info(f"INN cross-reference → {created} INTERACTS_WITH ilişkisi oluşturuldu/güncellendi.")


# ---------------------------------------------------------------------------
# Toplu yükleme
# ---------------------------------------------------------------------------

def load_all_drugs(parsed_dir: str = "data/parsed_json", reset: bool = False) -> None:
    """
    data/parsed_json/ altındaki tüm JSON'ları Neo4j'e yükler.

    Args:
        parsed_dir: JSON dosyalarının bulunduğu dizin
        reset:      True ise önce tüm veriyi siler
    """
    from src.graph.schema_builder import build_schema, drop_all_data

    if reset:
        drop_all_data()

    build_schema()

    json_files = list(Path(parsed_dir).glob("*.json"))
    logger.info(f"{len(json_files)} JSON dosyası yüklenecek...")

    for json_path in json_files:
        ilac_adi, kaynak, etken_madde, chunks = load_drug_from_json(json_path)
        if not chunks:
            continue

        logger.info(f"Yükleniyor: {ilac_adi} ({len(chunks)} chunk)")
        upsert_drug_node(ilac_adi, kaynak, etken_madde)

        for chunk in chunks:
            upsert_section_node(ilac_adi, chunk)
            madde = chunk.get("madde_no", "")
            if madde == "4.3":
                extract_contraindications(ilac_adi, chunk)
            elif madde == "4.5":
                extract_interactions(ilac_adi, chunk)
            elif madde == "4.4":
                extract_warnings(ilac_adi, chunk)

    logger.info("Tüm ilaçlar Neo4j'e yüklendi.")

    # Post-processing: jenerik INN cross-reference (INTERACTS_WITH tamamlama)
    build_interacts_with_from_sections(parsed_dir)
    logger.info("✓ Dalga 3 graf yüklemesi tamamlandı.")
