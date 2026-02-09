# 🧠 NG12 Cancer Risk Assessor + Conversational Guideline Agent

## 📌 Overview

The NG12 Cancer Risk Assessor is an AI-powered Clinical Decision Support
system built using Google Vertex AI Gemini, Retrieval Augmented
Generation (RAG), and FastAPI.

The application:

-   Assesses cancer referral risk using structured patient data\
-   Retrieves evidence from NICE NG12 clinical guidelines\
-   Provides grounded reasoning with citations\
-   Supports multi-turn conversational guideline queries

------------------------------------------------------------------------

# 🎯 Assignment Coverage

This project completes:

✅ Part 1 --- Deterministic Clinical Decision Agent\
✅ Part 2 --- Conversational RAG Chat Agent\
✅ Reuse of Vector Knowledge Base\
✅ Grounded Evidence + Citation Enforcement\
✅ Minimal UI Interface\
✅ Dockerized + Cloud Deployable

------------------------------------------------------------------------

# 🏥 Clinical Objective

The system evaluates whether a patient meets NG12 criteria for:

-   Urgent Referral\
-   Urgent Investigation\
-   Routine Monitoring\
-   Insufficient Evidence

------------------------------------------------------------------------

# 🧱 Architecture

User UI → FastAPI → Tool Calling + RAG + Gemini → Evidence + Citations

------------------------------------------------------------------------

# 🧪 Core Capabilities

## 🩺 Clinical Assessment Mode

Input Patient ID → System:

1.  Retrieves patient structured data
2.  Queries NG12 guideline vector database
3.  Runs reasoning using Gemini 1.5
4.  Returns decision + citations

------------------------------------------------------------------------

## 💬 Conversational Chat Mode

Supports:

-   Multi-turn conversation
-   Context memory
-   Evidence-grounded responses
-   Citation enforcement
-   Failure guardrails

------------------------------------------------------------------------

# 🧬 Technology Stack

Backend: - FastAPI - Python 3.11 - Google Vertex AI (Gemini 1.5) -
ChromaDB Vector Store

Frontend: - HTML / CSS / JavaScript

Infrastructure: - Docker - Google Cloud Run

------------------------------------------------------------------------

# ⚙️ Setup Instructions

## Clone Repository

git clone `<repo_url>`{=html} cd ng12-risk-assessor

## Create Virtual Environment

python -m venv venv venv`\Scripts`{=tex}`\activate`{=tex}

## Install Dependencies

pip install -r requirements.txt

## Vertex Authentication

gcloud auth application-default login

## Build Vector DB

python -m app.rag.ingest_ng12

## Run Locally

uvicorn app.main:app --reload --port 8080

------------------------------------------------------------------------

# ☁️ Production Deployment

gcloud run deploy ng12-agent --source . --allow-unauthenticated

------------------------------------------------------------------------

# 👨‍💻 Author

Sudheer Kumar Divvela

------------------------------------------------------------------------

# 📜 Disclaimer

This project is for demonstration and research purposes only.
