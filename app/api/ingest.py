
from fastapi import APIRouter
from pydantic import BaseModel
import uuid
from app.services.extract_pdf import extract_pages, apply_boundaries, find_inline_latex
from app.services.chunker import split_semantic
from app.services.embeddings import embed_texts
from app.services.pine import upsert_text_vectors

router = APIRouter(prefix="/ingest", tags=["ingestion"])

class UnitReq(BaseModel):
    bookId:int; chapterId:int; unitId:int
    pageStart:int; pageEnd:int
    pdfPath:str

@router.post("/unit")
def ingest(req:UnitReq):
    pages = extract_pages(req.pdfPath, req.pageStart, req.pageEnd)
    text, images = apply_boundaries(pages, None, None, None, None)
    latex = find_inline_latex(text)
    chunks = split_semantic(text)
    return {"previewChunks":chunks,"latex":latex,"images":images}

class ApproveReq(BaseModel):
    bookId:int; chapterId:int; unitId:int
    subject:str; gradeLevel:str
    chunks:list[str]

@router.post("/approve")
def approve(req:ApproveReq):
    vectors=[]
    for i,text in enumerate(req.chunks, start=1):
        emb = embed_texts([text])[0]
        cid = str(uuid.uuid4())
        vectors.append({
            "id":f"b:{req.bookId}:c:{req.chapterId}:u:{req.unitId}:ch:{cid}",
            "values":emb,
            "metadata":{
                "book_id":req.bookId,"chapter_id":req.chapterId,"unit_id":req.unitId,
                "ord":i,"subject":req.subject,"grade":req.gradeLevel
            }
        })
    upsert_text_vectors(vectors)
    return {"storedChunks":len(vectors),"unitId":req.unitId}
