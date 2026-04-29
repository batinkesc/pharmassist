"""
KUBExtractor — parse anında LLM tabanlı structured etkileşim çıkarımı.

Önceki durum:
  - rebuild_interactions.py: ayrı script, parse'dan sonra çalışıyor
  - severity unknown gelince sessiz geçiş
  - Türkçe severity normalize eksikti (sonradan eklendi, eksik mapping)
  - Retry yok — timeout veya boş JSON → unknown birikimi

Yeni durum:
  - IngestionPipeline parse anında bu modülü çağırır
  - Pydantic validation → hatalı kayıt drop edilir, log'a düşer
  - severity=unknown gelirse → severity-specific retry (1 kez)
  - Kapsamlı Türkçe normalizasyon
  - LLM erişilemezse [] döner (karantina tetiklemez)
  - Her DrugInteraction için confidence skoru

Desteklenen LLM backend:
  - LM Studio (default, yerel) → LM_STUDIO_URL
  - Anthropic API (alternatif) → ANTHROPIC_API_KEY gerekli
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Optional

from loguru import logger
from pydantic import BaseModel, field_validator, ValidationError

from src.core.content_policy import POLICY


# ------------------------------------------------------------------
# Severity enum + normalizasyon
# ------------------------------------------------------------------

class SeverityLevel(str, Enum):
    CONTRAINDICATED = "contraindicated"
    SEVERE          = "severe"
    MODERATE        = "moderate"
    MILD            = "mild"
    UNKNOWN         = "unknown"


# Kapsamlı Türkçe → İngilizce eşleştirme
_TR_SEVERITY_MAP: dict[str, str] = {
    # contraindicated
    "kontrendike":             "contraindicated",
    "kontrendikedir":          "contraindicated",
    "kullanılmamalı":          "contraindicated",
    "kullanılmamalıdır":       "contraindicated",
    "verilmemelidir":          "contraindicated",
    "kesinlikle önerilmez":    "contraindicated",
    "birlikte kullanılmamalı": "contraindicated",
    # severe
    "ciddi":                   "severe",
    "şiddetli":                "severe",
    "hayati":                  "severe",
    "tehlikeli":                "severe",
    "ağır":                    "severe",
    # moderate
    "orta":                    "moderate",
    "dikkatli":                "moderate",
    "dikkat":                  "moderate",
    "izlem":                   "moderate",
    "doz ayarı":               "moderate",
    "doz düzenlemesi":         "moderate",
    "önemli":                  "moderate",
    # mild
    "hafif":                   "mild",
    "minimal":                 "mild",
    "önemsiz":                 "mild",
    "sınırlı":                 "mild",
    # unknown
    "bilinmiyor":              "unknown",
    "belirsiz":                "unknown",
    "bilinmemektedir":         "unknown",
}

_VALID_SEVERITIES = {s.value for s in SeverityLevel}


def normalize_severity(raw: str) -> str:
    """
    LLM çıktısındaki ham severity değerini standart İngilizce forma çevirir.
    Eşleşme bulunamazsa 'unknown' döner.
    """
    if not raw:
        return "unknown"
    s = raw.lower().strip()
    if s in _VALID_SEVERITIES:
        return s
    for tr, en in _TR_SEVERITY_MAP.items():
        if tr in s:
            return en
    return "unknown"


# ------------------------------------------------------------------
# Pydantic modeli — LLM çıktısı buna parse edilir
# ------------------------------------------------------------------

def _normalize_raw_item(item: dict) -> dict:
    """
    LLM bazen beklenen 'drug_b' yerine farklı field adları kullanır.
    Bilinen alternatifleri 'drug_b' olarak normalize eder.

    Örnekler:
      {'drug1': 'X', 'drug2': 'Y', ...}  → drug2 → drug_b
      {'interaction': 'X', ...}           → interaction → drug_b
      {'drug': 'X', ...}                  → drug → drug_b
      {'name': 'X', ...}                  → name → drug_b
    """
    if "drug_b" in item:
        return item
    item = dict(item)  # kopyala, orijinali bozma
    for alt in ("drug2", "interaction", "drug", "name", "drug_name"):
        if alt in item:
            item["drug_b"] = item.pop(alt)
            # drug1 varsa temizle (ana ilaç, bize lazım değil)
            item.pop("drug1", None)
            break
    return item


class _RawInteraction(BaseModel):
    """LLM JSON çıktısından parse edilen ham etkileşim kaydı."""
    drug_b: str
    severity: str = "unknown"
    section: str = "4.5"
    mechanism: Optional[str] = None

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_sev(cls, v):
        return normalize_severity(str(v))

    @field_validator("drug_b", mode="before")
    @classmethod
    def clean_name(cls, v):
        return str(v).strip()[:200]

    @field_validator("section", mode="before")
    @classmethod
    def clean_section(cls, v):
        s = str(v).strip()
        return s if s in ("4.3", "4.4", "4.5") else "4.5"


# ------------------------------------------------------------------
# Pipeline için zengin etkileşim modeli
# ------------------------------------------------------------------

# Bilinen ilaç sınıfı isimleri — Drug node'u ile eşleşemezler, ayrı işlenir
KNOWN_DRUG_CLASSES: frozenset[str] = frozenset({
    "mao inhibitörleri", "mao inhibitorleri", "mao inhibitors",
    "beta blokerler", "beta-blokerler", "beta blockers",
    "nsaid", "nsaids", "nsaid'ler", "nsaid ler",
    "ace inhibitörleri", "ace inhibitorleri", "ace inhibitors",
    "kalsiyum kanal blokerleri", "calcium channel blockers",
    "anjiyotensin reseptör blokerleri", "arb",
    "ssri", "ssri'ler", "seçici serotonin geri alım inhibitörleri",
    "snri", "snri'ler",
    "trisiklik antidepresanlar", "tca",
    "antikoagülanlar", "antikoagulanlar", "anticoagulants",
    "antifungaller", "antifungals",
    "kortikosteroidler", "corticosteroids",
    "diüretikler", "diuretikler", "diuretics",
    "statinler", "statins",
    "opioidler", "opioids",
    "benzodiazepinler", "benzodiazepines",
    "aminoglikozitler", "aminoglycosides",
    "kinolon antibiyotikler", "fluorokinolonlar", "fluoroquinolones",
    "sitostatikler", "antineoplastikler",
    "hepatotoksik ilaçlar", "nefrotoksik ilaçlar",
    "cyp3a4 inhibitörleri", "cyp3a4 induktörleri",
    "cyp2d6 inhibitörleri", "cyp2c9 inhibitörleri",
})


def is_drug_class(name: str) -> bool:
    """Verilen ilaç adının bilinen bir ilaç sınıfı olup olmadığını kontrol eder."""
    return name.lower().strip() in KNOWN_DRUG_CLASSES


@dataclass
class DrugInteraction:
    """
    Bir KÜB'den çıkarılan tek ilaç-ilaç etkileşimi.
    IngestionPipeline bu listeyi Neo4j'e yazar.
    """
    drug_b_raw: str                                   # LLM'in verdiği ham ad
    severity: str                                     # normalize edilmiş
    source_section: Literal["4.3", "4.4", "4.5"]
    drug_b_canonical: Optional[str] = None            # NameResolver sonrası dolu
    mechanism: Optional[str] = None
    confidence: float = 1.0                           # 0-1; unknown → 0.3
    is_propagated: bool = False                       # INNResolver tarafından kopyalandı mı
    propagated_from: Optional[str] = None             # Hangi ilaçtan kopyalandı
    is_drug_class: bool = False                       # MAO inhibitörleri gibi sınıf isimleri

    def is_unknown(self) -> bool:
        return self.severity == "unknown"


# ------------------------------------------------------------------
# LM Studio prompt inşacı
# ------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "Extract drug-drug interactions from Turkish KUB (product information) text. "
    "Return ONLY a valid JSON array. Each object must have exactly these fields: "
    '{"drug_b":"<exact drug or INN name>","severity":"contraindicated|severe|moderate|mild|unknown","section":"4.3|4.5","mechanism":"<optional short text or null>"}. '
    "Rules: "
    "1. drug_b must be specific drug/INN name or drug class (e.g. 'MAO inhibitörleri') — no vague terms like 'some drugs'. "
    "2. severity MUST be one of the 5 English values above. "
    "3. contraindicated=birlikte kullanılmamalı/kontrendike; severe=ciddi/hayati/ölümcül; "
    "moderate=dikkatli/doz ayarı/izlem; mild=hafif/önemsiz. "
    "4. If unsure between moderate and mild, choose moderate. "
    "5. No markdown, no explanation — JSON array only."
)

_RETRY_SEVERITY_PROMPT = (
    "The previous response had 'unknown' severity for some interactions. "
    "For each interaction below, assign the correct severity based on clinical significance. "
    "Remember: contraindicated=do not use together; severe=life-threatening risk; "
    "moderate=use with caution/monitoring; mild=minor effect. "
    "Return ONLY the corrected JSON array."
)


def _build_user_prompt(ilac_adi: str, sections: dict[str, str], s45_window: str | None = None) -> str:
    """
    s45_window: sliding window modunda dışarıdan verilen 4.5 penceresi.
    None ise POLICY limiti uygulanır (kısa section'lar için).
    """
    parts = [f"Drug: {ilac_adi}"]
    s43 = (sections.get("4.3") or "").strip()
    if s43:
        parts.append(f"[Section 4.3 - Contraindications]\n{s43[:POLICY.extraction_section_43_chars]}")
    if s45_window is not None:
        parts.append(f"[Section 4.5 - Interactions (partial)]\n{s45_window}")
    else:
        s45 = (sections.get("4.5") or "").strip()
        if s45:
            parts.append(f"[Section 4.5 - Interactions]\n{s45[:POLICY.extraction_section_45_chars]}")
    parts.append("Output JSON array:")
    return "\n\n".join(parts)


def _make_windows(text: str) -> list[str]:
    """
    Uzun section 4.5 metnini örtüşen pencereler halinde böler.
    Her pencere extraction_window_chars uzunluğunda,
    bir sonrakiyle extraction_window_overlap kadar örtüşür.
    """
    size    = POLICY.extraction_window_chars
    overlap = POLICY.extraction_window_overlap
    step    = size - overlap
    windows = []
    start = 0
    while start < len(text):
        end = start + size
        windows.append(text[start:end])
        if end >= len(text):
            break
        start += step
    return windows


# ------------------------------------------------------------------
# LM Studio API istemcisi
# ------------------------------------------------------------------

def _get_lm_url() -> str:
    """LM_STUDIO_URL env var'dan okur, /chat/completions ekler."""
    base = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
    return base.rstrip("/") + "/chat/completions"

def _get_lm_api_key() -> str | None:
    """LM_STUDIO_API_KEY env var'dan okur (Groq / Together AI vb. için)."""
    return os.getenv("LM_STUDIO_API_KEY") or None

_DEFAULT_MODEL = os.getenv("LM_STUDIO_MODEL", "llama-3.3-70b-versatile")

# Rate limiter — sağlayıcıya göre env ile ayarlanır
# Groq free: LLM_MIN_INTERVAL_SEC=2.1  (30 req/min)
# Cerebras Qwen-3-235b: LLM_MIN_INTERVAL_SEC=13.0  (5 req/min)
# Cerebras llama3.1-8b: LLM_MIN_INTERVAL_SEC=2.1   (30 req/min)
# Yerel LM Studio: LLM_MIN_INTERVAL_SEC=0
_last_call_time: float = 0.0
_MIN_INTERVAL_SEC: float = float(os.getenv("LLM_MIN_INTERVAL_SEC", "2.1"))


def _call_lm_studio(
    system: str,
    user: str,
    model: str = _DEFAULT_MODEL,
    max_tokens: int = POLICY.extraction_max_tokens,
    timeout: int = POLICY.extraction_timeout_sec,
    temperature: float = 0.05,
) -> Optional[str]:
    """LM Studio'ya HTTP istek atar, ham yanıt metnini döner."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "max_tokens":  max_tokens,
        "temperature": temperature,
        "stream":      False,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "python-httpx/0.27.0",
    }
    api_key = _get_lm_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    url = _get_lm_url()
    # Rate limiting — Groq ve benzeri bulut servisler için
    global _last_call_time
    elapsed = time.time() - _last_call_time
    wait_needed = _MIN_INTERVAL_SEC - elapsed
    if wait_needed > 0:
        time.sleep(wait_needed)
    _last_call_time = time.time()

    logger.debug(f"LLM istek URL: {url} | key: {'set' if api_key else 'NONE'}")
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            usage = result.get("usage", {})
            if usage:
                logger.debug(
                    f"LM Studio token: prompt={usage.get('prompt_tokens','-')} "
                    f"completion={usage.get('completion_tokens','-')} "
                    f"total={usage.get('total_tokens','-')}"
                )
            return result["choices"][0]["message"]["content"]
    except urllib.error.URLError as e:
        logger.warning(f"LM Studio bağlantı hatası: {e}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        logger.warning(f"LM Studio yanıt parse hatası: {e}")
        return None
    except Exception as e:
        logger.warning(f"LM Studio beklenmedik hata: {e}")
        return None


# ------------------------------------------------------------------
# JSON parse yardımcısı
# ------------------------------------------------------------------

def _parse_json_array(text: str) -> list[dict]:
    """
    LLM yanıtından JSON array çıkarır.
    LLM bazen markdown code fence veya açıklama metni ekler — bunları temizler.
    """
    if not text:
        return []
    # Markdown code fence temizle
    text = re.sub(r"```(?:json)?", "", text).strip()
    # İlk [ ... ] bloğunu bul
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if not m:
        return []
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        # Trailing comma fix deneyi
        cleaned = re.sub(r",\s*([}\]])", r"\1", m.group())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return []


# ------------------------------------------------------------------
# Ana extraction sınıfı
# ------------------------------------------------------------------

class KUBExtractor:
    """
    Bir KÜB JSON'undaki 4.3 / 4.5 bölümlerinden ilaç etkileşimlerini çıkarır.

    Kullanım (IngestionPipeline içinde):
        extractor = KUBExtractor()
        interactions = extractor.extract(identity, sections)
    """

    def __init__(self, model: str = _DEFAULT_MODEL):
        self.model = model

    def extract(
        self,
        identity,           # DrugIdentity
        sections: dict[str, str],
    ) -> list[DrugInteraction]:
        """
        LLM'e 4.3 + 4.5 gönderir, structured DrugInteraction listesi döner.

        Adımlar:
          1. LLM çağrısı
          2. JSON parse
          3. Pydantic validation (hatalı kayıt drop)
          4. severity=unknown olanlar için retry
          5. NameResolver ile drug_b_canonical doldur
          6. confidence ata
        """
        if not sections.get("4.3") and not sections.get("4.5"):
            logger.debug(f"KUBExtractor: {identity.display_name} — 4.3/4.5 boş, atlanıyor")
            return []

        s45 = (sections.get("4.5") or "").strip()
        if len(s45) > POLICY.extraction_window_chars:
            interactions = self._extract_with_windows(identity, sections, s45)
        else:
            user_prompt = _build_user_prompt(identity.display_name, sections)
            raw_text = self._call_with_retry(user_prompt)
            if raw_text is None:
                logger.warning(f"KUBExtractor: {identity.display_name} — LLM erişilemedi")
                return []
            interactions = self._parse_and_validate(raw_text)

        # severity=unknown olanlar için tek retry
        unknown_items = [iw for iw in interactions if iw.is_unknown()]
        if unknown_items and len(unknown_items) < len(interactions):
            interactions = self._retry_unknowns(identity, interactions, unknown_items, sections)

        # İlaç sınıfı tespiti + NameResolver ile canonical_id doldur
        try:
            from src.core.name_resolver import get_resolver
            resolver = get_resolver()
            for iw in interactions:
                if is_drug_class(iw.drug_b_raw):
                    iw.is_drug_class = True
                    continue  # sınıf isimleri resolve edilmez
                match = resolver.resolve_one(iw.drug_b_raw)
                if match:
                    iw.drug_b_canonical = match.canonical_id
        except Exception as e:
            logger.debug(f"KUBExtractor: NameResolver hatası — {e}")

        # confidence ata
        for iw in interactions:
            iw.confidence = 0.3 if iw.is_unknown() else 1.0

        drug_class_count = sum(1 for i in interactions if i.is_drug_class)

        logger.info(
            f"KUBExtractor: {identity.display_name} → "
            f"{len(interactions)} etkileşim "
            f"({sum(1 for i in interactions if not i.is_unknown())} known, "
            f"{sum(1 for i in interactions if i.is_unknown())} unknown, "
            f"{drug_class_count} sinif)"
        )
        return interactions

    # ------------------------------------------------------------------
    # İç yardımcılar
    # ------------------------------------------------------------------

    def _extract_with_windows(
        self,
        identity,
        sections: dict[str, str],
        s45_full: str,
    ) -> list[DrugInteraction]:
        """
        Section 4.5 extraction_window_chars'tan uzunsa pencere pencere işler.
        Her pencereden gelen etkileşimler drug_b_raw adına göre birleştirilir.
        Çakışmada daha yüksek severity korunur.
        """
        windows = _make_windows(s45_full)
        logger.info(
            f"KUBExtractor sliding window: {identity.display_name} — "
            f"4.5 uzunluğu {len(s45_full)} char, {len(windows)} pencere"
        )

        severity_order = ["contraindicated", "severe", "moderate", "mild", "unknown"]

        merged: dict[str, DrugInteraction] = {}  # drug_b_raw.lower() → best interaction

        for i, window in enumerate(windows, 1):
            prompt = _build_user_prompt(identity.display_name, sections, s45_window=window)
            raw_text = self._call_with_retry(prompt)
            if raw_text is None:
                logger.warning(f"KUBExtractor window {i}/{len(windows)}: LLM erişilemedi, atlanıyor")
                continue

            window_interactions = self._parse_and_validate(raw_text)
            logger.debug(f"KUBExtractor window {i}/{len(windows)}: {len(window_interactions)} etkileşim")

            for iw in window_interactions:
                key = iw.drug_b_raw.lower()
                if key not in merged:
                    merged[key] = iw
                else:
                    existing = merged[key]
                    existing_rank = severity_order.index(existing.severity) if existing.severity in severity_order else 99
                    new_rank     = severity_order.index(iw.severity) if iw.severity in severity_order else 99
                    if new_rank < existing_rank:
                        merged[key] = iw

        interactions = list(merged.values())
        logger.info(
            f"KUBExtractor sliding window tamamlandı: {identity.display_name} — "
            f"{len(interactions)} benzersiz etkileşim ({len(windows)} pencere)"
        )
        return interactions

    def _call_with_retry(
        self, user_prompt: str, system: str = _SYSTEM_PROMPT
    ) -> Optional[str]:
        """İlk deneme + max_retries kadar tekrar dener (bağlantı hatası için).
        extraction_max_retries=0 → tek deneme (retry yok).
        extraction_max_retries=N → 1 ilk deneme + N retry = toplam N+1 deneme.
        """
        max_attempts = POLICY.extraction_max_retries + 1  # en az 1 deneme
        for attempt in range(1, max_attempts + 1):
            result = _call_lm_studio(
                system=system,
                user=user_prompt,
                model=self.model,
                max_tokens=POLICY.extraction_max_tokens,   # call-time oku (sweep monkey-patch için)
                timeout=POLICY.extraction_timeout_sec,
            )
            if result is not None:
                return result
            if attempt < max_attempts:
                wait = 2 ** attempt
                logger.debug(f"KUBExtractor retry {attempt}/{max_attempts-1} — {wait}s bekleniyor")
                time.sleep(wait)
        return None

    def _parse_and_validate(self, raw_text: str) -> list[DrugInteraction]:
        """JSON parse + Pydantic validation; hatalı kayıtlar drop edilir."""
        raw_list = _parse_json_array(raw_text)
        result: list[DrugInteraction] = []
        for item in raw_list:
            try:
                # LLM bazen farklı field adları kullanır — normalize et
                item = _normalize_raw_item(item)
                r = _RawInteraction(**item)
                result.append(DrugInteraction(
                    drug_b_raw=r.drug_b,
                    severity=r.severity,
                    source_section=r.section,
                    mechanism=r.mechanism,
                ))
            except (ValidationError, TypeError) as e:
                logger.debug(f"KUBExtractor: geçersiz kayıt atlandı — {item} | {e}")
        return result

    def _retry_unknowns(
        self,
        identity,
        all_interactions: list[DrugInteraction],
        unknown_items: list[DrugInteraction],
        sections: dict[str, str],
    ) -> list[DrugInteraction]:
        """
        severity=unknown kalan etkileşimler için tek ekstra LLM çağrısı.
        Unknown ilaç listesini tekrar gönderir, sadece severity sorulur.
        """
        unknown_names = ", ".join(iw.drug_b_raw for iw in unknown_items)
        retry_user = (
            f"Drug: {identity.display_name}\n"
            f"These interactions had unknown severity: {unknown_names}\n"
            f"Context: {sections.get('4.5','')[:800]}\n"
            f"Assign correct severity for each. Return JSON array only."
        )
        raw_retry = _call_lm_studio(
            system=_RETRY_SEVERITY_PROMPT,
            user=retry_user,
            model=self.model,
            max_tokens=256,
            timeout=60,
        )
        if not raw_retry:
            return all_interactions

        retry_parsed = self._parse_and_validate(raw_retry)
        if not retry_parsed:
            return all_interactions

        # Retry sonuçlarını mevcut listeyle birleştir
        retry_map = {r.drug_b_raw.lower(): r for r in retry_parsed}
        updated: list[DrugInteraction] = []
        for iw in all_interactions:
            if iw.is_unknown() and iw.drug_b_raw.lower() in retry_map:
                r = retry_map[iw.drug_b_raw.lower()]
                if not r.is_unknown():
                    iw.severity = r.severity
                    logger.debug(f"KUBExtractor retry: {iw.drug_b_raw} → {r.severity}")
            updated.append(iw)
        return updated
