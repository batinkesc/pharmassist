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
echo [1/6] Python venv kontrol ediliyor...
if not exist ".venv\Scripts\python.exe" (
    echo [HATA] .venv bulunamadi
    echo Cozum: python -m venv .venv ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] Python venv: BULUNDU
echo.

REM ========== CHECK 2: ENV ==========
echo [2/6] .env kontrol ediliyor...
if not exist ".env" (
    echo [UYARI] .env bulunamadi ^(ANTHROPIC_API_KEY eksik olabilir^)
) else (
    echo [OK] .env: BULUNDU
)
echo.

REM ========== CHECK 3: DOCKER ==========
echo [3/6] Docker kontrol ediliyor...
docker info >nul 2>&1
if errorlevel 1 (
    echo [HATA] Docker Desktop calismıyor!
    echo Cozum: Docker Desktop'i ac ve tekrar dene.
    pause
    exit /b 1
)
echo [OK] Docker: CALISIYOR
echo.

REM ========== CHECK 4: PORT CLEANUP ==========
echo [4/6] Portlar temizleniyor...
for /f "tokens=5" %%A in ('netstat -ano 2^>nul ^| findstr ":8080 "') do taskkill /PID %%A /F >nul 2>&1
for /f "tokens=5" %%A in ('netstat -ano 2^>nul ^| findstr ":8501 "') do taskkill /PID %%A /F >nul 2>&1
echo [OK] Portlar temizlendi
echo.

REM ========== CHECK 5: NEO4J ==========
echo [5/6] Neo4j kontrol ediliyor...
docker ps 2>nul | findstr "pharmassist-neo4j" >nul
if errorlevel 1 (
    echo [INFO] Neo4j container bulunamadi, baslatiliyor...
    docker-compose up -d neo4j
    if errorlevel 1 (
        echo [HATA] Neo4j baslatılamadı. docker-compose.yml kontrol edin.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Neo4j container mevcut.
)

REM Neo4j bolt portunu bekle (max 60 saniye)
echo [INFO] Neo4j bolt portu bekleniyor (7687)...
set NEO4J_READY=0
for /l %%i in (1,1,12) do (
    if !NEO4J_READY!==0 (
        powershell -Command "try { $t = New-Object Net.Sockets.TcpClient; $t.Connect('localhost', 7687); $t.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
        if not errorlevel 1 (
            set NEO4J_READY=1
            echo [OK] Neo4j: HAZIR ^(bolt://localhost:7687^)
        ) else (
            timeout /t 5 /nobreak >nul
        )
    )
)
if !NEO4J_READY!==0 (
    echo [UYARI] Neo4j 60 saniyede yanit vermedi, devam ediliyor...
)
echo.

REM ========== CHECK 6: CHROMADB ==========
echo [6/6] ChromaDB kontrol ediliyor...
if exist "chroma_db\" (
    echo [OK] ChromaDB: BULUNDU
) else (
    echo [UYARI] ChromaDB klasoru yok ^(ilk calisma - otomatik olusturulacak^)
)
echo.

REM ========== STARTUP ==========
echo Servisler baslatiliyor...
echo.

echo === FastAPI Baslatiliyor (port 8080) ===
start "PharmAssist-API" cmd /k ".venv\Scripts\python.exe -m uvicorn src.api.main:app --port 8080 --reload"
timeout /t 12 /nobreak >nul

echo.
echo === Streamlit Baslatiliyor (port 8501) ===
start "PharmAssist-UI" cmd /k ".venv\Scripts\python.exe -m streamlit run app.py --server.port 8501 --server.headless true"
timeout /t 5 /nobreak >nul

echo.
echo ===================================================
echo   SISTEM BASLATILDI
echo ===================================================
echo.
echo   FastAPI  : http://localhost:8080
echo   API Docs : http://localhost:8080/docs
echo   Streamlit: http://localhost:8501
echo   Neo4j UI : http://localhost:7474
echo.
echo   Kapatmak icin: taskkill /IM python.exe /F
echo.
pause

endlocal
