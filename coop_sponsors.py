
# coop_sponsors.py
from typing import Dict, Any
_COOP = {"pool_usd": 0.0, "sponsors": []}
def sponsor_add(name: str, spend_cap_usd: float) -> Dict[str,Any]:
    _COOP["sponsors"].append({"name": name, "cap_usd": float(spend_cap_usd), "spent_usd": 0.0})
    _COOP["pool_usd"] += float(spend_cap_usd); return _COOP
def spend_from_coop(user: str, amount_usd: float) -> Dict[str,Any]:
    amt = float(amount_usd)
    if _COOP["pool_usd"] < amt: return {"ok": False, "reason":"insufficient_coop_pool", "pool_usd": _COOP["pool_usd"]}
    _COOP["pool_usd"] -= amt; return {"ok": True, "user": user, "amount_usd": amt, "pool_usd": _COOP["pool_usd"]}
def state() -> Dict[str,Any]: return _COOP
