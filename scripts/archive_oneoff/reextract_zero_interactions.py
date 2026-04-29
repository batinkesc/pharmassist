"""
reextract_zero_interactions.py — 0 etkileşimli ilaçları yeniden işler.

Neo4j'den 0 INTERACTS_WITH/INTERACTS_WITH_CLASS/MENTIONS_INTERACTION olan ilaçları
tespit eder, parsed_json/kaynak_dosya üzerinden doğru PDF'i bulur ve --force ile yeniden ingest eder.

Kullanım:
    .venv/Scripts/python scripts/reextract_zero_interactions.py
    .venv/Scripts/python scripts/reextract_zero_interactions.py --dry-run
"""
import sys, os, argparse, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv; load_dotenv()

from pathlib import Path
from loguru import logger

from src.graph.neo4j_client import run_query
from src.pipeline.ingestion_pipeline import IngestionPipeline, IngestionStatus

_RAW_DIR    = Path("data/raw_pdfs")
_PARSED_DIR = Path("data/parsed_json")


def normalize(s: str) -> str:
    return (s.upper()
            .replace("İ","I").replace("I","I").replace("ı","I")
            .replace("Ö","O").replace("ö","O")
            .replace("Ü","U").replace("ü","U")
            .replace("Ş","S").replace("ş","S")
            .replace("Ğ","G").replace("ğ","G")
            .replace("Ç","C").replace("ç","C"))


def get_zero_interaction_drugs() -> list[str]:
    result = run_query("""
        MATCH (d:Drug)
        WHERE NOT (d)-[:INTERACTS_WITH]->()
          AND NOT (d)-[:INTERACTS_WITH_CLASS]->()
          AND NOT (d)-[:MENTIONS_INTERACTION]->()
        RETURN d.name AS name
        ORDER BY d.name
    """)
    return [r["name"] for r in result]


def build_drug_to_pdf_map() -> dict[str, Path]:
    """
    parsed_json/ klasöründeki tüm JSON'lardaki ilac_adi → kaynak_dosya eşleştirmesini döndürür.
    kaynak_dosya raw_pdfs/ içindeki orijinal PDF adıdır.
    """
    mapping: dict[str, Path] = {}  # normalize(ilac_adi) -> pdf_path

    for jf in _PARSED_DIR.glob("*.json"):
        try:
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        ilac_adi    = data.get("ilac_adi", "")
        kaynak      = data.get("kaynak_dosya", "")
        if not ilac_adi or not kaynak:
            continue

        # PDF dosyasını raw_pdfs içinde bul
        pdf_path = _RAW_DIR / kaynak
        if not pdf_path.exists():
            # Normalize edilmiş isimle dene
            norm_kaynak = normalize(kaynak)
            for pdf in _RAW_DIR.glob("*.pdf"):
                if normalize(pdf.name) == norm_kaynak:
                    pdf_path = pdf
                    break
            else:
                pdf_path = None

        if pdf_path and pdf_path.exists():
            mapping[normalize(ilac_adi)] = pdf_path

    return mapping


def find_pdf_for_drug(drug_name: str, mapping: dict[str, Path]) -> Path | None:
    norm = normalize(drug_name)
    if norm in mapping:
        return mapping[norm]
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Sadece listeyi göster, ingest etme")
    args = parser.parse_args()

    logger.info("0 etkileşimli ilaçlar sorgulanıyor...")
    zero_drugs = get_zero_interaction_drugs()
    logger.info(f"  {len(zero_drugs)} ilaç bulundu")

    logger.info("PDF eşleştirme haritası oluşturuluyor...")
    pdf_map = build_drug_to_pdf_map()
    logger.info(f"  {len(pdf_map)} ilaç-PDF eşleşmesi yüklendi")

    pairs: list[tuple[str, Path]] = []
    no_pdf: list[str] = []

    for drug in zero_drugs:
        pdf = find_pdf_for_drug(drug, pdf_map)
        if pdf:
            pairs.append((drug, pdf))
        else:
            no_pdf.append(drug)

    print("\n" + "=" * 65)
    print(f"YENİDEN İŞLENECEK: {len(pairs)} ilaç")
    print("=" * 65)
    for drug, pdf in pairs:
        print(f"  {drug}")
        print(f"    -> {pdf.name}")

    if no_pdf:
        print(f"\nPDF BULUNAMAYAN: {len(no_pdf)} ilaç")
        for d in no_pdf:
            print(f"  ! {d}")

    if args.dry_run:
        print("\n[DRY RUN] İngest yapılmadı.")
        return

    if not pairs:
        print("İşlenecek ilaç yok.")
        return

    print("\n" + "=" * 65)
    print("YENIDEN EXTRACTION BAŞLIYOR")
    print("=" * 65)

    pipeline = IngestionPipeline()
    ok = fail = quarant = 0

    for i, (drug, pdf) in enumerate(pairs, 1):
        print(f"\n[{i}/{len(pairs)}] {drug}")
        result = pipeline.ingest(pdf, force=True)
        if result.status == IngestionStatus.SUCCESS:
            print(f"  OK  {result.interaction_count} etkilesim")
            ok += 1
        elif result.status == IngestionStatus.QUARANTINE:
            print(f"  QRT {result.quarantine_reason}")
            quarant += 1
        else:
            print(f"  ERR {result.error}")
            fail += 1

    print("\n" + "=" * 65)
    print(f"SONUC: {ok} basarili, {quarant} karantina, {fail} hata — toplam {len(pairs)}")
    print("=" * 65)


if __name__ == "__main__":
    main()
