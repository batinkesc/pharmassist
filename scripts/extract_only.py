"""
extract_only.py — Sadece LLM extraction + Neo4j INTERACTS_WITH yazma.

Kullanım:
  .venv/Scripts/python scripts/extract_only.py

Yapılan işlemler:
  1. data/parsed_json/ altındaki tüm JSON'ları okur
  2. Neo4j'de INTERACTS_WITH sayısını kontrol eder — zaten işlendiyse atlar
  3. KUBExtractor ile LLM'den etkileşim çıkarır
  4. INNResolver ile INN propagation yapar
  5. Neo4j'e yazar

.env:
  LM_STUDIO_URL=http://<vast-ai-pod>:11434/v1   (Ollama endpoint)
  LM_STUDIO_MODEL=qwen2.5:14b                    (Ollama model adı)
"""

from __future__ import annotations

import json
import sys
import time
import argparse
from pathlib import Path

from loguru import logger

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.core.drug_record import DrugIdentity
from src.core.name_resolver import get_resolver
from src.ingestion.kub_extractor import KUBExtractor
from src.ingestion.inn_resolver import INNResolver
from src.graph.neo4j_client import run_query
from src.pipeline.ingestion_pipeline import IngestionPipeline

_PARSED_JSON_DIR = _ROOT / "data" / "parsed_json"


def already_extracted(canonical_id: str) -> bool:
    """Neo4j'de bu ilaçtan çıkan INTERACTS_WITH var mı?"""
    try:
        result = run_query(
            """
            MATCH (a:Drug {canonical_id: $cid})-[:INTERACTS_WITH]->()
            RETURN count(*) AS cnt
            """,
            {"cid": canonical_id},
        )
        return bool(result) and result[0].get("cnt", 0) > 0
    except Exception:
        return False


def extract_one(
    json_path: Path,
    extractor: KUBExtractor,
    inn_resolver: INNResolver,
    pipeline: IngestionPipeline,
    force: bool = False,
) -> dict:
    """Tek JSON için extraction yapar. Sonuç dict döner."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"JSON okuma hatası ({json_path.name}): {e}")
        return {"status": "failed", "reason": str(e)}

    ilac_adi    = data.get("ilac_adi", json_path.stem.replace("_", " "))
    etken_madde = data.get("etken_madde", "")
    canonical_id = data.get("canonical_id", "")

    identity = DrugIdentity.from_parsed(ilac_adi, etken_madde)
    # JSON'da canonical_id varsa kontrol et (tutarlılık)
    if canonical_id and canonical_id != identity.canonical_id:
        logger.warning(
            f"canonical_id uyumsuzluğu ({identity.display_name}): "
            f"JSON={canonical_id} computed={identity.canonical_id} — JSON'dakini kullanıyoruz"
        )
        # frozen dataclass — yeni örnek oluştur
        identity = DrugIdentity(
            canonical_id=canonical_id,
            normalized_name=identity.normalized_name,
            display_name=identity.display_name,
            inn=identity.inn,
            atc_code=identity.atc_code,
        )

    if not force and already_extracted(identity.canonical_id):
        logger.debug(f"[SKIP] {identity.display_name} — zaten extract edilmiş")
        return {"status": "skipped", "drug": identity.display_name}

    # Sections dict
    chunks = data.get("chunks", [])
    sections = pipeline._extract_sections_dict(chunks)

    if not sections.get("4.5"):
        logger.warning(f"[WARN] {identity.display_name} — 4.5 bölümü yok, atlanıyor")
        return {"status": "skipped", "drug": identity.display_name, "reason": "no_4.5"}

    # LLM Extraction
    try:
        interactions = extractor.extract(identity, sections)
    except Exception as e:
        logger.error(f"Extraction hatası ({identity.display_name}): {e}")
        return {"status": "failed", "drug": identity.display_name, "reason": str(e)}

    # INN Propagation
    try:
        propagated = inn_resolver.propagate_to_new_drug(identity, interactions)
        interactions = interactions + propagated
    except Exception as e:
        logger.warning(f"INNResolver hata ({identity.display_name}): {e}")
        propagated = []

    # Neo4j yaz
    if interactions:
        pipeline._write_interactions_neo4j(identity, interactions)

    # Retroactive resolve
    resolved = pipeline._retroactive_resolve(identity)
    if resolved:
        logger.info(f"Retroactive: {resolved} DrugMention çözüldü ({identity.display_name})")

    logger.success(
        f"[OK] {identity.display_name} — "
        f"{len(interactions)} etkileşim ({len(propagated)} INN prop)"
    )
    return {
        "status": "ok",
        "drug": identity.display_name,
        "interactions": len(interactions),
        "propagated": len(propagated),
    }


def main():
    parser = argparse.ArgumentParser(description="PharmAssist — Sadece LLM extraction")
    parser.add_argument("--model", default=None, help="LLM model adı (varsayılan: .env LM_STUDIO_MODEL)")
    parser.add_argument("--force", action="store_true", help="Zaten işlenenleri de yeniden işle")
    parser.add_argument("--limit", type=int, default=0, help="Kaç JSON işleneceği (0=hepsi)")
    parser.add_argument("--drug", type=str, default=None, help="Belirli ilaç adının bir kısmı (filtre)")
    args = parser.parse_args()

    import os
    # Model: --model argümanı varsa önce o, yoksa LM_STUDIO_MODEL env, yoksa kub_extractor default
    model = args.model or os.getenv("LM_STUDIO_MODEL", "qwen2.5:14b")
    endpoint = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
    logger.info(f"Endpoint : {endpoint}")
    logger.info(f"Model    : {model}")

    extractor   = KUBExtractor(model=model)
    inn_resolver = INNResolver()
    pipeline    = IngestionPipeline(skip_extraction=True)  # extractor yok, sadece yardımcı metodlar için

    json_files = sorted(_PARSED_JSON_DIR.glob("*.json"))
    if args.drug:
        json_files = [f for f in json_files if args.drug.upper() in f.stem.upper()]
    if args.limit:
        json_files = json_files[:args.limit]

    logger.info(f"Toplam işlenecek: {len(json_files)} JSON")

    stats = {"ok": 0, "skipped": 0, "failed": 0}
    start = time.time()

    for i, jf in enumerate(json_files, 1):
        logger.info(f"[{i}/{len(json_files)}] {jf.stem}")
        result = extract_one(jf, extractor, inn_resolver, pipeline, force=args.force)
        status = result.get("status", "failed")
        if status == "ok":
            stats["ok"] += 1
        elif status == "skipped":
            stats["skipped"] += 1
        else:
            stats["failed"] += 1

        # Her 10 ilacta bir NameResolver cache'i temizle
        if i % 10 == 0:
            get_resolver.cache_clear()
            elapsed = time.time() - start
            rate = i / elapsed * 60
            remaining = (len(json_files) - i) / (rate / 60) / 60
            logger.info(
                f"  İlerleme: {i}/{len(json_files)} — "
                f"{rate:.1f} ilaç/dk — tahmini kalan: {remaining:.0f} dk"
            )

    elapsed_total = time.time() - start
    logger.info(
        f"\n--- Özet ---\n"
        f"Başarılı : {stats['ok']}\n"
        f"Atlandı  : {stats['skipped']}\n"
        f"Hatalı   : {stats['failed']}\n"
        f"Süre     : {elapsed_total/60:.1f} dk\n"
    )


if __name__ == "__main__":
    main()
