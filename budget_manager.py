
# budget_manager.py
from typing import Dict, Any
def topup(user: Dict[str,Any], usd: float) -> Dict[str,Any]:
    cp = user.get("channel_pacing", [])
    for c in cp: c["max"] = round(c.get("max", 50) * 1.1, 2)
    return {"ok": True, "new_channel_pacing": cp, "added_usd": float(usd)}
