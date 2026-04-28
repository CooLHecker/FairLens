"""
app/routers/analysis.py  —  All FairLens API endpoints
"""
import io
import os
import uuid
import numpy as np
import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.config import MODULE_WEIGHTS, REPORTS_DIR, UPLOAD_DIR
from app.modules.hiring_bias      import run_hiring_analysis
from app.modules.ml_bias          import run_ml_analysis
from app.modules.manager_fairness import run_manager_analysis
from app.modules.leave_task_fairness import run_leave_task_analysis
from app.utils.gemini   import build_full_prompt, call_gemini
from app.utils.pdf_report import build_report

router = APIRouter(prefix="/api/v1", tags=["FairLens"])

os.makedirs(UPLOAD_DIR,  exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def _read_csv(upload: UploadFile) -> pd.DataFrame:
    try:
        contents = upload.file.read()
        return pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")


def _safe_score(result: dict | None) -> float | None:
    if result is None:
        return None
    return result.get("score")


def _header_score(score: float | None) -> str:
    if score is None:
        return "N/A"
    return str(score)


def _overall_score(module_scores: dict) -> float:
    total_w, weighted_sum = 0, 0.0
    for mod, score in module_scores.items():
        if score is not None:
            w = MODULE_WEIGHTS.get(mod, 0)
            weighted_sum += score * w
            total_w      += w
    return round(weighted_sum / total_w, 1) if total_w else 0.0


def _make_serialisable(obj):
    """Recursively convert DataFrames and numpy types to JSON-safe structures."""
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict("records")
    if isinstance(obj, dict):
        return {k: _make_serialisable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_serialisable(i) for i in obj]
    if isinstance(obj, np.ndarray):          # ← FIX: was silently returned as-is
        return [_make_serialisable(i) for i in obj.tolist()]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


# ── Health check ──────────────────────────────────────────────────────────────

@router.get("/health", summary="Health check")
def health():
    return {"status": "ok", "service": "FairLens Bias Detector API v1"}


# ── Hiring bias ───────────────────────────────────────────────────────────────

@router.post("/analyse/hiring", summary="Analyse hiring dataset for bias")
async def analyse_hiring(file: UploadFile = File(...)):
    df     = _read_csv(file)
    result = run_hiring_analysis(df)
    return JSONResponse(_make_serialisable(result))


# ── ML model bias ─────────────────────────────────────────────────────────────

@router.post("/analyse/ml-model", summary="Analyse ML model predictions for bias")
async def analyse_ml(file: UploadFile = File(...)):
    """
    CSV must contain: candidate_id, gender, caste, location, college_tier,
    education_level, actual_label, predicted_label, predicted_probability
    """
    df     = _read_csv(file)
    result = run_ml_analysis(df)
    return JSONResponse(_make_serialisable(result))


# ── Manager fairness ──────────────────────────────────────────────────────────

@router.post("/analyse/manager", summary="Analyse manager-level fairness")
async def analyse_manager(file: UploadFile = File(...)):
    """
    CSV must contain: candidate_id, manager_id, gender, caste, selected
    Optional: interview_score, location, college_tier, education_level
    """
    df     = _read_csv(file)
    result = run_manager_analysis(df)
    return JSONResponse(_make_serialisable(result))


# ── Leave / task fairness ─────────────────────────────────────────────────────

@router.post("/analyse/leave-task", summary="Analyse leave approval and task assignment fairness")
async def analyse_leave_task(
    leave_file: UploadFile = File(None),
    task_file:  UploadFile = File(None),
):
    """
    leave_file CSV: employee_id, gender, caste, department,
                    days_requested, days_approved, approved
    task_file  CSV: employee_id, gender, caste, department,
                    task_type, avg_task_complexity, promotion_track
    At least one file required.
    """
    if leave_file is None and task_file is None:
        raise HTTPException(422, "Provide at least one of leave_file or task_file")

    leave_df = _read_csv(leave_file) if leave_file else None
    task_df  = _read_csv(task_file)  if task_file  else None
    result   = run_leave_task_analysis(leave_df, task_df)
    return JSONResponse(_make_serialisable(result))


# ── Full audit (all modules) + PDF report ─────────────────────────────────────

@router.post("/analyse/full-audit", summary="Run all modules and generate PDF report")
async def full_audit(
    hiring_file:  UploadFile = File(...),
    ml_file:      UploadFile = File(None),
    manager_file: UploadFile = File(None),
    leave_file:   UploadFile = File(None),
    task_file:    UploadFile = File(None),
    gemini_key:   str        = Form(""),
):
    """
    Runs all available modules and returns a downloadable PDF bias audit report.
    Only hiring_file is mandatory; all others are optional.
    """
    # ── Run modules ──────────────────────────────────────────────────────────
    hiring_df     = _read_csv(hiring_file)
    hiring_result = run_hiring_analysis(hiring_df)

    ml_result = None
    if ml_file:
        ml_df     = _read_csv(ml_file)
        ml_result = run_ml_analysis(ml_df)

    manager_result = None
    if manager_file:
        mgr_df         = _read_csv(manager_file)
        manager_result = run_manager_analysis(mgr_df)

    leave_result = None
    if leave_file or task_file:
        leave_df     = _read_csv(leave_file) if leave_file else None
        task_df      = _read_csv(task_file)  if task_file  else None
        leave_result = run_leave_task_analysis(leave_df, task_df)

    # ── Compute overall score ─────────────────────────────────────────────────
    module_scores = {
        "hiring":    _safe_score(hiring_result),
        "ml_model":  _safe_score(ml_result),
        "manager":   _safe_score(manager_result),
        "leave_task":_safe_score(leave_result),
    }
    overall = _overall_score(module_scores)

    # ── Gemini AI narrative ───────────────────────────────────────────────────
    prompt = build_full_prompt(
        overall_score  = overall,
        module_scores  = module_scores,
        hiring_result  = hiring_result,
        ml_result      = ml_result,
        manager_result = manager_result,
        leave_result   = leave_result,
    )
    gemini  = call_gemini(prompt, api_key=gemini_key)

    # ── Generate PDF ──────────────────────────────────────────────────────────
    report_id   = uuid.uuid4().hex[:8]
    report_path = os.path.join(REPORTS_DIR, f"fairlens_report_{report_id}.pdf")

    build_report(
        out_path       = report_path,
        overall_score  = overall,
        module_scores  = module_scores,
        hiring_result  = hiring_result,
        ml_result      = ml_result,
        manager_result = manager_result,
        leave_result   = leave_result,
        gemini_text    = gemini,
        meta           = {
            "dataset": hiring_file.filename,
            "total":   len(hiring_df),
        },
    )

    return FileResponse(
        path         = report_path,
        media_type   = "application/pdf",
        filename     = f"fairlens_report_{report_id}.pdf",
        headers      = {
            "X-Overall-Score":  str(overall),
            "X-Hiring-Score":   _header_score(module_scores["hiring"]),
            "X-ML-Score":       _header_score(module_scores["ml_model"]),
            "X-Manager-Score":  _header_score(module_scores["manager"]),
            "X-Leave-Score":    _header_score(module_scores["leave_task"]),
            "X-Report-ID":      report_id,
        },
    )


# ── Download previously generated report ──────────────────────────────────────

@router.get("/report/{report_id}", summary="Download a previously generated report")
def download_report(report_id: str):
    path = os.path.join(REPORTS_DIR, f"fairlens_report_{report_id}.pdf")
    if not os.path.exists(path):
        raise HTTPException(404, "Report not found")
    return FileResponse(path, media_type="application/pdf",
                        filename=f"fairlens_report_{report_id}.pdf")
