"""
Embedding modülü — multilingual-e5-base ile KÜB chunk'larını vektörleştirir.

intfloat/multilingual-e5-base:
  - 768 boyutlu vektörler
  - Türkçe dahil 100+ dil desteği
  - RAG için query/passage prefix gerektirir:
      Sorgular  → "query: <metin>"
      Belgeler  → "passage: <metin>"
"""

from functools import lru_cache
from loguru import logger
from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-base"
PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Model singleton — ilk çağrıda yükler, sonra cache'ten döner."""
    logger.info(f"Embedding modeli yükleniyor: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    logger.info(f"Model hazır — {model.get_sentence_embedding_dimension()} dim")
    return model


def embed_chunks(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """
    KÜB chunk metinlerini vektörleştirir (passage prefix eklenir).

    Args:
        texts: Ham metin listesi
        batch_size: GPU/CPU batch boyutu

    Returns:
        Her metin için float listesi (768 boyutlu)
    """
    model = get_model()
    prefixed = [PASSAGE_PREFIX + t for t in texts]
    embeddings = model.encode(
        prefixed,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 10,
        normalize_embeddings=True,
    )
    return embeddings.tolist()


def embed_query(query_text: str) -> list[float]:
    """
    Kullanıcı sorgusunu vektörleştirir (query prefix eklenir).

    Args:
        query_text: Ham sorgu metni

    Returns:
        768 boyutlu float listesi
    """
    model = get_model()
    embedding = model.encode(
        QUERY_PREFIX + query_text,
        normalize_embeddings=True,
    )
    return embedding.tolist()
