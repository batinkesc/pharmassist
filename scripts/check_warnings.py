"""HAS_WARNING node kontrolü."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from src.graph.neo4j_client import run_query
from src.graph.graph_retriever import ilac_node_adlari_bul, drug_warnings

for ilac in ["BRUFEN", "CORDARONE", "SPORANOX", "XANAX"]:
    adlar = ilac_node_adlari_bul(ilac)
    print(f"\n{ilac} → {adlar[:2]}")
    if adlar:
        r = run_query(
            "MATCH (d:Drug)-[:HAS_WARNING]->(w:Warning) WHERE d.name IN $adlar RETURN count(w) as c",
            {"adlar": adlar}
        )
        print(f"  HAS_WARNING count: {r[0]['c'] if r else 0}")
        r2 = run_query(
            "MATCH (d:Drug)-[:HAS_WARNING]->(w:Warning) WHERE d.name IN $adlar RETURN w.ozet as o LIMIT 1",
            {"adlar": adlar}
        )
        for row in r2:
            print(f"  ozet[:100]: {str(row['o'])[:100]}")

    # drug_warnings ile test (hasta koşulları ile)
    wi_k = drug_warnings(ilac, ["böbrek yetmezliği", "karaciğer yetmezliği"])
    wi_all = drug_warnings(ilac, None)
    print(f"  drug_warnings(böbrek/karaciğer): {len(wi_k)}")
    print(f"  drug_warnings(None): {len(wi_all)}")
