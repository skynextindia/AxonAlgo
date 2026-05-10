# Finter 🚀
**Most advanced terminal with AI+Trading Agents**

Finter is a high-performance algorithmic trading system optimized for MetaTrader 5. It leverages the **Finy.AI Neural Engine** to validate institutional breakout patterns across multi-timeframe vectors.

---

### 🧠 Intelligence Layer: Finy.AI
The terminal is powered by **Finy.AI**, a proprietary neural assistant that:
- **Neural Interventions**: Automatically blocks low-probability trades based on macro-conflicts.
- **Deep Scan**: Provides real-time sentiment and institutional strength analysis.
- **Neural Lab**: Tracks real-time performance metrics and win-rate analytics.
- **Interactive Chat**: Direct interface for strategy queries and system status reports.

### 🚀 Core Capabilities
- **Institutional S/R Engine**: Clusters fractal highs/lows into dynamic supply/demand zones.
- **MTF Trend Filter**: Validates H4/D1 trend confluences using neural-weighted EMAs.
- **Finter Dashboard**: 300ms hyper-sync HUD for real-time order flow monitoring.
- **Risk Control Hub**: Dynamic 1% fixed fractional risk management with institutional safety toggles.

---

### 📊 System Metadata (Auto-Generated)
- **Last Updated**: 2026-05-11 04:55
- **Total Lines of Code & Docs**: 1,945
- **Neural Accuracy Engine**: V2.1 (Overclocked)

### 🛠️ Resolved Terminal Errors (Session v19.3 -> v19.4)
1. **Critical Logic Fix**: Resolved `datetime` reference error in the core execution loop causing bot stagnation.
2. **API Stability**: Patched `sqlite3.Row` JSON serialization error in the `/api/data` stream.
3. **Latency Optimization**: Reduced UI polling latency from 1s to 300ms via server-side `EVENTS_CACHE`.
4. **Symbol Sync**: Fixed MT5 symbol initialization gaps for inactive market pairs.

---

## 🚀 Setup
1. Clone: `git clone https://github.com/skynextindia/AxonAlgo.git`
2. Requirements: `pip install -r requirements.txt`
3. Initialize: `python main.py`
4. Command HUD: `python web_dashboard.py`

Code by @skynext
