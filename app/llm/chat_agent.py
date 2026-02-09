from __future__ import annotations
from typing import List, Tuple
import json

from app.rag.vector_store import VectorStore
from app.llm.gemini_client import GeminiClient


CHAT_SYSTEM_PROMPT = """You are a clinical guideline assistant for NICE NG12.

RULES:
- You MUST answer using ONLY the provided NG12 excerpts.
- If excerpts do not contain enough evidence, say evidence is insufficient.
- NEVER invent thresholds or referral criteria.
- When making clinical pathway statements, ALWAYS cite excerpt sources.

Output format (STRICT JSON ONLY):
{
  "answer": "...",
  "citations": [
    {"page": 123, "chunk_id": "ng12_0123_04", "excerpt": "..."}
  ]
}
"""


# ==========================
# Utility: Extract Chroma Hits
# ==========================
def _extract_hits(query_result: dict) -> List[dict]:

    docs = query_result.get("documents", [[]])[0]
    metas = query_result.get("metadatas", [[]])[0]
    ids = query_result.get("ids", [[]])[0]

    hits = []

    for i in range(len(docs)):
        meta = metas[i] or {}

        hits.append({
            "id": ids[i],
            "text": docs[i],
            "page": int(meta.get("page", -1)),
            "chunk_id": meta.get("chunk_id", ids[i])
        })

    return hits


# ==========================
# Chat Agent
# ==========================
class NG12ChatAgent:

    def __init__(self):
        self.vs = VectorStore()
        self.gem = GeminiClient()

    # --------------------------
    # Main Chat Method
    # --------------------------
    def chat(self, message: str, history: List[dict], top_k: int = 5) -> Tuple[str, List[dict]]:

        # 1️⃣ Embed user question
        q_emb = self.gem.embed_texts([message])[0]

        # 2️⃣ Retrieve guideline chunks
        qr = self.vs.query(q_emb, top_k=top_k)
        hits = _extract_hits(qr)

        # Guardrail: no evidence
        if not hits or all((h["text"] or "").strip() == "" for h in hits):
            return (
                "I couldn’t find support in the NG12 guideline excerpts for this question. "
                "Please refine the symptom or cancer type.",
                []
            )

        # 3️⃣ Build Evidence Block
        evidence = "\n\n".join(
            [f"[{h['chunk_id']} | p.{h['page']}] {h['text']}" for h in hits]
        )

        # 4️⃣ Include Short Conversation Context
        convo = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in history[-8:]
        ])

        # 5️⃣ Construct Prompt
        prompt = f"""{CHAT_SYSTEM_PROMPT}

Conversation so far:
{convo}

User question:
{message}

NG12 excerpts:
{evidence}

Return ONLY valid JSON. No markdown.
"""

        # 6️⃣ Call Gemini
        raw = self.gem.generate(prompt)

        # --------------------------
        # ⭐ CLEAN Markdown JSON
        # --------------------------
        clean_raw = raw.strip()

        if clean_raw.startswith("```"):
            clean_raw = clean_raw.replace("```json", "")
            clean_raw = clean_raw.replace("```", "")
            clean_raw = clean_raw.strip()

        # --------------------------
        # ⭐ Parse JSON Safely
        # --------------------------
        try:
            obj = json.loads(clean_raw)

            answer = obj.get("answer", "").strip()
            citations = obj.get("citations", [])

        except Exception:
            # Fallback if model returns plain text
            answer = clean_raw
            citations = [
                {
                    "page": h["page"],
                    "chunk_id": h["chunk_id"],
                    "excerpt": h["text"][:400]
                }
                for h in hits[:3]
            ]

        # --------------------------
        # ⭐ Normalize Citations
        # --------------------------
        norm_citations = []

        for c in citations[:5]:
            try:
                norm_citations.append({
                    "source": "NG12 PDF",
                    "page": int(c.get("page", -1)),
                    "chunk_id": c.get("chunk_id", ""),
                    "excerpt": (c.get("excerpt", "") or "")[:500]
                })
            except Exception:
                pass

        # If model forgot citations → attach fallback
        if not norm_citations:
            norm_citations = [
                {
                    "source": "NG12 PDF",
                    "page": h["page"],
                    "chunk_id": h["chunk_id"],
                    "excerpt": h["text"][:500]
                }
                for h in hits[:3]
            ]

        return answer, norm_citations
