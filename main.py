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
import json

db = TradingDatabase()
notifier = TelegramNotifier()

# Professional Logging with Rotation
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log_handler = RotatingFileHandler("axon_bot.log", maxBytes=5*1024*1024, backupCount=3)
log_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[log_handler, logging.StreamHandler()])
logger = logging.getLogger("Finter")

def main():
    logger.info("--- FINTER NEURAL CORE INITIALIZING ---")
    notifier.send_message("🚀 *Finter Neural Gatekeeper Online*\nSyncing with MT5 Node.")
    
    if not MT5Client.connect():
        logger.critical("Could not connect to MT5. Exiting.")
        return

    synergy = SynergyEngine()
    risk = RiskEngine(risk_per_trade=Config.RISK_PER_TRADE, min_rr=Config.MIN_RR)
    
    # Persistent state for UI focus
    last_scanned_symbol = "NONE"
    last_alignment = "{}"
    last_indicators = "{}"

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
                    last_scanned_symbol = symbol
                    db.update_bot_status("SCANNING_MARKET", symbol, "Fetching MT5 data feeds...", last_alignment, last_indicators)
                    # Find exact broker symbol (e.g. BTCUSDm)
                    exact_sym = MT5Client.resolve_symbol(symbol)
                    mt5.symbol_select(exact_sym, True)
                    
                    # Fetch Multi-Timeframe Data
                    df_exec = MT5Client.get_market_data(exact_sym, Config.TIMEFRAME) # Execution TF
                    df_h4 = MT5Client.get_market_data(exact_sym, mt5.TIMEFRAME_H4, count=100)
                    df_d1 = MT5Client.get_market_data(exact_sym, mt5.TIMEFRAME_D1, count=250)
                    
                    symbol_info = mt5.symbol_info(exact_sym)
                    if df_exec.empty or df_h4.empty or df_d1.empty or not symbol_info: continue

                    db.update_bot_status("ANALYZING_STRUCTURE", symbol, "Executing 8-Layer Alignment Analysis...", last_alignment, last_indicators)
                    
                    # 1. POSITION MANAGEMENT
                    positions = mt5.positions_get(symbol=exact_sym)
                    if positions:
                        for pos in positions:
                            if pos.comment == "Axon Intelligence":
                                new_sl = risk.manage_trailing_stop(pos, symbol_info)
                                if new_sl: TradeExecutor.update_sl(pos.ticket, new_sl)

                    # 2. 8-LAYER ALIGNMENT ANALYSIS
                    analysis = synergy.analyze(exact_sym, df_exec, df_h4, df_d1, symbol_info, db)
                    last_alignment = json.dumps(analysis.get('layers', {}))
                    last_indicators = json.dumps(analysis.get('indicators', {}))
                    
                    if analysis['direction'] != "FLAT":
                        db.update_bot_status("PLANNING_ENTRY", symbol, f"Signal detected: {analysis['direction']}. Validating Risk/Reward...", last_alignment, last_indicators)
                        if Config.TRADING_ENABLED:
                            # 3. ATR-BASED SL & TP CALCULATION
                            entry = df_exec['close'].iloc[-1]
                            atr = analysis.get('atr', 0)
                            
                            if analysis['direction'] == "BUY":
                                sl = entry - (1.5 * atr)
                                risk_amt = entry - sl
                                tp = entry + (2.5 * risk_amt)
                            else:
                                sl = entry + (1.5 * atr)
                                risk_amt = sl - entry
                                tp = entry - (2.5 * risk_amt)

                            # 4. RR VALIDATION (Layer 8)
                            rr = 2.5 # Fixed by logic above, but we verify against min_rr
                            if rr >= Config.MIN_RR:
                                db.update_bot_status("EXECUTING_TRADE", symbol, f"Opening {analysis['direction']} position...", last_alignment, last_indicators)
                                success, msg = TradeExecutor.open_position(
                                    exact_sym, analysis['direction'], 0.01,
                                    sl, tp,
                                    reason=analysis['reason'], 
                                    criteria=f"ATR: {round(atr, 5)} | SL: {round(sl, 5)} | TP: {round(tp, 5)}"
                                )
                                if success:
                                    logger.info(f"AUTHORIZED: {exact_sym} | 8-Layer Match")
                                    notifier.send_message(f"✅ *8-LAYER ALIGNMENT*: {exact_sym} {analysis['direction']}\nEntry: {entry}\nSL: {round(sl, 5)}\nTP: {round(tp, 5)}")
                        else:
                            logger.info(f"SIGNAL_BLOCKED: {exact_sym} - Trading Disabled in Config.")
                    else:
                        db.update_bot_status("IDLE_SCAN", symbol, analysis['reason'], last_alignment, last_indicators)
                        time.sleep(1) # Visual pause for UI readability

                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    print(f"CRASH in {symbol}:", tb)
                    logger.error(f"AXON_CRASH_XYZ {symbol} - EXCEPTION: {e}")
            
            # Live Feed Mode: 0.5s pulses for maximum responsiveness
            cooldown = 0.5 if len(Config.SYMBOLS) <= 1 else 3
            # Keep the last scanned symbol and data visible during sleep
            db.update_bot_status("LIVE_PULSE", last_scanned_symbol or "INITIALIZING...", f"Neural pulse active. Next sync in {cooldown}s...", last_alignment, last_indicators)
            time.sleep(cooldown)
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
