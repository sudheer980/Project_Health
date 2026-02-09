from typing import List, Dict, Any
from app.models import Patient, AssessmentResponse, Citation
from app.config import settings
from app.rag.vector_store import VectorStore
from app.llm.gemini_client import GeminiClient
from app.llm.prompts import ASSESSOR_SYSTEM_PROMPT

def build_query(patient: Patient) -> str:
    # Simple, readable query for retrieval
    symptoms = ", ".join(patient.symptoms)
    return f"NG12 criteria for: {symptoms}. Include age thresholds and urgent referral/investigation guidance."

def format_evidence(rows: List[Dict[str, Any]]) -> str:
    # rows: [{page, chunk_id, text}]
    lines = []
    for r in rows:
        lines.append(f"[{r['chunk_id']} | p.{r['page']}] {r['text']}")
    return "\n\n".join(lines)

def to_citations(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cits = []
    for r in rows:
        excerpt = (r["text"][:260] + "...") if len(r["text"]) > 260 else r["text"]
        cits.append({
            "source": "NG12 PDF",
            "page": int(r["page"]),
            "chunk_id": r["chunk_id"],
            "excerpt": excerpt
        })
    return cits

class NG12Assessor:
    def __init__(self):
        self.gem = GeminiClient()
        self.store = VectorStore()

    def retrieve(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        q_emb = self.gem.embed_texts([query])[0]
        res = self.store.query(q_emb, top_k=top_k)

        docs = res["documents"][0]
        metas = res["metadatas"][0]

        rows = []
        for d, m in zip(docs, metas):
            rows.append({
                "text": d,
                "page": m.get("page"),
                "chunk_id": m.get("chunk_id"),
                "source": m.get("source", "NG12 PDF"),
            })
        return rows

    def assess(self, patient: Patient, top_k: int = None) -> AssessmentResponse:
        k = top_k or settings.top_k
        query = build_query(patient)
        evidence_rows = self.retrieve(query, k)

        user_prompt = f"""
PATIENT:
{patient.model_dump_json(indent=2)}

NG12 EVIDENCE SNIPPETS:
{format_evidence(evidence_rows)}
""".strip()

        raw = self.gem.generate_json(ASSESSOR_SYSTEM_PROMPT, user_prompt)

        # If model forgot citations, attach retrieved ones as fallback
        if isinstance(raw, dict) and "citations" not in raw:
            raw["citations"] = to_citations(evidence_rows)

        # Build pydantic output
        citations = []
        for c in raw.get("citations", []):
            citations.append(Citation(**c))

        return AssessmentResponse(
            patient_id=raw.get("patient_id", patient.patient_id),
            decision=raw.get("decision", "INSUFFICIENT_EVIDENCE"),
            confidence=float(raw.get("confidence", 0.5)),
            summary=raw.get("summary", ""),
            reasoning=raw.get("reasoning", ""),
            citations=citations,
            debug={
                "rag_query": query,
                "model": settings.gen_model,
                "embed_model": settings.embed_model,
                "top_k": k
            }
        )
