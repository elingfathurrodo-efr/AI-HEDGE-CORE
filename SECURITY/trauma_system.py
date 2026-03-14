"""
TRAUMA_SYSTEM.PY - TRAUMA & ERROR TRACKING
============================================
Tracks errors per organism.
If too many errors → trigger rollback.
AI CANNOT MODIFY THIS FILE.
"""
import json, os
from datetime import datetime

class TraumaSystem:
    def __init__(self, base_path="."):
        self.base_path  = base_path
        self.trauma_log = os.path.join(base_path, "SECURITY/trauma_log.json")
        self._load_log()

    def _load_log(self):
        if os.path.exists(self.trauma_log):
            with open(self.trauma_log) as f:
                self.log = json.load(f)
        else:
            self.log = {}

    def _save_log(self):
        os.makedirs(os.path.dirname(self.trauma_log), exist_ok=True)
        with open(self.trauma_log, "w") as f:
            json.dump(self.log, f, indent=2)

    def record_error(self, organism_id: str, error_msg: str):
        """Record an error for an organism"""
        if organism_id not in self.log:
            self.log[organism_id] = {"errors": [], "error_count": 0, "trauma_level": 0}
        entry = {
            "time":  datetime.utcnow().isoformat(),
            "error": error_msg[:300]
        }
        self.log[organism_id]["errors"].append(entry)
        self.log[organism_id]["errors"] = self.log[organism_id]["errors"][-50:]
        self.log[organism_id]["error_count"] += 1
        self.log[organism_id]["trauma_level"] = min(10, self.log[organism_id]["error_count"] / 5)
        self._save_log()
        print(f"[TRAUMA] Error recorded for {organism_id}: {error_msg[:100]}")

    def should_rollback(self, organism_id: str) -> bool:
        """Returns True if organism should be rolled back"""
        if organism_id not in self.log:
            return False
        return self.log[organism_id].get("trauma_level", 0) >= 2

    def reset_trauma(self, organism_id: str):
        """Reset trauma after rollback"""
        if organism_id in self.log:
            self.log[organism_id]["error_count"]  = 0
            self.log[organism_id]["trauma_level"] = 0
            self._save_log()
        print(f"[TRAUMA] Trauma reset for {organism_id}")

    def get_trauma_level(self, organism_id: str) -> float:
        if organism_id not in self.log:
            return 0
        return self.log[organism_id].get("trauma_level", 0)

    def get_all_trauma(self) -> dict:
        return {k: v.get("trauma_level", 0) for k, v in self.log.items()}
