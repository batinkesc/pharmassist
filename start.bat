@echo off
setlocal enabledelayedexpansion

color 0A
title PharmAssist System

echo.
echo ===================================================
echo   PharmAssist - Klinik Karar Destek Sistemi
echo ===================================================
echo.

cd /d "%~dp0"

REM ========== CHECK 1: VENV ==========
echo [1/5] Python venv kontrol ediliyor...
if not exist ".venv\Scripts\python.exe" (
    echo [HATA] .venv bulunamadi
    echo Cozum: python -m venv .venv ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] Python venv: BULUNDU
echo.

REM ========== CHECK 2: ENV ==========
echo [2/5] .env kontrol ediliyor...
if not exist ".env" (
    echo [UYARI] .env bulunamadi (ANTHROPIC_API_KEY eksik olabilir)
) else (
    echo [OK] .env: BULUNDU
)
echo.

REM ========== CHECK 3: PORT CLEANUP ==========
echo [3/5] Portlar temizleniyor...
for /f "tokens=5" %%A in ('netstat -ano 2^>nul ^| findstr ":8080 "'') do taskkill /PID %%A /F 2>nul
for /f "tokens=5" %%A in ('netstat -ano 2^>nul ^| findstr ":8501 "'') do taskkill /PID %%A /F 2>nul
echo [OK] Portlar temizlendi
echo.

REM ========== CHECK 4: CHROMADB ==========
echo [4/5] ChromaDB kontrol ediliyor...
if exist "chroma_db\" (
    echo [OK] ChromaDB: BULUNDU
) else (
    echo [UYARI] ChromaDB: YOK (ilk calisma)
)
echo.

REM ========== CHECK 5: NEO4J DOCKER ==========
echo [5/5] Neo4j kontrol ediliyor...
docker ps 2>nul | findstr "pharmassist-neo4j" >nul
if errorlevel 1 (
    echo [INFO] Neo4j baslaniyor (docker-compose)...
    docker-compose up -d neo4j
    timeout /t 15 /nobreak
    echo [OK] Neo4j baslatildi
) else (
    echo [OK] Neo4j: ZATEN CALISIYYOR
)
echo.

REM ========== STARTUP ==========
echo [6/5] Servisler baslatiliyor...
echo.

echo === FastAPI Baslatiliyor (port 8080) ===
start "PharmAssist-API" cmd /k ".venv\Scripts\python -m uvicorn src.api.main:app --port 8080 --reload"
timeout /t 12 /nobreak

echo.
echo === Streamlit Baslatiliyor (port 8501) ===
start "PharmAssist-UI" cmd /k ".venv\Scripts\python -m streamlit run app.py --server.port 8501 --server.headless true"
timeout /t 10 /nobreak

echo.
echo ===================================================
echo   SISTEM BASLATILDI
echo ===================================================
echo.
echo   FastAPI  : http://localhost:8080
echo   Docs     : http://localhost:8080/docs
echo   Streamlit: http://localhost:8501
echo.
echo   Pencereler ayri tab'larda acildi
echo   Kapatmak: Ctrl+C yap ya da taskkill /IM python.exe /F
echo.
pause

endlocal
