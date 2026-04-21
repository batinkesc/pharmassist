"""
KÜB 4.3 + 4.4 + 4.5 bölümlerinden LLM tabanlı INTERACTS_WITH yeniden inşası.

Her ilaç için bu üç bölümün metni LM Studio yerel LLM'ine gönderilir;
model yapılandırılmış JSON çıktısı üretir → Neo4j'e yazılır.

Kullanım:
    .venv/Scripts/python scripts/rebuild_interactions.py
    .venv/Scripts/python scripts/rebuild_interactions.py --dry-run
    .venv/Scripts/python scripts/rebuild_interactions.py --drug LUSTRAL_50_MG_CENTIKLI_FILM_KA
    .venv/Scripts/python scripts/rebuild_interactions.py --limit 10 --dry-run
    .venv/Scripts/python scripts/rebuild_interactions.py --model mistralai/mistral-7b-instruct-v0.3
    .venv/Scripts/python scripts/rebuild_interactions.py --clear-existing
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger

LOG_FILE = ROOT / "logs" / "rebuild_interactions_full.log"
logger.add(str(LOG_FILE), encoding="utf-8", level="DEBUG", mode="a")
from src.graph.neo4j_client import run_query

# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
DEFAULT_MODEL  = "qwen/qwen2.5-coder-14b-instruct"

SYSTEM_PROMPT = (
    'Extract drug-drug interactions from Turkish KUB text. '
    'Return ONLY a JSON array. Each item: {"drug_b":"<name>","severity":"contraindicated|severe|moderate|mild|unknown","section":"4.3|4.5"}. '
    'Rules: exact drug/INN names only (no "some drugs"); drug class names OK (e.g. "MAO inhibitörleri"); '
    'contraindicated=kontrendike; severe=ciddi/hayati; moderate=dikkatli/doz ayarı; mild=hafif/önemsiz. '
    'No markdown, no explanation, JSON array only.'
)


def build_user_prompt(ilac_adi: str, sections: dict[str, str]) -> str:
    """LLM'e gönderilecek kullanıcı mesajını oluşturur — kısa prompt, düşük token."""
    parts = [f"Drug: {ilac_adi}"]
    # 4.3 kısa tut (kontrendikasyonlar özlü)
    s43 = sections.get("4.3", "").strip()
    if s43:
        parts.append(f"[4.3]{s43[:500]}")
    # 4.5 ana kaynak — biraz daha uzun
    s45 = sections.get("4.5", "").strip()
    if s45:
        parts.append(f"[4.5]{s45[:900]}")
    parts.append("Output interactions JSON:")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# LM Studio API çağrısı
# ---------------------------------------------------------------------------

def call_lm_studio(
    user_msg: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 512,
    temperature: float = 0.05,
    timeout: int = 180,
) -> Optional[str]:
    """LM Studio'ya istek gönderir, ham metin yanıtı döner."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        "max_tokens":  max_tokens,
        "temperature": temperature,
        "stream":      False,
    }
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        LM_STUDIO_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.URLError as e:
        logger.error(f"LM Studio bağlantı hatası: {e}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"LM Studio yanıt ayrıştırma hatası: {e}")
        return None


# ---------------------------------------------------------------------------
# JSON ayrıştırma (model bazen markdown code block içinde döner)
# ---------------------------------------------------------------------------

def parse_llm_json(raw: str) -> list[dict]:
    """LLM çıktısından JSON array ayrıştırır; başarısız olursa [] döner."""
    if not raw:
        return []

    # Markdown code block varsa çıkar
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if code_block:
        raw = code_block.group(1).strip()
    else:
        # En dış [ ... ] bloğunu bul
        start = raw.find("[")
        end   = raw.rfind("]")
        if start != -1 and end != -1:
            raw = raw[start:end+1]

    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        logger.warning(f"LLM JSON array değil, tip: {type(data)}")
        return []
    except json.JSONDecodeError as e:
        logger.warning(f"JSON ayrıştırma hatası: {e} | İlk 200 karakter: {raw[:200]}")
        return []


# ---------------------------------------------------------------------------
# Neo4j: ilaç adı → node eşleştirme
# ---------------------------------------------------------------------------

def _all_drug_names() -> dict[str, str]:
    """Neo4j'deki tüm Drug.name değerlerini {lowercase: orijinal} dict olarak döner."""
    rows = run_query("MATCH (d:Drug) RETURN d.name AS name")
    return {r["name"].lower(): r["name"] for r in rows}


def _find_drug_node(
    mention: str,
    drug_index: dict[str, str],
    exclude: str = "",
) -> Optional[str]:
    """
    mention → Neo4j Drug node adı döner; bulunamazsa None.
    Strateji (sırayla):
      1. Tam lowercase eşleşme
      2. mention, drug adının başında geçiyor (prefix)
      3. drug adı, mention'ı içeriyor (contains — min 6 karakter)
      4. Neo4j etken_madde contains araması
    """
    mention_lower = mention.lower().strip()
    if not mention_lower or len(mention_lower) < 4:
        return None

    # 1. Tam eşleşme
    if mention_lower in drug_index:
        result = drug_index[mention_lower]
        return result if result != exclude else None

    # 2. Prefix: drug adı mention ile başlıyor
    for key, orig in drug_index.items():
        if key.startswith(mention_lower) and orig != exclude:
            return orig

    # 3. Contains (her iki yönde, minimum 6 karakter)
    if len(mention_lower) >= 6:
        for key, orig in drug_index.items():
            if orig == exclude:
                continue
            if mention_lower in key or key.startswith(mention_lower[:6]):
                return orig

    # 4. Neo4j etken_madde araması
    rows = run_query(
        """
        MATCH (d:Drug)
        WHERE toLower(coalesce(d.etken_madde,'')) CONTAINS $m
           OR toLower(d.name) CONTAINS $m
        RETURN d.name AS name LIMIT 1
        """,
        {"m": mention_lower},
    )
    if rows and rows[0]["name"] != exclude:
        return rows[0]["name"]

    return None


# ---------------------------------------------------------------------------
# Neo4j yazma
# ---------------------------------------------------------------------------

VALID_SEVERITIES = {"contraindicated", "severe", "moderate", "mild", "unknown"}

_SEVERITY_TR_MAP = {
    "kontrendike": "contraindicated", "kontraendike": "contraindicated",
    "kontrendikedir": "contraindicated", "kullanılmamalı": "contraindicated",
    "ciddi": "severe", "hayati": "severe", "ölümcül": "severe",
    "tehlikeli": "severe", "şiddetli": "severe",
    "moderate": "moderate", "orta": "moderate", "dikkatli": "moderate",
    "hafif": "mild", "minimal": "mild", "önemsiz": "mild",
    "bilinmiyor": "unknown", "belirtilmemiş": "unknown",
}

def _normalize_severity(raw: str) -> str:
    """LLM çıktısındaki Türkçe/karma severity değerini standartlaştırır."""
    s = raw.lower().strip()
    if s in VALID_SEVERITIES:
        return s
    for tr_key, en_val in _SEVERITY_TR_MAP.items():
        if tr_key in s:
            return en_val
    return "unknown"


def upsert_interaction(
    drug_a: str,
    drug_b_node: str,
    severity: str,
    source_section: str,
    note: str = "",
    dry_run: bool = False,
) -> None:
    """INTERACTS_WITH ilişkisi oluşturur/günceller."""
    severity = _normalize_severity(severity)

    if dry_run:
        logger.debug(
            f"  [DRY] {drug_a[:30]} --[{severity}]--> {drug_b_node[:30]} ({source_section})"
        )
        return

    run_query(
        """
        MATCH (a:Drug {name: $drug_a})
        MATCH (b:Drug {name: $drug_b})
        MERGE (a)-[r:INTERACTS_WITH]->(b)
        ON CREATE SET r.severity       = $severity,
                      r.kaynak_madde   = $source_section,
                      r.kaynak         = 'llm_rebuild',
                      r.note           = $note
        ON MATCH  SET r.severity       = CASE
                          WHEN r.severity = 'unknown' OR $severity <> 'unknown'
                          THEN $severity
                          ELSE r.severity END,
                      r.kaynak_madde   = $source_section,
                      r.kaynak         = 'llm_rebuild',
                      r.note           = $note
        """,
        {
            "drug_a":         drug_a,
            "drug_b":         drug_b_node,
            "severity":       severity,
            "source_section": source_section,
            "note":           note[:200] if note else "",
        },
    )


def upsert_mention(
    drug_a: str,
    mention: str,
    severity: str,
    source_section: str,
    dry_run: bool = False,
) -> None:
    """Eşleşmeyen ilaç adları için DrugMention node oluşturur."""
    if dry_run:
        logger.debug(f"  [DRY MENTION] {drug_a[:30]} → {mention[:30]} ({severity})")
        return

    run_query(
        """
        MERGE (m:DrugMention {name: $mention})
        WITH m
        MATCH (d:Drug {name: $drug_a})
        MERGE (d)-[r:MENTIONS_INTERACTION]->(m)
        ON CREATE SET r.severity       = $severity,
                      r.kaynak_madde   = $source_section,
                      r.kaynak         = 'llm_rebuild'
        ON MATCH  SET r.severity       = $severity
        """,
        {
            "drug_a":         drug_a,
            "mention":        mention.strip()[:100],
            "severity":       severity if severity in VALID_SEVERITIES else "unknown",
            "source_section": source_section,
        },
    )


# ---------------------------------------------------------------------------
# İlaç JSON okuma
# ---------------------------------------------------------------------------

def load_sections(json_path: Path) -> tuple[str, dict[str, str]]:
    """JSON dosyasından (ilac_adi, {madde_no: icerik}) döner."""
    data   = json.loads(json_path.read_text(encoding="utf-8"))
    ilac   = data.get("ilac_adi", json_path.stem)
    sects  = {}
    for chunk in data.get("chunks", []):
        mno = chunk.get("madde_no", "")
        if mno in ("4.3", "4.4", "4.5"):
            # Aynı bölüm birden fazla chunk'a bölünmüşse birleştir
            sects[mno] = sects.get(mno, "") + "\n" + chunk.get("icerik", "")
    return ilac, sects


# ---------------------------------------------------------------------------
# Ana işleme
# ---------------------------------------------------------------------------

def process_drug(
    json_path: Path,
    drug_index: dict[str, str],
    model: str,
    dry_run: bool,
    verbose: bool = False,
) -> dict:
    """Tek bir ilaç JSON dosyasını işler. Özet dict döner."""
    ilac_adi, sections = load_sections(json_path)

    if not any(sections.get(s) for s in ("4.3", "4.4", "4.5")):
        logger.warning(f"  {ilac_adi}: 4.3/4.4/4.5 bölümü bulunamadı, atlanıyor")
        return {"drug": ilac_adi, "skipped": True, "extractions": 0}

    user_msg = build_user_prompt(ilac_adi, sections)

    # LLM çağrısı (3 deneme)
    raw = None
    for attempt in range(3):
        raw = call_lm_studio(user_msg, model=model)
        if raw:
            break
        logger.warning(f"  {ilac_adi}: LLM çağrısı başarısız (deneme {attempt+1}/3)")
        time.sleep(2)

    if not raw:
        return {"drug": ilac_adi, "skipped": True, "extractions": 0, "error": "llm_fail"}

    interactions = parse_llm_json(raw)

    if verbose:
        logger.debug(f"  {ilac_adi}: LLM {len(interactions)} etkileşim çıkardı")

    matched    = 0
    unmatched  = 0
    skipped    = 0

    for item in interactions:
        drug_b_mention = item.get("drug_b", "").strip()
        severity       = item.get("severity", "unknown").lower()
        source_section = item.get("source_section") or item.get("section", "4.5")
        note           = item.get("note", "")

        if not drug_b_mention or len(drug_b_mention) < 4:
            skipped += 1
            continue

        drug_b_node = _find_drug_node(drug_b_mention, drug_index, exclude=ilac_adi)

        if drug_b_node:
            upsert_interaction(
                ilac_adi, drug_b_node, severity, source_section, note, dry_run
            )
            matched += 1
        else:
            upsert_mention(ilac_adi, drug_b_mention, severity, source_section, dry_run)
            unmatched += 1

    logger.info(
        f"  {ilac_adi[:40]:40s} | "
        f"çıkarılan:{len(interactions):3d} | "
        f"matched:{matched:3d} | "
        f"mention:{unmatched:3d} | "
        f"atlandı:{skipped:2d}"
    )
    return {
        "drug":        ilac_adi,
        "extractions": len(interactions),
        "matched":     matched,
        "unmatched":   unmatched,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="KÜB 4.3+4.4+4.5 bölümlerinden LLM tabanlı INTERACTS_WITH yeniden inşası"
    )
    parser.add_argument("--dry-run",       action="store_true", help="Yazma yapmadan çalıştır")
    parser.add_argument("--drug",          type=str,  default=None, help="Tek bir ilaç (JSON dosya gövdesi)")
    parser.add_argument("--limit",         type=int,  default=None, help="İşlenecek maksimum ilaç sayısı")
    parser.add_argument("--model",         type=str,  default=DEFAULT_MODEL, help="LM Studio model ID")
    parser.add_argument("--clear-existing",action="store_true", help="Mevcut llm_rebuild kaynaklı ilişkileri temizle")
    parser.add_argument("--clear-all",    action="store_true", help="TÜM INTERACTS_WITH ilişkilerini sil (tam sıfırlama)")
    parser.add_argument("--parsed-dir",    type=str,  default="data/parsed_json")
    parser.add_argument("--verbose",       action="store_true")
    args = parser.parse_args()

    parsed_dir = ROOT / args.parsed_dir

    # LM Studio bağlantı kontrolü
    try:
        req = urllib.request.urlopen("http://localhost:1234/v1/models", timeout=5)
        models_data = json.loads(req.read())
        loaded_ids  = [m["id"] for m in models_data.get("data", [])]
        if args.model not in loaded_ids:
            logger.warning(f"Model '{args.model}' LM Studio'da yüklü değil!")
            logger.warning(f"Mevcut modeller: {loaded_ids}")
            # Fallback: ilk uygun modeli seç
            fallback = next((m for m in loaded_ids if "embed" not in m.lower()), None)
            if fallback:
                logger.warning(f"Fallback: '{fallback}' kullanılacak")
                args.model = fallback
            else:
                logger.error("Uygun model bulunamadı. LM Studio'yu kontrol et.")
                sys.exit(1)
        logger.info(f"LM Studio bağlantısı OK — Model: {args.model}")
    except Exception as e:
        logger.error(f"LM Studio bağlanamadı: {e}")
        logger.error("LM Studio'nun açık ve http://localhost:1234 adresinde çalıştığından emin ol.")
        sys.exit(1)

    # İlişki temizleme
    if not args.dry_run:
        if args.clear_all:
            count = run_query(
                "MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) AS cnt"
            )[0]["cnt"]
            # Büyük veri setinde toplu silme (10k'lık batch)
            deleted = 0
            while True:
                result = run_query(
                    "MATCH ()-[r:INTERACTS_WITH]->() WITH r LIMIT 10000 DELETE r RETURN count(*) AS cnt"
                )
                batch = result[0]["cnt"] if result else 0
                deleted += batch
                if batch == 0:
                    break
            logger.info(f"Temizlendi: {count} INTERACTS_WITH ilişkisi silindi (tam sıfırlama)")
        elif args.clear_existing:
            count = run_query(
                "MATCH ()-[r:INTERACTS_WITH {kaynak:'llm_rebuild'}]->() RETURN count(r) AS cnt"
            )[0]["cnt"]
            run_query("MATCH ()-[r:INTERACTS_WITH {kaynak:'llm_rebuild'}]->() DELETE r")
            logger.info(f"Temizlendi: {count} llm_rebuild ilişkisi silindi")

    # Neo4j drug index yükle
    logger.info("Neo4j Drug node'ları indeksleniyor...")
    drug_index = _all_drug_names()
    logger.info(f"{len(drug_index)} Drug node'u indekslendi")

    # İşlenecek dosyaları belirle
    if args.drug:
        json_files = list(parsed_dir.glob(f"{args.drug}*.json"))
        if not json_files:
            logger.error(f"'{args.drug}' için JSON dosyası bulunamadı")
            sys.exit(1)
    else:
        json_files = sorted(parsed_dir.glob("*.json"))

    if args.limit:
        json_files = json_files[:args.limit]

    logger.info(f"{len(json_files)} ilaç işlenecek (dry_run={args.dry_run})")

    # İşle
    results = []
    for i, json_path in enumerate(json_files, 1):
        logger.info(f"[{i:3d}/{len(json_files)}] {json_path.stem}")
        try:
            r = process_drug(json_path, drug_index, args.model, args.dry_run, args.verbose)
            results.append(r)
        except Exception as e:
            logger.error(f"  HATA: {json_path.stem}: {e}")
            results.append({"drug": json_path.stem, "error": str(e)})

    # Özet
    total_ex  = sum(r.get("extractions", 0) for r in results)
    total_m   = sum(r.get("matched", 0)     for r in results)
    total_u   = sum(r.get("unmatched", 0)   for r in results)
    skipped_c = sum(1 for r in results if r.get("skipped"))
    errored_c = sum(1 for r in results if r.get("error"))

    logger.info("=" * 60)
    logger.info(f"TAMAMLANDI{'  [DRY RUN]' if args.dry_run else ''}")
    logger.info(f"  İşlenen ilaç    : {len(results)}")
    logger.info(f"  Atlanılan       : {skipped_c}")
    logger.info(f"  Hatalı          : {errored_c}")
    logger.info(f"  Toplam çıkarılan: {total_ex}")
    logger.info(f"  Drug node eşleşti   : {total_m}")
    logger.info(f"  DrugMention (eşleşmedi): {total_u}")

    if not args.dry_run:
        dist = run_query(
            "MATCH ()-[r:INTERACTS_WITH]->() RETURN r.severity AS sev, count(*) AS cnt ORDER BY cnt DESC"
        )
        logger.info("Güncel severity dağılımı:")
        for d in dist:
            logger.info(f"  {d['sev']:20s}: {d['cnt']}")


if __name__ == "__main__":
    main()
