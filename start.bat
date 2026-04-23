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
echo [2/4] Portlar temizleniyor (8080 + 8501)...
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
echo [3/4] Neo4j (bolt:7687) kontrol ediliyor...

:: Zaten ayakta mı?
powershell -Command "try{$t=New-Object Net.Sockets.TcpClient;$t.Connect('localhost',7687);$t.Close();exit 0}catch{exit 1}" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Neo4j zaten calisiyor
    goto :neo4j_done
)

:: Docker kontrolü
docker info >nul 2>&1
if errorlevel 1 (
    echo [HATA] Docker Desktop calısmiyor! Baslatin ve tekrar deneyin.
    pause & exit /b 1
)

:: Neo4j container başlat (varsa çalıştır, yoksa oluştur)
echo [INFO] Neo4j baslatiliyor (docker-compose)...
docker-compose up -d neo4j >nul 2>&1

:: Hazır olana dek bekle (max 60 sn)
echo [INFO] Neo4j baslamasi bekleniyor...
set /a DENEME=0
:neo4j_bekle
set /a DENEME+=1
if !DENEME! gtr 12 (
    echo [UYARI] Neo4j 60sn icinde yanit vermedi, devam ediliyor...
    goto :neo4j_done
)
powershell -Command "try{$t=New-Object Net.Sockets.TcpClient;$t.Connect('localhost',7687);$t.Close();exit 0}catch{exit 1}" >nul 2>&1
if errorlevel 1 (
    timeout /t 5 /nobreak >nul
    goto :neo4j_bekle
)
echo [OK] Neo4j hazir

:neo4j_done
echo.

:: ── 4. SERVİSLER ─────────────────────────────────────
echo [4/4] Servisler baslatiliyor...
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
echo.
pause
endlocal
