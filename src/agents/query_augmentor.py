"""
Query Augmentation modülü.

Görev:
  - Hasta profili + kullanıcı sorusu → ChromaDB için arama stratejisi üretir
  - Hangi madde numaralarına öncelik verileceğini belirler
  - Hasta flags'lerini filtre olarak aktarır
  - Birden fazla ilaç için ayrı arama planları oluşturur

Klinik mantık:
  - Etkileşim sorusu → 4.5 öncelikli
  - Kontrendikasyon sorusu → 4.3 öncelikli
  - Doz sorusu + böbrek yetmezliği → 4.2[bobrek] öncelikli
  - Gebelik/emzirme → 4.6 öncelikli
  - Yan etki → 4.8 öncelikli
  - Genel kullanım uyarısı → 4.4 öncelikli
"""

import re
from dataclasses import dataclass, field
from loguru import logger

from src.agents.patient_profile import PatientProfile


# ---------------------------------------------------------------------------
# Soru türü tespiti için anahtar kelimeler
# ---------------------------------------------------------------------------

INTERACTION_KEYWORDS = re.compile(
    r"etkile[sş]im|beraber|kombinas|birlikte|yan\s+yana|ilave|ek\s+olarak"
    r"|ile\s+kullan|birlikte\s+ver"
    # Farmakokinetik/farmakodinamik etki değişimi sinyalleri
    r"|etki\s+nas[ıi]l\s+de[gğ]i[sş]|kan\s+d[üu]zeyi|plazma\s+d[üu]zeyi"
    r"|eklenirse|eklenebilir|eklendi[gğ]inde|ba[sş]lan[ıi]rsa|ba[sş]land[ıi][gğ][ıi]nda"
    r"|verili[rn]se|verildi[gğ]inde|[üu]zerine\s+etki|etkiler\s+mi"
    r"|nas[ıi]l\s+etkiler|ne\s+olur|ne\s+de[gğ]i[sş]|de[gğ]i[sş]tirir",
    re.IGNORECASE,
)
CONTRAINDICATION_KEYWORDS = re.compile(
    r"kontrendike|kullan[ıi]labilir\s+mi|verilir\s+mi|uygun\s+mu|yasak|sakıncalı"
    r"|yaz[ıi]labilir\s+mi|kullan[ıi]lır\s+mı|verilebilir\s+mi|verilmeli\s+mi"
    r"|kullanmal[ıi]\s+mı|reçete\s+edilebilir|uygun\s+mu|kontrendike\s+mi"
    r"|alerjisi.*verilebilir|alerji.*kullan",
    re.IGNORECASE,
)
DOSE_KEYWORDS = re.compile(
    r"doz|dozaj|pozoloji|kaç\s+(mg|tablet|kapsül|ml)|ne\s+kadar|miktar"
    r"|doz\s+ayar|azalt|artır|düşür",
    re.IGNORECASE,
)
PREGNANCY_KEYWORDS = re.compile(
    r"gebelik|hamile|laktasyon|emzir|anne\s+sütü|trimester|gebelikte",
    re.IGNORECASE,
)
SIDE_EFFECT_KEYWORDS = re.compile(
    r"yan\s+etki|advers|istenmeyen|reaksiyon|toksisite"
    r"|ba[sş]lad[ıi]|neden\s+olabilir|ilaca\s+ba[gğ]l[ıi]|ilactan\s+m[ıi]"
    r"|bu\s+ilaç.*m[ıi]|sebep\s+olur|yol\s+açar|ortaya\s+çıkt[ıi]"
    r"|şikayet|semptom.*ilaç|ilaç.*semptom"
    # Klinik risk/enfeksiyon sinyalleri — 4.8 bölümüne yönlendirir
    r"|enfeksiyon\s+riski|kanama\s+riski|ödem|hepatotoksisite|nefrotoksisite"
    r"|hipoglisemi|hiperglisemi|laktik\s+asidoz|nöropati|miyopati"
    r"|üriner|genitoüriner|mantar\s+enf|cilt\s+reaksiyon"
    r"|risk\s+hakkında|bu\s+ilaç.*risk|ilaç.*risk\s+ne|ne\s+(tür|gibi)\s+risk",
    re.IGNORECASE,
)
WARNING_KEYWORDS = re.compile(
    r"uyarı|önlem|dikkat|risk|tehlike|güvenlik",
    re.IGNORECASE,
)
OVERDOSE_KEYWORDS = re.compile(
    r"doz\s+aşım|toksik\s+doz|zehirlenme|overdoz",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Arama planı veri yapısı
# ---------------------------------------------------------------------------

@dataclass
class SearchPlan:
    """
    Tek bir ilaç için retrieval planı.

    Attributes:
        ilac_adi:       Aranacak ilaç adı (None ise tüm ilaçlar)
        madde_onceligi: Önce bu maddelerde ara (sıralı)
        patient_flags:  Hasta bazlı flag filtreleri
        n_results:      Her aramada kaç sonuç isteniyor
        sorgu:          Zenginleştirilmiş arama sorgusu
    """
    ilac_adi: str | None
    madde_onceligi: list[str]
    patient_flags: list[str]
    n_results: int
    sorgu: str


@dataclass
class AugmentedQuery:
    """
    Tam augmented query çıktısı.

    Attributes:
        ozgun_soru:     Kullanıcının ham sorusu
        soru_turleri:   Tespit edilen soru türleri
        arama_planlari: Her ilaç için SearchPlan listesi
        hasta_ozeti:    Promptta kullanılacak hasta profil özeti
    """
    ozgun_soru: str
    soru_turleri: list[str]
    arama_planlari: list[SearchPlan]
    hasta_ozeti: str


# ---------------------------------------------------------------------------
# Ana augmentation fonksiyonu
# ---------------------------------------------------------------------------

def augment_query(
    soru: str,
    profil: PatientProfile,
    hedef_ilaclar: list[str] | None = None,
    n_results: int = 5,
) -> AugmentedQuery:
    """
    Kullanıcı sorusu + hasta profilini zenginleştirilmiş arama planına çevirir.

    Args:
        soru:          Kullanıcı sorusu (Türkçe)
        profil:        Hasta profili
        hedef_ilaclar: Sorgunun ilgili olduğu ilaçlar (None ise tüm koleksiyon aranır)
        n_results:     Her plan için kaç chunk alınacak

    Returns:
        AugmentedQuery — arama planları ve hasta özeti
    """
    soru_turleri = _detect_question_types(soru, profil)
    madde_onceligi = _prioritize_sections(soru_turleri, profil)
    flags = profil.aktif_flags
    zengin_sorgu = _enrich_query(soru, profil, soru_turleri)

    logger.debug(f"Soru türleri: {soru_turleri}")
    logger.debug(f"Madde önceliği: {madde_onceligi}")
    logger.debug(f"Aktif flags: {flags}")

    # Her ilaç için ayrı plan (ya da ilaç belirtilmemişse tek genel plan)
    arama_planlari: list[SearchPlan] = []

    if hedef_ilaclar:
        for ilac in hedef_ilaclar:
            plan = SearchPlan(
                ilac_adi=ilac,
                madde_onceligi=madde_onceligi,
                patient_flags=flags,
                n_results=n_results,
                sorgu=zengin_sorgu,
            )
            arama_planlari.append(plan)
    else:
        # Genel arama — ilaç filtresi yok
        arama_planlari.append(SearchPlan(
            ilac_adi=None,
            madde_onceligi=madde_onceligi,
            patient_flags=flags,
            n_results=n_results,
            sorgu=zengin_sorgu,
        ))

    return AugmentedQuery(
        ozgun_soru=soru,
        soru_turleri=soru_turleri,
        arama_planlari=arama_planlari,
        hasta_ozeti=profil.ozet_metin(),
    )


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def _detect_question_types(soru: str, profil: PatientProfile) -> list[str]:
    """Sorunun hangi klinik kategorilere girdiğini tespit eder."""
    turleri = []

    if INTERACTION_KEYWORDS.search(soru):
        turleri.append("etkilesim")
    if CONTRAINDICATION_KEYWORDS.search(soru):
        turleri.append("kontrendikasyon")
    if DOSE_KEYWORDS.search(soru):
        turleri.append("doz")
    if PREGNANCY_KEYWORDS.search(soru) or profil.gebelik or profil.emzirme:
        turleri.append("gebelik_laktasyon")
    if SIDE_EFFECT_KEYWORDS.search(soru):
        turleri.append("yan_etki")
    if WARNING_KEYWORDS.search(soru):
        turleri.append("uyari")
    if OVERDOSE_KEYWORDS.search(soru):
        turleri.append("doz_asimi")

    # Hiçbiri eşleşmediyse genel sorgu
    if not turleri:
        turleri.append("genel")

    return turleri


def _prioritize_sections(soru_turleri: list[str], profil: PatientProfile) -> list[str]:
    """
    Soru türüne göre KÜB madde öncelik sırasını belirler.

    Mantık:
      - Her soru türü bir madde grubuna eşlenir
      - Hasta profili bazlı ekstralar eklenir (böbrek → 4.2, 4.4)
      - Kritik maddeler (4.3, 4.4, 4.5) her zaman dahil edilir
    """
    oncelikli: list[str] = []
    ek: list[str] = []

    for tur in soru_turleri:
        if tur == "etkilesim":
            oncelikli += ["4.5", "4.4"]
        elif tur == "kontrendikasyon":
            oncelikli += ["4.3", "4.4"]
        elif tur == "doz":
            oncelikli += ["4.2"]
        elif tur == "gebelik_laktasyon":
            oncelikli += ["4.6", "4.3"]
        elif tur == "yan_etki":
            oncelikli += ["4.8", "4.4"]
        elif tur == "uyari":
            oncelikli += ["4.4", "4.3"]
        elif tur == "doz_asimi":
            oncelikli += ["4.9"]
        else:  # genel
            oncelikli += ["4.3", "4.4", "4.5"]

    # Temel maddeler her zaman sonuçta olsun
    ek += ["4.3", "4.4", "4.5"]

    # Hasta profili ekstraları
    if profil.bobrek_yetmezligi:
        ek += ["4.2", "4.4"]
    if profil.karaciger_yetmezligi:
        ek += ["4.2", "4.4"]
    if profil.gebelik or profil.emzirme:
        ek += ["4.6"]
    if profil.geriyatrik:
        ek += ["4.2"]

    # Sırayı koru, tekrarları temizle
    seen = set()
    result = []
    for m in oncelikli + ek:
        if m not in seen:
            seen.add(m)
            result.append(m)

    return result


def _enrich_query(soru: str, profil: PatientProfile, soru_turleri: list[str]) -> str:
    """
    Hasta profilini sorguya ekleyerek daha spesifik bir retrieval sorgusu üretir.

    ChromaDB semantik arama için: kısa, yoğun bilgi içerikli metin daha iyi.
    """
    from src.agents.patient_profile import _lab_durumu

    parcalar = [soru]

    if profil.bobrek_yetmezligi:
        parcalar.append(f"böbrek yetmezliği GFR {profil.gfr}")
    if profil.karaciger_yetmezligi:
        parcalar.append(f"karaciğer yetmezliği Child-Pugh {profil.karaciger_skoru}")
    if profil.geriyatrik:
        parcalar.append(f"geriyatrik yaşlı hasta {profil.yas} yaş")
    if profil.pediyatrik:
        parcalar.append(f"pediyatrik çocuk hasta {profil.yas} yaş")
    if profil.gebelik:
        parcalar.append("gebelik hamile")
    if profil.emzirme:
        parcalar.append("laktasyon emzirme")

    if profil.mevcut_ilaclar and "etkilesim" in soru_turleri:
        ilac_metni = " ".join(profil.mevcut_ilaclar[:3])
        parcalar.append(f"ilaç etkileşimi {ilac_metni}")

    # Yan etki soruları için 4.8 semantik bağlamını güçlendir
    if "yan_etki" in soru_turleri:
        parcalar.append("yan etki istenmeyen etki advers reaksiyon güvenlilik profili")

    # Anormal lab değerlerini klinik terime çevir
    for anormal in profil.anormal_lab_degerleri:
        param = anormal["param"]
        durum = anormal["durum"]
        if param in ("ALT", "AST", "Bilirubin") and "yüksek" in durum:
            parcalar.append("karaciğer enzim yüksekliği hepatotoksisite")
        elif param == "Kreatinin" and "yüksek" in durum:
            parcalar.append("böbrek fonksiyon bozukluğu kreatinin yüksek")
        elif param == "K" and "yüksek" in durum:
            parcalar.append("hiperkalemi potasyum yüksek")
        elif param == "K" and "kritik_düşük" in durum:
            parcalar.append("hipokalemi potasyum düşük")
        elif param == "INR" and "yüksek" in durum:
            parcalar.append("antikoagülan INR yüksek kanama riski")
        elif param == "HbA1c" and "yüksek" in durum:
            parcalar.append("diyabet glisemik kontrol bozuk")

    return " ".join(parcalar)
