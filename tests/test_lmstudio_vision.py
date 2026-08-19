import base64
import requests
from pathlib import Path


IMAGE_PATH = Path("data/development/images/POT_001.jpeg")

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen/qwen3-vl-4b"


def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


image_base64 = image_to_base64(IMAGE_PATH)

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """
Analyze this civic issue image.

Identify the main civic issue visible in the image.

Choose exactly one:
- pothole
- damaged_road
- garbage_overflow
- illegal_dumping
- broken_streetlight
- water_leakage
- blocked_drain
- open_drain

Explain briefly why you selected the issue.
"""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ],
    "temperature": 0.1,
    "max_tokens": 300
}


response = requests.post(
    LM_STUDIO_URL,
    json=payload,
    timeout=120
)

response.raise_for_status()

data = response.json()

print("\n" + "=" * 60)
print("QWEN3-VL VISION TEST")
print("=" * 60)

print(data["choices"][0]["message"]["content"])