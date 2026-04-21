# RAGAS v3 Değerlendirme Raporu

**Tarih:** 2026-04-14  
**Test Süresi:** ~115 dakika (RAG: ~8 dk + RAGAS eval: ~115 dk)  
**Toplam Soru:** 30  

---

## 1. Genel Skorlar

| Metrik | Skor | Değerlendirme |
|--------|------|---------------|
| Faithfulness (Sadakat) | **0.7565** | Yanıt context'e ne kadar bağlı |
| Context Recall (Kapsam) | **0.7377** | Ground truth karşılanma oranı |
| **Genel Ortalama** | **0.7471** | GELİŞTİRİLEBİLİR (0.60–0.75) |

> **Not:** RAGAS sınırı 0.75 — ortalama 0.7471 ile eşiğin hemen altında.

---

## 2. Değerlendirme Konfigürasyonu

| Parametre | Değer |
|-----------|-------|
| RAG Pipeline (cevap üretici) | Claude Haiku (`claude-haiku-4-5-20251001`) |
| RAGAS Değerlendirici | Mistral 7B v0.3 (`mistralai/mistral-7b-instruct-v0.3`) |
| LM Studio URL | `http://localhost:1234/v1` |
| Context Size | 16384 token |
| Temperature | 0 |
| Max Tokens | 2048 |
| RAGAS max_workers | 2 |
| RAGAS timeout | 300 saniye |

---

## 3. NaN Analizi

Mistral 7B değerlendirici bazı sorularda timeout verdi (300s limit aşıldı).  
Bu NaN değerler ortalama hesabından **çıkarıldı** — skorlar NaN olmayan sorular üzerinden hesaplandı.

### Faithfulness NaN (18/30 soru — %60!)

Faithfulness değerlendirmesi Mistral için daha karmaşık (claim extraction + verification).

| # | Soru ID | Soru |
|---|---------|------|
| 1 | v3_q02 | GFR 20 olan hastada PRADAXA dozu nasıl ayarlanmalı? |
| 2 | v3_q03 | SPORANOX kullanan hastada CORDARONE kan düzeyi nasıl etkilenir? |
| 3 | v3_q04 | Gebelikte LAROXYL kullanımı güvenli midir? |
| 4 | v3_q07 | İSOPTİN kullanan hastaya CONCOR eklenirse ne olur? |
| 5 | v3_q10 | PLAVIX kullanan hastaya CANDİDİN başlanırsa antiplatelet etki nasıl değişir? |
| 6 | v3_q11 | Emziren annede LUSTRAL kullanımı güvenli midir? |
| 7 | v3_q12 | NORODOL ile CORDARONE birlikte kullanılabilir mi? |
| 8 | v3_q16 | GFR 40 olan hastada COLCHICUM DISPERT dozu nasıl ayarlanmalı? |
| 9 | v3_q17 | CYMBALTA kullanan hastada ALTİZEM SR eklenirse ne olur? |
| 10 | v3_q18 | Gebelikte COZAAR kullanılabilir mi? |
| 11 | v3_q19 | CLEXANE kullanan hastaya PLAVIX eklenmesi kanama riskini nasıl etkiler? |
| 12 | v3_q20 | Child-Pugh A karaciğer yetmezliği olan hastada LİPİTOR dozu nasıl ayarlanmalı? |
| 13 | v3_q21 | PROPYCIL kullanan hastaya AMİODARON (SANORONE) eklenirse ne olur? |
| 14 | v3_q22 | GFR 25 olan hastada JANUVIA'ya alternatif olarak AMARYL kullanılabilir mi? |
| 15 | v3_q24 | TEGRETOL kullanan hastada LAMICTAL DC dozu neden artırılmalıdır? |
| 16 | v3_q27 | 80 yaşındaki hastada RENITEC başlangıç dozu ne olmalı? |
| 17 | v3_q28 | İMURAN kullanan hastada ÜRİKOLİZ başlanırsa ne olur? |
| 18 | v3_q30 | GFR 15 olan hastada METAFORMAL kullanılabilir mi? |

### Context Recall NaN (3/30 soru — %10)

| # | Soru ID | Soru |
|---|---------|------|
| 1 | v3_q06 | 8 yaşındaki 25 kg epilepsi hastasında KEPPRA dozu? |
| 2 | v3_q09 | Astım hastasına ARLEC başlanabilir mi? |
| 3 | v3_q20 | Child-Pugh A karaciğer yetmezliğinde LİPİTOR dozu? |

---

## 4. Soru Bazlı Detay Tablosu

| # | Soru ID | Kategori | Soru (kısa) | F | CR | Yanıt (karakter) | Context (n) |
|---|---------|----------|-------------|---|-----|-------------------|-------------|
| 1 | v3_q01 | kontrendikasyon | TEGRETOL+SANORONE | 0.80 | 1.00 | 1945 | 9 |
| 2 | v3_q02 | doz_bobrek | PRADAXA+GFR20 | NaN | 1.00 | 1472 | 5 |
| 3 | v3_q03 | cyp450_etkilesim | SPORANOX+CORDARONE | NaN | 1.00 | 1756 | 9 |
| 4 | v3_q04 | gebelik | LAROXYL gebelik | NaN | 1.00 | 1223 | 5 |
| 5 | v3_q05 | kontrendikasyon_karaciger | ONAXAN+Child-C | 1.00 | 0.50 | 1131 | 5 |
| 6 | v3_q06 | doz_pediyatrik | KEPPRA 25kg çocuk | 0.667 | NaN | 2013 | 5 |
| 7 | v3_q07 | etkilesim_farmakodinamik | İSOPTİN+CONCOR | NaN | 1.00 | 1600 | 7 |
| 8 | v3_q08 | doz_bobrek | LAMICTAL+GFR35 | 0.571 | 0.333 | 2134 | 5 |
| 9 | v3_q09 | kontrendikasyon | ARLEC+astım | 0.833 | NaN | 981 | 5 |
| 10 | v3_q10 | cyp450_etkilesim | PLAVIX+CANDİDİN | NaN | 0.75 | 1825 | 9 |
| 11 | v3_q11 | laktasyon | LUSTRAL emzirme | NaN | 0.333 | 1734 | 6 |
| 12 | v3_q12 | etkilesim_ciddi | NORODOL+CORDARONE | NaN | 1.00 | 3099 | 9 |
| 13 | v3_q13 | doz_geriyatrik | XANAX 85 yaş | 1.00 | 0.667 | 1304 | 4 |
| 14 | v3_q14 | kontrendikasyon | BRUFEN+mide ülseri | 1.00 | 0.50 | 1266 | 5 |
| 15 | v3_q15 | etkilesim_doz | ALDACTONE+PLASORİN | 1.00 | 1.00 | 1870 | 5 |
| 16 | v3_q16 | doz_bobrek | COLCHICUM+GFR40 | NaN | 0.333 | 1152 | 3 |
| 17 | v3_q17 | cyp450_etkilesim | CYMBALTA+ALTİZEM | NaN | 0.667 | 3177 | 9 |
| 18 | v3_q18 | kontrendikasyon | COZAAR gebelik | NaN | 1.00 | 1303 | 6 |
| 19 | v3_q19 | etkilesim_farmakodinamik | CLEXANE+PLAVIX | NaN | 1.00 | 2524 | 8 |
| 20 | v3_q20 | doz_karaciger | LİPİTOR+Child-A | NaN | NaN | 2341 | 8 |
| 21 | v3_q21 | etkilesim_ciddi | PROPYCIL+AMİODARON | NaN | 1.00 | 2313 | 8 |
| 22 | v3_q22 | doz_bobrek | AMARYL+GFR25 | NaN | 0.00 | 1404 | 5 |
| 23 | v3_q23 | kontrendikasyon | AVELOX+miyastenia | 0.00 | 0.00 | 706 | 1 |
| 24 | v3_q24 | etkilesim_doz | TEGRETOL+LAMICTAL doz | NaN | 1.00 | 2201 | 15 |
| 25 | v3_q25 | yan_etki | JARDIANCE üriner inf. | 0.75 | 1.00 | 654 | 4 |
| 26 | v3_q26 | kontrendikasyon | CO-DIOVAN+hiperpot. | 0.60 | 1.00 | 1461 | 4 |
| 27 | v3_q27 | doz_geriyatrik | RENITEC 80 yaş | NaN | 1.00 | 1538 | 4 |
| 28 | v3_q28 | etkilesim_ciddi | İMURAN+ÜRİKOLİZ | NaN | 0.667 | 1831 | 8 |
| 29 | v3_q29 | kontrendikasyon | NORODOL+feokro. | 0.857 | 0.667 | 1374 | 4 |
| 30 | v3_q30 | doz_bobrek | METAFORMAL+GFR15 | NaN | 0.50 | 1217 | 5 |

> F = Faithfulness, CR = Context Recall, NaN = Mistral timeout (300s aşıldı)

---

## 5. Kategori Bazlı Analiz

### Context Recall — Kategori Ortalamaları

| Kategori | Soru Sayısı | Ortalama CR | En İyi | En Kötü |
|----------|-------------|-------------|--------|---------|
| kontrendikasyon | 7 | 0.74 | 1.00 (q01,q18,q26) | 0.00 (q23) |
| doz_bobrek | 6 | 0.53 | 1.00 (q02) | 0.00 (q22) |
| cyp450_etkilesim | 4 | 0.85 | 1.00 (q03) | 0.67 (q17) |
| etkilesim_farmakodinamik | 3 | 1.00 | 1.00 | 1.00 |
| etkilesim_ciddi | 3 | 0.89 | 1.00 (q12,q21) | 0.67 (q28) |
| gebelik/laktasyon | 3 | 0.78 | 1.00 (q04,q18) | 0.33 (q11) |
| doz_geriyatrik/pediyatrik | 3 | 0.83 | 1.00 (q27) | NaN (q06) |
| doz_karaciger | 2 | ~0.5 | 0.50 (q05) | NaN (q20) |
| yan_etki | 1 | 1.00 | 1.00 (q25) | — |
| etkilesim_doz | 2 | 1.00 | 1.00 | 1.00 |

### Kritik Başarısızlıklar (CR = 0.00)

| Soru ID | Soru | Sorun |
|---------|------|-------|
| v3_q22 | GFR 25'te AMARYL | Corpus'ta AMARYL/glimepirid GFR <30 uyarısı yok? |
| v3_q23 | AVELOX+miyastenia | Sadece 1 context alındı; florokinolon-miyastenia bağlantısı corpus'ta zayıf |

---

## 6. Dikkat Çeken Bulgular

### Yüksek Performans (F=1.0 veya CR=1.0)
- **v3_q01** (TEGRETOL+SANORONE): F=0.80, CR=1.00 — CYP3A4 etkileşim iyi yakalandı
- **v3_q05** (ONAXAN+Child-C): F=1.00 — Karaciğer kontrendikasyonu doğru
- **v3_q13** (XANAX 85 yaş): F=1.00 — Geriyatrik doz bilgisi corpus'ta mevcut
- **v3_q14** (BRUFEN+mide ülseri): F=1.00 — Kontrendikasyon net
- **v3_q15** (ALDACTONE+PLASORİN): F=1.00, CR=1.00 — INR etkileşimi tam kapsandı
- **v3_q25** (JARDIANCE üriner): F=0.75, CR=1.00 — Yan etki bilgisi tam

### Sorunlu Sorular

| Soru | F | CR | Sorun Tahmini |
|------|---|----|---------------|
| v3_q23 (AVELOX) | 0.00 | 0.00 | Corpus'ta sadece 1 chunk; florokinolon-nöromüsküler ilişki eksik |
| v3_q08 (LAMICTAL+GFR35) | 0.571 | 0.333 | Orta böbrek yetmezliği doz tablo bilgisi yetersiz |
| v3_q22 (AMARYL+GFR25) | NaN | 0.00 | AMARYL/glimepirid düşük GFR uyarısı corpus'ta bulunamadı |
| v3_q11 (LUSTRAL emzirme) | NaN | 0.333 | Emzirme bilgisi corpus'ta kısmi |
| v3_q16 (COLCHICUM+GFR40) | NaN | 0.333 | Sadece 3 context; kolşisin böbrek dozu kısmi |

---

## 7. Önceki RAGAS Versiyonlarıyla Karşılaştırma

| Versiyon | Soru Sayısı | Faithfulness | Context Recall | Ortalama | Evaluator |
|---------|-------------|-------------|----------------|----------|-----------|
| v2 (Dalga 2) | 25 | 0.5277 | — | — | Haiku |
| v7 (Mistral) | 25 | 0.7811 | 0.8864 | 0.8338 | Mistral |
| **v3 (bu test)** | **30** | **0.7565** | **0.7377** | **0.7471** | **Mistral** |

> v3'te 5 yeni soru eklendi, bazı kategoriler ilk kez test edildi.  
> Faithfulness NaN oranı v3'te %60 — timeout problemi Mistral için kronik.

---

## 8. NaN Sorununun Analizi

**Kök neden:** Mistral 7B 300 saniye RAGAS timeout limitini aşıyor.  
Faithfulness metriği: RAGAS önce tüm claim'leri listeler, sonra her birini context'te doğrular — iki adımlı, uzun bir prompt zinciri.

**Etki:** 30 sorudan 18'i (%60) faithfulness NaN → gerçek faithfulness skoru bilinmiyor.  
Context recall NaN oranı sadece %10 — daha basit prompt olduğu için daha hızlı.

**Öneriler:**
1. RAGAS timeout'u 300 → 600 saniyeye çıkar (`RunConfig(timeout=600)`)
2. `max_workers=1` yap — paralel job'lar Mistral'ı boğuyor olabilir
3. Alternatif: Faithfulness için daha basit local evaluator dene (Llama 3.2 3B gibi)

---

## 9. Sonuç ve Sonraki Adımlar

**Genel değerlendirme:** Sistem 0.75 eşiğinin hemen altında (**0.7471**).  
Context Recall 0.7377 — corpus kapsam sorunu hâlâ devam ediyor.  

**Öncelikli aksiyon noktaları:**

| Öncelik | Aksiyon | Beklenen Etki |
|---------|---------|---------------|
| 🔴 Yüksek | v3_q23 (AVELOX) için florokinolon-miyastenia chunk ekle | CR 0.00 → ≥0.5 |
| 🔴 Yüksek | v3_q22 (AMARYL) için glimepirid GFR <30 chunk ekle | CR 0.00 → ≥0.5 |
| 🟡 Orta | RAGAS timeout 600s'ye çıkar, max_workers=1 yap | NaN %60 → <%20 |
| 🟡 Orta | COLCHICUM DISPERT böbrek doz tablosu güçlendir | CR 0.333 → ≥0.67 |
| 🟡 Orta | LUSTRAL emzirme bölümünü KÜB'den yeniden parse et | CR 0.333 → ≥0.67 |
| 🟢 Düşük | LAMICTAL DC orta böbrek yetmezliği doz tablosu | CR 0.333 → ≥0.67 |
