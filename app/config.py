"""
FairLens — Central Configuration

HOW TO SET YOUR GEMINI API KEY (pick one):
  Option A — Edit this file:
      GEMINI_API_KEY = "AIza...your_key_here..."

  Option B — Environment variable (recommended for production):
      Windows:   set GEMINI_API_KEY=AIza...
      Mac/Linux: export GEMINI_API_KEY=AIza...

Get a free key at: https://aistudio.google.com/app/apikey

NOTE ON QUOTA ERRORS (429):
  The free tier has per-minute and per-day limits per model.
  FairLens automatically tries 4 different models in sequence:
    1. gemini-2.0-flash-lite  (lowest quota usage)
    2. gemini-2.0-flash
    3. gemini-1.5-flash
    4. gemini-1.5-flash-8b
  If all are exhausted, wait a few minutes or enable billing on GCP.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Gemini API key ────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# ── Qualification thresholds (merit-only, no demographics) ────────────────────
MIN_SKILLS_SCORE    = 50.0
MIN_EDUCATION_LEVEL = 1       # 0=HighSchool, 1=Bachelor, 2=Master, 3=PhD
MIN_CGPA            = 6.0

# ── Bias detection thresholds ─────────────────────────────────────────────────
STAT_SIG_PVALUE        = 0.05
DISPARATE_IMPACT_RATIO = 0.80  # EEOC 4/5ths rule

# ── Module weights (must sum to 100) ──────────────────────────────────────────
MODULE_WEIGHTS = {
    "hiring":    40,
    "ml_model":  20,
    "manager":   20,
    "leave_task": 20,
}

# ── Hiring attribute weights (must sum to 100) ────────────────────────────────
HIRING_ATTR_WEIGHTS = {
    "gender":          25,
    "caste":           25,
    "location":        15,
    "college_tier":    20,
    "education_level": 15,
}

# ── File storage paths ────────────────────────────────────────────────────────
UPLOAD_DIR  = "uploads"
REPORTS_DIR = "reports"
