import pandas as pd
import numpy as np

class BreakoutEngine:
    def __init__(self, volume_ma_period=20, atr_period=14):
        self.vol_period = volume_ma_period
        self.atr_period = atr_period

    def check_breakout(self, df, zones):
        """
        Validates if current price is breaking through a zone with momentum.
        """
        if len(df) < self.vol_period + 1 or not zones:
            return None

        # Calculate Technical Indicators needed for validation
        df = df.copy()
        df['atr'] = self._calculate_atr(df)
        df['vol_ma'] = df['tick_volume'].rolling(self.vol_period).mean()
        
        current_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]
        current_atr = df['atr'].iloc[-1]
        rel_volume = current_candle['tick_volume'] / df['vol_ma'].iloc[-1] if df['vol_ma'].iloc[-1] > 0 else 0

        for zone in zones:
            # BULLISH BREAKOUT logic
            # Price closes above resistance and previous close was below/inside it
            if current_candle['close'] > zone['max'] and prev_candle['close'] <= zone['max']:
                if self._validate_momentum(current_candle, current_atr, rel_volume):
                    return {
                        "type": "BULLISH_BREAKOUT", 
                        "zone_mid": zone['mid'], 
                        "confidence": round(rel_volume, 2),
                        "price": current_candle['close']
                    }

            # BEARISH BREAKOUT logic
            # Price closes below support and previous close was above/inside it
            if current_candle['close'] < zone['min'] and prev_candle['close'] >= zone['min']:
                if self._validate_momentum(current_candle, current_atr, rel_volume):
                    return {
                        "type": "BEARISH_BREAKOUT", 
                        "zone_mid": zone['mid'], 
                        "confidence": round(rel_volume, 2),
                        "price": current_candle['close']
                    }

        return None

    def _validate_momentum(self, candle, atr, rel_vol):
        """Filters out weak movements or fakeouts."""
        body_size = abs(candle['close'] - candle['open'])
        # 1. Candle body must be significant relative to ATR
        # 2. Volume must be above average
        return body_size > (0.4 * atr) and rel_vol > 1.1

    def _calculate_atr(self, df):
        high_low = df['high'] - df['low']
        high_cp = np.abs(df['high'] - df['close'].shift())
        low_cp = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
        return tr.rolling(self.atr_period).mean()
