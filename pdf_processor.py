"""PDF processing utilities for extracting and chunking text from textbooks."""
import os
import io
from typing import List, Dict, Tuple
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import settings


class PDFProcessor:
    """Process PDF files to extract text and create chunks."""
    
    def __init__(self):
        """Initialize the PDF processor."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> Tuple[List[str], int]:
        """
        Extract text from a PDF file, using OCR if necessary.
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Tuple of (list of text per page, total page count)
        """
        pages_text = []
        
        try:
            # Try to extract text directly first
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            page_count = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                
                # If no text found or very little text, use OCR
                if not text or len(text.strip()) < 50:
                    text = self._ocr_page(pdf_bytes, page_num)
                
                pages_text.append(text)
            
            return pages_text, page_count
            
        except Exception as e:
            # If PDF reading fails, try OCR on all pages
            return self._ocr_all_pages(pdf_bytes)
    
    def _ocr_page(self, pdf_bytes: bytes, page_num: int) -> str:
        """
        Perform OCR on a specific page.
        
        Args:
            pdf_bytes: PDF file content as bytes
            page_num: Page number to OCR (0-indexed)
            
        Returns:
            Extracted text from the page
        """
        try:
            images = convert_from_bytes(
                pdf_bytes,
                first_page=page_num + 1,
                last_page=page_num + 1
            )
            
            if images:
                text = pytesseract.image_to_string(images[0])
                return text
            
            return ""
            
        except Exception as e:
            print(f"OCR failed for page {page_num}: {str(e)}")
            return ""
    
    def _ocr_all_pages(self, pdf_bytes: bytes) -> Tuple[List[str], int]:
        """
        Perform OCR on all pages of a PDF.
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Tuple of (list of text per page, total page count)
        """
        try:
            images = convert_from_bytes(pdf_bytes)
            pages_text = []
            
            for image in images:
                text = pytesseract.image_to_string(image)
                pages_text.append(text)
            
            return pages_text, len(images)
            
        except Exception as e:
            print(f"OCR failed for all pages: {str(e)}")
            return [], 0
    
    def chunk_text(self, pages_text: List[str], textbook_id: str) -> List[Dict]:
        """
        Split text into chunks with metadata.
        
        Args:
            pages_text: List of text content per page
            textbook_id: ID of the textbook
            
        Returns:
            List of chunks with metadata
        """
        chunks_with_metadata = []
        
        for page_num, page_text in enumerate(pages_text):
            if not page_text.strip():
                continue
            
            # Split the page text into chunks
            chunks = self.text_splitter.split_text(page_text)
            
            for chunk_index, chunk in enumerate(chunks):
                # Detect if this might be a diagram caption
                is_diagram_caption = self._is_likely_diagram_caption(chunk)
                
                chunk_data = {
                    "text": chunk,
                    "metadata": {
                        "textbook_id": textbook_id,
                        "page_number": page_num + 1,
                        "chunk_index": chunk_index,
                        "is_diagram_caption": is_diagram_caption
                    }
                }
                chunks_with_metadata.append(chunk_data)
        
        return chunks_with_metadata
    
    def _is_likely_diagram_caption(self, text: str) -> bool:
        """
        Heuristic to detect if text is likely a diagram caption.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if likely a diagram caption
        """
        text_lower = text.lower()
        caption_indicators = [
            "figure",
            "fig.",
            "diagram",
            "chart",
            "graph",
            "table",
            "image",
            "illustration"
        ]
        
        # Check if text starts with caption indicators and is relatively short
        if len(text) < 500:
            for indicator in caption_indicators:
                if text_lower.startswith(indicator) or f"\n{indicator}" in text_lower:
                    return True
        
        return False


def save_uploaded_file(file_content: bytes, textbook_id: str, filename: str) -> str:
    """
    Save uploaded file to disk.
    
    Args:
        file_content: File content as bytes
        textbook_id: ID of the textbook
        filename: Original filename
        
    Returns:
        Path to saved file
    """
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    file_path = os.path.join(settings.upload_dir, f"{textbook_id}_{filename}")
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return file_path
