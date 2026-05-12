import os
from dotenv import load_dotenv
import MetaTrader5 as mt5

load_dotenv()

class Config:
    LOGIN = int(os.getenv("MT5_LOGIN", 0))
    PASSWORD = os.getenv("MT5_PASSWORD", "")
    SERVER = os.getenv("MT5_SERVER", "")
    SYMBOL = os.getenv("SYMBOL", "GOLD")
    TIMEFRAME = mt5.TIMEFRAME_M15 # Primary Scalp/Execution TF
    ZONE_THRESHOLD = float(os.getenv("ZONE_THRESHOLD_PIPS", 15))
    RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", 0.01))
    MIN_RR = float(os.getenv("MIN_RR", 1.5))
    TRADING_ENABLED = os.getenv("TRADING_ENABLED", "False").lower() == "true"
    MAX_SPREAD_PIPS = float(os.getenv("MAX_SPREAD_PIPS", 3.0))
    # Sessions in UTC: London (8-16), New York (13-21)
    SESSION_START = int(os.getenv("SESSION_START", 8)) 
    SESSION_END = int(os.getenv("SESSION_END", 21))
    TRAILING_STOP_PIPS = float(os.getenv("TRAILING_STOP_PIPS", 20))
    HTF_TIMEFRAME = mt5.TIMEFRAME_H4
    TREND_EMA = 200
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    SYMBOLS = ["XAUUSDm", "EURUSDm", "GBPJPYm", "BTCUSDm"]
    PARTIAL_TP_RR = 1.0
    BREAK_EVEN_RR = 1.1
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "axon_admin")
