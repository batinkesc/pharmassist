# PharmAssist — Detaylı Teknik Analiz & Problem Terapisi
**Tarih:** 2026-04-15  
**Amaç:** PDF Parse, İsim Normalizasyon, Neo4j Graph, ChromaDB Chunk Kalitesi — Köklü Sorunları Aydınlatmak

---

## PART 1: PDF PARSE ANALYSIS

### Problem 1.1: İlaç Adı Parse Hataları

**Gözlem:** PDF parser `/src/ingestion/pdf_parser.py`'de `_extract_drug_name()` kullanılıyor.

```python
# Satır 237-260: İlaç adı extraction
def _extract_drug_name(first_page_text: str) -> str:
    patterns = [
        re.compile(r"1\.\s*BE[ŞS]ER[İI]\s+TIBB[İI]\s+[ÜU]R[ÜU]N[ÜU]N\s+ADI\s*\n+(.+?)(?:\n|$)"),
        # ...
    ]
    for pattern in patterns:
        m = pattern.search(first_page_text)
        if m:
            name = m.group(1).strip().split("\n")[0].strip()
            return name[:120]
    return "Bilinmeyen İlaç"
```

**Sorunlar:**
1. **Trademark symbolü kaldırılmıyor:** 
   - Input: "AMLOPER® 4/5 mg film kaplı tablet"
   - Output: "AMLOPER® 4/5 mg film kaplı tablet"
   - Neo4j'de bu exact adla saklanıyor ✓ (sorun yok)
   - Ama user "AMLOPER" sorduğunda → `ilac_node_adlari_bul()` prefix match yapıyor ✓ (sorun yok)

2. **Dozaj varyantları ayrı entry'ler:**
   - "AMLOPER 4 mg / 10 mg tablet" → Node 1
   - "AMLOPER 4/5 mg tablet" → Node 2
   - "AMLOPER 5/10 mg" → Node 3
   - **Result:** Aynı ilaçtan 3 node → fragmented graph

3. **Metin parsing hatası riski:**
   - OCR output örneği: "A M L O P E R" (harf ayrı ayrı)
   - Regex birleştiriyor mu? **HAYIR**
   - Risk: "AMLOPER" ne zaman "A M L O P E R" olursa fail

**Kanıt İstenecek:**
```bash
# Dosya: scripts/validate_parse_quality.py (YENİ)
# 1. 64 PDF parse edildikten sonra kaç ilaç adı "Bilinmeyen İlaç" oldu?
# 2. Aynı etkin maddeden kaç unique node var?
# 3. Trademark sembollü ilaçların retrieval success rate'i kaç?
```

---

### Problem 1.2: Bölüm Tespiti (Section Detection) Eksik

**Gözlem:** Parser maddeleri tespit edecek regex'ler var (`_detect_sections()`).

```python
# Satır 348+
patterns = [
    re.compile(r"4\.\s*[0-9][\.\s]*[A-Z].*"),
    # ...
]
```

**Riskli Durumlar:**
1. **Madde 4.2 (Doz) tablo içinde:** 
   - Format: "| GFR 30-60 | 250 mg |" (tablo cell)
   - Text extraction'ı tablo bloğunu atlayabilir? 
   - `_extract_page_text_with_tables()` markdown'a çeviryor ✓ (iyi)
   - Ama markdown içinde "4.2" regex'i trigger olur mu? **UNTESTED**

2. **Çok sayıda alt-bölüm (4.2.1, 4.2.1.1):**
   - Parser en derinği bulabilir mi?
   - Ör: ONAXAN'da 4.2 → 4.2.1 → 4.2.1.1 (Haploloji sonra?)

3. **PDF corrupted metadata:**
   - Ör: "4   .   2" (nokta ayrı satırda)
   - Regex miss eder

**Kanıt İstenecek:**
```
Dosya: scripts/analyze_section_coverage.py (YENİ)
1. 64 ilaç × 18 madde = 1152 beklenen (madde, ilaç) çifti
2. Kaç tanesine chunk var? (target: ≥95%)
3. Hangi ilaçlarda kritik madde (4.2, 4.3, 4.5) eksik?
```

---

### Problem 1.3: Tablo Extraction Sıkıntıları

**Gözlem:** `_extract_page_text_with_tables()` tablolarıtespit ediyor.

```python
# Satır 109-160
try:
    tab_finder = page.find_tables()
    for tbl in tab_finder.tables:
        md = _table_to_markdown(tbl)
        if md:
            table_regions.append({...})
except Exception as e:
    logger.debug(f"find_tables başarısız")
```

**Sorunlar:**
1. **Kompleks tablolar (nested cells, merged cells):**
   - Markdown çevirimi incomplete olabilir
   - Ör: "GFR < 30 → Kontrendike" tek cell'e düşebilir

2. **Tablo sonrası metin:**
   - Tablo bbox'ından sonraki metin skip ediliyor?
   - Ör: Tablo sonrasında "Not: ..." yazısı kaybolur?

3. **Sayısal tablolar (doz tabloları):**
   - Kaç tablolık chunk kayboluyor?

**Kanıt İstenecek:**
```
Test: 5 ilaçın PDF'ini manual check et
  - Tablolar fully captured mi?
  - Markdown format readable mi?
  - Data integrity kontrolü
```

---

## PART 2: İLAÇ ADI NORMALIZATION PROBLEMI

### Problem 2.1: Duplicate Drug Names in Neo4j

**Gözlem:** `data/ilac_listesi_db.txt`'de 64 ilaç var, ama...

```
A-FERİN FORTE 500 mg/4 mg Film Kaplı Tablet
A-FERİN SİNÜS 500 mg/30 mg/1,25 mg film kaplı tablet
A-FERİN ZERO 120 mg/5 mL pediatrik şurup
A-FERİN ZERO 6 PLUS 250 mg/5 mL oral süspansiyon
A-FERİN® 1 mg+160 mg/5 mL pediyatrik şurup
A-FERİN® 300 mg/2 mg/10 mg kapsül
A-FERİN® FORTE 650 mg / 4 mg Film Kaplı Tablet
A-FERİN HOT tek kullanımlık toz içeren poşet
```

**Sorun:** Hepsi "A-FERİN" ama ayrı node.

**Clinical Impact:**
- Q: "A-FERİN yan etkileri neler?"
- Sistem tüm 8 varyantı birden mi fetch ediyor? **UNTESTED**
- Yoksa sadece ilk match'i döndürüyor? **LIKELY**

**Çözüm Eksikliği:**
```python
# Needed but MISSING:
def normalize_drug_name_for_search(user_input: str) -> str:
    """
    "A-FERİN" → all A-FERİN variants (A-FERİN®, A-FERİN®, A-FERİN®...)
    """
    base_name = re.match(r"^([A-ZÇĞİÖŞÜ\-]+)", user_input).group(1)
    # Neo4j'de "base_name STARTS WITH" query yap
    # OR
    # ChromaDB filter_ilac kısmında regex kullan
```

---

### Problem 2.2: Drug Name Resolution Pipeline

**Current Flow:**
```
user_input ("AMLOPER")
    ↓
ilac_node_adlari_bul(ilac: "AMLOPER")
    ├─ Exact match → "AMLOPER" (database exact?)
    ├─ Prefix match → toUpper(name) STARTS WITH "AMLOPER"
    └─ Contains fallback → toLower(name) CONTAINS "amloper"
    ↓
gercek_adlar = ["AMLOPER 4 mg/10 mg...", "AMLOPER 5/10 mg..."]
    ↓
multi_drug_interactions(gercek_adlar)
    ↓
Result: ilaç A + ilaç B etkileşimi
```

**Sorun:** If user says "AMLOPER İŞLE", system matches:
1. "AMLOPER" ✓
2. "İŞLE" → might match "İŞLE" (another drug) OR fail
3. **Result:** wrong interaction

**Test Case Eksikliği:**
```bash
# Test needed:
Q: "AMLOPER + DIŞ ANAESTEZ kombinasyonu etkileşimi nedir?"
Expected: AMLOPER + anesthetic
Actual: ??? (ilaç adı resolution başarılı mı?)
```

---

## PART 3: NEO4J GRAPH EFFECTIVENESS

### Problem 3.1: Graph Data Quality

**Soru:** Neo4j'de 427 drug node var. Kaç tanesinin:
- ✓ INTERACTS_WITH relation var?
- ✓ CONTRAINDICATED_FOR relation var?
- ✗ Orphan node (bağlantısız)?

**Example Query (çalıştırılamıyor çünkü Neo4j offline):**
```cypher
MATCH (d:Drug)
WHERE NOT (d)--()
RETURN COUNT(d) as orphan_count
```

**Expected Response:**
- If orphan_count > 50: **KRITIK SORUN** (graph incomplete)
- If < 10: **GOOD**

---

### Problem 3.2: Relationship Completeness

**Gözlem:** CYP450 mapper'da ~50 ilaç için static profile var.
```python
ILAC_CYP_PROFILI = {
    "CANDÍDIN": {"inhibitor": ["CYP2C9", "CYP3A4", "CYP2C19"]},
    # ... 49 ilaç daha ...
}
```

**Soru:** Kalan 377 ilaç için CYP450 relationship otomatik parse ediliyor mu?

**Test:**
```python
# PLAVIX + CANDÍDIN case
# Flukonazol (CANDÍDIN) CYP2C19 inhibitörü
# Klopidogrel (PLAVIX) CYP2C19 substratı
# → System etkileşim bulmalı

# How?
# Option 1: KÜB 4.5 metninden regex parse
# Option 2: Static mapping
# Option 3: Neo4j relationship tespiti

# Current status: ??? (nedenini kod okumadan anlamak zor)
```

---

### Problem 3.3: Query Performance

**Gözlem:** RAG engine multiple graph queries yapıyor.
```python
# src/agents/rag_engine.py
drug_interactions(ilac)           # Cypher query 1
drug_contraindications(ilac)      # Cypher query 2
multi_drug_interactions(ilaclar)  # Cypher query 3
```

**Risk:** Slow queries → timeout → LLM bağlamsız cevap verir

**Untested:**
- Average query time?
- Timeout frequency?
- Index tanımlanmış mı?

---

## PART 4: CHROMADB CHUNK QUALITY

### Problem 4.1: Chunk Size Distribution

**Gözlem:** 
```
Ortalama chunk: ??? (istatistik yok)
Min/Max: ??? (istatistik yok)
```

**Hedef:** 100-300 token (optimal RAG chunk size)

**Untested:**
- Çoğu chunk > 300 token? (context too noisy)
- Çoğu chunk < 100 token? (insufficient context)
- Chunk sınırları mantıklı mı? (metin ortasında kesilme?)

---

### Problem 4.2: Metadata Filtering

**Gözlem:** `ChromaStore.search()` filter_ilac parametresi kullanıyor.

```python
def search(self, query, filter_ilac=None, k=10):
    if filter_ilac:
        # {"ilac_adi": {"$in": filter_ilac}}
        # Exact match only!
```

**Problem:** 
- User "AMLOPER" sorduğunda
- Database "AMLOPER 4 mg/10 mg" ile arar
- Exact match fail → 0 results
- **Fallback:** prefix match (Dalga 6'da fixed)

**Status:** ✅ Fixed (veya kısmi fix)

---

### Problem 4.3: Reranker Score Analysis

**Untested:**
- Cross-encoder reranker'ın score distribution?
- False positives (0.9+ score ama irrelevant)?
- Threshold optimal mu (0.5, 0.6, 0.7)?

---

## PART 5: RAGAS EVALUASYON SORUNLARI

### Problem 5.1: NaN/Timeout Oranı

**v3 Results:**
```
Faithfulness: 0.7565 (NaN %60!)
Context Recall: 0.7377
```

**Sorun:** Faithful ness'in %60'ı NaN = evaluator timeout/error

**Çözüm (Dalga 6):**
- timeout: 300s → 600s
- max_workers: 2 → 1

**Untested:** Çalışmadı mı? (RAGAS v3 final koşu yapılmadı)

---

### Problem 5.2: Ground Truth Quality

**v3_q01 Example:**
```
Old GT: "Kontrendike değildir, CYP3A4 etkileşimi..."
New GT: "AV blok riski nedeniyle kontrendikedir; CYP3A4..."
```

**Soru:** 6 soru revizyon yapıldı fakat:
1. Revizyon doğru mu?
2. Tüm revizyon dosyaya kaydedildi mi?
3. RAGAS v3 final koşu bu yeni GT'yi kullanıyor mu?

**Status:** ??? (Unknown)

---

## PART 6: ACTIONABLE DIAGNOSTICS

### A. Immediate Tests to Run

```bash
# 1. PDF Parse Quality Audit
.venv/Scripts/python << 'EOF'
from src.ingestion.pdf_parser import extract_drug_info
from pathlib import Path

pdfs = list(Path("data/raw_pdfs").glob("*.pdf"))
print(f"PDF Count: {len(pdfs)}")

failures = []
for pdf in pdfs:
    try:
        result = extract_drug_info(str(pdf))
        if result['drug_name'] == "Bilinmeyen İlaç":
            failures.append((pdf.name, "drug_name parse failed"))
    except Exception as e:
        failures.append((pdf.name, str(e)))

print(f"Parse Failures: {len(failures)}/{len(pdfs)}")
for pdf_name, err in failures:
    print(f"  {pdf_name}: {err}")
EOF

# 2. ChromaDB Chunk Statistics
.venv/Scripts/python << 'EOF'
from src.retrieval.chroma_store import ChromaStore
cs = ChromaStore()
results = cs.collection.get(include=['documents', 'metadatas'])

chunk_sizes = [len(doc.split()) for doc in results['documents']]
print(f"Chunks: {len(chunk_sizes)}")
print(f"  Mean: {sum(chunk_sizes) / len(chunk_sizes):.0f} tokens")
print(f"  Median: {sorted(chunk_sizes)[len(chunk_sizes)//2]}")
print(f"  Range: {min(chunk_sizes)} - {max(chunk_sizes)}")

# Bölüm dağılımı
from collections import Counter
madde_dist = Counter([m.get('alt_madde', '?') for m in results['metadatas']])
for madde, cnt in madde_dist.most_common():
    print(f"  Madde {madde}: {cnt}")
EOF

# 3. Drug Name Duplication Analysis
.venv/Scripts/python << 'EOF'
import re

with open('data/ilac_listesi_db.txt') as f:
    ilaç_adlari = [line.split('[')[0].strip() for line in f]

# Base name çıkar
def get_base_name(full_name):
    m = re.match(r"^([A-ZÇĞİÖŞÜ\-]+)", full_name)
    return m.group(1) if m else full_name

base_names = [get_base_name(ad) for ad in ilaç_adlari]

from collections import Counter
dups = Counter(base_names)
duplicates = {k: v for k, v in dups.items() if v > 1}

print(f"Total drugs: {len(ilaç_adlari)}")
print(f"Unique base names: {len(dups)}")
print(f"Duplicates (>1 variant):")
for base, count in sorted(duplicates.items(), key=lambda x: -x[1])[:20]:
    print(f"  {base}: {count} variants")
EOF
```

---

### B. Code Review Findings

| Dosya | Sorun | Önem |
|-------|-------|------|
| `src/ingestion/pdf_parser.py` | İlaç adı normalization yok (trademark, dozaj) | ORTA |
| `src/ingestion/pdf_parser.py` | Tablo extraction edge cases untested | ORTA |
| `src/graph/graph_retriever.py` | Orphan node detection yok | ORTA |
| `src/retrieval/chroma_store.py` | Chunk quality metrics yok | DÜŞÜK |
| `src/analysis/cyp450_mapper.py` | 377/427 ilaç profil eksik | YÜKSEK |
| `src/evaluation/ragas_eval.py` | RAGAS v3 final koşu yapılmadı | KRİTİK |
| `start.bat` | Neo4j başlatma yok | KRİTİK |

---

## SONUÇ

**Temel Problem:**
- Sistem **çalışıyor** (80% klinik test başarısı)
- Ama **kırılgan**: parse hatası, normalization eksikliği, untested components

**Hemen Yapılması:**
1. ✅ Neo4j auto-start (fixed in start.bat)
2. ❌ RAGAS v3 final koşu
3. ❌ Ground truth doğrulama
4. ❌ Chunk quality metrics
5. ❌ Drug name duplication resolution

**Takvim:**
- **Hafta 1:** Diagnostic scripts çalıştır (4 saatlik)
- **Hafta 2:** Kritik fixler (8 saatlik)
- **Hafta 3:** Normalization + CYP mapping (12 saatlik)

---

**Bu rapor ne zaman tamamlanacak?** → Diagnostic scriptleri çalıştırınca yanıtlar belirtilir.
