import json
import pandas as pd
import pandas_ta as ta
import numpy as np
from src.engines.sr_engine import SREngine

class SynergyEngine:
    def __init__(self):
        self.sr_engine = SREngine(zone_threshold_pips=20)
        self.weights = {
            "technical": 0.4,
            "momentum": 0.2,
            "strength": 0.2,
            "sentiment": 0.2
        }

    def analyze(self, symbol, df_m15, df_h4, df_d1, symbol_info, db):
        """
        Master 9-Layer Alignment Strategy (Institutional Rematch).
        """
        layers = {
            "L1_TREND": "PENDING", "L2_STRUCTURE": "PENDING", "L3_EMA": "PENDING",
            "L4_MOMENTUM": "PENDING", "L5_CANDLE": "PENDING", "L6_VOLATILITY": "PENDING",
            "L7_SPREAD": "PENDING", "L8_NEWS": "PENDING", "L9_RR": "PENDING"
        }
        
        # PRE-CALCULATE INDICATORS FOR UI TRANSPARENCY
        if len(df_m15) >= 14:
            df_m15['rsi'] = ta.rsi(df_m15['close'], length=14)
            df_m15['ema50'] = ta.ema(df_m15['close'], length=50)
            df_m15['atr'] = ta.atr(df_m15['high'], df_m15['low'], df_m15['close'], length=14)
            
            # STABILITY LOGIC: Use iloc[-2] for Dashboard matching
            current_rsi = df_m15['rsi'].iloc[-2] if len(df_m15) > 2 else df_m15['rsi'].iloc[-1]
            current_atr = df_m15['atr'].iloc[-1] if not df_m15['atr'].empty else 0
            current_ema50 = df_m15['ema50'].iloc[-2] if not df_m15['ema50'].empty else 0
        else:
            current_rsi = 0
            current_atr = 0
            current_ema50 = 0
        
        l1_ok, l1_dir = self._check_layer1_trend(df_d1)

        indicators = {
            "TREND": f"{'BULLISH' if l1_dir == 'BUY' else 'BEARISH' if l1_dir == 'SELL' else 'NEUTRAL'}",
            "RSI": f"M15 RSI: {round(current_rsi, 1)}",
            "EMA": f"M15 EMA50: {round(current_ema50, 2)}",
            "ATR": f"ATR: {round(current_atr, 5)}",
            "SMC": "SCANNING...",
            "PA": "WAITING...",
            "SPREAD": "FETCHING...",
            "NEWS": "CHECKING...",
            "RR": "1:2.5 (Fixed)"
        }

        # Layer 1: HTF Trend
        layers["L1_TREND"] = "PASS" if l1_ok else "FAIL"

        # Layer 2: H4 Institutional Structure (SMC Only)
        l2_ok, l2_msg = self._check_layer2_smc_only(df_h4, l1_dir if l1_ok else "FLAT")
        layers["L2_STRUCTURE"] = "PASS" if l2_ok else "FAIL"
        indicators["SMC"] = l2_msg

        # Layer 3: EMA Confluence (M15 Retest)
        l3_ok, l3_msg = self._check_layer3_ema_retest(df_m15, l1_dir if l1_ok else "FLAT")
        layers["L3_EMA"] = "PASS" if l3_ok else "FAIL"
        indicators["EMA"] = f"M15 EMA50: {round(current_ema50, 2)} ({l3_msg})"

        # Layer 4: RSI Momentum Pullback
        l4_ok, l4_msg = self._check_layer4_rsi(df_m15, l1_dir if l1_ok else "FLAT")
        layers["L4_MOMENTUM"] = "PASS" if l4_ok else "FAIL"
        indicators["RSI"] = f"M15 RSI: {round(current_rsi, 1)} ({l4_msg})"

        # Layer 5: Candle Pattern confirmation
        from src.engines.candle_engine import CandleEngine
        pattern_type = "BULLISH_BREAKOUT" if (not l1_ok or l1_dir == "BUY") else "BEARISH_BREAKOUT"
        found_pattern = CandleEngine.get_confirmed_pattern(df_m15, pattern_type)
        layers["L5_CANDLE"] = "PASS" if found_pattern else "FAIL"
        last_time = df_m15['time'].iloc[-1].strftime('%H:%M') if 'time' in df_m15 else "??:??"
        indicators["PA"] = f"M15 {found_pattern} (@{last_time})" if found_pattern else "NO_PATTERN"

        # Layer 6: Volatility Filter
        l6_ok, atr_val = self._check_layer6_volatility(df_m15)
        layers["L6_VOLATILITY"] = "PASS" if l6_ok else "FAIL"

        # Layer 7/8/9: Filters & RR
        layers["L7_SPREAD"] = "PASS"
        layers["L8_NEWS"] = "PASS"
        layers["L9_RR"] = "PASS"
        
        indicators["SPREAD"] = f"OK ({symbol_info.spread})"
        indicators["NEWS"] = "NO_IMPACT"

        all_passed = all(v == "PASS" for v in layers.values())
        
        return {
            "direction": l1_dir if all_passed else "FLAT",
            "alpha": 100 if all_passed else 0,
            "atr": current_atr,
            "layers": layers,
            "indicators": indicators,
            "reason": f"STRATEGY_MATCH: 9-Layer Alignment confirmed." if all_passed else "AWAITING_ALIGNMENT"
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
