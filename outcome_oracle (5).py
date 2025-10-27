from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
try:
    from .jsonbin_client import JSONBinClient
except Exception:
    JSONBinClient = None
try:
    from .event_bus import publish
except Exception:
    def publish(*a, **k): pass

AIGX_PER_DOLLAR = 1.0
router = APIRouter()

class Event(BaseModel):
    user_id: str
    source: str
    kind: str
    amount_usd: Optional[float]=0.0
    metadata: Optional[Dict[str, Any]] = None

def _ensure_user_fields(record:dict, uid:str):
    users = record.get("users") or record.get("Users") or []
    target = None
    for u in users:
        if u.get("id")==uid or u.get("consent",{}).get("username")==uid:
            target = u; break
    if not target:
        target = {"id": uid}
        users.append(target)
        record["users"] = users
    target.setdefault("dealGraph", {"nodes": [], "edges": [], "revSplit": []})
    target.setdefault("intents", [])
    target.setdefault("r3", {"budget_usd": 0, "last_allocation": None})
    target.setdefault("mesh", {"sessions": []})
    target.setdefault("coop", {"pool_usd": 0, "sponsors": []})
    target.setdefault("autoStake_policy", {"ratio": 0.25, "weekly_cap_usd": 50, "enabled": True})
    target.setdefault("franchise_packs", [])
    target.setdefault("risk", {"complaints_rate": 0, "riskScore": 0, "region": "US"})
    target.setdefault("channel_pacing", [{"channel":"tiktok","min":0,"max":50}])
    target.setdefault("skills", [])
    target.setdefault("bounties_seen", [])
    target.setdefault("assets_published", [])
    target.setdefault("reactivation", {"last_run": None, "outcomes": []})
    target.setdefault("wallet", {}).setdefault("aigx", 0)
    target.setdefault("kpis", {"paid_events":0,"gmv_usd":0.0,"earnings_week_usd":0.0})
    return record, target

@router.post("/event")
def receive_event(event: Event):
    data = {}
    if JSONBinClient:
        try:
            jb = JSONBinClient(); data = jb.get_latest().get("record") or {}
        except Exception: data = {}
    data, user = _ensure_user_fields(data, event.user_id)

    if event.kind in ("PURCHASED","PAID","PAID_ESCROW","REUSE_FEE_PAID","NETTED_PROFIT"):
        user["wallet"]["aigx"] = round(float(user["wallet"].get("aigx",0)) + float(event.amount_usd or 0)*AIGX_PER_DOLLAR, 2)
        user["kpis"]["gmv_usd"] = round(float(user["kpis"].get("gmv_usd",0.0)) + float(event.amount_usd or 0), 2)
        if event.kind in ("PAID","PAID_ESCROW"):
            user["kpis"]["paid_events"] = int(user["kpis"].get("paid_events",0)) + 1
            publish("PAID", {"user_id":event.user_id,"amount_usd":event.amount_usd})
            pol = user.get("autoStake_policy", {})
            if pol.get("enabled"):
                ratio = float(pol.get("ratio",0.25))
                budget = round((event.amount_usd or 0.0) * ratio, 2)
                publish("R3_ENQUEUE", {"user_id":event.user_id,"budget_usd":budget})

    if event.kind in ("PROPOSAL_STALLED","ABANDONED_CART","REACTIVATION_SENT","FLASH_SALE_FIRED"):
        publish(event.kind, {"user_id":event.user_id, "meta":event.metadata or {}})

    user["kpis"]["earnings_week_usd"] = round(float(user["kpis"].get("earnings_week_usd",0.0)) + float(event.amount_usd or 0), 2)

    if JSONBinClient:
        try: jb.put_record(data)
        except Exception: pass
    return {"ok": True, "user": event.user_id}
