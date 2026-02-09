# app/models_chat.py
from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Client-generated session id")
    message: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=15)

class ChatCitation(BaseModel):
    source: str = "NG12 PDF"
    page: int
    chunk_id: str
    excerpt: str

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[ChatCitation]

class ChatHistoryItem(BaseModel):
    role: str
    content: str
    ts: float

class ChatHistoryResponse(BaseModel):
    session_id: str
    history: List[ChatHistoryItem]
