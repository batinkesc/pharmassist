"""
Dalga 2 — Toplu KÜB Yükleme Scripti (Faz 10)

DISABLED: This script was causing unauthorized API charges via vision_ocr.py
Contact user before re-enabling.

Kullanım:
    .venv/Scripts/python scripts/bulk_ingest.py [--reset] [--pdf-dir data/raw_pdfs]

Akış:
    1. raw_pdfs/ içindeki tüm PDF'leri parse et
    2. Her parse sonucu için Parse QA kontrolü yap
       ✓ geçen  → parsed_json/ kaydet + ChromaDB + Neo4j yükle
       ✗ geçemeyen → data/quarantine/ altına rapor yaz, sisteme ekleme
    3. Özet raporu ekrana bas
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Proje kökünü Python path'e ekle
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.ingestion.pdf_parser import KUBParser, _slugify, ImageBasedPDFError
from src.retrieval.chroma_store import load_all_chunks, index_chunks, get_chroma_client, get_or_create_collection
from src.graph.kub_to_graph import load_all_drugs
from src.data.normalization import normalize_drug_name


# ---------------------------------------------------------------------------
# Parse QA kriterleri — Phase 0 güçlendirilmiş versiyon
# ---------------------------------------------------------------------------

import re as _re

QA_MIN_SECTION_CHARS = 100      # 4.3 ve 4.5 minimum karakter
QA_MIN_TOTAL_CHARS   = 500      # Toplam içerik minimum
QA_CRITICAL_SECTIONS = ["4.3", "4.5"]   # Bu bölümler zorunlu
QA_SECTION_INTEGRITY_RE = _re.compile(   # Bölüm bütünlüğü: yanlış madde başlığı
    r"^\s*4\.([1-9])\s+[A-ZÇĞİÖŞÜ]", _re.MULTILINE
)


def parse_qa(result: dict) -> tuple[bool, list[str]]:
    """
    Parse sonucunu kalite kontrolünden geçirir (Phase 0 güçlendirilmiş).

    Kontroller:
      1. İlaç adı tespit edildi mi?
      2. Toplam içerik yeterli mi?
      3. Zorunlu bölümler (4.3, 4.5) var ve yeterince uzun mu?
      4. Bölüm bütünlüğü: chunk içinde yanlış madde başlığı var mı?
      5. İmza kodu temizlendi mi?

    Returns:
        (geçti: bool, uyarı_listesi: list[str])
    """
    hatalar  = []
    uyarilar = []   # Geçişi engellemez ama raporlanır
    chunks   = result.get("chunks", [])
    ilac_adi = result.get("ilac_adi", "")

    # 1. İlaç adı
    if not ilac_adi or ilac_adi in ("Bilinmeyen İlaç", "UNKNOWN", ""):
        hatalar.append(f"İlaç adı tespit edilemedi: '{ilac_adi}'")

    # 2. Toplam içerik
    ana_chunks = [c for c in chunks if not c.get("alt_madde") and c["madde_no"] != "ozel_uyari"]
    toplam = sum(len(c.get("icerik", "")) for c in ana_chunks)
    if toplam < QA_MIN_TOTAL_CHARS:
        hatalar.append(f"Toplam içerik çok az: {toplam} char (min {QA_MIN_TOTAL_CHARS})")

    # 3. Zorunlu bölümler
    for bolum_no in QA_CRITICAL_SECTIONS:
        bolum_chunks = [c for c in chunks if c["madde_no"] == bolum_no]
        if not bolum_chunks:
            hatalar.append(f"Bölüm {bolum_no} bulunamadı")
            continue
        icerik = " ".join(c.get("icerik", "") for c in bolum_chunks)
        if len(icerik) < QA_MIN_SECTION_CHARS:
            hatalar.append(
                f"Bölüm {bolum_no} çok kısa: {len(icerik)} char (min {QA_MIN_SECTION_CHARS})"
            )

    # 4. Bölüm bütünlüğü — chunk kendi maddesinden farklı 4.x başlığı içermemeli
    for c in ana_chunks:
        madde_no = c.get("madde_no", "")
        if not madde_no.startswith("4."):
            continue
        ana_no = ".".join(madde_no.split(".")[:2])   # "4.2.1" → "4.2"
        icerik = c.get("icerik", "")
        yabanci = [
            f"4.{m}" for m in QA_SECTION_INTEGRITY_RE.findall(icerik)
            if f"4.{m}" != ana_no
        ]
        if yabanci:
            uyarilar.append(
                f"Bölüm bütünlüğü: {madde_no} chunk içinde {list(set(yabanci))} başlığı var"
            )

    # 5. İmza kodu kalıntısı
    for c in chunks:
        if "Belge Doğrulama Kodu" in c.get("icerik", ""):
            hatalar.append(f"İmza kodu temizlenemedi: madde {c['madde_no']}")
            break

    gecti = len(hatalar) == 0
    return gecti, hatalar + [f"[UYARI] {u}" for u in uyarilar]


def write_quarantine_report(ilac_adi: str, pdf_name: str, hatalar: list[str]) -> Path:
    """Başarısız parse için karantina raporu yazar."""
    quarantine_dir = Path("data/quarantine")
    quarantine_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(ilac_adi or pdf_name)
    report_path = quarantine_dir / f"{slug}_parse_fail.md"

    lines = [
        f"# Parse QA Başarısız: {ilac_adi or pdf_name}",
        f"",
        f"**PDF Dosyası:** `{pdf_name}`  ",
        f"**Tarih:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"",
        f"## Tespit Edilen Sorunlar",
        "",
    ]
    for i, hata in enumerate(hatalar, 1):
        lines.append(f"{i}. {hata}")

    lines += [
        "",
        "## Ne Yapmalı",
        "",
        "- PDF'in TİTCK formatında tam KÜB olduğunu doğrula",
        "- 4.3 (Kontrendikasyonlar) ve 4.5 (Etkileşimler) bölümlerinin metinde geçtiğini kontrol et",
        "- Gerekirse farklı kaynak PDF kullan",
        "- Sorun giderildikten sonra `bulk_ingest.py` tekrar çalıştır",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# ChromaDB incremental yükleme (tek ilaç için)
# ---------------------------------------------------------------------------

def index_single_drug(chunks: list[dict], batch_size: int = 32) -> int:
    """
    Tek bir ilaca ait chunk'ları ChromaDB'ye yükler (incremental).
    Zaten mevcut chunk'lar atlanır.

    Returns:
        Eklenen chunk sayısı
    """
    from src.retrieval.chroma_store import (
        get_chroma_client, get_or_create_collection, _chunk_to_metadata
    )
    from src.processing.embedder import embed_chunks

    client = get_chroma_client()
    collection = get_or_create_collection(client)

    existing_ids = set(collection.get()["ids"])
    new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]

    if not new_chunks:
        return 0

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

    return len(new_chunks)


# ---------------------------------------------------------------------------
# Ana akış
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="PharmAssist Dalga 2 — Toplu KÜB Yükleme")
    parser.add_argument(
        "--pdf-dir", default="data/raw_pdfs",
        help="KÜB PDF'lerinin bulunduğu klasör (default: data/raw_pdfs)"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="ChromaDB koleksiyonunu sıfırdan başlat (mevcut chunk'ları sil)"
    )
    parser.add_argument(
        "--skip-graph", action="store_true",
        help="Neo4j yüklemesini atla (sadece ChromaDB)"
    )
    parser.add_argument(
        "--qa-only", action="store_true",
        help="Sadece Parse QA çalıştır, yükleme yapma"
    )
    args = parser.parse_args()

    pdf_dir = Path(args.pdf_dir)
    parsed_dir = Path("data/parsed_json")
    parsed_dir.mkdir(parents=True, exist_ok=True)

    # Önceki çalıştırmadan kalan stale karantina raporlarını temizle
    quarantine_dir = Path("data/quarantine")
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    stale = list(quarantine_dir.glob("*_parse_fail.md"))
    if stale:
        for f in stale:
            f.unlink()
        logger.info(f"Önceki çalıştırmadan {len(stale)} stale karantina raporu silindi.")

    if not pdf_dir.exists():
        logger.error(f"PDF dizini bulunamadı: {pdf_dir}")
        sys.exit(1)

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"PDF bulunamadı: {pdf_dir}")
        sys.exit(0)

    logger.info(f"{'='*60}")
    logger.info(f"PharmAssist Dalga 2 — Toplu KÜB Yükleme")
    logger.info(f"PDF dizini: {pdf_dir} ({len(pdf_files)} dosya)")
    logger.info(f"Mod: {'QA-only' if args.qa_only else 'Parse + ChromaDB' + ('' if args.skip_graph else ' + Neo4j')}")
    logger.info(f"ChromaDB reset: {args.reset}")
    logger.info(f"{'='*60}\n")

    # ChromaDB reset (istenirse)
    if args.reset and not args.qa_only:
        from src.retrieval.chroma_store import get_chroma_client, COLLECTION_NAME
        client = get_chroma_client()
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info("ChromaDB koleksiyonu sıfırlandı.")
        except Exception as e:
            logger.warning(f"Koleksiyon silinemedi (zaten yok olabilir): {e}")

    # İstatistikler
    sonuclar = {
        "toplam_pdf": len(pdf_files),
        "basarili": [],
        "karantina": [],
        "hata": [],
    }

    kub_parser = KUBParser()

    for idx, pdf_path in enumerate(pdf_files, 1):
        logger.info(f"[{idx}/{len(pdf_files)}] {pdf_path.name}")

        # Parse
        try:
            result = kub_parser.parse(pdf_path)
        except ImageBasedPDFError as e:
            # Vision OCR denendi ama yeterli metin çıkarılamadı (PDF kalitesi çok düşük)
            logger.warning(f"  ✗ Vision OCR başarısız: {pdf_path.name}")
            rapor_path = Path("data/quarantine") / f"{pdf_path.stem}_OCR_BASARISIZ.md"
            rapor_path.parent.mkdir(parents=True, exist_ok=True)
            rapor_path.write_text(
                f"# Vision OCR Başarısız: {pdf_path.name}\n\n"
                f"**Sorun:** {e}\n\n"
                f"**Yapılan:** Claude Haiku Vision OCR denendi ancak "
                f"yeterli metin çıkarılamadı.\n\n"
                f"**Olası Nedenler:**\n"
                f"- PDF kalitesi çok düşük (bulanık tarama)\n"
                f"- Çok küçük yazı tipi\n"
                f"- Sayfa boyutu tanınamıyor\n\n"
                f"**Sonraki Adım:** Farklı kaynak PDF dene veya elle metin gir.\n",
                encoding="utf-8",
            )
            sonuclar["karantina"].append({
                "pdf": pdf_path.name, "ilac_adi": "?",
                "hatalar": [str(e)], "rapor": str(rapor_path),
            })
            continue
        except Exception as e:
            logger.error(f"  ✗ Parse hatası: {e}")
            sonuclar["hata"].append({"pdf": pdf_path.name, "hata": str(e)})
            continue

        # Duplicate: parse() None döndürür → atla
        if result is None:
            sonuclar["duplicate"] = sonuclar.get("duplicate", 0) + 1
            continue

        ilac_adi = result.get("ilac_adi", "")

        # 🔧 NORMALIZASYON: Trademark sembolü, Unicode ve whitespace temizle
        ilac_adi_clean = normalize_drug_name(ilac_adi)
        if ilac_adi != ilac_adi_clean:
            logger.debug(f"  [NORM] '{ilac_adi}' → '{ilac_adi_clean}'")
            ilac_adi = ilac_adi_clean
            result["ilac_adi"] = ilac_adi_clean

        # Parse QA
        gecti, hatalar = parse_qa(result)

        if not gecti:
            logger.warning(f"  ✗ QA başarısız: {ilac_adi}")
            for h in hatalar:
                logger.warning(f"    → {h}")
            report = write_quarantine_report(ilac_adi, pdf_path.name, hatalar)
            logger.warning(f"  → Karantina raporu: {report}")
            sonuclar["karantina"].append({
                "pdf": pdf_path.name,
                "ilac_adi": ilac_adi,
                "hatalar": hatalar,
                "rapor": str(report),
            })
            continue

        logger.info(f"  ✓ QA geçti: {ilac_adi} ({len(result['chunks'])} chunk)")

        if args.qa_only:
            sonuclar["basarili"].append({"pdf": pdf_path.name, "ilac_adi": ilac_adi})
            continue

        # JSON kaydet
        slug = _slugify(ilac_adi)
        json_path = parsed_dir / f"{slug}.json"
        kub_parser.save_json(result, json_path)

        # ChromaDB'ye yükle
        try:
            eklenen = index_single_drug(result["chunks"])
            if eklenen > 0:
                logger.info(f"  ✓ ChromaDB: +{eklenen} chunk")
            else:
                logger.info(f"  ↩ ChromaDB: zaten yüklü, atlandı")
        except Exception as e:
            logger.error(f"  ✗ ChromaDB hatası: {e}")
            sonuclar["hata"].append({"pdf": pdf_path.name, "ilac_adi": ilac_adi, "hata": str(e)})
            continue

        sonuclar["basarili"].append({
            "pdf": pdf_path.name,
            "ilac_adi": ilac_adi,
            "chunk_sayisi": len(result["chunks"]),
        })

    # Neo4j toplu yükleme (başarılı tüm ilaçlar için, tek seferde)
    if not args.qa_only and not args.skip_graph and sonuclar["basarili"]:
        logger.info(f"\nNeo4j'e yükleniyor ({len(sonuclar['basarili'])} ilaç)...")
        try:
            load_all_drugs(str(parsed_dir), reset=args.reset)
            logger.info("  ✓ Neo4j yükleme tamamlandı")
        except Exception as e:
            logger.error(f"  ✗ Neo4j yükleme hatası: {e}")

    # Özet raporu
    logger.info(f"\n{'='*60}")
    logger.info(f"ÖZET RAPOR — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"{'='*60}")
    logger.info(f"Toplam PDF         : {sonuclar['toplam_pdf']}")
    logger.info(f"✓ Başarılı yükleme : {len(sonuclar['basarili'])}")
    logger.info(f"✗ Karantinaya alındı: {len(sonuclar['karantina'])}")
    logger.info(f"✗ Parse hatası     : {len(sonuclar['hata'])}")

    if sonuclar["basarili"]:
        logger.info(f"\nYüklenen ilaçlar:")
        for s in sonuclar["basarili"]:
            chunk_bilgi = f" ({s.get('chunk_sayisi', '?')} chunk)" if not args.qa_only else ""
            logger.info(f"  ✓ {s['ilac_adi']}{chunk_bilgi}")

    if sonuclar["karantina"]:
        logger.info(f"\nKarantinaya alınanlar:")
        for k in sonuclar["karantina"]:
            logger.info(f"  ✗ {k['ilac_adi']} → {k['rapor']}")

    if sonuclar["hata"]:
        logger.info(f"\nParse hataları:")
        for h in sonuclar["hata"]:
            logger.info(f"  ✗ {h['pdf']}: {h['hata']}")

    # ChromaDB toplam
    if not args.qa_only:
        try:
            from src.retrieval.chroma_store import get_chroma_client, get_or_create_collection
            col = get_or_create_collection(get_chroma_client())
            logger.info(f"\nChromaDB toplam chunk: {col.count()}")
        except Exception:
            pass

    logger.info(f"{'='*60}")

    # DB sağlık kontrolü — bulk_ingest sonrası otomatik çalış
    if not args.qa_only and sonuclar["basarili"]:
        logger.info("\nDB sağlık kontrolü çalıştırılıyor...")
        import subprocess
        import sys as _sys
        result = subprocess.run(
            [_sys.executable, str(Path(__file__).parent / "db_health_check.py")],
            capture_output=False,
        )
        if result.returncode != 0:
            logger.warning("DB sağlık kontrolü FAIL ile tamamlandı — loglara bakın.")


if __name__ == "__main__":
    main()
