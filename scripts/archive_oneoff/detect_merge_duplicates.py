#!/usr/bin/env python3
"""
Duplicate Detection & Merge Strategy

Problem: 423 ilaç, 186 unique base name, 106 duplication (%25)
Ör: EUTHYROX → 8 variant (100, 125, 150... mcg)

Strateji:
  1. Base name gruplaması (EUTHYROX → tüm variantlar)
  2. Her grup için canonical name seç
  3. ChromaDB: Meta veri güncelle (ilac_adi → canonical)
  4. Neo4j: Node merge (variant → canonical)

Kullanım:
  .venv/Scripts/python scripts/detect_merge_duplicates.py [--execute] [--canonical-strategy base|most-common]
"""

import sys
import os
import json
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.data.normalization import normalize_drug_name, get_base_name
import chromadb
from src.graph.neo4j_client import run_query


def detect_duplicates_in_json():
    """
    JSON dosyalarından duplicate'leri tespit et

    Returns:
        {base_name: [list of full names with variants]}
    """
    parsed_dir = Path("data/parsed_json")
    json_files = list(parsed_dir.glob("*.json"))

    logger.info(f"Scanning {len(json_files)} JSON files...")

    drugs_by_base = defaultdict(list)

    for json_file in json_files:
        try:
            with open(json_file, encoding='utf-8') as f:
                data = json.load(f)

            ilac_adi = data.get("ilac_adi", "")
            if not ilac_adi or ilac_adi == "UNKNOWN":
                continue

            base_name = get_base_name(ilac_adi)
            drugs_by_base[base_name].append(ilac_adi)

        except Exception as e:
            logger.error(f"  ✗ {json_file.name}: {e}")

    return drugs_by_base


def select_canonical_name(variants: list[str], strategy: str = "base") -> str:
    """
    Bir variant grubundan canonical ismi seç

    Stratejiler:
      - base: En kısa isim (ör: "EUTHYROX")
      - most-common: En sık geçen (dosya sayısı)
      - first: İlk sıradaki
    """
    if strategy == "base":
        # En kısa ismi seç — genelde base name'dir
        return min(variants, key=len)
    elif strategy == "most-common":
        # En uzun ismi seç (daha spesifik)
        return max(variants, key=len)
    else:  # first
        return variants[0]


def analyze_duplicates(drugs_by_base: dict, strategy: str = "base"):
    """
    Duplicate analizi ve merge planı oluştur

    Returns:
        {canonical_name: {variants: [...], actions: [...]}}
    """
    duplicates = {}
    merge_plan = {}

    for base_name, variants in drugs_by_base.items():
        if len(variants) <= 1:
            continue

        canonical = select_canonical_name(variants, strategy)
        other_variants = [v for v in variants if v != canonical]

        duplicates[base_name] = {
            "canonical": canonical,
            "variants": other_variants,
            "count": len(variants),
        }

        actions = []
        for v in other_variants:
            actions.append(f"ChromaDB: '{v}' → '{canonical}'")
            actions.append(f"Neo4j: Merge Drug('{v}') into Drug('{canonical}')")

        merge_plan[canonical] = {
            "merge_from": other_variants,
            "actions": actions
        }

    return duplicates, merge_plan


def report_duplicates(duplicates: dict):
    """
    Duplicate raporu yazdır
    """
    logger.info("\n" + "="*80)
    logger.info("DUPLICATE DETECTION RAPORU")
    logger.info("="*80)

    sorted_dups = sorted(duplicates.items(), key=lambda x: x[1]["count"], reverse=True)

    total_dup_count = sum(d["count"] for d in duplicates.values())
    total_dup_instances = sum(d["count"] - 1 for d in duplicates.values())

    logger.info(f"\nToplam base name: {len(duplicates)} (duplication var)")
    logger.info(f"Toplam variant'lar: {total_dup_count} ilaç")
    logger.info(f"Merge yapılacak: {total_dup_instances} variant")

    logger.info(f"\nTop 20 Duplicates:")
    for i, (base, info) in enumerate(sorted_dups[:20], 1):
        logger.info(
            f"  {i:2}. [{info['count']} variant] {base}")
        logger.info(
            f"      → Canonical: {info['canonical']}")
        for variant in info['variants'][:3]:
            logger.info(f"         - {variant}")
        if len(info['variants']) > 3:
            logger.info(f"         ... +{len(info['variants']) - 3} more")

    logger.info("\n" + "="*80)


def generate_merge_script(merge_plan: dict, output_file: str = "merge_plan.cypher"):
    """
    Neo4j merge işlemleri için Cypher script oluştur
    """
    cypher_queries = []

    for canonical, plan in merge_plan.items():
        for variant in plan["merge_from"]:
            # Drug node'ları merge et
            cypher_queries.append(f"""
// Merge variant '{variant}' into canonical '{canonical}'
MATCH (v:Drug {{name: '{variant}'}}), (c:Drug {{name: '{canonical}'}})
WHERE v <> c
// Move all relationships
MATCH (v)-[r]->(x)
CREATE (c)-[r_new:{{type: r.type}}]->(x)
SET r_new += properties(r)
DELETE r
// Move incoming relationships
MATCH (y)-[r2]->(v)
CREATE (y)-[r2_new:{{type: r2.type}}]->(c)
SET r2_new += properties(r2)
DELETE r2
// Delete variant node
DELETE v
            """.strip())

    script_path = Path("scripts") / output_file
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(cypher_queries))

    logger.info(f"\n✓ Cypher merge script oluşturuldu: {script_path}")
    return script_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Duplicate detection & merge planning")
    parser.add_argument("--execute", action="store_true", help="Merge işlemlerini gerçekten yap (risk!)")
    parser.add_argument("--canonical-strategy", choices=["base", "most-common", "first"],
                       default="base", help="Canonical name seçim stratejisi")
    args = parser.parse_args()

    logger.info("="*80)
    logger.info("DUPLICATE DETECTION & MERGE STRATEGY")
    logger.info("="*80)

    # Duplicate'leri tespit et
    logger.info("\n1️⃣  JSON dosyaları taranıyor...")
    drugs_by_base = detect_duplicates_in_json()

    # Analiz yap
    logger.info("\n2️⃣  Merge planı oluşturuluyor...")
    duplicates, merge_plan = analyze_duplicates(drugs_by_base, strategy=args.canonical_strategy)

    # Rapor
    report_duplicates(duplicates)

    # Merge script oluştur
    logger.info("\n3️⃣  Merge script'i hazırlanıyor...")
    generate_merge_script(merge_plan)

    logger.info("\n" + "="*80)
    logger.warning("⚠️  MERGE İŞLEMLERİ MANUEL")
    logger.warning("   ChromaDB: Verileri sıfırla ve yeniden index et")
    logger.warning("   Neo4j: Merge script'i çalıştır veya manuel review et")
    logger.warning("\n   Komut (ChromaDB reset): .venv/Scripts/python scripts/bulk_ingest.py --reset")
    logger.warning("   Komut (Neo4j Cypher): cat scripts/merge_plan.cypher | cypher-shell")
    logger.info("="*80)

    if args.execute:
        logger.warning("\n⚠️  --execute flag set — MERGE yapılacak!")
        logger.warning("   Bu işlem GERİ ALYNAMAZ — 5 saniye içinde CTRL+C bas")
        import time
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("\n✓ Cancelled")
            return

        # TODO: Gerçek merge işlemleri burada yapılacak
        logger.error("\n❌ Execute mode henüz tam implement edilmemiş")
        logger.error("   Manuel kontrol gerekli")


if __name__ == "__main__":
    main()
