import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, initial_balance=10000):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.trades = []
        self.equity_curve = [initial_balance]

    def run(self, df, sr_engine, breakout_engine, risk_engine, candle_engine):
        """
        Simulates the bot's logic bar-by-bar on historical data.
        """
        logger.info(f"Starting Backtest on {len(df)} bars...")
        
        # Start from index 300 to ensure we have enough data for S/R and EMAs
        for i in range(300, len(df) - 1):
            # The 'current' window of history the bot would see at this moment
            window = df.iloc[:i+1].copy()
            next_bar = df.iloc[i+1] # We use the next bar to see if SL/TP was hit
            
            # Logic Layers
            zones = sr_engine.get_zones(window)
            signal = breakout_engine.check_breakout(window, zones)
            
            if signal:
                if candle_engine.is_confirmed(window, signal['type']):
                    # Calculate Params as the Risk Engine would
                    # We mock symbol_info and account_info for simulation
                    entry_price = signal['price']
                    
                    # Approximate SL/TP based on zone (simplified for backtest)
                    if signal['type'] == "BULLISH_BREAKOUT":
                        sl = signal['zone_mid'] - 0.0010 # 10 pips approx
                        tp = signal['zone_mid'] + 0.0020 # 20 pips approx
                    else:
                        sl = signal['zone_mid'] + 0.0010
                        tp = signal['zone_mid'] - 0.0020
                        
                    self._execute_simulated_trade(df.iloc[i+1:], entry_price, sl, tp, signal['type'])

        return self.get_summary()

    def _execute_simulated_trade(self, future_data, entry, sl, tp, direction):
        """Checks future bars to see if SL or TP was hit first."""
        for _, bar in future_data.iterrows():
            if direction == "BULLISH_BREAKOUT":
                if bar['low'] <= sl: # Stop hit
                    pnl = -100 # Mock 1% risk
                    self.balance += pnl
                    self.trades.append({'type': 'BUY', 'result': 'LOSS', 'pnl': pnl})
                    break
                if bar['high'] >= tp: # Target hit
                    pnl = 150 # Mock 1.5 RR
                    self.balance += pnl
                    self.trades.append({'type': 'BUY', 'result': 'WIN', 'pnl': pnl})
                    break
            else:
                if bar['high'] <= sl: # Stop hit (inverted for sell logic)
                    pnl = -100
                    self.balance += pnl
                    self.trades.append({'type': 'SELL', 'result': 'LOSS', 'pnl': pnl})
                    break
                if bar['low'] >= tp:
                    pnl = 150
                    self.balance += pnl
                    self.trades.append({'type': 'SELL', 'result': 'WIN', 'pnl': pnl})
                    break
        
        self.equity_curve.append(self.balance)

    def get_summary(self):
        if not self.trades:
            return "No trades executed during backtest."
            
        wins = len([t for t in self.trades if t['result'] == 'WIN'])
        total = len(self.trades)
        win_rate = (wins / total) * 100
        net_profit = self.balance - self.initial_balance
        
        return {
            "Total Trades": total,
            "Win Rate": f"{round(win_rate, 2)}%",
            "Net Profit": round(net_profit, 2),
            "Final Balance": round(self.balance, 2)
        }
