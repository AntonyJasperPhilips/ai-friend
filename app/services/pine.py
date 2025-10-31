
from pinecone import Pinecone
from app.core.config import settings
pc=Pinecone(api_key=settings.PINECONE_API_KEY)
index=pc.Index(settings.PINECONE_TEXT_INDEX)
def upsert_text_vectors(v): index.upsert(vectors=v)
