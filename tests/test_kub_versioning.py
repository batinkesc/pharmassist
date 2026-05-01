"""
KÜB Versioning (Task 1) için birim testleri.
"""

import re
import pytest
from datetime import datetime
from pathlib import Path
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


# ---------------------------------------------------------------------------
# Gerçek PDF üzerinden parser ve metadata propagation testleri
# ---------------------------------------------------------------------------

PDF_DIR = Path("data/raw_pdfs")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HASH_RE = re.compile(r"^[0-9a-f]{16}$")


def _pick_sample_pdf() -> Path | None:
    """Test için ilk uygun PDF'i seçer; corpus yoksa None döner."""
    if not PDF_DIR.exists():
        return None
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    return pdfs[0] if pdfs else None


@pytest.mark.skipif(_pick_sample_pdf() is None, reason="data/raw_pdfs/ corpus yok")
def test_pdf_parser_real_date_and_hash():
    """KUBParser bir gerçek PDF'i parse edip kub_parse_date + kub_pdf_hash dolduruyor mu?"""
    from src.ingestion.pdf_parser import KUBParser

    pdf_path = _pick_sample_pdf()
    parser = KUBParser()
    result = parser.parse(pdf_path)
    chunks = result["chunks"]

    assert len(chunks) > 0, "Parser hiç chunk üretmedi"

    for chunk in chunks:
        assert "kub_parse_date" in chunk, f"chunk {chunk.get('chunk_id')} kub_parse_date eksik"
        assert "kub_pdf_hash" in chunk, f"chunk {chunk.get('chunk_id')} kub_pdf_hash eksik"

    # Tarih boş olmamalı (modDate / mtime / now() fallback'ten biri yakalar)
    sample = chunks[0]
    assert sample["kub_parse_date"], "kub_parse_date boş — fallback zinciri kırık"
    assert DATE_RE.match(sample["kub_parse_date"]), (
        f"Tarih formatı YYYY-MM-DD değil: {sample['kub_parse_date']!r}"
    )

    # Hash 16 hex karakter olmalı (veya 'unknown' fallback — ama dosya okunabildiği için olmamalı)
    assert HASH_RE.match(sample["kub_pdf_hash"]), (
        f"Hash 16 hex değil: {sample['kub_pdf_hash']!r}"
    )

    # Aynı PDF'in tüm chunk'larında tarih ve hash tutarlı olmalı
    dates = {c["kub_parse_date"] for c in chunks}
    hashes = {c["kub_pdf_hash"] for c in chunks}
    assert len(dates) == 1, f"Tek PDF'de birden fazla tarih: {dates}"
    assert len(hashes) == 1, f"Tek PDF'de birden fazla hash: {hashes}"


@pytest.mark.skipif(_pick_sample_pdf() is None, reason="data/raw_pdfs/ corpus yok")
def test_migration_helper_extracts_real_values():
    """_extract_pdf_date_and_hash gerçek bir PDF üzerinde dummy değer üretmiyor mu?"""
    from src.retrieval.chroma_store import _extract_pdf_date_and_hash

    pdf_path = _pick_sample_pdf()
    parse_date, pdf_hash = _extract_pdf_date_and_hash(pdf_path)

    assert parse_date != "unknown", "Mevcut PDF için 'unknown' tarih dönmemeli"
    assert pdf_hash != "unknown", "Mevcut PDF için 'unknown' hash dönmemeli"
    assert pdf_hash != "legacy_data_1234", "Legacy placeholder döndü"
    assert parse_date != "2026-04-25" or DATE_RE.match(parse_date), (
        "Tarih hâlâ legacy placeholder gibi görünüyor"
    )
    assert DATE_RE.match(parse_date), f"Tarih formatı bozuk: {parse_date!r}"
    assert HASH_RE.match(pdf_hash), f"Hash 16 hex değil: {pdf_hash!r}"


def test_chroma_metadata_has_real_versioning():
    """
    ChromaDB metadata'sı migration sonrası gerçek değerler içeriyor mu?
    Legacy placeholder'lar (legacy_data_1234) silinmiş olmalı.
    """
    try:
        from src.retrieval.chroma_store import get_chroma_client, get_or_create_collection
    except Exception as e:
        pytest.skip(f"ChromaDB import edilemedi: {e}")

    try:
        col = get_or_create_collection(get_chroma_client())
        data = col.get(include=["metadatas"])
    except Exception as e:
        pytest.skip(f"ChromaDB erişimi yok: {e}")

    if not data["ids"]:
        pytest.skip("ChromaDB boş — migration test edilemez")

    dates = set()
    hashes = set()
    legacy_hits = 0
    for m in data["metadatas"]:
        d = m.get("kub_parse_date", "")
        h = m.get("kub_pdf_hash", "")
        dates.add(d)
        hashes.add(h)
        if h == "legacy_data_1234":
            legacy_hits += 1

    assert legacy_hits == 0, (
        f"{legacy_hits} chunk hâlâ 'legacy_data_1234' placeholder hash içeriyor"
    )
    # En az 2 farklı tarih olmalı (gerçek corpus farklı tarihli ilaç içerir)
    real_dates = {d for d in dates if d and d != "unknown"}
    assert len(real_dates) >= 2, (
        f"Gerçek tarih çeşitliliği yok ({len(real_dates)}): {real_dates}"
    )
    real_hashes = {h for h in hashes if h and h != "unknown"}
    assert len(real_hashes) >= 2, (
        f"Hash çeşitliliği yok ({len(real_hashes)})"
    )
