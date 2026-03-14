"""
REGENERATION.PY - SELF-HEALING SYSTEM
=======================================
AI CANNOT MODIFY THIS FILE
Handles organism recovery, brain rollback, and self-repair.
"""
import json, os, shutil, glob
from datetime import datetime

class RegenerationSystem:
    def __init__(self, base_path="."):
        self.base_path = base_path
        self.max_backups = 5

    def backup_brain(self, organism_id: str) -> bool:
        """Backup brain before evolution"""
        org_path = os.path.join(self.base_path, f"ORGANISMS/{organism_id}")
        brain_path = os.path.join(org_path, "brain.py")
        dna_path   = os.path.join(org_path, "dna.json")
        mem_path   = os.path.join(org_path, "memory.json")

        backup_dir = os.path.join(org_path, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
        os.makedirs(backup_path, exist_ok=True)

        try:
            for src, name in [(brain_path,"brain.py"),(dna_path,"dna.json"),(mem_path,"memory.json")]:
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(backup_path, name))
            # Also write backup_brain.json (quick restore marker)
            backup_meta = {
                "organism_id": organism_id,
                "backed_up_at": datetime.utcnow().isoformat(),
                "backup_path": backup_path
            }
            with open(os.path.join(org_path, "backup_brain.json"), "w") as f:
                json.dump(backup_meta, f, indent=2)
            self._cleanup_old_backups(backup_dir)
            print(f"[REGEN] Backup created for {organism_id} at {backup_path}")
            return True
        except Exception as e:
            print(f"[REGEN ERROR] Backup failed: {e}")
            return False

    def rollback_brain(self, organism_id: str, version: str = "latest") -> bool:
        """Rollback organism brain to previous version"""
        org_path = os.path.join(self.base_path, f"ORGANISMS/{organism_id}")
        backup_dir = os.path.join(org_path, "backups")

        backups = sorted(glob.glob(os.path.join(backup_dir, "backup_*")), reverse=True)
        if not backups:
            print(f"[REGEN] No backups found for {organism_id}")
            return False

        restore_from = backups[0] if version == "latest" else None
        if not restore_from:
            for b in backups:
                if version in b:
                    restore_from = b
                    break
        if not restore_from:
            print(f"[REGEN] Backup version {version} not found")
            return False

        try:
            for fname in ["brain.py", "dna.json", "memory.json"]:
                src = os.path.join(restore_from, fname)
                dst = os.path.join(org_path, fname)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
            # Mark rollback
            rollback_info = {
                "rolled_back_at": datetime.utcnow().isoformat(),
                "restored_from": restore_from,
                "organism_id": organism_id
            }
            with open(os.path.join(org_path, "rollback_info.json"), "w") as f:
                json.dump(rollback_info, f, indent=2)
            # Remove quarantine if exists
            q_file = os.path.join(org_path, "QUARANTINED.txt")
            if os.path.exists(q_file):
                os.remove(q_file)
            print(f"[REGEN] Rollback SUCCESS for {organism_id} from {restore_from}")
            return True
        except Exception as e:
            print(f"[REGEN ERROR] Rollback failed: {e}")
            return False

    def emergency_restore_all(self):
        """Emergency: rollback ALL organisms"""
        org_base = os.path.join(self.base_path, "ORGANISMS")
        if not os.path.exists(org_base):
            return
        for organism_id in os.listdir(org_base):
            org_path = os.path.join(org_base, organism_id)
            if os.path.isdir(org_path):
                print(f"[REGEN] Emergency restore: {organism_id}")
                self.rollback_brain(organism_id)

    def create_organism_from_template(self, new_id: str, parent_dna: dict = None) -> bool:
        """Create new organism from template"""
        template_path = os.path.join(self.base_path, "BRAIN/brain_template")
        new_path = os.path.join(self.base_path, f"ORGANISMS/{new_id}")
        os.makedirs(new_path, exist_ok=True)
        os.makedirs(os.path.join(new_path, "backups"), exist_ok=True)

        try:
            # Copy brain.py from template
            template_brain = os.path.join(template_path, "brain.py")
            if os.path.exists(template_brain):
                shutil.copy2(template_brain, os.path.join(new_path, "brain.py"))

            # Create dna.json (mutated from parent if given)
            dna = parent_dna.copy() if parent_dna else {
                "strategy": "breakout",
                "risk": 0.01,
                "aggressiveness": 0.3,
                "layer_distance": 1.5,
                "sl_points": 200,
                "tp_ratio": 2.0,
                "ma_fast": 8,
                "ma_slow": 21,
                "rsi_period": 14,
                "rsi_overbought": 70,
                "rsi_oversold": 30
            }
            dna["organism_id"] = new_id
            dna["created_at"] = datetime.utcnow().isoformat()
            dna["generation"] = (parent_dna.get("generation", 0) + 1) if parent_dna else 1

            with open(os.path.join(new_path, "dna.json"), "w") as f:
                json.dump(dna, f, indent=2)

            # Create empty memory.json
            memory = {
                "organism_id": new_id,
                "created_at": datetime.utcnow().isoformat(),
                "total_trades": 0,
                "win_trades": 0,
                "loss_trades": 0,
                "total_profit": 0.0,
                "total_loss": 0.0,
                "win_rate": 0.0,
                "best_strategy": None,
                "market_patterns": [],
                "trade_history": []
            }
            with open(os.path.join(new_path, "memory.json"), "w") as f:
                json.dump(memory, f, indent=2)

            print(f"[REGEN] New organism {new_id} created!")
            return True
        except Exception as e:
            print(f"[REGEN ERROR] Create organism failed: {e}")
            return False

    def _cleanup_old_backups(self, backup_dir: str):
        """Keep only max_backups"""
        backups = sorted(glob.glob(os.path.join(backup_dir, "backup_*")), reverse=True)
        for old_backup in backups[self.max_backups:]:
            shutil.rmtree(old_backup, ignore_errors=True)

if __name__ == "__main__":
    regen = RegenerationSystem()
    print("Regeneration system ready.")
    regen.create_organism_from_template("organism_test_001")
