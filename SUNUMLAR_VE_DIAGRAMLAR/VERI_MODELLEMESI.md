# PharmAssist: Veri Modellemesi

## 1. Veri Katmanları (Data Layers)

```
┌──────────────────────────────────────────────────────────┐
│                   Presentation Layer                      │
│            (Streamlit UI + FastAPI Response)             │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│                   Business Logic Layer                    │
│  ├─ rag_engine.py (query pipeline)                       │
│  ├─ cumulative_risk.py (9 kategori risk analiz)         │
│  ├─ cyp450_mapper.py (enzyme profile mapping)           │
│  └─ query_augmentor.py (query enrichment)               │
└────────────────────┬─────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────┐  ┌───────▼──────┐  ┌──────▼────┐
│ Vector │  │  Relational  │  │    In-    │
│ Data   │  │  Graph Data  │  │  Memory   │
│        │  │              │  │  Cache    │
│ChromaDB│  │  Neo4j       │  │  @lru_    │
└────────┘  └──────────────┘  └───────────┘
```

---

## 2. ChromaDB: Vector Database Schema

**Collection Name:** `kub_chunks`

### Document Structure

```json
{
  "id": "chunk_001_cipralex_4.3",
  "text": "Kontrendikasyonlar: Hipersensitivite...",
  "embedding": [0.0234, -0.1456, 0.8923, ...],  // 1024 boyutlu
  "metadata": {
    "drug_name": "CIPRALEX",
    "section": "4.3",
    "section_title": "Kontrendikasyonlar",
    "page": 2,
    "content_hash": "abc123def456"
  }
}
```

### Collection Settings

| Özellik | Değer |
|---------|-------|
| **Name** | kub_chunks |
| **Metric** | cosine |
| **Embedding Model** | multilingual-e5-large (1024-dim) |
| **Persistence** | Disk (chroma_db/ directory) |
| **Metadata Filtering** | Enabled (drug_name, section) |
| **Total Documents** | 1036 |
| **Storage Size** | ~450 MB |

### Query Example

```python
# Section-based filtering
where_filter = {
    "$and": [
        {"section": {"$in": ["4.3", "4.4"]}},  # Kontrendikasyon bölümleri
        {"drug_name": {"$in": ["CIPRALEX", "JANUVIA"]}}
    ]
}

results = collection.query(
    query_embeddings=[query_embedding],  # 1024-dim
    n_results=8,
    where=where_filter
)

# Output:
# {
#   "ids": ["chunk_001", "chunk_005", ...],
#   "distances": [0.15, 0.22, ...],  # cosine distance
#   "documents": ["Hipersensitivite...", ...],
#   "metadatas": [{"drug": "CIPRALEX", ...}, ...]
# }
```

---

## 3. Neo4j: Graph Database Schema

### Node Types

```
┌─────────────────────────────────────────────────────┐
│                    Drug Node                        │
├─────────────────────────────────────────────────────┤
│ name: "CIPRALEX"                                   │
│ active_ingredient: "Escitalopram oxalate"          │
│ drug_id: "cipralex_001"                            │
│ sections: ["4.2", "4.3", "4.4", "4.5", "4.6"]     │
│ therapeutic_class: "SSRİ"                          │
│ has_section_4_3: true                              │
│ has_section_4_5: true                              │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│               CYP450Enzyme Node                      │
├─────────────────────────────────────────────────────┤
│ enzyme_id: "CYP2D6"                                │
│ function: "Dopamine/norepinephrine metabolism"     │
│ genetic_variants: ["*1", "*2", "*3", "*10"]        │
│ expression_level: "High"                            │
│ inhibitor_potency: "Strong/Moderate/Weak"          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│            PatientCondition Node                    │
├─────────────────────────────────────────────────────┤
│ condition_id: "renal_disease"                       │
│ label: "Chronic Kidney Disease"                    │
│ severity: "Moderate/Severe/ESRD"                   │
│ eGFR_range: "30-60"                                │
└─────────────────────────────────────────────────────┘
```

### Relationship Types

```cypher
// 1. Drug-to-Drug Interactions
Drug1 -[:INTERACTS_WITH {
    mechanism: "Serotonin syndrome risk",
    severity: "HIGH|MODERATE|LOW",
    clin_significance: "Avoid combination"
}]-> Drug2

// 2. Contraindications
Drug1 -[:CONTRAINDICATED_WITH {
    reason: "Hypersensitivity",
    severity: "ABSOLUTE|RELATIVE"
}]-> Drug2

// 3. Drug Metabolism
Drug -[:METABOLIZED_BY {
    primary: true,
    secondary: false,
    enzyme_inhibition_risk: "Strong/Weak"
}]-> CYP450Enzyme

// 4. Enzyme Inhibition
Drug -[:INHIBITS {
    potency: "Strong|Moderate|Weak",
    clinical_effect: "Increased Cmax"
}]-> CYP450Enzyme

// 5. Enzyme Induction
Drug -[:INDUCES {
    potency: "Strong|Moderate|Weak",
    clinical_effect: "Decreased Cmax"
}]-> CYP450Enzyme

// 6. Drug-Disease Contraindication
Drug -[:CONTRAINDICATED_IN]-> PatientCondition

// 7. Enzyme Polymorphism
CYP450Enzyme -[:HAS_VARIANT]-> CYP450Variant
```

### Cypher Query Examples

```cypher
// Query 1: Find all interactions
MATCH (d1:Drug {name: "CIPRALEX"})-[r:INTERACTS_WITH]->(d2:Drug)
RETURN d1.name, r.mechanism, r.severity, d2.name

// Query 2: Find contraindications
MATCH (d1:Drug {name: "CIPRALEX"})-[:CONTRAINDICATED_WITH]->(d2:Drug)
RETURN d1.name, d2.name

// Query 3: Find CYP450 cascade
MATCH (d1:Drug {name: "CIPRALEX"})-[:METABOLIZED_BY]->(c:CYP450),
      (d2:Drug)-[:INHIBITS]->(c)
WHERE d2.name IN ["KETOCONAZOLE", "FLUCONAZOLE"]
RETURN d1.name, c.enzyme_id, d2.name

// Query 4: Find all drugs metabolized by specific enzyme
MATCH (d:Drug)-[:METABOLIZED_BY {primary: true}]->(c:CYP450 {enzyme_id: "CYP3A4"})
RETURN d.name, d.therapeutic_class

// Query 5: Check for disease contraindication
MATCH (d:Drug)-[:CONTRAINDICATED_IN]->(c:PatientCondition {condition_id: "renal_disease"})
WHERE c.severity = "ESRD"
RETURN d.name, c.label
```

### Neo4j Constraints

```cypher
// Unique constraints
CREATE CONSTRAINT drug_name_unique FOR (d:Drug) REQUIRE d.name IS UNIQUE
CREATE CONSTRAINT enzyme_id_unique FOR (e:CYP450) REQUIRE e.enzyme_id IS UNIQUE

// Property existence constraints
CREATE CONSTRAINT drug_ingredient_required FOR (d:Drug) REQUIRE d.active_ingredient IS NOT NULL

// Indexes (performance)
CREATE INDEX drug_name_index FOR (d:Drug) ON (d.name)
CREATE INDEX enzyme_index FOR (e:CYP450) ON (e.enzyme_id)
```

### Neo4j Statistics (2026-04-08)

| Metrik | Değer |
|--------|-------|
| Total Nodes | 65 (59 Drug + 6 CYP450) |
| Total Relationships | 245 |
| Drug-Drug Interactions | 180 |
| Contraindications | 35 |
| CYP450 Metabolization | 30 |
| Avg Query Time | ~50ms |
| Database Size | ~45 MB |

---

## 4. API Request/Response Data Models

### Pydantic Schemas

```python
# src/api/schemas.py

from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# ========== REQUEST ==========

class LabValues(BaseModel):
    hemoglobin: float = Field(..., gt=0, le=20, description="g/dL")
    albumin: float = Field(..., gt=0, le=6)
    creatinine: float = Field(..., gt=0, le=15)
    ast: float = Field(..., gt=0, le=1000)
    alt: float = Field(..., gt=0, le=1000)
    platelets: float = Field(..., gt=0, le=500)
    inr: float = Field(..., gt=0, le=10)

class PatientProfile(BaseModel):
    age: int = Field(..., ge=18, le=120)
    gender: str = Field(..., pattern="^(Erkek|Kadın)$")
    weight_kg: Optional[float] = Field(None, gt=40, le=200)
    lab_values: LabValues
    renal_status: str = Field(
        ...,
        enum=["Normal", "Mild CKD", "Moderate CKD", "Severe CKD", "ESRD"]
    )
    hepatic_status: str = Field(
        ...,
        enum=["Normal", "Mild", "Moderate", "Severe"]
    )

class QueryPayload(BaseModel):
    patient_profile: PatientProfile
    selected_drugs: List[str] = Field(..., min_items=2, max_items=10)
    query_text: str = Field(..., min_length=10, max_length=500)
    query_type: Optional[str] = Field(None)  # auto-detected if None

# ========== RESPONSE ==========

class KumulatifRiskItem(BaseModel):
    category: str  # "ADR Overlap", "CYP450", etc
    level: str  # "HIGH", "MODERATE", "LOW"
    reasoning: str

class CYPEtkilesimItem(BaseModel):
    enzyme: str
    substrate_drug: str
    inhibitor_drug: str
    interaction_type: str  # "Inhibition", "Induction"
    effect: str
    clinical_consequence: str
    severity: str

class RAGResponse(BaseModel):
    rag_answer: str
    sources: List[str]
    kumulative_riskler: List[KumulatifRiskItem]
    cyp_etkilesimler: List[CYPEtkilesimItem]

class QueryResponse(BaseModel):
    status: str  # "success", "partial_success", "error"
    response: RAGResponse
    patient_id: Optional[str] = None
    timestamp: str  # ISO 8601
    latency_ms: int
    cost_usd: float

# Example
{
    "status": "success",
    "response": {
        "rag_answer": "KÜB belgelerine göre...",
        "sources": ["CIPRALEX | 4.3", "JANUVIA | 4.5"],
        "kumulative_riskler": [
            {"category": "CYP450", "level": "MODERATE", "reasoning": "..."}
        ],
        "cyp_etkilesimler": [
            {"enzyme": "CYP2D6", "substrate_drug": "JANUVIA", ...}
        ]
    },
    "patient_id": "uuid-xxx",
    "timestamp": "2026-04-10T14:00:00Z",
    "latency_ms": 2100,
    "cost_usd": 0.009
}
```

---

## 5. Entity-Relationship Diagram (ER)

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA STORAGE OVERVIEW                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────┐         ┌──────────────────────┐
│    ChromaDB         │         │    Neo4j             │
│   (Vector Store)    │         │  (Graph Database)    │
├─────────────────────┤         ├──────────────────────┤
│ kub_chunks:         │         │ Nodes:               │
│  - id               │         │  ✓ Drug (59)         │
│  - text (chunked)   │         │  ✓ CYP450 (6)       │
│  - embedding (1024) │         │  ✓ Interaction      │
│  - metadata:        │         │  ✓ Condition        │
│    • drug_name      │         │                      │
│    • section        │         │ Relationships:       │
│    • section_title  │         │  ✓ INTERACTS_WITH   │
│    • page           │         │  ✓ CONTRAINDICATED  │
│    • content_hash   │         │  ✓ METABOLIZED_BY   │
│                     │         │  ✓ INHIBITS         │
│ Count: 1036 docs    │         │  ✓ INDUCES          │
│ Size: 450 MB        │         │                      │
│ Metric: cosine      │         │ Count: 65 nodes,    │
│                     │         │ 245 relationships   │
│                     │         │ Size: 45 MB         │
└─────────────────────┘         └──────────────────────┘
         △                                 △
         │                                 │
    Embedding                        Graph Query
    Retrieval                        (Cypher)
         │                                 │
         └─────────────────┬───────────────┘
                           │
                   ┌───────▼──────────┐
                   │   FastAPI       │
                   │  /api/v1/query  │
                   │                 │
                   │ Orchestrator    │
                   │ (rag_engine.py) │
                   └─────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐    ┌──────▼──────┐    ┌─────▼───────┐
    │ Analysis │    │ Validation  │    │ LLM Call    │
    ├──────────┤    ├─────────────┤    ├─────────────┤
    │ - Risk   │    │ - Guardrail │    │ - Claude    │
    │ - CYP450 │    │ - Safeguard │    │ - Inference │
    └──────────┘    └─────────────┘    └─────────────┘
```

---

## 6. Dosya Depolama Şeması (File Storage)

```
PharmAssistVersion2/
│
├── data/
│   ├── raw_pdfs/
│   │   ├── cipralex.pdf
│   │   ├── januvia.pdf
│   │   └── ... (59 ilaç)
│   │
│   ├── parsed_json/
│   │   ├── cipralex.json
│   │   │   {
│   │   │     "drug_name": "CIPRALEX",
│   │   │     "sections": {
│   │   │       "4.2": "Dozaj...",
│   │   │       "4.3": "Kontrendikasyon...",
│   │   │       ...
│   │   │     }
│   │   │   }
│   │   └── ... (59 ilaç)
│   │
│   ├── quarantine/
│   │   ├── failed_drug_parse_fail.md
│   │   └── ... (başarısız ilaçlar)
│   │
│   └── eval/
│       ├── ragas_baseline_v1.json
│       │   {
│       │     "summary": {
│       │       "faithfulness": 0.40,
│       │       "context_recall": 0.74
│       │     }
│       │   }
│       │
│       ├── ragas_v2_results.json
│       │   {
│       │     "summary": {
│       │       "faithfulness": 0.7811,
│       │       "context_recall": 0.8864
│       │     },
│       │     "results": [...]
│       │   }
│       │
│       └── ragas_v2_questions.json
│           {
│             "questions": [
│               {
│                 "question": "...",
│                 "ground_truth": "...",
│                 "drug_context": ["CIPRALEX", ...]
│               }
│             ]
│           }
│
├── chroma_db/
│   ├── index/
│   │   └── ... (vector index files)
│   ├── chroma.sqlite3
│   └── data/
│       └── ... (embeddings)
│
└── src/
    ├── config/
    │   └── settings.py
    │       class Settings(BaseSettings):
    │           ANTHROPIC_API_KEY: str
    │           NEO4J_URI: str
    │           NEO4J_USER: str
    │           NEO4J_PASSWORD: str
    │           CHROMA_DB_PATH: Path
    │
    ├── api/schemas.py
    │   - PatientProfile
    │   - QueryPayload
    │   - RAGResponse
    │   - QueryResponse
    │
    └── ... (other modules)
```

---

## 7. Session & Cache Strategy

```python
# ChromaDB Connection Pooling
@lru_cache(maxsize=1)
def get_chroma_client():
    """Singleton pattern - reuse same connection"""
    return Client(settings)

# Neo4j Connection Pooling
@lru_cache(maxsize=1)
def get_neo4j_driver():
    """Singleton pattern - reuse same driver"""
    return GraphDatabase.driver(URI, auth=(...), max_pool_size=50)

# LRU Cache Examples
@lru_cache(maxsize=128)
def get_drug_cyp450_profile(drug_name: str):
    """Cache drug CYP450 profile"""
    return CYP450_DATABASE[drug_name]

@lru_cache(maxsize=256)
def estimate_egfr(creatinine: float, age: int, gender: str):
    """Cache eGFR calculation"""
    return calculate_egfr_cockcroft_gault(...)

# Response Caching (Redis optional)
# @cached(cache=redis_cache, key_builder=...)
# def query_rag(...):
#     ...
```

---

## 8. Security & Data Privacy

| Katman | Kontrolü |
|--------|----------|
| **API** | X-API-Key header (optional) |
| **DB** | Ne4j auth, ChromaDB local |
| **Patient Data** | Never logged, request_id only |
| **LLM Call** | API key from .env, HTTPS only |
| **Audit Log** | Timestamp, query_type, risk_level |
| **Export** | Patient name hashed in CSV/PDF |

---

## 9. Veri Akışı (Data Flow)

```
User Input
    │
    ▼
┌─────────────┐
│Streamlit UI │ → PatientProfile + selected_drugs
└─────┬───────┘
      │
      ▼
┌──────────────────────────────────────┐
│ FastAPI /api/v1/query                │
│ (Pydantic validation)                │
└─────┬────────────────────────────────┘
      │
      ├──→ ChromaDB: retrieval (text + metadata filter)
      │    └──→ Embedding lookup
      │
      ├──→ Neo4j: graph queries (Cypher)
      │    └──→ Drug-drug relationships
      │
      ├──→ Analysis Pipeline
      │    ├──→ Cumulative Risk (9 categories)
      │    └──→ CYP450 Mapping
      │
      ├──→ Prompt Formatting
      │    └──→ MUTLAK KURAL guardrail
      │
      ├──→ LLM Call (Claude Haiku)
      │    └──→ API response
      │
      └──→ Output Validation
           ├──→ "Güvenlidir" yasağı
           ├──→ İlaç adı validasyonu
           └──→ Token limit
                │
                ▼
            RAGResponse
                │
                ▼
            Streamlit Display
                │
                ├──→ Risk Summary (HIGH/MODERATE/LOW)
                ├──→ CYP450 Interactions
                ├──→ KÜB Sources
                └──→ Export (PDF/CSV)
```

---

## Summary: Data Layer Components

| Bileşen | Tür | Kapasite | Latency | Durum |
|---------|-----|----------|---------|-------|
| **ChromaDB** | Vector Store | 1036 chunks | 150ms | ✅ |
| **Neo4j** | Graph DB | 59 drugs, 245 rel | 200ms | ✅ |
| **FastAPI** | REST API | 100+ concurrent | <3s | ✅ |
| **Streamlit** | UI | Single user | ~2.1s | ✅ |
| **LLM Cache** | @lru_cache | 256 entries | <5ms | ✅ |
| **Settings** | Pydantic | .env validated | <1ms | ✅ |
