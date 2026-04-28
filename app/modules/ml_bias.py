"""
app/modules/ml_bias.py

Detects bias in ML model predictions.

Expected CSV columns:
    candidate_id, gender, caste, location, college_tier, education_level,
    actual_label, predicted_label, predicted_probability  (0.0–1.0)

actual_label     : ground truth (1=should hire, 0=should not)
predicted_label  : model's binary decision (1/0)
predicted_probability : model confidence score
"""
import numpy as np
import pandas as pd
from scipy import stats
from app.config import DISPARATE_IMPACT_RATIO, STAT_SIG_PVALUE

PROTECTED_ATTRS = ["gender", "caste", "location", "college_tier", "education_level"]


def _group_metrics(df: pd.DataFrame, col: str) -> pd.DataFrame:
    rows = []
    for grp, g in df.groupby(col):
        tp = ((g["predicted_label"] == 1) & (g["actual_label"] == 1)).sum()
        fp = ((g["predicted_label"] == 1) & (g["actual_label"] == 0)).sum()
        tn = ((g["predicted_label"] == 0) & (g["actual_label"] == 0)).sum()
        fn = ((g["predicted_label"] == 0) & (g["actual_label"] == 1)).sum()

        precision   = tp / (tp + fp)   if (tp + fp)   > 0 else 0.0
        recall      = tp / (tp + fn)   if (tp + fn)   > 0 else 0.0
        fpr         = fp / (fp + tn)   if (fp + tn)   > 0 else 0.0
        fnr         = fn / (fn + tp)   if (fn + tp)   > 0 else 0.0
        accuracy    = (tp + tn) / len(g) if len(g)    > 0 else 0.0
        pred_rate   = g["predicted_label"].mean()

        rows.append({
            col:         str(grp),
            "n":         len(g),
            "pred_positive_rate": round(pred_rate, 4),
            "precision": round(precision, 4),
            "recall":    round(recall, 4),
            "fpr":       round(fpr, 4),
            "fnr":       round(fnr, 4),
            "accuracy":  round(accuracy, 4),
        })
    return pd.DataFrame(rows)


def _disparate_impact(metrics: pd.DataFrame, col: str) -> dict:
    max_rate = metrics["pred_positive_rate"].max()
    if max_rate == 0:
        return {}
    return {
        row[col]: round(row["pred_positive_rate"] / max_rate, 4)
        for _, row in metrics.iterrows()
    }


def _equalised_odds_gap(metrics: pd.DataFrame) -> float:
    """Max difference in FPR or FNR across groups — equalized odds metric."""
    fpr_gap = metrics["fpr"].max() - metrics["fpr"].min()
    fnr_gap = metrics["fnr"].max() - metrics["fnr"].min()
    return round(max(fpr_gap, fnr_gap), 4)


def analyse_ml_attribute(df: pd.DataFrame, attr: str) -> dict:
    metrics = _group_metrics(df, attr)
    di      = _disparate_impact(metrics, attr)
    flagged = [g for g, r in di.items() if r < DISPARATE_IMPACT_RATIO]
    eq_gap  = _equalised_odds_gap(metrics)

    # Chi-square on predicted label vs group
    ct = pd.crosstab(df[attr], df["predicted_label"])
    chi2, p, dof, _ = stats.chi2_contingency(ct) if ct.shape[1] > 1 else (0, 1, 0, None)

    return {
        "attribute":        attr,
        "group_metrics":    metrics,
        "disparate_impact": di,
        "flagged_groups":   flagged,
        "equalised_odds_gap": eq_gap,
        "chi2":             round(chi2, 3),
        "p_value":          round(p, 5),
        "significant":      p < STAT_SIG_PVALUE,
    }


def run_ml_analysis(df: pd.DataFrame) -> dict:
    required = {"actual_label", "predicted_label"}
    missing  = required - set(df.columns)
    if missing:
        return {"module": "ml_model", "score": None,
                "error": f"Missing columns: {missing}"}

    if "predicted_probability" not in df.columns:
        df["predicted_probability"] = df["predicted_label"].astype(float)

    # Overall model accuracy
    overall_acc = (df["predicted_label"] == df["actual_label"]).mean()

    analyses = [analyse_ml_attribute(df, a) for a in PROTECTED_ATTRS if a in df.columns]

    # Score: penalise for DI violations + equalised-odds gaps + significance
    total_w   = len(analyses) * 20
    penalty   = 0.0
    breakdown = {}
    for a in analyses:
        w    = 20
        pen  = 0.0
        if a["significant"]:
            pen += 0.30 * w
        for _, ratio in a["disparate_impact"].items():
            if ratio < DISPARATE_IMPACT_RATIO:
                pen += (1 - ratio) * 0.50 * w
        if a["equalised_odds_gap"] > 0.15:
            pen += 0.20 * w
        pen = min(pen, w)
        penalty += pen
        breakdown[a["attribute"]] = {
            "weight": w, "penalty": round(pen, 2),
            "score":  round(w - pen, 2)
        }

    score = round(max(0, (total_w - penalty) / total_w * 100), 1) if total_w else 100.0

    return {
        "module":          "ml_model",
        "score":           score,
        "breakdown":       breakdown,
        "analyses":        analyses,
        "overall_accuracy": round(overall_acc, 4),
    }
