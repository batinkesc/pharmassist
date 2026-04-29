"""D/E/F extraction fonksiyonlarını mevcut Section verileriyle test et."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()

from src.graph.neo4j_client import run_query
from src.graph.kub_to_graph import (
    extract_dose_adjustments,
    extract_cyp_edges,
    extract_pregnancy_category,
)

# ── Test ilaçları ─────────────────────────────────────────────────────────────
TESTLER = [
    ("METAFORMAL 1000 MG FILM KAPLI TABLET", ["4.2", "4.5", "4.6"]),
    ("CORDARONE 150 MG/3 ML IV ENJEKSIYONLUK COZELTI", ["4.2", "4.5", "4.6"]),
    ("XANAX 1 MG TABLET", ["4.2", "4.5", "4.6"]),
]

for ilac_adi, madde_listesi in TESTLER:
    print(f"\n{'='*55}")
    print(f"  {ilac_adi[:50]}")
    print(f"{'='*55}")

    for madde_no in madde_listesi:
        rows = run_query(
            "MATCH (d:Drug {name:$n})-[:HAS_SECTION]->(s:Section) "
            "WHERE s.madde_no=$m RETURN s.icerik as ic LIMIT 1",
            {"n": ilac_adi, "m": madde_no}
        )
        if not rows or not rows[0].get("ic"):
            print(f"  {madde_no}: bölüm yok")
            continue

        chunk = {"madde_no": madde_no, "icerik": rows[0]["ic"],
                 "chunk_id": f"test_{ilac_adi[:10]}_{madde_no}"}

        if madde_no == "4.2":
            extract_dose_adjustments(ilac_adi, chunk)
        elif madde_no in ("4.5", "5.1"):
            extract_cyp_edges(ilac_adi, chunk)
        elif madde_no == "4.6":
            extract_pregnancy_category(ilac_adi, chunk)

# ── Sonuçları kontrol et ──────────────────────────────────────────────────────
print("\n\n=== D: REQUIRES_DOSE_ADJUSTMENT ===")
r = run_query("MATCH (d:Drug)-[r:REQUIRES_DOSE_ADJUSTMENT]->(d) RETURN d.name as n, r.gfr_esik as esik, r.operator as op, r.tip as tip LIMIT 10")
if r:
    for row in r:
        print(f"  {row['n'][:40]:<40} GFR {row['op']}{row['esik']} → {row['tip']}")
else:
    print("  (kayıt yok — 4.2 metni GFR içermiyorsa normal)")

print("\n=== E: CYP Kenarları ===")
r = run_query("""
    MATCH (d:Drug)-[r]->(e:CYPEnzyme)
    WHERE type(r) IN ['CYP_SUBSTRATE','CYP_INHIBITOR','CYP_INDUCER']
    RETURN d.name as ilac, type(r) as rol, e.name as enzim
    LIMIT 15
""")
if r:
    for row in r:
        print(f"  {row['ilac'][:35]:<35} {row['rol']:<15} {row['enzim']}")
else:
    print("  (kayıt yok)")

print("\n=== F: Gebelik Kategorisi ===")
r = run_query("MATCH (d:Drug) WHERE d.gebelik_kategorisi IS NOT NULL RETURN d.name as n, d.gebelik_kategorisi as k LIMIT 10")
if r:
    for row in r:
        print(f"  [{row['k']}] {row['n'][:50]}")
else:
    print("  (kayıt yok)")
