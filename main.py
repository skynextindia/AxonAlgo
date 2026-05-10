import time
import logging
from src.config import Config
from src.mt5_connection import MT5Client
from src.engines.sr_engine import SREngine
from src.engines.breakout_engine import BreakoutEngine
from src.engines.risk_engine import RiskEngine
from src.engines.filter_engine import FilterEngine
from src.engines.candle_engine import CandleEngine
from src.executor import TradeExecutor
import MetaTrader5 as mt5
from tabulate import tabulate

# Professional Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("axon_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AxonBot")

def main():
    logger.info("--- AXON TRADING BOT INITIALIZING ---")
    
    if not MT5Client.connect():
        logger.critical("Could not connect to MT5. Exiting.")
        return

    sr = SREngine(zone_threshold_pips=Config.ZONE_THRESHOLD)
    breakout = BreakoutEngine()
    risk = RiskEngine(risk_per_trade=Config.RISK_PER_TRADE, min_rr=Config.MIN_RR)

    try:
        while True:
            try:
                # 1. Refresh Account & Symbol Data
                df = MT5Client.get_market_data(Config.SYMBOL, Config.TIMEFRAME)
                symbol_info = mt5.symbol_info(Config.SYMBOL)
                account_info = mt5.account_info()
                
                if df.empty or not symbol_info or not account_info:
                    logger.warning("Waiting for market data/connection...")
                    time.sleep(10)
                    continue

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
                
                logger.info(f"[{Config.SYMBOL}] Price: {current_price} | Session: {'OPEN' if is_safe else 'CLOSED'}")
                
                if signal:
                    if not is_safe:
                        logger.warning(f"SIGNAL BLOCKED: {reason}")
                    else:
                        # 5. PRO FEATURE: MTF Trend Confirmation (H4)
                        htf_df = MT5Client.get_market_data(Config.SYMBOL, Config.HTF_TIMEFRAME, count=300)
                        trend_ok, trend_reason = FilterEngine.check_trend_confirmation(htf_df, signal['type'])
                        
                        if not trend_ok:
                            logger.warning(f"SIGNAL BLOCKED: {trend_reason}")
                        elif not CandleEngine.is_confirmed(df, signal['type']):
                            logger.info("SIGNAL BLOCKED: Waiting for Candle Confirmation (Engulfing/Hammer)")
                        else:
                            # Calculate Risk Parameters
                            trade_params = risk.calculate_trade_params(account_info.balance, symbol_info, signal, zones)
                            
                            if trade_params['valid']:
                                logger.info(f"!!! TRADE SIGNAL VALIDATED: {signal['type']} !!!")
                                
                                if Config.TRADING_ENABLED:
                                    TradeExecutor.open_position(
                                        Config.SYMBOL, 
                                        signal['type'], 
                                        trade_params['lots'], 
                                        trade_params['sl'], 
                                        trade_params['tp']
                                    )
                                    time.sleep(300) 
                                else:
                                    logger.info(f"DRY RUN: Lots={trade_params['lots']} SL={trade_params['sl']} TP={trade_params['tp']}")
                            else:
                                logger.info(f"Trade invalid: RR={trade_params['rr']} (Min={Config.MIN_RR})")
                
            except Exception as loop_error:
                logger.error(f"Unexpected error in trading loop: {loop_error}")
                time.sleep(5)
                
            time.sleep(60) 
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    finally:
        mt5.shutdown()
        logger.info("MT5 Connection Closed.")

if __name__ == "__main__":
    main()
