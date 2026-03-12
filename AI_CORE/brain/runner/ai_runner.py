import json
from AI_CORE.brain.brain_1 import decide

signal = {
 "symbol":"XAUUSD",
 "action":decide({}),
 "lot":0.01
}

with open("DATA/signal.json","w") as f:
    json.dump(signal,f)
