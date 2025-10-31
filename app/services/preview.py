
from typing import List, Dict

def build_preview(chunks:List[str], latex_list:List[str], images:list, req) -> Dict:
    proposed = []
    for i, ch in enumerate(chunks, start=1):
        proposed.append({
            "ord": i,
            "text": ch,
            "latex": latex_list if latex_list else [],
            "imageRefs": images if images else []
        })
    return {
        "unit": {
            "bookId":req.bookId, "chapterId":req.chapterId, "unitId":req.unitId,
            "language":req.languageCode, "pdfPath": req.pdfPath
        },
        "latexExtracted": latex_list,
        "images": images,
        "proposedChunks": proposed
    }
