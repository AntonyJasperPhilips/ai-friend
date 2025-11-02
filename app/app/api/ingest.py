
import os, uuid, tempfile, fitz, requests, time
import logging
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.services.extract_pdf import extract_pages, apply_boundaries, find_inline_latex, extract_image_data
from app.services.chunker import split_semantic
from app.services.embeddings import embed_texts, embed_images, embed_latex_formulas
from app.services.pine_text import upsert_text_vectors, delete_text_by_filter
from app.services.pine_image import upsert_image_vectors, delete_images_by_filter
from app.services.s3util import upload_image_bytes, fetch_image_from_s3
from app.services.caption import caption_image_bytes
from app.services.mathpix import extract_latex_from_image
from app.core.config import settings

logger = logging.getLogger(__name__)

# Cost tracking
_openai_cost_tracker = {
    "daily_spent": 0.0,
    "last_reset": time.time(),
    "total_images_today": 0,
    "total_chunks_today": 0
}

router = APIRouter(prefix="/ingest", tags=["ingestion:book-content"])

def _download_to_temp(url:str) -> str:
    r = requests.get(url, timeout=60); r.raise_for_status()
    fd, path = tempfile.mkstemp(suffix=".pdf"); os.close(fd)
    with open(path, "wb") as f: f.write(r.content)
    return path

@router.post("/unit")
async def ingest_unit_multipart(
    bookId: str = Form(...),
    chapterId: str = Form(...),
    unitId: str = Form(...),
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

        # Extract pages and text
        pages = extract_pages(tmp_path, pageStart, pageEnd)
        logger.info(f"Extracted {len(pages)} pages from PDF")
        text, images = apply_boundaries(pages, startText, endText, startMatchIdx, endMatchIdx)
        latex = find_inline_latex(text)
        chunks = split_semantic(text)
        
        logger.info(f"apply_boundaries returned {len(images)} image references")

        # Extract and upload images with improved error handling
        uploaded = []
        if images:
            logger.info(f"Processing {len(images)} image references for extraction")
            
            for ref in images:
                xref = ref.get("xref")
                page_no = ref.get("page")
                
                # Skip invalid xrefs (should already be filtered, but double-check)
                if not xref or xref <= 0:
                    logger.debug(f"Skipping invalid xref={xref} on page {page_no}")
                    continue
                
                try:
                    # Extract image data using the safe extraction function
                    img_dict = extract_image_data(tmp_path, xref)
                    
                    if not img_dict or not img_dict.get("image"):
                        logger.warning(f"No image data extracted for xref={xref}, page={page_no}")
                        continue
                    
                    img_bytes = img_dict["image"]
                    ext = img_dict.get("ext", "png").lower()
                    ctype = "image/png" if ext == "png" else "image/jpeg"
                    
                    # Upload to S3
                    try:
                        s3_uri, image_id, key = upload_image_bytes(img_bytes, ctype, bookId, chapterId, unitId)
                        logger.info(f"Uploaded image {image_id} to S3: {key}")
                    except Exception as e:
                        logger.error(f"Failed to upload image xref={xref} to S3: {e}")
                        continue
                    
                    # Generate caption (optional)
                    cap = ""
                    if settings.ENABLE_IMAGE_CAPTIONS:
                        try:
                            cap = caption_image_bytes(img_bytes) or ""
                            if cap:
                                logger.debug(f"Generated caption for image {image_id}: {cap[:50]}...")
                        except Exception as e:
                            logger.warning(f"Caption generation failed for image {image_id}: {e}")
                    
                    # Optional: Extract LaTeX from image using Mathpix
                    latex_from_image = ""
                    if settings.USE_MATHPIX:
                        try:
                            latex_from_image = extract_latex_from_image(img_bytes) or ""
                            if latex_from_image:
                                logger.debug(f"Extracted LaTeX from image {image_id} using Mathpix")
                        except Exception as e:
                            logger.warning(f"Mathpix LaTeX extraction failed for image {image_id}: {e}")
                    
                    uploaded.append({
                        "imageId": image_id,
                        "pageNo": page_no,
                        "s3Uri": s3_uri,
                        "caption": cap,
                        "latex": latex_from_image,
                        "width": img_dict.get("width"),
                        "height": img_dict.get("height"),
                        "bbox": ref.get("bbox")
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing image xref={xref}, page={page_no}: {e}", exc_info=True)
                    continue
        
        if uploaded:
            logger.info(f"Successfully processed {len(uploaded)} images")
        else:
            logger.warning("No images were successfully uploaded")

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
    bookId:str; chapterId:str; unitId:str
    subject:str; gradeLevel:str; languageCode:str="en"
    chunks: List[str]
    images: Optional[List[dict]] = None
    latex: Optional[List[str]] = None
    unitInstructions: Optional[str] = None

def _reset_cost_tracker_if_needed():
    """Reset daily cost tracker if 24 hours have passed."""
    daily_limit = 86400  # 24 hours in seconds
    if time.time() - _openai_cost_tracker["last_reset"] > daily_limit:
        _openai_cost_tracker["daily_spent"] = 0.0
        _openai_cost_tracker["last_reset"] = time.time()
        _openai_cost_tracker["total_images_today"] = 0
        _openai_cost_tracker["total_chunks_today"] = 0
        logger.info("Daily cost tracker reset")

def _process_images_sync(images: List[dict], book_id: str, chapter_id: str, unit_id: str, 
                        subject: str, grade_level: str, language_code: str):
    """Process images synchronously."""
    logger.info(f"Processing {len(images)} images synchronously for unit {unit_id}")
    
    try:
        # Fetch images from S3
        image_bytes_list = []
        image_metadata_list = []
        
        for img_info in images:
            try:
                s3_uri = img_info.get("s3Uri")
                if not s3_uri:
                    logger.warning(f"Image {img_info.get('imageId')} has no S3 URI, skipping")
                    continue
                
                img_bytes = fetch_image_from_s3(s3_uri)
                image_bytes_list.append(img_bytes)
                image_metadata_list.append(img_info)
            except Exception as e:
                logger.error(f"Failed to fetch image {img_info.get('imageId')} from S3: {e}")
                continue
        
        # Embed all images
        if image_bytes_list:
            try:
                embeddings = embed_images(image_bytes_list)
                logger.info(f"Generated {len(embeddings)} image embeddings")
                
                # Create image vectors for Pinecone
                image_vectors = []
                for i, (emb, img_info) in enumerate(zip(embeddings, image_metadata_list)):
                    img_vec = {
                        "id": f"chap:{chapter_id}:unit:{unit_id}:img:{img_info.get('imageId')}",
                        "values": emb,
                        "metadata": {
                            "type": "image",
                            "unit_id": unit_id,
                            "chapter_id": chapter_id,
                            "subject": subject,
                            "grade": grade_level,
                            "language": language_code,
                            "s3_uri": img_info.get("s3Uri"),
                            "caption": img_info.get("caption", ""),
                            "page": img_info.get("pageNo"),
                            "image_id": img_info.get("imageId")
                        }
                    }
                    image_vectors.append(img_vec)
                
                # Upsert to Pinecone image index
                upsert_image_vectors(image_vectors, namespace=str(book_id))
                logger.info(f"Upserted {len(image_vectors)} image vectors to Pinecone")
                
            except Exception as e:
                logger.error(f"Failed to embed images: {e}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Image processing failed for unit {unit_id}: {e}", exc_info=True)

async def process_images_background(images: List[dict], book_id: str, chapter_id: str, unit_id: str, 
                                   subject: str, grade_level: str, language_code: str):
    """Process images asynchronously in background."""
    logger.info(f"Background processing {len(images)} images for unit {unit_id}")
    _process_images_sync(images, book_id, chapter_id, unit_id, subject, grade_level, language_code)

@router.post("/approve")
async def approve(req:ApproveReq, background_tasks: BackgroundTasks = None):
    """Approve unit and store in Pinecone. Optionally process images asynchronously."""
    global _openai_cost_tracker
    
    # Reset cost tracker if needed
    _reset_cost_tracker_if_needed()
    
    # Validate image limit
    image_count = len(req.images) if req.images else 0
    if image_count > settings.MAX_IMAGES_PER_UNIT:
        raise HTTPException(
            400, 
            f"Too many images: {image_count}. Maximum allowed: {settings.MAX_IMAGES_PER_UNIT}"
        )
    
    # Estimate and check costs if tracking enabled
    if settings.ENABLE_COST_TRACKING:
        estimated_cost = (
            len(req.chunks) * 0.00013 +  # Text embeddings
            (len(req.latex) * 0.00013 if req.latex else 0) +  # LaTeX embeddings
            (image_count * 0.01 if settings.ENABLE_IMAGE_CAPTIONS else 0)  # Image captions (expensive)
        )
        
        if _openai_cost_tracker["daily_spent"] + estimated_cost > settings.OPENAI_API_BUDGET_DAILY:
            raise HTTPException(
                429, 
                f"Daily budget exceeded. Used: ${_openai_cost_tracker['daily_spent']:.2f}/{settings.OPENAI_API_BUDGET_DAILY}. "
                f"Required: ${estimated_cost:.2f}"
            )
        
        _openai_cost_tracker["daily_spent"] += estimated_cost
        _openai_cost_tracker["total_chunks_today"] += len(req.chunks)
    
    # Process text chunks
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
                "preview_text": text[:300],
                "unit_instructions": req.unitInstructions or ""
            }
        })
    upsert_text_vectors(vectors, namespace=str(req.bookId))
    logger.info(f"Upserted {len(vectors)} text chunks to Pinecone")
    
    if settings.ENABLE_COST_TRACKING:
        logger.warning(
            f"Cost tracking: ${_openai_cost_tracker['daily_spent']:.2f}/{settings.OPENAI_API_BUDGET_DAILY} spent, "
            f"{_openai_cost_tracker['total_chunks_today']} chunks today, {image_count} images queued"
        )
    
    # Process LaTeX formulas - embed and store in Pinecone text index
    latex_vectors = []
    if req.latex and len(req.latex) > 0:
        logger.info(f"Processing {len(req.latex)} LaTeX formulas for embedding")
        try:
            embeddings = embed_latex_formulas(req.latex)
            logger.info(f"Generated {len(embeddings)} LaTeX embeddings")
            
            # Create LaTeX vectors for Pinecone
            for i, (emb, latex_str) in enumerate(zip(embeddings, req.latex)):
                latex_vec = {
                    "id": f"chap:{req.chapterId}:unit:{req.unitId}:latex:{i+1}",
                    "values": emb,
                    "metadata": {
                        "type": "formula",
                        "unit_id": req.unitId,
                        "chapter_id": req.chapterId,
                        "subject": req.subject,
                        "grade": req.gradeLevel,
                        "language": req.languageCode,
                        "formula": latex_str,
                        "unit_instructions": req.unitInstructions or ""
                    }
                }
                latex_vectors.append(latex_vec)
            
            # Upsert to Pinecone text index
            upsert_text_vectors(latex_vectors, namespace=str(req.bookId))
            logger.info(f"Upserted {len(latex_vectors)} LaTeX vectors to Pinecone")
            
        except Exception as e:
            logger.error(f"Failed to embed LaTeX formulas: {e}", exc_info=True)
    
    # Process images - either sync or async based on config
    if req.images and len(req.images) > 0:
        if settings.PROCESS_IMAGES_ASYNC:
            # Process images in background for faster response
            if background_tasks:
                background_tasks.add_task(
                    process_images_background,
                    images=req.images,
                    book_id=req.bookId,
                    chapter_id=req.chapterId,
                    unit_id=req.unitId,
                    subject=req.subject,
                    grade_level=req.gradeLevel,
                    language_code=req.languageCode
                )
                logger.info(f"Queued {len(req.images)} images for background processing")
            else:
                logger.warning("BackgroundTasks not available, processing images synchronously")
                # Fallback to sync processing
                _process_images_sync(req.images, req.bookId, req.chapterId, req.unitId, 
                                    req.subject, req.gradeLevel, req.languageCode)
        else:
            # Synchronous processing
            _process_images_sync(req.images, req.bookId, req.chapterId, req.unitId, 
                                req.subject, req.gradeLevel, req.languageCode)
    
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

@router.delete("/unit/{unitId}")
async def delete_unit(unitId: str, bookId: str):
    """
    Delete all content for a unit (text chunks, formulas, images).
    This removes the unit's vectors from Pinecone but does NOT delete S3 files.
    """
    namespace = str(bookId)
    
    # Delete text chunks, formulas, and teacher notes
    text_filter = {"unit_id": unitId}
    try:
        delete_text_by_filter(text_filter, namespace=namespace)
        logger.info(f"Deleted text/formula/note vectors for unit {unitId} in book {bookId}")
    except Exception as e:
        logger.error(f"Failed to delete text vectors for unit {unitId}: {e}")
        raise HTTPException(500, f"Failed to delete unit: {e}")
    
    # Delete images
    image_filter = {"unit_id": unitId}
    try:
        delete_images_by_filter(image_filter, namespace=namespace)
        logger.info(f"Deleted image vectors for unit {unitId} in book {bookId}")
    except Exception as e:
        logger.error(f"Failed to delete image vectors for unit {unitId}: {e}")
        raise HTTPException(500, f"Failed to delete unit images: {e}")
    
    return {"message": f"Unit {unitId} deleted successfully", "unitId": unitId, "bookId": bookId}

@router.put("/unit/{unitId}")
async def update_unit(
    unitId: str,
    bookId: str = Form(...),
    chapterId: str = Form(...),
    subject: str = Form(...),
    gradeLevel: str = Form(...),
    languageCode: str = Form("en"),
    chunks: List[str] = Form(...),
    images: Optional[List[dict]] = Form(None),
    latex: Optional[List[str]] = Form(None),
    unitInstructions: Optional[str] = Form(None)
):
    """
    Update/replace all content for a unit.
    This deletes existing vectors and re-uploads with new content.
    """
    # First delete existing content
    try:
        await delete_unit(unitId=unitId, bookId=bookId)
    except Exception as e:
        logger.error(f"Failed to delete existing content for unit {unitId}: {e}")
        raise HTTPException(500, f"Failed to update unit: {e}")
    
    # Now re-approve with new content
    approve_req = ApproveReq(
        bookId=bookId,
        chapterId=chapterId,
        unitId=unitId,
        subject=subject,
        gradeLevel=gradeLevel,
        languageCode=languageCode,
        chunks=chunks,
        images=images,
        latex=latex,
        unitInstructions=unitInstructions
    )
    
    try:
        result = await approve(approve_req)
        logger.info(f"Successfully updated unit {unitId}")
        return result
    except Exception as e:
        logger.error(f"Failed to re-upload content for unit {unitId}: {e}")
        raise HTTPException(500, f"Failed to update unit: {e}")
