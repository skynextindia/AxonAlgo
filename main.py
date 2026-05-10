import time
from src.config import Config
from src.mt5_connection import MT5Client
from src.engines.sr_engine import SREngine
from src.engines.breakout_engine import BreakoutEngine
from src.engines.risk_engine import RiskEngine
from src.engines.filter_engine import FilterEngine
from src.executor import TradeExecutor
import MetaTrader5 as mt5
from tabulate import tabulate

def main():
    print("--- AXON TRADING BOT INITIALIZING ---")
    
    if not MT5Client.connect():
        return

    sr = SREngine(zone_threshold_pips=Config.ZONE_THRESHOLD)
    breakout = BreakoutEngine()
    risk = RiskEngine(risk_per_trade=Config.RISK_PER_TRADE, min_rr=Config.MIN_RR)

    try:
        while True:
            # 1. Refresh Account & Symbol Data
            df = MT5Client.get_market_data(Config.SYMBOL, Config.TIMEFRAME)
            symbol_info = mt5.symbol_info(Config.SYMBOL)
            account_info = mt5.account_info()
            
            if not df.empty and symbol_info and account_info:
                # 2. PRO FEATURE: Manage Active Trades (Trailing Stop)
                positions = mt5.positions_get(symbol=Config.SYMBOL)
                if positions:
                    for pos in positions:
                        if pos.comment == "Axon Breakout Bot":
                            new_sl = risk.manage_trailing_stop(pos, symbol_info)
                            if new_sl:
                                TradeExecutor.update_sl(pos.ticket, new_sl)

                # 3. PRO FEATURE: Market Safety Filter (Spread/Session)
                is_safe, reason = FilterEngine.is_market_safe(symbol_info)
                
                # 4. Analysis & Execution
                zones = sr.get_zones(df)
                signal = breakout.check_breakout(df, zones)
                current_price = df.iloc[-1]['close']
                
                print(f"\n[{Config.SYMBOL}] Price: {current_price} | Session: {'OPEN' if is_safe else 'CLOSED'} | Safe: {is_safe}")
                
                if signal:
                    if not is_safe:
                        print(f"!!! SIGNAL BLOCKED: {reason}")
                    else:
                        # Calculate Risk Parameters
                        trade_params = risk.calculate_trade_params(account_info.balance, symbol_info, signal, zones)
                        
                        if trade_params['valid']:
                            print(f"!!! TRADE SIGNAL VALIDATED !!!")
                            print(f"Type: {signal['type']} | Lots: {trade_params['lots']} | RR: {trade_params['rr']}")
                            
                            if Config.TRADING_ENABLED:
                                TradeExecutor.open_position(
                                    Config.SYMBOL, 
                                    signal['type'], 
                                    trade_params['lots'], 
                                    trade_params['sl'], 
                                    trade_params['tp']
                                )
                                print("Order submitted. Waiting for next cycle...")
                                time.sleep(300) 
                            else:
                                print("TRADING DISABLED in Config. Signal logged only.")
                        else:
                            print(f"Signal ignored: RR too low ({trade_params['rr']}) or lot size invalid.")
                else:
                    status_msg = "Scanning..." if is_safe else f"Paused ({reason})"
                    print(f"Status: {status_msg} (Zones: {len(zones)})")
            
            time.sleep(60) 
            
    except KeyboardInterrupt:
        print("Bot stopped by user.")

if __name__ == "__main__":
    main()
