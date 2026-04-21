import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Proje kök dizinini ekle
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv()

from src.analysis.cyp450_extractor import extract_cyp_profile_from_text

def test_single():
    # Sahte bir KÜB 4.5 metni
    text = """
    Lustral, karaciğerde sitokrom P450 sistemi tarafından metabolize edilir. 
    İn vitro çalışmalar sertralinin CYP3A4, CYP2C9 ve CYP2C19 enzimlerinin orta düzeyde inhibitörü olduğunu göstermiştir.
    Ayrıca sertralin bir CYP2D6 substratıdır.
    """
    drug = "LUSTRAL"
    
    print(f"Testing {drug} extraction...")
    res = extract_cyp_profile_from_text(text, drug)
    print(f"Result: {res}")

if __name__ == "__main__":
    test_single()
