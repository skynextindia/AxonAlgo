import os
from dotenv import load_dotenv
import MetaTrader5 as mt5

load_dotenv()

class Config:
    LOGIN = int(os.getenv("MT5_LOGIN", 0))
    PASSWORD = os.getenv("MT5_PASSWORD", "")
    SERVER = os.getenv("MT5_SERVER", "")
    SYMBOL = os.getenv("SYMBOL", "GOLD")
    TIMEFRAME = mt5.TIMEFRAME_H1 # Default
    ZONE_THRESHOLD = float(os.getenv("ZONE_THRESHOLD_PIPS", 15))
    RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", 0.01))
    MIN_RR = float(os.getenv("MIN_RR", 1.5))
    TRADING_ENABLED = os.getenv("TRADING_ENABLED", "False").lower() == "true"
    MAX_SPREAD_PIPS = float(os.getenv("MAX_SPREAD_PIPS", 3.0))
    # Sessions in UTC: London (8-16), New York (13-21)
    SESSION_START = int(os.getenv("SESSION_START", 8)) 
    SESSION_END = int(os.getenv("SESSION_END", 21))
    TRAILING_STOP_PIPS = float(os.getenv("TRAILING_STOP_PIPS", 20))
