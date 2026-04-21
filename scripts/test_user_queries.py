"""
Kullanıcı sorguları test scripti — 3 özel soru çalıştırıp JSON'a kaydet
Çalıştır: .venv/Scripts/python scripts/test_user_queries.py
"""
import sys
import os
import json
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.agents.patient_profile import PatientProfile
from src.agents.rag_engine import run_rag

# Test sorguları
SORGULAR = [
    {
        "id": "user_q1",
        "soru": "COZAAR böbrek yetmezliğinde nasıl kullanılmalı?",
        "profil": PatientProfile(
            yas=68,
            cinsiyet="erkek",
            gfr=32,
            endikasyonlar=["Hipertansiyon"],
        ),
        "hedef_ilaclar": ["COZAAR"],
    },
    {
        "id": "user_q2",
        "soru": "ELİQUİS ile ASPİRİN birlikte kullanılabilir mi?",
        "profil": PatientProfile(
            yas=72,
            cinsiyet="erkek",
            gfr=None,
            mevcut_ilaclar=["ASPİRİN 100 mg"],
            endikasyonlar=["Atriyal fibrilasyon"],
        ),
        "hedef_ilaclar": ["ELİQUİS", "ASPİRİN"],
    },
    {
        "id": "user_q3",
        "soru": "LUSTRAL gebelikte kullanılabilir mi?",
        "profil": PatientProfile(
            yas=31,
            cinsiyet="kadın",
            gfr=None,
            gebelik=True,
            endikasyonlar=["Depresyon"],
        ),
        "hedef_ilaclar": ["LUSTRAL"],
    },
]


def run_test():
    """Test sorgularını çalıştır ve sonuçları topla."""
    print("\n" + "="*70)
    print("KULLANICI SORGU TESTİ — 3 Soru")
    print("="*70)

    results = {
        "test_date": datetime.now().isoformat(),
        "test_type": "user_queries",
        "evaluator": "haiku",  # Turkish patch removed
        "queries": [],
    }

    for query_spec in SORGULAR:
        print(f"\n{'='*70}")
        print(f"Sorgu {query_spec['id'].upper()}: {query_spec['soru'][:60]}...")
        print(f"Hasta: {query_spec['profil'].yas}y, GFR={query_spec['profil'].gfr}")
        print(f"Hedef ilaçlar: {query_spec['hedef_ilaclar']}")
        print("-"*70)

        try:
            response = run_rag(
                soru=query_spec["soru"],
                profil=query_spec["profil"],
                hedef_ilaclar=query_spec["hedef_ilaclar"],
            )

            print("\nYANIT:")
            print(response.yanit[:300] + "..." if len(response.yanit) > 300 else response.yanit)

            # Kaynakları topla
            kaynaklar = []
            for kaynak in response.kaynaklar:
                kaynaklar.append({
                    "ilac_adi": kaynak.ilac_adi,
                    "madde_no": kaynak.madde_no,
                    "madde_baslik": kaynak.madde_baslik,
                    "icerik": kaynak.icerik[:200] if kaynak.icerik else "",
                    "sayfa": kaynak.sayfa,
                    "score": kaynak.score,
                })

            # Sonucu kaydet
            result_item = {
                "query_id": query_spec["id"],
                "question": query_spec["soru"],
                "patient": {
                    "age": query_spec["profil"].yas,
                    "gender": query_spec["profil"].cinsiyet,
                    "gfr": query_spec["profil"].gfr,
                    "pregnancy": query_spec["profil"].gebelik,
                    "current_drugs": query_spec["profil"].mevcut_ilaclar,
                    "indications": query_spec["profil"].endikasyonlar,
                    "allergies": query_spec["profil"].alerjiler,
                },
                "target_drugs": query_spec["hedef_ilaclar"],
                "answer": response.yanit,
                "sources": kaynaklar,
                "n_sources": len(response.kaynaklar),
                "tokens": {
                    "input": response.prompt_token_sayisi,
                    "output": response.yanit_token_sayisi,
                },
            }

            results["queries"].append(result_item)

            print(f"\n✓ Sorgu başarıyla çalıştırıldı ({len(kaynaklar)} kaynak)")

        except Exception as e:
            print(f"\n✗ Hata: {str(e)}")
            results["queries"].append({
                "query_id": query_spec["id"],
                "question": query_spec["soru"],
                "error": str(e),
            })

    # Sonuçları JSON dosyasına kaydet
    output_file = "data/eval/user_queries_test.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print(f"✓ Sonuçlar kaydedildi: {output_file}")
    print("="*70)

    return results


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY bulunamadı!")
        print("Çalıştırmak için: $env:ANTHROPIC_API_KEY='your-key' && python scripts/test_user_queries.py")
        sys.exit(1)

    run_test()
