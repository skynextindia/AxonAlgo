class CandleEngine:
    @staticmethod
    def get_confirmed_pattern(df, signal_type):
        """
        Analyzes the last two candles for psychological confirmation.
        Returns the pattern name if found, else None.
        """
        if len(df) < 2:
            return None
            
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        curr_body = abs(curr['close'] - curr['open'])
        prev_body = abs(prev['close'] - prev['open'])
        
        if signal_type == "BULLISH_BREAKOUT":
            if (curr['close'] > curr['open'] and prev['close'] < prev['open'] and 
                curr['close'] >= prev['open'] and curr['open'] <= prev['close']):
                return "ENGULFING"
            
            lower_wick = min(curr['open'], curr['close']) - curr['low']
            if lower_wick > (curr_body * 2) and curr_body > 0:
                return "HAMMER"
            
            upper_wick = curr['high'] - max(curr['open'], curr['close'])
            if curr_body > prev_body and upper_wick < (curr_body * 0.2):
                return "MOMENTUM"

        elif signal_type == "BEARISH_BREAKOUT":
            if (curr['close'] < curr['open'] and prev['close'] > prev['open'] and 
                curr['close'] <= prev['open'] and curr['open'] >= prev['close']):
                return "ENGULFING"
            
            upper_wick = curr['high'] - max(curr['open'], curr['close'])
            if upper_wick > (curr_body * 2) and curr_body > 0:
                return "SHOOTING_STAR"
            
            lower_wick = min(curr['open'], curr['close']) - curr['low']
            if curr_body > prev_body and lower_wick < (curr_body * 0.2):
                return "MOMENTUM"
            
        return None
