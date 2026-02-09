import os
import json
from typing import List, Dict, Any, Optional, Tuple

from google import genai
from google.genai.types import (
    Tool,
    FunctionDeclaration,
    Schema,
    Type,
    GenerateContentConfig,
)

from app.config import settings

class GeminiClient:
    def __init__(self):
        # google-genai uses env vars for Vertex routing per docs:
        # GOOGLE_GENAI_USE_VERTEXAI=True, GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION :contentReference[oaicite:7]{index=7}
        self.client = genai.Client()
        self.gen_model = settings.gen_model
        self.embed_model = settings.embed_model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # Using Vertex embeddings model; docs mention gemini-embedding-001 :contentReference[oaicite:8]{index=8}
        # Output: list of embedding vectors
        res = self.client.models.embed_content(
            model=self.embed_model,
            contents=texts,
        )
        # google-genai returns embeddings aligned with input order
        return [e.values for e in res.embeddings]

    def tool_call_get_patient(self, patient_id: str, tool_func_name: str = "get_patient") -> Dict[str, Any]:
        """
        Ask model to call get_patient(patient_id). We expect a function call in response.
        """
        fd = FunctionDeclaration(
            name=tool_func_name,
            description="Fetch a patient record from the patient database by patient_id.",
            parameters=Schema(
                type=Type.OBJECT,
                properties={
                    "patient_id": Schema(type=Type.STRING, description="Patient ID like PT-101"),
                },
                required=["patient_id"],
            ),
        )
        tools = [Tool(function_declarations=[fd])]

        prompt = f"""
You are a clinical decision support agent. You must retrieve the patient record first by calling `{tool_func_name}`.
Patient ID: {patient_id}
Call the tool now.
""".strip()

        resp = self.client.models.generate_content(
            model=self.gen_model,
            contents=prompt,
            config=GenerateContentConfig(tools=tools),
        )

        # Extract function call (robustly)
        cand = resp.candidates[0]
        parts = cand.content.parts
        for p in parts:
            if getattr(p, "function_call", None):
                return {
                    "name": p.function_call.name,
                    "args": dict(p.function_call.args or {})
                }

        # If model didn't call tool, fall back
        return {"name": tool_func_name, "args": {"patient_id": patient_id}}

    def generate_json(self, system: str, user: str) -> Dict[str, Any]:
        """
        Generate JSON only (best effort). We'll parse and retry once if needed.
        """
        content = f"""SYSTEM:
{system}

USER:
{user}
"""
        resp = self.client.models.generate_content(model=self.gen_model, contents=content)
        text = resp.text or ""

        # Try strict JSON parse
        try:
            return json.loads(text)
        except Exception:
            # Try to extract first JSON object
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end+1])
                except Exception:
                    pass

        # Last resort
        return {"error": "Model did not return valid JSON", "raw": text}
