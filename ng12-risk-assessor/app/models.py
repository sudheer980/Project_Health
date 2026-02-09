from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

class Patient(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    smoking_history: str
    symptoms: List[str]
    symptom_duration_days: int

class Citation(BaseModel):
    source: str = "NG12 PDF"
    page: int
    chunk_id: str
    excerpt: str

Decision = Literal["URGENT_REFERRAL", "URGENT_INVESTIGATION", "NOT_MET", "INSUFFICIENT_EVIDENCE"]

class AssessmentResponse(BaseModel):
    patient_id: str
    decision: Decision
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    reasoning: str
    citations: List[Citation]
    debug: Optional[Dict[str, Any]] = None

class AssessRequest(BaseModel):
    patient_id: str
    top_k: Optional[int] = None
