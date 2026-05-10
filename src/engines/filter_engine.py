from datetime import datetime
import pytz
from src.config import Config

class FilterEngine:
    @staticmethod
    def is_market_safe(symbol_info):
        """
        Validates if current conditions are suitable for professional trading.
        """
        if not symbol_info:
            return False, "No Symbol Info"

        # 1. Spread Filter (Protects against high costs/slippage)
        # Convert raw points to pips (assuming 10 points = 1 pip)
        spread_pips = (symbol_info.ask - symbol_info.bid) / (symbol_info.point * 10)
        if spread_pips > Config.MAX_SPREAD_PIPS:
            return False, f"High Spread: {round(spread_pips, 1)} pips"

        # 2. Session Filter (Protects against low liquidity/fakeouts)
        # We use UTC for consistency across VPS/Local deployments
        current_hour_utc = datetime.now(pytz.utc).hour
        if not (Config.SESSION_START <= current_hour_utc <= Config.SESSION_END):
            return False, f"Off-Session (UTC Hour: {current_hour_utc})"

        return True, "Conditions Optimal"

    @staticmethod
    def check_trend_confirmation(htf_df, signal_type):
        """
        Validates the signal against the Higher Timeframe (H4) trend.
        Uses the 200 EMA as the institutional trend baseline.
        """
        if len(htf_df) < Config.TREND_EMA:
            return True # Not enough data, skip check

        # Calculate 200 EMA
        ema = htf_df['close'].ewm(span=Config.TREND_EMA, adjust=False).mean().iloc[-1]
        current_price = htf_df['close'].iloc[-1]
        
        is_bullish = current_price > ema
        
        if signal_type == "BULLISH_BREAKOUT" and not is_bullish:
            return False, "Against H4 Downtrend (Price < 200 EMA)"
        
        if signal_type == "BEARISH_BREAKOUT" and is_bullish:
            return False, "Against H4 Uptrend (Price > 200 EMA)"
            
        return True, "Trend Aligned"
