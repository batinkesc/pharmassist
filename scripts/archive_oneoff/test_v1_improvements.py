import sys
from pathlib import Path

# Proje kök dizinini ekle
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger
from src.retrieval.chroma_store import search
from src.analysis.cyp450_mapper import analiz_et
from dataclasses import dataclass

@dataclass
class MockChunk:
    ilac_adi: str
    madde_no: str
    icerik: str
    chunk_id: str = "mock-1"

def test_retrieval_normalization():
    logger.info("TEST: Arama Normalizasyonu")
    # "Lustral®" yerine "Lustral 50 mg" ile arayalım
    query = "Lustral 50 mg dozajı nedir?"
    results = search(query, k=3)
    
    found_lustral = False
    for r in results:
        logger.info(f"  Bulunan İlaç: '{r['ilac_adi']}' (Skor: {r['score']:.3f})")
        if "LUSTRAL" in r['ilac_adi'].upper():
            found_lustral = True
            # Metadata kontrolü
            if '®' in r['ilac_adi']:
                logger.error("  HATA: Metadata hala trademark içeriyor!")
            else:
                logger.info("  BİLGİ: Metadata temiz.")
                
    if found_lustral:
        logger.success("✓ Retrieval normalizasyon testi geçti.")
    else:
        logger.warning("! Lustral bulunamadı (belki veritabanında başka isimle kayıtlı).")

def test_cyp_fallback():
    logger.info("TEST: Otomatik CYP Extraction")
    # Veritabanında (ILAC_CYP_PROFILI) olmayan bir ilaç simüle edelim
    # Örnek metin (KÜB 4.5'ten bir parça)
    mock_text = """
    Aşağıdaki ilaçlarla birlikte kullanımında etkileşim görülebilir:
    Pek bilinmeyen bu ilaç, CYP3A4 inhibitörü olan ilaçlarla birlikte kullanıldığında 
    kan düzeyi artabilir çünkü kendisi bir CYP3A4 substratıdır.
    """
    mock_chunks = [
        MockChunk(ilac_adi="X-ILACI", madde_no="4.5", icerik=mock_text)
    ]
    
    # Hastanın ilacı CYP3A4 inhibitörü olsun (örn: Klaritromisin)
    hasta_ilaclari = ["Klaritromisin"] # Bu statik listede var ve CYP3A4 inhibitörü
    
    logger.info("  'X-ILACI' (bilinmeyen ilaç) için etkileşim analizi yapılıyor...")
    sonuc = analiz_et(
        chunklar=mock_chunks,
        hasta_ilaclar=hasta_ilaclari,
        sorgu_ilaclar=["X-ILACI"]
    )
    
    logger.info(f"  Analiz Sonucu: {sonuc.ozet_metin}")
    if any(e.enzim == "CYP3A4" and e.rol == "inhibitor" for e in sonuc.etkilesimler):
        logger.success("✓ Otomatik CYP extraction ve fallback başarılı.")
    else:
        logger.error("x CYP extraction başarısız veya etkileşim tespit edilemedi.")

if __name__ == "__main__":
    logger.info("V1.0 STABLE İYİLEŞTİRME TESTLERİ")
    test_retrieval_normalization()
    print("-" * 50)
    test_cyp_fallback()
