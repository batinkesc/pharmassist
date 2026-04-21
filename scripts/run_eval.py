"""
RAGAS değerlendirme scripti.

Kullanım:
    # Dalga 1 soruları (8 soru):
    .venv/Scripts/python scripts/run_eval.py

    # Dalga 2 soruları (25 soru, 50+ ilaç corpus):
    .venv/Scripts/python scripts/run_eval.py --v2

    # Özel soru dosyası:
    .venv/Scripts/python scripts/run_eval.py --questions data/eval/ragas_v2_questions.json
"""

import sys, os, json, argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.agents.patient_profile import PatientProfile
from src.agents.rag_engine import run_rag
from src.evaluation.ragas_eval import run_ragas_evaluation, print_ragas_report


def load_test_questions(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_rag_on_question(q: dict) -> dict:
    """Bir test sorusu için RAG pipeline'ını çalıştırır."""
    hasta_data = q.get("hasta", {})
    profil = PatientProfile(
        yas=hasta_data.get("yas", 0),
        cinsiyet=hasta_data.get("cinsiyet", "belirtilmemiş"),
        gfr=hasta_data.get("gfr"),
        karaciger_skoru=hasta_data.get("karaciger_skoru"),
        mevcut_ilaclar=hasta_data.get("mevcut_ilaclar", []),
        alerjiler=hasta_data.get("alerjiler", []),
        endikasyonlar=hasta_data.get("endikasyonlar", []),
        gebelik=hasta_data.get("gebelik", False),
        emzirme=hasta_data.get("emzirme", False),
        lab_degerleri=hasta_data.get("lab_degerleri", {}),
    )

    # v2 sorularında hedef_ilaclar belirtilmişse kullan
    hedef_ilaclar = q.get("hedef_ilaclar")

    response = run_rag(soru=q["soru"], profil=profil, hedef_ilaclar=hedef_ilaclar)

    # Ek kaynaklar (Neo4j, kümülatif risk, CYP450) ÖNCE ekleniyor.
    # _truncate_contexts _MAX_CONTEXTS ile baştaki öğeleri alır; ek
    # kaynaklar sona eklenirse ChromaDB chunk sayısına göre kesilir.
    contexts = []
    if response.graf_baglami:
        contexts.append(response.graf_baglami)
    if response.kumlatif_metin:
        contexts.append(response.kumlatif_metin)
    if response.cyp_metin:
        contexts.append(response.cyp_metin)
    contexts += [k.icerik for k in response.kaynaklar]

    return {
        "question":     q["soru"],
        "answer":       response.yanit,
        "contexts":     contexts,
        "ground_truth": q["ground_truth"],
        "soru_id":      q["id"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PharmAssist RAGAS Değerlendirme")
    parser.add_argument("--v2", action="store_true",
                        help="Dalga 2 soru seti kullan (data/eval/ragas_v2_questions.json)")
    parser.add_argument("--v4", action="store_true",
                        help="Dalga 3 sonrası v4 ölçümü (aynı sorular, ragas_v4_results.json'a yazar)")
    parser.add_argument("--v10", action="store_true",
                        help="v10 clean questions (5 soru, tüm ilaçlar mevcut, Mistral ile)")
    parser.add_argument("--questions", default=None,
                        help="Özel soru dosyası (JSON)")
    parser.add_argument("--output", default=None,
                        help="Sonuç çıktı dosyası (JSON)")
    parser.add_argument("--evaluator", default=None, choices=["haiku", "local"],
                        help="RAGAS evaluator: 'haiku' (Anthropic API) veya 'local' (LM Studio). "
                             "Varsayılan: RAGAS_PROVIDER env var")
    args = parser.parse_args()

    # Soru dosyasını belirle
    if args.questions:
        questions_path = args.questions
        output_path = args.output or "data/eval/ragas_custom_results.json"
    elif args.v10:
        questions_path = "data/eval/ragas_v10_clean_questions.json"
        output_path = args.output or "data/eval/ragas_v11_results.json"
    elif args.v4:
        questions_path = "data/eval/ragas_v2_questions.json"  # Aynı sorular, yeni ayarlarla
        output_path = args.output or "data/eval/ragas_v4_results.json"
    elif args.v2:
        questions_path = "data/eval/ragas_v2_questions.json"
        output_path = args.output or "data/eval/ragas_v2_results.json"
    else:
        questions_path = "data/eval/test_questions.json"
        output_path = args.output or "data/eval/ragas_results.json"

    print("PharmAssist — RAGAS Değerlendirmesi")
    print("="*60)
    print(f"Soru dosyası: {questions_path}")
    print(f"Çıktı:        {output_path}")
    print("="*60)

    # 1. Test sorularını yükle
    sorular = load_test_questions(questions_path)
    logger.info(f"{len(sorular)} test sorusu yüklendi.")

    # 2. Her soru için RAG çalıştır
    import time
    eval_records = []
    for i, q in enumerate(sorular, 1):
        logger.info(f"Soru {i}/{len(sorular)}: {q['soru'][:50]}...")
        last_err = None
        for attempt in range(1, 4):  # 3 deneme
            try:
                record = run_rag_on_question(q)
                eval_records.append(record)
                logger.info(f"  -> {len(record['contexts'])} chunk, {len(record['answer'])} karakter yanit")
                last_err = None
                break
            except Exception as e:
                last_err = e
                logger.warning(f"  -> Deneme {attempt}/3 HATA: {e}")
                if attempt < 3:
                    time.sleep(5)
        if last_err is not None:
            logger.error(f"  -> 3 denemede basarisiz, soru atlanıyor: {last_err}")

    logger.info(f"\n{len(eval_records)} soru RAG ile islendi. RAGAS baslatiliyor...")

    # 3. RAGAS değerlendirmesi
    try:
        result = run_ragas_evaluation(eval_records, evaluator_provider=args.evaluator)
        scores = result["scores"]
        per_question = result["per_question"]

        print_ragas_report(scores)

        # 4. Sonuçları kaydet — per_question'a yanıt ve context bilgisi ekle
        per_q_extended = []
        for pq, rec in zip(per_question, eval_records):
            per_q_extended.append({
                **pq,
                "answer":       rec.get("answer", ""),
                "ground_truth": rec.get("ground_truth", ""),
                "contexts":     rec.get("contexts", []),
                "soru_id":      rec.get("soru_id", ""),
            })

        output = {
            "scores":       scores,
            "n_questions":  len(eval_records),
            "provider":     os.environ.get("LLM_PROVIDER", "claude"),
            "evaluator":    args.evaluator or os.environ.get("RAGAS_PROVIDER", "local"),
            "questions_file": questions_path,
            "per_question": per_q_extended,
        }
        os.makedirs("data/eval", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info(f"Sonuclar {output_path} dosyasina kaydedildi.")

    except Exception as e:
        logger.error(f"RAGAS degerlendirme hatasi: {e}")
        import traceback
        traceback.print_exc()
