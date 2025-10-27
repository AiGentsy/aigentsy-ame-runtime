from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from uuid import uuid4
from datetime import datetime
try:
    from .jsonbin_client import JSONBinClient  # optional
except Exception:
    JSONBinClient = None
try:
    from .event_bus import publish
except Exception:
    def publish(*a, **k): pass

router = APIRouter()

_INTENTS: Dict[str, Dict[str, Any]] = {}

def now_iso(): return datetime.utcnow().isoformat() + "Z"

class Intent(BaseModel):
    user_id: str
    intent: Dict[str, Any]
    escrow_usd: Optional[float] = 0.0

class Claim(BaseModel):
    intent_id: str
    agent: str

class Settle(BaseModel):
    intent_id: str
    outcome: Dict[str, Any]

@router.post("/publish")
def publish_intent(req: Intent):
    iid = str(uuid4())
    payload = {
        "id": iid,
        "from": req.user_id,
        "intent": req.intent or {},
        "status": "PUBLISHED",
        "events": [{"type":"INTENT_PUBLISHED","at": now_iso()}],
        "claimed_by": None,
        "settlement": None,
        "escrow_usd": float(req.escrow_usd or 0.0),
    }
    _INTENTS[iid] = payload
    publish("INTENT_PUBLISHED", {"id": iid, "user_id": req.user_id, "escrow_usd": payload["escrow_usd"]})
    # Optionally mirror to JSONBin (flat list)
    if JSONBinClient:
        try:
            jb = JSONBinClient(); data = jb.get_latest().get("record") or {}
            intents = data.setdefault("intents", []); intents.append({"id":iid, "from":req.user_id, "status":"OPEN", "body":req.intent, "escrow_usd": payload["escrow_usd"]})
            jb.put_record(data)
        except Exception: pass
    return {"ok": True, "intent_id": iid, "escrow_usd": payload["escrow_usd"]}

@router.post("/claim")
def claim_intent(req: Claim):
    it = _INTENTS.get(req.intent_id)
    if not it: raise HTTPException(status_code=404, detail="intent not found")
    it["status"] = "CLAIMED"; it["claimed_by"] = req.agent
    it["events"].append({"type":"INTENT_CLAIMED","agent":req.agent,"at": now_iso()})
    publish("INTENT_CLAIMED", {"id": req.intent_id, "agent": req.agent})
    return {"ok": True}

@router.post("/settle")
def settle_intent(req: Settle):
    it = _INTENTS.get(req.intent_id)
    if not it: raise HTTPException(status_code=404, detail="intent not found")
    it["status"] = "SETTLED"; it["settlement"] = req.outcome or {}
    it["events"].append({"type":"INTENT_SETTLED","outcome": req.outcome,"at": now_iso()})
    publish("INTENT_SETTLED", {"id": req.intent_id, "outcome": req.outcome})
    # If escrow was used, emit PAID_ESCROW via events bus for Oracle pipeline
    escrow = float(it.get("escrow_usd") or 0.0)
    if escrow > 0:
        publish("PAID_ESCROW", {"intent_id": req.intent_id, "amount_usd": escrow})
    return {"ok": True}
