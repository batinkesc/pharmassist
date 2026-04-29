# PharmAssist — Sprint Raporu
## 22 Nisan – 29 Nisan 2026

---

## 0. Özet Tablo

| Tarih | Başlık | Sonuç |
|-------|--------|-------|
| 22 Nis | Run 10 sistematik fix (4 sorun) | Run 10: F=0.679 CR=0.668 (qwen2.5 evaluator) |
| 25 Nis | Groq rebuild — 501 ilaç, tam corpus | DB reset → 10.883 Drug node, %0 unknown |
| 26 Nis | Run 12 baseline kabulü + GT kalite düzeltmesi | **F=0.7607 CU=0.8028 CR=0.7250 → Ort=0.7628 ✓ AKTİF BASELINE** |
| 26-27 Nis | Sprint v1.5.0 — 4 model-odaklı fix | Run 13: CR ↑ +1.2pp, F ↓ −8.7pp ⚠️ |
| 28 Nis | VALIDATE kuralları 3-6 + citation-level doğrulama | 14 yeni test → toplam 95 test |
| 29 Nis | Tag stripping + Run 16 & 17 | Run 17 merged: F=0.7089 CU=0.7487 CR=0.7630 Ort=0.7402 |
| 29 Nis | Diyagram güncellemesi + proje temizliği | sequence.puml + class.puml güncellendi |

---

## 1. Altyapı & Corpus Büyümesi (22–25 Nisan)

### 1.1 Groq API Entegrasyonu & Full Rebuild (25 Nisan)

Önceki mimari LM Studio üzerinden lokal çalışıyordu. Groq API entegrasyonu yapılarak bulut inference'a geçildi; ardından LLM extraction kalitesi için Together AI Qwen3-235B tercih edildi.

**DB Reset & Full Rebuild:**
- 561 PDF işlendi (`data/pdfs/` — tüm KÜB arşivi konsolide edildi)
- **501 ilaç** Drug node
- **10.883** başlangıç node sayısı
- **4.021 INTERACTS_WITH** (%0 unknown — tümü named node)
- **969 CONTRAINDICATED_FOR**, **891 CYP edge** (INHIBITOR/INDUCER/SUBSTRATE)

### 1.2 4.4 Sub-chunking (26 Nisan — Sprint v1.5.0 Fix C)

2500+ karakter Madde 4.4 bölümleri paragrafa göre ~2200 karakter parçalara bölündü (additive — eski chunk'lar kaldırılmadı).

- **422 ilaç**, **1.827 yeni sub-chunk**
- ChromaDB: 10.588 → **11.843 chunk** (+1.255 net eklenmiş)
- Feokromasitoma, miyastenia gravis gibi nadir klinik durumlar artık ayrı embedding'e sahip
- Context Recall'da ölçülebilir artış: CR +1.2pp (Run 12→13 karşılaştırması)

### 1.3 4.8 Sub-chunking (28 Nisan)

Yan etki bölümleri (Madde 4.8) de benzer şekilde parçalandı.

---

## 2. Sprint v1.5.0 — Model Davranış İyileştirmeleri (26–27 Nisan)

Dört fix; GT dosyasına dokunulmadı, tüm değişiklikler sistem genelinde:

| # | Fix | Neden | Etki |
|---|-----|-------|------|
| A | **Answer Calibration Layer** | Model her durumda "dikkatli kullanılmalıdır" diyordu; bağlamdan türetilen klinik etiket (KONTREDİKE / DİKKATLİ / DOZ_AYARI) system prompt'a eklendi | Over-conservatism azaldı |
| B | **CYP Zorunlu Kural** | CYP bilgisi mevcutken model görmezden geliyordu | CYP etkileşim açıklaması artık zorunlu |
| C | **4.4 Sub-chunking** | Bkz. §1.2 | CR ↑ |
| D | **Klinik Sinonim Genişletme** | 40+ tıbbi kısaltma (KBY/KOAH/DVT/SSRI…) ChromaDB retrieval sırasında genişletiliyor | Nadir klinik terimler için coverage ↑ |

**Ayrıca Run 12 öncesinde:**
- `SPECIAL_CONDITION_KEYWORDS`: feokromasitoma / miyastenia gravis / QT uzaması → 4.4 öncelik
- System prompt guardrail: KÜB dışı ilaç önerisi MUTLAK YASAK

**Run 13 Sonucu:**
```
F  = 0.6740  (↓ −8.7pp vs. baseline)   ⚠️ regresyon
CU = 0.7829  (↓ −2.0pp)
CR = 0.7365  (↑ +1.2pp)                ✅ sub-chunk etkisi doğrulandı
Ort= 0.7311
```

**Kök Neden (F Regresyonu):**
1. CYP Zorunlu Kural: model CYP cümleleri eklerken context'ten türetilemeyen ifadeler ekledi → faithfulness düştü
2. Answer Calibration: "DOZ_AYARI" etiketiyle model doz bilgisi vermeye zorlanırken chunk'ta kesin sayı olmadığında hallüsinasyon riski arttı
3. 4 NaN soru (Together.ai 503) — bunlar F ortalamasını çekti
4. CO-DİOVAN/hiperpotasemi false positive — kontrendikasyon doğrulaması yanlış çalıştı

---

## 3. VALIDATE Pipeline v2 — Post-LLM Guardrail Katmanı (28–29 Nisan)

### 3.1 Önceki Durum (Run 12 Baseline)

VALIDATE pipeline 4 adımdı:
1. Güvenli/zararsız ifade → Dikkatli kullanılmalıdır
2. Kontrendikasyon doğrulama (4.3 varlığı)
3. Doğrulanamayan cümle etiketleme `[DOĞRULANAMADI]`
4. Numerik değer doğrulama (doz/eşik)

### 3.2 Bu Sprintte Eklenen 3 Yeni Kural

#### Kural 4 (Revize) — Citation-Level Numerik Doğrulama

**Problem:** Model hem hallüsinasyon yapıp hem sahte kaynak ([İlaç | Madde 4.2]) ekliyordu. Önceki sistem tüm chunk'lara bakıyordu — yanlış chunk'ta sayı varsa yanlış geçti.

**Çözüm:** `_get_cited_section_text()` fonksiyonu eklendi.
- Model `[İlaç | Madde 4.2]` gibi bir kaynak belirtmişse → SADECE o bölümün chunk'larında doğrula
- Bölüm retrieve edilmemişse → atla (false positive riski)
- Kaynak yoksa → tüm chunk'lara bak (eski davranış)

```
None    → kaynak etiketi yok → tüm chunk'lara bak
""      → etiket var ama retrieve edilmemiş → atla
"text"  → bölüm metni → sadece buna göre doğrula
```

#### Kural 5 — CYP Yön Kontrolü (`_validate_cyp_direction`)

**Problem:** Model CYP mekanizmasını bazen ters yazıyor: "İnhibitör eklenince düzey azalır" gibi.

**Çözüm:** 4.5 chunk'ından inhibitör/indükleyici tespiti yapılır; `[CYP450]` etiketli cümlelerde:
- inhibitör + "düzeyi azalır" → `[DOĞRULANAMADI-CYP: inhibitör → düzey artmalı]`
- indükleyici + "düzeyi artar" → `[DOĞRULANAMADI-CYP: indükleyici → düzey azalmalı]`

#### Kural 6 — Verdict Uyum Denetimi (`_enforce_verdict_alignment`)

**Problem:** Bağlamda sadece 4.4 (dikkatli) chunk varken model "kontrendikedir" yazıyordu.

**Çözüm:** 4.3/4.4 chunk'larından desteklenen maks şiddet türetilir; model yanıtındaki ilk karar bununla karşılaştırılır:
- 4.3 chunk var → KONTREDİKE (seviye 4) destekleniyor
- Sadece 4.4 var → DİKKATLİ (seviye 2) maks
- Model, desteklenen seviyenin üzerindeyse → `[AŞIRI YORUM: bağlam bu şiddet seviyesini desteklemiyor]`

#### [AŞIRI YORUM] Etiketinin İyileştirilmesi

`_validate_kontraendikasyon` da iki kolda `[AŞIRI YORUM]` ekleyecek şekilde güncellendi:
- 4.3 chunk hiç yok → "kontrendikedir" → "dikkatli kullanılmalıdır [AŞIRI YORUM: Madde 4.3 retrieve edilmedi]"
- 4.3 var ama eşleşme yok → aynı dönüşüm

### 3.3 Güncel VALIDATE Pipeline (6 Adım)

```python
yanit = _GUVENLI_PATTERN.sub(...)               # 1. Güvenli → Dikkatli
yanit = _validate_kontraendikasyon(...)          # 2. 4.3 doğrulama + [AŞIRI YORUM]
yanit = _tag_unverifiable_sentences(...)         # 3. [DOĞRULANAMADI] etiketleme
yanit = _validate_numeric_claims(...)            # 4. Numerik + citation-level
yanit = _validate_cyp_direction(...)             # 5. CYP inhibitör/indükleyici yön
yanit = _enforce_verdict_alignment(...)          # 6. Verdict > desteklenen → [AŞIRI YORUM]
```

### 3.4 Test Kapsamı

| Kategori | Test Sayısı |
|----------|-------------|
| Citation-level doğrulama (yeni) | 3 |
| [AŞIRI YORUM] (her iki kol) | 2 |
| CYP yön kontrolü (inhibitör/indükleyici) | 3 |
| Verdict alignment overreach | 1 |
| Önceki testler (numerik, güvenli, profil) | 5 |
| **Toplam yeni testler** | **14** |
| **Genel toplam (tüm suite)** | **95 / 95** |

---

## 4. Tag Stripping — RAGAS False-Negative Önleme (29 Nisan)

### Problem

`[DOĞRULANAMADI]`, `[AŞIRI YORUM]` gibi sistem etiketleri `ragas_answer`'a geçince RAGAS faithfulness değerlendirmesi yanlış yapıyordu:
- RAGAS: "Bu cümle bağlamda var mı?" diye soruyor
- Cümle şimdi etiketle birlikte tam olarak uyuşmuyordu
- → False negative → faithfulness düşüyor

### Çözüm

`scripts/run_eval.py`'ye `_strip_validate_tags()` eklendi:

```python
_VALIDATE_TAG_RE = re.compile(
    r'\s*\[DOĞRULANAMADI(?:-\w+)?\s*[^\]]*\]'
    r'|\s*\[AŞIRI\s+YORUM[^\]]*\]'
    r'|\s*\[SİSTEM\s+DÜZELTMESİ[^\]]*\]'
    r'|\s*\[BİLGİ\s+YOK[^\]]*\]',
    re.IGNORECASE,
)
```

- `ragas_answer` → etiketler temizlenir (RAGAS değerlendirmesi için)
- `full_answer` → etiketler korunur (kullanıcıya gösterilir)

---

## 5. RAGAS Run Geçmişi (Tüm Sprint)

| Run | Tarih | F | CU | CR | Ort | Not |
|-----|-------|---|----|----|-----|-----|
| **Run 12** | 26 Nis | **0.7607** | **0.8028** | **0.7250** | **0.7628** | **AKTİF BASELINE ✓** |
| Run 13 | 27 Nis | 0.6740 | 0.7829 | 0.7365 | 0.7311 | Sprint v1.5.0 etki; F ⚠️ |
| Run 14 | 28 Nis | 0.7153 | 0.7752 | 0.7571 | 0.7492 | F regresyon kısmen toparlıyor |
| Run 15 | 28 Nis | 0.7244 | 0.7640 | 0.7577 | 0.7487 | Yakın sonuç |
| Run 16 | 28-29 Nis | 0.7153 | 0.7530 | 0.7571 | 0.7418 | VALIDATE 3-6 eklendi, tag stripping yok |
| **Run 17** | **29 Nis** | **0.7089** | **0.7487** | **0.7630** | **0.7402** | Tag stripping eklendi; AMARYL NaN kalıcı |

> **CR Trendi:** R12→R17 arası CR sürekli yükseliyor: 0.7250 → 0.7630 (+3.8pp) ✅  
> **F Trendi:** Baseline'ın altında seyrediyor (~−5pp) — kök neden: CO-DİOVAN false positive + Haiku model sınırı  
> **Gerçekçi Tavan:** ~0.75-0.76 (Haiku 4.5 + Together.ai değerlendirici + RAGAS semantik kısıtı)

### Kalıcı NaN Sorunu

`v3_q22` — "GFR 25 olan hastada JANUVIA'ya alternatif olarak AMARYL":
- Together.ai `statement_generator_prompt` her seferinde parse hatası veriyor
- Bu soruyu faithfulness = NaN bırakıyor
- Median imputation uygulanıyor (merged sonuçta ortalama kullanılıyor)

---

## 6. Mevcut Sistem Durumu (29 Nisan 2026)

### Corpus & Veritabanı

| Bileşen | Değer |
|---------|-------|
| ChromaDB chunk sayısı | **11.843** (501 ilaç, 4.4+4.8 sub-chunk dahil) |
| Neo4j Drug node | **501** |
| INTERACTS_WITH | **4.021** (%0 unknown) |
| CONTRAINDICATED_FOR | **969** |
| CYP edge toplamı | **891** |
| REQUIRES_DOSE_ADJUSTMENT | **158** |

### Pipeline Bileşenleri

| Bileşen | Durum | Son Değişiklik |
|---------|-------|----------------|
| PDF Parser | ✅ v2.0 | Nisan 11 |
| ChromaDB Retrieval | ✅ Faz 11 (section-aware + reranking) | Nisan 25 |
| Neo4j Graph | ✅ v1.4 (Groq rebuild) | Nisan 25-26 |
| Kümülatif Risk Analizi | ✅ 9 kategori | Nisan 9 |
| CYP450 Mapper | ✅ Statik + Neo4j + LLM fallback | Nisan 11 |
| Answer Calibration | ✅ Pre-LLM klinik etiket | Nisan 26 |
| VALIDATE Pipeline | ✅ 6 adım | **Nisan 29** |
| Tag Stripping (RAGAS) | ✅ | **Nisan 29** |

### Test Durumu

```
95 test / 95 geçiyor (0 başarısız, 0 atlanan)
```

### RAGAS Baseline

```
Run 12 — AKTİF BASELINE
  F  = 0.7607
  CU = 0.8028
  CR = 0.7250
  Ort= 0.7628 ✓ KABUL
```

---

## 7. Bilinen Sorunlar & Sınırlamalar

| # | Sorun | Etki | Öncelik |
|---|-------|------|---------|
| 1 | CO-DİOVAN/hiperpotasemi false positive | `_validate_kontraendikasyon` geçerli bir kontrendikasyon iddiasını "dikkatli" dönüştürüyor → F düşüyor | Orta |
| 2 | AMARYL (v3_q22) kalıcı NaN | Together.ai evaluator parse hatası, faithfulness ölçülemiyor | Düşük |
| 3 | d.inn = NULL | INN-bazlı propagation çalışmıyor; sonraki rebuild'de düzeltilecek | Düşük |
| 4 | RAGAS semantik tavan ~0.75 | Haiku 4.5 + Together.ai evaluator instability; gerçekçi maksimum | Kabul |

---

## 8. Sonraki Adımlar (Öncelik Sırasıyla)

1. **CO-DİOVAN False Positive Fix** — sinonim genişletme veya 4.3 chunk threshold ayarı ile `_validate_kontraendikasyon`'ın geçerli kontrendikasyonları bozmadığından emin ol → F regresyonunun en büyük kaynağı
2. **INN Propagation Fix** — Sonraki rebuild'de `DrugIdentity.inn` → Neo4j Drug node'a yaz; aynı etken madde sorguları düzelecek
3. **HyDE** (Hypothetical Document Embeddings) — Retrieval CR'ı daha da artırabilir
4. **UI: 501 ilaç multiselect refresh** — Corpus 501 ilacı kapsıyor ama UI listesi eski olabilir

---

*Rapor oluşturma tarihi: 29 Nisan 2026*  
*Kapsam: 22–29 Nisan 2026 sprint dönemi*
