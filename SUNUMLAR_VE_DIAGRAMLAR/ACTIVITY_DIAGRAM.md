# PharmAssist: Activity Diagrams

## Activity Diagram 1: Sorgu İşleme Pipeline (11 Adım)

```mermaid
graph TD
    Start([👤 Klinisyen Sorgu Gönderir]) -->|POST /query| A1["<b>Adım 1:</b> Hasta Profili Alımı<br/>- Yaş, cinsiyet, lab_values<br/>- renal/hepatic status"]
    
    A1 -->|Validasyon| A1V{Geçerli mi?}
    A1V -->|❌ Fail| Error1["⚠️ ValidationError<br/>(400 Bad Request)"]
    Error1 --> End1(["❌ Sonlandır"])
    A1V -->|✅ Pass| A2["<b>Adım 2:</b> Sorgu Tipi Tahmini<br/>- Anahtar kelime analizi<br/>- kontrendikasyon/etkileşim/doz"]
    
    A2 --> A3["<b>Adım 3:</b> Section-Based Filtering<br/>- query_type → KÜB bölümü<br/>- metadata filter hazırla"]
    
    A3 --> A4["<b>Adım 4:</b> ChromaDB Retrieval<br/>- Embedding oluştur<br/>- Primary k=8, Secondary k=4<br/>- Latency: ~150ms"]
    
    A4 -->|Sonuç?| A4C{Chunks bulunamadı mı?}
    A4C -->|❌ 0 chunks| Error2["⚠️ No relevant docs<br/>→ Fallback msg"]
    Error2 --> End2(["⚠️ Partial Response"])
    A4C -->|✅ 8-12 chunks| A5["<b>Adım 5:</b> Cross-Encoder Reranking<br/>- Relevance scoring<br/>- Top-8 seç<br/>- Latency: ~50ms"]
    
    A5 --> A6["<b>Adım 6:</b> Neo4j Graph Retrieval<br/>- Drug-drug relationships<br/>- Cypher: INTERACTS_WITH<br/>- Latency: ~200ms"]
    
    A6 -->|Graph sonuç| A6R{İlaç etkileşimi var mı?}
    A6R -->|Evet| A6Y["✅ Interaction found<br/>severity/mechanism"]
    A6R -->|Hayır| A6N["⚠️ No relationship<br/>ChromaDB'ye güven"]
    A6Y --> A7
    A6N --> A7["<b>Adım 7:</b> Kümülatif Risk Analizi<br/>- 9 kategori: ADR, böbrek,<br/>karaciğer, CYP450, polifarmasi vb<br/>- Risk level: HIGH/MODERATE/LOW"]
    
    A7 --> A8["<b>Adım 8:</b> CYP450 Enzyme Mapping<br/>- Substrate/Inhibitor/Inducer<br/>- CYP3A4, CYP2D6, CYP2C9 vb<br/>- Interaction chain tespit"]
    
    A8 --> A9["<b>Adım 9:</b> Bağlam Formatı<br/>+ MUTLAK KURAL Prompt<br/>- ChromaDB + Neo4j + CYP450<br/>- 'Bağlamda olmayan yazma'"]
    
    A9 --> A10["<b>Adım 10:</b> LLM Inference<br/>- claude-haiku-4-5-20251001<br/>- max_tokens=1400, temp=0<br/>- Latency: ~800ms<br/>- Cost: $0.009"]
    
    A10 -->|LLM Response| A10C{API başarılı mı?}
    A10C -->|❌ Timeout| Error3["⚠️ API Timeout<br/>→ Retry or fallback"]
    Error3 --> End3(["⚠️ Partial Response"])
    A10C -->|✅ 200 OK| A11["<b>Adım 11:</b> Output Validation<br/>- 'Güvenlidir' yasağı (regex)<br/>- İlaç adı validasyonu<br/>- Token limit (2000 words)"]
    
    A11 -->|Validasyon| A11C{Hata var mı?}
    A11C -->|Evet| A11F["🔧 Fix: Replace pattern<br/>→ '[SİSTEM DÜZELTMESİ: ...]'"]
    A11F --> A12
    A11C -->|Hayır| A12["✅ Response Ready<br/>- rag_answer<br/>- sources<br/>- kumulative_riskler<br/>- cyp_etkilesimler"]
    
    A12 --> End4(["✅ 200 OK Response<br/>Klinisyen'e döndür"])
    
    style Start fill:#e1f5e1
    style End4 fill:#e1f5e1
    style Error1 fill:#ffe1e1
    style Error2 fill:#ffe1e1
    style Error3 fill:#ffe1e1
```

---

## Activity Diagram 2: Sistem Başlangıcı (Startup)

```mermaid
graph TD
    Start(["🚀 Docker-Compose Up"]) --> DC["docker-compose up -d<br/>- api service<br/>- ui service<br/>- neo4j service"]
    
    DC --> API["FastAPI Boot<br/>(src/api/main.py)"]
    DC --> UI["Streamlit Boot<br/>(app.py)"]
    DC --> NEO4J["Neo4j Container<br/>(bolt://127.0.0.1:7687)"]
    
    API --> LIFESPAN["⚙️ Lifespan Hooks"]
    LIFESPAN --> LS1["1. Check ANTHROPIC_API_KEY"]
    LS1 -->|❌ Not set| ErrorAPI["❌ RuntimeError<br/>API fail"]
    LS1 -->|✅ Set| LS2["2. Init ChromaDB client<br/>(@lru_cache)"]
    
    LS2 --> LS3["3. Init Neo4j driver<br/>(@lru_cache, timeout=5s)"]
    LS3 --> LS4["4. Settings validation<br/>(Pydantic)"]
    LS4 --> APIOk["✅ API Ready<br/>(Port 8080)"]
    
    UI --> UIINIT["Streamlit Init"]
    UIINIT --> UI1["Load ChromaDB collection<br/>(kub_chunks)"]
    UI1 --> UI2["Display drug list (59)"]
    UI2 --> UIOk["✅ UI Ready<br/>(Port 8501)"]
    
    NEO4J --> NEO1["Neo4j Startup<br/>Password: env-based"]
    NEO1 --> NEO2["Load drug nodes (59)<br/>Load relationships"]
    NEO2 --> NEO3{Constraints<br/>OK?}
    NEO3 -->|❌ Fail| ErrorNEO["⚠️ Warning:<br/>Constraints may exist"]
    NEO3 -->|✅ OK| NEOOk["✅ Neo4j Ready<br/>(Port 7687)"]
    
    ErrorAPI --> End1(["❌ Startup Failed"])
    APIOk --> HealthCheck
    UIOk --> HealthCheck
    NEOOk --> HealthCheck["GET /health<br/>All dependencies check"]
    
    HealthCheck -->|All OK| SuccessStart(["✅ PharmAssist Ready<br/>http://localhost:8501"])
    
    style Start fill:#e1f5e1
    style SuccessStart fill:#e1f5e1
    style ErrorAPI fill:#ffe1e1
    style End1 fill:#ffe1e1
```

---

## Activity Diagram 3: Veri Alımı & İşleme (Ingestion)

```mermaid
graph TD
    Start(["📂 Yeni KÜB PDF'leri<br/>data/raw_pdfs/"]) --> Script["python scripts/bulk_ingest.py<br/>--v2"]
    
    Script --> Step1["📋 Step 1: PDF List Oluştur<br/>data/raw_pdfs/*.pdf"]
    Step1 --> Step2["🧹 Step 2: Stale Quarantine Temizle<br/>data/quarantine/*.md"]
    
    Step2 --> Loop["🔄 For each PDF:"]
    Loop --> Parse["<b>Parse:</b><br/>- PyMuPDF text extract<br/>- Camelot table extract<br/>- 8 madde bölümleri"]
    
    Parse --> ParseQA["<b>Parse QA:</b><br/>4.3 'Kontrendikasyonlar' exists?<br/>4.5 'İlaç-İlaç' exists?<br/>drug_name ≠ 'UNKNOWN'?<br/>Total content >500 chars?"]
    
    ParseQA -->|❌ Fail| Quarantine["⚠️ Move to<br/>data/quarantine/<br/>drug_name_parse_fail.md"]
    Quarantine --> NextPDF
    
    ParseQA -->|✅ Pass| GenerateJSON["💾 Generate<br/>data/parsed_json/drug_name.json<br/>{drug_name, sections, ...}"]
    
    GenerateJSON --> Chunk["✂️ Chunking:<br/>- 300-400 chars/chunk<br/>- Overlap: 100 chars<br/>- Metadata: {drug, section, title}"]
    
    Chunk --> Embed["🧬 Embedding:<br/>- multilingual-e5<br/>- 1024-dim vector<br/>- Normalize: L2"]
    
    Embed --> ChromaDB["📊 ChromaDB Insert:<br/>- Collection: kub_chunks<br/>- Index: cosine similarity<br/>- Metadata filter enabled"]
    
    ChromaDB --> Neo4j["🔗 Neo4j Load:<br/>- CREATE Drug node<br/>- CREATE relationships<br/>- MATCH constraints"]
    
    Neo4j --> NextPDF["Next PDF"]
    NextPDF -->|More?| Loop
    NextPDF -->|Done| Summary["📈 Summary Report:<br/>- Total drugs loaded<br/>- Total chunks: 1036<br/>- Parse QA fails"]
    
    Summary --> End(["✅ Bulk Ingest Complete<br/>ChromaDB: 1036 chunks<br/>Neo4j: 59 drugs"])
    
    style Start fill:#e1f5e1
    style End fill:#e1f5e1
    style Quarantine fill:#fff3e1
```

---

## Activity Diagram 4: Output Validation (Guardrails)

```mermaid
graph TD
    LLMResp(["🤖 LLM Response<br/>raw_answer"]) --> V1["<b>Guardrail 1:</b><br/>'Güvenlidir' Yasağı"]
    
    V1 --> V1C{Regex Match:<br/>'güvenlidir'<br/>'güvenle'<br/>'sorun yoktur' vb?}
    
    V1C -->|❌ Found| V1F["🔧 Replace:<br/>[SİSTEM DÜZELTMESİ:<br/>KÜB verileri bu kombinasyon<br/>için spesifik güvenlik<br/>onayı içermemektedir.<br/>Klinik değerlendirme önerilir.]"]
    V1F --> V2
    V1C -->|✅ Clean| V2["<b>Guardrail 2:</b><br/>İlaç Adı Validasyonu"]
    
    V2 --> V2C{For each drug<br/>in selected_drugs:<br/>drug in response<br/>AND<br/>drug in context?}
    
    V2C -->|❌ Found unvalidated| V2F["🔧 Replace:<br/>[DOĞRULANAMADI:<br/>'{drug}' bu sorgunun<br/>KÜB bağlamında<br/>bulunamadı.]"]
    V2F --> V3
    V2C -->|✅ All valid| V3["<b>Guardrail 3:</b><br/>Token/Word Count Limit"]
    
    V3 --> V3C{word_count > 2000?}
    V3C -->|❌ Too long| V3F["✂️ Truncate:<br/>response[:2000] +<br/>'[Yanıt uzun, kesildi...]'"]
    V3F --> Validated
    V3C -->|✅ OK| Validated["✅ All Validation Pass"]
    
    Validated --> Return(["✅ Return Response<br/>rag_answer<br/>sources<br/>kumulative_riskler<br/>cyp_etkilesimler"])
    
    style LLMResp fill:#e1e5ff
    style Return fill:#e1f5e1
```

---

## Key Metrics (Aktivite Metrikleri)

| Aktivite | Latency | Kritik | Hata Handling |
|----------|---------|--------|---------------|
| ChromaDB Retrieval | ~150ms | HIGH | Cache fallback |
| Cross-Encoder Reranking | ~50ms | MEDIUM | Skip if timeout |
| Neo4j Graph Query | ~200ms | MEDIUM | Query timeout=5s |
| LLM Inference | ~800ms | CRITICAL | Retry 2x, then fallback |
| Output Validation | ~20ms | HIGH | Strict (must pass) |
| **Total Pipeline** | **~2.1s** | **CRITICAL** | Timeout=3s |

---

## Error Handling Strategy

```
Request başarısız mu?
    ├─ ChromaDB fail → Fallback: default message
    ├─ Neo4j fail → Continue: ChromaDB results only
    ├─ LLM timeout → Retry 2x, then: generic response
    ├─ Validation fail → Fix: apply guardrail replacements
    └─ All fail → 503 Service Unavailable

Response quality
    ├─ Faithfulness < 0.65 → ⚠️ Warning flag
    ├─ No sources → ❌ Reject
    └─ Unknown drug in answer → 🔧 Mark as [DOĞRULANAMADI]
```
