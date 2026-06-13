# ================= ui_trade.py =================
import streamlit as st
from datetime import datetime

from logic import get_price, plan_trade
from risk_engine import compute_basic_perf, compute_adjustments
from ui_components import inject_css, inject_layout_css
from storage import save_trades


# ---------------------------------------------------------
# GLOBAL CSS FOR UNIFIED FONT SIZES + FLAT INPUTS
# ---------------------------------------------------------
FLAT_INPUT_CSS = """
<style>

.trade-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 15px;
}
.trade-table th {
    text-align: left;
    padding: 6px 10px;
    font-weight: 600;
    font-size: 16px;
}
.trade-table td {
    padding: 6px 10px;
    font-size: 15px;
}
.section-title {
    font-size: 20px !important;
    font-weight: 700 !important;
    margin-top: 20px;
}

/* Make st.metric values same size as number inputs */
[data-testid="stMetricValue"] {
    font-size: 15px !important;
    font-weight: 600 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 15px !important;
}

/* Remove borders from text_input and number_input */
input[type="text"], input[type="number"] {
    border: none !important;
    box-shadow: none !important;
    background-color: transparent !important;
    outline: none !important;
}

/* Remove border on focus */
input[type="text"]:focus, input[type="number"]:focus {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Remove borders from selectbox outer container */
div[data-baseweb="select"] > div {
    border: none !important;
    box-shadow: none !important;
    background-color: transparent !important;
}

/* Remove borders from selectbox internal control */
div[data-baseweb="select"] div {
    border: none !important;
    box-shadow: none !important;
    background-color: transparent !important;
}

/* Remove border highlight when selectbox is focused */
div[data-baseweb="select"]:focus-within {
    border: none !important;
    box-shadow: none !important;
}

/* Remove borders from number_input wrapper */
div[data-testid="stNumberInput"] > div {
    border: none !important;
    box-shadow: none !important;
    background-color: transparent !important;
}

/* Remove borders from text_input wrapper */
div[data-testid="stTextInput"] > div {
    border: none !important;
    box-shadow: none !important;
    background-color: transparent !important;
}

</style>
"""


def render_trade_planning():
    inject_layout_css()
    inject_css()
    st.markdown(FLAT_INPUT_CSS, unsafe_allow_html=True)

    st.markdown("<div class='section-title'>🧮 Trade Planning</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # SESSION STATE
    # ---------------------------------------------------------
    if "trades" not in st.session_state:
        st.session_state.trades = []
    if "balance" not in st.session_state:
        st.session_state.balance = 10000.0

    trades = st.session_state.trades
    balance = st.session_state.balance

    # ---------------------------------------------------------
    # 1. TRADE INPUTS (AESTHETIC LAYOUT)
    # ---------------------------------------------------------
    st.markdown("<div class='section-title'>Trade Inputs</div>", unsafe_allow_html=True)

    row1 = st.columns(4)
    with row1[0]:
        direction = st.selectbox("Direction", ["Long", "Short"])
    with row1[1]:
        symbol = st.text_input("Symbol", "BTCUSDT").upper()
    with row1[2]:
        exchange = st.text_input("Crypto Exchange", "Binance")
    with row1[3]:
        rr = st.number_input("Reward/Risk (RR)", 0.5, 10.0, 2.0, 0.5)

    row2 = st.columns([1, 1, 1, 0.5])
    with row2[0]:
        fee_pct = st.number_input("Fee % per side", 0.0, 1.0, 0.06, 0.01)
    with row2[1]:
        stop_distance = st.number_input("Stop Distance (USD)", 1.0, 10000.0, 350.0, 1.0)

    # PRICE + REFRESH BUTTON IN SAME ROW
    with row2[2]:
        raw_price = st.session_state.get(f"price_{symbol}", get_price(symbol))
        price = st.number_input("Price", value=float(raw_price), format="%.2f")

    with row2[3]:
        if st.button("↻"):
            new_price = get_price(symbol)
            st.session_state[f"price_{symbol}"] = new_price
            st.session_state.planned_entry = float(new_price)  # AUTO‑UPDATE PLANNED ENTRY
            st.rerun()

    # ---------------------------------------------------------
    # 2. ACCEPTABLE RISK CALCULATION
    # ---------------------------------------------------------
    perf_stats = compute_basic_perf(trades)
    adj = compute_adjustments(
        perf=perf_stats,
        trades=trades,
        balance=balance,
        base_risk=1.0,
    )

    recommended_risk = adj["recommended_risk"]
    drawdown_adj = adj["drawdown_adj"]
    trade_perf_risk = recommended_risk * drawdown_adj

    st.markdown("<div class='section-title'>Acceptable Risk</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        tp_risk_input = st.number_input(
            "Trade Performance Risk %",
            min_value=0.0,
            max_value=10.0,
            value=float(trade_perf_risk),
            step=0.05,
            format="%.2f",
        )

    with c2:
        regime_mult_input = st.number_input(
            "Regime Multiplier",
            min_value=0.1,
            max_value=3.0,
            value=1.0,
            step=0.05,
            format="%.2f",
        )

    with c3:
        acceptable_risk_pct = tp_risk_input * regime_mult_input
        st.metric("Acceptable Risk %", f"{acceptable_risk_pct:.2f}%")

    # ---------------------------------------------------------
    # 3. PLANNED TRADE (CONFIGURABLE ENTRY/EXIT)
    # ---------------------------------------------------------
    st.markdown("<div class='section-title'>Planned Trade</div>", unsafe_allow_html=True)

    # Planned Entry defaults to Price but remains editable
    if "planned_entry" not in st.session_state:
        st.session_state.planned_entry = float(price)
    if "planned_exit" not in st.session_state:
        st.session_state.planned_exit = float(price + rr * stop_distance)

    ce1, ce2 = st.columns(2)
    with ce1:
        planned_entry = st.number_input("Planned Entry", key="planned_entry", format="%.2f")
    with ce2:
        planned_exit = st.number_input("Planned Exit", key="planned_exit", format="%.2f")

    # Recompute dependent values
    risk_amount = balance * (acceptable_risk_pct / 100.0)
    units = risk_amount / stop_distance if stop_distance > 0 else 0.0

    if direction == "Long":
        stop_price = planned_entry - stop_distance
        gross_pnl = (planned_exit - planned_entry) * units
    else:
        stop_price = planned_entry + stop_distance
        gross_pnl = (planned_entry - planned_exit) * units

    notional_entry = abs(planned_entry * units)
    notional_exit = abs(planned_exit * units)
    total_fee = (notional_entry + notional_exit) * (fee_pct / 100.0)

    breakeven_price = (
        planned_entry + total_fee / units if direction == "Long"
        else planned_entry - total_fee / units
    )

    net_pnl = gross_pnl - total_fee
    pnl_color = "#00aa00" if net_pnl >= 0 else "#cc0000"

    planned_row = f"""
    <table class='trade-table'>
        <tr>
            <th>Symbol</th><th>Direction</th><th>Exchange</th><th>Risk %</th>
            <th>Units</th><th>Entry</th><th>Exit</th>
            <th>Breakeven</th><th>Stop Loss Price</th><th>Stop Loss Distance</th>
            <th>Trading Fee</th><th>PnL</th>
        </tr>
        <tr>
            <td>{symbol}</td>
            <td>{direction}</td>
            <td>{exchange}</td>
            <td>{acceptable_risk_pct:.2f}%</td>
            <td>{units:,.4f}</td>
            <td>{planned_entry:.2f}</td>
            <td>{planned_exit:.2f}</td>
            <td>{breakeven_price:.2f}</td>
            <td>{stop_price:.2f}</td>
            <td>{stop_distance:.2f}</td>
            <td>{total_fee:.2f}</td>
            <td style="color:{pnl_color}; font-weight:600;">{net_pnl:.2f}</td>
        </tr>
    </table>
    """

    st.markdown(planned_row, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 4. RECORD TRADE (NO TABLE SHOWN AFTER)
    # ---------------------------------------------------------
    if st.button("Record Trade"):
        trade = plan_trade(
            symbol=symbol,
            direction=direction,
            entry_price=planned_entry,
            stop_price=stop_price,
            target_price=planned_exit,
            units=units,
            fee_pct=fee_pct,
            rr=rr,
            final_risk_pct=acceptable_risk_pct,
        )

        trade["exchange"] = exchange

        pnl = trade["pnl"]
        balance_after = balance + pnl
        st.session_state.balance = balance_after
        trade["balance_after"] = balance_after

        st.session_state.trades.append(trade)
        save_trades(st.session_state.trades)

        st.success("Trade recorded successfully.")
