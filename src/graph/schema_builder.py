"""
Neo4j şema kurulumu — constraint ve index'ler.

Graf yapısı:
  (:Drug)                  — İlaç (ticari ad, etken madde, ATC kodu)
  (:Section)               — KÜB bölümü (4.3, 4.4, 4.5 ...)
  (:Interaction)           — İlaç etkileşimi
  (:Contraindication)      — Kontrendikasyon
  (:Warning)               — Özel uyarı / önlem

İlişkiler:
  (:Drug)-[:HAS_SECTION]->(:Section)
  (:Drug)-[:INTERACTS_WITH {severity, note}]->(:Drug)
  (:Drug)-[:CONTRAINDICATED_FOR {reason}]->(:Condition)
  (:Drug)-[:HAS_WARNING {category}]->(:Warning)
"""

from src.graph.neo4j_client import run_query
from loguru import logger


CONSTRAINTS = [
    "CREATE CONSTRAINT drug_name IF NOT EXISTS FOR (d:Drug) REQUIRE d.name IS UNIQUE",
    "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.section_id IS UNIQUE",
    "CREATE CONSTRAINT condition_name IF NOT EXISTS FOR (c:Condition) REQUIRE c.name IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX drug_etken IF NOT EXISTS FOR (d:Drug) ON (d.etken_madde)",
    "CREATE INDEX drug_atc IF NOT EXISTS FOR (d:Drug) ON (d.atc_kodu)",
    "CREATE INDEX section_madde IF NOT EXISTS FOR (s:Section) ON (s.madde_no)",
]


def build_schema() -> None:
    """Constraint ve index'leri oluşturur (idempotent)."""
    logger.info("Neo4j şeması kuruluyor...")

    for cypher in CONSTRAINTS:
        try:
            run_query(cypher)
            logger.debug(f"OK: {cypher[:60]}")
        except Exception as e:
            logger.warning(f"Constraint atlandı ({e}): {cypher[:60]}")

    for cypher in INDEXES:
        try:
            run_query(cypher)
            logger.debug(f"OK: {cypher[:60]}")
        except Exception as e:
            logger.warning(f"Index atlandı ({e}): {cypher[:60]}")

    logger.info("Şema kurulumu tamamlandı.")


def drop_all_data() -> None:
    """Tüm node ve ilişkileri siler (sıfırdan yükleme için)."""
    run_query("MATCH (n) DETACH DELETE n")
    logger.warning("Tüm Neo4j verisi silindi.")
