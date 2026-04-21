# PharmAssist — Yapılan ve Yapılacak Değerlendirmesi
**Tarih:** 2026-04-16  
**Durum:** Stabilizasyon AŞAMA 1 Tamamlandı, Ek Önlemler Belirlendi

---

## 1. PLAN vs GERÇEKLEŞEN

### PHARMASSIST_TOPARLAMA_PLANI Çerçevesi

**Orijinal Plan (Belirtildi - Daha önce):**

**AŞAMA 1: Stabilizasyon ve Teşhis**
1. ✅ RAGAS v3 final koşu (timeout 600s, max_workers=1)
2. ✅ CYP450 manuel liste dondurma (freeze notice eklendi)
3. ✅ Neo4j Severity Coverage check script (oluşturuldu)

**AŞAMA 2: CYP450 Otomatik Extraction** (pending)
**AŞAMA 3: Drug Name Normalization** (pending)
**AŞAMA 4: RAGAS Re-run ve Clinical Validation** (pending)

---

## 2. YAPILAN İŞLER — AŞAMA 1 (TAMAMLANDI)

### 2.1 RAGAS v3 Final Run ✅

**Amacı:** NaN oranını <20%'ye düşürmek, timeout/worker ayarlarını doğrulamak

**Tamamlanan Çalışma:**

| İşlem | Yapılan | Sonuç |
|-------|---------|-------|
| RAGAS v3 koşu | timeout=600s, max_workers=1 | ✅ |
| Evaluator | Mistral-7b-instruct-v0.3 (Local LM Studio) | ✅ |
| RAG Pipeline | 33 soru işlendi | ✅ |
| Evaluation | 66 metrik hesaplandı (2h 25m) | ✅ |
| Hiç TimeoutError | 0 exception (öncesi ~20) | ✅ |
| Hata kontrolü | 1 RagasOutputParserException (Q25) | ⚠️ Minor |

**Elde Edilen Metrikler:**

```
Faithfulness   : 0.7038 / 1.0  (öncesi: 0.7565, -5.3%)
Context Recall : 0.7601 / 1.0  (öncesi: 0.7377, +2.2%)
Genel Ortalama : 0.7319 / 1.0
Değerlendirme  : GELISTIRILEBILIR (0.60-0.75)

NaN Oranı:
  - Faithfulness: 1/33 (3%) ✅ (hedef: <20% BAŞARILI)
  - Context Recall: 0/33 (0%) ✅ (hedef: <10% BAŞARILI)
```

**Gerçekleşmeler:**
- ✅ NaN sorunu çözüldü (60% → 3%)
- ✅ max_workers=1 ve timeout=600 etkili oldu
- ⚠️ Faithfulness düştü (-5.3%) — sebep incelenmeli

### 2.2 CYP450 Manuel Liste Dondurma ✅

**Dosya:** `src/analysis/cyp450_mapper.py` (Line 127)

**Yapılan:**
```python
# Dalga 7'ye kadar manuel liste donduruluyor
# NOT: Bundan sonra yeni CYP ekleme AŞAMA 2'ye (otomatik extraction) taşındı
```

**İçerik:**
- 84 entry + yeni 2 entry (CANDÍDIN/CANDIMAX → CYP2C19 inhibitor)
- Statik mapping korunuyor, Dalga 7'den sonra extraction başlayacak

### 2.3 Neo4j Severity Check Script ✅

**Dosya:** `scripts/check_neo4j_severity.py`

**Yapılan:**
- Severity dağılımı sorgusu (INTERACTS_WITH relationships)
- Unknown severity kaynağı analizi
- Kritik kontrendikasyon özeti

**Output:**
- Toplam relationships sayısı
- Severity dağılımı (severe, moderate, mild, contraindicated, unknown)
- Hedef: Tüm interaction'ların severity tanımlı olması

---

## 3. BULUNMUŞ EKSTRA SORUNLAR — AŞAMA 1 Sonrası

### 3.1 Faithfulness Düşüşü (-5.3%) ⚠️

**Nedir:**
- RAGAS v3 Faithfulness: 0.7565 → 0.7038
- Context Recall: 0.7377 → 0.7601 (iyileşti)

**Olası Sebepler:**
1. **Ground Truth Revizyon Etkisi**
   - Önceki session'da 6 soruda GT revizyon yapıldı (v3_q01, q04, q20, q22, q23, q29)
   - Revizyon beklentileri daraltmış olabilir
   - LLM yanıtları beklentiden daha geniş → düşük faithfulness

2. **Mistral vs Haiku Evaluator Farkı**
   - RAGAS v2 (2026-04-08): Haiku evaluator → F:0.7811, CR:0.8864
   - RAGAS v3 (dün): Haiku evaluator → F:0.7565, CR:0.7377 (corpus genişlediği için mi?)
   - RAGAS v3 (bugün): Mistral evaluator → F:0.7038, CR:0.7601
   - Mistral'ın Türkçe JSON parse problemi vs evaluasyon filosofisi farkı?

3. **Corpus Genişlemesinin Etkisi**
   - Dalga 2'de 50+ ilaç eklendi (1000+ chunk)
   - Daha fazla chunk = daha fazla gürültü potansiyeli
   - Retrieval score threshold'lar yeniden optimize edilmedi

**Çözüm (AŞAMA 3'e ertelendi):**
- Ground truth revizyon sonuçlarını incelemek
- Corpus cleanup (ilgisiz chunks)
- Prompt engineering

### 3.2 Q25 Parser Exception ⚠️

**Soru:** "Hiperpotasemi olan hastada CO-DIOVAN kullanılabilir mi?"

**Hata:**
```
RagasOutputParserException: The output parser failed to parse the output including retries.
Prompt fix_output_format failed to parse output
```

**Sebep:** Mistral evaluator → Output JSON format beklentisi unmet

**Etki:** 1 soru NaN (3% — çok az)

**Çözüm (AŞAMA 2'de):** 
- Mistral output format debugging
- Değerlendirici prompt revision

---

## 4. KAPASITANS TABLOSU — ÖNCEKİ vs BUGÜN

| Kategori | AÇIŞ Problem Raporu | RAGAS v3 Bugün | Durum |
|----------|------------------|-----------|--------|
| **NaN Faithfulness** | 18/30 (60%) | 1/33 (3%) | ✅ **FIXED** |
| **NaN Context Recall** | 3/30 (10%) | 0/33 (0%) | ✅ **FIXED** |
| **TimeoutError** | ~20 exception | 0 | ✅ **FIXED** |
| **Faithfulness Score** | 0.7565 | 0.7038 | ⚠️ **DOWN** |
| **Context Recall** | 0.7377 | 0.7601 | ✓ **UP** |
| **Evaluator Stability** | Haiku (500-1500 token çeşitlilik) | Mistral (text-davinci compat) | ⚠️ **Farklı** |

**Sonuç:** Stabilizasyon başarılı, kalite iyileştirmesi bekliyor.

---

## 5. EKLENEN ÖNLEMLER — İLERİYE YÖNELIK

### 5.1 RAGAS Evaluator Seçimi

**Önceki durum:** 
- RAGAS v2 (Haiku): F:0.7811 CR:0.8864 (çok iyiydi ama api cost yüksek)
- RAGAS v3 (Haiku ilk): F:0.7565 CR:0.7377, NaN 60%

**Bugün yapılan:**
- RAGAS v3 (Mistral local): F:0.7038 CR:0.7601, NaN 3%

**Önlemler:**
1. ✅ Mistral LM Studio ile local evaluation — API cost sıfır
2. ✅ max_workers=1 + timeout=600 — stability
3. ⚠️ Evaluator consistency → Ground truth standardization gerekli

### 5.2 Ground Truth Standardization Kurası

**Problem:**
- 6 soruda GT revizyon yapıldı (daha sıkı beklenti)
- Diğer 27 soru GT standartlı değil
- Evaluator consistency yok

**Eklenen Önlem:**
- Tüm 33 soruda GT'nin "klinik kabul edilirlik" standardı belirlen
- Her soruda "iyi yanıt" kriterini deifini (faithfulness için)
- Düşük F'yi geçen soruları target sorguya çevir

**Zaman:** 2-3 saat (AŞAMA 2)

### 5.3 Retrieval Kalitesi Kontrol

**Problem:**
- Context Recall 0.7601 — hedef 0.80+
- 1000+ chunk'la gürültü artmış olabilir

**Eklenen Önlem:**
- ChromaDB chunk quality check (size, relevance)
- Neo4j graph health check (orphan nodes, relationship coverage)
- Retrieval score distribution analizi (p25, median, p75)

**Zaman:** 1-2 saat (AŞAMA 2'de, parallel)

### 5.4 Drug Name Normalization Yol Haritası

**Sorun (AÇIŞ Report'tan):**
- 423 ilaç, 186 unique base names, 106 duplication (%25)
- Trademark (®) sembolü normalization yok
- Neo4j graph fragmented

**Eklenen Önlem:**
- Normalizasyon stratejisi planı yapılıp
- Chrome retrieval'e prefix match fallback ✅ (zaten var)
- Neo4j'de ilaç adı merging (base name ile mapping tablo)
- Trademark cleaning (® sembolü) + Unicode normalization

**Zaman:** 2-4 saat (AŞAMA 3'de)

---

## 6. YAPILACAKLAR — AŞAMA 2-4 RODMAPı

### AŞAMA 2: CYP450 Otomatik Extraction + Bulk Ingest (3-4 gün)

**Yapılacak:**
1. ✅ Freeze notice → Manual list kapatıldı
2. CYP450 otomatik extraction - Madde 4.5'ten (interaction bölümü)
   - Pattern matching: "inhibits CYP", "substrat", "induces"
   - Extraction confidence score
   - Manual list ile merge
3. Bulk ingest — tüm 423 ilaç ChromaDB + Neo4j'ye
4. RAGAS v4 koşu — yeni corpus'ta metrikler

**Hedef:** F≥0.70, CR≥0.80, NaN <5%

---

### AŞAMA 3: Drug Name Normalization + Vision OCR (4-5 gün)

**Yapılacak:**
1. Trademark (®) temizliği
2. Unicode normalization (İ→I, ı→i vs)
3. Neo4j'de drug name consolidation (base name mapping)
4. 44 quarantine PDF'nin Vision OCR ile parse'ı
5. Re-index toplam 423 ilaç

**Hedef:** Duplication %25 → %5, Retrieval success 95%+

---

### AŞAMA 4: RAGAS v5 + Clinical Validation (2-3 gün)

**Yapılacak:**
1. RAGAS v5 koşu (all 33 questions with final state)
2. Ground truth standardization + s'core threshold
3. Klinik senaryolar (13-15 senaryo test)
4. v1.0 Stable karar

**Hedef:** F≥0.75, CR≥0.80, NaN <2%, Klinik test 15/15 geçti

---

## 7. ÖNEMLİ NOTLAR

### Masraflar
- **RAGAS v2 (Haiku API):** $1.07 (yapılmışken)
- **RAGAS v3 (Mistral Local):** $0.00 ✓ (yapılan)
- **Haftalık Token:** 99 remaining (yeterli değil)

### Akış
1. Stabilizasyon ✅ (NaN sorunu çözüldü)
2. Kalite iyileştirme (Faithfulness düşüşü araştırılacak)
3. Ölçek (423 ilaçla final state)
4. Üretim (v1.0 stable)

### Riski En Aza İndirmek
- ✅ Local LM (API free, cost kontrol)
- ✅ max_workers=1 (sequential, stable)
- ✅ Freeze strategy (manual list stable, otomatik ile merge)
- ✅ Staged testing (33 soruluk eval)

---

## 8. SONUÇ

**Yapılan:**
- ✅ RAGAS v3 tamamlandı (NaN 60% → 3%)
- ✅ max_workers=1 ve timeout=600 doğrulandı
- ✅ Local Mistral evaluator seçildi (free)
- ✅ Neo4j health check script oluşturuldu

**Bulunmuş Sorunlar:**
- ⚠️ Faithfulness -5.3% (GT revizyon etkisi?)
- ⚠️ 1 Q25 parser exception (minör)

**Eklenmiş Önlemler:**
- GT standardization kurası
- Retrieval quality check
- Drug name normalization stratejisi
- OCR plan (44 PDF)

**AŞAMA 2-4'e Gidiş:** Ready. Token limiti gözlemlenecek.

---

**Bu rapor** Stabilizasyon başarısını gösterir. Kalite iyileştirmesi ve ölçek next phase'dir.
