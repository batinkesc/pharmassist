@echo off
setlocal enabledelayedexpansion
color 0A
title PharmAssist Ultimate Starter (Local)

echo ===================================================
echo   PharmAssist - Akilli Yerel Baslatici (V1.2)
echo ===================================================

cd /d "%~dp0"

:: 1. Port Temizliği
echo [1/4] Portlar temizleniyor (8080, 8081, 8501)...
for %%P in (8080 8081 8501) do (
    for /f "tokens=5" %%A in ('netstat -ano 2^>nul ^| findstr ":%%P "') do (
        echo [!] %%P portunda calisan %%A PIDsli surec sonlandiriliyor...
        taskkill /PID %%A /F >nul 2>&1
    )
)
echo [OK] Portlar Temizlendi.

:: 2. Neo4j Kontrolü ve Başlatma
echo [2/4] Neo4j (7687) kontrol ediliyor...
netstat -ano | findstr ":7687" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Neo4j calismiyor! Servis olarak baslatilmaya calisiliyor...
    net start neo4j >nul 2>&1
    timeout /t 5 /nobreak >nul
    netstat -ano | findstr ":7687" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [UYARI] Neo4j otomatik baslatilamadi. Lutfen Neo4j Desktop'i manuel acin.
    ) else (
        echo [OK] Neo4j Baslatildi.
    )
) else (
    echo [OK] Neo4j zaten calisiyor.
)

:: 3. Venv Kontrolü
echo [3/4] Python venv kontrol ediliyor...
if not exist ".venv\Scripts\python.exe" (
    echo [HATA] .venv klasoru bulunamadi!
    pause
    exit /b 1
)

:: 4. Servisleri Başlatma
echo [4/4] Servisler baslatiliyor...

echo.
echo === FastAPI API (8080) Baslatiliyor ===
set PYTHONPATH=.
start "PharmAssist-API" cmd /c ".venv\Scripts\python.exe -m uvicorn src.api.main:app --port 8080 & pause"

echo Bekleniyor (10sn)...
timeout /t 10 /nobreak >nul

echo === Streamlit UI (8501) Baslatiliyor ===
start "PharmAssist-UI" cmd /c ".venv\Scripts\python.exe -m streamlit run app.py --server.port 8501 --server.headless true & pause"

echo.
echo ===================================================
echo   SISTEM HAZIR!
echo ===================================================
echo   API: http://localhost:8080/docs
echo   UI : http://localhost:8501
echo.
echo Pencereleri kapatmayin. Islem bittiginde Ctrl+C ile durdurabilirsiniz.
pause
