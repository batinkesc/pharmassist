# PharmAssist — KÜB Tabanlı Klinik Karar Destek Sistemi

> ⚠️ **Tıbbi Sorumluluk Reddi**
> PharmAssist bir **araştırma prototipidir**. **Tıbbi cihaz değildir** ve gerçek klinik karar, tanı veya tedavi amacıyla **kullanılamaz**. Çıktılar eksik veya hatalı olabilir. Her zaman resmi ürün bilgisine ve yetkin bir sağlık profesyoneline başvurun.

Türkiye TİTCK tarafından yayımlanan **KÜB (Kısa Ürün Bilgisi)** belgelerine dayalı, RAG tabanlı klinik karar destek sistemi prototipi. v1.9.0

## Ne Yapar?

Klinisyen veya eczacı serbest Türkçe soru sorar:

> *"82 yaşında kadın hasta, mevcut ilaçları metoprolol, ramipril, furosemid, digoksin. Ağrı için tramadol ekleyebilir miyim?"*

> *"GFR 28, warfarin kullanan hastaya klaritromisin yazabilir miyim?"*

Sistem hasta profilini otomatik çıkarır (yaş, böbrek fonksiyonu, ilaç listesi, tanılar, alerjiler, lab değerleri), hibrit vektör + graf deposundan ilgili KÜB metnini getirir ve **kaynaklı** bir yanıt üretir; yanıt üretimden sonra kaynak metinle deterministik olarak doğrulanır.

## Mimari

```
        Serbest Türkçe klinik soru
                    │
                    ▼
           ProfileExtractor        ← yaş, GFR, ilaç listesi, tanı, alerji, lab
                    │
                    ▼
            QueryAugmentor         ← soru türü: kontrendikasyon / etkileşim / doz / yan etki
                    │
              ┌─────┴─────┐
              ▼           ▼
          ChromaDB      Neo4j      ← 11.843 KÜB chunk + ilaç etkileşim grafu
              └─────┬─────┘
                    ▼
          AnswerCalibration        ← hasta profili ağırlıklı chunk seçimi
                    │
                    ▼
                   LLM             ← Claude Haiku (varsayılan) / OpenAI-uyumlu endpoint
                    │
                    ▼
           VALIDATE Pipeline       ← 7 deterministik post-hoc kontrol
```

### VALIDATE Pipeline — Deterministik Yanıt Doğrulama

LLM'e güvenmek yerine her yanıt, üretimden **sonra** kaynak metinle karşılaştırılır:

| # | Kontrol | Başarısızlıkta |
|---|---------|----------------|
| 1 | Kaynakta geçmeyen mutlak güvenlik iddiaları ("güvenlidir") | Sistem uyarısıyla değiştirilir |
| 2 | Kontrendikasyon iddiası ↔ Madde 4.3 içeriği | `[AŞIRI YORUM]` etiketi |
| 3 | Kaynak atıfı olmayan tıbbi iddialar | `[DOĞRULANAMADI]` etiketi |
| 4 | Numerik iddialar ↔ atıf verilen chunk'taki sayılar | Etiketlenir |
| 5 | CYP450 inhibitör/indükleyici yön doğruluğu | Etiketlenir |
| 6 | Verdict/şiddet seviyesi kaynakla uyumu | Etiketlenir |
| 7 | 3-katman yanıt formatı yapısal kontrolü | Loglanır |

Yanıtlar **[KÜB Aktarımı]** / **[Sistem Tespitleri]** / **[Değerlendirme]** olmak üzere 3 katmana ayrılır — okuyucu hangi cümlenin kaynaktan, hangisinin sistemden geldiğini her zaman bilir.

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| PDF Parsing | PyMuPDF + pdfplumber |
| Lab Raporu | PyMuPDF (hastane PDF formatı, 44+ parametre) |
| Embeddings | `intfloat/multilingual-e5-base` |
| Reranking | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` |
| Vector DB | ChromaDB (BM25 ile hibrit) |
| Graph DB | Neo4j |
| LLM | Claude Haiku 4.5 (varsayılan) / OpenAI-uyumlu endpoint |
| API | FastAPI |
| Frontend | Streamlit |
| Değerlendirme | RAGAS (3 metrik) |
| Test | pytest — 96 test |

## Corpus

| Metrik | Değer |
|--------|-------|
| İlaç sayısı | 501 |
| ChromaDB chunk | 11.843 |
| Neo4j `INTERACTS_WITH` | 4.021 |
| Bilinmeyen etkileşim şiddeti | %0 (INN propagation) |
| CYP450 kayıt | Statik tablo + LLM fallback, Neo4j'de |

## RAGAS Değerlendirme

**Aktif Baseline — Run 20** (33 klinik soru, evaluator: Together AI Qwen3-235B):

| Metrik | Skor |
|--------|------|
| Faithfulness | 0.7192 |
| Context Utilization | 0.7823 |
| Context Recall | 0.9010 |
| **Ortalama** | **0.8008** |

20 değerlendirme koşusu, regresyonlar ve kök neden analizleriyle birlikte [`data/eval/RAGAS_RUN_HISTORY.md`](data/eval/RAGAS_RUN_HISTORY.md) dosyasında kronolojik olarak takip edilir.

**Bilinen sınır:** Faithfulness ~0.72'de plato yapıyor. Kök neden analizi, retrieval kalitesinden çok evaluator'ın Türkçe klinik metindeki katılığına ve ground-truth granülaritesine işaret ediyor.

## Kurulum

### Gereksinimler

- Python 3.11+
- Neo4j 5.x (Desktop veya Docker)
- Anthropic API anahtarı (veya OpenAI-uyumlu herhangi bir LLM endpoint'i)

### Adımlar

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env          # ANTHROPIC_API_KEY, NEO4J_PASSWORD vb. doldurun
```

### Veri Hazırlığı

KÜB PDF'leri **bu repoyla birlikte dağıtılmaz**. TİTCK sitesinden ([titck.gov.tr](https://www.titck.gov.tr)) herkese açık olarak indirilebilir — ürünü aratıp KÜB PDF'ini indirin.

```bash
# 1. KÜB PDF'lerini data/raw_pdfs/ klasörüne koyun

# 2. Parse → QA kontrolü → ChromaDB + JSON
python scripts/bulk_ingest.py --pdf-dir data/raw_pdfs

# 3. Neo4j etkileşim grafını kur (ilaç düğümleri, INTERACTS_WITH, CYP450)
python scripts/load_graph.py
```

> Not: Görüntü tabanlı (taranmış) PDF'ler ücretli API çağıran vision OCR adımına düşer — ingest scripti bunu yapmadan önce uyarır.

### Çalıştırma

```bash
# Streamlit UI
streamlit run app.py
```

```bash
# veya REST API — Swagger: http://localhost:8080/docs
uvicorn src.api.main:app --port 8080
```

Windows'ta `start.bat` kullanılabilir (venv, port, Neo4j kontrolü yapıp API + UI başlatır).

### Docker

```bash
docker compose up --build
```

`api` (8080), `ui` (8501) ve `neo4j` (7474/7687) servislerini başlatır. Not: konteynerler **boş** ChromaDB volume'üyle başlar — veri hazırlığını bir kez çalıştırın.

## Değerlendirme ve Testler

```bash
python scripts/run_eval.py    # RAGAS değerlendirmesi (.env'de evaluator API anahtarı gerekir)
```

```bash
pytest tests/ -v              # 96 birim test, canlı servis gerektirmez
```

## Detaylı Dokümantasyon

- [`PROJE_DOKUMANTASYONU.md`](PROJE_DOKUMANTASYONU.md) — mimari, pipeline, API, RAGAS geçmişi
- [`docs/ARCHITECTURE_STANDARDS.md`](docs/ARCHITECTURE_STANDARDS.md) — mimari standartlar
- [`data/eval/RAGAS_RUN_HISTORY.md`](data/eval/RAGAS_RUN_HISTORY.md) — tüm run geçmişi
- [`README.md`](README.md) — English version

## Lisans

[MIT](LICENSE)
