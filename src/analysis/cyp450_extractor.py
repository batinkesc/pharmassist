import os
import json
import re
from loguru import logger
import anthropic
import openai
from dotenv import load_dotenv

load_dotenv(override=True)

# Prompts
CYP_EXTRACTION_SYSTEM_PROMPT = """Sen bir farmakoloji uzmanısın. Sana verilen ilaç prospektüsü (KÜB Madde 4.5) metninden, ilgili ilacın CYP450 enzim profilini çıkarman gerekiyor.

Çıkarılacak roller:
1. substrat (substrate): İlacın hangi enzimler tarafından metabolize edildiği.
2. inhibitor (inhibitor): İlacın hangi enzimleri baskıladığı.
3. induktor (inducer): İlacın hangi enzimleri uyardığı.

Yanıtını YALNIZCA aşağıdaki JSON formatında ver. Hiçbir açıklama ekleme:
{
  "substrat": ["CYP..."],
  "inhibitor": ["CYP..."],
  "induktor": ["CYP..."]
}

Eğer metinde bilgi yoksa boş liste döndür. Sadece CYP ile başlayan enzim isimlerini (örn: CYP3A4, CYP2C9) kullan."""

def extract_cyp_profile_from_text(text: str, drug_name: str) -> dict:
    """
    LLM kullanarak metinden CYP profilini çıkarır.
    """
    provider = os.environ.get("LLM_PROVIDER", "local").lower()  # CRITICAL: Default must be local (no API cost)
    
    user_prompt = f"İlaç: {drug_name}\n\nKÜB Madde 4.5 Metni:\n{text}"
    
    try:
        if provider == "local":
            return _call_local_extraction(user_prompt)
        else:
            return _call_claude_extraction(user_prompt)
    except Exception as e:
        logger.error(f"CYP extraction hatası ({drug_name}): {e}")
        return {"substrat": [], "inhibitor": [], "induktor": []}

def _call_claude_extraction(prompt: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    # CRITICAL: Must explicitly set, NO claude default
    model = os.environ.get("ANTHROPIC_MODEL")
    if not model:
        raise ValueError("ANTHROPIC_MODEL gerekli ancak tanımlanmamış. Claude kullanmayın — local Mistral kullanın.")
    
    message = client.messages.create(
        model=model,
        max_tokens=500,
        system=CYP_EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return _parse_json_safe(message.content[0].text)

def _call_local_extraction(prompt: str) -> dict:
    base_url = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")
    model_name = os.environ.get("LOCAL_MODEL_NAME", "local-model")
    client = openai.OpenAI(base_url=base_url, api_key="lm-studio")

    # LM Studio Mistral system role'ü desteklemiyor — system prompt'ı user message'e taşı
    combined_prompt = f"{CYP_EXTRACTION_SYSTEM_PROMPT}\n\n{prompt}"

    response = client.chat.completions.create(
        model=model_name,
        max_tokens=500,
        messages=[
            {"role": "user", "content": combined_prompt}
        ],
        temperature=0.0
    )

    return _parse_json_safe(response.choices[0].message.content or "{}")

def _parse_json_safe(text: str) -> dict:
    try:
        # JSON bloğunu ayıkla (LLM bazen ```json ... ``` içinde verebilir)
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            text = match.group(1)
        
        data = json.loads(text)
        # Şema doğrula
        return {
            "substrat":  [s.upper() for s in data.get("substrat", []) if isinstance(s, str)],
            "inhibitor": [i.upper() for i in data.get("inhibitor", []) if isinstance(i, str)],
            "induktor":  [i.upper() for i in data.get("induktor", []) if isinstance(i, str)],
        }
    except Exception as e:
        logger.warning(f"JSON parse hatası: {e} | Text: {text}")
        return {"substrat": [], "inhibitor": [], "induktor": []}
