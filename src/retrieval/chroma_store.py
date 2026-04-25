"""
ChromaDB vektör veritabanı modülü.

Desteklenen işlemler:
  - Chunk'ları embed edip kaydetme
  - Metadata filtreli semantik arama
  - Hasta profili bazlı hedefli retrieval
"""

import json
import re
from functools import lru_cache
from pathlib import Path
from loguru import logger
import chromadb
from chromadb.config import Settings

from src.data.normalization import normalize_drug_name
from src.processing.embedder import embed_chunks, embed_query

# Proje kökü = bu dosyadan 3 üst dizin (src/retrieval/chroma_store.py → /)
CHROMA_DB_PATH = str(Path(__file__).resolve().parent.parent.parent / "chroma_db")
COLLECTION_NAME = "kub_chunks"


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.PersistentClient:
    """Kalıcı ChromaDB istemcisi döner — singleton (lru_cache)."""
    return chromadb.PersistentClient(
        path=CHROMA_DB_PATH,
        settings=Settings(anonymized_telemetry=False),
    )


def get_or_create_collection(client: chromadb.PersistentClient):
    """KÜB chunk koleksiyonunu döner veya oluşturur."""
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Yükleme
# ---------------------------------------------------------------------------

def _chunk_to_metadata(chunk: dict) -> dict:
    """
    ChromaDB metadata sadece str/int/float/bool kabul eder.
    list tipindeki alanları (patient_flags) stringe çevirir.
    """
    meta = {
        "ilac_adi":         chunk["ilac_adi"],
        "madde_no":         chunk["madde_no"],
        "madde_baslik":     chunk["madde_baslik"],
        "risk_seviyesi":    chunk["risk_seviyesi"],
        "oncelik":          chunk["oncelik"],
        "sayfa":            chunk["sayfa"],
        "kaynak_dosya":     chunk["kaynak_dosya"],
    }
    # Opsiyonel alanlar
    if "alt_madde" in chunk:
        meta["alt_madde"] = chunk["alt_madde"]
        meta["alt_madde_etiketi"] = chunk.get("alt_madde_etiketi", "")
        meta["ust_chunk_id"] = chunk.get("ust_chunk_id", "")
    else:
        meta["alt_madde"] = ""
        meta["ust_chunk_id"] = ""

    # patient_flags → ayrı boolean alanlar (ChromaDB $contains desteklemiyor)
    flags = chunk.get("patient_flags", [])
    meta["flag_renal"]    = "renal"    in flags
    meta["flag_hepatic"]  = "hepatic"  in flags
    meta["flag_pediatric"] = "pediatric" in flags
    meta["flag_geriatric"] = "geriatric" in flags

    return meta


def load_all_chunks(parsed_json_dir: str = "data/parsed_json") -> list[dict]:
    """Tüm parse edilmiş JSON dosyalarından chunk'ları toplar."""
    chunks = []
    for json_file in Path(parsed_json_dir).glob("*.json"):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
        chunks.extend(data["chunks"])
    logger.info(f"{len(chunks)} chunk yüklendi ({parsed_json_dir})")
    return chunks


def index_chunks(
    chunks: list[dict],
    reset: bool = False,
    batch_size: int = 32,
) -> None:
    """
    Chunk'ları embed edip ChromaDB'ye kaydeder.

    Args:
        chunks:     parse edilmiş chunk listesi
        reset:      True ise mevcut koleksiyonu siler ve sıfırdan başlar
        batch_size: embedding batch boyutu
    """
    client = get_chroma_client()

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info("Mevcut koleksiyon silindi.")
        except Exception as e:
            logger.warning(f"Koleksiyon silinemedi (zaten yok olabilir): {e}")

    collection = get_or_create_collection(client)

    # Zaten indexed olanları atla
    existing_ids = set(collection.get()["ids"])
    new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]

    if not new_chunks:
        logger.info("Tüm chunk'lar zaten indexed. Atlanıyor.")
        return

    logger.info(f"{len(new_chunks)} yeni chunk embed ediliyor...")

    # Batch halinde işle
    for i in range(0, len(new_chunks), batch_size):
        batch = new_chunks[i: i + batch_size]
        texts = [c["icerik"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        metadatas = [_chunk_to_metadata(c) for c in batch]

        embeddings = embed_chunks(texts, batch_size=batch_size)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info(f"  Batch {i // batch_size + 1}: {len(batch)} chunk eklendi")

    total = collection.count()
    logger.info(f"✓ ChromaDB toplam: {total} chunk")


# ---------------------------------------------------------------------------
# Arama
# ---------------------------------------------------------------------------

def search(
    query: str,
    n_results: int = 5,
    filter_madde: list[str] | None = None,
    filter_ilac: list[str] | None = None,
    filter_patient_flags: list[str] | None = None,
) -> list[dict]:
    """
    Semantik arama + opsiyonel metadata filtresi.
    """
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    query_embedding = embed_query(query)

    where = _build_where(filter_madde, filter_ilac, filter_patient_flags)

    kwargs = dict(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    output = []
    for chunk_id, doc, meta, dist in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "chunk_id": chunk_id,
            **meta,
            "icerik": doc,
            "score": round(1 - dist, 4),
        })

    if filter_ilac and len(output) == 0:
        logger.warning(f"filter_ilac match başarısız: {filter_ilac}. Esnek arama yapılıyor...")
        where_relaxed = _build_where(filter_madde, None, filter_patient_flags)
        
        kwargs_no_ilac = dict(
            query_embeddings=[query_embedding],
            n_results=min(n_results * 5, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        if where_relaxed:
            kwargs_no_ilac["where"] = where_relaxed

        results_all = collection.query(**kwargs_no_ilac)
        resolved = _resolve_drug_names(filter_ilac)
        prefixes = [normalize_drug_name(r) for r in resolved]

        for chunk_id, doc, meta, dist in zip(
            results_all["ids"][0],
            results_all["documents"][0],
            results_all["metadatas"][0],
            results_all["distances"][0],
        ):
            normalized = normalize_drug_name(meta["ilac_adi"])
            if any(p in normalized for p in prefixes):
                output.append({
                    "chunk_id": chunk_id,
                    **meta,
                    "icerik": doc,
                    "score": round(1 - dist, 4),
                })
                if len(output) >= n_results:
                    break
    return output


def _normalize_ilac_adi(name: str) -> str:
    """DEPRECATED: Use normalize_drug_name from src.data.normalization"""
    return normalize_drug_name(name)


@lru_cache(maxsize=1)
def _load_quarantine_list() -> set[str]:
    """
    data/quarantine/ klasöründeki .md dosyalarından karantina ilaç adlarını yükler.
    Dönen küme: büyük harf, alt çizgi ile birleşik (örn. "BLITHE_FORT", "ACNOR").
    """
    quarantine_dir = Path(__file__).resolve().parent.parent.parent / "data" / "quarantine"
    names: set[str] = set()
    for f in quarantine_dir.glob("*.md"):
        stem = f.stem.upper()
        for suffix in ("_OCR_BASARISIZ", "_PARSE_FAIL"):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        parts = stem.split("_")
        drug_parts: list[str] = []
        for p in parts:
            if p and p[0].isdigit():
                break
            drug_parts.append(p)
        if drug_parts:
            names.add("_".join(drug_parts))
    return names


@lru_cache(maxsize=1)
def _get_drug_name_map() -> dict[str, str]:
    """normalize(ad) → orijinal ChromaDB adı mapping'i döner."""
    client = get_chroma_client()
    col = get_or_create_collection(client)
    results = col.get(limit=10000, include=['metadatas'])
    mapping: dict[str, str] = {}
    for m in results['metadatas']:
        name = m.get('ilac_adi', '')
        if name:
            mapping[normalize_drug_name(name)] = name
    return mapping


def _resolve_drug_names(names: list[str]) -> list[str]:
    """İlaç adlarını canonical adlarla eşleştirir."""
    mapping = _get_drug_name_map()
    resolved = []
    for name in names:
        norm = normalize_drug_name(name)
        if norm in mapping:
            resolved.append(mapping[norm])
            continue

        prefix_hits = []
        for key, orig in mapping.items():
            if key.startswith(norm) or norm in key:
                prefix_hits.append(orig)
        
        if prefix_hits:
            resolved.extend(list(dict.fromkeys(prefix_hits)))
            continue

        resolved.append(name)
    return resolved


def _build_where(
    filter_madde: list[str] | None,
    filter_ilac: list[str] | None,
    filter_patient_flags: list[str] | None,
) -> dict | None:
    conditions = []
    if filter_madde:
        if len(filter_madde) == 1:
            conditions.append({"madde_no": {"$eq": filter_madde[0]}})
        else:
            conditions.append({"madde_no": {"$in": filter_madde}})

    if filter_ilac:
        resolved = list(dict.fromkeys(_resolve_drug_names(filter_ilac)))
        if len(resolved) == 1:
            conditions.append({"ilac_adi": {"$eq": resolved[0]}})
        else:
            conditions.append({"ilac_adi": {"$in": resolved}})

    if filter_patient_flags:
        flag_map = {"renal": "flag_renal", "hepatic": "flag_hepatic", "pediatric": "flag_pediatric", "geriatric": "flag_geriatric"}
        flag_conditions = [{flag_map[f]: {"$eq": True}} for f in filter_patient_flags if f in flag_map]
        if len(flag_conditions) == 1:
            conditions.extend(flag_conditions)
        elif len(flag_conditions) > 1:
            conditions.append({"$or": flag_conditions})

    if not conditions: return None
    if len(conditions) == 1: return conditions[0]
    return {"$and": conditions}


def batch_search(query: str, priority_sections: list[str], secondary_sections: list[str], filter_ilac: list[str] | None = None, filter_patient_flags: list[str] | None = None, k_priority: int = 8, k_secondary: int = 4) -> list[dict]:
    results = []; seen_ids = set()
    def _run(sections, k):
        if not sections: return
        raw = search(query=query, n_results=k, filter_madde=sections, filter_ilac=filter_ilac, filter_patient_flags=filter_patient_flags)
        for chunk in raw:
            cid = chunk.get("chunk_id", "")
            if cid not in seen_ids:
                seen_ids.add(cid); results.append(chunk)
    _run(priority_sections, k_priority)
    _run(secondary_sections, k_secondary)
    return results


def hybrid_batch_search(
    query: str,
    priority_sections: list[str],
    secondary_sections: list[str],
    filter_ilac: list[str] | None = None,
    filter_patient_flags: list[str] | None = None,
    k_priority: int = 15,
    k_secondary: int = 10,
    bm25_n: int = 50,
) -> list[dict]:
    """
    BM25 + semantik hybrid arama, RRF ile birleştirir.

    Semantik aramadan gelen chunk metadata'sı korunur.
    BM25'te bulunan ama semantikte olmayan chunk'lar ChromaDB'den meta ile eklenir.

    Args:
        query:             Arama sorgusu
        priority_sections: Öncelikli KÜB madde no listesi
        secondary_sections: İkincil KÜB madde no listesi
        filter_ilac:       İlaç filtresi
        filter_patient_flags: Hasta flag filtresi
        k_priority:        Semantik priority arama k değeri
        k_secondary:       Semantik secondary arama k değeri
        bm25_n:            BM25 aday havuzu büyüklüğü

    Returns:
        RRF sıralamasına göre chunk dict listesi
    """
    from src.retrieval.bm25_index import get_bm25_index, reciprocal_rank_fusion

    all_sections = list(dict.fromkeys(priority_sections + secondary_sections))

    # 1. Semantik arama (mevcut batch_search)
    semantic_raw = batch_search(
        query=query,
        priority_sections=priority_sections,
        secondary_sections=secondary_sections,
        filter_ilac=filter_ilac,
        filter_patient_flags=filter_patient_flags,
        k_priority=k_priority,
        k_secondary=k_secondary,
    )

    # 2. BM25 keyword arama (patient_flags filtresi uygulanmaz — recall önceliği)
    bm25_idx = get_bm25_index()
    bm25_raw = bm25_idx.search(
        query=query,
        n=bm25_n,
        filter_madde=all_sections if all_sections else None,
        filter_ilac=filter_ilac,
    )

    # 3. RRF füzyon
    fused_ids = reciprocal_rank_fusion(semantic_raw, bm25_raw)

    # 4. Semantic chunk_id → metadata map
    semantic_map = {r["chunk_id"]: r for r in semantic_raw}

    # 5. BM25-only chunk'ları ChromaDB'den getir
    bm25_only_ids = [cid for cid in fused_ids if cid not in semantic_map]
    bm25_extra: dict[str, dict] = {}
    if bm25_only_ids:
        client = get_chroma_client()
        col = get_or_create_collection(client)
        try:
            fetched = col.get(
                ids=bm25_only_ids,
                include=["documents", "metadatas"],
            )
            for fid, doc, meta in zip(fetched["ids"], fetched["documents"], fetched["metadatas"]):
                # Patient flag kontrolü — semantikte bypass edilen flag mantığı burada da uygulanmaz
                # (yüksek recall için); reranker sonradan sıralar
                bm25_extra[fid] = {
                    "chunk_id": fid,
                    **meta,
                    "icerik": doc,
                    "score": 0.0,    # BM25-only chunk: semantik skor yok
                }
        except Exception as e:
            logger.debug(f"BM25-only chunk fetch hatası: {e}")

    # 6. Füzyon sırasına göre sonuç listesi oluştur
    results = []
    seen: set[str] = set()
    for cid in fused_ids:
        if cid in seen:
            continue
        seen.add(cid)
        if cid in semantic_map:
            results.append(semantic_map[cid])
        elif cid in bm25_extra:
            results.append(bm25_extra[cid])

    return results


def collection_stats() -> dict:
    client = get_chroma_client(); collection = get_or_create_collection(client)
    all_meta = collection.get(include=["metadatas"])["metadatas"]
    ilac_counts = {}; madde_counts = {}
    for m in all_meta:
        ilac_counts[m["ilac_adi"]] = ilac_counts.get(m["ilac_adi"], 0) + 1
        madde_counts[m["madde_no"]] = madde_counts.get(m["madde_no"], 0) + 1
    return {"toplam_chunk": collection.count(), "ilac_dagilimi": ilac_counts, "madde_dagilimi": dict(sorted(madde_counts.items()))}
