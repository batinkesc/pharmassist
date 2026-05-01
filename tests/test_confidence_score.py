import pytest
from src.agents.rag_engine import _hesapla_guven_skoru, RetrievedChunk

def test_kaynak_yok_veya_yanit_bos():
    # Kaynak yok
    skor, etiket = _hesapla_guven_skoru([], "BİLGİ YOK")
    assert skor == 0.0
    assert "Kaynak yok" in etiket

    # Yanıt boş
    chunk = RetrievedChunk(chunk_id="1", ilac_adi="A", madde_no="1", madde_baslik="B", icerik="C", score=0.9, sayfa=1, kaynak_dosya="D", alt_madde="", kub_parse_date="", kub_pdf_hash="")
    skor, etiket = _hesapla_guven_skoru([chunk], "   ")
    assert skor == 0.0
    assert "Kaynak yok" in etiket

def test_yuksek_skor():
    chunk1 = RetrievedChunk(chunk_id="1", ilac_adi="A", madde_no="1", madde_baslik="B", icerik="C", score=0.9, sayfa=1, kaynak_dosya="D", alt_madde="", kub_parse_date="", kub_pdf_hash="")
    chunk2 = RetrievedChunk(chunk_id="2", ilac_adi="A", madde_no="1", madde_baslik="B", icerik="C", score=0.85, sayfa=1, kaynak_dosya="D", alt_madde="", kub_parse_date="", kub_pdf_hash="")
    
    # 2 chunk, average score = 0.875. retrieval_skoru = 0.875.
    # 3 cümle, 0 doğrulanamadı. validate_orani = 1.0.
    # guven = 0.6 * 0.875 + 0.4 * 1.0 = 0.525 + 0.4 = 0.925
    yanit = "Bu birinci cümle. Bu ikinci cümle. Bu da üçüncü cümle."
    skor, etiket = _hesapla_guven_skoru([chunk1, chunk2], yanit)
    
    assert skor > 0.75
    assert "Yüksek güven" in etiket

def test_orta_skor_dogrulanamadi():
    chunk1 = RetrievedChunk(chunk_id="1", ilac_adi="A", madde_no="1", madde_baslik="B", icerik="C", score=0.80, sayfa=1, kaynak_dosya="D", alt_madde="", kub_parse_date="", kub_pdf_hash="")
    
    # retrieval_skoru = 0.80.
    # 2 cümle, 1 doğrulanamadı. validate_orani = 1.0 - (1/2) = 0.5.
    # guven = 0.6 * 0.80 + 0.4 * 0.5 = 0.48 + 0.20 = 0.68
    yanit = "Bu cümle doğru. Bu cümle yanlış [DOĞRULANAMADI]."
    skor, etiket = _hesapla_guven_skoru([chunk1], yanit)
    
    assert 0.55 <= skor < 0.75
    assert "Orta güven" in etiket

def test_matematik_dogrulugu():
    chunk1 = RetrievedChunk(chunk_id="1", ilac_adi="A", madde_no="1", madde_baslik="B", icerik="C", score=0.50, sayfa=1, kaynak_dosya="D", alt_madde="", kub_parse_date="", kub_pdf_hash="")
    
    # retrieval_skoru = 0.50.
    # 5 cümle, 3 [DOĞRULANAMADI], 1 [AŞIRI YORUM] -> total 4 hatalı
    # validate_orani = 1.0 - (4/5) = 0.2
    # guven = 0.6 * 0.50 + 0.4 * 0.2 = 0.30 + 0.08 = 0.38
    yanit = "Cümle bir. Cümle iki [DOĞRULANAMADI]. Cümle üç [AŞIRI YORUM: x]. Cümle dört [DOĞRULANAMADI]. Cümle beş [DOĞRULANAMADI]."
    skor, etiket = _hesapla_guven_skoru([chunk1], yanit)
    
    assert abs(skor - 0.38) < 0.0001
    assert "Düşük güven" in etiket
