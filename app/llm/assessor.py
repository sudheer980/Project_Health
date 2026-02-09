# app/llm/assessor.py
from typing import List, Dict, Any

from app.models import Patient, AssessmentResponse, Citation
from app.config import settings
from app.rag.vector_store import VectorStore
from app.llm.gemini_client import GeminiClient
from app.llm.prompts import ASSESSOR_SYSTEM_PROMPT


def build_query(patient: Patient) -> str:
    symptoms = ", ".join(patient.symptoms)
    return (
        f"NG12 criteria for: {symptoms}. "
        f"Include age thresholds and urgent referral/investigation guidance."
    )


def format_evidence(rows: List[Dict[str, Any]]) -> str:
    lines = []
    for r in rows:
        lines.append(f"[{r.get('chunk_id')} | p.{r.get('page')}] {r.get('text')}")
    return "\n\n".join(lines)


def to_rag_citations(rows: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    cits: List[Dict[str, Any]] = []
    for r in rows[:limit]:
        text = (r.get("text") or "").strip()
        excerpt = (text[:260] + "...") if len(text) > 260 else text
        cits.append(
            {
                "source": r.get("source", "NG12 PDF"),
                "page": int(r.get("page", -1) or -1),
                "chunk_id": r.get("chunk_id", ""),
                "excerpt": excerpt,
            }
        )
    return cits


def normalize_model_citations(raw_citations: Any) -> List[Dict[str, Any]]:
    """
    Model might return:
      - list[dict]
      - dict (single)
      - None / string / weird
    Normalize into list[dict].
    """
    if raw_citations is None:
        return []
    if isinstance(raw_citations, dict):
        raw_citations = [raw_citations]
    if not isinstance(raw_citations, list):
        return []

    out: List[Dict[str, Any]] = []
    for c in raw_citations:
        if not isinstance(c, dict):
            continue
        out.append(
            {
                "source": c.get("source", "NG12 PDF"),
                "page": int(c.get("page", -1) or -1),
                "chunk_id": c.get("chunk_id", "") or "",
                "excerpt": (c.get("excerpt", "") or "")[:500],
            }
        )
    return out


def merge_dedupe_citations(
    model_cits: List[Dict[str, Any]],
    rag_cits: List[Dict[str, Any]],
    limit: int,
) -> List[Dict[str, Any]]:
    """
    Merge model citations + RAG citations.
    Dedupe by (chunk_id, page).
    Keep ordering: model first (if any), then RAG.
    """
    merged: List[Dict[str, Any]] = []
    seen = set()

    for c in model_cits + rag_cits:
        chunk_id = (c.get("chunk_id") or "").strip()
        page = int(c.get("page", -1) or -1)
        key = (chunk_id, page)

        # skip invalid
        if not chunk_id and page == -1:
            continue

        if key in seen:
            continue
        seen.add(key)
        merged.append(c)

        if len(merged) >= limit:
            break

    return merged


class NG12Assessor:
    def __init__(self):
        self.gem = GeminiClient()
        self.store = VectorStore()

    def retrieve(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        q_emb = self.gem.embed_texts([query])[0]
        res = self.store.query(q_emb, top_k=top_k)

        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        ids = res.get("ids", [[]])[0]

        rows: List[Dict[str, Any]] = []
        for i in range(min(len(docs), len(metas))):
            m = metas[i] or {}
            rows.append(
                {
                    "text": docs[i],
                    "page": m.get("page", -1),
                    "chunk_id": m.get("chunk_id", ids[i] if i < len(ids) else ""),
                    "source": m.get("source", "NG12 PDF"),
                }
            )
        return rows

    def assess(self, patient: Patient, top_k: int = None) -> AssessmentResponse:
        k = int(top_k or settings.top_k)
        query = build_query(patient)

        # RAG retrieval (k chunks)
        evidence_rows = self.retrieve(query, k)

        user_prompt = f"""
PATIENT:
{patient.model_dump_json(indent=2)}

NG12 EVIDENCE SNIPPETS:
{format_evidence(evidence_rows)}
""".strip()

        # LLM output (dict)
        raw = self.gem.generate_json(ASSESSOR_SYSTEM_PROMPT, user_prompt)
        if not isinstance(raw, dict):
            raw = {"raw": str(raw)}

        # --- IMPORTANT: ALWAYS ensure citations are present and are up to k ---
        rag_cits = to_rag_citations(evidence_rows, limit=k)
        model_cits = normalize_model_citations(raw.get("citations"))
        merged_cits = merge_dedupe_citations(model_cits, rag_cits, limit=k)
        raw["citations"] = merged_cits

        # Build pydantic output
        citations: List[Citation] = []
        for c in raw.get("citations", []):
            try:
                citations.append(Citation(**c))
            except Exception:
                # skip malformed citation
                pass

        return AssessmentResponse(
            patient_id=raw.get("patient_id", patient.patient_id),
            decision=raw.get("decision", "INSUFFICIENT_EVIDENCE"),
            confidence=float(raw.get("confidence", 0.5) or 0.5),
            summary=raw.get("summary", ""),
            reasoning=raw.get("reasoning", ""),
            citations=citations,
            debug={
                "rag_query": query,
                "model": settings.gen_model,
                "embed_model": settings.embed_model,
                "top_k": k,
                "retrieved_chunks": len(evidence_rows),
            },
        )
