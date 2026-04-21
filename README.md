# PharmAssist — Klinik Karar Destek Sistemi

Türkiye TİTCK tarafından yayımlanan **KÜB (Kısa Ürün Bilgisi)** belgelerine dayalı RAG tabanlı klinik karar destek sistemi prototipi.

## Ne Yapar?

Klinisyen veya eczacı hastasına ilaç yazarken şu soruları sorabilir:

- *"Bu hastaya böbrek yetmezliği varken Pradaxa yazılabilir mi?"*
- *"Warfarin alan hastaya Plavix eklenirse kanama riski nedir?"*
- *"Sporanox kullanan hastada Cordarone kan düzeyi nasıl etkilenir?"*

Sistem soruyu **KÜB belgelerindeki gerçek metinle** karşılaştırır, hastanın klinik profilini (GFR, karaciğer skoru, mevcut ilaçlar, lab değerleri) dikkate alır ve kaynaklı bir yanıt üretir.

## Mimari

```
Soru + Hasta Profili
        │
        ▼
  QueryAugmentor       ← soru türü tespiti (kontrendikasyon / etkileşim / doz / yan etki)
        │
   ┌────┴────┐
   ▼         ▼
ChromaDB   Neo4j        ← KÜB chunk'ları + etkileşim/kontrendikasyon grafu
   └────┬────┘
        │
  Deterministik Analiz  ← CYP450 + kümülatif yan etki (LLM'den bağımsız)
        │
       LLM              ← kaynaklı yanıt (yalnızca KÜB içeriğine dayalı)
```

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| PDF Parsing | PyMuPDF + pdfplumber |
| Embeddings | `multilingual-e5-base` |
| Reranking | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` |
| Vector DB | ChromaDB |
| Graph DB | Neo4j |
| LLM | Claude Haiku 4.5 / Local LLM (qwen2.5:32b) |
| Backend | FastAPI |
| Frontend | Streamlit |

## Corpus (v1.2.0)

- **64 ilaç**, 1.120+ chunk (ChromaDB)
- **945 INTERACTS_WITH** ilişkisi (Neo4j, INN propagation dahil)
- **CYP450:** 84 kayıt statik tablo + LLM fallback

## RAGAS Değerlendirme (Run 10 — 2026-04-21)

| Metrik | Skor |
|--------|------|
| Faithfulness | 0.6792 |
| Context Recall | 0.6677 |

Evaluator: qwen2.5:32b (yerel) — 33 klinik soru

## Kurulum

```bash
# Bağımlılıklar
pip install -r requirements.txt

# Servisleri başlat (Neo4j + ChromaDB gerekli)
python start_system.py

# Streamlit UI
streamlit run app.py

# FastAPI
uvicorn src.api.main:app --port 8080
```

## Detaylı Dokümantasyon

`PROJE_DOKUMANTASYONU.md` — mimari, pipeline detayı, API, RAGAS geçmişi
