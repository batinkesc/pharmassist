"""
PharmAssist — Arayüz v2.0
Split panel: Sol = Hasta Profili (otomatik çıkarım) | Sağ = Klinik Sohbet
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from src.agents.patient_profile import PatientProfile, _lab_durumu
from src.agents.rag_engine import run_rag
from src.agents.profile_extractor import extract_context, ExtractedContext
from src.ingestion.lab_report_parser import parse_lab_report, LabReportResult

# ─── Sayfa Ayarları ─────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PharmAssist",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS Teması ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Arka plan ── */
[data-testid="stAppViewContainer"] { background: #f0f4f8; }
[data-testid="stMain"] { padding-top: 0; }
[data-testid="block-container"] { padding: 1rem 2rem 1rem 2rem; max-width: 100%; }
section[data-testid="stSidebar"] { display: none; }

/* ── Başlık çizgisi ── */
.pa-header {
    display: flex;
    align-items: center;
    padding: 0.6rem 0 0.8rem 0;
    border-bottom: 2px solid #1e3a5f;
    margin-bottom: 1.2rem;
    gap: 12px;
}
.pa-logo { font-size: 1.6rem; }
.pa-title { font-size: 1.35rem; font-weight: 700; color: #1e3a5f; margin: 0; }
.pa-sub   { font-size: 0.78rem; color: #64748b; margin: 0; }

/* ── Profil Kartları ── */
.pcard {
    background: white;
    border-radius: 10px;
    padding: 13px 15px;
    margin-bottom: 9px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.pcard-title {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94a3b8;
    margin-bottom: 9px;
}
.pcard-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 3px 0;
    font-size: 0.87rem;
    color: #0f172a;
    border-bottom: 1px solid #f8fafc;
}
.pcard-row:last-child { border-bottom: none; }
.pcard-lbl { color: #94a3b8; font-size: 0.82rem; }
.pcard-val { font-weight: 500; color: #0f172a; }
.pcard-empty { color: #cbd5e1; font-size: 0.84rem; font-style: italic; }

/* ── Karşılama ekranı ── */
.welcome-box {
    text-align: center;
    padding: 32px 20px;
    color: #94a3b8;
}
.welcome-icon { font-size: 2.2rem; margin-bottom: 10px; }
.welcome-title { font-size: 0.95rem; font-weight: 500; color: #64748b; margin-bottom: 6px; }
.welcome-example { font-size: 0.82rem; color: #cbd5e1; line-height: 1.6; margin-top: 8px;
                   background: #f8fafc; border-radius: 8px; padding: 10px 14px; text-align: left; }

/* ── İlaç Etiketleri ── */
.dtag {
    display: inline-block;
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.8rem;
    color: #334155;
    margin: 2px 2px 2px 0;
}
.dtag.hedef {
    background: #eff6ff;
    border-color: #93c5fd;
    color: #1d4ed8;
    font-weight: 600;
}
.dtag.alerji {
    background: #fff7ed;
    border-color: #fed7aa;
    color: #c2410c;
}

/* ── Risk Badge ── */
.rbadge {
    display: flex;
    align-items: flex-start;
    gap: 7px;
    border-radius: 7px;
    padding: 7px 11px;
    font-size: 0.83rem;
    margin-bottom: 5px;
    line-height: 1.4;
}
.rb-kritik { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; }
.rb-dikkat { background: #fffbeb; border: 1px solid #fde68a; color: #b45309; }
.rb-ok     { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
.rb-icon   { flex-shrink: 0; margin-top: 1px; }

/* ── Yanıt Meta ── */
.resp-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f1f5f9;
}
.meta-chip {
    font-size: 0.77rem;
    color: #475569;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 2px 10px;
}
.meta-chip strong { color: #1e3a5f; }

/* ── Kaynak Listesi ── */
.src-item {
    display: flex;
    align-items: flex-start;
    gap: 9px;
    padding: 8px 0;
    border-bottom: 1px solid #f8fafc;
    font-size: 0.84rem;
}
.src-item:last-child { border-bottom: none; }
.src-no {
    min-width: 22px; height: 22px;
    background: #1e3a5f; color: white;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; font-weight: 700; flex-shrink: 0;
}
.src-drug { font-weight: 600; color: #1e3a5f; }
.src-skor { font-size: 0.74rem; color: #94a3b8; margin-top: 1px; }

/* ── Text area girişi ── */
.stTextArea textarea {
    color: #0f172a !important;
    background: #ffffff !important;
    caret-color: #1e3a5f !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 10px !important;
    font-size: 0.92rem !important;
    padding: 10px 14px !important;
}
.stTextArea textarea:focus {
    border-color: #1e3a5f !important;
    box-shadow: 0 0 0 2px rgba(30,58,95,0.12) !important;
    outline: none !important;
}
.stTextArea textarea::placeholder { color: #94a3b8 !important; }

/* ── Chat mesaj içerikleri ── */
[data-testid="stChatMessage"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0;
    border-radius: 12px !important;
    margin-bottom: 10px;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] h4,
[data-testid="stChatMessage"] em,
[data-testid="stChatMessage"] strong {
    color: #0f172a !important;
}
[data-testid="stChatMessage"] .stMarkdown { color: #0f172a !important; }

/* ── Buton ── */
.stButton > button {
    border-radius: 8px;
    font-size: 0.83rem;
}

/* ── Popover trigger butonu (🧪 Lab) ── */
[data-testid="stPopover"] button {
    background-color: #f1f5f9 !important;
    color: #1e3a5f !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
}
[data-testid="stPopover"] button:hover {
    background-color: #e2e8f0 !important;
    border-color: #94a3b8 !important;
}
[data-testid="stPopover"] button p,
[data-testid="stPopover"] button span {
    color: #1e3a5f !important;
    font-size: 0.82rem !important;
}

/* ── Popover kutusu — sıfır padding, duvara dayalı ── */
[data-testid="stPopoverBody"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.09) !important;
    padding: 0 !important;
    overflow: hidden !important;
}
[data-testid="stPopoverBody"] > div {
    background-color: #ffffff !important;
    padding: 10px 12px !important;
}

/* Popover metin renkleri */
[data-testid="stPopoverBody"] p,
[data-testid="stPopoverBody"] span,
[data-testid="stPopoverBody"] label,
[data-testid="stPopoverBody"] small,
[data-testid="stPopoverBody"] div {
    color: #0f172a !important;
    font-size: 0.82rem !important;
}

/* File uploader — drop alanı tam genişlik, minimal */
[data-testid="stPopoverBody"] [data-testid="stFileUploaderDropzone"] {
    background: #f8fafc !important;
    border: 1.5px dashed #cbd5e1 !important;
    border-radius: 6px !important;
    padding: 6px 8px !important;
    margin: 0 !important;
}
[data-testid="stPopoverBody"] [data-testid="stFileUploaderDropzone"] * {
    color: #64748b !important;
    font-size: 0.78rem !important;
}
/* Yüklenen dosya kartı — açık arka plan */
[data-testid="stPopoverBody"] [data-testid="stFileUploaderFile"] {
    background: #f1f5f9 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    padding: 4px 8px !important;
}
[data-testid="stPopoverBody"] [data-testid="stFileUploaderFile"] * {
    color: #334155 !important;
    font-size: 0.78rem !important;
}
/* Drop zone içindeki büyük SVG ikon ve "Drag and drop" metni gizle */
[data-testid="stPopoverBody"] [data-testid="stFileUploaderDropzoneInstructions"] svg,
[data-testid="stPopoverBody"] [data-testid="stFileUploaderDropzoneInstructions"] span:first-child {
    display: none !important;
}
[data-testid="stPopoverBody"] [data-testid="stFileUploaderDropzoneInstructions"] {
    padding: 2px 0 !important;
    gap: 0 !important;
}
/* "Browse files" butonu — tam genişlik */
[data-testid="stPopoverBody"] [data-testid="stBaseButton-secondary"] {
    width: 100% !important;
    font-size: 0.78rem !important;
    padding: 4px !important;
}
/* Yüklenen dosyanın dark arka planını kaldır */
[data-testid="stPopoverBody"] [data-testid="stFileUploaderDropzone"] > div:has(button) {
    background: #f1f5f9 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
}

/* Popover içindeki butonlar */
[data-testid="stPopoverBody"] .stButton > button {
    background: #f1f5f9 !important;
    color: #1e3a5f !important;
    border: 1px solid #cbd5e1 !important;
    font-size: 0.8rem !important;
    padding: 2px 8px !important;
}
[data-testid="stPopoverBody"] .stButton > button:hover {
    background: #e2e8f0 !important;
}

/* ── Lab sil satırı butonları — küçük, hafif ── */
[data-testid="stMainBlockContainer"] .lab-del-btn > button {
    font-size: 0.78rem !important;
    padding: 2px 8px !important;
}

/* ── Genel metin rengi düzeltmeleri ── */
.stMarkdown p { color: #0f172a; }
</style>
""", unsafe_allow_html=True)


# ─── Sabitler ────────────────────────────────────────────────────────────────

_LOG_PATH = os.path.join(os.path.dirname(__file__), "data", "logs", "query_history.jsonl")


# ─── Yardımcı Fonksiyonlar ───────────────────────────────────────────────────

def _gecmis_kaydet(soru, yanit, hedef_ilaclar, soru_turleri, chunk_sayisi, model):
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


@st.cache_data(ttl=300)
def _get_ilac_listesi() -> list[str]:
    try:
        from src.retrieval.chroma_store import collection_stats
        stats = collection_stats()
        return sorted(stats.get("ilac_dagilimi", {}).keys())
    except Exception as e:
        logger.warning(f"İlaç listesi alınamadı: {e}")
        return []


def _eslestir_ilaclar(hedef_ilaclar: list[str], ilac_listesi: list[str]) -> list[str]:
    """Serbest metinle çıkarılan ilaç adlarını ChromaDB kayıtlarıyla eşleştirir."""
    if not hedef_ilaclar or not ilac_listesi:
        return hedef_ilaclar or []
    eslesmis = []
    for h in hedef_ilaclar:
        h_upper = h.upper().strip()
        tam = [i for i in ilac_listesi if h_upper in i.upper() or i.upper().startswith(h_upper)]
        if tam:
            eslesmis.extend(tam[:2])
        else:
            eslesmis.append(h)
    return list(dict.fromkeys(eslesmis))  # tekrarları sil, sırayı koru


# ─── Session State ────────────────────────────────────────────────────────────

if "mesajlar" not in st.session_state:
    st.session_state.mesajlar = []

if "ctx" not in st.session_state:
    st.session_state.ctx = ExtractedContext()

if "preview_ctx" not in st.session_state:
    st.session_state.preview_ctx = ExtractedContext()

if "lab_dosya_adi" not in st.session_state:
    st.session_state.lab_dosya_adi = ""

if "lab_parse_hata" not in st.session_state:
    st.session_state.lab_parse_hata = ""

# İlaç listesini session'a al — sadece bir kere yüklenir, spinner görünmez
if "ilac_listesi" not in st.session_state:
    st.session_state.ilac_listesi = _get_ilac_listesi()


# ─── Real-time profil önizleme ────────────────────────────────────────────────

def _on_soru_degisti():
    """textarea değişince profil panelini anında günceller (LLM çağrısı yok)."""
    text = st.session_state.get("soru_textarea", "")
    if text.strip():
        st.session_state.preview_ctx = extract_context(
            text, st.session_state.ilac_listesi
        )
    else:
        st.session_state.preview_ctx = ExtractedContext()


# ─── Profil Paneli ────────────────────────────────────────────────────────────

def _profil_paneli(ctx: ExtractedContext):
    """Sol panel — hasta profili kartları."""

    # Başlık
    st.markdown('<p style="font-weight:700;color:#1e3a5f;font-size:0.92rem;margin-bottom:12px;">HASTA PROFİLİ</p>',
                unsafe_allow_html=True)

    if not ctx.dolu_mu:
        st.markdown("""
        <div class="pcard" style="text-align:center;padding:22px 14px;">
            <div style="font-size:1.8rem;margin-bottom:8px;">💬</div>
            <div class="pcard-empty" style="font-style:normal;color:#94a3b8;font-size:0.86rem;line-height:1.5;">
                Sohbette hastanızı<br>tanıttığınızda profil<br>otomatik dolar.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Demografik ──
    demo_rows = ""
    if ctx.yas:
        demo_rows += f'<div class="pcard-row"><span class="pcard-lbl">Yaş</span><span class="pcard-val">{ctx.yas}</span></div>'
    if ctx.cinsiyet:
        demo_rows += f'<div class="pcard-row"><span class="pcard-lbl">Cinsiyet</span><span class="pcard-val">{ctx.cinsiyet.capitalize()}</span></div>'
    if ctx.kilo:
        demo_rows += f'<div class="pcard-row"><span class="pcard-lbl">Kilo</span><span class="pcard-val">{ctx.kilo} kg</span></div>'
    if demo_rows:
        st.markdown(f'<div class="pcard"><div class="pcard-title">👤 Demografik</div>{demo_rows}</div>',
                    unsafe_allow_html=True)

    # ── Klinik Durum ──
    klin_rows = ""
    if ctx.gfr is not None:
        if ctx.gfr < 30:
            evre, renk = "Şiddetli", "#dc2626"
        elif ctx.gfr < 60:
            evre, renk = "Orta", "#d97706"
        else:
            evre, renk = "Hafif", "#15803d"
        klin_rows += (f'<div class="pcard-row"><span class="pcard-lbl">eGFR</span>'
                      f'<span class="pcard-val">{ctx.gfr} &nbsp;<span style="color:{renk};font-size:0.78rem">{evre}</span></span></div>')
    if ctx.bobrek_yetmezligi and ctx.gfr is None:
        klin_rows += '<div class="pcard-row"><span class="pcard-lbl">Böbrek</span><span class="pcard-val" style="color:#d97706">⚠ Yetmezlik</span></div>'
    if ctx.karaciger_yetmezligi:
        kc = f"Child-Pugh {ctx.karaciger_skoru}" if ctx.karaciger_skoru else "Yetmezlik"
        klin_rows += f'<div class="pcard-row"><span class="pcard-lbl">Karaciğer</span><span class="pcard-val" style="color:#d97706">⚠ {kc}</span></div>'
    if ctx.gebelik:
        klin_rows += '<div class="pcard-row"><span class="pcard-lbl">Özel Durum</span><span class="pcard-val">🤰 Gebe</span></div>'
    if ctx.emzirme:
        klin_rows += '<div class="pcard-row"><span class="pcard-lbl">Özel Durum</span><span class="pcard-val">Emziriyor</span></div>'
    if ctx.endikasyonlar:
        for e in ctx.endikasyonlar[:3]:
            klin_rows += f'<div class="pcard-row"><span class="pcard-lbl">Tanı</span><span class="pcard-val">{e}</span></div>'
    if klin_rows:
        st.markdown(f'<div class="pcard"><div class="pcard-title">🩺 Klinik Durum</div>{klin_rows}</div>',
                    unsafe_allow_html=True)

    # ── Lab Değerleri (kompakt grid + sil) ──
    if ctx.lab_degerleri:
        items = list(ctx.lab_degerleri.items())
        cells = ""
        for param, val in items:
            try:
                durum = _lab_durumu(param, val)
            except Exception:
                durum = "bilinmiyor"
            vc = "#dc2626" if "kritik" in durum else "#d97706" if durum in ("yüksek", "düşük") else "#475569"
            cells += (
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:2px 4px;border-bottom:1px solid #f8fafc;min-width:0;gap:4px">'
                f'<span style="color:#94a3b8;font-size:0.72rem;white-space:nowrap;'
                f'overflow:hidden;text-overflow:ellipsis;max-width:58%">{param}</span>'
                f'<span style="color:{vc};font-weight:500;font-size:0.74rem;'
                f'white-space:nowrap;flex-shrink:0">{val}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="pcard">'
            f'<div class="pcard-title">🔬 Lab Değerleri'
            f'<span style="font-weight:400;color:#cbd5e1;margin-left:6px">({len(items)})</span>'
            f'</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0 8px">{cells}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        # Sil satırı
        c_sel, c_del = st.columns([5, 2])
        secilen = c_sel.selectbox(
            "lab_del",
            options=["— değer seç"] + [p for p in ctx.lab_degerleri],
            label_visibility="collapsed",
            key="lab_del_select",
        )
        if c_del.button("× Kaldır", key="lab_del_btn", use_container_width=True):
            if secilen != "— değer seç" and secilen in st.session_state.ctx.lab_degerleri:
                del st.session_state.ctx.lab_degerleri[secilen]
                st.rerun()

    # ── Mevcut İlaçlar ──
    if ctx.mevcut_ilaclar:
        tags = "".join(f'<span class="dtag">{i}</span>' for i in ctx.mevcut_ilaclar)
        st.markdown(f'<div class="pcard"><div class="pcard-title">💊 Mevcut İlaçlar</div><div style="margin-top:4px">{tags}</div></div>',
                    unsafe_allow_html=True)

    # ── Sorgulanan İlaç ──
    if ctx.hedef_ilaclar:
        tags = "".join(f'<span class="dtag hedef">{i}</span>' for i in ctx.hedef_ilaclar)
        st.markdown(f'<div class="pcard"><div class="pcard-title">🎯 Sorgulanan İlaç</div><div style="margin-top:4px">{tags}</div></div>',
                    unsafe_allow_html=True)

    # ── Alerjiler ──
    if ctx.alerjiler:
        tags = "".join(f'<span class="dtag alerji">{a}</span>' for a in ctx.alerjiler)
        st.markdown(f'<div class="pcard"><div class="pcard-title">⚠️ Alerjiler</div><div style="margin-top:4px">{tags}</div></div>',
                    unsafe_allow_html=True)

    # ── Temizle ──
    st.markdown("<div style='margin-top:6px'>", unsafe_allow_html=True)
    if st.button("🗑️ Profili & Sohbeti Temizle", use_container_width=True, type="secondary"):
        st.session_state.ctx = ExtractedContext()
        st.session_state.mesajlar = []
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ─── Risk Badge'leri ──────────────────────────────────────────────────────────

def _risk_badges(response, ctx: ExtractedContext):
    kritik, dikkat = [], []

    if ctx.gebelik:
        kritik.append("Hasta GEBE — gebelik kategorisi kontrol edilmeli")
    if ctx.emzirme:
        dikkat.append("Hasta EMZİRİYOR — laktasyon geçişi değerlendirilmeli")
    if ctx.bobrek_yetmezligi or (ctx.gfr is not None and ctx.gfr < 60):
        gfr_str = f" (eGFR {ctx.gfr})" if ctx.gfr else ""
        if ctx.gfr is not None and ctx.gfr < 30:
            kritik.append(f"Şiddetli böbrek yetmezliği{gfr_str} — doz ayarı zorunlu")
        else:
            dikkat.append(f"Böbrek fonksiyon bozukluğu{gfr_str} — doz ayarı gerekebilir")
    if ctx.karaciger_yetmezligi:
        skor = f" Child-Pugh {ctx.karaciger_skoru}" if ctx.karaciger_skoru else ""
        dikkat.append(f"Karaciğer yetmezliği{skor} — hepatik metabolizma etkilenebilir")

    for param, deger in ctx.lab_degerleri.items():
        try:
            durum = _lab_durumu(param, deger)
            if "kritik" in durum:
                kritik.append(f"{param}: {deger} — kritik değer")
            elif durum in ("yüksek", "düşük"):
                dikkat.append(f"{param}: {deger} — anormal")
        except Exception:
            pass

    if hasattr(response, "kumlatif_riskler") and response.kumlatif_riskler:
        for r in response.kumlatif_riskler:
            msg = f"{r.kategori_label}: {r.aciklama[:90]}"
            if r.siddet == "kritik":
                kritik.append(msg)
            else:
                dikkat.append(msg)

    if hasattr(response, "cyp_etkilesimler") and response.cyp_etkilesimler:
        for e in response.cyp_etkilesimler:
            msg = f"[{e.enzim}] {e.sonuc[:90]}"
            if e.siddet == "kritik":
                kritik.append(msg)
            else:
                dikkat.append(msg)

    if not kritik and not dikkat:
        st.markdown('<div class="rbadge rb-ok"><span class="rb-icon">✅</span><span>Profilde öne çıkan risk faktörü tespit edilmedi</span></div>',
                    unsafe_allow_html=True)
        return

    for k in kritik:
        st.markdown(f'<div class="rbadge rb-kritik"><span class="rb-icon">🔴</span><span><strong>KRİTİK:</strong> {k}</span></div>',
                    unsafe_allow_html=True)
    for d in dikkat:
        st.markdown(f'<div class="rbadge rb-dikkat"><span class="rb-icon">🟡</span><span><strong>DİKKAT:</strong> {d}</span></div>',
                    unsafe_allow_html=True)


# ─── Yanıt Görüntüleme ───────────────────────────────────────────────────────

def _yanit_goster(response, ctx: ExtractedContext):
    """Yapılandırılmış yanıt kartı."""

    # Meta şerit
    tur = " / ".join(response.soru_turleri) if response.soru_turleri else "genel"
    hedef = ", ".join(ctx.hedef_ilaclar[:3]) if ctx.hedef_ilaclar else "tüm KÜB"
    provider = os.environ.get("LLM_PROVIDER", "claude").upper()

    st.markdown(f"""
    <div class="resp-meta">
        <span class="meta-chip"><strong>Tür:</strong> {tur}</span>
        <span class="meta-chip"><strong>İlaç:</strong> {hedef}</span>
        <span class="meta-chip"><strong>Kaynak:</strong> {len(response.kaynaklar)} chunk</span>
        <span class="meta-chip"><strong>Model:</strong> {provider}</span>
    </div>
    """, unsafe_allow_html=True)

    # Risk badge'leri
    _risk_badges(response, ctx)

    # Güven Skoru Badge
    if hasattr(response, "guven_etiketi") and response.guven_etiketi:
        if "Yüksek" in response.guven_etiketi:
            renk = "#16a34a"  # yeşil
        elif "Orta" in response.guven_etiketi:
            renk = "#ca8a04"  # sarı
        elif "Düşük" in response.guven_etiketi:
            renk = "#dc2626"  # kırmızı
        else:
            renk = "#6b7280"  # gri
        
        guven_str = f"⬤ {response.guven_etiketi} ({response.guven_skoru:.2f})"
        st.markdown(f'<div style="color:{renk}; font-weight:600; font-size:0.9rem; margin-bottom:12px;">{guven_str}</div>', unsafe_allow_html=True)

    # Klinik yanıt
    st.markdown(response.yanit)

    # KÜB Versioning Footer
    if hasattr(response, "kub_tarihleri") and response.kub_tarihleri:
        tarih_str = ", ".join(response.kub_tarihleri)
        st.markdown(f'<div style="color:black; font-style:italic; font-size:0.8rem; margin-top:10px;">Kaynak KÜB Tarihleri: {tarih_str}</div>', unsafe_allow_html=True)

    # CYP450 kaynak notu
    cyp_src = getattr(response, "cyp_source", "unknown")
    if cyp_src == "llm_extraction":
        st.info("ℹ️ CYP450 profili KÜB metninden otomatik çıkarıldı — manuel doğrulama önerilir.", icon="ℹ️")
    elif cyp_src == "unavailable":
        st.warning("CYP450 profili bu ilaç için mevcut değil.", icon="⚠️")

    # Kaynaklar
    if response.kaynaklar:
        with st.expander(f"📚 {len(response.kaynaklar)} KÜB kaynağı"):
            kaynaklar_html = ""
            for i, k in enumerate(response.kaynaklar, 1):
                alt = f"[{k.alt_madde}]" if k.alt_madde else ""
                kaynaklar_html += f"""
                <div class="src-item">
                    <div class="src-no">{i}</div>
                    <div>
                        <div><span class="src-drug">{k.ilac_adi}</span>
                        — Madde {k.madde_no}{alt} <em>{k.madde_baslik}</em> (s.{k.sayfa})</div>
                        <div class="src-skor">Skor: {k.score:.3f}</div>
                    </div>
                </div>"""
            st.markdown(kaynaklar_html, unsafe_allow_html=True)


# ─── Ana Layout ─────────────────────────────────────────────────────────────

st.markdown("""
<div class="pa-header">
    <span class="pa-logo">💊</span>
    <div>
        <p class="pa-title">PharmAssist</p>
        <p class="pa-sub">KÜB Tabanlı Klinik Karar Destek Sistemi</p>
    </div>
</div>
""", unsafe_allow_html=True)

col_profil, col_chat = st.columns([2, 3], gap="large")

# ── Sol: Profil Paneli (committed + preview birleşimi) ──
with col_profil:
    display_ctx = st.session_state.ctx.merge(st.session_state.preview_ctx)
    _profil_paneli(display_ctx)

# ── Sağ: Sohbet ──
with col_chat:

    # Sohbet geçmişi
    if not st.session_state.mesajlar:
        st.markdown("""
        <div style="text-align:center;padding:28px 10px 16px 10px;color:#94a3b8;">
            <div style="font-size:1.8rem;margin-bottom:8px;">👨‍⚕️</div>
            <div style="font-size:0.9rem;font-weight:500;color:#64748b;">PharmAssist'e hoş geldiniz</div>
            <div style="font-size:0.82rem;margin-top:4px;line-height:1.5;">
                Aşağıya hastanızı ve sorunuzu yazın.
            </div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.mesajlar:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                if "response" in msg:
                    _yanit_goster(msg["response"], msg.get("ctx_snapshot", ExtractedContext()))
                else:
                    st.markdown(msg["content"])

    # ── Giriş Alanı ──
    st.markdown("<div style='margin-top:16px;'>", unsafe_allow_html=True)
    soru_input = st.text_area(
        "Sorgunuz",
        height=90,
        placeholder='Örn: "68 yaşında erkek, GFR 35, warfarin kullanıyor. Klaritromisin yazabilir miyim?"',
        key="soru_textarea",
        label_visibility="collapsed",
        on_change=_on_soru_degisti,
    )

    # Buton satırı: [📎 Lab] boşluk [Sorgula →]
    btn_lab, btn_bosluk, btn_gonder = st.columns([1, 2, 1])

    with btn_lab:
        with st.popover("🧪 Lab", use_container_width=True):
            st.markdown(
                '<p style="font-size:0.8rem;font-weight:600;color:#1e3a5f;margin:0 0 4px 0">'
                'Lab Raporu Yükle</p>'
                '<p style="font-size:0.73rem;color:#94a3b8;margin:0 0 8px 0">'
                'PDF, PNG veya JPG</p>',
                unsafe_allow_html=True,
            )
            lab_dosya = st.file_uploader(
                "Dosya seç",
                type=["pdf", "png", "jpg", "jpeg"],
                key="lab_uploader",
                label_visibility="collapsed",
            )
            if lab_dosya and lab_dosya.name != st.session_state.lab_dosya_adi:
                with st.spinner("Analiz ediliyor..."):
                    try:
                        result = parse_lab_report(lab_dosya.read(), lab_dosya.name)
                        if not result.profile_values:
                            st.session_state.lab_parse_hata = "Lab değeri bulunamadı — PDF formatı tanınmadı."
                        else:
                            st.session_state.ctx.lab_degerleri.update(
                                {k: float(v) for k, v in result.profile_values.items()}
                            )
                            st.session_state.lab_dosya_adi = lab_dosya.name
                            st.session_state.lab_parse_hata = ""
                    except Exception as e:
                        st.session_state.lab_parse_hata = f"Parse hatası: {e}"
                st.rerun()

            n_lab = len(st.session_state.ctx.lab_degerleri)
            if n_lab:
                st.markdown(
                    f'<p style="font-size:0.73rem;color:#15803d;margin:6px 0 0 0">'
                    f'✅ {n_lab} değer profilde aktif</p>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<p style="font-size:0.73rem;color:#94a3b8;margin:6px 0 0 0">'
                    'Henüz değer eklenmedi</p>',
                    unsafe_allow_html=True,
                )

    with btn_gonder:
        gonder = st.button("Sorgula →", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Parse Hata Mesajı ────────────────────────────────────────────────────
    if st.session_state.get("lab_parse_hata"):
        st.error(st.session_state.lab_parse_hata)
        st.session_state.lab_parse_hata = ""

# ─── Sorgu İşleme ────────────────────────────────────────────────────────────

if gonder and soru_input and soru_input.strip():
    import copy
    soru_text = soru_input.strip()

    # 1. Kullanıcı mesajını geçmişe ekle
    st.session_state.mesajlar.append({"role": "user", "content": soru_text})

    # 2. Profil çıkar ve birleştir (ilaç listesi session'dan — spinner yok)
    ilac_listesi = st.session_state.ilac_listesi
    yeni_ctx = extract_context(soru_text, ilac_listesi)
    st.session_state.ctx = st.session_state.ctx.merge(yeni_ctx)
    ctx = st.session_state.ctx

    # 3. PatientProfile oluştur
    gfr_hesap = ctx.gfr
    if ctx.bobrek_yetmezligi and not gfr_hesap:
        gfr_hesap = 45.0
    karaciger_skoru = ctx.karaciger_skoru
    if ctx.karaciger_yetmezligi and not karaciger_skoru:
        karaciger_skoru = "B"

    profil = PatientProfile(
        yas=ctx.yas or 45,
        cinsiyet=ctx.cinsiyet or "belirtilmemiş",
        kilo=ctx.kilo,
        gfr=gfr_hesap,
        karaciger_skoru=karaciger_skoru,
        gebelik=ctx.gebelik,
        emzirme=ctx.emzirme,
        mevcut_ilaclar=ctx.mevcut_ilaclar,
        alerjiler=ctx.alerjiler,
        endikasyonlar=ctx.endikasyonlar,
        lab_degerleri=ctx.lab_degerleri,
        pediyatrik_override=True if ctx.pediyatrik else None,
        geriyatrik_override=True if ctx.geriyatrik else None,
    )

    # 4. Hedef ilaçları ChromaDB ile doğrula
    hedef_ilaclar = _eslestir_ilaclar(ctx.hedef_ilaclar, ilac_listesi) if ctx.hedef_ilaclar else None

    # 5. RAG çalıştır
    soru_for_rag = ctx.temizlenmis_soru or soru_text

    with st.spinner("KÜB kaynakları taranıyor..."):
        try:
            response = run_rag(
                soru=soru_for_rag,
                profil=profil,
                hedef_ilaclar=hedef_ilaclar,
                n_results=8,
            )
        except Exception as e:
            st.error(f"Hata: {e}")
            st.session_state.mesajlar.pop()
            st.stop()

    # 6. Yanıtı geçmişe ekle
    st.session_state.mesajlar.append({
        "role": "assistant",
        "content": response.yanit,
        "response": response,
        "ctx_snapshot": copy.copy(ctx),
    })

    # 7. Log kaydet
    _gecmis_kaydet(
        soru=soru_for_rag,
        yanit=response.yanit,
        hedef_ilaclar=hedef_ilaclar or [],
        soru_turleri=response.soru_turleri,
        chunk_sayisi=len(response.kaynaklar),
        model=response.model,
    )

    st.rerun()


# ─── Footer ─────────────────────────────────────────────────────────────────

st.markdown("""
<hr style="border:none;border-top:1px solid #e2e8f0;margin:1.5rem 0 0.5rem 0;">
<p style="text-align:center;font-size:0.75rem;color:#94a3b8;margin:0;">
    ⚠️ Bu sistem yalnızca klinik karar desteği amaçlıdır.
    Nihai karar her zaman sorumlu hekime aittir.
</p>
""", unsafe_allow_html=True)
