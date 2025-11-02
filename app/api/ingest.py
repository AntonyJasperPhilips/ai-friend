
import os, uuid, tempfile, fitz, requests, time
import logging
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.services.extract_pdf import extract_pages, apply_boundaries, find_inline_latex, extract_image_data
from app.services.chunker import split_semantic
from app.services.embeddings import embed_texts, embed_images, embed_latex_formulas
from app.services.pine_text import upsert_text_vectors, delete_text_by_filter, query_text
from app.services.pine_image import upsert_image_vectors, delete_images_by_filter, query_images
from app.services.s3util import upload_image_bytes, fetch_image_from_s3, s3
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
    pdfFile: Optional[UploadFile] = File(None),
    languageCode: str = Form("en")
):
    if not pdfFile and not pdfUrl: raise HTTPException(400, "Provide either pdfFile or pdfUrl")
    
    # Validate page range
    if pageEnd < pageStart:
        raise HTTPException(400, "pageEnd must be >= pageStart")
    
    num_pages = pageEnd - pageStart + 1
    if num_pages > settings.MAX_PAGES_PER_REQUEST:
        raise HTTPException(
            400, 
            f"Too many pages: {num_pages}. Maximum allowed: {settings.MAX_PAGES_PER_REQUEST}. "
            f"Please split into smaller units."
        )
    
    tmp_path = None
    try:
        if pdfFile:
            fd, tmp_path = tempfile.mkstemp(suffix=".pdf"); os.close(fd)
            with open(tmp_path, "wb") as f: f.write(await pdfFile.read())
        else:
            tmp_path = _download_to_temp(pdfUrl)

        # Extract pages and text
        pages = extract_pages(tmp_path, pageStart, pageEnd, language_code=languageCode)
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
    
    if not images:
        logger.warning(f"No images provided for unit {unit_id}")
        return
    
    # Fetch images from S3
    image_bytes_list = []
    image_metadata_list = []
    
    for img_info in images:
        try:
            s3_uri = img_info.get("s3Uri")
            if not s3_uri:
                logger.warning(f"Image {img_info.get('imageId')} has no S3 URI, skipping")
                continue
            
            logger.debug(f"Fetching image {img_info.get('imageId')} from S3: {s3_uri}")
            img_bytes = fetch_image_from_s3(s3_uri)
            if not img_bytes or len(img_bytes) == 0:
                logger.warning(f"Image {img_info.get('imageId')} fetched but is empty")
                continue
                
            image_bytes_list.append(img_bytes)
            image_metadata_list.append(img_info)
            logger.debug(f"Successfully fetched image {img_info.get('imageId')}, size: {len(img_bytes)} bytes")
        except Exception as e:
            logger.error(f"Failed to fetch image {img_info.get('imageId')} from S3: {e}", exc_info=True)
            continue
    
    if not image_bytes_list:
        logger.error(f"No images successfully fetched from S3 for unit {unit_id}")
        return
    
    logger.info(f"Fetched {len(image_bytes_list)} images from S3, starting embedding process")
    
    # Embed all images
    try:
        embeddings = embed_images(image_bytes_list)
        logger.info(f"Generated {len(embeddings)} image embeddings")
        
        if len(embeddings) != len(image_metadata_list):
            logger.error(f"Mismatch: {len(embeddings)} embeddings but {len(image_metadata_list)} metadata items")
            return
        
        # Create image vectors for Pinecone
        image_vectors = []
        for i, (emb, img_info) in enumerate(zip(embeddings, image_metadata_list)):
            # Check if embedding is valid (not all zeros)
            if sum(emb) == 0.0:
                logger.warning(f"Image {img_info.get('imageId')} has zero embedding, might have failed")
            
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
            logger.debug(f"Created vector for image {img_info.get('imageId')}")
        
        # Upsert to Pinecone image index
        if image_vectors:
            try:
                upsert_image_vectors(image_vectors, namespace=str(book_id))
                logger.info(f"Successfully upserted {len(image_vectors)} image vectors to Pinecone namespace '{book_id}'")
            except Exception as e:
                logger.error(f"Failed to upsert image vectors to Pinecone: {e}", exc_info=True)
                raise
        else:
            logger.warning("No image vectors to upsert")
            
    except Exception as e:
        logger.error(f"Failed to embed and store images for unit {unit_id}: {e}", exc_info=True)
        raise

async def process_images_background(images: List[dict], book_id: str, chapter_id: str, unit_id: str, 
                                   subject: str, grade_level: str, language_code: str):
    """Process images asynchronously in background."""
    logger.info(f"Background processing {len(images)} images for unit {unit_id}")
    try:
        _process_images_sync(images, book_id, chapter_id, unit_id, subject, grade_level, language_code)
        logger.info(f"Successfully completed background image processing for unit {unit_id}")
    except Exception as e:
        logger.error(f"Background image processing failed for unit {unit_id}: {e}", exc_info=True)
        # Don't raise - background task should not fail the request

@router.post("/approve")
async def approve(req:ApproveReq, background_tasks: BackgroundTasks):
    """Approve unit and store in Pinecone. Optionally process images asynchronously."""
    global _openai_cost_tracker
    
    try:
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
        vectors = []
        try:
            for text in req.chunks:
                from app.services.embeddings import embed_texts
                emb = embed_texts([text])[0]
                cid = str(uuid.uuid4())
                vectors.append({
                    "id": f"chap:{req.chapterId}:unit:{req.unitId}:chunk:{cid}",
                    "values": emb,
                    "metadata": {
                        "type": "book_content",
                        "chapter_id": req.chapterId,
                        "unit_id": req.unitId,
                        "subject": req.subject,
                        "grade": req.gradeLevel,
                        "language": req.languageCode,
                        "preview_text": text[:300],
                        "unit_instructions": req.unitInstructions or ""
                    }
                })
            upsert_text_vectors(vectors, namespace=str(req.bookId))
            logger.info(f"Upserted {len(vectors)} text chunks to Pinecone")
        except Exception as e:
            logger.error(f"Failed to process text chunks: {e}", exc_info=True)
            raise HTTPException(500, f"Failed to process text chunks: {str(e)}")
        
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
                # Don't fail the whole request if LaTeX fails
        
        # Process images - either sync or async based on config
        if req.images and len(req.images) > 0:
            if settings.PROCESS_IMAGES_ASYNC:
                # Process images in background for faster response
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
                # Synchronous processing
                try:
                    _process_images_sync(req.images, req.bookId, req.chapterId, req.unitId, 
                                        req.subject, req.gradeLevel, req.languageCode)
                except Exception as e:
                    logger.error(f"Failed to process images synchronously: {e}", exc_info=True)
                    # Don't fail the whole request if image processing fails
        
        # Build response with safe chunk ID parsing
        chunk_responses = []
        for i, v in enumerate(vectors):
            try:
                chunk_id = v["id"].split(":")[-1].replace("chunk", "").strip(":")
                if not chunk_id:
                    chunk_id = v["id"]  # Fallback to full ID if parsing fails
            except Exception:
                chunk_id = v["id"]  # Fallback to full ID if parsing fails
            
            chunk_text = req.chunks[i] if i < len(req.chunks) else ""
            chunk_responses.append({
                "chunkUid": chunk_id,
                "ord": i + 1,
                "text": chunk_text,
                "latex": None,
                "tokens": len(chunk_text.split()) if chunk_text else 0,
                "images": req.images or []
            })
        
        return {
            "unitId": req.unitId,
            "bookId": req.bookId,
            "chapterId": req.chapterId,
            "chunks": chunk_responses,
            "images": req.images or []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in approve endpoint: {e}", exc_info=True)
        raise HTTPException(500, f"Internal server error: {str(e)}")

@router.delete("/unit/{unitId}")
async def delete_unit(unitId: str, bookId: str):
    """
    Delete all content for a unit (text chunks, formulas, images).
    Removes vectors from Pinecone AND deletes S3 files.
    """
    namespace = str(bookId)
    
    # First, get S3 URIs before deleting from Pinecone
    s3_keys_to_delete = []
    try:
        # Query images for this unit to get S3 URIs
        image_filter = {"unit_id": unitId}
        img_results = query_images([0.0] * 3072, top_k=1000, metadata_filter=image_filter, namespace=namespace)
        
        for match in getattr(img_results, "matches", []):
            md = match.metadata or {}
            s3_uri = md.get("s3_uri")
            if s3_uri and s3_uri.startswith("s3://"):
                # Extract bucket and key from s3:// URI
                parts = s3_uri.replace("s3://", "").split("/", 1)
                if len(parts) == 2:
                    bucket = parts[0]
                    key = parts[1]
                    s3_keys_to_delete.append(key)
        
        logger.info(f"Found {len(s3_keys_to_delete)} S3 images to delete for unit {unitId}")
    except Exception as e:
        logger.warning(f"Failed to query S3 URIs for unit {unitId}: {e}")
        s3_keys_to_delete = []
    
    # Delete text chunks, formulas, and teacher notes
    text_filter = {"unit_id": unitId}
    try:
        delete_text_by_filter(text_filter, namespace=namespace)
        logger.info(f"Deleted text/formula/note vectors for unit {unitId} in book {bookId}")
    except Exception as e:
        logger.error(f"Failed to delete text vectors for unit {unitId}: {e}")
        raise HTTPException(500, f"Failed to delete unit: {e}")
    
    # Delete image vectors from Pinecone
    image_filter = {"unit_id": unitId}
    try:
        delete_images_by_filter(image_filter, namespace=namespace)
        logger.info(f"Deleted image vectors for unit {unitId} in book {bookId}")
    except Exception as e:
        logger.error(f"Failed to delete image vectors for unit {unitId}: {e}")
        raise HTTPException(500, f"Failed to delete unit images: {e}")
    
    # Delete S3 files
    deleted_s3_count = 0
    if s3_keys_to_delete:
        try:
            s3_client = s3()
            for key in s3_keys_to_delete:
                try:
                    s3_client.delete_object(Bucket=settings.S3_BUCKET, Key=key)
                    deleted_s3_count += 1
                    logger.debug(f"Deleted S3 object: {key}")
                except Exception as e:
                    logger.warning(f"Failed to delete S3 object {key}: {e}")
            logger.info(f"Deleted {deleted_s3_count} S3 images for unit {unitId}")
        except Exception as e:
            logger.error(f"Failed to delete S3 files for unit {unitId}: {e}")
            # Don't fail the whole request if S3 delete fails
    
    return {
        "message": f"Unit {unitId} deleted successfully",
        "unitId": unitId,
        "bookId": bookId,
        "deletedS3Files": deleted_s3_count
    }

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
