
from fastapi import FastAPI
from app.api import ingest, teacher_notes, retrieve
app = FastAPI(
    title="AI Friend – Ingestion Engine (v2)",
    version="2.1.0",
    description="Namespaces by book, teacher notes (PDF/Text), S3 images+captions, dual-index retrieval"
)
app.include_router(ingest.router)
app.include_router(teacher_notes.router)
app.include_router(retrieve.router)
@app.get("/health")
def health(): return {"status":"ok"}
