class CandleEngine:
    @staticmethod
    def is_confirmed(df, signal_type):
        """
        Analyzes the last two candles for psychological confirmation.
        Returns True if a strong reversal/momentum pattern is present.
        """
        if len(df) < 2:
            return False
            
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Determine body and wick sizes
        curr_body = abs(curr['close'] - curr['open'])
        prev_body = abs(prev['close'] - prev['open'])
        
        if signal_type == "BULLISH_BREAKOUT":
            # Pattern 1: Bullish Engulfing (Current bullish body swallows previous bearish body)
            is_engulfing = (curr['close'] > curr['open'] and 
                           prev['close'] < prev['open'] and 
                           curr['close'] >= prev['open'] and 
                           curr['open'] <= prev['close'])
            
            # Pattern 2: Bullish Hammer (Long lower wick, small body at top)
            lower_wick = min(curr['open'], curr['close']) - curr['low']
            is_hammer = lower_wick > (curr_body * 2) and curr_body > 0
            
            # Pattern 3: Strong Momentum (Large body, little to no upper wick)
            upper_wick = curr['high'] - max(curr['open'], curr['close'])
            is_momentum = curr_body > prev_body and upper_wick < (curr_body * 0.2)
            
            return is_engulfing or is_hammer or is_momentum

        elif signal_type == "BEARISH_BREAKOUT":
            # Pattern 1: Bearish Engulfing
            is_engulfing = (curr['close'] < curr['open'] and 
                           prev['close'] > prev['open'] and 
                           curr['close'] <= prev['open'] and 
                           curr['open'] >= prev['close'])
            
            # Pattern 2: Shooting Star (Long upper wick, small body at bottom)
            upper_wick = curr['high'] - max(curr['open'], curr['close'])
            is_star = upper_wick > (curr_body * 2) and curr_body > 0
            
            # Pattern 3: Strong Momentum (Large body, little to no lower wick)
            lower_wick = min(curr['open'], curr['close']) - curr['low']
            is_momentum = curr_body > prev_body and lower_wick < (curr_body * 0.2)
            
            return is_engulfing or is_star or is_momentum
            
        return False
