"""
Mevcut Neo4j INTERACTS_WITH ilişkilerinin severity=unknown olanlarını
KÜB 4.5 metinlerinden yeniden hesaplar.

Kullanım:
    .venv/Scripts/python scripts/patch_severity.py
    .venv/Scripts/python scripts/patch_severity.py --dry-run   # değişiklik yapmadan sayar

Bu script sıfırdan rebuild gerektirmez — sadece unknown olanları günceller.
"""

import argparse
import json
import sys
from pathlib import Path

# Proje kökü
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger
from src.graph.neo4j_client import run_query
from src.graph.kub_to_graph import _extract_severity, _inn_tokens
from src.data.normalization import normalize_drug_name

def load_45_texts(parsed_dir: Path) -> dict[str, str]:
    """Her ilaç için 4.5 metin + etken_madde tokenlarını döner."""
    texts: dict[str, str] = {}
    for jf in parsed_dir.glob("*.json"):
        data = json.loads(jf.read_text(encoding="utf-8"))
        # İlaç adını normalize et ki Neo4j'deki normalize adlarla eşleşsin
        ilac = normalize_drug_name(data.get("ilac_adi", ""))
        for chunk in data.get("chunks", []):
            if chunk.get("madde_no") == "4.5":
                texts[ilac] = chunk.get("icerik", "")
                break
    return texts


def main(dry_run: bool = False, window: int = 1500) -> None:
    logger.info(f"Severity pencere boyutu: {window}")
    parsed_dir = ROOT / "data" / "parsed_json"
    drug_45 = load_45_texts(parsed_dir)
    logger.info(f"{len(drug_45)} ilaç için 4.5 metni yüklendi")

    # Tüm unknown INTERACTS_WITH ilişkilerini çek
    rows = run_query(
        """
        MATCH (a:Drug)-[r:INTERACTS_WITH]->(b:Drug)
        WHERE r.severity = 'unknown'
        RETURN a.name AS drug_a, b.name AS drug_b,
               coalesce(b.etken_madde, '') AS etken_b
        """
    )
    logger.info(f"severity=unknown ilişki sayısı: {len(rows)}")

    updated = 0
    still_unknown = 0

    for row in rows:
        drug_a = row["drug_a"]
        drug_b = row["drug_b"]
        etken_b = row["etken_b"]

        text_a = drug_45.get(drug_a, "")
        if not text_a:
            still_unknown += 1
            continue

        # Önce etken_madde tokenlarıyla dene (INN cross-ref yolu)
        tokens_b = _inn_tokens(etken_b) if etken_b else []
        matched_tok = next((t for t in tokens_b if t in text_a.lower()), None)

        # Token bulunamazsa drug_b adının kısa halini dene
        if not matched_tok:
            short_b = drug_b.split()[0] if drug_b else ""
            matched_tok = short_b if short_b and short_b.lower() in text_a.lower() else drug_b

        severity = _extract_severity(text_a, matched_tok, window)

        if severity == "unknown":
            still_unknown += 1
            continue

        updated += 1
        if dry_run:
            logger.debug(f"[DRY] {drug_a[:30]} → {drug_b[:30]}: {severity}")
        else:
            run_query(
                """
                MATCH (a:Drug {name: $drug_a})-[r:INTERACTS_WITH]->(b:Drug {name: $drug_b})
                WHERE r.severity = 'unknown'
                SET r.severity = $severity
                """,
                {"drug_a": drug_a, "drug_b": drug_b, "severity": severity},
            )

    logger.info(
        f"{'[DRY RUN] ' if dry_run else ''}Güncellenen: {updated} | "
        f"Hâlâ unknown: {still_unknown} / {len(rows)}"
    )

    # Özet dağılım
    dist = run_query(
        "MATCH ()-[r:INTERACTS_WITH]->() RETURN r.severity AS sev, count(*) AS cnt ORDER BY cnt DESC"
    )
    logger.info("Severity dağılımı:")
    for d in dist:
        logger.info(f"  {d['sev']:20s}: {d['cnt']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Değişiklik yapmadan say")
    parser.add_argument("--window", type=int, default=1500, help="Severity bağlam penceresi (karakter, default=1500)")
    args = parser.parse_args()
    main(dry_run=args.dry_run, window=args.window)
