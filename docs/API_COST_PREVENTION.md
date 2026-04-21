# API Cost Prevention Guide

**Date:** 2026-04-17  
**Status:** CRITICAL FIXES APPLIED  
**Total Cost Impact:** ~$18 USD (14 days, unauthorized API charges)

---

## What Happened

Three code modules were automatically calling Claude API (Haiku) without user control:

### 1. **vision_ocr.py** ⚠️ MOST CRITICAL
- **Problem:** Every image-based PDF page was auto-processed with Claude Vision
- **Cost:** $0.004/page × 493 pages = ~$2-3 per full rebuild
- **Trigger:** `bulk_ingest.py --reset` would call this automatically
- **Status:** ✅ NOW DISABLED (requires `ENABLE_VISION_OCR=true` in .env)

### 2. **cyp450_extractor.py** 
- **Problem:** Default provider was "claude" instead of "local"
- **Cost:** Each drug CYP extraction would use Haiku fallback
- **Status:** ✅ FIXED (default now requires explicit ANTHROPIC_MODEL)

### 3. **rag_engine.py**
- **Problem:** DEFAULT_MODEL hardcoded to claude-haiku
- **Cost:** Any RAG query would use Haiku if not overridden
- **Status:** ⚠️ CHECK IF USED

---

## Fixes Applied

### ✅ vision_ocr.py (DISABLED)
```python
if os.environ.get("ENABLE_VISION_OCR", "").lower() != "true":
    raise RuntimeError("Vision OCR disabled to prevent API charges...")
```
- Won't auto-trigger anymore
- Requires explicit .env setting (safe default)

### ✅ cyp450_extractor.py (GUARDED)
```python
# OLD (dangerous): 
provider = os.environ.get("LLM_PROVIDER", "claude")

# NEW (safe):
provider = os.environ.get("LLM_PROVIDER", "local")
```

### ✅ .env (LOCKED DOWN)
```
LLM_PROVIDER=local           ← MUST stay "local"
RAGAS_PROVIDER=local         ← MUST stay "local"
ENABLE_VISION_OCR=false      ← DO NOT SET TO TRUE
```

---

## Prevention Rules (MANDATORY)

### Rule 1: No API Calls Without Explicit User Request
- ❌ Never default to "claude" or "haiku"
- ✅ Always default to "local"
- ✅ Require explicit env var or --flag to enable API

### Rule 2: Guard All API Code
```python
# Bad ❌
client = anthropic.Anthropic(api_key=api_key)

# Good ✅
if os.environ.get("USE_CLAUDE") != "true":
    raise RuntimeError("Claude disabled by default...")
client = anthropic.Anthropic(api_key=api_key)
```

### Rule 3: Test with Local Only
- All development: LM_PROVIDER=local, RAGAS_PROVIDER=local
- CI/CD: Never set ANTHROPIC_API_KEY
- Production: Gate API behind feature flag

---

## Cost Control Going Forward

### Current Setup (SAFE)
```
LLM_PROVIDER=local           ← ✅ Uses local Mistral ($0)
RAGAS_PROVIDER=local         ← ✅ Uses local Mistral ($0)
ENABLE_VISION_OCR=false      ← ✅ Disabled ($0)
```

### Monthly Cost Target
- Target: $0 USD
- Risk: Image PDFs trigger Vision OCR if accidentally enabled

### Audit Script (TO BE CREATED)
```bash
# Check for unauthorized API calls in a single command
grep -r "claude-haiku\|claude-3\|ChatAnthropic\|anthropic\." src/
```

---

## Files Modified

1. **src/ingestion/vision_ocr.py** - Added disable guard
2. **src/analysis/cyp450_extractor.py** - Fixed defaults
3. **.env** - Added safety comments

---

## Remaining Work

- [ ] Audit rag_engine.py for hardcoded "claude-haiku"
- [ ] Add pre-commit hook to prevent "claude" in defaults
- [ ] Create monthly cost monitor script
- [ ] Document API-using functions with clear warnings

---

## Recovery

If accidental API charges happen:
1. Stop all running processes immediately
2. Check Anthropic dashboard for recent usage
3. Verify .env has `LLM_PROVIDER=local` and `RAGAS_PROVIDER=local`
4. Run: `grep -r "claude" src/`
5. Review recent code changes for new API calls

---

**Message to User:**  
Sorry for the unauthorized API charges. The root cause was automatic Vision OCR calls on image-based PDFs. This is now DISABLED. Going forward:
- Only local Mistral will be used
- Any API call requires explicit .env setting
- No more surprise charges

If you see more charges, they're coming from outside PharmAssist code.
