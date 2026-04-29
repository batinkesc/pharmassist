"""Tam RAG pipeline smoke testi — graf iyileştirme doğrulaması."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.agents.patient_profile import PatientProfile
from src.agents.rag_engine import run_rag

# Test 1: BRUFEN + aktif ülser (kontrendikasyon + neden)
print("=" * 60)
print("TEST: Aktif mide ülseri hastada BRUFEN")
print("=" * 60)
profil = PatientProfile(yas=55, cinsiyet="erkek")
resp = run_rag(
    soru="Aktif mide ülseri olan hastada BRUFEN kullanılabilir mi?",
    profil=profil,
)
print(resp.yanit)
print(f"\n--- Graf bağlamı (ilk 600 karakter) ---")
print((resp.graf_baglami or "")[:600])
