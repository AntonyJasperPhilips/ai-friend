
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db import models
from app.services.s3util import presign_get
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/unit/{unit_id}/images")
async def list_images(unit_id:int, db:Session=Depends(get_db)):
    rows = db.query(models.ImageCatalog).filter(models.ImageCatalog.unit_id==unit_id).all()
    out = []
    for r in rows:
        url = None
        if settings.S3_BUCKET and r.s3_uri and r.s3_uri.startswith("s3://"):
            key = r.s3_uri.split("/", 3)[-1]
            key = key.split("/",1)[-1] if "/" in key else key
            try:
                url = presign_get(key)
            except Exception:
                url = None
        out.append({
            "imageId": r.image_id, "page": r.page_no, "bbox": r.bbox,
            "s3Uri": r.s3_uri, "url": url, "caption": r.caption
        })
    return out
