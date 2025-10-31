
import os, uuid, tempfile, requests
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from app.services.extract_pdf import extract_pages, apply_boundaries, find_inline_latex
from app.services.chunker import split_semantic
from app.services.embeddings import embed_texts
from app.services.pine_text import upsert_text_vectors

router = APIRouter(prefix="/ingest/teacher-notes", tags=["ingestion:teacher-notes"])

def _download_to_temp(url:str) -> str:
    r = requests.get(url, timeout=60); r.raise_for_status()
    fd, path = tempfile.mkstemp(suffix=".pdf"); os.close(fd)
    with open(path, "wb") as f: f.write(r.content)
    return path

# PDF or URL variant (preview only)
@router.post("/pdf")
async def notes_pdf(
    bookId: int = Form(...),
    chapterId: int = Form(...),
    unitId: int = Form(...),
    pageStart: int = Form(...),
    pageEnd: int = Form(...),
    startText: Optional[str] = Form(None),
    endText: Optional[str] = Form(None),
    startMatchIdx: Optional[int] = Form(None),
    endMatchIdx: Optional[int] = Form(None),
    pdfUrl: Optional[str] = Form(None),
    pdfFile: Optional[UploadFile] = File(None),
    languageCode: str = Form("en")
):
    if not pdfFile and not pdfUrl: raise HTTPException(400, "Provide either pdfFile or pdfUrl")
    tmp_path=None
    try:
        if pdfFile:
            fd, tmp_path = tempfile.mkstemp(suffix=".pdf"); os.close(fd)
            with open(tmp_path, "wb") as f: f.write(await pdfFile.read())
        else:
            tmp_path = _download_to_temp(pdfUrl)
        pages = extract_pages(tmp_path, pageStart, pageEnd)
        text, _ = apply_boundaries(pages, startText, endText, startMatchIdx, endMatchIdx)
        latex = find_inline_latex(text)
        chunks = split_semantic(text)  # M-sized chunks
        return {
            "job": {"bookId":bookId,"chapterId":chapterId,"unitId":unitId},
            "languageCode": languageCode,
            "previewChunks": chunks,
            "latex": latex
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except Exception: pass

# Text variant (preview only)
class NotesTextReq(BaseModel):
    bookId:int; chapterId:int; unitId:int
    notesText:str; languageCode:str="en"

@router.post("/text")
async def notes_text(req: NotesTextReq):
    # split into M-sized chunks
    chunks = split_semantic(req.notesText)
    latex = []
    return {
        "job": {"bookId":req.bookId,"chapterId":req.chapterId,"unitId":req.unitId},
        "languageCode": req.languageCode,
        "previewChunks": chunks,
        "latex": latex
    }

# Approve (store as teacher_note vectors, namespaced by bookId)
class NotesApproveReq(BaseModel):
    bookId:int; chapterId:int; unitId:int
    subject:str; gradeLevel:str; languageCode:str="en"
    chunks: List[str]

@router.post("/approve")
async def notes_approve(req: NotesApproveReq):
    vectors=[]
    for i, text in enumerate(req.chunks, start=1):
        from app.services.embeddings import embed_texts
        emb = embed_texts([text])[0]
        cid = str(uuid.uuid4())
        vectors.append({
            "id":f"chap:{req.chapterId}:unit:{req.unitId}:tchunk:{cid}",
            "values":emb,
            "metadata":{
                "type": "teacher_note",
                "chapter_id":req.chapterId,"unit_id":req.unitId,
                "subject":req.subject,"grade":req.gradeLevel,"language":req.languageCode,
                "preview_text": text[:300]
            }
        })
    upsert_text_vectors(vectors, namespace=str(req.bookId))
    return {"storedChunks": len(vectors), "unitId": req.unitId}
