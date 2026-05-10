# 📂 AxonAlgo: Codebase & Architecture Map

This document details the file structure and module interactions of the AxonAlgo trading system.

---

## 🏗️ Folder Structure

```text
AxonAlgo/
├── main.py                 # Core Execution Loop
├── web_dashboard.py        # Admin Command Center (UI)
├── plan.md                 # Technical Blueprint
├── codebase.md             # Architecture Map (This file)
├── axon_bot.log            # Live System Logs
├── axon_trading.db         # SQLite Trade History
└── src/                    # System Core
    ├── config.py           # Global Parameters & Secrets
    ├── mt5_connection.py   # MetaTrader 5 Bridge
    ├── database.py         # Persistence Layer
    ├── executor.py         # Trade Placement & Management
    ├── notifier.py         # Telegram Notification Logic
    └── engines/            # Logic Modules
        ├── sr_engine.py       # Supply/Demand & FVG Detection
        ├── breakout_engine.py # Momentum & Breakout Validation
        ├── risk_engine.py     # Position Sizing & SL/TP Management
        ├── filter_engine.py   # Session & News Safety Checks
        ├── candle_engine.py   # Price Action Confirmation
        └── news_engine.py     # MT5 Calendar Integration
```

---

## 🔄 Core Data Flow

1.  **Ingestion**: `main.py` requests OHLC data from `mt5_connection.py`.
2.  **Perception**: `sr_engine.py` identifies institutional zones; `breakout_engine.py` checks for price penetration.
3.  **Filtration**: `filter_engine.py` cross-references the current time (UTC) and News Events via `news_engine.py`.
4.  **Confirmation**: `candle_engine.py` looks for Engulfing/Hammer patterns at the breakout point.
5.  **Risk Math**: `risk_engine.py` calculates the exact lot size based on account balance and zone distance.
6.  **Execution**: `executor.py` sends the encrypted order to MT5 and logs the entry to `database.py`.
7.  **Alerting**: `notifier.py` sends a formatted glassmorphic alert to the user's Telegram.

---

## 🧩 Module Breakdown

### `main.py`
The heartbeat of the system. It runs a non-blocking `while True` loop that cycles through the `SYMBOLS` list every 10 seconds. It coordinates all sub-engines.

### `src/engines/sr_engine.py`
Uses a clustering algorithm to find "Institutional Zones." It looks for price areas where the market previously "pivoted" with high volume.

### `src/engines/risk_engine.py`
The most critical safety module. It prevents "over-leveraging" by enforcing a strict 1% risk rule. It also handles the **Auto-Break-even** logic.

### `web_dashboard.py`
A Flask web application that reads from `config.py` and `database.py`. It uses TailwindCSS and Glassmorphism to provide a premium monitoring experience.

---

## 🛠️ Design Patterns
*   **Modular Engines**: Each engine is independent. You can swap the `breakout_engine` for a `mean_reversion_engine` without touching the rest of the code.
*   **Static Logic**: Utility engines (Filter, Candle) use `@staticmethod` for high-speed, memory-efficient processing.
*   **Singleton Bridge**: The `MT5Client` ensures only one connection is active to prevent terminal conflicts.

---
*Created by @Rohan for Axon Algo Technologies*
