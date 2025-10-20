
# r3_router.py
from typing import Dict, Any
from datetime import datetime
DEFAULT_PACINGS = [
    {"channel":"tiktok","min":0,"max":50},
    {"channel":"amazon","min":0,"max":50},
    {"channel":"shopify","min":0,"max":50},
]
def allocate(user: Dict[str,Any], budget_usd: float) -> Dict[str,Any]:
    allocations = []; channels = user.get("channel_pacing", DEFAULT_PACINGS)
    per = budget_usd / max(len(channels),1)
    for c in channels:
        amt = min(per, c.get("max", per))
        if amt > 0: allocations.append({"channel": c["channel"], "usd": round(amt,2)})
    return {"user": user.get("id") or user.get("username") or "unknown",
            "budget_usd": budget_usd, "allocations": allocations, "at": datetime.utcnow().isoformat() + "Z"}
