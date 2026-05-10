# 🎮 AxonAlgo: Master Command Center

This is the definitive guide for operating and managing the AxonAlgo institutional trading system.

---

## ⚡ Quick Start Commands

| Action | Command |
| :--- | :--- |
| **Start Trading Bot** | `python main.py` |
| **Start Admin Panel** | `python web_dashboard.py` |
| **Update Dependencies** | `pip install -r requirements.txt` |
| **Upgrade MT5 Library** | `python -m pip install --upgrade MetaTrader5` |
| **Check Active Logs** | `Get-Content axon_bot.log -Wait` |
| **Reset Database** | `Remove-Item axon_trading.db` |

---

## 🏛️ System Core Architecture

*   **Logic Engine**: Supply/Demand (S/R) + Fair Value Gaps (FVG) + Momentum Breakouts.
*   **Safety Layer**: 1% Fixed Risk + Auto-Break-even + Institutional Session Filtering.
*   **Asset Support**: Forex, Gold, and 24/7 Crypto support.
*   **UI**: Ultra-Premium Glassmorphism Admin Dashboard (Port 5000).

---

## 🛠️ Configuration Checklist (`src/config.py`)

1.  [ ] **SYMBOLS**: List of assets to scan (e.g., `["XAUUSDm", "BTCUSDm"]`).
2.  [ ] **RISK_PER_TRADE**: Default equity risk (e.g., `0.01` for 1%).
3.  [ ] **ADMIN_PASSWORD**: Your secure dashboard login.
4.  [ ] **TELEGRAM**: Ensure Token and Chat ID are populated for remote alerts.

---

## 🚑 Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **MT5 Not Connecting** | Ensure MT5 is open, logged in, and "Algo Trading" is Green. |
| **No Market Data** | Check symbol names in Market Watch (e.g., does it need an 'm' suffix?). |
| **Dashboard Refused** | Ensure `python web_dashboard.py` is running in a separate terminal. |
| **Calendar Error** | Update MT5 library: `pip install --upgrade MetaTrader5`. |

---

## 🔄 Development Workflow

1.  **Modify Code**: Make your changes in `src/engines/`.
2.  **Test**: Run `main.py` in "Scanner Mode" (`TRADING_ENABLED=False`).
3.  **Sync**: 
    ```powershell
    git add .
    git commit -m "Description of update"
    git push origin main
    ```
4.  **Monitor**: Keep the Web Dashboard open to track real-time Win Rate and PNL.

---
*Created by @Rohan for Axon Algo Technologies*
