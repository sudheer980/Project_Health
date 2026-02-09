# PROMPTS.md — NG12 Cancer Risk Assessor

## System Prompt Strategy (Part 1)

I use a strict system prompt to keep the model grounded and consistent:

1. **Grounding rule:** “Use ONLY the provided patient data and NG12 evidence snippets.”
2. **No hallucinations:** If evidence is missing/weak, return `INSUFFICIENT_EVIDENCE`.
3. **Deterministic output contract:** Return strict JSON with a fixed schema.
4. **Citation enforcement:** Every pathway statement must be backed by citations (page + chunk_id).
5. **Clinical safety posture:** Avoid inventing thresholds, durations, age cut-offs, or tests.

## Tool Use (Patient Retrieval)

The model is first asked to call a tool `get_patient(patient_id)` (function calling).
The application executes the tool against `patients.json` (simulated DB), then proceeds with RAG + reasoning.

## RAG Context Packing

- PDF is chunked per page with overlap.
- Retrieval query is built from symptoms and asks explicitly for “urgent referral/investigation criteria.”
- Retrieved chunks are formatted as:
  `[chunk_id | p.N] <text>`
This makes citations easy and keeps traceability.
