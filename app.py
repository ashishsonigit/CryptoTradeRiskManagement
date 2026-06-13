# ================= app.py =================
import streamlit as st

from ui_trade import render_trade_planning
from ui_perf import render_performance_dashboard
from ui_regime import render_regime_ui
from ui_history import render_history_ui
from ui_docs import render_docs_ui
from storage import load_trades, save_trades


# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "trades" not in st.session_state:
    st.session_state.trades = load_trades()

if "balance" not in st.session_state:
    if len(st.session_state.trades) > 0:
        st.session_state.balance = st.session_state.trades[-1].get("balance_after", 10_000.0)
    else:
        st.session_state.balance = 10_000.0

if "regime" not in st.session_state:
    st.session_state.regime = None


# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.title("📊 Trade Planner 3.0")

page = st.sidebar.radio(
    "Navigation",
    [
        "Trade Planner",
        "Performance Dashboard",
        "Market Regime",
        "Trade History",
        "Documentation",
    ]
)


# ---------------------------------------------------------
# PAGE ROUTING
# ---------------------------------------------------------
if page == "Trade Planner":
    render_trade_planning()

elif page == "Performance Dashboard":
    from risk_engine import compute_basic_perf
    perf = compute_basic_perf(st.session_state.trades)
    render_performance_dashboard(st.session_state, perf)

elif page == "Market Regime":
    render_regime_ui(st.session_state.regime)

elif page == "Trade History":
    render_history_ui(st.session_state)

elif page == "Documentation":
    render_docs_ui()
