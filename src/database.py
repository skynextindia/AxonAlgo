import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TradingDatabase:
    def __init__(self, db_path="axon_trading.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Creates the necessary tables for trade tracking."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        symbol TEXT,
                        type TEXT,
                        lots REAL,
                        entry_price REAL,
                        sl REAL,
                        tp REAL,
                        status TEXT DEFAULT 'OPEN',
                        exit_price REAL,
                        pnl REAL DEFAULT 0.0
                    )
                """)
                # System settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY,
                        risk_pct REAL,
                        trading_enabled INTEGER,
                        symbols TEXT
                    )
                """)
                # Initialize default settings if empty
                cursor.execute("SELECT count(*) FROM settings")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO settings (id, risk_pct, trading_enabled, symbols) VALUES (1, 1.0, 0, 'XAUUSDm,EURUSDm,GBPJPYm')")
                conn.commit()
        except Exception as e:
            logger.error(f"Database Initialization Failed: {e}")

    def get_system_settings(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()

    def update_system_settings(self, risk, enabled, symbols):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE settings SET risk_pct = ?, trading_enabled = ?, symbols = ? WHERE id = 1",
                        (risk, 1 if enabled else 0, symbols))

    def log_trade(self, symbol, trade_type, lots, entry, sl, tp):
        """Records a new open trade."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trades (symbol, type, lots, entry_price, sl, tp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (symbol, trade_type, lots, entry, sl, tp))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to log trade: {e}")
            return None

    def close_trade(self, trade_id, exit_price, pnl):
        """Updates a trade record when it is closed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE trades 
                    SET status = 'CLOSED', exit_price = ?, pnl = ?
                    WHERE id = ?
                """, (exit_price, pnl, trade_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to close trade record: {e}")

    def get_metrics(self):
        """Calculates win rate and total profitability."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT pnl FROM trades WHERE status = 'CLOSED'")
                pnls = [row[0] for row in cursor.fetchall()]
                
                if not pnls:
                    return {"wins": 0, "losses": 0, "win_rate": 0, "total_pnl": 0}
                
                wins = len([p for p in pnls if p > 0])
                losses = len([p for p in pnls if p <= 0])
                win_rate = (wins / len(pnls)) * 100
                
                return {
                    "wins": wins,
                    "losses": losses,
                    "win_rate": round(win_rate, 2),
                    "total_pnl": round(sum(pnls), 2)
                }
        except Exception as e:
            logger.error(f"Failed to fetch metrics: {e}")
            return None
