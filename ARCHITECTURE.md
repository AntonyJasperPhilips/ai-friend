# System Architecture

## Overview

The AI Friend Textbook Q&A system enables schools to upload textbook PDFs and allows students to ask questions directly from the book content. The system uses vector search and LLM technology to provide accurate, grade-appropriate answers.

## Architecture Diagram

```
┌─────────────┐
│   Student   │
│  Mobile App │
└──────┬──────┘
       │
       │ HTTP/REST
       │
┌──────▼──────────────────────────────────────────────────┐
│                    FastAPI Server                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Upload     │  │     Q&A      │  │  Management  │ │
│  │   Endpoint   │  │   Endpoint   │  │   Endpoints  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
          │                  │                  │
    ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │    PDF    │     │    Q&A    │     │  Vector   │
    │ Processor │     │  Service  │     │    DB     │
    └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
          │                  │                  │
          │                  │                  │
    ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │ Tesseract │     │  OpenAI   │     │ Pinecone  │
    │    OCR    │     │   GPT-4   │     │  Vector   │
    └───────────┘     └───────────┘     │   Store   │
                                        └───────────┘
```

## Components

### 1. FastAPI Server (main.py)

**Responsibilities:**
- HTTP request handling
- Input validation
- Route management
- Response formatting

**Key Endpoints:**
- `POST /api/v1/textbooks/upload` - Upload textbooks
- `POST /api/v1/questions/ask` - Ask questions
- `GET /api/v1/textbooks` - List textbooks
- `GET /api/v1/textbooks/{id}` - Get textbook details
- `DELETE /api/v1/textbooks/{id}` - Delete textbook

### 2. PDF Processor (pdf_processor.py)

**Responsibilities:**
- PDF text extraction
- OCR for scanned books
- Text chunking
- Diagram caption detection

**Key Features:**
- Attempts direct text extraction first
- Falls back to OCR if needed
- Splits text into chunks with overlap
- Identifies diagram captions heuristically

**Technologies:**
- PyPDF2: Direct PDF text extraction
- pdf2image: Convert PDF to images
- Tesseract OCR: Text recognition from images
- LangChain TextSplitter: Intelligent text chunking

### 3. Vector Database (vector_db.py)

**Responsibilities:**
- Embedding generation
- Vector storage
- Semantic search
- Textbook data isolation

**Key Features:**
- Uses OpenAI embeddings (1536 dimensions)
- Stores chunks with rich metadata
- Filters by textbook_id for isolation
- Returns similarity scores

**Technology:**
- Pinecone: Vector database
- OpenAI Embeddings: Text to vector conversion
- LangChain: Integration layer

### 4. Q&A Service (qa_service.py)

**Responsibilities:**
- Context building from retrieved chunks
- Grade-appropriate prompt engineering
- Answer generation
- Confidence calculation

**Key Features:**
- Grade-specific system prompts
- Emphasizes textbook-only knowledge
- Incorporates teacher notes
- Confidence scoring based on similarity

**Technology:**
- OpenAI GPT-4: Language model
- Custom prompting strategy

### 5. Data Models (models.py)

**Key Models:**
- `TextbookMetadata`: Textbook information
- `QuestionRequest`: Student question input
- `AnswerResponse`: Generated answer output
- `GradeLevel`: Enum for grade levels
- `Subject`: Enum for subjects

## Data Flow

### Textbook Upload Flow

1. **Client uploads PDF** with metadata
2. **FastAPI validates** input and file type
3. **PDF Processor extracts text** using PyPDF2 or OCR
4. **Text is chunked** with metadata (page number, diagram flags)
5. **Chunks are embedded** using OpenAI embeddings
6. **Embeddings stored** in Pinecone with metadata
7. **Response returned** with textbook ID and status

### Question Answering Flow

1. **Client submits question** with textbook_id and grade level
2. **FastAPI validates** input
3. **Question is embedded** using OpenAI embeddings
4. **Vector DB searches** for similar chunks in the specific textbook
5. **Top 5 chunks retrieved** with similarity scores
6. **Context is built** from retrieved chunks
7. **Prompt is constructed** with:
   - System prompt (grade-specific)
   - Textbook content context
   - Teacher notes
   - Student question
8. **GPT-4 generates answer** based on context
9. **Confidence calculated** from similarity scores
10. **Response returned** with answer, sources, and confidence

## Key Design Decisions

### 1. Why Pinecone?

- **Managed service**: No infrastructure to maintain
- **Scalability**: Handles millions of vectors
- **Speed**: Sub-second search times
- **Filtering**: Supports metadata filtering for textbook isolation

### 2. Why GPT-4?

- **Context understanding**: Excellent at understanding complex questions
- **Grade-appropriate language**: Can adjust tone and complexity
- **Following instructions**: Reliably stays within textbook context
- **Quality**: High-quality, coherent answers

### 3. Why Chunking?

- **Context windows**: LLMs have token limits
- **Precision**: Smaller chunks improve retrieval accuracy
- **Overlap**: Prevents information loss at chunk boundaries

### 4. Diagram Caption Detection

- **Heuristic approach**: Detects common caption patterns
- **Metadata tagging**: Marks chunks as diagrams for context
- **Source attribution**: Shows students when answers reference diagrams

### 5. Grade-Level Prompting

- **Tailored responses**: Adjusts vocabulary and complexity
- **Educational value**: Enhances learning at appropriate level
- **Safety**: Ensures age-appropriate content

## Scalability Considerations

### Current Architecture

- **In-memory metadata storage**: Simple but not persistent
- **Synchronous processing**: Blocks during upload
- **Single instance**: No load balancing

### Production Recommendations

1. **Database**: Replace in-memory storage with PostgreSQL or MongoDB
2. **Async processing**: Use Celery for background PDF processing
3. **Caching**: Add Redis for frequently asked questions
4. **Load balancing**: Deploy multiple FastAPI instances behind nginx
5. **Monitoring**: Add logging, metrics, and alerting
6. **Rate limiting**: Prevent abuse
7. **Authentication**: Add user/school authentication
8. **File storage**: Use S3 for PDF files

## Security Considerations

### Current Implementation

- Basic input validation
- File size limits
- No authentication

### Production Recommendations

1. **Authentication**: Add JWT or OAuth2
2. **Authorization**: Role-based access control
3. **API keys**: Secure OpenAI and Pinecone credentials
4. **Input sanitization**: Prevent injection attacks
5. **HTTPS**: Encrypt data in transit
6. **Audit logging**: Track all operations
7. **Data privacy**: Comply with FERPA and student privacy laws

## Performance Characteristics

### Upload Time
- Small PDF (10 pages): ~10-20 seconds
- Medium PDF (100 pages): ~1-3 minutes
- Large PDF (500 pages): ~5-10 minutes

**Factors:**
- Text extraction vs OCR (OCR is much slower)
- Page count
- Network latency to Pinecone

### Query Time
- Typical query: ~2-5 seconds

**Breakdown:**
- Embedding: ~0.5 seconds
- Vector search: ~0.2 seconds
- LLM generation: ~1-4 seconds

## Future Enhancements

1. **Multi-modal**: Support images, diagrams directly
2. **Interactive**: Follow-up questions and clarifications
3. **Collaborative**: Student annotations and notes
4. **Analytics**: Track question patterns and learning gaps
5. **Offline**: Support offline mode for students
6. **Multi-language**: Support textbooks in different languages
7. **Accessibility**: Screen reader support, text-to-speech
