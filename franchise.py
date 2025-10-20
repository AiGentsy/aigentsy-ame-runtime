
# franchise.py
from typing import List, Dict, Any
from uuid import uuid4
_PACKS: Dict[str, Dict[str,Any]] = {}
def publish_pack(author: str, manifests: List[str], fee_pct: float) -> Dict[str,Any]:
    pid = str(uuid4())
    _PACKS[pid] = {"id": pid, "author": author, "manifests": manifests, "fee_pct": float(fee_pct), "active_users": []}
    return _PACKS[pid]
def activate_pack(user: str, pack_id: str) -> Dict[str,Any]:
    p = _PACKS.get(pack_id)
    if not p: raise ValueError("pack not found")
    if user not in p["active_users"]: p["active_users"].append(user)
    return {"ok": True, "pack": p}
