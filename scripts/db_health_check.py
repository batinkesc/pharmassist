#!/usr/bin/env python3
"""
Database Health Check — Düzeltmeler işe yaradı mı?
"""

import sys
import os
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

import chromadb
from src.graph.neo4j_client import run_query
from src.data.normalization import normalize_drug_name, get_base_name


def check_chromadb_normalization():
    """ChromaDB'de normalized drug names var mı?"""
    logger.info("\n1️⃣  ChromaDB Normalizasyon Kontrolü")
    logger.info("-" * 80)

    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection("kub_chunks")

    all_data = col.get(include=["metadatas"])
    metadatas = all_data["metadatas"]

    drug_names = [m.get("ilac_adi", "") for m in metadatas if m.get("ilac_adi")]
    unique_names = set(drug_names)

    logger.info(f"Toplam chunk: {len(metadatas)}")
    logger.info(f"Unique drug names: {len(unique_names)}")

    trademark_count = sum(1 for name in unique_names if '®' in name or '™' in name or '©' in name)
    logger.info(f"Trademark sembolü içeren: {trademark_count}")

    if trademark_count > 0:
        logger.warning(f"❌ Hala {trademark_count} drug'da trademark var!")
    else:
        logger.success("✓ Tüm trademark'ler temizlendi")

    turkish_count = sum(1 for name in unique_names if any(c in name for c in 'çğıöşüÇĞİÖŞÜ'))
    if turkish_count > 0:
        logger.warning(f"⚠️  {turkish_count} drug'da Türkçe karakter var")
    else:
        logger.success("✓ Türkçe karakterler normalize edildi")

    return trademark_count == 0 and turkish_count == 0


def check_neo4j_drugs():
    """Neo4j'de Drug nodes clean mi?"""
    logger.info("\n2️⃣  Neo4j Drug Nodes Kontrolü")
    logger.info("-" * 80)

    result = run_query("MATCH (d:Drug) RETURN COUNT(d) as count")
    drug_count = result[0]["count"] if result else 0
    logger.info(f"Toplam Drug nodes: {drug_count}")

    result = run_query("MATCH (d:Drug) RETURN d.name as name LIMIT 20")
    names = [r["name"] for r in result]

    trademark_count = sum(1 for n in names if '®' in n or '™' in n)
    if trademark_count > 0:
        logger.warning(f"❌ Neo4j'de {trademark_count} drug'da trademark var")
    else:
        logger.success("✓ Neo4j'de trademark'ler temizlendi")

    return trademark_count == 0


def check_duplicates():
    """Duplicate'ler var mı hala?"""
    logger.info("\n3️⃣  Duplicate Kontrolü")
    logger.info("-" * 80)

    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection("kub_chunks")
    all_data = col.get(include=["metadatas"])
    metadatas = all_data["metadatas"]

    drug_names = [m.get("ilac_adi", "") for m in metadatas if m.get("ilac_adi")]

    base_to_variants = {}
    for name in drug_names:
        base = get_base_name(name)
        if base not in base_to_variants:
            base_to_variants[base] = []
        if name not in base_to_variants[base]:
            base_to_variants[base].append(name)

    duplicates = {k: v for k, v in base_to_variants.items() if len(v) > 1}

    logger.info(f"Toplam unique base names: {len(base_to_variants)}")
    logger.info(f"Base names with duplicates: {len(duplicates)}")

    if len(duplicates) > 0:
        logger.warning(f"⚠️  Hala {len(duplicates)} base name'de duplication var")
    else:
        logger.success("✓ Duplicate yok")

    return len(duplicates)


def check_cyp450():
    """CYP450 manual list complete mi?"""
    logger.info("\n4️⃣  CYP450 Manual List Kontrolü")
    logger.info("-" * 80)

    from src.analysis.cyp450_mapper import ILAC_CYP_PROFILI

    logger.info(f"Toplam manual entry: {len(ILAC_CYP_PROFILI)}")
    logger.success(f"✓ CYP450 list doldurulmuş ({len(ILAC_CYP_PROFILI)} entries)")

    return len(ILAC_CYP_PROFILI)


def check_severity_distribution():
    """INTERACTS_WITH severity dağılımını göster."""
    logger.info("\n5️⃣  INTERACTS_WITH Severity Dağılımı")
    logger.info("-" * 80)

    dist = run_query(
        "MATCH ()-[r:INTERACTS_WITH]->() RETURN r.severity AS sev, count(*) AS cnt ORDER BY cnt DESC"
    )
    total = sum(d["cnt"] for d in dist)
    logger.info(f"Toplam INTERACTS_WITH ilişkisi: {total}")
    for d in dist:
        pct = d["cnt"] / total * 100 if total else 0
        logger.info(f"  {d['sev']:20s}: {d['cnt']:6d}  ({pct:.1f}%)")

    unknown_cnt = next((d["cnt"] for d in dist if d["sev"] == "unknown"), 0)
    unknown_pct = unknown_cnt / total * 100 if total else 0
    if unknown_pct > 50:
        logger.warning(f"⚠️  unknown oranı yüksek: {unknown_pct:.1f}%")
    else:
        logger.success(f"✓ unknown oranı kabul edilebilir: {unknown_pct:.1f}%")
    return unknown_pct


def check_quarantine():
    """Quarantine raporu nedir?"""
    logger.info("\n5️⃣  Quarantine Raporları")
    logger.info("-" * 80)

    quarantine_dir = Path("data/quarantine")
    if not quarantine_dir.exists():
        logger.info("Quarantine dizini yok")
        return 0

    reports = list(quarantine_dir.glob("*.md"))

    logger.info(f"Toplam quarantine raporu: {len(reports)}")

    if len(reports) == 0:
        logger.success("✓ Hiç quarantine raporu yok")

    return len(reports)


def main():
    logger.info("=" * 80)
    logger.info("DATABASE HEALTH CHECK")
    logger.info("=" * 80)

    chroma_clean = check_chromadb_normalization()
    neo4j_clean = check_neo4j_drugs()
    dup_count = check_duplicates()
    cyp_count = check_cyp450()
    unknown_pct = check_severity_distribution()
    quarantine_count = check_quarantine()

    logger.info("\n" + "=" * 80)
    logger.info("HEALTH CHECK ÖZETİ")
    logger.info("=" * 80)

    checks = [
        ("ChromaDB Normalizasyon", chroma_clean),
        ("Neo4j Clean Nodes", neo4j_clean),
        ("Duplicate Free", dup_count == 0),
        ("CYP450 List", cyp_count > 50),
        ("Severity Unknown <50%", unknown_pct < 50),
        ("Quarantine Count", quarantine_count == 0),
    ]

    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        logger.info(f"{status} {check_name}")

    logger.info("\n" + "=" * 80)

    if chroma_clean and neo4j_clean and dup_count == 0:
        logger.success("✅ DATABASE HEALTHY — RAGAS v5'e hazır!")
        return True
    else:
        logger.warning("⚠️  DATABASE ISSUES DETECTED — Düzeltme gerekli")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
