from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import httpx

_JV_PROPOSALS: Dict[str, Dict[str, Any]] = {}
_ACTIVE_JVS: Dict[str, Dict[str, Any]] = {}

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def create_jv_proposal(
    proposer: str,
    partner: str,
    title: str,
    description: str,
    revenue_split: Dict[str, float],
    duration_days: int = 90,
    terms: Dict[str, Any] = None
) -> Dict[str, Any]:
    
    if proposer == partner:
        return {"ok": False, "error": "cannot_propose_to_self"}
    
    total_split = sum(revenue_split.values())
    if abs(total_split - 1.0) > 0.01:
        return {"ok": False, "error": "revenue_split_must_equal_100_percent"}
    
    proposal_id = f"jvp_{uuid4().hex[:8]}"
    
    proposal = {
        "id": proposal_id,
        "proposer": proposer,
        "partner": partner,
        "title": title,
        "description": description,
        "revenue_split": revenue_split,
        "duration_days": duration_days,
        "terms": terms or {},
        "status": "PENDING",
        "created_at": now_iso(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat() + "Z",
        "votes": {
            proposer: "APPROVED",
            partner: "PENDING"
        },
        "events": [{"type": "PROPOSAL_CREATED", "by": proposer, "at": now_iso()}]
    }
    
    _JV_PROPOSALS[proposal_id] = proposal
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                json={
                    "id": f"jv_notif_{uuid4().hex[:8]}",
                    "sender": proposer,
                    "recipient": partner,
                    "title": f"JV Proposal: {title}",
                    "body": f"{proposer} proposing JV. Review at /jv/proposals/{proposal_id}",
                    "meta": {"jv_proposal_id": proposal_id},
                    "status": "sent",
                    "timestamp": now_iso()
                }
            )
        except Exception as e:
            print(f"Failed to notify partner: {e}")
    
    return {"ok": True, "proposal_id": proposal_id, "proposal": proposal}


async def vote_on_jv(
    proposal_id: str,
    voter: str,
    vote: str,
    feedback: str = ""
) -> Dict[str, Any]:
    
    proposal = _JV_PROPOSALS.get(proposal_id)
    if not proposal:
        return {"ok": False, "error": "proposal_not_found"}
    
    if proposal["status"] != "PENDING":
        return {"ok": False, "error": f"proposal_already_{proposal['status'].lower()}"}
    
    if voter not in [proposal["proposer"], proposal["partner"]]:
        return {"ok": False, "error": "voter_not_party_to_proposal"}
    
    if vote.upper() not in ["APPROVED", "REJECTED"]:
        return {"ok": False, "error": "vote_must_be_APPROVED_or_REJECTED"}
    
    proposal["votes"][voter] = vote.upper()
    proposal["events"].append({
        "type": f"VOTE_{vote.upper()}",
        "by": voter,
        "feedback": feedback,
        "at": now_iso()
    })
    
    proposer_vote = proposal["votes"][proposal["proposer"]]
    partner_vote = proposal["votes"][proposal["partner"]]
    
    if proposer_vote == "APPROVED" and partner_vote == "APPROVED":
        proposal["status"] = "APPROVED"
        jv = await activate_jv(proposal)
        
        return {
            "ok": True,
            "status": "APPROVED",
            "jv_id": jv.get("jv_id"),
            "message": "JV activated"
        }
    
    elif "REJECTED" in [proposer_vote, partner_vote]:
        proposal["status"] = "REJECTED"
        proposal["rejection_reason"] = feedback
        
        return {
            "ok": True,
            "status": "REJECTED",
            "message": "JV proposal rejected"
        }
    
    return {
        "ok": True,
        "status": "PENDING",
        "message": "Vote recorded, waiting for other party"
    }


async def activate_jv(proposal: Dict[str, Any]) -> Dict[str, Any]:
    
    jv_id = f"jv_{uuid4().hex[:8]}"
    
    jv = {
        "id": jv_id,
        "proposal_id": proposal["id"],
        "parties": [proposal["proposer"], proposal["partner"]],
        "title": proposal["title"],
        "revenue_split": proposal["revenue_split"],
        "duration_days": proposal["duration_days"],
        "terms": proposal["terms"],
        "status": "ACTIVE",
        "created_at": now_iso(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=proposal["duration_days"])).isoformat() + "Z",
        "total_revenue": 0.0,
        "distributions": [],
        "events": [{"type": "JV_ACTIVATED", "at": now_iso()}]
    }
    
    _ACTIVE_JVS[jv_id] = jv
    
    return {"ok": True, "jv_id": jv_id, "jv": jv}


async def dissolve_jv(
    jv_id: str,
    requester: str,
    reason: str = ""
) -> Dict[str, Any]:
    
    jv = _ACTIVE_JVS.get(jv_id)
    if not jv:
        return {"ok": False, "error": "jv_not_found"}
    
    if requester not in jv["parties"]:
        return {"ok": False, "error": "requester_not_party_to_jv"}
    
    if jv["status"] != "ACTIVE":
        return {"ok": False, "error": f"jv_already_{jv['status'].lower()}"}
    
    jv["status"] = "DISSOLVING"
    jv["dissolution_requested_by"] = requester
    jv["dissolution_reason"] = reason
    jv["dissolution_effective_at"] = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat() + "Z"
    jv["events"].append({
        "type": "DISSOLUTION_REQUESTED",
        "by": requester,
        "reason": reason,
        "at": now_iso()
    })
    
    return {"ok": True, "jv": jv, "effective_at": jv["dissolution_effective_at"]}


def get_jv_proposal(proposal_id: str) -> Dict[str, Any]:
    proposal = _JV_PROPOSALS.get(proposal_id)
    if not proposal:
        return {"ok": False, "error": "proposal_not_found"}
    return {"ok": True, "proposal": proposal}


def get_active_jv(jv_id: str) -> Dict[str, Any]:
    jv = _ACTIVE_JVS.get(jv_id)
    if not jv:
        return {"ok": False, "error": "jv_not_found"}
    return {"ok": True, "jv": jv}


def list_jv_proposals(party: str = None, status: str = None) -> Dict[str, Any]:
    proposals = list(_JV_PROPOSALS.values())
    
    if party:
        proposals = [p for p in proposals if party in [p["proposer"], p["partner"]]]
    
    if status:
        proposals = [p for p in proposals if p["status"] == status.upper()]
    
    proposals.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"ok": True, "proposals": proposals, "count": len(proposals)}


def list_active_jvs(party: str = None) -> Dict[str, Any]:
    jvs = list(_ACTIVE_JVS.values())
    
    if party:
        jvs = [j for j in jvs if party in j["parties"]]
    
    jvs.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"ok": True, "jvs": jvs, "count": len(jvs)}


# ============ AUTONOMOUS MATCHING ============

SKILL_CATEGORIES = [
    "design", "development", "copywriting", "marketing",
    "seo", "video", "data_analysis", "consulting", "project_management"
]


def calculate_compatibility_score(
    agent1: Dict[str, Any],
    agent2: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate compatibility between two agents"""
    skills1 = set(agent1.get("profile", {}).get("skills", []))
    skills2 = set(agent2.get("profile", {}).get("skills", []))
    
    overlap = len(skills1.intersection(skills2))
    total_skills = len(skills1.union(skills2))
    complementary_score = 1 - (overlap / total_skills) if total_skills > 0 else 0
    
    score1 = int(agent1.get("outcomeScore", 50))
    score2 = int(agent2.get("outcomeScore", 50))
    reputation_diff = abs(score1 - score2)
    reputation_compatibility = 1 - (reputation_diff / 100)
    
    overall_score = (complementary_score * 0.50) + (reputation_compatibility * 0.50)
    
    return {
        "overall_score": round(overall_score, 3),
        "complementary_score": round(complementary_score, 3),
        "reputation_compatibility": round(reputation_compatibility, 3),
        "shared_skills": list(skills1.intersection(skills2)),
        "unique_skills": list(skills1.symmetric_difference(skills2))
    }


def suggest_jv_partners(
    agent: Dict[str, Any],
    all_agents: List[Dict[str, Any]],
    min_score: float = 0.6,
    limit: int = 5
) -> Dict[str, Any]:
    """AI suggests potential JV partners"""
    agent_username = agent.get("consent", {}).get("username") or agent.get("username")
    
    candidates = []
    
    for potential_partner in all_agents:
        partner_username = potential_partner.get("consent", {}).get("username") or potential_partner.get("username")
        
        if partner_username == agent_username:
            continue
        
        compatibility = calculate_compatibility_score(agent, potential_partner)
        
        if compatibility["overall_score"] >= min_score:
            candidates.append({
                "username": partner_username,
                "outcome_score": int(potential_partner.get("outcomeScore", 0)),
                "compatibility": compatibility
            })
    
    candidates.sort(key=lambda c: c["compatibility"]["overall_score"], reverse=True)
    
    return {
        "ok": True,
        "agent": agent_username,
        "suggested_partners": candidates[:limit],
        "total_compatible": len(candidates)
    }


async def auto_propose_jv(
    agent_username: str,
    suggested_partner: Dict[str, Any],
    all_agents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Automatically create JV proposal to suggested partner"""
    partner_username = suggested_partner["username"]
    compatibility = suggested_partner["compatibility"]
    
    agent = next((a for a in all_agents if (a.get("username") == agent_username or a.get("consent", {}).get("username") == agent_username)), None)
    partner = next((a for a in all_agents if (a.get("username") == partner_username or a.get("consent", {}).get("username") == partner_username)), None)
    
    if not agent or not partner:
        return {"ok": False, "error": "agent_not_found"}
    
    agent_score = int(agent.get("outcomeScore", 50))
    partner_score = int(partner.get("outcomeScore", 50))
    total_score = agent_score + partner_score
    
    agent_split = round(agent_score / total_score, 2) if total_score > 0 else 0.5
    partner_split = round(1.0 - agent_split, 2)
    
    result = await create_jv_proposal(
        proposer=agent_username,
        partner=partner_username,
        title=f"AI-Matched Partnership: {agent_username} + {partner_username}",
        description=f"Compatibility Score: {compatibility['overall_score']}. Complementary skills: {', '.join(compatibility['unique_skills'][:3])}",
        revenue_split={agent_username: agent_split, partner_username: partner_split},
        duration_days=90,
        terms={
            "ai_suggested": True,
            "compatibility_score": compatibility["overall_score"],
            "complementary_score": compatibility["complementary_score"]
        }
    )
    
    return result


def evaluate_jv_performance(
    jv: Dict[str, Any],
    users: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Evaluate JV partnership performance"""
    parties = jv["parties"]
    
    total_projects = 0
    total_revenue = float(jv.get("total_revenue", 0))
    on_time_count = 0
    disputes = 0
    
    for user in users:
        username = user.get("consent", {}).get("username") or user.get("username")
        
        if username not in parties:
            continue
        
        ledger = user.get("ownership", {}).get("ledger", [])
        
        for entry in ledger:
            if entry.get("jv_id") == jv["id"]:
                basis = entry.get("basis", "")
                
                if basis == "jv_revenue":
                    total_projects += 1
                
                if basis == "sla_bonus":
                    on_time_count += 1
                
                if basis == "bond_slash":
                    disputes += 1
    
    on_time_rate = (on_time_count / total_projects) if total_projects > 0 else 0
    dispute_rate = (disputes / total_projects) if total_projects > 0 else 0
    
    if on_time_rate >= 0.8 and dispute_rate < 0.1:
        grade = "excellent"
    elif on_time_rate >= 0.6 and dispute_rate < 0.2:
        grade = "good"
    else:
        grade = "fair"
    
    return {
        "jv_id": jv["id"],
        "parties": parties,
        "total_projects": total_projects,
        "total_revenue": round(total_revenue, 2),
        "on_time_rate": round(on_time_rate, 2),
        "dispute_rate": round(dispute_rate, 3),
        "performance_grade": grade,
        "evaluated_at": now_iso()
    }
