# ================= tests/test_smoke.py =================
def test_imports():
    import app
    import logic
    import risk_engine
    import ui_trade
    import ui_perf
    import ui_regime
    import ui_history
    import ui_docs


def test_risk_engine_basic():
    from risk_engine import compute_basic_perf, compute_adjustments

    trades = [
        {"result": "Win", "balance_after": 10100},
        {"result": "Loss", "balance_after": 10050},
    ]
    perf = compute_basic_perf(trades)
    adj = compute_adjustments(perf, trades, balance=10000, base_risk=1.0)
    assert "recommended_risk" in adj
