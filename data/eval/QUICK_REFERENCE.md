# RAGAS v10 Quick Reference

## Test Results at a Glance

| Metric | Haiku v10 | Mistral v10 | v9 Haiku | Change (v9→v10) |
|--------|-----------|-------------|----------|-----------------|
| **Faithfulness** | 0.6028 | 0.5208 | 0.5485 | +0.0543 (marginal) |
| **Context Recall** | 0.2000 | 0.7500 | 0.2000 | **0.0 (no improvement)** ❌ |
| **General Avg** | 0.4014 | 0.6354 | 0.3742 | +0.0272 |

## Key Finding

**Context Recall DID NOT IMPROVE for Haiku despite all drugs present in v10.**

- v9 Problem: 3 drugs missing (Klaritromisin, Metoprolol, Warfarin)
- v10 Solution: All 5 drugs exist in database
- Haiku Result: R=0.2 → R=0.2 (unchanged)
- Mistral Result: R=0.2 → R=0.75 (improved +55 points)

**Conclusion:** Database gaps were NOT Haiku's problem. Something else is wrong.

## Per-Question Pattern

| Q# | Topic | Haiku R | Mistral R | Gap |
|----|-------|---------|-----------|-----|
| 1 | Drug interaction | 0.0 | 1.0 | 100% |
| 2 | Drug transition | 0.0 | 0.0 | 0% ✓ |
| 3 | Drug combo + renal | 0.0 | 0.75 | 75% |
| 4 | Adverse warning | 1.0 | 1.0 | 0% ✓ |
| 5 | Dosing adjustment | 0.0 | 1.0 | 100% |

**Pattern:** Inference questions (Q1, Q3, Q5) → Haiku R=0, Mistral R>0

## Turkish Patch Verdict

❌ **INEFFECTIVE — Do NOT use**

- Faithfulness: +0.0543 improvement (within statistical noise)
- Context Recall: 0.0 improvement (completely failed)
- Reason: Problem is architectural (evaluator design), not instructional (prompt)

## Recommendation

1. **Revert** Turkish patch from `src/evaluation/ragas_eval.py`
2. **Use Mistral** as primary evaluator (R=0.75 >> Haiku's R=0.2)
3. **Improve RAG** by adding inference context (CYP450, mechanisms)

## Evaluator Selection Guide

| Use Haiku When | Use Mistral When |
|---|---|
| You need strict validation | You need realistic assessment |
| Cross-checking Mistral | Primary evaluation |
| Anything Haiku fails = definitely wrong | Measuring actual system quality |
| Benchmarking against rigid standards | Day-to-day development |

## What Questions Work

**Both evaluators perfect (F=1.0, R=1.0):**
- Q4: Serotonin syndrome risk (explicit KÜB warning)

**Why?** Exact match between answer and KÜB section text.

**Both evaluators struggle (Haiku R=0, Mistral R varies):**
- Q1, Q3, Q5: Require CYP450 mechanism inference

**Why?** Answer must infer mechanism from available chunks (not verbatim).

## Files to Review

**For detailed analysis:**
- `data/eval/RAGAS_V10_ANALYSIS.md` — 200+ lines, complete breakdown

**For structured summary:**
- `data/eval/V10_TEST_SUMMARY.txt` — Executive summary + next steps

**For raw results:**
- `data/eval/ragas_v10_haiku.json` — Haiku full per-question scores
- `data/eval/ragas_v10_mistral.json` — Mistral full per-question scores

## Next Steps (Ordered)

1. **Today:** Revert Turkish patch, update memory
2. **This week:** Set Mistral as default, document evaluator selection policy
3. **Next week:** Improve RAG retrieval (add CYP450 context to chunks)
4. **Later:** Fine-tune reranker, build custom medical evaluator

---

**Test Date:** 2026-04-11  
**Duration:** Haiku 1m 15s, Mistral 13m 54s  
**Status:** ✅ COMPLETE — Turkish patch ineffective, recommend revert
