# Quick Fix Summary - Image Extraction Issues

## The Core Problem 🎯

Your image extraction is failing because of **invalid XREF values (0)** being passed to `doc.extract_image()`. The current code swallows errors silently, making debugging impossible.

## Root Cause

In `app/app/api/ingest.py` lines 50-62:

```python
for ref in images:  # ref["xref"] might be 0
    try:
        d = doc.extract_image(ref["xref"])  # ❌ Fails when xref=0
    except Exception:
        continue  # ❌ Silently swallows all errors
```

## The Fix

```python
# Lines 49-62 in app/app/api/ingest.py
uploaded = []
doc = fitz.open(tmp_path)

for ref in images:
    # CRITICAL FIX: Skip invalid xrefs
    xref = ref.get("xref", 0)
    if xref == 0:
        continue
        
    try:
        d = doc.extract_image(xref)
        if not d or not d.get("image"):
            continue
            
        img_bytes = d["image"]
        ext = d.get("ext", "png").lower()
        ctype = "image/png" if ext == "png" else "image/jpeg"
        
        s3_uri, image_id, key = upload_image_bytes(img_bytes, ctype, bookId, chapterId, unitId)
        cap = caption_image_bytes(img_bytes) or ""
        
        uploaded.append({
            "imageId": image_id, 
            "pageNo": ref["page"], 
            "s3Uri": s3_uri, 
            "caption": cap
        })
    except Exception as e:
        # Log the error for debugging
        import logging
        logging.error(f"Failed to extract image xref={xref}, page={ref.get('page')}: {e}")
        continue

doc.close()
```

## Missing Components

### 1. Image Embedding Service ❌

You have no way to create vectors from images. Add to `app/app/services/embeddings.py`:

```python
def embed_images(image_bytes_list: List[bytes]) -> List[List[float]]:
    """
    Creates embeddings for images.
    Options:
    1. Use OpenAI CLIP via API (need separate service)
    2. Use local CLIP model
    3. Use AWS Bedrock Titan Multimodal
    """
    # TODO: Implement based on your infrastructure
    return []
```

**Recommended:** Use CLIP (local or via OpenAI).

### 2. Image Storage in Pinecone ❌

Your `/approve` endpoint doesn't store image vectors. Add after line 100 in `app/app/api/ingest.py`:

```python
# Add image vectorization
if req.images and len(req.images) > 0:
    from app.services.embeddings import embed_images
    from app.services.pine_image import upsert_image_vectors
    
    image_vectors = []
    # TODO: Fetch image bytes from S3 or pass in approve request
    # image_bytes = fetch_from_s3(...)
    # embeddings = embed_images(image_bytes)
    
    # For each image:
    # img_vec = {
    #     "id": f"unit:{req.unitId}:img:{img_id}",
    #     "values": embedding,
    #     "metadata": {...}
    # }
    # image_vectors.append(img_vec)
    
    # upsert_image_vectors(image_vectors, namespace=str(req.bookId))
```

## Why Images Fail Now

1. ✅ **Extraction code runs** in `/ingest/unit`
2. ✅ **Upload to S3 succeeds** (if xref is valid)
3. ❌ **Embedding fails** (no service exists)
4. ❌ **Pinecone storage fails** (not implemented)
5. ❌ **Retrieval in QA fails** (no image vectors)

## Testing

Add logging to see what's happening:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In ingest_unit_multipart, add:
logging.info(f"Extracted {len(images)} image references")
for ref in images:
    logging.info(f"Image xref={ref.get('xref')}, page={ref.get('page')}")
```

Run your upload and check logs for XREF=0 issues.

## Next Steps

1. ✅ Apply the XREF=0 fix above
2. ✅ Add error logging
3. ⏳ Implement image embedding service
4. ⏳ Integrate image vectors into approve flow
5. ⏳ Test with your sample PDFs

See `PROJECT_REVIEW.md` for full details.


