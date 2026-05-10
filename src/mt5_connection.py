import MetaTrader5 as mt5
import pandas as pd
import logging
from .config import Config

logger = logging.getLogger(__name__)

class MT5Client:
    @staticmethod
    def connect():
        try:
            if not mt5.initialize(login=Config.LOGIN, password=Config.PASSWORD, server=Config.SERVER):
                logger.error(f"MT5 Init Failed: {mt5.last_error()}")
                return False
            logger.info(f"Connected to MT5 Server: {Config.SERVER}")
            return True
        except Exception as e:
            logger.critical(f"MT5 Connection Crash: {e}")
            return False

    @staticmethod
    def get_market_data(symbol, timeframe, count=500):
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                logger.warning(f"No market data returned for {symbol}")
                return pd.DataFrame()
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
        except Exception as e:
            logger.error(f"Data Retrieval Error: {e}")
            return pd.DataFrame()
