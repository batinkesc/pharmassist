"""
RAGAS Sorun Teşhisi — Manuel Değerlendirme
"""
import sys, json
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from src.agents.patient_profile import PatientProfile
from src.agents.rag_engine import run_rag

# 5 test sorusu — basit ve doğrulanabilir
TEST_QUESTIONS = [
    {
        "id": 1,
        "soru": "Penisilin alerjisi olan bir çocuğa Augmentin yazılabilir mi?",
        "beklenen_cevap": "Hayır, kontrendikedir",
        "key_kontrol": ["kontrendikedir", "Augmentin", "penisilin"]
    },
    {
        "id": 2,
        "soru": "GFR 25 olan böbrek yetmezliği hastasında Augmentin dozu nasıl olmalı?",
        "beklenen_cevap": "Doz ayarlaması gerekir",
        "key_kontrol": ["doz", "böbrek", "ayarla"]
    },
    {
        "id": 3,
        "soru": "Warfarin kullanan hastaya Plavix eklenebilir mi?",
        "beklenen_cevap": "Etkileşim riski vardır",
        "key_kontrol": ["etkileşim", "Warfarin", "Plavix"]
    },
    {
        "id": 4,
        "soru": "Siprofloksasin gebelikte kullanılabilir mi?",
        "beklenen_cevap": "Kontrendikedir",
        "key_kontrol": ["gebelik", "kontrendikedir", "siprofloksasin"]
    },
    {
        "id": 5,
        "soru": "Karaciğer yetmezliği olan hastada Crestor kullanılabilir mi?",
        "beklenen_cevap": "Dikkatle kullanılır veya kontrendikedir",
        "key_kontrol": ["karaciğer", "Crestor"]
    }
]

def check_answer_quality(answer: str, key_tokens: list, q_id: int) -> dict:
    """Yanıtı manuel checklist'e göre değerlendir"""

    answer_lower = answer.lower()

    findings = {
        "q_id": q_id,
        "answer_length": len(answer),
        "key_tokens_found": [],
        "key_tokens_missing": [],
        "has_sources": "[" in answer and "]" in answer,
        "has_uncertainty": any(x in answer_lower for x in ["bilinmiyor", "eksik", "kayıt yok"]),
        "seems_hallucinated": False,
        "hallucination_signs": []
    }

    # Anahtarları kontrol et
    for token in key_tokens:
        if token.lower() in answer_lower:
            findings["key_tokens_found"].append(token)
        else:
            findings["key_tokens_missing"].append(token)

    # Hallucination belirtileri
    if "güvenlidir" in answer_lower or "zararsızdır" in answer_lower:
        findings["seems_hallucinated"] = True
        findings["hallucination_signs"].append("'güvenlidir' yasağı ihlali")

    if findings["key_tokens_missing"] and not findings["has_uncertainty"]:
        findings["seems_hallucinated"] = True
        findings["hallucination_signs"].append(f"kritik token {findings['key_tokens_missing'][0]} eksik")

    if not findings["has_sources"] and len(answer) > 500:
        findings["seems_hallucinated"] = True
        findings["hallucination_signs"].append("uzun cevap ama kaynak yok")

    return findings

# Test çalıştır
print("=" * 70)
print("RAGAS SORUN TEŞHİSİ — 5 Sorunun Manuel Değerlendirmesi")
print("=" * 70)

results = []

for test_q in TEST_QUESTIONS:
    print(f"\n[Q{test_q['id']}] {test_q['soru'][:60]}...")

    # RAG çalıştır
    hasta = PatientProfile(yas=45, cinsiyet='kadın')
    try:
        response = run_rag(soru=test_q['soru'], profil=hasta)

        # Manuel check
        quality = check_answer_quality(
            response.yanit,
            test_q['key_kontrol'],
            test_q['id']
        )

        results.append({
            "question_id": test_q['id'],
            "question": test_q['soru'],
            "expected": test_q['beklenen_cevap'],
            "actual_answer": response.yanit,
            "source_count": len(response.kaynaklar),
            "quality_check": quality
        })

        # Sonuç yazdır
        print(f"  ✓ Yanıt alındı ({len(response.yanit)} char)")
        print(f"  📚 Kaynaklar: {len(response.kaynaklar)}")
        print(f"  🔑 Bulundu: {quality['key_tokens_found']}")
        print(f"  ❌ Eksik: {quality['key_tokens_missing']}")
        print(f"  ⚠️  Hallucination şüphesi: {'EVET' if quality['seems_hallucinated'] else 'HAYIR'}")
        if quality['hallucination_signs']:
            print(f"     Sebepler: {quality['hallucination_signs']}")

    except Exception as e:
        print(f"  ❌ HATA: {e}")

# Özet
print("\n" + "=" * 70)
print("ÖZET")
print("=" * 70)

halluc_count = sum(1 for r in results if r['quality_check']['seems_hallucinated'])
key_missing_count = sum(len(r['quality_check']['key_tokens_missing']) for r in results)

print(f"✅ Başarılı soru: {len(results)}/5")
print(f"⚠️  Hallucination şüphesi: {halluc_count}/5")
print(f"🔑 Toplam eksik token: {key_missing_count}")
print(f"📚 Ortalama kaynak: {sum(r['source_count'] for r in results) / len(results):.1f}")

# Detaylı çıktıyı JSON'a kaydet
output_file = "data/eval/diagnosis_results.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n📄 Detaylı sonuçlar: {output_file}")

# Analiz
print("\n" + "=" * 70)
print("TAHLIL")
print("=" * 70)

if halluc_count >= 3:
    print("🚨 RİSK: 5 sorudan 3+ 'hallucination şüphesi' → Sistem zayıf olabilir")
    print("   (Bu Haiku'nun düşük skor vermesini açıklardı)")
elif halluc_count <= 1:
    print("✅ İYİ: Hallucination şüphesi az → Sistem temiz")
    print("   (Haiku'nun düşük skor vermesi = evaluator bias)")
else:
    print("⚠️  ORTA: 1-3 hallucination → Sistem stabil ama bazı sorunlar var")

print("\n» Sonraki: answers.json'u oku, her soruyu cevaplandır:")
print("  1. Yanıt doğru mu? (KÜB'de öyle mi?)")
print("  2. Tamamlık: Tüm önemli bilgi var mı?")
print("  3. Kaynaklar: Alıntılar doğru mu?")
