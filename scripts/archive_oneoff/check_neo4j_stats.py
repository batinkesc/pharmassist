"""Neo4j rebuild istatistiklerini gösterir."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv; load_dotenv()
from src.graph.neo4j_client import run_query

queries = [
    ("Drug nodes",                  "MATCH (d:Drug) RETURN count(d) as cnt"),
    ("INTERACTS_WITH",              "MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) as cnt"),
    ("INTERACTS_WITH_CLASS",        "MATCH ()-[r:INTERACTS_WITH_CLASS]->() RETURN count(r) as cnt"),
    ("MENTIONS_INTERACTION",        "MATCH ()-[r:MENTIONS_INTERACTION]->() RETURN count(r) as cnt"),
    ("REQUIRES_DOSE_ADJUSTMENT",    "MATCH ()-[r:REQUIRES_DOSE_ADJUSTMENT]->() RETURN count(r) as cnt"),
    ("CYP_SUBSTRATE",               "MATCH ()-[r:CYP_SUBSTRATE]->() RETURN count(r) as cnt"),
    ("CYP_INHIBITOR",               "MATCH ()-[r:CYP_INHIBITOR]->() RETURN count(r) as cnt"),
    ("CYP_INDUCER",                 "MATCH ()-[r:CYP_INDUCER]->() RETURN count(r) as cnt"),
    ("Gebelik kategorisi",          "MATCH (d:Drug) WHERE d.gebelik_kategorisi IS NOT NULL RETURN count(d) as cnt"),
    ("CONTRAINDICATED_FOR",         "MATCH ()-[r:CONTRAINDICATED_FOR]->() RETURN count(r) as cnt"),
    ("HAS_WARNING",                 "MATCH ()-[r:HAS_WARNING]->() RETURN count(r) as cnt"),
    ("HAS_SECTION",                 "MATCH ()-[r:HAS_SECTION]->() RETURN count(r) as cnt"),
]

print("=" * 45)
print("NEO4J REBUILD ISTATISTIKLERI")
print("=" * 45)
for label, q in queries:
    try:
        res = run_query(q)
        cnt = res[0]["cnt"] if res else 0
        print("  %-32s: %6d" % (label, cnt))
    except Exception as e:
        print("  %-32s: HATA - %s" % (label, e))
print("=" * 45)
