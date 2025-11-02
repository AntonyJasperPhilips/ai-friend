
import os, re, fitz, pytesseract
import logging
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image
from app.core.config import settings

logger = logging.getLogger(__name__)

class PageBlock:
    def __init__(self, page_no:int, text:str, images:list):
        self.page_no = page_no
        self.text = text or ""
        self.images = images  # [(xref, bbox)]

def extract_pages(pdf_path:str, page_start:int, page_end:int, language_code:str="en") -> List[PageBlock]:
    """Extract pages from PDF with text and image metadata."""
    if not os.path.exists(pdf_path): raise FileNotFoundError(f"PDF not found: {pdf_path}")
    doc = fitz.open(pdf_path)
    out = []
    try:
        # Map language codes to Tesseract language codes
        lang_map = {
            "en": "eng", "es": "spa", "fr": "fra", "de": "deu", "it": "ita",
            "pt": "por", "ru": "rus", "ar": "ara", "hi": "hin", "zh": "chi_sim",
            "ja": "jpn", "ko": "kor", "th": "tha", "vi": "vie", "tr": "tur",
            "nl": "nld", "pl": "pol", "uk": "ukr", "he": "heb"
        }
        ocr_lang = lang_map.get(language_code.lower(), "eng")
        
        for pno in range(max(1, page_start)-1, min(page_end, len(doc))):
            page = doc[pno]
            text = page.get_text() or ""
            
            # OCR for scanned pages with little text
            if settings.OCR_ENABLED and len(text.strip()) < 5:
                try:
                    mat = fitz.Matrix(2,2)
                    pix = page.get_pixmap(matrix=mat)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    if settings.TESSERACT_PATH and os.path.exists(settings.TESSERACT_PATH):
                        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
                    text = pytesseract.image_to_string(img, lang=ocr_lang)
                    logger.info(f"Applied OCR to page {pno+1} using language: {ocr_lang}")
                except Exception as e:
                    logger.warning(f"OCR failed for page {pno+1}: {e}")
            
            # Extract image references - filter invalid xrefs
            images = []
            try:
                image_list = page.get_images(full=True)
                logger.info(f"Page {pno+1}: PyMuPDF found {len(image_list)} image objects")
                
                for idx, img in enumerate(image_list):
                    xref = img[0]
                    bbox = img[3]  # Bounding box coordinates
                    # Only include valid xrefs (non-zero)
                    if xref > 0:
                        images.append((xref, bbox))
                        logger.debug(f"Page {pno+1}: Adding valid image xref={xref}")
                    else:
                        logger.warning(f"Page {pno+1}: Skipping invalid xref=0 (image {idx+1})")
                        
                if images:
                    logger.info(f"Found {len(images)} valid images on page {pno+1}")
                else:
                    logger.warning(f"No valid images found on page {pno+1} (PyMuPDF found {len(image_list)} objects)")
            except Exception as e:
                logger.error(f"Error extracting image list from page {pno+1}: {e}", exc_info=True)
            
            out.append(PageBlock(pno+1, text, images))
    finally:
        doc.close()
    return out

def _pick_nth(hay:str, needle:Optional[str], idx:Optional[int]) -> Optional[int]:
    if not needle: return None
    positions = [m.start() for m in re.finditer(re.escape(needle), hay)]
    if not positions: return None
    if idx is None or idx >= len(positions): return positions[0]
    return positions[idx]

def apply_boundaries(pages:List[PageBlock], start_text:Optional[str], end_text:Optional[str], start_idx:Optional[int], end_idx:Optional[int]) -> Tuple[str, list]:
    """Apply text boundaries and collect image references with improved filtering."""
    full = "".join([p.text for p in pages])
    s_i = _pick_nth(full, start_text, start_idx)
    e_i = _pick_nth(full, end_text, end_idx)
    # Policy: if invalid or missing, fallback to full
    if s_i is not None and e_i is not None and e_i > s_i:
        cut = full[s_i:e_i]
    elif s_i is not None and e_i is None:
        cut = full[s_i:]
    elif s_i is None and e_i is not None:
        cut = full[:e_i]
    else:
        cut = full
    
    # Collect image references (already filtered for xref > 0 in extract_pages)
    imgs = []
    for p in pages:
        for (xref, bbox) in p.images:
            imgs.append({
                "page": p.page_no, 
                "xref": xref, 
                "bbox": bbox
            })
    
    if imgs:
        logger.info(f"Collected {len(imgs)} valid image references from {len(pages)} pages")
    
    return cut, imgs

def find_inline_latex(text:str):
    """Find LaTeX formulas in text (both inline $...$ and block $$...$$)."""
    latex = []
    latex += re.findall(r"\$\$(.+?)\$\$", text, flags=re.DOTALL)
    latex += re.findall(r"\$(.+?)\$", text, flags=re.DOTALL)
    return [s.strip() for s in latex]

def extract_image_data(pdf_path: str, xref: int) -> Optional[Dict[str, Any]]:
    """
    Safely extract image data from PDF by xref.
    
    Args:
        pdf_path: Path to PDF file
        xref: Cross-reference number of the image
        
    Returns:
        Dictionary with 'image' (bytes), 'ext' (str), 'width', 'height', 'colorspace', etc.
        Returns None if extraction fails.
    """
    if xref <= 0:
        logger.warning(f"Invalid xref={xref}, cannot extract image")
        return None
        
    doc = None
    try:
        doc = fitz.open(pdf_path)
        img_dict = doc.extract_image(xref)
        
        if not img_dict or not img_dict.get("image"):
            logger.warning(f"Failed to extract image data for xref={xref}")
            return None
            
        logger.debug(f"Successfully extracted image xref={xref}, size={len(img_dict.get('image', b''))} bytes")
        return img_dict
        
    except Exception as e:
        logger.error(f"Exception extracting image xref={xref}: {e}")
        return None
    finally:
        if doc:
            doc.close()
