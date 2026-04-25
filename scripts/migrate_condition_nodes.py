"""
Condition node normalizasyon migrasyonu.

Sorun: "böbrek \nyetmezliği" gibi whitespace (newline/çoklu boşluk) içeren
       Condition node'ları var. Bunlar "böbrek yetmezliği" ile ayrı node
       olarak kaydedilmiş — sorgular birini buluyor, diğerini kaçırıyor.

Çözüm:
  1. Bozuk Condition node'larını tespit et
  2. Normalize edilmiş adı hesapla
  3. Eğer canonical (temiz) node varsa: tüm ilişkileri canonical'a taşı, bozuğu sil
  4. Canonical yoksa: bozuk node'un adını güncelle
"""
import sys, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()
from src.graph.neo4j_client import run_query
from loguru import logger


def normalize_condition_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().lower()


def migrate():
    # 1. Tüm Condition node'larını getir
    all_conditions = run_query("MATCH (c:Condition) RETURN c.name AS name")
    logger.info(f"Toplam {len(all_conditions)} Condition node bulundu.")

    bozuk = [(r["name"], normalize_condition_name(r["name"]))
             for r in all_conditions
             if r["name"] != normalize_condition_name(r["name"])]

    if not bozuk:
        logger.info("Bozuk Condition node yok — migrasyon gerekmiyor.")
        return

    logger.info(f"{len(bozuk)} bozuk Condition node tespit edildi:")
    for orig, norm in bozuk:
        logger.info(f"  '{repr(orig)}' → '{norm}'")

    canonical_names = {r["name"] for r in all_conditions}

    for orig_name, norm_name in bozuk:
        if norm_name in canonical_names and norm_name != orig_name:
            # Canonical node var — ilişkileri taşı, bozuğu sil
            logger.info(f"Merge: '{orig_name}' → '{norm_name}'")
            run_query(
                """
                MATCH (bozuk:Condition {name: $orig})
                MATCH (canonical:Condition {name: $norm})
                // CONTRAINDICATED_FOR ilişkilerini canonical'a taşı
                OPTIONAL MATCH (d:Drug)-[r:CONTRAINDICATED_FOR]->(bozuk)
                FOREACH (_ IN CASE WHEN d IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (d)-[:CONTRAINDICATED_FOR]->(canonical)
                )
                WITH bozuk, canonical
                DETACH DELETE bozuk
                """,
                {"orig": orig_name, "norm": norm_name},
            )
            logger.info(f"  ✓ Merge tamamlandı, bozuk node silindi.")
        else:
            # Canonical yok — sadece adı güncelle
            logger.info(f"Rename: '{orig_name}' → '{norm_name}'")
            run_query(
                "MATCH (c:Condition {name: $orig}) SET c.name = $norm",
                {"orig": orig_name, "norm": norm_name},
            )
            logger.info(f"  ✓ Rename tamamlandı.")

    # Sonuç kontrolü
    after = run_query("MATCH (c:Condition) RETURN c.name AS name ORDER BY c.name")
    logger.info(f"\nMigrasyon sonrası {len(after)} Condition node:")
    for r in after:
        logger.info(f"  '{r['name']}'")

    logger.info("Migrasyon tamamlandı.")


if __name__ == "__main__":
    migrate()
