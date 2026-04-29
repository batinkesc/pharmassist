"""
mini_hyde_test.py - Q16/Q21/Q28 icin mini RAGAS, HyDE + sinonim etkisini olcer
"""
import sys, os, json, time, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\kesic\Desktop\PharmAssistVersion2")
os.chdir(r"C:\Users\kesic\Desktop\PharmAssistVersion2")
from dotenv import load_dotenv; load_dotenv()
from loguru import logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

from src.agents.patient_profile import PatientProfile
from src.agents.rag_engine import run_rag
from src.evaluation.ragas_eval import run_ragas_evaluation, print_ragas_report

TARGET_IDS = {"v3_q16", "v3_q21", "v3_q28"}

with open("data/eval/ragas_v3_questions.json", encoding="utf-8") as f:
    all_q = json.load(f)

sorular = [q for q in all_q if q["id"] in TARGET_IDS]
print(f"Hedef soru sayisi: {len(sorular)}")

def _extract_sonuc(yanit):
    if "## SONUC" not in yanit and "## SONUÇ" not in yanit:
        return yanit
    for marker in ["## SONUÇ", "## SONUC"]:
        if marker in yanit:
            start = yanit.index(marker)
            rest = yanit[start:]
            nxt = re.search(r"\n##\s", rest[8:])
            if nxt:
                return rest[:nxt.start() + 8].strip()
            return rest.strip()
    return yanit

eval_records = []
for q in sorular:
    hasta_data = q.get("hasta", {})
    profil = PatientProfile(
        yas=hasta_data.get("yas", 0),
        cinsiyet=hasta_data.get("cinsiyet", "belirtilmemis"),
        gfr=hasta_data.get("gfr"),
        karaciger_skoru=hasta_data.get("karaciger_skoru"),
        mevcut_ilaclar=hasta_data.get("mevcut_ilaclar", []),
        alerjiler=hasta_data.get("alerjiler", []),
        endikasyonlar=hasta_data.get("endikasyonlar", []),
        gebelik=hasta_data.get("gebelik", False),
        emzirme=hasta_data.get("emzirme", False),
        lab_degerleri=hasta_data.get("lab_degerleri", {}),
    )
    hedef = q.get("hedef_ilaclar")
    logger.info(f"Soru: {q['soru'][:60]}")
    
    for attempt in range(1, 4):
        try:
            resp = run_rag(soru=q["soru"], profil=profil, hedef_ilaclar=hedef)
            contexts = []
            if resp.graf_baglami: contexts.append(resp.graf_baglami)
            if resp.kumlatif_metin: contexts.append(resp.kumlatif_metin)
            if resp.cyp_metin: contexts.append(resp.cyp_metin)
            contexts += [k.icerik for k in resp.kaynaklar]
            
            eval_records.append({
                "question": q["soru"],
                "answer": _extract_sonuc(resp.yanit),
                "full_answer": resp.yanit,
                "contexts": contexts,
                "ground_truth": q["ground_truth"],
                "soru_id": q["id"],
            })
            logger.info(f"  -> {len(contexts)} chunk, {len(resp.yanit)} karakter")
            break
        except Exception as e:
            logger.warning(f"  Deneme {attempt}/3 HATA: {e}")
            if attempt < 3: time.sleep(5)

print(f"\n{len(eval_records)} soru islendi, RAGAS basliyor...")

result = run_ragas_evaluation(eval_records)
print_ragas_report(result["scores"])

print("\nSORU BAZLI (vs Run13):")
run13 = {
    "v3_q16": {"cr": 0.333, "f": 0.423},
    "v3_q21": {"cr": 0.333, "f": 0.444},
    "v3_q28": {"cr": 0.5,   "f": 0.571},
}
for pq in result["per_question"]:
    sid = eval_records[pq["question_id"]-1]["soru_id"] if pq["question_id"] <= len(eval_records) else "?"
    cr = pq.get("context_recall")
    ff = pq.get("faithfulness")
    prev = run13.get(sid, {})
    cr_str = ("%.3f" % cr) if cr is not None else "NaN"
    ff_str = ("%.3f" % ff) if ff is not None else "NaN"
    prev_cr_str = ("%.3f" % prev.get("cr", 0)) if prev else "?"
    delta_str = ""
    if cr is not None and prev.get("cr") is not None:
        d = cr - prev["cr"]
        delta_str = (" (+%.3f)" % d) if d >= 0 else (" (%.3f)" % d)
    print(f"  {sid}: CR={prev_cr_str}->{cr_str}{delta_str} F={ff_str}")

with open("data/eval/mini_hyde_sinonim_results.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("\nSonuclar: data/eval/mini_hyde_sinonim_results.json")
