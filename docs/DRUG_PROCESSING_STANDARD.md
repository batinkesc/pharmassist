# PharmAssist — Drug Processing Pipeline Standard (v1.1)

**Tarih:** 2026-04-19  
**Durum:** Production Ready — IngestionPipeline (src/pipeline/) aktif  
**Amaç:** Yeni ilaç eklenmesinden veritabanına kadar sorunsuz, standardize bir akış sağlamak

---

## 🎯 Pipeline Nedir? (v1.1 — Unified)

```
PDF → IngestionPipeline (tek komut)
         ├── Parse (KUBParser)
         ├── DrugIdentity (canonical_id — tüm depolarda ortak anahtar)
         ├── QualityGate (karantina / devam kararı)
         ├── KUBExtractor (LLM → etkileşimler, parse anında)
         ├── INNResolver (INN propagation, otomatik)
         └── ChromaDB + Neo4j (aynı anda)
```

**Hedef:** Hiçbir aşamada sistem crash'ı olmayacak. Her ilaç:
- ✅ Kanonik ID (canonical_id) — duplicate güvenli
- ✅ Normalized drug name
- ✅ Temiz metadata
- ✅ Valid structure (QualityGate)
- ✅ LLM extraction (severity bilgili)
- ✅ INN propagation (otomatik)

---

## 📋 Eski İlaçları Düzelt

### Adım 1: 427 İlaçı Normalize Et

```bash
# Dry-run: Ne değişecek görmek için
.venv/Scripts/python scripts/reprocess_normalize_all.py --dry-run

# Gerçek çalıştırma: JSON dosyalarını normalize et
.venv/Scripts/python scripts/reprocess_normalize_all.py
```

**Output:**
- `data/backups/parsed_json_YYYYMMdd_HHMMSS/` — Backup alındı
- `data/parsed_json/*.json` — İlaç adları normalized
- `✓ X dosya güncellendi` — Sayı

**Kontrol:**
```bash
# JSON'larda normalized ad var mı?
cat data/parsed_json/lustral.json | grep ilac_adi
# Output: "ilac_adi": "LUSTRAL 50 MG TABLET"
```

### Adım 2: ChromaDB + Neo4j Yeniden Oluştur

```bash
# ChromaDB'yi sıfırla ve tüm chunk'ları yeniden index et
.venv/Scripts/python scripts/bulk_ingest.py --reset

# Neo4j'de drug node'larını doğrula
.venv/Scripts/python scripts/load_graph.py
```

---

## 🔍 Duplicate'leri Tespit Et ve Plan Yap

### Adım 1: Duplicate Detection

```bash
.venv/Scripts/python scripts/detect_merge_duplicates.py
```

**Output:**
```
DUPLICATE DETECTION RAPORU
================================================================================
Toplam base name: 106 (duplication var)
Toplam variant'lar: 423 ilaç
Merge yapılacak: 317 variant

Top 20 Duplicates:
  1. [8 variant] EUTHYROX
      → Canonical: EUTHYROX
         - EUTHYROX 100 MCG TABLET
         - EUTHYROX 125 MCG TABLET
         - ...
```

### Adım 2: Merge Script'i Gözden Geçir

```bash
# Cypher script oluşturuldu:
cat scripts/merge_plan.cypher

# Neo4j'de test çalıştır
# cypher-shell < scripts/merge_plan.cypher
```

**Not:** Merge işlemi **MANUEL ve KONTROLLÜ** yapılmalı. Relationship'ler etkilenebilir.

---

## ✅ Unit Tests Çalıştır

```bash
# Normalizasyon ve CYP450 fallback testleri
pytest tests/test_normalization_cyp450.py -v

# Çıktı:
# tests/test_normalization_cyp450.py::TestNormalizeDrugName::test_trademark_removal PASSED
# tests/test_normalization_cyp450.py::TestNormalizeDrugName::test_turkish_character_mapping PASSED
# ...
# ====== 20 passed in 0.45s ======
```

---

## 🆕 Yeni İlaç Ekleme Workflow (v1.1)

### Standart Flow

```
1. PDF dosyasını `data/raw_kub/` kopyala
2. IngestionPipeline çalıştır (tek komut)
   ↓
3. Otomatik olarak:
   ✓ PDF parse et (KUBParser)
   ✓ canonical_id oluştur (DrugIdentity)
   ✓ Duplicate kontrol (canonical_id üzerinden)
   ✓ Validasyon / QualityGate
   ✓ LLM extraction (4.3+4.5 → etkileşimler)
   ✓ INN propagation (aynı etken madde grubu)
   ✓ ChromaDB + Neo4j (aynı anda)
```

### Komutlar

```bash
# Tek PDF
.venv/Scripts/python -m src.pipeline.ingestion_pipeline --pdf data/raw_kub/ALTIZEM.pdf

# Tek PDF, mevcut kaydı sil ve yeniden ingest
.venv/Scripts/python -m src.pipeline.ingestion_pipeline --pdf data/raw_kub/ALTIZEM.pdf --force

# Tüm corpus (LLM extraction dahil — gecelik iş)
.venv/Scripts/python -m src.pipeline.ingestion_pipeline --all

# Tüm corpus, tüm kayıtları sil ve yeniden oluştur
.venv/Scripts/python -m src.pipeline.ingestion_pipeline --all --force

# LLM extraction olmadan (hızlı test, etkileşim verisi oluşmaz)
.venv/Scripts/python -m src.pipeline.ingestion_pipeline --all --skip-extraction

# Çıktı: [OK] | [SKIP] | [QUARANTINE] | [FAIL]
```

### ESKİ Komutlar (artık kullanılmaz)

```bash
# KULLANMA — IngestionPipeline'ı kullan
# python scripts/bulk_ingest.py
# python scripts/rebuild_interactions.py
# python scripts/propagate_inn_interactions.py
# python scripts/patch_severity.py
```

---

## 🚨 Validasyon Kuralları (Drug Validation Framework)

Yeni ilaç **otomatik olarak** aşağıdaki kontroller geçer:

| Kontrol | Gerekli | Min/Max | Fail → |
|---------|---------|---------|--------|
| **İlaç Adı** | Evet | 3-256 char | Quarantine |
| **Madde 4.3** | Evet | 100+ char | Quarantine |
| **Madde 4.5** | Evet | 100+ char | Quarantine |
| **Toplam Content** | Evet | 500+ char | Quarantine |
| **UTF-8 Encoding** | Evet | Valid | Quarantine |
| **Boş Chunk %** | Warning | <20% | Log warning |

---

## 📊 Quality Gates (Aşama Aşama)

### Aşama 1: Parse → Validate

```python
from src.data.drug_validation import validate_and_normalize_drug

result = parse_pdf("file.pdf")  # PDF parser çıktısı

if not validate_and_normalize_drug(result):
    # → data/quarantine/ altına rapport
    continue

# ✓ Devam et
```

### Aşama 2: Normalize

```python
from src.data.normalization import normalize_drug_name

cleaned_name = normalize_drug_name("LUSTRAL®")  # "LUSTRAL"
```

### Aşama 3: ChromaDB Index

```python
from src.retrieval.chroma_store import index_single_drug

eklenen = index_single_drug(result["chunks"])
# ✓ Chunks indexed
```

### Aşama 4: Neo4j Graph

```python
from src.graph.kub_to_graph import load_all_drugs

load_all_drugs("data/parsed_json")
# ✓ Drug nodes ve relationships oluşturuldu
```

### Aşama 5: CYP450 Profile

```python
from src.analysis.cyp450_mapper import get_cyp_interactions

# Otomatik: Manuel liste → Fallback extraction
cyp = get_cyp_interactions("LUSTRAL", patient)
# ✓ CYP interactions detected (or empty)
```

---

## 📝 Error Handling

### Scenario 1: Parse Başarısız

```
❌ Parse Error → data/quarantine/lustral_parse_fail.md
   Reason: "OCR failed — image-based PDF"
   Action: Manual review required
```

### Scenario 2: Validation Fail

```
❌ Validation Error → data/quarantine/lustral_qa_fail.md
   Errors:
     - MISSING_SECTION_4_5: Section 4.5 not found
   Action: Re-parse or manual correction
```

### Scenario 3: Normalization (Güvenli)

```
⚠️  Normalization:
   "LUSTRAL®" → "LUSTRAL"  (trademark removed)
   "İLAÇ"     → "ILAC"     (Turkish char normalized)
   Action: ✓ Automatically handled — no intervention needed
```

### Scenario 4: Duplicate Found

```
⚠️  Duplicate:
   "EUTHYROX 100 MCG" already exists → "EUTHYROX 125 MCG" als variant
   Action: Merge plan created — awaiting manual approval
```

---

## 🔄 Reprocessing Strategy

Eski verilerde sorun varsa:

```bash
# 1. Normalize all 427 drugs
.venv/Scripts/python scripts/reprocess_normalize_all.py

# 2. Detect duplicates
.venv/Scripts/python scripts/detect_merge_duplicates.py

# 3. Reset and rebuild
.venv/Scripts/python scripts/bulk_ingest.py --reset

# 4. Verify
pytest tests/test_normalization_cyp450.py -v
```

---

## 📊 Quality Metrics

### Başarılı Ekleme Kriteri

| Metrik | Hedef | Durum |
|--------|-------|-------|
| **Parse Success Rate** | ≥95% | ✓ 427/427 |
| **Validation Pass Rate** | ≥90% | ✓ (TBD) |
| **Normalization** | 100% | ✓ Automatic |
| **Duplicate Detection** | 100% | ✓ (TBD) |
| **CYP450 Coverage** | ≥80% | ✓ Manual + Fallback |
| **ChromaDB Consistency** | 100% | ✓ Indexed |
| **Neo4j Consistency** | 100% | ✓ Loaded |

---

## 🛠️ Tools Reference (v1.1)

| Tool | Amaç | Komut/Import |
|------|------|-------|
| **IngestionPipeline** | Yeni ilaç ekleme (TEK komut) | `python -m src.pipeline.ingestion_pipeline --pdf ...` |
| **NameResolver** | İlaç adı → canonical eşleştirme | `from src.core.name_resolver import get_resolver` |
| **DrugIdentity** | Kanonik ID oluştur | `from src.core.drug_record import DrugIdentity` |
| **ContentPolicy** | Boyut/limit okuma | `from src.core.content_policy import POLICY` |
| **QualityGate** | Parse QA (pipeline içinde otomatik) | `from src.ingestion.quality_gate import QualityGate` |
| **Normalization** | Drug name temizliği | `from src.data.normalization import normalize_drug_name` |
| **RAGAS Eval** | Değerlendirme çalıştır | `python scripts/run_eval.py` |
| **Unit Tests** | Regression testi | `pytest tests/ -v` |
| **DB Health** | ChromaDB ↔ Neo4j tutarlılık | `python scripts/db_health_check.py` |

---

## 🎓 Best Practices

### ✅ DO

- ✓ Her yeni PDF'den önce `bulk_ingest.py --dry-run` koş
- ✓ Saatlik `pytest tests/test_normalization_cyp450.py` koş
- ✓ Aylık backup al
- ✓ Quarterly duplicate detection raporu çıkar

### ❌ DON'T

- ✗ Neo4j node'larını manuel rename etme
- ✗ ChromaDB metadata'sını doğrudan edit etme
- ✗ Parse sonucunu validation geçirmeden use etme
- ✗ Normalizasyon olmadan drug name save etme

---

## 🚀 Future Improvements

1. **Automated Duplicate Merging** — Manual approval sonra otomasyonu
2. **Vision OCR Integration** — Image-based PDF'ler
3. **Real-time Monitoring** — DB consistency checks
4. **Incremental Reprocessing** — Full reset olmadan güncellemeler

---

## ❓ FAQ

**S: "LUSTRAL® 50 mg" ve "LUSTRAL 50 MG" aynı ilaç mı?**  
A: Evet. `normalize_drug_name("LUSTRAL® 50 mg")` → `"LUSTRAL 50 MG"`

**S: Duplicate merge yapıldıktan sonra query'ler çalışır mı?**  
A: Evet. Neo4j relationship'ler canonical node'a yönlendirilir.

**S: CYP450 extraction precision düşük olsa ne olur?**  
A: Fallback strategy: Manuel liste primer kalır, extraction sadece backup.

**S: Validation fail olan PDF'yi kurtarabilir miyiz?**  
A: Evet. `data/quarantine/` rapor vardır. PDF'yi fix et ve yeniden koş.

---

**Version:** 1.0 (Production)  
**Last Updated:** 2026-04-17  
**Status:** ACTIVE
