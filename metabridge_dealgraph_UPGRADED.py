from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime
import httpx

try:
    from event_bus import publish as event_publish
except Exception:
    def event_publish(*a, **k): pass

router = APIRouter()
_DEALGRAPHS: Dict[str, Dict[str, Any]] = {}

def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

class CreateReq(BaseModel):
    user_id: str
    opportunity: Dict[str, Any]
    roles_needed: List[str]
    rev_split: List[Dict[str, Any]]

class ActivateReq(BaseModel):
    user_id: str
    graph_id: str


async def _match_users_by_role(role: str, exclude: List[str] = None) -> List[Dict[str, Any]]:
    """
    Find users with matching traits/capabilities from your live user database.
    """
    exclude = exclude or []
    
    # Call your main.py /users/all endpoint
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get("https://aigentsy-ame-runtime.onrender.com/users/all")
            users = r.json().get("users", [])
        except Exception as e:
            print(f"Failed to fetch users: {e}")
            return []
    
    matches = []
    for u in users:
        username = u.get("username")
        if username in exclude:
            continue
        
        traits = u.get("traits", [])
        score = 0.0
        
        # Role matching logic
        if role == "developer" and any(t in traits for t in ["sdk", "technical", "cto"]):
            score = 0.85
        elif role == "marketer" and any(t in traits for t in ["marketing", "growth", "cmo"]):
            score = 0.75
        elif role == "legal" and "legal" in traits:
            score = 0.80
        elif role == "designer" and any(t in traits for t in ["branding", "design"]):
            score = 0.70
        elif role == "founder" and "founder" in traits:
            score = 0.65
        
        # Boost by outcome score
        outcome_score = int(u.get("outcomeScore", 0))
        if outcome_score > 60:
            score += 0.1
        elif outcome_score > 80:
            score += 0.15
        
        if score > 0:
            matches.append({
                "user": username,
                "role": role,
                "score": round(score, 2),
                "traits": traits,
                "outcome_score": outcome_score
            })
    
    # Sort by score, return top 3
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:3]


@router.post("/create")
async def create(req: CreateReq):
    """
    Create DealGraph with REAL user matching from your database.
    """
    gid = str(uuid4())
    
    # Find matches for each role
    all_matches = {}
    nodes = [{"id": req.user_id, "role": "initiator"}]
    edges = []
    
    for role in req.roles_needed:
        matches = await _match_users_by_role(role, exclude=[req.user_id])
        all_matches[role] = matches
        
        # Add best match to nodes
        if matches:
            best = matches[0]
            nodes.append({
                "id": best["user"],
                "role": role,
                "score": best["score"]
            })
            
            # Add edge from initiator to matched user
            rev_share = next((s["share"] for s in req.rev_split if s["role"] == role), 0.0)
            edges.append({
                "from": req.user_id,
                "to": best["user"],
                "type": "needs",
                "role": role,
                "rev_share": rev_share
            })
    
    g = {
        "id": gid,
        "user_id": req.user_id,
        "opportunity": req.opportunity or {},
        "roles": req.roles_needed or [],
        "rev_split": req.rev_split or [],
        "matches": all_matches,
        "nodes": nodes,
        "edges": edges,
        "status": "CREATED",
        "proposals_sent": [],
        "events": [{"type": "DEALGRAPH_CREATED", "at": now_iso()}],
        "created_at": now_iso()
    }
    
    _DEALGRAPHS[gid] = g
    event_publish("DEALGRAPH_CREATED", {"user_id": req.user_id, "graph_id": gid, "matches": len(nodes) - 1})
    
    return {
        "ok": True,
        "graph_id": gid,
        "matches": all_matches,
        "nodes": nodes,
        "edges": edges
    }


@router.post("/activate")
async def activate(req: ActivateReq):
    """
    Activate DealGraph = auto-send proposals to matched users.
    """
    g = _DEALGRAPHS.get(req.graph_id)
    if not g:
        raise HTTPException(status_code=404, detail="dealgraph not found")
    
    if g["status"] == "ACTIVATED":
        return {"ok": True, "message": "already activated"}
    
    # Auto-generate and send proposals to each matched user
    proposals_sent = []
    opportunity = g["opportunity"]
    budget = float(opportunity.get("budget", 0))
    
    for edge in g["edges"]:
        recipient = edge["to"]
        role = edge["role"]
        rev_share = float(edge["rev_share"])
        amount = round(budget * rev_share, 2)
        
        # Generate proposal
        proposal = {
            "id": f"prop_{uuid4().hex[:8]}",
            "sender": req.user_id,
            "recipient": recipient,
            "title": f"{opportunity.get('title', 'Opportunity')} - {role.title()} Role",
            "body": f"""You've been matched for the {role} role.

Project: {opportunity.get('title', 'Untitled')}
Budget: ${amount} ({int(rev_share * 100)}% share)
Deadline: {opportunity.get('deadline', 'TBD')}

Accept to join the DealGraph.""",
            "amount": amount,
            "meta": {
                "dealgraph_id": req.graph_id,
                "role": role,
                "rev_share": rev_share
            },
            "status": "sent",
            "timestamp": now_iso(),
            "auto_generated": True
        }
        
        # Send proposal via main.py
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                    json=proposal
                )
                proposals_sent.append(proposal)
            except Exception as e:
                print(f"Failed to send proposal to {recipient}: {e}")
    
    # Update graph status
    g["status"] = "ACTIVATED"
    g["proposals_sent"] = proposals_sent
    g["events"].append({"type": "DEALGRAPH_ACTIVATED", "at": now_iso()})
    
    event_publish("DEALGRAPH_ACTIVATED", {
        "user_id": req.user_id,
        "graph_id": req.graph_id,
        "proposals_sent": len(proposals_sent)
    })
    
    return {
        "ok": True,
        "proposals_sent": proposals_sent,
        "message": f"Sent {len(proposals_sent)} proposals"
    }


@router.get("/{graph_id}")
async def get_dealgraph(graph_id: str):
    """
    Retrieve DealGraph status.
    """
    g = _DEALGRAPHS.get(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail="dealgraph not found")
    return {"ok": True, "graph": g}
