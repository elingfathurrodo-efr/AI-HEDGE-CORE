"""
IMMUNITY.PY - CORE DNA PROTECTION SYSTEM
=========================================
AI CANNOT MODIFY THIS FILE
Protects the organism from:
- Infinite loops
- Suicidal strategies (overtrade, extreme risk)
- DNA corruption
- Memory overflow
- Malicious self-mutations
"""
import json, os, sys, time, traceback, hashlib
from datetime import datetime

# =============================================
# IMMUNE CONSTANTS - HARDCODED, NEVER FROM JSON
# =============================================
MAX_LOT_ABSOLUTE   = 1.0       # Never exceed this lot
MAX_DRAWDOWN_PCT   = 80        # Kill if drawdown > 80%
MAX_TRADES_PER_MIN = 5         # Prevent overtrade
MIN_BALANCE_USD    = 1.0       # Stop if balance < $1
IMMUNE_FILES = [
    "DNA/core_dna.json",
    "DNA/immunity.py",
    "DNA/regeneration.py",
    "SECURITY/trauma_system.py",
    "SECURITY/rollback.py",
    "SECURITY/fund_guardian.py"
]

DNA_SIGNATURE = "DNA_CORE_V1_LOCKED_DO_NOT_MODIFY"

class ImmunitySystem:
    def __init__(self, base_path="."):
        self.base_path = base_path
        self.trade_times = []
        self.errors = []

    def validate_dna(self):
        """Check DNA is not corrupted"""
        dna_path = os.path.join(self.base_path, "DNA/core_dna.json")
        try:
            with open(dna_path, "r") as f:
                dna = json.load(f)
            if dna.get("immutable_signature") != DNA_SIGNATURE:
                self._alert("DNA SIGNATURE MISMATCH! DNA may be corrupted!")
                return False
            return True
        except Exception as e:
            self._alert(f"DNA READ ERROR: {e}")
            return False

    def validate_lot(self, lot: float) -> float:
        """Ensure lot is within safe bounds"""
        lot = max(0.01, min(lot, MAX_LOT_ABSOLUTE))
        return round(lot, 2)

    def check_drawdown(self, initial_balance: float, current_balance: float) -> bool:
        """Returns True if safe, False if drawdown exceeded"""
        if initial_balance <= 0:
            return True
        dd = (initial_balance - current_balance) / initial_balance * 100
        if dd >= MAX_DRAWDOWN_PCT:
            self._alert(f"DRAWDOWN {dd:.1f}% EXCEEDED MAX {MAX_DRAWDOWN_PCT}%! STOP TRADING!")
            return False
        return True

    def check_overtrade(self) -> bool:
        """Returns True if safe to trade, False if overtrading"""
        now = time.time()
        self.trade_times = [t for t in self.trade_times if now - t < 60]
        if len(self.trade_times) >= MAX_TRADES_PER_MIN:
            self._alert(f"OVERTRADE DETECTED! {len(self.trade_times)} trades in last minute!")
            return False
        self.trade_times.append(now)
        return True

    def check_strategy_sanity(self, dna: dict) -> bool:
        """Prevent suicidal strategies"""
        risk = dna.get("risk", 0.01)
        aggression = dna.get("aggressiveness", 0.3)
        layer_dist = dna.get("layer_distance", 1.5)

        if risk > 0.5:
            self._alert(f"RISK TOO HIGH: {risk} > 0.5")
            return False
        if aggression > 0.9:
            self._alert(f"AGGRESSION TOO HIGH: {aggression}")
            return False
        if layer_dist < 0.5:
            self._alert(f"LAYER DISTANCE TOO SMALL: {layer_dist}")
            return False
        return True

    def protect_immune_files(self, proposed_changes: list) -> list:
        """Filter out any changes to immune files"""
        safe_changes = []
        for change in proposed_changes:
            file_path = change.get("file", "")
            blocked = False
            for immune in IMMUNE_FILES:
                if immune in file_path:
                    self._alert(f"BLOCKED: AI tried to modify immune file: {file_path}")
                    blocked = True
                    break
            if not blocked:
                safe_changes.append(change)
        return safe_changes

    def quarantine_organism(self, organism_id: str, reason: str):
        """Quarantine a broken organism"""
        quarantine_path = os.path.join(self.base_path, f"ORGANISMS/{organism_id}/QUARANTINED.txt")
        with open(quarantine_path, "w") as f:
            f.write(f"QUARANTINED: {datetime.utcnow().isoformat()}\nReason: {reason}\n")
        self._alert(f"Organism {organism_id} QUARANTINED: {reason}")

    def _alert(self, msg: str):
        """Log alert"""
        timestamp = datetime.utcnow().isoformat()
        alert = f"[IMMUNE ALERT {timestamp}] {msg}"
        print(alert)
        self.errors.append(alert)
        # Write to immune log
        log_path = os.path.join(self.base_path, "SECURITY/immune_log.txt")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(alert + "\n")

    def run_full_check(self, dna: dict, lot: float, balance: float, initial_balance: float) -> dict:
        """Full immune check before any action"""
        results = {
            "dna_ok": self.validate_dna(),
            "lot_safe": self.validate_lot(lot),
            "drawdown_ok": self.check_drawdown(initial_balance, balance),
            "overtrade_ok": self.check_overtrade(),
            "strategy_ok": self.check_strategy_sanity(dna)
        }
        results["all_ok"] = all([
            results["dna_ok"],
            results["drawdown_ok"],
            results["overtrade_ok"],
            results["strategy_ok"]
        ])
        return results

if __name__ == "__main__":
    immune = ImmunitySystem()
    print("DNA Check:", immune.validate_dna())
    print("Overtrade Check:", immune.check_overtrade())
    print("Lot Safe:", immune.validate_lot(0.01))
