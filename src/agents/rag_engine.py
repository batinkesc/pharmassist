"""
RAG Engine — ChromaDB retrieval + LLM orchestration.

Provider desteği (.env ile seçilir):
  LLM_PROVIDER=claude  → Anthropic Claude API (varsayılan)
  LLM_PROVIDER=local   → LM Studio / yerel OpenAI-uyumlu sunucu

Pipeline:
  1. augment_query() → AugmentedQuery (arama planları)
  2. Her SearchPlan için ChromaDB'de madde öncelik sırasıyla arama
  3. Chunk'ları kaynak bazlı grupla, tekrarları temizle
  4. Source-Aware Prompt oluştur
  5. LLM'e gönder (provider'a göre)
  6. RAGResponse döndür (yanıt + kaynak listesi)

Faithfulness kuralları:
  - Hiçbir zaman "güvenlidir", "zararsızdır" ifadesi kullanılmaz
  - Bilgi yoksa: "İncelenen prospektüslerde spesifik kayıt bulunamadı"
  - Her iddia için kaynak alıntısı zorunlu: [İlaç_Adı | Madde X.X | Sayfa Y]
"""

import os
import re
from dataclasses import dataclass, field
from loguru import logger
import anthropic
import openai
from dotenv import load_dotenv

load_dotenv(override=True)

from src.agents.patient_profile import PatientProfile
from src.agents.query_augmentor import augment_query, AugmentedQuery
from src.core.content_policy import POLICY
from src.retrieval.chroma_store import search, batch_search, hybrid_batch_search, _load_quarantine_list
from src.retrieval.reranker import rerank
from src.data.normalization import normalize_drug_name


# ---------------------------------------------------------------------------
# Sabitler — boyut/limit kararları ContentPolicy'den gelir
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_LOCAL_MODEL = "local-model"        # LM Studio'da yüklü model adı
DEFAULT_MAX_TOKENS = 1400                  # Geriye-dönük uyumluluk için; run_rag None geçilirse dinamik hesaplanır
MAX_CHUNKS_PER_QUERY  = POLICY.max_chunks_per_query
MIN_SCORE_THRESHOLD   = POLICY.min_score_threshold

# ---------------------------------------------------------------------------
# Dinamik token bütçesi — soru türüne göre LLM'e verilen max_tokens
# Kısa/odaklı soru türleri → daha az token → faithfulness artar (uzun cevap = daha fazla
# doğrulanamaz claim). Yan etki listeleri ve gebelik bölümleri meşru olarak uzun olabilir.
# ---------------------------------------------------------------------------
_SORU_TURU_BUTCE: dict[str, int] = {
    "negatif_bilgi_yok": 150,   # "[BİLGİ YOK: ...]" — 1 cümle yeterli
    "kontrendikasyon":   500,   # net karar + 1-2 koşul cümlesi
    "doz":               600,   # eşik + formül + 1 uyarı cümlesi
    "doz_bobrek":        600,
    "doz_karaciger":     600,
    "doz_geriyatrik":    550,
    "doz_pediyatrik":    600,
    "gebelik_laktasyon": 700,   # 4.6 bölümü uzun olabilir
    "etkilesim":         700,   # 2 ilaç + mekanizma özeti
    "cyp450_etkilesim":  750,   # CYP yönü + klinik etki
    "yan_etki":         1000,   # 4.8 listeleri meşru olarak uzundur (q31 gibi)
}
_DEFAULT_TUR_BUTCE = 600


def _dynamic_max_tokens(
    soru_turleri: list[str],
    hedef_ilaclar: list[str],
    cyp_var: bool = False,
) -> int:
    """Soru türü + ilaç sayısına göre LLM max_tokens bütçesi hesaplar.

    Mantık:
    - Her soru türünün bir tavan bütçesi var (kısa/odaklı türler düşük)
    - Birden fazla soru türü varsa en yüksek bütçeyi al
    - Ek ilaç başına +100 (2. ilaçtan itibaren, max 2 ilaç ek)
    - CYP mekanizması aktifse +100
    - Hard cap: 1200 (q31 gibi çok uzun yan etki listeleri için bile)
    """
    base = max(
        (_SORU_TURU_BUTCE.get(t, _DEFAULT_TUR_BUTCE) for t in soru_turleri),
        default=_DEFAULT_TUR_BUTCE,
    )
    extra_drugs = min(max(len(hedef_ilaclar) - 1, 0), 2)
    base += extra_drugs * 100
    if cyp_var:
        base += 100
    return min(base, 1200)


# ---------------------------------------------------------------------------
# Veri yapıları
# ---------------------------------------------------------------------------

@dataclass
class RetrievedChunk:
    """Zenginleştirilmiş chunk — retrieval çıktısı."""
    chunk_id: str
    ilac_adi: str
    madde_no: str
    madde_baslik: str
    icerik: str
    score: float
    sayfa: int
    kaynak_dosya: str
    alt_madde: str = ""

    def kaynak_etiketi(self) -> str:
        """Prompt içinde kullanılacak kaynak etiketi."""
        madde = f"{self.madde_no}"
        if self.alt_madde:
            madde += f"[{self.alt_madde}]"
        return f"[{self.ilac_adi} | Madde {madde} | Sayfa {self.sayfa}]"


@dataclass
class RAGResponse:
    """RAG pipeline çıktısı."""
    soru: str
    yanit: str
    kaynaklar: list[RetrievedChunk]
    hasta_ozeti: str
    soru_turleri: list[str]
    model: str
    prompt_token_sayisi: int = 0
    yanit_token_sayisi: int = 0
    kumlatif_riskler: list = field(default_factory=list)   # KumulatifRisk listesi
    cyp_etkilesimler: list = field(default_factory=list)   # CYPEtkilesim listesi
    quarantine_warnings: list = field(default_factory=list)  # Karantina uyarıları
    cyp_source: str = "unknown"  # "static_table" | "llm_extraction" | "unavailable" | "unknown"
    graf_baglami: str = ""      # Neo4j özet metni (RAGAS contexts için)
    kumlatif_metin: str = ""    # Kümülatif risk özet metni (RAGAS contexts için)
    cyp_metin: str = ""         # CYP450 özet metni (RAGAS contexts için)

    def kaynak_listesi(self) -> str:
        """Kullanılan kaynakları formatlı liste olarak döner."""
        if not self.kaynaklar:
            return "Kaynak bulunamadı."
        satirlar = []
        for i, k in enumerate(self.kaynaklar, 1):
            satirlar.append(
                f"{i}. {k.ilac_adi} — Madde {k.madde_no} ({k.madde_baslik}) "
                f"[Sayfa {k.sayfa}] (skor: {k.score:.3f})"
            )
        return "\n".join(satirlar)


# ---------------------------------------------------------------------------
# HyDE — Hypothetical Document Embeddings
# ---------------------------------------------------------------------------

def _generate_hyde_document(
    soru: str,
    hedef_ilaclar: list[str] | None,
    soru_turleri: list[str],
) -> str | None:
    """
    Verilen klinik soruya yanıt verebilecek kısa bir KÜB (prospektüs) paragrafı üretir.
    Bu varsayımsal metin, gerçek KÜB chunk'larına anlam olarak daha yakın embedding
    oluşturur → semantic retrieval kalitesini artırır (HyDE tekniği).

    Dönüş:
        str  — 2-3 cümlelik varsayımsal KÜB metni (retrieval query olarak kullanılır)
        None — API hatası veya ilgisiz sorular için
    """
    # Yalnızca semantik retrieval'ı iyileştireceği durumlar için çalıştır
    # Basit ilaç adı aramaları için gereksiz
    if not soru or len(soru.strip()) < 15:
        return None

    ilac_str = ", ".join(hedef_ilaclar) if hedef_ilaclar else "ilgili ilaç"
    tur_ipucu = ""
    if "kontrendikasyon" in soru_turleri:
        tur_ipucu = "Bölüm 4.3 (Kontrendikasyonlar) veya 4.4 (Özel uyarılar) çerçevesinde"
    elif "etkilesim" in soru_turleri:
        tur_ipucu = "Bölüm 4.5 (İlaç etkileşimleri) çerçevesinde"
    elif "doz" in soru_turleri:
        tur_ipucu = "Bölüm 4.2 (Pozoloji ve uygulama şekli) çerçevesinde"
    elif "gebelik" in soru_turleri:
        tur_ipucu = "Bölüm 4.6 (Gebelik ve emzirme döneminde kullanım) çerçevesinde"

    system_prompt = (
        "Sen bir ilaç Kısa Ürün Bilgisi (KÜB/prospektüs) uzmanısın. "
        "Kullanıcının sorusuna yanıt verecek gerçekçi bir KÜB paragrafı yaz. "
        "2-3 kısa cümle, teknik Türkçe terminoloji, spesifik tıbbi detaylar. "
        "Bu metin bir retrieval sistemi için kullanılacak — gerçekmiş gibi yaz."
    )
    user_prompt = (
        f"Soru: {soru}\n"
        f"İlaç: {ilac_str}\n"
        f"{('Konu: ' + tur_ipucu) if tur_ipucu else ''}\n\n"
        "Bu soruya yanıt verecek kısa bir KÜB paragrafı yaz (2-3 cümle):"
    )

    try:
        # HyDE her zaman yerel/bulut OpenAI-uyumlu endpoint'e gider (Claude API'ya değil)
        hyde_client = openai.OpenAI(
            base_url=os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1"),
            api_key=os.getenv("LM_STUDIO_API_KEY", "local"),
        )
        hyde_model = os.getenv("LM_STUDIO_MODEL", DEFAULT_LOCAL_MODEL)
        response = hyde_client.chat.completions.create(
            model=hyde_model,
            max_tokens=200,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        hyde_text = response.choices[0].message.content.strip()

        logger.debug(f"HyDE doc üretildi ({len(hyde_text)} karakter): {hyde_text[:80]}...")
        return hyde_text

    except Exception as e:
        logger.warning(f"HyDE oluşturulamadı (devam ediliyor): {e}")
        return None


# ---------------------------------------------------------------------------
# Retrieval katmanı
# ---------------------------------------------------------------------------

def _retrieve_chunks(
    augmented: AugmentedQuery,
    hyde_sorgu: str | None = None,
) -> list[RetrievedChunk]:
    """
    AugmentedQuery'deki planları çalıştırır, chunk'ları toplar ve sıralar.

    Faz 11 stratejisi (section-aware + reranking):
      1. Her plan için: priority sections k=8, secondary sections k=4 (batch_search)
      2. Kritik maddeler (4.3, 4.5, 4.6) için patient_flags filtresi uygulanmaz
      3. Sonuçları dedup + skor filtresi
      4. Cross-encoder reranker ile yeniden sırala → top MAX_CHUNKS_PER_QUERY
    """
    seen_ids: set[str] = set()
    seen_full_keys: set[str] = set()
    tum_chunklar: list[RetrievedChunk] = []

    KRITIK_MADDELER = {"4.3", "4.4", "4.5", "4.6"}  # 4.4 = special warnings (always retrieve)

    def _ekle(r: dict) -> None:
        chunk_id = r.get("chunk_id", "")
        if chunk_id in seen_ids or r["score"] < MIN_SCORE_THRESHOLD:
            return
        seen_ids.add(chunk_id)
        chunk = _to_retrieved_chunk(r)

        full_key = f"{chunk.ilac_adi}|{chunk.madde_no}|{chunk.alt_madde}"
        if full_key in seen_full_keys:
            return
        seen_full_keys.add(full_key)

        # Base chunk: aynı ilac+madde için sub-chunk zaten geldiyse atla
        if not chunk.alt_madde:
            madde_prefix = f"{chunk.ilac_adi}|{chunk.madde_no}|"
            if any(k.startswith(madde_prefix) and k != full_key for k in seen_full_keys):
                return

        tum_chunklar.append(chunk)

    # Doz sorguları biraz daha fazla chunk gerektirebilir ama baseline 15'e çıkarıldı
    k_prio = 20 if "doz" in augmented.soru_turleri else 15

    for plan in augmented.arama_planlari:
        # Bölüm listesini ikiye böl: önce 2 = priority, geri kalanı = secondary
        priority = plan.madde_onceligi[:2]
        secondary = [m for m in plan.madde_onceligi[2:] if m not in priority]

        # Kritik maddeler patient_flags'ten muaf
        crit_priority = [m for m in priority if m in KRITIK_MADDELER]
        norm_priority = [m for m in priority if m not in KRITIK_MADDELER]

        # 1. Geçiş: priority sections — hybrid (BM25 + semantik, RRF)
        # Kritik maddeler (4.3/4.4/4.5/4.6) flags filtresi almaz
        for sections, use_flags in [
            (crit_priority, False),
            (norm_priority, True),
        ]:
            if sections:
                raw = hybrid_batch_search(
                    query=plan.sorgu,
                    priority_sections=sections,
                    secondary_sections=[],
                    filter_ilac=[plan.ilac_adi] if plan.ilac_adi else None,
                    filter_patient_flags=plan.patient_flags if use_flags and plan.patient_flags else None,
                    k_priority=k_prio,
                    k_secondary=0,
                )
                for r in raw:
                    _ekle(r)

        # 2. Geçiş: secondary sections — hybrid
        if secondary:
            raw_sec = hybrid_batch_search(
                query=plan.sorgu,
                priority_sections=secondary,
                secondary_sections=[],
                filter_ilac=[plan.ilac_adi] if plan.ilac_adi else None,
                filter_patient_flags=plan.patient_flags if plan.patient_flags else None,
                k_priority=10,
                k_secondary=0,
            )
            for r in raw_sec:
                _ekle(r)

        # 3. HyDE geçişi — varsayımsal KÜB metni ile ek semantik retrieval
        if hyde_sorgu:
            hyde_sections = plan.madde_onceligi[:3] if plan.madde_onceligi else []
            if hyde_sections:
                raw_hyde = hybrid_batch_search(
                    query=hyde_sorgu,
                    priority_sections=hyde_sections,
                    secondary_sections=[],
                    filter_ilac=[plan.ilac_adi] if plan.ilac_adi else None,
                    filter_patient_flags=None,  # HyDE geçişi flags filtresi almaz
                    k_priority=3,   # Phase-1B: HyDE chunk cap — 8→3 (CU şişmesini önler)
                    k_secondary=0,
                )
                for r in raw_hyde:
                    _ekle(r)

    # İlaç adı boosting: hedef ilaçla exact match eden chunk'lar +0.05 skor alır
    # Bu, reranker'a giden aday havuzunu iyileştirir (sıralama reranker'a bırakılır)
    hedef_ilaclar = {
        normalize_drug_name(p.ilac_adi)
        for p in augmented.arama_planlari
        if p.ilac_adi
    }
    if hedef_ilaclar:
        for c in tum_chunklar:
            if normalize_drug_name(c.ilac_adi) in hedef_ilaclar:
                c.score = min(1.0, c.score + 0.05)

    # Skor'a göre azalan sırala
    tum_chunklar.sort(key=lambda x: x.score, reverse=True)

    # Reranking: cross-encoder ile top-30'u yeniden sırala
    RERANK_CANDIDATE_POOL = POLICY.rerank_pool_size
    if len(tum_chunklar) > 1:
        candidates = [
            {
                "chunk_id": c.chunk_id,
                "ilac_adi": c.ilac_adi,
                "madde_no": c.madde_no,
                "madde_baslik": c.madde_baslik,
                "icerik": c.icerik,
                "score": c.score,
                "sayfa": c.sayfa,
                "kaynak_dosya": c.kaynak_dosya,
                "alt_madde": c.alt_madde,
            }
            for c in tum_chunklar[:RERANK_CANDIDATE_POOL]
        ]
        reranked = rerank(augmented.ozgun_soru, candidates, top_k=MAX_CHUNKS_PER_QUERY)
        result = [_to_retrieved_chunk(r) for r in reranked]
        return result

    return tum_chunklar[:MAX_CHUNKS_PER_QUERY]


def _to_retrieved_chunk(raw: dict) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=raw.get("chunk_id", ""),
        ilac_adi=raw.get("ilac_adi", ""),
        madde_no=raw.get("madde_no", ""),
        madde_baslik=raw.get("madde_baslik", ""),
        icerik=raw.get("icerik", ""),
        score=raw.get("score", 0.0),
        sayfa=raw.get("sayfa", 0),
        kaynak_dosya=raw.get("kaynak_dosya", ""),
        alt_madde=raw.get("alt_madde", ""),
    )


# ---------------------------------------------------------------------------
# Prompt oluşturma
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Unified system prompt — Claude ve yerel modeller aynı kuralları kullanır.
# Kaynak önceliği: KÜB > Graf > CYP450
# Kaynak format: [İlaç Adı | Madde X.X]  (sayfa no hallüsinasyon riski — kaldırıldı)
# BİLGİ YOK format: "[BİLGİ YOK: Bu konu incelenen KÜB belgelerinde yer almamaktadır.]"
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT_BASE = """Sen bir klinik eczacı yapay zeka asistanısın. Sağlık profesyonellerine
KÜB (Kısa Ürün Bilgisi) belgelerine, ilaç etkileşim grafına ve CYP450 analizine dayalı,
hasta-spesifik yanıtlar sunuyorsun.

KONTRENDİKASYON KURALI (MUTLAK):
"Kontrendikedir" veya "kullanılmamalıdır" ifadelerini YALNIZCA KÜB Madde 4.3 metninde
AÇIKÇA bu hastalık/durum için yazıyorsa kullan.
Madde 4.2'de doz azaltımı veya 4.4'te "dikkatli kullanılmalıdır" yazıyorsa:
→ "Dikkatli kullanılmalıdır, doz ayarı gerekebilir." veya "Yakın izlem önerilir." kullan.

YANIT TAMAMLIĞI KURALI:
Kontrendikasyon veya kısıtlama bildirirken YALNIZCA "kontrendikedir" demek YETERSİZDİR.
Bağlamda bilgi varsa şunları mutlaka ekle:
1. EŞİK/KOŞUL: Hangi GFR değerinde, hangi Child-Pugh sınıfında, hangi dozda kontrendike?
   Örn: "GFR <30 mL/dak altında" veya "Child-Pugh B/C'de" gibi spesifik değer.
2. TİP: MUTLAK mı (Madde 4.3 — hiçbir koşulda) yoksa GÖRECELI mi (Madde 4.4 — dikkatli kullan)?
3. KLİNİK YOL: Bağlamda bir ilaç adı AÇIKÇA yazıyorsa onu aktar. Bağlamda ilaç adı geçmiyorsa
   HİÇBİR spesifik ilaç adı, ilaç sınıfı veya doz önerisi yazma.
   "DMAH", "metildopa", "heparin" vb. bağlamda yoksa YASAKTIR.

BAĞLAM KAYNAK ÖNCELİĞİ:
1. İLGİLİ KÜB BİLGİLERİ (en güvenilir — KÜB belgelerinden alınmıştır)
2. GRAF VERİTABANI BULGULARI (Neo4j etkileşim grafı)
3. OTOMATİK CYP450 ENZİM ANALİZİ (KÜB Madde 4.5'ten türetilmiştir)
Çakışma halinde KÜB'ü önceliklendir. Tüm bölümlerde bilgi yoksa "[BİLGİ YOK]" yaz.

MUTLAK KURALLAR:
1. Yalnızca yukarıdaki bağlam bölümlerinde AÇIKÇA yazan bilgileri yaz. Eğitim
   verilerinden hiçbir bilgi, doz, mekanizma veya ilaç adı ekleme.
2. KAYNAK ETİKETİ ZORUNLU: Her tıbbi iddia içeren cümle bir kaynak etiketine bağlı olmalı.
   KÜB → [İlaç Adı | Madde X.X]  |  Graf → [Graf]  |  CYP450 → [CYP450]
   Kaynak etiketi olmayan tıbbi iddia cümlesi YASAKTIR.
3. "Güvenlidir", "zararsızdır", "sorun yoktur" gibi mutlak ifadeler KULLANMA.
4. Bilgi yoksa: "[BİLGİ YOK: Bu konu incelenen KÜB belgelerinde yer almamaktadır.]"
5. Kritik uyarıları (4.3 kontrendikasyon, ciddi etkileşim, 4.4/4.8 uyarıları) öne çıkar.
6. Yanıtını Türkçe ver. Kesin tıbbi tavsiye verme — klinik karar hekimindir.
7. CYP450 MEKANİZMASI KURALI: CYP450 bölümünde yazan inhibisyon/indüksiyon/substrat
   bilgisini AYNEN aktar. Bağlamda yazılmayan ek metabolizma yorumu veya sonuç çıkarımı
   EKLEME. CYP450 bilgisi her zaman [CYP450] etiketi ile işaretlenmeli.
8. BİLGİ YOK KURALI: İlgili KÜB bölümü bağlamda yoksa veya soruyla ilgili spesifik bilgi
   içermiyorsa, ilgili cümle yerine "[BİLGİ YOK: ...]" yaz. Yorum veya tahminde bulunma.

YANIT FORMATI (ZORUNLU):
## SONUÇ bölümünü 3 katman hâlinde yaz — her katman etiketiyle başlar:

**[KÜB Aktarımı]**
KÜB belgelerindeki ilgili bilgileri doğrudan aktar.
Her cümle/madde bir KÜB kaynağına bağlı: [İlaç | Madde X.X]
Mümkünse KÜB'ün kendi ifadesini kullan — yorum veya çıkarım ekleme.
Doz tabloları, yan etki listeleri, kontrendikasyon maddeleri burada aktarılabilir.

**[Sistem Tespitleri]** *(Graf/CYP/Lab bulgusu varsa — yoksa bu başlığı yazma)*
Graf/CYP450/kümülatif risk bulgularını "tespit edildi / saptandı / gözlemlendi" diliyle yaz.
[Graf] ve [CYP450] etiketleri zorunlu. Yorum değil, bulgu.

**[Değerlendirme]**
Yukarıdaki KÜB verisi ve sistem tespitlerinden türetilen 1-2 cümle klinik sonuç.
Hasta-spesifik, net, soruya doğrudan yanıt.

## UYARI
[Klinik izlem önerileri. Son cümle: "Klinik karar hekimindir."]

NOT: ## KAYNAKLAR bölümünü YAZMA — bu bölüm sistem tarafından otomatik oluşturulur.

YASAK DAVRANIŞLAR:
- Sorulan ilaç dışında başka bir ilacın bilgilerini sunma.
- Bağlamda geçmeyen kontrendikasyon, doz veya yan etki uydurmak.
- Prompt metnini (## başlıkları, talimatları) yanıta kopyalamak.
- Bağlamda olmayan kaynak göstermek.
- Kaynak etiketi olmadan tıbbi iddia cümlesi yazmak.
- [KÜB Aktarımı] katmanına yorum veya çıkarım eklemek — bu katman yalnızca KÜB metni.
- Bağlamda adı AÇIKÇA GEÇMEYEN bir ilacı alternatif olarak önermek — MUTLAK YASAK.
  Bağlamda geçmeyen hiçbir ilaç adı, etken madde, ilaç sınıfı yazılamaz.
- ## KAYNAKLAR bölümü yazmak — bu bölüm sistem tarafından otomatik oluşturulur."""

SYSTEM_PROMPT = _SYSTEM_PROMPT_BASE  # Claude API için (system role'e verilir)

LOCAL_SYSTEM_PROMPT = _SYSTEM_PROMPT_BASE  # Yerel LLM için (user message başına eklenir)


_GUVENLI_PATTERN = re.compile(
    r"güvenlidir|güvenle\s+kullan[ıi]labilir|sorun\s+yoktur|risk\s+ta[sş][ıi]maz"
    r"|herhangi\s+bir\s+risk\s+[yo]k|zararsızdır|endişe\s+yoktur",
    re.IGNORECASE,
)
_GUVENLI_REPLACEMENT = (
    "[SİSTEM DÜZELTMESİ: KÜB verileri bu kombinasyon için spesifik güvenlik onayı "
    "içermemektedir. Klinik değerlendirme önerilir.]"
)


# ---------------------------------------------------------------------------
# FIX-1 — Hasta profili flag-drug relevance filtresi
# ---------------------------------------------------------------------------

_FLAG_DRUG_RELEVANCE: dict[str, dict] = {
    "renal": {
        "sections": {"4.2", "4.3"},
        "keywords": ["böbrek", "renal", "gfr", "kreatinin", "klirens", "diyaliz", "clcr", "egfr"],
    },
    "hepatic": {
        "sections": {"4.2", "4.3"},
        "keywords": ["karaciğer", "hepatik", "child-pugh", "siroz", "hepatik", "bilirubin"],
    },
    "geriatric": {
        "sections": {"4.2"},
        "keywords": ["yaşlı", "geriyatrik", "65 yaş", "ileri yaş", "yaşlılarda"],
    },
}


def _check_flag_relevance(flag: str, chunklar: list) -> bool:
    """
    Retrieval'dan gelen chunk'larda ilgili flag'in KÜB karşılığı var mı kontrol eder.
    True → flag prompt'a dahil edilebilir; False → flag susturulur.
    """
    cfg = _FLAG_DRUG_RELEVANCE.get(flag)
    if not cfg:
        return True  # Bilinmeyen flag — güvenli tarafta kal, dahil et

    target_sections = cfg["sections"]
    keywords = cfg["keywords"]

    for chunk in chunklar:
        madde = getattr(chunk, "madde_no", "") if hasattr(chunk, "madde_no") else chunk.get("madde_no", "")
        icerik = getattr(chunk, "icerik", "") if hasattr(chunk, "icerik") else chunk.get("icerik", "")
        if madde in target_sections:
            icerik_lower = icerik.lower()
            if any(kw in icerik_lower for kw in keywords):
                return True
    return False


def _build_filtered_hasta_ozeti(profil, chunklar: list) -> str:
    """
    Hasta özetini chunk relevance'a göre filtreler.
    Retrieval'da ilaç-spesifik KÜB desteği olmayan flag'ler prompt'a eklenmez;
    bu sayede LLM ilgisiz kontrendikasyon çıktısı üretmez.
    """
    from src.agents.patient_profile import PatientProfile
    if not isinstance(profil, PatientProfile):
        # Fallback: orijinal metin (profil nesnesi yoksa)
        return profil if isinstance(profil, str) else ""

    satirlar = []
    # yas=0 → varsayılan (belirtilmemiş); "Yaş: 0" prompt'a girerse model değer üretebilir
    yas_str = str(profil.yas) if profil.yas and profil.yas > 0 else "belirtilmemiş"
    cinsiyet_str = profil.cinsiyet if profil.cinsiyet and profil.cinsiyet != "belirtilmemiş" else "belirtilmemiş"
    satirlar.append(f"Yaş: {yas_str}, Cinsiyet: {cinsiyet_str}")

    # Böbrek — yalnızca ilacın KÜB'ünde renal bölüm varsa ekle
    if profil.bobrek_yetmezligi:
        if _check_flag_relevance("renal", chunklar):
            satirlar.append(
                f"Böbrek fonksiyonu: GFR={profil.gfr} mL/dak/1.73m² ({profil.bobrek_evresi})"
            )
        else:
            # GFR bilgisini ver ama "yetmezlik" vurgusunu azalt
            satirlar.append(f"Böbrek fonksiyonu: GFR={profil.gfr} mL/dak/1.73m² (Bu ilaç için KÜB'de özel renal kısıt belirtilmemiştir)")
    elif profil.gfr is not None:
        satirlar.append(f"Böbrek fonksiyonu: GFR={profil.gfr} mL/dak/1.73m² (normal sınırlar)")

    # Karaciğer — yalnızca ilacın KÜB'ünde hepatik bölüm varsa ekle
    if profil.karaciger_skoru:
        if profil.karaciger_yetmezligi:
            if _check_flag_relevance("hepatic", chunklar):
                satirlar.append(f"Karaciğer fonksiyonu: Child-Pugh {profil.karaciger_skoru}")
            else:
                satirlar.append(f"Karaciğer fonksiyonu: Child-Pugh {profil.karaciger_skoru} (Bu ilaç için KÜB'de özel hepatik kısıt belirtilmemiştir)")
        else:
            satirlar.append(f"Karaciğer fonksiyonu: Child-Pugh {profil.karaciger_skoru}")

    if profil.gebelik:
        satirlar.append("Durum: GEBELİK")
    if profil.emzirme:
        satirlar.append("Durum: EMZİRİYOR")

    if profil.mevcut_ilaclar:
        satirlar.append(f"Mevcut ilaçlar: {', '.join(profil.mevcut_ilaclar)}")

    if profil.alerjiler:
        satirlar.append(f"Alerjiler: {', '.join(profil.alerjiler)}")

    if profil.endikasyonlar:
        satirlar.append(f"Endikasyonlar: {', '.join(profil.endikasyonlar)}")

    if profil.kilo is not None:
        satirlar.append(f"Kilo: {profil.kilo} kg")

    # Anormal lab değerleri
    anormal = profil.anormal_lab_degerleri
    if anormal:
        lab_str = ", ".join(
            f"{l['param']}={l['deger']} {l['birim']} ({l['durum']})" for l in anormal
        )
        satirlar.append(f"Anormal lab değerleri: {lab_str}")

    # Geriyatrik uyarı — yalnızca ilacın KÜB'ünde geriyatrik bölüm varsa ekle
    if profil.geriyatrik and profil.yas >= 65:
        if _check_flag_relevance("geriatric", chunklar):
            satirlar.append(f"Not: Geriyatrik hasta ({profil.yas} yaş) — geriyatrik doz titrasyon değerlendirmesi gerekebilir")

    if profil.notlar:
        satirlar.append(f"Ek notlar: {profil.notlar}")

    return "\n".join(satirlar)


def validate_response(yanit: str, chunklar: list, soru: str = "") -> str:
    """
    Faz 12 — LLM yanıtı KÜB bağlamıyla doğrular.

    1. "güvenlidir" ve benzeri mutlak ifadeleri sistem uyarısıyla değiştirir.
    2. Kontrendikasyon iddiasını 4.3 chunk içeriğiyle çapraz kontrol eder.
    3. Gerçek post-processor: kaynak etiketi olmayan tıbbi iddia cümlelerini
       [DOĞRULANAMADI] ile işaretler.
    """
    def _validate_kontraendikasyon(yanit: str, chunklar: list, soru: str) -> str:
        _kontra_pattern = re.compile(
            r"kontrendikedir|kontrendikasyon|kullanılmamalıdır",
            re.IGNORECASE,
        )
        if not _kontra_pattern.search(yanit):
            return yanit

        # 4.3 chunk'ı bul
        chunk_43_list = [
            c for c in chunklar
            if (getattr(c, "madde_no", "") if hasattr(c, "madde_no") else c.get("madde_no", "")) == "4.3"
        ]

        if not chunk_43_list:
            logger.warning(
                "[VALIDATE] Yanıtta kontrendikasyon iddiası var ancak Madde 4.3 chunk'u bulunamadı."
            )
            _ASIRI_TAG_NO43 = " [AŞIRI YORUM: Madde 4.3 retrieve edilmedi, kontrendike kanıtlanamıyor]"
            yanit = re.sub(
                r"kontrendikedir",
                "dikkatli kullanılmalıdır" + _ASIRI_TAG_NO43,
                yanit, flags=re.IGNORECASE,
            )
            yanit = re.sub(
                r"kullanılmamalıdır",
                "dikkatli kullanılmalıdır" + _ASIRI_TAG_NO43,
                yanit, flags=re.IGNORECASE,
            )
            return yanit

        # 4.3 içeriğini birleştir
        icerik_43 = " ".join(
            (getattr(c, "icerik", "") if hasattr(c, "icerik") else c.get("icerik", "")).lower()
            for c in chunk_43_list
        )

        # Soru metninden klinik anahtar terimleri çıkar (hastalık/durum adları)
        # Her durum için sinonim listesi: KÜB metinleri aynı kavramı farklı kelimelerle
        # ifade edebilir (örn. "karaciğer yetmezliği" yerine "hepatik hastalık" gibi).
        # 4.3 metninde durum VEYA sinonimlerinden herhangi biri geçiyorsa eşleşmiş say.
        _KLINIK_DURUMLAR_SINONIM: dict[str, list[str]] = {
            "hiperpotasemi":      ["hiperpotasemi", "hiperkalem", "potasyum"],
            "hiperkalemi":        ["hiperkalem", "hiperpotasemi", "potasyum"],
            "potasyum":           ["potasyum", "hiperkalem", "hiperpotasem"],
            "hipopotasemi":       ["hipopotasemi", "hipokalem"],
            "hipokalemi":         ["hipokalem", "hipopotasemi"],
            "böbrek yetmezliği":  ["böbrek", "renal", "kreatinin", "gfr", "klirens",
                                   "diyaliz", "hemodiyaliz", "nefr"],
            "renal yetmezlik":    ["böbrek", "renal", "kreatinin", "gfr", "klirens"],
            "renal":              ["böbrek", "renal", "kreatinin", "gfr"],
            "karaciğer yetmezliği": ["karaciğer", "hepatik", "hepat", "child",
                                      "siroz", "bilirubin", "karaciğer fonksiyon"],
            "hepatik":            ["hepatik", "karaciğer", "hepat", "child", "siroz"],
            "gebelik":            ["gebelik", "hamilelik", "fetal", "embriyo",
                                   "prenatal", "hamile"],
            "hamile":             ["hamile", "gebelik", "fetal"],
            "laktasyon":          ["laktasyon", "emzirme", "anne sütü"],
            "emzir":              ["emzir", "laktasyon", "anne sütü"],
            "hipertansiyon":      ["hipertansiyon", "kan basıncı", "kb"],
            "kalp yetmezliği":    ["kalp yetmezliği", "kardiyak yetmezlik", "konjestif"],
            "diyabet":            ["diyabet", "glukoz", "insülin", "hipoglisemi"],
            "hipoglisemi":        ["hipoglisemi", "glukoz", "kan şekeri"],
            "hiperglisemi":       ["hiperglisemi", "glukoz", "kan şekeri"],
            "alerji":             ["alerji", "hipersensitivite", "anafilaksi", "ürtiker"],
            "hipersensitivite":   ["hipersensitivite", "alerji", "anafilaksi"],
            "üriner":             ["üriner", "idrar", "mesane", "üretral"],
            "enfeksiyon":         ["enfeksiyon", "infeksiyon", "bakteri", "mantar"],
            "trombositopeni":     ["trombositopeni", "trombosit", "plt"],
            "lökopeni":           ["lökopeni", "lökosit", "nötropeni"],
        }
        soru_lower = soru.lower()
        eslesmeyen_durumlar = []
        for durum, sinonimler in _KLINIK_DURUMLAR_SINONIM.items():
            if durum in soru_lower:
                # Durum veya sinonimlerinden herhangi biri 4.3 metninde geçiyorsa eşleşti
                if not any(s in icerik_43 for s in sinonimler):
                    eslesmeyen_durumlar.append(durum)

        if eslesmeyen_durumlar:
            logger.warning(
                "[VALIDATE] Kontrendikasyon iddiası var ancak 4.3 metninde '{}' geçmiyor — "
                "dikkatli kullan + [AŞIRI YORUM] ile düzeltiliyor.",
                ", ".join(eslesmeyen_durumlar),
            )
            _ASIRI_TAG = " [AŞIRI YORUM: Madde 4.3 bu durum için kontrendikasyon içermiyor]"
            yanit = re.sub(
                r"kontrendikedir",
                "dikkatli kullanılmalıdır" + _ASIRI_TAG,
                yanit,
                flags=re.IGNORECASE,
            )
            yanit = re.sub(
                r"kullanılmamalıdır",
                "dikkatli kullanılmalıdır" + _ASIRI_TAG,
                yanit,
                flags=re.IGNORECASE,
            )

        return yanit

    def _tag_unverifiable_sentences(yanit: str, chunklar: list) -> str:
        """
        Kaynak etiketi olmayan tıbbi iddia cümlelerini [DOĞRULANAMADI] ile işaretler.

        Whitelist (etiketlenmez):
          - [BİLGİ YOK], [SİSTEM DÜZELTMESİ], ## başlıklar, kısa cümleler (<35 char)
          - Zaten kaynak etiketi olan cümleler
          - ## KAYNAKLAR ve ## UYARI bölümleri (meta-bölümler)
        """
        # Geçerli kaynak etiketi kalıbı
        _SOURCE_TAG_RE = re.compile(
            r'\[[^\]]+\|\s*Madde\s+[\d.]+[^\]]*\]'   # [İlaç | Madde X.X]
            r'|\[Graf\]'
            r'|\[CYP450\]'
            r'|\[BİLGİ\s*YOK[^\]]*\]'
            r'|\[SİSTEM\s*DÜZELTMESİ[^\]]*\]'
            r'|\[DOĞRULANAMADI\]',
            re.IGNORECASE,
        )

        # Tıbbi iddia anahtar sözcükleri (bu kelimeler varsa cümle kaynak gerektirir)
        _CLAIM_KEYWORDS = [
            "kontrendik", "kullanılmamalı", "kullanılabilir", "doz", " mg", " mcg", " ml",
            "yan etki", "etkileşim", "metaboliz", "inhibis", "indüksi", "substrat",
            "böbrek", "karaciğer", "renal", "hepatik",
            "gebelik", "emzirme", "laktasyon",
            "pediatrik", "geriyatrik",
            "konsantrasyon", "plazma", "biyoyararlanım", "yarı ömür",
            "toksik", "teratojenik", "embriyo",
            "klirens", "gfr", "kreatinin",
            "dikkatli kullanıl", "izlem öneril", "uyarı",
        ]

        # Bağlamdaki ilaç adlarından token seti (prefix eşleşmesi için)
        drug_tokens: set[str] = set()
        for c in chunklar:
            ilac_adi = getattr(c, "ilac_adi", "") if hasattr(c, "ilac_adi") else c.get("ilac_adi", "")
            if ilac_adi:
                first = ilac_adi.upper().split()[0]
                if len(first) >= 4:
                    drug_tokens.add(first)

        # Korunacak bölümler (bu başlıktan sonraki satırlar etiketlenmez)
        _PROTECTED_SECTIONS = {"## KAYNAKLAR", "## UYARI"}
        # Etiketlenmeyecek satır başlangıçları
        _SKIP_LINE_STARTS = ("[BİLGİ YOK", "[SİSTEM", "[DOĞRULANAMADI", "##", "- ", "* ")

        lines = yanit.split("\n")
        result_lines: list[str] = []
        in_protected = False

        for line in lines:
            stripped = line.strip()

            # Bölüm başlığı takibi
            if stripped.startswith("##"):
                in_protected = stripped in _PROTECTED_SECTIONS
                result_lines.append(line)
                continue

            # Korunan bölüm — dokunma
            if in_protected:
                result_lines.append(line)
                continue

            # Boş satır
            if not stripped:
                result_lines.append(line)
                continue

            # Satırı cümlelere böl (nokta/ünlem/soru işareti + boşlukta)
            # (?!\[) — kaynak etiketi "[İlaç | Madde X.X]" öncesinde bölme
            segments = re.split(r'(?<=[.!?])\s+(?!\[)', line)
            processed: list[str] = []

            for seg in segments:
                s = seg.strip()
                if not s:
                    processed.append(seg)
                    continue

                # Whitelist: özel başlangıçlar veya kısa cümle
                if any(s.startswith(p) for p in _SKIP_LINE_STARTS) or len(s) < 35:
                    processed.append(seg)
                    continue

                # Zaten kaynak etiketi var — dokunma
                if _SOURCE_TAG_RE.search(seg):
                    processed.append(seg)
                    continue

                # Tıbbi iddia tespiti
                s_lower = s.lower()
                has_drug = any(tok in s.upper() for tok in drug_tokens)
                has_claim = any(kw in s_lower for kw in _CLAIM_KEYWORDS)

                if has_drug or has_claim:
                    logger.debug("[VALIDATE] Kaynak etiketi yok, etiketleniyor: %s", s[:60])
                    processed.append(seg.rstrip() + " [DOĞRULANAMADI]")
                else:
                    processed.append(seg)

            result_lines.append(" ".join(processed))

        tagged_count = yanit.count("[DOĞRULANAMADI]")
        after = "\n".join(result_lines)
        new_count = after.count("[DOĞRULANAMADI]")
        added = new_count - tagged_count
        if added > 0:
            logger.warning("[VALIDATE] {} cümle [DOĞRULANAMADI] ile işaretlendi.", added)

        return after

    def _validate_numeric_claims(yanit: str, chunklar: list) -> str:
        """
        Sayısal klinik iddia doğrulama — Faz 16+.

        Cevapta geçen spesifik sayısal değerleri (doz, GFR eşiği, lab değeri)
        retrieved chunk'larla karşılaştırır. Hiçbir chunk'ta bulunmayan değer
        içeren cümleler [DOĞRULANAMADI] ile etiketlenir.

        Yakalanan hallüsinasyon örnekleri:
          - "2.5 mg başlangıç dozu önerilir" → KÜB'de yoksa flag
          - "GFR < 30 mL/dak altında kontrendike" → chunk'ta başka eşik varsa flag
          - "kreatinin 1.5 mg/dL üzerinde dikkat" → kaynaklı değilse flag

        Kapsam dışı (false positive riski yüksek):
          - Hasta profili değerleri (GFR=20 soruda geçiyor → flag çıkmamalı)
          - Çok yaygın dozlar (500 mg parasetamol gibi)
        """
        # ── Tüm chunk içeriklerini birleştir (küçük harf) ────────────────
        all_chunk_text = " ".join(
            (getattr(c, "icerik", "") if hasattr(c, "icerik") else c.get("icerik", "")).lower()
            for c in chunklar
        )

        if not all_chunk_text.strip():
            return yanit

        # ── Doz kalıbı: "X mg", "X mcg", "X ml", "X iu", "X mmol" ──────
        _DOZ_PATTERN = re.compile(
            r'\b(\d+(?:[.,]\d+)?)\s*(mg|mcg|ml|iu|mmol|μg|µg|ng|mg/ml|mg/dl|mek)\b',
            re.IGNORECASE,
        )

        # ── GFR eşik kalıbı: "GFR < 30", "GFR 30", "GFR ≥ 60" ──────────
        _GFR_PATTERN = re.compile(
            r'\b(?:gfr|egfr|kreatinin\s+klerensi?)\s*[<>≤≥=]?\s*(\d+)',
            re.IGNORECASE,
        )

        # Soru metnindeki sayıları topla — bunlar hasta profili değeri, flag çıkmamalı
        soru_numbers: set[str] = set()
        for m in re.finditer(r'\b\d+(?:[.,]\d+)?\b', soru):
            soru_numbers.add(m.group().replace(',', '.'))

        # ── Kaynaklı cümle için alıntılanan bölüm metnini çıkar ───────────────
        _CITED_MADDE_RE = re.compile(
            r'\[.+?\|\s*(?:KÜB\s+)?Madde\s+([\d.]+)',
            re.IGNORECASE,
        )

        def _get_cited_section_text(seg: str) -> str | None:
            """
            Segment içindeki [İlaç | Madde X.X] etiketinden madde numarasını çıkarır
            ve o maddeye ait chunk metinlerini birleştirir. Etiket yoksa None döner.
            """
            m = _CITED_MADDE_RE.search(seg)
            if not m:
                return None
            cited_madde = m.group(1).strip()  # örn. "4.2"
            section_parts = []
            for c in chunklar:
                madde = (
                    getattr(c, "madde_no", None)
                    if hasattr(c, "madde_no")
                    else c.get("madde_no", "")
                )
                if madde and madde.strip() == cited_madde:
                    txt = (
                        getattr(c, "icerik", "")
                        if hasattr(c, "icerik")
                        else c.get("icerik", "")
                    )
                    section_parts.append(txt.lower())
            # None  → citation etiketi yok (geniş mod, tüm chunk'lar)
            # ""    → etiketi var ama bölüm retrieve edilmemiş (doğrulama atla)
            # "..." → etiketi var ve bölüm metni mevcut (sıkı mod)
            return " ".join(section_parts) if section_parts else ""

        # ── Cümle bazlı kontrol ──────────────────────────────────────────
        _SKIP_STARTS = ("[BİLGİ YOK", "[SİSTEM", "[DOĞRULANAMADI", "##", "- ", "* ", "[")
        _SPECIAL_TAGS_RE = re.compile(
            r'\[Graf\]|\[CYP450\]|\[BİLGİ\s*YOK[^\]]*\]'
            r'|\[SİSTEM\s*DÜZELTMESİ[^\]]*\]|\[DOĞRULANAMADI\]',
            re.IGNORECASE,
        )
        _PROTECTED_SECTIONS_NUM = {"## KAYNAKLAR", "## UYARI"}

        lines = yanit.split("\n")
        result_lines: list[str] = []
        in_protected = False
        flagged_count = 0

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("##"):
                in_protected = stripped in _PROTECTED_SECTIONS_NUM
                result_lines.append(line)
                continue
            if in_protected or not stripped:
                result_lines.append(line)
                continue

            segments = re.split(r'(?<=[.!?])\s+(?!\[)', line)
            processed: list[str] = []

            for seg in segments:
                s = seg.strip()
                if not s or len(s) < 30:
                    processed.append(seg)
                    continue
                if any(s.startswith(p) for p in _SKIP_STARTS):
                    processed.append(seg)
                    continue
                if _SPECIAL_TAGS_RE.search(seg):
                    # Graf/CYP/BİLGİ YOK/SİSTEM etiketleri → sayısal kontrol atla
                    processed.append(seg)
                    continue

                # Alıntılanan bölümü belirle:
                # - Madde etiketi varsa → o bölümün metnine karşı doğrula (sıkı mod)
                # - Etiket yoksa → tüm chunk metni (geniş mod)
                cited_text = _get_cited_section_text(seg)
                # None  → citation tag yok → geniş mod (tüm chunk'lar)
                # ""    → tag var ama bölüm retrieve edilmemiş → skip (doğrulama yapılamaz)
                # "..." → tag var, bölüm mevcut → sıkı mod
                if cited_text is not None and cited_text == "":
                    # Alıntılanan bölüm retrieve edilmemiş — false positive riski yüksek, atla
                    processed.append(seg)
                    continue

                has_citation = cited_text is not None
                check_text = cited_text if has_citation else all_chunk_text

                def _number_in_text(num_str: str, unit: str, text: str) -> bool:
                    # Her iki ondalık notasyonu dene (KÜB Türkçe virgül, Haiku nokta kullanabilir)
                    num_dot   = num_str.replace(',', '.')   # 7,5 → 7.5
                    num_comma = num_str.replace('.', ',')   # 7.5 → 7,5
                    unit_l    = unit.lower().strip()
                    patterns  = [
                        f"{num_dot} {unit_l}",    # "7.5 mg"
                        f"{num_comma} {unit_l}",  # "7,5 mg"
                        f"{num_dot}{unit_l}",     # "7.5mg" (boşluksuz)
                        f"{num_comma}{unit_l}",   # "7,5mg"
                        num_dot,                  # sadece sayı (geniş kontrol)
                        num_comma,
                    ]
                    return any(p in text for p in patterns)

                s_lower = s.lower()
                flagged = False

                # Doz kontrolü
                for m in _DOZ_PATTERN.finditer(s_lower):
                    num, unit = m.group(1), m.group(2)
                    if num in soru_numbers:
                        continue  # Hasta profili değeri
                    if not _number_in_text(num, unit, check_text):
                        mode = "alıntılanan bölümde" if has_citation else "chunk'larda"
                        logger.warning(
                            "[VALIDATE-NUM] Doz değeri %s bulunamadı: %s %s — cümle: %s",
                            mode, num, unit, s[:80],
                        )
                        flagged = True
                        break

                # GFR eşik kontrolü
                if not flagged:
                    for m in _GFR_PATTERN.finditer(s_lower):
                        num = m.group(1)
                        if num in soru_numbers:
                            continue
                        if not _number_in_text(num, "", check_text):
                            mode = "alıntılanan bölümde" if has_citation else "chunk'larda"
                            logger.warning(
                                "[VALIDATE-NUM] GFR eşiği %s bulunamadı: %s — cümle: %s",
                                mode, num, s[:80],
                            )
                            flagged = True
                            break

                if flagged:
                    processed.append(seg.rstrip() + " [DOĞRULANAMADI]")
                    flagged_count += 1
                else:
                    processed.append(seg)

            result_lines.append(" ".join(processed))

        if flagged_count > 0:
            logger.warning(
                "[VALIDATE-NUM] {} sayısal iddia doğrulanamadı (doz/GFR chunk'larda yok).",
                flagged_count,
            )

        return "\n".join(result_lines)

    # ────────────────────────────────────────────────────────────────────────
    def _validate_cyp_direction(yanit: str, chunklar: list) -> str:
        """
        Rule 4 — CYP mekanizması → etki yönü doğrulama.

        4.5 chunk metnindeki enzim rolü ile yanıttaki düzey değişim yönünü karşılaştırır:
          - İnhibitör  → hedef ilaç plazma düzeyi ARTMALI  (artar/yükselir)
          - İndükleyici → hedef ilaç plazma düzeyi AZALMALI (azalır/düşer)

        Yanlış yön ifadesi [DOĞRULANAMADI-CYP] ile işaretlenir.
        """
        # [CYP450] etiketli cümle yoksa atla
        if "[CYP450]" not in yanit.upper().replace(" ", "").replace("\n", ""):
            if not re.search(r'\[CYP450\]', yanit, re.IGNORECASE):
                return yanit

        # 4.5 chunk metnini birleştir
        cyp_chunk_text = " ".join(
            (getattr(c, "icerik", "") if hasattr(c, "icerik") else c.get("icerik", "")).lower()
            for c in chunklar
            if (getattr(c, "madde_no", "") if hasattr(c, "madde_no") else c.get("madde_no", "")) == "4.5"
        )
        if not cyp_chunk_text.strip():
            return yanit

        is_inhibitor = bool(re.search(r'inhibit(?:ör|ör[üu]|or)', cyp_chunk_text, re.IGNORECASE))
        is_inducer   = bool(re.search(r'indükl?e(?:yici|yici)', cyp_chunk_text, re.IGNORECASE))

        if not is_inhibitor and not is_inducer:
            return yanit  # Yalnızca substrat — yön doğrulaması gerekmez

        _ARTAR_RE  = re.compile(r'düzey[i]?\s*(?:artar|artabilir|yükselir|yükselme)', re.IGNORECASE)
        _AZALIR_RE = re.compile(r'düzey[i]?\s*(?:azalır|azalabilir|düşer|düşme)', re.IGNORECASE)

        lines   = yanit.split("\n")
        changed = False

        for i, line in enumerate(lines):
            if not re.search(r'\[CYP450\]', line, re.IGNORECASE):
                continue
            line_artar  = bool(_ARTAR_RE.search(line))
            line_azalir = bool(_AZALIR_RE.search(line))

            if is_inhibitor and line_azalir and not line_artar:
                logger.warning(
                    "[VALIDATE-CYP] İnhibitör + 'düzeyi azalır' çelişkisi: %s", line[:80]
                )
                lines[i] = line.rstrip() + " [DOĞRULANAMADI-CYP: inhibitör → düzey artmalı]"
                changed = True

            elif is_inducer and line_artar and not line_azalir:
                logger.warning(
                    "[VALIDATE-CYP] İndükleyici + 'düzeyi artar' çelişkisi: %s", line[:80]
                )
                lines[i] = line.rstrip() + " [DOĞRULANAMADI-CYP: indükleyici → düzey azalmalı]"
                changed = True

        if changed:
            logger.warning("[VALIDATE-CYP] CYP yön uyumsuzluğu düzeltildi.")

        return "\n".join(lines)

    # ────────────────────────────────────────────────────────────────────────
    def _enforce_verdict_alignment(yanit: str, chunklar: list, soru: str) -> str:
        """
        Rule 5 — Verdict alignment: modelin ## SONUÇ cümlesi ile bağlam
        tarafından desteklenen şiddet seviyesini hizalar.

        Desteklenen seviyeler (1→4, yüksek = daha kısıtlayıcı):
          1 = GÜVENLİ / dikkat gerektirmiyor
          2 = DİKKATLİ_KULLANIM (Madde 4.4)
          3 = ÖNERİLMEZ (4.4 şiddetli uyarı, kullanılmamalı tavsiyesi)
          4 = KONTREDİKE (Madde 4.3 açık kontrendikasyon)

        Model, bağlamın desteklediğinden DAHA YÜKSEK seviyede verdict
        veriyorsa [AŞIRI YORUM] ile işaretlenir ve otomatik düşürülür.
        """
        def _icerik(c) -> str:
            return (getattr(c, "icerik", "") if hasattr(c, "icerik") else c.get("icerik", "")).lower()
        def _madde(c) -> str:
            return getattr(c, "madde_no", "") if hasattr(c, "madde_no") else c.get("madde_no", "")

        icerik_43 = " ".join(_icerik(c) for c in chunklar if _madde(c) == "4.3")
        icerik_44 = " ".join(_icerik(c) for c in chunklar if _madde(c) == "4.4")
        soru_lower = soru.lower()

        # Bağlamın desteklediği max seviyeyi belirle
        _KONTRE_ANAHTAR = re.compile(
            r"kontrendikedir|kontrendike|kullanılmamalı|verilmemeli|uygulanmamalı",
            re.IGNORECASE,
        )
        _DIKKATLI_ANAHTAR = re.compile(
            r"dikkatli|izlem|takip|önlem|uyarı|dozayar|doz\s+azalt",
            re.IGNORECASE,
        )

        has_43 = bool(icerik_43.strip())
        kontre_in_43  = has_43 and bool(_KONTRE_ANAHTAR.search(icerik_43))
        dikkatli_in_44 = bool(_DIKKATLI_ANAHTAR.search(icerik_44))

        # Soruda belirtilen klinik durumun 4.3 metninde geçip geçmediğini kontrol et
        # (zaten _validate_kontraendikasyon'da da yapılıyor ama burada verdict seviyesi için)
        _RENAL_KWORDS    = ["böbrek", "renal", "gfr", "kreatinin", "diyaliz"]
        _HEPATIK_KWORDS  = ["karaciğer", "hepatik", "siroz", "child"]
        _GEBE_KWORDS     = ["gebelik", "hamile", "fetal"]
        _EMZIR_KWORDS    = ["emzir", "laktasyon"]

        _KLINIK_GRUPLARI = [_RENAL_KWORDS, _HEPATIK_KWORDS, _GEBE_KWORDS, _EMZIR_KWORDS]

        soru_klinik_gruplari = [
            grp for grp in _KLINIK_GRUPLARI
            if any(k in soru_lower for k in grp)
        ]

        # 4.3 kontre var ama soruda belirtilen klinik grubun 4.3'te karşılığı yok?
        kontre_destek = False
        if kontre_in_43:
            if not soru_klinik_gruplari:
                kontre_destek = True  # Klinik grup belirtilmemiş → 4.3 kontreyi genel kabul et
            else:
                # En az bir grubun sözcüklerinden birinin 4.3'te geçmesi yeterli
                kontre_destek = any(
                    any(k in icerik_43 for k in grp)
                    for grp in soru_klinik_gruplari
                )

        # Desteklenen max seviye
        if kontre_destek:
            max_desteklenen = 4  # KONTREDİKE
        elif dikkatli_in_44 or (has_43 and kontre_in_43 and not kontre_destek):
            max_desteklenen = 2  # DİKKATLİ
        else:
            max_desteklenen = 2  # default — bilgi eksikse dikkatli varsay

        # Modelin ilk SONUÇ cümlesindeki verdict seviyesini bul
        sonuc_match = re.search(
            r'##\s*SONU[ÇC].*?\n(.*?)(?:\n|$)', yanit, re.IGNORECASE
        )
        if not sonuc_match:
            return yanit
        ilk_cumle = sonuc_match.group(1).strip()

        model_kontre   = bool(_KONTRE_ANAHTAR.search(ilk_cumle))
        model_onerulmez = bool(re.search(r'önerilmez|önerilmemeli', ilk_cumle, re.IGNORECASE))
        # model_dikkatli = bool(_DIKKATLI_ANAHTAR.search(ilk_cumle))

        if model_kontre:
            model_seviye = 4
        elif model_onerulmez:
            model_seviye = 3
        else:
            model_seviye = 2

        # Aşırı yorum var mı?
        if model_seviye > max_desteklenen:
            logger.warning(
                "[VALIDATE-VERDICT] Aşırı yorum: model=%d, bağlam_max=%d — ilk cümle: %s",
                model_seviye, max_desteklenen, ilk_cumle[:80],
            )
            # İlk SONUÇ cümlesini [AŞIRI YORUM] ile işaretle — _validate_kontraendikasyon
            # zaten global re.sub yapıyor; burada sadece verdict-level uyumsuzluğunu logla
            # ve SONUÇ satırına ek not ekle
            yanit = yanit.replace(
                ilk_cumle,
                ilk_cumle.rstrip() + " [AŞIRI YORUM: bağlam bu şiddet seviyesini desteklemiyor]",
                1,
            )

        return yanit

    # ── 1. "Güvenlidir" yasağı ───────────────────────────────────────────────
    yanit = _GUVENLI_PATTERN.sub(_GUVENLI_REPLACEMENT, yanit)

    # ── 2. Kontrendikasyon guardrail (FIX-2 + FIX-3) ────────────────────────
    yanit = _validate_kontraendikasyon(yanit, chunklar, soru)

    # ── 3. Kaynak etiketi olmayan tıbbi iddia cümlelerini işaretle ───────────
    yanit = _tag_unverifiable_sentences(yanit, chunklar)

    # ── 4. Sayısal klinik iddia doğrulama (doz/GFR hallüsinasyon tespiti) ────
    yanit = _validate_numeric_claims(yanit, chunklar)

    # ── 5. CYP mekanizması yön doğrulama (inhibitör↑ / indükleyici↓) ─────────
    yanit = _validate_cyp_direction(yanit, chunklar)

    # ── 6. Verdict alignment (model severity > bağlam desteği → [AŞIRI YORUM]) ─
    yanit = _enforce_verdict_alignment(yanit, chunklar, soru)

    # ── 7. Format yapısal kontrolü — [KÜB Aktarımı] ve KÜB kaynak etiketi ─────
    yanit = _validate_format_structure(yanit)

    return yanit


def _validate_format_structure(yanit: str) -> str:
    """
    3-katman format yapısal kontrolü:
    - ## SONUÇ bölümünde [KÜB | Madde X.X] formatında en az 1 kaynak etiketi var mı?
    - [DOĞRULANAMADI] sayısı eşiği: 3+ ise uyarı logu at
    - Format başlıkları ([KÜB Aktarımı], [Sistem Tespitleri], [Değerlendirme]) mevcut mu?

    Şimdilik tespit + uyarı; gelecek sprint'te retry mekanizması eklenebilir.
    """
    if "## SONUÇ" not in yanit:
        return yanit

    # SONUÇ bölümünü ayır
    start = yanit.index("## SONUÇ")
    end_match = __import__("re").search(r"\n## ", yanit[start + 8:])
    sonuc = yanit[start: start + 8 + end_match.start()] if end_match else yanit[start:]

    # Kontrol 1: KÜB kaynak etiketi var mı?
    kub_tag_re = __import__("re").compile(r"\[.+?\|\s*Madde\s*\d+[\.\d]*\]", __import__("re").IGNORECASE)
    if not kub_tag_re.search(sonuc):
        logger.warning("[FORMAT] ## SONUÇ'ta KÜB kaynak etiketi ([İlaç | Madde X.X]) bulunamadı — format kuralı ihlali")

    # Kontrol 2: [DOĞRULANAMADI] yoğunluğu
    dogru_count = yanit.count("[DOĞRULANAMADI]") + yanit.count("[DOĞRULANAMADI-")
    if dogru_count >= 3:
        logger.warning("[FORMAT] {} adet [DOĞRULANAMADI] etiketi — yanıt kalitesi düşük, kaynak atfı yetersiz", dogru_count)

    # Kontrol 3: 3-katman başlıkları var mı? (opsiyonel — debug logu sadece)
    _re = __import__("re")
    has_kub = bool(_re.search(r"\[KÜB Aktarımı\]|\[KUB Aktarimi\]|KÜB Aktarımı", sonuc, _re.IGNORECASE))
    has_deg = bool(_re.search(r"\[Değerlendirme\]|\[Degerlendirme\]|Değerlendirme\]", sonuc, _re.IGNORECASE))
    if not has_kub or not has_deg:
        logger.debug("[FORMAT] 3-katman başlıkları eksik — KÜB Aktarımı:{} Değerlendirme:{}", has_kub, has_deg)

    return yanit


# ---------------------------------------------------------------------------
# Answer Calibration Layer — pre-LLM klinik karar kalibrasyonu
# ---------------------------------------------------------------------------

# Genişletilmiş klinik durum listesi — 4.3 eşleşme kontrolü için
_KLINIK_DURUMLAR_EXTENDED = [
    "hiperpotasemi", "hiperkalemi", "potasyum",
    "hipopotasemi", "hipokalemi",
    "böbrek yetmezliği", "renal yetmezlik", "renal", "böbrek",
    "karaciğer yetmezliği", "hepatik", "karaciğer", "siroz",
    "gebelik", "hamile", "laktasyon", "emzir",
    "hipertansiyon", "kalp yetmezliği", "kardiyak",
    "diyabet", "hipoglisemi", "hiperglisemi",
    "alerji", "hipersensitivite",
    "üriner", "enfeksiyon", "trombositopeni", "lökopeni",
    # Yeni eklenenler — dışarıdan review + Q28 analizi
    "feokromasitoma", "miyastenia gravis", "myasteni",
    "parkinson", "epilepsi", "lupus", "porfiri",
    "tirotoksikoz", "hipertiroidi", "hipotiroid",
    "astım", "bronkospazm", "koah",
    "miyopati", "rabdomiyoliz",
    "tromboz", "pulmoner emboli",
    "qrs", "qt uzaması", "aritmi",
    "aktif ülser", "gastrointestinal kanama", "kanama",
]

_KONTRENDIKE_RE = re.compile(
    r"kontrendikedir|kontrendike|kullanılmamalıdır|kullanılmaz|verilmemelidir"
    r"|kullanımı\s+kontrendike",
    re.IGNORECASE,
)
_DIKKATLI_RE = re.compile(
    r"dikkatli\s+kullan|ihtiyatla\s+kullan|özen\s+göster|yakın\s+izlem"
    r"|dikkatle\s+kullan|kullanılmalıdır.*dikkat",
    re.IGNORECASE,
)


def _calibrate_clinical_severity(
    chunklar: list,
    soru: str,
    soru_turleri: list[str],
) -> str:
    """
    Getirilen chunk'lardan LLM öncesi deterministik klinik karar etiketi üretir.

    Kontrendikasyon veya doz sorularında:
    - 4.3 bölümü sorudaki klinik durumu içeriyorsa → KONTREDİKE
    - 4.3 yok / durumu içermiyor, 4.4 dikkatli kullanım diyorsa → DİKKATLİ_KULLANIM
    - 4.2 bölümü varsa → DOZ_AYARI_GEREKEBİLİR
    - Hiçbiri uymuyorsa → boş string (LLM kendi karar verir)

    Returns: prompt'a eklenecek ÖN DEĞERLENDİRME bloğu (string) veya ""
    """
    ilgili_tipler = {"kontrendikasyon", "doz", "yan_etki", "uyari"}
    if not any(t in soru_turleri for t in ilgili_tipler):
        return ""

    soru_lower = soru.lower()

    # Chunk'ları madde bazlı grupla
    def _icerik(c) -> str:
        return (getattr(c, "icerik", "") if hasattr(c, "icerik") else c.get("icerik", "")).lower()

    def _madde(c) -> str:
        return getattr(c, "madde_no", "") if hasattr(c, "madde_no") else c.get("madde_no", "")

    chunks_43 = [c for c in chunklar if _madde(c) == "4.3"]
    chunks_44 = [c for c in chunklar if _madde(c) == "4.4"]
    chunks_42 = [c for c in chunklar if _madde(c) == "4.2"]

    icerik_43 = " ".join(_icerik(c) for c in chunks_43)
    icerik_44 = " ".join(_icerik(c) for c in chunks_44)
    icerik_42 = " ".join(_icerik(c) for c in chunks_42)

    # Soruda geçen klinik durumları bul
    eslesen_durumlar = [d for d in _KLINIK_DURUMLAR_EXTENDED if d in soru_lower]

    # 1. 4.3 + kontrendike kelime + klinik durum eşleşmesi → KONTREDİKE
    #    ÖNEMLİ: Durum soruda belirtilmemişse etiket basma — LLM kendi değerlendirsin.
    #    "10 yaş altı kontrendike" gibi hastaya uygulanmayan kuralları yakalamayı önler.
    if chunks_43 and _KONTRENDIKE_RE.search(icerik_43):
        if eslesen_durumlar and any(d in icerik_43 for d in eslesen_durumlar):
            # Sorudaki klinik durum 4.3 metninde geçiyor → gerçek kontrendikasyon
            etiket = "KONTREDİKE"
        elif eslesen_durumlar:
            # 4.3 var, kontrendike kelimesi var ama sorunun durumu 4.3'te yok
            # → Başka bir grup için kontrendike; bu hasta için dikkatli kullanım
            etiket = "DİKKATLİ_KULLANIM"
        else:
            # Soruda klinik durum belirtilmemiş → LLM bağlamı okusun, biz etiket basma
            etiket = ""
    # 2. 4.3 yok / eşleşme yok ama 4.4 dikkatli kullanım diyor → DİKKATLİ
    elif chunks_44 and _DIKKATLI_RE.search(icerik_44):
        if eslesen_durumlar and any(d in icerik_44 for d in eslesen_durumlar):
            etiket = "DİKKATLİ_KULLANIM"
        elif not eslesen_durumlar and _DIKKATLI_RE.search(icerik_44):
            etiket = "DİKKATLİ_KULLANIM"
        else:
            etiket = ""
    # 3. 4.2 doz bilgisi varsa
    elif chunks_42 and "doz" in soru_lower:
        etiket = "DOZ_AYARI_GEREKEBİLİR"
    else:
        return ""

    if not etiket:
        return ""

    # Etiket açıklamaları
    aciklama = {
        "KONTREDİKE": (
            "Getirilen KÜB bağlamı, sorudaki klinik durum için 4.3 Kontrendikasyon bölümünde "
            "KONTREDİKASYON içermektedir. İlk cümlen bu kararı net yansıtmalı."
        ),
        "DİKKATLİ_KULLANIM": (
            "Getirilen KÜB bağlamı bu durum için 4.3 Kontrendikasyon DEĞİL; "
            "4.4 Özel Uyarılar bölümünde DİKKATLİ KULLANIM uyarısı içermektedir. "
            "'Kontrendikedir' veya 'kullanılmamalıdır' YAZMA — bunun yerine "
            "'dikkatli kullanılmalıdır / yakın izlem gerekir' kullan."
        ),
        "DOZ_AYARI_GEREKEBİLİR": (
            "Getirilen KÜB bağlamı 4.2 Pozoloji bölümünde bu hasta için "
            "DOZ AYARI bilgisi içermektedir. KÜB'de belirtilen doz bilgilerini aktar. "
            "KÜB'de bulunmayan spesifik değerler (GFR eşiği, mg miktarı, laboratuvar değerleri) EKLEME — "
            "hastanın GFR, kreatinin veya diğer değerlerini TAHMIN ETME; "
            "yalnızca soruda/profilde açıkça verilen ve KÜB bağlamındaki bilgileri kullan."
        ),
    }

    logger.debug(f"[Kalibrasyon] Etiket: {etiket} | Durum: {eslesen_durumlar}")

    return (
        f"\n## KLİNİK ÖN DEĞERLENDİRME (Sistem — Değiştirilemez)\n"
        f"**Karar Etiketi: {etiket}**\n"
        f"{aciklama[etiket]}\n"
    )


_MADDE_ACIKLAMALARI: dict[str, str] = {
    "4.1": "Endikasyonlar",
    "4.2": "Pozoloji / Doz",
    "4.3": "Kontrendikasyonlar",
    "4.4": "Özel uyarılar",
    "4.5": "İlaç etkileşimleri",
    "4.6": "Gebelik / Emzirme",
    "4.7": "Araç kullanımı",
    "4.8": "İstenmeyen etkiler",
    "4.9": "Doz aşımı",
}


def _inject_auto_kaynaklar(yanit: str, chunklar: list) -> str:
    """
    LLM'in KAYNAKLAR bölümünü chunk metadata'sıyla değiştirir (Aksiyon 3).

    - LLM'in yazdığı ## KAYNAKLAR varsa → içeriğini sil, metadata ile doldur
    - Yoksa → ## UYARI'dan önce ekle
    - Böylece LLM parafraz/halüsinasyon ile yanlış alıntı yapamaz
    """
    seen: set[tuple] = set()
    lines: list[str] = []

    for c in chunklar:
        ilac = getattr(c, "ilac_adi", "") if hasattr(c, "ilac_adi") else c.get("ilac_adi", "")
        madde = getattr(c, "madde_no", "") if hasattr(c, "madde_no") else c.get("madde_no", "")
        if not ilac or not madde:
            continue
        key = (ilac.upper(), madde)
        if key in seen:
            continue
        seen.add(key)
        aciklama = _MADDE_ACIKLAMALARI.get(madde, f"Madde {madde}")
        lines.append(f"- {ilac} — Madde {madde}: {aciklama}")

    if not lines:
        return yanit

    kaynaklar_content = "\n".join(lines)
    kaynaklar_bolumu = f"## KAYNAKLAR\n{kaynaklar_content}"

    # LLM ## KAYNAKLAR yazdıysa → bloğun tamamını metadata ile değiştir
    if "## KAYNAKLAR" in yanit:
        # KAYNAKLAR başlığından sonraki bölümü bul
        idx = yanit.index("## KAYNAKLAR")
        # Sonraki ## başlığını bul
        rest = yanit[idx + len("## KAYNAKLAR"):]
        next_section = re.search(r'\n##\s', rest)
        if next_section:
            after = rest[next_section.start():]
            yanit = yanit[:idx] + kaynaklar_bolumu + "\n" + after.lstrip("\n")
        else:
            yanit = yanit[:idx] + kaynaklar_bolumu
    elif "## UYARI" in yanit:
        # KAYNAKLAR yoksa → ## UYARI'dan önce ekle
        idx = yanit.index("## UYARI")
        yanit = yanit[:idx] + kaynaklar_bolumu + "\n\n" + yanit[idx:]
    else:
        # İkisi de yoksa → sona ekle
        yanit = yanit.rstrip() + f"\n\n{kaynaklar_bolumu}"

    return yanit


def _build_user_prompt(
    soru: str,
    hasta_ozeti: str,
    chunklar: list[RetrievedChunk],
    graf_baglami: str = "",
    kumlatif_metin: str = "",
    cyp_metin: str = "",
    soru_turleri: list[str] | None = None,
    coverage_uyari: str = "",
) -> str:
    """Kullanıcı prompt'unu oluşturur."""

    soru_turleri = soru_turleri or []
    etkilesim_sorusu = "etkilesim" in soru_turleri or "cyp450_etkilesim" in soru_turleri

    # ── Answer Calibration Layer ─────────────────────────────────────────────
    kalibrasyon_blogu = _calibrate_clinical_severity(chunklar, soru, soru_turleri)

    kub_bolumu = _format_chunks_for_prompt(chunklar, soru=soru)  # Contextual Compression aktif

    graf_bolumu = f"\n## GRAF VERİTABANI BULGULARI (Neo4j)\n{graf_baglami}\n" if graf_baglami else ""

    # Kümülatif analiz: KÜB metninde desteklenen konular için (kısıtlı)
    kumlatif_bolumu = (
        f"\n## OTOMATİK KÜMÜLATİF RİSK ANALİZİ\n{kumlatif_metin}\n"
    ) if kumlatif_metin else ""

    # CYP450 analizi: etkileşim sorusuysa öne çıkar, değilse standart ekle
    if cyp_metin:
        if etkilesim_sorusu:
            cyp_bolumu = (
                f"\n## CYP450 MEKANİZMA ANALİZİ (ÖNCELİKLİ)\n"
                f"Bu etkileşim sorusu için CYP450 enzim mekanizması kritik öneme sahiptir.\n"
                f"Aşağıdaki mekanizma bilgilerini yanıtın ODAK NOKTASI olarak kullan:\n"
                f"{cyp_metin}\n"
            )
        else:
            cyp_bolumu = (
                f"\n## OTOMATİK CYP450 ENZİM ANALİZİ\n"
                f"{cyp_metin}\n"
            )
    else:
        cyp_bolumu = ""

    # Etkileşim sorusuysa CYP bölümünü KÜB'ün hemen ardına taşı (öncelik sinyali)
    if etkilesim_sorusu and cyp_bolumu:
        bolum_sirasi = f"{kub_bolumu}\n{cyp_bolumu}{graf_bolumu}{kumlatif_bolumu}"
    else:
        bolum_sirasi = f"{kub_bolumu}\n{graf_bolumu}{kumlatif_bolumu}{cyp_bolumu}"

    # ── CYP Kural (v2 — sınırlı aktarım) ────────────────────────────────────
    # CYP bilgisi varsa → SADECE verilen metni aktar, kendi bilgini ekleme
    if cyp_metin and etkilesim_sorusu:
        cyp_talimati = (
            "- CYP450 BİLGİSİ: Yukarıdaki CYP450 bölümündeki mekanizma bilgisini (inhibisyon/indüksiyon/substrat) "
            "## SONUÇ'ta kısaca [CYP450] etiketiyle belirt. "
            "SADECE yukarıda verilen CYP450 metnindeki bilgileri aktar — "
            "KÜB veya CYP bölümünde olmayan ek mekanizma bilgisi, [BİLGİ YOK] açıklaması veya genel LLM bilgisi EKLEME."
        )
    elif cyp_metin:
        cyp_talimati = (
            "- CYP450 BİLGİSİ MEVCUT: Bu bölümdeki enzim bilgisi (inhibisyon/substrat/indüksiyon) "
            "soruyla ilgiliyse yanıta dahil et — [CYP450] etiketiyle. "
            "Yalnızca bu bölümde yazanları kullan, ek yorum ekleme."
        )
    else:
        cyp_talimati = ""

    prompt = f"""## HASTA PROFİLİ
{hasta_ozeti}
{kalibrasyon_blogu}
## İLGİLİ KÜB BİLGİLERİ
{bolum_sirasi}
## SORU{coverage_uyari}
{soru}

## YANIT TALİMATLARI
- KONU SINIRI: Yanıtını YALNIZCA soruyla doğrudan ilgili bilgilerle sınırla.
  Soru doz ayarı ise → etkileşim anlatma. Soru emzirme ise → gebelik bilgisi verme.
  Soru yan etki ise → doz bilgisi ekleme.

- KARAR VE BAŞLANGIÇ: ## SONUÇ bölümündeki ilk cümle soruya net bir cevap olmalı:
  * Kontrendikasyon varsa: "Hayır, [eşik/koşul belirt] durumunda kontrendikedir [İlaç | Madde 4.3]."
    → Ardından: hangi GFR değeri, hangi karaciğer skoru, hangi dozda kontrendike — spesifik ver.
    → Madde 4.2 veya 4.4 doz/izlem bilgisi bağlamda varsa ekle; yoksa "[BİLGİ YOK]" de.
  * Kullanılabilirse: "Evet, dikkatli kullanılabilir [İlaç | Madde X.X]." veya "Doz ayarı gerekir."
    → Doz eşiği, izlem sıklığı, uygulama koşullarını bağlamdan ver.
  * Tüm bağlam bölümlerinde soruyla ilgili bilgi yoksa:
    "[BİLGİ YOK: Bu konu incelenen KÜB belgelerinde yer almamaktadır.]"
  * ASLA "klinisyen karar versin" ile başlama — önce net bilgi ver, sonra öneri ekle.

- KAYNAK KURALI (KRİTİK): Her tıbbi iddia cümlesinin SONUNA kaynak etiketi ekle.
  KÜB → [İlaç Adı | Madde X.X] | Graf → [Graf] | CYP450 → [CYP450]
  Bağlamda AÇIKÇA bulunmayan hiçbir bilgiyi yazma.

- KAYNAK ÖNCELİĞİ: KÜB bilgisi > CYP450 mekanizması > Graf. Çakışmada KÜB önceliklidir.
- Madde 4.4 (Uyarılar) ve 4.8 (Yan etkiler) soruyla ilgiliyse — mutlaka değerlendir.
- Hasta profilini göz önünde bulundur: yaş, böbrek/karaciğer fonksiyonu, mevcut ilaçlar.
- HASTA DEĞERİ YASAĞI: Hasta profilinde veya soruda açıkça belirtilmeyen sayısal hasta değerlerini
  (yaş, GFR, kreatinin, ağırlık, laboratuvar sonuçları vb.) ÜRETME ve YAZMA.
  Profil boşsa ya da değer verilmemişse → o değere atıfta bulunma.
- OTOMATİK KÜMÜLATİF RİSK bulgularını yalnızca KÜB'de desteklenen konular için kullan.
{cyp_talimati}
- YANIT DETAYI: ## SONUÇ en az 3 cümle içermeli; klinik karar için gereken tüm bilgileri
  (mekanizma, doz etkisi, izlem önerisi, uyarılar) kapsamalıdır. Eksik bölümler [BİLGİ YOK] ile belirt.
- ALTERNATİF İLAÇ (MUTLAK YASAK): Bağlamda adı AÇIKÇA yazılmayan hiçbir ilaç adı,
  etken madde veya ilaç sınıfı önerme. "DMAH", "warfarin", "heparin", "metildopa" vb.
  bağlamda geçmiyorsa yazılamaz — "değerlendirilebilir" veya "tercih edilebilir" formunda
  bile yasak. Yalnızca: "[Bu konuda ek klinik değerlendirme gereklidir.]" yaz.

- ZORUNLU FORMAT — ## SONUÇ bölümünü tam olarak aşağıdaki 3 katmanda yaz:

## SONUÇ

**[KÜB Aktarımı]**
KÜB belgelerindeki ilgili bilgileri doğrudan aktar.
Her cümle/madde bir KÜB kaynağına bağlı: [İlaç | Madde X.X]
Mümkünse KÜB'ün kendi ifadesini kullan — yorum veya çıkarım ekleme.

**[Sistem Tespitleri]** *(Graf/CYP/Lab bulgusu varsa — yoksa bu başlığı yazma)*
Graf/CYP450/kümülatif risk bulgularını "tespit edildi / saptandı / gözlemlendi" diliyle yaz.
[Graf] ve [CYP450] etiketleri zorunlu. Yorum değil, bulgu.

**[Değerlendirme]**
Yukarıdaki KÜB verisi ve sistem tespitlerinden türetilen 1-2 cümle klinik sonuç.
Hasta-spesifik, net, soruya doğrudan yanıt.

## UYARI
[Klinik uyarı ve izlem önerileri. Son cümle: "Klinik karar hekimindir."]

(## KAYNAKLAR yazmayın — sistem otomatik ekliyor)"""

    return prompt


_ALT_MADDE_KEYWORDS: dict[str, list[str]] = {
    "bobrek_karaciger": ["böbrek yetmezliği", "karaciğer yetmezliği", "kreatinin", "klerens", "klirens", "renal", "CLcr", "eGFR"],
    "pediyatrik":       ["çocuk", "pediyatrik", "bebek", "adölesan", "yaş arası", "kg/gün", "mg/kg"],
    "geriyatrik":       ["yaşlı", "geriyatrik", "65 yaş", "ileri yaş"],
}

# Madde bazında chunk limiti — uzun bölümler kesilmeden gönderilir
_MADDE_CHUNK_LIMITS: dict[str, int] = {
    "4.3": 800,    # Kontrendikasyonlar — genellikle kısa liste
    "4.2": 3000,   # Pozoloji — doz tabloları uzun olabilir
    "4.4": 3000,   # Özel uyarılar — kritik, kesilmemeli
    "4.5": 2500,   # Etkileşimler
    "4.6": 4000,   # Gebelik/laktasyon — her iki bölüm birlikte gelir
    "4.8": 3000,   # Yan etkiler
}
_DEFAULT_LIMIT = POLICY.chunk_window_chars   # ContentPolicy — diğer maddeler için
_WINDOW_SIZE   = POLICY.chunk_window_chars   # keyword penceresi


def _extract_chunk_window(icerik: str, alt_madde: str, madde_no: str = "") -> str:
    """
    Sub-chunk için akıllı pencere çıkarımı.

    Madde bazında limit uygular: 4.6 gebelik/laktasyon tam gönderilir,
    4.3 kontrendikasyon kısaltılır. Alt madde varsa keyword etrafından pencere alır.
    """
    # Madde bazında limit belirle
    limit = _MADDE_CHUNK_LIMITS.get(madde_no, _DEFAULT_LIMIT)

    if not alt_madde:
        # Base chunk — madde limitine kadar gönder
        return icerik[:limit] + ("\n[... devamı mevcut, özet gösterildi]" if len(icerik) > limit else "")

    # Alt madde varsa — keyword ile ilgili pencereyi çıkar
    keywords = _ALT_MADDE_KEYWORDS.get(alt_madde, [])
    icerik_lower = icerik.lower()

    best_pos = -1
    for kw in keywords:
        pos = icerik_lower.find(kw.lower())
        if pos != -1:
            best_pos = pos
            break

    if best_pos == -1:
        return icerik[:limit] + ("\n[... devamı mevcut, özet gösterildi]" if len(icerik) > limit else "")

    # keyword başlangıcından itibaren pencere al
    start = max(0, best_pos - 200)
    end = min(len(icerik), start + _WINDOW_SIZE)
    pencere = icerik[start:end]

    prefix = "...\n" if start > 0 else ""
    suffix = "\n[... devamı mevcut]" if end < len(icerik) else ""
    return prefix + pencere + suffix


def _compress_chunk_by_query(text: str, soru: str, madde_no: str = "") -> str:
    """
    Contextual Compression — sorguyla ilgili satırları/paragrafları filtreler.

    Strateji (deterministik, LLM gerektirmez):
    - Metni satırlara / kısa paragraflara böl
    - Her satırı sorgu anahtar kelimeleriyle skorla
    - Eşik altındaki satırları çıkar (boilerplate temizleme)
    - Minimum _CC_MIN_LINES satır garanti edilir (bilgi kaybı önleme)
    - Yalnızca _CC_THRESHOLD'dan uzun metinlere uygulanır

    Neden gerekli?
    - Büyük chunklar gürültü içerir → LLM context'te olmayan iddialar üretiyor (F ↓)
    - RAGAS CU: getirilen chunk'ın cevaba katkısını ölçer — ilgisiz satırlar CU'yu düşürür
    """
    _CC_THRESHOLD = 1200   # 1200+ karakter chunk'lara CC uygula (gürültü/uzun belgeler)
    _CC_MIN_LINES = 4      # En az bu kadar satır koru
    _CC_SCORE_THRESHOLD = 1  # Bir satırda en az bu kadar keyword olmalı

    if len(text) < _CC_THRESHOLD:
        return text

    # Sorgu anahtar kelimeleri (2+ karakter, Türkçe stop-word'ler hariç)
    _STOP = {
        "bir", "bu", "de", "da", "ile", "ve", "veya", "için", "olan",
        "olan", "olarak", "olan", "gibi", "kadar", "daha", "çok", "ne",
        "mi", "mı", "mu", "mü", "ki", "ise", "ama", "ancak", "olan",
        "madde", "kub", "bölüm", "bkz", "bakınız",
    }
    soru_lower = soru.lower()
    keywords = [
        w for w in re.split(r'\W+', soru_lower)
        if len(w) >= 3 and w not in _STOP
    ]

    if not keywords:
        return text

    # Satır bazlı bölme (tek \n yeterli — KÜB metni satır bazlı)
    lines = [ln for ln in text.split('\n') if ln.strip()]
    if len(lines) <= _CC_MIN_LINES:
        return text

    def score_line(line: str) -> int:
        ll = line.lower()
        return sum(1 for kw in keywords if kw in ll)

    scored = [(ln, score_line(ln)) for ln in lines]
    # Eşik altındaki satırlar: sıfır puanlı "boilerplate"
    kept = [ln for ln, sc in scored if sc >= _CC_SCORE_THRESHOLD]

    # Minimum satır garantisi: ilk 2 + en yüksek puanlılar
    if len(kept) < _CC_MIN_LINES:
        top_lines = sorted(lines[:2])  # başlık satırları
        # Skor sırasına göre ek satır ekle
        extra = [ln for ln, sc in sorted(scored, key=lambda x: -x[1])
                 if ln not in top_lines]
        kept = lines[:2] + extra[:max(0, _CC_MIN_LINES - 2)]

    # 4.3 kontrendikasyon ve 4.6 gebelik bölümlerinde çok agresif kısaltma yapma
    if madde_no in ("4.3", "4.6"):
        # Bu bölümlerde sadece uzun satırlar kırpılıyor (satır değil karakter limiti)
        return text

    compressed = '\n'.join(kept)

    # Sıkıştırma çok agresif olduysa orijinale dön (>%70 kayıp)
    if len(compressed) < len(text) * 0.30:
        return text

    if len(compressed) < len(text):
        logger.debug(f"[CC] {madde_no}: {len(text)} → {len(compressed)} kar "
                     f"(%{100*(1-len(compressed)/len(text)):.0f} azaltma)")

    return compressed


def _format_chunks_for_prompt(chunklar: list[RetrievedChunk], soru: str = "") -> str:
    """
    Chunk listesini prompt için etiketli formata çevirir (Faz 12).

    Her chunk açık KAYNAK etiketi ile gönderilir:
      --- KAYNAK: {ilaç_adı} | KÜB Madde {section_no}: {section_title} ---
    Bu format LLM'in bağlamı ile yanıtı eşleştirmesini kolaylaştırır.

    Faz 16+: Contextual Compression — soru parametresi verilirse sorguyla
    ilgisiz satırlar çıkarılır (F ↑ + CU ↑).
    """
    if not chunklar:
        return "İlgili KÜB bilgisi bulunamadı."

    parcalar = []
    for chunk in chunklar:
        madde_label = chunk.madde_no
        if chunk.alt_madde:
            madde_label += f"[{chunk.alt_madde}]"
        header = f"--- KAYNAK: {chunk.ilac_adi} | KÜB Madde {madde_label}: {chunk.madde_baslik} ---"
        icerik = chunk.icerik.strip()
        icerik = _extract_chunk_window(icerik, chunk.alt_madde, chunk.madde_no)
        # Contextual Compression — soru verilmişse gürültüyü filtrele
        if soru:
            icerik = _compress_chunk_by_query(icerik, soru, chunk.madde_no)
        parcalar.append(f"{header}\n{icerik}")

    return "\n\n".join(parcalar)


# ---------------------------------------------------------------------------
# Ana RAG fonksiyonu
# ---------------------------------------------------------------------------

def _auto_detect_drugs_from_query(soru: str) -> list[str]:
    """
    Sorgu metnindeki büyük harfli ilaç adlarını NameResolver ile tespit eder.

    Strateji:
      - Türkçe ilaç adları sorgularda genellikle BÜYÜK HARF ile yazılır (LİPİTOR, BRUFEN)
      - ≥4 karakter büyük harfli tokenlar aday olarak alınır
      - NameResolver prefix/exact eşleşmesi ile onaylanır
      - Fuzzy/substring fallback kullanılmaz — yanlış pozitif riski yüksek

    Döner: normalize edilmiş display_name listesi (boş olabilir)
    """
    import re as _re
    from src.core.name_resolver import get_resolver
    from src.data.normalization import normalize_drug_name as _norm

    # Türkçe büyük harf karakterleri içeren ≥4 karakterlik tokenlar
    # Örn: "LİPİTOR", "BRUFEN", "METAFORMAL", "SPORANOX"
    # Dışarıda kalır: "GFR" (3 char), "KÜB" (3 char), "NSAİİ" (resolver bulamaz)
    candidates = _re.findall(
        r'\b[A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ]{3,}(?:[\s\-][A-ZÇĞİÖŞÜ]{2,}){0,2}\b',
        soru,
    )

    if not candidates:
        return []

    resolver = get_resolver()
    detected: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        matches = resolver.resolve(candidate)
        if not matches:
            continue

        first = matches[0]
        if first.canonical_id in seen:
            continue

        # Kalite filtresi: ilaç display_name'inin ilk kelimesi candidate ile başlamalı
        # Bu, fuzzy/substring eşleşmelerin yanlış sürüklenmesini önler
        display_first = _norm(first.display_name).upper().split()[0]
        candidate_norm = _norm(candidate).upper().split()[0]

        if display_first.startswith(candidate_norm[:4]):
            detected.append(_norm(first.display_name))
            seen.add(first.canonical_id)
            logger.debug(f"Auto-detect: '{candidate}' → '{first.display_name}'")

    return detected


def run_rag(
    soru: str,
    profil: PatientProfile,
    hedef_ilaclar: list[str] | None = None,
    n_results: int = 5,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> RAGResponse:
    """
    Tam RAG pipeline'ını çalıştırır.

    Args:
        soru:          Klinisyenin sorusu
        profil:        Hasta profili
        hedef_ilaclar: Sorgunun odaklandığı ilaçlar (None ise genel)
        model:         Claude model ID
        max_tokens:    Maksimum yanıt token sayısı

    Returns:
        RAGResponse — yanıt + kaynaklar + metadata
    """
    logger.info(f"RAG pipeline başladı: '{soru[:60]}...' " if len(soru) > 60 else f"RAG pipeline başladı: '{soru}'")

    # Hedef ilaç adlarını normalize et — ® ™ © gibi semboller ChromaDB filtresini kırıyor
    if hedef_ilaclar:
        hedef_ilaclar = [normalize_drug_name(i) for i in hedef_ilaclar]
    else:
        # hedef_ilaclar verilmemişse soru metninden otomatik tespit et
        hedef_ilaclar = _auto_detect_drugs_from_query(soru) or None

    if hedef_ilaclar:
        logger.info(f"Hedef ilaçlar: {hedef_ilaclar}")

    # 1. Query augmentation
    augmented = augment_query(soru, profil, hedef_ilaclar, n_results=n_results)
    logger.info(f"Soru türleri: {augmented.soru_turleri}")

    # 1b. HyDE — varsayımsal KÜB paragrafı ile retrieval kalitesini artır
    hyde_sorgu: str | None = None
    try:
        hyde_sorgu = _generate_hyde_document(
            soru=soru,
            hedef_ilaclar=hedef_ilaclar,
            soru_turleri=augmented.soru_turleri,
        )
        if hyde_sorgu:
            logger.info(f"HyDE aktif ({len(hyde_sorgu)} karakter)")
    except Exception as _hyde_err:
        logger.warning(f"HyDE atlandı: {_hyde_err}")

    # 2. ChromaDB retrieval
    chunklar = _retrieve_chunks(augmented, hyde_sorgu=hyde_sorgu)
    logger.info(f"{len(chunklar)} chunk alındı (min skor: {chunklar[-1].score:.3f} max: {chunklar[0].score:.3f})" if chunklar else "Chunk bulunamadı")

    # 3. Neo4j CombiGraph bağlamı
    graf_baglami = ""
    try:
        from src.graph.combi_retriever import build_graph_context
        hasta_kosullar = []
        if profil.bobrek_yetmezligi:
            hasta_kosullar.append("böbrek yetmezliği")
        if profil.karaciger_yetmezligi:
            hasta_kosullar.append("karaciğer yetmezliği")
        if profil.gebelik:
            hasta_kosullar.append("gebelik")
        gc = build_graph_context(
            sorgu_ilaclar=hedef_ilaclar or [],
            hasta_ilaclar=profil.mevcut_ilaclar,
            hasta_kosullar=hasta_kosullar,
            hasta_yas=profil.yas,
            hasta_endikasyonlar=list(profil.endikasyonlar) if profil.endikasyonlar else [],
        )
        graf_baglami = gc.ozet_metin
        logger.info(f"Graf bağlamı hazır: {len(gc.kontrendikasyonlar)} kontrendikasyon, {len(gc.etkilesimler)} etkileşim")
    except Exception as e:
        logger.exception(f"Neo4j graf bağlamı alınamadı ({type(e).__name__}): {e}")

    # 3b. Kümülatif yan etki analizi (Phase 8 - Senaryo 2)
    # Yalnızca (a) sorgunun hedef ilaçları ve (b) hastanın mevcut ilaçlarına ait
    # chunk'lar değerlendirmeye alınır. Bağlamdan gelen alakalı-ama-ilgisiz chunk'lar
    # kümülatif riske dahil edilmez — aksi hâlde retrieval gürültüsü yanlış uyarı üretir.
    kumlatif_metin = ""
    kum_sonuc = None
    try:
        from src.analysis.cumulative_risk import analiz_et as kumlatif_analiz

        def _norm(s: str) -> str:
            """Türkçe karakterleri ve sembol gürültüsünü normalize eder (karşılaştırma için)."""
            return (s.upper()
                    .replace('İ', 'I').replace('Ş', 'S').replace('Ğ', 'G')
                    .replace('Ü', 'U').replace('Ö', 'O').replace('Ç', 'C')
                    .replace('®', '').replace('™', '').replace('°', ''))

        # Marka adı karşılaştırması: ilk kelime yeterli (® sonrası fark yaratmasın)
        _hedef_kisalar = {_norm(i.split()[0]) for i in (hedef_ilaclar or [])}
        _hasta_kisalar = {_norm(i.split()[0]) for i in profil.mevcut_ilaclar if i.strip()}
        _ilgili_kisalar = _hedef_kisalar | _hasta_kisalar

        if _ilgili_kisalar:
            # Exact match: _norm(ilac_adi) == k ya da ilac_adi'nin ilk kelimesi eşleşiyor
            # Substring yerine exact — "META" "METAFORMAL"'ı da eşleştirmesin
            kum_chunklar = [
                c for c in chunklar
                if _norm(c.ilac_adi).split()[0] in _ilgili_kisalar
            ]
        else:
            kum_chunklar = []

        if len(kum_chunklar) >= 2:
            kum_sonuc = kumlatif_analiz(kum_chunklar, profil.mevcut_ilaclar)
            kumlatif_metin = kum_sonuc.ozet_metin
            if kum_sonuc.riskler:
                logger.info(f"Kümülatif risk: {len(kum_sonuc.riskler)} kategori tespit edildi")
        else:
            logger.debug("Kümülatif risk: yeterli hedef chunk yok, atlandı")
    except Exception as e:
        logger.warning(f"Kümülatif risk analizi atlandı: {e}")

    # 3c. CYP450 ontoloji analizi (Phase 8 - Senaryo 3)
    cyp_metin = ""
    cyp_sonuc = None
    try:
        from src.analysis.cyp450_mapper import analiz_et as cyp_analiz
        cyp_sonuc = cyp_analiz(
            chunklar=chunklar,
            hasta_ilaclar=profil.mevcut_ilaclar,
            sorgu_ilaclar=hedef_ilaclar,
        )
        cyp_metin = cyp_sonuc.ozet_metin
        if cyp_sonuc.etkilesimler:
            logger.info(f"CYP450: {len(cyp_sonuc.etkilesimler)} etkileşim tespit edildi")
    except Exception as e:
        logger.warning(f"CYP450 analizi atlandı: {e}")

    # 4. Bölüm kapsama kontrolü — eksik KÜB bölümleri için LLM uyarısı (Aksiyon 5)
    _SORU_TURU_GEREKLI_BOLUM: dict[str, str] = {
        "kontrendikasyon":   "4.3",
        "doz":               "4.2",
        "doz_bobrek":        "4.2",
        "doz_karaciger":     "4.2",
        "doz_geriyatrik":    "4.2",
        "doz_pediyatrik":    "4.2",
        "yan_etki":          "4.8",
        "gebelik_laktasyon": "4.6",
        "etkilesim":         "4.5",
        "cyp450_etkilesim":  "4.5",
    }
    gelen_bolumler = {c.madde_no for c in chunklar}
    eksik_bolumler = sorted({
        _SORU_TURU_GEREKLI_BOLUM[st]
        for st in augmented.soru_turleri
        if st in _SORU_TURU_GEREKLI_BOLUM
        and _SORU_TURU_GEREKLI_BOLUM[st] not in gelen_bolumler
    })
    coverage_uyari = ""
    if eksik_bolumler:
        eksik_str = ", ".join(f"Madde {b}" for b in eksik_bolumler)
        coverage_uyari = (
            f"\n⚠️ BAĞLAM UYARISI: Bu soru için gereken {eksik_str} bölümü KÜB'den "
            f"alınamadı. Bu bölüm(ler) için kesinlikle [BİLGİ YOK: ...] kullan, "
            f"tahminde bulunma.\n"
        )
        logger.warning(f"[COVERAGE] Eksik KÜB bölümleri: {eksik_bolumler} (soru türleri: {augmented.soru_turleri})")

    # 4b. Prompt oluştur — FIX-1: hasta özetini chunk relevance'a göre filtrele
    filtered_hasta_ozeti = _build_filtered_hasta_ozeti(profil, chunklar)
    user_prompt = _build_user_prompt(
        soru, filtered_hasta_ozeti, chunklar,
        graf_baglami, kumlatif_metin, cyp_metin,
        soru_turleri=augmented.soru_turleri,
        coverage_uyari=coverage_uyari,
    )

    # 4c. LLM çağrısı (provider'a göre)
    provider = os.environ.get("LLM_PROVIDER", "claude").lower()

    if provider == "local":
        yanit, kullanulan_model, giris_token, cikis_token = _call_local_llm(
            user_prompt, max_tokens
        )
    else:
        yanit, kullanulan_model, giris_token, cikis_token = _call_claude(
            user_prompt, model, max_tokens
        )

    # 5. Faz 12 — Yanıt doğrulama ("güvenlidir" yasağı + bağlam kontrolü)
    yanit = validate_response(yanit, chunklar, soru=soru)

    # 5b. Auto-KAYNAKLAR enjeksiyonu — LLM yazmıyor, chunk metadata'sından üretilir (Aksiyon 3)
    yanit = _inject_auto_kaynaklar(yanit, chunklar)

    # 6. Karantina kontrolü — hedef_ilaclar için OCR bekleyen ilaçları tespit et
    quarantine_warnings: list[str] = []
    if hedef_ilaclar:
        q_list = _load_quarantine_list()
        for ilac in hedef_ilaclar:
            normalized = ilac.upper().replace(" ", "_")
            if normalized in q_list:
                quarantine_warnings.append(ilac)

    return RAGResponse(
        soru=soru,
        yanit=yanit,
        kaynaklar=chunklar,
        hasta_ozeti=augmented.hasta_ozeti,
        soru_turleri=augmented.soru_turleri,
        model=kullanulan_model,
        prompt_token_sayisi=giris_token,
        yanit_token_sayisi=cikis_token,
        kumlatif_riskler=kum_sonuc.riskler if kum_sonuc is not None else [],
        cyp_etkilesimler=cyp_sonuc.etkilesimler if cyp_sonuc is not None else [],
        cyp_source=cyp_sonuc.source if cyp_sonuc is not None else "unknown",
        graf_baglami=graf_baglami,
        kumlatif_metin=kumlatif_metin,
        cyp_metin=cyp_metin,
        quarantine_warnings=quarantine_warnings,
    )


def _call_claude(
    user_prompt: str,
    model: str,
    max_tokens: int,
) -> tuple[str, str, int, int]:
    """Anthropic Claude API'yi çağırır. (yanit, model, giris_token, cikis_token)"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY ortam değişkeni tanımlı değil.")

    client = anthropic.Anthropic(api_key=api_key)
    logger.info(f"Claude API çağrısı yapılıyor ({model})...")

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    yanit = message.content[0].text
    logger.info(f"Yanit alindi ({message.usage.output_tokens} token)")
    return yanit, model, message.usage.input_tokens, message.usage.output_tokens


def _call_local_llm(
    user_prompt: str,
    max_tokens: int,
) -> tuple[str, str, int, int]:
    """LM Studio (OpenAI-uyumlu) yerel sunucuyu çağırır. (yanit, model, giris_token, cikis_token)"""
    base_url = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")
    model_name = os.environ.get("LOCAL_MODEL_NAME", "local-model")

    client = openai.OpenAI(base_url=base_url, api_key="lm-studio")
    logger.info(f"Yerel LLM çağrısı yapılıyor ({base_url} | {model_name})...")

    # System role'ü user message'a birleştir — bazı modeller (Gemma, Llama vb.)
    # system role'ü desteklemiyor; bu şekilde tüm modeller çalışır.
    combined_prompt = f"{LOCAL_SYSTEM_PROMPT}\n\n{user_prompt}"

    response = client.chat.completions.create(
        model=model_name,
        max_tokens=max_tokens,
        messages=[
            {"role": "user", "content": combined_prompt},
        ],
        temperature=0.1,
        extra_body={"think": False},  # Gemma4/Qwen3 thinking mode'u kapat — içerik boş gelmesin
    )

    # Thinking mode'lu modeller (Gemma4, Qwen3) content="", reasoning="..." döner.
    # Ollama v1 API'de thinking içeriği "reasoning" alanında geliyor.
    raw = response.choices[0].message
    content = getattr(raw, "content", None) or ""
    reasoning = getattr(raw, "reasoning", None) or ""
    # content doluysa kullan; boşsa reasoning'i kullan (thinking mode fallback)
    yanit = content if content.strip() else reasoning
    giris_token = response.usage.prompt_tokens if response.usage else 0
    cikis_token = response.usage.completion_tokens if response.usage else 0
    logger.info(f"Yanit alindi ({cikis_token} token)")
    return yanit, model_name, giris_token, cikis_token
