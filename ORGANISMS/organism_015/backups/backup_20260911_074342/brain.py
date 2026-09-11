"""
BRAIN TEMPLATE - BASE BRAIN THAT ALL ORGANISMS INHERIT
=======================================================
AI CAN MODIFY COPIES OF THIS FILE (in each organism folder)
AI CANNOT MODIFY THIS TEMPLATE DIRECTLY
"""
import json, os, math, random
from datetime import datetime

class OrganismBrain:
    """
    Core brain logic. Each organism gets its own copy.
    The AI can rewrite this class's methods (in organism copies),
    but cannot change DNA/immunity/security files.
    """
    def __init__(self, organism_id: str, base_path: str = "."):
        self.organism_id = organism_id
        self.base_path = base_path
        self.dna = self._load_dna()
        self.memory = self._load_memory()

    def _load_dna(self) -> dict:
        dna_path = os.path.join(self.base_path, f"ORGANISMS/{self.organism_id}/dna.json")
        with open(dna_path, "r") as f:
            return json.load(f)

    def _load_memory(self) -> dict:
        mem_path = os.path.join(self.base_path, f"ORGANISMS/{self.organism_id}/memory.json")
        if os.path.exists(mem_path):
            with open(mem_path, "r") as f:
                return json.load(f)
        return {"trade_history": [], "market_patterns": []}

    def save_memory(self):
        mem_path = os.path.join(self.base_path, f"ORGANISMS/{self.organism_id}/memory.json")
        with open(mem_path, "w") as f:
            json.dump(self.memory, f, indent=2)

    # =============================================
    # STRATEGY ANALYSIS - AI CAN EVOLVE THESE
    # =============================================

    def analyze_breakout(self, candles: list) -> dict:
        """S1: Breakout strategy"""
        if len(candles) < 50:
            return {"signal": "NONE", "confidence": 0}
        highs = [c["high"] for c in candles[-50:]]
        lows  = [c["low"]  for c in candles[-50:]]
        resistance = max(highs[:-1])
        support    = min(lows[:-1])
        current    = candles[-1]["close"]
        atr        = self._calc_atr(candles, 14)

        if current > resistance + (atr * 0.1):
            return {"signal": "BUY", "confidence": 0.8, "reason": f"Breakout resistance {resistance:.2f}"}
        elif current < support - (atr * 0.1):
            return {"signal": "SELL", "confidence": 0.8, "reason": f"Breakout support {support:.2f}"}
        return {"signal": "NONE", "confidence": 0}

    def analyze_trend(self, candles: list) -> dict:
        """S2: Trend Following"""
        if len(candles) < 50:
            return {"signal": "NONE", "confidence": 0}
        closes = [c["close"] for c in candles]
        ma_fast = self._calc_ma(closes, self.dna.get("ma_fast", 8))
        ma_slow = self._calc_ma(closes, self.dna.get("ma_slow", 21))
        adx     = self._calc_adx_simple(candles, 14)

        if ma_fast > ma_slow and adx > 20:
            return {"signal": "BUY", "confidence": 0.7, "reason": f"MA{self.dna['ma_fast']} cross up, ADX={adx:.1f}"}
        elif ma_fast < ma_slow and adx > 20:
            return {"signal": "SELL", "confidence": 0.7, "reason": f"MA{self.dna['ma_fast']} cross down, ADX={adx:.1f}"}
        return {"signal": "NONE", "confidence": 0}

    def analyze_momentum(self, candles: list) -> dict:
        """S3: Momentum"""
        if len(candles) < 30:
            return {"signal": "NONE", "confidence": 0}
        closes = [c["close"] for c in candles]
        rsi    = self._calc_rsi(closes, self.dna.get("rsi_period", 14))
        macd_line, signal_line = self._calc_macd(closes)

        if rsi > 55 and macd_line > signal_line and macd_line > 0:
            return {"signal": "BUY", "confidence": 0.75, "reason": f"RSI={rsi:.1f} MACD bullish"}
        elif rsi < 45 and macd_line < signal_line and macd_line < 0:
            return {"signal": "SELL", "confidence": 0.75, "reason": f"RSI={rsi:.1f} MACD bearish"}
        return {"signal": "NONE", "confidence": 0}

    def analyze_mean_reversion(self, candles: list) -> dict:
        """S4: Mean Reversion"""
        if len(candles) < 20:
            return {"signal": "NONE", "confidence": 0}
        closes = [c["close"] for c in candles]
        bb_upper, bb_mid, bb_lower = self._calc_bollinger(closes, 20, 2)
        rsi = self._calc_rsi(closes, 14)
        current = closes[-1]

        if current < bb_lower and rsi < self.dna.get("rsi_oversold", 30):
            return {"signal": "BUY", "confidence": 0.65, "reason": f"Below BB lower, RSI={rsi:.1f}"}
        elif current > bb_upper and rsi > self.dna.get("rsi_overbought", 70):
            return {"signal": "SELL", "confidence": 0.65, "reason": f"Above BB upper, RSI={rsi:.1f}"}
        return {"signal": "NONE", "confidence": 0}

    def analyze_scalping(self, candles: list) -> dict:
        """S5: Scalping Micro"""
        if len(candles) < 10:
            return {"signal": "NONE", "confidence": 0}
        closes = [c["close"] for c in candles]
        volumes = [c.get("volume", 1) for c in candles]
        avg_vol = sum(volumes[-10:]) / 10
        cur_vol = volumes[-1]
        change  = closes[-1] - closes[-2]
        atr     = self._calc_atr(candles, 5)

        if cur_vol > avg_vol * 1.5 and change > atr * 0.05:
            return {"signal": "BUY", "confidence": 0.6, "reason": "Scalp: volume spike up"}
        elif cur_vol > avg_vol * 1.5 and change < -atr * 0.05:
            return {"signal": "SELL", "confidence": 0.6, "reason": "Scalp: volume spike down"}
        return {"signal": "NONE", "confidence": 0}

    def analyze_session_breakout(self, candles: list, current_session: str) -> dict:
        """S6: Session Breakout"""
        session_opens = ["Asia", "London", "NewYork"]
        if current_session not in session_opens:
            return {"signal": "NONE", "confidence": 0}
        if len(candles) < 10:
            return {"signal": "NONE", "confidence": 0}
        atr   = self._calc_atr(candles, 10)
        change = candles[-1]["close"] - candles[-10]["open"]
        if change > atr * 0.3:
            return {"signal": "BUY", "confidence": 0.7, "reason": f"{current_session} session breakout up"}
        elif change < -atr * 0.3:
            return {"signal": "SELL", "confidence": 0.7, "reason": f"{current_session} session breakout down"}
        return {"signal": "NONE", "confidence": 0}

    def analyze_sr_bounce(self, candles: list) -> dict:
        """S7: Support/Resistance Bounce"""
        if len(candles) < 20:
            return {"signal": "NONE", "confidence": 0}
        highs  = [c["high"]  for c in candles[-20:]]
        lows   = [c["low"]   for c in candles[-20:]]
        closes = [c["close"] for c in candles[-20:]]
        resistance = sorted(highs)[-3]
        support    = sorted(lows)[2]
        current    = closes[-1]
        atr        = self._calc_atr(candles, 14)
        rsi        = self._calc_rsi(closes, 14)

        if abs(current - support) < atr * 0.2 and rsi < 45:
            return {"signal": "BUY", "confidence": 0.72, "reason": f"SR bounce at support {support:.2f}"}
        elif abs(current - resistance) < atr * 0.2 and rsi > 55:
            return {"signal": "SELL", "confidence": 0.72, "reason": f"SR bounce at resistance {resistance:.2f}"}
        return {"signal": "NONE", "confidence": 0}

    def decide_signal(self, candles: list, current_session: str = "London") -> dict:
        """
        Combine all 7 strategies + memory learning.
        Returns final trading signal.
        """
        strategy = self.dna.get("strategy", "combined")
        signals = []

        all_analyses = [
            self.analyze_breakout(candles),
            self.analyze_trend(candles),
            self.analyze_momentum(candles),
            self.analyze_mean_reversion(candles),
            self.analyze_scalping(candles),
            self.analyze_session_breakout(candles, current_session),
            self.analyze_sr_bounce(candles)
        ]

        buy_votes  = sum(1 for a in all_analyses if a["signal"] == "BUY")
        sell_votes = sum(1 for a in all_analyses if a["signal"] == "SELL")
        max_confidence = max((a.get("confidence",0) for a in all_analyses), default=0)
        best_reason    = next((a.get("reason","") for a in all_analyses if a.get("confidence",0) == max_confidence), "")

        aggression = self.dna.get("aggressiveness", 0.3)
        min_votes  = 2 if aggression < 0.5 else 1

        if buy_votes > sell_votes and buy_votes >= min_votes:
            return {
                "signal": "BUY",
                "confidence": max_confidence,
                "votes": buy_votes,
                "reason": best_reason,
                "organism_id": self.organism_id,
                "lot": self.dna.get("risk", 0.01),
                "sl_points": self.dna.get("sl_points", 200),
                "tp_ratio":  self.dna.get("tp_ratio", 2.0),
                "timestamp": datetime.utcnow().isoformat()
            }
        elif sell_votes > buy_votes and sell_votes >= min_votes:
            return {
                "signal": "SELL",
                "confidence": max_confidence,
                "votes": sell_votes,
                "reason": best_reason,
                "organism_id": self.organism_id,
                "lot": self.dna.get("risk", 0.01),
                "sl_points": self.dna.get("sl_points", 200),
                "tp_ratio":  self.dna.get("tp_ratio", 2.0),
                "timestamp": datetime.utcnow().isoformat()
            }
        return {"signal": "NONE", "confidence": 0, "organism_id": self.organism_id}

    def learn_from_trade(self, trade_result: dict):
        """Update memory from completed trade"""
        self.memory["total_trades"] = self.memory.get("total_trades", 0) + 1
        if trade_result.get("profit", 0) > 0:
            self.memory["win_trades"] = self.memory.get("win_trades", 0) + 1
            self.memory["total_profit"] = self.memory.get("total_profit", 0) + trade_result["profit"]
        else:
            self.memory["loss_trades"] = self.memory.get("loss_trades", 0) + 1
            self.memory["total_loss"]   = self.memory.get("total_loss", 0) + abs(trade_result.get("profit", 0))

        total = self.memory["total_trades"]
        wins  = self.memory["win_trades"]
        self.memory["win_rate"] = wins / total if total > 0 else 0
        self.memory["trade_history"].append({
            "time":   datetime.utcnow().isoformat(),
            "signal": trade_result.get("signal"),
            "profit": trade_result.get("profit", 0),
            "strategy": trade_result.get("strategy", "unknown")
        })
        # Keep only last 1000 trades in memory
        self.memory["trade_history"] = self.memory["trade_history"][-1000:]
        self.save_memory()

    # =============================================
    # TECHNICAL INDICATORS
    # =============================================
    def _calc_ma(self, data: list, period: int) -> float:
        if len(data) < period:
            return data[-1] if data else 0
        return sum(data[-period:]) / period

    def _calc_rsi(self, closes: list, period: int = 14) -> float:
        if len(closes) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, period + 1):
            diff = closes[-i] - closes[-i-1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _calc_macd(self, closes: list, fast=12, slow=26, signal=9):
        if len(closes) < slow + signal:
            return 0, 0
        ema_fast = self._calc_ema(closes, fast)
        ema_slow = self._calc_ema(closes, slow)
        macd_line = ema_fast - ema_slow
        return macd_line, macd_line * 0.9  # Simplified signal

    def _calc_ema(self, data: list, period: int) -> float:
        if len(data) < period:
            return data[-1] if data else 0
        k = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for price in data[period:]:
            ema = price * k + ema * (1 - k)
        return ema

    def _calc_atr(self, candles: list, period: int = 14) -> float:
        if len(candles) < period + 1:
            return 1.0
        trs = []
        for i in range(1, period + 1):
            high = candles[-i]["high"]
            low  = candles[-i]["low"]
            prev_close = candles[-i-1]["close"]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)
        return sum(trs) / period

    def _calc_bollinger(self, closes: list, period=20, std_dev=2):
        if len(closes) < period:
            c = closes[-1]
            return c*1.01, c, c*0.99
        subset = closes[-period:]
        mid = sum(subset) / period
        variance = sum((x - mid)**2 for x in subset) / period
        std = math.sqrt(variance)
        return mid + std_dev*std, mid, mid - std_dev*std

    def _calc_adx_simple(self, candles: list, period=14) -> float:
        """Simplified ADX approximation"""
        if len(candles) < period:
            return 0
        ranges = [c["high"] - c["low"] for c in candles[-period:]]
        return (sum(ranges) / period) * 10  # Normalize


if __name__ == "__main__":
    print("Brain template loaded. Copy to ORGANISMS/organism_XXX/brain.py")
