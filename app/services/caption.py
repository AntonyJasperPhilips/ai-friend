
import base64
from typing import Optional
from openai import OpenAI
from app.core.config import settings

def caption_image_bytes(image_bytes: bytes) -> Optional[str]:
    """Uses GPT-4o vision to caption an image. Returns a concise, caption-style sentence."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    messages = [
        {
            "role": "system",
            "content": "You are a scientific diagram captioner. In 1 sentence, describe the diagram for retrieval. Avoid opinions."
        },
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Caption this educational diagram succinctly."},
                {"type": "input_image", "image_data": b64}
            ]
        }
    ]
    resp = client.chat.completions.create(model="gpt-4o", messages=messages, temperature=0)
    return resp.choices[0].message.content.strip()
