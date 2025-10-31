
import os, re, fitz, pytesseract
from typing import List, Tuple, Optional
from PIL import Image
from app.core.config import settings

class PageBlock:
    def __init__(self, page_no:int, text:str, images:list):
        self.page_no = page_no
        self.text = text or ""
        self.images = images  # [(xref, bbox)]

def extract_pages(pdf_path:str, page_start:int, page_end:int) -> List[PageBlock]:
    if not os.path.exists(pdf_path): raise FileNotFoundError(f"PDF not found: {pdf_path}")
    doc = fitz.open(pdf_path)
    out = []
    for pno in range(max(1, page_start)-1, min(page_end, len(doc))):
        page = doc[pno]
        text = page.get_text() or ""
        if settings.OCR_ENABLED and len(text.strip()) < 5:
            try:
                mat = fitz.Matrix(2,2)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                if settings.TESSERACT_PATH and os.path.exists(settings.TESSERACT_PATH):
                    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
                text = pytesseract.image_to_string(img, lang="eng")
            except Exception:
                pass
        images = [(im[0], im[3]) for im in page.get_images(full=True)]
        out.append(PageBlock(pno+1, text, images))
    doc.close()
    return out

def _pick_nth(hay:str, needle:Optional[str], idx:Optional[int]) -> Optional[int]:
    if not needle: return None
    positions = [m.start() for m in re.finditer(re.escape(needle), hay)]
    if not positions: return None
    if idx is None or idx >= len(positions): return positions[0]
    return positions[idx]

def apply_boundaries(pages:List[PageBlock], start_text:Optional[str], end_text:Optional[str], start_idx:Optional[int], end_idx:Optional[int]) -> Tuple[str, list]:
    full = "".join([p.text for p in pages])
    s_i = _pick_nth(full, start_text, start_idx)
    e_i = _pick_nth(full, end_text, end_idx)
    # Policy C: if invalid or missing, fallback to full
    if s_i is not None and e_i is not None and e_i > s_i:
        cut = full[s_i:e_i]
    elif s_i is not None and e_i is None:
        cut = full[s_i:]
    elif s_i is None and e_i is not None:
        cut = full[:e_i]
    else:
        cut = full
    imgs = []
    for p in pages:
        for (xref, bbox) in p.images:
            imgs.append({"page": p.page_no, "xref": xref, "bbox": bbox})
    return cut, imgs

def find_inline_latex(text:str):
    latex = []
    latex += re.findall(r"\$\$(.+?)\$\$", text, flags=re.DOTALL)
    latex += re.findall(r"\$(.+?)\$", text, flags=re.DOTALL)
    return [s.strip() for s in latex]
