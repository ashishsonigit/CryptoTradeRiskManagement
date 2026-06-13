# ================= ui_history.py =================
import streamlit as st
import pandas as pd
from ui_components import inject_css, inject_layout_css
from storage import save_trades


def render_history_ui(state):
    inject_layout_css()
    inject_css()
    st.title("📜 Trade History")

    trades = state["trades"]

    if len(trades) == 0:
        st.info("No trades recorded yet.")
        return

    df = pd.DataFrame(trades)

    # Ensure exchange column exists even if older trades didn't have it
    if "exchange" not in df.columns:
        df["exchange"] = ""

    st.subheader("Summary Metrics")

    total_trades = len(df)
    wins = (df["pnl"] > 0).sum()
    winrate = wins / total_trades * 100
    avg_rr = df["actual_rr"].mean() if "actual_rr" in df.columns else 0.0
    avg_pnl = df["pnl"].mean()
    total_pnl = df["pnl"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Trades", total_trades)
    c2.metric("Winrate", f"{winrate:.1f}%")
    c3.metric("Avg RR", f"{avg_rr:.2f}")
    c4.metric("Avg PnL", f"{avg_pnl:.2f}")
    c5.metric("Total PnL", f"{total_pnl:.2f}")

    st.markdown("---")

    st.subheader("Trade Table")

    def color_rows(row):
        if row["pnl"] < 0:
            return ['background-color: #ffcccc'] * len(row)
        else:
            return ['background-color: #ccffcc'] * len(row)

    styled_df = df.style.apply(color_rows, axis=1)

    st.dataframe(styled_df, use_container_width=True)

    st.markdown("---")

    if st.button("Reset All Trade History"):
        state["trades"].clear()
        save_trades(state["trades"])
        st.success("Trade history cleared.")
        st.experimental_rerun()
