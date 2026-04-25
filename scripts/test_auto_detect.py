"""_auto_detect_drugs_from_query testi."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv; load_dotenv()

from src.agents.rag_engine import _auto_detect_drugs_from_query

test_cases = [
    ("Child-Pugh A karaciğer yetmezliği olan hastada LİPİTOR dozu nasıl ayarlanmalı?",
     ["lipitor"]),
    ("Aktif mide ülseri olan hastada BRUFEN kullanılabilir mi?",
     ["brufen"]),
    ("SPORANOX kullanan hastada CORDARONE kan düzeyi nasıl etkilenir?",
     ["sporanox", "cordarone"]),
    ("GFR 15 olan hastada METAFORMAL kullanılabilir mi?",
     ["metaformal"]),
    ("Gebelikte LAROXYL kullanımı güvenli midir?",
     ["laroxyl"]),
    ("8 yaşındaki çocukta KEPPRA dozu nedir?",
     ["keppra"]),
    # False positive testleri
    ("KÜB belgesine göre NSAİİ kullanan hasta",
     []),  # KÜB 3 char, NSAİİ resolver bulamaz
    ("GFR değeri düşük karaciğer yetmezlikli hasta",
     []),  # Hiç büyük harfli ilaç yok
]

print("=== Auto-Detect Test ===\n")
for soru, beklenen in test_cases:
    sonuc = _auto_detect_drugs_from_query(soru)
    sonuc_lower = [s.split()[0].lower() for s in sonuc]
    beklenen_karsi = all(any(b in s for s in sonuc_lower) for b in beklenen) if beklenen else not sonuc
    status = "✅" if beklenen_karsi else "❌"
    print(f"{status} '{soru[:60]}'")
    print(f"   Tespit: {sonuc}")
    print(f"   Beklenen içermeli: {beklenen}\n")
