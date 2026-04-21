"""
PharmAssist tiplendirilmiş exception hiyerarşisi.

Önceki durum: tüm hatalar ya Exception ya da sessiz geçiş.
Yeni durum  : her hata katmanı kendi exception'ını fırlatır;
              üst katmanlar tip üzerinden yakalar.
"""


class PharmAssistError(Exception):
    """Tüm uygulama hatalarının tabanı."""


# ---------------------------------------------------------------------------
# Ingestion katmanı
# ---------------------------------------------------------------------------

class IngestionError(PharmAssistError):
    """PDF okuma, parse veya yükleme hatası."""


class QuarantineError(IngestionError):
    """
    KÜB kalite eşiğini geçemedi — karantinaya alınmalı.
    .reason: neden karantina
    .drug_name: normalize ilaç adı (varsa)
    """
    def __init__(self, reason: str, drug_name: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.drug_name = drug_name


class DuplicateIngestionError(IngestionError):
    """Aynı canonical_id zaten sistemde mevcut."""
    def __init__(self, canonical_id: str, drug_name: str):
        super().__init__(f"Duplicate: {drug_name} ({canonical_id})")
        self.canonical_id = canonical_id
        self.drug_name = drug_name


# ---------------------------------------------------------------------------
# Extraction katmanı
# ---------------------------------------------------------------------------

class ExtractionError(PharmAssistError):
    """LLM structured extraction başarısız."""


class ExtractionTimeoutError(ExtractionError):
    """LM Studio timeout."""


class ExtractionParseError(ExtractionError):
    """LLM çıktısı JSON parse edilemedi."""


# ---------------------------------------------------------------------------
# Resolver katmanı
# ---------------------------------------------------------------------------

class ResolverError(PharmAssistError):
    """İsim çözümleme hatası."""


class DrugNotFoundError(ResolverError):
    """İsim hiçbir eşleşme döndürmedi."""
    def __init__(self, query: str):
        super().__init__(f"Drug not found: '{query}'")
        self.query = query


# ---------------------------------------------------------------------------
# Graph katmanı
# ---------------------------------------------------------------------------

class GraphError(PharmAssistError):
    """Neo4j sorgu veya bağlantı hatası."""


class GraphConnectionError(GraphError):
    """Neo4j'e bağlanılamadı."""
