
from typing import Optional
from app.core.config import settings
from app.services.embeddings import embed_texts
from pinecone import Pinecone

pc = Pinecone(api_key=settings.PINECONE_API_KEY)
img_index = pc.Index(settings.PINECONE_IMAGE_INDEX)

def upsert_image_vectors(vectors):
    if not vectors: return
    img_index.upsert(vectors=vectors)

def query_images(query:str, top_k:int=3, metadata_filter:Optional[dict]=None):
    qvec = embed_texts([query])[0]
    res = img_index.query(vector=qvec, top_k=top_k, include_metadata=True, filter=metadata_filter or {})
    out = []
    for m in res.matches:
        out.append({"id": m.id, "score": m.score, "metadata": m.metadata})
    return out
