"""
ROLLBACK.PY - FAILSAFE ROLLBACK ORCHESTRATOR
============================================
AI CANNOT MODIFY THIS FILE.

Purpose:
- Provide a single, stable rollback entry-point for the whole organism.
- Can be called by GitHub Actions or by other modules when errors spike.

What it does:
- Uses RegenerationSystem to rollback one organism (or all organisms)
- Resets trauma level after successful rollback

Note:
- This is a *controller*; it does not decide trading logic.
- Keeps project future-proof: you always have SECURITY/rollback.py present.
"""

import os
import sys
from datetime import datetime

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_PATH)

from DNA.regeneration import RegenerationSystem
from SECURITY.trauma_system import TraumaSystem


class RollbackController:
    def __init__(self, base_path: str = BASE_PATH):
        self.base_path = base_path
        self.regen = RegenerationSystem(base_path)
        self.trauma = TraumaSystem(base_path)

    def rollback_one(self, organism_id: str, version: str = "latest") -> bool:
        ok = self.regen.rollback_brain(organism_id, version=version)
        if ok:
            self.trauma.reset_trauma(organism_id)
        return ok

    def rollback_all(self) -> int:
        org_dir = os.path.join(self.base_path, "ORGANISMS")
        if not os.path.exists(org_dir):
            return 0
        count = 0
        for org_id in os.listdir(org_dir):
            org_path = os.path.join(org_dir, org_id)
            if not os.path.isdir(org_path):
                continue
            if org_id.startswith("_"):
                continue
            if self.rollback_one(org_id):
                count += 1
        return count


if __name__ == "__main__":
    rb = RollbackController(BASE_PATH)
    target = os.environ.get("ORGANISM_ID", "")
    if target:
        ok = rb.rollback_one(target)
        print(f"[ROLLBACK] {datetime.utcnow().isoformat()} rollback_one({target}) -> {ok}")
    else:
        n = rb.rollback_all()
        print(f"[ROLLBACK] {datetime.utcnow().isoformat()} rollback_all -> {n} organisms")
