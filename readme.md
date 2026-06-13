# TradePlanner 2.0 📈

A full-stack trading workflow app built with **Streamlit**, combining:

- 🧮 Trade Planning  
- 📈 Performance Analytics  
- 🌐 Market Regime Engine  
- 📜 Trade History  
- 📚 Documentation  

---

## Features

### 🧮 Trade Planning
- Direction, RR, symbol, stop distance, fees
- Live price fetch (`get_price`)
- Risk engine–driven position sizing
- Auto-calculated:
  - Entry, stop, target
  - Units
  - Risk amount
  - Final risk %

### 📈 Performance Dashboard
- Winrate, loss streak, max drawdown
- Expectancy, profit factor, average RR
- Equity curve
- Drawdown curve
- Rolling winrate (20-trade window)
- RR distribution
- Weekday × hour performance heatmap
- Risk evolution (baseline vs recommended vs final)
- Market intelligence snapshot:
  - Fear & Greed
  - LunarCrush sentiment
  - ETF flows
  - TradingView indicators
  - Whale activity
  - Exchange flows
  - News event risk

### 🌐 Market Regime Engine
- Trend, volatility, breadth, liquidity, macro scores
- Market risk score
- Risk mode (Hostile → Aggressive)
- Regime multiplier
- Raw JSON view + explanation

### 📜 Trade History
- Filters: symbol, direction, result, date range
- Free-text search
- Sorting by any column
- Pagination
- CSV export
- Color-coded rows (Win/Loss)
- Summary metrics

### 📚 Documentation
- In-app documentation for:
  - Trade Planning
  - Performance Dashboard
  - Market Regime Engine
  - Trade History
  - Risk Engine
  - Architecture overview

---

## Project Structure

```text
TradePlanner-2.0/
├── app.py                # Main entry, routing, sidebar
├── logic.py              # Price fetch, trade planning, market intel
├── risk_engine.py        # Perf stats, drawdown, recommended risk
├── ui_trade.py           # Trade Planning page
├── ui_perf.py            # Performance Dashboard
├── ui_regime.py          # Market Regime Dashboard
├── ui_history.py         # Trade History page
├── ui_docs.py            # Documentation page
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── architecture.md       # Detailed architecture notes
└── data/                 # Optional data/cache
