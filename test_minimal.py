"""Minimal test that doesn't require external dependencies."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_models():
    """Test that models work correctly."""
    print("Testing models...")
    
    try:
        from models import (
            GradeLevel, Subject, QuestionRequest, 
            TextbookUploadRequest, AnswerResponse
        )
        
        # Test enums
        assert GradeLevel.HIGH_SCHOOL.value == "high_school"
        assert Subject.MATH.value == "math"
        print("✓ Enums work correctly")
        
        # Test QuestionRequest
        question = QuestionRequest(
            question="What is photosynthesis?",
            textbook_id="test-id",
            student_grade_level=GradeLevel.HIGH_SCHOOL
        )
        assert question.question == "What is photosynthesis?"
        print("✓ QuestionRequest model works correctly")
        
        # Test AnswerResponse
        answer = AnswerResponse(
            answer="Test answer",
            sources=[],
            confidence=0.9,
            textbook_title="Test Book"
        )
        assert answer.confidence == 0.9
        print("✓ AnswerResponse model works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Model tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi_app():
    """Test FastAPI app structure."""
    print("\nTesting FastAPI app structure...")
    
    try:
        # Just check if the file has correct structure
        with open('main.py', 'r') as f:
            content = f.read()
            
        # Check for key components
        assert 'from fastapi import FastAPI' in content
        assert 'app = FastAPI' in content
        assert '/api/v1/textbooks/upload' in content
        assert '/api/v1/questions/ask' in content
        print("✓ FastAPI app has correct structure")
        
        return True
        
    except Exception as e:
        print(f"✗ FastAPI app tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Running Minimal Structure Tests")
    print("=" * 60)
    
    all_passed = True
    
    if not test_models():
        all_passed = False
    
    if not test_fastapi_app():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
