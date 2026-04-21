"""
QualityGate — KÜB parse çıktısının kalite kapısı.

Önceki durum:
  - DrugValidator mevcut ama bulk_ingest.py onu çağırmıyor (ölü kod)
  - Parse QA mantığı bulk_ingest.py'da inline, hardcoded sabitlerle
  - Quarantine raporu informal, yapılandırılmamış

Yeni durum:
  - IngestionPipeline her zaman QualityGate.check() çağırır
  - DrugValidator buraya entegre edildi
  - QualityResult yapılandırılmış: should_quarantine, flags, score
  - Sabitler ContentPolicy'den gelir
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from src.core.content_policy import POLICY
from src.data.drug_validation import DrugValidator


# ------------------------------------------------------------------
# Quarantine flag kodları
# ------------------------------------------------------------------

class QFlag:
    DRUG_NAME_MISSING   = "DRUG_NAME_MISSING"
    SECTION_43_MISSING  = "SECTION_43_MISSING"
    SECTION_45_MISSING  = "SECTION_45_MISSING"
    SECTION_43_SHORT    = "SECTION_43_SHORT"
    SECTION_45_SHORT    = "SECTION_45_SHORT"
    TOTAL_CONTENT_SHORT = "TOTAL_CONTENT_SHORT"
    ENCODING_ERROR      = "ENCODING_ERROR"
    NO_CHUNKS           = "NO_CHUNKS"
    # Uyarı (karantina değil, log'a düşer)
    LOW_INTERACTION_HINT = "LOW_INTERACTION_HINT"   # extraction sonrası sıfır ilişki


# ------------------------------------------------------------------
# Sonuç veri yapısı
# ------------------------------------------------------------------

@dataclass
class QualityResult:
    """
    Bir KÜB için kalite kapısı sonucu.

    should_quarantine=True  → IngestionPipeline karantinaya gönderir
    should_quarantine=False → devam eder, ama flags uyarı içerebilir
    """
    should_quarantine: bool
    flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    score: float = 1.0      # 0-1 kalite skoru; 1=mükemmel, 0=karantina

    def summary(self) -> str:
        status = "QUARANTINE" if self.should_quarantine else "PASS"
        lines = [f"[QualityGate] {status} | score={self.score:.2f}"]
        for f in self.flags:
            lines.append(f"  ✗ {f}")
        for w in self.warnings:
            lines.append(f"  ⚠ {w}")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Ana sınıf
# ------------------------------------------------------------------

class QualityGate:
    """
    KÜB parse sonucunu kontrol eder; karantina / geçiş kararı verir.

    Kullanım:
        gate = QualityGate()
        result = gate.check(parse_data)
        if result.should_quarantine:
            ...
    """

    # Karantina gerektiren minimum eşikler (ContentPolicy'den alınsaydı
    # burada tekrar edilmez; ancak bu değerler kalitatif QA kararı,
    # ContentPolicy ise boyut/performans kararı — ayrı tutuyoruz)
    _MIN_SECTION_CHARS = 100
    _MIN_TOTAL_CHARS = 500

    def check(self, parse_data: dict[str, Any]) -> QualityResult:
        """
        parse_data: pdf_parser.py çıktısı (ilac_adi, etken_madde, chunks, ...)
        """
        flags: list[str] = []
        warnings: list[str] = []

        # --- 1. Mevcut DrugValidator entegrasyonu ---
        validator = DrugValidator(parse_data)
        validator.validate()
        for err in validator.errors:
            flags.append(f"{err.code}: {err.message}")
        for warn in validator.warnings:
            warnings.append(f"{warn.code}: {warn.message}")

        # --- 2. Kritik bölüm içerik kontrolü ---
        sections = self._extract_sections(parse_data.get("chunks", []))

        for sec_no, flag_missing, flag_short in [
            ("4.3", QFlag.SECTION_43_MISSING, QFlag.SECTION_43_SHORT),
            ("4.5", QFlag.SECTION_45_MISSING, QFlag.SECTION_45_SHORT),
        ]:
            content = sections.get(sec_no, "")
            if not content:
                if flag_missing not in flags:
                    flags.append(flag_missing)
            elif len(content) < self._MIN_SECTION_CHARS:
                flags.append(f"{flag_short}: {len(content)} chars < {self._MIN_SECTION_CHARS}")

        # --- 3. Toplam içerik ---
        total = sum(len(c.get("icerik", "")) for c in parse_data.get("chunks", []))
        if total < self._MIN_TOTAL_CHARS:
            flags.append(f"{QFlag.TOTAL_CONTENT_SHORT}: {total} chars")

        # --- 4. Karantina kararı ---
        # Sadece "error" seviyesindeki flag'ler (validasyon hatası veya
        # kritik bölüm eksikliği) karantinayı tetikler.
        critical_flags = [
            f for f in flags
            if any(k in f for k in [
                "MISSING", "TOO_SHORT", "DRUG_NAME", "ENCODING",
                "NO_CHUNKS", "TOTAL_CONTENT_SHORT",
            ])
        ]
        should_quarantine = len(critical_flags) > 0

        # Kalite skoru: flag'ler arttıkça düşer
        score = max(0.0, 1.0 - len(flags) * 0.15)

        result = QualityResult(
            should_quarantine=should_quarantine,
            flags=flags,
            warnings=warnings,
            score=score,
        )

        if should_quarantine:
            logger.warning(f"QualityGate QUARANTINE: {parse_data.get('ilac_adi','?')}\n{result.summary()}")
        elif flags:
            logger.info(f"QualityGate PASS (with warnings): {parse_data.get('ilac_adi','?')}")

        return result

    @staticmethod
    def _extract_sections(chunks: list[dict]) -> dict[str, str]:
        """Chunk listesinden bölüm no → birleşik içerik sözlüğü oluşturur."""
        sections: dict[str, str] = {}
        for chunk in chunks:
            sec = chunk.get("madde_no", "")
            if sec:
                sections[sec] = sections.get(sec, "") + chunk.get("icerik", "")
        return sections

    def flag_low_interactions(self, ilac_adi: str, interaction_count: int) -> None:
        """
        Extraction sonrası sıfır ilişki tespitinde çağrılır.
        Karantina tetiklemez — sadece log'a düşer.
        Corpus sınırlaması mı, extraction hatası mı ayırt etmek için
        gelecekte analiz yapılabilir.
        """
        if interaction_count == 0:
            logger.info(
                f"[QFlag.LOW_INTERACTION_HINT] {ilac_adi}: "
                "0 etkileşim çıkarıldı — corpus sınırlaması veya kısa 4.5 bölümü olabilir"
            )
