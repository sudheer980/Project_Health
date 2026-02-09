import os
import requests
from pypdf import PdfReader
from app.config import settings
from app.rag.chunking import build_page_chunks
from app.rag.vector_store import VectorStore
from app.llm.gemini_client import GeminiClient

NG12_URL = "https://www.nice.org.uk/guidance/ng12/resources/suspected-cancer-recognition-and-referral-pdf-1837268071621"

def download_pdf(dest_path: str):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return

    r = requests.get(NG12_URL, timeout=120)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(r.content)

def extract_pages(pdf_path: str):
    reader = PdfReader(pdf_path)
    pages = []
    # NOTE: pypdf pages are 0-indexed; we store human page numbers as 1-indexed.
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"page": i + 1, "text": text})
    return pages

def main():
    if not settings.google_cloud_project and settings.use_vertexai:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is required when GOOGLE_GENAI_USE_VERTEXAI=True")

    download_pdf(settings.pdf_path)
    pages = extract_pages(settings.pdf_path)

    chunks = build_page_chunks(pages, chunk_size=1200, overlap=150)
    if not chunks:
        raise RuntimeError("No text extracted from PDF. Check PDF download or parsing.")

    gem = GeminiClient()
    store = VectorStore()

    # Batch embeddings (safe default: 64)
    batch_size = 64
    all_ids, all_docs, all_metas, all_embs = [], [], [], []

    for c in chunks:
        all_ids.append(c["chunk_id"])
        all_docs.append(c["text"])
        all_metas.append({"page": c["page"], "chunk_id": c["chunk_id"], "source": "NG12 PDF"})

    for start in range(0, len(all_docs), batch_size):
        docs_batch = all_docs[start:start+batch_size]
        embs = gem.embed_texts(docs_batch)
        all_embs.extend(embs)

    store.upsert(
        ids=all_ids,
        documents=all_docs,
        embeddings=all_embs,
        metadatas=all_metas
    )

    print(f"✅ Ingested {len(all_docs)} chunks into Chroma at: {settings.chroma_dir}")

if __name__ == "__main__":
    main()
