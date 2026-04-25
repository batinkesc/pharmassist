"""
PharmAssist FastAPI uygulaması.

Başlatmak için:
    .venv/Scripts/uvicorn src.api.main:app --reload --port 8080

Swagger UI:
    http://localhost:8080/docs
"""

import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.api.routes import router
from src.config.settings import settings

load_dotenv(override=True)

# Loguru stdout encoding
logger.remove()
logger.add(
    sys.stdout,
    format="{time:HH:mm:ss} | {level:<8} | {message}",
    level="INFO",
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Uygulama başlangıç / bitiş olayları."""
    logger.info("PharmAssist API basliyor...")
    # Env var doğrulaması
    if settings.llm_provider == "claude" and not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY ayarlanmamış! .env dosyasını kontrol edin. "
            "API başlatılamadı."
        )
    if not settings.postgres_password:
        logger.warning("POSTGRES_PASSWORD ayarlanmamış — .env dosyasını kontrol edin.")
    if not settings.neo4j_password:
        logger.warning("NEO4J_PASSWORD ayarlanmamış — .env dosyasını kontrol edin.")
    if settings.auth_enabled:
        logger.info("API key authentication aktif (X-API-Key header gerekli).")
    else:
        logger.warning("API key authentication devre dışı — üretim ortamında PHARMASSIST_API_KEY ayarlayın.")
    # Embedding modelini önceden yükle (ilk istek yavaş olmasın)
    from src.processing.embedder import get_model
    get_model()
    logger.info("Embedding modeli hazir.")
    yield
    logger.info("PharmAssist API kapaniyor.")


app = FastAPI(
    title="PharmAssist API",
    description=(
        "KÜB (Kısa Ürün Bilgisi) belgelerine dayalı Klinik Karar Destek Sistemi.\n\n"
        "Hasta profiline göre ilaç güvenliği, etkileşim ve doz analizi yapar."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
