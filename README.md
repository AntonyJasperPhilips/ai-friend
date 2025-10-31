# AI Friend - Textbook Q&A System

A system that enables schools to upload textbooks (PDFs, including scanned books) and allows students to ask questions directly from book content using a mobile app. The system ensures answers are accurate, student-friendly, subject-aware, and based on the actual textbook content, not generic web knowledge.

## Features

- **PDF Upload & Processing**: Upload textbooks as PDFs, with automatic OCR for scanned books
- **Intelligent Text Extraction**: Extracts text and identifies diagram captions
- **Vector Search**: Uses Pinecone to retrieve relevant content chunks
- **Context-Aware Q&A**: Generates answers using LLM with:
  - Retrieved textbook content
  - Teacher notes
  - Student grade level
  - Subject-specific context
- **Student-Friendly Responses**: Tailored explanations appropriate for grade levels (Elementary, Middle School, High School, College)

## Architecture

The system consists of:

1. **PDF Processor**: Extracts text from PDFs using PyPDF2 and Tesseract OCR
2. **Text Chunking**: Splits text into manageable chunks with metadata
3. **Vector Database**: Stores embeddings in Pinecone for semantic search
4. **Q&A Service**: Uses OpenAI GPT-4 to generate contextual answers
5. **REST API**: FastAPI-based endpoints for uploading textbooks and asking questions

## Tech Stack

- **Backend**: FastAPI (Python)
- **PDF Processing**: PyPDF2, pdf2image, Tesseract OCR
- **Vector Database**: Pinecone
- **LLM**: OpenAI GPT-4
- **Embeddings**: OpenAI Embeddings (via LangChain)

## Setup

### Prerequisites

- Python 3.9+
- Tesseract OCR installed on your system
- OpenAI API key
- Pinecone API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/AntonyJasperPhilips/ai-friend.git
cd ai-friend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR:
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **macOS**: `brew install tesseract`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

4. Create a `.env` file from the example:
```bash
cp .env.example .env
```

5. Configure your `.env` file with your API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
```

### Running the Application

Start the API server:
```bash
python main.py
```

Or use uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Upload Textbook
```
POST /api/v1/textbooks/upload
```
Upload a PDF textbook with metadata (title, subject, grade level, teacher notes)

#### Ask Question
```
POST /api/v1/questions/ask
```
Submit a question about a textbook and receive an answer based on the content

#### List Textbooks
```
GET /api/v1/textbooks
```
Get all uploaded textbooks

#### Get Textbook Details
```
GET /api/v1/textbooks/{textbook_id}
```
Get details about a specific textbook

## Usage Example

### 1. Upload a Textbook

```bash
curl -X POST "http://localhost:8000/api/v1/textbooks/upload" \
  -F "file=@/path/to/textbook.pdf" \
  -F "title=Introduction to Biology" \
  -F "subject=biology" \
  -F "grade_level=high_school" \
  -F "author=John Smith" \
  -F "teacher_notes=Focus on chapters 3-5 for this semester"
```

### 2. Ask a Question

```bash
curl -X POST "http://localhost:8000/api/v1/questions/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is photosynthesis?",
    "textbook_id": "textbook-uuid-here",
    "student_grade_level": "high_school"
  }'
```

## How It Works

### Textbook Upload Flow

1. PDF is uploaded via the API
2. Text is extracted using PyPDF2; if insufficient text is found, OCR is applied
3. Text is split into chunks with metadata (page number, diagram detection)
4. Chunks are embedded using OpenAI embeddings
5. Embeddings are stored in Pinecone with metadata

### Question Answering Flow

1. Student submits a question via the API
2. Question is embedded and used to search Pinecone
3. Top 5 relevant chunks are retrieved (including diagram captions)
4. Context + teacher notes + grade level are passed to GPT-4
5. GPT-4 generates a grade-appropriate answer based solely on textbook content
6. Answer is returned with source references and confidence score

## Supported Grade Levels

- `elementary`: K-5 (Simple language, clear explanations)
- `middle_school`: 6-8 (Age-appropriate language)
- `high_school`: 9-12 (Academic language)
- `college`: College-level (Comprehensive, detailed explanations)

## Supported Subjects

- Math
- Science
- English
- History
- Geography
- Physics
- Chemistry
- Biology
- Literature
- Other

## Configuration

Key configuration options in `.env`:

- `MAX_UPLOAD_SIZE`: Maximum PDF file size (default: 50MB)
- `CHUNK_SIZE`: Text chunk size for processing (default: 1000 characters)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200 characters)
- `UPLOAD_DIR`: Directory for storing uploaded files (default: ./uploads)

## Development

### Project Structure

```
ai-friend/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── models.py            # Pydantic data models
├── pdf_processor.py     # PDF text extraction and chunking
├── vector_db.py         # Pinecone integration
├── qa_service.py        # Question answering with LLM
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables
└── README.md            # This file
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.