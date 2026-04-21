"""
Hasta profili şeması ve doğrulama.

Örnek kullanım:
    profile = PatientProfile(
        yas=68,
        cinsiyet="erkek",
        kilo=75.5,
        gfr=38,
        karaciger_skoru=None,
        mevcut_ilaclar=["Metformin 1000 mg", "Ramipril 10 mg", "Atorvastatin 20 mg"],
        alerjiler=["penisilin"],
        endikasyonlar=["Tip 2 Diyabet", "Hipertansiyon", "Hiperlipidemi"],
        lab_degerleri={"ALT": 120, "K": 5.6, "HbA1c": 8.2},
    )
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Lab değeri referans eşikleri (evrensel klinik standartlar)
# ---------------------------------------------------------------------------

LAB_ESIKLERI = {
    "ALT":      {"normal_ust": 40,   "kritik_kat": 3,   "birim": "U/L",        "flag": "hepatic"},
    "AST":      {"normal_ust": 40,   "kritik_kat": 3,   "birim": "U/L",        "flag": "hepatic"},
    "GGT":      {"normal_ust": 60,   "kritik_kat": 3,   "birim": "U/L",        "flag": "hepatic"},
    "ALP":      {"normal_ust": 120,  "kritik_kat": 3,   "birim": "U/L",        "flag": "hepatic"},
    "Kreatinin":{"kritik_ust": 1.5,                     "birim": "mg/dL",      "flag": "renal"},
    "K":        {"kritik_ust": 5.5,  "kritik_alt": 3.5, "birim": "mEq/L",      "flag": None},
    "Na":       {"kritik_ust": 150,  "kritik_alt": 130, "birim": "mEq/L",      "flag": None},
    "INR":      {"kritik_ust": 2.5,                     "birim": "",           "flag": None},
    "HbA1c":    {"kritik_ust": 9.0,                     "birim": "%",          "flag": None},
    "Hemoglobin":{"kritik_alt": 8.0,                    "birim": "g/dL",       "flag": None},
    "Trombosit":{"kritik_alt": 50,                      "birim": "x10³/µL",    "flag": None},
    "Bilirubin":{"kritik_ust": 2.0,                     "birim": "mg/dL",      "flag": "hepatic"},
}


def _lab_durumu(param: str, deger: float) -> str:
    """
    Sayısal lab değerini nitel etikete çevirir.
    Dönüş: "normal" | "yüksek" | "kritik_yüksek" | "düşük" | "kritik_düşük"
    """
    esik = LAB_ESIKLERI.get(param)
    if not esik:
        return "bilinmiyor"

    birim = esik.get("birim", "")

    # Hepatik enzimler — kat bazlı
    if "kritik_kat" in esik and "normal_ust" in esik:
        kritik_sinir = esik["normal_ust"] * esik["kritik_kat"]
        if deger >= kritik_sinir:
            return "kritik_yüksek"
        if deger > esik["normal_ust"]:
            return "yüksek"
        return "normal"

    # Üst sınır kontrolü
    if "kritik_ust" in esik and deger >= esik["kritik_ust"]:
        return "kritik_yüksek"

    # Alt sınır kontrolü
    if "kritik_alt" in esik and deger <= esik["kritik_alt"]:
        return "kritik_düşük"

    return "normal"


@dataclass
class PatientProfile:
    """
    Klinik karar desteği için hasta profili.

    Alanlar:
        yas:              Yaş (yıl)
        cinsiyet:         "erkek" | "kadın" | "belirtilmemiş"
        kilo:             Kilo (kg) — None ise bilinmiyor
        gfr:              eGFR (mL/dak/1.73 m²) — None ise böbrek fonksiyonu bilinmiyor
        karaciger_skoru:  Child-Pugh skoru ("A" | "B" | "C") — None ise bilinmiyor
        mevcut_ilaclar:   Kullanılan ilaçlar listesi (tam adıyla)
        alerjiler:        Bilinen alerjiler
        endikasyonlar:    Aktif tanılar / endikasyonlar
        gebelik:          True ise gebe
        emzirme:          True ise emziriyor
        lab_degerleri:    {"ALT": 120, "K": 5.6, "HbA1c": 8.2, ...}
        notlar:           Ek klinik notlar
    """

    yas: int = 0
    cinsiyet: str = "belirtilmemiş"
    kilo: Optional[float] = None
    gfr: Optional[float] = None
    karaciger_skoru: Optional[str] = None
    mevcut_ilaclar: list[str] = field(default_factory=list)
    alerjiler: list[str] = field(default_factory=list)
    endikasyonlar: list[str] = field(default_factory=list)
    gebelik: bool = False
    emzirme: bool = False
    lab_degerleri: dict[str, float] = field(default_factory=dict)
    notlar: str = ""
    # Override flag'ler — True verilirse yaş tabanlı otomatik türetimi geçersiz kılar
    pediyatrik_override: Optional[bool] = None
    geriyatrik_override: Optional[bool] = None

    # -----------------------------------------------------------------------
    # Türetilmiş özellikler
    # -----------------------------------------------------------------------

    @property
    def bobrek_yetmezligi(self) -> bool:
        """GFR < 60 → böbrek yetmezliği mevcut."""
        return self.gfr is not None and self.gfr < 60

    @property
    def bobrek_evresi(self) -> str:
        """CKD evresini döner (GFR biliniyorsa)."""
        if self.gfr is None:
            return "bilinmiyor"
        if self.gfr >= 90:
            return "Evre 1 (G1, GFR ≥90)"
        if self.gfr >= 60:
            return "Evre 2 (G2, GFR 60-89)"
        if self.gfr >= 45:
            return "Evre 3a (G3a, GFR 45-59)"
        if self.gfr >= 30:
            return "Evre 3b (G3b, GFR 30-44)"
        if self.gfr >= 15:
            return "Evre 4 (G4, GFR 15-29)"
        return "Evre 5 (G5, GFR <15 — terminal dönem)"

    @property
    def karaciger_yetmezligi(self) -> bool:
        """Child-Pugh B veya C → karaciğer yetmezliği."""
        return self.karaciger_skoru in ("B", "C")

    @property
    def geriyatrik(self) -> bool:
        """65 yaş ve üzeri → geriyatrik. Override True ise yaştan bağımsız aktif."""
        if self.geriyatrik_override is not None:
            return self.geriyatrik_override
        return self.yas >= 65

    @property
    def pediyatrik(self) -> bool:
        """18 yaş altı → pediatrik. Override True ise yaştan bağımsız aktif."""
        if self.pediyatrik_override is not None:
            return self.pediyatrik_override
        return self.yas < 18

    @property
    def aktif_flags(self) -> list[str]:
        """
        ChromaDB filtresi için aktif patient_flags listesi döner.
        Değerler: "renal", "hepatic", "pediatric", "geriatric"
        Lab değerlerinden türetilen ek flag'ler de eklenir.
        """
        flags = []
        if self.bobrek_yetmezligi:
            flags.append("renal")
        if self.karaciger_yetmezligi:
            flags.append("hepatic")
        if self.pediyatrik:
            flags.append("pediatric")
        if self.geriyatrik:
            flags.append("geriatric")

        # Lab değerlerinden ek flag
        for param, deger in self.lab_degerleri.items():
            durum = _lab_durumu(param, deger)
            if durum in ("yüksek", "kritik_yüksek", "kritik_düşük"):
                esik = LAB_ESIKLERI.get(param, {})
                flag = esik.get("flag")
                if flag and flag not in flags:
                    flags.append(flag)

        return flags

    @property
    def anormal_lab_degerleri(self) -> list[dict]:
        """
        Normal dışı lab değerlerini döner.
        [{"param": "ALT", "deger": 120, "birim": "U/L", "durum": "kritik_yüksek"}, ...]
        """
        anormal = []
        for param, deger in self.lab_degerleri.items():
            durum = _lab_durumu(param, deger)
            if durum != "normal" and durum != "bilinmiyor":
                esik = LAB_ESIKLERI.get(param, {})
                anormal.append({
                    "param": param,
                    "deger": deger,
                    "birim": esik.get("birim", ""),
                    "durum": durum,
                })
        return anormal

    def ozet_metin(self) -> str:
        """
        Hasta profilini klinisyen-dostu kısa metin olarak döner.
        Prompt'a eklemek için kullanılır.
        """
        satirlar = []
        satirlar.append(f"Yaş: {self.yas}, Cinsiyet: {self.cinsiyet}")

        if self.gfr is not None:
            satirlar.append(f"Böbrek fonksiyonu: GFR={self.gfr} mL/dak/1.73m² ({self.bobrek_evresi})")
        else:
            satirlar.append("Böbrek fonksiyonu: bilinmiyor")

        if self.karaciger_skoru:
            satirlar.append(f"Karaciğer fonksiyonu: Child-Pugh {self.karaciger_skoru}")

        if self.gebelik:
            satirlar.append("Durum: GEBELİK")
        if self.emzirme:
            satirlar.append("Durum: EMZİRİYOR")

        if self.mevcut_ilaclar:
            satirlar.append(f"Mevcut ilaçlar: {', '.join(self.mevcut_ilaclar)}")

        if self.alerjiler:
            satirlar.append(f"Alerjiler: {', '.join(self.alerjiler)}")

        if self.endikasyonlar:
            satirlar.append(f"Tanılar: {', '.join(self.endikasyonlar)}")

        # Lab değerleri — anormal olanlar öne çıkar
        if self.lab_degerleri:
            lab_satirlari = []
            anormal = {a["param"] for a in self.anormal_lab_degerleri}
            for param, deger in self.lab_degerleri.items():
                esik = LAB_ESIKLERI.get(param, {})
                birim = esik.get("birim", "")
                durum = _lab_durumu(param, deger)
                if param in anormal:
                    durum_etiket = {
                        "yüksek": "↑",
                        "kritik_yüksek": "↑↑ KRİTİK",
                        "düşük": "↓",
                        "kritik_düşük": "↓↓ KRİTİK",
                    }.get(durum, "")
                    lab_satirlari.append(f"{param}: {deger} {birim} {durum_etiket}".strip())
                else:
                    lab_satirlari.append(f"{param}: {deger} {birim}".strip())
            satirlar.append(f"Laboratuvar: {' | '.join(lab_satirlari)}")

        if self.notlar:
            satirlar.append(f"Notlar: {self.notlar}")

        return "\n".join(satirlar)

    @classmethod
    def from_dict(cls, data: dict) -> "PatientProfile":
        """Sözlükten PatientProfile oluşturur."""
        return cls(
            yas=data.get("yas", 0),
            cinsiyet=data.get("cinsiyet", "belirtilmemiş"),
            gfr=data.get("gfr"),
            karaciger_skoru=data.get("karaciger_skoru"),
            mevcut_ilaclar=data.get("mevcut_ilaclar", []),
            alerjiler=data.get("alerjiler", []),
            endikasyonlar=data.get("endikasyonlar", []),
            gebelik=data.get("gebelik", False),
            emzirme=data.get("emzirme", False),
            lab_degerleri=data.get("lab_degerleri", {}),
            notlar=data.get("notlar", ""),
        )

    def to_dict(self) -> dict:
        """PatientProfile'ı sözlüğe çevirir."""
        return {
            "yas": self.yas,
            "cinsiyet": self.cinsiyet,
            "gfr": self.gfr,
            "karaciger_skoru": self.karaciger_skoru,
            "mevcut_ilaclar": self.mevcut_ilaclar,
            "alerjiler": self.alerjiler,
            "endikasyonlar": self.endikasyonlar,
            "gebelik": self.gebelik,
            "emzirme": self.emzirme,
            "lab_degerleri": self.lab_degerleri,
            "notlar": self.notlar,
        }
