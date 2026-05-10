import MetaTrader5 as mt5
import pandas as pd
from .config import Config

class MT5Client:
    @staticmethod
    def connect():
        if not mt5.initialize(login=Config.LOGIN, password=Config.PASSWORD, server=Config.SERVER):
            print(f"MT5 Init Failed: {mt5.last_error()}")
            return False
        print(f"Connected to {Config.SERVER}")
        return True

    @staticmethod
    def get_market_data(symbol, timeframe, count=500):
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            return pd.DataFrame()
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
