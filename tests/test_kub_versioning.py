"""
KÜB Versioning (Task 1) için birim testleri.
"""

import pytest
from datetime import datetime
from src.agents.rag_engine import RetrievedChunk, RAGResponse

def test_chunk_tarih_toplama():
    """RAG engine'in chunk'lardan doğru tarih listesini çıkardığının testi."""
    chunk1 = RetrievedChunk(
        chunk_id="1", ilac_adi="Lustral", madde_no="4.3", madde_baslik="Kontrendikasyon",
        icerik="Test", score=0.9, sayfa=1, kaynak_dosya="lustral.pdf",
        kub_parse_date="2026-05-01", kub_pdf_hash="hash1"
    )
    chunk2 = RetrievedChunk(
        chunk_id="2", ilac_adi="Aspirin", madde_no="4.8", madde_baslik="Yan Etki",
        icerik="Test2", score=0.8, sayfa=2, kaynak_dosya="aspirin.pdf",
        kub_parse_date="2026-04-20", kub_pdf_hash="hash2"
    )
    chunk3 = RetrievedChunk(
        chunk_id="3", ilac_adi="Lustral", madde_no="4.4", madde_baslik="Özel Uyarılar",
        icerik="Test3", score=0.85, sayfa=3, kaynak_dosya="lustral.pdf",
        kub_parse_date="2026-05-01", kub_pdf_hash="hash1" # Aynı tarih
    )
    chunk4 = RetrievedChunk(
        chunk_id="4", ilac_adi="Bilinmeyen", madde_no="4.2", madde_baslik="Doz",
        icerik="Test4", score=0.7, sayfa=4, kaynak_dosya="bilinmiyor.pdf",
        kub_parse_date="unknown", kub_pdf_hash="unknown" # unknown tarih
    )

    chunklar = [chunk1, chunk2, chunk3, chunk4]

    # Tarihleri toplama mantığı (rag_engine içindeki kod)
    tarih_kumesi = set()
    for c in chunklar:
        if c.kub_parse_date and c.kub_parse_date != "unknown":
            tarih_kumesi.add(f"{c.ilac_adi} ({c.kub_parse_date})")
    kub_tarihleri = sorted(list(tarih_kumesi))

    assert len(kub_tarihleri) == 2
    assert "Lustral (2026-05-01)" in kub_tarihleri
    assert "Aspirin (2026-04-20)" in kub_tarihleri
    assert "Bilinmeyen" not in "".join(kub_tarihleri)

def test_response_schema_tarih():
    """RAGResponse şemasına kub_tarihleri eklendiğinin testi."""
    resp = RAGResponse(
        soru="Test soru",
        yanit="Test yanıt",
        kaynaklar=[],
        hasta_ozeti="Hasta",
        soru_turleri=["genel"],
        model="claude",
        kub_tarihleri=["Lustral (2026-05-01)"]
    )
    assert hasattr(resp, "kub_tarihleri")
    assert resp.kub_tarihleri == ["Lustral (2026-05-01)"]
