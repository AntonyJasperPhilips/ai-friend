
from typing import List
from openai import OpenAI
from app.core.config import settings
EMBED_MODEL = "text-embedding-3-large"
def embed_texts(texts:List[str]) -> List[List[float]]:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]
