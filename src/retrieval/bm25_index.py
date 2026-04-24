"""
BM25 Keyword Index — ChromaDB üzerinde hybrid retrieval için.

Görev:
  - ChromaDB chunk'larını BM25Okapi ile indeksler
  - Semantik arama ile birleştirilmek üzere skor üretir
  - Reciprocal Rank Fusion (RRF) ile iki skorlamayı birleştirir

Kullanım:
  from src.retrieval.bm25_index import get_bm25_index, hybrid_search_rrf

  idx = get_bm25_index()            # singleton, ilk çağrıda inşa edilir
  results = idx.search(query, n=50, filter_madde=["4.3","4.5"])

Neden BM25 gerekiyor?
  - Semantik model "warfarin", "GFR 40", "Child-Pugh C" gibi exact keyword'leri
    anlam benzerliği yetersizse kaçırıyor.
  - BM25 tam metin eşleşmesi yapar → recall artışı, özellikle ilaç adları ve
    klinik parametreler için.
"""

import re
import threading
from functools import lru_cache
from typing import Optional

import numpy as np
from loguru import logger
from rank_bm25 import BM25Okapi

from src.data.normalization import normalize_drug_name


# ---------------------------------------------------------------------------
# Tokenizasyon
# ---------------------------------------------------------------------------

_SPLIT_RE = re.compile(r"[\s,;:.!?()\[\]/\-]+")
_MIN_TOKEN_LEN = 2


def _tokenize(text: str) -> list[str]:
    """
    Türkçe-uyumlu BM25 tokenizasyonu.

    - ® ™ © ve Türkçe karakterler normalize edilir
    - Noktalama ve boşluklarda böler
    - 2 karakterden kısa token'lar atılır (stopword etkisi)
    """
    normalized = normalize_drug_name(text)          # ® kaldır, büyük harf, TR→ASCII
    tokens = _SPLIT_RE.split(normalized)
    return [t for t in tokens if len(t) >= _MIN_TOKEN_LEN]


# ---------------------------------------------------------------------------
# BM25 Index sınıfı
# ---------------------------------------------------------------------------

class BM25Index:
    """
    ChromaDB koleksiyonundan inşa edilen BM25 keyword indeksi.

    Attributes:
        chunk_ids:  ChromaDB ID listesi (indeks ↔ chunk_id eşleşmesi)
        metadatas:  Her chunk'ın metadata dict'i
        documents:  Ham metin listesi
        bm25:       BM25Okapi nesnesi
    """

    def __init__(self) -> None:
        self.chunk_ids:  list[str]  = []
        self.metadatas:  list[dict] = []
        self.documents:  list[str]  = []
        self.bm25:       Optional[BM25Okapi] = None
        self._built = False

    def build(self, collection) -> None:
        """ChromaDB koleksiyonundan BM25 indeksini inşa eder."""
        logger.info("BM25 indeksi inşa ediliyor...")

        # Tüm chunk'ları çek (limit 10000 — corpus max ~1500)
        data = collection.get(
            include=["documents", "metadatas"],
            limit=10000,
        )

        self.chunk_ids = data["ids"]
        self.metadatas = data["metadatas"]
        self.documents = data["documents"]

        tokenized = [_tokenize(doc) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized)
        self._built = True

        logger.info(f"BM25 indeksi hazır: {len(self.chunk_ids)} chunk")

    def search(
        self,
        query: str,
        n: int = 50,
        filter_madde: list[str] | None = None,
        filter_ilac:  list[str] | None = None,
    ) -> list[dict]:
        """
        BM25 arama — metadata filtreleri uygulanabilir.

        Args:
            query:        Aranacak metin
            n:            Döndürülecek max sonuç sayısı
            filter_madde: Madde no filtresi (["4.3", "4.5"] gibi)
            filter_ilac:  İlaç adı filtresi (normalize edilmiş liste beklenir)

        Returns:
            [{"chunk_id": str, "bm25_score": float, "bm25_rank": int}, ...]
        """
        if not self._built or self.bm25 is None:
            logger.warning("BM25 indeksi henüz inşa edilmedi.")
            return []

        tokens = _tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        ranked_idx = np.argsort(scores)[::-1]

        # İlaç filtresi için normalize edilmiş prefix seti
        norm_ilac_prefixes: set[str] = set()
        if filter_ilac:
            for name in filter_ilac:
                norm = normalize_drug_name(name)
                # İlk kelime yeterli (WARFARIN, COLCHICUM gibi)
                first = norm.split()[0] if norm.split() else norm
                norm_ilac_prefixes.add(first)

        results = []
        for idx in ranked_idx:
            if len(results) >= n:
                break
            if scores[idx] <= 0:          # BM25 skoru 0 — hiç match yok
                break

            meta = self.metadatas[idx]

            # Madde filtresi
            if filter_madde and meta.get("madde_no") not in filter_madde:
                continue

            # İlaç filtresi — prefix eşleşmesi
            if norm_ilac_prefixes:
                ilac_norm = normalize_drug_name(meta.get("ilac_adi", ""))
                ilac_first = ilac_norm.split()[0] if ilac_norm.split() else ""
                if ilac_first not in norm_ilac_prefixes:
                    continue

            results.append({
                "chunk_id":   self.chunk_ids[idx],
                "bm25_score": float(scores[idx]),
                "bm25_rank":  len(results) + 1,
            })

        return results


# ---------------------------------------------------------------------------
# Singleton yönetimi (thread-safe)
# ---------------------------------------------------------------------------

_bm25_instance: Optional[BM25Index] = None
_bm25_lock = threading.Lock()


def get_bm25_index() -> BM25Index:
    """
    Thread-safe singleton BM25 indeksi döner.
    İlk çağrıda ChromaDB'den inşa edilir, sonraki çağrılarda cache'den döner.
    """
    global _bm25_instance
    if _bm25_instance is not None and _bm25_instance._built:
        return _bm25_instance

    with _bm25_lock:
        if _bm25_instance is not None and _bm25_instance._built:
            return _bm25_instance

        from src.retrieval.chroma_store import get_chroma_client, get_or_create_collection
        collection = get_or_create_collection(get_chroma_client())

        _bm25_instance = BM25Index()
        _bm25_instance.build(collection)

    return _bm25_instance


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------

def reciprocal_rank_fusion(
    semantic_results: list[dict],
    bm25_results:     list[dict],
    k: int = 60,
    semantic_weight: float = 0.7,
    bm25_weight:     float = 0.3,
) -> list[str]:
    """
    Semantik ve BM25 sıralamalarını RRF ile birleştirir.

    Standart RRF: score(d) = Σ weight_i / (k + rank_i(d))
    Ağırlıklar: semantik %70, BM25 %30 (semantik embedding daha güvenilir).

    Args:
        semantic_results: [{"chunk_id": str, ...}, ...] — embedding sıralaması
        bm25_results:     [{"chunk_id": str, "bm25_rank": int}, ...]
        k:                RRF sabit terimi (60 standart değer)
        semantic_weight:  Semantik ağırlık
        bm25_weight:      BM25 ağırlık

    Returns:
        chunk_id listesi, RRF skoruna göre azalan sırada
    """
    rrf_scores: dict[str, float] = {}

    for rank, result in enumerate(semantic_results, 1):
        cid = result["chunk_id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + semantic_weight / (k + rank)

    for result in bm25_results:
        cid = result["chunk_id"]
        rank = result["bm25_rank"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + bm25_weight / (k + rank)

    return sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)
