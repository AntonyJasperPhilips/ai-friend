# Architecture: Current vs Recommended

## Current Architecture ⚠️

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  (app/app/main.py - runs on port 8080)                      │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐ ┌────────▼────────┐ ┌───────▼──────────┐
│  /ingest/unit  │ │  /ingest/approve │ │   /qa/query      │
│  (Upload)      │ │  (Store)         │ │   (Retrieve)     │
└───────┬────────┘ └────────┬─────────┘ └───────┬──────────┘
        │                   │                   │
        ├─ Extract PDF      ├─ Embed Text       ├─ Query Text
        ├─ Extract Images   ├─ Upsert Vectors   ├─ Query Images
        ├─ ❌ Upload to S3  ├─ ❌ No Image      ├─ ❌ No Images
        │   IMMEDIATELY     │   Processing      │   Returned
        └───────────────────┴───────────────────┴───────────────┘
        
┌─────────────────────────────────────────────────────────────┐
│  Problems:                                                  │
│  ❌ Images uploaded before preview                         │
│  ❌ No image embeddings created                            │
│  ❌ Images not stored in Pinecone                          │
│  ❌ Silent failures (XREF=0)                               │
│  ❌ No job tracking                                        │
└─────────────────────────────────────────────────────────────┘
```

## Recommended Architecture ✅

```
┌─────────────────────────────────────────────────────────────┐
│              FastAPI + Worker Architecture                  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐ ┌────────▼────────┐ ┌───────▼──────────┐
│  Upload API    │ │   Job Queue     │ │   QA API         │
│  (Synchronous) │ │   (Async)       │ │   (Real-time)    │
└───────┬────────┘ └────────┬─────────┘ └───────┬──────────┘
        │                   │                   │
        ├─ Extract only     ├─ Process chunks   ├─ Query Text
        ├─ Store in DB      ├─ Embed images     ├─ Query Images
        ├─ Return preview   ├─ Upload to S3     ├─ Return Context
        │   (no S3 yet)     ├─ Upsert vectors   └───────────────┘
        └─────────┬─────────┘   └────────┬───────────────┘
                  │                     │
        ┌─────────▼─────────┐ ┌────────▼────────┐
        │   PostgreSQL      │ │    Pinecone     │
        │   (Job Metadata)  │ │   (Vectors)     │
        │                   │ │                 │
        │ • UnitIngestJob   │ │ • Text Index    │
        │ • UnitChunk       │ │ • Image Index   │
        │ • ImageCatalog    │ │                 │
        │ • Audit Log       │ │                 │
        └─────────┬─────────┘ └────────┬────────┘
                  │                     │
        ┌─────────▼─────────────────────▼─────────┐
        │         AWS S3 (Image Storage)          │
        │  • Presigned URLs                        │
        │  • Lifecycle policies                    │
        └──────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Improvements:                                             │
│  ✅ Proper 2-phase: Preview → Approve                     │
│  ✅ Image embeddings created                               │
│  ✅ Async processing for large PDFs                        │
│  ✅ Job tracking & status                                  │
│  ✅ Error logging & monitoring                             │
│  ✅ Admin endpoints for management                         │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow: Current vs Recommended

### Current (Broken) Flow ❌

```
Admin Uploads PDF
      │
      ├─> Extract text ✅
      ├─> Extract images ✅
      ├─> Upload images to S3 ✅ (wrong timing)
      ├─> Generate captions ✅
      │
      ├─> Return preview
      │
      ├─> Admin approves
      │
      ├─> Embed text chunks ✅
      ├─> Store in Pinecone ✅
      │
      └─> ❌ Images NEVER stored in Pinecone
          ❌ No image vectors
          ❌ QA can't retrieve images
```

### Recommended Flow ✅

```
Admin Uploads PDF
      │
      ├─> Extract text ✅
      ├─> Extract images ✅
      ├─> Return preview ONLY
      │   (no S3 upload yet)
      │
      ├─> Store job in DB ✅
      │   Status: "previewed"
      │
      ├─> Admin reviews & approves
      │
      ├─> Update DB status: "processing"
      │
      ├─> Queue async job:
      │   ├─> Embed text chunks ✅
      │   ├─> Upload images to S3 ✅
      │   ├─> Generate captions ✅
      │   ├─> Embed images ✅
      │   ├─> Upsert text vectors ✅
      │   └─> Upsert image vectors ✅
      │
      ├─> Update DB status: "completed"
      │
      └─> Student Query
          ├─> Query text vectors ✅
          ├─> Query image vectors ✅
          └─> Return with images ✅
```

## Component Breakdown

### Phase 1: Upload & Preview ✅

**Endpoint:** `POST /ingest/unit`

**Responsibilities:**
- Parse PDF with PyMuPDF
- Extract text with OCR fallback
- Extract image references (no data yet)
- Apply text boundaries
- Chunk semantic text
- Return preview JSON

**Storage:**
- ❌ Nothing yet (memory only)

### Phase 2: Processing ✅

**Endpoint:** `POST /ingest/job/{jobId}/process`

**Trigger:** Admin approves preview

**Responsibilities:**
- Create text embeddings
- Upload images to S3
- Generate image captions
- Create image embeddings
- Upsert to Pinecone (text + image)
- Update database records

**Storage:**
- ✅ PostgreSQL: Job status, chunks, images
- ✅ Pinecone: Text & image vectors
- ✅ S3: Image files

### Phase 3: Query ✅

**Endpoint:** `POST /qa/query`

**Responsibilities:**
- Embed user question
- Query text vectors
- Query image vectors
- Filter by unit/chapter/subject
- Format response with LaTeX
- Return presigned image URLs

**Response:**
```json
{
  "answer": "The photosynthesis equation is...",
  "context": {
    "text_chunks": [...],
    "images": [
      {
        "url": "https://s3.../presigned",
        "caption": "Diagram showing..."
      }
    ]
  },
  "latex": [
    "6CO_2 + 6H_2O \\rightarrow C_6H_{12}O_6 + 6O_2"
  ]
}
```

## Database Schema

### UnitIngestJob (Tracking)

```sql
CREATE TABLE unit_ingest_jobs (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT NOT NULL,
    chapter_id BIGINT NOT NULL,
    unit_id BIGINT NOT NULL,
    page_start INT NOT NULL,
    page_end INT NOT NULL,
    status VARCHAR(16) DEFAULT 'queued',
    error TEXT,
    preview_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### UnitChunk (Metadata)

```sql
CREATE TABLE unit_chunks (
    id BIGSERIAL PRIMARY KEY,
    unit_id BIGINT NOT NULL,
    chunk_uid VARCHAR(64) NOT NULL,
    text TEXT,
    latex TEXT[],
    tokens INT,
    pinecone_id VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### ImageCatalog (Metadata)

```sql
CREATE TABLE images_catalog (
    id BIGSERIAL PRIMARY KEY,
    unit_id BIGINT NOT NULL,
    image_id VARCHAR(64) NOT NULL,
    s3_key VARCHAR(256) NOT NULL,
    caption TEXT,
    page_no INT,
    pinecone_id VARCHAR(128),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Technology Stack

### Current ✅ (Keep)
- FastAPI - API framework
- Pinecone - Vector DB
- AWS S3 - Object storage
- OpenAI - Embeddings & captions
- PyMuPDF - PDF parsing
- pytesseract - OCR

### Missing ❌ (Add)
- PostgreSQL - Metadata storage
- Redis - Job queue & caching
- Celery - Async workers
- SQLAlchemy - ORM
- Alembic - Migrations
- CLIP - Image embeddings

## Implementation Priority

### Week 1: Critical Fixes
1. ✅ Fix XREF=0 handling
2. ✅ Add error logging
3. ✅ Implement image embedding
4. ✅ Store images in Pinecone
5. ✅ Test end-to-end

### Week 2: Database
1. Set up PostgreSQL
2. Add SQLAlchemy models
3. Migrate with Alembic
4. Integrate job tracking
5. Admin endpoints

### Week 3: Production
1. Add Redis/Celery
2. Async job processing
3. Monitoring & logging
4. Error handling
5. Load testing

### Week 4: Polish
1. Admin UI (optional)
2. Documentation
3. Performance tuning
4. Security hardening
5. Deployment scripts

## Docker Compose Setup

```yaml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/edura enfo
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./app:/app
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: edura enf
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  celery:
    build: .
    command: celery -A app.workers worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/edura enf
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
```

This architecture scales and handles production workloads.


