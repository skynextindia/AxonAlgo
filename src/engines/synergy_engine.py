import json
import pandas as pd
import pandas_ta as ta
import numpy as np
from src.engines.sr_engine import SREngine
from src.engines.news_engine import NewsEngine
from src.config import Config

class SynergyEngine:
    def __init__(self):
        self.sr_engine = SREngine(zone_threshold_pips=20)
        self.news_engine = NewsEngine(buffer_minutes=60)
        self.weights = {
            "technical": 0.4,
            "momentum": 0.2,
            "strength": 0.2,
            "sentiment": 0.2
        }

    def analyze(self, symbol, df_m15, df_h4, df_d1, symbol_info, db):
        """
        Master 9-Layer Alignment Strategy with Weighted Scalar Scoring.
        Returns alignment_score (0.0-1.0).
        """
        layers = {
            "L1_TREND": 0.0, "L2_STRUCTURE": 0.0, "L3_EMA": 0.0,
            "L4_MOMENTUM": 0.0, "L5_CANDLE": 0.0, "L6_VOLATILITY": 0.0,
            "L7_SPREAD": 0.0, "L8_NEWS": 0.0, "L9_RR": 0.0
        }
        
        # Weights for scalar score (Adjusted for Institutional Bias)
        weights = {
            "L1_TREND": 0.20,      # HTF Context is King
            "L2_STRUCTURE": 0.15,  # SMC Zones
            "L3_EMA": 0.10,        # Dynamic Support
            "L4_MOMENTUM": 0.10,   # RSI Pullback
            "L5_CANDLE": 0.15,     # PA Execution Trigger
            "L6_VOLATILITY": 0.10, # ATR Filter
            "L7_SPREAD": 0.05,     # Execution Cost
            "L8_NEWS": 0.10,       # Macro Filter
            "L9_RR": 0.05          # Math Validation
        }

        # PRE-CALCULATE INDICATORS
        if len(df_m15) >= 14:
            df_m15['rsi'] = ta.rsi(df_m15['close'], length=14)
            df_m15['ema50'] = ta.ema(df_m15['close'], length=50)
            df_m15['atr'] = ta.atr(df_m15['high'], df_m15['low'], df_m15['close'], length=14)
            
            current_rsi = df_m15['rsi'].iloc[-2] if len(df_m15) > 2 else df_m15['rsi'].iloc[-1]
            current_atr = df_m15['atr'].iloc[-1] if not df_m15['atr'].empty else 0
            current_ema50 = df_m15['ema50'].iloc[-2] if not df_m15['ema50'].empty else 0
        else:
            current_rsi, current_atr, current_ema50 = 0, 0, 0
        
        l1_ok, l1_dir = self._check_layer1_trend(df_d1)

        indicators = {
            "TREND": f"{'BULLISH' if l1_dir == 'BUY' else 'BEARISH' if l1_dir == 'SELL' else 'NEUTRAL'}",
            "RSI": f"M15 RSI: {round(current_rsi, 1)}",
            "EMA": f"M15 EMA50: {round(current_ema50, 2)}",
            "ATR": f"ATR: {round(current_atr, 5)}",
            "SMC": "SCANNING...", "PA": "WAITING...", "SPREAD": "FETCHING...", "NEWS": "CHECKING...", "RR": "1:2.5"
        }

        # CALCULATE SCALAR LAYERS
        if l1_ok: layers["L1_TREND"] = 1.0
        
        l2_ok, l2_msg = self._check_layer2_smc_only(df_h4, l1_dir if l1_ok else "FLAT")
        if l2_ok: layers["L2_STRUCTURE"] = 1.0
        indicators["SMC"] = l2_msg

        l3_ok, l3_msg = self._check_layer3_ema_retest(df_m15, l1_dir if l1_ok else "FLAT")
        if l3_ok: layers["L3_EMA"] = 1.0
        indicators["EMA"] = f"M15 EMA50: {round(current_ema50, 2)} ({l3_msg})"

        l4_ok, l4_msg = self._check_layer4_rsi(df_m15, l1_dir if l1_ok else "FLAT")
        if l4_ok: layers["L4_MOMENTUM"] = 1.0
        indicators["RSI"] = f"M15 RSI: {round(current_rsi, 1)} ({l4_msg})"

        from src.engines.candle_engine import CandleEngine
        pattern_type = "BULLISH_BREAKOUT" if (not l1_ok or l1_dir == "BUY") else "BEARISH_BREAKOUT"
        found_pattern = CandleEngine.get_confirmed_pattern(df_m15, pattern_type)
        if found_pattern: layers["L5_CANDLE"] = 1.0
        last_time = df_m15['time'].iloc[-1].strftime('%H:%M') if 'time' in df_m15 else "??:??"
        indicators["PA"] = f"M15 {found_pattern} (@{last_time})" if found_pattern else "NO_PATTERN"

        l6_ok, _ = self._check_layer6_volatility(df_m15)
        if l6_ok: layers["L6_VOLATILITY"] = 1.0

        # Layer 7: Dynamic Spread Filtering
        max_spread = symbol_info.spread_limit if hasattr(symbol_info, 'spread_limit') else Config.MAX_SPREAD_PIPS * 10
        if symbol_info.spread <= max_spread:
            layers["L7_SPREAD"] = 1.0
            indicators["SPREAD"] = f"OK ({symbol_info.spread})"
        else:
            layers["L7_SPREAD"] = 0.0
            indicators["SPREAD"] = f"HIGH ({symbol_info.spread})"
        
        is_news_volatile, news_name = self.news_engine.is_volatile_now(symbol)
        if not is_news_volatile:
            layers["L8_NEWS"] = 1.0
            indicators["NEWS"] = "NO_IMPACT"
        else:
            layers["L8_NEWS"] = 0.0
            indicators["NEWS"] = f"HIGH_IMPACT: {news_name}"

        layers["L9_RR"] = 1.0     # Fixed RR for now
        indicators["RR"] = "1:2.5"

        # Final Scalar Calculation
        alignment_score = sum(layers[k] * weights[k] for k in layers)
        
        # Mapping layers back to PASS/FAIL for UI backward compatibility
        ui_layers = {k: "PASS" if v > 0.5 else "FAIL" for k, v in layers.items()}

        return {
            "direction": l1_dir if alignment_score >= 0.7 else "FLAT",
            "alignment_score": round(alignment_score, 2),
            "alpha": round(alignment_score * 100, 0),
            "atr": current_atr,
            "layers": ui_layers,
            "indicators": indicators,
            "reason": f"ALIGNED: {int(alignment_score*100)}%" if alignment_score >= 0.7 else "DIVERGENCE"
        }

    def _check_layer1_trend(self, df):
        if len(df) < 200: return False, "FLAT"
        df['ema50'] = ta.ema(df['close'], length=50)
        df['ema200'] = ta.ema(df['close'], length=200)
        last = df.iloc[-1]
        is_buy = last['ema50'] > last['ema200'] and last['close'] > last['ema200']
        is_sell = last['ema50'] < last['ema200'] and last['close'] < last['ema200']
        return (True, "BUY") if is_buy else (True, "SELL") if is_sell else (False, "FLAT")

    def _check_layer2_smc_only(self, df_h4, bias):
        if bias == "FLAT": return False, "NO_BIAS"
        last_price = df_h4['close'].iloc[-1]
        
        # Fair Value Gaps
        fvgs = self.sr_engine.get_fvgs(df_h4)
        for fvg in fvgs:
            if fvg['type'] == bias and fvg['min'] <= last_price <= fvg['max']:
                return True, f"SMC FVG: {round(fvg['mid'], 2)}"
        
        # Demand/Supply Zones
        zones = self.sr_engine.get_zones(df_h4)
        for zone in zones:
            if zone['min'] <= last_price <= zone['max']:
                return True, f"SMC ZONE: {round(zone['mid'], 2)}"
        
        return False, "NO_SMC_ZONE"

    def _check_layer3_ema_retest(self, df, bias):
        if len(df) < 50: return False, "DATA_MIN"
        ema50 = ta.ema(df['close'], length=50).iloc[-2]
        price = df['close'].iloc[-1]
        threshold = ema50 * 0.0015
        if abs(price - ema50) < threshold:
            return True, "RETESTING"
        return False, "NO_RETEST"

    def _check_layer4_rsi(self, df, bias):
        rsi = ta.rsi(df['close'], length=14).iloc[-2]
        if bias == "BUY" and rsi < 40: return True, "OVERSOLD"
        if bias == "SELL" and rsi > 60: return True, "OVERBOUGHT"
        return False, "NORMAL"

    def _check_layer6_volatility(self, df):
        atr = ta.atr(df['high'], df['low'], df['close'], length=14).iloc[-1]
        avg_atr = ta.atr(df['high'], df['low'], df['close'], length=14).rolling(20).mean().iloc[-1]
        return (True, atr) if (atr > avg_atr * 0.5 and atr < avg_atr * 3.0) else (False, atr)
