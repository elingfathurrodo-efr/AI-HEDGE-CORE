#!/usr/bin/env python3
"""
SEA-TO Immunity System
Deteksi error, rollback, dan karantina
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

class ImmunitySystem:
    def __init__(self):
        self.backup_dir = Path('SECURITY/BACKUP/stable_versions')
        self.quarantine_dir = Path('SECURITY/QUARANTINE')
        self.trauma_dir = Path('BRAIN/TRAUMA')
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.trauma_dir.mkdir(parents=True, exist_ok=True)
    
    def check_dna_integrity(self):
        """Cek apakah DNA Core masih utuh"""
        try:
            with open('DNA/core_rules.json', 'r') as f:
                dna = json.load(f)
            
            # Cek immutable flag
            if not dna.get('immutable', False):
                print("🚨 CRITICAL: DNA Core immutable flag missing!")
                return False
            
            # Cek forbidden mutations tidak berubah
            required_fields = ['max_risk_per_trade', 'max_daily_drawdown', 'evolution_protocol']
            for field in required_fields:
                if field not in str(dna):
                    print(f"🚨 CRITICAL: DNA Core corrupted - {field} missing")
                    return False
            
            return True
            
        except Exception as e:
            print(f"🚨 CRITICAL: DNA Core unreadable: {e}")
            return False
    
    def check_brain_health(self):
        """Cek kesehatan semua organism"""
        brain_dir = Path('BRAIN/ACTIVE')
        corrupted = []
        
        for org_file in brain_dir.glob('organism_*.json'):
            try:
                with open(org_file, 'r') as f:
                    data = json.load(f)
                
                # Validasi struktur
                if 'genes' not in data or 'fitness' not in data:
                    corrupted.append(org_file)
                    continue
                
                # Cek trauma score terlalu tinggi
                if data.get('trauma_score', 0) > 10:
                    print(f"⚠️ High trauma detected: {org_file.name}")
                    self.move_to_trauma(org_file, data)
                    
            except Exception as e:
                print(f"⚠️ Corrupted file: {org_file.name}")
                corrupted.append(org_file)
        
        return len(corrupted) == 0
    
    def move_to_trauma(self, filepath, data):
        """Pindahkan brain yang trauma"""
        trauma_path = self.trauma_dir / f"trauma_{filepath.name}"
        shutil.move(filepath, trauma_path)
        
        # Log trauma
        with open(self.trauma_dir / 'trauma_log.json', 'a') as f:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "organism": data.get('id'),
                "trauma_score": data.get('trauma_score'),
                "reason": "excessive_losses"
            }
            f.write(json.dumps(log_entry) + "\n")
    
    def create_backup(self):
        """Buat snapshot sistem yang stabil"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"stable_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        # Backup DNA
        shutil.copytree('DNA', backup_path / 'DNA', dirs_exist_ok=True)
        
        # Backup BRAIN (hanya yang sehat)
        brain_backup = backup_path / 'BRAIN'
        brain_backup.mkdir(exist_ok=True)
        for org_file in Path('BRAIN/ACTIVE').glob('organism_*.json'):
            shutil.copy(org_file, brain_backup)
        
        print(f"💾 Backup created: {backup_path}")
        
        # Hapus backup lama (keep last 10)
        backups = sorted(self.backup_dir.glob('stable_*'))
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                shutil.rmtree(old_backup)
    
    def rollback(self, backup_name=None):
        """Rollback ke versi stabil"""
        if backup_name is None:
            # Ambil backup terbaru
            backups = sorted(self.backup_dir.glob('stable_*'))
            if not backups:
                print("❌ No backup available for rollback!")
                return False
            backup_path = backups[-1]
        else:
            backup_path = self.backup_dir / backup_name
        
        print(f"⏮️ Rolling back to: {backup_path}")
        
        # Restore DNA
        shutil.rmtree('DNA')
        shutil.copytree(backup_path / 'DNA', 'DNA')
        
        # Restore BRAIN
        shutil.rmtree('BRAIN/ACTIVE')
        Path('BRAIN/ACTIVE').mkdir()
        for org_file in (backup_path / 'BRAIN').glob('*.json'):
            shutil.copy(org_file, 'BRAIN/ACTIVE')
        
        print("✅ Rollback complete")
        return True
    
    def full_system_check(self):
        """Pengecekan sistem lengkap"""
        print("🔍 Running Immunity Check...")
        
        checks = {
            'dna_integrity': self.check_dna_integrity(),
            'brain_health': self.check_brain_health(),
            'disk_space': True,  # TODO: Implement check
            'github_connection': True  # TODO: Implement check
        }
        
        if not all(checks.values()):
            print("⚠️ System compromised! Initiating rollback...")
            self.rollback()
            return False
        
        print("✅ System healthy")
        self.create_backup()
        return True

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--restore-if-needed', action='store_true')
    args = parser.parse_args()
    
    immunity = ImmunitySystem()
    
    if args.check_only:
        healthy = immunity.check_dna_integrity() and immunity.check_brain_health()
        exit(0 if healthy else 1)
    
    if args.restore_if_needed:
        if not immunity.check_dna_integrity():
            immunity.rollback()
    
    immunity.full_system_check()

if __name__ == "__main__":
    main()
