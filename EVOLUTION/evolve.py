"""
EVOLVE.PY - EVOLUTION ENGINE
==============================
GitHub Actions runs this daily.
- Tests all organisms
- Tournament to pick best
- Mutates DNA
- Creates new organisms
- Prunes weak organisms
"""
import json, os, sys, random, shutil, copy, importlib.util
from datetime import datetime

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_PATH)

ORGANISMS_DIR  = os.path.join(BASE_PATH, "ORGANISMS")
MAX_ORGANISMS  = 20
MIN_ORGANISMS  = 3
MUTATION_RATE  = 0.25
SURVIVAL_RATE  = 0.5

try:
    from DNA.immunity    import ImmunitySystem
    from DNA.regeneration import RegenerationSystem
    from SECURITY.trauma_system import TraumaSystem
    IMMUNE = ImmunitySystem(BASE_PATH)
    REGEN  = RegenerationSystem(BASE_PATH)
    TRAUMA = TraumaSystem(BASE_PATH)
except Exception as e:
    print(f"[EVOLVE] Warning: Could not load systems: {e}")
    IMMUNE = None
    REGEN  = None

# ================================================
# MUTATION PARAMETERS
# ================================================
MUTABLE_PARAMS = {
    "risk":             (0.01, 0.05, 0.005),
    "aggressiveness":   (0.1,  0.8,  0.05),
    "layer_distance":   (0.8,  5.0,  0.2),
    "sl_points":        (100,  500,  25),
    "tp_ratio":         (1.0,  5.0,  0.2),
    "ma_fast":          (3,    15,   1),
    "ma_slow":          (15,   50,   2),
    "rsi_period":       (7,    21,   1),
    "rsi_overbought":   (60,   80,   2),
    "rsi_oversold":     (20,   40,   2),
    "min_confidence":   (0.4,  0.9,  0.05)
}

STRATEGY_OPTIONS = [
    "breakout", "trend", "momentum",
    "mean_reversion", "scalping", "session_breakout",
    "sr_bounce", "combined"
]


def get_all_organisms():
    """Get list of all valid organisms"""
    organisms = []
    for org_id in os.listdir(ORGANISMS_DIR):
        org_path = os.path.join(ORGANISMS_DIR, org_id)
        if not os.path.isdir(org_path):
            continue
        if os.path.exists(os.path.join(org_path, "QUARANTINED.txt")):
            continue
        dna_path = os.path.join(org_path, "dna.json")
        mem_path = os.path.join(org_path, "memory.json")
        if os.path.exists(dna_path):
            organisms.append(org_id)
    return organisms

def load_organism_score(org_id: str) -> float:
    """Calculate fitness score for organism"""
    mem_path = os.path.join(ORGANISMS_DIR, org_id, "memory.json")
    if not os.path.exists(mem_path):
        return 0.0
    with open(mem_path) as f:
        mem = json.load(f)
    total_profit = mem.get("total_profit", 0)
    total_loss   = mem.get("total_loss", 0)
    win_rate     = mem.get("win_rate", 0)
    total_trades = mem.get("total_trades", 0)
    if total_trades < 3:
        return random.uniform(0.1, 0.5)  # New organism, give small random score
    net = total_profit - total_loss
    score = net * (1 + win_rate) * (1 + min(total_trades/100, 1))
    return score

def tournament_selection(organisms: list, k=3) -> str:
    """Tournament selection: pick best from k random"""
    if len(organisms) < k:
        k = len(organisms)
    candidates = random.sample(organisms, k)
    scores = {org: load_organism_score(org) for org in candidates}
    return max(scores, key=scores.get)

def mutate_dna(parent_dna: dict, mutation_rate: float = MUTATION_RATE) -> dict:
    """Create mutated child DNA from parent"""
    child = copy.deepcopy(parent_dna)
    for param, (min_val, max_val, step) in MUTABLE_PARAMS.items():
        if random.random() < mutation_rate:
            current = child.get(param, (min_val + max_val) / 2)
            delta   = random.choice([-step, step]) * random.uniform(0.5, 2.0)
            new_val = current + delta
            new_val = max(min_val, min(max_val, new_val))
            if isinstance(min_val, int):
                new_val = int(round(new_val))
            else:
                new_val = round(new_val, 4)
            child[param] = new_val
    # Sometimes mutate strategy
    if random.random() < mutation_rate * 0.5:
        child["strategy"] = random.choice(STRATEGY_OPTIONS)
    return child

def crossover_dna(parent1_dna: dict, parent2_dna: dict) -> dict:
    """Crossover: mix genes from 2 parents"""
    child = copy.deepcopy(parent1_dna)
    for param in MUTABLE_PARAMS.keys():
        if random.random() < 0.5:
            child[param] = parent2_dna.get(param, parent1_dna.get(param))
    return child

def get_next_organism_id() -> str:
    """Generate next organism ID"""
    existing = [d for d in os.listdir(ORGANISMS_DIR) if d.startswith("organism_")]
    if not existing:
        return "organism_001"
    nums = []
    for e in existing:
        try:
            nums.append(int(e.split("_")[1]))
        except:
            pass
    next_num = max(nums) + 1 if nums else 1
    return f"organism_{next_num:03d}"

def create_new_organism(parent_id: str, parent_dna: dict, is_crossover: bool = False,
                         parent2_id: str = None) -> str:
    """Create new organism as offspring"""
    new_id = get_next_organism_id()
    print(f"[EVOLVE] Creating {new_id} from {parent_id}")

    # Backup parent first
    if REGEN:
        REGEN.backup_brain(parent_id)

    # Mutate DNA
    if is_crossover and parent2_id:
        parent2_dna_path = os.path.join(ORGANISMS_DIR, parent2_id, "dna.json")
        with open(parent2_dna_path) as f:
            parent2_dna = json.load(f)
        child_dna = crossover_dna(parent_dna, parent2_dna)
        child_dna = mutate_dna(child_dna, mutation_rate=MUTATION_RATE * 0.5)
        child_dna["parents"] = [parent_id, parent2_id]
    else:
        child_dna = mutate_dna(parent_dna)
        child_dna["parents"] = [parent_id]

    child_dna["organism_id"] = new_id
    child_dna["generation"]  = parent_dna.get("generation", 1) + 1
    child_dna["born_at"]     = datetime.utcnow().isoformat()

    # Use regeneration system to create organism
    if REGEN:
        REGEN.create_organism_from_template(new_id, child_dna)
    else:
        # Manual creation
        new_path = os.path.join(ORGANISMS_DIR, new_id)
        os.makedirs(new_path, exist_ok=True)
        template_brain = os.path.join(BASE_PATH, "BRAIN/brain_template/brain.py")
        if os.path.exists(template_brain):
            shutil.copy2(template_brain, os.path.join(new_path, "brain.py"))
        with open(os.path.join(new_path, "dna.json"), "w") as f:
            json.dump(child_dna, f, indent=2)
        with open(os.path.join(new_path, "memory.json"), "w") as f:
            json.dump({"organism_id": new_id, "total_trades": 0, "win_rate": 0, "trade_history": []}, f, indent=2)

    return new_id

def prune_weak_organisms(organisms: list) -> list:
    """Remove weakest organisms to stay under MAX_ORGANISMS"""
    if len(organisms) <= MIN_ORGANISMS:
        return organisms
    scores = {org: load_organism_score(org) for org in organisms}
    sorted_orgs = sorted(organisms, key=lambda x: scores[x], reverse=True)
    # Always keep top MIN_ORGANISMS
    if len(sorted_orgs) > MAX_ORGANISMS:
        to_remove = sorted_orgs[MAX_ORGANISMS:]
        for org_id in to_remove:
            org_path = os.path.join(ORGANISMS_DIR, org_id)
            # Archive rather than delete
            archive_path = os.path.join(BASE_PATH, f"ORGANISMS/_archive/{org_id}")
            os.makedirs(os.path.dirname(archive_path), exist_ok=True)
            if os.path.exists(org_path):
                shutil.move(org_path, archive_path)
                print(f"[EVOLVE] Archived weak organism: {org_id} (score: {scores[org_id]:.4f})")
    return sorted_orgs[:MAX_ORGANISMS]

def write_evolution_log(generation_data: dict):
    """Write evolution history"""
    log_path = os.path.join(BASE_PATH, "MEMORY/evolution_log.json")
    history = []
    if os.path.exists(log_path):
        with open(log_path) as f:
            try:
                history = json.load(f)
            except:
                history = []
    history.append(generation_data)
    history = history[-100:]  # Keep last 100 evolutions
    with open(log_path, "w") as f:
        json.dump(history, f, indent=2)

def run_evolution():
    """Main evolution cycle"""
    print("=" * 60)
    print(f"[EVOLVE] Evolution started at {datetime.utcnow().isoformat()}")
    print("=" * 60)

    # Validate DNA
    if IMMUNE and not IMMUNE.validate_dna():
        print("[EVOLVE] DNA compromised! Aborting evolution.")
        return

    organisms = get_all_organisms()
    print(f"[EVOLVE] Found {len(organisms)} organisms")

    if not organisms:
        print("[EVOLVE] No organisms! Creating starter organisms...")
        if REGEN:
            REGEN.create_organism_from_template("organism_001")
            REGEN.create_organism_from_template("organism_002")
        organisms = get_all_organisms()

    # Score all organisms
    scores = {}
    for org_id in organisms:
        score = load_organism_score(org_id)
        scores[org_id] = score
        print(f"  {org_id}: {score:.4f}")

    # Tournament: select parents
    survivors = int(len(organisms) * SURVIVAL_RATE)
    survivors = max(survivors, MIN_ORGANISMS)
    sorted_orgs = sorted(organisms, key=lambda x: scores[x], reverse=True)
    parent_pool = sorted_orgs[:max(2, survivors)]

    print(f"[EVOLVE] Parent pool: {parent_pool}")

    new_organisms = []

    # Create offspring through mutation
    n_mutants = max(1, len(parent_pool) // 2)
    for _ in range(n_mutants):
        parent_id = tournament_selection(parent_pool)
        parent_dna_path = os.path.join(ORGANISMS_DIR, parent_id, "dna.json")
        with open(parent_dna_path) as f:
            parent_dna = json.load(f)
        new_id = create_new_organism(parent_id, parent_dna)
        new_organisms.append(new_id)

    # Create offspring through crossover (if 2+ parents)
    if len(parent_pool) >= 2:
        n_crossover = max(1, len(parent_pool) // 3)
        for _ in range(n_crossover):
            p1 = tournament_selection(parent_pool)
            p2 = tournament_selection(parent_pool)
            if p1 != p2:
                p1_dna_path = os.path.join(ORGANISMS_DIR, p1, "dna.json")
                with open(p1_dna_path) as f:
                    p1_dna = json.load(f)
                new_id = create_new_organism(p1, p1_dna, is_crossover=True, parent2_id=p2)
                new_organisms.append(new_id)

    print(f"[EVOLVE] Created {len(new_organisms)} new organisms: {new_organisms}")

    # Prune weak organisms
    all_organisms = get_all_organisms()
    survivors_after = prune_weak_organisms(all_organisms)
    print(f"[EVOLVE] Organisms after pruning: {len(survivors_after)}")

    # Log evolution
    evolution_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "organisms_before": organisms,
        "scores": scores,
        "new_organisms": new_organisms,
        "organisms_after": survivors_after,
        "best_organism": sorted_orgs[0] if sorted_orgs else None,
        "best_score": scores.get(sorted_orgs[0], 0) if sorted_orgs else 0
    }
    write_evolution_log(evolution_data)

    print(f"[EVOLVE] Evolution complete! Best: {evolution_data['best_organism']}")
    print("=" * 60)

if __name__ == "__main__":
    run_evolution()
