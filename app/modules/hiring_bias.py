"""
app/modules/hiring_bias.py
Bias analysis for resume / hiring datasets.
"""
import numpy as np
import pandas as pd
from scipy import stats
from app.config import (
    DISPARATE_IMPACT_RATIO, HIRING_ATTR_WEIGHTS,
    MIN_CGPA, MIN_EDUCATION_LEVEL, MIN_SKILLS_SCORE, STAT_SIG_PVALUE,
)


# ── Merit computation ─────────────────────────────────────────────────────────

def compute_skills_score(df: pd.DataFrame) -> pd.Series:
    """
    Merit-only score (0–100):
        40% normalised CGPA  +  35% normalised experience  +  25% normalised education
    No demographic columns involved.
    """
    cgpa_norm = (df["cgpa"].clip(0, 10) - 4.0) / 6.0
    exp_norm  = df["years_experience"].clip(0, 15) / 15.0
    edu_norm  = df["education_level"].clip(0, 3) / 3.0
    return ((0.40 * cgpa_norm + 0.35 * exp_norm + 0.25 * edu_norm) * 100).clip(0, 100).round(1)


def compute_is_qualified(df: pd.DataFrame) -> pd.Series:
    """
    Binary flag: 1 if candidate clears ALL merit thresholds.
    Gender / caste / location / college_tier are intentionally excluded.
    """
    return (
        (df["skills_score"]    >= MIN_SKILLS_SCORE) &
        (df["education_level"] >= MIN_EDUCATION_LEVEL) &
        (df["cgpa"]            >= MIN_CGPA)
    ).astype(int)


# ── Statistical tests ─────────────────────────────────────────────────────────

def _selection_rates(df: pd.DataFrame, col: str) -> pd.DataFrame:
    g = df.groupby(col)["selected"].agg(["sum", "count"]).reset_index()
    g.columns = [col, "selected", "total"]
    g["rate"] = (g["selected"] / g["total"]).round(4)
    return g


def _chi_square(df: pd.DataFrame, col: str):
    ct = pd.crosstab(df[col], df["selected"])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    return round(chi2, 3), round(p, 5), dof


def _disparate_impact(rates_df: pd.DataFrame, col: str) -> dict:
    max_rate = rates_df["rate"].max()
    if max_rate == 0:
        return {}
    return {
        str(row[col]): round(row["rate"] / max_rate, 4)
        for _, row in rates_df.iterrows()
    }


def _qualified_rejection(df: pd.DataFrame, col: str) -> pd.DataFrame:
    q = df[df["is_qualified"] == 1]
    if q.empty:
        return pd.DataFrame()
    g = q.groupby(col)["selected"].agg(["sum", "count"]).reset_index()
    g.columns = [col, "selected", "qualified"]
    g["rejected"]       = g["qualified"] - g["selected"]
    g["rejection_rate"] = (g["rejected"] / g["qualified"]).round(4)
    return g


def analyse_attribute(df: pd.DataFrame, attr: str) -> dict:
    rates        = _selection_rates(df, attr)
    chi2, p, dof = _chi_square(df, attr)
    di           = _disparate_impact(rates, attr)
    qbr          = _qualified_rejection(df, attr)
    flagged      = [g for g, r in di.items() if r < DISPARATE_IMPACT_RATIO]
    return {
        "attribute":           attr,
        "selection_rates":     rates,
        "chi2":                chi2,
        "p_value":             p,
        "dof":                 dof,
        "significant":         p < STAT_SIG_PVALUE,
        "disparate_impact":    di,
        "flagged_groups":      flagged,
        "qualified_rejection": qbr,
    }


# ── Module entry point ────────────────────────────────────────────────────────

PROTECTED_ATTRS = list(HIRING_ATTR_WEIGHTS.keys())


def run_hiring_analysis(df: pd.DataFrame) -> dict:
    # Ensure derived columns exist
    if "skills_score" not in df.columns:
        df["skills_score"] = compute_skills_score(df)
    if "is_qualified" not in df.columns:
        df["is_qualified"] = compute_is_qualified(df)

    analyses = [analyse_attribute(df, a) for a in PROTECTED_ATTRS if a in df.columns]

    # Score
    total_weight  = sum(HIRING_ATTR_WEIGHTS.values())
    total_penalty = 0.0
    breakdown     = {}
    for a in analyses:
        attr   = a["attribute"]
        weight = HIRING_ATTR_WEIGHTS.get(attr, 10)
        penalty = 0.0
        if a["significant"]:
            penalty += 0.30 * weight
        for _, ratio in a["disparate_impact"].items():
            if ratio < DISPARATE_IMPACT_RATIO:
                penalty += (1 - ratio) * 0.50 * weight
        qbr = a["qualified_rejection"]
        if not qbr.empty and "rejection_rate" in qbr.columns:
            if qbr["rejection_rate"].max() - qbr["rejection_rate"].min() > 0.20:
                penalty += 0.20 * weight
        penalty = min(penalty, weight)
        total_penalty += penalty
        breakdown[attr] = {"weight": weight, "penalty": round(penalty, 2),
                           "score": round(weight - penalty, 2)}

    raw   = max(0, total_weight - total_penalty)
    score = round((raw / total_weight) * 100, 1)

    return {
        "module":    "hiring",
        "score":     score,
        "breakdown": breakdown,
        "analyses":  analyses,
        "summary": {
            "total":         len(df),
            "selected":      int(df["selected"].sum()),
            "qualified":     int(df["is_qualified"].sum()),
            "selection_rate": round(df["selected"].mean(), 4),
            "avg_skills":    round(df["skills_score"].mean(), 2),
            "avg_cgpa":      round(df["cgpa"].mean(), 2),
        },
    }
