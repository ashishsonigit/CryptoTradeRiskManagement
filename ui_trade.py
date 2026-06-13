# ================= ui_trade.py =================
import streamlit as st
from datetime import datetime

from logic import get_price, plan_trade
from risk_engine import compute_basic_perf, compute_adjustments
from ui_components import (
    metric_with_explanation,
    inject_css,
    inject_layout_css,
)
from storage import save_trades


def render_trade_planning():
    inject_layout_css()
    inject_css()
    st.title("🧮 Trade Planning")

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
    # 1. TRADE INPUTS
    # ---------------------------------------------------------
    st.subheader("Trade Inputs")

    c1, c2, c3 = st.columns(3)
    with c1:
        direction = st.selectbox("Direction", ["Long", "Short"])
    with c2:
        rr = st.number_input("Reward/Risk (RR)", 0.5, 10.0, 2.0, 0.5)
    with c3:
        symbol = st.text_input("Symbol", "BTCUSDT").upper()

    c4, c5, c6 = st.columns(3)
    with c4:
        fee_pct = st.number_input("Fee % per side", 0.0, 1.0, 0.06, 0.01)
    with c5:
        stop_distance = st.number_input("Stop Distance (USD)", 1.0, 10000.0, 350.0, 1.0)
    with c6:
        if st.button("Refresh Price"):
            st.session_state[f"price_{symbol}"] = get_price(symbol)

        raw_price = st.session_state.get(f"price_{symbol}", get_price(symbol))
        price = st.number_input("Price", value=float(raw_price), format="%.2f")

    # ---------------------------------------------------------
    # 2. FINAL RISK CALCULATION
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

    st.subheader("Final Risk Calculation")

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
        final_risk_pct = tp_risk_input * regime_mult_input
        metric_with_explanation(
            "Final Risk %",
            f"{final_risk_pct:.2f}%",
            "Final risk % used for position sizing."
        )

    # ---------------------------------------------------------
    # 3. PLAN TRADE (PREVIEW)
    # ---------------------------------------------------------
    st.subheader("Plan Trade (Preview)")

    risk_amount = balance * (final_risk_pct / 100.0)
    units = risk_amount / stop_distance if stop_distance > 0 else 0.0

    if direction == "Long":
        stop_price = price - stop_distance
        target_price = price + rr * stop_distance
    else:
        stop_price = price + stop_distance
        target_price = price - rr * stop_distance

    notional_entry = abs(price * units)
    notional_exit = abs(target_price * units)
    total_fee = (notional_entry + notional_exit) * (fee_pct / 100.0)

    breakeven_price = (
        price + total_fee / units if direction == "Long" else price - total_fee / units
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entry", f"{price:.2f}")
    c2.metric("Stop Loss", f"{stop_price:.2f}")
    c3.metric("Breakeven", f"{breakeven_price:.2f}")
    c4.metric("Units", f"{units:,.4f}")

    # ---------------------------------------------------------
    # 4. ACTUAL TRADE (STATEFUL INPUTS)
    # ---------------------------------------------------------
    st.subheader("Actual Trade")

    # Initialize persistent fields
    if "actual_entry" not in st.session_state:
        st.session_state.actual_entry = float(price)
    if "actual_exit" not in st.session_state:
        st.session_state.actual_exit = float(target_price)
    if "actual_units" not in st.session_state:
        st.session_state.actual_units = float(units)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        exchange = st.text_input("Exchange", "Nexo")

    with c2:
        actual_entry = st.number_input(
            "Actual Entry",
            key="actual_entry",
            format="%.2f",
        )

    with c3:
        actual_exit = st.number_input(
            "Actual Exit",
            key="actual_exit",
            format="%.2f",
        )

    with c4:
        actual_units = st.number_input(
            "Units",
            key="actual_units",
            format="%.4f",
        )

    # ---------------------------------------------------------
    # 5. RECORD TRADE
    # ---------------------------------------------------------
    if st.button("Record Trade"):
        trade = plan_trade(
            symbol=symbol,
            direction=direction,
            entry_price=actual_entry,
            stop_price=stop_price,
            target_price=actual_exit,
            units=actual_units,
            fee_pct=fee_pct,
            rr=rr,
            final_risk_pct=final_risk_pct,
        )

        pnl = trade["pnl"]
        balance_after = balance + pnl
        st.session_state.balance = balance_after
        trade["balance_after"] = balance_after

        st.session_state.trades.append(trade)
        save_trades(st.session_state.trades)

        st.success("Trade recorded successfully.")

        st.markdown("### Trade Summary")

        summary_rows = [
            ("Date", trade["date"]),
            ("Time", trade["time"]),
            ("Symbol", symbol),
            ("Direction", direction),
            ("Exchange", exchange),
            ("Actual Entry", f"{actual_entry:.2f}"),
            ("Actual Exit", f"{actual_exit:.2f}"),
            ("Units", f"{actual_units:,.4f}"),
            ("PnL", f"{pnl:.2f}"),
            ("Trading Fees", f"{trade['total_fee']:.2f}"),
            ("Actual RR", f"{trade['actual_rr']:.2f}"),
            ("Result", trade["result"]),
            ("Updated Balance", f"{balance_after:.2f}"),
        ]

        table_html = "<table class='summary-table'>"
        for label, value in summary_rows:
            table_html += f"<tr><th>{label}</th><td>{value}</td></tr>"
        table_html += "</table>"

        st.markdown(table_html, unsafe_allow_html=True)
