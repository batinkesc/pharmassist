#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from src.agents.rag_engine import run_rag, _SYSTEM_PROMPT_BASE
from src.agents.patient_profile import PatientProfile

profil = PatientProfile(yas=60, cinsiyet="erkek", mevcut_ilaclar=[], alerjiler=[], endikasyonlar=[])
resp = run_rag(
    soru="CORDARONE kullanan hastada SPORANOX baslanirsa ne olur?",
    profil=profil,
    hedef_ilaclar=["CORDARONE 150 MG/3 ML IV ENJEKSIYONLUK COZELTI", "SPORANOX 10 MG / ML ORAL COZELTI"],
)

gercek = resp.prompt_token_sayisi
sys_p  = _SYSTEM_PROMPT_BASE.format(cyp_talimati="")
graf   = resp.graf_baglami or ""
kum    = resp.kumlatif_metin or ""
cyp    = resp.cyp_metin or ""

def tok(s): return len(s) // 3  # kaba tahmin

print("=" * 55)
print(f"{'Bileşen':<30} {'Kar':>8} {'~Token':>8}")
print("=" * 55)
print(f"{'Sistem promptu':<30} {len(sys_p):>8,} {tok(sys_p):>8,}")
print(f"{'Graf bağlamı':<30} {len(graf):>8,} {tok(graf):>8,}")
print(f"{'Kümülatif risk':<30} {len(kum):>8,} {tok(kum):>8,}")
print(f"{'CYP metni':<30} {len(cyp):>8,} {tok(cyp):>8,}")

kalan_token = gercek - tok(sys_p) - tok(graf) - tok(kum) - tok(cyp)
print(f"{'KÜB chunks + diğer (kalan)':<30} {'':>8} {kalan_token:>8,}")
print("-" * 55)
print(f"{'Gerçek toplam (API)':<30} {'':>8} {gercek:>8,}")
print()

# Chunk boyutu limitleri
from src.agents.rag_engine import _MADDE_CHUNK_LIMITS
print("=== _MADDE_CHUNK_LIMITS (karakter) ===")
for madde, limit in sorted(_MADDE_CHUNK_LIMITS.items()):
    print(f"  Madde {madde}: {limit:,} kar  ~{limit//3:,} tok")
