from pydantic import BaseModel
import os

class Settings(BaseModel):
    # Vertex AI / google-genai
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    google_cloud_location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    use_vertexai: bool = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "True").lower() == "true"

    # Models (configurable so you can switch to Gemini 1.5 if your env still has it)
    gen_model: str = os.getenv("GEN_MODEL", "gemini-2.0-flash")
    embed_model: str = os.getenv("EMBED_MODEL", "gemini-embedding-001")

    # Paths
    patients_path: str = os.getenv("PATIENTS_PATH", "data/patients.json")
    pdf_path: str = os.getenv("NG12_PDF_PATH", "data/ng12.pdf")
    chroma_dir: str = os.getenv("CHROMA_DIR", "data/chroma")

    # RAG defaults
    top_k: int = int(os.getenv("TOP_K", "5"))

settings = Settings()
