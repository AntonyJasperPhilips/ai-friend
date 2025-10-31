
def split_semantic(text):
    parts=text.split("\n\n")
    chunks=[]
    cur=""
    def tokens(s):return len(s.split())
    for p in parts:
        if tokens(cur)+tokens(p)>600:
            chunks.append(cur.strip())
            cur=p
        else:
            cur=(cur+"\n\n"+p) if cur else p
    if cur.strip():chunks.append(cur.strip())
    return chunks
