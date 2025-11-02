
from openai import OpenAI
from app.core.config import settings
def embed_texts(texts):
    client=OpenAI(api_key=settings.OPENAI_API_KEY)
    r=client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in r.data]
