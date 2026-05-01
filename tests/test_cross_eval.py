"""
Cross-Evaluator Agreement (Task 3) için birim testleri.

Kapsam:
  - _get_llm("model_b") provider plumbing (env var → ChatOpenAI)
  - build_records: Run 20 JSON formatından eval_records dönüşümü
  - compute_stats: Pearson r + mean abs delta + NaN sayım
  - high_disagreement detection: NaN-vs-valid ve |Δ| > 0.25 vakaları
"""

import math
import pytest
from langchain_openai import ChatOpenAI
from src.evaluation.ragas_eval import _get_llm
from scripts.cross_eval_agreement import build_records, compute_stats


# ---------------------------------------------------------------------------
# _get_llm provider plumbing
# ---------------------------------------------------------------------------

def test_get_llm_model_b_uses_env_var(monkeypatch):
    """RAGAS_MODEL_2 env değişkeni ChatOpenAI model'ine doğru geçiyor mu?"""
    monkeypatch.setenv("RAGAS_MODEL_2", "openai/gpt-oss-120b")
    monkeypatch.setenv("TOGETHER_API_KEY", "test_key")
    monkeypatch.setenv("LM_STUDIO_URL", "https://test.url/v1")

    llm = _get_llm("model_b")

    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "openai/gpt-oss-120b"
    assert "test.url" in str(llm.openai_api_base)


def test_get_llm_model_b_default_when_env_missing(monkeypatch):
    """RAGAS_MODEL_2 yoksa default DeepSeek modeline düşer."""
    monkeypatch.delenv("RAGAS_MODEL_2", raising=False)
    monkeypatch.setenv("TOGETHER_API_KEY", "test_key")

    llm = _get_llm("model_b")
    assert llm.model_name == "deepseek-ai/DeepSeek-V3-1"


# ---------------------------------------------------------------------------
# build_records: Run 20 JSON → RAGAS records
# ---------------------------------------------------------------------------

def test_build_records_extracts_required_fields():
    """Run 20 per_question'dan question/answer/contexts/ground_truth çıkarır."""
    fake_run20 = {
        "per_question": [
            {
                "question": "Soru 1",
                "ragas_answer": "RAGAS-temizlenmiş cevap",
                "answer": "Ham cevap",
                "contexts": ["ctx 1", "ctx 2"],
                "ground_truth": "GT 1",
                "extra_field": "ignored",
            }
        ]
    }
    records = build_records(fake_run20)
    assert len(records) == 1
    r = records[0]
    assert r["question"] == "Soru 1"
    # ragas_answer öncelikli (RAGAS evaluator için temizlenmiş versiyon)
    assert r["answer"] == "RAGAS-temizlenmiş cevap"
    assert r["contexts"] == ["ctx 1", "ctx 2"]
    assert r["ground_truth"] == "GT 1"


def test_build_records_falls_back_to_answer():
    """ragas_answer yoksa answer'a düşer."""
    fake_run20 = {
        "per_question": [
            {"question": "Q", "answer": "fallback", "contexts": [], "ground_truth": ""}
        ]
    }
    records = build_records(fake_run20)
    assert records[0]["answer"] == "fallback"


def test_build_records_empty():
    """per_question boşsa boş liste döner."""
    assert build_records({"per_question": []}) == []
    assert build_records({}) == []


# ---------------------------------------------------------------------------
# compute_stats: Pearson r + mean abs delta + NaN sayım
# ---------------------------------------------------------------------------

def test_compute_stats_perfect_correlation():
    """Aynı skorlar → r=1.0, delta=0."""
    a = [0.5, 0.7, 0.9, 1.0]
    b = [0.5, 0.7, 0.9, 1.0]
    s = compute_stats(a, b)
    assert s["pearson_r"] == 1.0
    assert s["mean_abs_delta"] == 0.0
    assert s["n_nan_a"] == 0
    assert s["n_nan_b"] == 0


def test_compute_stats_nan_handling():
    """NaN'lar valid çiftlerden hariç tutuluyor; ayrı sayılıyor."""
    a = [0.5, float("nan"), 0.9, 1.0]
    b = [0.4, 0.6, float("nan"), 0.9]
    s = compute_stats(a, b)
    # Sadece (0.5, 0.4) ve (1.0, 0.9) valid pair
    assert s["n_nan_a"] == 1
    assert s["n_nan_b"] == 1
    assert s["mean_abs_delta"] is not None
    # Manuel: |0.5-0.4|=0.1, |1.0-0.9|=0.1 → mean=0.1
    assert abs(s["mean_abs_delta"] - 0.1) < 0.001


def test_compute_stats_too_few_valid_pairs():
    """1 veya 0 valid çift → pearson_r None."""
    a = [0.5, float("nan"), float("nan")]
    b = [0.5, 0.7, 0.9]
    s = compute_stats(a, b)
    assert s["pearson_r"] is None
    assert s["mean_abs_delta"] is None
    assert s["n_nan_a"] == 2
    assert s["n_nan_b"] == 0


def test_compute_stats_negative_correlation():
    """Ters orantılı skorlar → negatif r."""
    a = [0.1, 0.3, 0.7, 0.9]
    b = [0.9, 0.7, 0.3, 0.1]
    s = compute_stats(a, b)
    assert s["pearson_r"] < -0.95


# ---------------------------------------------------------------------------
# Cross-eval output JSON sanity (eğer dosya varsa)
# ---------------------------------------------------------------------------

def test_cross_eval_output_no_legacy_fix_report():
    """fix_report.py post-hoc patch script'i artık repo'da olmamalı."""
    from pathlib import Path
    assert not Path("scripts/fix_report.py").exists(), (
        "scripts/fix_report.py one-off patch script'i; ana script bug'ı düzeltildi"
    )


def test_cross_eval_output_high_disagreement_includes_nan():
    """
    Mevcut output'ta NaN-vs-valid vakaları high_disagreement listesinde olmalı.
    (Bug fix doğrulama: önce filtreleniyordu, şimdi flag'leniyor.)
    """
    import json
    from pathlib import Path

    out = Path("data/eval/cross_eval_agreement.json")
    if not out.exists():
        pytest.skip("Cross-eval output yok — script henüz koşulmamış")

    data = json.loads(out.read_text(encoding="utf-8"))
    hd = data.get("high_disagreement", [])

    # Faithfulness'ta NaN_A varsa, en az 1 tanesi high_disagreement'ta görünmeli
    fa_nan = data.get("per_metric", {}).get("faithfulness", {}).get("n_nan_a", 0)
    if fa_nan > 0:
        nan_failures = [h for h in hd if h.get("delta") and "NaN" in str(h["delta"])]
        assert len(nan_failures) > 0, (
            "Faithfulness'ta NaN_A var ama high_disagreement'ta hiç NaN flag yok"
        )
