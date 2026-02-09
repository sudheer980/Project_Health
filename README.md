# NG12 Cancer Risk Assessor 
FastAPI service that:
- Accepts a Patient ID
- Uses tool calling to retrieve structured patient data (from `patients.json`)
- Runs RAG over the official NICE NG12 guideline PDF
- Returns an assessment JSON with citations (page + chunk_id)

## Why model IDs are configurable
Gemini 1.5 model IDs appear retired in Google’s lifecycle table, so the app uses `GEN_MODEL` env var to switch models if needed.

## Setup (Local)

### 1) Create a venv and install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

