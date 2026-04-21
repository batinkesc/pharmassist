"""
DrugIdentity — sistemdeki bir ilacın kanonik kimliği.

Önceki durum:
  - ChromaDB normalize UPPERCASE ad kullanıyor
  - Neo4j ham KÜB adı (trademark dahil) saklıyor
  - Duplicate kontrolü 3 ayrı yerde, farklı mantıkla
  - INN eşleştirme her modülde farklı

Yeni durum:
  - DrugIdentity.canonical_id → her depoda aynı birincil anahtar
  - normalized_name → dosya adı, ChromaDB metadata
  - display_name → UI gösterimi (orijinal KÜB adı)
  - inn → INN propagation ve eşleştirme

canonical_id = normalize edilmiş adın SHA-1'inin ilk 12 karakteri.
Bu sayede aynı ilaç farklı PDF versiyonlarıyla gelse bile
canonical_id aynı kalır → duplicate tespiti güvenilir.
"""

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from src.data.normalization import normalize_drug_name


@dataclass(frozen=True)
class DrugIdentity:
    """
    Bir ilacın tüm depolarda (ChromaDB, Neo4j, dosya sistemi) kullanılan
    kanonik kimliği.

    Örnekler:
        canonical_id  : "a3f8c21b09d4"
        normalized_name: "BELOC_ZOK_MITE_25_MG_TABLET"
        display_name  : "BELOC ZOK® MITE 25 mg tablet"
        inn           : "metoprolol suksinat"
        atc_code      : "C07AB12" (opsiyonel)
    """

    canonical_id: str       # SHA-1[:12] — tüm depolarda birincil anahtar
    normalized_name: str    # boşluk→_, uppercase, trademark yok — dosya/key adı
    display_name: str       # orijinal KÜB adı — UI gösterimi
    inn: str                # lowercase etken madde — INN eşleştirme
    atc_code: Optional[str] = field(default=None)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @staticmethod
    def from_parsed(ilac_adi: str, etken_madde: str, atc_kodu: Optional[str] = None) -> "DrugIdentity":
        """
        pdf_parser çıktısından DrugIdentity oluşturur.

        normalized_name: normalize_drug_name() sonucu boşluklar "_" ile
        canonical_id   : normalized_name'in SHA-1[:12]'si
        inn            : etken_madde lowercase, extra whitespace temizlendi
        """
        normalized = normalize_drug_name(ilac_adi)          # "BELOC ZOK MITE 25 MG TABLET"
        file_slug = re.sub(r"\s+", "_", normalized)          # "BELOC_ZOK_MITE_25_MG_TABLET"
        file_slug = re.sub(r"[/\\:*?\"<>|]", "_", file_slug) # path-unsafe karakterler (ör. "500 MG / 4 MG")
        file_slug = re.sub(r"_+", "_", file_slug).strip("_") # çift alt çizgi temizle
        canonical_id = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
        inn_clean = re.sub(r"\s+", " ", etken_madde or "").strip().lower()

        return DrugIdentity(
            canonical_id=canonical_id,
            normalized_name=file_slug,
            display_name=ilac_adi.strip(),
            inn=inn_clean,
            atc_code=(atc_kodu or "").strip() or None,
        )

    # ------------------------------------------------------------------
    # Yardımcılar
    # ------------------------------------------------------------------

    def matches_query(self, query: str) -> bool:
        """
        Kullanıcı girdisinin bu ilaçla eşleşip eşleşmediğini hızlı kontrol eder.
        NameResolver'ın tam fuzzy mantığına alternatif değil, hızlı ön eleme.
        """
        q = normalize_drug_name(query)
        return (
            q == self.normalized_name
            or self.normalized_name.startswith(q.split("_")[0])
            or q in self.normalized_name
        )

    def __str__(self) -> str:
        return f"{self.display_name} [{self.canonical_id}]"
