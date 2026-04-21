import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

def test_api():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"API SUCCESS: {message.content[0].text}")
    except Exception as e:
        print(f"API FAILURE: {e}")

if __name__ == "__main__":
    test_api()
