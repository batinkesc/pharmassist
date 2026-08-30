# PharmAssist — RAG-Based Clinical Decision Support on Turkish Drug Labels

> ⚠️ **Medical Disclaimer**
> PharmAssist is a **research prototype**. It is **not a medical device** and must **not** be used for real clinical decision-making, diagnosis, or treatment. Outputs may be incomplete or incorrect. Always consult the official product label and a qualified healthcare professional.

A retrieval-augmented generation (RAG) system that answers free-text clinical questions using **KÜB documents** — the Turkish equivalent of the SmPC (Summary of Product Characteristics), published by the Turkish Medicines and Medical Devices Agency (TİTCK). v1.9.0

## What It Does

A clinician or pharmacist asks a free-text question in Turkish:

> *"82 yaşında kadın hasta, mevcut ilaçları metoprolol, ramipril, furosemid, digoksin. Ağrı için tramadol ekleyebilir miyim?"*
> ("82-year-old female patient on metoprolol, ramipril, furosemide, digoxin. Can I add tramadol for pain?")

> *"GFR 28, warfarin kullanan hastaya klaritromisin yazabilir miyim?"*
> ("Patient on warfarin with GFR 28 — can I prescribe clarithromycin?")

The system automatically extracts the patient profile (age, renal function, drug list, diagnoses, allergies, lab values), retrieves the relevant label text from a hybrid vector + graph store, and generates a **source-cited** answer that is then post-validated against the retrieved text.

## Why Is Everything in Turkish?

The corpus consists of Turkish regulatory documents, and the target users are Turkish clinicians. Prompts, retrieval, the UI, and answers are therefore **intentionally Turkish** — translating the prompt layer would break alignment with the source text. Documentation is in English; the domain layer stays Turkish by design.

## Architecture

```
        Free-text clinical question (Turkish)
                        │
                        ▼
              ProfileExtractor          ← age, GFR, drug list, diagnoses, allergies, labs
                        │
                        ▼
               QueryAugmentor           ← intent: contraindication / interaction / dose / side effect
                        │
                 ┌──────┴──────┐
                 ▼             ▼
             ChromaDB        Neo4j      ← 11,843 SmPC chunks + drug interaction graph
                 └──────┬──────┘
                        ▼
             AnswerCalibration          ← patient-profile-weighted chunk selection
                        │
                        ▼
                       LLM              ← Claude Haiku (default) / any OpenAI-compatible endpoint
                        │
                        ▼
              VALIDATE Pipeline         ← 7 deterministic post-hoc checks on the answer
```

### VALIDATE Pipeline — Deterministic Answer Verification

Instead of trusting the LLM, every answer is checked against the retrieved source text **after** generation:

| # | Check | On failure |
|---|-------|------------|
| 1 | Absolute safety claims ("is safe") unsupported by source | Replaced with system warning |
| 2 | Contraindication claim vs. section 4.3 content | Tagged `[AŞIRI YORUM]` (over-interpretation) |
| 3 | Medical claims without a source citation | Tagged `[DOĞRULANAMADI]` (unverified) |
| 4 | Numeric claims vs. numbers in the cited chunk | Tagged |
| 5 | CYP450 inhibitor/inducer direction correctness | Tagged |
| 6 | Verdict/severity alignment with the source | Tagged |
| 7 | Structural check of the 3-layer answer format | Logged |

Answers use a 3-layer format separating **verbatim label transfer**, **system findings** (graph/CYP/lab), and **assessment** — so the reader always knows which sentence comes from the source and which from the system.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| PDF parsing | PyMuPDF + pdfplumber |
| Lab report parsing | PyMuPDF (hospital PDF format, 44+ parameters) |
| Embeddings | `intfloat/multilingual-e5-base` |
| Reranking | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` |
| Vector DB | ChromaDB (hybrid with BM25) |
| Graph DB | Neo4j |
| LLM | Claude Haiku 4.5 (default) / any OpenAI-compatible endpoint |
| API | FastAPI |
| Frontend | Streamlit |
| Evaluation | RAGAS (3 metrics) |
| Tests | pytest — 96 tests |

## Corpus

| Metric | Value |
|--------|-------|
| Drugs | 501 |
| ChromaDB chunks | 11,843 |
| Neo4j `INTERACTS_WITH` edges | 4,021 |
| Unknown interaction severity | 0% (via INN propagation) |
| CYP450 records | Static table + LLM fallback, stored in Neo4j |

## Evaluation (RAGAS)

**Active baseline — Run 20** (33 clinical questions, evaluator: Qwen3-235B via Together AI):

| Metric | Score |
|--------|-------|
| Faithfulness | 0.7192 |
| Context Utilization | 0.7823 |
| Context Recall | 0.9010 |
| **Average** | **0.8008** |

20 evaluation runs are tracked chronologically in [`data/eval/RAGAS_RUN_HISTORY.md`](data/eval/RAGAS_RUN_HISTORY.md), including regressions and their root-cause analyses.

**Known limitation:** faithfulness plateaus around 0.72. Root-cause analysis points to evaluator strictness on Turkish clinical text and ground-truth granularity rather than retrieval quality — documented in the run history.

## Getting Started

### Prerequisites

- Python 3.11+
- Neo4j 5.x (Desktop or Docker)
- An Anthropic API key (or any OpenAI-compatible LLM endpoint)

### Install

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env          # then fill in ANTHROPIC_API_KEY, NEO4J_PASSWORD, ...
```

### Data Bootstrap

KÜB PDFs are **not distributed with this repository**. They are publicly available from TİTCK ([titck.gov.tr](https://www.titck.gov.tr)) — search a product and download its KÜB ("Kısa Ürün Bilgisi") PDF.

```bash
# 1. Place KÜB PDFs into data/raw_pdfs/

# 2. Parse → QA gate → ChromaDB + JSON
python scripts/bulk_ingest.py --pdf-dir data/raw_pdfs

# 3. Build the Neo4j interaction graph (drug nodes, INTERACTS_WITH, CYP450)
python scripts/load_graph.py
```

> Note: image-based (scanned) PDFs fall back to a vision OCR step that calls a paid API — the ingest script warns before doing so.

### Run

```bash
# Streamlit UI
streamlit run app.py
```

```bash
# or the REST API — Swagger at http://localhost:8080/docs
uvicorn src.api.main:app --port 8080
```

Windows users can use `start.bat` (checks venv, ports, Neo4j, then launches API + UI).

### Docker

```bash
docker compose up --build
```

Starts `api` (8080), `ui` (8501), and `neo4j` (7474/7687). Note: containers start with an **empty** ChromaDB volume — run the data bootstrap against it once.

## Evaluation & Tests

```bash
python scripts/run_eval.py    # RAGAS evaluation (requires evaluator API key in .env)
```

```bash
pytest tests/ -v              # 96 unit tests, no live services required
```

## Project Structure

```
├── app.py                      # Streamlit UI (split panel: patient profile | chat)
├── src/
│   ├── agents/                 # RAG engine + VALIDATE, profile extraction, query augmentation
│   ├── ingestion/              # KÜB PDF parsing, section/subsection extraction, lab reports
│   ├── retrieval/              # ChromaDB store, BM25, cross-encoder reranking
│   ├── graph/                  # Neo4j client, graph construction, graph retrieval
│   ├── analysis/               # CYP450 mapping, cumulative risk
│   ├── core/                   # DrugIdentity, NameResolver, ContentPolicy, QualityGate
│   ├── pipeline/               # End-to-end ingestion pipeline
│   ├── api/                    # FastAPI routes and schemas
│   └── evaluation/             # RAGAS integration
├── scripts/                    # Ingestion, graph loading, evaluation
├── tests/                      # 96 pytest tests
├── data/
│   ├── eval/                   # RAGAS results + run history
│   └── diagrams/               # UML diagrams (class, sequence, use case, activity)
└── docs/                       # Architecture standards, sprint reports (Turkish)
```

## Documentation

- [`PROJE_DOKUMANTASYONU.md`](PROJE_DOKUMANTASYONU.md) — full technical documentation (Turkish)
- [`docs/ARCHITECTURE_STANDARDS.md`](docs/ARCHITECTURE_STANDARDS.md) — architecture standards (Turkish)
- [`data/eval/RAGAS_RUN_HISTORY.md`](data/eval/RAGAS_RUN_HISTORY.md) — all 20 evaluation runs
- [`README_TR.md`](README_TR.md) — this README in Turkish

## License

[MIT](LICENSE)
