from typing import List, Dict

def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> List[str]:
    text = " ".join(text.split())
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
        if end == len(text):
            break
    return chunks

def build_page_chunks(pages: List[Dict], chunk_size: int = 1200, overlap: int = 150) -> List[Dict]:
    """
    pages: [{ "page": int, "text": str }]
    returns: [{ "page": int, "chunk_id": str, "text": str }]
    """
    out = []
    for p in pages:
        page_num = p["page"]
        chunks = chunk_text(p["text"], chunk_size=chunk_size, overlap=overlap)
        for idx, ch in enumerate(chunks):
            chunk_id = f"ng12_{page_num:04d}_{idx:02d}"
            out.append({"page": page_num, "chunk_id": chunk_id, "text": ch})
    return out
