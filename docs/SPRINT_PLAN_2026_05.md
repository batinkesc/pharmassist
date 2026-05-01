# Sprint Planı — Sunum Hazırlığı (2026-05-01 → 2026-05-14)

**Versiyon:** 1.1  
**Oluşturma:** 2026-05-01  
**Sunum Tarihi:** 2026-05-14/15  
**Durum:** AKTİF

---

## 0. Git Çalışma Kuralı (ÖNEMLİ — Önce Oku)

**Bu sprintte HİÇBİR çalışma `master`'a yapılmaz.** Sunuma yetişmezse veya sonuçlar tatmin etmezse master kirletilmemiş kalmalı.

### Çalışma Branch'i
```
sprint/sunum-2026-05
```

### Branch Kurulum (sen 1 kez çalıştır)
```bash
git checkout master
git pull
git checkout -b sprint/sunum-2026-05
git push -u origin sprint/sunum-2026-05
```

### Her Ajanın Uyması Gereken Kurallar
1. **Her task başında doğrula:** `git branch --show-current` → çıktı `sprint/sunum-2026-05` olmalı. Değilse DUR ve raporla.
2. **Her task sonunda commit at:** `git add <değişen-dosyalar>` + `git commit -m "Task N: <kısa-başlık>"`. `git add -A` veya `git add .` KULLANMA.
3. **Push opsiyoneldir** — kullanıcı isterse yapar, ajan kendiliğinden push etmez.
4. **`master`'a merge YOK** — sprint sonunda kullanıcı karar verir. Ajanlar merge başlatmaz.
5. **Conflict olursa DUR** — kullanıcıya sor, kendiliğinden çözme.

### Sprint Sonu (Sunum Sonrası)
Kullanıcı 2 seçenek arasından birini seçer:
- **Başarılıysa:** `master`'a merge (PR veya direkt)
- **Yetişmezse / kötüyse:** Branch korunur, master temiz kalır, ileride bakılır

---

## 1. Amaç

PharmAssist'in sunuma hazır hale gelmesi için tespit edilen açıkları kapatmak. RAGAS metric optimizasyonu **DURDURULDU** (Run 20 baseline olarak korunuyor). Hedef: savunulabilir değerlendirme çerçevesi + temporal validity + uncertainty quantification + sunum hikayesi.

**RAGAS hakkında karar:** Run 20 (F:0.7192 CU:0.7823 CR:0.9010 Ort:0.8008) main baseline olarak donduruldu. Bu sprintte RAGAS'a yeniden bakılmayacak. Yeni metrik koşusu sadece final raporlama için 1 kez yapılacak (Task 6).

---

## 2. Davranış Kuralları (Her Ajan Önce Okur)

### Genel
1. **Atomik görev yap** — yalnızca verilen task'ın spec'inde olanı, scope büyütme.
2. **Test çalıştır ve sonucu raporla** — geçtiğini iddia etme, çıktıyı yapıştır.
3. **Mevcut testi kırarsan dur ve raporla** — kendi başına düzeltmeye çalışma.
4. **`PROJE_DOKUMANTASYONU.md` güncellenir** ama büyük yeniden yazım YOK — sadece ilgili bölüm.
5. **`CLAUDE.md` veya memory dosyalarına dokunma.**
6. **Yeni dosya açmadan önce** ilgili modülde benzer dosya var mı bak, varsa onu genişlet.
7. Bu projede **severity, cumulative risk, CYP analizi DETERMİNİSTİK** — LLM çağrısı eklemek istediğinde ÖNCE kullanıcıya sor.
8. **Türkçe değişken/fonksiyon adları** kullanılıyor — yenide aynı stili sürdür.
9. **ChromaDB persistent veriyi WIPE ETME.** Migration gerekiyorsa idempotent script yaz.
10. **Antigravity ya da Claude Code:** task'ı bitirdikten sonra `## Antigravity Notları` veya `## Doğrulama Notları` bölümünü doldur, status'u güncelle, **sıradaki task'ı kendiliğinden başlatma**.

### Çıktı Format Standardı (her task sonunda)
```
- Değişen dosyalar (mutlak path):
- Eklenen/silinen kod (özet):
- Çalıştırılan test komutu:
- Test çıktısı (son 20 satır yeter):
- git diff --stat çıktısı:
- Yeni eklenen testler:
- Engeller / sorular:
```

### Proje Bağlamı (özet)
- **Mimari:** ChromaDB (multilingual-e5-large) + reranker → retrieval; Neo4j → graf (4021 IW + 891 CYP); Claude Haiku 4.5 → yanıt; Together AI Qwen3-235B → KUB extraction + RAGAS evaluator.
- **VALIDATE:** 6 adımlı post-processing (`src/agents/rag_engine.py:609-1212`).
- **3-katman cevap formatı:** `[KÜB Aktarımı]/[Sistem Tespitleri]/[Değerlendirme]`
- **Test:** pytest, `tests/` altında 95 test geçiyor — kırma.
- **Konfig:** `src/config/settings.py` (Pydantic BaseSettings).
- **Detay:** `PROJE_DOKUMANTASYONU.md`

---

## 3. Workflow Protokolü

### Status Tipleri
| Status | Anlam |
|--------|-------|
| `PENDING_DETAIL` | Spec eksik, henüz başlanamaz |
| `READY` | Spec hazır, başlanabilir |
| `IN_PROGRESS` | Bir ajan üzerinde çalışıyor |
| `DONE` | Ajan bitti dedi, doğrulanmadı |
| `VERIFIED` | Claude Code doğruladı, kapalı |
| `BLOCKED` | Engel var, açıklama Notlar'da |

### Akış
```
PENDING_DETAIL → READY → IN_PROGRESS → DONE → VERIFIED
                          ↓
                       BLOCKED (gerekirse)
```

### Antigravity'nin Yaptığı
1. **Branch kontrolü:** `git branch --show-current` → `sprint/sunum-2026-05` değilse DUR.
2. Status `READY` olan en küçük numaralı task'ı seç.
3. Status'u `IN_PROGRESS` yap, `Atanan` alanına "Antigravity" yaz.
4. Task'ı yap.
5. **Commit at:** `git add <dosyalar>` + `git commit -m "Task N: <başlık>"`.
6. `Antigravity Notları` bölümünü "Çıktı Format Standardı"na göre doldur (commit hash'i de ekle).
7. Status'u `DONE` yap, dur.

### Claude Code'un (Ben) Yaptığı
1. Status `DONE` olan task'ları al.
2. Belirtilen dosyaları oku, gerçek diff'i kontrol et.
3. Acceptance criteria'yı tek tek doğrula.
4. Verification command'ları çalıştır.
5. ✅ ise: `Doğrulama Notları` bölümünü doldur, status'u `VERIFIED` yap, sıradaki task'ı `READY` işaretle.
6. ❌ ise: Düzeltme listesini `Doğrulama Notları`'na yaz, status'u `IN_PROGRESS` geri al.

### Limit Yönetimi
- Claude Code limiti dolduğunda Antigravity tek başına çalışmaya devam eder.
- **Kural:** Verifikasyon olmadan 1'den fazla task'a `DONE` koyma. Bekle.
- Limit gelince Claude Code bekleyen `DONE` task'ları sırayla doğrular.

---

## 4. Hafta Görünümü

| # | Task | Tahmini Süre | Atanabilir | Status |
|---|------|--------------|-----------|--------|
| 1 | KÜB Versioning + Cevap Footer | 1 gün | Antigravity | `IN_PROGRESS` |
| 2 | Aggregate Confidence Label | 1 gün | Antigravity | `READY` |
| 3 | Cross-Evaluator Agreement Script | 1.5 gün | Antigravity | `PENDING_DETAIL` |
| 4 | VALIDATE Coverage Metric | 1 gün | Antigravity | `PENDING_DETAIL` |
| 5 | NaN Sorularının Kök Neden Raporu (Q14, Q23, Q26) | 1 gün | Antigravity | `PENDING_DETAIL` |
| 6 | Final RAGAS Run + Konsolide Rapor | 0.5 gün | Sen | `PENDING_DETAIL` |
| 7 | Sunum Slide Outline (1. taslak) | 2 gün | Sen + Claude Code | `PENDING_DETAIL` |
| M1 | Klinisyen feedback (5-10 örnek) | Paralel | Sen (insan ağı) | Manuel |

**Skip listesi:** INN-NULL fix (re-ingest gerektirir, risk yüksek), quarantine automation (etki düşük), yeni model fix denemesi.

---

## 5. Görevler (Detay)

---

### Task 1: KÜB Versioning + Cevap Footer

**Status:** `IN_PROGRESS`  
**Atanan:** Antigravity  
**Tahmini Süre:** 1 gün

#### Goal
Her chunk'a parse_date ve pdf_hash eklemek; her cevabın altında kullanılan KÜB tarih(ler)ini italic ile göstermek.

#### Why
Klinikte KÜB'ler güncellenir. Şu an chunk metadata'da tarih yok → klinisyen "bu yanıt hangi tarihli KÜB'e dayanıyor?" sorusunu soramıyor. Sunumda "temporal validity'i ihmal etmedik" sinyali için kritik.

#### Files
- `src/ingestion/pdf_parser.py`
- `src/ingestion/kub_extractor.py`
- `src/retrieval/chroma_store.py`
- `src/agents/rag_engine.py`
- `src/api/schemas.py`
- `app.py`
- `tests/` (yeni test dosyası)
- `PROJE_DOKUMANTASYONU.md` (bölüm 5)

#### Concrete Spec

**1. PDF parse aşamasında metadata çıkar (`pdf_parser.py`):**
- Her PDF için PyMuPDF üzerinden `doc.metadata.get('modDate', '')` veya `creationDate` oku, ISO formatına çevir (`"2026-04-25"`).
- Boşsa fallback: `os.path.getmtime(pdf_path)` → ISO.
- Hash: `hashlib.sha1(open(pdf, 'rb').read()).hexdigest()[:16]`.

**2. Chunk metadata'ya 2 string alan ekle:**
- `kub_parse_date: str` — ISO format (örn. `"2026-04-25"`)
- `kub_pdf_hash: str` — 16 karakter hex
- ChromaDB metadata yalnızca `str/int/float/bool` kabul ediyor — string olarak ekle.

**3. RAGResponse'a yeni alan (`rag_engine.py`):**
```python
@dataclass
class RAGResponse:
    # ... mevcut alanlar
    kub_tarihleri: list[str] = field(default_factory=list)
```
`run_rag()` çıkışında kaynaklarda kullanılan unique tarihleri topla, sıralı liste döndür.

**4. Cevap footer template'i:**
- API response'ta `kub_tarihleri: list[str]` alanı (`schemas.py`).
- `app.py` Streamlit'te Klinik Yanıt'ın altında küçük italic gri yazı:
  - 1 tarih: `"_Kaynak KÜB tarihi: 2026-04-25_"`
  - >1 tarih: `"_Kaynak KÜB tarihleri (en eski → en yeni): 2026-04-22, 2026-04-25_"`

**5. Mevcut DB için migration:**
- `chroma_store.py` içine `migrate_add_kub_dates()` fonksiyonu — idempotent, mevcut chunk'lara metadata enjekte eder.
- ÖNEMLİ: ChromaDB persistent veriyi WIPE ETME. Sadece metadata UPDATE.
- Script bir kez çalıştırılır, log üretir.

#### Acceptance Criteria
- [ ] Yeni sorgu API yanıtında `kub_tarihleri` listesi var ve boş değil.
- [ ] Streamlit UI'da Klinik Yanıt altında "Kaynak KÜB tarih(leri): ..." satırı görünüyor.
- [ ] `tests/test_kub_versioning.py` — en az 3 test:
  1. Chunk metadata'sında `kub_parse_date` ve `kub_pdf_hash` var
  2. RAGResponse.kub_tarihleri unique ve sıralı
  3. Migration idempotent (2 kez çalıştırınca aynı sonuç)
- [ ] Mevcut 95 test geçiyor.
- [ ] `PROJE_DOKUMANTASYONU.md` Bölüm 5 (Veri Modeli) altına chunk metadata listesine 2 yeni alan eklendi.

#### Verification Commands
```bash
pytest tests/ -v
pytest tests/test_kub_versioning.py -v
python -c "from src.retrieval.chroma_store import _client; col = _client().get_collection('kub_chunks'); print(col.peek(1))"
```
Son komutta peek çıktısında `kub_parse_date` ve `kub_pdf_hash` görünmeli.

#### Antigravity Notları
*(Burayı yapan ajan doldurur)*

#### Doğrulama Notları
*(Burayı Claude Code doldurur)*

#### Blockerlar
*(varsa)*

---

### Task 2: Aggregate Confidence Label

**Status:** `READY`  
**Atanan:** —  
**Tahmini Süre:** 1 gün  
**Bağımlılık:** Yok (Task 1'den bağımsız)

#### Goal
Her yanıt için tek aggregate güven skoru (0.0-1.0) + üç-seviyeli etiket (yüksek/orta/düşük) hesaplamak ve UI + API'da göstermek.

#### Why
Şu an retrieval skoru chunk başına var ama yanıt seviyesinde aggregate güven yok. Klinisyen "bu yanıta ne kadar güveneyim?" sorusunu soruyor. Demo'da "düşük güvenli yanıt" senaryosu (out-of-corpus, S13-S15) çok etkili.

#### Files
- `src/agents/rag_engine.py`
- `src/api/schemas.py`
- `app.py`
- `tests/test_confidence_score.py` (yeni)

#### Concrete Spec

**1. Confidence formülü (`rag_engine.py` içinde yeni fonksiyon):**
```python
def _hesapla_guven_skoru(
    kaynaklar: list[RetrievedChunk],
    yanit_metni: str,
) -> tuple[float, str]:
    """
    0.0-1.0 arası güven skoru ve etiket döner.
    
    Formül:
      retrieval_skoru = mean(top-3 chunk score) — kaynak yoksa 0.0
      validate_orani = 1 - (count(['DOĞRULANAMADI', 'AŞIRI YORUM']) 
                            / max(cumle_sayisi, 1))
      guven = 0.6 * retrieval_skoru + 0.4 * validate_orani
    
    Etiket:
      kaynak yoksa → "Kaynak yok — yanıt üretilmedi"
      >= 0.75    → "Yüksek güven"
      0.55-0.75  → "Orta güven"
      < 0.55     → "Düşük güven — manuel doğrulama önerilir"
    """
```

Cümle sayımı için: `re.split(r'[.!?]+', yanit_metni)` filtreli (boş cümle hariç).

**2. RAGResponse'a 2 alan:**
```python
guven_skoru: float = 0.0
guven_etiketi: str = ""
```

**3. API response (`schemas.py`)** — aynı 2 alan.

**4. UI'da görselleştirme (`app.py`):**
- Klinik Yanıt başlığının yanında `st.metric` veya inline badge.
- Renk eşlemesi:
  - "Yüksek güven" → yeşil
  - "Orta güven" → sarı
  - "Düşük güven ..." → kırmızı/turuncu
  - "Kaynak yok ..." → gri
- Format: `⬤ Yüksek güven (0.82)` *(emoji yerine renkli markdown veya HTML span kullanılabilir; Streamlit'in native renk desteği yok ise `st.markdown` ile inline CSS)*.

**5. Edge case handling:**
- `len(kaynaklar) == 0` → guven_skoru=0.0, etiket="Kaynak yok — yanıt üretilmedi"
- `len(yanit_metni.strip()) == 0` → aynı

#### Acceptance Criteria
- [ ] Tüm sorgu yanıtlarında `guven_skoru` (float) ve `guven_etiketi` (str) mevcut.
- [ ] S13-S15 (klinik_test.py corpus dışı senaryolar) için "Düşük güven" veya "Kaynak yok" çıkıyor.
- [ ] "Augmentin penisilin alerjisi" gibi net soru için "Yüksek güven" çıkıyor.
- [ ] UI'da renkli badge görünüyor (Streamlit ekran görüntüsü Antigravity Notları'na yapıştırılabilir).
- [ ] `tests/test_confidence_score.py` — 4 test:
  1. Kaynak yok → 0.0 + "Kaynak yok ..."
  2. Yüksek skor + 0 etiket → > 0.75
  3. Orta skor + 1 [DOĞRULANAMADI] → 0.55-0.75
  4. Formül matematik doğru (manuel hesap karşılaştırması)
- [ ] Mevcut 95 test geçiyor.

#### Verification Commands
```bash
pytest tests/test_confidence_score.py -v
pytest tests/ -v  # tümü geçmeli
python scripts/klinik_test.py --senaryo S13  # Düşük güven beklenir
python scripts/klinik_test.py --senaryo S01  # Yüksek güven beklenir
```

#### Antigravity Notları
*(boş)*

#### Doğrulama Notları
*(boş)*

#### Blockerlar
*(varsa)*

---

### Task 3: Cross-Evaluator Agreement Script

**Status:** `PENDING_DETAIL`  
**Atanan:** —  
**Tahmini Süre:** 1.5 gün

#### Goal
Aynı soru setini Qwen3-235B + Haiku 4.5 ile paralel evaluate et, evaluator'lar arası korelasyon ve disagreement raporla.

#### Why
RAGAS gürültüsünü ölç → "Run 20 baseline" iddiasının istatistiksel temelini kur. Sunumda "evaluator gürültüsünü ölçtük, korelasyon 0.X" cümlesini hak edersin. Tek evaluator bağımlılığını kırar.

#### Detay Spec
*(Task 2 doğrulandıktan sonra Claude Code yazacak. Şu an PENDING_DETAIL — Antigravity başlatamaz.)*

Ön düşünceler:
- Mevcut 33 soru üzerinde Haiku 4.5 maliyet kestirimi: ~5 soru için $0.70 görüldü → 33 soru ~$5. Kabul edilebilir tek seferlik maliyet.
- Output: per-soru F skor karşılaştırma tablosu + Pearson r + Cohen's kappa.
- `scripts/cross_evaluator.py` yeni dosya, `data/eval/cross_evaluator_report.md` çıktı.

---

### Task 4: VALIDATE Coverage Metric

**Status:** `PENDING_DETAIL`  
**Atanan:** —  
**Tahmini Süre:** 1 gün

#### Goal
Her yanıt için: kaç cümle kaynak-etiketli, kaç cümle `[DOĞRULANAMADI]`, kaç cümle `[AŞIRI YORUM]` — sistemin kendi davranışını ölçen, RAGAS-bağımsız bir metric.

#### Why
RAGAS gürültüsünden bağımsız. Sistemin kendi etiketleme davranışını ölçer. Sunumda "kendi metric çerçevemiz var" cümlesini hak eder.

#### Detay Spec
*(Sıra geldiğinde yazılacak)*

---

### Task 5: NaN Sorularının Kök Neden Raporu

**Status:** `PENDING_DETAIL`  
**Atanan:** —  
**Tahmini Süre:** 1 gün

#### Goal
Q14 ALDACTONE+PLASORİN, Q23 TEGRETOL+LAMICTAL, Q26 RENITEC için NaN/düşük skor üretildiği nedenleri belgele. Çözülebilenleri çöz, çözülemeyenleri açıkça sınıflandır (GT problemi / evaluator sınırı / sistem hatası).

#### Why
Bunlar tam olarak **safety-critical** kategoriler (antikoagülan, geriyatrik, feokromasitoma). Sunumda "biliyoruz, analiz ettik, sınıflandırdık" cümlesi gerekir.

#### Detay Spec
*(Sıra geldiğinde yazılacak)*

---

### Task 6: Final RAGAS Run + Konsolide Rapor

**Status:** `PENDING_DETAIL`  
**Atanan:** Sen (lokal makine, Together AI quota)  
**Tahmini Süre:** 0.5 gün

#### Goal
Tüm task'lar VERIFIED olduktan sonra **TEK SEFERLİK** RAGAS run-21 koştur. Sonuçları + cross-evaluator raporu + VALIDATE coverage + NaN raporunu tek bir konsolide markdown'a topla.

#### Detay Spec
*(Sıra geldiğinde yazılacak)*

---

### Task 7: Sunum Slide Outline (1. Taslak)

**Status:** `PENDING_DETAIL`  
**Atanan:** Birlikte  
**Tahmini Süre:** 2 gün (paralel)

#### Goal
10-12 slaytlık sunum iskeleti.

#### Detay Spec
*(8 Mayıs civarı yazılacak)*

---

## 6. Manuel Görevler (Kod Değil)

### M1 — Klinisyen Feedback
**Atanan:** Sen  
**Status:** Manuel — Paralel başlat  
**Tahmini Süre:** 1-2 hafta (insan ağı)

**Adımlar:**
1. En iyi 5-10 örnek soru-yanıt PDF'i hazırla (sistem çıktısı + 3-katman format dahil).
2. 1-2 hekim/eczacı arkadaşa gönder. 4-li skala iste:
   - Doğru
   - Kısmen doğru
   - Yanlış
   - Tehlikeli yanlış
3. Geri bildirim notlarını topla.
4. Sunumda "n=2 uzman feedback'i aldık, sonuçlar X" cümlesi hak edilir.

**Çıktı:** `docs/KLINISYEN_FEEDBACK_2026_05.md`

---

## 7. Değişiklik Günlüğü

| Tarih | Değişiklik | Yapan |
|-------|-----------|-------|
| 2026-05-01 | Sprint planı oluşturuldu, Task 1+2 detaylandı | Claude Code |
| 2026-05-01 | v1.1: Bölüm 0 (Git Çalışma Kuralı) eklendi — branch `sprint/sunum-2026-05`, master'a yazma yasağı | Claude Code |

---

## 8. Sözlük / Hızlı Referans

**Dosya yolları (mutlak):**
- Ana proje: `C:\Users\kesic\Desktop\PharmAssistVersion2`
- Bu dosya: `docs/SPRINT_PLAN_2026_05.md`
- Test dizini: `tests/`
- Eval dizini: `data/eval/`
- Quarantine: `data/quarantine/`

**Önemli kod referansları:**
- VALIDATE pipeline: `src/agents/rag_engine.py:609-1212`
- HyDE: `src/agents/rag_engine.py:157-200`
- Confidence formula entegrasyonu: `src/agents/rag_engine.py` (run_rag dönüşü)
- ChromaDB: `src/retrieval/chroma_store.py`
- Patient profile: `src/agents/patient_profile.py`
- Cumulative risk (deterministik): `src/analysis/cumulative_risk.py`
- CYP mapper (84 kayıt): `src/analysis/cyp450_mapper.py`

**Test komutları:**
```bash
pytest tests/ -v                          # tümü
pytest tests/test_X.py -v                 # tek dosya
python scripts/klinik_test.py             # 15 senaryo
python scripts/klinik_test.py --senaryo S01  # tek senaryo
python scripts/run_eval.py                # RAGAS — sadece Task 6'da
```

**Çevre değişkenleri (.env):**
- `LLM_PROVIDER=claude` (yanıt üretimi için)
- `LM_STUDIO_URL`, `LM_STUDIO_MODEL=Qwen3-235B` (extraction)
- `RAGAS_PROVIDER=local`, `RAGAS_MODEL=Qwen3-235B`

---

## 9. Bilinen Açık Konular (Bu Sprintte Kapatılmıyor)

- INN-NULL Neo4j sorunu (`d.inn = NULL` Groq rebuild'inde). **Sunumda dürüst söylenecek.**
- Quarantine listesi manuel (otomatik QA gate yok).
- Klinisyen-validated GT eksik (M1 paralel iş).

---

**Bu doküman canlıdır. Her status değişikliğinde güncellenir.**
