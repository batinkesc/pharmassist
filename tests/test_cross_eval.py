import os
import pytest
from langchain_openai import ChatOpenAI
from src.evaluation.ragas_eval import _get_llm

def test_get_llm_model_b_correct_model(monkeypatch):
    monkeypatch.setenv("RAGAS_MODEL_2", "deepseek-ai/DeepSeek-V3-1")
    monkeypatch.setenv("TOGETHER_API_KEY", "test_key")
    monkeypatch.setenv("LM_STUDIO_URL", "https://test.url/v1")
    
    llm = _get_llm("model_b")
    
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "deepseek-ai/DeepSeek-V3-1"
    assert "test.url" in str(llm.openai_api_base)
