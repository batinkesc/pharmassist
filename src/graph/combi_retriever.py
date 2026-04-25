"""
CombiGraph Retriever — ChromaDB + Neo4j birleşik sorgu katmanı.

Hasta profilindeki mevcut ilaçlar ve sorgu edilen ilaçlar için:
  1. Neo4j'den kontrendikasyon ve etkileşim bilgisi çeker
  2. Bu bilgiyi prompt context'ine ekler
  3. ChromaDB chunk'larıyla birleştirir
"""

from dataclasses import dataclass
from loguru import logger

from src.core.content_policy import POLICY
from src.graph.graph_retriever import (
    drug_contraindications,
    drug_interactions,
    multi_drug_interactions,
    drugs_for_condition,
)


@dataclass
class GraphContext:
    """Neo4j'den çekilen graf bağlamı."""
    kontrendikasyonlar: list[dict]   # {ilac, kosul, kaynak}
    etkilesimler: list[dict]          # {ilac_a, ilac_b, siddet, kaynak}
    hasta_ilac_etkilesimleri: list[dict]  # mevcut ilaçlar arası çakışmalar
    ozet_metin: str                   # prompt'a eklenecek formatlı metin


def build_graph_context(
    sorgu_ilaclar: list[str],
    hasta_ilaclar: list[str],
    hasta_kosullar: list[str],
) -> GraphContext:
    """
    Sorgu ve hasta profili için Neo4j bağlamını oluşturur.

    Args:
        sorgu_ilaclar:  Sorguda geçen ilaç adları (Neo4j'deki tam adlarla eşleşmeli)
        hasta_ilaclar:  Hastanın mevcut ilaçları
        hasta_kosullar: Hasta koşulları (böbrek yetmezliği, gebelik vb.)
    """
    kontrendikasyonlar = []
    etkilesimler = []

    # Sorgu ilaçlarının kontrendikasyon ve etkileşimlerini çek
    for ilac in sorgu_ilaclar:
        ki = drug_contraindications(ilac)
        if ki:
            for row in ki:
                row["ilac"] = ilac
            kontrendikasyonlar.extend(ki)
            logger.debug(f"  {ilac}: {len(ki)} kontrendikasyon")

        ei = drug_interactions(ilac)
        if ei:
            for row in ei:
                row["ana_ilac"] = ilac
            etkilesimler.extend(ei)
            logger.debug(f"  {ilac}: {len(ei)} etkileşim")

    # Hasta koşullarına göre kontrendike ilaçları da kontrol et
    for kosul in hasta_kosullar:
        rows = drugs_for_condition(kosul)
        for row in rows:
            if row not in kontrendikasyonlar:
                kontrendikasyonlar.append(row)

    # Hasta'nın mevcut ilaçları arasındaki Neo4j etkileşimleri
    tum_ilaclar = list(set(sorgu_ilaclar + hasta_ilaclar))
    hasta_ilac_etkilesimleri = multi_drug_interactions(tum_ilaclar) if len(tum_ilaclar) > 1 else []

    ozet = _format_graph_context(kontrendikasyonlar, etkilesimler, hasta_ilac_etkilesimleri)

    return GraphContext(
        kontrendikasyonlar=kontrendikasyonlar,
        etkilesimler=etkilesimler,
        hasta_ilac_etkilesimleri=hasta_ilac_etkilesimleri,
        ozet_metin=ozet,
    )


def _format_graph_context(
    kontrendikasyonlar: list[dict],
    etkilesimler: list[dict],
    hasta_etkilesimleri: list[dict],
) -> str:
    """Graf bağlamını prompt için formatlı metne çevirir."""
    parcalar = []

    if kontrendikasyonlar:
        satirlar = ["**Graf Tabanlı Kontrendikasyonlar (Neo4j):**"]
        # ContentPolicy limiti — CO-DIOVAN gibi 100+ kontrendikasyonlu ilaçlar
        # LM Studio context'ini taşırıyordu; şimdi en fazla POLICY değeri kadar
        for row in kontrendikasyonlar[:POLICY.max_contraindications_in_context]:
            ilac = row.get("ilac") or row.get("ilac_adi", "?")
            kosul = row.get("kosul", "?")
            neden = row.get("neden", "")
            neden_str = f" | Gerekçe: {neden}" if neden else ""
            satirlar.append(f"  - {ilac} → {kosul} durumunda kontrendike{neden_str}")
        if len(kontrendikasyonlar) > POLICY.max_contraindications_in_context:
            satirlar.append(
                f"  ... ve {len(kontrendikasyonlar) - POLICY.max_contraindications_in_context} "
                "kontrendikasyon daha (tam liste KÜB'de mevcuttur)"
            )
        parcalar.append("\n".join(satirlar))

    if etkilesimler:
        satirlar = ["**Graf Tabanlı Etkileşimler (Neo4j):**"]
        for row in etkilesimler[:POLICY.max_interactions_in_context]:
            ana = row.get("ana_ilac", "?")
            diger = row.get("etkilesen_ilac", "?")
            siddet = row.get("siddet", "")
            mekanizma = row.get("mekanizma", "")
            siddet_str = f" [{siddet}]" if siddet and siddet != "unknown" else ""
            mek_str = f" — {mekanizma}" if mekanizma else ""
            tip = row.get("tip", "")
            tip_str = " (metin eşleşmesi)" if tip == "metin" else ""
            satirlar.append(f"  - {ana} ↔ {diger}{siddet_str}{mek_str}{tip_str}")
        if len(etkilesimler) > POLICY.max_interactions_in_context:
            satirlar.append(
                f"  ... ve {len(etkilesimler) - POLICY.max_interactions_in_context} etkileşim daha"
            )
        parcalar.append("\n".join(satirlar))

    if hasta_etkilesimleri:
        satirlar = ["**⚠️ Hasta İlaç Listesinde Tespit Edilen Etkileşimler:**"]
        for row in hasta_etkilesimleri[:POLICY.max_patient_interactions_in_context]:
            satirlar.append(f"  - {row.get('ilac_a')} ↔ {row.get('ilac_b')}")
        parcalar.append("\n".join(satirlar))

    if not parcalar:
        return "Graf veritabanında ilgili kontrendikasyon veya etkileşim kaydı bulunamadı."

    return "\n\n".join(parcalar)
