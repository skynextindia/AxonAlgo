import MetaTrader5 as mt5
import pandas as pd
import json

# --- PRICE ACTION VERIFICATION TOOL ---
# This script prints the exact O/H/L/C of the candles that triggered the PA signal

def verify_pa():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    symbol = "BTCUSDm"
    timeframe = mt5.TIMEFRAME_M15
    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 2)
    if rates is None or len(rates) < 2:
        print("No data")
        return
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    print(f"--- {symbol} PA AUDIT (M15) ---")
    print(f"PREVIOUS ({prev['time']}): Open={prev['open']}, Close={prev['close']}")
    print(f"CURRENT  ({curr['time']}):  Open={curr['open']}, Close={curr['close']}")
    print("-" * 30)
    
    # Check for Engulfing manually to demonstrate
    is_bearish_engulfing = (curr['close'] < curr['open'] and prev['close'] > prev['open'] and 
                           curr['close'] <= prev['open'] and curr['open'] >= prev['close'])
    
    if is_bearish_engulfing:
        print("RESULT: BEARISH ENGULFING DETECTED")
    else:
        print("RESULT: SCANNING FOR OTHER PATTERNS (MOMENTUM/STAR)")

    mt5.shutdown()

if __name__ == "__main__":
    verify_pa()
