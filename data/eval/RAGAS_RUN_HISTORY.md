# RAGAS Run History — Kronolojik Sıra

**Son Güncelleme:** 2026-04-27

---

## Canonical Runs (Üretim Kalitesi)

Bu çalıştırmalar sistemin gerçek performansını ölçmek için yapıldı.

| Run | Dosya | Tarih | Soru | Evaluator | Faithfulness | Context Recall | Not |
|-----|-------|-------|------|-----------|-------------|---------------|-----|
| **Run 1** | `archive/v1/ragas_baseline_v1.json` | 2026-04-07 | 8 | Haiku | 0.4000 | 0.7417 | Dalga 1 corpus (4 ilaç), temel sistem |
| **Run 2** | `archive/v2/ragas_v2_results.json` | 2026-04-08 | 25 | Haiku | 0.7811 | 0.8864 | Dalga 2 corpus (60 ilaç); Haiku eval skoru yüksek (ground truth basit) |
| **Run 3** | `archive/v3/ragas_v3_first_run.json` | 2026-04-14 | 30 | Mistral local | 0.7565 | 0.7377 | İlk Mistral eval; NaN faith=18/30 (60%) sorun |
| **Run 4** | `archive/v3/ragas_v3_final.json` | 2026-04-15 | 33 | Mistral local | 0.7038 | 0.7601 | max_workers=1 + timeout=600s; NaN faith=1/33 ✅ |
| **Run 5** | `archive/v5/ragas_v5_results.json` | 2026-04-17 | 33 | Mistral local | 0.6755 | 0.8646 | LM Studio system role fix; CR +10.4 puan ↑ |
| **Run 6** | `archive/v6_run6/ragas_v6_results.json` | 2026-04-19 | 32 | Mistral local | **0.7179** | 0.8065 | GT kalite düzeltmesi (23 soru) + 945 IW; F >0.70 hedef ✅; 7 NaN, 1 ctx overflow |
| **Run 7** | `ragas_v7_mistral_results.json` | 2026-04-19 | 33 | Mistral local | 0.7036 | 0.8102 | Yeni mimari (src/core, DrugIdentity, INNResolver); evaluator Mistral |
| **Run 8** | `ragas_v8_mistral_results.json` | 2026-04-19 | 33 | Mistral local | 0.5548 | **0.8898** | Mistral eval — F düştü, CR yüksek; mimari stabilizasyon |
| **Run 9** | `ragas_v9_qwen25_results.json` | 2026-04-19 | 33 | qwen2.5:32b | 0.6574 | 0.6571 | İlk qwen2.5:32b eval; Mistral→qwen geçişi; CR düşük (evaluator stricter) |
| **Run 10** | `ragas_v10_qwen25_results.json` | 2026-04-21 | 33 | qwen2.5:32b | **0.6792** | **0.6677** | 4 sistematik fix: SIDE_EFFECT_KW, INTERACTION_KW, CYP öncelik, K.end. validasyon; Run 9'a göre F +2.2pp CR +1.1pp ↑ |
| **Run 11** | `ragas_v7_qwen3_results.json` | 2026-04-26 | 33 | Together AI Qwen3-235B | 0.7029 | 0.7283 | Yeni evaluator (Together API); 3-metrik seti ilk kez: F+CU+CR; **CU=0.7xxx** (yeni metrik) |
| **Run 12** | `ragas_v8_gt_fixed_results.json` | 2026-04-26 | 32 | Together AI Qwen3-235B | **0.7607** | **0.7250** | GT kalite düzeltmesi (Q02/Q08/Q20/Q29) + Q11 kaldırıldı; CU=0.8028; Genel ort=0.7628 ✓ KABUL; 2 NaN (Q14,Q23) |
| **Mini-13** | `mini_ragas_run13.json` | 2026-04-26 | 5 | Together AI Qwen3-235B | 0.6989 | **0.8167** | Sprint fix doğrulama (5 zor soru); Q29 feokromasitoma: CR 0.0→0.75 ✅; CU=0.6605; Ort=0.7254 |
| **Run 13** | `ragas_v9_run13_results.json` | 2026-04-27 | 32 | Together AI Qwen3-235B | 0.6740 | 0.7365 | Sprint v1.5.0 etki ölçümü; CU=0.7829; Genel ort=0.7311; CR ↑ +1.2pp ✅; F ↓ −8.7pp ⚠️; 4 NaN F; **Run 12 baseline korunuyor** |

### Özet Trend

```
Faithfulness:    0.40 → 0.78 → 0.76 → 0.70 → 0.68 → 0.72 → 0.70 → 0.55 → 0.66 → 0.68 → 0.70 → 0.76 → 0.67
Context Recall:  0.74 → 0.89 → 0.74 → 0.76 → 0.86 → 0.81 → 0.81 → 0.89 → 0.66 → 0.67 → 0.73 → 0.73 → 0.74
```
Run 2'nin Haiku eval skoru direkt karşılaştırılamaz.  
Run 3-8: Mistral local evaluator. Run 9-10: qwen2.5:32b evaluator (daha strict → CR düşük görünür).  
Run 11-13: Together AI Qwen3-235B evaluator; 3-metrik standard (F+CU+CR) devrede.  

**Yeni Metrik — Context Utilization (CU):** Run 11'den itibaren standart. "Getirilen chunk'lar cevap için gerçekten kullanıldı mı?" sorusunu ölçer. GT gerektirmez (GT-free). Run 12: CU=0.8028.

Run 2'nin Haiku eval skoru direkt karşılaştırılamaz (farklı evaluator).  
Run 3'ten itibaren tüm evaluator Mistral local — bu çalıştırmalar karşılaştırılabilir.

**Mini-13 Soru Bazlı (Sprint doğrulama):**
| Soru ID | Soru | F | CU | CR | Not |
|---------|------|---|----|----|-----|
| v3_q02 | PRADAXA GFR 20 doz | 0.667 | 1.000 | 1.000 | CU mükemmel |
| v3_q05 | ONAXAN Child-Pugh C | 0.300 | 0.833 | 0.333 | Retrieval sorunu devam ediyor |
| v3_q06 | KEPPRA pediyatrik doz | 1.000 | 0.500 | 1.000 | F mükemmel; CU iyileşebilir |
| v3_q24 | TEGRETOL+LAMICTAL | 0.778 | 0.143 | 1.000 | CR fix ✅; CU düşük (17 chunk → az kullanım) |
| v3_q29 | **NORODOL feokromasitoma** | 0.750 | 0.826 | **0.750** | **4.4 sub-chunk fix: CR 0.0→0.75 ✅** |

**Run 13 Soru Bazlı (Sprint v1.5.0 tam ölçüm, 32 soru):**
| Soru | F | CU | CR | Not |
|------|---|----|----|-----|
| TEGRETOL+SANORONE etkileşim | 0.636 | 1.000 | 0.750 | |
| PRADAXA GFR 20 doz | 0.714 | 1.000 | 0.667 | |
| SPORANOX+CORDARONE CYP | 0.545 | 0.677 | 0.600 | |
| LAROXYL gebelik | 1.000 | 1.000 | 0.600 | |
| **ONAXAN Child-Pugh C** | **0.750** | 0.833 | **0.750** | Answer Calibration ✅ (Run 12: CR=? iyileşme) |
| KEPPRA pediyatrik doz | 0.889 | 0.500 | 1.000 | |
| İSOPTİN+CONCOR | 0.411 | 0.826 | 1.000 | F düşük |
| LAMICTAL DC GFR 35 | 0.500 | 1.000 | 0.500 | |
| ARLEC astım | 0.667 | 0.667 | 0.667 | |
| PLAVIX+CANDİDİN antiplatelet | NaN | 0.729 | 0.600 | F NaN |
| NORODOL+CORDARONE | NaN | NaN | 0.800 | F+CU NaN |
| XANAX yaşlı doz | NaN | 1.000 | 0.667 | F NaN |
| BRUFEN aktif ülser | 0.857 | 0.754 | 0.667 | |
| ALDACTONE+PLASORİN doz | 0.429 | 1.000 | 0.750 | |
| COLCHICUM GFR 40 | 0.429 | 0.833 | 0.500 | |
| CYMBALTA+ALTİZEM | 0.424 | 1.000 | 0.333 | F+CR düşük |
| COZAAR gebelik | 0.929 | 0.770 | 0.750 | |
| CLEXANE+PLAVIX kanama | 0.636 | 0.696 | 1.000 | |
| LİPİTOR Child-Pugh A | 0.750 | 0.698 | 0.800 | |
| PROPYCIL+SANORONE | 0.600 | 0.926 | 1.000 | |
| AMARYL GFR 25 | 0.444 | 0.659 | 0.333 | |
| AVELOX miyastenia gravis | 0.875 | 0.533 | 0.750 | |
| TEGRETOL+LAMICTAL DC doz | 1.000 | 0.611 | 1.000 | |
| JARDIANCE üriner enfeksiyon | 0.778 | 0.291 | 0.667 | CU düşük |
| CO-DIOVAN hiperpotasemi | 0.473 | 0.942 | 1.000 | Answer Calibration ✅ |
| **RENITEC 80 yaş doz** | **0.133** | 1.000 | 0.500 | F çok düşük — analiz gerekiyor |
| İMURAN+ÜRİKOLİZ | 1.000 | 0.796 | 1.000 | |
| **NORODOL feokromasitoma** | 0.571 | **0.948** | 0.500 | CU ↑; CR sub-chunk bağımlı |
| METAFORMAL GFR 15 | 0.889 | 0.915 | 1.000 | |
| JARDIANCE yan etki | NaN | 0.325 | 0.667 | F NaN |
| PLAVIX+CANDİDİN mantar | 0.643 | 1.000 | 1.000 | |
| LUSTRAL emzirme | 0.900 | 0.333 | 0.750 | |

**Run 13 Kök Neden Analizi (F −8.7pp):**
- 4 NaN Faithfulness (Q10, Q11, Q12, Q30) — Run 12'de 0 NaN vardı → ortalamayı düşürüyor
- Answer Calibration Layer: bazı sorularda severity override → LLM output ile KÜB metni semantik uyumsuzluğu
- CYP Zorunlu Kural: CYP açıklaması her zaman retrieved chunk'larda karşılığı yok → F penaltısı
- Q26 RENITEC F=0.133 anomali → inceleme listesine alındı
- **Run 12 (F=0.7607, CU=0.8028, CR=0.7250) → Aktif Baseline korunuyor**

---

## Experimental Runs (Hata Ayıklama / Geçici)

Bu çalıştırmalar evaluator seçimi, NaN sorunu ve Turkish patch gibi konuları araştırmak için yapıldı. Sistem performansını temsil etmez.

| Run | Dosya | Tarih | Soru | Evaluator | Faithfulness | Context Recall | Amaç |
|-----|-------|-------|------|-----------|-------------|---------------|------|
| Exp-v4 (haiku) | `archive/v4/ragas_v4_haiku_results.json` | 2026-04-14 | 24 | Haiku | 0.4902 | 0.3438 | Evaluator karşılaştırma |
| Exp-v4 (llama) | `archive/v4/ragas_v4_llama_results.json` | 2026-04-14 | 25 | Haiku | 0.5113 | 0.5887 | Llama ile RAG deneyi |
| Exp-v4 (main) | `archive/v4/ragas_v4_results.json` | 2026-04-14 | 25 | Haiku | 0.4903 | 0.3167 | Ground truth revizyonu testi |
| Exp-v6 | `archive/v6/ragas_v6_results.json` | 2026-04-14 | 25 | Haiku | 0.5032 | 0.4233 | Context window deneyi |
| Exp-v7 (haiku) | `archive/v7/ragas_v7_haiku_eval.json` | 2026-04-14 | 25 | Haiku | 0.4895 | 0.3867 | Haiku eval baseline |
| Exp-v7 (mistral fixed) | `archive/v7/ragas_v7_mistral_eval_fixed.json` | 2026-04-14 | 25 | Haiku | 0.6527 | 0.9384 | Mistral RAG + Haiku eval |
| Exp-v8 | `archive/v8/ragas_v8_mistral_detailed.json` | 2026-04-15 | 25 | Mistral local | 0.7195 | 0.9205 | İlk tam Mistral-Mistral run |
| Exp-v9 | `archive/v9/ragas_v9_haiku_fixed.json` | 2026-04-15 | 5 | Haiku | 0.5485 | 0.2000 | Turkish patch testi (5 soru) |
| Exp-v10 (haiku) | `archive/v10/ragas_v10_haiku.json` | 2026-04-16 | 5 | Haiku | 0.6028 | 0.2000 | Turkish patch karşılaştırma |
| Exp-v10 (mistral) | `archive/v10/ragas_v10_mistral.json` | 2026-04-16 | 5 | Mistral local | 0.5208 | 0.7500 | Turkish patch son test |

**v9/v10 Sonucu:** Turkish patch etkisiz — Haiku evaluator Türkçe metni zayıf puanladı. Mistral local evaluator seçildi.

---

## Soru Setleri

| Dosya | İçerik | Kullanıldığı Runs |
|-------|--------|------------------|
| `archive/v1/test_questions.json` | 8 soru — Dalga 1 temel | Run 1 |
| `archive/v2/ragas_v2_questions.json` | 25 soru — Dalga 2 | Run 2, Exp-v4 through v8 |
| `ragas_v3_questions.json` | 33 soru — Dalga 3 (mevcut) | Run 3 (30), Run 4-5 (33), Run 11 (33), Run 12 (32, Q11 kaldırıldı, 4 GT fix) |
| `archive/v10/ragas_v10_clean_questions.json` | 5 soru — Turkish patch | Exp-v9, Exp-v10 |

---

## Değerlendirici Notları

- **Haiku (Anthropic API):** Türkçe metni zayıf puanlıyor; ground truth basit olduğunda şişirilmiş Context Recall verir.
- **Mistral local (LM Studio):** Run 3'ten itibaren standart evaluator. Daha strict, Türkçe uyumlu.
- **NaN:** Mistral'ın RAGAS JSON çıktısını parse edemediği durumlarda NaN oluşur — o soru ortalamadan çıkarılır.
- **Together AI Qwen3-235B:** Run 11+ evaluator. Mistral/qwen2.5'ten daha tutarlı JSON çıktısı; NaN oranı düşük. Context_utilization NaN: LLM karmaşık sorularda CU judgment üretemediğinde (Q14 ALDACTONE+PLASORİN, Q23 TEGRETOL+LAMICTAL).
- **Context Utilization (CU):** Run 11'den itibaren standart metrik. Rakam interpretation: 0.80+ = iyi retrieval-answer alignment, 0.50 altı = getirilen chunk'lar cevaba yansımıyor.
