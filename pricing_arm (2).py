# Simple epsilon-greedy A/B tuner for bundles
from typing import Dict, Any, List
import random

_experiments: Dict[str, Dict[str, Any]] = {}

async def start_bundle_test(username: str, bundles: List[str], epsilon: float = 0.15):
    exp_id = f"exp_{len(_experiments)+1}"
    _experiments[exp_id] = {"user": username, "bundles": bundles, "epsilon": epsilon, "wins": {b:0 for b in bundles}, "shows": {b:0 for b in bundles}}
    return {"id": exp_id, "bundles": bundles}

async def next_arm(username: str, exp_id: str):
    exp = _experiments.get(exp_id)
    if not exp: return {"error":"no_exp"}
    if random.random() < exp["epsilon"]:
        choice = random.choice(exp["bundles"])
    else:
        # pick best win rate
        rates = [(b, (exp["wins"][b] / max(1, exp["shows"][b]))) for b in exp["bundles"]]
        choice = sorted(rates, key=lambda x: x[1], reverse=True)[0][0]
    exp["shows"][choice] += 1
    return {"bundle_id": choice}

async def record_outcome(username: str, exp_id: str, bundle_id: str, revenue_usd: float):
    exp = _experiments.get(exp_id)
    if not exp: return {"error":"no_exp"}
    if revenue_usd > 0:
        exp["wins"][bundle_id] += 1
    return {"wins": exp["wins"], "shows": exp["shows"]}

async def best_arm(username: str, exp_id: str):
    exp = _experiments.get(exp_id)
    if not exp: return {"error":"no_exp"}
    rates = [(b, (exp["wins"][b] / max(1, exp["shows"][b]))) for b in exp["bundles"]]
    return sorted(rates, key=lambda x: x[1], reverse=True)[0][0]
