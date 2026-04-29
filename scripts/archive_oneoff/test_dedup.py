import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from src.graph.graph_retriever import drug_contraindications
from collections import Counter

rows = drug_contraindications("ASPIRIN COMPLEX 500 MG/30 MG ORAL SUSPANSIYON ICIN GRANUL ICEREN SASE")
print(f"ASPIRIN COMPLEX: {len(rows)} satir (beklenen: 6)")
c = Counter(r["kosul"] for r in rows)
for k, v in c.items():
    print(f"  {k}: {v} kez")

rows2 = drug_contraindications("BRUFEN 400 MG FILM TABLET")
print(f"\nBRUFEN: {len(rows2)} satir")
for r in rows2:
    print(f"  {r['kosul']}: {str(r.get('neden',''))[:80]}")
