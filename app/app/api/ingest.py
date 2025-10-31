
import os, uuid, tempfile, fitz, requests
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from app.services.extract_pdf import extract_pages, apply_boundaries, find_inline_latex
from app.services.chunker import split_semantic
from app.services.embeddings import embed_texts
from app.services.pine_text import upsert_text_vectors
from app.services.s3util import upload_image_bytes
from app.services.caption import caption_image_bytes

router = APIRouter(prefix="/ingest", tags=["ingestion:book-content"])

def _download_to_temp(url:str) -> str:
    r = requests.get(url, timeout=60); r.raise_for_status()
    fd, path = tempfile.mkstemp(suffix=".pdf"); os.close(fd)
    with open(path, "wb") as f: f.write(r.content)
    return path

@router.post("/unit")
async def ingest_unit_multipart(
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
    pdfFile: Optional[UploadFile] = File(None)
):
    if not pdfFile and not pdfUrl: raise HTTPException(400, "Provide either pdfFile or pdfUrl")
    tmp_path = None
    try:
        if pdfFile:
            fd, tmp_path = tempfile.mkstemp(suffix=".pdf"); os.close(fd)
            with open(tmp_path, "wb") as f: f.write(await pdfFile.read())
        else:
            tmp_path = _download_to_temp(pdfUrl)

        pages = extract_pages(tmp_path, pageStart, pageEnd)
        text, images = apply_boundaries(pages, startText, endText, startMatchIdx, endMatchIdx)
        latex = find_inline_latex(text)
        chunks = split_semantic(text)

        uploaded = []
        doc = fitz.open(tmp_path)
        for ref in images:
            try:
                d = doc.extract_image(ref["xref"])
                img_bytes = d["image"]
                ext = d.get("ext","png").lower()
                ctype = "image/png" if ext == "png" else "image/jpeg"
                s3_uri, image_id, key = upload_image_bytes(img_bytes, ctype, bookId, chapterId, unitId)
                cap = caption_image_bytes(img_bytes) or ""
                uploaded.append({"imageId": image_id, "pageNo": ref["page"], "s3Uri": s3_uri, "caption": cap})
            except Exception:
                continue
        doc.close()

        return {
            "job": {"bookId":bookId, "chapterId":chapterId, "unitId":unitId},
            "pageStart": pageStart, "pageEnd": pageEnd,
            "boundaries": {"startText": startText, "endText": endText, "startMatchIdx": startMatchIdx, "endMatchIdx": endMatchIdx},
            "previewChunks": chunks,
            "latex": latex,
            "images": uploaded
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except Exception: pass

class ApproveReq(BaseModel):
    bookId:int; chapterId:int; unitId:int
    subject:str; gradeLevel:str; languageCode:str="en"
    chunks: List[str]
    images: Optional[List[dict]] = None

@router.post("/approve")
async def approve(req:ApproveReq):
    vectors=[]
    for i, text in enumerate(req.chunks, start=1):
        from app.services.embeddings import embed_texts
        emb = embed_texts([text])[0]
        cid = str(uuid.uuid4())
        vectors.append({
            "id":f"chap:{req.chapterId}:unit:{req.unitId}:chunk:{cid}",
            "values":emb,
            "metadata":{
                "type": "book_content",
                "chapter_id":req.chapterId,"unit_id":req.unitId,
                "subject":req.subject,"grade":req.gradeLevel,"language":req.languageCode,
                "preview_text": text[:300]
            }
        })
    upsert_text_vectors(vectors, namespace=str(req.bookId))
    return {
        "unitId": req.unitId,
        "bookId": req.bookId,
        "chapterId": req.chapterId,
        "chunks": [
            {
                "chunkUid": v["id"].split(":")[-1].replace("chunk","").strip(":"),
                "ord": i+1,
                "text": req.chunks[i],
                "latex": None,
                "tokens": len(req.chunks[i].split()),
                "images": req.images or []
            } for i, v in enumerate(vectors)
        ],
        "images": req.images or []
    }
