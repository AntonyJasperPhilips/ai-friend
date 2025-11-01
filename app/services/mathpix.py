
import base64, requests
from typing import Optional
from app.core.config import settings

MATHPIX_URL = "https://api.mathpix.com/v3/text"

def extract_latex_from_image(image_bytes:bytes) -> Optional[str]:
    if not settings.USE_MATHPIX:
        return None
    if not settings.MATHPIX_APP_ID or not settings.MATHPIX_APP_KEY:
        return None
    headers = {
        "app_id": settings.MATHPIX_APP_ID,
        "app_key": settings.MATHPIX_APP_KEY,
        "Content-type": "application/json"
    }
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    body = {
        "src": f"data:image/png;base64,{b64}",
        "formats": ["text", "data", "latex_simplified"],
        "data_options": {"include_asciimath": True}
    }
    r = requests.post(MATHPIX_URL, headers=headers, json=body, timeout=30)
    if r.status_code != 200:
        return None
    data = r.json()
    return data.get("latex_simplified") or data.get("text")
