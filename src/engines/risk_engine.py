import MetaTrader5 as mt5
from src.config import Config
import logging

logger = logging.getLogger(__name__)

class RiskEngine:
    def __init__(self, risk_per_trade=0.01, min_rr=1.5):
        self.risk_pct = risk_per_trade
        self.min_rr = min_rr

    def calculate_trade_params(self, balance, symbol_info, signal, zones):
        """
        Determines SL, TP, and Lot Size using S/R zones and account risk.
        """
        if not symbol_info:
            return {"valid": False, "reason": "No symbol info"}

        entry_price = signal['price']
        
        # SL/TP Selection based on Signal Direction
        if signal['type'] == "BULLISH_BREAKOUT":
            # SL placed slightly below the broken zone mid-line
            sl = signal['zone_mid'] - (symbol_info.point * 100) # 10 pip buffer
            # TP targeted at the next highest resistance zone
            tp = self._find_next_target(entry_price, zones, "UP", symbol_info.point)
        else:
            # SL placed slightly above the broken zone mid-line
            sl = signal['zone_mid'] + (symbol_info.point * 100)
            tp = self._find_next_target(entry_price, zones, "DOWN", symbol_info.point)

        # Risk Math
        risk_amount_money = balance * self.risk_pct
        lot_size = self._calculate_lots(entry_price, sl, symbol_info, risk_amount_money)
        
        # Reward:Risk Validation
        risk_pips = abs(entry_price - sl)
        reward_pips = abs(tp - entry_price)
        rr = reward_pips / risk_pips if risk_pips > 0 else 0
        
        return {
            "sl": round(sl, symbol_info.digits),
            "tp": round(tp, symbol_info.digits),
            "lots": lot_size,
            "rr": round(rr, 2),
            "valid": rr >= self.min_rr and lot_size >= symbol_info.volume_min
        }

    def _find_next_target(self, price, zones, direction, point):
        """Identifies the next S/R zone to use as a TP target."""
        if direction == "UP":
            targets = [z['mid'] for z in zones if z['mid'] > price + (point * 10)]
            return min(targets) if targets else price + (point * 500) # Default 50 pips if no zone
        else:
            targets = [z['mid'] for z in zones if z['mid'] < price - (point * 10)]
            return max(targets) if targets else price - (point * 500)

    def _calculate_lots(self, entry, sl, info, risk_money):
        """Calculates lot size based on fixed fractional risk."""
        point_delta = abs(entry - sl)
        if point_delta == 0: return 0
        
        # tick_value is the profit in deposit currency for 1 lot per 1 tick
        value_per_point = info.trade_tick_value / info.trade_tick_size
        lots = risk_money / (point_delta * value_per_point)
        
        lots = round(lots / info.volume_step) * info.volume_step
        return max(info.volume_min, min(info.volume_max, round(lots, 2)))

    def manage_trailing_stop(self, position, symbol_info):
        """
        Calculates a new SL to trail the price, protecting profits.
        """
        current_price = mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask
        trailing_dist = Config.TRAILING_STOP_PIPS * symbol_info.point * 10
        
        if position.type == mt5.POSITION_TYPE_BUY:
            new_sl = current_price - trailing_dist
            if new_sl > position.sl + (symbol_info.point * 10): # Only move if profit increased by 1 pip
                return round(new_sl, symbol_info.digits)
        else:
            new_sl = current_price + trailing_dist
            if new_sl < position.sl - (symbol_info.point * 10) or position.sl == 0:
                return round(new_sl, symbol_info.digits)
        
        return None
