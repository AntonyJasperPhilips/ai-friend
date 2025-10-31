
import fitz

def extract_pages(pdf_path, start, end):
    doc=fitz.open(pdf_path)
    pages=[]
    for p in range(start-1, min(end, len(doc))):
        page=doc[p]
        pages.append({"text":page.get_text(),"images":page.get_images(full=True)})
    doc.close()
    return pages

def apply_boundaries(pages, *args):
    full="".join([p["text"] for p in pages])
    images=[]
    return full, images

def find_inline_latex(text):
    import re
    return re.findall(r"\$(.+?)\$", text)
