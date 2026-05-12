import streamlit as st
import pandas as pd
import json
import os
import streamlit.components.v1 as components
from datetime import datetime

from kiteconnect import KiteConnect
from streamlit_autorefresh import st_autorefresh

from kite_fetch import (
    load_instruments,
    fetch_option_chain,
)

from charts import (
    plot_oi_chart,
    plot_pcr_gauge,
    plot_total_oi_trend,
)

from database import (
    initialize_database,
    save_oi_snapshot,
    load_today_history,
    load_full_history,
)

from ai_engine import generate_ai_signal

from alerts import send_telegram_alert

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="PulseIQ — OI Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =====================================================
# AUTO SHOW REQUEST TOKEN
# =====================================================

query_params = st.query_params

request_token = query_params.get(
    "request_token",
    None
)

if request_token:

    st.markdown(
        """
        <div style='
            background:#07140d;
            border:1px solid #00ff66;
            padding:25px;
            border-radius:15px;
            margin-bottom:20px;
        '>

        <h2 style='color:#00ff66;'>
            🔑 Request Token Detected
        </h2>

        <p style='color:#a0ffb8;'>
            Copy this token and paste into login box.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.code(request_token)

    st.success("✅ Token Ready To Copy")

# =====================================================
# CUSTOM CSS — HERO + SIDEBAR
# =====================================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Exo+2:ital,wght@1,900&family=Rajdhani:wght@300;400;600&display=swap" rel="stylesheet">

<style>

/* ── Global app background ── */
.stApp { background: #030d05; }
.block-container { padding-top: 1rem; padding-bottom: 1rem; }

/* ══════════════════════════════════════════
   HERO BANNER
══════════════════════════════════════════ */
.hero {
    background: #020f06;
    border-radius: 16px;
    padding: 1.8rem 2.2rem;
    display: flex;
    align-items: center;
    gap: 26px;
    border: 1px solid #00ff6633;
    position: relative;
    overflow: hidden;
    margin-bottom: 1rem;
}
.hero::before {
    content: '';
    position: absolute;
    top: -80px; left: -80px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, #00ff4415 0%, transparent 65%);
    border-radius: 50%;
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -60px; right: 5%;
    width: 200px; height: 200px;
    background: radial-gradient(circle, #00ff4408 0%, transparent 65%);
    border-radius: 50%;
    pointer-events: none;
}
.bolt-ring {
    flex-shrink: 0;
    width: 70px; height: 70px;
    border-radius: 50%;
    border: 2px solid #00ff6677;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 0 14px #00ff4433;
    animation: rp 2.5s ease-in-out infinite;
}
@keyframes rp {
    0%,100% { box-shadow: 0 0 14px #00ff4433; }
    50%      { box-shadow: 0 0 28px #00ff4466; }
}
.brand-name {
    font-family: 'Exo 2', sans-serif;
    font-style: italic;
    font-weight: 900;
    font-size: 56px;
    color: #e8fff0;
    letter-spacing: -1px;
    text-shadow: 0 0 12px #00ff8855, 0 0 40px #00ff4422;
}
.ecg-path {
    stroke: #00ff66;
    stroke-width: 2.8;
    fill: none;
    stroke-linecap: round;
    stroke-dasharray: 185;
    stroke-dashoffset: 185;
    animation: draw 1.3s ease 0.5s forwards, ecgpulse 2.8s ease-in-out 1.9s infinite;
}
@keyframes draw     { to { stroke-dashoffset: 0; } }
@keyframes ecgpulse { 0%,100%{stroke-opacity:1} 50%{stroke-opacity:0.35} }
.subtitle {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 300;
    font-size: 12.5px;
    letter-spacing: 0.3em;
    color: #00cc55;
    text-transform: uppercase;
    margin-top: 5px;
    text-shadow: 0 0 8px #00ff4444;
}
.hero-divider { width:1px; height:50px; background:linear-gradient(to bottom,transparent,#00ff6644,transparent); flex-shrink:0; }
.badge {
    font-family: 'Rajdhani', sans-serif;
    font-size: 11.5px;
    letter-spacing: 0.14em;
    padding: 3px 11px;
    border-radius: 5px;
    white-space: nowrap;
    text-align: center;
    margin-bottom: 6px;
    display: block;
}
.blv {
    color: #39ff14;
    border: 1px solid #39ff1455;
    background: #39ff140d;
    box-shadow: 0 0 8px #39ff1422;
}
.blv::before {
    content: '';
    display: inline-block;
    width: 5px; height: 5px;
    border-radius: 50%;
    background: #39ff14;
    box-shadow: 0 0 6px #39ff14;
    margin-right: 5px;
    vertical-align: middle;
    animation: blink 1s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.1} }
.bnse {
    color: #00ff66;
    border: 1px solid #00ff6644;
    background: #00ff660d;
    box-shadow: 0 0 6px #00ff6618;
}

/* ══════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #020f06 !important;
    border-right: 1px solid #00ff6620 !important;
}

/* Sidebar section label (st.sidebar.markdown with ### ) */
[data-testid="stSidebar"] h3 {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.28em !important;
    text-transform: uppercase !important;
    color: #00ff6677 !important;
    border-bottom: 1px solid #00ff6618 !important;
    padding-bottom: 6px !important;
    margin: 0.8rem 0 0.4rem !important;
}

/* All sidebar labels */
[data-testid="stSidebar"] label p {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 11px !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: #00ff6677 !important;
}

/* Selectbox */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #041208 !important;
    border: 1px solid #00ff6630 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] span {
    color: #a0ffb8 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 13px !important;
    letter-spacing: 0.08em !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg {
    fill: #00ff6666 !important;
}

/* Number input */
[data-testid="stSidebar"] input[type="number"],
[data-testid="stSidebar"] input[type="text"],
[data-testid="stSidebar"] input[type="password"] {
    background: #041208 !important;
    border: 1px solid #00ff6630 !important;
    border-radius: 8px !important;
    color: #a0ffb8 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 14px !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stSidebar"] input:focus {
    border-color: #00ff66aa !important;
    box-shadow: 0 0 10px #00ff4430 !important;
}

/* Stepper +/- buttons */
[data-testid="stSidebar"] [data-testid="stNumberInputStepDown"],
[data-testid="stSidebar"] [data-testid="stNumberInputStepUp"] {
    background: #041208 !important;
    border-color: #00ff6630 !important;
    color: #00ff66 !important;
}

/* All buttons in sidebar */
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: #00ff660d !important;
    border: 1px solid #00ff6644 !important;
    border-radius: 8px !important;
    color: #00ff66 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 0 8px #00ff4415 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #00ff6622 !important;
    border-color: #00ff66aa !important;
    box-shadow: 0 0 18px #00ff4440 !important;
    color: #39ff14 !important;
}

/* Link button */
[data-testid="stSidebar"] a[data-testid="stLinkButton"],
[data-testid="stSidebar"] a[data-testid="stLinkButton"]:visited {
    display: block !important;
    width: 100% !important;
    background: #041208 !important;
    border: 1px solid #00ff6633 !important;
    border-radius: 8px !important;
    color: #00ff66 !important;
    text-align: center !important;
    padding: 0.45rem 1rem !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    text-decoration: none !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] a[data-testid="stLinkButton"]:hover {
    background: #00ff6618 !important;
    box-shadow: 0 0 14px #00ff4433 !important;
}

/* Divider */
[data-testid="stSidebar"] hr {
    border: none !important;
    border-top: 1px solid #00ff6618 !important;
    margin: 0.8rem 0 !important;
}

/* Success / error messages */
[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: #00ff660d !important;
    border: 1px solid #00ff6630 !important;
    border-radius: 8px !important;
    color: #a0ffb8 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 13px !important;
}

/* Sidebar mini brand stamp */
.sb-brand {
    font-family: 'Exo 2', sans-serif;
    font-style: italic;
    font-weight: 900;
    font-size: 20px;
    color: #00ff66;
    letter-spacing: 1px;
    text-shadow: 0 0 10px #00ff6677;
    padding: 0.6rem 0 0.4rem;
    border-bottom: 1px solid #00ff6620;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.sb-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #39ff14;
    box-shadow: 0 0 8px #39ff14;
    display: inline-block;
    animation: blink 1s ease-in-out infinite;
}

/* ── Metric cards neon tint ── */
[data-testid="stMetric"] {
    background: #041208 !important;
    border: 1px solid #00ff6622 !important;
    border-radius: 10px !important;
    padding: 0.8rem 1rem !important;
}
[data-testid="stMetricLabel"] p  { color: #00ff6688 !important; font-family: 'Rajdhani', sans-serif !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; font-size: 11px !important; }
[data-testid="stMetricValue"]    { color: #a0ffb8 !important; font-family: 'Rajdhani', sans-serif !important; font-size: 22px !important; font-weight: 600 !important; }

/* ── Tab styling ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #00ff6622 !important;
    gap: 4px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: #00ff6677 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 12px !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    border-radius: 6px 6px 0 0 !important;
    border: 1px solid transparent !important;
    padding: 6px 16px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #00ff66 !important;
    border-color: #00ff6633 !important;
    background: #00ff660d !important;
    box-shadow: 0 0 10px #00ff4420 !important;
}

/* ── Subheaders ── */
[data-testid="stMarkdownContainer"] h3,
.stSubheader {
    color: #a0ffb8 !important;
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 0.1em !important;
    font-size: 14px !important;
    text-transform: uppercase !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #00ff6622 !important;
    border-radius: 10px !important;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    background: #00ff660d !important;
    border: 1px solid #00ff6644 !important;
    border-radius: 8px !important;
    color: #00ff66 !important;
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 0.15em !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
}

/* ── Info / warning boxes ── */
[data-testid="stAlert"] {
    background: #041208 !important;
    border: 1px solid #00ff6622 !important;
    border-radius: 10px !important;
    color: #a0ffb8 !important;
    font-family: 'Rajdhani', sans-serif !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #00ff66 !important; }

</style>
""", unsafe_allow_html=True)

# =====================================================
# HERO BANNER
# =====================================================
st.markdown("""
<div class="hero">
  <div class="bolt-ring">
    <svg width="38" height="38" viewBox="0 0 38 38" fill="none">
      <polygon points="22,2 8,21 19,21 16,36 30,17 19,17"
        fill="#39ff14" stroke="#aaff77" stroke-width="1"
        style="filter:drop-shadow(0 0 8px #39ff14aa)"/>
    </svg>
  </div>
  <div style="flex:1">
    <div style="display:flex;align-items:flex-end;gap:4px;line-height:1">
      <span class="brand-name">PulseIQ</span>
      <svg width="140" height="40" viewBox="0 0 140 40" style="margin-bottom:6px">
        <polyline class="ecg-path" points="0,22 16,22 22,22 28,4 35,38 42,10 49,26 60,22 85,22"/>
        <line x1="85" y1="22" x2="140" y2="22" stroke="#00ff66" stroke-width="1.2" opacity="0.28"/>
      </svg>
    </div>
    <div class="subtitle">Live Open Interest Analytics Dashboard</div>
  </div>
  <div class="hero-divider"></div>
  <div>
    <div class="badge blv">Live</div>
    <div class="badge bnse">NSE · NFO</div>
  </div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# CONFIG
# =====================================================
TOKEN_FILE = "tokens/token.json"
os.makedirs("tokens", exist_ok=True)
initialize_database()
API_KEY    = st.secrets["API_KEY"]
API_SECRET = st.secrets["API_SECRET"]

# =====================================================
# SIDEBAR — BRAND STAMP
# =====================================================
st.sidebar.markdown("""
<div class="sb-brand">
  <span class="sb-dot"></span> PulseIQ
</div>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR — SETTINGS
# =====================================================
st.sidebar.markdown("### ⚙ Settings")

selected_index = st.sidebar.selectbox(
    "Select Index",
    ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"],
)

# Reset load state when index changes to prevent stale data / NoneType error
if "prev_index" not in st.session_state:
    st.session_state.prev_index = selected_index
if st.session_state.prev_index != selected_index:
    st.session_state.prev_index    = selected_index
    st.session_state.load_clicked  = False
    st.session_state.manual_strike = 0
    st.rerun()

range_choice = st.sidebar.selectbox(
    "ATM Strike Range",
    [f"ATM ± {i}" for i in range(1, 11)],
    index=4,
)
num_strikes = int(range_choice.split("±")[1].strip())

if "manual_strike" not in st.session_state:
    st.session_state.manual_strike = 0

manual_strike = st.sidebar.number_input(
    "Custom ATM Strike (0 = Auto)",
    value=st.session_state.manual_strike,
    step=50,
    key="manual_strike",
)

refresh_seconds = st.sidebar.selectbox(
    "Refresh Interval (sec)",
    [30, 60, 120, 180, 300],
    index=3,
)

alert_interval_minutes = st.sidebar.selectbox(
    "Telegram Alert Interval (min)",
    [1, 3, 5, 10, 15, 30],
    index=1,
)

# =====================================================
# GLOBAL AUTO REFRESH
# =====================================================

st_autorefresh(
    interval=10 * 1000,
    key="app_refresh"
)

st.sidebar.markdown("---")



if "load_clicked" not in st.session_state:
    st.session_state.load_clicked = False

if st.sidebar.button("⚡ Load Data", use_container_width=True):
    st.session_state.load_clicked = True

# =====================================================
# TOKEN FUNCTIONS
# =====================================================
def save_token(access_token):
    with open(TOKEN_FILE, "w") as f:
        json.dump({
            "access_token": access_token,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }, f, indent=4)

def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def get_kite():
    kite = KiteConnect(api_key=API_KEY)
    token_data = load_token()
    if token_data:
        kite.set_access_token(token_data["access_token"])
    return kite

def is_token_valid():
    try:
        token_data = load_token()
        if not token_data:
            return False, None
        if token_data["date"] != datetime.now().strftime("%Y-%m-%d"):
            return False, None
        kite = KiteConnect(api_key=API_KEY)
        kite.set_access_token(token_data["access_token"])
        profile = kite.profile()
        return True, profile
    except:
        return False, None

def authenticate_user(request_token):
    try:
        kite = KiteConnect(api_key=API_KEY)
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        access_token = data["access_token"]
        kite.set_access_token(access_token)
        profile = kite.profile()
        save_token(access_token)
        return True, profile
    except Exception as e:
        return False, str(e)

# =====================================================
# HEADER
# =====================================================
st.markdown(
    f"<p style='font-family:Rajdhani,sans-serif;font-size:13px;font-weight:600;"
    f"letter-spacing:0.2em;text-transform:uppercase;color:#00ff6688;margin:0 0 0.8rem;'>"
    f"⚡ {selected_index} — Options OI Dashboard</p>",
    unsafe_allow_html=True,
)

# =====================================================
# MARKET STATUS
# =====================================================
import pytz
_ist = pytz.timezone("Asia/Kolkata")
_now = datetime.now(_ist)
_weekday = _now.weekday()
_t = _now.time()
_market_open = (
    _weekday < 5 and
    _t >= datetime.strptime("09:15", "%H:%M").time() and
    _t <= datetime.strptime("15:30", "%H:%M").time()
)

if _market_open:
    components.html("""
    <link href="https://fonts.googleapis.com/css2?family=Radhani:wght@500;700;900&family=Rajdhani:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
    *{box-sizing:border-box;margin:0;padding:0}
    .market-bar{display:inline-flex;align-items:center;gap:18px;background:linear-gradient(135deg,#001a0a 0%,#00110a 100%);border:1px solid #00ff6633;border-radius:12px;padding:10px 20px;position:relative;overflow:hidden}
    .market-bar::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(to right,transparent,#00ff6666,transparent)}
    .live-dot{width:8px;height:8px;border-radius:50%;background:#00ff66;box-shadow:0 0 10px #00ff66;position:relative;animation:pd 1.5s ease-in-out infinite}
    .live-dot::after{content:'';position:absolute;inset:-4px;border-radius:50%;border:1px solid #00ff6644;animation:re 1.5s ease-out infinite}
    @keyframes pd{0%,100%{box-shadow:0 0 6px #00ff66}50%{box-shadow:0 0 16px #00ff66cc}}
    @keyframes re{0%{transform:scale(1);opacity:.8}100%{transform:scale(2.5);opacity:0}}
    .live-wrap{display:flex;align-items:center;gap:7px}
    .live-lbl{font-family:'Rajdhani',sans-serif;font-size:11px;font-weight:600;letter-spacing:.25em;text-transform:uppercase;color:#00ff66}
    .vdiv{width:1px;height:28px;background:linear-gradient(to bottom,transparent,#00ff6644,transparent)}
    .mkt-status{font-family:'Rajdhani',sans-serif;font-size:11px;font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:#00cc44}
    .clock-wrap{display:flex;align-items:baseline;gap:4px}
    .clock-time{font-family:'Radhani',monospace;font-size:14px;font-weight:700;color:#e8fff0;letter-spacing:.06em;text-shadow:0 0 14px #00ff6655;min-width:96px}
    .colon{color:#00ff66;animation:cb 1s step-end infinite}
    @keyframes cb{0%,100%{opacity:1}50%{opacity:.2}}
    .clock-ampm{font-family:'Rajdhani',sans-serif;font-size:11px;font-weight:600;letter-spacing:.15em;color:#39ff14}
    .clock-ist{font-family:'Rajdhani',sans-serif;font-size:10px;letter-spacing:.2em;color:#00ff6677;margin-left:2px}
    .nse-badge{font-family:'Rajdhani',sans-serif;font-size:10px;font-weight:600;letter-spacing:.14em;color:#00cc44;border:1px solid #00ff6633;background:#00ff660d;border-radius:5px;padding:2px 8px}
    .session-wrap{display:flex;flex-direction:column;gap:3px}
    .session-label{font-family:'Rajdhani',sans-serif;font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:#00ff6655}
    .session-bar{width:100px;height:4px;background:#00ff6618;border-radius:4px;overflow:hidden}
    .session-fill{height:100%;background:linear-gradient(to right,#00cc44,#39ff14);border-radius:4px;box-shadow:0 0 6px #00ff6666;transition:width 1s linear}
    </style>
    <div class="market-bar">
      <div class="live-wrap"><div class="live-dot"></div><span class="live-lbl">Live</span></div>
      <div class="vdiv"></div>
      <span class="mkt-status">Market Open</span>
      <div class="vdiv"></div>
      <div class="clock-wrap">
        <span class="clock-time" id="ct">--<span class="colon">:</span>--<span class="colon">:</span>--</span>
        <span class="clock-ampm" id="ap">--</span>
        <span class="clock-ist">IST</span>
      </div>
      <div class="vdiv"></div>
      <div class="session-wrap">
        <span class="session-label">Session</span>
        <div class="session-bar"><div class="session-fill" id="sf" style="width:0%"></div></div>
      </div>
      <div class="vdiv"></div>
      <span class="nse-badge">NSE · NFO</span>
    </div>
    <script>
    function tick(){
      const now=new Date();
      const ist=new Date(now.toLocaleString("en-US",{timeZone:"Asia/Kolkata"}));
      let h=ist.getHours(),m=ist.getMinutes(),s=ist.getSeconds();
      const ap=h>=12?"PM":"AM"; h=h%12||12;
      const p=n=>String(n).padStart(2,"0");
      document.getElementById("ct").innerHTML=`${p(h)}<span class="colon">:</span>${p(m)}<span class="colon">:</span>${p(s)}`;
      document.getElementById("ap").textContent=ap;
      const nowMin=ist.getHours()*60+ist.getMinutes()+ist.getSeconds()/60;
      const pct=Math.max(0,Math.min((nowMin-555)/375*100,100)).toFixed(2);
      document.getElementById("sf").style.width=pct+"%";
    }
    setInterval(tick,1000); tick();
    </script>
    """, height=60)
else:
    # Determine reason
    if _weekday >= 5:
        reason = "Weekend"
    elif _t < datetime.strptime("09:15", "%H:%M").time():
        reason = "Pre-Market"
    else:
        reason = "After Hours"

    st.markdown(f"""
    <div style="display:inline-flex;align-items:center;gap:8px;
                background:#1a0000;border:1px solid #ff444433;
                border-radius:8px;padding:5px 14px;margin-bottom:0.8rem;">
        <span style="width:8px;height:8px;border-radius:50%;background:#ff4444;
                     box-shadow:0 0 8px #ff4444;display:inline-block;"></span>
        <span style="font-family:'Rajdhani',sans-serif;font-size:12px;
                     letter-spacing:0.18em;color:#ff4444;text-transform:uppercase;">
            Market Closed
        </span>
        <span style="font-family:'Rajdhani',sans-serif;font-size:11px;
                     color:#ff444477;letter-spacing:0.1em;">
             {reason} · {_now.strftime("%I:%M:%S %p")} IST
        </span>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# LIVE INDEX PRICES TICKER
# =====================================================



MARKET_SYMBOLS = {
    "NIFTY":      "NSE:NIFTY 50",
    "BANKNIFTY":  "NSE:NIFTY BANK",
    "FINNIFTY":   "NSE:NIFTY FIN SERVICE",
    "MIDCPNIFTY": "NSE:NIFTY MID SELECT",
    "SENSEX":     "BSE:SENSEX",
    "BANKEX":     "BSE:BANKEX",
}

try:
    _kite         = get_kite()
    ticker_quotes = _kite.ltp(list(MARKET_SYMBOLS.values()))
    ticker_cols   = st.columns(6)

    for i, (name, symbol) in enumerate(MARKET_SYMBOLS.items()):
        price = ticker_quotes.get(symbol, {}).get("last_price", 0)
        # Highlight the currently selected index
        is_selected  = name == selected_index
        border_color = "#00ff66aa" if is_selected else "#00ff6630"
        glow         = "0 0 18px #00ff6633" if is_selected else "0 0 8px #00ff6610"
        name_color   = "#39ff14"   if is_selected else "#00ff66"

        with ticker_cols[i]:
            st.markdown(f"""
            <div style="background:#041208;border:1px solid {border_color};
                        border-radius:14px;padding:14px;text-align:center;
                        box-shadow:{glow};">
                <div style="color:{name_color};font-size:11px;letter-spacing:0.14em;
                            margin-bottom:7px;font-family:'Rajdhani',sans-serif;
                            text-transform:uppercase;">{name}</div>
                <div style="color:#eafff0;font-size:22px;font-weight:700;
                            font-family:'Rajdhani',sans-serif;">
                    {price:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)

except Exception:
    pass

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# =====================================================
# AUTH VALIDATION
# =====================================================
valid, profile = is_token_valid()

# =====================================================
# SIDEBAR — AUTH SECTION
# =====================================================
if not valid:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔐 Authentication")

    kite = KiteConnect(api_key=API_KEY)
    st.sidebar.link_button(
        "⚡ Open Kite Login",
        kite.login_url(),
        use_container_width=True,
    )

    request_token = st.sidebar.text_input(
        "Enter request_token",
        value=request_token if request_token else "",
        type="password",
        placeholder="Paste token here...",
    )

    if st.sidebar.button("Authenticate", use_container_width=True):
        if request_token.strip() == "":
            st.sidebar.error("Please enter request_token")
        else:
            success, result = authenticate_user(request_token)
            if success:
                st.sidebar.success(f"✅ {result['user_name']}")
                st.rerun()
            else:
                st.sidebar.error(result)

# =====================================================
# SIDEBAR — LOGGED IN STATE
# =====================================================
if valid:
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"<div style='font-family:Rajdhani,sans-serif;font-size:12px;"
        f"letter-spacing:0.12em;color:#00ff66;padding:4px 0;'>"
        f"<span style='color:#39ff14'>●</span> {profile['user_name']}</div>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Logout", use_container_width=True):
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        st.rerun()

# =====================================================
# MAIN DASHBOARD
# =====================================================

if valid and st.session_state.load_clicked:

    now_ts = datetime.now()

    last_fetch = st.session_state.get("last_fetch_time")

    should_fetch = (
        last_fetch is None or
        (now_ts - last_fetch).total_seconds() >= refresh_seconds
    )

    try:

        if should_fetch:

            kite = get_kite()

            @st.cache_data(ttl=3600)
            def get_instruments():
                return load_instruments(kite)

            instruments_df = get_instruments()

            with st.spinner("Fetching live option chain..."):

                option_df, spot_price, atm_strike, expiry = fetch_option_chain(
                    kite=kite,
                    instruments=instruments_df,
                    selected_index=selected_index,
                    strike_range=num_strikes,
                    custom_atm=manual_strike if manual_strike != 0 else 0,
                )

                total_ce_oi = option_df["CE_OI"].sum()
                total_pe_oi = option_df["PE_OI"].sum()

                total_pcr = round(
                    total_pe_oi / total_ce_oi,
                    2
                ) if total_ce_oi != 0 else 0

                live_data = {
                    "data": option_df,
                    "spot": spot_price,
                    "atm": atm_strike,
                    "expiry": expiry,
                    "total_ce_oi": total_ce_oi,
                    "total_pe_oi": total_pe_oi,
                    "total_pcr": total_pcr,
                    "timestamp": datetime.now(),
                }

                st.session_state.cached_live_data = live_data
                st.session_state.last_fetch_time = now_ts

        else:

            live_data = st.session_state.get("cached_live_data")

            if live_data is None:

                st.warning("Waiting for first live fetch...")

                st.stop()

            save_oi_snapshot(
            spot=float(live_data["spot"]),
            atm=float(live_data["atm"]),
            total_ce_oi=float(live_data["total_ce_oi"]),
            total_pe_oi=float(live_data["total_pe_oi"]),
            total_pcr=float(live_data["total_pcr"]),
            index_name=str(selected_index),
        )

        history_df = load_today_history(selected_index)
        full_history_df = load_full_history(selected_index)

        if history_df is None:
            history_df = pd.DataFrame()

        if full_history_df is None:
            full_history_df = pd.DataFrame()
        # =====================================================
        # AI SIGNAL
        # =====================================================

        signal_data = generate_ai_signal(
            spot_price=live_data["spot"],

            previous_spot=history_df["spot"].iloc[-2]
            if len(history_df) > 1
            else live_data["spot"],

            total_pcr=live_data["total_pcr"],

            total_ce_oi=live_data["total_ce_oi"],

            total_pe_oi=live_data["total_pe_oi"],

            atm_ce_volume=live_data["data"]["CE_VOLUME"].max(),

            atm_pe_volume=live_data["data"]["PE_VOLUME"].max(),
        )

        tab1, tab2 = st.tabs(
            ["📡 Live Dashboard", "📈 Historical Analytics"]
        )

        with tab1:

            metric1, metric2, metric3, metric4, metric5, metric6 = st.columns(6)

            metric1.metric(
                f"{selected_index} Spot",
                f"{live_data['spot']:,.2f}"
            )

            metric2.metric(
                "ATM",
                live_data["atm"]
            )

            metric3.metric(
                "PCR",
                live_data["total_pcr"]
            )

            metric4.metric(
                "CE OI",
                f"{round(live_data['total_ce_oi']/1e7, 2)} Cr"
            )

            metric5.metric(
                "PE OI",
                f"{round(live_data['total_pe_oi']/1e7, 2)} Cr"
            )

            # =====================================================
            # AI SIGNAL BOX
            # =====================================================

            st.markdown("---")

            st.subheader("🤖 AI Trade Signal")

            signal = signal_data["signal"]

            # =====================================================
                        # =====================================================
            # TELEGRAM ALERTS
            # =====================================================

            if "last_signal" not in st.session_state:

                st.session_state.last_signal = None

            last_alert_time = st.session_state.get("last_alert_time")

            alert_due = (
                last_alert_time is None or
                (datetime.now() - last_alert_time).total_seconds()
                >= alert_interval_minutes * 60
            )

            if (
                signal != st.session_state.last_signal
                and alert_due
            ):

                strike_col = None

                for col in live_data["data"].columns:

                    if col.upper() == "STRIKE":

                        strike_col = col
                        break

                if strike_col:

                    atm_row = live_data["data"][
                        live_data["data"][strike_col] == live_data["atm"]
                    ]

                else:

                    atm_row = pd.DataFrame()

                atm_ce_oi = (
                    atm_row["CE_OI"].iloc[0]
                    if not atm_row.empty else 0
                )

                atm_pe_oi = (
                    atm_row["PE_OI"].iloc[0]
                    if not atm_row.empty else 0
                )

                alert_message = f"""

🚀 PulseIQ Premium Signals

Index: {selected_index}

Signal: {signal}

ATM Strike: {live_data['atm']}

PCR: {live_data['total_pcr']}

Spot: {live_data['spot']:,.2f}

ATM CE OI: {round(atm_ce_oi/1e5, 2)} L

ATM PE OI: {round(atm_pe_oi/1e5, 2)} L

Time: {datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%I:%M:%S %p')} IST

"""

                send_telegram_alert(alert_message)

                st.session_state.last_signal = signal
                st.session_state.last_alert_time = datetime.now()

            confidence = signal_data["confidence"]

            if signal == "BUY CALL":

                st.success(
                    f"📈 {signal} | Confidence: {confidence}"
                )

            elif signal == "BUY PUT":

                st.error(
                    f"📉 {signal} | Confidence: {confidence}"
                )

            else:

                st.warning(
                    f"⚠️ {signal} | Confidence: {confidence}"
                )

            if (
                not history_df.empty
                and "spot" in history_df.columns
                and len(history_df) > 1
            ):

                open_price = history_df["spot"].iloc[0]

                live_price = live_data["spot"]

                price_delta = round(
                    live_price - open_price,
                    2
                )

                metric6.metric(
                    "Day Change",
                    f"{live_price:,.2f}",
                    delta=f"{price_delta:+.2f}"
                )

            else:

                metric6.metric(
                    "Day Change",
                    f"{live_data['spot']:,.2f}"
                )

            st.markdown("---")

            chart_col1, chart_col2 = st.columns([3, 1])

            with chart_col1:

                st.subheader("📈 Strike-wise OI")

                st.plotly_chart(
                    plot_oi_chart(
                        live_data["data"],
                        live_data["atm"]
                    ),
                    use_container_width=True,
                    key="live_oi_chart",
                )

            with chart_col2:

                st.subheader("📊 PCR")

                st.plotly_chart(
                    plot_pcr_gauge(
                        live_data["total_pcr"]
                    ),
                    use_container_width=True,
                    key="pcr_gauge_chart",
                )

            st.markdown("---")

            st.subheader("📋 Live Option Chain")

            st.dataframe(
                live_data["data"],
                use_container_width=True,
                hide_index=True,
                height=420,
            )

            st.markdown("---")

            st.subheader("📈 Today's OI Trend")

            st.plotly_chart(
                plot_total_oi_trend(history_df),
                use_container_width=True,
                key="today_trend_chart",
            )

        with tab2:

            st.subheader("📋 Historical Data")

            st.dataframe(
                full_history_df,
                use_container_width=True,
                hide_index=True,
                height=700,
            )

        st.markdown("---")

        # =====================================================
        # BUILD CSV
        # =====================================================

        df_csv = live_data["data"].copy()

        for col in df_csv.columns:

            if df_csv[col].dtype == object:

                df_csv[col] = df_csv[col].apply(
                    lambda x:
                    x.decode("latin-1", errors="ignore")
                    if isinstance(x, bytes)
                    else x
                )

        totals = {}

        for col in df_csv.columns:

            if df_csv[col].dtype in ["float64", "int64"]:

                totals[col] = df_csv[col].sum()

            else:

                totals[col] = "TOTAL"

        df_csv = pd.concat(
            [df_csv, pd.DataFrame([totals])],
            ignore_index=True
        )

        st.download_button(
            "⬇ Download Option Chain CSV",
            df_csv.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_index}_option_chain_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )

        st.caption(
            f"Last Updated: {live_data['timestamp'].strftime('%d-%b-%Y %H:%M:%S')}"
        )

    except Exception as e:
        st.error(f"Error: {e}")

elif not valid:
    st.warning("Please authenticate using Kite → use the sidebar")

else:
    st.info("Select settings and click '⚡ Load Data'")