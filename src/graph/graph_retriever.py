"""
Neo4j graf sorgu katmanı — CombiGraph retrieval.

Fonksiyonlar:
  ilac_node_adlari_bul(sorgu_adi)     → Neo4j'deki gerçek node adı/adlarını döner
  drug_interactions(ilac_adi)         → ilaçın bilinen etkileşimleri
  drug_contraindications(ilac_adi)    → kontrendikasyon condition listesi
  multi_drug_interactions(ilaclar)    → çoklu ilaç kombinasyon kontrolü
  drugs_for_condition(kosul)          → bir durumda kontrendike ilaçlar
  drug_summary(ilac_adi)              → node özet bilgisi
"""

from src.graph.neo4j_client import run_query
from loguru import logger


def ilac_node_adlari_bul(sorgu_adi: str) -> list[str]:
    """
    Kullanıcı/sorgu ilaç adını Neo4j'deki gerçek Drug node adlarına çevirir.

    Arama sırası:
      1. NameResolver (canonical_id → display_name yoluyla Neo4j sorgusu)
      2. canonical_id doğrudan Neo4j eşleşmesi
      3. Prefix fallback (NameResolver bulamazsa)
      4. Contains fallback (son çare)

    NameResolver tüm fuzzy mantığını merkezileştirdiğinden bu fonksiyon
    artık sadece Neo4j'de mevcut node adlarını döndürür.
    """
    # 1. NameResolver — canonical_id üzerinden
    try:
        from src.core.name_resolver import get_resolver
        resolver = get_resolver()
        matches = resolver.resolve(sorgu_adi)
        if matches:
            # canonical_id'ye göre Neo4j'de ara
            cids = [m.canonical_id for m in matches]
            sonuc = run_query(
                "MATCH (d:Drug) WHERE d.canonical_id IN $cids RETURN d.name AS n",
                {"cids": cids},
            )
            if sonuc:
                return [r["n"] for r in sonuc]
            # canonical_id Neo4j'de yoksa display_name ile dene
            display_names = [m.display_name for m in matches]
            sonuc = run_query(
                "MATCH (d:Drug) WHERE d.name IN $names RETURN d.name AS n",
                {"names": display_names},
            )
            if sonuc:
                return [r["n"] for r in sonuc]
    except Exception as e:
        logger.debug(f"NameResolver Neo4j lookup hatası: {e}")

    # 2. Exact match (NameResolver bulamadıysa)
    sonuc = run_query(
        "MATCH (d:Drug) WHERE d.name = $n RETURN d.name AS n",
        {"n": sorgu_adi},
    )
    if sonuc:
        return [r["n"] for r in sonuc]

    # 3. Prefix fallback
    temiz = sorgu_adi.upper().split()[0]
    sonuc = run_query(
        "MATCH (d:Drug) WHERE toUpper(d.name) STARTS WITH $n RETURN d.name AS n",
        {"n": temiz},
    )
    if sonuc:
        return [r["n"] for r in sonuc]

    # 4. Contains fallback
    sonuc = run_query(
        "MATCH (d:Drug) WHERE toLower(d.name) CONTAINS toLower($n) RETURN d.name AS n",
        {"n": sorgu_adi},
    )
    return [r["n"] for r in sonuc]


def _resolve_ilaclar(ilaclar: list[str]) -> list[str]:
    """
    Kısa ilaç adları listesini Neo4j gerçek node adlarına çevirir.
    Bulunamayanları atlar, bulunanları düz liste olarak döner.
    """
    gercek_adlar = []
    for ilac in ilaclar:
        bulunanlar = ilac_node_adlari_bul(ilac)
        if bulunanlar:
            gercek_adlar.extend(bulunanlar)
        else:
            logger.debug(f"Graf: '{ilac}' için node bulunamadı, atlandı")
    return list(dict.fromkeys(gercek_adlar))  # sırayı koruyarak tekrarları kaldır


def drug_interactions(ilac_adi: str) -> list[dict]:
    """
    Bir ilacın Neo4j'deki etkileşim listesini döner.
    Hem gerçek Drug node'larıyla (INTERACTS_WITH) hem de
    metinden çıkarılan DrugMention node'larıyla (MENTIONS_INTERACTION) eşleşmeleri içerir.
    """
    gercek_adlar = ilac_node_adlari_bul(ilac_adi)
    if not gercek_adlar:
        logger.debug(f"drug_interactions: '{ilac_adi}' için node yok")
        return []

    logger.debug(f"drug_interactions: '{ilac_adi}' → {gercek_adlar}")
    # İki ayrı sorgu — collect() + tek büyük OOM önlemek için LIMIT intermediate'de uygulanır
    real_rows = run_query(
        """
        MATCH (d:Drug)
        WHERE d.name IN $adlar
        MATCH (d)-[r1:INTERACTS_WITH]->(real:Drug)
        RETURN real.name    AS etkilesen_ilac,
               r1.severity  AS siddet,
               r1.kaynak_madde AS kaynak,
               'dogrulandi' AS tip
        ORDER BY
          CASE r1.severity
            WHEN 'contraindicated' THEN 0
            WHEN 'severe'          THEN 1
            WHEN 'moderate'        THEN 2
            WHEN 'mild'            THEN 3
            ELSE                        4
          END
        LIMIT 60
        """,
        {"adlar": gercek_adlar},
    )
    mention_rows = run_query(
        """
        MATCH (d:Drug)
        WHERE d.name IN $adlar
        MATCH (d)-[r2:MENTIONS_INTERACTION]->(mention:DrugMention)
        RETURN mention.name    AS etkilesen_ilac,
               'unknown'       AS siddet,
               r2.kaynak_madde AS kaynak,
               'metin'         AS tip
        LIMIT 60
        """,
        {"adlar": gercek_adlar},
    )
    # Birleştir, tekrarları çıkar, doğrulanmış önce
    seen: set[str] = set()
    merged: list[dict] = []
    for row in real_rows + mention_rows:
        key = (row.get("etkilesen_ilac") or "").strip()
        if key and key not in seen:
            seen.add(key)
            merged.append(row)
    return merged[:100]


def drug_contraindications(ilac_adi: str) -> list[dict]:
    """Bir ilacın kontrendike olduğu durumları döner."""
    gercek_adlar = ilac_node_adlari_bul(ilac_adi)
    if not gercek_adlar:
        logger.debug(f"drug_contraindications: '{ilac_adi}' için node yok")
        return []

    logger.debug(f"drug_contraindications: '{ilac_adi}' → {gercek_adlar}")
    return run_query(
        """
        MATCH (d:Drug)-[r:CONTRAINDICATED_FOR]->(c:Condition)
        WHERE d.name IN $adlar
        RETURN c.name AS kosul, r.kaynak_chunk AS kaynak
        ORDER BY c.name
        """,
        {"adlar": gercek_adlar},
    )


def multi_drug_interactions(ilaclar: list[str]) -> list[dict]:
    """
    Verilen ilaç listesi içinde birbirleriyle etkileşen çiftleri döner.
    Hasta profili üzerindeki mevcut ilaçlar için kombinasyon kontrolü.
    """
    gercek_adlar = _resolve_ilaclar(ilaclar)
    if len(gercek_adlar) < 2:
        return []

    logger.debug(f"multi_drug_interactions: {len(ilaclar)} giriş → {len(gercek_adlar)} node")
    return run_query(
        """
        MATCH (a:Drug)-[r:INTERACTS_WITH]->(b:Drug)
        WHERE a.name IN $adlar AND b.name IN $adlar
        RETURN a.name AS ilac_a, b.name AS ilac_b,
               r.severity AS siddet, r.kaynak_madde AS kaynak
        """,
        {"adlar": gercek_adlar},
    )


def drugs_for_condition(kosul: str) -> list[dict]:
    """Belirtilen durumda kontrendike olan ilaçları döner."""
    return run_query(
        """
        MATCH (d:Drug)-[r:CONTRAINDICATED_FOR]->(c:Condition)
        WHERE toLower(c.name) CONTAINS toLower($kosul)
        RETURN d.name AS ilac, c.name AS kosul, r.kaynak_chunk AS kaynak
        ORDER BY d.name
        """,
        {"kosul": kosul},
    )


def drug_summary(ilac_adi: str) -> dict | None:
    """Drug node'u ve bağlı section sayılarını döner."""
    gercek_adlar = ilac_node_adlari_bul(ilac_adi)
    if not gercek_adlar:
        return None

    results = run_query(
        """
        MATCH (d:Drug)
        WHERE d.name IN $adlar
        OPTIONAL MATCH (d)-[:HAS_SECTION]->(s:Section)
        OPTIONAL MATCH (d)-[:INTERACTS_WITH]->(other:Drug)
        OPTIONAL MATCH (d)-[:CONTRAINDICATED_FOR]->(c:Condition)
        RETURN d.name          AS ilac_adi,
               d.kaynak_dosya  AS kaynak_dosya,
               count(DISTINCT s)     AS section_sayisi,
               count(DISTINCT other) AS etkilesim_sayisi,
               count(DISTINCT c)     AS kontrendikasyon_sayisi
        LIMIT 1
        """,
        {"adlar": gercek_adlar},
    )
    return results[0] if results else None


def graph_stats() -> dict:
    """Graf istatistiklerini döner."""
    counts = run_query(
        """
        MATCH (d:Drug)         WITH count(d) AS drugs
        MATCH (s:Section)      WITH drugs, count(s) AS sections
        MATCH (c:Condition)    WITH drugs, sections, count(c) AS conditions
        OPTIONAL MATCH ()-[r:INTERACTS_WITH]->()         WITH drugs, sections, conditions, count(r) AS interactions
        OPTIONAL MATCH ()-[r2:MENTIONS_INTERACTION]->()  WITH drugs, sections, conditions, interactions, count(r2) AS mentions
        RETURN drugs, sections, conditions, interactions, mentions
        """
    )
    return counts[0] if counts else {}
