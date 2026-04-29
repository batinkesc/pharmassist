"""Az section'lı ilaçları bul — muhtemelen resim bazlı PDF kaynaklı."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from src.graph.neo4j_client import run_query

r = run_query("""
    MATCH (d:Drug)
    OPTIONAL MATCH (d)-[:HAS_SECTION]->(s:Section)
    WITH d, count(s) as sc
    ORDER BY sc, d.name
    RETURN d.name as ilac, d.etken_madde as etken, sc as section_sayisi
""")

print(f"Toplam Drug node: {len(r)}\n")

esikler = [(0, "SIFIR section"), (1, "1 section"), (2, "2 section"), (3, "3 section")]
for esik, etiket in esikler:
    grup = [row for row in r if row["section_sayisi"] == esik]
    if grup:
        print(f"=== {etiket} ({len(grup)} ilaç) ===")
        for row in grup:
            print(f"  {row['ilac'][:55]:<55} | {str(row.get('etken',''))[:25]}")
        print()

# 4-5 section da şüpheli olabilir (normal KÜB 10+ section içerir)
az = [row for row in r if row["section_sayisi"] <= 5]
print(f"\nToplam <= 5 section: {len(az)} ilaç")
print(f"Normal (>= 6 section): {len(r) - len(az)} ilaç")
