import MetaTrader5 as mt5
import logging
from src.database import TradingDatabase

logger = logging.getLogger(__name__)
db = TradingDatabase()

class TradeExecutor:
    @staticmethod
    def get_filling_mode(symbol):
        """Detects the correct filling mode for the broker symbol."""
        sym_info = mt5.symbol_info(symbol)
        if not sym_info: return mt5.ORDER_FILLING_IOC
        
        # Bits: 1 = FOK, 2 = IOC
        filling = sym_info.filling_mode
        if filling & 1: # SYMBOL_FILLING_FOK
            return mt5.ORDER_FILLING_FOK
        elif filling & 2: # SYMBOL_FILLING_IOC
            return mt5.ORDER_FILLING_IOC
        else:
            return mt5.ORDER_FILLING_RETURN

    @staticmethod
    def open_position(symbol, signal_type, lots, sl, tp, reason="", criteria=""):
        """Sends an execution request to MT5 with dynamic filling and safety TP/SL."""
        try:
            order_type = mt5.ORDER_TYPE_BUY if signal_type in ["BULLISH_BREAKOUT", "BUY"] else mt5.ORDER_TYPE_SELL
            tick = mt5.symbol_info_tick(symbol)
            if tick is None: return False, "No Price Feed"
                
            filling_mode = TradeExecutor.get_filling_mode(symbol)
            price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(lots),
                "type": order_type,
                "price": price,
                "sl": float(sl),
                "tp": float(tp),
                "magic": 123456,
                "comment": "Finter Neural",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }

            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                # If failed due to filling, try RETURN mode
                if result.retcode in [mt5.TRADE_RETCODE_INVALID_FILL]:
                    request["type_filling"] = mt5.ORDER_FILLING_RETURN
                    result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                err_msg = f"{result.comment} (Code: {result.retcode})"
                logger.error(f"ORDER FAILED: {err_msg}")
                return False, err_msg
            
            # Record to Local Database
            db.log_trade(symbol, signal_type, lots, result.price, sl, tp, reason, criteria)
            return True, f"Executed at {result.price}"
        except Exception as e:
            logger.critical(f"Execution Engine Crash: {e}")
            return False, str(e)

    @staticmethod
    def update_sl(ticket, new_sl):
        """Modifies the Stop Loss of an existing position with error handling."""
        try:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": float(new_sl),
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"TRAIL SYNC: Ticket #{ticket} moved SL to {new_sl}")
                return True
            return False
        except Exception as e:
            logger.error(f"Trailing Update Failed: {e}")
            return False

    @staticmethod
    def close_partial(ticket, symbol, lots):
        """Closes a portion of a position (e.g. 50% at TP1)."""
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position: return False
            
            order_type = mt5.ORDER_TYPE_SELL if position[0].type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).bid if order_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": symbol,
                "volume": float(lots),
                "type": order_type,
                "price": price,
                "magic": 123456,
                "comment": "Partial TP",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
        except Exception as e:
            logger.error(f"Partial Close Error: {e}")
            return False

    @staticmethod
    def modify_position(ticket, sl, tp):
        """Modifies both SL and TP for an existing position."""
        try:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": float(sl),
                "tp": float(tp),
            }
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
        except Exception as e:
            logger.error(f"Modify Position Error: {e}")
            return False
