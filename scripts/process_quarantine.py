"""
Karantinada bekleyen resim bazlı PDF'leri Claude Vision OCR ile işler.

Kullanım:
    .venv/Scripts/python scripts/process_quarantine.py
    .venv/Scripts/python scripts/process_quarantine.py --dry-run   # sadece listele
    .venv/Scripts/python scripts/process_quarantine.py --limit 5   # ilk 5'i işle

Akış:
    1. data/quarantine/*_OCR_GEREKLI.md dosyalarından PDF adlarını çıkar
    2. Her PDF için KUBParser(use_vision_ocr=True) ile parse et
    3. Parse QA geçerse → parsed_json + ChromaDB + Neo4j'e yükle
    4. Başarılı olanların karantina raporlarını sil
    5. Sonuç özeti yaz
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from loguru import logger
from src.ingestion.pdf_parser import KUBParser, _slugify, ImageBasedPDFError
from src.retrieval.chroma_store import index_chunks, get_chroma_client, get_or_create_collection
from src.graph.kub_to_graph import (
    upsert_drug_node, upsert_section_node,
    extract_contraindications, extract_interactions, extract_warnings,
)

QUARANTINE_DIR  = ROOT / "data" / "quarantine"
PARSED_JSON_DIR = ROOT / "data" / "parsed_json"
RAW_PDF_DIR     = ROOT / "data" / "raw_pdfs"


def _parse_qa(result: dict) -> tuple[bool, list[str]]:
    """Parse QA — bulk_ingest.py ile aynı kriterler."""
    hatalar = []
    chunks = result.get("chunks", [])
    maddeler = {c["madde_no"] for c in chunks}

    if "4.3" not in maddeler:
        hatalar.append("4.3 (Kontrendikasyonlar) bölümü bulunamadı")
    if "4.5" not in maddeler:
        hatalar.append("4.5 (Etkileşimler) bölümü bulunamadı")

    ilac_adi = result.get("ilac_adi", "")
    if not ilac_adi or ilac_adi == "Bilinmeyen İlaç":
        hatalar.append("İlaç adı çıkarılamadı")

    toplam_icerik = sum(len(c.get("icerik", "")) for c in chunks)
    if toplam_icerik < 500:
        hatalar.append(f"Toplam içerik çok kısa: {toplam_icerik} char")

    return len(hatalar) == 0, hatalar


def _load_to_neo4j(ilac_adi: str, kaynak: str, etken: str, chunks: list[dict]) -> None:
    upsert_drug_node(ilac_adi, kaynak, etken)
    for chunk in chunks:
        upsert_section_node(ilac_adi, chunk)
        madde = chunk.get("madde_no", "")
        if madde == "4.3":
            extract_contraindications(ilac_adi, chunk)
        elif madde == "4.5":
            extract_interactions(ilac_adi, chunk)
        elif madde == "4.4":
            extract_warnings(ilac_adi, chunk)


def main(dry_run: bool = False, limit: int = 0) -> None:
    # Karantina raporlarından PDF adlarını bul
    ocr_reports = sorted(QUARANTINE_DIR.glob("*_OCR_GEREKLI.md"))
    if not ocr_reports:
        logger.info("Karantinada OCR_GEREKLI rapor yok. Çıkılıyor.")
        return

    logger.info(f"{len(ocr_reports)} OCR_GEREKLI rapor bulundu.")

    # PDF adlarını rapor adından çıkar
    pending: list[tuple[Path, Path]] = []
    for report in ocr_reports:
        stem = report.stem.replace("_OCR_GEREKLI", "")
        # raw_pdfs içinde eşleşen PDF'i bul (encoding farkı olabilir)
        matches = list(RAW_PDF_DIR.glob(f"{stem}.pdf"))
        if not matches:
            # Büyük/küçük harf farkı için ikinci deneme
            matches = [p for p in RAW_PDF_DIR.glob("*.pdf") if p.stem == stem]
        if matches:
            pending.append((matches[0], report))
        else:
            logger.warning(f"PDF bulunamadı: {stem}.pdf — atlanıyor")

    if limit > 0:
        pending = pending[:limit]

    logger.info(f"İşlenecek PDF: {len(pending)}")

    if dry_run:
        for pdf_path, report in pending:
            logger.info(f"  [DRY] {pdf_path.name}")
        return

    parser = KUBParser(use_vision_ocr=True)

    basarili = 0
    karantina = 0
    hata = 0

    for i, (pdf_path, report_path) in enumerate(pending, 1):
        logger.info(f"\n[{i}/{len(pending)}] {pdf_path.name}")

        # Parse
        try:
            result = parser.parse(pdf_path)
        except ImageBasedPDFError as e:
            logger.error(f"  ✗ Vision OCR başarısız: {e}")
            hata += 1
            continue
        except Exception as e:
            logger.error(f"  ✗ Parse hatası: {e}")
            hata += 1
            continue

        # QA
        gecti, hatalar = _parse_qa(result)
        if not gecti:
            logger.warning(f"  ✗ QA başarısız: {hatalar}")
            karantina += 1
            continue

        ilac_adi  = result["ilac_adi"]
        etken     = result.get("etken_madde", "")
        kaynak    = pdf_path.name
        chunks    = result["chunks"]

        logger.info(f"  ✓ QA geçti: {ilac_adi} ({len(chunks)} chunk)")

        # JSON kaydet
        slug = _slugify(ilac_adi)
        json_path = PARSED_JSON_DIR / f"{slug}.json"
        import json
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"  → JSON: {json_path.name}")

        # ChromaDB
        try:
            index_chunks(chunks, reset=False)
            logger.info(f"  → ChromaDB yüklendi")
        except Exception as e:
            logger.error(f"  ChromaDB hatası: {e}")

        # Neo4j
        try:
            _load_to_neo4j(ilac_adi, kaynak, etken, chunks)
            logger.info(f"  → Neo4j yüklendi")
        except Exception as e:
            logger.error(f"  Neo4j hatası: {e}")

        # Karantina raporunu sil
        report_path.unlink(missing_ok=True)
        logger.info(f"  → Karantina raporu silindi: {report_path.name}")

        basarili += 1

    # Özet
    logger.info(f"\n{'='*55}")
    logger.info(f"SONUÇ: ✓ {basarili} başarılı | ✗ {karantina} QA başarısız | ⚡ {hata} hata")

    if basarili > 0:
        col = get_or_create_collection(get_chroma_client())
        logger.info(f"ChromaDB toplam: {col.count()} chunk")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Karantina OCR işleyici")
    parser.add_argument("--dry-run", action="store_true", help="Sadece listele")
    parser.add_argument("--limit", type=int, default=0, help="Max işlenecek PDF sayısı")
    args = parser.parse_args()
    main(dry_run=args.dry_run, limit=args.limit)
