import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv; load_dotenv()
from src.graph.neo4j_client import run_query

q = "MATCH (d:Drug) WHERE d.name CONTAINS 'NORODOL' OPTIONAL MATCH (d)-[r:INTERACTS_WITH]->() OPTIONAL MATCH (d)-[c:CONTRAINDICATED_FOR]->() RETURN d.name AS name, count(DISTINCT r) AS interactions, count(DISTINCT c) AS contraindications ORDER BY d.name"
res = run_query(q)
for r in res:
    print("%-55s  int=%-3d  cont=%d" % (r["name"], r["interactions"], r["contraindications"]))
