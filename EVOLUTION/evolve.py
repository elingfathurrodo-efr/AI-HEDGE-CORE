#!/usr/bin/env python3
"""
SEA-TO Evolution Engine
Genetic Algorithm untuk evolusi strategi trading
"""

import json
import random
import numpy as np
import os
import sys
from datetime import datetime
from pathlib import Path

class Genome:
    def __init__(self, organism_id, genes=None):
        self.id = organism_id
        self.genes = genes or self._create_genesis_genes()
        self.fitness = 0.0
        self.age = 0
        self.trauma_score = 0
        
    def _create_genesis_genes(self):
        """Gen awal untuk organism"""
        return {
            "entry_logic": {
                "candle_pattern_weight": random.uniform(0.3, 0.7),
                "rsi_threshold": random.uniform(30, 70),
                "ema_fast_period": random.randint(5, 20),
                "ema_slow_period": random.randint(21, 50),
                "volume_confirmation": random.choice([True, False])
            },
            "exit_logic": {
                "take_profit_multiplier": random.uniform(1.5, 3.0),
                "trailing_activation": random.uniform(0.5, 2.0),
                "time_based_exit": random.randint(300, 1800)  # detik
            },
            "risk_parameters": {
                "position_size_multiplier": random.uniform(0.5, 1.5),
                "max_concurrent_trades": random.randint(1, 5),
                "layer_spacing_pips": random.uniform(3, 10)
            },
            "adaptation": {
                "volatility_sensitivity": random.uniform(0.1, 1.0),
                "trend_following_bias": random.uniform(-1.0, 1.0),
                "mean_reversion_bias": random.uniform(-1.0, 1.0)
            }
        }
    
    def mutate(self, mutation_rate=0.1):
        """Mutasi gen dengan batasan keamanan"""
        # Load DNA Core untuk cek forbidden mutations
        with open('DNA/core_rules.json', 'r') as f:
            core_rules = json.load(f)
        
        forbidden = core_rules['evolution_safety']['forbidden_mutations']
        
        new_genes = json.loads(json.dumps(self.genes))  # Deep copy
        
        for category in new_genes:
            if category in forbidden:
                continue  # Skip kategori yang dilindungi
                
            for gene_name in new_genes[category]:
                if gene_name in forbidden:
                    continue  # Skip gen yang dilindungi
                    
                if random.random() < mutation_rate:
                    current_val = new_genes[category][gene_name]
                    
                    # Mutasi berdasarkan tipe data
                    if isinstance(current_val, float):
                        mutation = random.gauss(0, 0.1)
                        new_genes[category][gene_name] = max(0.0, min(1.0, current_val + mutation))
                    elif isinstance(current_val, int):
                        new_genes[category][gene_name] += random.randint(-2, 2)
                    elif isinstance(current_val, bool):
                        new_genes[category][gene_name] = not current_val
        
        self.genes = new_genes
        self.age += 1
        
    def to_file(self, filepath):
        """Simpan organism ke file"""
        data = {
            "id": self.id,
            "genes": self.genes,
            "fitness": self.fitness,
            "age": self.age,
            "trauma_score": self.trauma_score,
            "birth_date": datetime.now().isoformat(),
            "generation": int(self.id.split('_')[-1])
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def from_file(cls, filepath):
        """Load organism dari file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        org = cls(data['id'], data['genes'])
        org.fitness = data.get('fitness', 0)
        org.age = data.get('age', 0)
        org.trauma_score = data.get('trauma_score', 0)
        return org

class EvolutionEngine:
    def __init__(self):
        self.population = []
        self.generation = 0
        self.load_population()
        
    def load_population(self):
        """Load populasi dari folder BRAIN/ACTIVE"""
        brain_dir = Path('BRAIN/ACTIVE')
        brain_dir.mkdir(parents=True, exist_ok=True)
        
        organism_files = list(brain_dir.glob('organism_*.json'))
        
        if not organism_files:
            # Genesis: Buat populasi awal
            print("🌱 Creating Genesis Population...")
            for i in range(50):
                org = Genome(f"organism_{i:03d}")
                org.to_file(brain_dir / f"organism_{i:03d}.json")
                self.population.append(org)
        else:
            for file_path in organism_files:
                try:
                    org = Genome.from_file(file_path)
                    self.population.append(org)
                except Exception as e:
                    print(f"⚠️ Corrupted organism {file_path}: {e}")
    
    def evaluate_fitness(self, organism):
        """
        Evaluasi fitness berdasarkan:
        1. Profit factor (historical)
        2. Sharpe ratio
        3. Max drawdown compliance
        4. Win rate
        """
        # Simulasi evaluasi (dalam produksi, ini dari data MT5)
        # TODO: Integrasi dengan MT5 trading history
        
        simulated_profit = random.gauss(0.02, 0.05)  # Simulasi
        risk_penalty = abs(simulated_profit) * 0.1 if simulated_profit < 0 else 0
        
        organism.fitness = max(0, simulated_profit - risk_penalty)
        return organism.fitness
    
    def select_parents(self, tournament_size=3):
        """Tournament selection"""
        tournament = random.sample(self.population, tournament_size)
        tournament.sort(key=lambda x: x.fitness, reverse=True)
        return tournament[0]
    
    def crossover(self, parent1, parent2):
        """Crossover dua parent"""
        child_genes = {}
        
        for category in parent1.genes:
            child_genes[category] = {}
            for gene_name in parent1.genes[category]:
                # Uniform crossover
                if random.random() < 0.5:
                    child_genes[category][gene_name] = parent1.genes[category][gene_name]
                else:
                    child_genes[category][gene_name] = parent2.genes[category][gene_name]
        
        child_id = f"organism_{len(self.population):03d}_gen{self.generation}"
        child = Genome(child_id, child_genes)
        return child
    
    def evolve_generation(self):
        """Satu siklus evolusi"""
        print(f"🧬 Generation {self.generation} Evolution Started")
        
        # Evaluasi fitness semua organism
        for org in self.population:
            self.evaluate_fitness(org)
        
        # Sort by fitness
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Elitism: Simpan 10% terbaik
        elite_count = max(1, len(self.population) // 10)
        new_population = self.population[:elite_count]
        
        # Generate offspring sampai populasi penuh
        while len(new_population) < len(self.population):
            parent1 = self.select_parents()
            parent2 = self.select_parents()
            
            child = self.crossover(parent1, parent2)
            child.mutate(mutation_rate=0.1)
            
            new_population.append(child)
        
        self.population = new_population
        self.generation += 1
        
        # Simpan ke file
        self.save_population()
        
        print(f"✅ Evolution Complete. Best Fitness: {self.population[0].fitness:.4f}")
    
    def save_population(self):
        """Simpan populasi ke disk"""
        brain_dir = Path('BRAIN/ACTIVE')
        
        # Hapus file lama
        for old_file in brain_dir.glob('organism_*.json'):
            old_file.unlink()
        
        # Simpan yang baru
        for org in self.population:
            org.to_file(brain_dir / f"{org.id}.json")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--generation', type=str, default='auto')
    args = parser.parse_args()
    
    engine = EvolutionEngine()
    
    if args.generation == 'auto':
        engine.evolve_generation()
    else:
        for _ in range(int(args.generation)):
            engine.evolve_generation()

if __name__ == "__main__":
    main()
