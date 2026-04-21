# RAGAS v3 Final Run - Sonuçlar

**Tarih:** 2026-04-15 22:32:27 — 2026-04-16 00:57:26  
**Süre:** 2 saat 25 dakika  
**Evaluator:** Mistral-7b-instruct-v0.3 (Local LM Studio)  
**Ayarlar:** max_workers=1, timeout=600s  

---

## 📊 Final Metrikler

```
Faithfulness   (Sadakat)  : 0.7038 / 1.0  ↓
Context Recall (Kapsam)   : 0.7601 / 1.0  ↑
Genel Ortalama            : 0.7319 / 1.0
Değerlendirme             : GELISTIRILEBILIR (0.60-0.75)
```

---

## 📈 Önceki vs Yeni (Karşılaştırma)

| Metrik | v3 Eski Run (Dün) | v3 Yeni Run (Bugün) | Değişim |
|--------|-------------------|-------------------|---------|
| **Faithfulness** | 0.7565 | 0.7038 | **-0.0527** ↓ |
| **Context Recall** | 0.7377 | 0.7601 | **+0.0224** ↑ |
| **Genel Ortalama** | 0.7471 | 0.7319 | **-0.0152** ↓ |
| **NaN Faithfulness** | 18/30 (60%) | 1/33 (3%) | **-57 puan** ✅ |
| **NaN Context Recall** | 3/30 (10%) | 0/33 (0%) | **-3 puan** ✅ |

---

## 🔴 Issues Bulundu

### 1. RagasOutputParserException - Job[50]
```
Prompt fix_output_format failed to parse output: The output parser 
failed to parse the output including retries.
Exception raised in Job[50]: RagasOutputParserException(...)
```
**Impact:** 1 question (Q25: "Hiperpotasemi olan hastada CO-DIOVAN kullanılabilir mi?") NaN returned

---

## 📋 NaN Analizi

**Faithfulness NaN:** 1 soru (indeks: 25)
- Q25: "Hiperpotasemi olan hastada CO-DIOVAN kullanılabilir mi?"
- **Sebep:** Mistral evaluator prompt parsing failure
- **İyileştirme:** Yeni değerlendirici denemesi veya prompt revision

**Context Recall NaN:** 0 soru ✅

---

## 🎯 Bulguların Değerlendirmesi

### ✅ Pozitif
1. **NaN Oranı Dramatik İyileşti**
   - Faithfulness NaN: 60% → 3% (18 → 1 soru)
   - Context Recall NaN: 10% → 0% (3 → 0 soru)
   - Hedef: <20% NaN → **BAŞARILI** ✓

2. **Hiç TimeoutError yok**
   - max_workers=1 ve timeout=600s etkili oldu
   - Sequential evaluation stable çalıştı

3. **Context Recall İyileşti**
   - 0.7377 → 0.7601 (+2.2%)
   - RAG pipeline better

### ⚠️ Kaygılar
1. **Faithfulness Düştü**
   - 0.7565 → 0.7038 (-5.3%)
   - Neden? 
     - Mistral evaluator strictness farkı?
     - Ground truth revizyon 6 sorunun negative impact?
     - LLM model difference (Mistral vs Haiku)?

2. **1 Parser Exception**
   - Job[50]: Output parser bozuk
   - Q25 NaN döndürdü
   - Mistral output format inconsistent?

---

## 📌 Sonraki Adımlar (AŞAMA 2)

### Immediate (Bu Hafta)
1. **Q25 İnceleme**
   - "Hiperpotasemi olan hastada CO-DIOVAN kullanılabilir mi?"
   - Mistral evaluator bunu neden parse edemedi?
   - Test çıktısı neydi?

2. **Faithfulness Düşüşü Analizi**
   - Dün hangi 6 ground truth revizyon yapıldı?
   - Hangisi faithfulness'ı düşürdü?
   - Revert mi yapılmalı?

3. **Evaluator Karşılaştırması** (optional)
   - Mistral vs Haiku evaluate etme differences
   - LM Studio stability kontrol

### Medium (Sonraki Hafta)
4. **RAG Prompt Optimization**
   - Context Recall 0.7601 — hedef 0.80+
   - Chunk retrieval quality check
   - Neo4j graph context optimization

5. **Faithfulness Target 0.75+**
   - Prompt engineering
   - Output validation rules tightening

---

## 📁 Dosyalar

- **Detaylı Log:** `/logs/ragas_v3_final.log` (368 satır)
- **Sonuç JSON:** `/data/eval/ragas_v3_final.json`
- **Bu Rapor:** `RAGAS_V3_FINAL_RESULTS.md`

---

## 🔗 Karşılaştırma: Eski run (2026-04-14)

**Previous Run (dün):**
- Faithfulness: 0.7565
- Context Recall: 0.7377
- NaN Faithfulness: 18/30 (60%)
- NaN Context Recall: 3/30 (10%)
- Parallel Job TimeoutErrors: ~20+
- Evaluation süresi: ~2 saat

**New Run (bugün):**
- Faithfulness: 0.7038 (-5.3%)
- Context Recall: 0.7601 (+2.2%)
- NaN Faithfulness: 1/33 (3%)  ✅ Huge improvement
- NaN Context Recall: 0/33 (0%) ✅ Huge improvement
- Parallel Job Timeouts: 0
- Evaluation süresi: ~2.5 saat (33 soruluk, biraz daha uzun)

---

**SONUÇ:** 
- NaN sorunu çözüldü ✅
- Timeout ayarları çalıştı ✅
- Faithfulness'da düşüş incelenmesi lazım (6 GT revizyon etkisi mi?)
- Context Recall iyi yönde ilerledi ✓

**Token Limit:** Detaylı analiz sonra yapılacak
