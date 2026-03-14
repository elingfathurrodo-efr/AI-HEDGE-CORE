"""
FUND_GUARDIAN.PY - CAPITAL PROTECTION SYSTEM
=============================================
Implements the 2x rule: when balance doubles, lock 50%.
Locked fund only released after next market session.
AI CANNOT MODIFY THIS FILE.
"""
import json, os
from datetime import datetime, timezone

class FundGuardian:
    def __init__(self, base_path=".", initial_balance: float = 50.0):
        self.base_path = base_path
        self.state_file = os.path.join(base_path, "SECURITY/fund_state.json")
        self._load_state(initial_balance)

    def _load_state(self, initial_balance: float):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                self.state = json.load(f)
        else:
            self.state = {
                "initial_balance":  initial_balance,
                "locked_fund":      0.0,
                "trading_fund":     initial_balance,
                "current_balance":  initial_balance,
                "last_double_at":   None,
                "locked_since_session": None,
                "unlock_after_session": None,
                "history": []
            }
            self._save_state()

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def get_current_session(self) -> str:
        h = datetime.now(timezone.utc).hour
        if 0 <= h < 9:   return "Asia"
        if 8 <= h < 17:  return "London"
        if 13 <= h < 22: return "NewYork"
        return "Closed"

    def update_balance(self, new_balance: float):
        """Update balance and check for 2x rule trigger"""
        old_balance = self.state["current_balance"]
        self.state["current_balance"] = new_balance
        initial = self.state["initial_balance"]

        # Check 2x trigger
        if new_balance >= initial * 2 and self.state["locked_fund"] == 0:
            locked = new_balance / 2
            trading = new_balance / 2
            self.state["locked_fund"]     = locked
            self.state["trading_fund"]    = trading
            self.state["last_double_at"]  = datetime.utcnow().isoformat()
            session_now = self.get_current_session()
            self.state["locked_since_session"] = session_now
            print(f"[FUND] 2x RULE TRIGGERED! Balance: ${new_balance:.2f}")
            print(f"[FUND] Locked: ${locked:.2f} | Trading: ${trading:.2f}")
            print(f"[FUND] Locked since session: {session_now}")
            self._save_state()
        else:
            self.state["trading_fund"] = new_balance - self.state["locked_fund"]
            self._save_state()

    def can_use_locked_fund(self) -> bool:
        """Can locked fund be released?"""
        locked_session = self.state.get("locked_since_session")
        if not locked_session or self.state["locked_fund"] == 0:
            return False
        current_session = self.get_current_session()
        # Must be in a DIFFERENT session than when it was locked
        if current_session != locked_session and current_session != "Closed":
            print(f"[FUND] Locked fund can be released! Was locked in {locked_session}, now {current_session}")
            return True
        return False

    def release_locked_fund(self):
        """Release locked fund for trading (after session change)"""
        if self.can_use_locked_fund():
            self.state["trading_fund"] += self.state["locked_fund"]
            print(f"[FUND] Released ${self.state['locked_fund']:.2f} locked fund for trading")
            self.state["locked_fund"]  = 0.0
            self.state["locked_since_session"] = None
            self._save_state()
            return True
        return False

    def get_available_trading_fund(self) -> float:
        return self.state.get("trading_fund", self.state.get("current_balance", 50.0))

    def get_locked_fund(self) -> float:
        return self.state.get("locked_fund", 0.0)

    def get_status(self) -> dict:
        return {
            "current_balance":  self.state["current_balance"],
            "locked_fund":      self.state["locked_fund"],
            "trading_fund":     self.state["trading_fund"],
            "can_unlock":       self.can_use_locked_fund(),
            "current_session":  self.get_current_session()
        }

    def trailing_lock(self, entry_price: float, current_price: float, direction: str,
                      initial_margin: float) -> float:
        """
        Calculate trailing stop lock level.
        Returns locked price level (ghost SL).
        """
        if initial_margin <= 0:
            return current_price
        if direction == "BUY":
            profit_pct = (current_price - entry_price) / entry_price * 100
        else:
            profit_pct = (entry_price - current_price) / entry_price * 100

        # Trailing table
        trailing_table = [
            (95, 90), (90, 80), (80, 65), (70, 54),
            (60, 44), (50, 35), (40, 28), (30, 20),
            (20, 10), (10, 5)
        ]
        lock_pct = 0
        for profit_threshold, lock_threshold in trailing_table:
            if profit_pct >= profit_threshold:
                lock_pct = lock_threshold
                break

        if lock_pct == 0:
            return None  # No lock yet

        # Calculate lock price
        if direction == "BUY":
            lock_price = entry_price * (1 + lock_pct / 100)
        else:
            lock_price = entry_price * (1 - lock_pct / 100)
        return lock_price

if __name__ == "__main__":
    guardian = FundGuardian(initial_balance=50.0)
    guardian.update_balance(100.0)
    print("Status:", guardian.get_status())
    print("Lock price BUY:", guardian.trailing_lock(2350, 2400, "BUY", 50))
