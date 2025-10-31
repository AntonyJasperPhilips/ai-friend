
from fastapi import FastAPI
from app.api import ingest
import uvicorn

app = FastAPI(title="EduRAG Final - FastAPI Only (No DB)")
app.include_router(ingest.router)

@app.get("/health")
def health(): 
    return {"status":"ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
