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

app = FastAPI(title="NG12 Cancer Risk Assessor", version="2.0")

# Serve UI Static Files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# =====================
# Initialize Services
# =====================

store = PatientStore()
assessor = NG12Assessor()
gem = GeminiClient()

# Chat Mode Services
chat_store = ChatStore()
chat_agent = NG12ChatAgent()

# =====================
# UI Home Page
# =====================

@app.get("/")
def home():
    return FileResponse("web/index.html")

# =====================
# PART 1 — Clinical Assessor
# =====================

@app.post("/assess", response_model=AssessmentResponse)
def assess(req: AssessRequest):

    # Tool Call Simulation
    tool_call = gem.tool_call_get_patient(req.patient_id)
    patient_id = tool_call.get("args", {}).get("patient_id", req.patient_id)

    patient = store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient not found: {patient_id}")

    # RAG + Reasoning
    result = assessor.assess(patient, top_k=req.top_k)
    return result

# =====================
# PART 2 — Chat Mode
# =====================

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    # Store user message
    chat_store.add(req.session_id, "user", req.message)

    # Get conversation history
    history = chat_store.to_openai_style(req.session_id, max_messages=12)

    # Run Chat Agent (RAG + Gemini)
    answer, citations = chat_agent.chat(
        message=req.message,
        history=history,
        top_k=req.top_k
    )

    # Store assistant response
    chat_store.add(req.session_id, "assistant", answer)

    return {
        "session_id": req.session_id,
        "answer": answer,
        "citations": citations
    }

# =====================
# Chat History
# =====================

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

# =====================
# Clear Chat Session
# =====================

@app.delete("/chat/{session_id}")
def chat_clear(session_id: str):
    chat_store.clear(session_id)
    return {"session_id": session_id, "cleared": True}

# =====================
# Health Check
# =====================

@app.get("/health")
def health():
    return {"status": "ok"}
