"""
INN Propagation — Aynı etken madde grubundaki INTERACTS_WITH ilişkilerini yay.

Örnek: diltiazem için DILTIAREC'in 16 ilişkisi var ama ALTIZEM SR'nin 0'ı.
Bu script aynı INN grubundaki tüm ilaçlara aynı ilişkileri ekler.

Kullanım:
    .venv/Scripts/python scripts/propagate_inn_interactions.py
    .venv/Scripts/python scripts/propagate_inn_interactions.py --dry-run
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger
from src.graph.neo4j_client import run_query
from src.graph.kub_to_graph import _inn_tokens


def build_inn_groups() -> dict[str, list[str]]:
    """INN tokenına göre ilaç grupları oluştur."""
    drugs = run_query(
        "MATCH (d:Drug) RETURN d.name AS name, coalesce(d.etken_madde,'') AS em"
    )
    groups: dict[str, list[str]] = defaultdict(list)
    for d in drugs:
        tokens = _inn_tokens(d["em"])
        if tokens:
            primary = sorted(tokens, key=len, reverse=True)[0]
            groups[primary].append(d["name"])

    return {inn: names for inn, names in groups.items() if len(names) > 1}


def get_interactions_for_drug(drug_name: str) -> list[dict]:
    """Bir ilacın tüm INTERACTS_WITH ilişkilerini getir (hem kaynak hem hedef)."""
    rows = run_query(
        """
        MATCH (a:Drug {name: $name})-[r:INTERACTS_WITH]->(b:Drug)
        RETURN b.name AS target, r.severity AS sev,
               coalesce(r.kaynak_madde, '4.5') AS sec, 'out' AS dir
        UNION
        MATCH (a:Drug)-[r:INTERACTS_WITH]->(b:Drug {name: $name})
        RETURN a.name AS target, r.severity AS sev,
               coalesce(r.kaynak_madde, '4.5') AS sec, 'in' AS dir
        """,
        {"name": drug_name},
    )
    return rows


def propagate(
    src_drug: str,
    tgt_drug: str,
    interacting_drug: str,
    direction: str,
    severity: str,
    section: str,
    dry_run: bool,
) -> None:
    """src_drug'ın ilişkisini tgt_drug'a kopyala."""
    sev = severity or "unknown"
    if dry_run:
        if direction == "out":
            logger.debug(f"  [DRY] {tgt_drug[:28]:28s} --[{sev}]--> {interacting_drug[:28]:28s}")
        else:
            logger.debug(f"  [DRY] {interacting_drug[:28]:28s} --[{sev}]--> {tgt_drug[:28]:28s}")
        return

    if direction == "out":
        run_query(
            """
            MATCH (a:Drug {name: $tgt})
            MATCH (b:Drug {name: $interact})
            MERGE (a)-[r:INTERACTS_WITH]->(b)
            ON CREATE SET r.severity     = $sev,
                          r.kaynak_madde = $sec,
                          r.kaynak       = 'inn_propagated',
                          r.method       = 'inn_propagation'
            ON MATCH SET  r.severity = CASE
                              WHEN r.severity = 'unknown' AND $sev <> 'unknown' THEN $sev
                              ELSE r.severity END
            """,
            {"tgt": tgt_drug, "interact": interacting_drug, "sev": sev, "sec": section},
        )
    else:
        run_query(
            """
            MATCH (a:Drug {name: $interact})
            MATCH (b:Drug {name: $tgt})
            MERGE (a)-[r:INTERACTS_WITH]->(b)
            ON CREATE SET r.severity     = $sev,
                          r.kaynak_madde = $sec,
                          r.kaynak       = 'inn_propagated',
                          r.method       = 'inn_propagation'
            ON MATCH SET  r.severity = CASE
                              WHEN r.severity = 'unknown' AND $sev <> 'unknown' THEN $sev
                              ELSE r.severity END
            """,
            {"tgt": tgt_drug, "interact": interacting_drug, "sev": sev, "sec": section},
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    groups = build_inn_groups()
    logger.info(f"Toplam multi-drug INN grubu: {len(groups)}")

    stats = {"groups_processed": 0, "new_relationships": 0, "drugs_gained": 0}

    for inn, drug_names in sorted(groups.items()):
        # Gruptaki her ilacın mevcut ilişkilerini al
        drug_interactions: dict[str, list[dict]] = {}
        for name in drug_names:
            rels = get_interactions_for_drug(name)
            drug_interactions[name] = rels

        # Gruptan birinin ilişkisi var, diğerinin yok mu?
        has_rels = [n for n, rels in drug_interactions.items() if rels]
        no_rels = [n for n, rels in drug_interactions.items() if not rels]

        if not has_rels or not no_rels:
            continue

        stats["groups_processed"] += 1
        if args.verbose:
            logger.info(
                f"INN:{inn:20s} kaynaklar:{len(has_rels)} hedefler:{len(no_rels)}"
            )

        # Tüm gruptan toplanan benzersiz ilişkiler
        all_rels: list[tuple] = []
        seen: set[tuple] = set()
        for name in has_rels:
            for r in drug_interactions[name]:
                key = (r["target"], r["dir"])
                if key not in seen:
                    seen.add(key)
                    all_rels.append((r["target"], r["dir"], r["sev"], r["sec"]))

        # 0-ilişkili ilaçlara yaz
        for tgt in no_rels:
            gained = 0
            for interact, direction, sev, sec in all_rels:
                if interact == tgt:
                    continue  # kendisiyle ilişki olmaz
                propagate(
                    src_drug=has_rels[0],
                    tgt_drug=tgt,
                    interacting_drug=interact,
                    direction=direction,
                    severity=sev,
                    section=sec,
                    dry_run=args.dry_run,
                )
                gained += 1
                stats["new_relationships"] += 1

            if gained > 0:
                stats["drugs_gained"] += 1
                if args.verbose:
                    logger.debug(f"    {tgt[:40]:40s} ← {gained} ilişki")

    logger.info("=" * 60)
    logger.info(f"TAMAMLANDI{'  [DRY RUN]' if args.dry_run else ''}")
    logger.info(f"  İşlenen INN grubu    : {stats['groups_processed']}")
    logger.info(f"  Kazanılan ilaç sayısı: {stats['drugs_gained']}")
    logger.info(f"  Yeni ilişki sayısı   : {stats['new_relationships']}")

    if not args.dry_run:
        total = run_query(
            "MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) AS c"
        )[0]["c"]
        zero = run_query(
            """
            MATCH (d:Drug)
            WHERE NOT (d)-[:INTERACTS_WITH]-() AND NOT ()-[:INTERACTS_WITH]->(d)
            RETURN count(d) AS c
            """
        )[0]["c"]
        logger.info(f"  Toplam INTERACTS_WITH: {total}")
        logger.info(f"  Hâlâ 0 ilişkili Drug : {zero}")


if __name__ == "__main__":
    main()
