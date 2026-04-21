"""
FIX-3 — Combined Prompt Faithfulness Ablasyon Testi

Amac: LM Studio'da system prompt formatinin LLM yanit kalitesine etkisini izole et.

FORMAT A (mevcut): system prompt + user_prompt tek user mesaji olarak
FORMAT B (delimiter): <SYSTEM>...</SYSTEM> delimiter'i ile bölünmüs tek user mesaji

Cikti:
  data/eval/ablation_format_a.json
  data/eval/ablation_format_b.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

# Proje kökünü sys.path'e ekle
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import openai
except ImportError:
    print("HATA: openai paketi bulunamadi. '.venv/Scripts/pip install openai' calistirin.")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# LOCAL_SYSTEM_PROMPT — rag_engine.py ile ayni (kopyalanmis)
# ------------------------------------------------------------------
LOCAL_SYSTEM_PROMPT = """KONTRENDİKASYON KURALI (MUTLAK):
"Kontrendikedir", "kullanılmamalıdır", "kontrendikasyon" ifadelerini YALNIZCA
KÜB Madde 4.3 metninde AÇIKÇA bu hastalık/durum için kontrendikasyon yazıyorsa kullan.
Madde 4.2'de doz azaltımı veya Madde 4.4'te "dikkatli kullanılmalıdır" yazıyorsa:
"Dikkatli kullanılmalıdır, doz ayarı gerekebilir." veya "Yakın izlem altında kullanılabilir." ifadelerini kullan.

Sen bir klinik eczacı yapay zeka asistanısın. Sana verilen KÜB (ilaç prospektüsü) metinlerine dayanarak soruları yanıtlıyorsun.

KESİN KURALLAR — İHLAL ETME:
1. YALNIZCA "İLGİLİ KÜB BİLGİLERİ" başlığı altındaki metni kullan. Başka hiçbir kaynaktan bilgi ekleme.
2. Sorulan ilaç hangisiyse, YALNIZCA o ilaç hakkındaki KÜB metnini kullan. Farklı bir ilaç hakkında bilgi verme.
3. KÜB metninde açıkça yazmayan hiçbir şeyi söyleme. "X kontrendikedir" diyebilmek için KÜB metninde "kontrendike" veya "kullanılmamalı" gibi bir ifade geçmeli.
4. Kaynak olarak yalnızca KÜB bölümünde verilen ilaç adı ve madde numaralarını kullan. Sayfa numarası uydurma.
5. Prompt içindeki ## başlıklarını veya talimat metinlerini yanıtına KOPYALAMA.
6. Yanıtı şu yapıda ver — başka format kullanma:
   ### 1. Kısa Özet
   ### 2. Detaylı Analiz
   ### 3. Önemli Uyarılar
   ### 4. Kaynaklar
7. Türkçe yanıt ver."""


# ------------------------------------------------------------------
# Yardimci: basit user_prompt olustur (RAG pipeline'siz)
# ------------------------------------------------------------------

def _build_minimal_user_prompt(soru: str, hasta: dict, hedef_ilaclar: list[str]) -> str:
    """
    Pipeline overhead olmadan sadece soru + hasta özeti iceren minimal prompt.
    Bu sayede FORMAT farki izole edilir; retrieval farklilik kaynagi olarak gelmez.
    """
    ilaclar_str = ", ".join(hedef_ilaclar) if hedef_ilaclar else "belirtilmedi"
    mevcut_str = ", ".join(hasta.get("mevcut_ilaclar") or []) or "yok"

    hasta_ozeti = (
        f"Yas: {hasta.get('yas', '?')}, Cinsiyet: {hasta.get('cinsiyet', '?')}, "
        f"GFR: {hasta.get('gfr') or 'bilinmiyor'}, "
        f"Karaciger: {hasta.get('karaciger_skoru') or 'normal'}, "
        f"Gebelik: {'evet' if hasta.get('gebelik') else 'hayir'}, "
        f"Emzirme: {'evet' if hasta.get('emzirme') else 'hayir'}, "
        f"Mevcut ilaclar: {mevcut_str}"
    )

    return (
        f"## HASTA PROFİLİ\n{hasta_ozeti}\n\n"
        f"## HEDEF İLAÇLAR\n{ilaclar_str}\n\n"
        f"## İLGİLİ KÜB BİLGİLERİ\n"
        f"[ABLASYON TESTİ: KÜB bağlamı sağlanmamıştır. "
        f"Yalnızca prompt format etkisi ölçülmektedir.]\n\n"
        f"## SORU\n{soru}"
    )


# ------------------------------------------------------------------
# LLM cagri fonksiyonlari (her format icin ayri)
# ------------------------------------------------------------------

def _call_format_a(client: openai.OpenAI, model: str, user_prompt: str, max_tokens: int) -> str:
    """FORMAT A: system + user tek mesajda, düz birleştirme (mevcut uygulama)."""
    combined = f"{LOCAL_SYSTEM_PROMPT}\n\n{user_prompt}"
    resp = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0.1,
        messages=[{"role": "user", "content": combined}],
    )
    return resp.choices[0].message.content or ""


def _call_format_b(client: openai.OpenAI, model: str, user_prompt: str, max_tokens: int) -> str:
    """FORMAT B: <SYSTEM>...</SYSTEM> delimiter'li birleştirme."""
    combined = f"<SYSTEM>\n{LOCAL_SYSTEM_PROMPT}\n</SYSTEM>\n\n{user_prompt}"
    resp = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0.1,
        messages=[{"role": "user", "content": combined}],
    )
    return resp.choices[0].message.content or ""


def _call_format_system_role(
    client: openai.OpenAI, model: str, user_prompt: str, max_tokens: int
) -> tuple[str, bool]:
    """
    Opsiyonel FORMAT C: gercek system role.
    Bazi modeller (Gemma, Llama) bunu desteklemez; crash durumunda FORMAT A'ya fallback.
    Donus: (yanit, system_role_desteklendi)
    """
    try:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.1,
            messages=[
                {"role": "system", "content": LOCAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content or "", True
    except Exception as exc:
        logger.warning(f"System role desteklenmiyor, FORMAT A'ya fallback: {exc}")
        return _call_format_a(client, model, user_prompt, max_tokens), False


# ------------------------------------------------------------------
# Ana isleme
# ------------------------------------------------------------------

def run_ablation(
    questions_path: Path,
    output_dir: Path,
    max_questions: int | None,
    max_tokens: int,
    include_system_role: bool,
    delay: float,
) -> None:
    base_url = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")
    model_name = os.environ.get("LOCAL_MODEL_NAME", "local-model")

    logger.info(f"LM Studio: {base_url} | Model: {model_name}")

    client = openai.OpenAI(base_url=base_url, api_key="lm-studio")

    # Sorulari yukle
    with open(questions_path, encoding="utf-8") as f:
        questions: list[dict] = json.load(f)

    if max_questions:
        questions = questions[:max_questions]

    logger.info(f"{len(questions)} soru islenecek.")

    results_a: list[dict] = []
    results_b: list[dict] = []
    results_sys: list[dict] = []  # opsiyonel FORMAT C

    for i, q in enumerate(questions, 1):
        qid = q.get("id", f"q{i:02d}")
        soru = q.get("soru", "")
        hasta = q.get("hasta", {})
        hedef = q.get("hedef_ilaclar", [])

        logger.info(f"[{i}/{len(questions)}] {qid}: {soru[:60]}...")

        user_prompt = _build_minimal_user_prompt(soru, hasta, hedef)

        # FORMAT A
        try:
            ans_a = _call_format_a(client, model_name, user_prompt, max_tokens)
        except Exception as e:
            logger.error(f"FORMAT A hata ({qid}): {e}")
            ans_a = f"HATA: {e}"

        results_a.append({
            "question_id": qid,
            "soru": soru,
            "format": "A",
            "format_desc": "system+user tek mesajda düz birleştirme",
            "answer": ans_a,
            "answer_len": len(ans_a),
        })

        if delay > 0:
            time.sleep(delay)

        # FORMAT B
        try:
            ans_b = _call_format_b(client, model_name, user_prompt, max_tokens)
        except Exception as e:
            logger.error(f"FORMAT B hata ({qid}): {e}")
            ans_b = f"HATA: {e}"

        results_b.append({
            "question_id": qid,
            "soru": soru,
            "format": "B",
            "format_desc": "<SYSTEM>...</SYSTEM> delimiter'li birleştirme",
            "answer": ans_b,
            "answer_len": len(ans_b),
        })

        if delay > 0:
            time.sleep(delay)

        # Opsiyonel FORMAT C (system role)
        if include_system_role:
            ans_sys, supported = _call_format_system_role(client, model_name, user_prompt, max_tokens)
            results_sys.append({
                "question_id": qid,
                "soru": soru,
                "format": "C_system_role",
                "format_desc": "gercek system role (model destekliyorsa)",
                "system_role_supported": supported,
                "answer": ans_sys,
                "answer_len": len(ans_sys),
            })
            if delay > 0:
                time.sleep(delay)

    # Kaydet
    output_dir.mkdir(parents=True, exist_ok=True)
    path_a = output_dir / "ablation_format_a.json"
    path_b = output_dir / "ablation_format_b.json"

    with open(path_a, "w", encoding="utf-8") as f:
        json.dump(results_a, f, ensure_ascii=False, indent=2)
    logger.info(f"FORMAT A kayit: {path_a}")

    with open(path_b, "w", encoding="utf-8") as f:
        json.dump(results_b, f, ensure_ascii=False, indent=2)
    logger.info(f"FORMAT B kayit: {path_b}")

    if include_system_role and results_sys:
        path_sys = output_dir / "ablation_format_c_sysrole.json"
        with open(path_sys, "w", encoding="utf-8") as f:
            json.dump(results_sys, f, ensure_ascii=False, indent=2)
        logger.info(f"FORMAT C (system role) kayit: {path_sys}")

    # Özet
    n = len(questions)
    avg_a = sum(r["answer_len"] for r in results_a) / n if n else 0
    avg_b = sum(r["answer_len"] for r in results_b) / n if n else 0

    print("\n" + "=" * 60)
    print("ABLASYON TESTİ ÖZET")
    print("=" * 60)
    print(f"  İşlenen soru sayısı : {n}")
    print(f"  FORMAT A ort. uzunluk: {avg_a:.0f} karakter")
    print(f"  FORMAT B ort. uzunluk: {avg_b:.0f} karakter")

    if include_system_role and results_sys:
        avg_sys = sum(r["answer_len"] for r in results_sys) / n
        desteklenen = sum(1 for r in results_sys if r.get("system_role_supported"))
        print(f"  FORMAT C ort. uzunluk: {avg_sys:.0f} karakter")
        print(f"  System role destekleyen: {desteklenen}/{n}")

    print(f"\n  Cikti dosyalari: {output_dir}")
    print("=" * 60)
    print("\nSonraki adim: Bu dosyalar üzerinde RAGAS degerlendir.")
    print("  scripts/ragas_eval.py --format-a data/eval/ablation_format_a.json ...")


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FIX-3: Prompt format ablasyon testi (FORMAT A vs B vs C)"
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=Path("data/eval/ragas_v3_questions.json"),
        help="Soru seti JSON dosyasi (varsayilan: data/eval/ragas_v3_questions.json)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/eval"),
        help="Cikti dizini (varsayilan: data/eval)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        metavar="N",
        help="Islenecek maksimum soru sayisi (tümü için belirtme)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="LLM yanit icin max token (varsayilan: 512)",
    )
    parser.add_argument(
        "--include-system-role",
        action="store_true",
        help="FORMAT C (gercek system role) de dahil et — crash durumunda FORMAT A'ya fallback",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Her LLM cagrisi arasinda bekleme saniyesi (varsayilan: 0.5)",
    )

    args = parser.parse_args()

    questions_path = PROJECT_ROOT / args.questions if not args.questions.is_absolute() else args.questions
    output_dir = PROJECT_ROOT / args.output_dir if not args.output_dir.is_absolute() else args.output_dir

    if not questions_path.exists():
        logger.error(f"Soru dosyasi bulunamadi: {questions_path}")
        sys.exit(1)

    run_ablation(
        questions_path=questions_path,
        output_dir=output_dir,
        max_questions=args.max,
        max_tokens=args.max_tokens,
        include_system_role=args.include_system_role,
        delay=args.delay,
    )


if __name__ == "__main__":
    main()
