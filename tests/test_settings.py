"""
Settings modülü testleri.
"""

import pytest
from src.config.settings import Settings


class TestSettings:
    def test_default_provider(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
        monkeypatch.delenv("APP_ENV", raising=False)
        s = Settings(_env_file=None)
        assert s.llm_provider == "claude"

    def test_auth_disabled_when_no_key(self, monkeypatch):
        monkeypatch.delenv("PHARMASSIST_API_KEY", raising=False)
        s = Settings(_env_file=None)
        assert s.auth_enabled is False

    def test_auth_enabled_when_key_set(self, monkeypatch):
        monkeypatch.setenv("PHARMASSIST_API_KEY", "supersecret")
        s = Settings(_env_file=None)
        assert s.auth_enabled is True

    def test_invalid_anthropic_key_format(self, monkeypatch):
        from pydantic import ValidationError
        monkeypatch.setenv("ANTHROPIC_API_KEY", "invalid-key-format")
        with pytest.raises(ValidationError):
            Settings(_env_file=None)

    def test_empty_anthropic_key_treated_as_none(self, monkeypatch):
        # .env.example'daki boş `ANTHROPIC_API_KEY=` satırı veya CI'daki boş env
        # crash'e yol açmamalı — boş string tanımsız sayılır.
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        s = Settings(_env_file=None)
        assert s.anthropic_api_key is None

    def test_invalid_neo4j_url(self, monkeypatch):
        from pydantic import ValidationError
        monkeypatch.setenv("NEO4J_URL", "http://localhost:7687")
        with pytest.raises(ValidationError):
            Settings(_env_file=None)

    def test_valid_neo4j_url_neo4j_scheme(self, monkeypatch):
        monkeypatch.setenv("NEO4J_URL", "neo4j://localhost:7687")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        s = Settings(_env_file=None)
        assert s.neo4j_url.startswith("neo4j://")

    def test_production_flag(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "production")
        s = Settings(_env_file=None)
        assert s.is_production is True

    def test_development_not_production(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "development")
        s = Settings(_env_file=None)
        assert s.is_production is False
