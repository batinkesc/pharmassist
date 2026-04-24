"""
ContentPolicy — sistemdeki tüm boyut ve limit kararları tek dosyada.

Önceki durum: 8 farklı dosyada hardcoded sabit (1800, 2000, 512, 9, 8...).
Yeni durum  : tüm kod buradan import eder; tek değişiklik her yere yansır.

Kullanım:
    from src.core.content_policy import POLICY
    window = POLICY.chunk_window_chars
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ContentPolicy:
    # ------------------------------------------------------------------
    # Parse / ingestion aşaması
    # ------------------------------------------------------------------

    # pdf_parser.py — metadata kırpma üst limitleri
    drug_name_max_chars: int = 200       # eski: 120 (çok kısaydı)
    etken_madde_max_chars: int = 500     # eski: 300

    # kub_to_graph.py — Section.icerik Neo4j'de tam saklanır
    # 0 = sınır yok (eski kod 2000 ile kırpıyordu, tüm içerik kayboluyordu)
    section_storage_max_chars: int = 0

    # ------------------------------------------------------------------
    # LLM structured extraction (kub_extractor.py)
    # ------------------------------------------------------------------
    extraction_section_43_chars: int = 1000   # prompt'a gönderilen 4.3 uzunluğu
    extraction_section_45_chars: int = 2000   # prompt'a gönderilen 4.5 uzunluğu
    extraction_max_tokens: int = 2000   # 768 → 2000: uzun etkileşim listelerinde JSON kesiliyor (insülin vb.)
    extraction_timeout_sec: int = 180
    extraction_max_retries: int = 3           # bağlantı hatası retry

    # Sliding window — section 4.5 bu sınırı aşarsa pencere pencere işlenir
    extraction_window_chars: int = 2000       # her pencere max uzunluğu (extraction_section_45_chars ile eşit)
    extraction_window_overlap: int = 400      # pencereler arası overlap (cümle kesilmesini önler)

    # severity pencere taraması (kub_to_graph._extract_severity)
    severity_window_chars: int = 2000         # eski: 1500

    # chunk başına max mention (kub_to_graph.extract_interactions)
    max_mentions_per_chunk: int = 25          # eski: 10 (çok ilaçlı bölümlerde kayıp vardı)

    # ------------------------------------------------------------------
    # RAG / retrieval aşaması (rag_engine.py)
    # ------------------------------------------------------------------
    chunk_window_chars: int = 4000            # eski: 2500 — 4.6 laktasyon (idx 2693) gibi uzun bölümler kesilmesin
    max_chunks_per_query: int = 15            # eski: 12 — LLM'e daha geniş bağlam
    rerank_pool_size: int = 30               # eski: 20 — reranker'a daha fazla aday
    min_score_threshold: float = 0.50        # eski: 0.55 — recall için gevşetildi

    # ------------------------------------------------------------------
    # Graf bağlamı (combi_retriever.py) — LM Studio overflow fix
    # ------------------------------------------------------------------
    max_contraindications_in_context: int = 20   # CO-DIOVAN 101 → 20
    max_interactions_in_context: int = 15
    max_patient_interactions_in_context: int = 10

    # ------------------------------------------------------------------
    # Evaluation (ragas_eval.py) — runtime ile aynı tutulur, drift engeli
    # ------------------------------------------------------------------
    eval_max_contexts: int = 12              # eski: 9 — max_chunks_per_query ile paralel
    eval_max_chunk_chars: int = 4000          # chunk_window_chars ile eşit


# Tek global instance — tüm sistem bu nesneyi import eder
POLICY = ContentPolicy()
