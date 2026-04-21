"""
PharmAssist — Streamlit Arayüzü
KÜB tabanlı Klinik Karar Destek Sistemi
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import re
import json
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from src.agents.patient_profile import PatientProfile, LAB_ESIKLERI, _lab_durumu
from src.agents.rag_engine import run_rag
from src.ingestion.lab_parser import parse_lab_file

# ---------------------------------------------------------------------------
# Sayfa ayarları
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="PharmAssist",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main-header { font-size: 1.8rem; font-weight: 700; color: #1a5276; }
.sub-header  { font-size: 0.95rem; color: #5d6d7e; margin-bottom: 1rem; }

.risk-kritik {
    background: #fde8e8;
    border-left: 4px solid #c0392b;
    padding: 0.6rem 1rem;
    border-radius: 4px;
    margin-bottom: 0.4rem;
    font-size: 0.9rem;
    color: #7b1a1a !important;
}
.risk-dikkat {
    background: #fef9e7;
    border-left: 4px solid #f39c12;
    padding: 0.6rem 1rem;
    border-radius: 4px;
    margin-bottom: 0.4rem;
    font-size: 0.9rem;
    color: #7d5a00 !important;
}
.risk-bilgi {
    background: #eaf4fb;
    border-left: 4px solid #2e86c1;
    padding: 0.6rem 1rem;
    border-radius: 4px;
    margin-bottom: 0.4rem;
    font-size: 0.9rem;
    color: #1a4a6b !important;
}
.risk-ok {
    background: #eafaf1;
    border-left: 4px solid #27ae60;
    padding: 0.6rem 1rem;
    border-radius: 4px;
    margin-bottom: 0.4rem;
    font-size: 0.9rem;
    color: #1a5c35 !important;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Yardımcı: Kalıcı sorgu geçmişi (JSONL)
# ---------------------------------------------------------------------------

_LOG_PATH = os.path.join(os.path.dirname(__file__), "data", "logs", "query_history.jsonl")


def _gecmis_kaydet(soru: str, yanit: str, hedef_ilaclar: list, soru_turleri: list, chunk_sayisi: int, model: str) -> None:
    """Sorguyu JSONL log dosyasına ekler. Hassas hasta verisi (lab değerleri) yazılmaz."""
    kayit = {
        "tarih": datetime.now().isoformat(timespec="seconds"),
        "soru": soru,
        "yanit_ozet": yanit[:300] + ("…" if len(yanit) > 300 else ""),
        "hedef_ilaclar": hedef_ilaclar or [],
        "soru_turleri": soru_turleri or [],
        "chunk_sayisi": chunk_sayisi,
        "model": model or "",
    }
    try:
        os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"Geçmiş log yazılamadı: {e}")


def _gecmis_yukle(son_n: int = 20) -> list[dict]:
    """JSONL dosyasından son N kaydı yükler."""
    if not os.path.exists(_LOG_PATH):
        return []
    try:
        with open(_LOG_PATH, encoding="utf-8") as f:
            satirlar = f.readlines()
        kayitlar = []
        for satir in reversed(satirlar):
            satir = satir.strip()
            if satir:
                try:
                    kayitlar.append(json.loads(satir))
                except json.JSONDecodeError:
                    continue
                if len(kayitlar) >= son_n:
                    break
        return kayitlar
    except Exception as e:
        logger.warning(f"Geçmiş log okunamadı: {e}")
        return []


# ---------------------------------------------------------------------------
# Yardımcı: ChromaDB'den ilaç listesi
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def _get_ilac_listesi() -> list[str]:
    try:
        from src.retrieval.chroma_store import collection_stats
        stats = collection_stats()
        return sorted(stats.get("ilac_dagilimi", {}).keys())
    except Exception as e:
        logger.warning(f"İlaç listesi ChromaDB'den alınamadı: {e}")
        return []


# ---------------------------------------------------------------------------
# Yardımcı: İlaç adı kısaltma (UI-3)
# ---------------------------------------------------------------------------

_DOZ_RE = re.compile(r"\d[\d.,]*\s*(?:mg|mcg|µg|ml|g\b|iu|ui|mmol|meq|miu|%)", re.IGNORECASE)


def _kisa_ad_uret(tam_ad: str) -> str:
    """'AUGMENTIN 400 MG/57 MG oral süspansiyon...' → 'AUGMENTIN 400MG/57MG'"""
    parcalar = tam_ad.split()
    marka = parcalar[0] if parcalar else tam_ad
    eslesmeler = _DOZ_RE.findall(tam_ad)
    if eslesmeler:
        doz = "/".join(e.strip().replace(" ", "").upper() for e in eslesmeler[:2])
        return f"{marka} {doz}"
    # Doz bilgisi yoksa ilk 3 kelimeyi al
    return " ".join(parcalar[:3])


@st.cache_data(ttl=300)
def _get_ilac_harita() -> dict[str, str]:
    """Kısa ad → tam ad eşlemesi. Çakışan kısa adlara sayaç eklenir."""
    harita: dict[str, str] = {}
    for tam in _get_ilac_listesi():
        kisa = _kisa_ad_uret(tam)
        if kisa in harita:
            sayac = 2
            while f"{kisa} ({sayac})" in harita:
                sayac += 1
            kisa = f"{kisa} ({sayac})"
        harita[kisa] = tam
    return harita


# ---------------------------------------------------------------------------
# Yardımcı: Risk özeti kartları
# ---------------------------------------------------------------------------

def _risk_ozeti_goster(profil: PatientProfile, hedef_ilaclar: list[str]) -> None:
    """Hasta profili ve lab değerlerine göre renkli risk kartları gösterir."""
    kritik: list[str] = []
    dikkat: list[str] = []
    bilgi:  list[str] = []

    # Hasta profili bazlı riskler
    if profil.gebelik:
        kritik.append("Hasta GEBE — tüm ilaçlar için gebelik kategorisi kontrol edilmeli")
    if profil.emzirme:
        dikkat.append("Hasta EMZİRİYOR — laktasyon geçişi değerlendirilmeli")
    if profil.bobrek_yetmezligi:
        evre = profil.bobrek_evresi
        msg = f"Böbrek yetmezliği ({evre}, GFR={profil.gfr}) — doz ayarı gerekebilir"
        if profil.gfr is not None and profil.gfr < 30:
            kritik.append(msg)
        else:
            dikkat.append(msg)
    if profil.karaciger_yetmezligi:
        dikkat.append(f"Karaciğer yetmezliği (Child-Pugh {profil.karaciger_skoru}) — hepatik metabolizma etkilenebilir")
    if profil.geriyatrik:
        bilgi.append(f"Geriyatrik hasta ({profil.yas} yaş) — doz ve tolerabilite dikkatli değerlendirilmeli")
    if profil.pediyatrik:
        dikkat.append(f"Pediatrik hasta ({profil.yas} yaş) — pediatrik doz uygulaması kontrol edilmeli")

    # Lab değeri bazlı riskler
    for anormal in profil.anormal_lab_degerleri:
        param  = anormal["param"]
        deger  = anormal["deger"]
        durum  = anormal["durum"]
        birim  = anormal["birim"]
        ok = "↑↑" if durum == "kritik_yüksek" else ("↓↓" if durum == "kritik_düşük" else ("↑" if durum == "yüksek" else "↓"))

        mesaj_map = {
            "ALT":       f"ALT: {deger} {birim} {ok} — Karaciğer enzim yüksekliği, hepatotoksisite riski",
            "AST":       f"AST: {deger} {birim} {ok} — Karaciğer enzim yüksekliği",
            "Bilirubin": f"Bilirubin: {deger} {birim} {ok} — Hepatik fonksiyon bozukluğu",
            "GGT":       f"GGT: {deger} {birim} {ok} — Karaciğer/safra yolu hasarı",
            "Kreatinin": f"Kreatinin: {deger} {birim} {ok} — Böbrek fonksiyon bozukluğu",
            "K":         f"K⁺: {deger} {birim} {ok} — {'Hiperkalemi' if durum == 'kritik_yüksek' else 'Hipokalemi'} riski",
            "Na":        f"Na⁺: {deger} {birim} {ok} — {'Hipernatremi' if durum == 'kritik_yüksek' else 'Hiponatremi'} riski",
            "INR":       f"INR: {deger} {ok} — Antikoagülasyon yüksek, kanama riski artmış",
            "HbA1c":     f"HbA1c: {deger}% {ok} — Glisemik kontrol bozuk",
            "Hemoglobin":f"Hemoglobin: {deger} {birim} {ok} — Anemi, ilaç toleransı azalabilir",
            "Trombosit": f"Trombosit: {deger} {birim} {ok} — Trombositopeni, kanama riski",
        }
        mesaj = mesaj_map.get(param, f"{param}: {deger} {birim} {ok}")

        if "kritik" in durum:
            kritik.append(mesaj)
        else:
            dikkat.append(mesaj)

    # Alerjiler
    if profil.alerjiler:
        bilgi.append(f"Bilinen alerji: {', '.join(profil.alerjiler)} — çapraz reaktivite kontrol edilmeli")

    # Mevcut ilaç etkileşim uyarısı
    if profil.mevcut_ilaclar and hedef_ilaclar:
        bilgi.append(
            f"Mevcut {len(profil.mevcut_ilaclar)} ilaç ile etkileşim analiz edildi: "
            f"{', '.join(profil.mevcut_ilaclar[:3])}{'...' if len(profil.mevcut_ilaclar) > 3 else ''}"
        )

    if not (kritik or dikkat or bilgi):
        st.markdown('<div class="risk-ok">✅ Hasta profilinde öne çıkan risk faktörü tespit edilmedi</div>',
                    unsafe_allow_html=True)
        return

    for k in kritik:
        st.markdown(f'<div class="risk-kritik">🔴 <strong>KRİTİK:</strong> {k}</div>', unsafe_allow_html=True)
    for d in dikkat:
        st.markdown(f'<div class="risk-dikkat">🟡 <strong>DİKKAT:</strong> {d}</div>', unsafe_allow_html=True)
    for b in bilgi:
        st.markdown(f'<div class="risk-bilgi">🔵 <strong>BİLGİ:</strong> {b}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "gecmis" not in st.session_state:
    st.session_state.gecmis = []

if "kalici_gecmis" not in st.session_state:
    st.session_state.kalici_gecmis = _gecmis_yukle(20)

# UI-1: Lab belgesi parse sonuçları bekleyen onay
if "pending_lab" not in st.session_state:
    st.session_state.pending_lab = {}

# UI-1: param → session_state key eşlemesi (Kabul Et işleminde kullanılır)
_LAB_KEY_MAP: dict[str, str] = {
    "ALT":        "lab_alt",
    "AST":        "lab_ast",
    "INR":        "lab_inr",
    "K":          "lab_k",
    "Na":         "lab_na",
    "Kreatinin":  "lab_kreatinin",
    "HbA1c":      "lab_hba1c",
    "Bilirubin":  "lab_bilirubin",
    "Hemoglobin": "lab_hgb",
    "Trombosit":  "lab_trombo",
    "GFR":        "gfr_input",
}

# İlaç listesini önceden yükle (sidebar'da kullanılacak)
ilac_listesi = _get_ilac_listesi()
ilac_harita = _get_ilac_harita()   # {kisa_ad: tam_ad}
kisa_adlar = sorted(ilac_harita.keys())

# ---------------------------------------------------------------------------
# Sidebar — Hasta Profili (UI-4: Expander grupları)
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 💊 PharmAssist")

    # --- Expander 1: Hasta Profili ---
    with st.expander("👤 Hasta Profili", expanded=True):
        yas = st.number_input("Yaş", min_value=0, max_value=120, value=45, step=1)
        cinsiyet = st.selectbox("Cinsiyet", ["belirtilmemiş", "erkek", "kadın"])
        kilo = st.number_input(
            "Kilo (kg)", min_value=0.0, max_value=300.0,
            value=0.0, step=0.5, key="kilo_input",
            help="0 = bilinmiyor",
        )
        kilo_val = kilo if kilo > 0 else None
        gfr = st.number_input(
            "eGFR (mL/dk/1.73m²)", min_value=0.0, max_value=200.0,
            value=0.0, step=1.0, key="gfr_input",
            help="0 = bilinmiyor / normal",
        )
        gfr_val = gfr if gfr > 0 else None

        st.markdown("**Özel Durumlar**")
        gebelik   = st.checkbox("Gebe")
        emzirme   = st.checkbox("Emziriyor")
        pediatrik = st.checkbox("Pediatrik hasta (<18 yaş)")
        geriatrik = st.checkbox("Geriatrik hasta (≥65 yaş)")
        bobrek    = st.checkbox("Böbrek yetmezliği")
        karaciger = st.checkbox("Karaciğer yetmezliği")

        st.markdown("**Alerjiler**")
        alerjiler_raw = st.text_input("Virgülle ayırın", placeholder="penisilin, sülfamid",
                                       key="alerji_input")
        alerjiler = [a.strip() for a in alerjiler_raw.split(",") if a.strip()]

        st.markdown("**Endikasyonlar / Tanılar**")
        endikasyon_raw = st.text_input("Virgülle ayırın", placeholder="hipertansiyon, diyabet",
                                        key="endikasyon_input")
        endikasyonlar = [e.strip() for e in endikasyon_raw.split(",") if e.strip()]

    # --- Expander 2: Laboratuvar (UI-1: Lab belgesi yükleme) ---
    with st.expander("🧪 Laboratuvar", expanded=False):

        # -- UI-1: Dosya yükleme --
        lab_dosyasi = st.file_uploader(
            "Lab raporu yükle (PDF / PNG / JPG)",
            type=["pdf", "png", "jpg", "jpeg"],
            key="lab_uploader",
            help="Dijital PDF önerilir. Görüntü formatı için pytesseract kurulu olmalıdır.",
        )

        # Yeni dosya yüklendiyse parse et (aynı dosyayı tekrar parse etme)
        if lab_dosyasi is not None:
            if st.session_state.get("_lab_upload_ad") != lab_dosyasi.name:
                with st.spinner("Lab raporu analiz ediliyor..."):
                    try:
                        _parsed = parse_lab_file(lab_dosyasi.read(), lab_dosyasi.name)
                        st.session_state.pending_lab = _parsed
                        st.session_state["_lab_upload_ad"] = lab_dosyasi.name
                        if not _parsed:
                            st.warning("Tanınan lab parametresi bulunamadı. Değerleri manuel girin.")
                    except Exception as _exc:
                        st.error(f"Parse hatası: {_exc}")
                        st.session_state.pending_lab = {}

        # Tespit edilen değerler varsa önizleme + onay ekranı
        _pending = st.session_state.get("pending_lab", {})
        if _pending:
            st.success(f"**{len(_pending)} değer tespit edildi** — kontrol edip onaylayın:")
            _pcols = st.columns(2)
            for _i, (_p, _v) in enumerate(_pending.items()):
                _pcols[_i % 2].caption(f"{_p}: **{_v}**")

            _kab_col, _sil_col = st.columns(2)
            with _kab_col:
                if st.button("✅ Kabul Et ve Doldur", key="lab_kabul", use_container_width=True):
                    for _param, _skey in _LAB_KEY_MAP.items():
                        if _param in _pending:
                            st.session_state[_skey] = float(_pending[_param])
                    st.session_state.pending_lab = {}
                    st.session_state.pop("_lab_upload_ad", None)
                    st.rerun()
            with _sil_col:
                if st.button("❌ İptal", key="lab_iptal", use_container_width=True):
                    st.session_state.pending_lab = {}
                    st.session_state.pop("_lab_upload_ad", None)
                    st.rerun()

        st.caption("0 = bilinmiyor / girilmedi")

        lab_col1, lab_col2 = st.columns(2)
        with lab_col1:
            lab_alt       = st.number_input("ALT (U/L)",           min_value=0.0, value=0.0, step=1.0,              key="lab_alt")
            lab_ast       = st.number_input("AST (U/L)",           min_value=0.0, value=0.0, step=1.0,              key="lab_ast")
            lab_inr       = st.number_input("INR",                 min_value=0.0, value=0.0, step=0.1, format="%.1f", key="lab_inr")
            lab_k         = st.number_input("K⁺ (mEq/L)",          min_value=0.0, value=0.0, step=0.1, format="%.1f", key="lab_k")
            lab_na        = st.number_input("Na⁺ (mEq/L)",         min_value=0.0, value=0.0, step=1.0,              key="lab_na")
        with lab_col2:
            lab_kreatinin = st.number_input("Kreatinin (mg/dL)",   min_value=0.0, value=0.0, step=0.1, format="%.1f", key="lab_kreatinin")
            lab_hba1c     = st.number_input("HbA1c (%)",           min_value=0.0, value=0.0, step=0.1, format="%.1f", key="lab_hba1c")
            lab_bilirubin = st.number_input("Bilirubin (mg/dL)",   min_value=0.0, value=0.0, step=0.1, format="%.1f", key="lab_bilirubin")
            lab_hgb       = st.number_input("Hemoglobin (g/dL)",   min_value=0.0, value=0.0, step=0.1, format="%.1f", key="lab_hgb")
            lab_trombo    = st.number_input("Trombosit (x10³/µL)", min_value=0.0, value=0.0, step=1.0,              key="lab_trombo")

        # Sıfır olmayan değerleri topla
        lab_degerleri: dict[str, float] = {}
        _lab_raw = {
            "ALT": lab_alt, "AST": lab_ast, "INR": lab_inr,
            "K": lab_k, "Na": lab_na, "Kreatinin": lab_kreatinin,
            "HbA1c": lab_hba1c, "Bilirubin": lab_bilirubin,
            "Hemoglobin": lab_hgb, "Trombosit": lab_trombo,
        }
        for _k, _v in _lab_raw.items():
            if _v > 0:
                lab_degerleri[_k] = _v

        # Anormal değer uyarısı
        if lab_degerleri:
            _uyarilar = []
            for _param, _deger in lab_degerleri.items():
                _durum = _lab_durumu(_param, _deger)
                if _durum == "kritik_yüksek":
                    _uyarilar.append(f"🔴 {_param}: {_deger} ↑↑")
                elif _durum == "kritik_düşük":
                    _uyarilar.append(f"🔴 {_param}: {_deger} ↓↓")
                elif _durum in ("yüksek", "düşük"):
                    _uyarilar.append(f"🟡 {_param}: {_deger}")
            if _uyarilar:
                st.warning("**Anormal Lab:**\n" + "\n".join(_uyarilar))

    # --- Expander 3: Mevcut İlaçlar ---
    with st.expander("💊 Mevcut İlaçlar", expanded=False):
        if kisa_adlar:
            st.caption("Sistemde bulunan ilaçları seçin")

            # Arama alanı
            mevcut_ara = st.text_input(
                "Mevcut İlaç Ara",
                placeholder="Örn: Metformin, Lisinopril...",
                label_visibility="collapsed",
                key="mevcut_ilac_ara",
            )

            # Filtreleme
            mevcut_filtrelenmis = (
                [k for k, v in ilac_harita.items()
                 if mevcut_ara.upper() in k.upper() or mevcut_ara.upper() in v.upper()]
                if mevcut_ara
                else kisa_adlar
            )

            # Multiselect ile seçim
            mevcut_kisa_secim = st.multiselect(
                "Seç",
                options=mevcut_filtrelenmis,
                placeholder="Kullandığı ilaçları seçin",
                key="mevcut_ilaclar_multiselect",
                label_visibility="collapsed",
            )

            # Kısa adları tam ada çevir
            mevcut_ilaclar = [ilac_harita[k] for k in mevcut_kisa_secim]
        else:
            # Fallback: manual giriş (ChromaDB başarısız olduğunda)
            st.warning("İlaç listesi yüklenemedi. Manuel giriş yapın:")
            ilaclar_raw = st.text_area(
                "Her satıra bir ilaç yazın",
                height=80,
                placeholder="Warfarin 5 mg\nAspirin 100 mg",
                key="mevcut_ilaclar_manual",
            )
            mevcut_ilaclar = [i.strip() for i in ilaclar_raw.splitlines() if i.strip()]

    st.markdown("---")
    n_results = st.slider("Retrieval chunk sayısı", min_value=3, max_value=15, value=8)
    provider_label = os.environ.get("LLM_PROVIDER", "claude").upper()
    st.caption(f"LLM: {provider_label}")


# ---------------------------------------------------------------------------
# Ana panel — başlık
# ---------------------------------------------------------------------------

st.markdown('<p class="main-header">💊 PharmAssist</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">KÜB Tabanlı Klinik Karar Destek Sistemi</p>',
            unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hedef ilaç seçimi
# ---------------------------------------------------------------------------

if kisa_adlar:
    # 50+ ilaç için arama/filtreleme
    ara_col, toplam_col = st.columns([3, 1])
    with toplam_col:
        st.caption(f"**{len(kisa_adlar)}** ilaç yüklü")
    with ara_col:
        ilac_ara = st.text_input(
            "İlaç Ara",
            placeholder="Örn: Norvasc, Metoprolol...",
            label_visibility="collapsed",
        )

    # Hem kısa hem tam ada göre filtrele
    filtrelenmis = (
        [k for k, v in ilac_harita.items()
         if ilac_ara.upper() in k.upper() or ilac_ara.upper() in v.upper()]
        if ilac_ara
        else kisa_adlar
    )

    hedef_kisa_secim = st.multiselect(
        "Analiz Edilecek İlaç(lar)",
        options=filtrelenmis,
        placeholder="Seçin veya boş bırakın (tüm KÜB taranır)",
        help="Belirli ilaç(lar) seçerseniz retrieval yalnızca o ilaçlara odaklanır.",
    )
    # Kısa adları tam ada çevir — RAG engine tam adı bekler
    hedef_ilaclar_secim = [ilac_harita[k] for k in hedef_kisa_secim]
else:
    hedef_ilaclar_secim = []
    st.info("ChromaDB bağlantısı kurulamadı veya koleksiyon boş.", icon="ℹ️")

# ---------------------------------------------------------------------------
# Soru girişi ve butonlar
# ---------------------------------------------------------------------------

soru = st.text_area(
    "Klinik Soru",
    height=90,
    placeholder="Örn: Böbrek yetmezliği olan bu hastaya Augmentin yazılabilir mi?",
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    gonder = st.button("Sorgula", type="primary", use_container_width=True)
with col2:
    temizle = st.button("Temizle", use_container_width=True)

if temizle:
    st.session_state.gecmis = []
    st.rerun()

# ---------------------------------------------------------------------------
# Sorgu çalıştır
# ---------------------------------------------------------------------------

if gonder and soru.strip():
    # Hasta profili oluştur
    gfr_hesap = gfr_val
    if bobrek and not gfr_val:
        gfr_hesap = 45.0

    karaciger_skoru = "B" if karaciger else None

    profil = PatientProfile(
        yas=yas,
        cinsiyet=cinsiyet,
        kilo=kilo_val,
        gfr=gfr_hesap,
        karaciger_skoru=karaciger_skoru,
        gebelik=gebelik,
        emzirme=emzirme,
        mevcut_ilaclar=mevcut_ilaclar,
        alerjiler=alerjiler,
        endikasyonlar=endikasyonlar,
        lab_degerleri=lab_degerleri,
        pediyatrik_override=True if pediatrik else None,
        geriyatrik_override=True if geriatrik else None,
    )

    hedef_ilaclar = hedef_ilaclar_secim if hedef_ilaclar_secim else None

    with st.spinner("KÜB kaynakları taranıyor..."):
        try:
            response = run_rag(
                soru=soru.strip(),
                profil=profil,
                hedef_ilaclar=hedef_ilaclar,
                n_results=n_results,
            )
        except Exception as e:
            st.error(f"Hata: {e}")
            st.stop()

    # Geçmişe ekle (session — en fazla 5 tut)
    st.session_state.gecmis.insert(0, {
        "soru": soru.strip(),
        "yanit": response.yanit,
        "kaynaklar": response.kaynaklar,
        "soru_turleri": response.soru_turleri,
        "model": response.model,
    })
    st.session_state.gecmis = st.session_state.gecmis[:5]

    # Kalıcı log'a kaydet
    _gecmis_kaydet(
        soru=soru.strip(),
        yanit=response.yanit,
        hedef_ilaclar=hedef_ilaclar or [],
        soru_turleri=response.soru_turleri,
        chunk_sayisi=len(response.kaynaklar),
        model=response.model,
    )
    # Kalıcı geçmişi yenile
    st.session_state.kalici_gecmis = _gecmis_yukle(20)

    # ---------------------------------------------------------------------------
    # Sonuç göster
    # ---------------------------------------------------------------------------

    st.markdown("---")

    # Metadata satırı
    meta_cols = st.columns(5)
    _model_parts = response.model.split("-") if response.model else []
    _model_label = _model_parts[1].upper() if len(_model_parts) > 1 else (response.model.upper() if response.model else "—")
    meta_cols[0].metric("Model", _model_label)

    soru_turu_tam = " / ".join(response.soru_turleri) if response.soru_turleri else "genel"
    soru_turu_kisa = soru_turu_tam if len(soru_turu_tam) <= 18 else soru_turu_tam[:16] + "…"
    meta_cols[1].metric("Soru Türü", soru_turu_kisa, help=soru_turu_tam)

    meta_cols[2].metric("Hedef İlaç", len(hedef_ilaclar) if hedef_ilaclar else "tümü")
    meta_cols[3].metric("Kaynak Chunk", len(response.kaynaklar))
    meta_cols[4].metric("Yanıt Token", response.yanit_token_sayisi)

    # Karantina uyarıları — OCR bekleyen ilaçlar
    if hasattr(response, 'quarantine_warnings') and response.quarantine_warnings:
        for drug in response.quarantine_warnings:
            st.warning(f"⚠️ {drug} için KÜB belgesi OCR işlemi bekliyor. Bilgiler eksik olabilir.")

    # Sıfır chunk uyarısı (UI-2)
    if not response.kaynaklar:
        import difflib
        uyari = (
            "Bu ilaç için KÜB belgesi bulunamadı. "
            "İlaç seçimini kontrol edin veya seçim yapmadan sorgulayın."
        )
        if hedef_ilaclar and ilac_listesi:
            ilac_upper_map = {i.upper(): i for i in ilac_listesi}
            oneriler: list[str] = []
            for ilac in hedef_ilaclar:
                benzerler = difflib.get_close_matches(
                    ilac.upper(), ilac_upper_map.keys(), n=3, cutoff=0.4
                )
                oneriler.extend(ilac_upper_map[b] for b in benzerler)
            if oneriler:
                benzer_liste = "\n".join(
                    f"- {o}" for o in list(dict.fromkeys(oneriler))[:5]
                )
                uyari += f"\n\n**ChromaDB'de benzer adlar:**\n{benzer_liste}"
        st.warning(uyari)

    # Risk özeti paneli
    st.markdown("#### Risk Özeti")
    _risk_ozeti_goster(profil, hedef_ilaclar or [])

    # Kümülatif risk bulguları
    if response.kumlatif_riskler:
        st.markdown("##### Kümülatif Yan Etki Analizi")
        for r in response.kumlatif_riskler:
            css = "risk-kritik" if r.siddet == "kritik" else "risk-dikkat"
            sembol = "🔴 KRİTİK" if r.siddet == "kritik" else "🟡 DİKKAT"
            st.markdown(
                f'<div class="{css}">{sembol} — <strong>{r.kategori_label}</strong>: {r.aciklama}</div>',
                unsafe_allow_html=True,
            )

    # CYP450 etkileşim bulguları
    if response.cyp_etkilesimler:
        st.markdown("##### CYP450 Enzim Etkileşimleri")
        for e in response.cyp_etkilesimler:
            css = "risk-kritik" if e.siddet == "kritik" else "risk-dikkat"
            sembol = "🔴 KRİTİK" if e.siddet == "kritik" else "🟡 DİKKAT"
            st.markdown(
                f'<div class="{css}">{sembol} [{e.enzim}] — {e.sonuc}</div>',
                unsafe_allow_html=True,
            )

    # CYP450 kaynak görünürlüğü
    cyp_source = getattr(response, "cyp_source", "unknown")
    if cyp_source == "unavailable":
        st.warning("⚠️ Bu ilaç için CYP450 profili mevcut değil — otomatik çıkarım başarısız oldu.")
    elif cyp_source == "llm_extraction":
        st.info("ℹ️ CYP450 profili KÜB metninden otomatik çıkarıldı (manuel doğrulama önerilir).")

    # Klinik yanıt
    st.markdown("#### Klinik Yanıt")
    with st.container(border=True):
        st.markdown(response.yanit)

    # Kaynaklar
    if response.kaynaklar:
        st.markdown("#### Kullanılan Kaynaklar")
        with st.expander(f"{len(response.kaynaklar)} chunk göster", expanded=False):
            for i, k in enumerate(response.kaynaklar, 1):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(
                        f"**{i}. {k.ilac_adi}** — Madde {k.madde_no}"
                        f"{'[' + k.alt_madde + ']' if k.alt_madde else ''} "
                        f"*{k.madde_baslik}* (s.{k.sayfa})"
                    )
                    with st.expander("İçerik"):
                        st.text(k.icerik[:800] + ("…" if len(k.icerik) > 800 else ""))
                with col_b:
                    st.metric("Skor", f"{k.score:.3f}")

    # Hasta profili özeti
    if response.hasta_ozeti:
        with st.expander("Hasta Profili Özeti"):
            st.text(response.hasta_ozeti)

elif gonder and not soru.strip():
    st.warning("Lütfen bir soru girin.")


# ---------------------------------------------------------------------------
# Sorgu geçmişi — kalıcı log
# ---------------------------------------------------------------------------

kalici = st.session_state.get("kalici_gecmis", [])
if kalici:
    st.markdown("---")
    with st.expander(f"Geçmiş Sorgular ({len(kalici)} kayıt)", expanded=False):
        for kayit in kalici:
            tarih = kayit.get("tarih", "")[:16].replace("T", " ")
            tur = " / ".join(kayit.get("soru_turleri", [])) or "genel"
            ilaclar = ", ".join(kayit.get("hedef_ilaclar", [])) or "tümü"
            baslik = f"{tarih} — {kayit['soru'][:70]}{'…' if len(kayit['soru']) > 70 else ''}"
            with st.expander(baslik):
                st.caption(f"Tür: {tur} | İlaçlar: {ilaclar} | Chunk: {kayit.get('chunk_sayisi', '?')} | Model: {kayit.get('model', '?')}")
                st.markdown(kayit.get("yanit_ozet", ""))


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.caption(
    "⚠️ Bu sistem yalnızca klinik karar desteği amaçlıdır. "
    "Nihai karar her zaman sorumlu hekime aittir."
)
