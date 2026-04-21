"""
FastAPI router — PharmAssist endpoint'leri.

Endpoint'ler:
  GET  /health          → sistem durumu
  POST /query           → RAG sorgusu (ana endpoint)
  GET  /stats           → ChromaDB koleksiyon istatistikleri
"""

import re
from pathlib import Path
from fastapi import APIRouter, Depends, Header, HTTPException
from loguru import logger

from src.api.schemas import (
    QueryRequest, QueryResponse, StatsResponse, HealthResponse,
    ChunkSource, KumulatifRiskItem, CYPEtkilesimItem,
    QuarantineItem, QuarantineResponse,
)
from src.agents.patient_profile import PatientProfile
from src.agents.rag_engine import run_rag, DEFAULT_MODEL
from src.retrieval.chroma_store import collection_stats, get_chroma_client, get_or_create_collection
from src.config.settings import settings

router = APIRouter()


def _verify_api_key(x_api_key: str = Header(default=None)) -> None:
    """PHARMASSIST_API_KEY ayarlanmışsa X-API-Key header'ı doğrular."""
    if not settings.auth_enabled:
        return
    if x_api_key != settings.pharmassist_api_key:
        raise HTTPException(status_code=401, detail="Geçersiz veya eksik X-API-Key")


@router.get("/health", response_model=HealthResponse, tags=["sistem"])
def health_check():
    """Sistem durumunu döner."""
    try:
        client = get_chroma_client()
        collection = get_or_create_collection(client)
        count = collection.count()
        # Yüklü ilaç sayısı
        all_meta = collection.get(include=["metadatas"])["metadatas"]
        ilac_sayisi = len({m.get("ilac_adi", "") for m in all_meta})
    except Exception as e:
        logger.error(f"ChromaDB bağlantı hatası: {e}")
        raise HTTPException(status_code=503, detail="ChromaDB bağlantısı kurulamadı")

    return HealthResponse(
        durum="ok",
        chroma_chunk_sayisi=count,
        yuklü_ilac_sayisi=ilac_sayisi,
        model=DEFAULT_MODEL,
    )


@router.post("/query", response_model=QueryResponse, tags=["rag"])
def query(req: QueryRequest, _: None = Depends(_verify_api_key)):
    """
    Ana RAG sorgu endpoint'i.

    Hasta profilini ve soruyu alır, KÜB'e dayalı klinik analiz döner.
    """
    # PatientProfile oluştur
    profil = PatientProfile(
        yas=req.hasta.yas,
        cinsiyet=req.hasta.cinsiyet,
        gfr=req.hasta.gfr,
        karaciger_skoru=req.hasta.karaciger_skoru,
        mevcut_ilaclar=req.hasta.mevcut_ilaclar,
        alerjiler=req.hasta.alerjiler,
        endikasyonlar=req.hasta.endikasyonlar,
        gebelik=req.hasta.gebelik,
        emzirme=req.hasta.emzirme,
        lab_degerleri=req.hasta.lab_degerleri,
        notlar=req.hasta.notlar,
    )

    logger.info(f"Query alındı: '{req.soru[:60]}' | Hasta: {req.hasta.yas}y GFR={req.hasta.gfr}")

    try:
        response = run_rag(
            soru=req.soru,
            profil=profil,
            hedef_ilaclar=req.hedef_ilaclar,
            n_results=req.n_results,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"RAG hatası: {e}")
        raise HTTPException(status_code=500, detail="RAG pipeline hatası")

    kaynaklar = [
        ChunkSource(
            chunk_id=k.chunk_id,
            ilac_adi=k.ilac_adi,
            madde_no=k.madde_no,
            madde_baslik=k.madde_baslik,
            alt_madde=k.alt_madde,
            sayfa=k.sayfa,
            score=k.score,
            kaynak_etiketi=k.kaynak_etiketi(),
        )
        for k in response.kaynaklar
    ]

    kumlatif_riskler = [
        KumulatifRiskItem(
            kategori_kodu=r.kategori_kodu,
            kategori_label=r.kategori_label,
            ilaclar=r.ilaclar,
            siddet=r.siddet,
            aciklama=r.aciklama,
        )
        for r in response.kumlatif_riskler
    ]

    cyp_etkilesimler = [
        CYPEtkilesimItem(
            enzim=e.enzim,
            sorgu_ilac=e.sorgu_ilac,
            etkilesen_ilac=e.etkilesen_ilac,
            rol=e.rol,
            sonuc=e.sonuc,
            siddet=e.siddet,
        )
        for e in response.cyp_etkilesimler
    ]

    return QueryResponse(
        soru=response.soru,
        yanit=response.yanit,
        kaynaklar=kaynaklar,
        hasta_ozeti=response.hasta_ozeti,
        soru_turleri=response.soru_turleri,
        model=response.model,
        prompt_token_sayisi=response.prompt_token_sayisi,
        yanit_token_sayisi=response.yanit_token_sayisi,
        kumlatif_riskler=kumlatif_riskler,
        cyp_etkilesimler=cyp_etkilesimler,
        cyp_source=response.cyp_source,
        quarantine_warnings=response.quarantine_warnings,
    )


@router.get("/stats", response_model=StatsResponse, tags=["sistem"])
def stats():
    """ChromaDB koleksiyon istatistiklerini döner."""
    try:
        data = collection_stats()
    except Exception as e:
        logger.error(f"Stats hatası: {e}")
        raise HTTPException(status_code=500, detail="İstatistik alınamadı")

    return StatsResponse(
        toplam_chunk=data["toplam_chunk"],
        ilac_dagilimi=data["ilac_dagilimi"],
        madde_dagilimi=data["madde_dagilimi"],
    )


@router.get("/quarantine", response_model=QuarantineResponse, tags=["sistem"])
def quarantine():
    """
    Parse QA'dan geçemeyen ilaçların listesini döner.
    data/quarantine/ klasöründeki rapor dosyalarından okunur.
    """
    quarantine_dir = Path(__file__).resolve().parent.parent.parent / "data" / "quarantine"
    items: list[QuarantineItem] = []

    if quarantine_dir.exists():
        for md_file in sorted(quarantine_dir.glob("*_parse_fail.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                # İlaç adını başlıktan al
                ilac_match = re.search(r"^#\s+Parse QA Başarısız:\s*(.+)$", content, re.MULTILINE)
                ilac_adi = ilac_match.group(1).strip() if ilac_match else md_file.stem
                # PDF dosya adını al
                pdf_match = re.search(r"\*\*PDF Dosyası:\*\*\s*`([^`]+)`", content)
                pdf_dosyasi = pdf_match.group(1) if pdf_match else ""
                # Hataları al
                hatalar = re.findall(r"^\d+\.\s+(.+)$", content, re.MULTILINE)
                items.append(QuarantineItem(
                    ilac_adi=ilac_adi,
                    pdf_dosyasi=pdf_dosyasi,
                    hatalar=hatalar,
                    rapor_dosyasi=str(md_file),
                ))
            except Exception as e:
                logger.warning(f"Karantina raporu okunamadı ({md_file}): {e}")

    return QuarantineResponse(karantina_sayisi=len(items), ilaçlar=items)
