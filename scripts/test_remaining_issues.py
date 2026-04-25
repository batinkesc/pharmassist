import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from src.graph.neo4j_client import run_query

# Kaç ilaçta CONTRAINDICATED_FOR var?
r1 = run_query("MATCH (d:Drug) RETURN count(d) as total")
r2 = run_query("MATCH (d:Drug)-[:CONTRAINDICATED_FOR]->() RETURN count(DISTINCT d) as cnt")
total = r1[0]["total"]
ci_cnt = r2[0]["cnt"]
print(f"Toplam Drug: {total}")
print(f"CONTRAINDICATED_FOR olan Drug: {ci_cnt} ({100*ci_cnt//total}%)")
print(f"Kapsama DIŞINDA Drug: {total - ci_cnt} ({100*(total-ci_cnt)//total}%)")

# severity=contraindicated olan INTERACTS_WITH
r3 = run_query("MATCH ()-[r:INTERACTS_WITH]->() WHERE r.severity = 'contraindicated' RETURN count(r) as cnt")
print(f"\nINTERACTS_WITH severity='contraindicated': {r3[0]['cnt']}")

# Condition listesi
r4 = run_query("MATCH (c:Condition) RETURN c.name ORDER BY c.name")
print(f"\nCondition node listesi ({len(r4)}):")
for row in r4:
    print(f"  - {row['c.name']}")

# Klinik acidan onemli ama eksik condition ornekleri — CONDITION_RE nin yakalamadigini tahmin ettiklerimiz
print("\n--- Klinik Acidan Eksik Olabilecek Condition Ornekleri ---")
missing_examples = [
    "aktif ulser", "aktif kanama", "asiri duyarlilik",
    "peptik ulser", "gastrointestinal kanama", "kardiyak yetmezlik"
]
for ex in missing_examples:
    r = run_query(f"MATCH (c:Condition) WHERE toLower(c.name) CONTAINS '{ex}' RETURN c.name")
    status = "VAR" if r else "YOK"
    print(f"  '{ex}': {status}")
