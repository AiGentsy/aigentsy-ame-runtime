
# intent_exchange.py
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime
_INTENTS: Dict[str, Dict[str, Any]] = {}
def now_iso(): return datetime.utcnow().isoformat() + "Z"
def publish(intent: dict) -> dict:
    iid = str(uuid4()); payload = {"id": iid, "intent": intent or {}, "status": "PUBLISHED",
                                   "events": [{"type":"INTENT_PUBLISHED","at": now_iso()}],
                                   "claimed_by": None, "settlement": None}
    _INTENTS[iid] = payload; return payload
def claim(intent_id: str, agent: str) -> dict:
    it = _INTENTS.get(intent_id); 
    if not it: raise ValueError("intent not found")
    it["status"] = "CLAIMED"; it["claimed_by"] = agent
    it["events"].append({"type":"INTENT_CLAIMED","agent":agent,"at": now_iso()}); return it
def settle(intent_id: str, outcome: dict) -> dict:
    it = _INTENTS.get(intent_id); 
    if not it: raise ValueError("intent not found")
    it["status"] = "SETTLED"; it["settlement"] = outcome or {}
    it["events"].append({"type":"INTENT_SETTLED","outcome": outcome,"at": now_iso()}); return it
def get(intent_id: str) -> dict: return _INTENTS.get(intent_id, {})
