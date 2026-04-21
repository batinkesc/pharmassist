"""
Pytest sabit ayarları ve ortak fixture'lar.
"""

import os
import sys

import pytest

# Proje kökünü sys.path'e ekle (pytest'in src import etmesi için)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def hasta_dict():
    """Temel hasta profili dict'i."""
    return {
        "yas": 68,
        "cinsiyet": "erkek",
        "gfr": 38.0,
        "karaciger_skoru": None,
        "mevcut_ilaclar": ["Metformin 1000 mg", "Ramipril 10 mg"],
        "alerjiler": ["penisilin"],
        "endikasyonlar": ["Tip 2 Diyabet", "Hipertansiyon"],
        "gebelik": False,
        "emzirme": False,
        "lab_degerleri": {"ALT": 120, "K": 5.6, "HbA1c": 8.2},
        "notlar": "",
    }


@pytest.fixture
def query_payload(hasta_dict):
    """Geçerli /query POST gövdesi."""
    return {
        "soru": "Bu hastaya ibuprofen verebilir miyiz?",
        "hasta": hasta_dict,
        "hedef_ilaclar": None,
        "n_results": 3,
    }
