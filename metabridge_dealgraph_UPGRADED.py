from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
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

class AgentMatchReq(BaseModel):
    agent_id: str
    skills_needed: List[str]
    budget_usd: float


async def _match_users_by_role(role: str, exclude: List[str] = None) -> List[Dict[str, Any]]:
    """Find users with matching traits/capabilities"""
    exclude = exclude or []
    
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
        
        if role == "developer" and any(t in traits for t in ["sdk", "technical", "cto"]):
            score = 0.85
        elif role == "marketer" and any(t in traits for t in ["marketing", "growth", "cmo"]):
            score = 0.75
        elif role == "legal" and "legal" in traits:
            score = 0.80
        elif role == "designer" and any(t in traits for t in ["branding", "design"]):
            score = 0.70
        elif role == "video" and any(t in traits for t in ["content", "video", "tiktok"]):
            score = 0.75
        elif role == "copywriter" and any(t in traits for t in ["content", "marketing", "copywriting"]):
            score = 0.70
        elif role == "founder" and "founder" in traits:
            score = 0.65
        
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
    
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:3]


async def _match_complementary_agents(agent_id: str, skills_needed: List[str]) -> List[Dict[str, Any]]:
    """Match agent with complementary skills for bundling"""
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get("https://aigentsy-ame-runtime.onrender.com/users/all")
            users = r.json().get("users", [])
        except Exception as e:
            print(f"Failed to fetch users: {e}")
            return []
    
    # Get requesting agent's skills
    requester = next((u for u in users if u.get("username") == agent_id), None)
    if not requester:
        return []
    
    requester_traits = set(requester.get("traits", []))
    
    matches = []
    for u in users:
        username = u.get("username")
        if username == agent_id:
            continue
        
        candidate_traits = set(u.get("traits", []))
        
        # Calculate complementary score
        # Higher score if they have skills requester doesn't
        complementary = candidate_traits - requester_traits
        overlap = candidate_traits & requester_traits
        
        has_needed = sum(1 for skill in skills_needed if skill in candidate_traits)
        
        if has_needed == 0:
            continue
        
        # Score: needed skills + complementary - overlap penalty
        score = (has_needed * 0.4) + (len(complementary) * 0.1) - (len(overlap) * 0.05)
        
        # Boost by outcome score
        outcome_score = int(u.get("outcomeScore", 0))
        if outcome_score > 60:
            score += 0.1
        elif outcome_score > 80:
            score += 0.15
        
        matches.append({
            "user": username,
            "skills": list(candidate_traits),
            "needed_skills": [s for s in skills_needed if s in candidate_traits],
            "complementary_skills": list(complementary),
            "score": round(score, 2),
            "outcome_score": outcome_score
        })
    
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]


@router.post("/create")
async def create(req: CreateReq):
    """Create DealGraph with real user matching"""
    gid = str(uuid4())
    
    all_matches = {}
    nodes = [{"id": req.user_id, "role": "initiator"}]
    edges = []
    
    for role in req.roles_needed:
        matches = await _match_users_by_role(role, exclude=[req.user_id])
        all_matches[role] = matches
        
        if matches:
            best = matches[0]
            nodes.append({
                "id": best["user"],
                "role": role,
                "score": best["score"]
            })
            
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


@router.post("/match_agents")
async def match_agents(req: AgentMatchReq):
    """Agent-to-agent matching for bundled services"""
    
    matches = await _match_complementary_agents(req.agent_id, req.skills_needed)
    
    if not matches:
        return {"ok": True, "matches": [], "message": "No complementary agents found"}
    
    # Create bundle proposals
    bundles = []
    for match in matches:
        bundle_id = f"bundle_{uuid4().hex[:8]}"
        
        # Calculate bundle pricing (discount for combined)
        individual_price = req.budget_usd
        match_estimated_price = req.budget_usd * 0.8
        bundle_price = round((individual_price + match_estimated_price) * 0.85, 2)
        discount_pct = round((1 - (bundle_price / (individual_price + match_estimated_price))) * 100, 1)
        
        bundle = {
            "bundle_id": bundle_id,
            "agents": [req.agent_id, match["user"]],
            "skills_covered": list(set(req.skills_needed) & set(match["needed_skills"])),
            "individual_prices": {
                req.agent_id: individual_price,
                match["user"]: match_estimated_price
            },
            "bundle_price": bundle_price,
            "discount_pct": discount_pct,
            "revenue_split": {
                req.agent_id: 0.55,
                match["user"]: 0.45
            },
            "match_score": match["score"],
            "status": "PROPOSED",
            "created_at": now_iso()
        }
        
        bundles.append(bundle)
    
    return {
        "ok": True,
        "matches": matches,
        "bundles": bundles,
        "count": len(bundles)
    }


@router.post("/activate")
async def activate(req: ActivateReq):
    """Activate DealGraph and send proposals"""
    g = _DEALGRAPHS.get(req.graph_id)
    if not g:
        raise HTTPException(status_code=404, detail="dealgraph not found")
    
    if g["status"] == "ACTIVATED":
        return {"ok": True, "message": "already activated"}
    
    proposals_sent = []
    opportunity = g["opportunity"]
    budget = float(opportunity.get("budget", 0))
    
    for edge in g["edges"]:
        recipient = edge["to"]
        role = edge["role"]
        rev_share = float(edge["rev_share"])
        amount = round(budget * rev_share, 2)
        
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
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                    json=proposal
                )
                proposals_sent.append(proposal)
            except Exception as e:
                print(f"Failed to send proposal to {recipient}: {e}")
    
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
    """Retrieve DealGraph status"""
    g = _DEALGRAPHS.get(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail="dealgraph not found")
    return {"ok": True, "graph": g}
