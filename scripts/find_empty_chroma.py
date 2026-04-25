"""ChromaDB'de az chunk'lı ilaçları bul — resim bazlı PDF kaynaklı boş içerik."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()

from src.retrieval.chroma_store import get_chroma_client, get_or_create_collection
from collections import Counter

client = get_chroma_client()
col = get_or_create_collection(client)

# Tüm chunk'ları çek (sadece metadata)
result = col.get(include=["metadatas"])
metadatas = result["metadatas"]

print(f"ChromaDB toplam chunk: {len(metadatas)}\n")

# İlaç başına chunk sayısını say
ilac_chunk = Counter()
for m in metadatas:
    ilac_adi = m.get("ilac_adi") or m.get("drug_name") or "BILINMIYOR"
    # İlacın kısa adını al (ilk 40 char)
    ilac_chunk[ilac_adi[:50]] += 1

print(f"Farklı ilaç: {len(ilac_chunk)}\n")

# Az chunk'lı ilaçlar (şüpheli)
az_chunk = [(ilac, cnt) for ilac, cnt in sorted(ilac_chunk.items(), key=lambda x: x[1]) if cnt <= 5]
print(f"=== <= 5 chunk'lı ilaçlar ({len(az_chunk)} adet) — muhtemelen resim bazlı ===")
for ilac, cnt in az_chunk:
    print(f"  [{cnt:2d} chunk] {ilac}")

orta = [(ilac, cnt) for ilac, cnt in sorted(ilac_chunk.items(), key=lambda x: x[1]) if 6 <= cnt <= 10]
print(f"\n=== 6-10 chunk'lı ilaçlar ({len(orta)} adet) — zayıf içerik ===")
for ilac, cnt in orta[:20]:
    print(f"  [{cnt:2d} chunk] {ilac}")

normal = sum(1 for cnt in ilac_chunk.values() if cnt > 10)
print(f"\nNormal (>10 chunk): {normal} ilaç")
print(f"Zayıf (<=5 chunk):  {len(az_chunk)} ilaç")
print(f"Orta (6-10 chunk):  {len(orta)} ilaç")
