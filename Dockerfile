# ── Build aşaması ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

# Sistem bağımlılıkları (PyMuPDF, Camelot, psycopg2 için)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını önce kopyala (Docker layer cache için)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY src/ ./src/
COPY app.py .
COPY configs/ ./configs/
COPY data/parsed_json/ ./data/parsed_json/

# ChromaDB kalıcı depolama için klasör
RUN mkdir -p chroma_db logs

# ── FastAPI servisi ────────────────────────────────────────────────────────────
FROM base AS api

EXPOSE 8080

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]

# ── Streamlit UI servisi ───────────────────────────────────────────────────────
FROM base AS ui

EXPOSE 8501

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
