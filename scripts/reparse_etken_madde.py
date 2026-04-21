"""
Mevcut parsed JSON'lara etken_madde alanı ekler.

Her JSON için:
  1. etken_madde alanı zaten varsa atla
  2. Yoksa kaynak PDF'i yeniden parse et, etken_madde'yi çıkar
  3. JSON'ı güncelle (diğer alanlar değişmez)

Kullanım:
    python scripts/reparse_etken_madde.py
    python scripts/reparse_etken_madde.py --force   # var olanları da güncelle
"""

import json
import sys
import argparse
from pathlib import Path

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from src.ingestion.pdf_parser import _extract_etken_madde
import pymupdf


def get_etken_madde_from_pdf(pdf_path: Path) -> str:
    """PDF'den etken_madde metnini çıkarır."""
    try:
        doc = pymupdf.open(str(pdf_path))
        # Madde 2 genellikle ilk 4-5 sayfada — 4000 karakter yeterli
        full_text = ""
        for i, page in enumerate(doc):
            full_text += page.get_text()
            if len(full_text) >= 4000:
                break
        doc.close()
        return _extract_etken_madde(full_text[:4000])
    except Exception as e:
        logger.warning(f"PDF okuma hatası ({pdf_path.name}): {e}")
        return ""


def main():
    parser = argparse.ArgumentParser(description="JSON'lara etken_madde alanı ekle")
    parser.add_argument("--force", action="store_true",
                        help="Zaten etken_madde olan JSON'ları da güncelle")
    args = parser.parse_args()

    json_dir = Path("data/parsed_json")
    pdf_dir  = Path("data/raw_pdfs")

    json_files = sorted(json_dir.glob("*.json"))
    logger.info(f"Toplam {len(json_files)} JSON dosyası bulundu.")

    updated = 0
    skipped = 0
    failed  = 0
    empty   = 0

    for json_path in json_files:
        data = json.loads(json_path.read_text(encoding="utf-8"))

        # etken_madde zaten varsa atla (--force yoksa)
        if not args.force and "etken_madde" in data:
            skipped += 1
            continue

        kaynak = data.get("kaynak_dosya", "")
        pdf_path = pdf_dir / kaynak

        if not pdf_path.exists():
            logger.warning(f"PDF bulunamadı: {kaynak} ({data.get('ilac_adi', '?')})")
            data["etken_madde"] = ""
            failed += 1
        else:
            etken = get_etken_madde_from_pdf(pdf_path)
            data["etken_madde"] = etken
            if etken:
                logger.info(f"  {data.get('ilac_adi', json_path.stem)[:45]:45s} → {etken[:60]}")
                updated += 1
            else:
                logger.warning(f"  {data.get('ilac_adi', json_path.stem)[:45]:45s} → [BOŞ — etken madde bulunamadı]")
                empty += 1

        # JSON'ı kaydet (ilac_adi hemen altına etken_madde gelsin)
        ordered = {"ilac_adi": data.pop("ilac_adi"), "etken_madde": data.pop("etken_madde", "")}
        ordered.update(data)
        json_path.write_text(
            json.dumps(ordered, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    logger.info("─" * 60)
    logger.info(f"Güncellendi : {updated}")
    logger.info(f"Boş kaldı  : {empty}  (PDF parse edildi ama etken madde bulunamadı)")
    logger.info(f"PDF yok    : {failed} (kaynak PDF eksik)")
    logger.info(f"Atlandı    : {skipped} (etken_madde zaten mevcut)")
    logger.info(f"Toplam     : {len(json_files)}")

    if empty > 0:
        logger.warning("Boş kalan JSON'ları kontrol et — Madde 2 formatı farklı olabilir.")


if __name__ == "__main__":
    main()
