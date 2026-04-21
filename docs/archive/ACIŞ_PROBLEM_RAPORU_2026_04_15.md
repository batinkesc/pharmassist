# PharmAssist — AÇIŞ PROBLEM RAPORU
**Tarih:** 2026-04-15  
**Durum:** KRİTİK BULGULAR

---

## 🔴 PROBLEM 1: İLAÇ ADI DUPLICATION (KRITIK)

### Bulgu

```
Toplam İlaçlar:         423
Unique Base Names:      186  (44% oranında!)
Duplicates (>1 var):    106  (25% duplication)

Örnek:
  A-FERİN:    8 variant
  ARTJET:     8 variant  
  EUTHYROX:   8 variant
  HUMALOG:    8 variant
  ... (102 ilaç daha)
```

### Neden Bu Problem?

Duplication senaryoları:

**Senaryo 1: Doz varyantları**
```
EUTHYROX 100 mcg tablet
EUTHYROX 125 mcg tablet
EUTHYROX 150 mcg tablet
EUTHYROX 175 mcg tablet
EUTHYROX 200 mcg tablet
EUTHYROX 25 mcg tablet
EUTHYROX 50 mcg tablet
EUTHYROX 75 mcg tablet
```
→ 8 ayrı Neo4j node

**Senaryo 2: Formülasyon varyantları**
```
HUMALOG 100 IU/ml 10 ml flakon
HUMALOG 100 IU/ml 3 ml kartuş
HUMALOG KWIKPEN 100 U/ml enjektör
... (5 varyant daha)
```
→ 8 ayrı Neo4j node

**Senaryo 3: Marka+formülasyon**
```
A-FERİN FORTE 500 mg/4 mg tablet
A-FERİN SINUS 500 mg/30 mg tablet
A-FERİN ZERO 120 mg/5 mL şurup
... (5 varyant daha)
```
→ 8 ayrı Neo4j node

### Etkisi (Impact)

#### **Senaryo A: Retrieval Başarısızlığı**
```
User: "EUTHYROX kullanan hastada yan etkileri neler?"
      ↓
ChromaDB arar filter_ilac=["EUTHYROX"]
      ↓
Exact match fail (DB'de "EUTHYROX 100 mcg tablet")
      ↓
Fallback: Prefix match "EUTHYROX*" → 8 sonuç
      ↓
Result: ✓ OK (Fallback çalışıyor)
```

#### **Senaryo B: Graph Fragmentation**
```
Neo4j'de:
  Drug: "EUTHYROX 100 mcg" ← Node 1
  Drug: "EUTHYROX 125 mcg" ← Node 2
  ...
  Drug: "EUTHYROX 75 mcg" ← Node 8

Query: "EUTHYROX kullanan hastada kontrendikasyon?"
       ↓
drug_contraindications("EUTHYROX")
       ↓
ilac_node_adlari_bul("EUTHYROX")
       ↓
Returns: ALL 8 variants ✓
       ↓
But:
  - Eğer ilk 3 variantta kontrendikasyon yoksa
  - User sadece ilk 3'ün sonucunu görebilir (limit k=5)
  - Diğer 5 varianttaki kontrendikasyon kayboluyor
```

#### **Senaryo C: Etkileşim Çift Analizi**
```
User: "EUTHYROX + WARFARIN etkileşimi?"
      ↓
multi_drug_interactions(["EUTHYROX", "WARFARIN"])
      ↓
_resolve_ilaclar(["EUTHYROX", "WARFARIN"])
      ↓
gercek_adlar = [
  "EUTHYROX 100 mcg tablet",
  "EUTHYROX 125 mcg tablet",
  "EUTHYROX 150 mcg tablet",  ← Tüm 8'si döner
  ...
  "WARFARIN ..." ← 1 node (unique)
]
      ↓
Neo4j: 8 × 1 = 8 interaction pair sorgusunun yapılması
       ← Unnecessary overload
```

### Mevcut Çözüm Durumu

**Dalga 1-6:**
- ✓ `ilac_node_adlari_bul()` prefix match eklenmiş (Prefix match fallback)
- ✓ ChromaDB `_resolve_drug_names()` fallback mekanizması

**Kapsamayan Şey:**
- ✗ Neo4j'de duplication var (graph overloaded)
- ✗ Query efficiency düşük (8 node yerine 1 ile yapılabilir)
- ✗ Kullanıcı "EUTHYROX" dediğinde tüm 8'nin sonucu mı döndürülüyor? (test yok)

---

## 🔴 PROBLEM 2: TRADEMARK SYMBOL NORMALIZATION (KRITIK)

### Bulgu

```
İlaçlar: 423
Trademark (®) içeren: ??? (script output trimmed ama büyük sayı)
Örnek:
  AMLOPER® 10/10 mg tablet
  LAROXYL® 25 mg tablet
  PLAVIX® 75 mg tablet
```

### Sorun

1. **Veritabanında® kaydediliyor:**
   ```
   Neo4j node.name: "AMLOPER® 10/10 mg"
   ```

2. **User "AMLOPER" sorduğunda:**
   ```
   Exact match: FAIL (® yüzünden)
   Prefix match: OK (toUpper(name) STARTS WITH "AMLOPER")
   ```

3. **ChromaDB metadata:**
   ```
   Chunk: {
     "ilac_adi": "AMLOPER® 10/10 mg",
     "madde_no": "4.5"
   }
   
   filter_ilac=["AMLOPER"] → Exact match FAIL
   Fallback: Prefix match OK
   ```

**Status:** Partially fixed by prefix match fallback, but ugly.

---

## 🟡 PROBLEM 3: PDF PARSE QUALITY (ORTA)

### Untested Components

1. **OCR fallback (v2.1 Vision)**
   - Resim bazlı PDF'ler tespit ediliyor mu?
   - Vision OCR çalışıyor mu?
   - Output quality good?
   → **UNTESTED**

2. **Tablo extraction**
   - Complex tables (nested, merged cells)?
   - Table integrity preserved?
   → **UNTESTED**

3. **Madde tespiti (section detection)**
   - Tüm 18 madde parse ediliyor mu?
   - Eksik madde var mı?
   → **UNTESTED**

### Test Yapılması Gerekenler

```python
# Test 1: Parse success rate
for pdf in data/raw_pdfs:
    result = extract_drug_info(pdf)
    if result['drug_name'] == "Bilinmeyen İlaç":
        FAIL += 1

# Test 2: Section coverage
for drug in 423_drugs:
    for madde in [1, 2, 3, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6]:
        if not has_chunk(drug, madde):
            MISSING += 1
```

---

## 🟡 PROBLEM 4: NEO4J GRAPH HEALTH (ORTA)

### Bilinmeyen Durumlar

1. **Orphan nodes (bağlantısız):**
   ```cypher
   MATCH (d:Drug) WHERE NOT (d)--() RETURN COUNT(d)
   ```
   Expected: < 10  
   Actual: ???

2. **Relationship coverage:**
   - 427 node × 18 madde = ?
   - Kaç (drug, madde) çifti?
   - Target: ≥95%
   - Actual: ???

3. **CYP450 completeness:**
   - 427 ilaçtan kaç tanesinde CYP profile?
   - Static mapping: ~50
   - Parsed from KÜB: ???
   - Total coverage: ???

---

## 🟡 PROBLEM 5: CHROMADB CHUNK QUALITY (ORTA)

### Bilinmeyen Metrikler

```
Chunk count:        ???
Avg chunk size:     ??? (target: 100-300 tokens)
Min/Max:            ???
Section coverage:   ???
Metadata quality:   ???
```

---

## 🟡 PROBLEM 6: RAGAS EVALUASYON EKSIKLIKLERI (KRITIK)

### v3 Sonuçları

```
Faithfulness:   0.7565 (NaN %60 — VERY HIGH!)
Context Recall: 0.7377
```

### Yapılması Gerekenler

1. **✗ RAGAS v3 final koşu:**
   ```bash
   .venv/Scripts/python scripts/run_eval.py \
       --questions data/eval/ragas_v3_questions.json \
       --evaluator local \
       --output data/eval/ragas_v3_final.json
   ```
   → Timeout fix'i (600s) işe yarадı mı? NaN %20 altına düştü mü?

2. **✗ Ground truth doğrulama:**
   - v3_q01, v3_q04, v3_q20, v3_q22, v3_q23, v3_q29 revizyon yapıldı
   - Dosyaya kaydedildi mi?
   - v3_final query'si yeni GT'yi kullanıyor mu?

3. **✗ Klinik v3 senaryoları:**
   - S16 (Jardiance), S17 (Candidin+Plavix), S18 (Lustral) test sonuçları?
   - Tüm 3 geçti mi?

---

## ÖZET: KAPASITANS PROBLEMI

| Alan | Durum | Sorun | Risk |
|------|-------|-------|------|
| **İlaç Adı Duplication** | 423 ilaç, 106 duplication (%25) | Graph fragmented, retrieval noisy | 🔴 HIGH |
| **Trademark Normalization** | ® sembolü varsa normalization yok | Partial fallback, ugly | 🟡 MID |
| **PDF Parse Quality** | OCR, tablo, madde tespiti untested | Unknown parse success | 🟡 MID |
| **Neo4j Graph Health** | Orphan nodes, coverage unknown | Incomplete graph | 🟡 MID |
| **ChromaDB Chunk Quality** | Metrics yok | Unknown chunk size | 🟡 MID |
| **RAGAS Evaluasyon** | v3 final koşu yapılmadı | Improvement unknown | 🔴 HIGH |

---

## IMMEDIATE ACTIONS

**🔴 CRITICAL (hemen):**
1. RAGAS v3 final koşu (4 saat)
2. Ground truth doğrulama (1 saat)

**🟡 HIGH (bu hafta):**
3. Drug name normalization strategy (plan, 2 saat)
4. ChromaDB chunk quality analysis (1 saat)
5. Neo4j graph health check (1 saat)

**🟢 MEDIUM (sonraki hafta):**
6. PDF parse validation (4 saat)
7. CYP450 mapping completion (6 saat)

---

**Bu rapor ne demek:** Sistem işlediği halde **veri kalitesi ve evaluasyon metrikleri belirsiz**. Diagnostic'ler çalıştırılmadan iyileştirme yapılamaz.
