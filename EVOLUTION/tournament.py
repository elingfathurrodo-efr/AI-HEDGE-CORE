"""
TOURNAMENT.PY - ORGANISM COMPETITION
======================================
Runs tournament between organisms.
Updates scores and marks the champion.
"""
import json, os, sys, random, importlib.util, time
from datetime import datetime

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_PATH)
ORGANISMS_DIR = os.path.join(BASE_PATH, "ORGANISMS")

def simulate_trade(brain_signal: dict, market_direction: str) -> dict:
    """Simulate trade outcome"""
    signal = brain_signal.get("signal", "NONE")
    if signal == "NONE":
        return {"profit": 0, "result": "NO_TRADE"}
    confidence = brain_signal.get("confidence", 0.5)
    lot        = brain_signal.get("lot", 0.01)
    sl_points  = brain_signal.get("sl_points", 200)
    tp_ratio   = brain_signal.get("tp_ratio", 2.0)
    tp_points  = sl_points * tp_ratio
    pip_value  = 0.10  # XAUUSD approx $0.10 per point per 0.01 lot
    # Win probability based on confidence + random
    win_prob   = confidence * 0.6 + (0.4 if signal == market_direction else 0.1)
    won        = random.random() < win_prob
    if won:
        profit = tp_points * pip_value * lot / 0.01
    else:
        profit = -(sl_points * pip_value * lot / 0.01)
    return {"profit": round(profit, 4), "result": "WIN" if won else "LOSS", "signal": signal}

def run_tournament():
    print("=" * 60)
    print(f"[TOURNAMENT] Started: {datetime.utcnow().isoformat()}")
    print("=" * 60)

    organisms = []
    for org_id in os.listdir(ORGANISMS_DIR):
        org_path = os.path.join(ORGANISMS_DIR, org_id)
        if not os.path.isdir(org_path): continue
        if os.path.exists(os.path.join(org_path, "QUARANTINED.txt")): continue
        brain_path = os.path.join(org_path, "brain.py")
        dna_path   = os.path.join(org_path, "dna.json")
        mem_path   = os.path.join(org_path, "memory.json")
        if os.path.exists(brain_path) and os.path.exists(dna_path):
            organisms.append(org_id)

    if len(organisms) < 2:
        print("[TOURNAMENT] Not enough organisms for tournament")
        return

    print(f"[TOURNAMENT] {len(organisms)} organisms competing")

    # Simulate 20 rounds
    scores = {org: 0 for org in organisms}
    directions = ["BUY", "SELL", "BUY", "SELL", "BUY"]
    
    for round_num in range(20):
        mkt_dir = random.choice(directions)
        # Generate mock candles
        candles = [{"open": 2350+i*0.5, "high": 2351+i*0.5, "low": 2349+i*0.5,
                    "close": 2350+i*0.5+(0.5 if mkt_dir=="BUY" else -0.5), "volume": 500+i*10}
                   for i in range(60)]
        
        for org_id in organisms:
            try:
                brain_path = os.path.join(ORGANISMS_DIR, org_id, "brain.py")
                spec = importlib.util.spec_from_file_location("brain_"+org_id, brain_path)
                mod  = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                brain = mod.OrganismBrain(org_id, BASE_PATH)
                signal = brain.decide_signal(candles, "London")
                result = simulate_trade(signal, mkt_dir)
                scores[org_id] += result["profit"]
                brain.learn_from_trade({**result, "strategy": signal.get("reason","")})
            except Exception as e:
                print(f"[TOURNAMENT] {org_id} error: {e}")

    # Update memory with tournament results
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print("\n🏆 TOURNAMENT RESULTS:")
    for rank, (org_id, score) in enumerate(ranked, 1):
        emoji = "🥇" if rank==1 else "🥈" if rank==2 else "🥉" if rank==3 else f"{rank}."
        print(f"  {emoji} {org_id}: {score:.4f}")

    # Save tournament results
    result_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "participants": organisms,
        "champion": ranked[0][0],
        "scores": dict(ranked),
        "rounds": 20
    }
    result_path = os.path.join(BASE_PATH, "MEMORY/tournament_results.json")
    with open(result_path, "w") as f:
        json.dump(result_data, f, indent=2)
    print(f"\n[TOURNAMENT] Champion: {ranked[0][0]} | Score: {ranked[0][1]:.4f}")

if __name__ == "__main__":
    run_tournament()
