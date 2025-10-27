from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime
try:
    from .event_bus import publish
except Exception:
    def publish(*a, **k): pass

router = APIRouter()
_DEALGRAPHS: Dict[str, Dict[str, Any]] = {}
def now_iso() -> str: return datetime.utcnow().isoformat() + "Z"

class CreateReq(BaseModel):
    user_id: str
    opportunity: Dict[str, Any]
    roles_needed: List[str]
    rev_split: List[Dict[str, Any]]

class ActivateReq(BaseModel):
    user_id: str
    graph_id: str

@router.post("/create")
def create(req: CreateReq):
    gid = str(uuid4())
    g = {"id": gid, "opportunity": req.opportunity or {}, "roles": req.roles_needed or [], "rev_split": req.rev_split or [],
         "nodes": [], "edges": [], "status": "CREATED", "events": [{"type":"DEALGRAPH_CREATED","at": now_iso()}]}
    _DEALGRAPHS[gid] = g
    publish("DEALGRAPH_CREATED", {"user_id": req.user_id, "graph_id": gid})
    return {"ok": True, "graph_id": gid}

@router.post("/activate")
def activate(req: ActivateReq):
    g = _DEALGRAPHS.get(req.graph_id)
    if not g: raise HTTPException(status_code=404, detail="dealgraph not found")
    g["status"] = "ACTIVATED"; g["events"].append({"type":"DEALGRAPH_ACTIVATED","at": now_iso()})
    publish("DEALGRAPH_ACTIVATED", {"user_id": req.user_id, "graph_id": req.graph_id})
    return {"ok": True}
