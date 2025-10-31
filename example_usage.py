"""Example script demonstrating how to use the AI Friend API."""
import requests
import json
import os
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"


def check_health():
    """Check if the API is running."""
    print("Checking API health...")
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        print("✓ API is healthy")
        print(f"  Response: {response.json()}")
        return True
    else:
        print(f"✗ API health check failed: {response.status_code}")
        return False


def upload_textbook(pdf_path, title, subject, grade_level, author=None, teacher_notes=None):
    """
    Upload a textbook PDF.
    
    Args:
        pdf_path: Path to the PDF file
        title: Title of the textbook
        subject: Subject (e.g., 'biology', 'math')
        grade_level: Grade level (e.g., 'high_school')
        author: Optional author name
        teacher_notes: Optional teacher notes
        
    Returns:
        Textbook ID if successful, None otherwise
    """
    print(f"\nUploading textbook: {title}")
    
    if not os.path.exists(pdf_path):
        print(f"✗ File not found: {pdf_path}")
        return None
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
        data = {
            'title': title,
            'subject': subject,
            'grade_level': grade_level
        }
        
        if author:
            data['author'] = author
        if teacher_notes:
            data['teacher_notes'] = teacher_notes
        
        response = requests.post(
            f"{BASE_URL}/api/v1/textbooks/upload",
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Textbook uploaded successfully")
        print(f"  ID: {result['id']}")
        print(f"  Pages: {result['page_count']}")
        print(f"  Processed: {result['processed']}")
        return result['id']
    else:
        print(f"✗ Upload failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return None


def list_textbooks():
    """List all uploaded textbooks."""
    print("\nListing all textbooks...")
    
    response = requests.get(f"{BASE_URL}/api/v1/textbooks")
    
    if response.status_code == 200:
        textbooks = response.json()
        print(f"✓ Found {len(textbooks)} textbook(s)")
        
        for i, book in enumerate(textbooks, 1):
            print(f"\n  {i}. {book['title']}")
            print(f"     ID: {book['id']}")
            print(f"     Subject: {book['subject']}")
            print(f"     Grade Level: {book['grade_level']}")
            print(f"     Pages: {book['page_count']}")
            print(f"     Processed: {book['processed']}")
        
        return textbooks
    else:
        print(f"✗ Failed to list textbooks: {response.status_code}")
        return []


def ask_question(textbook_id, question, student_grade_level):
    """
    Ask a question about a textbook.
    
    Args:
        textbook_id: ID of the textbook
        question: The question to ask
        student_grade_level: Grade level of the student
        
    Returns:
        Answer response if successful, None otherwise
    """
    print(f"\nAsking question: {question}")
    
    data = {
        'question': question,
        'textbook_id': textbook_id,
        'student_grade_level': student_grade_level
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/questions/ask",
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Answer received")
        print(f"\n  Answer: {result['answer']}")
        print(f"\n  Confidence: {result['confidence']:.2f}")
        print(f"  Textbook: {result['textbook_title']}")
        print(f"\n  Sources:")
        for i, source in enumerate(result['sources'], 1):
            print(f"    {i}. Page {source['page_number']} (Diagram: {source['is_diagram_caption']})")
            print(f"       Preview: {source['text_preview'][:100]}...")
        
        return result
    else:
        print(f"✗ Question failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return None


def delete_textbook(textbook_id):
    """Delete a textbook."""
    print(f"\nDeleting textbook: {textbook_id}")
    
    response = requests.delete(f"{BASE_URL}/api/v1/textbooks/{textbook_id}")
    
    if response.status_code == 200:
        print(f"✓ Textbook deleted successfully")
        return True
    else:
        print(f"✗ Delete failed: {response.status_code}")
        return False


def main():
    """Main example workflow."""
    print("=" * 70)
    print("AI Friend - Textbook Q&A Example")
    print("=" * 70)
    
    # Check if API is running
    if not check_health():
        print("\n⚠ Please start the API server first:")
        print("  python main.py")
        return
    
    # List existing textbooks
    textbooks = list_textbooks()
    
    # Example: Upload a textbook (you need to provide a PDF file)
    print("\n" + "-" * 70)
    print("Example: Upload Textbook")
    print("-" * 70)
    print("\nTo upload a textbook, use:")
    print("  textbook_id = upload_textbook(")
    print("      pdf_path='path/to/your/textbook.pdf',")
    print("      title='Introduction to Biology',")
    print("      subject='biology',")
    print("      grade_level='high_school',")
    print("      author='Dr. Jane Smith',")
    print("      teacher_notes='Focus on cellular biology'")
    print("  )")
    
    # Example: Ask a question (if textbooks exist)
    if textbooks:
        print("\n" + "-" * 70)
        print("Example: Ask Question")
        print("-" * 70)
        
        textbook_id = textbooks[0]['id']
        print(f"\nUsing textbook: {textbooks[0]['title']}")
        
        # Ask a question
        ask_question(
            textbook_id=textbook_id,
            question="What are the main topics covered in the first chapter?",
            student_grade_level="high_school"
        )
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)
    print("\nFor more examples, see API_USAGE.md")


if __name__ == "__main__":
    main()
