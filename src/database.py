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
                        pnl REAL DEFAULT 0.0,
                        reason TEXT,
                        criteria TEXT
                    )
                """)
                # System settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY,
                        risk_pct REAL,
                        trading_enabled INTEGER,
                        min_alpha_score REAL DEFAULT 0.75,
                        symbols TEXT
                    )
                """)
                # --- SHADOW OBSERVATIONS ---
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS observations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        symbol TEXT,
                        direction TEXT,
                        entry_price REAL,
                        finy_score REAL,
                        status TEXT DEFAULT 'PENDING',
                        outcome TEXT,
                        reason TEXT
                    )
                """)
                # Initialize default settings if empty
                cursor.execute("SELECT count(*) FROM settings")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO settings (id, risk_pct, trading_enabled, min_alpha_score, symbols) VALUES (1, 1.0, 0, 0.75, 'XAUUSDm,EURUSDm,GBPJPYm')")

                # --- PER-SYMBOL STATUS (Persistent Matrix) ---
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS symbol_status (
                        symbol TEXT PRIMARY KEY,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                        strategy_alignment TEXT,
                        current_indicators TEXT
                    )
                """)
                # --- SYSTEM STATUS (LIVE ACTIONS) ---
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_status (
                        id INTEGER PRIMARY KEY,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                        current_action TEXT,
                        current_symbol TEXT,
                        planning_notes TEXT,
                        strategy_alignment TEXT,
                        current_indicators TEXT
                    )
                """)
                cursor.execute("SELECT count(*) FROM system_status")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO system_status (id, current_action, current_symbol, planning_notes, strategy_alignment, current_indicators) VALUES (1, 'INITIALIZING', 'NONE', 'Syncing nodes...', '{}', '{}')")
                conn.commit()
        except Exception as e:
            logger.error(f"Database Initialization Failed: {e}")

    def get_system_settings(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()

    def update_system_settings(self, risk, enabled, symbols, min_alpha=0.75):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE settings SET risk_pct = ?, trading_enabled = ?, symbols = ?, min_alpha_score = ? WHERE id = 1",
                        (risk, 1 if enabled else 0, symbols, min_alpha))

    def update_bot_status(self, action, symbol="NONE", notes="", alignment="{}", indicators="{}"):
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 1. Update Global Action
                conn.execute("""
                    UPDATE system_status 
                    SET current_action = ?, current_symbol = ?, planning_notes = ?, strategy_alignment = ?, current_indicators = ?, last_updated = CURRENT_TIMESTAMP 
                    WHERE id = 1
                """, (action, symbol, notes, alignment, indicators))
                
                # 2. Update Persistent Symbol Matrix
                if symbol != "NONE":
                    conn.execute("""
                        INSERT INTO symbol_status (symbol, strategy_alignment, current_indicators, last_updated)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(symbol) DO UPDATE SET
                            strategy_alignment=excluded.strategy_alignment,
                            current_indicators=excluded.current_indicators,
                            last_updated=excluded.last_updated
                    """, (symbol, alignment, indicators))
        except Exception as e:
            logger.error(f"Failed to update bot status: {e}")

    def get_all_symbol_statuses(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT * FROM symbol_status").fetchall()
                return {r['symbol']: dict(r) for r in rows}
        except Exception as e:
            logger.error(f"Failed to fetch symbol statuses: {e}")
            return {}

    def get_bot_status(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                return conn.execute("SELECT * FROM system_status WHERE id = 1").fetchone()
        except Exception as e:
            logger.error(f"Failed to fetch bot status: {e}")
            return None

    def log_trade(self, symbol, trade_type, lots, entry, sl, tp, reason="", criteria=""):
        """Records a new open trade with execution logic."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trades (symbol, type, lots, entry_price, sl, tp, reason, criteria)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, trade_type, lots, entry, sl, tp, reason, criteria))
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
