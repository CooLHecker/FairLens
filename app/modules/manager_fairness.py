"""
app/modules/manager_fairness.py

Detects bias at the individual manager / interviewer level.

Expected CSV columns:
    candidate_id, manager_id, gender, caste, location,
    college_tier, education_level, interview_score (0–100),
    selected, is_qualified (optional)

Key questions answered:
  1. Does a manager's selection rate differ significantly by protected group?
  2. Are some managers consistent outliers in accepting/rejecting protected groups?
  3. Is there a gap in interview_score assigned to same-merit candidates across groups?
"""
import numpy as np
import pandas as pd
from scipy import stats
from app.config import DISPARATE_IMPACT_RATIO, STAT_SIG_PVALUE

PROTECTED_ATTRS = ["gender", "caste", "location", "college_tier"]


# ── Per-manager bias profile ──────────────────────────────────────────────────

def _manager_attribute_bias(mgr_df: pd.DataFrame, attr: str) -> dict:
    if attr not in mgr_df.columns or mgr_df[attr].nunique() < 2:
        return {}
    rates = mgr_df.groupby(attr)["selected"].mean().round(4).to_dict()
    max_r = max(rates.values()) if rates else 0
    di    = {str(g): round(v / max_r, 4) if max_r else 1.0 for g, v in rates.items()}
    flagged = [g for g, r in di.items() if r < DISPARATE_IMPACT_RATIO]

    # Score gap in interview_score across groups (if column exists)
    score_gap = None
    if "interview_score" in mgr_df.columns:
        grp_scores = mgr_df.groupby(attr)["interview_score"].mean()
        score_gap  = round(grp_scores.max() - grp_scores.min(), 2)

    return {
        "attribute":        attr,
        "selection_rates":  {str(k): v for k, v in rates.items()},
        "disparate_impact": di,
        "flagged_groups":   flagged,
        "interview_score_gap": score_gap,
    }


def _profile_manager(mgr_id, mgr_df: pd.DataFrame) -> dict:
    biased_attrs = []
    attr_results = {}
    for attr in PROTECTED_ATTRS:
        if attr in mgr_df.columns:
            res = _manager_attribute_bias(mgr_df, attr)
            attr_results[attr] = res
            if res.get("flagged_groups"):
                biased_attrs.append(attr)

    bias_score = max(0, 100 - len(biased_attrs) * 20)   # simple penalty per flagged attr

    return {
        "manager_id":    str(mgr_id),
        "total_reviewed": len(mgr_df),
        "selection_rate": round(mgr_df["selected"].mean(), 4),
        "bias_score":    bias_score,
        "biased_attrs":  biased_attrs,
        "attr_details":  attr_results,
    }


# ── Org-level consistency test ────────────────────────────────────────────────

def _org_level_chi2(df: pd.DataFrame, attr: str):
    """Do selection outcomes differ by (manager × protected group) combination?"""
    if attr not in df.columns:
        return None, None
    ct = pd.crosstab(df["manager_id"], df[attr])
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        return None, None
    chi2, p, _, _ = stats.chi2_contingency(ct)
    return round(chi2, 3), round(p, 5)


# ── Module entry point ────────────────────────────────────────────────────────

def run_manager_analysis(df: pd.DataFrame) -> dict:
    required = {"manager_id", "selected"}
    missing  = required - set(df.columns)
    if missing:
        return {"module": "manager", "score": None,
                "error": f"Missing columns: {missing}"}

    manager_profiles = []
    for mgr_id, mgr_df in df.groupby("manager_id"):
        if len(mgr_df) >= 5:          # need at least 5 reviews to assess
            manager_profiles.append(_profile_manager(mgr_id, mgr_df))

    if not manager_profiles:
        return {"module": "manager", "score": 100,
                "note": "Not enough data per manager (need ≥5 reviews each)"}

    # Org-level tests
    org_tests = {}
    for attr in PROTECTED_ATTRS:
        chi2, p = _org_level_chi2(df, attr)
        org_tests[attr] = {"chi2": chi2, "p_value": p,
                           "significant": p < STAT_SIG_PVALUE if p is not None else False}

    # Flag managers with bias_score < 60 as outliers
    flagged_managers = [m for m in manager_profiles if m["bias_score"] < 60]
    avg_score = round(np.mean([m["bias_score"] for m in manager_profiles]), 1)

    # Module score
    penalty = 0.0
    for attr, t in org_tests.items():
        if t["significant"]:
            penalty += 15
    penalty += len(flagged_managers) / max(len(manager_profiles), 1) * 40
    score = round(max(0, 100 - penalty), 1)

    return {
        "module":            "manager",
        "score":             score,
        "total_managers":    len(manager_profiles),
        "flagged_managers":  len(flagged_managers),
        "avg_manager_bias_score": avg_score,
        "manager_profiles":  manager_profiles,
        "org_level_tests":   org_tests,
        "flagged_details":   flagged_managers,
    }
