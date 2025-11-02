
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

def delete_image_vectors(ids, namespace:str):
    """Delete vectors from image index by IDs."""
    if not ids: return
    image_index().delete(ids=ids, namespace=namespace)

def delete_images_by_filter(metadata_filter, namespace:str):
    """Delete vectors from image index by metadata filter."""
    image_index().delete(filter=metadata_filter, namespace=namespace)