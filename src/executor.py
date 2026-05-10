import MetaTrader5 as mt5

class TradeExecutor:
    @staticmethod
    def open_position(symbol, signal_type, lots, sl, tp):
        """Sends an execution request to MT5."""
        
        order_type = mt5.ORDER_TYPE_BUY if signal_type == "BULLISH_BREAKOUT" else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
        
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
            print(f"FAILED to open order: {result.comment} (Code: {result.retcode})")
            return False
        
        print(f"SUCCESS: {signal_type} opened at {result.price} | Lots: {lots} | SL: {sl} | TP: {tp}")
        return True

    @staticmethod
    def update_sl(ticket, new_sl):
        """Modifies the Stop Loss of an existing position."""
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": float(new_sl),
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"TRAILED SL: Ticket #{ticket} moved to {new_sl}")
            return True
        return False
