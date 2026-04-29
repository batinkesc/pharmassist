"""
token_sweep.py — Optimal max_tokens bulmak icin sweep testi.

Her ilac icin 4.5 bolumunun ilk parcasini farkli token limitleriyle
DOGRUDAN _call_lm_studio'ya gondererek karsılastırır.
Sliding window KULLANILMAZ — 1 istek/seviye/ilac → rate limit guvenli.

Kullanim:
    .venv/Scripts/python scripts/token_sweep.py
"""
import sys, os, time, json, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv; load_dotenv()

from pathlib import Path
from src.ingestion.pdf_parser import KUBParser
from src.ingestion.kub_extractor import (
    _call_lm_studio, _parse_json_array, _SYSTEM_PROMPT, _DEFAULT_MODEL
)

# ── Konfigürasyon ─────────────────────────────────────────────────────────────
RAW_DIR = Path("data/raw_pdfs")
PREFIXES = ["PRADAXA_150", "PLAVIX", "XARELTO_15"]
TOKEN_LEVELS = [512, 1024, 1500, 2000, 2500, 3000]

# Sweep icin 4.5 bolumunun kac karakterini kullan (tek pencere)
S45_CHARS = 3000   # ~750 token input; kisa tutarak TPM limitini asmiyoruz
S43_CHARS = 500

# Istekler arasi bekleme (Groq TPM limiti icin)
INTER_LEVEL_SLEEP = 8   # token seviyeleri arasinda bekleme (saniye)

# ── PDF bul ───────────────────────────────────────────────────────────────────
pdfs = []
for prefix in PREFIXES:
    matches = sorted(RAW_DIR.glob(f"*{prefix}*"))
    if not matches:
        for f in RAW_DIR.iterdir():
            fname_norm = f.stem.upper().replace("İ", "I").replace("ı", "I")
            if prefix.upper() in fname_norm:
                matches.append(f); break
    if matches:
        pdfs.append(matches[0])

print(f"Test PDFleri ({len(pdfs)}):")
for p in pdfs: print(f"  {p.name}")
if not pdfs:
    print("HATA: PDF bulunamadi"); sys.exit(1)

# ── Parse ─────────────────────────────────────────────────────────────────────
parser = KUBParser()
drug_data = []  # [{name, s43, s45}]

for pdf_path in pdfs:
    try:
        parse_data = parser.parse(pdf_path)
    except Exception as e:
        print(f"  PARSE HATA: {pdf_path.name}: {e}"); continue

    ilac_adi = parse_data.get("ilac_adi", pdf_path.stem[:50])
    sections: dict[str, str] = {}
    for chunk in parse_data.get("chunks", []):
        madde = chunk.get("madde_no") or chunk.get("bolum_no")
        if madde and "icerik" in chunk:
            sections[madde] = chunk["icerik"]

    s45 = (sections.get("4.5") or "").strip()
    s43 = (sections.get("4.3") or "").strip()
    if not s45:
        print(f"  {pdf_path.stem[:40]}: 4.5 bolumu yok, atlaniyor"); continue

    drug_data.append({
        "name": ilac_adi,
        "short": pdf_path.stem[:30],
        "s43": s43[:S43_CHARS],
        "s45": s45[:S45_CHARS],
        "s45_full_len": len(s45),
    })
    print(f"  {ilac_adi}: 4.5={len(s45)} char, 4.3={len(s43)} char")

print()

# ── Sweep ─────────────────────────────────────────────────────────────────────
print("="*72)
print(f"{'Ilac':<30} {'tokens':>6} {'etkilesim':>10} {'unknown':>8}  delta")
print("="*72)
print(f"  (Tek pencere: ilk {S45_CHARS} char / 4.5, {INTER_LEVEL_SLEEP}s aralikli)")
print("="*72)

results = {}  # short -> {tok: count}

for drug in drug_data:
    short = drug["short"]
    results[short] = {}
    prev_count = -1
    stable_count = 0

    # Prompt bir kez insa edilir, sadece max_tokens degisir
    parts = [f"Drug: {drug['name']}"]
    if drug["s43"]:
        parts.append(f"[Section 4.3 - Contraindications]\n{drug['s43']}")
    parts.append(f"[Section 4.5 - Interactions (first {S45_CHARS} chars)]\n{drug['s45']}")
    parts.append("Output JSON array:")
    user_prompt = "\n\n".join(parts)

    for i, max_tok in enumerate(TOKEN_LEVELS):
        if i > 0:
            time.sleep(INTER_LEVEL_SLEEP)

        raw = _call_lm_studio(
            system=_SYSTEM_PROMPT,
            user=user_prompt,
            model=_DEFAULT_MODEL,
            max_tokens=max_tok,
            timeout=45,
        )

        if raw is None:
            # 429 veya baska hata
            n_total = -1  # hata isareti
            n_unknown = 0
        else:
            items = _parse_json_array(raw)
            n_total   = len(items)
            n_unknown = sum(1 for it in items
                           if str(it.get("severity","")).lower()
                           in ("unknown","bilinmiyor",""))

        results[short][max_tok] = max(n_total, 0)

        if n_total < 0:
            delta_str = "HATA(429?)"
            print(f"{short:<30} {max_tok:>6}  {'ERR':>8}  {'':>7}  {delta_str}")
            # Rate limit — daha uzun bekle
            time.sleep(30)
            prev_count = 0
            continue

        delta_str = ""
        if prev_count >= 0:
            diff = n_total - prev_count
            delta_str = f"({'+'if diff>=0 else ''}{diff})"

        print(f"{short:<30} {max_tok:>6}  {n_total:>8}  {n_unknown:>7}  {delta_str}")

        # Stabilite kontrolu: 2 seviye ust uste artmiyorsa dur
        if prev_count >= 0 and n_total <= prev_count:
            stable_count += 1
            if stable_count >= 2:
                print(f"  >>> Sabitlendi: {prev_count} etkilesim @ {max_tok} tokens")
                break
        else:
            stable_count = 0
        prev_count = n_total

    print()

# ── Ozet ──────────────────────────────────────────────────────────────────────
print("="*72)
print("OZET — Token seviyesine gore ortalama etkilesim:")
print("="*72)
prev_avg = 0.0
for tok in TOKEN_LEVELS:
    vals = [v[tok] for v in results.values() if tok in v]
    if not vals: continue
    avg = sum(vals) / len(vals)
    gain = avg - prev_avg if prev_avg > 0 else 0.0
    print(f"  {tok:>5} tokens:  ort={avg:5.1f}  toplam={sum(vals):3d}  kazanim={gain:+.1f}")
    prev_avg = avg

print()
all_totals = [(tok, sum(v.get(tok, 0) for v in results.values())) for tok in TOKEN_LEVELS]
all_totals = [(t, c) for t, c in all_totals if c > 0]
if all_totals:
    max_total = max(c for _, c in all_totals)
    for tok, cnt in all_totals:
        if cnt >= max_total * 0.95:
            print(f"TAVSIYE: {tok} tokens — maksimumun en az %95'i ({cnt}/{max_total})")
            break
