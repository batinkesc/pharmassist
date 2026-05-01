# Cross-Evaluator Agreement Raporu
Tarih: 2026-05-02  |  Evaluator A: Qwen/Qwen3-235B-A22B-Instruct-2507-tput  |  Evaluator B: meta-llama/Llama-3.3-70B-Instruct-Turbo

## Özet
| Metrik | Pearson r | Mean |Δ| | A NaN | B NaN |
|---|---|---|---|---|
| faithfulness | 0.75 | 0.10 | 3 | 0 |
| context_utilization | 0.62 | 0.13 | 1 | 0 |
| context_recall | 0.65 | 0.06 | 1 | 0 |

## Yüksek Disagreement (|Δ| > 0.25 veya NaN vs Skor)
| Soru ID | Metrik | Skor A | Skor B | Δ |
|---|---|---|---|---|
| Q03 | context_utilization | 0.61 | 1.00 | 0.39 |
| Q05 | faithfulness | NaN | 0.29 | NaN (A failed) |
| Q08 | context_recall | 0.50 | 1.00 | 0.50 |
| Q11 | context_utilization | 0.53 | 0.81 | 0.28 |
| Q12 | context_utilization | 1.00 | 0.68 | 0.32 |
| Q14 | faithfulness | NaN | 0.73 | NaN (A failed) |
| Q18 | faithfulness | NaN | 0.89 | NaN (A failed) |
| Q18 | context_utilization | NaN | 0.88 | NaN (A failed) |
| Q18 | context_recall | NaN | 1.00 | NaN (A failed) |
| Q19 | context_recall | 0.50 | 1.00 | 0.50 |
| Q24 | faithfulness | 0.62 | 0.91 | 0.29 |
| Q26 | context_utilization | 0.79 | 0.48 | 0.31 |
| Q33 | context_utilization | 0.64 | 0.00 | 0.64 |
| Q33 | context_recall | 1.00 | 0.00 | 1.00 |

## Yorum
- Korelasyon yorumu (0.7+ = acceptable, 0.5-0.7 = moderate, <0.5 = low)
- NaN vs valid skor durumları en ciddi disagreement olarak rapora eklendi.
