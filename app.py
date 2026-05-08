import streamlit as st
import pandas as pd
import json
import os
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
    plot_spot_trend,
    )

from database import (
    initialize_database,
    save_oi_snapshot,
    load_today_history,
    load_full_history,
)

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

st_autorefresh(interval=refresh_seconds * 1000, key="nifty_refresh")

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

    try:
        kite = get_kite()

        @st.cache_data(ttl=3600)
        def get_instruments():
            return load_instruments(kite)

        instruments_df = get_instruments()

        with st.spinner("Fetching live option chain..."):
            live_data = fetch_option_chain(
                kite=kite,
                instruments_df=instruments_df,
                index_name=selected_index,
                num_strikes=num_strikes,
                manual_atm=manual_strike if manual_strike != 0 else None,
            )

        save_oi_snapshot(
            spot=live_data["spot"],
            atm=live_data["atm"],
            total_ce_oi=live_data["total_ce_oi"],
            total_pe_oi=live_data["total_pe_oi"],
            total_pcr=live_data["total_pcr"],
        )

        history_df      = load_today_history()
        full_history_df = load_full_history()

        tab1, tab2 = st.tabs(["📡 Live Dashboard", "📈 Historical Analytics"])

        with tab1:
            # ── 6 metric cards including live price change ──
            metric1, metric2, metric3, metric4, metric5, metric6 = st.columns(6)
            metric1.metric(f"{selected_index} Spot", f"{live_data['spot']:,.2f}")
            metric2.metric("ATM",   live_data["atm"])
            metric3.metric("PCR",   live_data["total_pcr"])
            metric4.metric("CE OI", f"{round(live_data['total_ce_oi']/1e7, 2)} Cr")
            metric5.metric("PE OI", f"{round(live_data['total_pe_oi']/1e7, 2)} Cr")

            # Live index price change from history
            if not history_df.empty and "spot" in history_df.columns and len(history_df) > 1:
                open_price  = history_df["spot"].iloc[0]
                live_price  = live_data["spot"]
                price_delta = round(live_price - open_price, 2)
                metric6.metric("Day Change", f"{live_price:,.2f}", delta=f"{price_delta:+.2f}")
            else:
                metric6.metric("Day Change", f"{live_data['spot']:,.2f}")

            st.markdown("---")
            chart_col1, chart_col2 = st.columns([3, 1])
            with chart_col1:
                st.subheader("📈 Strike-wise OI")
                st.plotly_chart(
                    plot_oi_chart(live_data["data"], live_data["atm"]),
                    use_container_width=True,
                    key="live_oi_chart",
                )
            with chart_col2:
                st.subheader("📊 PCR")
                st.plotly_chart(
                    plot_pcr_gauge(live_data["total_pcr"]),
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
            # Only Today's Trend — historical removed
            st.subheader("📈 Today's OI Trend")
            st.plotly_chart(
                plot_total_oi_trend(history_df,
    selected_index),
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

        # Build CSV with totals row appended
        df_csv = live_data["data"].copy()
        totals = {}
        for col in df_csv.columns:
            if df_csv[col].dtype in ["float64", "int64"]:
                totals[col] = df_csv[col].sum()
            else:
                totals[col] = "TOTAL"
        df_csv = pd.concat(
            [df_csv, pd.DataFrame([totals])], ignore_index=True
        )

        st.download_button(
            "⬇ Download Option Chain CSV",
            df_csv.to_csv(index=False),
            file_name=f"{selected_index}_option_chain_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )
        st.caption(
            f"Last Updated: {live_data['timestamp'].strftime('%d-%b-%Y %H:%M:%S')}"
        )

    except Exception as e:
        st.error(f"Error: {e}")

elif not valid:
    st.warning("Please authenticate using Kite →  use the sidebar")

else:
    st.info("Select settings and click '⚡ Load Data'")