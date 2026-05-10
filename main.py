import time
import logging
import datetime as dt
from src.config import Config
from src.mt5_connection import MT5Client
from src.engines.sr_engine import SREngine
from src.engines.breakout_engine import BreakoutEngine
from src.engines.risk_engine import RiskEngine
from src.engines.filter_engine import FilterEngine
from src.engines.candle_engine import CandleEngine
from src.executor import TradeExecutor
from src.database import TradingDatabase
from src.notifier import TelegramNotifier
import MetaTrader5 as mt5
from logging.handlers import RotatingFileHandler
from tabulate import tabulate

db = TradingDatabase()
notifier = TelegramNotifier()

# Professional Logging with Rotation (Max 5MB per file, keep 3 backups)
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log_handler = RotatingFileHandler("axon_bot.log", maxBytes=5*1024*1024, backupCount=3)
log_handler.setFormatter(log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler, logging.StreamHandler()]
)
logger = logging.getLogger("AxonBot")

def main():
    logger.info("--- AXON TRADING BOT INITIALIZING ---")
    notifier.send_message("🚀 *AxonAlgo Bot Starting Up*...\nInitializing connection to MT5.")
    
    if not MT5Client.connect():
        logger.critical("Could not connect to MT5. Exiting.")
        notifier.send_message("❌ *CRITICAL ERROR*: Could not connect to MT5.")
        return

    sr = SREngine(zone_threshold_pips=Config.ZONE_THRESHOLD)
    breakout = BreakoutEngine()
    risk = RiskEngine(risk_per_trade=Config.RISK_PER_TRADE, min_rr=Config.MIN_RR)
    
    last_status_report = time.time()

    try:
        while True:
            for symbol in Config.SYMBOLS:
                try:
                    logger.info(f"Scanning {symbol}...")
                    # 1. Refresh Account & Symbol Data
                    df = MT5Client.get_market_data(symbol, Config.TIMEFRAME)
                    symbol_info = mt5.symbol_info(symbol)
                    account_info = mt5.account_info()
                    
                    if df.empty:
                        logger.warning(f"No price data found for {symbol}. Is it in Market Watch?")
                        continue
                    
                    if not symbol_info:
                        logger.warning(f"Could not fetch symbol info for {symbol}.")
                        continue

                    # 2. ADVANCED MANAGEMENT: Break-even & Partial TP
                    positions = mt5.positions_get(symbol=symbol)
                    if positions:
                        for pos in positions:
                            if pos.comment == "Axon Breakout Bot":
                                # Trailing Stop
                                new_sl = risk.manage_trailing_stop(pos, symbol_info)
                                if new_sl:
                                    TradeExecutor.update_sl(pos.ticket, new_sl)
                                
                                # Break-even Logic
                                current_rr = abs(pos.price_current - pos.price_open) / abs(pos.price_open - pos.sl) if pos.sl != 0 else 0
                                if current_rr >= Config.BREAK_EVEN_RR and pos.sl != pos.price_open:
                                    TradeExecutor.update_sl(pos.ticket, pos.price_open)
                                    logger.info(f"MOVE TO BE: Ticket #{pos.ticket} secured at entry.")
                                    notifier.send_message(f"🛡️ *BREAK-EVEN*: Secure at entry for {symbol}")

                    # 3. Market Safety Filter
                    is_safe, reason = FilterEngine.is_market_safe(symbol_info)
                    
                    # 4. Analysis
                    zones = sr.get_zones(df)
                    fvgs = sr.get_fvgs(df) # SMC Feature
                    signal = breakout.check_breakout(df, zones)
                    current_price = df.iloc[-1]['close']
                    
                    logger.info(f"[{symbol}] Price: {current_price} | Zones Found: {len(zones)}")
                    
                    if signal:
                        # 5. Confirmation Layers (Trend + Candle + FVG Alignment)
                        htf_df = MT5Client.get_market_data(symbol, Config.HTF_TIMEFRAME, count=300)
                        trend_ok, _ = FilterEngine.check_trend_confirmation(htf_df, signal['type'])
                        
                        if is_safe and trend_ok and CandleEngine.is_confirmed(df, signal['type']):
                            trade_params = risk.calculate_trade_params(account_info.balance, symbol_info, signal, zones)
                            
                            if trade_params['valid'] and Config.TRADING_ENABLED:
                                success = TradeExecutor.open_position(
                                    symbol, signal['type'], trade_params['lots'], 
                                    trade_params['sl'], trade_params['tp']
                                )
                                if success:
                                    notifier.send_trade_alert(signal['type'], symbol, trade_params['lots'], trade_params['sl'], trade_params['tp'], trade_params['rr'])
                
                except Exception as symbol_error:
                    logger.error(f"Error processing {symbol}: {symbol_error}")
            
            time.sleep(10) # Faster cycle for multi-symbol
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    finally:
        mt5.shutdown()
        logger.info("MT5 Connection Closed.")

if __name__ == "__main__":
    main()
