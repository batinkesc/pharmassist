"""A+B+C graf iyileştirmeleri testi."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()

from src.graph.graph_retriever import drug_warnings, drug_class_interactions
from src.graph.combi_retriever import build_graph_context

# ──── A: HAS_WARNING ────
print("=== A: HAS_WARNING ===")
test_ilaclar = ["BRUFEN", "SPORANOX", "CORDARONE"]
for ilac in test_ilaclar:
    # Hasta koşullarıyla filtreli
    wi = drug_warnings(ilac, ["böbrek yetmezliği", "karaciğer yetmezliği"])
    print(f"  {ilac} [böbrek/karaciğer]: {len(wi)} uyarı")
    for w in wi[:2]:
        print(f"    §{w.get('bolum','')} | {str(w.get('ozet',''))[:80]}")

print()

# ──── B: INTERACTS_WITH_CLASS ────
print("=== B: INTERACTS_WITH_CLASS ===")
for ilac in test_ilaclar:
    ci = drug_class_interactions(ilac)
    print(f"  {ilac}: {len(ci)} sınıf etkileşimi")
    for row in ci[:3]:
        print(f"    → {row.get('sinif_adi','')} [{row.get('siddet','')}] {str(row.get('mekanizma',''))[:50]}")

print()

# ──── C: contraindicated INTERACTS_WITH → kontrendikasyon bölümü ────
print("=== C: severity=contraindicated ayrımı ===")
from src.graph.graph_retriever import drug_interactions

# CORDARONE'un etkileşimlerine bak, contraindicated var mı?
ei = drug_interactions("CORDARONE")
kontr_count = sum(1 for r in ei if (r.get("siddet") or "").lower() == "contraindicated")
normal_count = len(ei) - kontr_count
print(f"  CORDARONE etkileşim toplam: {len(ei)} → contraindicated: {kontr_count}, diğer: {normal_count}")

print()

# ──── Tam build_graph_context testi ────
print("=== build_graph_context bütünleşik test ===")
ctx = build_graph_context(
    sorgu_ilaclar=["CORDARONE"],
    hasta_ilaclar=[],
    hasta_kosullar=["karaciğer yetmezliği"],
)
print(f"  kontrendikasyonlar: {len(ctx.kontrendikasyonlar)}")
print(f"  etkilesimler: {len(ctx.etkilesimler)}")
print(f"  uyarilar: {len(ctx.uyarilar)}")
print(f"  sinif_etkilesimleri: {len(ctx.sinif_etkilesimleri)}")
print()
print("--- PROMPT METNİ (ilk 1500 char) ---")
print(ctx.ozet_metin[:1500])
