
from pinecone import Pinecone
from app.core.config import settings

_pc = None
_index = None

def image_index():
    global _pc, _index
    if _index is None:
        _pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        _index = _pc.Index(settings.PINECONE_IMAGE_INDEX)
    return _index

def upsert_image_vectors(vectors, namespace:str):
    if not vectors: return
    image_index().upsert(vectors=vectors, namespace=namespace)

def query_images(vector, top_k=3, metadata_filter=None, namespace:str="default"):
    return image_index().query(vector=vector, top_k=top_k, include_metadata=True, filter=metadata_filter or {}, namespace=namespace)
