"""
Faz 2 RAG Engine test scripti.

Test senaryosu: 68 yaşında CKD Evre 3b hastası
  - GFR=38, Metformin + Ramipril + Atorvastatin kullanıyor
  - Hekim İbuprofen eklemek istiyor — ne düşünürsün?
"""

import sys
import os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.agents.patient_profile import PatientProfile
from src.agents.query_augmentor import augment_query
from src.agents.rag_engine import run_rag


def test_augmentation():
    """Query augmentation'ı Claude API çağrısı yapmadan test eder."""
    print("\n" + "="*60)
    print("TEST 1: Query Augmentation")
    print("="*60)

    profil = PatientProfile(
        yas=68,
        cinsiyet="erkek",
        gfr=38,
        mevcut_ilaclar=["Metformin 1000 mg", "Ramipril 10 mg", "Atorvastatin 20 mg"],
        alerjiler=["penisilin"],
        endikasyonlar=["Tip 2 Diyabet", "Hipertansiyon", "Hiperlipidemi"],
    )

    print("\nHasta Profili:")
    print(profil.ozet_metin())
    print(f"\nAktif Flags: {profil.aktif_flags}")
    print(f"Geriyatrik: {profil.geriyatrik}, Böbrek yetmezliği: {profil.bobrek_yetmezligi}")
    print(f"CKD Evresi: {profil.bobrek_evresi}")

    soru = "Bu hastaya ibuprofen verebilir miyiz? Mevcut ilaçlarla etkileşimi var mı?"
    aq = augment_query(soru, profil)

    print(f"\nOrijinal soru: {soru}")
    print(f"Tespit edilen türler: {aq.soru_turleri}")
    print(f"Madde önceliği: {aq.arama_planlari[0].madde_onceligi}")
    print(f"Zenginleştirilmiş sorgu: {aq.arama_planlari[0].sorgu}")
    print(f"Patient flags: {aq.arama_planlari[0].patient_flags}")
    print("\nTEST 1 GEÇTI")


def test_rag_full():
    """Tam RAG pipeline'ını test eder (Claude API gerektirir)."""
    print("\n" + "="*60)
    print("TEST 2: Tam RAG Pipeline (Claude API)")
    print("="*60)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY bulunamadi — bu test atlanıyor.")
        print("Çalıştırmak için: $env:ANTHROPIC_API_KEY='your-key' && python scripts/test_rag.py")
        return

    profil = PatientProfile(
        yas=68,
        cinsiyet="erkek",
        gfr=38,
        mevcut_ilaclar=["Metformin 1000 mg", "Ramipril 10 mg", "Atorvastatin 20 mg"],
        alerjiler=["penisilin"],
        endikasyonlar=["Tip 2 Diyabet", "Hipertansiyon", "Hiperlipidemi"],
    )

    soru = "Bu hastaya ibuprofen verebilir miyiz? Mevcut ilaçlarla etkileşimi var mı?"

    print(f"\nSoru: {soru}")
    print("\nRAG çalıştırılıyor...")

    response = run_rag(
        soru=soru,
        profil=profil,
        hedef_ilaclar=None,  # Tüm koleksiyonda ara
    )

    print("\n" + "-"*60)
    print("YANIT:")
    print("-"*60)
    print(response.yanit)

    print("\n" + "-"*60)
    print("KULLANILAN KAYNAKLAR:")
    print("-"*60)
    print(response.kaynak_listesi())

    print(f"\nToken kullanımı: {response.prompt_token_sayisi} giriş, {response.yanit_token_sayisi} çıkış")
    print("\nTEST 2 TAMAMLANDI")


if __name__ == "__main__":
    test_augmentation()
    test_rag_full()
