import json
import random
import os
from datetime import datetime

signal_path = "AI_CLOUD/data/signal.json"

symbols = ["XAUUSD","EURUSD","GBPUSD","USDJPY"]

actions = ["BUY","SELL","WAIT"]

symbol = random.choice(symbols)

action = random.choice(actions)

confidence = round(random.uniform(0.5,0.9),2)

signal = {
    "symbol": symbol,
    "action": action,
    "confidence": confidence,
    "lot": 0.01,
    "timestamp": str(datetime.utcnow())
}

os.makedirs("AI_CLOUD/data", exist_ok=True)

with open(signal_path,"w") as f:
    json.dump(signal,f,indent=2)

print("AI SIGNAL:",signal)
