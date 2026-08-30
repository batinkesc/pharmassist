"""
PharmAssist uygulama ayarları — startup'ta env var doğrulaması yapar.

Kullanım:
    from src.config.settings import settings
    print(settings.anthropic_api_key)
"""

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------
    llm_provider: Literal["claude", "local"] = "claude"
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    lm_studio_url: str = "http://localhost:1234/v1"
    local_model_name: str = "meta-llama-3.1-8b-instruct"

    # ------------------------------------------------------------------
    # Veritabanları
    # ------------------------------------------------------------------
    neo4j_url: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: Optional[str] = Field(None, alias="NEO4J_PASSWORD")

    chroma_collection_name: str = "kub_chunks"

    # ------------------------------------------------------------------
    # Uygulama
    # ------------------------------------------------------------------
    app_env: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"

    # Opsiyonel API anahtarı — ayarlanırsa /query X-API-Key header gerektirir.
    # Boş bırakılırsa endpoint authentication olmadan açık kalır.
    pharmassist_api_key: Optional[str] = Field(None, alias="PHARMASSIST_API_KEY")

    # CORS — production'da kısıtlanmalı: ALLOWED_ORIGINS=https://app.example.com
    allowed_origins: list[str] = Field(
        default=["*"],
        alias="ALLOWED_ORIGINS",
        description="Virgülle ayrılmış origin listesi veya ['*']",
    )

    # ------------------------------------------------------------------
    # Validasyonlar
    # ------------------------------------------------------------------

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: Optional[str], info) -> Optional[str]:
        # Sadece llm_provider=claude ise zorunlu — provider değerini values'dan okuyamayız
        # çünkü henüz validate edilmemiş olabilir; runtime'da main.py'den kontrol edilir.
        if v is not None and not v.startswith("sk-ant-"):
            raise ValueError("ANTHROPIC_API_KEY geçersiz format (sk-ant- ile başlamalı)")
        return v

    @field_validator("neo4j_url")
    @classmethod
    def validate_neo4j_url(cls, v: str) -> str:
        if not (v.startswith("bolt://") or v.startswith("neo4j://")):
            raise ValueError("NEO4J_URL bolt:// veya neo4j:// ile başlamalı")
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def auth_enabled(self) -> bool:
        return bool(self.pharmassist_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Modül-seviyesi singleton — `from src.config.settings import settings` ile kullanılır
settings = get_settings()
