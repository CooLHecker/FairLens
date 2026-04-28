"""
FairLens — Premium Streamlit Frontend v2.0
"""

import base64
from pathlib import Path

import streamlit as st
import requests
import time
import os
import textwrap
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

def load_logo_b64() -> str:
    logo_path = BASE_DIR / "assets" / "fairlens_logo.png"
    with logo_path.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

st.set_page_config(
    page_title="FairLens — AI Bias Detection",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BACKEND_URL = os.getenv("FAIRLENS_BACKEND_URL", "http://localhost:8000").rstrip("/")
_LOGO_B64 = load_logo_b64()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{background:#04040f!important;font-family:'DM Sans',sans-serif;color:#e8e8f0;}
[data-testid="stHeader"]{display:none!important;}[data-testid="stToolbar"]{display:none!important;}
[data-testid="stDecoration"]{display:none!important;}footer{display:none!important;}#MainMenu{display:none!important;}
.block-container{padding:0!important;max-width:100%!important;}
::-webkit-scrollbar{width:4px;}::-webkit-scrollbar-track{background:#04040f;}::-webkit-scrollbar-thumb{background:#2a1f6e;border-radius:4px;}
#bg-canvas{position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;}
.fl-wrap{position:sticky;top:0;z-index:1000;padding:14px 48px;background:rgba(4,4,15,0.92);backdrop-filter:blur(24px);border-bottom:1px solid rgba(94,60,255,0.15);}
.fl-wrap [data-testid="stHorizontalBlock"]{align-items:center;}
.fl-wrap [data-testid="column"]{display:flex;align-items:center;}
.fl-wrap [data-testid="column"] > div{width:100%;}
.fl-logo{display:flex;align-items:center;gap:12px;}
.fl-logo img{height:46px;width:auto;object-fit:contain;filter:drop-shadow(0 0 12px rgba(94,60,255,0.45));}
.fl-logo-text{font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;background:linear-gradient(135deg,#7c5cfc,#00d4ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-0.02em;}
.fl-learn-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px;padding:10px 48px 0;align-items:stretch;}
.fl-gauge-shell{background:linear-gradient(180deg,rgba(255,255,255,0.03),rgba(255,255,255,0.015));border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:18px 18px 10px;margin:10px 0 26px;box-shadow:0 14px 40px rgba(8,8,20,0.28);}
.fl-mini-score-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin:14px 0 6px;}
.fl-mini-score{background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:14px 16px;}
.fl-mini-score-label{font-size:0.73rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:rgba(232,232,240,0.42);margin-bottom:8px;}
.fl-mini-score-value{font-family:'Syne',sans-serif;font-size:1.15rem;font-weight:700;margin-bottom:8px;}
.fl-mini-score-bar{height:7px;border-radius:999px;background:rgba(255,255,255,0.06);overflow:hidden;}
.fl-mini-score-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#5e3cff,#00d4ff);box-shadow:0 0 12px rgba(94,60,255,0.35);}
.fl-hero{min-height:88vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 48px 60px;text-align:center;position:relative;}
.fl-hero-badge{display:inline-flex;align-items:center;gap:8px;padding:6px 18px;border-radius:6px;background:rgba(94,60,255,0.10);border:1px solid rgba(94,60,255,0.28);font-size:0.75rem;font-weight:600;color:#a78bfa;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:32px;}
.fl-hero-title{font-family:'Impact','Arial Black',sans-serif;font-size:clamp(3rem,7vw,6rem);font-weight:900;line-height:1.0;letter-spacing:-0.01em;margin-bottom:24px;color:#fff;text-align:center;text-transform:uppercase;}
.fl-hero-title .accent{background:linear-gradient(135deg,#7c5cfc 0%,#00d4ff 60%,#a78bfa 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.fl-hero p{font-size:1.1rem;line-height:1.7;color:rgba(232,232,240,0.52);max-width:580px;margin:0 auto 52px;font-weight:300;}
.fl-section{padding:70px 48px;max-width:1300px;margin:0 auto;}
.fl-section-label{font-size:0.72rem;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;color:#7c5cfc;margin-bottom:10px;}
.fl-section-title{font-family:'Syne',sans-serif;font-size:clamp(1.7rem,3vw,2.4rem);font-weight:700;color:#fff;margin-bottom:12px;letter-spacing:-0.02em;}
.fl-section-title-center{font-family:'Syne',sans-serif;font-size:clamp(1.7rem,3vw,2.4rem);font-weight:700;color:#fff;margin-bottom:12px;letter-spacing:-0.02em;text-align:center;}
.fl-section-sub{font-size:0.95rem;color:rgba(232,232,240,0.42);max-width:520px;line-height:1.65;}
.fl-section-sub-center{font-size:0.95rem;color:rgba(232,232,240,0.42);max-width:580px;line-height:1.65;margin:0 auto;text-align:center;}
.upload-card{background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:24px;transition:all 0.3s ease;margin-bottom:8px;}
.upload-card:hover{background:rgba(94,60,255,0.06);border-color:rgba(94,60,255,0.22);transform:translateY(-2px);box-shadow:0 8px 32px rgba(94,60,255,0.10);}
.upload-card-header{display:flex;align-items:flex-start;gap:14px;margin-bottom:14px;}
.upload-card-icon{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0;}
.icon-blue{background:rgba(94,60,255,0.15);}.icon-cyan{background:rgba(0,212,255,0.12);}.icon-purple{background:rgba(167,139,250,0.15);}.icon-green{background:rgba(52,211,153,0.12);}.icon-orange{background:rgba(251,146,60,0.12);}
.upload-card-title{font-family:'Syne',sans-serif;font-size:0.95rem;font-weight:700;color:#fff;margin-bottom:3px;}
.upload-card-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.62rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;}
.badge-required{background:rgba(239,68,68,0.10);color:#f87171;border:1px solid rgba(239,68,68,0.2);}
.badge-optional{background:rgba(94,60,255,0.10);color:#a78bfa;border:1px solid rgba(94,60,255,0.2);}
.upload-card-desc{font-size:0.8rem;color:rgba(232,232,240,0.38);line-height:1.55;margin-bottom:14px;}
.upload-success{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:5px;background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.2);color:#34d399;font-size:0.76rem;font-weight:500;margin-top:6px;}
.fl-audit-wrap{text-align:center;padding:52px 48px;}
.fl-metric-card{background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:22px 18px;text-align:center;transition:all 0.3s ease;}
.fl-metric-card:hover{border-color:rgba(94,60,255,0.28);background:rgba(94,60,255,0.05);}
.fl-metric-value{font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;margin-bottom:4px;}
.fl-metric-label{font-size:0.7rem;color:rgba(232,232,240,0.38);font-weight:600;letter-spacing:0.07em;text-transform:uppercase;}
.fl-risk-info{background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:20px 24px;margin:12px 0 28px;font-size:0.82rem;color:rgba(232,232,240,0.55);line-height:1.6;}
.fl-risk-info strong{color:rgba(232,232,240,0.85);font-weight:600;}
.fl-risk-row{display:flex;align-items:center;gap:10px;margin-top:8px;}
.fl-risk-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.fl-insights{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:28px 32px;margin-bottom:28px;}
.fl-insight-item{display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.045);font-size:0.86rem;color:rgba(232,232,240,0.68);line-height:1.5;}
.fl-insight-item:last-child{border-bottom:none;}
.fl-insight-dot{width:6px;height:6px;border-radius:50%;margin-top:7px;flex-shrink:0;}
.fl-alert{padding:12px 18px;border-radius:8px;margin:14px 0;font-size:0.86rem;}
.fl-alert-error{background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);color:#fca5a5;}
.fl-alert-success{background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.2);color:#6ee7b7;}
.fl-alert-info{background:rgba(94,60,255,0.08);border:1px solid rgba(94,60,255,0.2);color:#a78bfa;}
.fl-divider{height:1px;background:linear-gradient(90deg,transparent,rgba(94,60,255,0.25),transparent);margin:0 48px;}
.fl-learn-card{background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.07);border-radius:18px;padding:28px;transition:all 0.3s ease;height:100%;min-height:220px;display:flex;flex-direction:column;justify-content:flex-start;box-shadow:0 12px 30px rgba(6,6,20,0.18);}
.fl-learn-card:hover{border-color:rgba(94,60,255,0.22);background:rgba(94,60,255,0.04);transform:translateY(-3px);}
.fl-learn-card-icon{font-size:1.8rem;margin-bottom:14px;display:block;}
.fl-learn-card-title{font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#fff;margin-bottom:8px;}
.fl-learn-card-desc{font-size:0.83rem;color:rgba(232,232,240,0.42);line-height:1.6;}
[data-testid="stFileUploader"]{background:rgba(255,255,255,0.015)!important;border:1.5px dashed rgba(94,60,255,0.28)!important;border-radius:10px!important;padding:10px!important;}
[data-testid="stFileUploader"]:hover{border-color:rgba(94,60,255,0.55)!important;background:rgba(94,60,255,0.03)!important;}
[data-testid="stFileUploaderDropzone"]{background:transparent!important;}
[data-testid="stFileUploaderDropzoneInstructions"]{color:rgba(232,232,240,0.38)!important;font-size:0.78rem!important;}
.stProgress>div>div{background:linear-gradient(90deg,#5e3cff,#00d4ff)!important;}
[data-testid="stMetric"]{background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:18px;}
[data-testid="stMetricValue"]{color:#fff!important;font-family:'Syne',sans-serif!important;}
.element-container{margin-bottom:0!important;}
/* Buttons */
.stButton,.stDownloadButton{width:100%;}
.stButton>button,.stDownloadButton>button{background:linear-gradient(180deg,rgba(20,18,40,0.92),rgba(12,12,28,0.88))!important;color:#eef2ff!important;border:1px solid rgba(148,163,184,0.18)!important;border-radius:14px!important;font-family:'DM Sans',sans-serif!important;font-weight:700!important;font-size:0.92rem!important;letter-spacing:0.01em!important;padding:0 18px!important;min-height:46px!important;width:100%!important;display:flex!important;align-items:center!important;justify-content:center!important;gap:8px!important;white-space:nowrap!important;line-height:1!important;box-shadow:0 10px 30px rgba(2,6,23,0.28), inset 0 1px 0 rgba(255,255,255,0.06)!important;backdrop-filter:blur(10px)!important;transition:transform 0.18s ease,box-shadow 0.18s ease,border-color 0.18s ease,background 0.18s ease!important;}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-1px)!important;border-color:rgba(125,211,252,0.34)!important;box-shadow:0 14px 34px rgba(30,41,59,0.34), 0 0 0 1px rgba(255,255,255,0.04) inset!important;}
.stButton>button:focus:not(:active),.stDownloadButton>button:focus:not(:active){outline:none!important;box-shadow:0 0 0 3px rgba(96,165,250,0.22),0 12px 28px rgba(37,99,235,0.18)!important;border-color:rgba(96,165,250,0.42)!important;}
.stButton>button:active,.stDownloadButton>button:active{transform:translateY(0)!important;box-shadow:0 8px 18px rgba(15,23,42,0.24)!important;}
.stButton>button[kind="primary"],.stDownloadButton>button{background:linear-gradient(135deg,#6d4aff 0%,#4f46e5 55%,#00c2ff 100%)!important;border-color:rgba(125,211,252,0.42)!important;color:#ffffff!important;box-shadow:0 14px 34px rgba(79,70,229,0.32),0 0 0 1px rgba(255,255,255,0.08) inset!important;}
.stButton>button[kind="primary"]:hover,.stDownloadButton>button:hover{box-shadow:0 18px 40px rgba(79,70,229,0.38),0 0 0 1px rgba(255,255,255,0.10) inset!important;}
@media (max-width: 980px){
  .fl-wrap{padding:14px 24px;}
  .fl-section,.fl-hero,.fl-audit-wrap{padding-left:24px;padding-right:24px;}
  .fl-divider{margin:0 24px;}
  .fl-learn-grid{grid-template-columns:1fr;gap:16px;padding:10px 24px 0;}
}
</style>
""", unsafe_allow_html=True)

# ── Animated Magnifying Glass Background ──────────────────────────────────────
st.markdown("""
<canvas id="bg-canvas"></canvas>
<script>
(function() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    function resize() { canvas.width=window.innerWidth; canvas.height=window.innerHeight; }
    resize(); window.addEventListener('resize', resize);
    let t = 0;
    const cx0=0.5,cy0=0.44,orbitR=0.055;
    function drawMagnifier(cx,cy,radius,alpha) {
        ctx.save(); ctx.globalAlpha=alpha;
        const W=canvas.width,H=canvas.height,px=cx*W,py=cy*H,r=radius*Math.min(W,H);
        const glow=ctx.createRadialGradient(px,py,r*0.7,px,py,r*1.3);
        glow.addColorStop(0,'rgba(94,60,255,0.14)');glow.addColorStop(0.5,'rgba(94,60,255,0.05)');glow.addColorStop(1,'rgba(94,60,255,0)');
        ctx.beginPath();ctx.arc(px,py,r*1.3,0,Math.PI*2);ctx.fillStyle=glow;ctx.fill();
        const lensGrad=ctx.createRadialGradient(px-r*0.22,py-r*0.22,0,px,py,r);
        lensGrad.addColorStop(0,'rgba(160,120,255,0.09)');lensGrad.addColorStop(0.6,'rgba(94,60,255,0.05)');lensGrad.addColorStop(1,'rgba(0,212,255,0.03)');
        ctx.beginPath();ctx.arc(px,py,r,0,Math.PI*2);ctx.fillStyle=lensGrad;ctx.fill();
        ctx.beginPath();ctx.arc(px,py,r,0,Math.PI*2);
        const ring=ctx.createLinearGradient(px-r,py-r,px+r,py+r);
        ring.addColorStop(0,'rgba(140,100,255,0.55)');ring.addColorStop(0.5,'rgba(0,212,255,0.38)');ring.addColorStop(1,'rgba(94,60,255,0.22)');
        ctx.strokeStyle=ring;ctx.lineWidth=Math.max(1.5,r*0.045);ctx.stroke();
        ctx.beginPath();ctx.arc(px-r*0.18,py-r*0.18,r*0.58,-Math.PI*0.9,-Math.PI*0.1);
        ctx.strokeStyle='rgba(255,255,255,0.13)';ctx.lineWidth=Math.max(1,r*0.028);ctx.stroke();
        ctx.save();ctx.globalAlpha=alpha*0.15;
        ctx.beginPath();ctx.moveTo(px-r*0.55,py);ctx.lineTo(px+r*0.55,py);ctx.moveTo(px,py-r*0.55);ctx.lineTo(px,py+r*0.55);
        ctx.strokeStyle='rgba(0,212,255,0.9)';ctx.lineWidth=0.7;ctx.stroke();ctx.restore();
        const angle=Math.PI*0.75;
        const hx1=px+Math.cos(angle)*r*0.95,hy1=py+Math.sin(angle)*r*0.95;
        const hx2=hx1+Math.cos(angle)*r*0.65,hy2=hy1+Math.sin(angle)*r*0.65;
        const hGrad=ctx.createLinearGradient(hx1,hy1,hx2,hy2);
        hGrad.addColorStop(0,'rgba(94,60,255,0.65)');hGrad.addColorStop(1,'rgba(0,212,255,0.28)');
        ctx.beginPath();ctx.moveTo(hx1,hy1);ctx.lineTo(hx2,hy2);
        ctx.strokeStyle=hGrad;ctx.lineWidth=Math.max(3,r*0.09);ctx.lineCap='round';ctx.stroke();
        ctx.restore();
    }
    function drawParticle(x,y,size,alpha,color){ctx.save();ctx.globalAlpha=alpha;ctx.beginPath();ctx.arc(x,y,size,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();ctx.restore();}
    const particles=Array.from({length:28},()=>({x:Math.random(),y:Math.random(),vx:(Math.random()-0.5)*0.00007,vy:(Math.random()-0.5)*0.00007,size:Math.random()*1.4+0.4,alpha:Math.random()*0.13+0.025,color:Math.random()>0.5?'rgba(94,60,255,1)':'rgba(0,212,255,1)',phase:Math.random()*Math.PI*2}));
    function drawGrid(){ctx.save();ctx.globalAlpha=0.02;ctx.strokeStyle='rgba(94,60,255,1)';ctx.lineWidth=0.5;const W=canvas.width,H=canvas.height,step=64;for(let x=0;x<W;x+=step){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}for(let y=0;y<H;y+=step){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}ctx.restore();}
    function animate(){ctx.clearRect(0,0,canvas.width,canvas.height);drawGrid();const W=canvas.width,H=canvas.height;
        particles.forEach(p=>{p.x+=p.vx;p.y+=p.vy;if(p.x<0)p.x=1;if(p.x>1)p.x=0;if(p.y<0)p.y=1;if(p.y>1)p.y=0;const pulse=0.8+0.2*Math.sin(t*0.5+p.phase);drawParticle(p.x*W,p.y*H,p.size,p.alpha*pulse,p.color);});
        const mx=cx0+orbitR*Math.cos(t*0.35),my=cy0+orbitR*0.45*Math.sin(t*0.35);drawMagnifier(mx,my,0.14,0.26);
        const mx2=0.79+0.025*Math.cos(t*0.28+2),my2=0.66+0.018*Math.sin(t*0.28+1);drawMagnifier(mx2,my2,0.055,0.14);
        t+=0.008;requestAnimationFrame(animate);}
    animate();
})();
</script>
""", unsafe_allow_html=True)

# ── State ─────────────────────────────────────────────────────────────────────
for k, v in [("page","home"),("report_data",None),("pdf_bytes",None),("audit_scores",{})]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Navbar (logo and buttons aligned on one row) ──────────────────────────────
st.markdown('<div class="fl-wrap">', unsafe_allow_html=True)
logo_col, spacer_col, nc1, nc2, nc3 = st.columns([1.1, 5.0, 1.15, 1.45, 1.45], gap="small")
with logo_col:
    st.markdown(f'''<div class="fl-logo"><img src="data:image/png;base64,{_LOGO_B64}" alt="FairLens"/></div>''', unsafe_allow_html=True)
with nc1:
    if st.button("🏠 Home", key="nav_home", type="secondary"):
        st.session_state.page = "home"; st.rerun()
with nc2:
    if st.button("📊 Dashboard", key="nav_dash", type="secondary"):
        st.session_state.page = "dashboard"; st.rerun()
with nc3:
    if st.button("ℹ️ Learn More", key="nav_learn", type="secondary"):
        st.session_state.page = "learn"; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="fl-divider"></div>', unsafe_allow_html=True)

# ── Helper functions ──────────────────────────────────────────────────────────
def safe_float(s):
    if s in (None, "N/A", "—", "–", "", "-"):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None

def score_color(s):
    v = safe_float(s)
    if v is None: return "#a78bfa"
    if v >= 75: return "#34d399"
    if v >= 50: return "#fbbf24"
    return "#f87171"

def risk_level(s):
    v = safe_float(s)
    if v is None: return "UNKNOWN", "#a78bfa"
    if v >= 75: return "LOW", "#34d399"
    if v >= 50: return "MODERATE", "#fbbf24"
    return "HIGH", "#f87171"

def parse_header_score(headers, key):
    val = str(headers.get(key, "")).strip()
    if not val or val.lower() in {"n/a", "none", "null", "nan", "—", "–", "", "-"}:
        return "N/A"
    try:
        return float(val)
    except (ValueError, TypeError):
        return "N/A"


def progress_width(score):
    value = safe_float(score)
    if value is None:
        return 0
    return max(0, min(100, value))


def build_score_chip(label, score):
    value = safe_float(score)
    display = f"{value:.1f}" if value is not None else "N/A"
    color = score_color(score)
    width = progress_width(score)
    return textwrap.dedent(f"""
    <div class=\"fl-mini-score\">
      <div class=\"fl-mini-score-label\">{label}</div>
      <div class=\"fl-mini-score-value\" style=\"color:{color};\">{display}</div>
      <div class=\"fl-mini-score-bar\"><div class=\"fl-mini-score-fill\" style=\"width:{width}%;background:{color};\"></div></div>
    </div>
    """).strip()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LEARN MORE
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "learn":
    st.markdown("""
    <div class="fl-section">
      <div class="fl-section-label">About FairLens</div>
      <div class="fl-section-title">Built for Ethical Organizations</div>
      <div class="fl-section-sub">
        FairLens helps organizations uncover hidden unfairness in hiring systems, promotions, salaries,
        workload allocation, leave approvals, and machine learning decisions.
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="fl-learn-grid">
      <div class="fl-learn-card">
        <span class="fl-learn-card-icon">🎯</span>
        <div class="fl-learn-card-title">Detect Hidden Bias</div>
        <div class="fl-learn-card-desc">Statistical analysis across gender, caste, location, and education uncovers demographic disparities invisible to the naked eye.</div>
      </div>
      <div class="fl-learn-card">
        <span class="fl-learn-card-icon">📈</span>
        <div class="fl-learn-card-title">Visualize Fairness Scores</div>
        <div class="fl-learn-card-desc">Module-level and overall fairness scores displayed in clean, intuitive dashboards your leadership can act on immediately.</div>
      </div>
      <div class="fl-learn-card">
        <span class="fl-learn-card-icon">📄</span>
        <div class="fl-learn-card-title">Download Audit Reports</div>
        <div class="fl-learn-card-desc">AI-generated PDF reports with Gemini insights, charts, and actionable recommendations ready to share with stakeholders.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:0 48px 32px;">
    <div style="background:rgba(94,60,255,0.05);border:1px solid rgba(94,60,255,0.18);border-radius:16px;padding:28px;">
      <div style="font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:700;color:#fff;margin-bottom:16px;">Fairness Score Scale</div>
      <div style="display:flex;gap:14px;flex-wrap:wrap;">
        <div style="flex:1;min-width:130px;padding:14px;background:rgba(52,211,153,0.07);border:1px solid rgba(52,211,153,0.18);border-radius:10px;text-align:center;">
          <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#34d399;">75–100</div>
          <div style="font-size:0.72rem;color:rgba(232,232,240,0.45);margin-top:4px;">LOW BIAS ✅</div>
        </div>
        <div style="flex:1;min-width:130px;padding:14px;background:rgba(251,191,36,0.07);border:1px solid rgba(251,191,36,0.18);border-radius:10px;text-align:center;">
          <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#fbbf24;">50–74</div>
          <div style="font-size:0.72rem;color:rgba(232,232,240,0.45);margin-top:4px;">MODERATE BIAS ⚠️</div>
        </div>
        <div style="flex:1;min-width:130px;padding:14px;background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.18);border-radius:10px;text-align:center;">
          <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#f87171;">0–49</div>
          <div style="font-size:0.72rem;color:rgba(232,232,240,0.45);margin-top:4px;">HIGH BIAS ❌</div>
        </div>
      </div>
    </div>
    </div>""", unsafe_allow_html=True)

    if st.button("← Back to Home", key="back_learn", type="secondary"):
        st.session_state.page = "home"; st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "dashboard":
    if not st.session_state.audit_scores:
        st.markdown("""
        <div class="fl-hero" style="min-height:60vh;">
          <div class="fl-hero-badge">📊 Dashboard</div>
          <div class="fl-hero-title" style="font-size:2.5rem;">No Audit Results Yet</div>
          <p>Run a full audit from the Home page to see your fairness dashboard.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("← Back to Home", key="go_home_dash", type="secondary"):
            st.session_state.page = "home"; st.rerun()
    else:
        scores  = st.session_state.audit_scores
        overall = scores.get("overall", 0)
        hiring  = scores.get("hiring", "N/A")
        ml      = scores.get("ml_model", "N/A")
        manager = scores.get("manager", "N/A")
        leave   = scores.get("leave_task", "N/A")

        risk_txt, risk_color = risk_level(overall)

        st.markdown("""<div class="fl-section" style="padding-bottom:20px;">
          <div class="fl-section-label">Audit Results</div>
          <div class="fl-section-title">Fairness Dashboard</div>
        </div>""", unsafe_allow_html=True)

        def fmt(s):
            v = safe_float(s)
            return f"{v:.1f}" if v is not None else str(s)

        m1,m2,m3,m4,m5 = st.columns(5, gap="small")
        for col, label, val, color in [
            (m1,"Overall Score", fmt(overall), score_color(overall)),
            (m2,"Hiring Score",  fmt(hiring),  score_color(hiring)),
            (m3,"Risk Level",    risk_txt,      risk_color),
            (m4,"ML Bias Score", fmt(ml),       score_color(ml)),
            (m5,"Manager Score", fmt(manager),  score_color(manager)),
        ]:
            with col:
                st.markdown(f"""<div class="fl-metric-card">
                  <div class="fl-metric-value" style="color:{color};">{val}</div>
                  <div class="fl-metric-label">{label}</div>
                </div>""", unsafe_allow_html=True)

        # Risk Level explanation
        st.markdown(f"""
        <div style="padding:0 4px;">
        <div class="fl-risk-info">
          <strong>ℹ️ What does Risk Level mean?</strong><br>
          Risk Level summarises your organisation's overall fairness posture based on combined scores across all uploaded modules.
          <div class="fl-risk-row"><div class="fl-risk-dot" style="background:#34d399;box-shadow:0 0 5px #34d399;"></div><strong style="color:#34d399;">LOW</strong>&nbsp;(75–100) — Strong fairness practices. Minimal detectable bias.</div>
          <div class="fl-risk-row"><div class="fl-risk-dot" style="background:#fbbf24;box-shadow:0 0 5px #fbbf24;"></div><strong style="color:#fbbf24;">MODERATE</strong>&nbsp;(50–74) — Some disparity detected. Review flagged modules and implement corrective policies.</div>
          <div class="fl-risk-row"><div class="fl-risk-dot" style="background:#f87171;box-shadow:0 0 5px #f87171;"></div><strong style="color:#f87171;">HIGH</strong>&nbsp;(0–49) — Significant bias found. Immediate action and a structured DEI audit recommended.</div>
          <div class="fl-risk-row"><div class="fl-risk-dot" style="background:#a78bfa;"></div><strong style="color:#a78bfa;">UNKNOWN</strong>&nbsp;— Insufficient data for a reliable score. Upload more CSV modules.</div>
        </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="padding:0 48px;">', unsafe_allow_html=True)

        h_f  = safe_float(hiring)
        m_f  = safe_float(ml)
        mg_f = safe_float(manager)
        lv_f = safe_float(leave)

        insights = []
        if h_f is not None:
            if h_f>=75: insights.append(("✅","#34d399","Hiring process shows strong demographic fairness."))
            elif h_f>=50: insights.append(("⚠️","#fbbf24",f"Moderate hiring imbalance detected — review demographic breakdown (score: {h_f:.1f})."))
            else: insights.append(("❌","#f87171",f"High hiring bias alert — immediate review recommended (score: {h_f:.1f})."))
        if m_f is not None:
            if m_f>=75: insights.append(("✅","#34d399","ML model predictions are largely unbiased across protected groups."))
            elif m_f>=50: insights.append(("⚠️","#fbbf24","ML model shows moderate disparate impact — consider fairness-aware retraining."))
            else: insights.append(("❌","#f87171","ML model bias is significant — model fairness audit is critical."))
        if mg_f is not None:
            if mg_f>=75: insights.append(("✅","#34d399","Manager-level fairness is consistent across review panels."))
            else: insights.append(("⚠️","#fbbf24",f"Manager fairness needs attention — consider structured calibration (score: {mg_f:.1f})."))
        if lv_f is not None:
            if lv_f>=75: insights.append(("✅","#34d399","Leave approvals appear consistent and equitable."))
            else: insights.append(("⚠️","#fbbf24",f"Leave approval disparities found — recommend policy review (score: {lv_f:.1f})."))
        if not insights:
            insights.append(("ℹ️","#a78bfa","Audit complete. Upload optional modules for richer insights."))

        items_html = "".join([
            f'<div class="fl-insight-item"><div class="fl-insight-dot" style="background:{c};box-shadow:0 0 5px {c};"></div><span>{icon} {text}</span></div>'
            for icon,c,text in insights
        ])
        st.markdown(f"""<div class="fl-insights">
          <div style="font-family:'Syne',sans-serif;font-size:0.95rem;font-weight:700;color:#fff;margin-bottom:14px;">AI Insights Summary</div>
          {items_html}
        </div>""", unsafe_allow_html=True)

        try:
            import plotly.graph_objects as go
            score_data = {k:v for k,v in [("Hiring",h_f),("ML Model",m_f),("Manager",mg_f),("Leave/Task",lv_f)] if v is not None}
            st.markdown('<div class="fl-gauge-shell">', unsafe_allow_html=True)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=overall,
                number={"suffix": " / 100", "font": {"size": 34, "color": score_color(overall), "family": "Syne"}},
                title={"text": "Overall Fairness Score", "font": {"size": 18, "color": "#e8e8f0", "family": "Syne"}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "rgba(0,0,0,0)"},
                    "bar": {"color": score_color(overall), "thickness": 0.34},
                    "bgcolor": "rgba(255,255,255,0.05)",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, 50], "color": "rgba(248,113,113,0.25)"},
                        {"range": [50, 75], "color": "rgba(251,191,36,0.22)"},
                        {"range": [75, 100], "color": "rgba(52,211,153,0.22)"},
                    ],
                    "threshold": {"line": {"color": "#ffffff", "width": 4}, "thickness": 0.75, "value": overall},
                },
                domain={"x": [0, 1], "y": [0, 1]},
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8e8f0", family="DM Sans"),
                height=360,
                margin=dict(l=12, r=12, t=36, b=10),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            if score_data:
                chips = "".join([build_score_chip(label, value) for label, value in score_data.items()])
                st.markdown(f"<div class=\"fl-mini-score-grid\">{chips}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception:
            pass

        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.pdf_bytes:
            st.markdown("<div style=\"text-align:center;padding:28px 0 16px;\"><div style=\"font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#fff;margin-bottom:14px;\">Your audit report is ready</div></div>", unsafe_allow_html=True)
            col_c = st.columns([2,1,2])[1]
            with col_c:
                st.download_button(label="⬇️  Download PDF Report", data=st.session_state.pdf_bytes, file_name="fairlens_audit_report.pdf", mime="application/pdf", use_container_width=True)

        if st.button("← Run Another Audit", key="back_home_dash", type="secondary"):
            st.session_state.page = "home"; st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ═══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("""
    <div class="fl-hero">
      <div class="fl-hero-badge">✦ AI-Powered Fairness Auditing</div>
      <div class="fl-hero-title">Detect Bias.<br><span class="accent">Build Fair Decisions.</span></div>
      <p>AI-powered fairness audits for hiring, promotions, salaries, leave approvals, workload distribution, and automated decisions.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="fl-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="fl-section" style="padding-bottom:20px;text-align:center;">
      <div class="fl-section-label" style="text-align:center;">Data Upload</div>
      <div class="fl-section-title-center">Upload Your Data</div>
      <div class="fl-section-sub-center">Drop your CSV files below. Only Hiring Data is required — all others are optional but improve audit depth.</div>
    </div>""", unsafe_allow_html=True)

    pad_l, grid_area, pad_r = st.columns([1,10,1])
    with grid_area:
        row1_c1, row1_c2 = st.columns(2)
        row2_c1, row2_c2 = st.columns(2)
        row3_c1, row3_sp = st.columns([1,1])

        upload_defs = [
            (row1_c1, "icon-blue",  "📋", "Hiring Data",         "required", "hiring_upload",  "Upload candidate hiring decisions CSV. Must include gender, caste, location, college tier, education level, and selection outcome."),
            (row1_c2, "icon-cyan",  "🤖", "ML Predictions",      "optional", "ml_upload",      "Upload ML model output CSV with actual vs predicted labels and predicted probabilities."),
            (row2_c1, "icon-purple","👔", "Manager Appraisal",   "optional", "manager_upload", "Upload appraisal and review data per manager to identify patterns of demographic favouritism."),
            (row2_c2, "icon-green", "🌿", "Leave Records",       "optional", "leave_upload",   "Upload leave approval/rejection records to detect demographic disparities in grant rates."),
        ]

        uploaded = {}
        for col, icon_cls, icon, title, badge_type, key, desc in upload_defs:
            badge_cls = "badge-required" if badge_type == "required" else "badge-optional"
            badge_lbl = "Required" if badge_type == "required" else "Optional"
            with col:
                st.markdown(f"""<div class="upload-card">
                  <div class="upload-card-header">
                    <div class="upload-card-icon {icon_cls}">{icon}</div>
                    <div>
                      <div class="upload-card-title">{title}</div>
                      <span class="upload-card-badge {badge_cls}">{badge_lbl}</span>
                    </div>
                  </div>
                  <div class="upload-card-desc">{desc}</div>
                </div>""", unsafe_allow_html=True)
                f = st.file_uploader("", type=["csv"], key=key, label_visibility="collapsed")
                uploaded[key] = f
                if f:
                    st.markdown(f'<div class="upload-success">✓ {title} loaded</div>', unsafe_allow_html=True)

        with row3_c1:
            st.markdown("""<div class="upload-card">
              <div class="upload-card-header">
                <div class="upload-card-icon icon-orange">📂</div>
                <div>
                  <div class="upload-card-title">Task Assignments</div>
                  <span class="upload-card-badge badge-optional">Optional</span>
                </div>
              </div>
              <div class="upload-card-desc">Upload task/project assignment data to check for inequitable workload distribution.</div>
            </div>""", unsafe_allow_html=True)
            task_f = st.file_uploader("", type=["csv"], key="task_upload", label_visibility="collapsed")
            if task_f:
                st.markdown('<div class="upload-success">✓ Task data loaded</div>', unsafe_allow_html=True)

    hiring_file  = uploaded.get("hiring_upload")
    ml_file      = uploaded.get("ml_upload")
    manager_file = uploaded.get("manager_upload")
    leave_file   = uploaded.get("leave_upload")

    # Audit button
    st.markdown('<div class="fl-audit-wrap">', unsafe_allow_html=True)
    run_col = st.columns([3,2,3])[1]
    with run_col:
        run_audit = st.button("🔍 Run Fairness Audit", key="run_audit", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if run_audit:
        if not hiring_file:
            st.markdown('<div class="fl-alert fl-alert-error">❌ Hiring data CSV is required. Please upload it above.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="padding:0 48px;">', unsafe_allow_html=True)
            status_ph   = st.empty()
            progress_ph = st.empty()
            prog_bar    = progress_ph.progress(0.0)

            for progress, msg in [(0.15,"🔍 Validating files…"),(0.35,"📊 Running hiring analysis…"),(0.55,"🤖 Checking ML fairness…"),(0.70,"📋 Evaluating task allocation…"),(0.85,"🌿 Analysing leave patterns…"),(0.93,"👔 Manager-level check…")]:
                status_ph.markdown(f'<div class="fl-alert fl-alert-info">{msg}</div>', unsafe_allow_html=True)
                prog_bar.progress(progress)
                time.sleep(0.28)

            try:
                files = {}
                # Reset file pointers before reading to fix multiple-upload bug
                hiring_file.seek(0)
                files["hiring_file"] = (hiring_file.name, hiring_file.read(), "text/csv")
                if ml_file:
                    ml_file.seek(0)
                    files["ml_file"] = (ml_file.name, ml_file.read(), "text/csv")
                if manager_file:
                    manager_file.seek(0)
                    files["manager_file"] = (manager_file.name, manager_file.read(), "text/csv")
                if leave_file:
                    leave_file.seek(0)
                    files["leave_file"] = (leave_file.name, leave_file.read(), "text/csv")
                if task_f:
                    task_f.seek(0)
                    files["task_file"] = (task_f.name, task_f.read(), "text/csv")

                resp = requests.post(f"{BACKEND_URL}/api/v1/analyse/full-audit", files=files, data={"generate_pdf":"true"}, timeout=120)
                prog_bar.progress(1.0)

                if resp.status_code == 200:
                    overall_score = float(resp.headers.get("X-Overall-Score", 0))
                    hiring_score  = float(resp.headers.get("X-Hiring-Score", 0))
                    ml_score  = parse_header_score(resp.headers, "X-ML-Score")
                    mgr_score = parse_header_score(resp.headers, "X-Manager-Score")
                    lv_score  = parse_header_score(resp.headers, "X-Leave-Score")

                    st.session_state.pdf_bytes = resp.content
                    st.session_state.audit_scores = {
                        "overall":    overall_score,
                        "hiring":     hiring_score,
                        "ml_model":   ml_score  if ml_file      else "N/A",
                        "manager":    mgr_score if manager_file  else "N/A",
                        "leave_task": lv_score  if (leave_file or task_f) else "N/A",
                    }
                    st.session_state.report_data = True
                    status_ph.markdown('<div class="fl-alert fl-alert-success">✅ Audit complete! Redirecting to dashboard…</div>', unsafe_allow_html=True)
                    time.sleep(1.2)
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    try: err = resp.json().get("detail", resp.text[:300])
                    except Exception: err = resp.text[:300]
                    status_ph.markdown(f'<div class="fl-alert fl-alert-error">❌ Backend error {resp.status_code}: {err}</div>', unsafe_allow_html=True)
                    progress_ph.empty()

            except requests.exceptions.ConnectionError:
                status_ph.markdown('<div class="fl-alert fl-alert-error">❌ Cannot reach backend. Run: <code>uvicorn main:app --reload --port 8000</code></div>', unsafe_allow_html=True)
                progress_ph.empty()
            except Exception as e:
                status_ph.markdown(f'<div class="fl-alert fl-alert-error">❌ Unexpected error: {e}</div>', unsafe_allow_html=True)
                progress_ph.empty()

            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:80px;"></div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
