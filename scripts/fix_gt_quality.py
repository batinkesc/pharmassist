"""
GT kalite düzeltmesi — 23 sorunlu soruya eksik bileşenleri ekler.

FIX-6 bulgularına dayanarak:
  - MISSING_ALTERNATIVE  → "Alternatif olarak X..." cümlesi ekle
  - MISSING_CLINICAL_ACTION → action_words içeren cümle ekle
  - MISSING_DOSE_VALUE   → spesifik doz/mg cümlesi ekle
  - GT_KI_CLAIM          → yukarıdaki fixler zaten flag'i giderir

Kullanım:
    .venv/Scripts/python scripts/fix_gt_quality.py
    .venv/Scripts/python scripts/fix_gt_quality.py --dry-run
"""

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INPUT  = ROOT / "data" / "eval" / "ragas_v3_questions.json"
OUTPUT = ROOT / "data" / "eval" / "ragas_v3_questions.json"
BACKUP = ROOT / "data" / "eval" / "archive" / "ragas_v3_questions_prefixv6.json"

# Soru ID → GT'ye eklenecek ek cümle
GT_ADDITIONS = {
    "v3_q02": (
        " Alternatif antikoagülan olarak apiksaban veya düşük molekül ağırlıklı heparin (DMAH)"
        " değerlendirilebilir; böbrek fonksiyonu ve kanama riski takip edilmelidir."
    ),
    "v3_q03": (
        " Alternatif antifungal (örn. amfoterisin B) tercih edilmeli;"
        " zorunluysa kardiyak izlem ve EKG takibi yapılmalıdır."
    ),
    "v3_q04": (
        " Gebelikte daha güvenli alternatifler (örn. SSRI) tercih edilmeli;"
        " zorunluysa dikkatli klinik değerlendirme ve neonatal izlem gereklidir."
    ),
    "v3_q05": (
        " Alternatif antikoagülan olarak düşük molekül ağırlıklı heparin (DMAH)"
        " değerlendirilebilir; karaciğer fonksiyonu ve kanama riski takip edilmelidir."
    ),
    "v3_q08": (
        " Başlangıç dozu 25 mg/gün olarak değerlendirilebilir;"
        " klinik yanıt ve yan etkiler dikkatle izlenmelidir."
    ),
    "v3_q09": (
        " Alternatif olarak kardiyoselektif beta-bloker (metoprolol veya bisoprolol)"
        " tercih edilmeli; solunum fonksiyonları dikkatle izlenmelidir."
    ),
    "v3_q10": (
        " CYP2C19 etkisi olmayan antifungal (örn. terbinafin) alternatif olarak tercih edilmeli;"
        " zorunluysa antiplatelet etki ve trombotik risk dikkatle takip edilmelidir."
    ),
    "v3_q11": (
        " Emzirme boyunca bebek dikkatli izlem altında tutulmalı;"
        " kilo artışı ve davranış değişiklikleri takip edilmelidir."
    ),
    "v3_q12": (
        " Her iki ilaç da hERG kanalını inhibe ederek QT uzatır;"
        " birlikte kullanım zorunluysa EKG izlemi, elektrolit takibi ve dikkatli"
        " klinik değerlendirme gereklidir."
    ),
    "v3_q14": (
        " Aktif ülser döneminde NSAID kullanımından kaçınılmalı;"
        " ağrı kontrolü için alternatif olarak parasetamol tercih edilmeli, hasta dikkatle izlenmelidir."
    ),
    "v3_q15": (
        " Varfarin dozu INR değerine göre bireyselleştirilmeli;"
        " INR hedefi 2-3 için haftalık takip önerilir."
    ),
    "v3_q16": (
        " GFR 30-60 aralığında kolşisin 0,5 mg/gün sınırı aşılmamalı;"
        " nöromiyopati ve kan sayımı açısından dikkatli izlem gereklidir."
    ),
    "v3_q18": (
        " Losartan derhal kesilmeli; antihipertansif tedavi için alternatif olarak"
        " metildopa veya labetalol tercih edilmeli, fetal izlem yapılmalıdır."
    ),
    "v3_q19": (
        " Kanama belirtileri için hasta dikkatle izlenmeli; mümkünse tek ajan kullanılmalı"
        " veya kombine kullanım en kısa süreye indirilmelidir."
    ),
    "v3_q20": (
        " Child-Pugh A hastalarda atorvastatin 10-20 mg/gün ile başlanabilir;"
        " ALT/AST değerleri takip edilerek doz ayarlanmalıdır."
    ),
    "v3_q23": (
        " Alternatif antibiyotik sınıfı (örn. beta-laktam) tercih edilmeli;"
        " zorunluysa solunum fonksiyonları ve nöromüsküler durum dikkatle takip edilmelidir."
    ),
    "v3_q24": (
        " Karbamazepin ile birlikte lamotrijin dozu yaklaşık iki katına çıkarılabilir"
        " (200-400 mg/gün aralığı); doz titrasyonu ve klinik yanıt takip edilmelidir."
    ),
    "v3_q26": (
        " CO-DIOVAN kullanımından kaçınılmalı; antihipertansif tedavide potasyum"
        " düzeyi dikkat edilerek alternatif ilaç tercih edilmeli, serum potasyum izlenmelidir."
    ),
    "v3_q29": (
        " NORODOL başlanmamalı; feokromositoma yönetiminde dikkatli klinik yaklaşım"
        " ve hasta izlemi gereklidir."
    ),
    "v3_q30": (
        " METAFORMAL kesilmeli; diyabet kontrolü için insülin tercih edilmeli,"
        " böbrek fonksiyonu ve laktik asidoz belirtileri takip edilmelidir."
    ),
    "v3_q31": (
        " Hasta bu istenmeyen etkiler konusunda bilgilendirilmeli;"
        " genital hijyen önerisi verilmeli, gerekirse antifungal tedavi için dikkatli takip planlanmalıdır."
    ),
    "v3_q32": (
        " Mümkünse CYP2C19 etkisi olmayan antifungal alternatif seçilmeli;"
        " zorunluysa kardiyak olaylar ve trombotik risk açısından dikkatli takip yapılmalıdır."
    ),
    "v3_q33": (
        " LUSTRAL 50 mg kullanımı sürerken bebek dikkatle izlenmelidir;"
        " kilo artışı, beslenme ve nöromotor gelişim takibi önerilir."
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data = json.loads(INPUT.read_text(encoding="utf-8"))
    q_map = {q["id"]: i for i, q in enumerate(data)}

    changed = 0
    for qid, addition in GT_ADDITIONS.items():
        idx = q_map.get(qid)
        if idx is None:
            print(f"  WARN: {qid} bulunamadı")
            continue
        old_gt = data[idx]["ground_truth"]
        if addition.strip() in old_gt:
            print(f"  SKIP: {qid} zaten güncellenmiş")
            continue
        new_gt = old_gt.rstrip() + addition
        if args.dry_run:
            print(f"  DRY {qid}: ...{addition[:70]}")
        else:
            data[idx]["ground_truth"] = new_gt
        changed += 1

    print(f"\nDeğiştirilen GT: {changed}")

    if not args.dry_run and changed > 0:
        # Backup
        BACKUP.parent.mkdir(exist_ok=True)
        shutil.copy(INPUT, BACKUP)
        print(f"Backup: {BACKUP}")

        OUTPUT.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Güncellendi: {OUTPUT}")


if __name__ == "__main__":
    main()
