import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
import json
import os

# --- SYNC DIAGNOSTIC TOOL ---
# This script compares the Bot's RSI calculation with the live MT5 state
# to identify why your chart shows a different value.

def run_diagnostic():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    symbol = "BTCUSDm" # Change if needed
    timeframe = mt5.TIMEFRAME_H1
    
    # 1. Fetch data (Increased to 1000 for perfect convergence)
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1000)
    df = pd.DataFrame(rates)
    
    # 2. Calculate using Bot's method (pandas_ta)
    df['rsi_ta'] = ta.rsi(df['close'], length=14)
    
    # 3. Get values
    live_rsi = df['rsi_ta'].iloc[-1]
    closed_rsi = df['rsi_ta'].iloc[-2]
    
    print(f"--- {symbol} RSI DIAGNOSTIC (M15) ---")
    print(f"Bot Display Value (Closed): {round(closed_rsi, 2)}  <-- Matches iloc[-2]")
    print(f"Live Moving Value (Active): {round(live_rsi, 2)}    <-- Matches iloc[-1]")
    print("-" * 30)
    print("If your chart shows a different value, check:")
    print("1. Are you looking at the currently moving candle or the one that just finished?")
    print("2. Is your RSI set to 'Close' price on the chart?")
    print("3. Does your broker data match (check the 'Close' price of the last candle)?")
    
    mt5.shutdown()

if __name__ == "__main__":
    run_diagnostic()
