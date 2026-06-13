# ================= ui_perf.py =================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from ui_components import (
    metric_with_explanation,
    inject_css,
    inject_layout_css,
)


def render_performance_dashboard(state, perf):
    inject_layout_css()
    inject_css()
    st.title("📈 Performance Dashboard")

    trades = state["trades"]

    if len(trades) == 0:
        st.info("No trades recorded yet.")
        return

    df = pd.DataFrame(trades)
    df["trade_num"] = df.index + 1

    # ---------------------------------------------------------
    # 1. SUMMARY METRICS
    # ---------------------------------------------------------
    st.subheader("1. Core Performance Metrics")

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        metric_with_explanation("Winrate", f"{perf['winrate']:.1f}%", "Percentage of profitable trades.")
    with c2:
        metric_with_explanation("Max Drawdown", f"{perf['max_drawdown']:.2f}%", "Largest equity decline.")
    with c3:
        metric_with_explanation("Loss Streak", perf["loss_streak"], "Longest losing streak.")
    with c4:
        metric_with_explanation("Total Trades", len(df), "Total number of trades.")
    with c5:
        metric_with_explanation("Expectancy", f"{perf['expectancy']:.2f}", "Expected PnL per trade.")
    with c6:
        metric_with_explanation("Profit Factor", f"{perf['profit_factor']:.2f}", "Gross profit / gross loss.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 1B. RECOMMENDED RISK % (CLEAN, ALIGNED, WITH ARROW + EXPLANATIONS)
    # ---------------------------------------------------------
    st.subheader("How Recommended Risk % Was Calculated")

    base_risk = perf.get("base_risk", 1.0)
    winrate_adj = perf.get("winrate_adj", 0.0)
    loss_streak_adj = perf.get("loss_streak_adj", 0.0)
    pnl_trend_adj = perf.get("pnl_trend_adj", 0.0)
    drawdown_adj = perf.get("drawdown_adj", 1.0)
    recommended_risk = perf.get("recommended_risk", base_risk)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Base Risk %", f"{base_risk:.2f}%")
    c2.metric("Winrate Adj", f"{winrate_adj:+.2f}%")
    c3.metric("Loss Streak Adj", f"{loss_streak_adj:+.2f}%")
    c4.metric("PnL Trend Adj", f"{pnl_trend_adj:+.2f}%")
    c5.metric("Drawdown Multiplier", f"{drawdown_adj:.2f}×")
    c6.metric("Recommended Risk %", f"{recommended_risk:.2f}%")

    # ARROW
    st.markdown(
        """
        <div style="text-align:center; font-size:32px; color:#000000; margin-top:-10px;">
            ↓
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ATTRIBUTE EXPLANATIONS
    st.markdown(
        f"""
        <div style="color:#000000; font-size:15px; margin-top:10px;">
            <b>Base Risk %</b> — Your default risk per trade.<br>
            <b>Winrate Adj</b> — Adjusts risk based on recent winrate.<br>
            <b>Loss Streak Adj</b> — Reduces risk during losing streaks.<br>
            <b>PnL Trend Adj</b> — Adjusts risk based on recent PnL momentum.<br>
            <b>Drawdown Multiplier</b> — Scales risk down when in drawdown.<br>
            <b>Recommended Risk %</b> — Final dynamic risk % after all adjustments.<br>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # FORMULA (BIGGER + BLACK)
    st.markdown(
        """
        <div style="color:#000000; font-weight:700; font-size:20px; margin-top:15px;">
            Formula
        </div>

        <div style="color:#000000; font-size:22px; font-weight:600; margin-top:5px;">
            Recommended Risk % = (Base Risk + Winrate Adj + Loss Streak Adj + PnL Trend Adj) × Drawdown Multiplier
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ---------------------------------------------------------
    # 2. EQUITY CURVE
    # ---------------------------------------------------------
    df["equity"] = df["balance_after"]
    fig_equity = px.line(df, x="trade_num", y="equity", title="Equity Curve", markers=True)
    st.plotly_chart(fig_equity, use_container_width=True)

    st.markdown("**What this shows**\n\nTracks your account balance after each trade.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 3. DRAWDOWN CURVE
    # ---------------------------------------------------------
    balances = df["balance_after"].tolist()
    peaks = np.maximum.accumulate(balances)
    df["drawdown"] = (df["balance_after"] - peaks) / peaks * 100

    fig_dd = px.line(df, x="trade_num", y="drawdown", title="Drawdown Curve")
    st.plotly_chart(fig_dd, use_container_width=True)

    st.markdown("**What this shows**\n\nShows how far you are from your equity peak.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 4. ROLLING WINRATE
    # ---------------------------------------------------------
    df["rolling_winrate"] = (
        df["result"].map(lambda x: 1 if x == "Win" else 0).rolling(20).mean() * 100
    )

    fig_rw = px.line(df, x="trade_num", y="rolling_winrate", title="Rolling Winrate (20 Trades)")
    st.plotly_chart(fig_rw, use_container_width=True)

    st.markdown("**What this shows**\n\nReveals edge stability over time.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 5. RR DISTRIBUTION
    # ---------------------------------------------------------
    fig_rr = px.histogram(df, x="actual_rr", nbins=30, title="RR Distribution")
    st.plotly_chart(fig_rr, use_container_width=True)

    st.markdown("**What this shows**\n\nDistribution of your R-multiples.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 6. EXPECTANCY OVER TIME
    # ---------------------------------------------------------
    df["cum_pnl"] = df["pnl"].cumsum()
    df["avg_pnl"] = df["cum_pnl"] / (df.index + 1)

    fig_exp = px.line(df, x="trade_num", y="avg_pnl", title="Expectancy Over Time")
    st.plotly_chart(fig_exp, use_container_width=True)

    st.markdown("**What this shows**\n\nAverage PnL per trade over time.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 7. PERFORMANCE HEATMAP
    # ---------------------------------------------------------
    dt = pd.to_datetime(df["date"] + " " + df["time"])
    df["weekday"] = dt.dt.day_name()
    df["hour"] = dt.dt.hour

    pivot = df.pivot_table(index="weekday", columns="hour", values="pnl", aggfunc="mean")

    fig_hm = px.imshow(pivot, aspect="auto", color_continuous_scale="RdYlGn", title="PnL Heatmap")
    st.plotly_chart(fig_hm, use_container_width=True)

    st.markdown("**What this shows**\n\nWhen you trade best.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 8. DRAWDOWN HEATMAP
    # ---------------------------------------------------------
    heat_matrix = np.array([df["drawdown"].values])

    fig_dd_heat = px.imshow(
        heat_matrix,
        aspect="auto",
        color_continuous_scale="RdYlGn_r",
        title="Drawdown Heatmap"
    )

    fig_dd_heat.update_xaxes(
        tickmode="array",
        tickvals=list(range(len(df))),
        ticktext=list(df["trade_num"])
    )
    fig_dd_heat.update_yaxes(showticklabels=False)

    st.plotly_chart(fig_dd_heat, use_container_width=True)

    st.markdown("**What this shows**\n\nHighlights clusters of stress periods.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 9. TRADE SEQUENCE SCATTER
    # ---------------------------------------------------------
    fig_scatter = px.scatter(
        df,
        x="trade_num",
        y="pnl",
        color=df["result"].map({"Win": "green", "Loss": "red"}),
        title="Trade Sequence Scatter Plot"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("**What this shows**\n\nReveals streaks, volatility, and behavior patterns.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 10. PNL BAR CHART
    # ---------------------------------------------------------
    df["color"] = df["pnl"].apply(lambda x: "green" if x >= 0 else "red")

    fig_pnl = px.bar(
        df,
        x="trade_num",
        y="pnl",
        color="color",
        title="PnL per Trade",
        color_discrete_map={"green": "green", "red": "red"},
    )
    fig_pnl.update_layout(showlegend=False)

    st.plotly_chart(fig_pnl, use_container_width=True)

    st.markdown("**What this shows**\n\nGreen = wins or breakeven, red = losses.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 11. TRADE TABLE
    # ---------------------------------------------------------
    st.subheader("11. Trade History Snapshot")

    def color_rows(row):
        if row["pnl"] < 0:
            return ['background-color: #ffcccc'] * len(row)
        else:
            return ['background-color: #ccffcc'] * len(row)

    styled_df = df.style.apply(color_rows, axis=1)

    st.dataframe(styled_df, use_container_width=True)
