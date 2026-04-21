"""
INNResolver — INN (etken madde) bazlı ilaç gruplaması ve etkileşim yayımı.

Önceki durum:
  - propagate_inn_interactions.py: ayrı script, manuel çalıştırılıyor
  - Çalıştırılmayı unutmak kolay
  - INN tokenizasyonu kaba (ilk 120 char, min 8 char token)

Yeni durum:
  - INNResolver ingestion pipeline'ına entegre
  - Her yeni ilaç eklendiğinde INN grubu otomatik güncellenir
  - propagate(): aynı INN'li ilaçların mevcut etkileşimlerini yeni ilaca kopyalar
  - Kopyalanan ilişkiler kaynak='inn_propagated' olarak etiketlenir

Bağımlılık:
  - src/core/name_resolver.py   → NameResolver (registry)
  - src/graph/neo4j_client.py   → run_query
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger

from src.core.name_resolver import get_resolver
from src.graph.neo4j_client import run_query

if TYPE_CHECKING:
    from src.core.drug_record import DrugIdentity
    from src.ingestion.kub_extractor import DrugInteraction


@dataclass
class PropagationResult:
    """INN propagation sonucu."""
    source_drug: str        # Kaynak ilaç (aynı INN grubundan)
    target_drug: str        # Hedef (yeni eklenen ilaç)
    interactions_added: int
    skipped: int            # Zaten mevcutsa atlanıyor


class INNResolver:
    """
    INN bazlı etkileşim yayma servisi.

    Senaryo:
      ALTIZEM SR (diltiazem) için 5 etkileşim mevcut.
      DILTIAREC (diltiazem) yeni ekleniyor → 0 etkileşim.
      INNResolver.propagate(DILTIAREC) → ALTIZEM'in 5 etkileşimi kopyalanır.
    """

    def propagate_to_new_drug(
        self,
        new_identity: "DrugIdentity",
        existing_interactions: list["DrugInteraction"],
    ) -> list["DrugInteraction"]:
        """
        Yeni eklenen ilaç için INN grubundaki diğer ilaçların
        etkileşimlerini bulur ve ekler.

        Mantık:
          1. new_identity.inn ile INN grubunu bul (NameResolver)
          2. Gruptaki diğer ilaçların Neo4j INTERACTS_WITH'lerini çek
          3. existing_interactions'ta zaten olmayanları ekle
          4. Yeni ilişkileri 'inn_propagated' kaynakla döner

        Bu fonksiyon yalnızca DrugInteraction listesi döner;
        Neo4j'e yazma IngestionPipeline'ın AtomicWriter'ında olur.
        """
        if not new_identity.inn:
            return []

        resolver = get_resolver()
        inn_group = resolver.resolve_inn_group(new_identity.inn)

        # Kendisi hariç gruptaki ilaçlar
        peers = [d for d in inn_group if d.canonical_id != new_identity.canonical_id]
        if not peers:
            return []

        logger.debug(
            f"INNResolver: {new_identity.display_name} için INN grubu "
            f"({new_identity.inn}) → {len(peers)} peer bulundu"
        )

        # Mevcut etkileşimlerdeki drug_b canonical_id'leri
        existing_targets = {iw.drug_b_canonical for iw in existing_interactions if iw.drug_b_canonical}

        propagated: list[DrugInteraction] = []
        seen_targets: set[str] = set(existing_targets)

        for peer in peers:
            # Peer'in Neo4j'deki INTERACTS_WITH ilişkilerini çek
            peer_interactions = self._fetch_neo4j_interactions(peer.display_name)

            for row in peer_interactions:
                target_name = row.get("etkilesen_ilac", "")
                if not target_name:
                    continue

                target_identity = resolver.resolve_one(target_name)
                target_cid = target_identity.canonical_id if target_identity else None

                # Zaten mevcut veya bu turu içinde eklendiyse atla
                if target_cid and target_cid in seen_targets:
                    continue
                if not target_cid and target_name in seen_targets:
                    continue

                key = target_cid or target_name
                seen_targets.add(key)

                # Lazy import — circular dependency önlemi
                from src.ingestion.kub_extractor import DrugInteraction as DI
                propagated.append(DI(
                    drug_b_raw=target_name,
                    drug_b_canonical=target_cid,
                    severity=row.get("siddet", "unknown"),
                    mechanism=None,
                    source_section=row.get("kaynak", "4.5") or "4.5",
                    confidence=0.7,    # propagation = biraz daha düşük güven
                    is_propagated=True,
                    propagated_from=peer.display_name,
                ))

        if propagated:
            logger.info(
                f"INNResolver: {new_identity.display_name} → "
                f"{len(propagated)} etkileşim INN grubundan yayıldı"
            )

        return propagated

    @staticmethod
    def _fetch_neo4j_interactions(ilac_adi: str) -> list[dict]:
        """Bir ilacın Neo4j'deki mevcut INTERACTS_WITH listesini çeker."""
        try:
            return run_query(
                """
                MATCH (d:Drug)-[r:INTERACTS_WITH]->(b:Drug)
                WHERE d.name = $n OR toUpper(d.name) STARTS WITH toUpper($prefix)
                RETURN b.name AS etkilesen_ilac,
                       r.severity AS siddet,
                       r.kaynak_madde AS kaynak
                LIMIT 50
                """,
                {"n": ilac_adi, "prefix": ilac_adi.split()[0].upper()},
            )
        except Exception as e:
            logger.warning(f"INNResolver Neo4j sorgusu başarısız ({ilac_adi}): {e}")
            return []

    def get_inn_group_stats(self) -> list[dict]:
        """
        Tüm INN gruplarının istatistiklerini döner.
        Hangi grubun kaç ilaç içerdiğini, ortalama etkileşim sayısını gösterir.
        (Debug / raporlama amaçlı)
        """
        resolver = get_resolver()
        stats = []
        seen_inns: set[str] = set()

        for drug in resolver.all_drugs():
            if not drug.inn or drug.inn in seen_inns:
                continue
            group = resolver.resolve_inn_group(drug.inn)
            if len(group) > 1:
                seen_inns.add(drug.inn)
                stats.append({
                    "inn": drug.inn,
                    "drug_count": len(group),
                    "drugs": [d.display_name for d in group],
                })

        return sorted(stats, key=lambda x: x["drug_count"], reverse=True)
