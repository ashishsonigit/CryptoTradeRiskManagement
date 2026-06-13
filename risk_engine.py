# ================= risk_engine.py =================
import numpy as np
import pandas as pd


def compute_basic_perf(trades):
    """
    Compute core performance stats from a list of trade dicts.
    Expected keys per trade:
    - pnl
    - result ("Win" / "Loss")
    - balance_after
    """
    if len(trades) == 0:
        return {
            "winrate": 0.0,
            "loss_streak": 0,
            "max_drawdown": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
        }

    df = pd.DataFrame(trades)

    total_trades = len(df)
    wins = (df["result"] == "Win").sum()
    losses = (df["result"] == "Loss").sum()

    winrate = wins / total_trades * 100 if total_trades > 0 else 0.0

    # Loss streak
    loss_streak = 0
    current_streak = 0
    for res in df["result"]:
        if res == "Loss":
            current_streak += 1
            loss_streak = max(loss_streak, current_streak)
        else:
            current_streak = 0

    # Max drawdown from balance_after
    balances = df["balance_after"].tolist()
    peaks = np.maximum.accumulate(balances)
    drawdowns = (np.array(balances) - peaks) / peaks * 100
    max_drawdown = float(drawdowns.min()) if len(drawdowns) > 0 else 0.0

    # Expectancy
    avg_win = df.loc[df["result"] == "Win", "pnl"].mean() if wins > 0 else 0.0
    avg_loss = df.loc[df["result"] == "Loss", "pnl"].mean() if losses > 0 else 0.0
    lossrate = 1.0 - (winrate / 100.0)
    expectancy = (winrate / 100.0) * avg_win + lossrate * avg_loss

    # Profit factor
    gross_profit = df.loc[df["pnl"] > 0, "pnl"].sum()
    gross_loss = -df.loc[df["pnl"] < 0, "pnl"].sum()
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

    return {
        "winrate": float(winrate),
        "loss_streak": int(loss_streak),
        "max_drawdown": float(max_drawdown),
        "expectancy": float(expectancy),
        "profit_factor": float(profit_factor),
    }


def compute_adjustments(perf, trades, balance, base_risk=1.0):
    """
    Compute risk adjustments based on performance.
    Returns:
    - recommended_risk: base risk % from performance
    - drawdown_adj: multiplier based on max drawdown
    """
    winrate = perf["winrate"]
    max_dd = perf["max_drawdown"]
    loss_streak = perf["loss_streak"]

    # Base risk from winrate
    if winrate >= 60:
        recommended_risk = base_risk * 1.5
    elif winrate >= 50:
        recommended_risk = base_risk * 1.2
    elif winrate >= 40:
        recommended_risk = base_risk * 1.0
    else:
        recommended_risk = base_risk * 0.7

    # Drawdown adjustment
    if max_dd <= -5:
        drawdown_adj = 0.8
    elif max_dd <= -10:
        drawdown_adj = 0.6
    elif max_dd <= -20:
        drawdown_adj = 0.4
    else:
        drawdown_adj = 1.0

    # Loss streak soft cap
    if loss_streak >= 5:
        recommended_risk *= 0.7

    return {
        "recommended_risk": float(recommended_risk),
        "drawdown_adj": float(drawdown_adj),
        "max_drawdown": float(max_dd),
    }
