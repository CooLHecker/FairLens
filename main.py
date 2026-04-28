"""
main.py  —  FairLens FastAPI Application
─────────────────────────────────────────
Run:   uvicorn main:app --reload --port 8000
Docs:  http://localhost:8000/docs
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers.analysis import router

load_dotenv()

app = FastAPI(
    title       = "FairLens — HR Bias Detection API",
    description = """
## FairLens Bias Detector

Detects and quantifies bias in HR processes across 4 modules:

| Module | Description |
|--------|-------------|
| **Hiring Bias** | Analyses resume / selection data for demographic bias |
| **ML Model Bias** | Checks ML model predictions for disparate impact |
| **Manager Fairness** | Identifies biased managers / interviewers |
| **Leave & Task Fairness** | Detects bias in leave approvals and task assignments |

### Fairness Score
- **75–100**: LOW BIAS ✅
- **50–74**: MODERATE BIAS ⚠️
- **0–49**: HIGH BIAS ❌

Higher score = more fair hiring process.
    """,
    version     = "1.0.0",
    contact     = {"name": "FairLens Team"},
)

# ── CORS (configurable for development and production) ──────────────────────
cors_origins_env = os.getenv("FAIRLENS_CORS_ORIGINS", "*")
allow_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()] or ["*"]
allow_all_origins = allow_origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins     = allow_origins,
    allow_credentials = not allow_all_origins,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.include_router(router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service":  "FairLens Bias Detection API",
        "version":  "1.0.0",
        "docs":     "/docs",
        "health":   "/api/v1/health",
        "endpoints": {
            "hiring":     "POST /api/v1/analyse/hiring",
            "ml_model":   "POST /api/v1/analyse/ml-model",
            "manager":    "POST /api/v1/analyse/manager",
            "leave_task": "POST /api/v1/analyse/leave-task",
            "full_audit": "POST /api/v1/analyse/full-audit  ← generates PDF",
        },
    }
