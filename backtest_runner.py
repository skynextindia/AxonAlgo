import logging
from src.config import Config
from src.mt5_connection import MT5Client
from src.engines.sr_engine import SREngine
from src.engines.breakout_engine import BreakoutEngine
from src.engines.risk_engine import RiskEngine
from src.engines.candle_engine import CandleEngine
from src.engines.backtest_engine import BacktestEngine
import MetaTrader5 as mt5
from tabulate import tabulate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Backtester")

def run_backtest():
    logger.info("--- AXON BACKTESTER STARTING ---")
    
    if not MT5Client.connect():
        return

    # Fetch 2000 bars for testing
    df = MT5Client.get_market_data(Config.SYMBOL, Config.TIMEFRAME, count=2000)
    
    if df.empty:
        logger.error("Could not fetch historical data.")
        return

    # Initialize Engines
    sr = SREngine(zone_threshold_pips=Config.ZONE_THRESHOLD)
    breakout = BreakoutEngine()
    risk = RiskEngine()
    candle = CandleEngine()
    backtester = BacktestEngine(initial_balance=10000)

    # Run Simulation
    results = backtester.run(df, sr, breakout, risk, candle)
    
    print("\n" + "="*30)
    print("      BACKTEST RESULTS")
    print("="*30)
    if isinstance(results, dict):
        for k, v in results.items():
            print(f"{k:15}: {v}")
    else:
        print(results)
    print("="*30)

    mt5.shutdown()

if __name__ == "__main__":
    run_backtest()
