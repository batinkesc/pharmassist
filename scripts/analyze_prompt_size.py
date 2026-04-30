#!/usr/bin/env python3
"""Prompt bileşenlerinin token boyutunu analiz eder."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from src.agents.rag_engine import run_rag, _SYSTEM_PROMPT_BASE, _build_user_prompt
from src.agents.patient_profile import PatientProfile

# Kaba token tahmini: 1 token ≈ 4 karakter (Türkçe için biraz daha fazla)
def est_tokens(text: str) -> int:
    return len(text) // 3  # Türkçe için daha küçük bölen

profil = PatientProfile(yas=60, cinsiyet="erkek", mevcut_ilaclar=[], alerjiler=[], endikasyonlar=[])
resp = run_rag(
    soru="CORDARONE kullanan hastada SPORANOX baslanirsa ne olur?",
    profil=profil,
    hedef_ilaclar=["CORDARONE 150 MG/3 ML IV ENJEKSIYONLUK COZELTI", "SPORANOX 10 MG / ML ORAL COZELTI"],
)

# Sistem promptu
sys_prompt = _SYSTEM_PROMPT_BASE.format(cyp_talimati="")
print(f"Sistem promptu    : {len(sys_prompt):6,} kar  ~{est_tokens(sys_prompt):5,} token")

# Graf bağlamı
graf = resp.graf_baglami or ""
print(f"Graf bağlamı      : {len(graf):6,} kar  ~{est_tokens(graf):5,} token")

# Kümülatif risk
kum = resp.kumlatif_metin or ""
print(f"Kümülatif risk    : {len(kum):6,} kar  ~{est_tokens(kum):5,} token")

# CYP metni
cyp = resp.cyp_metin or ""
print(f"CYP metni         : {len(cyp):6,} kar  ~{est_tokens(cyp):5,} token")

# Gerçek token sayısı
print(f"\nGerçek input      : {resp.prompt_token_sayisi:6,} token (API'dan)")
print(f"Gerçek output     : {resp.yanit_token_sayisi:6,} token")

# Graf bağlamı alt bileşenler
print("\n=== GRAF BAĞLAMI DETAYI ===")
satırlar = [s for s in graf.split("\n") if s.strip()]
kontred = [s for s in satırlar if "kontrendike" in s.lower()]
etkilesim = [s for s in satırlar if "etkileşim" in s.lower() or "↔" in s]
uyari = [s for s in satırlar if "uyarı" in s.lower() or "warning" in s.lower()]
print(f"Kontrendikasyon satırları : {len(kontred)}")
print(f"Etkileşim satırları       : {len(etkilesim)}")
print(f"Uyarı satırları           : {len(uyari)}")
print(f"Toplam satır              : {len(satırlar)}")
