import time
import logging
import datetime
from src.config import Config
from src.mt5_connection import MT5Client
from src.engines.synergy_engine import SynergyEngine
from src.engines.risk_engine import RiskEngine
from src.engines.filter_engine import FilterEngine
from src.executor import TradeExecutor
from src.database import TradingDatabase
from src.notifier import TelegramNotifier
import MetaTrader5 as mt5
from logging.handlers import RotatingFileHandler
import os
import sqlite3

db = TradingDatabase()
notifier = TelegramNotifier()

# Professional Logging with Rotation
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log_handler = RotatingFileHandler("axon_bot.log", maxBytes=5*1024*1024, backupCount=3)
log_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[log_handler, logging.StreamHandler()])
logger = logging.getLogger("AxonBot")

def main():
    logger.info("--- AXON NEURAL CORE INITIALIZING ---")
    notifier.send_message("🚀 *Axon Neural Gatekeeper Online*\nSyncing with MT5 Node.")
    
    if not MT5Client.connect():
        logger.critical("Could not connect to MT5. Exiting.")
        return

    synergy = SynergyEngine()
    risk = RiskEngine(risk_per_trade=Config.RISK_PER_TRADE, min_rr=Config.MIN_RR)
    
    try:
        while True:
            # DYNAMIC SYNC: Refresh settings from Database
            sys_settings = db.get_system_settings()
            raw_symbols = sys_settings['symbols'].split(',')
            Config.SYMBOLS = [s.strip() for s in raw_symbols if s.strip()]
            Config.RISK_PER_TRADE = sys_settings['risk_pct'] / 100
            Config.TRADING_ENABLED = bool(sys_settings['trading_enabled'])

            for symbol in Config.SYMBOLS:
                try:
                    # Find exact broker symbol (e.g. BTCUSDm)
                    exact_sym = MT5Client.resolve_symbol(symbol)
                    mt5.symbol_select(exact_sym, True)
                    
                    df = MT5Client.get_market_data(exact_sym, Config.TIMEFRAME)
                    symbol_info = mt5.symbol_info(exact_sym)
                    account_info = mt5.account_info()
                    
                    if df.empty or not symbol_info: continue

                    # 1. PROTECT MANUAL TRADES: Only manage bot positions
                    positions = mt5.positions_get(symbol=symbol)
                    if positions:
                        for pos in positions:
                            # If it's a bot position, manage it (Magic Number or Comment)
                            if pos.comment == "Axon Intelligence":
                                new_sl = risk.manage_trailing_stop(pos, symbol_info)
                                if new_sl: TradeExecutor.update_sl(pos.ticket, new_sl)

                    # 2. SYNERGY ANALYSIS
                    analysis = synergy.analyze(symbol, df)
                    
                    if analysis['direction'] != "FLAT":
                        # 3. NEURAL GATE: Alpha Validation
                        if analysis['alpha'] >= 75:
                            if Config.TRADING_ENABLED:
                                # Prepare Execution
                                # Logic for SL/TP based on ATR/SR simplified here for brevity
                                sl_dist = (df['close'].iloc[-1] - df['low'].iloc[-5:-1].min()) if analysis['direction'] == "BUY" else (df['high'].iloc[-5:-1].max() - df['close'].iloc[-1])
                                sl = df['close'].iloc[-1] - sl_dist if analysis['direction'] == "BUY" else df['close'].iloc[-1] + sl_dist
                                tp = df['close'].iloc[-1] + (sl_dist * 2) if analysis['direction'] == "BUY" else df['close'].iloc[-1] - (sl_dist * 2)
                                
                                success = TradeExecutor.open_position(
                                    symbol, analysis['direction'], 0.01, # Standard Micro for testing
                                    sl, tp,
                                    reason=analysis['reason'], 
                                    criteria=f"Alpha: {analysis['alpha']}% | Tech: {analysis['breakdown']['technical']} | Mom: {analysis['breakdown']['momentum']}"
                                )
                                if success:
                                    logger.info(f"AUTHORIZED: {symbol} @ Alpha {analysis['alpha']}%")
                                    notifier.send_message(f"✅ *AUTHORIZED*: {symbol} entry @ Alpha {analysis['alpha']}%")
                        else:
                            # SHADOW OBSERVATION: Log rejected trade for learning
                            logger.info(f"REJECTED: {symbol} Alpha {analysis['alpha']}% insufficient.")
                            with sqlite3.connect(db.db_path) as conn:
                                conn.execute("INSERT INTO observations (symbol, direction, entry_price, finy_score, reason) VALUES (?,?,?,?,?)",
                                           (symbol, analysis['direction'], df['close'].iloc[-1], analysis['alpha'], "Insufficient Alpha Synergy"))
                            # Finy.AI Neural Intervention logged
                            logger.info(f"Finy.AI: Blocked {symbol} {analysis['direction']} - Insufficient Alpha Synergy")

                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    print(f"CRASH in {symbol}:", tb)
                    logger.error(f"AXON_CRASH_XYZ {symbol} - EXCEPTION: {e}")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
