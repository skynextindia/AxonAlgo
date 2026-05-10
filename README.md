# AxonAlgo 🚀
**Professional Institutional-Grade MT5 Breakout Trading Bot**

AxonAlgo is a high-performance algorithmic trading system built for MetaTrader 5. It specializes in detecting high-momentum breakouts from institutional Support and Resistance zones using a multi-layer confirmation stack.

## 🧠 Core Engines
- **S/R Zone Engine**: Clusters fractal highs/lows into supply/demand zones.
- **Breakout Validator**: Confirms momentum using Relative Volume and ATR expansion.
- **MTF Trend Filter**: Validates trades against the H4 200-period EMA.
- **Candlestick Psychology**: Detects Engulfing, Hammer, and Shooting Star patterns.
- **Risk Engine**: Dynamic SL/TP based on market structure with 1% fixed fractional risk.
- **Position Manager**: Automated Trailing Stop to lock in profits.

## 🚀 Setup & Installation
1. Clone the repo: `git clone https://github.com/skynextindia/AxonAlgo.git`
2. Install requirements: `pip install -r requirements.txt`
3. Configure your `.env` (Rename `.env.example` to `.env`)
4. Run the bot: `python main.py`

## ⚠️ Safety Disclaimer
Trading involves significant risk. This bot is provided for educational purposes. Always test in a Demo account before going live.
