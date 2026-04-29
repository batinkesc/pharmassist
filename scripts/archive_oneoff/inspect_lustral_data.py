import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Proje kök dizinini ekle
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv()

import chromadb
from src.analysis.cyp450_extractor import extract_cyp_profile_from_text

def inspect_real_data():
    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection("kub_chunks")
    
    target = "LUSTRAL"
    chunks = col.get(where={"madde_no": "4.5"}, include=["documents", "metadatas"])
    found_text = ""
    found_name = ""
    
    for doc, meta in zip(all_chunks := chunks["documents"], chunks["metadatas"]):
        if target.upper() in meta["ilac_adi"].upper():
            found_text += "\n" + doc
            found_name = meta["ilac_adi"]
            
    if not found_text:
        print(f"Could not find {target} in ChromaDB.")
        return

    print(f"--- REAL TEXT FOR {found_name} ---")
    print(found_text[:1000]) # First 1000 chars
    print("--- EXTRACTION ---")
    res = extract_cyp_profile_from_text(found_text, found_name)
    print(f"Automated: {res}")

if __name__ == "__main__":
    inspect_real_data()
