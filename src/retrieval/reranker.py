"""
Cross-encoder Reranker (Faz 11)

İlk retrieval sonuçlarını cross-encoder ile yeniden puanlayarak
bağlama giren chunk'ların soruyla alakasını artırır.

Model: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
- mMARCO multilingual model — 26 dil destekler, Türkçe dahil
- Önceki model (ms-marco-MiniLM-L-6-v2) yalnızca İngilizce'ydi,
  Türkçe KÜB içeriğini hatalı sıralıyordu (#6 faithfulness fix)
"""

from functools import lru_cache
from loguru import logger

_RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


@lru_cache(maxsize=1)
def _get_reranker():
    """Cross-encoder modelini singleton olarak yükler."""
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(_RERANKER_MODEL, max_length=512)
        logger.info(f"Reranker modeli yüklendi: {_RERANKER_MODEL}")
        return model
    except Exception as e:
        logger.warning(f"Reranker yüklenemedi, devre dışı: {e}")
        return None


def rerank(query: str, chunks: list[dict], top_k: int = 10) -> list[dict]:
    """
    Cross-encoder ile chunk listesini yeniden sıralar.

    Args:
        query:   Kullanıcı sorusu / augmented query
        chunks:  ChromaDB'den gelen chunk listesi (her biri 'icerik' alanına sahip)
        top_k:   Kaç chunk döneceği

    Returns:
        Yeniden sıralanmış, top_k chunk'tan oluşan liste.
        Reranker devre dışıysa orijinal listeyi döner.
    """
    if not chunks:
        return chunks

    model = _get_reranker()
    if model is None:
        logger.debug("Reranker aktif değil — orijinal sıra korunuyor")
        return chunks[:top_k]

    # Cross-encoder (query, document) çiftlerini puanla
    pairs = [(query, c["icerik"]) for c in chunks]
    try:
        scores = model.predict(pairs)
    except Exception as e:
        logger.warning(f"Reranker predict hatası: {e} — fallback")
        return chunks[:top_k]

    # Score'ları chunk'lara ekle ve sırala
    scored = sorted(
        zip(scores, chunks),
        key=lambda x: x[0],
        reverse=True,
    )

    result = []
    for score, chunk in scored[:top_k]:
        chunk_copy = dict(chunk)
        chunk_copy["rerank_score"] = round(float(score), 4)
        result.append(chunk_copy)

    logger.debug(f"Reranker: {len(chunks)} → {len(result)} chunk (top score: {scored[0][0]:.3f})")
    return result
