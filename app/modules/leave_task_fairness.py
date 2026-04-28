"""
app/modules/leave_task_fairness.py

Detects bias in workplace leave approvals and task assignments.

Leave CSV columns:
    employee_id, gender, caste, location, department,
    leave_type, days_requested, days_approved, approved (1/0)

Task CSV columns:
    employee_id, gender, caste, location, department,
    task_type (high_value/routine/admin), task_count,
    avg_task_complexity (1–5), promotion_track (1/0)
"""
import numpy as np
import pandas as pd
from scipy import stats
from app.config import DISPARATE_IMPACT_RATIO, STAT_SIG_PVALUE

PROTECTED_ATTRS = ["gender", "caste", "location", "department"]


# ── Leave fairness ────────────────────────────────────────────────────────────

def _leave_approval_rates(df: pd.DataFrame, attr: str) -> dict:
    grp = df.groupby(attr).agg(
        total        =("approved", "count"),
        approved_cnt =("approved", "sum"),
        approval_rate=("approved", "mean"),
        avg_days_req =("days_requested", "mean"),
        avg_days_appr=("days_approved",  "mean"),
    ).round(4).reset_index()

    # Fulfilment ratio: days_approved / days_requested
    grp["fulfilment_ratio"] = (grp["avg_days_appr"] / grp["avg_days_req"].replace(0, np.nan)).round(4)
    return grp


def analyse_leave_attribute(df: pd.DataFrame, attr: str) -> dict:
    if attr not in df.columns:
        return {}
    rates = _leave_approval_rates(df, attr)

    # Disparate impact on approval rate
    max_rate = rates["approval_rate"].max()
    di = {str(row[attr]): round(row["approval_rate"] / max_rate, 4) if max_rate else 1.0
          for _, row in rates.iterrows()}
    flagged = [g for g, r in di.items() if r < DISPARATE_IMPACT_RATIO]

    # Fulfilment ratio gap
    fr_gap = round(rates["fulfilment_ratio"].max() - rates["fulfilment_ratio"].min(), 4) \
             if "fulfilment_ratio" in rates.columns else None

    # Chi-square on approved
    ct = pd.crosstab(df[attr], df["approved"])
    chi2, p, dof, _ = stats.chi2_contingency(ct) if ct.shape == (ct.shape[0], 2) and ct.shape[0] > 1 \
                      else (0, 1, 0, None)

    return {
        "attribute":         attr,
        "rates_table":       rates,
        "disparate_impact":  di,
        "flagged_groups":    flagged,
        "fulfilment_gap":    fr_gap,
        "chi2":              round(chi2, 3),
        "p_value":           round(p, 5),
        "significant":       p < STAT_SIG_PVALUE,
    }


def run_leave_analysis(df: pd.DataFrame) -> dict:
    required = {"approved", "days_requested", "days_approved"}
    missing  = required - set(df.columns)
    if missing:
        return {"submodule": "leave", "score": None,
                "error": f"Missing columns: {missing}"}

    analyses = [analyse_leave_attribute(df, a) for a in PROTECTED_ATTRS if a in df.columns]
    analyses = [a for a in analyses if a]

    penalty = 0.0
    for a in analyses:
        if a.get("significant"):
            penalty += 15
        for _, r in a.get("disparate_impact", {}).items():
            if r < DISPARATE_IMPACT_RATIO:
                penalty += (1 - r) * 20
        if (a.get("fulfilment_gap") or 0) > 0.20:
            penalty += 10

    score = round(max(0, 100 - penalty), 1)
    return {"submodule": "leave", "score": score, "analyses": analyses,
            "summary": {"total_requests": len(df),
                        "overall_approval_rate": round(df["approved"].mean(), 4)}}


# ── Task fairness ─────────────────────────────────────────────────────────────

def analyse_task_attribute(df: pd.DataFrame, attr: str) -> dict:
    if attr not in df.columns:
        return {}

    grp = df.groupby(attr).agg(
        count              =("employee_id", "count"),
        avg_complexity     =("avg_task_complexity", "mean"),
        high_value_pct     =("task_type",
                             lambda x: (x == "high_value").mean()),
        promotion_track_pct=("promotion_track", "mean"),
    ).round(4).reset_index() if "avg_task_complexity" in df.columns else \
        df.groupby(attr).agg(count=("employee_id", "count")).reset_index()

    # Disparate impact on high-value task assignment
    if "high_value_pct" in grp.columns:
        max_hvp = grp["high_value_pct"].max()
        di = {str(row[attr]): round(row["high_value_pct"] / max_hvp, 4) if max_hvp else 1.0
              for _, row in grp.iterrows()}
        flagged = [g for g, r in di.items() if r < DISPARATE_IMPACT_RATIO]
    else:
        di, flagged = {}, []

    # Kruskal-Wallis on task complexity across groups
    groups = [g["avg_task_complexity"].dropna().values
              for _, g in df.groupby(attr) if "avg_task_complexity" in df.columns]
    if len(groups) >= 2 and all(len(g) > 0 for g in groups):
        stat, p = stats.kruskal(*groups)
    else:
        stat, p = 0, 1

    return {
        "attribute":        attr,
        "group_table":      grp,
        "disparate_impact": di,
        "flagged_groups":   flagged,
        "kruskal_stat":     round(stat, 3),
        "p_value":          round(p, 5),
        "significant":      p < STAT_SIG_PVALUE,
    }


def run_task_analysis(df: pd.DataFrame) -> dict:
    if "task_type" not in df.columns and "avg_task_complexity" not in df.columns:
        return {"submodule": "task", "score": None,
                "error": "Need task_type or avg_task_complexity column"}

    analyses = [analyse_task_attribute(df, a) for a in PROTECTED_ATTRS if a in df.columns]
    analyses = [a for a in analyses if a]

    penalty = 0.0
    for a in analyses:
        if a.get("significant"):
            penalty += 15
        for _, r in a.get("disparate_impact", {}).items():
            if r < DISPARATE_IMPACT_RATIO:
                penalty += (1 - r) * 20

    score = round(max(0, 100 - penalty), 1)
    return {"submodule": "task", "score": score, "analyses": analyses}


# ── Combined module entry point ───────────────────────────────────────────────

def run_leave_task_analysis(leave_df: pd.DataFrame = None,
                            task_df:  pd.DataFrame = None) -> dict:
    results = {"module": "leave_task"}
    scores  = []

    if leave_df is not None:
        lr = run_leave_analysis(leave_df)
        results["leave"] = lr
        if lr.get("score") is not None:
            scores.append(lr["score"])

    if task_df is not None:
        tr = run_task_analysis(task_df)
        results["task"] = tr
        if tr.get("score") is not None:
            scores.append(tr["score"])

    results["score"] = round(np.mean(scores), 1) if scores else None
    return results
