
# metabridge_dealgraph.py
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime
_DEALGRAPHS: Dict[str, Dict[str, Any]] = {}
def now_iso() -> str: return datetime.utcnow().isoformat() + "Z"
def create_dealgraph(opportunity: dict, roles_needed: List[str], rev_split: List[dict]) -> dict:
    gid = str(uuid4())
    g = {"id": gid, "opportunity": opportunity or {}, "roles": roles_needed or [], "rev_split": rev_split or [],
         "nodes": [], "edges": [], "status": "CREATED", "events": [{"type":"DEALGRAPH_CREATED","at": now_iso()}]}
    _DEALGRAPHS[gid] = g; return g
def invite_roles(graph_id: str) -> dict:
    g = _DEALGRAPHS.get(graph_id); 
    if not g: raise ValueError("dealgraph not found")
    g["status"] = "INVITED"; g["events"].append({"type":"DEALGRAPH_INVITED","at": now_iso()}); return g
def activate(graph_id: str) -> dict:
    g = _DEALGRAPHS.get(graph_id); 
    if not g: raise ValueError("dealgraph not found")
    g["status"] = "ACTIVATED"; g["events"].append({"type":"DEALGRAPH_ACTIVATED","at": now_iso()}); return g
def get(graph_id: str) -> dict: return _DEALGRAPHS.get(graph_id, {})
