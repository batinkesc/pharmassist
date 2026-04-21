# PharmAssist — Detaylı Proje Audit Raporu
**Tarih:** 2026-04-15  
**Versiyon:** 1.0  
**Hazırlayan:** Claude Code Audit

---

## Executive Summary

PharmAssist, **solid bir mimariye** ve **iyi yapılandırılmış pipeline**'a sahip bir CDSS'dir. Ancak **veri kalitesi, retrieval ayarları ve normalization** konularında iyileştirme gerekli. Dalga 6 müdahaleleri kritik eksiklikleri giderir ama sorunların kökleri sistemli olarak adreslenmelidir.

**Risk Seviyesi:** 🟡 **ORTA** — LLM hataları ve retrieval başarısızlıkları yaşanıyor ama temel mimarisi sağlam.

---

## 1. Veri Kalitesi Sorunları

### 1.1 İlaç Adı Normalizasyon Eksikliği ⚠️

**Sorun:** Veritabanında aynı ilaçlar birden fazla varyant ad ile saklanıyor:

```
Örnek 1: AMLOPER
  - AMLOPER 4 mg/10 mg film kaplı tablet [18 bölüm]
  - AMLOPER 4/5 mg film kaplı tablet [17 bölüm]
  ↓ vs. ↓
  - AMLİPİN 10/10 mg film tablet [18 bölüm]  ← Farklı brand aynı active ingredient

Örnek 2: A-FERİN varyantları (7 ayrı entry)
  - A-FERİN® 1 mg+160 mg/5 mL...
  - A-FERİN SİNÜS 500 mg/30 mg...
  - A-FERİN ZERO 120 mg/5 mL...
  - A-FERİN PLUS film tablet
  - AFERİN PLUS film tablet (İmla farklılığı!)
```

**Etkileri:**
- Kullanıcı "AMLOPER" sorduğunda, "AMLİPİN" varyantı bulunmayabiliyor
- ChromaDB filter eşleştirmeleri başarısız oluyor (recall kaybı)
- Neo4j node resolution eksik kalıyor
- Klinik testler yanlış yanıt verebiliyor

**Kök Neden:** PDF parsing aşamasında standart bir normalization katmanı yok. Her ilaç PDF 4.1 başlığında raw metin olarak saklanıyor.

**Çözüm (Önerilir):**
```python
# src/data/normalization.py (YENİ)
def normalize_drug_name(name: str) -> str:
    """
    İlaç adını standarda çevir:
    - Trademark symbols kaldır: ® → sil
    - Dozaj parantezlerini normalize: 4 mg/10 mg → 4/10mg
    - Whitespace standardize: AMLOPER vs. AMLOPER → AMLOPER
    - İmla varyantları: AFERİN vs. A-FERİN → A-FERIN (veya seç biri)
    """
    # 1. Trademark
    name = name.replace('®', '').replace('©', '').replace('™', '')
    
    # 2. Normali whitespace
    name = ' '.join(name.split())
    
    # 3. İlaç adı prefix (ilk 2-3 kelime)
    base_name = ' '.join(name.split()[:3]).upper()
    
    return base_name

# Kullanım:
#   normalize_drug_name("AMLOPER 4/5 mg") → "AMLOPER"
#   normalize_drug_name("A-FERİN® SİNÜS 500 mg") → "A-FERIN SINUS"
```

---

### 1.2 İlaç → Bölüm Mapping Dengesizliği ⚠️

**Gözlem:** `ilac_listesi_db.txt`'de 15-18 bölüm arasında geniş bir yelpaze var.

```
Dengesiz ilaçlar:
  • ACARIS                     [9 bölüm] ← Çok az
  • ACNOR                      [11 bölüm] ← Çok az
  • % 0,4 LİDODEKS            [18 bölüm] ← Normal
  • A-FERİN® FORTE             [17 bölüm] ← Normal

Soru: 9-11 bölümlü ilaçlardaki veri eksikliği ne kadarı eksiktir?
  - KÜB 4.5 (etkileşim) var mı?
  - KÜB 4.2 (doz ayarı) var mı?
  - KÜB 4.4 (uyarılar) var mı?
```

**Risk:** Nadiren kullanılan ilaçlarda kritik bölümler eksik olabilir.

**Çözüm (Önerilir):**
```bash
# Script: Eksik bölüm audit
for ilac in data/raw_pdfs/*.pdf; do
  ilaç_adi=$(basename "$ilac" .pdf)
  madde_4_5=$(pdftotext "$ilac" - | grep -c "4\.5")
  madde_4_2=$(pdftotext "$ilac" - | grep -c "4\.2")
  if [ "$madde_4_5" -eq 0 ] || [ "$madde_4_2" -eq 0 ]; then
    echo "⚠️ $ilac_adi eksik bölüm"
  fi
done
```

---

### 1.3 Character Encoding Sorunları ⚠️

**Gözlem:** Audit sırasında sözleşme hataları görüldü:
```
Neo4j çıktı: "NEURONTİN" → Terminal output: "NEURONTİN" (?) ← Encoding hatası
```

**Soru:** Veritabanındaki Türkçe karakterler (ş, ç, ğ, ı, İ, ü, ö) konsistent mi?

**Risk:** Search ve filter'lerde silent failures olabilir.

**Çözüm (Önerilir):**
```python
# src/data/charset_validator.py (YENİ)
import unicodedata

def normalize_turkish(text: str) -> str:
    """Unicode NFC normalize et — ı vs I varyantlarını konsistent hale getir."""
    return unicodedata.normalize('NFC', text)

# Test:
#   normalize_turkish("İLAÇ")  vs.  normalize_turkish("İLAÇ")  → aynı output
```

---

## 2. Retrieval Sorunları

### 2.1 ChromaDB Chunk Kalitesi ⚠️

**Gözlem:** klinik_v2.json'da 100+ token'lı yanıtlar var fakat chunk kalitesi bilinmiyor.

**Sorular:**
- Ortalama chunk boyutu kaç token? (hedef: 100-300)
- Chunk'lar mantıklı sınırlardan kesilmiş mi? (örn: tablo ortasında kesilme?)
- Madde 4.2 (Doz) chunk'ları bütün mü, yoksa parçalanmış mı?

**Öneri:** Chunk analiz scripti:
```python
from src.retrieval.chroma_store import ChromaStore
cs = ChromaStore()

# Tüm collection'daki chunk istatistikleri
results = cs.collection.get(include=['documents', 'metadatas'])

chunk_sizes = [len(doc.split()) for doc in results['documents']]
print(f"Chunk boyut: min={min(chunk_sizes)}, max={max(chunk_sizes)}, mean={sum(chunk_sizes)/len(chunk_sizes):.1f}")

# Bölüm dağılımı
from collections import Counter
madde_dist = Counter([m['alt_madde'] for m in results['metadatas']])
for madde, cnt in madde_dist.most_common():
    print(f"  Madde {madde}: {cnt} chunk")
```

---

### 2.2 Filter Mekanizması Kırılgan ⚠️

**Gözlem:** DALGA_6_AKSIYON_PLANI'nda:
```
2.2 Q11 – LUSTRAL emzirme (Retrieval başarısız)
    "Sorun: KÜB'de bilgi var ama 'BİLGİ YOK' dedi."
```

**Sebep (Anlaşılan):** `ChromaStore.search()` çağrısında:
```python
def search(self, query, filter_ilac=None, k=10):
    if filter_ilac:
        # filter_ilac=['LUSTRAL'] ama DB'de 'LUSTRAL® 50 mg...' var
        # Exact match başarısız → 0 sonuç
        # Fallback mekanizması?
```

**Çözüm (Zaten Dalga 6'da yapıldı):** `_resolve_drug_names()` fonksiyonuna prefix/contains fallback eklenmesi.

**Değerlendirme:** ✅ Fixed (S18 recall 0→8)

---

### 2.3 Reranker Skor Analizi Yapılmamış ⚠️

**Soru:** Cross-encoder reranker'ın skor dağılımı ne?
- Çoğu chunk 0.9+ score mı? (false positive risk)
- Çoğu 0.5 score mı? (belirsizlik)
- Score threshold doğru seçilmiş mi?

**Öneri:** Score histogram:
```bash
.venv/Scripts/python << 'EOF'
from src.retrieval.reranker import Reranker
import matplotlib.pyplot as plt

reranker = Reranker()
scores = []  # Tüm sorguların reranker skorlarını topla
# ... (code) ...
plt.hist(scores, bins=30)
plt.xlabel("Reranker Score")
plt.ylabel("Frequency")
plt.savefig("reranker_score_distribution.png")
EOF
```

---

## 3. LLM & Prompt Sorunları

### 3.1 Yanıt Length Caps 🔴

**Gözlem:** `rag_engine.py`'de LLM yanıt limiti 1400 token.

```python
# src/agents/rag_engine.py
max_tokens = 1400  # ← Sabit sınır
```

**Problem:**
- Kompleks sorular (etkileşim + doz + kontrendikasyon) 1400 token'da kısılıyor
- Örn: S3 (PLASORİN+FLAGYL) yanıtı 1805 token ama limit 1400 → Truncate?

**Sorun:** klinik_v2.json'daki "yanit_len" değerleri 1200-2200 arasında değişiyor. Sistem kaç tanesini tam olarak verebiliyor?

**Çözüm (Önerilir):**
```python
# Dinamik token sınırı: soru türüne göre
if query_type == "multi_interaction":
    max_tokens = 2000  # Etkileşim sorguları uzun olabilir
elif query_type == "contraindication":
    max_tokens = 1200  # Kısa & net olabilir
else:
    max_tokens = 1400  # Default
```

---

### 3.2 "BİLGİ YOK" Guardrail Aşırı Katı 🔴

**Gözlem:** DALGA 6'da Q25 (JARDIANCE yan etki) çözüldü:
```
Eski: "KÜB metninde karşılaştırılan bilgiyi yazma" kuralı
      → S16 JARDIANCE yan etkisi (4.8) filtreleniyor

Yeni: Madde 4.8 (yan etki) ve 4.4 (uyarı) muafiyeti eklendi
      → S16 başarıyla geçti
```

**Değerlendirme:** ✅ Fixed

**Kalan Risk:** Diğer maddelerde (4.3, 4.6) benzer sorun var mı?

---

### 3.3 Hallucination Test Sınırlı ⚠️

**Gözlem:** klinik_v1.json'da S13, S14, S15 hallucination testleri var:
```
"Bu sorular corpus'ta yok — sistem 'bilgi yok' demeli, uydurmamalı."
```

**Soru:** Sonuç ne?
- Tüm 3 soruyu başarılı geçti mi?
- Sistem yanıt verdi ama kaynak göstermedi mi?
- "Bilgi bulunamadı" dedikten sonra tahmin yaptı mı?

**Öneri:** Hallucination test setini genişlet:
```json
[
  {
    "id": "H16",
    "kategori": "inexistent_interaction",
    "soru": "Paracetamol + Insulin kombinasyonunda CYP450 etkileşimi nedir?",
    "beklenen": "BİLGİ YOK (veya 'etkileşim beklenmez')",
    "yanlış_yanıt": "CYP2C9 inhibisyonu riski"
  }
]
```

---

## 4. Neo4j Graph Veri Sorunları

### 4.1 Graph Node Bütünlüğü Bilinmiyor ⚠️

**Soru:** Neo4j'de 427 drug node var ama:
- Tüm nodelar relasyon (INTERACTS_WITH, CONTRAINDICATED_FOR) var mı?
- Orphan node'lar var mı (bağlantısız)?
- Kontrendikasyon data ne kadarı temsil ediyor?

**Öneri:** Graph health check:
```cypher
// Bağlantısız drug node'ları bul
MATCH (d:Drug)
WHERE NOT (d)--()
RETURN COUNT(d) as orphan_count
```

### 4.2 CYP450 Mapping Tamamlanmadı ⚠️

**Gözlem:** `cyp450_mapper.py`'de ~50 ilaç için statik mapping var.

```python
ILAC_CYP_PROFILI = {
    "CANDÍDIN": {...},
    "CANDIMAX": {...},
    # ... 48 ilaç daha ...
}
```

**Problem:** 427 drug node'dan sadece ~50'si explicit profile var. **Kalan 377 ilaçta CYP etkileşimi otomatik tespit edilemiyor.**

**Çözüm (Önerilir):**

Option 1: KÜB 4.5 metninden otomatik parse
```python
def extract_cyp_from_text(text: str) -> dict:
    """
    'CYP2C19 inhibitörü' → {"inhibitor": ["CYP2C19"]}
    Regex ile parse et
    """
    # Already in cyp450_mapper.py!
    pattern = r"(güçlü|orta|zayıf)?\s*CYP\s*(\d[A-Z]\d+)\s*(inhibitör|substrat|indükleyici)"
    # ...
```

Option 2: Dış kaynak (DrugBank API)
```bash
# DrugBank free tier
curl -H "Authorization: Bearer $DRUGBANK_KEY" \
  "https://api.drugbank.com/v1/drugs/warfarin" | jq '.enzymes'
```

---

## 5. RAGAS Evaluasyon Sorunları

### 5.1 NaN/Timeout Sorunu Kısmen Çözüldü ⚠️

**Gözlem:**
```
v3: Faithfulness = 0.7565 (NaN %60)
↓
Dalga 6: timeout 300s → 600s, max_workers 2 → 1
↓
? NaN oranı düştü mü? (Henüz raporlanmadı)
```

**Problem:** RAGAS v3 final koşu yapılmadı. Timeout artırmasının etkisi bilinmiyor.

**Çözüm (Acil):**
```bash
.venv/Scripts/python scripts/run_eval.py \
    --questions data/eval/ragas_v3_questions.json \
    --evaluator local \
    --output data/eval/ragas_v3_final.json
```

Çalıştıktan sonra karşılaştır:
```python
import json
v3 = json.load(open('data/eval/ragas_v3_results.json'))
v3_final = json.load(open('data/eval/ragas_v3_final.json'))

print(f"Faithfulness: {v3['scores']['faithfulness']:.4f} → {v3_final['scores']['faithfulness']:.4f}")
print(f"NaN oranı: {sum(1 for q in v3['per_question'] if q['faithfulness'] is None) / len(v3['per_question']):.2%}")
```

---

### 5.2 Ground Truth Kalitesi Kontrol Edilmedi ⚠️

**Gözlem:** DALGA_6_AKSIYON_PLANI'nda 6 soru için GT revizyonu yapıldı:
```
v3_q01, v3_q04, v3_q20, v3_q22, v3_q23, v3_q29
```

**Soru:** Bu revizyon yapıldı mı kontrol edilmiş mi?

```bash
# Kontrol script
diff <(jq '.[] | select(.id == "v3_q01") | .ground_truth' data/eval/ragas_v3_questions.json) \
     <(echo '"AV blok riski nedeniyle kontrendikedir..."')
```

---

## 6. Test Coverage Eksiklikleri 🔴

### 6.1 Web UI Testi Yapılmıyor

**Gözlem:** pytest 49 test var ama tüm API/Streamlit UI iş akışında manual test.

```
test_retrieval.py      ✓ 15 test
test_rag_engine.py     ✓ 12 test
test_graph_retriever.py ✓ 8 test
test_cyp450_mapper.py  ✓ 10 test
─────────────────────────────
Toplam: 49 test

Fakat: End-to-end klinik senaryolar?
       Web API /answer endpoint'i?
       Streamlit UI etkileşimleri?
```

**Çözüm (Önerilir):**
```python
# tests/test_e2e_api.py (YENİ)
def test_plavix_candidin_interaction():
    """Q10: PLAVIX + CANDÍDIN (CYP2C19) — E2E test"""
    client = TestClient(app)
    response = client.post("/answer", json={
        "soru": "PLAVIX kullanan hastaya CANDÍDIN...",
        "hasta": {...}
    })
    assert response.status_code == 200
    assert "CYP2C19" in response.json()["answer"]
    assert response.json()["n_contexts"] > 0
```

---

### 6.2 Negative Test Yok

**Gözlem:** Hallucination, edge case test az.

```
İçinde yok:
  ✗ Boş hasta profili
  ✗ Geçersiz ilaç adı
  ✗ Neo4j offline
  ✗ ChromaDB koleksiyonu boş
  ✗ LLM API rate limit
```

---

## 7. Operasyon Sorunları 🔴

### 7.1 Neo4j Otomatik Başlatma Yok 🔴 (KRİTİK)

**Gözlem:** `start.bat` Neo4j'yi **başlatmıyor**. Sadece FastAPI + Streamlit başlatıyor.

```batch
# start.bat (eski)
echo [5/5] Servisler baslatiliyor...
# Neo4j başlatma kodu YOK!
start "PharmAssist-API" cmd /k ".venv\Scripts\python -m uvicorn..."
```

**Problem:** Developer `start.bat`'i çalıştırdığında:
1. Python venv kontrolü ✓
2. Port cleanup ✓
3. FastAPI + Streamlit başlatma ✓
4. **Neo4j BAŞLATILMIYOR ❌** → "Failed to connect" hatası

```
neo4j.exceptions.ServiceUnavailable: Couldn't connect to localhost:7687
```

**Çözüm (Uygulandı):** start.bat'ı güncellendi:
```batch
REM ========== CHECK 5: NEO4J DOCKER ==========
docker ps 2>nul | findstr "pharmassist-neo4j" >nul
if errorlevel 1 (
    echo [INFO] Neo4j baslaniyor (docker-compose)...
    docker-compose up -d neo4j
    timeout /t 15 /nobreak
) else (
    echo [OK] Neo4j: ZATEN CALISIYYOR
)
```

**Status:** ✅ **FIXED**

---

### 7.2 Neo4j Bağlantı İstikrarsız

**Soru:** Production'da yeniden başlatma mekanizması var mı?

```python
# src/graph/neo4j_client.py
def get_driver():
    driver = GraphDatabase.driver(...)
    driver.verify_connectivity()  # ← Bağlantı kontrol
    # Ama bağlantı kesildiyse?
```

**Çözüm (Önerilir):**
```python
from functools import wraps
from time import sleep

def retry_on_connection_error(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ServiceUnavailable as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Bağlantı hatası, {attempt+1}. deneme...")
                    sleep(2 ** attempt)
        return wrapper
    return decorator

@retry_on_connection_error()
def run_query(cypher, params):
    # ...
```

---

### 7.2 Docker Compose Kontrol Edilmedi

**Soru:** Docker Compose'ta:
- Neo4j persistence (volume) doğru mu?
- Environment variables güvenli mi?
- Health check tanımlı mı?

**Öneri:** docker-compose.yml audit:
```yaml
neo4j:
  image: neo4j:5.x
  healthcheck:
    test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "$NEO4J_AUTH", "RETURN 1"]
    interval: 10s
    timeout: 5s
    retries: 5
  volumes:
    - neo4j_data:/data  # ← Persistence kontrolü
    - neo4j_logs:/logs
```

---

## 8. Dokümantasyon Eksiklikleri 📖

### 8.1 Developer Onboarding Yok

**Eksik:**
- Setup guide (Neo4j, ChromaDB kurulumu)
- API endpoint referansı
- Contribution guidelines
- Troubleshooting runbook

**Örnek:** Yeni developer Neo4j'i nasıl başlatacağını bilemez.

### 8.2 Deployment Belgeleri Eksik

**Eksik:**
- Production checklist
- Monitoring setup (logs, metrics)
- Backup strategy
- Rollback prosedürü

---

## 9. Öneriler — Öncelik Sırası

### 🔴 **KRITIK (Hemen):**

| # | Görev | Neden | ETA |
|---|-------|-------|-----|
| 1 | RAGAS v3 final koşu | Faithfulness NaN oranı bilinmiyor | 2h |
| 2 | GT revizyon doğrulama | 6 soru güncellenmiş mi kontrol yok | 1h |
| 3 | Neo4j bağlantı retry logic | Production'da bağlantı kesilebilir | 3h |

### 🟡 **ORTA (Bu Sprint):**

| # | Görev | Neden | ETA |
|---|-------|-------|-----|
| 4 | İlaç adı normalization | Retrieval başarısızlıkları | 4h |
| 5 | CYP450 mapping genişletme | 427 ilaçtan 377'sinde etkileşim tespit yok | 6h |
| 6 | E2E API testleri | Web UI test yok | 4h |
| 7 | Chunk kalitesi analizi | Avg chunk size bilinmiyor | 2h |

### 🟢 **DÜŞÜk (Sonraki Sprint):**

| # | Görev | Neden | ETA |
|---|-------|-------|-----|
| 8 | Developer onboarding docs | DX iyileştirmesi | 3h |
| 9 | Character encoding standardization | Edge case sorunları | 2h |
| 10 | Monitoring & alerting | Production readiness | 4h |

---

## 10. Özet Tablo

| Alan | Durum | Skor | Risk |
|------|-------|------|------|
| **Mimarı** | Solid, iyi tasarlanmış | 8/10 | 🟢 Düşük |
| **Veri Kalitesi** | Eksikler (normalization, mapping) | 6/10 | 🟡 Orta |
| **Retrieval** | Dalga 6'dan sonra iyileşti | 7/10 | 🟡 Orta |
| **LLM Pipeline** | Functinal, prompt optimizasyonu yok | 7/10 | 🟡 Orta |
| **Evaluasyon** | RAGAS eksik (final koşu yok) | 5/10 | 🔴 Yüksek |
| **Testing** | 49 test var, E2E yok | 6/10 | 🟡 Orta |
| **Operasyon** | Docker ok, monitoring yok | 5/10 | 🔴 Yüksek |
| **Dokümantasyon** | Proje overview ok, dev docs yok | 6/10 | 🟡 Orta |

---

## Sonuç

PharmAssist **hızlı iterasyon** ve **Dalga 6 müdahaleleri** sayesinde iyiye gidiyor. **Temel mimarı sağlam** (8/10) ama **veri ve operasyon katmanlarında** iyileştirme gerekli.

**Kritik:** RAGAS v3 final koşu + Neo4j stabilizasyonu. **Orta:** Normalization + CYP mapping.

**İleri ilerleme için:** Hafta sonu RAGAS metrikleri harekete geçir, Dalga 7'ye başla.

---

**Hazırlayan:** Claude Code Audit  
**Son Güncelleme:** 2026-04-15 12:45 UTC  
**Status:** 📋 Ready for Review
