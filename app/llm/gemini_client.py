import json
from typing import List, Dict, Any

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
        """
        Vertex AI Gemini client wrapper.

        Requires environment variables:
        GOOGLE_GENAI_USE_VERTEXAI=True
        GOOGLE_CLOUD_PROJECT=<project-id>
        GOOGLE_CLOUD_LOCATION=<region>
        """
        self.client = genai.Client()
        self.gen_model = settings.gen_model
        self.embed_model = settings.embed_model

    # ==========================
    # Embeddings
    # ==========================
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Vertex AI embedding model.
        """

        res = self.client.models.embed_content(
            model=self.embed_model,
            contents=texts
        )

        return [e.values for e in res.embeddings]

    # ==========================
    # Tool Calling
    # ==========================
    def tool_call_get_patient(self, patient_id: str, tool_func_name: str = "get_patient") -> Dict[str, Any]:
        """
        Ask Gemini to call the get_patient tool.
        """

        fd = FunctionDeclaration(
            name=tool_func_name,
            description="Fetch patient record by patient_id",
            parameters=Schema(
                type=Type.OBJECT,
                properties={
                    "patient_id": Schema(
                        type=Type.STRING,
                        description="Patient ID like PT-101"
                    ),
                },
                required=["patient_id"],
            ),
        )

        tools = [Tool(function_declarations=[fd])]

        prompt = f"""
You are a clinical decision support agent.
You must retrieve the patient record first by calling `{tool_func_name}`.

Patient ID: {patient_id}

Call the tool now.
""".strip()

        resp = self.client.models.generate_content(
            model=self.gen_model,
            contents=prompt,
            config=GenerateContentConfig(tools=tools),
        )

        # Extract function call safely
        cand = resp.candidates[0]
        parts = cand.content.parts

        for p in parts:
            if getattr(p, "function_call", None):
                return {
                    "name": p.function_call.name,
                    "args": dict(p.function_call.args or {})
                }

        # fallback
        return {"name": tool_func_name, "args": {"patient_id": patient_id}}

    # ==========================
    # JSON Generation
    # ==========================
    def generate_json(self, system: str, user: str) -> Dict[str, Any]:
        """
        Force Gemini to return JSON.
        """

        content = f"""
SYSTEM:
{system}

USER:
{user}
"""

        resp = self.client.models.generate_content(
            model=self.gen_model,
            contents=content
        )

        text = resp.text or ""

        # Strict JSON parse
        try:
            return json.loads(text)
        except Exception:
            pass

        # Extract JSON block
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                pass

        return {
            "error": "Model did not return valid JSON",
            "raw": text
        }

    # ==========================
    # ⭐ NEW — TEXT GENERATION
    # ==========================
    def generate(self, prompt: str) -> str:
        """
        Generic text generation helper.
        Used by Chat Agent & Reasoning Agent.
        """

        resp = self.client.models.generate_content(
            model=self.gen_model,
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.2
            )
        )

        return resp.text or ""
