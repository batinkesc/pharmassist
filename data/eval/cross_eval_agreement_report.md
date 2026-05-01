# Cross-Evaluator Agreement Raporu
Tarih: 2026-05-02  |  Evaluator A: Qwen/Qwen3-235B-A22B-Instruct-2507-tput  |  Evaluator B: openai/gpt-oss-120b

## Özet
| Metrik | Pearson r | Mean |Δ| | A NaN | B NaN |
|---|---|---|---|---|
| faithfulness | 0.46 | 0.14 | 3 | 2 |
| context_utilization | 0.41 | 0.16 | 1 | 0 |
| context_recall | 0.46 | 0.19 | 1 | 0 |

## Yüksek Disagreement (|Δ| > 0.25 veya NaN vs valid skor)
| Soru ID | Metrik | Skor A | Skor B | Δ |
|---|---|---|---|---|
| Q01 | context_recall | 1.00 | 0.33 | 0.67 |
| Q03 | context_recall | 1.00 | 0.67 | 0.33 |
| Q05 | faithfulness | NaN | 0.42 | NaN (A failed) |
| Q07 | faithfulness | 0.31 | NaN | NaN (B failed) |
| Q10 | context_recall | 1.00 | 0.50 | 0.50 |
| Q11 | faithfulness | 0.74 | NaN | NaN (B failed) |
| Q11 | context_utilization | 0.53 | 0.81 | 0.28 |
| Q12 | context_utilization | 1.00 | 0.59 | 0.41 |
| Q13 | faithfulness | 0.90 | 0.36 | 0.54 |
| Q14 | faithfulness | NaN | 0.55 | NaN (A failed) |
| Q14 | context_utilization | 1.00 | 0.29 | 0.71 |
| Q14 | context_recall | 1.00 | 0.50 | 0.50 |
| Q15 | context_utilization | 0.62 | 0.12 | 0.50 |
| Q18 | faithfulness | NaN | 0.43 | NaN (A failed) |
| Q18 | context_utilization | NaN | 0.72 | NaN (A failed) |
| Q18 | context_recall | NaN | 1.00 | NaN (A failed) |
| Q20 | faithfulness | 0.81 | 0.53 | 0.28 |
| Q21 | context_utilization | 1.00 | 0.71 | 0.29 |
| Q22 | faithfulness | 0.84 | 0.58 | 0.26 |
| Q22 | context_utilization | 0.96 | 0.53 | 0.43 |
| Q23 | context_recall | 1.00 | 0.50 | 0.50 |
| Q24 | context_recall | 1.00 | 0.50 | 0.50 |
| Q26 | context_utilization | 0.79 | 0.42 | 0.37 |
| Q28 | faithfulness | 0.62 | 1.00 | 0.38 |
| Q28 | context_utilization | 0.95 | 0.50 | 0.45 |
| Q28 | context_recall | 1.00 | 0.00 | 1.00 |
| Q31 | context_recall | 1.00 | 0.00 | 1.00 |
| Q33 | context_recall | 1.00 | 0.00 | 1.00 |

## Yorum
- **Korelasyon eşikleri:** 0.7+ = acceptable, 0.5–0.7 = moderate, <0.5 = low
- **En yüksek anlaşma:** context_recall (r=0.46)
- **En düşük anlaşma:** context_utilization (r=0.41)
- **Toplam high-disagreement vakası:** 28 (33 soru × 3 metrik = 99 değerlendirmeden)
