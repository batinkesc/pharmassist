"""
FastAPI Pydantic şemaları — request ve response modelleri.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ---------------------------------------------------------------------------
# Request şemaları
# ---------------------------------------------------------------------------

class PatientProfileRequest(BaseModel):
    yas: int = Field(..., ge=0, le=120, description="Hasta yaşı")
    cinsiyet: str = Field("belirtilmemiş", description="erkek | kadın | belirtilmemiş")
    gfr: Optional[float] = Field(None, ge=0, le=200, description="eGFR mL/dak/1.73m²")
    karaciger_skoru: Optional[str] = Field(None, description="Child-Pugh: A | B | C")
    mevcut_ilaclar: list[str] = Field(default_factory=list)
    alerjiler: list[str] = Field(default_factory=list)
    endikasyonlar: list[str] = Field(default_factory=list)
    gebelik: bool = False
    emzirme: bool = False
    lab_degerleri: dict[str, float] = Field(
        default_factory=dict,
        description="Lab değerleri: {'ALT': 120, 'K': 5.6, 'HbA1c': 8.2, ...}"
    )
    notlar: str = ""

    model_config = {
        "json_schema_extra": {
            "example": {
                "yas": 68,
                "cinsiyet": "erkek",
                "gfr": 38.0,
                "mevcut_ilaclar": ["Metformin 1000 mg", "Ramipril 10 mg", "Atorvastatin 20 mg"],
                "alerjiler": ["penisilin"],
                "endikasyonlar": ["Tip 2 Diyabet", "Hipertansiyon", "Hiperlipidemi"],
                "lab_degerleri": {"ALT": 120, "AST": 95, "K": 5.6, "HbA1c": 8.2, "Kreatinin": 1.8}
            }
        }
    }


class QueryRequest(BaseModel):
    soru: str = Field(..., min_length=5, description="Klinisyenin sorusu")
    hasta: PatientProfileRequest
    hedef_ilaclar: Optional[list[str]] = Field(
        None,
        description="Sorgunun odaklandığı ilaçlar (None ise tüm koleksiyon)"
    )
    n_results: int = Field(5, ge=1, le=15, description="Retrieval chunk sayısı")

    model_config = {
        "json_schema_extra": {
            "example": {
                "soru": "Bu hastaya ibuprofen verebilir miyiz? Mevcut ilaçlarla etkileşimi var mı?",
                "hasta": {
                    "yas": 68,
                    "cinsiyet": "erkek",
                    "gfr": 38.0,
                    "mevcut_ilaclar": ["Metformin 1000 mg", "Ramipril 10 mg", "Atorvastatin 20 mg"],
                    "alerjiler": ["penisilin"],
                    "endikasyonlar": ["Tip 2 Diyabet", "Hipertansiyon", "Hiperlipidemi"]
                }
            }
        }
    }


# ---------------------------------------------------------------------------
# Response şemaları
# ---------------------------------------------------------------------------

class ChunkSource(BaseModel):
    chunk_id: str
    ilac_adi: str
    madde_no: str
    madde_baslik: str
    alt_madde: str
    sayfa: int
    score: float
    kaynak_etiketi: str


class KumulatifRiskItem(BaseModel):
    kategori_kodu: str
    kategori_label: str
    ilaclar: list[str]
    siddet: str
    aciklama: str


class CYPEtkilesimItem(BaseModel):
    enzim: str
    sorgu_ilac: str
    etkilesen_ilac: str
    rol: str
    sonuc: str
    siddet: str


class QueryResponse(BaseModel):
    soru: str
    yanit: str
    kaynaklar: list[ChunkSource]
    hasta_ozeti: str
    soru_turleri: list[str]
    model: str
    prompt_token_sayisi: int
    yanit_token_sayisi: int
    kumlatif_riskler: list[KumulatifRiskItem] = []
    cyp_etkilesimler: list[CYPEtkilesimItem] = []
    cyp_source: str = "unknown"
    quarantine_warnings: list[str] = []
    kub_tarihleri: list[str] = []


class StatsResponse(BaseModel):
    toplam_chunk: int
    ilac_dagilimi: dict[str, int]
    madde_dagilimi: dict[str, int]


class QuarantineItem(BaseModel):
    ilac_adi: str
    pdf_dosyasi: str
    hatalar: list[str]
    rapor_dosyasi: str


class QuarantineResponse(BaseModel):
    karantina_sayisi: int
    ilaçlar: list[QuarantineItem]


class HealthResponse(BaseModel):
    durum: str
    chroma_chunk_sayisi: int
    yuklü_ilac_sayisi: int
    model: str
