"""
Neo4j graf yükleme scripti.

Kullanım:
  python scripts/load_graph.py               # Tam yükleme (reset=True)
  python scripts/load_graph.py --update-only  # Sadece etken_madde + INTERACTS_WITH güncelle (node silmez)
"""
import sys, os, argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="DEBUG")

from src.graph.kub_to_graph import load_all_drugs, build_interacts_with_from_sections
from src.graph.graph_retriever import graph_stats, drug_summary, drug_contraindications, drug_interactions
from src.graph.neo4j_client import run_query

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-only", action="store_true",
                        help="Mevcut node'ları silmeden etken_madde ve INTERACTS_WITH güncelle")
    args = parser.parse_args()

    if args.update_only:
        # --update-only: sadece Drug node'larına etken_madde property ekle + cross-reference çalıştır
        logger.info("--update-only modu: Drug node'lar korunuyor, etken_madde + INTERACTS_WITH güncelleniyor...")
        import json
        from pathlib import Path
        from src.graph.kub_to_graph import upsert_drug_node

        json_files = list(Path("data/parsed_json").glob("*.json"))
        for jf in json_files:
            data = json.loads(jf.read_text(encoding="utf-8"))
            ilac_adi     = data.get("ilac_adi", jf.stem)
            kaynak_dosya = data.get("kaynak_dosya", jf.name)
            etken_madde  = data.get("etken_madde", "")
            upsert_drug_node(ilac_adi, kaynak_dosya, etken_madde)

        logger.info(f"{len(json_files)} Drug node'u etken_madde ile güncellendi.")
        build_interacts_with_from_sections("data/parsed_json")
    else:
        # Tam yükleme (reset=True → temiz başlangıç)
        load_all_drugs("data/parsed_json", reset=True)

    # İstatistikler
    print("\n=== Graf İstatistikleri ===")
    stats = graph_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # INTERACTS_WITH sayısı
    r = run_query("MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) AS cnt")
    print(f"  interacts_with_count: {r[0]['cnt'] if r else '?'}")

    # PLASORİN etkileşimleri
    print("\n=== PLASORİN Etkileşimleri ===")
    for row in drug_interactions("PLASORİN 10 mg tablet"):
        print(f"  - {row['etkilesen_ilac']}")

    # PLAVIX etkileşimleri
    print("\n=== PLAVIX Etkileşimleri ===")
    for row in drug_interactions("PLAVIX® 75 mg film kaplı tablet"):
        print(f"  - {row['etkilesen_ilac']}")
