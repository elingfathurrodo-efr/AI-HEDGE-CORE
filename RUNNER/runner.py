"""
RUNNER.PY - MAIN ORGANISM RUNNER
==================================
Connects all brains to the market world.
Reads market data -> runs best organism brain -> writes signal.json
"""
import json, os, sys, time, requests, traceback
from datetime import datetime, timezone

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_PATH)

from DNA.immunity    import ImmunitySystem
from DNA.regeneration import RegenerationSystem
from SECURITY.trauma_system import TraumaSystem

SIGNAL_FILE = os.path.join(BASE_PATH, "signal.json")
ORGANISMS_DIR = os.path.join(BASE_PATH, "ORGANISMS")

class Runner:
    def __init__(self):
        self.immune   = ImmunitySystem(BASE_PATH)
        self.regen    = RegenerationSystem(BASE_PATH)
        self.trauma   = TraumaSystem(BASE_PATH)
        self.active_organism = None
        self._load_active_organism()

    # --------------------------------------------------
    # ORGANISM SELECTION
    # --------------------------------------------------
    def _load_active_organism(self):
        """Load the best-performing organism"""
        best_id, best_score = None, -999
        for org_id in os.listdir(ORGANISMS_DIR):
            org_path = os.path.join(ORGANISMS_DIR, org_id)
            if not os.path.isdir(org_path):
                continue
            # Skip quarantined
            if os.path.exists(os.path.join(org_path, "QUARANTINED.txt")):
                continue
            mem_path = os.path.join(org_path, "memory.json")
            if os.path.exists(mem_path):
                with open(mem_path) as f:
                    mem = json.load(f)
                score = mem.get("total_profit", 0) - mem.get("total_loss", 0)
                score = score * (1 + mem.get("win_rate", 0))
                if score > best_score:
                    best_score = score
                    best_id = org_id
        if best_id:
            self.active_organism = best_id
            print(f"[RUNNER] Active organism: {best_id} (score: {best_score:.4f})")
        else:
            # Fallback to organism_001
            self.active_organism = "organism_001"
            print(f"[RUNNER] Fallback to organism_001")

    # --------------------------------------------------
    # MARKET DATA
    # --------------------------------------------------
    def get_market_data(self, symbol="XAUUSD", count=100) -> list:
        """
        Fetch market candles from free API.
        Uses Yahoo Finance or Alpha Vantage (free tier).
        Returns list of candle dicts.
        """
        candles = []
        try:
            # Yahoo Finance - free, no key needed
            yf_symbol = "GC=F" if symbol == "XAUUSD" else symbol
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}?interval=1m&range=1d"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            chart = data["chart"]["result"][0]
            timestamps = chart["timestamp"]
            ohlcv = chart["indicators"]["quote"][0]
            for i in range(min(count, len(timestamps))):
                if ohlcv["open"][i] is None:
                    continue
                candles.append({
                    "time":   timestamps[i],
                    "open":   ohlcv["open"][i],
                    "high":   ohlcv["high"][i],
                    "low":    ohlcv["low"][i],
                    "close":  ohlcv["close"][i],
                    "volume": ohlcv["volume"][i] or 0
                })
            print(f"[RUNNER] Got {len(candles)} candles for {symbol} via Yahoo")
        except Exception as e:
            print(f"[RUNNER] Yahoo fetch error: {e}, using mock data")
            # Fallback mock data for testing
            import random
            price = 2350.0
            for i in range(count):
                change = random.uniform(-5, 5)
                price  = max(100, price + change)
                candles.append({
                    "time":   int(time.time()) - (count - i) * 60,
                    "open":   price - abs(change),
                    "high":   price + abs(change) * 0.5,
                    "low":    price - abs(change) * 0.5,
                    "close":  price,
                    "volume": random.randint(100, 1000)
                })
        return candles

    def get_current_session(self) -> str:
        """Determine current market session"""
        now = datetime.now(timezone.utc)
        h = now.hour
        if 0 <= h < 9:
            return "Asia"
        elif 8 <= h < 17:
            return "London"
        elif 13 <= h < 22:
            return "NewYork"
        return "Closed"

    # --------------------------------------------------
    # BRAIN EXECUTION
    # --------------------------------------------------
    def run_organism_brain(self, candles: list, session: str) -> dict:
        """Load and run active organism's brain"""
        org_id = self.active_organism
        brain_path = os.path.join(ORGANISMS_DIR, org_id, "brain.py")
        dna_path   = os.path.join(ORGANISMS_DIR, org_id, "dna.json")

        if not os.path.exists(brain_path) or not os.path.exists(dna_path):
            print(f"[RUNNER] Missing brain files for {org_id}")
            return {"signal": "NONE"}

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"brain_{org_id}", brain_path)
            brain_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(brain_mod)
            brain = brain_mod.OrganismBrain(org_id, BASE_PATH)
            result = brain.decide_signal(candles, session)
            return result
        except Exception as e:
            print(f"[RUNNER] Brain error for {org_id}: {e}")
            self.trauma.record_error(org_id, str(e))
            # Check if should rollback
            if self.trauma.should_rollback(org_id):
                print(f"[RUNNER] Triggering rollback for {org_id}")
                self.regen.rollback_brain(org_id)
            return {"signal": "NONE"}

    # --------------------------------------------------
    # SIGNAL WRITING
    # --------------------------------------------------
    def write_signal(self, signal_data: dict):
        """Write signal.json for MT5 EA to read"""
        signal_data["generated_at"] = datetime.utcnow().isoformat()
        signal_data["valid_seconds"] = 65  # Valid for 1 candle + buffer
        with open(SIGNAL_FILE, "w") as f:
            json.dump(signal_data, f, indent=2)
        print(f"[RUNNER] Signal written: {signal_data.get('signal')} | {signal_data.get('reason','')}")

    # --------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------
    def run_once(self, symbol="XAUUSD"):
        """Run one cycle: fetch -> analyze -> signal"""
        # Immune check first
        if not self.immune.validate_dna():
            print("[RUNNER] DNA compromised! Halting.")
            return

        candles = self.get_market_data(symbol)
        session = self.get_current_session()
        print(f"[RUNNER] Session: {session}, Candles: {len(candles)}")

        if len(candles) < 30:
            self.write_signal({"signal": "NONE", "reason": "Not enough data"})
            return

        signal = self.run_organism_brain(candles, session)
        signal["symbol"]  = symbol
        signal["session"] = session
        self.write_signal(signal)
        return signal

    def run_loop(self, symbol="XAUUSD", interval_seconds=60):
        """Continuous loop - run every minute"""
        print(f"[RUNNER] Starting loop for {symbol}, interval={interval_seconds}s")
        while True:
            try:
                result = self.run_once(symbol)
                print(f"[RUNNER] Cycle done: {result}")
            except Exception as e:
                print(f"[RUNNER] Loop error: {e}")
                traceback.print_exc()
            time.sleep(interval_seconds)

if __name__ == "__main__":
    runner = Runner()
    result = runner.run_once()
    print("Signal:", json.dumps(result, indent=2))
