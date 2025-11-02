
import re
from typing import List
from app.core.config import settings

def split_semantic(unit_text:str, chunk_size:int=None, overlap:int=None) -> List[str]:
    """
    Split text with configurable chunk size and overlap.
    
    Args:
        unit_text: Text to chunk
        chunk_size: Target tokens per chunk (default: 600)
        overlap: Token overlap between chunks (default: 50)
    """
    if not unit_text: 
        return []
    
    # Use config defaults or provided values
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP
    
    parts = re.split(r"\n\s*(Chapter|Unit|Section|Example|Exercise|Theorem|Proof|Definition|Figure)\b|\n\n+", unit_text)
    chunks, cur = [], ""
    def approx_tokens(s): return max(1, len(s.split()))
    
    for p in parts:
        if not p: continue
        if approx_tokens(cur) + approx_tokens(p) > chunk_size:
            if cur.strip(): 
                chunks.append(cur.strip())
            
            # Add overlap from previous chunk
            cur_words = cur.strip().split()
            if len(cur_words) > overlap:
                cur = " ".join(cur_words[-overlap:]) + " " + p
            else:
                cur = p
        else:
            cur += ("" if not cur else "\n") + p
    
    if cur.strip(): 
        chunks.append(cur.strip())
    
    # Re-balance large chunks
    balanced = []
    for c in chunks:
        if approx_tokens(c) <= chunk_size:
            balanced.append(c)
        else:
            paras = c.split("\n\n")
            buf = ""
            
            for para in paras:
                if approx_tokens(buf) + approx_tokens(para) > chunk_size:
                    if buf.strip(): 
                        balanced.append(buf.strip())
                    
                    # Add overlap
                    prev_words = buf.strip().split() if buf.strip() else []
                    if len(prev_words) > overlap:
                        buf = " ".join(prev_words[-overlap:]) + "\n\n" + para
                    else:
                        buf = para
                else:
                    buf = (buf + "\n\n" + para) if buf else para
            
            if buf.strip(): 
                balanced.append(buf.strip())
    
    return balanced
