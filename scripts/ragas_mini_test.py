"""
ragas_mini_test.py — RAGAS Together AI bağlantı ve kalite mini testi.

3 soru ile hızlı doğrulama: API erişilebilir mi, 3 metrik hesaplanıyor mu?
Metrikler: faithfulness + context_utilization + context_recall

Kullanım:
    .venv/Scripts/python scripts/ragas_mini_test.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv; load_dotenv()

from src.evaluation.ragas_eval import run_ragas_evaluation, print_ragas_report

# 3 temsili soru — RAG sisteminin gerçek çıktısını simüle eder
MINI_RECORDS = [
    {
        "question": "Warfarin ile aspirin birlikte kullanılabilir mi?",
        "answer": (
            "Warfarin ve aspirin birlikte kullanımı kanama riskini artırır. "
            "Bu kombinasyon kontrendike olmasa da çok dikkatli izlem gerektirir. "
            "INR sık sık kontrol edilmeli, mide koruyucu kullanılmalıdır."
        ),
        "contexts": [
            "Warfarin ile aspirin etkileşimi: Aspirin antitrombosit etkisi ile warfarinin antikoagülan "
            "etkisini potansiyelize eder. Birlikte kullanımda ciddi kanama riski artar. "
            "INR düzenli izlenmelidir. Gastrointestinal kanama riski önemli ölçüde yükselir.",
            "NSAID'ler ve warfarin: NSAID grubu ilaçlar warfarin metabolizmasını etkileyebilir. "
            "Kanama zamanını uzatabilirler. Gastrik mukoza koruması önerilir.",
        ],
        "ground_truth": (
            "Warfarin ile aspirin birlikte kullanımı kanama riskini önemli ölçüde artırır, "
            "dikkatli izlem ve INR takibi gerektirir."
        ),
    },
    {
        "question": "Metformin böbrek yetmezliğinde kullanılır mı?",
        "answer": (
            "Metformin ciddi böbrek yetmezliğinde kontrendikedir. "
            "GFR 30 ml/dk/1.73m2 altında kullanılmamalıdır. "
            "GFR 30-45 arası dikkatli kullanım gerektirir."
        ),
        "contexts": [
            "Metformin ve böbrek fonksiyonu: GFR < 30 mL/dk/1.73m2 durumunda metformin "
            "kontrendikedir. Laktik asidoz riski nedeniyle böbrek yetmezliğinde kullanılmaz. "
            "GFR 30-45 arasında tedaviye devam için fayda-risk değerlendirmesi yapılmalıdır.",
            "Doz ayarlaması: Böbrek fonksiyonu düzenli izlenmeli, "
            "GFR değerine göre doz ayarlanmalı veya ilaç kesilmelidir.",
        ],
        "ground_truth": (
            "Metformin GFR < 30 mL/dk/1.73m2 durumunda kontrendikedir, "
            "GFR 30-45 arasında dikkatli kullanım gerektirir."
        ),
    },
    {
        "question": "Amlodipin gebelikte güvenli midir?",
        "answer": (
            "Amlodipin gebelik kategorisi C'dir. "
            "Gebelikte kullanımı önerilmez. "
            "Ancak zorunlu durumlarda hekim gözetiminde kullanılabilir."
        ),
        "contexts": [
            "Amlodipin gebelik ve laktasyon: Gebelik kategorisi C. "
            "Hayvan çalışmalarında fetal toksisite gösterilmiştir. "
            "İnsanlarda yeterli veri yoktur. Gebelikte kullanımdan kaçınılmalıdır.",
        ],
        "ground_truth": (
            "Amlodipin gebelik kategorisi C olup gebelikte kullanımı önerilmez."
        ),
    },
]


def main():
    print("=" * 60)
    print("RAGAS MİNİ TEST — Together AI (Qwen3-235B)")
    print("=" * 60)
    print(f"Model  : {os.environ.get('RAGAS_MODEL', '?')}")
    print(f"URL    : {os.environ.get('LM_STUDIO_URL', '?')}")
    print(f"Sorular: {len(MINI_RECORDS)}")
    print(f"Metrikler: faithfulness + context_utilization + context_recall")
    print()

    try:
        result = run_ragas_evaluation(MINI_RECORDS)
        print_ragas_report(result["scores"])

        print("\nSORU BAZLI:")
        for q in result["per_question"]:
            f  = q.get("faithfulness")
            cu = q.get("context_utilization")
            cr = q.get("context_recall")
            f_str  = ("%.4f" % f)  if f  is not None else "NaN  "
            cu_str = ("%.4f" % cu) if cu is not None else "NaN  "
            cr_str = ("%.4f" % cr) if cr is not None else "NaN  "
            print(f"  Q{q['question_id']}: F={f_str}  CU={cu_str}  CR={cr_str}  — {q['question'][:45]}")

    except Exception as e:
        print(f"HATA: {e}")
        import traceback; traceback.print_exc()


if __name__ == "__main__":
    main()
