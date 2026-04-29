"""Mevcut corpus ve graph istatistikleri."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from src.graph.neo4j_client import run_query

print("=== CORPUS DURUMU ===\n")

r = run_query("MATCH (d:Drug) RETURN count(d) as n")
print(f"Drug node: {r[0]['n']}")

r = run_query("MATCH (d:Drug)-[:HAS_SECTION]->(s:Section) WITH d, count(s) as sc WHERE sc > 0 RETURN count(d) as n")
print(f"Section-li ilaç: {r[0]['n']}")

r = run_query("MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) as n")
print(f"INTERACTS_WITH: {r[0]['n']}")

r = run_query("MATCH ()-[r:INTERACTS_WITH]->() WHERE r.severity='unknown' RETURN count(r) as n")
print(f"  unknown severity: {r[0]['n']}")

r = run_query("MATCH ()-[:HAS_WARNING]->() RETURN count(*) as n")
print(f"HAS_WARNING: {r[0]['n']}")

r = run_query("MATCH ()-[:INTERACTS_WITH_CLASS]->() RETURN count(*) as n")
print(f"INTERACTS_WITH_CLASS: {r[0]['n']}")

r = run_query("MATCH ()-[:CONTRAINDICATED_FOR]->() RETURN count(*) as n")
print(f"CONTRAINDICATED_FOR: {r[0]['n']}")

print("\n=== GFR/DOZ THRESHOLD (D hazırlık) ===")
r = run_query("""
    MATCH (d:Drug)-[:HAS_SECTION]->(s:Section)
    WHERE s.madde_no = '4.2' AND toLower(s.icerik) CONTAINS 'gfr'
    RETURN count(d) as n
""")
print(f"  GFR geçen 4.2 bölümü olan ilaç: {r[0]['n']}")

r = run_query("""
    MATCH (d:Drug)-[:HAS_SECTION]->(s:Section)
    WHERE s.madde_no = '4.2' AND (
        toLower(s.icerik) CONTAINS 'böbrek' OR
        toLower(s.icerik) CONTAINS 'renal'
    )
    RETURN count(d) as n
""")
print(f"  Böbrek/renal geçen 4.2 bölümü: {r[0]['n']}")

print("\n=== GEBELİK KATEGORISI (F hazırlık) ===")
r = run_query("""
    MATCH (d:Drug)-[:HAS_SECTION]->(s:Section)
    WHERE s.madde_no = '4.6'
    RETURN count(d) as n
""")
print(f"  4.6 bölümü olan ilaç: {r[0]['n']}")

r = run_query("""
    MATCH (d:Drug)-[:HAS_SECTION]->(s:Section)
    WHERE s.madde_no = '4.6' AND (
        toLower(s.icerik) CONTAINS 'kategori' OR
        toLower(s.icerik) CONTAINS 'fda'
    )
    RETURN count(d) as n
""")
print(f"  4.6'da kategori/FDA geçen: {r[0]['n']}")

print("\n=== CYP450 COVERAGE (E hazırlık) ===")
r = run_query("""
    MATCH (d:Drug)-[:HAS_SECTION]->(s:Section)
    WHERE s.madde_no IN ['4.5', '5.1'] AND toLower(s.icerik) CONTAINS 'cyp'
    RETURN count(DISTINCT d) as n
""")
print(f"  CYP geçen 4.5/5.1 bölümü olan ilaç: {r[0]['n']}")

print("\n=== DRUG NODE LİSTESİ (alfabetik) ===")
r = run_query("MATCH (d:Drug) RETURN d.name as n, d.etken_madde as e ORDER BY d.name")
for row in r:
    print(f"  {row['n'][:50]:<50} | {str(row.get('e',''))[:30]}")
