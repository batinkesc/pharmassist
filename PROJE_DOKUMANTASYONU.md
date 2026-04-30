# PharmAssist — Proje Dokümantasyonu

**Versiyon:** 1.8.0  
**Son Güncelleme:** 2026-04-30  
**Durum:** 3-katman yanıt formatı ([KÜB Aktarımı]/[Sistem Tespitleri]/[Değerlendirme]) uygulandı. VALIDATE step 7 eklendi. CYP extraction Neo4j'e taşındı (API maliyeti azaltıldı). **Run 20: F:0.7192 | CU:0.7823 | CR:0.9010 | Ort:0.8008** — baseline Run 18'e göre +0.1pp; CU +3.1pp ↑. **AKTİF BASELINE: Run 18** (F:0.7127 | CU:0.7516 | CR:0.9343 | Ort:0.7995 ✓). **95 test geçiyor.** Eski baseline: Run 12 (F:0.7607 | CU:0.8028 | CR:0.7250).

---

## 1. Proje Nedir?

PharmAssist, Türkiye'de TİTCK (Türkiye İlaç ve Tıbbi Cihaz Kurumu) tarafından yayımlanan **KÜB (Kısa Ürün Bilgisi)** PDF belgelerine dayalı bir **Klinik Karar Destek Sistemi (CDSS)**'dir.

Bir klinisyen veya eczacı hastasına ilaç yazarken şu soruları sisteme sorabilir:

- "Bu hastaya böbrek yetmezliği varken Augmentin yazılabilir mi?"
- "Warfarin alan bir hastaya Onaxan başlanırsa ne olur?"
- "Klaritromisin kullanan hastada Plavix etkinliği nasıl etkilenir?"

Sistem, soruyu KÜB belgelerindeki gerçek metinle karşılaştırır, hastanın klinik profilini (yaş, böbrek/karaciğer fonksiyonu, mevcut ilaçlar, lab değerleri) dikkate alır ve **kaynaklı, evidence-based** bir yanıt üretir.

### Neyi Yapmaz

- "Güvenlidir" veya "sorun yoktur" demez — her zaman evidence-based ifade kullanır.
- KÜB dışı bilgi üretmez — yanıt yalnızca yüklü belgelere dayanır.
- Nihai klinik kararı vermez — sistem "Karar Destekleyici"dir, "Karar Verici" değil.

---

## 2. Mimariye Genel Bakış

Sistem iki ana katmandan oluşur: **Ingestion** (veri yükleme) ve **RAG** (sorgu-yanıt).

### 2.1 Ingestion Pipeline (yeni: tek entry point)

```
PDF
 └→ IngestionPipeline (src/pipeline/ingestion_pipeline.py)
       ├── [1] KUBParser         → ham metin + bölümler
       ├── [2] DrugIdentity      → canonical_id (tüm depolarda ortak anahtar)
       ├── [3] QualityGate       → karantina / devam kararı
       ├── [4] KUBExtractor      → LLM ile 4.3+4.5 → DrugInteraction[] (parse anında)
       ├── [5] INNResolver       → aynı etken madde → IW yayma (otomatik)
       └── [6] AtomicWriter      → ChromaDB + Neo4j aynı anda
```

Eski durum (4 ayrı script, transactional garanti yok):
`bulk_ingest → load_graph → rebuild_interactions → propagate_inn`

### 2.2 RAG Pipeline (sorgu-yanıt)

```
Klinisyen Sorusu + Hasta Profili
            │
            ▼
   ┌──────────────────┐
   │  QueryAugmentor  │  ← Soru türü tespiti, madde önceliği
   └────────┬─────────┘
            │
     ┌──────┴──────┐
     │             │
     ▼             ▼
┌─────────┐  ┌──────────┐
│ChromaDB │  │  Neo4j   │ ← ContentPolicy ile context limitli
│Retrieval│  │  Graph   │   (max 20 kontrendikasyon, 15 etkileşim)
│+Reranker│  │(Cypher)  │
└────┬────┘  └────┬─────┘
     │             │
     └──────┬──────┘
            │
            ▼
   ┌─────────────────────┐
   │  Deterministik Analiz│
   │  - Kümülatif Risk   │
   │  - CYP450 Mapping   │
   └────────┬────────────┘
            │
            ▼
   ┌──────────────────┐
   │  LLM (Claude     │  ← Faithfulness guardrail aktif
   │  Haiku 4.5)      │
   └────────┬─────────┘
            │
            ▼
   Yanıt + Kaynaklar + Risk Uyarıları
```

Pipeline 5 aşamadan oluşur:

1. **Query Augmentation** — soruyu anlayıp KÜB madde önceliği belirle
2. **ChromaDB Retrieval** — semantik arama + cross-encoder reranking ile ilgili chunk'ları getir
3. **Neo4j Graph** — kontrendikasyon ve etkileşim verilerini ekle (ContentPolicy limitli)
4. **Deterministik Analiz** — kümülatif yan etki (LLM'den bağımsız) + CYP450 çakışması
5. **LLM** — tüm bağlamı birleştirip yanıt üret

---

## 3. Teknoloji Yığını

| Katman | Teknoloji | Açıklama |
|--------|-----------|----------|
| PDF Parsing | PyMuPDF + pdfplumber + Camelot | Tablo dahil tam metin çıkarma |
| Embeddings | `multilingual-e5-large` (sentence-transformers) | Türkçe semantik arama |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` | İlk retrieval sonrası doğruluk artırımı |
| Vector DB | ChromaDB (persistent) | Cosine similarity, metadata filtreli arama |
| Graph DB | Neo4j | Kontrendikasyon ve etkileşim ilişki grafu |
| LLM (RAG) | Claude Haiku 4.5 (Anthropic API) / Local LLM (qwen2.5:32b via LM Studio/Ollama) | Yerel: maliyet sıfır; API: ~$0.009/sorgu |
| LLM (Extraction) | Together AI — Qwen3-235B-A22B | KUBExtractor; LM Studio'dan Together AI'a geçildi (2026-04-25); `LM_STUDIO_URL=api.together.xyz`, `LM_STUDIO_MODEL=Qwen3-235B` |
| LLM (RAGAS Eval) | Together AI — Qwen3-235B-A22B (Run 11-12) | Extraction ile aynı endpoint/model; `RAGAS_MODEL=Qwen3-235B`, `RAGAS_PROVIDER=local` |
| Backend | FastAPI | REST API, Swagger UI dahil |
| Frontend | Streamlit | Klinisyen arayüzü |
| Config | Pydantic BaseSettings | Env var validasyonu, startup kontrolü |
| Test | pytest | **81 test**, dış bağımlılık gerektirmez |
| Container | Docker + docker-compose | Multi-stage build, Neo4j dahil |
| Değerlendirme | RAGAS 0.4.3 | Faithfulness + Context Utilization + Context Recall (3-metrik standart, Run 11+) |

---

## 4. Proje Klasör Yapısı

```
PharmAssistVersion2/
├── app.py                          ← Streamlit UI (port 8501)
├── start_system.py                 ← servis başlatıcı
├── PROJE_DOKUMANTASYONU.md         ← bu belge
│
├── src/
│   ├── core/                       ← [YENİ v1.1] Sistemin temeli
│   │   ├── content_policy.py       ← TÜM boyut/limit kararları (tek yer)
│   │   ├── drug_record.py          ← DrugIdentity — canonical_id, normalized_name, inn
│   │   ├── name_resolver.py        ← TÜM isim eşleştirme servisi (tek yer)
│   │   └── exceptions.py           ← Typed exception hiyerarşisi
│   │
│   ├── pipeline/                   ← [YENİ v1.1] Ingestion orkestratörü
│   │   └── ingestion_pipeline.py   ← 4 script → 1 entry point (CLI dahil)
│   │
│   ├── agents/
│   │   ├── rag_engine.py           ← ana RAG pipeline; ContentPolicy entegre
│   │   ├── query_augmentor.py      ← soru sınıflandırma + zenginleştirme
│   │   └── patient_profile.py      ← PatientProfile modeli
│   │
│   ├── ingestion/
│   │   ├── pdf_parser.py           ← KUBParser v2.2 (PyMuPDF + tablo desteği)
│   │   ├── kub_extractor.py        ← [YENİ] LLM extraction; parse anında, Pydantic validasyonlu
│   │   ├── inn_resolver.py         ← [YENİ] INN propagation; ingestion'a entegre
│   │   ├── quality_gate.py         ← [YENİ] DrugValidator pipeline'a bağlandı
│   │   ├── kub_sections.py         ← KÜB madde başlıkları + öncelik haritası
│   │   ├── subsection_parser.py    ← 4.2 alt bölüm ayrıştırıcı
│   │   ├── lab_parser.py           ← lab raporu → parametre çıkarma
│   │   └── vision_ocr.py           ← Claude Vision OCR (karantina PDFleri için)
│   │
│   ├── retrieval/
│   │   ├── chroma_store.py         ← ChromaDB arama, metadata filtreli
│   │   └── reranker.py             ← cross-encoder reranking
│   │
│   ├── graph/
│   │   ├── neo4j_client.py         ← Neo4j singleton bağlantısı
│   │   ├── graph_retriever.py      ← Cypher sorgular; NameResolver entegre
│   │   ├── combi_retriever.py      ← ChromaDB + Neo4j birleşik bağlam; ContentPolicy limitli
│   │   ├── kub_to_graph.py         ← KÜB JSON → Neo4j; Section tam içerik (kırpma yok)
│   │   └── schema_builder.py       ← Neo4j constraint + index
│   │
│   ├── analysis/
│   │   ├── cumulative_risk.py      ← deterministik 9-kategori yan etki analizi
│   │   ├── cyp450_mapper.py        ← statik CYP450 profil tablosu (84 kayıt)
│   │   └── cyp450_extractor.py     ← LLM CYP extraction fallback
│   │
│   ├── evaluation/
│   │   └── ragas_eval.py           ← RAGAS pipeline; ContentPolicy entegre (drift engeli)
│   │
│   ├── api/
│   │   ├── main.py                 ← FastAPI (port 8080)
│   │   ├── routes.py               ← endpoint'ler
│   │   └── schemas.py              ← Pydantic request/response
│   │
│   ├── config/
│   │   └── settings.py             ← Pydantic BaseSettings, env validasyonu
│   │
│   └── data/
│       ├── normalization.py        ← normalize_drug_name (trademark + Türkçe char)
│       └── drug_validation.py      ← DrugValidator (QualityGate tarafından kullanılıyor)
│
├── scripts/
│   ├── run_eval.py                 ← RAGAS değerlendirme başlatıcı
│   ├── klinik_test.py              ← 15 klinik senaryo validasyon scripti
│   ├── db_health_check.py          ← ChromaDB ↔ Neo4j tutarlılık kontrolü
│   ├── gt_quality_check.py         ← GT soru kalite analizi (flag'ler)
│   ├── fix_gt_quality.py           ← GT kalite düzeltme scripti
│   │
│   │   # Artık kullanılmayan (IngestionPipeline'a entegre edildi):
│   ├── bulk_ingest.py              ← [ESKİ] → ingestion_pipeline.py kullan
│   ├── rebuild_interactions.py     ← [ESKİ] → kub_extractor.py ile entegre
│   ├── propagate_inn_interactions.py← [ESKİ] → inn_resolver.py ile entegre
│   └── patch_severity.py           ← [ESKİ] → extraction anında çözülüyor
│
├── data/
│   ├── raw_kub/                    ← ham TİTCK KÜB PDF dosyaları
│   ├── parsed_json/                ← her PDF'in chunk JSON'u (canonical_id dahil)
│   ├── quarantine/                 ← parse QA geçemeyen karantina raporları
│   └── eval/
│       ├── ragas_v3_questions.json ← aktif soru seti (32 soru — 4 GT fix, Q11 kaldırıldı)
│       ├── ragas_v7_qwen3_results.json  ← Run 11 (Qwen3)
│       ├── ragas_v8_gt_fixed_results.json ← Run 12 — AKTİF BASELINE (F:0.7607)
│       ├── ragas_v9_run13_results.json   ← Run 13 — Sprint ölçümü (F:0.6740, CR ↑)
│       ├── RAGAS_RUN_HISTORY.md    ← Run 1–13 kronolojisi
│       └── archive/                ← canonical (v1,v2,v3,v5,v6_run6) + exp runs
│
├── docs/
│   ├── ARCHITECTURE_STANDARDS.md  ← güncel mimari kurallar (v1.1)
│   ├── DRUG_PROCESSING_STANDARD.md← ilaç ekleme prosedürü (v1.1)
│   └── API_COST_PREVENTION.md     ← API maliyet önlemleri
│
├── configs/
│   └── app_config.yaml            ← RAG, LLM, Neo4j ayarları
├── tests/                         ← pytest (81 test)
├── chroma_db/                     ← ChromaDB persistent storage
└── logs/                          ← sorgu geçmişi, uygulama logları
```

---

## 5. Veri Modeli — KÜB Bölümleri

Her KÜB belgesi TİTCK formatında şu bölümleri içerir:

| Madde | Başlık | Klinik Önemi |
|-------|--------|--------------|
| 4.1 | Endikasyonlar | Hangi hastalıklar için |
| 4.2 | Pozoloji | Doz, uygulama, doz ayarı |
| 4.3 | Kontrendikasyonlar | Kesinlikle kullanılmamalı |
| 4.4 | Özel uyarılar | Dikkat edilmesi gereken durumlar |
| 4.5 | İlaç etkileşimleri | Diğer ilaçlarla çakışma |
| 4.6 | Gebelik / Laktasyon | Hamile ve emziren hastalarda kullanım |
| 4.8 | İstenmeyen etkiler | Yan etkiler |
| 4.9 | Doz aşımı | Zehirlenme yönetimi |

Sistem sorunun türüne göre ilgili maddeleri **öncelikli** olarak arar.

---

## 6. Hasta Profili

Her sorgu bir `PatientProfile` nesnesiyle birlikte gönderilir.

### Alanlar

```python
PatientProfile(
    yas=68,
    cinsiyet="erkek",
    kilo=75.5,                   # kg — doz hesaplaması için (özellikle pediatrik)
    gfr=38.0,                    # eGFR mL/dak/1.73m² — böbrek fonksiyonu
    karaciger_skoru="B",         # Child-Pugh A/B/C
    mevcut_ilaclar=["Warfarin", "Metformin"],
    alerjiler=["penisilin"],
    endikasyonlar=["Tip 2 Diyabet", "Hipertansiyon"],
    gebelik=False,
    emzirme=False,
    lab_degerleri={
        "ALT": 120,              # U/L
        "Kreatinin": 1.8,        # mg/dL
        "INR": 2.8,
        "K": 5.6,                # mEq/L
    }
)
```

### Türetilen Özellikler

- `bobrek_yetmezligi` → GFR < 60
- `bobrek_evresi` → CKD Evre 1–5
- `karaciger_yetmezligi` → Child-Pugh B veya C
- `geriyatrik` → yaş ≥ 65
- `pediyatrik` → yaş < 18
- `aktif_flags` → ChromaDB filtresi için `["renal", "hepatic", "geriatric"]`
- `anormal_lab_degerleri` → eşik dışı değerlerin listesi

### Lab Eşikleri

| Parametre | Kritik Üst | Kritik Alt | Birim |
|-----------|-----------|-----------|-------|
| ALT | 3× normal (120 U/L) | — | U/L |
| AST | 3× normal (120 U/L) | — | U/L |
| Kreatinin | ≥ 1.5 | — | mg/dL |
| K⁺ | ≥ 5.5 | ≤ 3.5 | mEq/L |
| Na⁺ | ≥ 150 | ≤ 130 | mEq/L |
| INR | ≥ 2.5 | — | — |
| HbA1c | ≥ 9.0 | — | % |
| Hemoglobin | — | ≤ 8.0 | g/dL |
| Trombosit | — | ≤ 50 | x10³/µL |
| Bilirubin | ≥ 2.0 | — | mg/dL |

---

## 7. RAG Pipeline Detayı

### 6.1 Query Augmentation (`src/agents/query_augmentor.py`)

Soru önce **türüne göre sınıflandırılır**:

| Soru Türü | Örnek İfade | Öncelikli Madde |
|-----------|------------|-----------------|
| `etkilesim` | "beraber kullanılabilir mi", "etkileşimi var mı" | 4.5, 4.4 |
| `kontrendikasyon` | "yazılabilir mi", "kullanılır mı", "kontrendike mi" | 4.3, 4.4 |
| `doz` | "dozu ne", "kaç mg", "doz ayarı" | 4.2 |
| `gebelik_laktasyon` | "hamile", "emzirme", "gebelikte" | 4.6, 4.3 |
| `yan_etki` | "yan etkisi", "advers etki", "neden olur" | 4.8, 4.4 |
| `doz_asimi` | "doz aşımı", "zehirlenme" | 4.9 |

Hasta profili sorguya eklenir: `"böbrek yetmezliği GFR 38 doz ayarı"` gibi zenginleştirilmiş metin ChromaDB aramasına gider.

### 6.2 ChromaDB Retrieval (`src/retrieval/chroma_store.py`)

- **Embedding modeli:** `multilingual-e5-large` (multilingual-e5-base'den yükseltildi)
- **Koleksiyon:** `kub_chunks` — **501 ilaç aktif corpus**, **8.757 chunk** (2026-04-25 Groq rebuild, 561 PDF)
- **Arama stratejisi (Faz 11 — section-aware + reranking):**
  1. Önce öncelikli maddelerle dar arama (k=8)
  2. Sonra ikincil maddelerle ek arama (k=4)
  3. Kritik maddeler (4.3, 4.5, 4.6) hasta filtresi olmadan aranır
  4. Cross-encoder reranking: top-20 aday → top-12 seçim
- **Minimum skor eşiği:** 0.55
- **İlaç adı normalizasyonu (v1.0):** Merkezi `src.data.normalization` modülü ile tüm ilaç adlarından trademark sembolleri (®, ™ vb.) temizlenmiş ve veritabanı kalıcı olarak normalize edilmiştir. Arama sırasında sorgular aynı normalizasyondan geçerek "LUSTRAL®" ve "LUSTRAL" gibi varyantların tek bir klinik varlığa ulaşması sağlanır.

### 6.3 Neo4j Graph Retrieval (`src/graph/`)

**Graf Şeması (v1.4 — Groq Rebuild):**

```
(:Drug)-[:HAS_SECTION]->(:Section)
(:Drug)-[:INTERACTS_WITH {severity, kaynak_madde, confidence}]->(:Drug)
(:Drug)-[:CONTRAINDICATED_FOR {kaynak_chunk}]->(:Condition)
(:Drug)-[:MENTIONS_INTERACTION]->(:DrugMention)
(:Drug)-[:CYP_INHIBITOR|CYP_INDUCER|CYP_SUBSTRATE]->(:CYPEnzyme)
(:Drug)-[:REQUIRES_DOSE_ADJUSTMENT]->(:DoseCondition)
(:Drug)-[:INTERACTS_WITH_CLASS]->(:DrugClass)
(:Drug)-[:HAS_WARNING]->(:Warning)
```

**Güncel İstatistikler (2026-04-26 — Groq Rebuild):**

| İlişki Tipi | Sayı | Açıklama |
|-------------|------|----------|
| INTERACTS_WITH | **4.021** | Drug↔Drug named bağlantı, %0 unknown |
| CONTRAINDICATED_FOR | 969 | Kontrendike durumlar |
| CYP_INHIBITOR | 552 | CYP enzim inhibitör bağlantıları |
| CYP_SUBSTRATE | 225 | CYP substrat bağlantıları |
| CYP_INDUCER | 114 | CYP indükleyici bağlantıları |
| REQUIRES_DOSE_ADJUSTMENT | 158 | Doz ayarı gerektiren durumlar |
| MENTIONS_INTERACTION | 10.007 | Ham metin etkileşim bahisleri |
| INTERACTS_WITH_CLASS | 571 | İlaç sınıfı bazlı etkileşimler |
| **Toplam Drug node** | **501** | 561 PDF'den (eski: 64 ilaç) |
| **Toplam edge** | **25.869** | — |

**LLM-based Extraction (v1.4 — Together AI):** `KUBExtractor` her ilaç için 4.3+4.5 bölümlerini **Together AI Qwen3-235B**'ye göndererek structured JSON alır. LM Studio'dan Together AI bulut inference'a geçildi (2026-04-25); Groq API entegrasyonu yapıldı ardından Qwen3-235B kalitesi nedeniyle Together AI tercih edildi. Severity ENUM zorunlu; unknown gelirse retry uygulanır.

**INN Propagation (v1.1):** `INNResolver.propagate_to_new_drug()` — aynı INN grubundaki ilişkileri yeni eklenen ilaca kopyalar. ⚠️ `d.inn` alanı mevcut rebuild'de boş (NULL) — INN propagation çalışmıyor. Sonraki rebuild'de düzeltilecek (bkz. Bilinen Sorunlar).

⚠️ **Bilinen Sorun — d.inn = NULL:** Groq rebuild'inde `DrugIdentity.inn` alanı Neo4j Drug node'larına yazılmadı. `unique_inn = 0`. Pratik etkisi: INTERACTS_WITH node-to-node bağlı olduğu için anlık sorun yok. INN-bazlı "aynı etken madde" sorgularında eksiklik oluşabilir.

**Context Limiter (v1.1):** `ContentPolicy.max_contraindications_in_context=20` — CO-DIOVAN gibi 100+ kontrendikasyonlu ilaçlarda LM Studio context overflow sorunu çözüldü.

### 6.4 Kümülatif Risk Analizi (`src/analysis/cumulative_risk.py`)

Birden fazla ilacın aynı organ sistemini olumsuz etkilemesi durumunda kümülatif risk hesaplanır.

**9 kategori:** Kardiyak/QT, Hepatotoksisite, Nefrotoksisite, Hematolojik, Nörotoksisite/SSS, Solunum, Gastrointestinal, Alerji/Anafilaksi, Endokrin/Elektrolit

- 2 ilaç aynı kategoride → `🟡 DİKKAT`
- 3+ ilaç aynı kategoride → `🔴 KRİTİK`

### 6.5 CYP450 Ontoloji Analizi (`src/analysis/cyp450_mapper.py`)

İlaçların CYP450 enzim profilleri karşılaştırılarak metabolizma etkileşimleri tespit edilir.

**3 senaryo:** inhibitör↔substrat (kan düzeyi artar), indükleyici↔substrat (etkinlik azalır), substrat↔substrat (rekabetif inhibisyon).

**Neo4j CYP Edge'leri (v1.4):** Groq rebuild ile CYP_INHIBITOR/CYP_INDUCER/CYP_SUBSTRATE ilişkileri Neo4j'e yazılıyor (toplam 891 edge). Statik tablo + Neo4j fallback ikili katman.

**Statik profil tablosu:** 84+ kritik ilaç kaydı içeren dondurulmuş (frozen) manuel liste.

**Otomatik Extraction Fallback (v1.0):** İlaç statik listede yoksa, sisteme eklenen `cyp450_extractor.py` modülü LLM (Anthropic veya Local LM Studio) kullanarak KÜB Madde 4.5 metninden enzim profilini (substrat, inhibitör, indükleyici) anlık olarak çıkarır. Bu sayede yeni eklenen tüm ilaçlar manuel veri girişi gerektirmeden analiz edilebilir. Şu an için manuel liste boşsa otomasyon devreye girmektedir (Hassasiyet ölçümü sonrası öncelik durumu "Otomasyon-Önce" olarak değiştirilecektir).

### 6.6 Prompt Yapısı ve Guardrail

**SYSTEM_PROMPT (MUTLAK KURAL):**
> "Aşağıdaki BAĞLAM bölümünde yer almayan hiçbir bilgiyi, ilaç adını, etken maddeyi, dozu veya mekanizmayı yazma."

**VALIDATE Pipeline (6 adım — post-LLM guardrail):**
1. "güvenlidir/zararsızdır" → "dikkatli kullanılmalıdır" (deterministik regex)
2. Kontrendikasyon doğrulama: 4.3 chunk varlığı + sinonim eşleştirme; yok/uyuşmuyorsa → `[AŞIRI YORUM]`
3. Doğrulanamayan cümleler → `[DOĞRULANAMADI]` etiketi
4. Numerik değer doğrulama: kaynak varsa sadece cited section chunk'ına, yoksa tüm chunk'lara bak (citation-level)
5. CYP yön kontrolü: inhibitör→düzey artmalı, indükleyici→düzey azalmalı; ters ise `[DOĞRULANAMADI-CYP]`
6. Verdict uyum: model seviyesi > desteklenen seviye → `[AŞIRI YORUM: bağlam bu şiddet seviyesini desteklemiyor]`

**RAGAS Tag Stripping:** `ragas_answer`'da VALIDATE etiketleri temizlenir (faithfulness false-negative önlenir). `full_answer`'da kullanıcı için korunur.

**Kaynak formatı:** `[İlaç Adı | Madde 4.3 | Sayfa 12]`

---

## 8. RAGAS Değerlendirme Sonuçları

### Metodoloji

**RAGAS (Retrieval Augmented Generation Assessment)** — LLM tabanlı otomatik değerlendirme çerçevesi.

**3-Metrik Standart (Run 11+ — 2026-04-26):**
- **Faithfulness (F):** LLM yanıtındaki her iddia retrieved context'te destekleniyor mu? (`desteklenen claim / toplam claim`) — GT gerektirmez
- **Context Utilization (CU):** Getirilen chunk'lar cevap için gerçekten kullanıldı mı? GT-free context_precision — Run 11'den itibaren standart
- **Context Recall (CR):** Ground truth'u karşılamak için gerekli bilgi chunk'larda mevcut mu? GT gerektirir

**Değerlendirici:** Together AI Qwen3-235B-A22B (Run 11-12) — önceki: Mistral-7B (Run 3-8), qwen2.5:32b (Run 9-10)  
**RAG modeli:** claude-haiku-4-5-20251001  
**Soru seti:** `data/eval/ragas_v3_questions.json` — 32 soru (Q11 kaldırıldı, 4 GT düzeltmesi — 2026-04-26)

### Soru Seti (v3 — 32 Soru, Mevcut — 2026-04-26 GT Fix)

| Kategori | Soru Sayısı | Örnek |
|----------|-------------|-------|
| Kontrendikasyon | 10 | Penisilin alerjisi, böbrek yetmezliği, hiperpotasemi |
| İlaç etkileşimi / CYP450 | 10 | Tegretol+Sanorone, İsoptin+Concor, Norodol+Cordarone |
| Böbrek/karaciğer doz ayarı | 6 | PRADAXA GFR 20, KEPPRA GFR 28 |
| Gebelik / emzirme | 4 | Perilife gebelik, Flagyl emzirme |
| Özel hasta grubu | 2 | Geriyatrik, pediatrik (Q11 kaldırıldı — Q33 ile çakışıyordu) |

**GT Kalite Düzeltmeleri (2026-04-26):**
- **Q02** PRADAXA GFR 20: KÜB-dışı alternatif doz (apiksaban/enoksaparin) GT'den çıkarıldı
- **Q08** LAMICTAL DC GFR 35: "şiddetli" → "orta dereceli böbrek bozukluğu (GFR 30-60)"
- **Q20** PROPYCIL+AMİODARON: Child-Pugh A=dikkatli, B/C=kontrendike şeklinde netleştirildi
- **Q29** METAFORMAL GFR 15: "kontrendikedir" → "çok dikkatli kullanılmalıdır (KÜB 4.4 özel uyarı)" — feokromasitoma 4.4 uyarısı, 4.3 kontrendikasyon değil
- **Q11** kaldırıldı: Q33 ile duplicate + GT çelişkisi

### Canonical Run Sonuçları

| Run | Tarih | Evaluator | Soru | F | CU | CR | Not |
|-----|-------|-----------|------|---|----|----|-----|
| Run 1 | 2026-04-07 | Haiku | 8 | 0.4000 | — | 0.7417 | Karşılaştırılamaz |
| Run 2 | 2026-04-08 | Haiku | 25 | 0.7811 | — | 0.8864 | Karşılaştırılamaz |
| Run 3 | 2026-04-14 | Mistral-7B | 30 | 0.7565 | — | 0.7377 | NaN %60 |
| Run 4 | 2026-04-15 | Mistral-7B | 33 | 0.7038 | — | 0.7601 | NaN %3 ✅ |
| Run 5 | 2026-04-17 | Mistral-7B | 33 | 0.6755 | — | **0.8646** | LM Studio fix |
| Run 6 | 2026-04-19 | Mistral-7B | 32 | **0.7179** | — | 0.8065 | GT rev. + 945 IW |
| Run 7 | 2026-04-19 | Mistral-7B | 33 | 0.7036 | — | 0.8102 | Yeni mimari |
| Run 8 | 2026-04-19 | Mistral-7B | 33 | 0.5548 | — | 0.8898 | F geçici düştü |
| Run 9 | 2026-04-19 | qwen2.5:32b | 33 | 0.6574 | — | 0.6571 | Evaluator geçişi |
| Run 10 | 2026-04-21 | qwen2.5:32b | 33 | 0.6792 | — | 0.6677 | 4 sistematik fix |
| Run 11 | 2026-04-26 | Qwen3-235B | 33 | 0.7029 | ~0.75 | 0.7283 | Yeni evaluator; 3-metrik ilk kez |
| **Run 12** | **2026-04-26** | **Qwen3-235B** | **32** | **0.7607** | **0.8028** | **0.7250** | **GT kalite fix (4 soru); Ort=0.7628 ✓ KABUL → AKTİF BASELINE** |
| Run 13 | 2026-04-27 | Qwen3-235B | 32 | 0.6740 | 0.7829 | 0.7365 | Sprint v1.5.0 etki ölçümü; CR ↑ ✅; F ↓ ⚠️ (4 NaN); Ort=0.7311 |
| Run 14 | 2026-04-28 | Qwen3-235B | 32 | 0.7153 | 0.7752 | 0.7571 | F kısmen toparlıyor; Ort=0.7492 |
| Run 15 | 2026-04-28 | Qwen3-235B | 32 | 0.7244 | 0.7640 | 0.7577 | Yakın sonuç; Ort=0.7487 |
| Run 16 | 2026-04-29 | Qwen3-235B | 32 | 0.7153 | 0.7530 | 0.7571 | VALIDATE 3-6 eklendi (tag stripping yok); Ort=0.7418 |
| Run 17 | 2026-04-29 | Qwen3-235B | 32 | 0.7089 | 0.7487 | 0.7630 | Tag stripping eklendi; AMARYL NaN kalıcı; Ort=0.7402 |

> **Not:** Run 1-2 Haiku eval (karşılaştırılamaz). Run 3-8 Mistral-7B. Run 9-10 qwen2.5:32b (daha strict). Run 11-13 Together AI Qwen3-235B (3-metrik standart: F+CU+CR).

**Aktif Baseline (Qwen3-235B, 3-metrik):** F=0.7607 | CU=0.8028 | CR=0.7250 | **Ort=0.7628 ✓ KABUL** (Run 12)  
**Run 17 Son Durum:** F=0.7089 CU=0.7487 CR=0.7630 Ort=0.7402 — CR ↑ +3.8pp (baseline'dan), F ~−5pp (CO-DİOVAN false positive başlıca neden)  
**Gerçekçi Tavan:** ~0.75-0.76 (Haiku 4.5 + Together.ai evaluator instability)  
**Sonraki Hedef:** CO-DİOVAN false positive fix → F regresyonunu giderme

> **Detaylı kronoloji ve experimental run'lar:** `data/eval/RAGAS_RUN_HISTORY.md`

### Run 10 Sistematik Fix'leri (2026-04-21)

| # | Sorun | Çözüm | Etki |
|---|-------|-------|------|
| Fix 1 | Q25 (JARDIANCE üriner) yanlış sınıflandırma — "risk" WARNING'e gidiyordu, 4.8 getirilmiyordu | SIDE_EFFECT_KEYWORDS'e "üriner", "enfeksiyon riski", "risk hakkında" eklendi | yan_etki türü doğru tespiti |
| Fix 2 | "eklenirse/başlanırsa" INTERACTION_KEYWORDS'de yoktu → CYP soruları yanlış türe gidiyordu | INTERACTION_KEYWORDS'e conditional yapılar eklendi | CYP etkileşim soruları doğru retrieve |
| Fix 3 | CYP bölümü prompt'ta en sonda kalıyordu → model ignore ediyordu | Etkileşim sorularında CYP bölümü prompt başına alındı, "ÖNCELİKLİ" header eklendi | CYP mekanizma yanıtları iyileşti |
| Fix 4 | Kontrendikasyon validasyonu 4.3 varlığı kontrol ediyordu, içeriğini değil | validate_response() 4.3 metninde klinik durum anahtar kelimesini arar; yoksa "kontrendikedir"→"dikkatli kullanılmalıdır" | Yanlış kontrendikasyon iddiası engellendi |

---

## 11. Geliştirme Stratejisi

### Veri Kalitesi ✅ (2026-04-26 itibarıyla)
Corpus, pipeline ve graf verisi büyük sıçrama yaptı:
- **501 ilaç**, **10.588 chunk** (4.4 sub-chunking sonrası), ChromaDB'de aktif
- **4.021 INTERACTS_WITH** ilişkisi (%0 unknown — named node bağlantılar)
- **969 CONTRAINDICATED_FOR**, **891 CYP edge**, **158 REQUIRES_DOSE_ADJUSTMENT**
- **CYP450:** 84 kayıt statik tablo + Neo4j CYP edge + LLM fallback extraction
- Kümülatif risk: 9 kategori, deterministik
- RAGAS benchmark: F=0.7607 | CU=0.8028 | CR=0.7250 | **Ort=0.7628 ✓ KABUL** (Run 12)
- VALIDATE Pipeline: 6 adım (citation-level + CYP yön + verdict alignment)
- **95 pytest test geçiyor**

### Sprint 2026-04-26 — Model Davranış İyileştirmeleri ✅

4 model-odaklı geliştirme (GT bazlı fix yapılmadı, tüm değişiklikler sistem genelinde):

| # | Fix | Açıklama | Etkilenen Dosya |
|---|-----|----------|-----------------|
| A | **Answer Calibration Layer** | Pre-LLM deterministik klinik etiket: 4.3 → KONTREDİKE, 4.4 → DİKKATLİ_KULLANIM, 4.2 → DOZ_AYARI. Over-conservatism bias'ını azaltır. | `rag_engine.py` |
| B | **CYP Zorunlu Kural** | Etkileşim sorusunda CYP bilgisi mevcutsa LLM MUTLAKA [CYP450] etiketiyle açıklamalı. | `rag_engine.py` |
| C | **4.4 Sub-chunking** | 2500+ karakter 4.4 bölümleri paragrafa göre ~2200 karakter parçalara bölündü (additive). 422 ilaç, 1827 yeni sub-chunk. Feokromasitoma gibi rare condition'lar artık ayrı embedding'e sahip. | `subsection_parser.py`, `add_44_subchunks.py` |
| D | **Klinik Sinonim Genişletme** | 40+ tıbbi kısaltma (KBY/KOAH/DVT/SSRI vb.) → tam Türkçe karşılığı. Yalnızca ChromaDB retrieval'da kullanılır. | `query_augmentor.py` |

Ayrıca Run 12 öncesinde:
- **SPECIAL_CONDITION_KEYWORDS**: feokromasitoma/miyastenia gravis/QT uzaması → 4.4 öncelik
- **System prompt guardrail**: KÜB dışı ilaç önerisi MUTLAK YASAK

### Bilinen Sorunlar (Çözüm Bekleyen)
| # | Sorun | Etki | Öncelik |
|---|-------|------|---------|
| 1 | Q14/Q23 context_utilization NaN | RAGAS ortalamasını etkiliyor (2/32 = %6) | Düşük |
| 2 | LIPITON/URIKOLIZ eval adı eşleşme sorunu | Eval coverage eksik görünüyor (RAG'da eşleşiyor) | Düşük |

### Sonraki Hedefler
1. **F Regresyon Analizi** — Run 13 F=0.674 kök neden: NaN soruları (Q10/Q11/Q12/Q30), Answer Calibration etki, CYP zorunlu kural → hedeflenen fix
2. **Q26 RENITEC Anomali** — F=0.133 çok düşük, model yanıtı analiz edilmeli
3. **HyDE** — Hypothetical Document Embeddings retrieval geliştirme
4. **Contextual Compression** — Chunk'lardan ilgili bölümü öne çıkarma
5. **UI güncellemesi** — 501 ilaç corpus ile multiselect refresh

### Run 1–2 Arasında Uygulanan Düzeltmeler (v2 Fix)

| # | Sorun | Düzeltme | Etki |
|---|-------|----------|------|
| 1 | Neo4j/CYP450 bağlamları RAGAS'a geçilmiyordu | `run_eval.py` contexts listesine ek kaynaklar eklendi (önce) | En yüksek katkı |
| 2 | CYP450 statik tablosu sadece 4 ilaç içeriyordu | 25 sorgu ilacı dahil 57 kayda genişletildi | CYP analizi aktif hale geldi |
| 3 | İlaç adı `$eq` eşleşme hatası → 0 chunk | Trademark normalizasyonu + ChromaDB adı çözümlemesi | COZAAR gibi ilaçlar artık bulunuyor |
| 4 | LLM 1200 kar görürken RAGAS 800 kar görüyordu | `_MAX_CHUNK_CHARS = 800 → 1200` | Bağlam uyumu sağlandı |
| 5 | `validate_response()` NO-OP (boş döngü) | Gerçek token tespiti + loglama eklendi | KÜB dışı içerik izlenebilir oldu |
| 6 | `_MAX_CONTEXTS = 6` ek kaynakları kesiyordu | `_MAX_CONTEXTS = 9` + ek kaynaklar listeye önce alındı | Fix #1'in çalışması sağlandı |
| 7 | RAGAS NaN %16 | `max_tokens = 1024 → 2048`, NaN soru loglama | Parse hatası azaldı |
| 8 | `lab_degerleri` PatientProfile'a geçilmiyordu | `run_eval.py` profil oluşturmaya eklendi | Q25 (K=5.8) query enrichment düzeldi |

---

## 9. API

### Endpoint'ler

| Method | Yol | Açıklama |
|--------|-----|----------|
| GET | `/api/v1/health` | Sistem durumu, ChromaDB chunk sayısı |
| POST | `/api/v1/query` | Ana sorgu endpoint'i |
| GET | `/api/v1/stats` | ChromaDB koleksiyon istatistikleri |
| GET | `/api/v1/quarantine` | Parse QA geçemeyen KÜB listesi |

### POST /api/v1/query — İstek

```json
{
  "soru": "Bu hastaya Augmentin yazılabilir mi?",
  "hasta": {
    "yas": 68,
    "cinsiyet": "erkek",
    "gfr": 38.0,
    "karaciger_skoru": null,
    "mevcut_ilaclar": ["Warfarin 5mg", "Metformin 1000mg"],
    "alerjiler": ["penisilin"],
    "endikasyonlar": ["Tip 2 Diyabet", "Hipertansiyon"],
    "gebelik": false,
    "emzirme": false,
    "lab_degerleri": {
      "ALT": 120,
      "K": 5.6,
      "INR": 2.8,
      "Kreatinin": 1.8
    }
  },
  "hedef_ilaclar": ["AUGMENTIN 400 MG/57 MG ORAL SÜSPANSIYON"],
  "n_results": 8
}
```

### POST /api/v1/query — Yanıt

```json
{
  "soru": "Bu hastaya Augmentin yazılabilir mi?",
  "yanit": "### 1. Kısa Özet\n...",
  "kaynaklar": [
    {
      "ilac_adi": "AUGMENTIN 400 MG/57 MG...",
      "madde_no": "4.3",
      "madde_baslik": "Kontrendikasyonlar",
      "sayfa": 4,
      "score": 0.812,
      "kaynak_etiketi": "[AUGMENTIN | Madde 4.3 | Sayfa 4]"
    }
  ],
  "kumlatif_riskler": [...],
  "cyp_etkilesimler": [...],
  "soru_turleri": ["kontrendikasyon"],
  "model": "claude-haiku-4-5-20251001",
  "prompt_token_sayisi": 2847,
  "yanit_token_sayisi": 412
}
```

---

## 10. Streamlit UI

`app.py` — port 8501

**Mevcut Durum — Sidebar (Hasta Profili):** Yaş, kilo, cinsiyet, eGFR, özel durum checkbox'ları, mevcut ilaçlar (multiselect), alerjiler, endikasyonlar, 10 lab parametresi, lab belgesi yükleme (UI-1 tamamlandı).

**Mevcut Ana Panel:**
1. İlaç seçimi (60 ilaç, çoklu)
2. Soru girişi
3. Risk Özeti Paneli (🔴 KRİTİK / 🟡 DİKKAT / 🔵 BİLGİ)
4. Kümülatif Yan Etki Analizi (Phase 8)
5. CYP450 Enzim Etkileşimleri (Phase 8)
6. Klinik Yanıt (LLM çıktısı, markdown)
7. Kaynaklar (chunk içerikleri, skorlar)
8. Sorgu geçmişi (son 5 sorgu)

---

### Faz 14 — UI Geliştirme Planı

Her madde ayrı bir geliştirme seansında uygulanacak şekilde tasarlandı.

---

#### UI-1 — Lab Belgesi Yükleme ve Otomatik Parse

**Ne:** Kullanıcı lab raporunu PDF veya görüntü olarak yükler. Sistem değerleri otomatik tespit edip forma doldurur; kullanıcı kontrol edip onaylar.

**Neden:** Manuel giriş hata kaynağı (5.2 yerine 52 gibi). Klinisyenin lab raporu zaten elinde — tekrar yazmak gereksiz sürtünme. Hatalı lab verisi yanlış risk değerlendirmesine yol açar.

**Nasıl yapılır:**
- `src/ingestion/lab_parser.py` — yeni modül
  - PyMuPDF ile PDF'den metin çıkar
  - Regex ile parametre tespiti: `ALT`, `SGPT`, `Alanin aminotransferaz` → `ALT` (geniş eşleşme, hastaneden hastaneye farklı format)
  - Desteklenen parametreler: ALT, AST, Kreatinin, K, Na, INR, HbA1c, Bilirubin, Hemoglobin, Trombosit, GFR
  - Döndürür: `{"ALT": 87.0, "Kreatinin": 1.8, ...}` — sadece tespit edilenler
- `app.py` sidebar'a `st.file_uploader` (PDF/PNG/JPG) eklenir
- Parse edilen değerler form alanlarına otomatik doldurulur (`st.session_state` üzerinden)
- "Kabul et / düzenle" adımı zorunlu — parse hatası klinik hata riski taşır
- Parse edilemeyen alanlar boş kalır, kullanıcı manuel tamamlar

**Kısıtlar:** OCR gerektirmez (dijital PDF yeterli). Görüntü formatı için `pytesseract` opsiyonel.

**✅ Tamamlandı — 2026-04-09**

| Dosya | Değişiklik |
|-------|-----------|
| `src/ingestion/lab_parser.py` | Yeni modül — `parse_lab_pdf`, `parse_lab_image`, `parse_lab_file` |
| `app.py` | Import, `pending_lab` session state, `_LAB_KEY_MAP`, lab uploader widget, Kabul Et / İptal butonu |

**Uygulama detayları:**
- `lab_parser.py`: 11 parametre için çok-pattern regex (ALT/SGPT/Alanin aminotransferaz → `ALT` vb.), Türkçe ondalık virgül desteği, `_sanity_check()` ile makul olmayan değer filtresi
- `app.py` Laboratuvar expander'ına `st.file_uploader` (PDF/PNG/JPG) eklendi
- Dosya yüklenince parse → `st.session_state.pending_lab` → 2 kolonlu önizleme
- **✅ Kabul Et ve Doldur**: `_LAB_KEY_MAP` üzerinden session_state key'lerini günceller → `st.rerun()` ile formlar dolar
- **❌ İptal**: pending_lab temizlenir
- GFR da lab'dan parse edilebilir (`key="gfr_input"`)
- Aynı dosyayı tekrar parse etmemek için `_lab_upload_ad` kontrolü

---

#### UI-2 — Sıfır Chunk Uyarısı

**Ne:** Sorgu sonucunda hiç chunk bulunamazsa kullanıcıya açıklayıcı uyarı gösterilir.

**Neden:** Şu an `len(response.kaynaklar) == 0` olduğunda kullanıcı sadece genel/boş bir yanıt görüyor. Neden olduğunu anlamıyor; ilaç adı seçim hatasını fark etmiyor.

**Nasıl yapılır:**
- `app.py`'de sorgu sonrası `if not response.kaynaklar:` kontrolü
- Sarı uyarı kutusu: `"Bu ilaç için KÜB belgesi bulunamadı. İlaç seçimini kontrol edin veya seçim yapmadan sorgulayın."`
- Ek öneri: Seçilen ilaç adını ChromaDB listesiyle karşılaştır, benzer ada sahip ilaçları öner

**✅ Uygulama Notu (2026-04-08):**
- `app.py` satır 464–484'e eklendi
- Metadata satırının hemen altında, Risk Özeti panelinden önce gösteriliyor
- Kullanıcı ilaç seçmişse `difflib.get_close_matches` (cutoff=0.4, max 5 öneri) ile ChromaDB listesindeki benzer adlar uyarıya ekleniyor
- Dış bağımlılık yok — `difflib` standart kütüphane

---

#### UI-3 — İlaç Adı Kısaltma (Multiselect Okunabilirliği)

**Ne:** Multiselect'te uzun KÜB adları yerine kısa form gösterilir; tam ad tooltip veya parantez içinde yer alır.

**Neden:** `"AUGMENTİN 400 mg/57 mg oral süspansiyon hazırlamak için kuru toz içeren saşe"` multiselect kutusunda yarısı kesiliyor. 60 ilaçla seçim kullanışsız hale geliyor.

**Nasıl yapılır:**
- `_get_ilac_listesi()` fonksiyonuna kısa ad üretimi eklenir: ilk 2-3 kelime + doz bilgisi (ör: `AUGMENTIN 400mg/57mg`)
- `ilac_adi_map: dict[str, str]` = `{kisa_ad: tam_ad}` — sorgu sırasında tam ad kullanılır
- Multiselect `options=kisa_adlar`, seçim sonrası `tam_ad = ilac_adi_map[secim]` ile çözümlenir

**Uygulama Notu (2026-04-08):**
- `import re` eklendi
- `_DOZ_RE` regex: `400 MG`, `57 MG`, `10 mg` gibi doz token'larını tanır
- `_kisa_ad_uret(tam_ad)` → marka adı + regex ile tespit edilen ilk 2 doz token'ı birleştirilir (`400MG/57MG`); doz yoksa ilk 3 kelime döner
- `_get_ilac_harita()` → `{kisa_ad: tam_ad}` map'i, `@st.cache_data(ttl=300)` ile önbellekte; çakışan kısa adlara otomatik sayaç eklenir (ör: `NORVASC 10MG (2)`)
- Multiselect `options=kisa_adlar`; arama hem kısa hem tam ada bakar; seçim sonrası `hedef_ilaclar_secim = [ilac_harita[k] for k in hedef_kisa_secim]` ile tam ad çözümleniyor — RAG engine değişmeden çalışıyor
- **Durum: TAMAMLANDI**

---

#### UI-4 — Sidebar Tab Yapısı

**Ne:** Mevcut uzun sidebar üç sekmeye bölünür: `[Hasta Profili]` `[Laboratuvar]` `[Mevcut İlaçlar]`.

**Neden:** Sidebar'da 20+ input var. Klinisyen hangi alanı nerede arayacağını bulmakta zorlanıyor. Lab sekmesinde yükleme butonu (UI-1) daha doğal konumlanır.

**Nasıl yapılır:**
- `st.tabs(["👤 Hasta", "🧪 Laboratuvar", "💊 Mevcut İlaçlar"])` — sidebar içinde Streamlit tab desteği yok, ana panel üstüne taşınabilir ya da `st.expander` gruplarıyla bölünebilir
- Alternatif: sidebar'ı `st.expander` bloklarına böl (Genel Bilgiler / Lab / İlaçlar)
- Lab sekmesine UI-1 yükleme widget'ı entegre edilir

**Uygulama Notu (2026-04-08):**
- `st.expander` alternatiği uygulandı — sidebar içinde `st.tabs` Streamlit tarafından desteklenmiyor
- Sidebar başlığı `"### 👤 Hasta Profili"` → `"### 💊 PharmAssist"` olarak güncellendi
- 3 expander grubu oluşturuldu:
  - `👤 Hasta Profili` (`expanded=True`) — yaş, cinsiyet, eGFR, özel durumlar, alerjiler, endikasyonlar
  - `🧪 Laboratuvar` (`expanded=False`) — 10 lab parametresi + anormal değer uyarısı
  - `💊 Mevcut İlaçlar` (`expanded=False`) — ilaç listesi text area
- Tüm değişkenler `with st.sidebar:` scope'unda kaldı; `PatientProfile` oluşturma kodu değişmedi
- `expander` içindeki widget'lar görsel olarak kapalı olsa da Streamlit tarafından daima render edilir → `lab_degerleri` her zaman tanımlı
- **Durum: TAMAMLANDI (2026-04-08)**

**Güncelleme (2026-04-10):**
- **Kilo alanı eklendi:** `👤 Hasta Profili` expander'ında yaş ve cinsiyet arasına "Kilo (kg)" input eklendi (0-300 kg aralığı, 0.5 adım)
  - PatientProfile schema'sına `kilo: Optional[float]` field'ı eklendi
  - Tıbbi doz hesaplamaları için gerekli (özellikle pediatrik/geriatrik hastalar)
- **Mevcut İlaçlar UI refaktörü:** text area → multiselect dropdown
  - **Eski sistem:** Virgülle ayrılmış ilaç listesi (manuel giriş)
  - **Yeni sistem:** ChromaDB'den dinamik ilaç listesi + arama filtresi + multiselect
  - İlaç listesi sidebar'ın dışında önceden yükleniyor (ilaç_listesi + ilac_harita)
  - Fallback mekanizması: ChromaDB başarısız olursa, manual text_area sunuluyor
  - Prefix match fallback var (exact match başarısız olduğunda)
- **Durum: TAMAMLANDI (2026-04-10)**

---

#### UI-5 — Sorgu Geçmişi Kalıcı Log

**Ne:** Sorgu geçmişi session yerine dosyaya yazılır; sayfa yenilenince kaybolmaz.

**Neden:** Şu an `st.session_state.gecmis` kapanınca sıfırlanıyor. Klinisyen önceki sorgulara dönemez. Log dosyası aynı zamanda sistem kullanımını izlemek ve sunum için örnek veri toplamak açısından değerli.

**Nasıl yapılır:**
- Her sorgu sonrası `data/logs/query_history.jsonl` dosyasına satır eklenir (soru, yanıt özeti, ilaçlar, tarih-saat, chunk sayısı)
- Uygulama açılışında son 20 kayıt yüklenir
- Sidebar veya ana panelde "Geçmiş Sorgular" expander olarak gösterilir
- Hassas hasta verisi (lab değerleri) log'a yazılmaz — yalnızca soru + yanıt + metadata

**Uygulama Notu (2026-04-08):** ✅ Tamamlandı.
- `app.py`'ye `import json` + `from datetime import datetime` eklendi
- `_gecmis_kaydet()` fonksiyonu: her sorguda `data/logs/query_history.jsonl`'e satır ekler; lab değerleri, yaş, GFR, tanılar yazılmaz
- `_gecmis_yukle()` fonksiyonu: dosyadan son 20 kaydı ters sırada (en yeni başta) okur
- `st.session_state.kalici_gecmis` uygulama açılışında dosyadan yüklenir
- Sorgu sonrası `_gecmis_kaydet()` çağrılır ve `kalici_gecmis` güncellenir
- Eski session-only "Önceki Sorgular" kaldırıldı; yerine `Geçmiş Sorgular (N kayıt)` expander geldi — her kayıtta tarih, tür, ilaçlar, chunk sayısı ve yanıt özeti (ilk 300 karakter) gösterilir
- `data/logs/` dizini oluşturuldu

---

### Faz 14 Öncelik Tablosu

| # | Geliştirme | Efor | Klinik Değer |
|---|-----------|------|--------------|
| UI-1 | Lab belgesi yükleme + otomatik parse | Orta | Çok Yüksek | ✅ 2026-04-09 |
| UI-2 | Sıfır chunk uyarısı | Düşük | Yüksek |
| UI-3 | İlaç adı kısaltma | Düşük | Orta |
| UI-4 | Sidebar tab/expander yapısı | Orta | Orta |
| UI-5 | Sorgu geçmişi kalıcı log | Düşük | Orta |

**Önerilen sıra:** UI-2 → UI-3 → UI-1 → UI-4 → UI-5
(Hızlı kazanımlar önce, sonra büyük yapısal değişiklikler)

---

## 11. Konfigürasyon

### .env Dosyası (Zorunlu)

```env
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=claude                  # "claude" | "local"
NEO4J_URL=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
PHARMASSIST_API_KEY=...              # Tanımlıysa /query header ister
ALLOWED_ORIGINS=*                    # Production'da kısıtla
APP_ENV=development
```

### configs/app_config.yaml

```yaml
rag:
  min_similarity_score: 0.30
  max_n_results: 15
llm:
  max_tokens: 1400
neo4j:
  query_timeout: 5
patient:
  geriyatrik_yas_esigi: 65
  bobrek_yetmezligi_gfr_esigi: 60
```

---

## 12. Servis Yönetimi

```bash
# Streamlit (UI)
.venv/Scripts/streamlit run app.py --server.port 8501 --server.headless true

# FastAPI (API)
.venv/Scripts/uvicorn src.api.main:app --port 8080

# Docker
docker-compose up -d
```

**Process Kill (Windows)** — `taskkill` bash'tan çalışmıyor:
```python
subprocess.run(['powershell', '-NoProfile', '-Command', f'Stop-Process -Id {pid} -Force'])
```

---

## 13. Testler

```bash
.venv/Scripts/python -m pytest tests/ -v
# 49 passed
```

| Dosya | Test Sayısı | Kapsam |
|-------|-------------|--------|
| `test_patient_profile.py` | 16 | PatientProfile özellikleri, lab eşikleri |
| `test_schemas.py` | 25 | Pydantic request/response modelleri, Phase 8 şemaları |
| `test_settings.py` | 8 | Env var validasyonu, auth flag, production modu |

---

## 14. Yüklü KÜB Corpus

### Dalga 1 (4 ilaç — Temel Sistem)

| İlaç | Etken Madde |
|------|------------|
| AUGMENTIN 400mg/57mg | Amoksisilin + Klavulanik Asit |
| A-FERİN 1mg+160mg/5mL | Parasetamol + Psödoefedrin |
| ONAXAN 20mg | Rivaroksaban |
| PLASORİN 10mg | Varfarin |

### Dalga 2 (60 ilaç — 2026-04-07)

ChromaDB: **1036 chunk** | Neo4j: **59 ilaç**

Gruplar: Antikoagülanlar (Eliquis, Plavix, Clexane), Antihipertansifler (Norvasc, Beloc, Concor, Cozaar, Lasix), Antidiyabetikler (Januvia, Jardiance, Lantus, Victoza), Antibiyotikler (Cipro, Flagyl, Augmentin), Statinler (Crestor, Lipitor), Nöroloji (Keppra, Xanax, Lustral, Cipralex, Contramal), Diğer (Voltaren, Colchicum Dispert, Ürikoliz, Zofran, Zofrantm, Pantpas, ve daha fazlası).

### Dalga 3 — Tam TİTCK Corpus (2026-04-14)

ChromaDB: **7.585 chunk** | Neo4j: **427 ilaç** | INTERACTS_WITH: **20.497**

Tüm erişilebilir TİTCK KÜB PDF'leri toplu işlendi (`scripts/bulk_ingest.py`). 44 resim bazlı PDF karantinaya alındı (`data/quarantine/*_OCR_GEREKLI.md`) — şimdilik işlenmedi, ilerleyen sürümlerde ele alınacak.

---

## 15. Kod Kalitesi ve Mimari Kararlar

**ChromaDB singleton:** `@lru_cache(maxsize=1)` ile her `search()` çağrısında yeni client oluşturulması önlendi.

**Neo4j singleton + timeout:** `@lru_cache` + `connection_timeout=5` ile uzun sorgular engellendi.

**İlaç adı normalizasyonu:** PDF'den gelen PUA trademark karakterleri (`®` → `\uf8e8`, `\uf0d2`, `\uf6da`) `_TRADEMARK_RE` regex ile normalize edilir; `_get_drug_name_map()` lru_cache ile process boyunca bir kez yüklenir.

**ChromaDB prefix match:** `_resolve_drug_names()` önce exact normalized match, sonra `key.startswith(norm)` prefix match dener. "METFORMIN" → "METAFORMAL 1000 mg film kaplı tablet" ve "METAFORMAL 850 mg..." şeklinde tüm varyantları döndürür.

**Phase 8 defensive coding:**
```python
kum_sonuc = None
try:
    kum_sonuc = kumlatif_analiz(...)
except Exception as e:
    logger.warning(...)
kumlatif_riskler = kum_sonuc.riskler if kum_sonuc is not None else []
```

**Patient flags filtresi istisnası:** 4.3, 4.4, 4.5 maddeleri hasta filtresi olmadan aranır — evrensel uyarılar kaçırılmasın.

**RAGAS contexts bütünlüğü:** Neo4j, kümülatif risk ve CYP450 çıktıları RAGAS contexts listesinin **başına** eklenir; ChromaDB chunk'ları sonra gelir. `_MAX_CONTEXTS = 9` (3 ek kaynak + 6 chunk).

### Bilinçli Sınırlılıklar

- `MIN_SCORE_THRESHOLD = 0.55` — düşük skorlu chunk'lar atılır
- `MAX_CHUNKS_PER_QUERY = 12` — token limiti için cap
- Cross-encoder reranker İngilizce eğitimli — Türkçe sıralama kalitesi sınırlı
- `INTERACTS_WITH` severity %75.4 "unknown" — INN cross-ref eşleşmesinde bağlam penceresi yeterli değil
- CYP profil tablosu statik — yeni ilaç eklenince `cyp450_mapper.py` güncellenmeli
- Vision OCR maliyeti yüksek (~$0.70/PDF) — karantina PDFleri şimdilik işlenmedi

---

## 16. Dalga 4 — Yapılan Değişiklikler (2026-04-11 / 2026-04-12)

### Phase 0 — KÜB PDF Parse Yeniden Yazımı

`src/ingestion/pdf_parser.py` tamamen yeniden yazıldı (v2.0):

| Sorun | Çözüm |
|-------|-------|
| `get_text()` stream order — tablolar ve uyarı kutuları yanlış sırada | `get_text('blocks')` + Y-koordinat sıralaması `(round(y1/5)*5, x0)` |
| Tablo yapısı kayboluyordu — hücreler birleşik metin | `find_tables()` + bbox çakışma tespiti → GFM markdown |
| Madde 1 öncesi kare kutu uyarıları parse edilmiyordu (CONTRAMAL, CİPRO) | `_extract_ozel_uyari()` → `ozel_uyari` chunk, `risk_seviyesi="critical"` |
| Resim bazlı PDF'ler sessizce başarısız | `ImageBasedPDFError` + karantina raporu (`data/quarantine/`) |
| İmza kodu satırları chunk'lara karışıyordu | `_clean_chunk_text()` regex temizleme |

Yeni fonksiyonlar: `ImageBasedPDFError`, `_check_image_based()`, `_page_text_sorted()`, `_table_to_markdown()`, `_extract_page_text_with_tables()`, `_extract_ozel_uyari()`, `_clean_chunk_text()`

### Phase 0.6 — Full Corpus Re-Index

| Metrik | Önceki | Sonrası |
|--------|--------|---------|
| Toplam ilaç | 59 | **64** |
| ChromaDB chunk | 1031 | **1120** |
| Neo4j INTERACTS_WITH | 0* | **247** |
| Karantina | 0 | 1 (resim bazlı PDF) |

*INN cross-reference ile çalışıyor, `etken_madde` alanı gereksiz.

### Phase 2 & 3 — CYP450 ve Neo4j Doğrulama

- CYP450 entegrasyonu aktif: `cyp_metin` LLM prompt'una + RAGAS contexts listesine geçiyor
- Neo4j 247 INTERACTS_WITH ilişkisi — önceki "0 ilişki" sorunu mevcut değilmiş

### Phase 4 — RAGAS Strateji Yenileme

**v10 bulgusu:** Turkish patch (Haiku prompt öneki) etkisiz — kaldırıldı.

- `_TURKISH_SYSTEM_PREFIX` ve `_patch_prompts_for_turkish()` silindi (`ragas_eval.py`)
- Default evaluator: **Mistral (local)** — v10'da R=0.75, Haiku R=0.2
- v10 ground truth KÜB'e göre düzeltildi (JANUVIA 50 mg GFR<45, CRESTOR aktif KI)
- `run_eval.py`'e `--v10` seçeneği eklendi

### Phase 5 — Corpus ve CYP Profil Genişletmesi

Yeni ilaçlar: **METAFORMAL 1000 mg** (Metformin), **ZİTOREL 500 mg** (Azitromisin), **BELOC ZOK 25 mg**, **BELOC ZOK 50 mg**

CYP profil tablosu: 49 → **84 kayıt** (`src/analysis/cyp450_mapper.py`)
Eklenenler: JANUVIA, JARDIANCE, DİAMİCRON, DELTACORTRİL, ALDACTONE, LANSOR, NAPROSYN, ÜRİKOLİZ, NEURONTİN, KEPPRA, LİPİTOR, ZİTOREL, METAFORMAL, BELOC ZOK, PLASORİN varyantları

### Phase 6 — Klinik Validasyon Script'i

`scripts/klinik_test.py` — 15 senaryo (12 DB + 3 hallucination test):

```bash
.venv/Scripts/python scripts/klinik_test.py                    # Tüm 15 senaryo
.venv/Scripts/python scripts/klinik_test.py --sadece-db        # S13-15 hariç
.venv/Scripts/python scripts/klinik_test.py --soru 5           # Tek soru
.venv/Scripts/python scripts/klinik_test.py --output sonuc.json
```

**İlk çalıştırma sonuçları (2026-04-11, `data/eval/klinik_v1.json`):**

| Soru | Tür | Sonuç | Not |
|------|-----|-------|-----|
| S01 AUGMENTİN + penisilin | Kontrendikasyon | ✓ İyi | Net "kontrendikedir" |
| S02 KEPPRA GFR 28 | Doz ayarı | ✗ Zayıf | Doz tablosu retrieval'da kesilmiş |
| S03 PLASORİN + FLAGYL | CYP etkileşimi | ✗ Zayıf | CYP buldu ama yanıta entegre edemedi |
| S04 LANTUS gebelik | Gebelik | ✓ İyi | Kategori C, klinik gözlem vurgusu |
| S05 LUSTRAL + CONTRAMAL | Farmakodinamik | ✓ İyi | Serotonin sendromu riski doğru |
| S06 CRESTOR Child-Pugh B | Kontrendikasyon | ✓ İyi | Net "kontrendikedir" |
| S07 CİPRO + PLASORİN | CYP1A2 | ✓ İyi | INR takibi zorunluluğu doğru |
| S08 XANAX 83 yaş + demans | Geriyatrik | ~ Kısmi | "Başlanabilir" — çok müsamahakâr |
| S09 FLAGYL emzirme | Emzirme | ✓ İyi | "Kullanılmamalı" net |
| S10 NEURONTİN 10 yaş | Pediatrik | ✗ Zayıf | Pediyatrik doz tablosu bulamadı |
| S11 PLAVIX + LANSOR | CYP2C19 | ~ Kısmi | Mekanizma tam ifade edilmedi |
| S12 DİAMİCRON GFR 40 | Doz ayarı | ✓ İyi | Hipoglisemi uyarısı mevcut |
| S13 Verapamil | Hallucination | ✓ GEÇTI | BİLGİ YOK dedi |
| S14 Mirtazapin | Hallucination | ✓ GEÇTI | BİLGİ YOK dedi |
| S15 Lisinopril | Hallucination | ✓ GEÇTI | BİLGİ YOK dedi |

**İkinci çalıştırma sonuçları (2026-04-12, `data/eval/klinik_v2.json`) — Phase 7 düzeltmeleri sonrası:**

| Soru | Tür | v1 | v2 | Değişim |
|------|-----|----|----|---------|
| S01 AUGMENTİN + penisilin | Kontrendikasyon | ✓ | ✓ | — |
| S02 KEPPRA GFR 28 | Doz ayarı | ✗ | ✓ | **Düzeldi** — `_extract_chunk_window` GFR tablosunu buldu |
| S03 PLASORİN + FLAGYL | CYP etkileşimi | ✗ | ✓ | **Düzeldi** — CYP2C9 substrat rekabeti → INR artışı yanıta girdi |
| S04 LANTUS gebelik | Gebelik | ✓ | ✓ | — |
| S05 LUSTRAL + CONTRAMAL | Farmakodinamik | ✓ | ✓ | — |
| S06 CRESTOR Child-Pugh B | Kontrendikasyon | ✓ | ~ | *Kısmi* — "dikkatle kullanılır" (KÜB Child-Pugh ≤7 izin verir) |
| S07 CİPRO + PLASORİN | CYP1A2 | ✓ | ✓ | — |
| S08 XANAX 83 yaş + demans | Geriyatrik | ~ | ~ | *Kısmi* — hâlâ müsamahakâr |
| S09 FLAGYL emzirme | Emzirme | ✓ | ✓ | — |
| S10 NEURONTİN 10 yaş | Pediatrik | ✗ | ✓ | **Düzeldi** — pediyatrik doz şeması retrieval'da geldi |
| S11 PLAVIX + LANSOR | CYP2C19 | ~ | ~ | *Kısmi* — mekanizma var ama stent trombozu riski zayıf |
| S12 DİAMİCRON GFR 40 | Doz ayarı | ✓ | ✓ | — |
| S13 Verapamil | Hallucination | ✓ | ✓ | — |
| S14 Mirtazapin | Hallucination | ✓ | ✓ | — |
| S15 Lisinopril | Hallucination | ✓ | ✓ | — |

**Özet:** DB soruları 12/12 tamamlandı, Hallucination 3/3 ✓. v1'deki 3 ✗ (S02, S03, S10) → v2'de tümü ✓. Kısmi kalan: S06, S08, S11.

### Phase 7 — RAG Engine Kapanış Düzeltmeleri (2026-04-12)

`src/agents/rag_engine.py` üç bağımsız sorun giderildi:

#### Sorun 1 — Doz Tablosu Sub-chunk Kesimi

| Değişiklik | Detay |
|-----------|-------|
| `_format_chunks_for_prompt` — sabit 1200 char kesme | Kaldırıldı |
| `_extract_chunk_window()` fonksiyonu eklendi | `alt_madde` varsa keyword ile ilgili bölümü bul, ±2000 char pencere al |
| Anahtar kelime haritası `_ALT_MADDE_KEYWORDS` | `bobrek_karaciger` → klirens/böbrek/renal; `pediyatrik` → çocuk/kg; `geriyatrik` → yaşlı |
| Alt_madde olmayan chunk'lar | 1800 char ile sınırlı (değişmedi) |
| `k_priority` doz sorularında | 10 → **15** (`augmented.soru_turleri`'nde `"doz"` varsa) |

**Kök neden:** KEPPRA `bobrek_karaciger` sub-chunk 9198 char, GFR dozu 5406. karakterde — 1200 char kesimde tamamen kayboluyordu.

#### Sorun 2 — CYP → LLM Entegrasyon

| Değişiklik | Detay |
|-----------|-------|
| `cyp_metin` ayrı bölüme çıkarıldı | `OTOMATİK KÜMÜLATİF RİSK ANALİZİ` + `OTOMATİK CYP450 ENZİM ANALİZİ` ayrı başlıklar |
| CYP bölüm açıklaması | "KÜB belgelerinde açıkça yazılmasa da bu mekanistik bilgiyi yanıta dahil et" |
| YANIT TALİMATLARI güncellendi | CYP varsa `[BİLGİ YOK]` yazma kuralı eklendi |
| ZORUNLU KAYNAK KURALI güncellendi | CYP bulgular için KÜB kaynağı muafiyeti — "CYP450 analizi" atfı yeterli |

**Kök neden:** `_build_user_prompt`'taki "KÜB metninde karşılığı bulunmayan analiz bulgularını yanıta dahil etme" kuralı CYP bulgularını da kapsıyordu; LLM KÜB'de sessiz kalınca [BİLGİ YOK] yazıyordu.

**Doğrulama sonuçları:**
- S02 KEPPRA GFR 28: "kreatinin klerensi <30 mL/dak'da günde iki kez 250-500 mg" ✓
- S03 PLASORİN+FLAGYL: "CYP3A4, CYP1A2, CYP2C9 substrat rekabeti → INR değişimi" ✓

---

## 17. Dalga 5 — Yapılan Değişiklikler (2026-04-14)

### Corpus Genişlemesi

427 ilaç, 7.585 chunk — TİTCK'ın erişilebilir tüm KÜB PDF'leri işlendi. 44 resim bazlı PDF karantinaya alındı.

### ChromaDB İlaç Adı Çözümleme Düzeltmesi

**Sorun:** Kısa ilaç adıyla arama yapıldığında (ör. "METFORMIN") ChromaDB hiç chunk bulamıyordu.

**Çözüm:** `_resolve_drug_names()` fonksiyonu (`src/retrieval/chroma_store.py`) üç aşamalı hale getirildi:
1. Exact normalized match (PUA + Türkçe karakter + whitespace normalizasyonu)
2. Prefix match: `key.startswith(norm)` — tüm eşleşen varyantları döndürür
3. Fallback: orijinal adı kullan

**Etki:** "METFORMIN" → METAFORMAL 1000 mg + 850 mg her ikisini de getirir.

### Neo4j INTERACTS_WITH Severity Patch

**Sorun:** 20.484 INTERACTS_WITH ilişkisinin tamamı `severity="unknown"` olarak oluşturulmuştu.

**Çözüm:** `scripts/patch_severity.py` — her ilacın 4.5 bölümü metnini okuyarak eşleşme noktası ±500 char penceresinde `_SEVERITY_RULES` anahtar kelimelerine bakıyor.

**Sonuç:** 5.034 ilişki güncellendi:
- contraindicated: 2.118
- moderate: 1.888
- severe: 790
- mild: 251

### DB Sağlık Kontrolü Scripti

`scripts/db_health_check.py` — kalıcı kontrol aracı:
- ChromaDB: chunk sayısı, benzersiz ilaç, 4.3/4.5 varlığı
- Neo4j: Drug node sayısı, INTERACTS_WITH, severity dağılımı, yalnız node'lar, boş etken_madde
- Çapraz tutarlılık: ChromaDB ↔ Neo4j normalize karşılaştırma (`_norm()`)
- `--fix` flag'i ile `patch_severity.py` tetiklenir

**Mevcut durum: 12 PASS, 1 WARN, 0 FAIL**
(WARN: 8 ilaçta INTERACTS_WITH ilişkisi yok — bu ilaçların 4.5 bölümünde etkileşim belirtilmemiş)

### Vision OCR Pipeline (Karantina İçin)

Resim bazlı PDF'leri işlemek için Claude Haiku Vision tabanlı OCR sistemi geliştirildi.

| Dosya | Açıklama |
|-------|----------|
| `src/ingestion/vision_ocr.py` | Her sayfa 150 DPI PNG olarak render → Claude Haiku Vision → `_strip_markdown_bold()` |
| `src/ingestion/pdf_parser.py` v2.1 | `KUBParser(use_vision_ocr=True)` parametresi |
| `scripts/process_quarantine.py` | Karantina PDF'leri toplu işleyici (`--dry-run`, `--limit N`) |

**Maliyet notu:** ~$0.70/PDF — 44 karantina PDF için ~$30, tam TİTCK genişletmesinde ~$840. Şimdilik kullanılmıyor; karantina PDFleri sorgulardan dışlanmış değil (DB'de yok sadece).

### Toplu İngest İyileştirmeleri (`scripts/bulk_ingest.py`)

- Her başarılı ingest sonrası `db_health_check.py` otomatik çalışır
- `ImageBasedPDFError` → karantina raporu `_OCR_GEREKLI.md` olarak yazılır

---

## 18. Dalga 6 — Yapılan Değişiklikler (2026-04-15)

### ChromaDB Recall ve Normalizasyon İyileştirmesi

**Sorun:** "LUSTRAL" gibi sorgular, veritabanındaki "LUSTRAL® 50 mg..." isimleriyle trademark sembolü veya dozaj farklılıkları nedeniyle her zaman eşleşmiyordu (recall kaybı). Özellikle Lustral emzirme (4.6) verisi retrieval sırasında gözden kaçabiliyordu.

**Çözüm:** 
- `_resolve_drug_names()` fonksiyonu esnetildi: Prefix match'e ek olarak **"contains"** match eklendi.
- `search()` fonksiyonu fallback mekanizması: İlaç filtresiyle 0 sonuç dönerse, filtre gevşetilerek tüm koleksiyonda prefix/contains match ile arama yapılır.
- **Sonuç:** Lustral sorgularında recall 0 chunk'tan 8 chunk'a yükseldi (S18 testi).

### CYP450 Mapping Genişletmesi (Ticari İsimler)

**Sorun:** Flukonazol (substrat) etkileşimleri, hastanın "CANDİDİN" veya "CANDİMAX" gibi ticari isimler kullandığı senaryolarda sistem tarafından tanınmıyordu.

**Çözüm:** 
- `src/analysis/cyp450_mapper.py` içindeki enzim tablosuna **CANDİDİN** ve **CANDİMAX** isimleri eklendi.
- Bu ilaçlar artık otomatik olarak **CYP2C19** inhibitörü olarak işlenmektedir.
- **Sonuç:** S17 testinde Candidin + Plavix etkileşimi (antiplatelet etki azalması) başarıyla tespit edildi.

### Yan Etki (4.8) ve Özel Uyarı (4.4) Prompt Muafiyeti

**Sorun:** Jardiance (empagliflozin) gibi ilaçlarda yan etki sorgulandığında, sistem 4.8 maddesindeki bilgileri [BİLGİ YOK] kuralı nedeniyle bazen filtreleyebiliyordu.

**Çözüm:**
- `SYSTEM_PROMPT` ve `_build_user_prompt` güncellendi.
- Madde 4.8 (Yan etkiler) ve 4.4 (Özel uyarılar) bölümleri için muafiyet (exemption) talimatları eklendi: "Bağlamda bilgi varsa, bu bölümlerdeki uyarıları mutlaka değerlendir ve BİLGİ YOK yazma."
- **Sonuç:** S16 testinde Jardiance yan etkileri (vajinal moniliyazis, poliüri vb.) eksiksiz raporlandı.

### RAGAS Stabilizasyon Ayarları

**Sorun:** RAGAS değerlendirmeleri sırasında yerel LLM (Mistral) üzerindeki yoğunluk nedeniyle %60'a varan NaN/timeout hataları alınıyordu.

**Çözüm:**
- `ragas_eval.py` RunConfig ayarları güncellendi:
  - `max_workers`: 2 → **1**
  - `timeout`: 300s → **600s**
  - `ChatOpenAI` (Mistral) timeout: 240s → **600s**
- **Soru Seti Genişletmesi:** `ragas_v3_questions.json` dosyasına S16, S17 ve S18 senaryoları (v3_q31-33) eklenerek ground truth set genişletildi.

### Klinik Validasyon v3 Sonuçları

| Soru | Tür | Durum | Gözlem |
| :--- | :--- | :--- | :--- |
| **S16** Jardiance 4.8 | Yan Etki | **✓ GEÇTİ** | Guardrail esnetilmesiyle yan etkiler net raporlandı. |
| **S17** Candidin + Plavix | CYP450 | **✓ GEÇTİ** | Mapping sayesinde 3 CYP etkileşimi tespit edildi. |
| **S18** Lustral Emzirme | Recall | **✓ GEÇTİ** | Retrieval başarısı 0 -> 8 chunk. |

---

## 19. Dalga 7 — v1.0 Stable Hazırlığı (2026-04-16)

### Kalıcı Veritabanı Normalizasyonu (v1.0)

**Sorun:** İlaç adlarındaki trademark (®/™) sembolleri ve Unicode karakter uyumsuzlukları retrieval recall kaybına yol açıyordu.

**Çözüm:** 
- Merkezi [normalization.py](file:///c:/Users/kesic/Desktop/PharmAssistVersion2/src/data/normalization.py) modülü oluşturuldu.
- Neo4j ve ChromaDB veritabanları kalıcı olarak normalize edildi.
- **Sonuç:** Trademark sembolü içeren 0 kayıt kaldı; recall hataları çözüldü.

### Otomatik CYP450 Extraction (v1.0 Automation)

**Sorun:** Manuel CYP450 listesinin bakımı zordur ve yeni ilaçları kapsayamazdı.

**Çözüm:** 
- [cyp450_extractor.py](file:///c:/Users/kesic/Desktop/PharmAssistVersion2/src/analysis/cyp450_extractor.py) ile LLM tabanlı fallback extraction eklendi.
- **Sonuç:** Manuel veri girişi zorunluluğu ortadan kalktı.

---

---

## 20. Dalga 8 — Yapılan Değişiklikler (2026-04-17)

### LM Studio System Role Uyumsuzluğu Giderildi

**Sorun:** LM Studio'da aktif model değiştirildiğinde (Gemma/Llama aileleri) `{"role": "system"}` mesajları reddediliyordu. Bu hata `rag_engine.py`'deki `_call_local_llm` fonksiyonunda Q1-24'ü geçerken Q25+'ı tamamen bloke ediyordu.

**Çözüm:** `_call_local_llm` — sistem promptunu kullanıcı mesajıyla birleştirdi:
```python
combined_prompt = f"{LOCAL_SYSTEM_PROMPT}\n\n{user_prompt}"
messages = [{"role": "user", "content": combined_prompt}]
```

**Etki:** RAGAS Run 5 boyunca 33 sorunun tamamı işlendi (önceki run'da Q25+ fail oluyordu).

### ISOPTIN ve PERILIFE İlaç Adı Düzeltmesi

**Sorun:** KÜB Madde 1 formatında "İSOPTİN® 40 mg film kaplı tablet" ifadesinde `®` + satır sonu nedeniyle parser yalnızca "İSOPTİN" çıkarıyordu. PERILIFE için de aynı sorun mevcuttu.

**Çözüm:**
- `data/parsed_json/ISOPTIN_40_MG_FILM_KAPLI_TABLET.json` — 17 chunk'ta `ilac_adi` güncellendi
- `data/parsed_json/PERILIFE_1_MG_FILM_TABLET.json` — 17 chunk, yeni isim
- `data/parsed_json/PERILIFE_2_MG_FILM_TABLET.json` — force-parse ile yeni dosya (duplikat engeli bypass)
- `data/quarantine/PERILIFE_1_MG_ML_ORAL_COZELTI_OCR_BASARISIZ.md` — görüntü bazlı PDF karantina

**Neo4j güncellemesi:** ISOPTIN 40 MG, ISOPTIN 80 MG, PERILIFE 1 MG, PERILIFE 2 MG için `HAS_SECTION` + `INTERACTS_WITH` bağlantıları kuruldu.

### CYP450 Tablosu Genişletmesi (86 → 90 kayıt)

Eklenen kayıtlar:
```python
"Verapamil": {"substrat": ["CYP3A4","CYP1A2"], "inhibitor": ["CYP3A4","CYP1A2"], "induktor": []},
"ISOPTIN":   {"substrat": ["CYP3A4","CYP1A2"], "inhibitor": ["CYP3A4","CYP1A2"], "induktor": []},
"Risperidon":{"substrat": ["CYP2D6","CYP3A4"], "inhibitor": [], "induktor": []},
"PERILIFE":  {"substrat": ["CYP2D6","CYP3A4"], "inhibitor": [], "induktor": []},
```

### RAGAS Run 5 Sonuçları

| Metrik | Run 4 (v3 final) | Run 5 (v5) | Değişim |
|--------|-----------------|-----------|---------|
| Faithfulness | 0.7038 | **0.6755** | -0.028 ↓ |
| Context Recall | 0.7601 | **0.8646** | +0.104 ↑ |
| NaN Faith | 1/33 (3%) | 1/33 (3%) | — |
| NaN CR | 0/33 (0%) | 1/33 (3%) | +1 |

- **NaN Faith:** Q11 "NORODOL ile CORDARONE birlikte kullanılabilir mi?" — Mistral parse hatası
- **NaN CR:** Q6 "İSOPTİN kullanan hastaya CONCOR eklenirse ne olur?" — Mistral parse hatası
- **CR artışının nedeni:** LM Studio fix sayesinde tüm 33 soru düzgün işlendi
- **Faithfulness düşüşünün nedeni:** Araştırılıyor (6 ground truth revizyonu etkisi?)

### RAGAS Archive Yeniden Yapılandırması

`data/eval/` klasörü düzenlendi:

```
data/eval/
├── ragas_v3_questions.json          ← aktif soru seti (32 soru — GT fix 2026-04-26)
├── RAGAS_RUN_HISTORY.md             ← kronolojik run tablosu
├── QUICK_REFERENCE.md
└── archive/
    ├── v1/                          ← Run 1 canonical (8 soru, Haiku eval)
    ├── v2/                          ← Run 2 canonical (25 soru, Haiku eval)
    ├── v3/                          ← Run 3 + Run 4 canonical (Mistral eval)
    │   ├── ragas_v3_first_run.json  ← Run 3: 30 soru, NaN=60%
    │   └── ragas_v3_final.json      ← Run 4: 33 soru, NaN=3% ✅
    ├── v5/                          ← Run 5 canonical (LM Studio fix)
    │   ├── ragas_v5_results.json
    │   └── ragas_v5_qa_export.md
    └── exp/                         ← experimental/debug runs (karşılaştırılmaz)
        ├── v4/  v6/  v7/  v8/  v9/  v10/
```

Bir sonraki canonical run `v6` adını alacak (`exp/v6` ile çakışma yok).

---

## 21. Dalga 9 — INTERACTS_WITH LLM Rebuild (2026-04-19)

### Motivasyon

Dalga 8 sonrası `patch_severity.py` çalıştırıldı: 17.044 unknown → 10.484 unknown kaldı (6.560 çözüldü). Kalan %61'in kök nedeni: regex tabanlı extraction `_SEVERITY_RULES` anahtar kelimelerini bulamıyor çünkü ilaç 4.5'te sadece "neutral listing" (şiddet belirtilmeksizin isim geçiyor). Ayrıca 4.3 kontrendikasyonları ve 4.4 uyarı bölümlerindeki drug-drug etkileşimleri hiç yakalanmıyordu.

### Yapılan Değişiklikler

**Karar:** Tüm 22.482 INTERACTS_WITH ilişkisi silindi. Yerine LLM tabanlı extraction ile sıfırdan yeniden inşa.

**Script:** `scripts/rebuild_interactions.py`

| Parametre | Değer |
|-----------|-------|
| Model | `qwen/qwen2.5-coder-14b-instruct` (LM Studio yerel) |
| Bölümler | 4.3 (max 500 char) + 4.5 (max 900 char) |
| Prompt boyutu | ~484 token (eski 2000 token'dan 76% küçük) |
| Timeout | 180s/ilaç |
| Ortalama hız | ~57s/ilaç |
| Tahmini süre | 439 ilaç × 57s ≈ ~7 saat |
| Başlangıç | 2026-04-19 00:19 |
| Bitiş | 2026-04-19 06:02 (~6 saat) |

**Çıkış formatı:**
```json
[{"drug_b": "selejilin", "severity": "contraindicated", "section": "4.3"},
 {"drug_b": "varfarin",  "severity": "moderate",        "section": "4.5"}]
```

**Neo4j yazma stratejisi:**
- Drug B Neo4j'de bulunursa → `INTERACTS_WITH` ilişkisi (`kaynak='llm_rebuild'`)
- Bulunmazsa → `DrugMention` node + `MENTIONS_INTERACTION` ilişkisi (drug class / external drug)
- Severity normalizasyonu: Türkçe ("kontrendike") → İngilizce ("contraindicated") `_normalize_severity()`

**LM Studio optimizasyon notları:**
- 6GB VRAM, Qwen-14B Q4_K_M (~8.5GB) → GPU Offload 28-30 layer (güvenli sınır)
- 48 layer ile VRAM taşması → swap → 5dk+ timeout sorunu yaşandı
- Context Length: 8192, Flash Attention: ON, KV Cache GPU Offload: ON

### Rebuild Tamamlandığında Yapılacaklar

```bash
# 1. Severity dağılımını kontrol et
.venv/Scripts/python -c "
from src.graph.neo4j_client import run_query
rows = run_query('MATCH ()-[r:INTERACTS_WITH]->() RETURN r.severity AS s, count(*) AS c ORDER BY c DESC')
for r in rows: print(r['s'], r['c'])
"

# 2. DB health check
.venv/Scripts/python scripts/db_health_check.py

# 3. DrugMention analizi (drug class mapping fırsatları)
.venv/Scripts/python -c "
from src.graph.neo4j_client import run_query
rows = run_query('MATCH (m:DrugMention)<-[r:MENTIONS_INTERACTION]-() RETURN m.name, count(r) AS c ORDER BY c DESC LIMIT 20')
for r in rows: print(r['m.name'], r['c'])
"
```

### Dalga 10 — INN Propagation + Retry (2026-04-19)

**Sorun:** LLM rebuild sonrası 72 ilaçta 0 ilişki. Kök neden: aynı etken maddenin farklı markaları ayrı işlendi, bazı formülasyonların KÜB metni daha zengin.

**Adım 1 — INN Propagation** (`scripts/propagate_inn_interactions.py`):
- 13 INN grubu, 42 ilaç, 347 yeni ilişki → Toplam: 598 → **945**
- 72 → 30 sıfır-ilişkili ilaç
- `kaynak='inn_propagated'` ile işaretlendi

**Adım 2 — Targeted Retry** (`scripts/retry_zero_interactions.py`):
- 30 sıfır-ilişkili ilaç için 4.3:800/4.5:2000 char + max_tokens:1024
- Sonuç: 0 yeni eşleşme — tüm etkileşimler corpus dışı (heparin, disülfiram, ketokonazol vb.)
- 5 ilaç timeout aldı (büyük JSON çıktısı): XANAX (2), LANTUS (2), HUMALOG KWIKPEN 200

**Final durum:**
| Severity | Sayı |
|----------|------|
| contraindicated | 370 |
| unknown | 258 |
| moderate | 214 |
| severe | 100 |
| mild | 3 |
| **TOPLAM** | **945** |

**30 sıfır-ilişkili ilaç kategorileri:**
- Corpus-dışı etkileşim (PLAVIX, FLAGYL, PRADAXA, FOSAMAX): heparin/warfarin/ketokonazol corpus'ta yok
- İnsülin grubu (HUMALOG×6, LANTUS, NOVORAPID×3, FIASP): insülin sınıfı etkileşimleri DrugMention'da
- Timeout (XANAX×2): çok büyük JSON çıktısı, 1024 token yetmiyor
- RAG sistemi için sorun değil: ChromaDB'de KÜB metinleri mevcut

---

## 22. Sonraki Adımlar

### Kısa Vadeli
- **NaN analizi:** Run 6'da 7 NaN (3 faithfulness, 4 context_recall) — hangi sorular, neden?
- **Context Recall düşüşü:** 0.8646 → 0.8065 — GT değişimi mi, NaN mı?
- **Büyük context overflow fix:** v3_q26 CO-DIOVAN (101 kontraendikasyon) → max graph bağlam sınırı
- **Parser + kub_to_graph iyileştirmeleri:** Sonraki dalga

### Orta Vadeli
- **v1.0 Stable kararı:** Faithfulness >0.70 ✅ aşıldı; CR >0.80 hedefi kalan
- **OCR genişleme:** Karantinadaki 47 PDF işlenmesi (~$30 maliyet)
- **RAG prompt optimizasyonu:** Context Recall 0.8065 → hedef 0.85+
