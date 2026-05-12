import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
import json
from datetime import datetime, timedelta
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import Config
from src.mt5_connection import MT5Client
from src.engines.sr_engine import SREngine
from src.engines.candle_engine import CandleEngine

def get_current_bar(df, timestamp):
    """Returns the bar that was active/current at the given timestamp."""
    # Find the last bar with time <= timestamp
    mask = df['time'] <= timestamp
    if not mask.any(): return None
    return df[mask].iloc[-1]

def calculate_indicators(df):
    """Calculates all supported indicators for a dataframe."""
    if len(df) < 2: return df
    df = df.copy()
    df['rsi'] = ta.rsi(df['close'], length=14)
    df['ema50'] = ta.ema(df['close'], length=50)
    df['ema200'] = ta.ema(df['close'], length=200)
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    return df

def fetch_mtf_dataset(symbol="BTCUSDm"):
    if not MT5Client.connect():
        return {"error": "MT5 Connection Failed"}

    # Define Time Windows
    now = datetime.now()
    start_date = (now - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Fetch data with enough buffer for indicators (EMA200 needs at least 200 bars)
    # 15m: 2 days + 300 bars buffer
    # 4H: 2 days + 200 bars buffer
    # D1: 2 days + 250 bars buffer
    
    df_15m = calculate_indicators(MT5Client.get_market_data(symbol, mt5.TIMEFRAME_M15, count=500))
    df_4h = calculate_indicators(MT5Client.get_market_data(symbol, mt5.TIMEFRAME_H4, count=300))
    df_d1 = calculate_indicators(MT5Client.get_market_data(symbol, mt5.TIMEFRAME_D1, count=300))

    sr_engine = SREngine(zone_threshold_pips=50) # BTC needs higher threshold
    
    mtf_dataset = []
    
    # Iterate through 15m bars for Yesterday and Today
    target_15m = df_15m[df_15m['time'] >= start_date]
    
    for _, row_15m in target_15m.iterrows():
        ts = row_15m['time']
        
        # 1. LTF (15M) Context
        # Find index in full df to get slice for patterns
        idx_15m = df_15m[df_15m['time'] == ts].index[0]
        df_15m_slice = df_15m.iloc[:idx_15m+1]
        
        ltf_data = {
            "ohlcv": { "o": row_15m['open'], "h": row_15m['high'], "l": row_15m['low'], "c": row_15m['close'] },
            "rsi": row_15m['rsi'],
            "ema50": row_15m['ema50'],
            "pattern": CandleEngine.get_confirmed_pattern(df_15m_slice, "BULLISH_BREAKOUT") or CandleEngine.get_confirmed_pattern(df_15m_slice, "BEARISH_BREAKOUT")
        }
        
        # 2. ITF (4H) Context
        row_4h = get_current_bar(df_4h, ts)
        itf_data = {}
        if row_4h is not None:
            idx_4h = df_4h[df_4h['time'] == row_4h['time']].index[0]
            df_4h_slice = df_4h.iloc[:idx_4h+1]
            
            itf_data = {
                "ohlcv": { "o": row_4h['open'], "h": row_4h['high'], "l": row_4h['low'], "c": row_4h['close'] },
                "rsi": row_4h['rsi'],
                "atr": row_4h['atr'],
                "zones": sr_engine.get_zones(df_4h_slice)[:3],
                "fvgs": sr_engine.get_fvgs(df_4h_slice)[-3:]
            }
            
        # 3. HTF (D1) Context
        row_d1 = get_current_bar(df_d1, ts)
        htf_data = {}
        if row_d1 is not None:
            trend = "BULLISH" if row_d1['close'] > row_d1['ema200'] else "BEARISH"
            htf_data = {
                "ohlcv": { "o": row_d1['open'], "h": row_d1['high'], "l": row_d1['low'], "c": row_d1['close'] },
                "ema200": row_d1['ema200'],
                "trend_bias": trend
            }
            
        mtf_dataset.append({
            "timestamp": ts.strftime('%Y-%m-%d %H:%M'),
            "HTF_DAILY": htf_data,
            "ITF_4H": itf_data,
            "LTF_15M": ltf_data
        })

    mt5.shutdown()
    return mtf_dataset

if __name__ == "__main__":
    data = fetch_mtf_dataset("BTCUSDm")
    print(json.dumps(data, indent=2))
