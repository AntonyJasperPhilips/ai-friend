
from fastapi import APIRouter
from pydantic import BaseModel
from app.services import pine, pine_img, rag_prompt
from app.core.config import settings
from openai import OpenAI
from app.services.s3util import presign_get

router = APIRouter(prefix="/qa", tags=["qa"])

class QAReq(BaseModel):
    question:str; bookId:int; chapterId:int; unitId:int
    subject:str; gradeLevel:str; languageCode:str="en"
    allowSubjectFallback:bool=False; topK:int=5; imageTopK:int=3

@router.post("/query")
async def query(req:QAReq):
    filt = {
        "book_id": req.bookId,
        "chapter_id": req.chapterId,
        "unit_id": req.unitId,
        "subject": req.subject,
        "language": req.languageCode
    }
    text_matches = pine.query_text(req.question, top_k=req.topK, metadata_filter=filt)
    image_matches = pine_img.query_images(req.question, top_k=req.imageTopK, metadata_filter=filt)

    ctx_parts, citations = [], []
    for m in text_matches:
        md = m.get("metadata", {})
        preview = md.get("preview_text","")
        ctx_parts.append(preview)
        citations.append({"id": m.get("id"), "ord": md.get("ord")})

    system = rag_prompt.system_prompt(req.subject, req.gradeLevel, req.languageCode)
    user = rag_prompt.user_prompt(req.question, "\n\n".join(ctx_parts), teacher="", unit_instructions="")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
        temperature=0.2
    )
    answer = resp.choices[0].message.content

    # Build image payload with presigned URLs
    images = []
    for m in image_matches:
        md = m.get("metadata", {})
        s3_uri = md.get("s3_uri")
        url = None
        if s3_uri and s3_uri.startswith("s3://"):
            key = s3_uri.split("/", 3)[-1]
            key = key.split("/",1)[-1] if "/" in key else key
            try:
                url = presign_get(key)
            except Exception:
                url = None
        images.append({
            "id": m.get("id"),
            "score": m.get("score"),
            "caption": md.get("caption"),
            "page": md.get("page"),
            "url": url
        })

    return {"answer": answer, "citations": citations, "images": images}
