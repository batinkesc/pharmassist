"""
add_48_subchunks.py — Mevcut ChromaDB'ye 4.8 sub-chunk'larını ekler.

4.8 (İstenmeyen etkiler) bölümleri genellikle 5K-50K karakter monolitik chunk
olarak parse edilir. Bu durum yan etki aramasında düşük CU ve CR'ye yol açar.

Kullanım:
    python scripts/add_48_subchunks.py [--dry-run] [--drug <DRUG_ADI>]
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from src.ingestion.subsection_parser import extract_48_subchunks
from src.retrieval.chroma_store import get_chroma_client, get_or_create_collection
from src.processing.embedder import embed_chunks


def _get_all_48_chunks(collection, drug_filter=None):
    where = {"madde_no": "4.8"}
    if drug_filter:
        where = {"$and": [{"madde_no": "4.8"}, {"ilac_adi": drug_filter}]}

    results = collection.get(
        where=where,
        include=["documents", "metadatas"],
        limit=10000,
    )

    chunks = []
    for cid, doc, meta in zip(results.get("ids", []), results.get("documents", []), results.get("metadatas", [])):
        # Zaten sub-chunk olanları atla
        if meta.get("alt_madde", ""):
            continue
        chunks.append({
            "chunk_id":     cid,
            "ilac_adi":     meta.get("ilac_adi", ""),
            "madde_no":     "4.8",
            "madde_baslik": meta.get("madde_baslik", "İstenmeyen etkiler"),
            "icerik":       doc,
            "sayfa":        meta.get("sayfa", 0),
            "kaynak_dosya": meta.get("kaynak_dosya", ""),
            "risk_seviyesi": meta.get("risk_seviyesi", "info"),
            "oncelik":      meta.get("oncelik", "standard"),
            "toplam_sayfa": meta.get("toplam_sayfa", 0),
            "parse_tarihi": datetime.now().isoformat(),
        })
    return chunks


def _already_exists(collection, chunk_id):
    res = collection.get(ids=[chunk_id], include=[])
    return len(res.get("ids", [])) > 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--drug", type=str, default=None)
    args = parser.parse_args()

    logger.info("=== 4.8 Sub-chunk Ekleme Scripti ===")
    if args.dry_run:
        logger.info("DRY-RUN modu aktif")

    client = get_chroma_client()
    collection = get_or_create_collection(client)

    base_chunks = _get_all_48_chunks(collection, drug_filter=args.drug)
    logger.info(f"{len(base_chunks)} adet 4.8 base chunk bulundu")

    all_sub = []
    split_count = 0

    for bc in base_chunks:
        subs = extract_48_subchunks(bc)
        if subs:
            split_count += 1
            all_sub.extend(subs)

    logger.info(f"Bölünen ilaç: {split_count} | Üretilen sub-chunk: {len(all_sub)}")

    if not all_sub or args.dry_run:
        logger.info("DRY-RUN veya sub-chunk yok — çıkılıyor.")
        return

    # Mevcut olanları filtrele
    new_chunks = [sc for sc in all_sub if not _already_exists(collection, sc["chunk_id"])]
    logger.info(f"Yeni eklenecek: {len(new_chunks)} (mevcut: {len(all_sub) - len(new_chunks)})")

    if not new_chunks:
        logger.info("Tüm sub-chunk'lar zaten mevcut.")
        return

    BATCH = 50
    written = 0
    for i in range(0, len(new_chunks), BATCH):
        batch = new_chunks[i:i + BATCH]
        try:
            embeddings = embed_chunks([c["icerik"] for c in batch])
        except Exception as e:
            logger.error(f"Embedding hatası: {e}")
            continue

        ids   = [c["chunk_id"] for c in batch]
        docs  = [c["icerik"] for c in batch]
        metas = []
        for c in batch:
            flags = c.get("patient_flags", [])
            metas.append({
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
            })

        collection.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metas)
        written += len(batch)
        logger.info(f"  Yazıldı: {written}/{len(new_chunks)}")

    logger.info(f"\n✅ Tamamlandı. ChromaDB toplam: {collection.count()} chunk")


if __name__ == "__main__":
    main()
