"""
Drug Validation Framework — Yeni ilaç eklenmesini sorunsuz hale getir

Pipeline: PDF Parse → Validate → Normalize → Index (ChromaDB + Neo4j)

Her adımda Quality Gate:
  1. Parse çıktı format kontrolü
  2. İlaç adı ve kritik bölümleri kontrol
  3. Normalizasyon ve veri temizliği
  4. Final: DB sorunsuz ekleme

Kullanım:
  validator = DrugValidator(parse_result)
  if validator.validate():
      print(validator.errors)
      return None
  normalized = validator.normalize()
  # ChromaDB ve Neo4j'ye ekle
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from loguru import logger

from .normalization import normalize_drug_name, get_base_name


@dataclass
class ValidationError:
    """Validasyon hatası"""
    level: str  # "error" | "warning"
    code: str  # Hata kodu (ör: "MISSING_SECTION_4_3")
    message: str
    field: Optional[str] = None
    value: Any = None


@dataclass
class DrugValidationResult:
    """Validasyon sonucu"""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    normalized_name: Optional[str] = None

    def is_critical(self) -> bool:
        """Kritik hata var mı?"""
        return any(e.level == "error" for e in self.errors)

    def summary(self) -> str:
        """Özet raporu"""
        lines = []
        if self.valid:
            lines.append("✓ Validation PASSED")
        else:
            lines.append("✗ Validation FAILED")

        if self.errors:
            lines.append(f"  Errors: {len(self.errors)}")
            for e in self.errors[:3]:
                lines.append(f"    - [{e.code}] {e.message}")

        if self.warnings:
            lines.append(f"  Warnings: {len(self.warnings)}")
            for w in self.warnings[:3]:
                lines.append(f"    - [{w.code}] {w.message}")

        return "\n".join(lines)


class DrugValidator:
    """
    İlaç validasyonu — parse sonucundan DB'ye kadar
    """

    # Konfigürasyon
    MIN_SECTION_CHARS = 100  # 4.3, 4.5 minimum karakter
    MIN_TOTAL_CHARS = 500  # Toplam minimum
    CRITICAL_SECTIONS = ["4.3", "4.5"]  # Zorunlu bölümler

    def __init__(self, parse_result: Dict[str, Any]):
        """
        Args:
            parse_result: PDF parser çıktısı
        """
        self.parse_result = parse_result
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def validate(self) -> bool:
        """
        Validasyon sürecini çalıştır

        Returns:
            True if valid (no errors), False if has errors
        """
        self.errors.clear()
        self.warnings.clear()

        # Validasyon kuralları
        self._validate_drug_name()
        self._validate_structure()
        self._validate_sections()
        self._validate_content_quality()
        self._validate_encoding()

        return not self.is_critical()

    def normalize(self) -> Dict[str, Any]:
        """
        Veriyi normalize et ve temizle

        Returns:
            Cleaned parse result
        """
        result = dict(self.parse_result)

        # İlaç adını normalize et
        original_name = result.get("ilac_adi", "")
        normalized_name = normalize_drug_name(original_name)

        if original_name != normalized_name:
            logger.info(f"Normalizing: '{original_name}' → '{normalized_name}'")
            result["ilac_adi"] = normalized_name

        # Chunks'taki ilac_adi'yi de güncelle
        for chunk in result.get("chunks", []):
            chunk["ilac_adi"] = normalized_name

        return result

    def get_result(self) -> DrugValidationResult:
        """Validasyon sonucunu döndür"""
        return DrugValidationResult(
            valid=not self.is_critical(),
            errors=self.errors,
            warnings=self.warnings,
            normalized_name=normalize_drug_name(
                self.parse_result.get("ilac_adi", "")
            )
        )

    def is_critical(self) -> bool:
        """Kritik hata var mı?"""
        return any(e.level == "error" for e in self.errors)

    # ====== Validasyon Kuralları ======

    def _validate_drug_name(self):
        """İlaç adı validasyonu"""
        ilac_adi = self.parse_result.get("ilac_adi", "").strip()

        # Boş veya bilinmeyen
        if not ilac_adi or ilac_adi in ("UNKNOWN", "Bilinmeyen İlaç", ""):
            self.errors.append(ValidationError(
                level="error",
                code="DRUG_NAME_MISSING",
                message="İlaç adı boş veya bilinmeyen",
                field="ilac_adi"
            ))
            return

        # Çok kısa
        if len(ilac_adi) < 3:
            self.errors.append(ValidationError(
                level="error",
                code="DRUG_NAME_TOO_SHORT",
                message=f"İlaç adı çok kısa: '{ilac_adi}' (min 3 karakter)",
                field="ilac_adi",
                value=ilac_adi
            ))

        # Çok uzun
        if len(ilac_adi) > 256:
            self.warnings.append(ValidationError(
                level="warning",
                code="DRUG_NAME_VERY_LONG",
                message=f"İlaç adı çok uzun: {len(ilac_adi)} chars",
                field="ilac_adi"
            ))

    def _validate_structure(self):
        """Parse çıktı yapısı validasyonu"""
        required_fields = ["ilac_adi", "chunks"]

        for field in required_fields:
            if field not in self.parse_result:
                self.errors.append(ValidationError(
                    level="error",
                    code=f"MISSING_FIELD_{field.upper()}",
                    message=f"Gerekli alan eksik: {field}",
                    field=field
                ))

        # Chunks list olmalı
        chunks = self.parse_result.get("chunks", [])
        if not isinstance(chunks, list):
            self.errors.append(ValidationError(
                level="error",
                code="CHUNKS_NOT_LIST",
                message="chunks alan list olmalı",
                field="chunks",
                value=type(chunks).__name__
            ))

    def _validate_sections(self):
        """Kritik bölümler validasyonu"""
        chunks = self.parse_result.get("chunks", [])

        # Bölümleri gruplaştır
        sections_found = {}
        for chunk in chunks:
            madde_no = chunk.get("madde_no", "")
            icerik = chunk.get("icerik", "")

            if madde_no not in sections_found:
                sections_found[madde_no] = ""
            sections_found[madde_no] += icerik

        # Zorunlu bölümleri kontrol et
        for section in self.CRITICAL_SECTIONS:
            if section not in sections_found:
                self.errors.append(ValidationError(
                    level="error",
                    code=f"MISSING_SECTION_{section}",
                    message=f"Kritik bölüm eksik: Madde {section}",
                    field="sections"
                ))
            else:
                content_len = len(sections_found[section])
                if content_len < self.MIN_SECTION_CHARS:
                    self.errors.append(ValidationError(
                        level="error",
                        code=f"SECTION_{section}_TOO_SHORT",
                        message=f"Madde {section} çok kısa: {content_len} chars (min {self.MIN_SECTION_CHARS})",
                        field=section,
                        value=content_len
                    ))

    def _validate_content_quality(self):
        """İçerik kalitesi validasyonu"""
        chunks = self.parse_result.get("chunks", [])

        # Toplam içerik
        total_chars = sum(len(c.get("icerik", "")) for c in chunks)

        if total_chars < self.MIN_TOTAL_CHARS:
            self.errors.append(ValidationError(
                level="error",
                code="TOTAL_CONTENT_TOO_SHORT",
                message=f"Toplam içerik çok az: {total_chars} chars (min {self.MIN_TOTAL_CHARS})",
                field="total_content",
                value=total_chars
            ))

        # Boş chunk sayısı
        empty_chunks = sum(1 for c in chunks if not c.get("icerik", "").strip())
        if empty_chunks > len(chunks) * 0.2:  # %20'den fazla boş
            self.warnings.append(ValidationError(
                level="warning",
                code="TOO_MANY_EMPTY_CHUNKS",
                message=f"Çok sayıda boş chunk: {empty_chunks}/{len(chunks)} (%{empty_chunks*100//len(chunks)})",
                field="chunks"
            ))

    def _validate_encoding(self):
        """Encoding validasyonu"""
        ilac_adi = self.parse_result.get("ilac_adi", "")

        # Invalid UTF-8 sequences
        try:
            ilac_adi.encode('utf-8').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            self.errors.append(ValidationError(
                level="error",
                code="INVALID_ENCODING",
                message="İlaç adında geçersiz UTF-8 karakteri",
                field="ilac_adi"
            ))

        # Control characters
        control_chars = [c for c in ilac_adi if ord(c) < 32 and c not in '\n\t']
        if control_chars:
            self.warnings.append(ValidationError(
                level="warning",
                code="CONTROL_CHARACTERS",
                message=f"İlaç adında kontrol karakterleri: {repr(control_chars)}",
                field="ilac_adi"
            ))


def validate_and_normalize_drug(parse_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Yeni ilaç parse sonucunu validate et ve normalize et

    Returns:
        Normalized result if valid, None if validation fails
    """
    validator = DrugValidator(parse_result)

    if not validator.validate():
        result = validator.get_result()
        logger.error(f"Drug validation failed:\n{result.summary()}")
        return None

    normalized = validator.normalize()
    logger.info(f"✓ Drug validated and normalized: {normalized.get('ilac_adi')}")

    return normalized
