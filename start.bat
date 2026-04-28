@echo off
setlocal enabledelayedexpansion
color 0A
title PharmAssist

echo.
echo ===================================================
echo   PharmAssist - Klinik Karar Destek Sistemi
echo ===================================================
echo.
cd /d "%~dp0"

:: ── 1. VENV ──────────────────────────────────────────
echo [1/4] Python venv...
if not exist ".venv\Scripts\python.exe" (
    echo [HATA] .venv bulunamadi. Cozum: python -m venv .venv ^&^& pip install -r requirements.txt
    pause & exit /b 1
)
echo [OK] venv bulundu
echo.

:: ── 2. PORT TEMİZLİĞİ (zorla) ────────────────────────
echo [2/5] Portlar temizleniyor (8080 + 8501)...
for %%P in (8080 8501) do (
    for /f "tokens=5" %%A in ('netstat -ano 2^>nul ^| findstr /R ":%P  " 2^>nul') do (
        if not "%%A"=="0" taskkill /PID %%A /F >nul 2>&1
    )
)
:: Kısa bekleme — OS port serbest bırakma süresi
timeout /t 2 /nobreak >nul
echo [OK] Portlar temizlendi
echo.

:: ── 3. NEO4J ─────────────────────────────────────────
echo [3/5] Neo4j (bolt:7687) kontrol ediliyor...
powershell -Command "try{$t=New-Object Net.Sockets.TcpClient;$t.Connect('localhost',7687);$t.Close();exit 0}catch{exit 1}" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Neo4j calisiyor
) else (
    echo [UYARI] Neo4j bulunamadi ^(7687^). Lutfen Neo4j Desktop veya Docker ile manuel baslatin.
    echo          Graf sorgulari cevapsiz kalir, diger servisler calismaya devam eder.
)
echo.

:: ── 4. CHROMADB ───────────────────────────────────────
echo [4/5] ChromaDB (PersistentClient) kontrol ediliyor...
:: ChromaDB bu projede HTTP servis degil, PersistentClient kullanir (chroma_db/ klasoru).
:: Servis acmaya gerek yok — veri varligi kontrol edilir.
if exist "%~dp0chroma_db\chroma.sqlite3" (
    echo [OK] ChromaDB verisi mevcut: chroma_db\chroma.sqlite3
) else (
    echo [UYARI] chroma_db\chroma.sqlite3 bulunamadi.
    echo          Veri eksik olabilir. Rebuild icin: python scripts/rebuild_chromadb.py
)
echo.

:: ── 5. SERVİSLER ─────────────────────────────────────
echo [5/5] Servisler baslatiliyor...
echo.

set PYTHONPATH=%~dp0

echo === FastAPI (port 8080) ===
start "PharmAssist-API" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe -m uvicorn src.api.main:app --port 8080 --reload"
timeout /t 10 /nobreak >nul

echo === Streamlit UI (port 8501) ===
start "PharmAssist-UI" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe -m streamlit run app.py --server.port 8501"
timeout /t 3 /nobreak >nul

echo.
echo ===================================================
echo   HAZIR
echo ===================================================
echo.
echo   UI      : http://localhost:8501
echo   API     : http://localhost:8080
echo   API Docs: http://localhost:8080/docs
echo   Neo4j   : http://localhost:7474
echo   ChromaDB: PersistentClient (chroma_db/ klasoru, servis gerekmez)
pause
endlocal
