# API Usage Guide

This guide provides examples of how to use the AI Friend Textbook Q&A API.

## Prerequisites

Before using the API, make sure you have:
1. The API server running (see README.md for setup instructions)
2. Valid API keys configured in your `.env` file
3. A PDF textbook ready to upload

## API Endpoints

### 1. Health Check

Check if the API is running:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "message": "Service is operational"
}
```

### 2. Upload Textbook

Upload a PDF textbook with metadata:

```bash
curl -X POST "http://localhost:8000/api/v1/textbooks/upload" \
  -F "file=@./biology_textbook.pdf" \
  -F "title=Introduction to Biology" \
  -F "subject=biology" \
  -F "grade_level=high_school" \
  -F "author=Dr. Jane Smith" \
  -F "isbn=978-0-123456-78-9" \
  -F "teacher_notes=Focus on cellular biology for the midterm exam"
```

**Parameters:**
- `file` (required): PDF file of the textbook
- `title` (required): Title of the textbook
- `subject` (required): One of: `math`, `science`, `english`, `history`, `geography`, `physics`, `chemistry`, `biology`, `literature`, `other`
- `grade_level` (required): One of: `elementary`, `middle_school`, `high_school`, `college`
- `author` (optional): Author name
- `isbn` (optional): ISBN number
- `teacher_notes` (optional): Notes from the teacher about the textbook

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Introduction to Biology",
  "subject": "biology",
  "grade_level": "high_school",
  "author": "Dr. Jane Smith",
  "isbn": "978-0-123456-78-9",
  "teacher_notes": "Focus on cellular biology for the midterm exam",
  "upload_date": "2024-01-15T10:30:00Z",
  "page_count": 350,
  "processed": true
}
```

**Note:** Save the `id` from the response - you'll need it to ask questions about this textbook.

### 3. Ask a Question

Submit a question about an uploaded textbook:

```bash
curl -X POST "http://localhost:8000/api/v1/questions/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is photosynthesis and what are its main stages?",
    "textbook_id": "550e8400-e29b-41d4-a716-446655440000",
    "student_grade_level": "high_school",
    "additional_context": "I am preparing for the biology exam"
  }'
```

**Parameters:**
- `question` (required): The student's question
- `textbook_id` (required): ID of the textbook (from upload response)
- `student_grade_level` (required): Student's grade level
- `additional_context` (optional): Additional context from the student

Response:
```json
{
  "answer": "Photosynthesis is the process by which plants convert light energy into chemical energy...",
  "sources": [
    {
      "page_number": 45,
      "is_diagram_caption": false,
      "text_preview": "Photosynthesis occurs in the chloroplasts of plant cells..."
    },
    {
      "page_number": 46,
      "is_diagram_caption": true,
      "text_preview": "Figure 3.2: The Calvin cycle showing the light-independent reactions..."
    }
  ],
  "confidence": 0.92,
  "textbook_title": "Introduction to Biology"
}
```

### 4. List Textbooks

Get all uploaded textbooks:

```bash
curl http://localhost:8000/api/v1/textbooks
```

Response:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Introduction to Biology",
    "subject": "biology",
    "grade_level": "high_school",
    "author": "Dr. Jane Smith",
    "isbn": "978-0-123456-78-9",
    "teacher_notes": "Focus on cellular biology for the midterm exam",
    "upload_date": "2024-01-15T10:30:00Z",
    "page_count": 350,
    "processed": true
  }
]
```

### 5. Get Textbook Details

Get details about a specific textbook:

```bash
curl http://localhost:8000/api/v1/textbooks/550e8400-e29b-41d4-a716-446655440000
```

Response: Same as individual textbook in list response.

### 6. Delete Textbook

Delete a textbook and all its data:

```bash
curl -X DELETE http://localhost:8000/api/v1/textbooks/550e8400-e29b-41d4-a716-446655440000
```

Response:
```json
{
  "message": "Textbook deleted successfully"
}
```

## Using with Python

Here's a Python example using the `requests` library:

```python
import requests

BASE_URL = "http://localhost:8000"

# Upload textbook
def upload_textbook(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'title': 'Introduction to Biology',
            'subject': 'biology',
            'grade_level': 'high_school',
            'author': 'Dr. Jane Smith',
            'teacher_notes': 'Focus on cellular biology'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/textbooks/upload",
            files=files,
            data=data
        )
        
        return response.json()

# Ask question
def ask_question(textbook_id, question):
    data = {
        'question': question,
        'textbook_id': textbook_id,
        'student_grade_level': 'high_school'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/questions/ask",
        json=data
    )
    
    return response.json()

# Example usage
if __name__ == "__main__":
    # Upload
    result = upload_textbook('biology_textbook.pdf')
    textbook_id = result['id']
    print(f"Uploaded textbook with ID: {textbook_id}")
    
    # Ask question
    answer = ask_question(textbook_id, "What is photosynthesis?")
    print(f"Answer: {answer['answer']}")
    print(f"Confidence: {answer['confidence']}")
```

## Interactive API Documentation

Once the server is running, you can access interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

These interfaces allow you to test the API directly from your browser.

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: File too large
- `422 Unprocessable Entity`: Failed to process PDF
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Note: This implementation does not include rate limiting. In production, consider adding rate limiting to prevent abuse.

## Best Practices

1. **File Size**: Keep PDF files under 50MB for optimal performance
2. **Question Format**: Ask clear, specific questions for best results
3. **Grade Level**: Always specify the correct student grade level for age-appropriate answers
4. **Teacher Notes**: Include helpful teacher notes during upload to provide additional context
5. **Error Handling**: Always check response status codes and handle errors appropriately
