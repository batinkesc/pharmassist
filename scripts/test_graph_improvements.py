"""Graf iyileştirmelerini test eder."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.graph.combi_retriever import build_graph_context

print("=" * 60)
print("TEST 1: BRUFEN — kontrendikasyon neden metni")
print("=" * 60)
ctx = build_graph_context(
    sorgu_ilaclar=["BRUFEN 400 MG FILM TABLET"],
    hasta_ilaclar=[],
    hasta_kosullar=[],
)
print(ctx.ozet_metin[:1500])

print("\n" + "=" * 60)
print("TEST 2: SPORANOX + CORDARONE — etkileşim mekanizması")
print("=" * 60)
ctx2 = build_graph_context(
    sorgu_ilaclar=["SPORANOX 10 MG / ML ORAL COZELTI"],
    hasta_ilaclar=["CORDARONE 150 MG/3 ML IV ENJEKSIYONLUK COZELTI"],
    hasta_kosullar=[],
)
print(ctx2.ozet_metin[:1500])

print("\n" + "=" * 60)
print("TEST 3: Böbrek yetmezliği — duplicate condition fix kontrolü")
print("=" * 60)
from src.graph.graph_retriever import drug_contraindications
rows = drug_contraindications("METAFORMAL 1000 MG FILM KAPLI TABLET")
print(f"Kontrendikasyon sayısı: {len(rows)}")
for r in rows[:5]:
    print(f"  kosul='{r.get('kosul')}' neden='{(r.get('neden') or '')[:100]}'")
