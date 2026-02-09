from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

class VectorStore:
    def __init__(self, persist_dir: str = settings.chroma_dir, collection: str = "ng12"):
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.col = self.client.get_or_create_collection(name=collection, metadata={"hnsw:space": "cosine"})

    def upsert(self, ids: List[str], documents: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]):
        self.col.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def query(self, query_embedding: List[float], top_k: int = 5):
        return self.col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
