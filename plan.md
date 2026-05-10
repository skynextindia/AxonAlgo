# 🚀 AxonAlgo: Institutional-Grade Trading Intelligence

AxonAlgo is a modular, high-frequency execution engine designed for MetaTrader 5. It leverages Smart Money Concepts (SMC), institutional supply/demand zones, and multi-timeframe confirmation to execute high-probability trades across Forex, Gold, and Crypto.

---

## 🏛️ System Architecture

### 1. Market Perception Engine (`sr_engine.py`)
*   **Institutional Zone Clustering**: Analyzes thousands of historical pivot points and clusters them into high-density "Demand" and "Supply" zones.
*   **Fair Value Gap (FVG) Detection**: Identifies institutional imbalances where price moved too fast, creating liquidity gaps that the market is likely to fill.
*   **Strength Scoring**: Each zone is scored based on "rejections" and "volume profile" to distinguish between weak retail levels and strong institutional barriers.

### 2. Execution Logic (`breakout_engine.py` & `candle_engine.py`)
*   **Momentum Validation**: Uses ATR (Average True Range) and Relative Volume to filter out fakeouts. A breakout is only valid if it occurs with high impulse.
*   **Psychological Confirmation**: Detects Candlestick patterns (Engulfing, Hammers, Shooting Stars) to ensure professional traders are entering the move.
*   **Dynamic Sensitivity**: Logic automatically adjusts for different assets (e.g., higher volatility in Gold vs. EURUSD).

### 3. Risk Intelligence Engine (`risk_engine.py`)
*   **Fixed Fractional Position Sizing**: Automatically calculates lot size based on a fixed percentage of account equity (default 1%).
*   **Institutional Reward-to-Risk (RR)**: Enforces a minimum 1.5 RR. If the target is too close or the stop is too wide, the trade is rejected.
*   **Trade Management**:
    *   **Auto-Break-even**: Moves Stop Loss to entry at 1.1 RR.
    *   **Trailing Stop**: Follows price movement using ATR-based volatility buffers to lock in profit.

---

## 🛡️ Operational Security & VPS Readiness

### 1. Market Safety Filters (`filter_engine.py`)
*   **Session Filtering**: Limits Forex/Gold trading to high-liquidity London/New York sessions.
*   **Spread Protection**: Blocks execution during "rollover" or news spikes where costs exceed profitable thresholds.
*   **Smart Crypto Support**: Automatically enables 24/7 execution for Crypto assets while keeping weekend blocks for traditional markets.

### 2. Remote Monitoring & Control
*   **Ultra-Pro Command Center**: A Flask-based, glassmorphic dashboard for real-time monitoring and parameter adjustment.
*   **Telegram Integration**: Real-time trade alerts, daily performance reports, and system heartbeat notifications.
*   **VPS Watchdog**: Auto-restart capability via `run_bot.bat` for persistent 24/7 operation.

---

## 📈 Current Portfolio Support
*   **Metals**: XAUUSD (Gold)
*   **Forex**: EURUSD, GBPJPY (and all majors)
*   **Crypto**: BTCUSD, ETHUSD (and all top-tier altcoins)

---

## 🛠️ Technical Stack
*   **Language**: Python 3.13+
*   **Terminal**: MetaTrader 5 (Official API)
*   **Database**: SQLite3 (Trade persistence and analytics)
*   **Web**: Flask + TailwindCSS (Admin Panel)
*   **Data Science**: Pandas, NumPy (Technical Analysis)

---

## 🚀 Roadmap (Future Upgrades)
- [ ] **Multi-Timeframe Correlation**: H1 trend alignment combined with M5 execution.
- [ ] **Sentiment AI**: Integration with MyFXBook/DailyFX retail sentiment data.
- [ ] **Deep Learning Score**: Using a neural net to provide a "Confidence Score" (0-100) for every signal.
- [ ] **Automated Backtesting**: A one-click suite to optimize settings for new assets.

---
*Created by @Rohan for Axon Algo Technologies*
