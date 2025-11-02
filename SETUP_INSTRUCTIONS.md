# Setup Instructions

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This includes:
- boto3 (for S3)
- openai (for embeddings)
- pinecone-client (for vector DB)
- PyMuPDF (for PDF parsing)
- pytesseract (for OCR)
- And all other dependencies

### 2. Configure Environment

Create `.env` file in `app/app/` directory:

```env
# Required
OPENAI_API_KEY=sk-your_key_here
PINECONE_API_KEY=your_pinecone_key
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET=your_bucket_name

# Optional defaults
PINECONE_TEXT_INDEX=edu-text-chunks
PINECONE_IMAGE_INDEX=edu-image-chunks
OCR_ENABLED=true
ENABLE_IMAGE_CAPTIONS=true
```

### 3. Start Application

```bash
cd app
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Or use the batch file:
```bash
run_app.bat
```

### 4. Test

Open http://localhost:8080/docs

Upload a PDF and check logs!

---

## ✅ What's Implemented

- ✅ PDF image extraction
- ✅ Text chunking
- ✅ Image embedding
- ✅ Pinecone storage
- ✅ RAG retrieval
- ✅ Comprehensive logging

---

## 📝 Your Current Issue

**Error:** `Failed to upload image xref=248 to S3: Invalid endpoint`

**Cause:** AWS_REGION not configured

**Fix:** Add `AWS_REGION=us-east-1` to `.env`

---

## 🎉 Once Configured

Your students can:
- Ask questions
- Get answers
- See relevant images
- View formulas/diagrams

**Everything is ready!** Just add the AWS credentials.

