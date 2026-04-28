"""
app/utils/gemini.py  —  Gemini LLM integration
Uses the official google-genai SDK (>=1.0.0).

Quota/rate-limit strategy:
  Tries models in priority order until one succeeds.
  Free tier limits vary per model — having fallbacks means
  one exhausted quota does not kill the whole audit.
"""
import time
from app.config import GEMINI_API_KEY

# ── Model fallback chain ──────────────────────────────────────────────────────
# Tried in order. If one hits 429/quota, the next is tried automatically.
# All of these work with a free API key from https://aistudio.google.com/app/apikey
MODEL_FALLBACK_CHAIN = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.0-flash-lite",   # fastest, lowest quota usage — try first
    "gemini-2.0-flash",        # standard flash
    "gemini-1.5-flash",        # older but separate quota pool
    "gemini-1.5-flash-8b",     # lightest 1.5 model, separate limits
]


def _try_model(client, model: str, prompt: str) -> str:
    """Attempt a single model call. Raises on any error."""
    from google.genai import types
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.35,
            top_p=0.9,
            max_output_tokens=2200,
        ),
    )
    if not response.candidates:
        raise ValueError("No candidates returned (possible safety filter)")
    text = response.text
    if not text or not text.strip():
        raise ValueError("Empty response returned")
    return text.strip()


def call_gemini(prompt: str, api_key: str = "") -> str:
    key = (api_key or GEMINI_API_KEY or "").strip()

    if not key or key == "YOUR_GEMINI_API_KEY":
        return (
            "AI Summary Unavailable — No API key provided.\n\n"
            "To enable AI-generated insights:\n"
            "  1. Get a free key at https://aistudio.google.com/app/apikey\n"
            "  2. Open app/config.py and set:  GEMINI_API_KEY = 'AIza...'\n"
            "  3. Restart the server.\n\n"
            "The statistical analysis in this report is complete and valid without AI narrative."
        )

    try:
        from google import genai
        client = genai.Client(api_key=key)
    except Exception as e:
        return f"Gemini SDK initialisation failed: {e}"

    errors = []
    for model in MODEL_FALLBACK_CHAIN:
        try:
            result = _try_model(client, model, prompt)
            return f"[Model: {model}]\n\n{result}"
        except Exception as e:
            err = str(e)
            # 429 / quota exhausted — try next model
            if any(x in err for x in ["429", "RESOURCE_EXHAUSTED", "quota"]):
                errors.append(f"{model}: quota exhausted")
                time.sleep(1)   # brief pause before next attempt
                continue
            # Auth error — no point trying other models
            if any(x in err for x in ["401", "403", "API_KEY_INVALID", "invalid api key"]):
                return (
                    "Gemini Authentication Failed\n\n"
                    "The API key is invalid or revoked.\n"
                    "Check your key at https://aistudio.google.com/app/apikey"
                )
            # Any other error on this model — try next
            errors.append(f"{model}: {err[:120]}")
            continue

    # All models failed
    error_summary = "\n".join(f"  • {e}" for e in errors)
    return (
        "Gemini Quota Exhausted Across All Models\n\n"
        f"All {len(MODEL_FALLBACK_CHAIN)} models hit their rate limits:\n"
        f"{error_summary}\n\n"
        "Options:\n"
        "  1. Wait a few minutes and retry — free tier resets per minute/day\n"
        "  2. Enable billing on your Google Cloud project for higher quotas\n"
        "     https://console.cloud.google.com/billing\n\n"
        "The statistical analysis in this report is complete and valid without AI narrative."
    )


def build_full_prompt(
    overall_score: float,
    module_scores: dict,
    hiring_result:  dict = None,
    ml_result:      dict = None,
    manager_result: dict = None,
    leave_result:   dict = None,
) -> str:
    score_lines = []
    labels = {
        "hiring":     "Hiring Bias",
        "ml_model":   "ML Model Bias",
        "manager":    "Manager Fairness",
        "leave_task": "Leave & Task Fairness",
    }
    for key, label in labels.items():
        val = module_scores.get(key)
        score_lines.append(
            f"  - {label}: {val}/100" if val is not None else f"  - {label}: NOT RUN"
        )

    evidence_lines = []

    if hiring_result:
        s = hiring_result.get("summary", {})
        evidence_lines.append(
            f"Hiring: {s.get('total','?')} candidates, "
            f"selection rate {s.get('selection_rate','?')}, "
            f"avg CGPA {s.get('avg_cgpa','?')}."
        )
        for a in hiring_result.get("analyses", []):
            if a.get("flagged_groups"):
                evidence_lines.append(
                    f"  - {a['attribute'].upper()}: adverse impact on "
                    f"{', '.join(str(f) for f in a['flagged_groups'])} "
                    f"(p={a.get('p_value')}, significant={a.get('significant')})"
                )

    if ml_result:
        evidence_lines.append(
            f"ML Model: overall accuracy {ml_result.get('overall_accuracy','?')}."
        )
        for a in ml_result.get("analyses", []):
            if a.get("flagged_groups"):
                evidence_lines.append(
                    f"  - {a['attribute'].upper()}: DI violation for "
                    f"{', '.join(str(f) for f in a['flagged_groups'])}, "
                    f"equalised-odds gap={a.get('equalised_odds_gap')}"
                )

    if manager_result:
        evidence_lines.append(
            f"Manager: {manager_result.get('total_managers','?')} managers, "
            f"{manager_result.get('flagged_managers','?')} flagged."
        )
        for m in (manager_result.get("flagged_details") or [])[:3]:
            evidence_lines.append(
                f"  - Manager {m.get('manager_id')} biased on: "
                f"{', '.join(m.get('biased_attrs', []))}"
            )

    if leave_result:
        for sub_key, label in [("leave", "Leave"), ("task", "Task")]:
            sub = leave_result.get(sub_key, {})
            for a in sub.get("analyses", []):
                if a.get("flagged_groups"):
                    evidence_lines.append(
                        f"  - {label}/{a.get('attribute','').upper()}: "
                        f"adverse impact on "
                        f"{', '.join(str(f) for f in a['flagged_groups'])}"
                    )

    evidence_block = (
        "\n".join(evidence_lines) if evidence_lines
        else "  (No detailed evidence available)"
    )

    return f"""You are an expert in algorithmic fairness and HR bias auditing for Indian organisations.

A company ran FairLens bias analysis across multiple HR modules.

OVERALL FAIRNESS SCORE: {overall_score}/100
SCORING GUIDE: 75-100 = LOW BIAS | 50-74 = MODERATE BIAS | 0-49 = HIGH BIAS

MODULE SCORES:
{chr(10).join(score_lines)}

KEY EVIDENCE FROM THE DATA:
{evidence_block}

Provide a concise report with exactly these five sections:

1. EXECUTIVE SUMMARY (3-4 sentences): Overall fairness posture of this organisation.
2. CRITICAL FINDINGS: The 3-5 most urgent bias signals. Reference specific attributes and groups.
3. ROOT CAUSES: Likely systemic causes specific to the Indian HR context.
4. PRIORITY ACTIONS: 4-6 concrete ranked fixes for HR teams and data scientists.
5. MONITORING DASHBOARD: 5 specific metrics to track monthly (include target thresholds).

Keep the full response under 650 words, use short paragraphs or bullets where helpful, and make sure every section is fully completed.
Be direct, evidence-based, and constructive. Do not repeat the input data back.
"""
