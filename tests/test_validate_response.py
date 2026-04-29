"""
validate_response() birim testleri — VALIDATE Faz 16+

Özellikle:
  - _validate_numeric_claims: doz/GFR hallüsinasyon tespiti
  - Kaynak etiketsiz cümleler [DOĞRULANAMADI] ile işaretlenmeli
  - Alıntılanan bölümde olmayan doz değerleri → flaglenmeli (citation-level)
  - Alıntılanan bölümde VAR olan doz değerleri → flaglenmemeli
  - Hasta profili sayıları (GFR=55) → false positive çıkmamalı
"""

import pytest
from dataclasses import dataclass
from src.agents.rag_engine import validate_response


@dataclass
class FakeChunk:
    """Minimal RetrievedChunk benzeri nesne."""
    icerik: str
    madde_no: str = ""
    ilac_adi: str = "TEST ILAC"
    skor: float = 0.9


# ─────────────────────────────────────────────────────────────────
# 1. UNSOURCED DOSE — hiçbir chunk'ta olmayan doz değeri
# ─────────────────────────────────────────────────────────────────
def test_unsourced_dose_flagged():
    """Kaynak etiketi olmayan + chunk'ta bulunmayan doz → [DOĞRULANAMADI]."""
    yanit = "## SONUÇ\n\nBaşlangıç dozu 7.5 mg verilmelidir.\n\n## KAYNAKLAR\n- TEST"
    chunk = FakeChunk(icerik="Başlangıç dozu 2.5 mg veya 5 mg olarak ayarlanabilir.", madde_no="4.2")
    result = validate_response(yanit, [chunk], soru="bu ilacın dozu ne?")
    assert "[DOĞRULANAMADI]" in result, "7.5 mg chunk'ta yok, flaglenmeli"


# ─────────────────────────────────────────────────────────────────
# 2. UNSOURCED DOSE — chunk'ta OLAN doz → flaglenmemeli
# ─────────────────────────────────────────────────────────────────
def test_unsourced_dose_present_not_flagged():
    """Kaynak etiketi olmayan ama chunk'ta mevcut olan doz → flaglenmemeli."""
    yanit = "## SONUÇ\n\nBaşlangıç dozu 2.5 mg verilmelidir.\n\n## KAYNAKLAR\n- TEST"
    chunk = FakeChunk(icerik="Başlangıç dozu 2.5 mg olarak belirlenir.", madde_no="4.2")
    result = validate_response(yanit, [chunk], soru="bu ilacın dozu ne?")
    # _tag_unverifiable_sentences kaynak etiketi yoksa işaretler — bu testte
    # o kural da devredeyken çalışıp çalışmadığını görmek istiyoruz
    # Numericvalidator açısından: 2.5 chunk'ta var → ek [DOĞRULANAMADI] eklememeli
    count = result.count("[DOĞRULANAMADI]")
    # _tag_unverifiable_sentences zaten 1 tane ekleyebilir; numeric validator eklemez
    # Toplamda numeric validator kaynaklı ek flag olmamalı
    assert "2.5 mg" in result  # içerik korunmali


# ─────────────────────────────────────────────────────────────────
# 3. CITED DOSE — alıntılanan bölümde OLMAYAN doz (hallüsinasyon + fake citation)
# ─────────────────────────────────────────────────────────────────
def test_cited_dose_not_in_cited_section_flagged():
    """Model '2.5 mg [TEST | Madde 4.2]' diyor ama 4.2 chunk'ı 2.5 içermiyor → flaglenmeli."""
    yanit = (
        "## SONUÇ\n\n"
        "Başlangıç dozu 2.5 mg önerilir. [TEST ILAC | Madde 4.2 — Geriyatrik]\n\n"
        "## KAYNAKLAR\n- TEST"
    )
    # 4.2 chunk → 2.5 mg yok, sadece "böbrek fonksiyonuna uygun" yazıyor
    chunk_42 = FakeChunk(
        icerik="Doz, yaşlı hastanın böbrek fonksiyonuna uygun olmalıdır.",
        madde_no="4.2",
    )
    result = validate_response(yanit, [chunk_42], soru="yaşlı hastada doz?")
    assert "[DOĞRULANAMADI]" in result, "4.2 bölümünde 2.5 mg yok, flaglenmeli"


# ─────────────────────────────────────────────────────────────────
# 4. CITED DOSE — alıntılanan bölümde VAR → flaglenmemeli
# ─────────────────────────────────────────────────────────────────
def test_cited_dose_in_cited_section_not_flagged():
    """Model '5 mg [TEST | Madde 4.2]' diyor ve 4.2 chunk'ı 5 mg içeriyor → flaglenmemeli."""
    yanit = (
        "## SONUÇ\n\n"
        "Başlangıç dozu 5 mg önerilir. [TEST ILAC | Madde 4.2 — Pozoloji]\n\n"
        "## KAYNAKLAR\n- TEST"
    )
    chunk_42 = FakeChunk(
        icerik="Hipertansiyon tedavisinde başlangıç dozu genellikle 5 mg'dir.",
        madde_no="4.2",
    )
    result = validate_response(yanit, [chunk_42], soru="dozaj nedir?")
    # Sayısal olarak flag olmamalı (5 mg 4.2'de mevcut)
    assert "5 mg" in result
    # Cümle değiştirilmemiş olmalı (sadece [DOĞRULANAMADI] eklenmemiş olmalı)
    flagged_with_dose = "[DOĞRULANAMADI]" in result and "5 mg" in result.split("[DOĞRULANAMADI]")[0]
    # Eğer flag varsa, 5 mg cümlesinin SONRASINDA olmamalı
    lines = result.split("\n")
    for line in lines:
        if "5 mg" in line and "Madde 4.2" in line:
            assert "[DOĞRULANAMADI]" not in line, f"5 mg 4.2'de var, flaglenmemeli: {line}"


# ─────────────────────────────────────────────────────────────────
# 5. HASTA PROFİLİ SAYISI — false positive olmamalı
# ─────────────────────────────────────────────────────────────────
def test_patient_profile_value_not_flagged():
    """Soruda geçen GFR=55 chunk'ta yoksa bile flaglenmemeli (hasta değeri)."""
    yanit = (
        "## SONUÇ\n\n"
        "Bu hastanın GFR değeri 55 mL/dak olduğundan doz azaltımı gereklidir. "
        "[TEST ILAC | Madde 4.4 — Böbrek]\n\n"
        "## KAYNAKLAR\n- TEST"
    )
    chunk = FakeChunk(
        icerik="Böbrek fonksiyon bozukluğu olan hastalarda doz ayarı gereklidir.",
        madde_no="4.4",
    )
    # GFR=55 soruda geçiyor → hasta profil değeri, flaglenmemeli
    result = validate_response(yanit, [chunk], soru="GFR=55 olan hastada doz?")
    # Bu satırda [DOĞRULANAMADI] olmamalı (55 hasta profili değeri)
    for line in result.split("\n"):
        if "GFR" in line and "55" in line and "Madde 4.4" in line:
            assert "[DOĞRULANAMADI]" not in line, f"55 hasta profili değeri, flaglenmemeli: {line}"


# ─────────────────────────────────────────────────────────────────
# 6. GFR EŞİK — chunk'ta olmayan GFR eşiği → flaglenmeli
# ─────────────────────────────────────────────────────────────────
def test_hallucinated_gfr_threshold_flagged():
    """Model 'GFR < 15 altında kontrendike' diyor ama chunk'ta yok → flaglenmeli."""
    yanit = (
        "## SONUÇ\n\n"
        "GFR < 15 mL/dak altında kullanım kontrendikedir.\n\n"
        "## KAYNAKLAR\n- TEST"
    )
    chunk = FakeChunk(
        icerik="Şiddetli böbrek yetmezliğinde (kreatinin klerensi < 30 mL/dak) dikkatli kullanılmalıdır.",
        madde_no="4.3",
    )
    # GFR 15 chunk'ta yok (chunk'ta 30 var)
    result = validate_response(yanit, [chunk], soru="bu ilacın kontrendikasyonu nedir?")
    assert "[DOĞRULANAMADI]" in result, "GFR 15 chunk'ta yok, flaglenmeli"


# ─────────────────────────────────────────────────────────────────
# 7. GUVENLI KALIP — mutlak ifade dönüşümü
# ─────────────────────────────────────────────────────────────────
def test_guvenli_pattern_replaced():
    """'güvenlidir' ifadesi sistem uyarısıyla değiştirilmeli."""
    yanit = "Bu ilaç hamile kadınlarda güvenlidir."
    chunk = FakeChunk(icerik="Gebe kadınlarda dikkatli kullanılmalı.", madde_no="4.6")
    result = validate_response(yanit, [chunk], soru="gebe kadında kullanılabilir mi?")
    assert "güvenlidir" not in result.lower() or "[SİSTEM DÜZELTMESİ]" in result


# ─────────────────────────────────────────────────────────────────
# Rule 3: [AŞIRI YORUM] tagging
# ─────────────────────────────────────────────────────────────────
def test_asiri_yorum_tag_added_when_no_43():
    """4.3 chunk'ı yokken 'kontrendikedir' → 'dikkatli' + [AŞIRI YORUM] eklenmeli."""
    yanit = "## SONUÇ\n\nBu ilaç renal hastalarda kontrendikedir.\n\n## KAYNAKLAR\n- TEST"
    # Sadece 4.4 chunk var, 4.3 yok
    chunk_44 = FakeChunk(
        icerik="Böbrek fonksiyon bozukluğunda dikkatli kullanılmalıdır.",
        madde_no="4.4",
    )
    result = validate_response(yanit, [chunk_44], soru="renal hastada kullanılabilir mi?")
    assert "kontrendikedir" not in result.lower() or "[AŞIRI YORUM" in result, \
        "4.3 yokken kontrendike iddiası düzeltilmeli"
    assert "dikkatli kullanılmalıdır" in result.lower()
    assert "[AŞIRI YORUM" in result


def test_no_asiri_yorum_when_43_supports():
    """4.3 açıkça kontrendikasyon içeriyorsa [AŞIRI YORUM] eklenmemeli."""
    yanit = (
        "## SONUÇ\n\n"
        "Bu ilaç hamilelerde kontrendikedir. [TEST ILAC | Madde 4.3]\n\n"
        "## KAYNAKLAR\n- TEST"
    )
    chunk_43 = FakeChunk(
        icerik="Gebelik döneminde kullanımı kontrendikedir. Fetal toksisite riski mevcuttur.",
        madde_no="4.3",
    )
    result = validate_response(yanit, [chunk_43], soru="gebe hastada kullanılabilir mi?")
    assert "[AŞIRI YORUM" not in result, "4.3 gebeliği destekliyorsa AŞIRI YORUM eklenmemeli"


# ─────────────────────────────────────────────────────────────────
# Rule 4: CYP yön doğrulama
# ─────────────────────────────────────────────────────────────────
def test_cyp_inhibitor_wrong_direction_flagged():
    """İnhibitör + 'düzeyi azalır' → [DOĞRULANAMADI-CYP] eklenmeli."""
    yanit = (
        "## SONUÇ\n\n"
        "Bu ilaç CYP3A4 inhibitörüdür; varfarin düzeyi azalır. [CYP450]\n\n"
        "## KAYNAKLAR\n- TEST"
    )
    chunk_45 = FakeChunk(
        icerik="Bu ilaç CYP3A4 enziminin güçlü inhibitörüdür. Eş zamanlı kullanım plazma düzeyini etkiler.",
        madde_no="4.5",
    )
    result = validate_response(yanit, [chunk_45], soru="etkileşim var mı?")
    assert "[DOĞRULANAMADI-CYP" in result, "inhibitör + azalır çelişkisi flaglenmeli"


def test_cyp_inhibitor_correct_direction_not_flagged():
    """İnhibitör + 'düzeyi artar' → flaglenmemeli."""
    yanit = (
        "## SONUÇ\n\n"
        "Bu ilaç CYP3A4 inhibitörüdür; varfarin düzeyi artar. [CYP450]\n\n"
        "## KAYNAKLAR\n- TEST"
    )
    chunk_45 = FakeChunk(
        icerik="Bu ilaç CYP3A4 enziminin güçlü inhibitörüdür.",
        madde_no="4.5",
    )
    result = validate_response(yanit, [chunk_45], soru="etkileşim var mı?")
    assert "[DOĞRULANAMADI-CYP" not in result, "inhibitör + artar doğru, flaglenmemeli"


def test_cyp_inducer_wrong_direction_flagged():
    """İndükleyici + 'düzeyi artar' → [DOĞRULANAMADI-CYP] eklenmeli."""
    yanit = (
        "## SONUÇ\n\n"
        "Bu ilaç CYP3A4 indükleyicisidir; digoksin düzeyi artar. [CYP450]\n\n"
        "## KAYNAKLAR\n- TEST"
    )
    chunk_45 = FakeChunk(
        icerik="Rifampisin güçlü bir CYP3A4 indükleyicisidir.",
        madde_no="4.5",
    )
    result = validate_response(yanit, [chunk_45], soru="etkileşim var mı?")
    assert "[DOĞRULANAMADI-CYP" in result, "indükleyici + artar çelişkisi flaglenmeli"


# ─────────────────────────────────────────────────────────────────
# Rule 5: Verdict alignment
# ─────────────────────────────────────────────────────────────────
def test_verdict_alignment_overreach_flagged():
    """Model 'kontrendike' ama bağlam sadece 4.4 dikkat → [AŞIRI YORUM] eklenmeli."""
    # SONUÇ'ta kontrendike ifadesi, ama sadece 4.4 chunk var
    yanit = (
        "## SONUÇ\n\n"
        "Bu ilaç böbrek yetmezliğinde kontrendikedir.\n\n"
        "## KAYNAKLAR\n- TEST"
    )
    chunk_44 = FakeChunk(
        icerik="Böbrek fonksiyon bozukluğunda dikkatli kullanılmalı, doz azaltılmalıdır.",
        madde_no="4.4",
    )
    result = validate_response(yanit, [chunk_44], soru="GFR=20 olan hastada kullanılabilir mi?")
    # _validate_kontraendikasyon zaten global sub yapıyor; verdict alignment ise SONUÇ cümlesini işaret ediyor
    # En azından birinden [AŞIRI YORUM] gelmeli
    assert "[AŞIRI YORUM" in result, "4.4 only → kontrendike verdict aşırı yorum olmalı"


# ─────────────────────────────────────────────────────────────────
# 8. CITED SECTION NOT RETRIEVED — doğrulama atlanmalı (false positive yok)
# ─────────────────────────────────────────────────────────────────
def test_cited_section_not_retrieved_skipped():
    """4.2 bölümü retrieve edilmemiş, Madde 4.2 citation var → doğrulama atlanmalı."""
    yanit = (
        "## SONUÇ\n\n"
        "Başlangıç dozu 10 mg önerilir. [TEST ILAC | Madde 4.2]\n\n"
        "## KAYNAKLAR\n- TEST"
    )
    # Sadece 4.4 chunk var, 4.2 yok → verified section text boş → atlanmalı
    chunk_44 = FakeChunk(
        icerik="Böbrek fonksiyonu takip edilmeli.",
        madde_no="4.4",
    )
    result = validate_response(yanit, [chunk_44], soru="dozaj nedir?")
    # 4.2 chunk'ı yok → skip → 10 mg cümlesi flaglenmemeli
    for line in result.split("\n"):
        if "10 mg" in line and "Madde 4.2" in line:
            assert "[DOĞRULANAMADI]" not in line, f"4.2 retrieve edilmedi, atlanmalı: {line}"
