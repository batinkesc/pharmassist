"""
DrugMention → INTERACTS_WITH dönüştürücü.

LLM rebuild sonrası MENTIONS_INTERACTION olarak kalan kayıtları inceler:
  1. Çöp (cümle parçası, ilaç sınıfı, OCR gürültüsü) olanları filtreler
  2. Geçerli ilaç adlarını Drug node'larıyla eşleştirir (INN + normalize)
  3. Eşleşen DrugMention'ları INTERACTS_WITH'e dönüştürür
  4. Corpus dışı olanları DrugMention olarak bırakır

Kullanım:
    .venv/Scripts/python scripts/resolve_drug_mentions.py
    .venv/Scripts/python scripts/resolve_drug_mentions.py --dry-run
    .venv/Scripts/python scripts/resolve_drug_mentions.py --min-confidence 0.8
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger
from src.graph.neo4j_client import run_query
from src.graph.kub_to_graph import _inn_tokens
from src.data.normalization import normalize_drug_name

# ---------------------------------------------------------------------------
# Çöp filtresi
# ---------------------------------------------------------------------------

# Bu kelimeler mention başında veya içinde → ilaç adı değil, cümle parçası
_GARBAGE_STARTS = re.compile(
    r'^(ayrıca|ayrca|bunun|bunları|bu ilac|diğer|diger|bazı|bazi|'
    r'birlikte|kombine|eşzamanlı|eszamanli|özellikle|ozellikle|'
    r'proton|güçlü|guclu|oral|sistemik|topikal|intravenoz|iv |im )',
    re.IGNORECASE,
)

# Bu kalıplar → ilaç sınıfı veya koşul (DrugMention olarak kalsın)
_DRUG_CLASS = re.compile(
    r'(inhibitör|inhibitor|antagonist|agonist|blok[eö]r|blocker|'
    r'analitler|anestezi|antibiyot|antifung|antiviral|antihiper|'
    r'diüretik|diuretik|hormon|vitamin|mineral|kortikoster|'
    r'immüno|immuno|enzim|resept[oö]r|ler$|lar$|ler\b|lar\b)',
    re.IGNORECASE,
)

# Cümle parçası işaretleri
_SENTENCE_CLUES = re.compile(
    r'(ile$|ile\b|lerl|larla|\bve\b|\bveya\b|\bolan\b|\biçin\b|'
    r'\bkullan|\btedavi|\bhastal|\bdurumla|\bnedeni|\bgibi\b|'
    r"'[a-zçğışöü]|'[a-zçğışöü])",
    re.IGNORECASE,
)


def is_valid_drug_mention(name: str) -> bool:
    """Gerçek bir ilaç adı mı yoksa cümle parçası/sınıf mı?"""
    name = name.strip()
    if len(name) < 4 or len(name) > 50:
        return False
    # Çok fazla boşluk = cümle parçası
    if name.count(' ') > 2:
        return False
    if _GARBAGE_STARTS.search(name):
        return False
    if _SENTENCE_CLUES.search(name):
        return False
    return True


def is_drug_class(name: str) -> bool:
    """İlaç sınıfı mı? (DrugMention olarak anlamlı, Drug node eşleştirmesi değil)"""
    return bool(_DRUG_CLASS.search(name))


# ---------------------------------------------------------------------------
# Türkçe çekim eki soyma (INN eşleştirmesi için)
# ---------------------------------------------------------------------------

_TR_SUFFIXES = [
    'lerin', 'larin', 'lerin', 'larin',
    'inin', 'unun', 'ünün', 'nın', 'nin', 'nun', 'nün',
    'ile', 'ile', 'den', 'dan', 'ten', 'tan',
    'de', 'da', 'te', 'ta', 'ye', 'ya', 'e', 'a',
    'ler', 'lar', 'in', 'un', 'ün', 'ın',
]


def strip_turkish_suffix(word: str) -> str:
    """Türkçe çekim ekini soyar: 'varfarine' → 'varfarin'"""
    low = word.lower()
    for suf in _TR_SUFFIXES:
        if low.endswith(suf) and len(low) - len(suf) >= 5:
            return low[: len(low) - len(suf)]
    return low


# ---------------------------------------------------------------------------
# Drug index oluşturma
# ---------------------------------------------------------------------------

def build_drug_index() -> tuple[dict, dict]:
    """
    İki index döner:
      inn_index  : {inn_token → drug_name}  — etken_madde INN tokenları
      norm_index : {normalized_name → drug_name}  — normalize ilaç adları + ilk kelime
    """
    drugs = run_query(
        "MATCH (d:Drug) RETURN d.name AS name, coalesce(d.etken_madde,'') AS em"
    )
    inn_index: dict[str, str] = {}
    norm_index: dict[str, str] = {}

    for d in drugs:
        orig = d["name"]
        norm = normalize_drug_name(orig).lower()
        norm_index[norm] = orig

        # İlk kelime (marka prefix, min 5 char)
        first = norm.split()[0]
        if len(first) >= 5 and first not in norm_index:
            norm_index[first] = orig

        # INN tokenları
        for tok in _inn_tokens(d["em"]):
            if tok not in inn_index:
                inn_index[tok] = orig

    logger.info(f"Drug index: {len(norm_index)} normalize ad, {len(inn_index)} INN token")
    return inn_index, norm_index


# ---------------------------------------------------------------------------
# Eşleştirme
# ---------------------------------------------------------------------------

def find_drug_node(
    mention: str,
    inn_index: dict,
    norm_index: dict,
    exclude: str = "",
) -> tuple[str | None, str]:
    """
    mention → (drug_name, method) döner. Bulunamazsa (None, "").

    Yöntemler (güven sırasıyla):
      1. normalize tam eşleşme
      2. suffix soyulmuş normalize eşleşme
      3. INN token tam eşleşmesi
      4. INN token suffix-soyulmuş eşleşmesi
    """
    raw_low = mention.lower().strip()
    norm = normalize_drug_name(mention).lower()
    stripped = strip_turkish_suffix(norm.split()[0])  # ilk kelime suffix soyulmuş

    # 1. Tam normalize eşleşme
    if norm in norm_index:
        cand = norm_index[norm]
        if cand != exclude:
            return cand, "exact_norm"

    # 2. Suffix soyulmuş normalize
    if stripped in norm_index:
        cand = norm_index[stripped]
        if cand != exclude:
            return cand, "suffix_stripped"

    # 3. INN token tam eşleşmesi (mention kelimesi INN token ile birebir)
    mention_tokens = set(raw_low.split())
    for tok, drug in inn_index.items():
        if tok in mention_tokens and drug != exclude:
            return drug, "inn_exact"

    # 4. INN token suffix-soyulmuş eşleşmesi
    stripped_tokens = {strip_turkish_suffix(w) for w in mention.split()}
    for tok, drug in inn_index.items():
        if tok in stripped_tokens and drug != exclude:
            return drug, "inn_suffix"

    return None, ""


# ---------------------------------------------------------------------------
# Neo4j yazma
# ---------------------------------------------------------------------------

_VALID_SEV = {"contraindicated", "severe", "moderate", "mild", "unknown"}


def convert_to_interacts_with(
    src_drug: str,
    drug_b: str,
    severity: str,
    section: str,
    method: str,
    dry_run: bool,
) -> None:
    sev = severity if severity in _VALID_SEV else "unknown"
    if dry_run:
        logger.debug(
            f"  [DRY] {src_drug[:28]:28s} --[{sev}]--> {drug_b[:28]:28s} ({section}, {method})"
        )
        return

    run_query(
        """
        MATCH (a:Drug {name: $src})
        MATCH (b:Drug {name: $tgt})
        MERGE (a)-[r:INTERACTS_WITH]->(b)
        ON CREATE SET r.severity     = $sev,
                      r.kaynak_madde = $sec,
                      r.kaynak       = 'mention_resolved',
                      r.method       = $method
        ON MATCH  SET r.severity = CASE
                          WHEN r.severity = 'unknown' AND $sev <> 'unknown' THEN $sev
                          ELSE r.severity END,
                      r.method   = $method
        """,
        {"src": src_drug, "tgt": drug_b, "sev": sev, "sec": section, "method": method},
    )


# ---------------------------------------------------------------------------
# Ana işlev
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    inn_index, norm_index = build_drug_index()

    # Tüm MENTIONS_INTERACTION kayıtları
    rows = run_query(
        """
        MATCH (src:Drug)-[r:MENTIONS_INTERACTION]->(m:DrugMention)
        RETURN src.name AS src_drug, m.name AS mention,
               r.severity AS sev, r.kaynak_madde AS sec
        """
    )
    logger.info(f"Toplam MENTIONS_INTERACTION: {len(rows)}")

    stats = {
        "garbage":    0,
        "drug_class": 0,
        "converted":  0,
        "no_match":   0,
    }
    method_counts: dict[str, int] = {}

    for row in rows:
        src   = row["src_drug"]
        ment  = row["mention"].strip()
        sev   = row["sev"] or "unknown"
        sec   = row["sec"] or "4.5"

        # Filtre: çöp
        if not is_valid_drug_mention(ment):
            stats["garbage"] += 1
            if args.verbose:
                logger.debug(f"  [GARBAGE] {ment[:50]}")
            continue

        # Filtre: ilaç sınıfı — eşleştirme yapma, DrugMention'da kalsın
        if is_drug_class(ment):
            stats["drug_class"] += 1
            if args.verbose:
                logger.debug(f"  [CLASS]   {ment[:50]}")
            continue

        # Eşleştir
        drug_b, method = find_drug_node(ment, inn_index, norm_index, exclude=src)

        if drug_b:
            convert_to_interacts_with(src, drug_b, sev, sec, method, args.dry_run)
            stats["converted"] += 1
            method_counts[method] = method_counts.get(method, 0) + 1
            if args.verbose:
                logger.debug(
                    f"  [OK:{method:14s}] {ment[:20]:20s} -> {drug_b[:30]:30s} [{sev}]"
                )
        else:
            stats["no_match"] += 1

    # Özet
    logger.info("=" * 60)
    logger.info(f"TAMAMLANDI{'  [DRY RUN]' if args.dry_run else ''}")
    logger.info(f"  Çöp / cümle parçası   : {stats['garbage']}")
    logger.info(f"  İlaç sınıfı (kaldı)   : {stats['drug_class']}")
    logger.info(f"  Dönüştürüldü          : {stats['converted']}")
    logger.info(f"  Corpus dışı (kaldı)   : {stats['no_match']}")
    logger.info(f"  Yöntem dağılımı       : {method_counts}")

    if not args.dry_run:
        dist = run_query(
            "MATCH ()-[r:INTERACTS_WITH]->() RETURN r.severity AS s, count(*) AS c ORDER BY c DESC"
        )
        logger.info("Güncel INTERACTS_WITH dağılımı:")
        total = sum(d["c"] for d in dist)
        for d in dist:
            logger.info(f"  {d['s']:20s}: {d['c']}")
        logger.info(f"  TOPLAM              : {total}")


if __name__ == "__main__":
    main()
