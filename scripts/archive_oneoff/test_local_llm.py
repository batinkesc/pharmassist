import openai
from dotenv import load_dotenv
import os

load_dotenv()

def test_local():
    base_url = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")
    model_name = os.environ.get("LOCAL_MODEL_NAME", "local-model")
    client = openai.OpenAI(base_url=base_url, api_key="lm-studio")
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            max_tokens=20,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"LOCAL SUCCESS: {response.choices[0].message.content}")
    except Exception as e:
        print(f"LOCAL FAILURE: {e}")

if __name__ == "__main__":
    test_local()
