
import re
from typing import List
def split_semantic(unit_text:str) -> List[str]:
    if not unit_text: return []
    parts = re.split(r"\n\s*(Chapter|Unit|Section|Example|Exercise|Theorem|Proof|Definition|Figure)\b|\n\n+", unit_text)
    chunks, cur = [], ""
    def approx_tokens(s): return max(1, len(s.split()))
    for p in parts:
        if not p: continue
        if approx_tokens(cur) + approx_tokens(p) > 600:
            if cur.strip(): chunks.append(cur.strip())
            cur = p
        else:
            cur += ("" if not cur else "\n") + p
    if cur.strip(): chunks.append(cur.strip())
    # medium 300–600 target balancing
    balanced = []
    for c in chunks:
        if len(c.split()) <= 650: balanced.append(c)
        else:
            paras = c.split("\n\n")
            buf = ""
            for para in paras:
                if len((buf + " " + para).split()) > 600:
                    if buf.strip(): balanced.append(buf.strip())
                    buf = para
                else:
                    buf = (buf + "\n\n" + para) if buf else para
            if buf.strip(): balanced.append(buf.strip())
    return balanced
