import sys
from pathlib import Path

# Proje kök dizinini ekle
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import json
import chromadb
from loguru import logger
from src.analysis.cyp450_mapper import ILAC_CYP_PROFILI
from src.analysis.cyp450_extractor import extract_cyp_profile_from_text
from src.data.normalization import normalize_drug_name

def measure():
    logger.info("CYP450 Extractor Hassasiyet (Precision/Recall) Ölçümü - V2")
    
    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection("kub_chunks")
    
    # Tüm Madde 4.5 chunk'larını çek
    all_chunks = col.get(where={"madde_no": "4.5"}, include=["documents", "metadatas"])
    
    # İlaç bazlı grupla (Tüm chunkları birleştir)
    drug_texts = {}
    for doc, meta in zip(all_chunks["documents"], all_chunks["metadatas"]):
        d_name = meta["ilac_adi"]
        drug_texts[d_name] = drug_texts.get(d_name, "") + "\n" + doc
    
    # Test edilecek hedef ilaçlar (Manuel listede olanlar)
    target_keys = ["LUSTRAL", "PLAVIX", "ELİQUİS", "XANAX", "FLAGYL", "CİPRO", "ONAXAN"]
    
    results = []
    
    for target in target_keys:
        # Bu hedef kelimeyi içeren gerçek ilacı bul
        found_key = None
        for k in drug_texts.keys():
            if target.upper() in k.upper():
                found_key = k
                break
        
        if not found_key:
            logger.warning(f"  {target} için KÜB metni ChromaDB'de bulunamadı.")
            continue
            
        ground_truth = ILAC_CYP_PROFILI.get(target) or ILAC_CYP_PROFILI.get(normalize_drug_name(target))
        if not ground_truth:
            logger.warning(f"  {target} için ground truth bulunamadı.")
            continue
            
        text = drug_texts[found_key]
        logger.info(f"  Analiz ediliyor: {found_key} (Karakter: {len(text)})")
        
        # Otomatik çıkarım yap (LLM)
        automated = extract_cyp_profile_from_text(text, found_key)
        
        # Karşılaştırma
        gt_subs = set(ground_truth.get("substrat", []))
        auto_subs = set(automated.get("substrat", []))
        gt_inh = set(ground_truth.get("inhibitor", []))
        auto_inh = set(automated.get("inhibitor", []))

        # TP: Örtüşenler
        tp_subs = gt_subs & auto_subs
        tp_inh = gt_inh & auto_inh
        tp_count = len(tp_subs) + len(tp_inh)
        
        # FP: Otomasyonun fazladan buldukları (Yanlış alarm)
        fp_subs = auto_subs - gt_subs
        fp_inh = auto_inh - gt_inh
        fp_count = len(fp_subs) + len(fp_inh)
        
        # FN: Manuel listede olup otomasyonun kaçırdıkları
        fn_subs = gt_subs - auto_subs
        fn_inh = gt_inh - auto_inh
        fn_count = len(fn_subs) + len(fn_inh)
        
        results.append({
            "drug": target,
            "tp": tp_count,
            "fp": fp_count,
            "fn": fn_count,
            "tp_list": list(tp_subs) + list(tp_inh),
            "fp_list": list(fp_subs) + list(fp_inh),
            "fn_list": list(fn_subs) + list(fn_inh)
        })
        
        logger.info(f"    Sonuç: TP={tp_count}, FP={fp_count}, FN={fn_count}")
        if fp_count > 0: logger.debug(f"      Faller Positive: {list(fp_subs) + list(fp_inh)}")
        if fn_count > 0: logger.debug(f"      Faller Negative: {list(fn_subs) + list(fn_inh)}")

    # Genel İstatistik
    total_tp = sum(r["tp"] for r in results)
    total_fp = sum(r["fp"] for r in results)
    total_fn = sum(r["fn"] for r in results)
    
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    
    logger.info("="*60)
    logger.success(f"ÖLÇÜM SONUÇLARI:")
    logger.info(f"  Toplam TP (Doğru Eşleşme): {total_tp}")
    logger.info(f"  Toplam FP (Yanlış/Fazla):   {total_fp}")
    logger.info(f"  Toplam FN (Kaçırılan):       {total_fn}")
    logger.info(f"  Hassasiyet (Precision): %{precision*100:.1f}")
    logger.info(f"  Geri Çağırma (Recall):  %{recall*100:.1f}")
    logger.info("="*60)
    
    if precision >= 0.85: # Kullanıcı %80 dedi, biz %85'i hedefliyoruz
        logger.success("✅ KRİTER SAĞLANDI: Otomasyon birincil yapılabilir.")
    else:
        logger.warning("❌ KRİTER SAĞLANAMADI: Otomasyon iyileştirilmeli veya strateji korunmalı.")

if __name__ == "__main__":
    measure()
