# PharmAssist — Mimari Standartlar (v1.1)

**Versiyon:** 1.1 (Implementasyon tamamlandı)  
**Son Güncelleme:** 2026-04-19  
**Durum:** ACTIVE — bu belge planı değil gerçek sistemi tanımlar.

---

## 1. Temel İlkeler

### 1.1 Kanonik İlaç Kimliği

Her ilaç için tek bir `canonical_id` vardır. Bu ID tüm depolarda aynıdır:

```python
# src/core/drug_record.py
identity = DrugIdentity.from_parsed(ilac_adi, etken_madde)
# identity.canonical_id  → "a3f8c21b09d4"  (SHA-1[:12])
# identity.normalized_name → "BELOC_ZOK_25_MG_TABLET"
# identity.display_name  → "BELOC ZOK® 25 mg tablet"
# identity.inn           → "metoprolol suksinat"
```

**Kural:** Hiçbir modül ilaç adını kendi fuzzy mantığıyla eşleştirmez. Her zaman `NameResolver.resolve()` çağrılır.

### 1.2 ContentPolicy — Tek Boyut Politikası

Tüm boyut ve limit kararları `src/core/content_policy.py` dosyasındaki `POLICY` nesnesinden gelir.

```python
from src.core.content_policy import POLICY

# Kullanım örneği
window = POLICY.chunk_window_chars       # 2500 — rag_engine
max_ki = POLICY.max_contraindications_in_context  # 20 — combi_retriever
max_ctx = POLICY.eval_max_contexts       # 9 — ragas_eval
```

**Kural:** Hiçbir dosyaya hardcoded boyut sabiti eklenmez. `POLICY` güncellenir.

### 1.3 Ingestion — Tek Entry Point

```bash
# Doğru kullanım
.venv/Scripts/python -m src.pipeline.ingestion_pipeline --pdf data/raw_kub/ALTIZEM.pdf
.venv/Scripts/python -m src.pipeline.ingestion_pipeline --all
.venv/Scripts/python -m src.pipeline.ingestion_pipeline --all --force

# Hatalı kullanım (artık kullanılmaz)
# python scripts/bulk_ingest.py       ← ESKİ
# python scripts/rebuild_interactions.py ← ESKİ
# python scripts/propagate_inn_interactions.py ← ESKİ
```

**Kural:** Yeni ilaç eklemek için yalnızca `IngestionPipeline` kullanılır. Pipeline QualityGate, KUBExtractor ve INNResolver'ı otomatik çalıştırır.

---

## 2. Veri Akışı

### 2.1 Ingestion (PDF → DB)

```
PDF
 └→ KUBParser.parse()
       ↓ ParsedData {ilac_adi, etken_madde, chunks, sections}
 └→ DrugIdentity.from_parsed()
       ↓ canonical_id (SHA-1[:12] of normalized_name)
 └→ _already_exists(canonical_id) → SKIP veya devam
 └→ QualityGate.check()
       ↓ PASS → devam | FAIL → quarantine/*.md
 └→ KUBExtractor.extract()
       ↓ [DrugInteraction(drug_b, severity, section, confidence)]
       ↓ severity=unknown → retry (1 kez)
       ↓ Pydantic validation → hatalı kayıt drop
 └→ INNResolver.propagate_to_new_drug()
       ↓ Aynı INN grubundan kopyalanan etkileşimler (is_propagated=True)
 └→ AtomicWriter
       ├── ChromaDB: chunks + canonical_id metadata
       └── Neo4j: Drug node + Section node + INTERACTS_WITH
```

### 2.2 RAG Sorgusu (Query → Yanıt)

```
Kullanıcı Sorusu + PatientProfile
 └→ query_augmentor.augment_query()
       ↓ AugmentedQuery {soru_turu, oncelikli_maddeler, zenginlestirilmis_sorgu}
 └→ chroma_store.batch_search()
       ↓ Chunk listesi (cross-encoder reranked, top-12, score>0.55)
 └→ combi_retriever.build_graph_context()
       ↓ GraphContext (max 20 KI, max 15 IW — ContentPolicy)
       ↓ NameResolver ile eşleştirme
 └→ cumulative_risk.analyze() + cyp450_mapper.get_cyp_interactions()
       ↓ Deterministik analizler (LLM'den bağımsız)
 └→ rag_engine._build_user_prompt()
       ↓ Chunk window: 2500 char (ContentPolicy)
 └→ LLM (Claude Haiku / LM Studio)
       ↓ validate_response() → "güvenlidir" yasağı
 └→ RAGResponse {yanit, kaynaklar, risk_ozetleri}
```

---

## 3. Neo4j Veri Modeli

### 3.1 Node Tipleri

```cypher
(:Drug {
  name: "BELOC ZOK® 25 mg tablet",   // display_name — UNIQUE
  canonical_id: "a3f8c21b09d4",        // DrugIdentity.canonical_id
  etken_madde: "metoprolol suksinat",
  kaynak_dosya: "BELOC_ZOK_25_MG.pdf",
  created_at: timestamp()
})

(:Section {
  section_id: "BELOC_ZOK_4.5_001",   // chunk_id
  madde_no: "4.5",
  icerik: "..."                        // TAM içerik — kırpma yok (v1.1)
})

(:Condition {name: "böbrek yetmezliği"})
(:Warning {text: "..."})
(:DrugMention {name: "heparin"})      // corpus dışı ilaç
```

### 3.2 İlişkiler

```cypher
(Drug)-[:HAS_SECTION]->(Section)
(Drug)-[:INTERACTS_WITH {
  severity: "contraindicated|severe|moderate|mild|unknown",
  kaynak_madde: "4.3|4.4|4.5",
  kaynak: "llm_extraction|inn_propagated",
  confidence: 0.0-1.0
}]->(Drug)
(Drug)-[:MENTIONS_INTERACTION]->(DrugMention)  // corpus dışı
(Drug)-[:CONTRAINDICATED_FOR]->(Condition)
(Drug)-[:HAS_WARNING]->(Warning)
```

### 3.3 Değişmeyen Kurallar

- `Drug.canonical_id` Neo4j'de index'li — `NameResolver`'dan gelen canonical_id ile hızlı sorgu
- `Section.icerik` TAM içerik saklanır (eski [:2000] kırpma v1.1'de kaldırıldı)
- `INTERACTS_WITH` kaynak alanı zorunlu: `llm_extraction` veya `inn_propagated`
- `canonical_id` boş Drug node oluşturulmaz

---

## 4. ContentPolicy Referansı

```python
# src/core/content_policy.py — güncel değerler

# Parse / storage
drug_name_max_chars: int = 200
etken_madde_max_chars: int = 500
section_storage_max_chars: int = 0   # 0 = sınırsız

# LLM extraction
extraction_section_43_chars: int = 1000
extraction_section_45_chars: int = 2000
extraction_max_tokens: int = 768
extraction_timeout_sec: int = 180
extraction_max_retries: int = 3

# RAG / retrieval
chunk_window_chars: int = 2500
max_chunks_per_query: int = 12
rerank_pool_size: int = 20
min_score_threshold: float = 0.55

# Graf bağlamı (LM Studio overflow fix)
max_contraindications_in_context: int = 20
max_interactions_in_context: int = 15
max_patient_interactions_in_context: int = 10

# Evaluation (runtime ile aynı — drift engeli)
eval_max_contexts: int = 9
eval_max_chunk_chars: int = 2500
```

---

## 5. NameResolver Kullanım Kuralı

```python
from src.core.name_resolver import get_resolver

resolver = get_resolver()  # singleton, lazy-load, LRU cache

# Kullanıcı girdisinden ilaç bul
matches = resolver.resolve("PLAVIX")          # → [DrugIdentity, ...]
one     = resolver.resolve_one("klaritromisin")  # → DrugIdentity | None

# INN grubu — propagation için
group = resolver.resolve_inn_group("diltiazem")  # → [ALTIZEM, DILTIAREC, ...]

# Yeni ilaç eklendikten sonra cache temizle
get_resolver.cache_clear()
```

**Arama sırası:** canonical_id → normalized exact → prefix → INN → fuzzy (difflib ≥0.80) → substring

---

## 6. QualityGate — Karantina Kriterleri

Aşağıdaki durumlar `should_quarantine=True` üretir:

| Flag | Koşul |
|------|-------|
| `DRUG_NAME_MISSING` | ilac_adi boş veya "Bilinmeyen İlaç" |
| `SECTION_43_MISSING` | 4.3 bölümü bulunamadı |
| `SECTION_45_MISSING` | 4.5 bölümü bulunamadı |
| `SECTION_43_SHORT` | 4.3 < 100 karakter |
| `SECTION_45_SHORT` | 4.5 < 100 karakter |
| `TOTAL_CONTENT_SHORT` | Toplam < 500 karakter |
| `ENCODING_ERROR` | Geçersiz UTF-8 |

Karantina raporları: `data/quarantine/{ilaç_adı}_parse_fail.md`

---

## 7. Hata Yönetimi

```
Ingestion katmanı : IngestionError, QuarantineError, DuplicateIngestionError
Extraction katmanı: ExtractionError, ExtractionTimeoutError, ExtractionParseError
Resolver katmanı  : ResolverError, DrugNotFoundError
Graph katmanı     : GraphError, GraphConnectionError
```

Her katman kendi exception'ını fırlatır; `IngestionPipeline` üst katmanda yakalar, `IngestionStatus.FAILED` döndürür ve sonraki PDF'e devam eder. Tek bir hata tüm batch'i durdurmaz.

---

## 8. Test Kapsamı

```bash
# Mevcut testler
pytest tests/ -v              # 49 test

# Yeni modüller için test (henüz yazılmadı)
# tests/test_drug_record.py    → DrugIdentity, canonical_id tutarlılığı
# tests/test_name_resolver.py  → resolve(), resolve_inn_group(), fuzzy eşleşme
# tests/test_quality_gate.py   → flag tespiti, karantina kararı
# tests/test_kub_extractor.py  → Pydantic validation, severity normalizasyon
```

---

**Bu belge gerçek implementasyonu tanımlar. Planlanan ama yapılmayan hiçbir şey burada yer almaz.**
