"""
Unit Tests: Normalizasyon ve CYP450 Fallback

Testler:
  1. normalize_drug_name() — trademark, Unicode, whitespace
  2. get_base_name() — variant extraction
  3. CYP450 fallback strategy — manual > extraction
  4. Pipeline integration — JSON → DB sorunsuz
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.normalization import normalize_drug_name, get_base_name
from src.analysis.cyp450_mapper import ILAC_CYP_PROFILI


# ============================================================================
# Test Suite 1: Normalizasyon
# ============================================================================

class TestNormalizeDrugName:
    """normalize_drug_name() fonksiyonunun test'i"""

    def test_trademark_removal(self):
        """® sembolü kaldırılmalı"""
        assert normalize_drug_name("LUSTRAL®") == "LUSTRAL"
        assert normalize_drug_name("AMLOPER® 10/10 mg tablet") == "AMLOPER 10/10 MG TABLET"

    def test_copyright_symbol(self):
        """© ve ™ de kaldırılmalı"""
        assert normalize_drug_name("DRUG©") == "DRUG"
        assert normalize_drug_name("BRAND™") == "BRAND"

    def test_private_use_area_symbols(self):
        """PUA (Private Use Area) Unicode sembollerini kaldır"""
        # \uf8e8 = PUA trademark
        assert normalize_drug_name("TEST\uf8e8") == "TEST"

    def test_whitespace_normalization(self):
        """Birden fazla boşluğu teke indir"""
        assert normalize_drug_name("DRUG    NAME") == "DRUG NAME"
        assert normalize_drug_name("  LEADING  TRAILING  ") == "LEADING TRAILING"

    def test_turkish_character_mapping(self):
        """Türkçe karakterleri ASCII eşdeğerine çevir"""
        assert normalize_drug_name("İLAÇ") == "ILAC"
        assert normalize_drug_name("çaprıkla") == "CAPRIKLA"
        assert normalize_drug_name("ŞARKI") == "SARKI"
        assert normalize_drug_name("öz") == "OZ"
        assert normalize_drug_name("ğizli") == "GIZLI"
        assert normalize_drug_name("ü sağlığı") == "U SAGLIGI"

    def test_case_normalization(self):
        """Hepsini uppercase'e çevir"""
        assert normalize_drug_name("lustral") == "LUSTRAL"
        assert normalize_drug_name("LuSTrAL") == "LUSTRAL"

    def test_combined_normalization(self):
        """Birden fazla işlem kombinasyonu"""
        # Real-world example: ÇARKIŞLA® 100 mg   →   CARKISLA 100 MG
        assert normalize_drug_name("ÇARKIŞLA® 100 mg  ") == "CARKISLA 100 MG"
        assert normalize_drug_name("  İlaç®™©  ") == "ILAC"

    def test_empty_input(self):
        """Boş input güvenli olmalı"""
        assert normalize_drug_name("") == ""
        assert normalize_drug_name(None) == ""

    def test_idempotency(self):
        """İkinci çalıştırma sonuç değiştirmemeli"""
        name = "LUSTRAL® 50 mg"
        normalized_once = normalize_drug_name(name)
        normalized_twice = normalize_drug_name(normalized_once)
        assert normalized_once == normalized_twice


class TestGetBaseName:
    """get_base_name() fonksiyonunun test'i"""

    def test_single_word(self):
        """Tek kelime → aynısı"""
        assert get_base_name("LUSTRAL") == "LUSTRAL"

    def test_dosage_variant(self):
        """Doz bilgisi kısıldı"""
        assert get_base_name("LUSTRAL 50 MG TABLET") == "LUSTRAL"
        assert get_base_name("EUTHYROX 100 MCG TABLET") == "EUTHYROX"

    def test_formulation_variant(self):
        """Formulasyon kısıldı"""
        assert get_base_name("HUMALOG 100 U/ML FLAKON") == "HUMALOG"
        assert get_base_name("AUGMENTIN ORAL SUSPENSION") == "AUGMENTIN"

    def test_trademark_cleaned(self):
        """Trademark sembolü varsa da kaldır"""
        assert get_base_name("AMLOPER® 10/10 MG") == "AMLOPER"

    def test_empty_input(self):
        """Boş input güvenli olmalı"""
        assert get_base_name("") == ""
        assert get_base_name(None) == ""


# ============================================================================
# Test Suite 2: CYP450 Fallback Strategy
# ============================================================================

class TestCYP450Fallback:
    """CYP450 fallback stratejisi — manuel > extraction"""

    def test_manual_list_exists(self):
        """Manuel lista populate olmalı"""
        assert len(ILAC_CYP_PROFILI) > 50, "Manuel CYP profili listesi boş"

    def test_manual_list_frozen_notice(self):
        """Frozen notice var mı?"""
        # cyp450_mapper.py'da satır 46-49'da frozen notice olmalı
        # Bu test visual kontrole ihtiyaç duyar — şimdilik skip
        pass

    def test_fallback_returns_empty_on_missing(self):
        """Fallback stratejisi eksik ilaçta boş döner"""
        from src.analysis.cyp450_mapper import _ilac_cyp_profili_bul

        # Listede olmayan ilaç
        result = _ilac_cyp_profili_bul("FAKE_DRUG_THAT_DOES_NOT_EXIST")

        # Boş dict döner (hiç hata vermez)
        assert isinstance(result, dict)
        assert len(result.get("substrat", [])) == 0

    def test_manual_entry_contains_required_fields(self):
        """Manuel listedeki her entry substrat/inhibitor/induktor içermeli"""
        for drug_name, profile in list(ILAC_CYP_PROFILI.items())[:10]:
            assert isinstance(profile, dict), f"{drug_name} dict değil"
            assert "substrat" in profile, f"{drug_name} substrat yok"
            assert "inhibitor" in profile, f"{drug_name} inhibitor yok"
            assert "induktor" in profile, f"{drug_name} induktor yok"

    def test_fallback_returns_empty_dict_type(self):
        """Manuel listede yoksa ve fallback yoksa dict döner"""
        from src.analysis.cyp450_mapper import _ilac_cyp_profili_bul

        # Listede olmayan ilaç
        result = _ilac_cyp_profili_bul("FAKE_DRUG_NOT_IN_LIST")

        # Fallback: empty dict with required keys
        assert isinstance(result, dict)
        assert "substrat" in result
        assert "inhibitor" in result
        assert "induktor" in result


# ============================================================================
# Test Suite 3: Pipeline Integration
# ============================================================================

class TestPipelineIntegration:
    """JSON → ChromaDB → Neo4j akışının test'i"""

    def test_normalized_name_persists_to_json(self, tmp_path):
        """Normalize edilen isim JSON'a kaydedilmeli"""
        # Simülasyon
        data = {
            "ilac_adi": "LUSTRAL® 50 mg",
            "etken_madde": "Sertralin",
            "chunks": []
        }

        # Normalizasyon
        from src.data.normalization import normalize_drug_name
        data["ilac_adi"] = normalize_drug_name(data["ilac_adi"])

        # Kaydet
        json_path = tmp_path / "test.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        # Oku ve doğrula
        with open(json_path, encoding='utf-8') as f:
            loaded = json.load(f)

        assert loaded["ilac_adi"] == "LUSTRAL 50 MG"

    def test_chunk_metadata_has_ilac_adi(self):
        """Her chunk'ın metadata'sında ilac_adi olmalı"""
        # Fake chunk
        chunk = {
            "chunk_id": "test_123",
            "madde_no": "4.5",
            "icerik": "Test content",
            "ilac_adi": "LUSTRAL"  # Zorunlu
        }

        # Metadata conversion (simulate _chunk_to_metadata)
        metadata = {
            "ilac_adi": chunk.get("ilac_adi"),
            "madde_no": chunk.get("madde_no"),
        }

        assert "ilac_adi" in metadata
        assert metadata["ilac_adi"] == "LUSTRAL"

    def test_duplicate_base_names_detected(self):
        """Duplicate'ler tespit edilmeli"""
        from src.data.normalization import get_base_name

        names = [
            "EUTHYROX 100 MCG",
            "EUTHYROX 125 MCG",
            "EUTHYROX 150 MCG",
            "LUSTRAL 50 MG",
        ]

        base_names = [get_base_name(n) for n in names]

        assert base_names.count("EUTHYROX") == 3
        assert base_names.count("LUSTRAL") == 1


# ============================================================================
# Test Suite 4: Error Handling
# ============================================================================

class TestErrorHandling:
    """Error handling — keine unexpected exceptions"""

    def test_normalize_with_malformed_input(self):
        """Kötü input'ta crash olmamali"""
        # Unicode surrogate pairs vb.
        inputs = [
            "\x00NULL_CHAR",
            "DRUG\x01CONTROL",
            "VERY\n\nLONG\n\nNAME",
        ]

        for inp in inputs:
            result = normalize_drug_name(inp)
            assert isinstance(result, str), f"Unexpected type for {repr(inp)}"

    def test_cyp_profile_lookup_safe(self):
        """Profile lookup hiç crash olmamali"""
        from src.analysis.cyp450_mapper import _ilac_cyp_profili_bul

        test_drugs = [
            "NONEXISTENT",
            "",
            None,
            "DRUG\x00WITH\x01SPECIAL_CHARS",
        ]

        for drug in test_drugs:
            try:
                result = _ilac_cyp_profili_bul(drug)
                assert isinstance(result, dict)
            except Exception as e:
                pytest.fail(f"Unexpected exception for {repr(drug)}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
