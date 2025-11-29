from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from jsonbin_client import JSONBinClient
from event_bus import publish

router = APIRouter()

class AllocateReq(BaseModel):
    user_id: str
    budget_usd: float

def predict_roi(user:dict, channel:str)->float:
    base = 1.0
    if channel == "tiktok": base = 1.1
    if channel == "amazon": base = 1.05
    if channel == "shopify": base = 1.0
    return base

@router.post("/allocate")
def allocate(req: AllocateReq):
    jb = JSONBinClient()
    data = jb.get_latest().get("record") or {}
    users = data.get("users") or []
    u = next((x for x in users if x.get("id")==req.user_id or x.get("consent",{}).get("username")==req.user_id), None)
    if not u:
        return {"ok": False, "error":"user_not_found"}
    channels = ["tiktok","amazon","shopify"]
    scored = [(ch, predict_roi(u, ch)) for ch in channels]
    best = sorted(scored, key=lambda x: x[1], reverse=True)[0][0]
    r3 = u.setdefault("r3", {"budget_usd":0,"last_allocation":None})
    r3["budget_usd"] = float(r3.get("budget_usd",0)) + float(req.budget_usd)
    r3["last_allocation"] = {"channel": best, "budget_usd": req.budget_usd}
    jb.put_record(data)
    publish("R3_ALLOCATED", {"user_id":req.user_id, "channel":best, "budget_usd":req.budget_usd})
    return {"ok": True, "channel": best}
