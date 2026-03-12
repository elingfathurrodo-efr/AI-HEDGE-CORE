import json
import random
import os

signal_file = "DATA/signal.json"

symbol = "XAUUSD"

actions = ["BUY","SELL"]

action = random.choice(actions)

signal = {
    "symbol": symbol,
    "action": action,
    "lot": 0.01
}

os.makedirs("DATA", exist_ok=True)

with open(signal_file,"w") as f:
    json.dump(signal,f,indent=2)

print("AI generated signal:",signal)
