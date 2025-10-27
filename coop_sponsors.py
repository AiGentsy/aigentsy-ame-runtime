from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()
_state = {"pool_usd": 0.0, "sponsors": []}

class SponsorAdd(BaseModel):
    name: str
    spend_cap_usd: float

@router.post("/sponsor")
def sponsor_add(req: SponsorAdd):
    _state["sponsors"].append({"name": req.name, "cap": req.spend_cap_usd})
    _state["pool_usd"] = float(_state.get("pool_usd",0)) + float(req.spend_cap_usd)
    return {"ok": True, "pool_usd": _state["pool_usd"], "sponsors": _state["sponsors"]}

def state():
    return _state
