# 📚 AI Friend API Endpoints

Complete list of all endpoints in your application.

**Base URL**: `http://localhost:8080` (or your deployed URL)  
**API Docs**: `http://localhost:8080/docs` (Swagger UI)

---

## 🏥 Health Check

### `GET /health`
**Purpose**: Check if API is running

**Response**:
```json
{
  "status": "ok"
}
```

---

## 📖 Book Content Ingestion

### `POST /ingest/unit`
**Purpose**: Upload and preview a unit (extract text, images, LaTeX)

**Method**: Multipart form data

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bookId` | string | ✅ | Book identifier |
| `chapterId` | string | ✅ | Chapter identifier |
| `unitId` | string | ✅ | Unit identifier |
| `pageStart` | integer | ✅ | Starting page number |
| `pageEnd` | integer | ✅ | Ending page number |
| `startText` | string | ⭕ | Text boundary start |
| `endText` | string | ⭕ | Text boundary end |
| `startMatchIdx` | integer | ⭕ | Start text match index |
| `endMatchIdx` | integer | ⭕ | End text match index |
| `pdfFile` | file | ⭕ | PDF file upload |
| `pdfUrl` | string | ⭕ | PDF URL |
| `languageCode` | string | ⭕ | Language for OCR (default: "en") |

**Response**:
```json
{
  "job": {
    "bookId": "123",
    "chapterId": "456",
    "unitId": "789"
  },
  "pageStart": 1,
  "pageEnd": 10,
  "boundaries": {...},
  "previewChunks": ["chunk1", "chunk2"],
  "latex": ["$E=mc^2$"],
  "images": [
    {
      "imageId": "uuid",
      "pageNo": 3,
      "s3Uri": "s3://bucket/...",
      "caption": "...",
      "width": 800,
      "height": 600
    }
  ]
}
```

---

### `POST /ingest/approve`
**Purpose**: Store approved unit in Pinecone

**Method**: JSON

**Request Body**:
```json
{
  "bookId": "123",
  "chapterId": "456",
  "unitId": "789",
  "subject": "Mathematics",
  "gradeLevel": "10",
  "languageCode": "en",
  "chunks": ["chunk1", "chunk2"],
  "images": [...],  // Optional
  "latex": ["$E=mc^2$"],  // Optional
  "unitInstructions": "Explain concepts simply"  // Optional
}
```

**Response**:
```json
{
  "unitId": "789",
  "bookId": "123",
  "chapterId": "456",
  "chunks": [...],
  "images": [...]
}
```

---

### `PUT /ingest/unit/{unitId}`
**Purpose**: Update/replace entire unit

**Method**: Multipart form data

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bookId` | string | ✅ | Book identifier |
| `chapterId` | string | ✅ | Chapter identifier |
| `subject` | string | ✅ | Subject name |
| `gradeLevel` | string | ✅ | Grade level |
| `languageCode` | string | ⭕ | Language (default: "en") |
| `chunks` | array | ✅ | Text chunks |
| `images` | array | ⭕ | Image list |
| `latex` | array | ⭕ | LaTeX formulas |
| `unitInstructions` | string | ⭕ | Custom instructions |

**Response**: Same as `/ingest/approve`

---

### `DELETE /ingest/unit/{unitId}`
**Purpose**: Delete entire unit (Pinecone + S3)

**Method**: DELETE

**Query Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bookId` | string | ✅ | Book identifier |

**Response**:
```json
{
  "message": "Unit 789 deleted successfully",
  "unitId": "789",
  "bookId": "123",
  "deletedS3Files": 5
}
```

---

## 👨‍🏫 Teacher Notes Ingestion

### `POST /ingest/teacher-notes/pdf`
**Purpose**: Upload teacher notes from PDF

**Method**: Multipart form data

**Parameters**: Same as `/ingest/unit` + `languageCode`

**Response**:
```json
{
  "job": {...},
  "languageCode": "en",
  "previewChunks": [...],
  "latex": [...]
}
```

---

### `POST /ingest/teacher-notes/text`
**Purpose**: Upload teacher notes as text

**Method**: JSON

**Request Body**:
```json
{
  "bookId": "123",
  "chapterId": "456",
  "unitId": "789",
  "notesText": "Teacher notes here...",
  "languageCode": "en"
}
```

**Response**: Same as PDF variant

---

### `POST /ingest/teacher-notes/approve`
**Purpose**: Store teacher notes in Pinecone

**Method**: JSON

**Request Body**:
```json
{
  "bookId": "123",
  "chapterId": "456",
  "unitId": "789",
  "subject": "Mathematics",
  "gradeLevel": "10",
  "languageCode": "en",
  "chunks": ["note1", "note2"]
}
```

**Response**:
```json
{
  "storedChunks": 5,
  "unitId": "789"
}
```

---

## 🤖 AI Query & Retrieval

### `POST /qa/query`
**Purpose**: Ask questions and get AI answers

**Method**: JSON

**Request Body**:
```json
{
  "question": "What is photosynthesis?",
  "bookId": "123",
  "chapterId": "456",
  "unitId": "789",
  "subject": "Biology",
  "gradeLevel": "10",
  "languageCode": "en",
  "topK": 5,                    // Optional, default: 5
  "imageTopK": 3,               // Optional, default: 3
  "allowSubjectFallback": false // Optional, default: false
}
```

**Response**:
```json
{
  "answer": "Photosynthesis is the process...",
  "sources": {
    "bookChunks": [...],
    "teacherNotes": [...],
    "formulas": ["$...$"],
    "images": [
      {
        "imageId": "uuid",
        "s3Url": "https://...",
        "caption": "...",
        "confidence": 0.92
      }
    ]
  },
  "unitInstructions": "..."
}
```

---

## 📊 Endpoint Summary

| Method | Path | Purpose | Tags |
|--------|------|---------|------|
| `GET` | `/health` | Health check | - |
| `POST` | `/ingest/unit` | Upload unit (preview) | `ingestion:book-content` |
| `POST` | `/ingest/approve` | Store unit | `ingestion:book-content` |
| `PUT` | `/ingest/unit/{unitId}` | Update unit | `ingestion:book-content` |
| `DELETE` | `/ingest/unit/{unitId}` | Delete unit | `ingestion:book-content` |
| `POST` | `/ingest/teacher-notes/pdf` | Upload notes PDF | `ingestion:teacher-notes` |
| `POST` | `/ingest/teacher-notes/text` | Upload notes text | `ingestion:teacher-notes` |
| `POST` | `/ingest/teacher-notes/approve` | Store notes | `ingestion:teacher-notes` |
| `POST` | `/qa/query` | Query AI | `qa` |

**Total Endpoints**: 9

---

## 🔐 Security Notes

- ⚠️ No authentication built into FastAPI
- 🔒 Protected by Spring Boot gateway in production
- 🌐 Should run behind private network
- 📝 Uses namespaces (bookId) for data isolation

---

## 🧪 Testing

### Quick Test with cURL

```bash
# Health check
curl http://localhost:8080/health

# Query
curl -X POST http://localhost:8080/qa/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is mitosis?",
    "bookId": "123",
    "chapterId": "456",
    "unitId": "789",
    "subject": "Biology",
    "gradeLevel": "10",
    "languageCode": "en"
  }'
```

### Using Swagger UI

Visit `http://localhost:8080/docs` for interactive API testing.

---

## 📝 Additional Features

### Built-in Limits
- ✅ Max 500 pages per upload
- ✅ Max 100 images per unit
- ✅ Cost tracking & budgets
- ✅ Async image processing

### Multilingual Support
- ✅ 20+ languages for OCR
- ✅ Multilingual responses

### Smart Retrieval
- ✅ Chunk overlap (50 tokens)
- ✅ Subject validation
- ✅ Formula extraction
- ✅ Image embeddings

---

**Last Updated**: Session 2 - All features complete ✅

