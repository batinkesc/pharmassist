"""
add_44_subchunks.py — Mevcut ChromaDB'ye 4.4 sub-chunk'larını ekler.

Tüm corpus'u yeniden parse etmeden, ChromaDB'deki mevcut 4.4 chunk'larından
paragraf tabanlı sub-chunk'lar üretir ve ekler.

Kullanım:
    python scripts/add_44_subchunks.py [--dry-run] [--drug <DRUG_ADI>]

Seçenekler:
    --dry-run    ChromaDB'ye yazmadan sadece rapor üretir
    --drug       Tek bir ilaç için çalıştır (test amaçlı)
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Proje kökünü sys.path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from src.ingestion.subsection_parser import extract_44_subchunks
from src.retrieval.chroma_store import (
    get_chroma_client,
    get_or_create_collection,
)
from src.processing.embedder import embed_chunks


def _get_all_44_chunks(collection, drug_filter: str | None = None) -> list[dict]:
    """ChromaDB'den tüm 4.4 chunk'larını çeker."""
    where = {"madde_no": "4.4"}
    if drug_filter:
        where = {"$and": [{"madde_no": "4.4"}, {"ilac_adi": drug_filter}]}

    results = collection.get(
        where=where,
        include=["documents", "metadatas"],
        limit=10000,  # yeterli üst sınır
    )

    chunks = []
    ids = results.get("ids", [])
    docs = results.get("documents", [])
    metas = results.get("metadatas", [])

    for cid, doc, meta in zip(ids, docs, metas):
        chunk = {
            "chunk_id":      cid,
            "ilac_adi":      meta.get("ilac_adi", ""),
            "madde_no":      "4.4",
            "madde_baslik":  meta.get("madde_baslik", "Özel kullanım uyarıları ve önlemleri"),
            "icerik":        doc,
            "sayfa":         meta.get("sayfa", 0),
            "kaynak_dosya":  meta.get("kaynak_dosya", ""),
            "risk_seviyesi": meta.get("risk_seviyesi", "warning"),
            "oncelik":       meta.get("oncelik", "important"),
            "toplam_sayfa":  meta.get("toplam_sayfa", 0),
            "parse_tarihi":  datetime.now().isoformat(),
        }
        # Zaten sub-chunk olan 4.4'leri atla (alt_madde dolu olanlar)
        if meta.get("alt_madde", ""):
            continue
        chunks.append(chunk)

    return chunks


def _already_exists(collection, chunk_id: str) -> bool:
    """Verilen chunk_id zaten var mı?"""
    res = collection.get(ids=[chunk_id], include=[])
    return len(res.get("ids", [])) > 0


def main():
    parser = argparse.ArgumentParser(description="4.4 sub-chunk üretici ve yükleyici")
    parser.add_argument("--dry-run", action="store_true",
                        help="Yazmadan sadece rapor üret")
    parser.add_argument("--drug", type=str, default=None,
                        help="Tek bir ilaç adı filtrele (test)")
    args = parser.parse_args()

    logger.info("=== 4.4 Sub-chunk Ekleme Scripti ===")
    if args.dry_run:
        logger.info("DRY-RUN modu aktif — ChromaDB'ye yazılmayacak")

    client = get_chroma_client()
    collection = get_or_create_collection(client)

    # Mevcut 4.4 chunk'larını çek (base, sub-chunk olmayan)
    logger.info(f"ChromaDB'den 4.4 chunk'ları çekiliyor{' (ilaç: ' + args.drug + ')' if args.drug else ''}...")
    base_chunks = _get_all_44_chunks(collection, drug_filter=args.drug)
    logger.info(f"  {len(base_chunks)} adet 4.4 base chunk bulundu")

    stats = {
        "total_base": len(base_chunks),
        "split_candidate": 0,
        "sub_chunks_generated": 0,
        "sub_chunks_written": 0,
        "sub_chunks_skipped_existing": 0,
        "drugs_split": [],
    }

    all_sub_chunks = []

    for base_chunk in base_chunks:
        drug_name = base_chunk["ilac_adi"]
        text_len = len(base_chunk["icerik"])

        sub_chunks = extract_44_subchunks(base_chunk)
        if not sub_chunks:
            continue

        stats["split_candidate"] += 1
        stats["sub_chunks_generated"] += len(sub_chunks)
        stats["drugs_split"].append(f"{drug_name} ({text_len} char → {len(sub_chunks)} parts)")
        all_sub_chunks.extend(sub_chunks)

    logger.info(f"\n=== Üretim Özeti ===")
    logger.info(f"  Bölünecek ilaç sayısı : {stats['split_candidate']}")
    logger.info(f"  Üretilen sub-chunk    : {stats['sub_chunks_generated']}")

    if not all_sub_chunks:
        logger.info("Eklenecek sub-chunk yok. Çıkılıyor.")
        return

    # İlaç listesi
    logger.info("\nBölünen ilaçlar:")
    for d in sorted(stats["drugs_split"]):
        logger.info(f"  {d}")

    if args.dry_run:
        logger.info("\nDRY-RUN: Yazma atlandı.")
        return

    # Mevcut olanları filtrele
    new_chunks = []
    for sc in all_sub_chunks:
        if _already_exists(collection, sc["chunk_id"]):
            stats["sub_chunks_skipped_existing"] += 1
            logger.debug(f"  Zaten var, atlandı: {sc['chunk_id']}")
        else:
            new_chunks.append(sc)

    if not new_chunks:
        logger.info("Tüm sub-chunk'lar zaten mevcut. Yeni ekleme yok.")
        return

    logger.info(f"\n{len(new_chunks)} yeni sub-chunk embed ediliyor...")

    # Embed ve yaz — batch 50
    BATCH = 50
    written = 0
    for i in range(0, len(new_chunks), BATCH):
        batch = new_chunks[i:i + BATCH]
        try:
            embeddings = embed_chunks([c["icerik"] for c in batch])
        except Exception as e:
            logger.error(f"Embedding hatası (batch {i//BATCH + 1}): {e}")
            continue

        ids   = [c["chunk_id"] for c in batch]
        docs  = [c["icerik"] for c in batch]
        metas = []
        for c in batch:
            flags = c.get("patient_flags", [])
            meta = {
                "ilac_adi":          c["ilac_adi"],
                "madde_no":          c["madde_no"],
                "madde_baslik":      c["madde_baslik"],
                "risk_seviyesi":     c["risk_seviyesi"],
                "oncelik":           c["oncelik"],
                "sayfa":             c["sayfa"],
                "kaynak_dosya":      c["kaynak_dosya"],
                "alt_madde":         c["alt_madde"],
                "alt_madde_etiketi": c.get("alt_madde_etiketi", ""),
                "ust_chunk_id":      c.get("ust_chunk_id", ""),
                "flag_renal":        "renal"     in flags,
                "flag_hepatic":      "hepatic"   in flags,
                "flag_pediatric":    "pediatric" in flags,
                "flag_geriatric":    "geriatric" in flags,
            }
            metas.append(meta)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=docs,
            metadatas=metas,
        )
        written += len(batch)
        logger.info(f"  Yazıldı: {written}/{len(new_chunks)}")

    stats["sub_chunks_written"] = written

    logger.info(f"\n=== Sonuç ===")
    logger.info(f"  Toplam base 4.4 chunk : {stats['total_base']}")
    logger.info(f"  Bölünen ilaç sayısı   : {stats['split_candidate']}")
    logger.info(f"  Üretilen sub-chunk    : {stats['sub_chunks_generated']}")
    logger.info(f"  Yazılan sub-chunk     : {stats['sub_chunks_written']}")
    logger.info(f"  Atlandı (mevcut)      : {stats['sub_chunks_skipped_existing']}")
    logger.info(f"\nChromaDB koleksiyon toplam: {collection.count()} chunk")
    logger.info("✅ Tamamlandı.")


if __name__ == "__main__":
    main()
