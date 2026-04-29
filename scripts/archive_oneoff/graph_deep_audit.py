"""Graf derinlemesine analiz — ne var, ne kullanılıyor, ne eksik."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from src.graph.neo4j_client import run_query

print("=== RELATIONSHIP PROPERTY KEYS ===")
for rel in ["INTERACTS_WITH", "CONTRAINDICATED_FOR", "HAS_WARNING", "INTERACTS_WITH_CLASS", "HAS_SECTION"]:
    r = run_query(f"MATCH ()-[r:{rel}]->() RETURN keys(r) as k LIMIT 1")
    print(f"  {rel}: {r[0]['k'] if r else 'yok'}")

print("\n=== HAS_WARNING SAMPLE (kullanılmıyor!) ===")
r = run_query("MATCH (d:Drug)-[:HAS_WARNING]->(w:Warning) RETURN d.name as n, w.ozet as o LIMIT 4")
for row in r:
    print(f"  [{row['n'][:35]}] {row['o'][:90]}")

print("\n=== INTERACTS_WITH_CLASS (kullanılmıyor!) ===")
r = run_query("MATCH (d:Drug)-[r:INTERACTS_WITH_CLASS]->(c) RETURN d.name as d, c.name as c, r.severity as s LIMIT 5")
for row in r:
    print(f"  {row['d'][:35]} → {row['c']} [{row['s']}]")

print("\n=== severity=contraindicated INTERACTS_WITH ===")
r = run_query("MATCH (a:Drug)-[r:INTERACTS_WITH]->(b:Drug) WHERE r.severity='contraindicated' RETURN a.name as a, b.name as b, r.mechanism as m LIMIT 5")
for row in r:
    print(f"  {row['a'][:30]} ↔ {row['b'][:30]} | mec: {str(row['m'])[:50]}")

print("\n=== SECTION NODE — kullanılabilecek alanlar ===")
r = run_query("MATCH (s:Section) RETURN keys(s) as k LIMIT 1")
print(f"  Section properties: {r[0]['k'] if r else 'yok'}")

# Hasta profili ile karşılaştırma yapılabilir mi?
print("\n=== GFR/Doz threshold: 4.2 section içeriği örneği ===")
r = run_query("""
    MATCH (d:Drug {name: 'METAFORMAL 1000 MG FILM KAPLI TABLET'})-[:HAS_SECTION]->(s:Section)
    WHERE s.madde_no = '4.2'
    RETURN s.icerik
    LIMIT 1
""")
if r:
    print(r[0]["s.icerik"][:400])

print("\n=== Kontrendikasyon varsa, ilaç-hasta koşul eşleşmesi ===")
r = run_query("""
    MATCH (d:Drug)-[:CONTRAINDICATED_FOR]->(c:Condition)
    WHERE c.name IN ['böbrek yetmezliği', 'gebelik', 'karaciğer yetmezliği']
    RETURN c.name as kosul, count(d) as ilac_sayisi
    ORDER BY ilac_sayisi DESC
""")
for row in r:
    print(f"  {row['kosul']}: {row['ilac_sayisi']} ilaç kontrendike")

print("\n=== INTERACTS_WITH: mekanizma coverage per severity ===")
r = run_query("""
    MATCH ()-[r:INTERACTS_WITH]->()
    RETURN r.severity as sev,
           count(r) as total,
           sum(CASE WHEN r.mechanism IS NOT NULL THEN 1 ELSE 0 END) as has_mec
    ORDER BY total DESC
""")
for row in r:
    pct = int(100 * row['has_mec'] // row['total']) if row['total'] else 0
    print(f"  {row['sev']}: {row['total']} toplam, mekanizma %{pct}")
