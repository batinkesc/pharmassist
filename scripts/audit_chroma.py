"""
ChromaDB vs Parsed JSON Audit
Hangi ilaçlar veritabanında eksik?
"""
import sys, json, os
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path
from src.retrieval.chroma_store import search

# Parsed JSON'daki tüm ilaçları listele
parsed_dir = Path('data/parsed_json')
parsed_drugs = {}

for json_file in sorted(parsed_dir.glob('*.json')):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        drug_name = data.get('ilac_adi', 'UNKNOWN')
        chunk_count = len(data.get('chunks', []))
        parsed_drugs[drug_name] = {
            'file': json_file.name,
            'chunk_count': chunk_count
        }

print("="*80)
print("CHROMADB vs PARSED JSON AUDIT")
print("="*80)
print(f"\nParsed JSON'da {len(parsed_drugs)} ilaç bulundu\n")

# Her ilaç için ChromaDB kontrolü
missing_drugs = []
partial_drugs = []
complete_drugs = []

for drug_name, info in sorted(parsed_drugs.items()):
    expected_chunks = info['chunk_count']

    # ChromaDB'de ara
    try:
        results = search(drug_name, n_results=100, filter_ilac=[drug_name])
        actual_chunks = len(results)
    except:
        actual_chunks = 0

    # Durumu belirle
    if actual_chunks == 0:
        status = "❌ MISSING"
        missing_drugs.append((drug_name, expected_chunks))
    elif actual_chunks < expected_chunks:
        status = f"⚠️  PARTIAL ({actual_chunks}/{expected_chunks})"
        partial_drugs.append((drug_name, expected_chunks, actual_chunks))
    else:
        status = f"✅ COMPLETE ({actual_chunks})"
        complete_drugs.append(drug_name)

    print(f"{status:30} {drug_name[:50]}")

print("\n" + "="*80)
print("ÖZET")
print("="*80)
print(f"✅ Tam yüklü: {len(complete_drugs)}")
print(f"⚠️  Kısmi yüklü: {len(partial_drugs)}")
print(f"❌ Eksik: {len(missing_drugs)}")

if missing_drugs:
    print(f"\n❌ EKSIK İLAÇLAR ({len(missing_drugs)}):")
    for drug, chunks in missing_drugs:
        print(f"   • {drug} ({chunks} chunk eksik)")

if partial_drugs:
    print(f"\n⚠️  KÍSMI YÜKLÜ ({len(partial_drugs)}):")
    for drug, expected, actual in partial_drugs:
        print(f"   • {drug}: {actual}/{expected} chunk")

print(f"\nSonuç: {len(missing_drugs) + len(partial_drugs)} ilaçta veri yükleme problemi!")
