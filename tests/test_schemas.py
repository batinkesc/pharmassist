"""
Pydantic şema doğrulama testleri — dış bağımlılık gerektirmez.
"""

import pytest
from pydantic import ValidationError

from src.api.schemas import (
    PatientProfileRequest,
    QueryRequest,
    QueryResponse,
    ChunkSource,
    KumulatifRiskItem,
    CYPEtkilesimItem,
)


class TestPatientProfileRequest:
    def test_minimal_valid(self):
        p = PatientProfileRequest(yas=30)
        assert p.yas == 30
        assert p.cinsiyet == "belirtilmemiş"
        assert p.mevcut_ilaclar == []

    def test_yas_sinir_deger(self):
        PatientProfileRequest(yas=0)
        PatientProfileRequest(yas=120)

    def test_yas_negatif_hatasi(self):
        with pytest.raises(ValidationError):
            PatientProfileRequest(yas=-1)

    def test_yas_asiri_buyuk_hatasi(self):
        with pytest.raises(ValidationError):
            PatientProfileRequest(yas=121)

    def test_gfr_sinirlar(self):
        p = PatientProfileRequest(yas=50, gfr=0)
        assert p.gfr == 0
        p2 = PatientProfileRequest(yas=50, gfr=200)
        assert p2.gfr == 200

    def test_gfr_asiri_buyuk_hatasi(self):
        with pytest.raises(ValidationError):
            PatientProfileRequest(yas=50, gfr=201)

    def test_lab_degerleri(self):
        p = PatientProfileRequest(yas=50, lab_degerleri={"ALT": 45.0, "K": 4.2})
        assert p.lab_degerleri["ALT"] == 45.0


class TestQueryRequest:
    def test_valid_query(self, hasta_dict):
        q = QueryRequest(
            soru="Bu hastaya ibuprofen verebilir miyiz?",
            hasta=PatientProfileRequest(**hasta_dict),
        )
        assert q.n_results == 5  # default

    def test_soru_cok_kisa(self, hasta_dict):
        with pytest.raises(ValidationError):
            QueryRequest(
                soru="Mı?",
                hasta=PatientProfileRequest(**hasta_dict),
            )

    def test_n_results_sinirlar(self, hasta_dict):
        hasta = PatientProfileRequest(**hasta_dict)
        QueryRequest(soru="Yeterli uzunlukta soru?", hasta=hasta, n_results=1)
        QueryRequest(soru="Yeterli uzunlukta soru?", hasta=hasta, n_results=15)

    def test_n_results_sifir_hatasi(self, hasta_dict):
        with pytest.raises(ValidationError):
            QueryRequest(
                soru="Yeterli uzunlukta soru?",
                hasta=PatientProfileRequest(**hasta_dict),
                n_results=0,
            )

    def test_hedef_ilaclar_none(self, hasta_dict):
        q = QueryRequest(
            soru="Yeterli uzunlukta soru?",
            hasta=PatientProfileRequest(**hasta_dict),
            hedef_ilaclar=None,
        )
        assert q.hedef_ilaclar is None


class TestQueryResponse:
    def test_minimal_response(self):
        r = QueryResponse(
            soru="Test soru",
            yanit="Test yanıt",
            kaynaklar=[],
            hasta_ozeti="68y erkek",
            soru_turleri=["etkilesim"],
            model="claude-haiku",
            prompt_token_sayisi=100,
            yanit_token_sayisi=50,
        )
        assert r.kumlatif_riskler == []
        assert r.cyp_etkilesimler == []


class TestKumulatifRiskItem:
    def _valid(self, **kwargs):
        defaults = dict(
            kategori_kodu="RENAL",
            kategori_label="Böbrek Yükü",
            ilaclar=["Augmentin", "Plasоrin"],
            siddet="yüksek",
            aciklama="Kombine kullanımda nefrotoksisite riski.",
        )
        defaults.update(kwargs)
        return KumulatifRiskItem(**defaults)

    def test_valid_creation(self):
        item = self._valid()
        assert item.kategori_kodu == "RENAL"
        assert item.siddet == "yüksek"
        assert len(item.ilaclar) == 2

    def test_bos_ilac_listesi(self):
        item = self._valid(ilaclar=[])
        assert item.ilaclar == []

    def test_tek_ilac(self):
        item = self._valid(ilaclar=["Augmentin"])
        assert item.ilaclar == ["Augmentin"]

    def test_zorunlu_alan_eksik_kategori_kodu(self):
        with pytest.raises(ValidationError):
            KumulatifRiskItem(
                kategori_label="Böbrek",
                ilaclar=[],
                siddet="düşük",
                aciklama="Test",
            )

    def test_zorunlu_alan_eksik_siddet(self):
        with pytest.raises(ValidationError):
            KumulatifRiskItem(
                kategori_kodu="HEPATIK",
                kategori_label="Karaciğer",
                ilaclar=[],
                aciklama="Test",
            )

    def test_json_serializable(self):
        item = self._valid()
        d = item.model_dump()
        assert d["kategori_kodu"] == "RENAL"
        assert isinstance(d["ilaclar"], list)


class TestCYPEtkilesimItem:
    def _valid(self, **kwargs):
        defaults = dict(
            enzim="CYP3A4",
            sorgu_ilac="Onaxan",
            etkilesen_ilac="Augmentin",
            rol="inhibitör",
            sonuc="Onaxan plazma düzeyi artabilir",
            siddet="orta",
        )
        defaults.update(kwargs)
        return CYPEtkilesimItem(**defaults)

    def test_valid_creation(self):
        item = self._valid()
        assert item.enzim == "CYP3A4"
        assert item.rol == "inhibitör"

    def test_farkli_enzimler(self):
        for enzim in ["CYP2D6", "CYP2C9", "CYP1A2"]:
            item = self._valid(enzim=enzim)
            assert item.enzim == enzim

    def test_zorunlu_alan_eksik_enzim(self):
        with pytest.raises(ValidationError):
            CYPEtkilesimItem(
                sorgu_ilac="Onaxan",
                etkilesen_ilac="Augmentin",
                rol="inhibitör",
                sonuc="Test",
                siddet="düşük",
            )

    def test_zorunlu_alan_eksik_rol(self):
        with pytest.raises(ValidationError):
            CYPEtkilesimItem(
                enzim="CYP3A4",
                sorgu_ilac="Onaxan",
                etkilesen_ilac="Augmentin",
                sonuc="Test",
                siddet="orta",
            )

    def test_json_serializable(self):
        item = self._valid()
        d = item.model_dump()
        assert d["enzim"] == "CYP3A4"
        assert d["siddet"] == "orta"

    def test_response_icinde_listeler(self):
        r = QueryResponse(
            soru="Test soru",
            yanit="Test yanıt",
            kaynaklar=[],
            hasta_ozeti="45y kadın",
            soru_turleri=["cyp450"],
            model="claude-haiku",
            prompt_token_sayisi=80,
            yanit_token_sayisi=40,
            kumlatif_riskler=[
                KumulatifRiskItem(
                    kategori_kodu="RENAL",
                    kategori_label="Böbrek",
                    ilaclar=["DrugA"],
                    siddet="yüksek",
                    aciklama="Risk var.",
                )
            ],
            cyp_etkilesimler=[
                CYPEtkilesimItem(
                    enzim="CYP2D6",
                    sorgu_ilac="DrugA",
                    etkilesen_ilac="DrugB",
                    rol="substrat",
                    sonuc="Etki artar",
                    siddet="orta",
                )
            ],
        )
        assert len(r.kumlatif_riskler) == 1
        assert len(r.cyp_etkilesimler) == 1
        assert r.kumlatif_riskler[0].kategori_kodu == "RENAL"
        assert r.cyp_etkilesimler[0].enzim == "CYP2D6"
