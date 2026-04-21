# RAGAS Run History — Kronolojik Sıra

**Son Güncelleme:** 2026-04-21

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

### Özet Trend

```
Faithfulness:    0.40 → 0.78 → 0.76 → 0.70 → 0.68 → 0.72 → 0.70 → 0.55 → 0.66 → 0.68
Context Recall:  0.74 → 0.89 → 0.74 → 0.76 → 0.86 → 0.81 → 0.81 → 0.89 → 0.66 → 0.67
```
Run 2'nin Haiku eval skoru direkt karşılaştırılamaz.  
Run 3-8: Mistral local evaluator. Run 9-10: qwen2.5:32b evaluator (daha strict → CR düşük görünür).

Run 2'nin Haiku eval skoru direkt karşılaştırılamaz (farklı evaluator).  
Run 3'ten itibaren tüm evaluator Mistral local — bu çalıştırmalar karşılaştırılabilir.

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
| `ragas_v3_questions.json` | 33 soru — Dalga 3 (mevcut) | Run 3 (30), Run 4-5 (33) |
| `archive/v10/ragas_v10_clean_questions.json` | 5 soru — Turkish patch | Exp-v9, Exp-v10 |

---

## Değerlendirici Notları

- **Haiku (Anthropic API):** Türkçe metni zayıf puanlıyor; ground truth basit olduğunda şişirilmiş Context Recall verir.
- **Mistral local (LM Studio):** Run 3'ten itibaren standart evaluator. Daha strict, Türkçe uyumlu.
- **NaN:** Mistral'ın RAGAS JSON çıktısını parse edemediği durumlarda NaN oluşur — o soru ortalamadan çıkarılır.
