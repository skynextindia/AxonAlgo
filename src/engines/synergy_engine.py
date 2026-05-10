import pandas as pd
import pandas_ta as ta
import numpy as np

class SynergyEngine:
    def __init__(self):
        self.weights = {
            "technical": 0.4,
            "momentum": 0.2,
            "strength": 0.2,
            "sentiment": 0.2
        }

    def analyze(self, symbol, df, currency_strength=None, ai_sentiment=0.5):
        """
        Master Analysis: Returns a Direction and a Probability Alpha Score.
        """
        # 1. Technical Score (SR + Trend)
        tech_score = self._calc_technical_score(df)
        
        # 2. Momentum Score (RSI + MACD)
        mom_score = self._calc_momentum_score(df)
        
        # 3. Strength Score (Contextual)
        str_score = ai_sentiment * 100 # Placeholder for strength matrix
        
        # 4. Sentiment Score (AI Research)
        sent_score = ai_sentiment * 100
        
        # Aggregate Alpha
        alpha_score = (tech_score * self.weights['technical']) + \
                      (mom_score * self.weights['momentum']) + \
                      (str_score * self.weights['strength']) + \
                      (sent_score * self.weights['sentiment'])
        
        direction = "FLAT"
        if alpha_score > 70:
            # Determine direction based on Trend
            ema_200 = df['close'].iloc[-1] > df['ema_200'].iloc[-1]
            direction = "BUY" if ema_200 else "SELL"
            
        return {
            "direction": direction,
            "alpha": round(alpha_score, 2),
            "breakdown": {
                "technical": round(tech_score, 2),
                "momentum": round(mom_score, 2),
                "sentiment": round(sent_score, 2)
            },
            "reason": self._generate_synergy_reason(direction, alpha_score)
        }

    def _calc_technical_score(self, df):
        # EMA Trend + Price Action
        df['ema_50'] = ta.ema(df['close'], length=50)
        df['ema_200'] = ta.ema(df['close'], length=200)
        
        curr_price = df['close'].iloc[-1]
        e50 = df['ema_50'].iloc[-1]
        e200 = df['ema_200'].iloc[-1]
        
        score = 50
        if curr_price > e50 > e200: score += 30 # Strong Up
        elif curr_price < e50 < e200: score += 30 # Strong Down
        
        return min(max(score, 0), 100)

    def _calc_momentum_score(self, df):
        rsi = ta.rsi(df['close'], length=14).iloc[-1]
        
        # Mean Reversion Logic
        score = 50
        if rsi < 30: score = 90 # Oversold (Buy Momentum Potential)
        elif rsi > 70: score = 90 # Overbought (Sell Momentum Potential)
        
        return score

    def _generate_synergy_reason(self, direction, alpha):
        if direction == "FLAT": return "Insufficient Alpha for institutional entry."
        return f"Synergy Alpha {alpha}%: High confluence across Technical/Sentiment vectors. Entry authorized."
