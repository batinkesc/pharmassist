"""
reset_databases.py — ChromaDB + Neo4j sıfırlama (yeni pipeline öncesi)

Yapılanlar:
  1. ChromaDB koleksiyonu silinir (chroma_db/)
  2. Neo4j: tüm node ve relationship silinir
  3. data/parsed_json/ temizlenir (pipeline yeniden oluşturur)
  4. data/quarantine/ korunur (referans için)

Kullanım:
  .venv/Scripts/python scripts/reset_databases.py
  .venv/Scripts/python scripts/reset_databases.py --confirm
"""

import argparse
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def reset_chromadb() -> None:
    from src.retrieval.chroma_store import get_chroma_client, COLLECTION_NAME
    print("ChromaDB sifirlanıyor...")
    client = get_chroma_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"  OK: '{COLLECTION_NAME}' koleksiyonu silindi")
    except Exception as e:
        print(f"  WARN: {e}")

    chroma_dir = _ROOT / "chroma_db"
    if chroma_dir.exists():
        try:
            shutil.rmtree(chroma_dir)
            print(f"  OK: {chroma_dir} klasoru silindi")
        except PermissionError:
            print(f"  WARN: {chroma_dir} dosyasi baska process tarafindan kullaniliyor — koleksiyon silindi, klasor korundu (sorun degil)")


def reset_neo4j() -> None:
    from src.graph.neo4j_client import run_query
    print("Neo4j sifirlanıyor...")
    counts = run_query("MATCH (n) RETURN count(n) AS cnt")
    total = counts[0]["cnt"] if counts else 0
    print(f"  Mevcut: {total} node")

    # Batch halinde sil (büyük db'de timeout engeli)
    deleted = 0
    while True:
        result = run_query(
            "MATCH (n) WITH n LIMIT 5000 DETACH DELETE n RETURN count(n) AS cnt"
        )
        batch = result[0]["cnt"] if result else 0
        deleted += batch
        if batch == 0:
            break
    print(f"  OK: {deleted} node silindi")


def reset_parsed_json() -> None:
    parsed_dir = _ROOT / "data" / "parsed_json"
    if not parsed_dir.exists():
        print("parsed_json/ zaten yok")
        return
    files = list(parsed_dir.glob("*.json"))
    for f in files:
        f.unlink()
    print(f"  OK: {len(files)} JSON dosyası silindi (data/parsed_json/)")


def main() -> None:
    parser = argparse.ArgumentParser(description="PharmAssist veritabani sifirlama")
    parser.add_argument("--confirm", action="store_true",
                        help="Onay istemeden dogrudan calistir")
    args = parser.parse_args()

    print("=" * 60)
    print("PharmAssist — Veritabani Sifirlama")
    print("=" * 60)
    print("Bu islem:")
    print("  - ChromaDB koleksiyonunu siler")
    print("  - Neo4j'deki tum node/relationship siler")
    print("  - data/parsed_json/ icindeki JSON'lari siler")
    print("  - data/quarantine/ ve backups/ KORUNUR")
    print()

    if not args.confirm:
        ans = input("Devam etmek istiyor musunuz? (evet/hayir): ").strip().lower()
        if ans not in ("evet", "e", "yes", "y"):
            print("Iptal edildi.")
            sys.exit(0)

    print()
    reset_chromadb()
    print()
    reset_neo4j()
    print()
    reset_parsed_json()
    print()
    print("=" * 60)
    print("Sifirlama tamamlandi.")
    print("Simdi pipeline'i baslatin:")
    print("  .venv/Scripts/python -m src.pipeline.ingestion_pipeline --all")
    print("=" * 60)


if __name__ == "__main__":
    main()
