import MetaTrader5 as mt5
import logging

logger = logging.getLogger(__name__)

class TradeExecutor:
    @staticmethod
    def open_position(symbol, signal_type, lots, sl, tp):
        """Sends an execution request to MT5 with error handling."""
        try:
            order_type = mt5.ORDER_TYPE_BUY if signal_type == "BULLISH_BREAKOUT" else mt5.ORDER_TYPE_SELL
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Could not get tick info for {symbol}")
                return False
                
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
                "comment": "Axon Breakout Bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"ORDER FAILED: {result.comment} (Code: {result.retcode})")
                return False
            
            logger.info(f"ORDER SUCCESS: {signal_type} @ {result.price} | Lots: {lots}")
            return True
        except Exception as e:
            logger.critical(f"Execution Engine Crash: {e}")
            return False

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
