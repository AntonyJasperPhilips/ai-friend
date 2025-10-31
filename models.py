"""Data models for the AI Friend application."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GradeLevel(str, Enum):
    """Student grade levels."""
    ELEMENTARY = "elementary"  # K-5
    MIDDLE_SCHOOL = "middle_school"  # 6-8
    HIGH_SCHOOL = "high_school"  # 9-12
    COLLEGE = "college"


class Subject(str, Enum):
    """Subject areas for textbooks."""
    MATH = "math"
    SCIENCE = "science"
    ENGLISH = "english"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    LITERATURE = "literature"
    OTHER = "other"


class TextbookUploadRequest(BaseModel):
    """Request model for textbook upload metadata."""
    title: str = Field(..., description="Title of the textbook")
    subject: Subject = Field(..., description="Subject area of the textbook")
    grade_level: GradeLevel = Field(..., description="Target grade level")
    author: Optional[str] = Field(None, description="Author of the textbook")
    isbn: Optional[str] = Field(None, description="ISBN of the textbook")
    teacher_notes: Optional[str] = Field(None, description="Teacher notes about the textbook")


class TextbookMetadata(BaseModel):
    """Metadata for a textbook."""
    id: str = Field(..., description="Unique identifier for the textbook")
    title: str
    subject: Subject
    grade_level: GradeLevel
    author: Optional[str] = None
    isbn: Optional[str] = None
    teacher_notes: Optional[str] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    page_count: int
    processed: bool = False


class QuestionRequest(BaseModel):
    """Request model for student questions."""
    question: str = Field(..., description="The student's question")
    textbook_id: str = Field(..., description="ID of the textbook to query")
    student_grade_level: GradeLevel = Field(..., description="Grade level of the student")
    additional_context: Optional[str] = Field(None, description="Additional context from the student")


class AnswerResponse(BaseModel):
    """Response model for answers."""
    answer: str = Field(..., description="The generated answer")
    sources: List[dict] = Field(default_factory=list, description="Source chunks used to generate the answer")
    confidence: float = Field(..., description="Confidence score of the answer (0-1)")
    textbook_title: str = Field(..., description="Title of the textbook used")


class ChunkMetadata(BaseModel):
    """Metadata for a text chunk."""
    textbook_id: str
    page_number: int
    chunk_index: int
    is_diagram_caption: bool = False
    diagram_description: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str
