"""
PatientProfile ve lab eşik testleri — dış bağımlılık gerektirmez.
"""

import pytest
from src.agents.patient_profile import PatientProfile, LAB_ESIKLERI, _lab_durumu


class TestPatientProfileOzellikleri:
    def test_bobrek_yetmezligi_true(self):
        p = PatientProfile(yas=68, gfr=38.0)
        assert p.bobrek_yetmezligi is True

    def test_bobrek_yetmezligi_false(self):
        p = PatientProfile(yas=45, gfr=72.0)
        assert p.bobrek_yetmezligi is False

    def test_bobrek_yetmezligi_bilinmiyor(self):
        p = PatientProfile(yas=45, gfr=None)
        assert p.bobrek_yetmezligi is False

    def test_bobrek_evresi_gfr_none(self):
        p = PatientProfile(yas=50)
        assert p.bobrek_evresi == "bilinmiyor"

    def test_bobrek_evresi_evre3b(self):
        p = PatientProfile(yas=50, gfr=35.0)
        assert "3b" in p.bobrek_evresi

    def test_geriyatrik_sinir(self):
        assert PatientProfile(yas=65).geriyatrik is True
        assert PatientProfile(yas=64).geriyatrik is False

    def test_karaciger_yetmezligi(self):
        assert PatientProfile(yas=50, karaciger_skoru="B").karaciger_yetmezligi is True
        assert PatientProfile(yas=50, karaciger_skoru="C").karaciger_yetmezligi is True
        assert PatientProfile(yas=50, karaciger_skoru="A").karaciger_yetmezligi is False
        assert PatientProfile(yas=50, karaciger_skoru=None).karaciger_yetmezligi is False


class TestLabDurumu:
    def test_alt_normal(self):
        assert _lab_durumu("ALT", 30) == "normal"

    def test_alt_yuksek(self):
        assert _lab_durumu("ALT", 80) == "yüksek"

    def test_alt_kritik(self):
        # kritik_kat=3, normal_ust=40 → kritik_sinir=120
        assert _lab_durumu("ALT", 120) == "kritik_yüksek"

    def test_k_kritik_yuksek(self):
        assert _lab_durumu("K", 5.5) == "kritik_yüksek"

    def test_k_kritik_dusuk(self):
        assert _lab_durumu("K", 3.5) == "kritik_düşük"

    def test_k_normal(self):
        assert _lab_durumu("K", 4.0) == "normal"

    def test_bilinmeyen_param(self):
        assert _lab_durumu("XYZ", 99) == "bilinmiyor"


class TestOverrideFlags:
    """pediyatrik_override ve geriyatrik_override yaş tabanlı türetmeyi geçersiz kılar."""

    def test_pediyatrik_override_true_yetiskin(self):
        """25 yaşlı yetişkin, override True → pediatrik aktif."""
        p = PatientProfile(yas=25, pediyatrik_override=True)
        assert p.pediyatrik is True

    def test_pediyatrik_override_false_cocuk(self):
        """10 yaşlı çocuk, override False → pediatrik devre dışı."""
        p = PatientProfile(yas=10, pediyatrik_override=False)
        assert p.pediyatrik is False

    def test_pediyatrik_override_none_yas_tabanli(self):
        """Override None → yaşa göre otomatik türetme."""
        assert PatientProfile(yas=17).pediyatrik is True
        assert PatientProfile(yas=18).pediyatrik is False

    def test_geriyatrik_override_true_genc(self):
        """40 yaşlı genç, override True → geriyatrik aktif."""
        p = PatientProfile(yas=40, geriyatrik_override=True)
        assert p.geriyatrik is True

    def test_geriyatrik_override_false_yasli(self):
        """70 yaşlı hasta, override False → geriyatrik devre dışı."""
        p = PatientProfile(yas=70, geriyatrik_override=False)
        assert p.geriyatrik is False

    def test_geriyatrik_override_none_yas_tabanli(self):
        """Override None → yaşa göre otomatik türetme."""
        assert PatientProfile(yas=65).geriyatrik is True
        assert PatientProfile(yas=64).geriyatrik is False

    def test_override_aktif_flags_yansir(self):
        """Override True verilen flag aktif_flags listesine girer."""
        p = PatientProfile(yas=30, pediyatrik_override=True)
        assert "pediatric" in p.aktif_flags

    def test_override_false_aktif_flags_disinda(self):
        """Override False verilen flag aktif_flags listesine girmez."""
        p = PatientProfile(yas=70, geriyatrik_override=False)
        assert "geriatric" not in p.aktif_flags


class TestLabEsikleriTamligi:
    """LAB_ESIKLERI içindeki her parametrenin gerekli alanları içerdiğini doğrular."""

    def test_her_param_birim_var(self):
        for param, esik in LAB_ESIKLERI.items():
            assert "birim" in esik, f"{param} için 'birim' eksik"

    def test_her_param_en_az_bir_sinir_var(self):
        sinir_anahtarlari = {"normal_ust", "kritik_ust", "kritik_alt", "kritik_kat"}
        for param, esik in LAB_ESIKLERI.items():
            assert bool(sinir_anahtarlari & esik.keys()), (
                f"{param} için sınır anahtarı bulunamadı"
            )
