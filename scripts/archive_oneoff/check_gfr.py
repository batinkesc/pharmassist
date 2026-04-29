"""GFR regex debug."""
import sys, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()
from src.graph.neo4j_client import run_query

for ilac in ["METAFORMAL 1000 MG FILM KAPLI TABLET", "JANUVIA 100 MG FILM KAPLI TABLET"]:
    r = run_query(
        "MATCH (d:Drug {name:$n})-[:HAS_SECTION]->(s:Section) WHERE s.madde_no='4.2' RETURN s.icerik as ic LIMIT 1",
        {"n": ilac}
    )
    if not r or not r[0].get("ic"):
        print(f"{ilac[:40]}: 4.2 bölüm YOK\n")
        continue
    txt = r[0]["ic"]
    print(f"\n{ilac[:50]}")
    print(f"4.2 uzunluk: {len(txt)} char")
    # GFR/kreatinin içeren satırlar
    for line in txt.splitlines():
        if re.search(r'GFR|kreatinin\s+klerensi|eGFR|CrCl|mL/dak|ml/min|böbrek', line, re.IGNORECASE):
            print(f"  > {line.strip()[:120]}")
