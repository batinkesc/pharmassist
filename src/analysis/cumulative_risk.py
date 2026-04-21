"""
Kümülatif Yan Etki Risk Modülü — Senaryo 2

Birden fazla ilacın ortak yan etki kategorisi taşıması durumunda
toplam riski hesaplar.

Mantık:
  - Her retrieved chunk'ın içeriği yan etki kategorileri için taranır
  - Aynı kategoride 2+ ilaç sinyal veriyorsa → DİKKAT
  - Aynı kategoride 3+ ilaç sinyal veriyorsa → KRİTİK
  - Sonuç hem prompt'a eklenir hem RAGResponse'a aktarılır

Yan etki kategorileri (klinik öncelik sırasına göre):
  kardiyak, hepatik, renal, hematolojik, nörolojik,
  solunum, gastrointestinal, alerji, endokrin
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Kategori tanımları — anahtar kelimeler
# ---------------------------------------------------------------------------

YAN_ETKI_KATEGORILERI: dict[str, dict] = {
    "kardiyak": {
        "label": "Kardiyak / QT Uzaması",
        "keywords": re.compile(
            r"qt\s*uzama|kalp\s*ritim|aritmi|bradikardi|taşikardi"
            r"|ventriküler|atriyal\s*fibril|kalp\s*durma|kardiyak\s*arrest"
            r"|torsades|palpitasyon|miyokard",
            re.IGNORECASE,
        ),
        "organ": "kardiyak",
    },
    "hepatik": {
        "label": "Hepatotoksisite",
        "keywords": re.compile(
            r"hepat|karaciğer\s*(hasar|yetmezlik|enzim|toksis)"
            r"|ALT|AST|transaminaz|sarılık|kolestaz|hepatit"
            r"|bilirubin\s*yüksel|karaciğerde\s*(yan|etki|bozuk)",
            re.IGNORECASE,
        ),
        "organ": "hepatik",
    },
    "renal": {
        "label": "Nefrotoksisite",
        "keywords": re.compile(
            r"böbrek\s*(hasar|yetmezlik|toksis|bozuk|fonksiyon)"
            r"|nefrotoks|kreatinin\s*yüksel|GFR\s*düş|renal\s*(hasar|yetmezlik)"
            r"|akut\s*böbrek|idrar\s*(azal|kesil)|oligüri",
            re.IGNORECASE,
        ),
        "organ": "renal",
    },
    "hematolojik": {
        "label": "Kanama / Hematolojik Risk",
        "keywords": re.compile(
            r"kanama|hemoraji|trombositopeni|anemi|lökopeni"
            r"|pansitopeni|koagülasyon|INR|antikoagül|pıhtılaşma"
            r"|epistaksis|ekimoz|hematom|kan\s*(kayıp|kaybı)",
            re.IGNORECASE,
        ),
        "organ": "hematolojik",
    },
    "nörolojik": {
        "label": "Nörotoksisite / SSS",
        "keywords": re.compile(
            r"nörotoks|serotonin\s*sendrom|konvülsiyon|nöbet|baş\s*dönmesi"
            r"|baş\s*ağrısı|konfüzyon|bilinç\s*(bozuk|kayıp)"
            r"|ensefalopati|SSS|merkezi\s*sinir|tremor|parestezi",
            re.IGNORECASE,
        ),
        "organ": "nörolojik",
    },
    "solunum": {
        "label": "Solunum Toksisitesi",
        "keywords": re.compile(
            r"bronkospazm|solunum\s*(depresyon|yetmezlik|baskı)"
            r"|pulmoner\s*(toksis|fibrozis|ödem)|dispne|apne"
            r"|interstisyel\s*akciğer",
            re.IGNORECASE,
        ),
        "organ": "solunum",
    },
    "gastrointestinal": {
        "label": "Gastrointestinal Toksisite",
        "keywords": re.compile(
            r"gastrointestinal\s*(kanama|ülser|perforasyon)"
            r"|GI\s*(kanama|toksis)|peptik\s*ülser|mide\s*(kanama|ülser)"
            r"|bulantı.*kusma|diyare.*ağır|kolit",
            re.IGNORECASE,
        ),
        "organ": "gastrointestinal",
    },
    "alerji": {
        "label": "Alerji / Anafilaksi",
        "keywords": re.compile(
            r"anafilaksi|anafilaktik|aşırı\s*duyarlılık|alerjik\s*reaksiyon"
            r"|anjiyoödem|ürtiker|Steven.*Johnson|toksik\s*epidermal",
            re.IGNORECASE,
        ),
        "organ": "alerji",
    },
    "endokrin": {
        "label": "Endokrin / Elektrolit Bozukluğu",
        "keywords": re.compile(
            r"hiperkalemi|hipokalemi|hiponatremi|hipernatremi"
            r"|hipoglisemi|hiperglisemi|hipomagnezemi"
            r"|elektrolit\s*(bozuk|dengesizlik)",
            re.IGNORECASE,
        ),
        "organ": "endokrin",
    },
}


# ---------------------------------------------------------------------------
# Veri yapıları
# ---------------------------------------------------------------------------

@dataclass
class KumulatifRisk:
    """Tek bir yan etki kategorisi için kümülatif risk bulgusu."""
    kategori_kodu: str
    kategori_label: str
    ilaclar: list[str]          # Bu kategoriyi tetikleyen ilaçlar
    siddet: str                 # "kritik" | "dikkat"
    aciklama: str


@dataclass
class KumulatifRiskSonucu:
    """Tüm kümülatif risk analizi çıktısı."""
    riskler: list[KumulatifRisk] = field(default_factory=list)
    ozet_metin: str = ""        # Prompt'a eklenecek formatlı metin

    @property
    def kritik_var_mi(self) -> bool:
        return any(r.siddet == "kritik" for r in self.riskler)

    @property
    def risk_yok(self) -> bool:
        return len(self.riskler) == 0


# ---------------------------------------------------------------------------
# Ana analiz fonksiyonu
# ---------------------------------------------------------------------------

def analiz_et(chunklar: list, hasta_ilaclar: list[str] | None = None) -> KumulatifRiskSonucu:
    """
    Retrieved chunk listesini tarayarak kümülatif yan etki riskini hesaplar.

    Args:
        chunklar:      RAG engine'den gelen RetrievedChunk listesi
        hasta_ilaclar: Hastanın mevcut ilaçları (ek sinyal için)

    Returns:
        KumulatifRiskSonucu
    """
    # Her kategori için hangi ilaçların sinyal verdiğini topla
    # {kategori_kodu: {ilac_adi: True}}
    kategori_ilac_map: dict[str, set[str]] = {k: set() for k in YAN_ETKI_KATEGORILERI}

    for chunk in chunklar:
        ilac = getattr(chunk, "ilac_adi", "") or ""
        madde = getattr(chunk, "madde_no", "") or ""
        icerik = getattr(chunk, "icerik", "") or ""

        # Sadece yan etki (4.8) ve uyarı (4.4) maddelerini tara
        # Diğer maddeler false-positive üretebilir
        if madde not in ("4.8", "4.4", "4.5", "4.3"):
            continue

        if not ilac or not icerik:
            continue

        for kat_kodu, kat in YAN_ETKI_KATEGORILERI.items():
            if kat["keywords"].search(icerik):
                kategori_ilac_map[kat_kodu].add(ilac)

    # Risk hesapla
    riskler: list[KumulatifRisk] = []
    for kat_kodu, ilaclar in kategori_ilac_map.items():
        if len(ilaclar) < 2:
            continue  # Tek ilaç → kümülatif risk yok

        kat = YAN_ETKI_KATEGORILERI[kat_kodu]
        siddet = "kritik" if len(ilaclar) >= 3 else "dikkat"
        ilac_listesi = sorted(ilaclar)

        aciklama = (
            f"{len(ilaclar)} ilaç birlikte {kat['label'].lower()} riski taşıyor: "
            f"{', '.join(ilac_listesi)}"
        )

        riskler.append(KumulatifRisk(
            kategori_kodu=kat_kodu,
            kategori_label=kat["label"],
            ilaclar=ilac_listesi,
            siddet=siddet,
            aciklama=aciklama,
        ))

    # Şiddete göre sırala (kritik önce)
    riskler.sort(key=lambda r: 0 if r.siddet == "kritik" else 1)

    ozet = _format_ozet(riskler)

    return KumulatifRiskSonucu(riskler=riskler, ozet_metin=ozet)


def _format_ozet(riskler: list[KumulatifRisk]) -> str:
    """Kümülatif riskleri prompt için formatlı metne çevirir."""
    if not riskler:
        return ""

    satirlar = ["**⚠️ Kümülatif Yan Etki Risk Analizi:**"]
    for r in riskler:
        sembol = "🔴 KRİTİK" if r.siddet == "kritik" else "🟡 DİKKAT"
        satirlar.append(f"  {sembol} — {r.aciklama}")

    return "\n".join(satirlar)
