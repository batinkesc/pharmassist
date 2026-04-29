import sys
import os
from pathlib import Path

# Proje kök dizinini ekle
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger
import chromadb
from chromadb.config import Settings
from src.data.normalization import normalize_drug_name
from src.graph.neo4j_client import run_query

def normalize_chromadb():
    logger.info("ChromaDB normalizasyonu başlatılıyor...")
    client = chromadb.PersistentClient(
        path=str(ROOT / "chroma_db"),
        settings=Settings(anonymized_telemetry=False)
    )
    
    try:
        collection = client.get_collection("kub_chunks")
    except Exception as e:
        logger.error(f"Koleksiyon bulunamadı: {e}")
        return

    # Tüm verileri çek
    results = collection.get(include=["metadatas"])
    ids = results["ids"]
    metadatas = results["metadatas"]
    
    updated_count = 0
    batch_ids = []
    batch_metas = []
    
    for i, meta in enumerate(metadatas):
        old_name = meta.get("ilac_adi", "")
        new_name = normalize_drug_name(old_name)
        
        if old_name != new_name:
            meta["ilac_adi"] = new_name
            batch_ids.append(ids[i])
            batch_metas.append(meta)
            updated_count += 1
            
        # 100'lük batch'ler halinde güncelle
        if len(batch_ids) >= 100:
            collection.update(ids=batch_ids, metadatas=batch_metas)
            batch_ids = []
            batch_metas = []
            logger.info(f"  {updated_count} chunk güncellendi...")

    if batch_ids:
        collection.update(ids=batch_ids, metadatas=batch_metas)
        
    logger.info(f"✓ ChromaDB tamamlandı. Toplam {updated_count} metadata güncellendi.")

def normalize_neo4j():
    logger.info("Neo4j normalizasyonu başlatılıyor...")
    
    # Tüm ilaç düğümlerini al
    drugs = run_query("MATCH (d:Drug) RETURN d.name as name")
    
    updated_count = 0
    for drug in drugs:
        old_name = drug["name"]
        new_name = normalize_drug_name(old_name)
        
        if old_name != new_name:
            # Önce hedef isimli bir düğüm var mı kontrol et (merge riskine karşı)
            # Eğer varsa, bu düğümü onunla birleştirmek gerekebilir ama şimdilik sadece ismi güncelliyoruz.
            # Not: Neo4j'de aynı isimli birden fazla düğüm olabilir, bu yüzden UNIQUE constraint'e dikkat!
            run_query(
                "MATCH (d:Drug {name: $old}) SET d.name = $new",
                {"old": old_name, "new": new_name}
            )
            updated_count += 1
            if updated_count % 50 == 0:
                logger.info(f"  {updated_count} düğüm güncellendi...")

    logger.info(f"✓ Neo4j tamamlandı. Toplam {updated_count} Drug düğümü güncellendi.")

if __name__ == "__main__":
    logger.info("VERİTABANI KALICI NORMALİZASYON SÜRECİ")
    normalize_chromadb()
    normalize_neo4j()
    logger.info("Süreç başarıyla tamamlandı.")
