#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PharmAssist System Starter - Python Version
Tüm kontrolleri yapar ve servisları başlatır
"""

import os
import sys
import time
import socket
import subprocess
import platform
import signal
from pathlib import Path

class Colors:
    OK = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    INFO = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    print("\n" + "="*60)
    print(f"{Colors.BOLD}  PharmAssist - Klinik Karar Destek Sistemi{Colors.RESET}")
    print("="*60 + "\n")

def log(msg, level="INFO"):
    """Mesaj yazdır"""
    timestamp = time.strftime("%H:%M:%S")
    if level == "OK":
        print(f"{Colors.OK}[OK {timestamp}]{Colors.RESET} {msg}")
    elif level == "ERROR":
        print(f"{Colors.ERROR}[XX {timestamp}]{Colors.RESET} {msg}")
    elif level == "WARNING":
        print(f"{Colors.WARNING}[!! {timestamp}]{Colors.RESET} {msg}")
    else:
        print(f"{Colors.INFO}[-- {timestamp}]{Colors.RESET} {msg}")

def check_venv():
    """Python venv kontrolü"""
    print(f"\n{Colors.BOLD}[ADIM 1/6] Python venv kontrol ediliyor...{Colors.RESET}")

    venv_python = Path(".venv/Scripts/python.exe") if platform.system() == "Windows" else Path(".venv/bin/python")

    if not venv_python.exists():
        log(f"venv bulunamadı: {venv_python}", "ERROR")
        log("Çözüm: python -m venv .venv && pip install -r requirements.txt", "ERROR")
        return False

    log(f"Python venv: {venv_python.parent.parent}", "OK")
    return True

def check_env():
    """Environment variables (.env) kontrolü"""
    print(f"\n{Colors.BOLD}[ADIM 2/6] Ortam değişkenleri kontrolü...{Colors.RESET}")

    if not Path(".env").exists():
        log(".env dosyası bulunamadı", "WARNING")
        log("ANTHROPIC_API_KEY eksik olabilir", "WARNING")
        return False

    # .env içeriğini kontrol et
    with open(".env", "r") as f:
        env_content = f.read()

    if "ANTHROPIC_API_KEY" not in env_content:
        log(".env'de ANTHROPIC_API_KEY yok", "ERROR")
        return False

    log(".env dosyası: OK", "OK")
    return True

def check_requirements():
    """requirements.txt kontrolü"""
    print(f"\n{Colors.BOLD}[ADIM 3/6] Gerekli paketler kontrolü...{Colors.RESET}")

    if not Path("requirements.txt").exists():
        log("requirements.txt bulunamadı", "WARNING")
        return False

    log("requirements.txt: OK", "OK")
    return True

def check_ports():
    """Port kontrolü ve temizliği"""
    print(f"\n{Colors.BOLD}[ADIM 4/6] Port kontrolleri (8080, 8501)...{Colors.RESET}")

    ports = {
        8080: "FastAPI",
        8501: "Streamlit"
    }

    for port, service in ports.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()

            if result == 0:
                log(f"Port {port} ({service}): ZATENKullanılıyor", "WARNING")
                # Windows: taskkill, Linux: fuser
                if platform.system() == "Windows":
                    os.system(f"taskkill /IM python.exe /FI \"MEMUSAGE gt 10\" /F 2>nul")
                else:
                    os.system(f"fuser -k {port}/tcp 2>/dev/null")
                time.sleep(2)
            else:
                log(f"Port {port} ({service}): Serbest", "OK")
        except Exception as e:
            log(f"Port {port} kontrolü: {e}", "WARNING")

    return True

def check_dependencies():
    """ChromaDB ve Neo4j kontrolü"""
    print(f"\n{Colors.BOLD}[ADIM 5/6] Bağımlılıklar kontrolü...{Colors.RESET}")

    # ChromaDB
    if Path("chroma_db").exists():
        log("ChromaDB dizini: Bulundu", "OK")
    else:
        log("ChromaDB dizini: Yok (ilk çalıştırma)", "WARNING")

    # Neo4j - socket ile hızlı kontrol
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 7687))
        sock.close()

        if result == 0:
            log("Neo4j (bolt://127.0.0.1:7687): Bağlı", "OK")
            return True
        else:
            log("Neo4j: Erişilemiyor (docker-compose up -d neo4j)", "WARNING")
            return True  # Warning ama devam et
    except Exception as e:
        log(f"Neo4j kontrol hatası: {e}", "WARNING")
        return True

def start_fastapi():
    """FastAPI başlat"""
    print(f"\n{Colors.BOLD}[ADIM 6/6] Servisler başlatılıyor...{Colors.RESET}")
    print(f"\n{Colors.INFO}[1/2] FastAPI başlatılıyor (port 8080)...{Colors.RESET}")

    cmd = [".venv/Scripts/python" if platform.system() == "Windows" else ".venv/bin/python",
           "-m", "uvicorn", "src.api.main:app", "--port", "8080", "--log-level", "info"]

    log(f"Komut: {' '.join(cmd)}", "INFO")

    try:
        # Non-blocking başlatma (arka planda)
        if platform.system() == "Windows":
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.Popen(cmd)

        log("FastAPI başlatıldı (arka planda)", "OK")
        log("Bekleniyor: 8 saniye", "INFO")
        time.sleep(8)
        return True
    except Exception as e:
        log(f"FastAPI başlatma hatası: {e}", "ERROR")
        return False

def start_streamlit():
    """Streamlit başlat"""
    print(f"\n{Colors.INFO}[2/2] Streamlit başlatılıyor (port 8501)...{Colors.RESET}")

    cmd = [".venv/Scripts/python" if platform.system() == "Windows" else ".venv/bin/python",
           "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"]

    log(f"Komut: {' '.join(cmd)}", "INFO")

    try:
        # Non-blocking başlatma (arka planda)
        if platform.system() == "Windows":
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.Popen(cmd)

        log("Streamlit başlatıldı (arka planda)", "OK")
        log("Bekleniyor: 6 saniye", "INFO")
        time.sleep(6)
        return True
    except Exception as e:
        log(f"Streamlit başlatma hatası: {e}", "ERROR")
        return False

def health_check():
    """Servis health check"""
    print(f"\n{Colors.BOLD}Sağlık kontrolleri yapılıyor...{Colors.RESET}")

    import urllib.request
    import json

    # FastAPI health check
    try:
        response = urllib.request.urlopen("http://localhost:8080/health", timeout=5)
        data = json.loads(response.read())
        log(f"FastAPI: HAZIR ✓", "OK")
        return True
    except Exception as e:
        log(f"FastAPI: Henüz hazırlanıyor ({str(e)[:30]})", "WARNING")
        return False

def print_summary():
    """Özet bilgi yazdır"""
    print("\n" + "="*60)
    print(f"{Colors.BOLD}{Colors.OK}✓ SISTEM BAŞLATILDI{Colors.RESET}")
    print("="*60)
    print(f"\n{Colors.INFO}Adresler:{Colors.RESET}")
    print(f"  FastAPI   : {Colors.BOLD}http://localhost:8080{Colors.RESET}")
    print(f"  API Docs  : {Colors.BOLD}http://localhost:8080/docs{Colors.RESET}")
    print(f"  Streamlit : {Colors.BOLD}http://localhost:8501{Colors.RESET}")
    print(f"\n{Colors.INFO}Kapatmak için:{Colors.RESET}")
    print(f"  Windows: taskkill /IM python.exe /F")
    print(f"  Linux:   pkill -f python")
    print("\n" + "="*60 + "\n")

def main():
    """Ana başlatma fonksiyonu"""
    try:
        print_header()

        # Kontroller
        if not check_venv():
            sys.exit(1)

        check_env()  # Warning olabilir
        check_requirements()  # Warning olabilir
        check_ports()
        check_dependencies()  # Warning olabilir

        # Servisler başlat
        if start_fastapi() and start_streamlit():
            time.sleep(2)
            health_check()
            print_summary()
            log("Sistem başarıyla başlatıldı!", "OK")
        else:
            log("Bazı servisler başlatılamadı", "ERROR")
            sys.exit(1)

    except KeyboardInterrupt:
        log("\nSistem kapatılıyor...", "WARNING")
        sys.exit(0)
    except Exception as e:
        log(f"Beklenmedik hata: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
