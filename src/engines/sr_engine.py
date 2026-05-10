import pandas as pd
import numpy as np

class SREngine:
    def __init__(self, zone_threshold_pips=15):
        self.zone_threshold = zone_threshold_pips

    def get_zones(self, df):
        """Detects and clusters support/resistance zones."""
        pivots = self._find_pivots(df)
        if pivots.empty:
            return []
        return self._cluster_pivots(pivots)

    def _find_pivots(self, df, window=5):
        """Identifies fractal Highs and Lows."""
        df['is_high'] = (df['high'] == df['high'].rolling(window=window*2+1, center=True).max())
        df['is_low'] = (df['low'] == df['low'].rolling(window=window*2+1, center=True).min())
        
        highs = df[df['is_high']][['high']].rename(columns={'high': 'price'})
        lows = df[df['is_low']][['low']].rename(columns={'low': 'price'})
        
        return pd.concat([highs, lows])

    def _cluster_pivots(self, pivots):
        """Groups prices into zones based on proximity."""
        prices = sorted(pivots['price'].values)
        zones = []
        if not prices: return zones

        current_group = [prices[0]]
        
        for i in range(1, len(prices)):
            # If price is within threshold of the group average, add to group
            if prices[i] - np.mean(current_group) < self.zone_threshold * 0.01: # Simplified pip conversion
                current_group.append(prices[i])
            else:
                zones.append({
                    'min': round(min(current_group), 5),
                    'max': round(max(current_group), 5),
                    'mid': round(np.mean(current_group), 5),
                    'strength': len(current_group)
                })
                current_group = [prices[i]]
        
        # Add last group
        zones.append({
            'min': round(min(current_group), 5),
            'max': round(max(current_group), 5),
            'mid': round(np.mean(current_group), 5),
            'strength': len(current_group)
        })
        
        # Sort by strength (most touches)
        return sorted(zones, key=lambda x: x['strength'], reverse=True)

    def get_fvgs(self, df):
        """
        Detects Fair Value Gaps (Imbalances) where price skipped levels.
        Commonly used in Smart Money Concepts (SMC).
        """
        fvgs = []
        if len(df) < 3: return fvgs
        
        for i in range(2, len(df)):
            # Bullish FVG (Gap between Bar 1 High and Bar 3 Low)
            if df.iloc[i-2]['high'] < df.iloc[i]['low']:
                fvgs.append({
                    'min': df.iloc[i-2]['high'],
                    'max': df.iloc[i]['low'],
                    'mid': (df.iloc[i-2]['high'] + df.iloc[i]['low']) / 2,
                    'type': 'BULLISH'
                })
            # Bearish FVG (Gap between Bar 1 Low and Bar 3 High)
            elif df.iloc[i-2]['low'] > df.iloc[i]['high']:
                fvgs.append({
                    'min': df.iloc[i]['high'],
                    'max': df.iloc[i-2]['low'],
                    'mid': (df.iloc[i-2]['low'] + df.iloc[i]['high']) / 2,
                    'type': 'BEARISH'
                })
        return fvgs
