"""Question answering service using LLM with context from textbook."""
from typing import List, Dict
from openai import OpenAI
from config import settings
from models import GradeLevel


class QAService:
    """Question answering service with context-aware prompting."""
    
    def __init__(self):
        """Initialize the QA service."""
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def generate_answer(
        self,
        question: str,
        context_chunks: List[Dict],
        student_grade_level: GradeLevel,
        textbook_metadata: Dict
    ) -> tuple[str, float]:
        """
        Generate an answer using LLM with context.
        
        Args:
            question: The student's question
            context_chunks: Retrieved context chunks from Pinecone
            student_grade_level: Grade level of the student
            textbook_metadata: Metadata about the textbook
            
        Returns:
            Tuple of (answer, confidence_score)
        """
        # Build context from retrieved chunks
        context = self._build_context(context_chunks)
        
        # Get teacher notes if available
        teacher_notes = textbook_metadata.get("teacher_notes", "")
        
        # Build the prompt
        prompt = self._build_prompt(
            question=question,
            context=context,
            student_grade_level=student_grade_level,
            subject=textbook_metadata.get("subject", ""),
            teacher_notes=teacher_notes
        )
        
        # Generate answer using OpenAI
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(student_grade_level)
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            # Calculate confidence based on context relevance
            confidence = self._calculate_confidence(context_chunks)
            
            return answer, confidence
            
        except Exception as e:
            print(f"Error generating answer: {str(e)}")
            return "I apologize, but I encountered an error generating an answer. Please try again.", 0.0
    
    def _build_context(self, context_chunks: List[Dict]) -> str:
        """
        Build context string from retrieved chunks.
        
        Args:
            context_chunks: List of context chunks with metadata
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(context_chunks):
            metadata = chunk.get("metadata", {})
            page_num = metadata.get("page_number", "unknown")
            text = chunk.get("text", "")
            is_diagram = metadata.get("is_diagram_caption", False)
            
            label = "Diagram/Figure Caption" if is_diagram else "Text"
            context_parts.append(f"[{label} from Page {page_num}]\n{text}")
        
        return "\n\n".join(context_parts)
    
    def _get_system_prompt(self, grade_level: GradeLevel) -> str:
        """
        Get the system prompt based on grade level.
        
        Args:
            grade_level: Student's grade level
            
        Returns:
            System prompt
        """
        grade_descriptions = {
            GradeLevel.ELEMENTARY: "elementary school students (grades K-5). Use simple language, avoid jargon, and explain concepts clearly with examples.",
            GradeLevel.MIDDLE_SCHOOL: "middle school students (grades 6-8). Use age-appropriate language and provide clear explanations with relevant examples.",
            GradeLevel.HIGH_SCHOOL: "high school students (grades 9-12). Use appropriate academic language and provide thorough explanations.",
            GradeLevel.COLLEGE: "college-level students. Use academic language and provide comprehensive, detailed explanations."
        }
        
        description = grade_descriptions.get(
            grade_level,
            "students. Use clear and appropriate language."
        )
        
        return f"""You are a helpful and knowledgeable tutor assistant for {description}

Your role is to:
1. Answer questions based ONLY on the provided textbook content
2. Make answers accurate, clear, and appropriate for the student's grade level
3. Be subject-aware and use proper terminology from the textbook
4. If the context doesn't contain enough information to answer the question, clearly state that
5. Never make up information or use general web knowledge - stick to the textbook
6. Consider any teacher notes provided to enhance your explanation
7. When referencing diagrams or figures, acknowledge them in your answer

Remember: Your primary goal is to help students learn from their actual textbook content."""
    
    def _build_prompt(
        self,
        question: str,
        context: str,
        student_grade_level: GradeLevel,
        subject: str,
        teacher_notes: str
    ) -> str:
        """
        Build the user prompt.
        
        Args:
            question: Student's question
            context: Retrieved context
            student_grade_level: Student's grade level
            subject: Subject area
            teacher_notes: Teacher's notes
            
        Returns:
            Formatted prompt
        """
        prompt_parts = [
            f"Subject: {subject}",
            f"Student Grade Level: {student_grade_level.value}",
        ]
        
        if teacher_notes:
            prompt_parts.append(f"\nTeacher Notes:\n{teacher_notes}")
        
        prompt_parts.extend([
            f"\nTextbook Content:\n{context}",
            f"\nStudent Question: {question}",
            "\nProvide a clear, accurate answer based on the textbook content above."
        ])
        
        return "\n".join(prompt_parts)
    
    def _calculate_confidence(self, context_chunks: List[Dict]) -> float:
        """
        Calculate confidence score based on context relevance.
        
        Args:
            context_chunks: Retrieved context chunks
            
        Returns:
            Confidence score between 0 and 1
        """
        if not context_chunks:
            return 0.0
        
        # Use similarity scores to calculate confidence
        scores = [chunk.get("similarity_score", 0.0) for chunk in context_chunks]
        
        if not scores:
            return 0.5
        
        # Average of top scores with emphasis on the best match
        top_score = max(scores)
        avg_score = sum(scores) / len(scores)
        
        # Weighted combination
        confidence = (top_score * 0.7 + avg_score * 0.3)
        
        return min(confidence, 1.0)


# Global instance
qa_service = QAService()
