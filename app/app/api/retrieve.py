
from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
from app.services.embeddings import embed_texts
from app.services.pine_text import query_text
from app.services.pine_image import query_images
from app.services.s3util import presign_get
from app.services.rag_prompt import system_prompt, user_prompt
from app.core.config import settings

router = APIRouter(prefix="/qa", tags=["qa"])

class QAReq(BaseModel):
    question:str; bookId:str; chapterId:str; unitId:str
    subject:str; gradeLevel:str; languageCode:str="en"
    topK:int=5; imageTopK:int=3

@router.post("/query")
async def query(req:QAReq):
    qvec = embed_texts([req.question])[0]
    ns = str(req.bookId)
    base_filter = {"chapter_id": req.chapterId, "unit_id": req.unitId, "subject": req.subject, "language": req.languageCode}

    # book content
    f_book = dict(base_filter); f_book["type"] = "book_content"
    book_res = query_text(qvec, top_k=req.topK, metadata_filter=f_book, namespace=ns)

    # teacher notes
    f_notes = dict(base_filter); f_notes["type"] = "teacher_note"
    note_res = query_text(qvec, top_k=min(3, req.topK), metadata_filter=f_notes, namespace=ns)

    # images
    img_res = query_images(qvec, top_k=req.imageTopK, metadata_filter={"subject": req.subject, "language": req.languageCode, "unit_id": req.unitId}, namespace=ns)

    # build payload
    book_ctx = [m.metadata.get("preview_text","") for m in getattr(book_res, "matches", [])]
    note_ctx = [m.metadata.get("preview_text","") for m in getattr(note_res, "matches", [])]

    images = []
    for m in getattr(img_res, "matches", []):
        md = m.metadata or {}
        s3_uri = md.get("s3_uri")
        url = None
        if s3_uri and s3_uri.startswith("s3://"):
            key = s3_uri.split("/",3)[-1]
            key = key.split("/",1)[-1] if "/" in key else key
            try: url = presign_get(key)
            except Exception: url = None
        images.append({"id": m.id, "score": m.score, "caption": md.get("caption"), "page": md.get("page"), "url": url})

    # Generate AI answer using RAG
    system_msg = system_prompt(req.subject, req.gradeLevel, req.languageCode)
    context_str = "\n\n".join(book_ctx + note_ctx) if book_ctx or note_ctx else "No relevant material found."
    user_msg = user_prompt(req.question, context_str, teacher="", unit_instructions="")
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        temperature=0.2
    )
    answer = resp.choices[0].message.content

    return {
        "answer": answer,
        "bookContext": book_ctx[:req.topK],
        "teacherNotesContext": note_ctx[:min(3, req.topK)],
        "images": images
    }
