"""
0 INTERACTS_WITH olan ilaçlar için artırılmış parametrelerle LLM yeniden çalıştırma.

Değişiklikler (rebuild_interactions.py'a göre):
  - 4.3: 500→800 chars
  - 4.5: 900→2000 chars
  - max_tokens: 512→1024

Kullanım:
    .venv/Scripts/python scripts/retry_zero_interactions.py
    .venv/Scripts/python scripts/retry_zero_interactions.py --dry-run
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger
from src.graph.neo4j_client import run_query

LOG_FILE = ROOT / "logs" / "retry_zero_interactions.log"
logger.add(str(LOG_FILE), encoding="utf-8", level="DEBUG", mode="a")

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
DEFAULT_MODEL  = "qwen/qwen2.5-coder-14b-instruct"

SYSTEM_PROMPT = (
    'Extract drug-drug interactions from Turkish KUB text. '
    'Return ONLY a JSON array. Each item: {"drug_b":"<name>","severity":"contraindicated|severe|moderate|mild|unknown","section":"4.3|4.5"}. '
    'Rules: exact drug/INN names only (no "some drugs"); drug class names OK (e.g. "MAO inhibitörleri"); '
    'contraindicated=kontrendike; severe=ciddi/hayati; moderate=dikkatli/doz ayarı; mild=hafif/önemsiz. '
    'No markdown, no explanation, JSON array only.'
)

_SEVERITY_TR_MAP = {
    "kontrendike": "contraindicated",
    "kontrendikedir": "contraindicated",
    "ciddi": "severe",
    "hayati": "severe",
    "önemli": "severe",
    "orta": "moderate",
    "hafif": "mild",
}

_VALID_SEV = {"contraindicated", "severe", "moderate", "mild", "unknown"}


def _normalize_severity(sev: str) -> str:
    if not sev:
        return "unknown"
    low = sev.lower().strip()
    if low in _VALID_SEV:
        return low
    for tr, en in _SEVERITY_TR_MAP.items():
        if tr in low:
            return en
    return "unknown"


def build_user_prompt(ilac_adi: str, sections: dict[str, str]) -> str:
    parts = [f"Drug: {ilac_adi}"]
    s43 = sections.get("4.3", "").strip()
    if s43:
        parts.append(f"[4.3]{s43[:800]}")   # 500 → 800
    s45 = sections.get("4.5", "").strip()
    if s45:
        parts.append(f"[4.5]{s45[:2000]}")  # 900 → 2000
    parts.append("Output interactions JSON:")
    return "\n".join(parts)


def load_sections(json_path: Path) -> tuple[str, dict[str, str]]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    ilac = data.get("ilac_adi", json_path.stem)
    sects: dict[str, str] = {}
    for chunk in data.get("chunks", []):
        mno = chunk.get("madde_no", "")
        if mno in ("4.3", "4.4", "4.5"):
            sects[mno] = sects.get(mno, "") + "\n" + chunk.get("icerik", "")
    return ilac, sects


def call_llm(messages: list, model: str, timeout: int = 180) -> str:
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 1024,     # 512 → 1024
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        LM_STUDIO_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]


def parse_llm_json(raw: str) -> list[dict]:
    # JSON bloku çıkar
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    text = m.group(0) if m else raw
    # Trailing comma fix
    text = re.sub(r",\s*\]", "]", text)
    text = re.sub(r",\s*\}", "}", text)
    try:
        return json.loads(text)
    except Exception as e:
        logger.warning(f"JSON parse hatası: {e} | Ham: {raw[:200]}")
        return []


def build_drug_index() -> dict[str, str]:
    drugs = run_query("MATCH (d:Drug) RETURN d.name AS name")
    index = {}
    for d in drugs:
        norm = d["name"].lower().strip()
        index[norm] = d["name"]
        first_word = norm.split()[0]
        if len(first_word) >= 5 and first_word not in index:
            index[first_word] = d["name"]
    return index


def find_drug(mention: str, index: dict[str, str], exclude: str) -> str | None:
    low = mention.lower().strip()
    if low in index and index[low] != exclude:
        return index[low]
    # İlk kelime eşleşmesi
    first = low.split()[0]
    if first in index and index[first] != exclude:
        return index[first]
    return None


def write_interaction(src: str, tgt: str, sev: str, sec: str, dry_run: bool) -> None:
    if dry_run:
        logger.debug(f"  [DRY] {src[:30]:30s} --[{sev}]--> {tgt[:30]:30s}")
        return
    run_query(
        """
        MATCH (a:Drug {name: $src})
        MATCH (b:Drug {name: $tgt})
        MERGE (a)-[r:INTERACTS_WITH]->(b)
        ON CREATE SET r.severity     = $sev,
                      r.kaynak_madde = $sec,
                      r.kaynak       = 'llm_retry',
                      r.method       = 'llm_retry'
        ON MATCH SET  r.severity = CASE
                          WHEN r.severity = 'unknown' AND $sev <> 'unknown' THEN $sev
                          ELSE r.severity END
        """,
        {"src": src, "tgt": tgt, "sev": sev, "sec": sec},
    )


def write_mention(src: str, mention: str, sev: str, sec: str, dry_run: bool) -> None:
    if dry_run:
        return
    run_query(
        """
        MATCH (a:Drug {name: $src})
        MERGE (m:DrugMention {name: $mention})
        MERGE (a)-[r:MENTIONS_INTERACTION]->(m)
        ON CREATE SET r.severity = $sev, r.kaynak_madde = $sec
        """,
        {"src": src, "mention": mention, "sev": sev, "sec": sec},
    )


def get_zero_relationship_drugs() -> list[str]:
    rows = run_query("""
        MATCH (d:Drug)
        WHERE NOT (d)-[:INTERACTS_WITH]-() AND NOT ()-[:INTERACTS_WITH]->(d)
        RETURN d.name AS name ORDER BY d.name
    """)
    return [r["name"] for r in rows]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    zero_drugs = get_zero_relationship_drugs()
    logger.info(f"0 ilişkili ilaç sayısı: {len(zero_drugs)}")

    drug_index = build_drug_index()
    parsed_dir = ROOT / "data" / "parsed_json"

    stats = {"processed": 0, "skipped": 0, "matched": 0, "mention": 0, "errors": 0}

    for i, drug_name in enumerate(zero_drugs, 1):
        # JSON dosyasını bul
        stem = re.sub(r"[^A-Za-z0-9]", "_", drug_name)[:40]
        candidates = list(parsed_dir.glob(f"{stem}*.json")) or list(
            parsed_dir.glob(f"{''.join(stem.split()[:2])}*.json")
        )
        if not candidates:
            # Daha geniş arama
            words = drug_name.split()[:3]
            pattern = "_".join(re.sub(r"[^A-Za-z0-9]", "_", w) for w in words)
            candidates = list(parsed_dir.glob(f"{pattern}*.json"))

        if not candidates:
            logger.warning(f"[{i}/{len(zero_drugs)}] JSON bulunamadı: {drug_name}")
            stats["skipped"] += 1
            continue

        json_path = candidates[0]
        ilac_adi, sections = load_sections(json_path)

        if not any(sections.get(s) for s in ("4.3", "4.4", "4.5")):
            logger.warning(f"[{i}/{len(zero_drugs)}] Bölüm yok: {drug_name}")
            stats["skipped"] += 1
            continue

        logger.info(f"[{i}/{len(zero_drugs)}] {drug_name}")

        user_msg = build_user_prompt(ilac_adi, sections)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ]

        # LLM çağrısı
        raw = None
        for attempt in range(3):
            try:
                raw = call_llm(messages, args.model)
                break
            except Exception as e:
                logger.warning(f"  Deneme {attempt+1} hata: {e}")
                time.sleep(5)

        if raw is None:
            logger.error(f"  LLM yanıt vermedi: {drug_name}")
            stats["errors"] += 1
            continue

        items = parse_llm_json(raw)
        logger.debug(f"  {drug_name}: {len(items)} etkileşim çıkarıldı")

        matched = 0
        mentioned = 0
        for item in items:
            drug_b = (item.get("drug_b") or "").strip()
            sev = _normalize_severity(item.get("severity", ""))
            sec = item.get("source_section") or item.get("section", "4.5")

            if not drug_b or len(drug_b) < 3:
                continue

            tgt = find_drug(drug_b, drug_index, exclude=drug_name)
            if tgt:
                write_interaction(drug_name, tgt, sev, sec, args.dry_run)
                matched += 1
                stats["matched"] += 1
                if args.verbose:
                    logger.debug(f"    MATCH: {drug_b} → {tgt} [{sev}]")
            else:
                write_mention(drug_name, drug_b, sev, sec, args.dry_run)
                mentioned += 1
                stats["mention"] += 1

        logger.info(
            f"  {drug_name:40s} | matched:{matched:3d} | mention:{mentioned:3d}"
        )
        stats["processed"] += 1

    logger.info("=" * 60)
    logger.info(f"TAMAMLANDI{'  [DRY RUN]' if args.dry_run else ''}")
    logger.info(f"  İşlenen    : {stats['processed']}")
    logger.info(f"  Atlanan    : {stats['skipped']}")
    logger.info(f"  Eşleşen    : {stats['matched']}")
    logger.info(f"  DrugMention: {stats['mention']}")
    logger.info(f"  Hata       : {stats['errors']}")

    if not args.dry_run:
        total = run_query(
            "MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) AS c"
        )[0]["c"]
        zero = run_query(
            """MATCH (d:Drug)
               WHERE NOT (d)-[:INTERACTS_WITH]-() AND NOT ()-[:INTERACTS_WITH]->(d)
               RETURN count(d) AS c"""
        )[0]["c"]
        logger.info(f"  Toplam INTERACTS_WITH: {total}")
        logger.info(f"  Hâlâ 0 ilişkili Drug : {zero}")


if __name__ == "__main__":
    main()
