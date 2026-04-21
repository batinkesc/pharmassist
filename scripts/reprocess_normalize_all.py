#!/usr/bin/env python3
"""
Tüm parse edilen JSON'ları yeniden işle — normalizasyon ekle

Yapılanlar:
  1. data/parsed_json/*.json dosyalarını oku
  2. İlaç adını normalize et
  3. ChromaDB metadata'daki ilac_adi'yi güncelle
  4. Neo4j'de drug node name'ini güncelle
  5. Backup al, sonra güncelle

Kullanım:
  .venv/Scripts/python scripts/reprocess_normalize_all.py [--dry-run]
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.data.normalization import normalize_drug_name
import chromadb
from src.graph.neo4j_client import run_query


def backup_json_dir():
    """JSON dizini backup et"""
    parsed_dir = Path("data/parsed_json")
    backup_dir = Path("data/backups") / f"parsed_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Symlink veya copy
    import shutil
    for json_file in parsed_dir.glob("*.json"):
        shutil.copy2(json_file, backup_dir / json_file.name)

    logger.info(f"✓ Backup oluşturuldu: {backup_dir}")
    return backup_dir


def normalize_json_files(dry_run=False):
    """
    Tüm parsed JSON dosyalarını normalize et

    Returns:
        (changed_count, error_count)
    """
    parsed_dir = Path("data/parsed_json")
    json_files = list(parsed_dir.glob("*.json"))

    logger.info(f"Toplam JSON dosyası: {len(json_files)}")

    changed_count = 0
    error_count = 0
    changes_log = []

    for json_file in sorted(json_files):
        try:
            with open(json_file, encoding='utf-8') as f:
                data = json.load(f)

            original_name = data.get("ilac_adi", "")
            if not original_name or original_name == "UNKNOWN":
                continue

            normalized_name = normalize_drug_name(original_name)

            if original_name != normalized_name:
                logger.debug(f"  [{json_file.name}] '{original_name}' → '{normalized_name}'")
                changes_log.append({
                    "file": json_file.name,
                    "original": original_name,
                    "normalized": normalized_name
                })

                if not dry_run:
                    data["ilac_adi"] = normalized_name
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    changed_count += 1
                else:
                    changed_count += 1

        except Exception as e:
            logger.error(f"  ✗ {json_file.name}: {e}")
            error_count += 1

    logger.info(f"✓ {changed_count} dosya güncellendi (errors: {error_count})")
    return changed_count, error_count, changes_log


def update_chroma_metadata(dry_run=False):
    """
    ChromaDB'deki metadata'da ilac_adi'yi normalize et

    Returns:
        updated_count
    """
    logger.info("\nChromaDB metadata güncelleniyor...")

    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection("kub_chunks")

    all_data = col.get(include=["metadatas"])

    updated_count = 0
    updates_needed = []

    for metadata in all_data["metadatas"]:
        original_name = metadata.get("ilac_adi", "")
        if not original_name or original_name == "UNKNOWN":
            continue

        normalized_name = normalize_drug_name(original_name)

        if original_name != normalized_name:
            updates_needed.append({
                "original": original_name,
                "normalized": normalized_name,
                "count": sum(1 for m in all_data["metadatas"] if m.get("ilac_adi") == original_name)
            })
            updated_count += 1

    # ChromaDB metadata doğrudan güncelleme yok — delete + re-add gerekir
    # Şimdilik log et, sonra bulk işlem yap
    logger.warning(f"⚠️  ChromaDB'de {updated_count} unique ilac_adi normalize edilmeli")
    logger.warning("   (Direct metadata update ChromaDB'de yapılamıyor — delete+re-add gerekir)")

    for update in updates_needed[:5]:  # İlk 5'ini göster
        logger.info(f"    '{update['original']}' ({update['count']} chunk) → '{update['normalized']}'")

    return updated_count


def update_neo4j_drugs(dry_run=False):
    """
    Neo4j'deki Drug node'larını normalize et

    Returns:
        updated_count
    """
    logger.info("\nNeo4j Drug node'ları güncelleniyor...")

    # Tüm Drug node'larını oku
    result = run_query("""
        MATCH (d:Drug)
        RETURN d.name as name, COUNT(*) as count
    """)

    updated_count = 0
    updates_needed = []

    for row in result:
        original_name = row.get("name", "")
        if not original_name or original_name == "UNKNOWN":
            continue

        normalized_name = normalize_drug_name(original_name)

        if original_name != normalized_name:
            updates_needed.append({
                "original": original_name,
                "normalized": normalized_name
            })
            updated_count += 1

    if updates_needed and not dry_run:
        logger.warning("⚠️  Neo4j node'larının adını değiştirmek riski vardır")
        logger.warning("   (Relationship'ler etkilenebilir)")
        logger.warning("   Şimdilik güncelleme YAPMAYıyoruz — manuel review gerekli")

    logger.warning(f"⚠️  Neo4j'de {updated_count} Drug node normalize edilmeli")
    for update in updates_needed[:5]:
        logger.info(f"    '{update['original']}' → '{update['normalized']}'")

    return updated_count


def main():
    parser = argparse.ArgumentParser(description="427 ilaçı normalize et")
    parser.add_argument("--dry-run", action="store_true", help="Test modu — değişiklik yapma")
    parser.add_argument("--skip-backup", action="store_true", help="Backup atlayıp doğrudan işle (tehlikeli!)")
    args = parser.parse_args()

    logger.info("="*80)
    logger.info("REPROCESSING: 427 İlaç Normalizasyonu")
    logger.info("="*80)

    if args.dry_run:
        logger.warning("⚠️  DRY-RUN MODE — Değişiklik yapılmayacak")

    # Backup
    if not args.skip_backup:
        backup_json_dir()

    # JSON dosyalarını normalize et
    logger.info("\n1️⃣  JSON dosyaları normalize ediliyor...")
    json_changed, json_errors, changes_log = normalize_json_files(dry_run=args.dry_run)

    # ChromaDB metadata
    logger.info("\n2️⃣  ChromaDB metadata kontrol ediliyor...")
    chroma_updated = update_chroma_metadata(dry_run=args.dry_run)

    # Neo4j nodes
    logger.info("\n3️⃣  Neo4j nodes kontrol ediliyor...")
    neo4j_updated = update_neo4j_drugs(dry_run=args.dry_run)

    # Özet
    logger.info("\n" + "="*80)
    logger.success("REPROCESSING ÖZETİ:")
    logger.info(f"  JSON dosyaları: {json_changed} normalize edildi")
    logger.info(f"  ChromaDB metadata: {chroma_updated} gereken güncelleme")
    logger.info(f"  Neo4j nodes: {neo4j_updated} gereken güncelleme")
    logger.info("="*80)

    # Warnings
    if chroma_updated > 0:
        logger.warning("\n⚠️  ChromaDB MANUEL İŞLEM GEREKLİ")
        logger.warning("   Adım: ChromaDB'yi sıfırla ve tüm chunk'ları yeniden index et")
        logger.warning("   Komut: .venv/Scripts/python scripts/bulk_ingest.py --reset")

    if neo4j_updated > 0:
        logger.warning("\n⚠️  Neo4j MANUEL İNCELEME GEREKLİ")
        logger.warning("   Relationship'ler etkilenebilir — sistem mimarı review etmeli")

    if not args.dry_run and json_changed > 0:
        logger.success(f"\n✓ {json_changed} dosya güncellendi")
        logger.info("  Sonraki adım: ChromaDB ve Neo4j yeniden oluştur")
    elif args.dry_run:
        logger.info(f"\n✓ DRY-RUN: {json_changed} dosya güncellenmesi önerileniyor")
        logger.info("  Gerçek çalıştırma için: --dry-run bayrağını kaldır")


if __name__ == "__main__":
    main()
