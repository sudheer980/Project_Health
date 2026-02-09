from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Part 1 Imports
from app.models import AssessRequest, AssessmentResponse
from app.patient_store import PatientStore
from app.llm.assessor import NG12Assessor
from app.llm.gemini_client import GeminiClient

# Part 2 Imports
from app.chat_store import ChatStore
from app.models_chat import ChatRequest, ChatResponse, ChatHistoryResponse
from app.llm.chat_agent import NG12ChatAgent


BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"

app = FastAPI(title="NG12 Cancer Risk Assessor", version="2.0")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def home():
    return FileResponse(str(WEB_DIR / "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


# =====================
# Initialize Services
# =====================

store = PatientStore()
assessor = NG12Assessor()
gem = GeminiClient()

chat_store = ChatStore()
chat_agent = NG12ChatAgent()


# =====================
# PART 1 — Clinical Assessor
# =====================

@app.post("/assess", response_model=AssessmentResponse)
def assess(req: AssessRequest):

    tool_call = gem.tool_call_get_patient(req.patient_id)
    patient_id = tool_call.get("args", {}).get("patient_id", req.patient_id)

    patient = store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient not found: {patient_id}")

    return assessor.assess(patient, top_k=req.top_k)


# =====================
# PART 2 — Chat Mode
# =====================

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    chat_store.add(req.session_id, "user", req.message)

    history = chat_store.to_openai_style(req.session_id, max_messages=12)

    answer, citations = chat_agent.chat(
        message=req.message,
        history=history,
        top_k=req.top_k
    )

    chat_store.add(req.session_id, "assistant", answer)

    return {
        "session_id": req.session_id,
        "answer": answer,
        "citations": citations
    }


@app.get("/chat/{session_id}/history", response_model=ChatHistoryResponse)
def chat_history(session_id: str):

    history = chat_store.get(session_id)

    return {
        "session_id": session_id,
        "history": [
            {"role": msg.role, "content": msg.content, "ts": msg.ts}
            for msg in history
        ]
    }


@app.delete("/chat/{session_id}")
def chat_clear(session_id: str):
    chat_store.clear(session_id)
    return {"session_id": session_id, "cleared": True}
