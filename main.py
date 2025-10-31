"""Main FastAPI application for the AI Friend textbook Q&A system."""
import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
import json
from datetime import datetime

from config import settings
from models import (
    TextbookUploadRequest,
    TextbookMetadata,
    QuestionRequest,
    AnswerResponse,
    HealthResponse,
    GradeLevel,
    Subject
)
from pdf_processor import PDFProcessor, save_uploaded_file
from vector_db import vector_db
from qa_service import qa_service

app = FastAPI(
    title="AI Friend - Textbook Q&A API",
    description="API for uploading textbooks and answering student questions",
    version="1.0.0"
)

# In-memory storage for textbook metadata (in production, use a database)
textbooks_db = {}

pdf_processor = PDFProcessor()


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint."""
    return HealthResponse(
        status="healthy",
        message="AI Friend Textbook Q&A API is running"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Service is operational"
    )


@app.post("/api/v1/textbooks/upload", response_model=TextbookMetadata)
async def upload_textbook(
    file: UploadFile = File(..., description="PDF file of the textbook"),
    title: str = Form(..., description="Title of the textbook"),
    subject: str = Form(..., description="Subject area"),
    grade_level: str = Form(..., description="Grade level"),
    author: Optional[str] = Form(None, description="Author name"),
    isbn: Optional[str] = Form(None, description="ISBN"),
    teacher_notes: Optional[str] = Form(None, description="Teacher notes")
):
    """
    Upload a textbook PDF and process it for Q&A.
    
    This endpoint:
    1. Accepts a PDF file (including scanned books)
    2. Extracts text using OCR if necessary
    3. Chunks the text and identifies diagram captions
    4. Stores embeddings in Pinecone for retrieval
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Check file size
    if len(file_content) > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_upload_size} bytes"
        )
    
    # Generate unique ID
    textbook_id = str(uuid.uuid4())
    
    try:
        # Validate enums
        try:
            subject_enum = Subject(subject.lower())
            grade_level_enum = GradeLevel(grade_level.lower())
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subject or grade_level. Error: {str(e)}"
            )
        
        # Save file
        file_path = save_uploaded_file(file_content, textbook_id, file.filename)
        
        # Extract text from PDF
        pages_text, page_count = pdf_processor.extract_text_from_pdf(file_content)
        
        if not pages_text or page_count == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to extract text from PDF"
            )
        
        # Create textbook metadata
        metadata = TextbookMetadata(
            id=textbook_id,
            title=title,
            subject=subject_enum,
            grade_level=grade_level_enum,
            author=author,
            isbn=isbn,
            teacher_notes=teacher_notes,
            page_count=page_count,
            processed=False
        )
        
        # Store metadata
        textbooks_db[textbook_id] = metadata.model_dump()
        
        # Chunk text
        chunks = pdf_processor.chunk_text(pages_text, textbook_id)
        
        # Store chunks in Pinecone
        vector_db.store_chunks(chunks, metadata.model_dump())
        
        # Update processed status
        metadata.processed = True
        textbooks_db[textbook_id]["processed"] = True
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing textbook: {str(e)}"
        )


@app.post("/api/v1/questions/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Answer a student's question based on textbook content.
    
    This endpoint:
    1. Retrieves relevant text chunks and diagram captions from Pinecone
    2. Passes context + teacher notes + student grade level to LLM
    3. Generates a student-friendly, subject-aware answer
    """
    # Validate textbook exists
    if request.textbook_id not in textbooks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Textbook not found"
        )
    
    textbook_metadata = textbooks_db[request.textbook_id]
    
    # Check if textbook is processed
    if not textbook_metadata.get("processed", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Textbook is still being processed"
        )
    
    try:
        # Search for relevant chunks
        context_chunks = vector_db.search_similar_chunks(
            query=request.question,
            textbook_id=request.textbook_id,
            top_k=5
        )
        
        if not context_chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant content found in the textbook for this question"
            )
        
        # Generate answer
        answer, confidence = qa_service.generate_answer(
            question=request.question,
            context_chunks=context_chunks,
            student_grade_level=request.student_grade_level,
            textbook_metadata=textbook_metadata
        )
        
        # Format sources
        sources = [
            {
                "page_number": chunk["metadata"].get("page_number"),
                "is_diagram_caption": chunk["metadata"].get("is_diagram_caption", False),
                "text_preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
            }
            for chunk in context_chunks
        ]
        
        return AnswerResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            textbook_title=textbook_metadata["title"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating answer: {str(e)}"
        )


@app.get("/api/v1/textbooks/{textbook_id}", response_model=TextbookMetadata)
async def get_textbook(textbook_id: str):
    """Get textbook metadata by ID."""
    if textbook_id not in textbooks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Textbook not found"
        )
    
    metadata_dict = textbooks_db[textbook_id]
    return TextbookMetadata(**metadata_dict)


@app.get("/api/v1/textbooks", response_model=list[TextbookMetadata])
async def list_textbooks():
    """List all textbooks."""
    return [TextbookMetadata(**metadata) for metadata in textbooks_db.values()]


@app.delete("/api/v1/textbooks/{textbook_id}")
async def delete_textbook(textbook_id: str):
    """Delete a textbook and its associated data."""
    if textbook_id not in textbooks_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Textbook not found"
        )
    
    try:
        # Delete from vector database
        vector_db.delete_textbook_chunks(textbook_id)
        
        # Delete from metadata storage
        del textbooks_db[textbook_id]
        
        return {"message": "Textbook deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting textbook: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port
    )
