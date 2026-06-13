# ================= storage.py =================
import json
import os

FILE_PATH = "trade_history.json"


def load_trades():
    """Load trades from disk if file exists."""
    if not os.path.exists(FILE_PATH):
        return []
    try:
        with open(FILE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_trades(trades):
    """Save trades to disk."""
    try:
        with open(FILE_PATH, "w") as f:
            json.dump(trades, f, indent=4)
    except Exception as e:
        print("Error saving trades:", e)
