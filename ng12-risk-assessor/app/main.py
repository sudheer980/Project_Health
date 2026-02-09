from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.models import AssessRequest, AssessmentResponse
from app.patient_store import PatientStore
from app.llm.assessor import NG12Assessor
from app.llm.gemini_client import GeminiClient

app = FastAPI(title="NG12 Cancer Risk Assessor", version="1.0")

# Serve UI
app.mount("/static", StaticFiles(directory="web"), name="web")

store = PatientStore()
assessor = NG12Assessor()
gem = GeminiClient()

@app.get("/")
def home():
    return FileResponse("web/index.html")

@app.post("/assess", response_model=AssessmentResponse)
def assess(req: AssessRequest):
    # 1) Tool use: model calls get_patient (we execute it)
    tool_call = gem.tool_call_get_patient(req.patient_id)
    patient_id = tool_call.get("args", {}).get("patient_id", req.patient_id)

    patient = store.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient not found: {patient_id}")

    # 2) RAG + 3) reasoning
    result = assessor.assess(patient, top_k=req.top_k)
    return result

@app.get("/health")
def health():
    return {"status": "ok"}
