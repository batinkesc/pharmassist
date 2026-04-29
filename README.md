# PharmAssist — KÜB Tabanlı Klinik Karar Destek Sistemi

Türkiye TİTCK tarafından yayımlanan **KÜB (Kısa Ürün Bilgisi)** belgelerine dayalı RAG tabanlı klinik karar destek sistemi prototipi. v1.6.0

## Ne Yapar?

Klinisyen veya eczacı, hastasına ilaç yazarken serbest Türkçe soru sorabilir:

> *"82 yaşında kadın hasta, mevcut ilaçları metoprolol, ramipril, furosemid, digoksin. Ağrı için tramadol ekleyebilir miyim?"*

> *"GFR 28, warfarin kullanan hastaya klaritromisin yazabilir miyim?"*

> *"Child-Pugh B karaciğer yetmezliği olan hastada atorvastatin dozu ne olmalı?"*

Sistem soruyu **KÜB belgelerindeki gerçek metinle** karşılaştırır, hastanın klinik profilini otomatik çıkarır ve kaynaklı bir yanıt üretir.

---

## Mimari

```
Serbest Türkçe Soru
        │
        ▼
 ProfileExtractor        ← yaş, GFR, ilaç listesi, tanı, alerji, lab değerleri
        │
        ▼
  QueryAugmentor         ← soru türü: kontrendikasyon / etkileşim / doz / yan etki
        │
   ┌────┴────┐
   ▼         ▼
ChromaDB   Neo4j          ← 11.843 KÜB chunk + ilaç etkileşim grafu
   └────┬────┘
        │
 AnswerCalibration        ← hasta profili ağırlıklı chunk seçimi
        │
  VALIDATE Pipeline       ← 6 deterministik kural (güvenli/kontrendike/CYP/numerik/yön/verdict)
        │
       LLM                ← Groq llama-3.3-70b / Claude Haiku — kaynaklı yanıt
```

---

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| PDF Parsing | PyMuPDF + pdfplumber |
| Lab Raporu | PyMuPDF (hastane PDF formatı, 44+ parametre) |
| Embeddings | `multilingual-e5-base` |
| Reranking | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` |
| Vector DB | ChromaDB |
| Graph DB | Neo4j |
| LLM | Claude Haiku 4.5 (varsayılan) / Groq API (opsiyonel) |
| Frontend | Streamlit |
| Test | pytest — 95 test |

---

## Corpus (v1.6.0)

| Metrik | Değer |
|--------|-------|
| İlaç sayısı | 501 |
| ChromaDB chunk | 11.843 |
| Neo4j INTERACTS_WITH | 4.021 |
| CYP450 kayıt | Statik tablo + LLM fallback |
| Bilinmeyen etkileşim oranı | %0 (INN propagation) |

---

## RAGAS Değerlendirme

**Aktif Baseline — Run 12** (2026-04-26)

| Metrik | Skor |
|--------|------|
| Faithfulness | **0.7607** |
| Context Utilization | **0.8028** |
| Context Recall | **0.7250** |
| **Ortalama** | **0.7628** |

Evaluator: Together AI Qwen3-235B — 32 klinik soru (GT kalite doğrulamalı)

Geçmiş: `data/eval/RAGAS_RUN_HISTORY.md`

---

## VALIDATE Pipeline (v2 — 6 Adım)

Her LLM yanıtı kaynak metinle karşılaştırılır:

1. **Güvenli kullanım** — kaynakta geçmiyor mu? `[DOĞRULANAMADI]`
2. **Kontrendikasyon** — klinik profille çelişiyor mu? `[AŞIRI YORUM]`
3. **Doğrulanamaz ifade** — kayıt yok mu? `[DOĞRULANAMADI-KAYNAK YOK]`
4. **Numerik doğrulama** — cited chunk'taki sayıyla uyuşuyor mu?
5. **CYP yön kontrolü** — inhibitör/indükleyici yönü doğru mu?
6. **Verdict uyum denetimi** — şiddet seviyesi destekleniyor mu?

---

## Özellikler

### Otomatik Hasta Profili Çıkarımı
Serbest metin sorgularından otomatik çıkarır:
- Yaş, cinsiyet, kilo
- GFR, böbrek/karaciğer yetmezliği, Child-Pugh skoru
- Mevcut ilaçlar (`"mevcut ilaçları: X, Y, Z"` liste formatı dahil)
- Tanılar (AMI, AF, DM, HT, epilepsi, romatoid artrit vb. — 29 bilinen tanı)
- Alerjiler
- Lab değerleri (metin içi: `ALT: 45`, `INR: 2.1`)
- Hedef ilaç (`"eklemek istiyorum"`, `"yazmak istiyorum"`, `"sordu"` vb.)

### Lab Sonuç PDF'den Veri Çıkarma
- Hastane/laboratuvar çıktısı PDF yükle → 44+ parametre otomatik çıkarılır
- Değerler profil paneline direkt eklenir
- Renk kodlaması: kritik / anormal / normal
- Profil panelinden bireysel değer silme

### Risk Uyarıları
- Böbrek/karaciğer yetmezliği doz ayarı uyarısı
- CYP450 etkileşim analizi
- Kümülatif yan etki (QT uzaması, kanama, nefrotoksisite...)
- Gebelik/laktasyon kategorisi

---

## Kurulum

```bash
# 1. Bağımlılıklar
pip install -r requirements.txt

# 2. .env dosyası
cp .env.example .env
# GROQ_API_KEY, ANTHROPIC_API_KEY, NEO4J_* değerlerini doldurun

# 3. Servisleri başlat (Neo4j + ChromaDB)
python start_system.py

# 4. Streamlit UI
streamlit run app.py
```

### Servis Gereksinimleri

| Servis | Port | Amaç |
|--------|------|-------|
| Neo4j | 7474 / 7687 | İlaç etkileşim grafu |
| ChromaDB | 8000 | KÜB vektör deposu |

---

## Proje Yapısı

```
PharmAssistVersion2/
├── app.py                          # Streamlit UI
├── src/
│   ├── agents/
│   │   ├── rag_engine.py           # RAG + VALIDATE pipeline
│   │   ├── profile_extractor.py    # Hasta profili çıkarımı (regex)
│   │   └── patient_profile.py      # PatientProfile veri sınıfı
│   ├── ingestion/
│   │   ├── lab_report_parser.py    # e-Nabız PDF parser (Web UI)
│   │   ├── lab_parser.py           # KÜB pipeline lab parser
│   │   └── kub_extractor.py        # KÜB PDF → chunk
│   ├── retrieval/
│   │   └── chroma_store.py         # ChromaDB arayüzü
│   └── core/
│       └── content_policy.py       # İçerik politikası
├── data/
│   ├── pdfs/                       # KÜB PDF'leri (561 dosya)
│   ├── eval/                       # RAGAS değerlendirme sonuçları
│   └── diagrams/                   # Mimari diyagramlar
├── tests/                          # 95 pytest testi
├── scripts/                        # Pipeline ve değerlendirme scriptleri
└── docs/                           # Sprint raporları
```

---

## Değerlendirme

```bash
# RAGAS değerlendirmesi
python scripts/run_eval.py

# Birim testler
pytest tests/ -v
```

---

## Detaylı Dokümantasyon

- `PROJE_DOKUMANTASYONU.md` — mimari, pipeline, API, RAGAS geçmişi (v1.6.0)
- `docs/SPRINT_RAPORU_2026_04_22_29.md` — son sprint özeti
- `data/eval/RAGAS_RUN_HISTORY.md` — tüm run geçmişi
- `data/diagrams/` — sequence ve class diyagramları

---

> ⚠️ Bu sistem yalnızca araştırma ve klinik karar desteği amaçlıdır. Nihai karar her zaman sorumlu hekime aittir.
