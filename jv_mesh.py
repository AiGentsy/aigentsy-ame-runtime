from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import httpx

_JV_PROPOSALS: Dict[str, Dict[str, Any]] = {}
_ACTIVE_JVS: Dict[str, Dict[str, Any]] = {}

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


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
    
    # Auto-calculate fair revenue split based on reputation
    agent = next((a for a in all_agents if (a.get("username") == agent_username or a.get("consent", {}).get("username") == agent_username)), None)
    partner = next((a for a in all_agents if (a.get("username") == partner_username or a.get("consent", {}).get("username") == partner_username)), None)
    
    if not agent or not partner:
        return {"ok": False, "error": "agent_not_found"}
    
    agent_score = int(agent.get("outcomeScore", 50))
    partner_score = int(partner.get("outcomeScore", 50))
    total_score = agent_score + partner_score
    
    # Split based on reputation ratio
    agent_split = round(agent_score / total_score, 2) if total_score > 0 else 0.5
    partner_split = round(1.0 - agent_split, 2)
    
    # Create proposal using existing function
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
