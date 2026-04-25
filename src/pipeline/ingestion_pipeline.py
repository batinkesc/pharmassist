"""
IngestionPipeline — 4 ayrı scriptin yerine geçen tek orkestratör.

Önceki durum (4 manuel adım, transactional garanti yok):
  1. scripts/bulk_ingest.py       → parse + ChromaDB
  2. scripts/load_graph.py        → Neo4j temel node'lar
  3. scripts/rebuild_interactions.py → LLM extraction
  4. scripts/propagate_inn_interactions.py → INN yayma

Yeni durum (tek çağrı, tutarlı durum):
  pipeline = IngestionPipeline()
  result   = pipeline.ingest(pdf_path)   # hepsi burada

Garantiler:
  - DrugIdentity.canonical_id → ChromaDB ve Neo4j'de aynı birincil anahtar
  - Duplicate tespiti canonical_id üzerinden — isim varyantları sorun değil
  - QualityGate her zaman çalışır (bulk_ingest'teki inline QA kaldırıldı)
  - LLM extraction başarısız olursa pipeline devam eder (karantina olmaz)
  - INN propagation otomatik — unutulamaz
  - NameResolver güncelleme: yeni ilaç eklendikten sonra cache clear

Kullanım (CLI):
  .venv/Scripts/python -m src.pipeline.ingestion_pipeline --pdf data/raw_kub/ALTIZEM.pdf
  .venv/Scripts/python -m src.pipeline.ingestion_pipeline --all
  .venv/Scripts/python -m src.pipeline.ingestion_pipeline --all --force
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from loguru import logger

# Proje kökü sys.path'e — dotenv ÖNCE yükle, sonra import et
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env", override=True)

from src.core.drug_record import DrugIdentity
from src.core.name_resolver import get_resolver
from src.ingestion.pdf_parser import KUBParser, ImageBasedPDFError
from src.ingestion.quality_gate import QualityGate
from src.ingestion.kub_extractor import KUBExtractor
from src.ingestion.inn_resolver import INNResolver
from src.retrieval.chroma_store import index_chunks, get_chroma_client, get_or_create_collection
from src.graph.kub_to_graph import (
    upsert_drug_node,
    upsert_section_node,
    extract_contraindications,
    extract_warnings,
    extract_dose_adjustments,
    extract_cyp_edges,
    extract_pregnancy_category,
)
from src.graph.neo4j_client import run_query

_PARSED_JSON_DIR = _ROOT / "data" / "parsed_json"
_QUARANTINE_DIR  = _ROOT / "data" / "quarantine"
_RAW_KUB_DIR     = _ROOT / "data" / "raw_pdfs"


# ------------------------------------------------------------------
# Sonuç enum + dataclass
# ------------------------------------------------------------------

class IngestionStatus(str, Enum):
    SUCCESS    = "success"
    SKIPPED    = "skipped"       # Duplicate — force=False
    QUARANTINE = "quarantine"    # QualityGate başarısız
    FAILED     = "failed"        # Beklenmedik hata


@dataclass
class IngestionResult:
    status: IngestionStatus
    drug_name: str
    canonical_id: str = ""
    interaction_count: int = 0
    propagated_count: int = 0
    quarantine_reason: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status in (IngestionStatus.SUCCESS, IngestionStatus.SKIPPED)

    def __str__(self) -> str:
        if self.status == IngestionStatus.SUCCESS:
            return (
                f"[OK] {self.drug_name} ({self.canonical_id}) — "
                f"{self.interaction_count} etkileşim, "
                f"{self.propagated_count} INN propagation"
            )
        if self.status == IngestionStatus.SKIPPED:
            return f"[SKIP] {self.drug_name} — zaten mevcut"
        if self.status == IngestionStatus.QUARANTINE:
            return f"[QUARANTINE] {self.drug_name} — {self.quarantine_reason}"
        return f"[FAIL] {self.drug_name} — {self.error}"


# ------------------------------------------------------------------
# Ana pipeline
# ------------------------------------------------------------------

class IngestionPipeline:
    """
    PDF → ChromaDB + Neo4j tek seferlik, tutarlı yükleme.

    Her adım hata alırsa sonraki adımlar etkilenmez;
    sadece o adımın katkısı eksik kalır ve log'a düşer.
    """

    def __init__(
        self,
        llm_model: str = "qwen/qwen2.5-coder-14b-instruct",
        skip_extraction: bool = False,
    ):
        self.parser       = KUBParser()
        self.quality_gate = QualityGate()
        self.extractor    = KUBExtractor(model=llm_model) if not skip_extraction else None
        self.inn_resolver = INNResolver()

    # ------------------------------------------------------------------
    # Tekli PDF ingestion
    # ------------------------------------------------------------------

    def ingest(self, pdf_path: Path, force: bool = False) -> IngestionResult:
        """
        Tek PDF'i pipeline'dan geçirir.

        Args:
            pdf_path: KÜB PDF dosyası
            force   : True → mevcut kayıt silinip yeniden ingest
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return IngestionResult(
                status=IngestionStatus.FAILED,
                drug_name=pdf_path.stem,
                error=f"Dosya bulunamadı: {pdf_path}",
            )

        # ----- Adım 1: Parse -----
        try:
            parse_data = self.parser.parse(str(pdf_path))
        except ImageBasedPDFError as e:
            return IngestionResult(
                status=IngestionStatus.QUARANTINE,
                drug_name=pdf_path.stem,
                quarantine_reason=f"Resim bazlı PDF: {e}",
            )
        except Exception as e:
            return IngestionResult(
                status=IngestionStatus.FAILED,
                drug_name=pdf_path.stem,
                error=f"Parse hatası: {e}",
            )

        if parse_data is None:
            return IngestionResult(
                status=IngestionStatus.QUARANTINE,
                drug_name=pdf_path.stem,
                quarantine_reason="Parser None döndü (image-based veya bozuk PDF)",
            )

        ilac_adi    = parse_data.get("ilac_adi", "Bilinmeyen İlaç")
        etken_madde = parse_data.get("etken_madde", "")

        # ----- Adım 2: DrugIdentity -----
        identity = DrugIdentity.from_parsed(ilac_adi, etken_madde)

        # ----- Adım 3: Duplicate kontrolü -----
        if not force and self._already_exists(identity.canonical_id):
            logger.info(f"[SKIP] {identity.display_name} ({identity.canonical_id}) — zaten mevcut")
            return IngestionResult(
                status=IngestionStatus.SKIPPED,
                drug_name=identity.display_name,
                canonical_id=identity.canonical_id,
            )

        # ----- Adım 4: Quality Gate -----
        qr = self.quality_gate.check(parse_data)
        if qr.should_quarantine:
            self._write_quarantine_report(identity, qr.flags)
            return IngestionResult(
                status=IngestionStatus.QUARANTINE,
                drug_name=identity.display_name,
                canonical_id=identity.canonical_id,
                quarantine_reason="; ".join(qr.flags[:3]),
            )

        # ----- Adım 5: JSON kaydet -----
        try:
            json_path = self._save_parsed_json(identity, parse_data)
        except Exception as e:
            return IngestionResult(
                status=IngestionStatus.FAILED,
                drug_name=identity.display_name,
                canonical_id=identity.canonical_id,
                error=f"JSON kaydetme hatası: {e}",
            )

        # ----- Adım 6: ChromaDB -----
        chunks = parse_data.get("chunks", [])
        self._write_chromadb(identity, chunks)

        # ----- Adım 7: Neo4j temel node'lar -----
        self._write_neo4j_base(identity, parse_data, chunks)

        # ----- Adım 8: LLM Extraction -----
        sections = self._extract_sections_dict(chunks)
        interactions = []
        if self.extractor:
            try:
                interactions = self.extractor.extract(identity, sections)
            except Exception as e:
                logger.warning(f"KUBExtractor hata ({identity.display_name}): {e}")

        # ----- Adım 9: INN Propagation -----
        propagated = []
        try:
            propagated = self.inn_resolver.propagate_to_new_drug(identity, interactions)
            interactions = interactions + propagated
        except Exception as e:
            logger.warning(f"INNResolver hata ({identity.display_name}): {e}")

        # ----- Adım 10: Neo4j INTERACTS_WITH yaz -----
        if interactions:
            self._write_interactions_neo4j(identity, interactions)

        # ----- Adım 11: QualityGate.flag_low_interactions -----
        self.quality_gate.flag_low_interactions(identity.display_name, len(interactions))

        # ----- Adım 12: NameResolver cache temizle -----
        get_resolver.cache_clear()

        # ----- Adım 13: Retroactive DrugMention çözümü -----
        # Yeni ilaç eklendikten sonra bu ilacı referans eden eski DrugMention'ları bul ve düzelt
        resolved = self._retroactive_resolve(identity)
        if resolved:
            logger.info(f"Retroactive: {resolved} DrugMention -> INTERACTS_WITH ({identity.display_name})")

        logger.success(
            f"[OK] {identity.display_name} — "
            f"{len(interactions)} etkileşim ({len(propagated)} INN), "
            f"{len(chunks)} chunk"
        )
        return IngestionResult(
            status=IngestionStatus.SUCCESS,
            drug_name=identity.display_name,
            canonical_id=identity.canonical_id,
            interaction_count=len(interactions) - len(propagated),
            propagated_count=len(propagated),
        )

    # ------------------------------------------------------------------
    # Toplu ingestion
    # ------------------------------------------------------------------

    def ingest_all(
        self,
        raw_dir: Path = _RAW_KUB_DIR,
        force: bool = False,
    ) -> list[IngestionResult]:
        """data/raw_kub/ altındaki tüm PDF'leri sırayla ingest eder."""
        raw_dir = Path(raw_dir)
        pdfs = sorted(raw_dir.glob("*.pdf"))
        logger.info(f"Toplu ingest: {len(pdfs)} PDF bulundu ({raw_dir})")

        results: list[IngestionResult] = []
        for i, pdf in enumerate(pdfs, 1):
            logger.info(f"[{i}/{len(pdfs)}] {pdf.name}")
            result = self.ingest(pdf, force=force)
            results.append(result)
            _log_result(result)

        # Özet
        ok       = sum(1 for r in results if r.status == IngestionStatus.SUCCESS)
        skipped  = sum(1 for r in results if r.status == IngestionStatus.SKIPPED)
        quarant  = sum(1 for r in results if r.status == IngestionStatus.QUARANTINE)
        failed   = sum(1 for r in results if r.status == IngestionStatus.FAILED)
        logger.info(
            f"\nSonuç: {ok} başarılı, {skipped} atlandı, "
            f"{quarant} karantina, {failed} hata — toplam {len(results)}"
        )
        return results

    # ------------------------------------------------------------------
    # İç yardımcılar
    # ------------------------------------------------------------------

    def _already_exists(self, canonical_id: str) -> bool:
        """ChromaDB'de canonical_id metadata'sı var mı?"""
        try:
            client = get_chroma_client()
            col = get_or_create_collection(client)
            result = col.get(where={"canonical_id": canonical_id}, limit=1)
            return len(result.get("ids", [])) > 0
        except Exception:
            return False

    def _save_parsed_json(self, identity: DrugIdentity, parse_data: dict) -> Path:
        """Parse sonucunu data/parsed_json/ altına kaydeder."""
        _PARSED_JSON_DIR.mkdir(parents=True, exist_ok=True)
        # canonical_id'yi JSON'a ekle
        parse_data["canonical_id"] = identity.canonical_id
        parse_data["normalized_name"] = identity.normalized_name
        json_path = _PARSED_JSON_DIR / f"{identity.normalized_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(parse_data, f, ensure_ascii=False, indent=2)
        return json_path

    def _write_chromadb(self, identity: DrugIdentity, chunks: list[dict]) -> None:
        """Chunk'lara canonical_id ekler ve ChromaDB'ye yazar."""
        for chunk in chunks:
            chunk.setdefault("canonical_id", identity.canonical_id)
        try:
            index_chunks(chunks)
        except Exception as e:
            logger.error(f"ChromaDB yazma hatası ({identity.display_name}): {e}")

    def _write_neo4j_base(
        self,
        identity: DrugIdentity,
        parse_data: dict,
        chunks: list[dict],
    ) -> None:
        """Drug node, Section node'ları ve kontrendikasyon/uyarı ilişkilerini yazar."""
        try:
            upsert_drug_node(
                ilac_adi=identity.display_name,
                kaynak_dosya=parse_data.get("kaynak_dosya", ""),
                etken_madde=identity.inn,
                canonical_id=identity.canonical_id,
            )
            for chunk in chunks:
                upsert_section_node(identity.display_name, chunk)
                madde = chunk.get("madde_no", "")
                if madde == "4.3":
                    extract_contraindications(identity.display_name, chunk)
                if madde == "4.4":
                    extract_warnings(identity.display_name, chunk)
                if madde == "4.2":                          # D: GFR eşikleri
                    extract_dose_adjustments(identity.display_name, chunk)
                if madde in ("4.5", "5.1"):                 # E: CYP450
                    extract_cyp_edges(identity.display_name, chunk)
                if madde == "4.6":                          # F: Gebelik kategorisi
                    extract_pregnancy_category(identity.display_name, chunk)
        except Exception as e:
            logger.error(f"Neo4j base yazma hatası ({identity.display_name}): {e}")

    def _write_interactions_neo4j(self, identity: DrugIdentity, interactions) -> None:
        """INTERACTS_WITH ilişkilerini Neo4j'e yazar. İlaç sınıfları DrugClass node olarak ayrılır."""
        written = 0
        for iw in interactions:
            target_name = iw.drug_b_raw
            try:
                if iw.is_drug_class:
                    # İlaç sınıfları → DrugClass node + INTERACTS_WITH_CLASS ilişkisi
                    run_query(
                        """
                        MATCH (a:Drug)
                        WHERE a.name = $a_name OR a.canonical_id = $a_cid
                        WITH a LIMIT 1
                        MERGE (c:DrugClass {name: $class_name})
                        MERGE (a)-[r:INTERACTS_WITH_CLASS]->(c)
                        SET r.severity     = $severity,
                            r.kaynak_madde = $section,
                            r.confidence   = $confidence
                        """,
                        {
                            "a_name":     identity.display_name,
                            "a_cid":      identity.canonical_id,
                            "class_name": target_name,
                            "severity":   iw.severity,
                            "section":    iw.source_section,
                            "confidence": iw.confidence,
                        },
                    )
                else:
                    run_query(
                        """
                        MATCH (a:Drug)
                        WHERE a.name = $a_name OR a.canonical_id = $a_cid
                        WITH a LIMIT 1
                        MERGE (b_raw:DrugMention {name: $b_name})
                        WITH a, b_raw
                        OPTIONAL MATCH (b:Drug)
                        WHERE b.canonical_id = $b_cid OR toUpper(b.name) STARTS WITH $b_prefix
                        WITH a, b_raw, b LIMIT 1
                        FOREACH (_ IN CASE WHEN b IS NOT NULL THEN [1] ELSE [] END |
                            MERGE (a)-[r:INTERACTS_WITH]->(b)
                            SET r.severity     = $severity,
                                r.kaynak_madde = $section,
                                r.kaynak       = $source,
                                r.confidence   = $confidence,
                                r.mechanism    = $mechanism
                        )
                        FOREACH (_ IN CASE WHEN b IS NULL THEN [1] ELSE [] END |
                            MERGE (a)-[r2:MENTIONS_INTERACTION]->(b_raw)
                            SET r2.severity     = $severity,
                                r2.kaynak_madde = $section
                        )
                        """,
                        {
                            "a_name":     identity.display_name,
                            "a_cid":      identity.canonical_id,
                            "b_name":     target_name,
                            "b_cid":      iw.drug_b_canonical or "",
                            "b_prefix":   target_name.split()[0].upper() if target_name else "",
                            "severity":   iw.severity,
                            "section":    iw.source_section,
                            "source":     "inn_propagated" if iw.is_propagated else "llm_extraction",
                            "confidence": iw.confidence,
                            "mechanism":  iw.mechanism or "",
                        },
                    )
                written += 1
            except Exception as e:
                logger.debug(f"INTERACTS_WITH yazma ({target_name}): {e}")
        logger.debug(f"Neo4j: {written}/{len(interactions)} ilişki yazıldı")

    def _retroactive_resolve(self, identity: DrugIdentity) -> int:
        """
        Yeni eklenen ilacın INN ve adıyla eşleşen eski DrugMention node'larını Drug node'a çevirir.
        MENTIONS_INTERACTION → INTERACTS_WITH olarak güncellenir.
        Döndürülen değer: kaç DrugMention çözüldü.
        """
        resolved = 0
        # Eşleşme kriterleri: yeni ilacın marka adı başlangıcı veya INN tokeni
        inn_tokens = [t for t in (identity.inn or "").lower().split() if len(t) >= 4]
        brand_prefix = identity.display_name.split()[0].upper()

        try:
            # Bu ilacı referans eden DrugMention'ları bul
            result = run_query(
                """
                MATCH (source:Drug)-[r:MENTIONS_INTERACTION]->(m:DrugMention)
                WHERE toUpper(m.name) STARTS WITH $brand_prefix
                   OR any(tok IN $inn_tokens WHERE toLower(m.name) CONTAINS tok)
                RETURN source.name AS src, source.canonical_id AS src_cid,
                       m.name AS mention, r.severity AS sev, r.kaynak_madde AS sec
                """,
                {"brand_prefix": brand_prefix, "inn_tokens": inn_tokens},
            )
            if not result:
                return 0

            for row in result:
                try:
                    run_query(
                        """
                        MATCH (source:Drug)-[r:MENTIONS_INTERACTION]->(m:DrugMention {name: $mention})
                        WHERE source.name = $src OR source.canonical_id = $src_cid
                        WITH source, r, m
                        MATCH (target:Drug)
                        WHERE target.canonical_id = $target_cid
                        MERGE (source)-[r2:INTERACTS_WITH]->(target)
                        SET r2.severity     = $sev,
                            r2.kaynak_madde = $sec,
                            r2.kaynak       = 'retroactive_resolved',
                            r2.confidence   = 0.85
                        DELETE r
                        WITH m
                        WHERE NOT (m)<-[:MENTIONS_INTERACTION]-()
                        DELETE m
                        """,
                        {
                            "src":        row["src"],
                            "src_cid":    row["src_cid"],
                            "mention":    row["mention"],
                            "target_cid": identity.canonical_id,
                            "sev":        row["sev"],
                            "sec":        row["sec"],
                        },
                    )
                    resolved += 1
                except Exception as e:
                    logger.debug(f"Retroactive resolve hatası ({row.get('mention')}): {e}")
        except Exception as e:
            logger.debug(f"Retroactive resolve sorgu hatası: {e}")

        return resolved

    @staticmethod
    def _extract_sections_dict(chunks: list[dict]) -> dict[str, str]:
        """Chunk listesinden madde_no → birleşik içerik dict'i oluşturur."""
        sections: dict[str, str] = {}
        for chunk in chunks:
            sec = chunk.get("madde_no", "")
            if sec:
                sections[sec] = sections.get(sec, "") + chunk.get("icerik", "")
        return sections

    @staticmethod
    def _write_quarantine_report(identity: DrugIdentity, flags: list[str]) -> None:
        _QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        report_path = _QUARANTINE_DIR / f"{identity.normalized_name}_parse_fail.md"
        lines = [
            f"# Karantina: {identity.display_name}",
            f"canonical_id: `{identity.canonical_id}`",
            "",
            "## Sebepler",
            *[f"- {f}" for f in flags],
        ]
        report_path.write_text("\n".join(lines), encoding="utf-8")
        logger.warning(f"Karantina raporu: {report_path}")


# ------------------------------------------------------------------
# Yardımcılar
# ------------------------------------------------------------------

def _log_result(result: IngestionResult) -> None:
    if result.status == IngestionStatus.SUCCESS:
        logger.success(str(result))
    elif result.status == IngestionStatus.SKIPPED:
        logger.debug(str(result))
    elif result.status == IngestionStatus.QUARANTINE:
        logger.warning(str(result))
    else:
        logger.error(str(result))


# ------------------------------------------------------------------
# CLI giriş noktası
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="PharmAssist Ingestion Pipeline")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--pdf",  type=Path, help="Tek PDF dosyası")
    grp.add_argument("--all",  action="store_true", help="Tüm raw_kub/ PDF'leri")
    parser.add_argument("--force",            action="store_true", help="Mevcut kaydı sil, yeniden ingest")
    parser.add_argument("--skip-extraction",  action="store_true", help="LLM extraction atla")
    parser.add_argument("--model",            default="qwen/qwen2.5-coder-14b-instruct")
    parser.add_argument("--raw-dir",          type=Path, default=_RAW_KUB_DIR)
    args = parser.parse_args()

    pipeline = IngestionPipeline(llm_model=args.model, skip_extraction=args.skip_extraction)

    if args.pdf:
        result = pipeline.ingest(args.pdf, force=args.force)
        print(result)
        sys.exit(0 if result.ok else 1)
    else:
        results = pipeline.ingest_all(raw_dir=args.raw_dir, force=args.force)
        failed = sum(1 for r in results if r.status == IngestionStatus.FAILED)
        sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
