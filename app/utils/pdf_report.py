"""
app/utils/pdf_report.py  —  FairLens multi-module PDF report generator
"""
import textwrap
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#0D1B2A")
BLUE   = colors.HexColor("#1B4F72")
ACCENT = colors.HexColor("#2E86C1")
GREEN  = colors.HexColor("#1E8449")
AMBER  = colors.HexColor("#D4AC0D")
RED    = colors.HexColor("#C0392B")
LGRAY  = colors.HexColor("#F2F3F4")
MGRAY  = colors.HexColor("#BFC9CA")
WHITE  = colors.white

W, H = A4


# ── Style helpers ─────────────────────────────────────────────────────────────
def _styles():
    S = {}
    S["title"]    = ParagraphStyle("title",    fontName="Helvetica-Bold",   fontSize=20, textColor=WHITE,  alignment=TA_CENTER, spaceAfter=4)
    S["subtitle"] = ParagraphStyle("subtitle", fontName="Helvetica",        fontSize=10, textColor=MGRAY,  alignment=TA_CENTER)
    S["h1"]       = ParagraphStyle("h1",       fontName="Helvetica-Bold",   fontSize=13, textColor=NAVY,   spaceBefore=12, spaceAfter=5)
    S["h2"]       = ParagraphStyle("h2",       fontName="Helvetica-Bold",   fontSize=11, textColor=BLUE,   spaceBefore=8,  spaceAfter=4)
    S["body"]     = ParagraphStyle("body",     fontName="Helvetica",        fontSize=9.5,textColor=colors.black, leading=14, spaceAfter=5)
    S["small"]    = ParagraphStyle("small",    fontName="Helvetica",        fontSize=8,  textColor=BLUE,   leading=12)
    S["bullet"]   = ParagraphStyle("bullet",   fontName="Helvetica",        fontSize=9.5,textColor=colors.black, leading=13, leftIndent=14, spaceAfter=3)
    S["th"]       = ParagraphStyle("th",       fontName="Helvetica-Bold",   fontSize=8.5,textColor=WHITE,  alignment=TA_CENTER)
    S["td"]       = ParagraphStyle("td",       fontName="Helvetica",        fontSize=8.5,textColor=colors.black, alignment=TA_CENTER)
    S["tdl"]      = ParagraphStyle("tdl",      fontName="Helvetica",        fontSize=8.5,textColor=colors.black, alignment=TA_LEFT)
    S["flag"]     = ParagraphStyle("flag",     fontName="Helvetica-Bold",   fontSize=9,  textColor=RED)
    S["ok"]       = ParagraphStyle("ok",       fontName="Helvetica-Bold",   fontSize=9,  textColor=GREEN)
    S["disc"]     = ParagraphStyle("disc",     fontName="Helvetica-Oblique",fontSize=7.5,textColor=MGRAY,  alignment=TA_CENTER)
    return S


def _hr(story):
    story.append(HRFlowable(width="100%", thickness=1, color=MGRAY, spaceAfter=5, spaceBefore=2))


def _section(story, text, S):
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"▌ {text}", S["h1"]))
    _hr(story)


def _wrap(text, key, S, w=80):
    return Paragraph("<br/>".join(textwrap.wrap(str(text), w)), S[key])


def _score_color(s):
    if s is None: return MGRAY
    return GREEN if s >= 75 else (AMBER if s >= 50 else RED)


def _score_label(s):
    if s is None: return "N/A"
    return "LOW BIAS" if s >= 75 else ("MODERATE BIAS" if s >= 50 else "HIGH BIAS")


def _tbl(data, col_widths, hdr_bg=NAVY):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1,  0), hdr_bg),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LGRAY]),
        ("GRID",          (0, 0), (-1, -1), 0.4, MGRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
    ]))
    return t


def _gemini_blocks(text: str, S: dict) -> list:
    items = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            items.append(Spacer(1, 3))
        elif line.startswith(("##", "**")) or (line.endswith(":") and len(line) < 60):
            clean = line.lstrip("#").replace("**", "").strip()
            items.append(Paragraph(f"<b>{clean}</b>", S["body"]))
        elif line.startswith(("- ", "• ", "* ")):
            items.append(Paragraph("• " + line.lstrip("-•* ").replace("**",""), S["bullet"]))
        else:
            items.append(Paragraph(line.replace("**",""), S["body"]))
    return items


# ── Cover & score dashboard ───────────────────────────────────────────────────

def _cover(story, S, overall_score, module_scores, meta):
    # Banner
    bt = Table([[Paragraph("FairLens — HR Bias Audit Report", S["title"])]],
               colWidths=[W - 3.6*cm])
    bt.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), NAVY),
        ("TOPPADDING", (0,0),(-1,-1), 20),
        ("BOTTOMPADDING",(0,0),(-1,-1), 20),
    ]))
    story.append(bt)
    story.append(Spacer(1, 6))

    # Meta row
    mt = Table([[
        _wrap(f"Dataset: {meta.get('dataset','—')}", "body", S),
        _wrap(f"Generated: {datetime.now().strftime('%d %b %Y  %H:%M')}", "body", S),
        _wrap(f"Candidates: {meta.get('total','—')}", "body", S),
    ]], colWidths=[(W-3.6*cm)/3]*3)
    mt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), LGRAY),
        ("TOPPADDING",(0,0),(-1,-1), 6), ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
    ]))
    story.append(mt)
    story.append(Spacer(1, 14))

    # Big score
    sc = overall_score or 0
    clr = _score_color(sc)
    story.append(Table([[
        Paragraph(f"<font size=52><b>{sc:.0f}</b></font>",
                  ParagraphStyle("big", fontName="Helvetica-Bold", fontSize=52,
                                 textColor=clr, alignment=TA_CENTER)),
        Paragraph(
            f"<font size=14><b>/ 100</b></font><br/>"
            f"<font size=11>Overall Fairness Score</font><br/><br/>"
            f"<font color='#{clr.hexval()[2:]}' size=12><b>{_score_label(sc)}</b></font>",
            ParagraphStyle("sl", fontName="Helvetica", fontSize=11, textColor=NAVY,
                           alignment=TA_LEFT, leading=20)),
    ]], colWidths=[7*cm, 9*cm], style=TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("BACKGROUND",(0,0),(-1,-1),LGRAY),
        ("TOPPADDING",(0,0),(-1,-1),18),("BOTTOMPADDING",(0,0),(-1,-1),18),
        ("LEFTPADDING",(0,0),(0,0),30),
    ])))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "<font color='#C0392B'><b>0–49 HIGH BIAS</b></font> &nbsp;│&nbsp; "
        "<font color='#D4AC0D'><b>50–74 MODERATE BIAS</b></font> &nbsp;│&nbsp; "
        "<font color='#1E8449'><b>75–100 LOW BIAS</b></font>",
        ParagraphStyle("sg", fontName="Helvetica", fontSize=9, textColor=BLUE,
                       alignment=TA_CENTER, spaceAfter=10)))

    # Module score cards
    _section(story, "Module Scores at a Glance", S)
    MODULE_LABELS = {
        "hiring":    "Hiring Bias",
        "ml_model":  "ML Model Bias",
        "manager":   "Manager Fairness",
        "leave_task":"Leave / Task Fairness",
    }
    card_data = [[Paragraph("Module", S["th"]),
                  Paragraph("Score", S["th"]),
                  Paragraph("Status", S["th"]),
                  Paragraph("Weight in Overall", S["th"])]]
    WEIGHTS = {"hiring":40,"ml_model":20,"manager":20,"leave_task":20}
    for mod, score in module_scores.items():
        clr2 = _score_color(score)
        lbl  = _score_label(score) if score is not None else "Not provided"
        card_data.append([
            _wrap(MODULE_LABELS.get(mod, mod), "tdl", S),
            Paragraph(f"<b>{score:.0f}</b>" if score is not None else "—",
                      ParagraphStyle("ms", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=clr2, alignment=TA_CENTER)),
            Paragraph(lbl, ParagraphStyle("ml", fontName="Helvetica-Bold", fontSize=8.5,
                                          textColor=clr2, alignment=TA_CENTER)),
            Paragraph(f"{WEIGHTS.get(mod,0)}%", S["td"]),
        ])
    story.append(_tbl(card_data, [6*cm, 3*cm, 5*cm, 3.5*cm]))


# ── Hiring module section ─────────────────────────────────────────────────────

def _hiring_section(story, S, result):
    story.append(PageBreak())
    _section(story, "Module 1 — Hiring Bias Analysis", S)

    if result.get("error"):
        story.append(Paragraph(f"Error: {result['error']}", S["body"]))
        return

    summ = result.get("summary", {})
    story.append(_tbl([
        [Paragraph("Metric", S["th"]), Paragraph("Value", S["th"])],
        [_wrap("Total Candidates","tdl",S), Paragraph(str(summ.get("total","—")),S["td"])],
        [_wrap("Selected","tdl",S),         Paragraph(f"{summ.get('selected','—')} ({summ.get('selection_rate',0):.1%})",S["td"])],
        [_wrap("Qualified (merit)","tdl",S),Paragraph(str(summ.get("qualified","—")),S["td"])],
        [_wrap("Avg Skills Score","tdl",S), Paragraph(f"{summ.get('avg_skills','—')}/100",S["td"])],
        [_wrap("Avg CGPA","tdl",S),         Paragraph(str(summ.get("avg_cgpa","—")),S["td"])],
    ], [9*cm, 7*cm]))
    story.append(Spacer(1,8))

    # Score breakdown
    story.append(Paragraph("Attribute Score Breakdown", S["h2"]))
    bd = result.get("breakdown", {})
    bk_data = [[Paragraph(h,S["th"]) for h in ["Attribute","Max Weight","Penalty","Score","Status"]]]
    for attr, v in bd.items():
        pct = v["score"]/v["weight"]*100 if v["weight"] else 0
        st  = ("✓ FAIR" if pct>=75 else ("⚠ MODERATE" if pct>=50 else "✗ BIASED"))
        sc  = S["ok"] if pct>=75 else (ParagraphStyle("am",fontName="Helvetica-Bold",fontSize=9,textColor=AMBER) if pct>=50 else S["flag"])
        bk_data.append([
            _wrap(attr.replace("_"," ").title(),"tdl",S),
            Paragraph(str(v["weight"]),S["td"]),
            Paragraph(f"-{v['penalty']:.1f}",S["td"]),
            Paragraph(f"{v['score']:.1f}",S["td"]),
            Paragraph(st, sc),
        ])
    story.append(_tbl(bk_data,[5*cm,3*cm,3*cm,3.5*cm,3*cm]))
    story.append(Spacer(1,8))

    # Per attribute tables
    story.append(Paragraph("Per-Attribute Statistical Detail", S["h2"]))
    for a in result.get("analyses", []):
        attr   = a["attribute"]
        sig    = a["significant"]
        flagged = a["flagged_groups"]
        badge  = Paragraph("⚠ BIAS DETECTED" if (sig or flagged) else "✓ No significant bias",
                           S["flag"] if (sig or flagged) else S["ok"])
        ht = Table([[_wrap(attr.replace("_"," ").title(),"body",S), badge]],
                   colWidths=[12*cm,4.5*cm])
        ht.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),LGRAY),("TOPPADDING",(0,0),(-1,-1),5),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),8),
        ]))
        story.append(ht)
        story.append(Paragraph(
            f"χ²={a['chi2']}  p={a['p_value']:.5f}  df={a['dof']}",
            ParagraphStyle("st",fontName="Helvetica",fontSize=8.5,textColor=BLUE,
                           spaceBefore=3,spaceAfter=5)))

        rates = a["selection_rates"]
        di_map = a["disparate_impact"]
        rd = [[Paragraph(h,S["th"]) for h in ["Group","Total","Selected","Rate","Disp. Impact"]]]
        for _, row in rates.iterrows():
            grp = str(row[attr])
            di  = di_map.get(grp, 1.0)
            dic = RED if di<0.80 else (AMBER if di<0.90 else GREEN)
            rd.append([
                _wrap(grp,"tdl",S),
                Paragraph(str(int(row["total"])),S["td"]),
                Paragraph(str(int(row["selected"])),S["td"]),
                Paragraph(f"{row['rate']:.1%}",S["td"]),
                Paragraph(f"{di:.3f}", ParagraphStyle("di",fontName="Helvetica-Bold",
                          fontSize=8.5,textColor=dic,alignment=TA_CENTER)),
            ])
        story.append(_tbl(rd,[4*cm,2.5*cm,2.5*cm,3.5*cm,4*cm], hdr_bg=ACCENT))

        if flagged:
            story.append(Paragraph(
                f"⚠ Adverse impact groups (DI &lt; 0.80): "
                f"<font color='#C0392B'><b>{', '.join(str(f) for f in flagged)}</b></font>",
                ParagraphStyle("fi",fontName="Helvetica",fontSize=8.5,
                               textColor=RED,spaceBefore=3,spaceAfter=6)))
        story.append(Spacer(1,8))


# ── ML model section ──────────────────────────────────────────────────────────

def _ml_section(story, S, result):
    story.append(PageBreak())
    _section(story, "Module 2 — ML Model Bias Analysis", S)

    if result is None:
        story.append(Paragraph("No ML predictions CSV provided — module skipped.", S["body"]))
        return
    if result.get("error"):
        story.append(Paragraph(f"Error: {result['error']}", S["body"]))
        return

    story.append(Paragraph(
        f"Overall model accuracy: <b>{result.get('overall_accuracy',0):.1%}</b>  │  "
        f"Fairness score: <b>{result.get('score','—')}/100</b>", S["body"]))
    story.append(Spacer(1,6))

    for a in result.get("analyses", []):
        attr = a["attribute"]
        story.append(Paragraph(attr.replace("_"," ").title(), S["h2"]))
        story.append(Paragraph(
            f"χ²={a['chi2']}  p={a['p_value']:.5f}  "
            f"Equalised-Odds Gap={a['equalised_odds_gap']:.3f}",
            ParagraphStyle("st2",fontName="Helvetica",fontSize=8.5,textColor=BLUE,spaceAfter=5)))

        gm = a["group_metrics"]
        di_map = a["disparate_impact"]
        hdr = [Paragraph(h,S["th"]) for h in
               ["Group","N","Pred+Rate","Precision","Recall","FPR","FNR","DI Ratio"]]
        rows = [hdr]
        for _, row in gm.iterrows():
            grp = str(row[attr])
            di  = di_map.get(grp, 1.0)
            dic = RED if di<0.80 else (AMBER if di<0.90 else GREEN)
            rows.append([
                _wrap(grp,"tdl",S),
                Paragraph(str(int(row["n"])),S["td"]),
                Paragraph(f"{row['pred_positive_rate']:.1%}",S["td"]),
                Paragraph(f"{row['precision']:.1%}",S["td"]),
                Paragraph(f"{row['recall']:.1%}",S["td"]),
                Paragraph(f"{row['fpr']:.1%}",S["td"]),
                Paragraph(f"{row['fnr']:.1%}",S["td"]),
                Paragraph(f"{di:.3f}",ParagraphStyle("di2",fontName="Helvetica-Bold",
                          fontSize=8.5,textColor=dic,alignment=TA_CENTER)),
            ])
        story.append(_tbl(rows,[3.5*cm,1.2*cm,2*cm,2*cm,2*cm,1.8*cm,1.8*cm,2.2*cm],ACCENT))
        story.append(Spacer(1,8))


# ── Manager fairness section ──────────────────────────────────────────────────

def _manager_section(story, S, result):
    story.append(PageBreak())
    _section(story, "Module 3 — Manager Fairness Analysis", S)

    if result is None:
        story.append(Paragraph("No manager data provided — module skipped.", S["body"]))
        return
    if result.get("error"):
        story.append(Paragraph(f"Error: {result['error']}", S["body"]))
        return
    if result.get("note"):
        story.append(Paragraph(result["note"], S["body"]))
        return

    story.append(Paragraph(
        f"Total managers analysed: <b>{result.get('total_managers','—')}</b>  │  "
        f"Flagged managers: <b>{result.get('flagged_managers','—')}</b>  │  "
        f"Avg manager bias score: <b>{result.get('avg_manager_bias_score','—')}/100</b>",
        S["body"]))
    story.append(Spacer(1,6))

    # Org-level tests
    story.append(Paragraph("Organisation-Level Consistency Tests", S["h2"]))
    org = result.get("org_level_tests", {})
    ot_data = [[Paragraph(h,S["th"]) for h in ["Attribute","Chi²","p-value","Significant?"]]]
    for attr, t in org.items():
        sig = t.get("significant", False)
        ot_data.append([
            _wrap(attr.replace("_"," ").title(),"tdl",S),
            Paragraph(str(t.get("chi2","—")),S["td"]),
            Paragraph(str(t.get("p_value","—")),S["td"]),
            Paragraph("YES ⚠",S["flag"]) if sig else Paragraph("No ✓",S["ok"]),
        ])
    story.append(_tbl(ot_data,[6*cm,3*cm,3*cm,4*cm]))
    story.append(Spacer(1,8))

    # Flagged managers table
    flagged = result.get("flagged_details", [])
    if flagged:
        story.append(Paragraph(f"Flagged Managers (Bias Score &lt; 60) — {len(flagged)} found", S["h2"]))
        fm_data = [[Paragraph(h,S["th"]) for h in
                    ["Manager ID","Reviewed","Sel. Rate","Bias Score","Biased Attributes"]]]
        for m in flagged:
            fm_data.append([
                _wrap(m["manager_id"],"tdl",S),
                Paragraph(str(m["total_reviewed"]),S["td"]),
                Paragraph(f"{m['selection_rate']:.1%}",S["td"]),
                Paragraph(str(m["bias_score"]),
                          ParagraphStyle("bs",fontName="Helvetica-Bold",fontSize=9,
                                         textColor=RED,alignment=TA_CENTER)),
                _wrap(", ".join(m["biased_attrs"]) or "—","tdl",S),
            ])
        story.append(_tbl(fm_data,[4*cm,2.5*cm,3*cm,3*cm,5*cm]))


# ── Leave / task fairness section ─────────────────────────────────────────────

def _leave_task_section(story, S, result):
    story.append(PageBreak())
    _section(story, "Module 4 — Leave & Task Fairness Analysis", S)

    if result is None:
        story.append(Paragraph("No leave/task data provided — module skipped.", S["body"]))
        return

    for submod in ["leave", "task"]:
        sub = result.get(submod)
        if not sub:
            continue
        title = "Leave Approval Fairness" if submod == "leave" else "Task Assignment Fairness"
        story.append(Paragraph(title, S["h2"]))

        if sub.get("error"):
            story.append(Paragraph(f"Error: {sub['error']}", S["body"]))
            continue

        if submod == "leave":
            summ = sub.get("summary", {})
            story.append(Paragraph(
                f"Total requests: <b>{summ.get('total_requests','—')}</b>  │  "
                f"Overall approval rate: <b>{summ.get('overall_approval_rate',0):.1%}</b>",
                S["body"]))

        for a in sub.get("analyses", []):
            if not a:
                continue
            attr = a.get("attribute","")
            story.append(Paragraph(attr.replace("_"," ").title(),
                                   ParagraphStyle("subh",fontName="Helvetica-Bold",fontSize=9.5,
                                                  textColor=BLUE,spaceBefore=6,spaceAfter=3)))

            if submod == "leave" and "rates_table" in a:
                rt = a["rates_table"]
                cols = [c for c in ["approval_rate","fulfilment_ratio","avg_days_req","avg_days_appr"]
                        if c in rt.columns]
                hdr = [attr.replace("_"," ").title()] + [c.replace("_"," ").title() for c in cols]
                rows_data = [[Paragraph(h,S["th"]) for h in hdr]]
                di_map = a.get("disparate_impact", {})
                for _, row in rt.iterrows():
                    grp = str(row[attr])
                    di  = di_map.get(grp, 1.0)
                    dic = RED if di < 0.80 else GREEN
                    r   = [_wrap(grp,"tdl",S)]
                    for c in cols:
                        val = row[c]
                        if "rate" in c or "ratio" in c:
                            r.append(Paragraph(f"{val:.1%}",
                                               ParagraphStyle("cv",fontName="Helvetica-Bold",fontSize=8.5,
                                                              textColor=dic,alignment=TA_CENTER) if c=="approval_rate" else S["td"]))
                        else:
                            r.append(Paragraph(f"{val:.1f}",S["td"]))
                    rows_data.append(r)
                cw = [4*cm] + [3*cm]*len(cols)
                story.append(_tbl(rows_data, cw, ACCENT))

            flagged = a.get("flagged_groups", [])
            if flagged:
                story.append(Paragraph(
                    f"⚠ Adverse impact: <font color='#C0392B'><b>{', '.join(str(f) for f in flagged)}</b></font>",
                    ParagraphStyle("fi2",fontName="Helvetica",fontSize=8.5,textColor=RED,
                                   spaceBefore=3,spaceAfter=5)))
            story.append(Spacer(1,6))


# ── AI section ────────────────────────────────────────────────────────────────

def _ai_section(story, S, gemini_text):
    story.append(PageBreak())
    _section(story, "AI-Powered Analysis & Recommendations (Gemini)", S)
    story.append(Paragraph(
        "The following narrative was generated by Google Gemini based on all module results above.",
        S["body"]))
    story.append(Spacer(1,6))
    for item in _gemini_blocks(gemini_text, S):
        story.append(item)


# ── Methodology ───────────────────────────────────────────────────────────────

def _methodology(story, S):
    story.append(PageBreak())
    _section(story, "Methodology & Definitions", S)
    items = [
        ("Skills Score (0–100)",
         "40% normalised CGPA + 35% normalised experience (capped 15 yrs) + 25% normalised "
         "education level. No demographic columns used."),
        ("is_qualified",
         "1 if skills_score ≥ 50 AND education_level ≥ Bachelor AND CGPA ≥ 6.0. "
         "Demographic attributes explicitly excluded."),
        ("Disparate Impact Ratio",
         "EEOC 4/5ths rule: group selection rate ÷ highest group rate. Below 0.80 = adverse impact."),
        ("Equalised Odds",
         "ML fairness criterion: FPR and FNR should be equal across groups. "
         "Gap > 0.15 flagged as significant."),
        ("Manager Bias Score",
         "Per-manager score 0–100. Starts at 100, deducts 20 pts per protected attribute "
         "with flagged disparate impact. Managers scoring below 60 are flagged."),
        ("Overall Fairness Score",
         "Weighted average: Hiring 40%, ML Model 20%, Manager 20%, Leave/Task 20%. "
         "Missing modules are excluded from the average."),
    ]
    for title, body in items:
        story.append(Paragraph(f"<b>{title}</b>", S["body"]))
        story.append(Paragraph(body,
                               ParagraphStyle("mb",fontName="Helvetica",fontSize=9,
                                              textColor=colors.black,leading=13,
                                              leftIndent=12,spaceAfter=8)))


# ── Main entry point ──────────────────────────────────────────────────────────

def build_report(
    out_path:    str,
    overall_score: float,
    module_scores: dict,
    hiring_result: dict  = None,
    ml_result:     dict  = None,
    manager_result:dict  = None,
    leave_result:  dict  = None,
    gemini_text:   str   = "",
    meta:          dict  = None,
):
    meta = meta or {}
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
    )
    S     = _styles()
    story = []

    _cover(story, S, overall_score, module_scores, meta)
    _hiring_section(story, S, hiring_result or {})
    _ml_section(story, S, ml_result)
    _manager_section(story, S, manager_result)
    _leave_task_section(story, S, leave_result)
    if gemini_text:
        _ai_section(story, S, gemini_text)
    _methodology(story, S)

    # Footer disclaimer
    story.append(Spacer(1,12))
    story.append(HRFlowable(width="100%",thickness=1,color=MGRAY,spaceAfter=5))
    story.append(Paragraph(
        "FairLens report is auto-generated. Statistical significance indicates patterns for "
        "investigation, not proof of intentional discrimination. Consult HR and legal professionals.",
        S["disc"]))

    doc.build(story)
    return out_path
