"""
ChromaDB + Neo4j rebuild - SADECE mevcut JSON dosyalarından.
PDF parse edilmez. API cagrisi sifir.
"""
import sys
import os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.retrieval.chroma_store import load_all_chunks, index_chunks
from src.graph.kub_to_graph import load_all_drugs


def rebuild_chroma():
    logger.info("=== ChromaDB Rebuild (JSON -> ChromaDB) ===")
    chunks = load_all_chunks("data/parsed_json")
    logger.info(f"Toplam chunk: {len(chunks)}")

    # Duplicate chunk_id'leri kaldir
    seen = set()
    unique_chunks = []
    for c in chunks:
        if c["chunk_id"] not in seen:
            seen.add(c["chunk_id"])
            unique_chunks.append(c)
    logger.info(f"Unique chunk: {len(unique_chunks)} ({len(chunks) - len(unique_chunks)} duplicate kaldirildi)")

    index_chunks(unique_chunks, reset=True)
    logger.info("ChromaDB rebuild tamamlandi.")


def rebuild_neo4j():
    logger.info("=== Neo4j Rebuild (JSON -> Neo4j) ===")
    load_all_drugs("data/parsed_json")
    logger.info("Neo4j rebuild tamamlandi.")


if __name__ == "__main__":
    rebuild_chroma()
    rebuild_neo4j()
    logger.info("=== TUM ISLEMLER TAMAMLANDI ===")
