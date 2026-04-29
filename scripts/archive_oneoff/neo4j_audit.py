"""Neo4j graf durum analizi."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from src.graph.neo4j_client import get_driver

driver = get_driver()
with driver.session() as s:
    # Node counts
    print("=== NODES ===")
    r = s.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as cnt ORDER BY cnt DESC")
    for rec in r:
        print(f"  {rec['label']}: {rec['cnt']}")

    # Relationship counts
    print("\n=== RELATIONSHIPS ===")
    r2 = s.run("MATCH ()-[r]->() RETURN type(r) as t, count(r) as cnt ORDER BY cnt DESC")
    for rec in r2:
        print(f"  {rec['t']}: {rec['cnt']}")

    # INTERACTS_WITH property coverage
    print("\n=== INTERACTS_WITH PROPERTY COVERAGE ===")
    r3 = s.run("""
        MATCH ()-[r:INTERACTS_WITH]->()
        RETURN
          count(r) as total,
          sum(CASE WHEN r.severity IS NOT NULL THEN 1 ELSE 0 END) as has_severity,
          sum(CASE WHEN r.mechanism IS NOT NULL THEN 1 ELSE 0 END) as has_mechanism,
          sum(CASE WHEN r.description IS NOT NULL THEN 1 ELSE 0 END) as has_description,
          sum(CASE WHEN r.source IS NOT NULL THEN 1 ELSE 0 END) as has_source
    """)
    for rec in r3:
        total = rec['total']
        print(f"  Total: {total}")
        print(f"  has_severity:    {rec['has_severity']} ({100*rec['has_severity']//total}%)")
        print(f"  has_mechanism:   {rec['has_mechanism']} ({100*rec['has_mechanism']//total}%)")
        print(f"  has_description: {rec['has_description']} ({100*rec['has_description']//total}%)")
        print(f"  has_source:      {rec['has_source']} ({100*rec['has_source']//total}%)")

    # Severity distribution
    print("\n=== SEVERITY DISTRIBUTION ===")
    r4 = s.run("""
        MATCH ()-[r:INTERACTS_WITH]->()
        RETURN r.severity as sev, count(r) as cnt
        ORDER BY cnt DESC
    """)
    for rec in r4:
        print(f"  '{rec['sev']}': {rec['cnt']}")

    # CONTRAINDICATED_FOR property coverage
    print("\n=== CONTRAINDICATED_FOR PROPERTY COVERAGE ===")
    r5 = s.run("""
        MATCH ()-[r:CONTRAINDICATED_FOR]->()
        RETURN
          count(r) as total,
          sum(CASE WHEN r.reason IS NOT NULL THEN 1 ELSE 0 END) as has_reason,
          sum(CASE WHEN r.source IS NOT NULL THEN 1 ELSE 0 END) as has_source
    """)
    for rec in r5:
        total = rec['total']
        print(f"  Total: {total}")
        print(f"  has_reason:  {rec['has_reason']} ({100*rec['has_reason']//total if total>0 else 0}%)")
        print(f"  has_source:  {rec['has_source']} ({100*rec['has_source']//total if total>0 else 0}%)")

    # Condition node types
    print("\n=== CONDITION NODE TYPES (sample 10) ===")
    r6 = s.run("MATCH (c:Condition) RETURN c.name LIMIT 10")
    for rec in r6:
        print(f"  {rec['c.name']}")

    # Drug nodes — how many have INN linked
    print("\n=== DRUG INN COVERAGE ===")
    r7 = s.run("""
        MATCH (d:Drug)
        RETURN
          count(d) as total,
          sum(CASE WHEN d.inn IS NOT NULL THEN 1 ELSE 0 END) as has_inn,
          sum(CASE WHEN d.atc IS NOT NULL THEN 1 ELSE 0 END) as has_atc
    """)
    for rec in r7:
        total = rec['total']
        print(f"  Total drugs: {total}")
        print(f"  has_inn: {rec['has_inn']} ({100*rec['has_inn']//total if total>0 else 0}%)")
        print(f"  has_atc: {rec['has_atc']} ({100*rec['has_atc']//total if total>0 else 0}%)")

    # Isolated drugs (no relationships at all)
    print("\n=== ISOLATED DRUGS (no relationships) ===")
    r8 = s.run("""
        MATCH (d:Drug)
        WHERE NOT (d)-[]-()
        RETURN d.name
        LIMIT 20
    """)
    isolated = [rec['d.name'] for rec in r8]
    print(f"  Count: {len(isolated)}")
    for name in isolated[:10]:
        print(f"  - {name}")

    # Sample INTERACTS_WITH
    print("\n=== SAMPLE INTERACTS_WITH (5) ===")
    r9 = s.run("""
        MATCH (a:Drug)-[r:INTERACTS_WITH]->(b:Drug)
        RETURN a.name as a, b.name as b, r.severity as sev, r.mechanism as mec
        LIMIT 5
    """)
    for rec in r9:
        print(f"  {rec['a']} -> {rec['b']} | sev:{rec['sev']} | mec:{str(rec['mec'])[:50]}")

    # Sample CONTRAINDICATED_FOR
    print("\n=== SAMPLE CONTRAINDICATED_FOR (5) ===")
    r10 = s.run("""
        MATCH (d:Drug)-[r:CONTRAINDICATED_FOR]->(c)
        RETURN d.name as drug, c.name as cond, r.reason as reason
        LIMIT 5
    """)
    for rec in r10:
        print(f"  {rec['drug']} -> {rec['cond']} | {str(rec['reason'])[:60]}")

driver.close()
print("\nAudit tamamlandi.")
