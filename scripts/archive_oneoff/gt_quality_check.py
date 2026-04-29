"""
GT Kalite Check - RAGAS ground truth doğrulama scripti.
Kullanım: .venv/Scripts/python scripts/gt_quality_check.py data/eval/ragas_v3_questions.json
"""

import json
import re
import sys
from pathlib import Path

MECHANISM_WORDS = ['cyp', 'enzim', 'inhibitör', 'inhibisyon', 'indükleme', 'indüksiyon', 'substrat']
ACTION_WORDS = ['izlem', 'doz', 'takip', 'kontrol', 'dikkat', 'önlem', 'alternatif']
DOSE_RE = re.compile(r'\d+[\.,]?\d*\s*(?:mg|mcg|µg)', re.IGNORECASE)

# Pozitif KI pattern: "kontrendike" ama "kontrendike değil" değil
KI_POSITIVE_RE = re.compile(r'kontrendike(?!\s+değil)')


def tr_lower(s: str) -> str:
    return (s.replace('İ', 'i').replace('I', 'ı')
             .replace('Ş', 'ş').replace('Ğ', 'ğ')
             .replace('Ü', 'ü').replace('Ö', 'ö')
             .replace('Ç', 'ç').lower())


def check_item(item: dict) -> list[str]:
    flags = []
    soru = tr_lower(item.get('soru', ''))
    gt_raw = item.get('ground_truth', '')
    gt = tr_lower(gt_raw)

    # KURAL 1 — KI/dikkatli kullanım ayrımı
    if 'kontrendikedir' in gt or 'kullanılmamalıdır' in gt:
        flags.append('GT_KI_CLAIM')

    # KURAL 2 — Mekanizma zorunluluğu (etkileşim soruları)
    if any(w in soru for w in ['etkileşim', 'cyp', 'birlikte']):
        if not any(w in gt for w in MECHANISM_WORDS):
            flags.append('MISSING_MECHANISM')

    # KURAL 3 — Doz soruları sayısal değer içermeli
    if any(w in soru for w in ['doz', 'mg', 'pozoloji']):
        if not DOSE_RE.search(gt_raw):
            flags.append('MISSING_DOSE_VALUE')

    # KURAL 4 — Kontrendike ise alternatif belirtilmeli
    has_ki = bool(KI_POSITIVE_RE.search(gt)) or 'kullanılamaz' in gt
    if has_ki and 'alternatif' not in gt:
        flags.append('MISSING_ALTERNATIVE')

    # KURAL 5 — Klinik aksiyon kelimesi
    if not any(w in gt for w in ACTION_WORDS):
        flags.append('MISSING_CLINICAL_ACTION')

    return flags


def main():
    if len(sys.argv) < 2:
        print("Kullanım: python scripts/gt_quality_check.py <json_dosyası>")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"HATA: Dosya bulunamadı: {json_path}")
        sys.exit(1)

    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    results = []
    for item in data:
        flags = check_item(item)
        if flags:
            results.append({
                'soru_id': item['id'],
                'flags': flags,
                'gt_ozet': item['ground_truth'][:100]
            })

    output = {
        'toplam_soru': len(data),
        'sorunlu_soru_sayisi': len(results),
        'sonuclar': results
    }

    # Terminal çıktısı
    sep = '=' * 60
    print(f"\n{sep}")
    print("GT KALİTE RAPORU")
    print(sep)
    print(f"Dosya          : {json_path}")
    print(f"Toplam soru    : {len(data)}")
    print(f"Sorunlu soru   : {len(results)}")
    print(sep)

    flag_counts: dict[str, int] = {}
    for r in results:
        for f in r['flags']:
            flag_counts[f] = flag_counts.get(f, 0) + 1

    print("\nFlag özeti:")
    for flag, count in sorted(flag_counts.items(), key=lambda x: -x[1]):
        print(f"  {flag:<26} {count} soru")

    print(f"\n{sep}")
    print("Detay:")
    print(sep)
    for r in results:
        print(f"\n[{r['soru_id']}]  {', '.join(r['flags'])}")
        print(f"  GT: {r['gt_ozet']}...")

    # JSON raporu kaydet
    out_path = json_path.parent / 'gt_quality_report.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n\nJSON raporu kaydedildi: {out_path}")


if __name__ == '__main__':
    main()
