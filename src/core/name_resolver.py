"""
NameResolver — sistemdeki tek isim çözümleme servisi.

Önceki durum (4 farklı yerde, 4 farklı mantık):
  - graph_retriever.py  : exact → prefix → contains
  - chroma_store.py     : exact normalized → prefix → substring
  - rebuild_interactions: exact → prefix → contains≥6 → Cypher CONTAINS
  - kub_to_graph.py     : INN token match (ilk 120 char, min 8 char)

Yeni durum:
  Tüm kod NameResolver.resolve() çağırır.
  Arama sırası: canonical_id → normalized exact → prefix → INN → fuzzy (difflib)

Nasıl kullanılır:
    from src.core.name_resolver import get_resolver
    resolver = get_resolver()                   # singleton, lazy-load
    matches = resolver.resolve("PLAVIX")        # → [DrugIdentity, ...]
    group   = resolver.resolve_inn_group("klopidogrel")  # → tüm aynı INN'liler
"""

from __future__ import annotations

import difflib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from loguru import logger

from src.core.drug_record import DrugIdentity
from src.data.normalization import normalize_drug_name

# Parsed JSON dizini — buradan registry oluşturulur
_PARSED_JSON_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "parsed_json"

# Fuzzy eşleşme için minimum benzerlik oranı (0-1)
_FUZZY_THRESHOLD = 0.80


class NameResolver:
    """
    Parsed JSON dosyalarından oluşturulan ilaç kaydı (DrugIdentity) üzerinde
    çok katmanlı isim çözümleme yapar.
    """

    def __init__(self, registry: dict[str, DrugIdentity]):
        """
        registry: canonical_id → DrugIdentity eşlemesi.
        build_registry() ile oluşturulur.
        """
        self._by_canonical: dict[str, DrugIdentity] = registry
        self._by_normalized: dict[str, DrugIdentity] = {
            d.normalized_name: d for d in registry.values()
        }

        # INN exact lookup (tam etken_madde string)
        self._by_inn: dict[str, list[DrugIdentity]] = {}
        for d in registry.values():
            self._by_inn.setdefault(d.inn, []).append(d)

        # INN token lookup — "metoprolol suksinat" → "metoprolol" ile de bulunur
        # Token: etken_madde içindeki 4+ harfli kelimeler ayrı ayrı indekslenir
        self._by_inn_token: dict[str, list[DrugIdentity]] = {}
        for d in registry.values():
            if d.inn:
                for token in d.inn.lower().split():
                    if len(token) >= 4:
                        self._by_inn_token.setdefault(token, []).append(d)

        # Fuzzy için tüm normalized adlar + INN tokenları
        self._all_normalized: list[str] = list(self._by_normalized.keys())
        self._all_inn_tokens: list[str] = list(self._by_inn_token.keys())
        self._all: list[DrugIdentity] = list(registry.values())

    # ------------------------------------------------------------------
    # Ana API
    # ------------------------------------------------------------------

    def resolve(self, query: str) -> list[DrugIdentity]:
        """
        Kullanıcı girdisini DrugIdentity listesine çevirir.

        Arama sırası (ilk eşleşmede durur):
          1. canonical_id exact
          2. normalized_name exact
          3. normalized_name prefix (ilk token)
          4. INN lookup
          5. fuzzy (difflib, threshold=0.80)
          6. normalized_name contains (son çare)

        Hiçbir eşleşme yoksa boş liste döner (exception fırlatmaz).
        """
        if not query or not query.strip():
            return []

        # 1. canonical_id exact
        if query in self._by_canonical:
            return [self._by_canonical[query]]

        # 2. normalized exact
        normalized = normalize_drug_name(query)
        slug = re.sub(r"\s+", "_", normalized)
        if slug in self._by_normalized:
            return [self._by_normalized[slug]]

        # 3. prefix — ilk token
        first_token = slug.split("_")[0]
        prefix_matches = [
            d for n, d in self._by_normalized.items()
            if n.startswith(first_token)
        ]
        if prefix_matches:
            return prefix_matches

        # 4. INN lookup — üç katman:
        #    4a. Tam etken_madde exact ("metoprolol suksinat")
        #    4b. INN token exact ("metoprolol" → BELOC ZOK)
        #    4c. INN token fuzzy (Türkçe yazım varyasyonu: "varfarin" ↔ "warfarin")
        inn_query = query.lower().strip()
        if inn_query in self._by_inn:
            return self._by_inn[inn_query]
        if inn_query in self._by_inn_token:
            return self._by_inn_token[inn_query]
        inn_close = difflib.get_close_matches(
            inn_query, self._all_inn_tokens, n=3, cutoff=0.82
        )
        if inn_close:
            results: list[DrugIdentity] = []
            seen: set[str] = set()
            for key in inn_close:
                for d in self._by_inn_token[key]:
                    if d.canonical_id not in seen:
                        results.append(d)
                        seen.add(d.canonical_id)
            if results:
                return results

        # 5. fuzzy
        close = difflib.get_close_matches(
            slug, self._all_normalized, n=5, cutoff=_FUZZY_THRESHOLD
        )
        if close:
            return [self._by_normalized[n] for n in close]

        # 6. substring fallback
        sub_matches = [
            d for n, d in self._by_normalized.items()
            if first_token in n
        ]
        if sub_matches:
            return sub_matches

        logger.debug(f"NameResolver: '{query}' için eşleşme bulunamadı")
        return []

    def resolve_one(self, query: str) -> Optional[DrugIdentity]:
        """İlk eşleşmeyi döner, yoksa None."""
        results = self.resolve(query)
        return results[0] if results else None

    def resolve_inn_group(self, inn: str) -> list[DrugIdentity]:
        """
        Aynı INN'e sahip tüm ilaçları döner.
        INN propagation için kullanılır.
        """
        return self._by_inn.get(inn.lower().strip(), [])

    def all_drugs(self) -> list[DrugIdentity]:
        """Kayıttaki tüm ilaçlar."""
        return list(self._all)

    def size(self) -> int:
        return len(self._by_canonical)


# ------------------------------------------------------------------
# Registry oluşturucu
# ------------------------------------------------------------------

def build_registry(parsed_json_dir: Path = _PARSED_JSON_DIR) -> dict[str, DrugIdentity]:
    """
    data/parsed_json/ altındaki tüm JSON dosyalarından DrugIdentity registry'si oluşturur.
    Bu registry NameResolver'a verilir.
    """
    registry: dict[str, DrugIdentity] = {}
    skipped = 0

    for json_path in sorted(parsed_json_dir.glob("*.json")):
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            ilac_adi = data.get("ilac_adi", "").strip()
            etken_madde = data.get("etken_madde", "").strip()
            if not ilac_adi or ilac_adi == "Bilinmeyen İlaç":
                skipped += 1
                continue
            identity = DrugIdentity.from_parsed(ilac_adi, etken_madde)
            if identity.canonical_id in registry:
                logger.warning(
                    f"Duplicate canonical_id={identity.canonical_id}: "
                    f"'{identity.display_name}' vs '{registry[identity.canonical_id].display_name}'"
                )
            else:
                registry[identity.canonical_id] = identity
        except Exception as e:
            logger.warning(f"Registry: {json_path.name} atlandı — {e}")
            skipped += 1

    logger.info(f"NameResolver registry: {len(registry)} ilaç yüklendi, {skipped} atlandı")
    return registry


@lru_cache(maxsize=1)
def get_resolver() -> NameResolver:
    """
    Singleton NameResolver — uygulama ömrü boyunca tek instance.
    İlk çağrıda parsed_json/ okunur; sonraki çağrılar cache'den gelir.

    Registry yenilenmesi gerekiyorsa (yeni ilaç eklendiyse):
        get_resolver.cache_clear()
        resolver = get_resolver()
    """
    registry = build_registry()
    return NameResolver(registry)
