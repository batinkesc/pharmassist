"""Groq API baglanti testi — detayli hata."""
import sys, os, json, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv; load_dotenv()

url     = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1").rstrip("/") + "/chat/completions"
api_key = os.getenv("LM_STUDIO_API_KEY", "")
model   = os.getenv("LM_STUDIO_MODEL", "llama-3.3-70b-versatile")

print(f"URL   : {url}")
print(f"Model : {model}")
print(f"Key   : {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '(kisa)'}")
print()

payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": "Sadece JSON array dondur."},
        {"role": "user",   "content": "Aspirin-warfarin etkilesimini tek satirlik JSON olarak dondur."},
    ],
    "max_tokens": 200,
    "temperature": 0.05,
    "stream": False,
}

data = json.dumps(payload).encode("utf-8")
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
    "User-Agent": "python-httpx/0.27.0",
}
req = urllib.request.Request(url, data=data, headers=headers, method="POST")

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        print("BASARILI!")
        print(body["choices"][0]["message"]["content"][:400])
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"HTTP {e.code} hatasi:")
    print(body[:600])
except Exception as e:
    print(f"Beklenmedik hata: {type(e).__name__}: {e}")
