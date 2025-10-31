
from fastapi import FastAPI
from app.api import ingest
app = FastAPI(title="EduRAG Final - FastAPI Only (No DB)")
app.include_router(ingest.router)
@app.get("/health")
def health(): return {"status":"ok"}
