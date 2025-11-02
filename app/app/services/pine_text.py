
from pinecone import Pinecone
from app.core.config import settings

_pc = None
_index = None

def text_index():
    global _pc, _index
    if _index is None:
        _pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        _index = _pc.Index(settings.PINECONE_TEXT_INDEX)
    return _index

def upsert_text_vectors(vectors, namespace:str):
    if not vectors: return
    text_index().upsert(vectors=vectors, namespace=namespace)

def query_text(vector, top_k=5, metadata_filter=None, namespace:str="default"):
    return text_index().query(vector=vector, top_k=top_k, include_metadata=True, filter=metadata_filter or {}, namespace=namespace)

def delete_text_vectors(ids, namespace:str):
    """Delete vectors from text index by IDs."""
    if not ids: return
    text_index().delete(ids=ids, namespace=namespace)

def delete_text_by_filter(metadata_filter, namespace:str):
    """Delete vectors from text index by metadata filter."""
    text_index().delete(filter=metadata_filter, namespace=namespace)