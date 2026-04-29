"""
CombiGraph Retriever — ChromaDB + Neo4j birleşik sorgu katmanı.

Hasta profilindeki mevcut ilaçlar ve sorgu edilen ilaçlar için:
  1. Neo4j'den kontrendikasyon ve etkileşim bilgisi çeker
  2. Bu bilgiyi prompt context'ine ekler
  3. ChromaDB chunk'larıyla birleştirir
"""

import re
from dataclasses import dataclass
from loguru import logger

from src.core.content_policy import POLICY
from src.graph.graph_retriever import (
    drug_contraindications,
    drug_interactions,
    drug_warnings,
    drug_class_interactions,
    multi_drug_interactions,
    drugs_for_condition,
)


@dataclass
class GraphContext:
    """Neo4j'den çekilen graf bağlamı."""
    kontrendikasyonlar: list[dict]        # {ilac, kosul, kaynak}
    etkilesimler: list[dict]              # {ilac_a, ilac_b, siddet, kaynak}
    hasta_ilac_etkilesimleri: list[dict]  # mevcut ilaçlar arası çakışmalar
    uyarilar: list[dict]                  # HAS_WARNING node'ları (ozet, bolum)
    sinif_etkilesimleri: list[dict]       # INTERACTS_WITH_CLASS (sinif_adi, siddet)
    ozet_metin: str                       # prompt'a eklenecek formatlı metin


def _filter_contraindications_by_profile(
    kontrendikasyonlar: list[dict],
    hasta_kosullar: list[str],
    hasta_yas: int | None = None,
    hasta_endikasyonlar: list[str] | None = None,
    max_count: int = 10,
) -> list[dict]:
    """
    Kontrendikasyonları hasta profiline göre filtreler ve önceliklendirir.

    Strateji:
      1. Pediyatrik kontrendikasyonları yetişkin hastadan kesin hariç tut (yaş ≥18)
      2. Hasta koşulu/tanısıyla örtüşen kontrendikasyonları önceliklendir
      3. Diğerlerini de dahil et ama max_count ile sınırla

    Bu sayede LLM'e gönderilen kontrendikasyon sayısı düşer ve
    hastaya uymayan uyarılar false positive üretmez.
    """
    if not kontrendikasyonlar:
        return []

    yetiskin = hasta_yas is not None and hasta_yas >= 18

    # Pediyatrik/çocuk-özel kontrendikasyon tespiti
    _PEDIATRIK_RE = re.compile(
        r"çocuk|pediatr|pediyatr|\d+\s*yaş\s*alt[ıi]|bebek|yenidoğan|neonatal",
        re.IGNORECASE,
    )

    # Hasta bağlamı için anahtar kelime seti
    hasta_anahtar: set[str] = set()
    for k in (hasta_kosullar or []):
        hasta_anahtar.update(k.lower().replace("-", " ").split())
    for e in (hasta_endikasyonlar or []):
        hasta_anahtar.update(e.lower().replace("-", " ").split())
    # Kısa stopword'leri çıkar
    _STOP = {"ve", "ile", "için", "olan", "olan", "bir", "da", "de", "ki"}
    hasta_anahtar -= _STOP

    kesinlikle_disla: list[dict] = []
    oncelikli: list[dict] = []
    diger: list[dict] = []

    for row in kontrendikasyonlar:
        kosul_text = (row.get("kosul") or "").lower()
        neden_text = (row.get("neden") or "").lower()
        combined = kosul_text + " " + neden_text

        # Kural 1: Pediyatrik kontrendikasyonu yetişkin hastadan hariç tut
        if yetiskin and _PEDIATRIK_RE.search(combined):
            kesinlikle_disla.append(row)
            continue

        # Kural 2: Hasta profiliyle örtüşen kontrendikasyonları önceliklendir
        if hasta_anahtar and any(kw in combined for kw in hasta_anahtar):
            oncelikli.append(row)
        else:
            diger.append(row)

    disla_sayisi = len(kesinlikle_disla)
    if disla_sayisi > 0:
        logger.debug(
            f"Kontrendikasyon filtresi: {disla_sayisi} pediyatrik/profil-dışı kayıt dışlandı, "
            f"{len(oncelikli)} öncelikli + {len(diger)} diğer kaldı"
        )

    # Önce profil-eşleşen, sonra diğerleri; toplamda max_count
    sonuc = oncelikli + diger
    return sonuc[:max_count]


def build_graph_context(
    sorgu_ilaclar: list[str],
    hasta_ilaclar: list[str],
    hasta_kosullar: list[str],
    hasta_yas: int | None = None,
    hasta_endikasyonlar: list[str] | None = None,
) -> GraphContext:
    """
    Sorgu ve hasta profili için Neo4j bağlamını oluşturur.

    Args:
        sorgu_ilaclar:       Sorguda geçen ilaç adları (Neo4j'deki tam adlarla eşleşmeli)
        hasta_ilaclar:       Hastanın mevcut ilaçları
        hasta_kosullar:      Hasta koşulları (böbrek yetmezliği, gebelik vb.)
        hasta_yas:           Hastanın yaşı (pediyatrik kontrendikasyon filtresi için)
        hasta_endikasyonlar: Hastanın tanı/endikasyonları (kontrendikasyon önceliklendirme için)
    """
    kontrendikasyonlar = []
    etkilesimler = []
    uyarilar = []
    sinif_etkilesimleri = []

    # Sorgu ilaçlarının kontrendikasyon, etkileşim, uyarı ve sınıf etkileşimlerini çek
    for ilac in sorgu_ilaclar:
        ki = drug_contraindications(ilac)
        if ki:
            for row in ki:
                row["ilac"] = ilac
            kontrendikasyonlar.extend(ki)
            logger.debug(f"  {ilac}: {len(ki)} kontrendikasyon (ham)")

        ei = drug_interactions(ilac)
        if ei:
            for row in ei:
                row["ana_ilac"] = ilac
            etkilesimler.extend(ei)
            logger.debug(f"  {ilac}: {len(ei)} etkileşim")

        # A: HAS_WARNING — hasta koşullarına göre filtreli
        wi = drug_warnings(ilac, hasta_kosullar if hasta_kosullar else None)
        if wi:
            for row in wi:
                row["ilac"] = ilac
            uyarilar.extend(wi)
            logger.debug(f"  {ilac}: {len(wi)} HAS_WARNING uyarısı")

        # B: INTERACTS_WITH_CLASS — ilaç sınıfı etkileşimleri
        ci = drug_class_interactions(ilac)
        if ci:
            sinif_etkilesimleri.extend(ci)
            logger.debug(f"  {ilac}: {len(ci)} sınıf etkileşimi")

    # Hasta koşullarına göre kontrendike ilaçları da kontrol et
    for kosul in hasta_kosullar:
        rows = drugs_for_condition(kosul)
        for row in rows:
            if row not in kontrendikasyonlar:
                kontrendikasyonlar.append(row)

    # Fix #4: Kontrendikasyonları hasta profiline göre filtrele ve önceliklendir
    # → Pediyatrik kontrendikasyonlar yetişkin hastadan dışlanır
    # → Hasta koşuluyla örtüşenler önce gelir; toplamda max 10 ile sınırlanır
    ham_sayisi = len(kontrendikasyonlar)
    kontrendikasyonlar = _filter_contraindications_by_profile(
        kontrendikasyonlar,
        hasta_kosullar=hasta_kosullar,
        hasta_yas=hasta_yas,
        hasta_endikasyonlar=hasta_endikasyonlar,
        max_count=10,
    )
    logger.info(
        f"Kontrendikasyon filtresi: {ham_sayisi} ham → {len(kontrendikasyonlar)} "
        f"(hasta_yas={hasta_yas})"
    )

    # Hasta'nın mevcut ilaçları arasındaki Neo4j etkileşimleri
    tum_ilaclar = list(set(sorgu_ilaclar + hasta_ilaclar))
    hasta_ilac_etkilesimleri = multi_drug_interactions(tum_ilaclar) if len(tum_ilaclar) > 1 else []

    ozet = _format_graph_context(
        kontrendikasyonlar, etkilesimler, hasta_ilac_etkilesimleri,
        uyarilar=uyarilar, sinif_etkilesimleri=sinif_etkilesimleri,
    )

    return GraphContext(
        kontrendikasyonlar=kontrendikasyonlar,
        etkilesimler=etkilesimler,
        hasta_ilac_etkilesimleri=hasta_ilac_etkilesimleri,
        uyarilar=uyarilar,
        sinif_etkilesimleri=sinif_etkilesimleri,
        ozet_metin=ozet,
    )


def _format_graph_context(
    kontrendikasyonlar: list[dict],
    etkilesimler: list[dict],
    hasta_etkilesimleri: list[dict],
    uyarilar: list[dict] | None = None,
    sinif_etkilesimleri: list[dict] | None = None,
) -> str:
    """
    Graf bağlamını prompt için formatlı metne çevirir.

    C aksiyonu: INTERACTS_WITH severity='contraindicated' olan etkileşimler
    kontrendikasyon bölümüne taşınır; diğerleri etkileşim bölümünde kalır.
    """
    parcalar = []

    # C: etkilesimler'i severity'ye göre ayır
    contraind_from_interactions: list[dict] = []
    normal_etkilesimler: list[dict] = []
    for row in etkilesimler:
        if (row.get("siddet") or "").lower() == "contraindicated":
            contraind_from_interactions.append(row)
        else:
            normal_etkilesimler.append(row)

    # Kontrendikasyonlar bölümü (CONTRAINDICATED_FOR + severity='contraindicated' INTERACTS_WITH)
    tum_kontralar = list(kontrendikasyonlar)
    for row in contraind_from_interactions:
        # INTERACTS_WITH satırını kontrendikasyon formatına dönüştür
        tum_kontralar.append({
            "ilac": row.get("ana_ilac", "?"),
            "kosul": row.get("etkilesen_ilac", "?"),
            "neden": row.get("mekanizma", ""),
            "_kaynak": "interacts_with_kontr",
        })

    if tum_kontralar:
        satirlar = ["**Graf Tabanlı Kontrendikasyonlar (Neo4j):**"]
        for row in tum_kontralar[:POLICY.max_contraindications_in_context]:
            ilac = row.get("ilac") or row.get("ilac_adi", "?")
            kosul = row.get("kosul", "?")
            neden = row.get("neden", "")
            # INTERACTS_WITH kökenli kontrendikasyonlar için etiket ekle
            kaynak_etiketi = " [ilaç etkileşimi]" if row.get("_kaynak") == "interacts_with_kontr" else ""
            neden_str = f" | Gerekçe: {neden}" if neden else ""
            satirlar.append(
                f"  - {ilac} → {kosul} ile birlikte kontrendike{kaynak_etiketi}{neden_str}"
            )
        if len(tum_kontralar) > POLICY.max_contraindications_in_context:
            satirlar.append(
                f"  ... ve {len(tum_kontralar) - POLICY.max_contraindications_in_context} "
                "kontrendikasyon daha (tam liste KÜB'de mevcuttur)"
            )
        parcalar.append("\n".join(satirlar))

    # Etkileşimler bölümü (sadece contraindicated olmayan satırlar)
    if normal_etkilesimler:
        satirlar = ["**Graf Tabanlı Etkileşimler (Neo4j):**"]
        for row in normal_etkilesimler[:POLICY.max_interactions_in_context]:
            ana = row.get("ana_ilac", "?")
            diger = row.get("etkilesen_ilac", "?")
            siddet = row.get("siddet", "")
            mekanizma = row.get("mekanizma", "")
            siddet_str = f" [{siddet}]" if siddet and siddet != "unknown" else ""
            mek_str = f" — {mekanizma}" if mekanizma else ""
            tip = row.get("tip", "")
            tip_str = " (metin eşleşmesi)" if tip == "metin" else ""
            satirlar.append(f"  - {ana} ↔ {diger}{siddet_str}{mek_str}{tip_str}")
        if len(normal_etkilesimler) > POLICY.max_interactions_in_context:
            satirlar.append(
                f"  ... ve {len(normal_etkilesimler) - POLICY.max_interactions_in_context} etkileşim daha"
            )
        parcalar.append("\n".join(satirlar))

    # B: İlaç sınıfı etkileşimleri
    if sinif_etkilesimleri:
        satirlar = ["**Graf Tabanlı İlaç Sınıfı Etkileşimleri (Neo4j):**"]
        for row in sinif_etkilesimleri[:10]:
            ana = row.get("ana_ilac", "?")
            sinif = row.get("sinif_adi", "?")
            siddet = row.get("siddet", "")
            mekanizma = row.get("mekanizma", "")
            siddet_str = f" [{siddet}]" if siddet and siddet != "unknown" else ""
            mek_str = f" — {mekanizma}" if mekanizma else ""
            satirlar.append(f"  - {ana} ↔ {sinif} sınıfı{siddet_str}{mek_str}")
        parcalar.append("\n".join(satirlar))

    # A: HAS_WARNING uyarıları — hasta koşuluna göre filtreli
    if uyarilar:
        satirlar = ["**⚠️ Graf Uyarıları (KÜB Bölüm 4.4/4.5):**"]
        # Aynı içerikli uyarıları dedup et (ilacın birden fazla dozu aynı Warning'e sahip olabilir)
        gorulmus_ozet: set[str] = set()
        uyarilar_dedup = []
        for row in uyarilar:
            ozet_key = (row.get("ozet") or "")[:80]
            if ozet_key not in gorulmus_ozet:
                gorulmus_ozet.add(ozet_key)
                uyarilar_dedup.append(row)
        for row in uyarilar_dedup[:5]:
            ilac = row.get("ilac", "")
            # ozet genellikle "4.4 Özel kullanım..." ile başlar; ilk anlamlı satırı al
            ozet_raw = (row.get("ozet") or "")
            # Bölüm başlığını atla, ilk içerik satırına geç
            ozet_satirlar = [s.strip() for s in ozet_raw.splitlines() if len(s.strip()) > 10]
            ozet = " ".join(ozet_satirlar[1:3])[:200] if len(ozet_satirlar) > 1 else ozet_raw[:200]
            ilac_str = f"[{ilac}] " if ilac else ""
            satirlar.append(f"  - {ilac_str}{ozet}")
        parcalar.append("\n".join(satirlar))

    if hasta_etkilesimleri:
        satirlar = ["**⚠️ Hasta İlaç Listesinde Tespit Edilen Etkileşimler:**"]
        for row in hasta_etkilesimleri[:POLICY.max_patient_interactions_in_context]:
            satirlar.append(f"  - {row.get('ilac_a')} ↔ {row.get('ilac_b')}")
        parcalar.append("\n".join(satirlar))

    if not parcalar:
        return "Graf veritabanında ilgili kontrendikasyon veya etkileşim kaydı bulunamadı."

    return "\n\n".join(parcalar)
