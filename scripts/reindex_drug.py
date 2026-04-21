"""
Tek bir PDF'i ChromaDB'den temizleyip yeniden index eder.

Kullanım:
    .venv/Scripts/python scripts/reindex_drug.py data/raw_pdfs/ea6e4f8593926.pdf

    # Eski ilaç adı manuel belirtmek gerekirse (ChromaDB temizliği için):
    .venv/Scripts/python scripts/reindex_drug.py data/raw_pdfs/ea6e4f8593926.pdf --old-name ea6e4f8593926
"""

import sys
import os
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.ingestion.pdf_parser import KUBParser, _slugify
from src.retrieval.chroma_store import get_chroma_client, get_or_create_collection


def delete_drug_from_chroma(ilac_adi: str) -> int:
    """ChromaDB'den belirli bir ilaca ait tüm chunk'ları siler."""
    client = get_chroma_client()
    col = get_or_create_collection(client)

    result = col.get(where={"ilac_adi": ilac_adi})
    ids = result.get("ids", [])

    if not ids:
        logger.warning(f"ChromaDB'de '{ilac_adi}' için chunk bulunamadı.")
        return 0

    col.delete(ids=ids)
    logger.info(f"ChromaDB'den silindi: '{ilac_adi}' → {len(ids)} chunk")
    return len(ids)


def delete_drug_from_neo4j(ilac_adi: str) -> None:
    """
    Neo4j'den Drug node'unu ve tüm ilişkilerini siler.
    CIPRALEX ghost node gibi yanlış adlı node'ları temizlemek için kullanılır.
    """
    try:
        from src.graph.neo4j_client import run_query
        result = run_query(
            """
            MATCH (d:Drug {name: $name})
            OPTIONAL MATCH (d)-[r]-()
            WITH d, collect(r) AS rels, count(r) AS rel_count
            FOREACH (r IN rels | DELETE r)
            DELETE d
            RETURN rel_count
            """,
            {"name": ilac_adi},
        )
        if result:
            logger.info(f"Neo4j'den silindi: '{ilac_adi}' ({result[0].get('rel_count', 0)} ilişki)")
        else:
            logger.warning(f"Neo4j'de '{ilac_adi}' node'u bulunamadı.")
    except Exception as e:
        logger.warning(f"Neo4j silme başarısız: {e}")


def index_chunks(chunks: list[dict], batch_size: int = 32) -> int:
    """Chunk'ları ChromaDB'ye yükler."""
    from src.retrieval.chroma_store import _chunk_to_metadata
    from src.processing.embedder import embed_chunks

    client = get_chroma_client()
    col = get_or_create_collection(client)

    existing_ids = set(col.get()["ids"])
    new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]

    if not new_chunks:
        logger.warning("Tüm chunk'lar zaten mevcut, ekleme yapılmadı.")
        return 0

    for i in range(0, len(new_chunks), batch_size):
        batch = new_chunks[i: i + batch_size]
        texts = [c["icerik"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        metadatas = [_chunk_to_metadata(c) for c in batch]
        embeddings = embed_chunks(texts, batch_size=batch_size)
        col.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    logger.info(f"ChromaDB'ye eklendi: {len(new_chunks)} chunk")
    return len(new_chunks)


def main():
    parser = argparse.ArgumentParser(description="Tek PDF'i yeniden index et")
    parser.add_argument("pdf", help="PDF dosya yolu")
    parser.add_argument(
        "--old-name", default=None,
        help="ChromaDB'de eski (yanlış) ilaç adı — belirtilirse önce silinir"
    )
    parser.add_argument(
        "--skip-graph", action="store_true",
        help="Neo4j güncellemesini atla"
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        logger.error(f"PDF bulunamadı: {pdf_path}")
        sys.exit(1)

    logger.info(f"{'='*50}")
    logger.info(f"Yeniden index: {pdf_path.name}")
    logger.info(f"{'='*50}")

    # 1. Eski ilaç adıyla ChromaDB ve Neo4j'den temizle
    if args.old_name:
        delete_drug_from_chroma(args.old_name)
        if not args.skip_graph:
            delete_drug_from_neo4j(args.old_name)
    else:
        # JSON'dan eski adı bul (eğer varsa)
        stem = pdf_path.stem
        old_json = Path("data/parsed_json") / f"{stem.upper()}.json"
        if not old_json.exists():
            old_json = Path("data/parsed_json") / f"{stem}.json"
        if old_json.exists():
            import json
            with open(old_json, encoding="utf-8") as f:
                old_data = json.load(f)
            old_name = old_data.get("ilac_adi", "")
            if old_name:
                logger.info(f"Eski ilaç adı JSON'dan alındı: '{old_name}'")
                delete_drug_from_chroma(old_name)
            old_json.unlink()
            logger.info(f"Eski JSON silindi: {old_json}")

    # 2. Yeniden parse et
    kub_parser = KUBParser()
    result = kub_parser.parse(pdf_path)
    ilac_adi = result["ilac_adi"]
    logger.info(f"Yeni ilaç adı: '{ilac_adi}'")

    # 3. JSON kaydet
    parsed_dir = Path("data/parsed_json")
    parsed_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(ilac_adi)
    json_path = parsed_dir / f"{slug}.json"
    kub_parser.save_json(result, json_path)

    # 4. ChromaDB'ye yükle
    eklenen = index_chunks(result["chunks"])

    # 5. Neo4j güncelle
    if not args.skip_graph:
        try:
            from src.graph.kub_to_graph import (
                upsert_drug_node, upsert_section_node,
                extract_contraindications, extract_interactions, extract_warnings,
            )
            upsert_drug_node(ilac_adi, result["kaynak_dosya"])
            for chunk in result["chunks"]:
                upsert_section_node(ilac_adi, chunk)
                madde = chunk.get("madde_no", "")
                if madde == "4.3":
                    extract_contraindications(ilac_adi, chunk)
                elif madde == "4.5":
                    extract_interactions(ilac_adi, chunk)
                elif madde == "4.4":
                    extract_warnings(ilac_adi, chunk)
            logger.info(f"Neo4j güncellendi: '{ilac_adi}'")
        except Exception as e:
            logger.warning(f"Neo4j güncellenemedi (atlandı): {e}")

    logger.info(f"{'='*50}")
    logger.info(f"Tamamlandı: '{ilac_adi}' — {len(result['chunks'])} chunk, {eklenen} yeni")
    logger.info(f"JSON: {json_path}")

    # ChromaDB toplam
    try:
        col = get_or_create_collection(get_chroma_client())
        logger.info(f"ChromaDB toplam: {col.count()} chunk")
    except Exception:
        pass


if __name__ == "__main__":
    main()
