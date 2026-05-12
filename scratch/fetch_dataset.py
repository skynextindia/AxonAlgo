import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
import json
from datetime import datetime, timedelta
import os
import sys

# Add project root to path to import engines
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import Config
from src.mt5_connection import MT5Client
from src.engines.sr_engine import SREngine
from src.engines.candle_engine import CandleEngine

def fetch_ai_dataset(symbol="XAUUSDm", days=3):
    if not MT5Client.connect():
        return {"error": "MT5 Connection Failed"}

    # 4H candles for 3 days = ~18 candles. 
    # Fetch 100 to ensure indicators (EMA/RSI) are accurate.
    tf = mt5.TIMEFRAME_H4
    count = 100 
    
    df = MT5Client.get_market_data(symbol, tf, count=count)
    if df.empty:
        return {"error": f"No data for {symbol}"}

    # Calculate Indicators
    df['rsi'] = ta.rsi(df['close'], length=14)
    df['ema50'] = ta.ema(df['close'], length=50)
    df['ema200'] = ta.ema(df['close'], length=200)
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

    sr_engine = SREngine(zone_threshold_pips=20)
    
    dataset = []
    
    # We want the last 3 days. 
    # Current time - 3 days.
    cutoff_time = datetime.now() - timedelta(days=days)
    
    # Filter for the last 3 days
    df_filtered = df[df['time'] >= cutoff_time].copy()
    
    for i in range(len(df)):
        current_time = df.iloc[i]['time']
        if current_time < cutoff_time:
            continue
            
        # Get slice up to this candle for "lookback" indicators (Zones/FVGs)
        df_slice = df.iloc[:i+1]
        
        # Calculate Zones and FVGs based on data available UP TO THIS CANDLE
        # Note: In a real dataset, you'd want to know what zones existed AT that time.
        zones = sr_engine.get_zones(df_slice)
        fvgs = sr_engine.get_fvgs(df_slice)
        
        # Candle patterns
        bull_pattern = CandleEngine.get_confirmed_pattern(df_slice, "BULLISH_BREAKOUT")
        bear_pattern = CandleEngine.get_confirmed_pattern(df_slice, "BEARISH_BREAKOUT")
        
        entry = {
            "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'),
            "ohlcv": {
                "open": float(df.iloc[i]['open']),
                "high": float(df.iloc[i]['high']),
                "low": float(df.iloc[i]['low']),
                "close": float(df.iloc[i]['close']),
                "volume": int(df.iloc[i]['tick_volume'])
            },
            "indicators": {
                "rsi": float(df.iloc[i]['rsi']) if not pd.isna(df.iloc[i]['rsi']) else None,
                "ema50": float(df.iloc[i]['ema50']) if not pd.isna(df.iloc[i]['ema50']) else None,
                "ema200": float(df.iloc[i]['ema200']) if not pd.isna(df.iloc[i]['ema200']) else None,
                "atr": float(df.iloc[i]['atr']) if not pd.isna(df.iloc[i]['atr']) else None
            },
            "market_structure": {
                "active_zones": zones[:3], # Top 3 strongest
                "active_fvgs": fvgs[-3:],  # Last 3 gaps
                "patterns": {
                    "bullish": bull_pattern,
                    "bearish": bear_pattern
                }
            }
        }
        dataset.append(entry)

    mt5.shutdown()
    return dataset

if __name__ == "__main__":
    # Target BTCUSDm as requested
    target = "BTCUSDm"
    data = fetch_ai_dataset(target, days=3)
    print(json.dumps(data, indent=2))
