# AI Friend – Educational RAG System

**Production-Ready** educational content management with AI-powered tutoring.

**Requires**: OpenAI, Pinecone, AWS S3 keys in `.env`.

## 🚀 Quick Start
1) Double-click `run_app.bat` (creates venv, installs dependencies).
2) Fill `.env` with API keys (see `.env.example`).
3) Run `run_app.bat` again.
4) Open http://localhost:8080/docs

## 📊 Architecture

```
Spring Boot (Gateway/Auth) → FastAPI (Processing) → Pinecone/S3/OpenAI
```

## 🔄 Flow

### Upload & Process
- `POST /ingest/unit` → Preview chunks/images/Latex (no storage)
- `POST /ingest/approve` → Store in Pinecone (async images)
- `PUT /ingest/unit/{id}` → Update unit
- `DELETE /ingest/unit/{id}` → Delete unit

### Query
- `POST /qa/query` → Get AI answer with context + images + formulas

### Teacher Notes
- `POST /ingest/teacher-notes/pdf` → Upload teacher notes
- `POST /ingest/teacher-notes/approve` → Store notes

## ⚙️ Configuration

### Required `.env` Variables
```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=bucket-class-friend-ai
```

### Optional Optimization
```env
# Cost controls
MAX_IMAGES_PER_UNIT=100
ENABLE_COST_TRACKING=true
OPENAI_API_BUDGET_DAILY=100.0

# Chunking (better retrieval)
CHUNK_SIZE=600
CHUNK_OVERLAP=50

# Embeddings (50% cost savings)
EMBED_MODEL=text-embedding-3-large  # or text-embedding-3-small

# Async processing (faster)
PROCESS_IMAGES_ASYNC=true
ENABLE_IMAGE_CAPTIONS=true

# Mathpix (optional)
USE_MATHPIX=false
MATHPIX_APP_ID=...
MATHPIX_APP_KEY=...
```

## ✨ Features

✅ **PDF Processing** - Text, images, formulas, OCR  
✅ **Dual Vector Storage** - Separate text & image indexes  
✅ **Smart Chunking** - 300-600 tokens with 50-token overlap  
✅ **Cost Controls** - Daily budgets, image limits  
✅ **Async Processing** - Fast responses, no timeouts  
✅ **RAG Answers** - Student-friendly AI tutoring  
✅ **Subject Context** - Grade-appropriate responses  
✅ **Unit Instructions** - Custom prompt guidance  
✅ **Multilingual** - All languages supported  
✅ **Update/Delete** - Full CRUD operations  
✅ **Mathpix** - Optional formula extraction  

## 📖 See Also

- `IMPLEMENTATION_COMPLETE.md` - Full feature list
- `IMPLEMENTATION_SUMMARY.md` - Latest updates & optimizations
- `Dockerfile` - Container deployment
