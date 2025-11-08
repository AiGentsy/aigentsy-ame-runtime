from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import httpx

_HIVE_MEMBERS: Dict[str, Dict[str, Any]] = {}
_HIVE_TREASURY: Dict[str, Any] = {
    "total_revenue": 0.0,
    "distributed": 0.0,
    "pending": 0.0,
    "last_distribution": None
}

HIVE_REWARD_RATE = 0.10

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def join_hive(
    username: str,
    opt_in_data_sharing: bool = True
) -> Dict[str, Any]:
    """Join MetaHive and start earning rewards"""
    
    if username in _HIVE_MEMBERS:
        return {"ok": False, "error": "already_member"}
    
    # Get user's OutcomeScore
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(
                f"https://aigentsy-ame-runtime.onrender.com/score/outcome?username={username}"
            )
            outcome_score = r.json().get("score", 50)
        except Exception:
            outcome_score = 50
    
    member = {
        "username": username,
        "joined_at": now_iso(),
        "opt_in_data_sharing": opt_in_data_sharing,
        "contribution_credits": 0,
        "outcome_score": outcome_score,
        "total_earned": 0.0,
        "last_payout": None,
        "status": "ACTIVE"
    }
    
    _HIVE_MEMBERS[username] = member
    
    # Give joining bonus
    member["contribution_credits"] += 10
    
    return {"ok": True, "member": member, "joining_bonus": 10}


def leave_hive(username: str) -> Dict[str, Any]:
    """Leave MetaHive (forfeit pending rewards)"""
    
    member = _HIVE_MEMBERS.get(username)
    if not member:
        return {"ok": False, "error": "not_member"}
    
    member["status"] = "LEFT"
    member["left_at"] = now_iso()
    
    return {"ok": True, "message": "Left hive, pending rewards forfeited"}


def record_contribution(
    username: str,
    contribution_type: str,
    value: float = 1.0
) -> Dict[str, Any]:
    """Record member contribution and award credits"""
    
    member = _HIVE_MEMBERS.get(username)
    if not member:
        return {"ok": False, "error": "not_hive_member"}
    
    if member["status"] != "ACTIVE":
        return {"ok": False, "error": "member_not_active"}
    
    # Calculate credits based on contribution type
    credits = 0
    if contribution_type == "pattern_contribution":
        credits = 5
    elif contribution_type == "pattern_usage_success":
        credits = 3
    elif contribution_type == "hive_query":
        credits = 1
    elif contribution_type == "pattern_verification":
        credits = 2
    elif contribution_type == "revenue_generated":
        credits = int(value * 0.5)
    
    member["contribution_credits"] += credits
    
    return {
        "ok": True,
        "credits_earned": credits,
        "total_credits": member["contribution_credits"]
    }


async def record_hive_revenue(
    source: str,
    amount_usd: float,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Record revenue generated through hive patterns"""
    
    # Add to treasury
    _HIVE_TREASURY["total_revenue"] += amount_usd
    _HIVE_TREASURY["pending"] += amount_usd
    
    return {
        "ok": True,
        "amount": amount_usd,
        "treasury": {
            "total": round(_HIVE_TREASURY["total_revenue"], 2),
            "pending": round(_HIVE_TREASURY["pending"], 2)
        }
    }


async def distribute_hive_rewards() -> Dict[str, Any]:
    """Distribute pending rewards to active members"""
    
    pending = _HIVE_TREASURY["pending"]
    if pending <= 0:
        return {"ok": True, "message": "no_pending_rewards"}
    
    # Get active members
    active_members = {
        username: member
        for username, member in _HIVE_MEMBERS.items()
        if member["status"] == "ACTIVE"
    }
    
    if not active_members:
        return {"ok": True, "message": "no_active_members"}
    
    # Calculate total weight (contribution credits * outcome score multiplier)
    total_weight = 0.0
    for member in active_members.values():
        credits = member["contribution_credits"]
        outcome_multiplier = 1.0 + (member["outcome_score"] / 200.0)
        weight = credits * outcome_multiplier
        total_weight += weight
    
    if total_weight == 0:
        return {"ok": True, "message": "no_eligible_members"}
    
    # Distribute rewards
    distributions = []
    async with httpx.AsyncClient(timeout=10) as client:
        for username, member in active_members.items():
            credits = member["contribution_credits"]
            outcome_multiplier = 1.0 + (member["outcome_score"] / 200.0)
            weight = credits * outcome_multiplier
            
            share = weight / total_weight
            amount = round(pending * share, 2)
            
            if amount < 0.01:
                continue
            
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                    json={
                        "username": username,
                        "amount": amount,
                        "basis": "hive_rewards",
                        "ref": "monthly_distribution"
                    }
                )
                
                member["total_earned"] += amount
                member["last_payout"] = now_iso()
                
                distributions.append({
                    "username": username,
                    "amount": amount,
                    "credits": credits,
                    "outcome_score": member["outcome_score"],
                    "weight": round(weight, 2)
                })
            except Exception as e:
                print(f"Failed to pay {username}: {e}")
    
    # Update treasury
    total_distributed = sum(d["amount"] for d in distributions)
    _HIVE_TREASURY["distributed"] += total_distributed
    _HIVE_TREASURY["pending"] -= total_distributed
    _HIVE_TREASURY["last_distribution"] = now_iso()
    
    return {
        "ok": True,
        "total_distributed": round(total_distributed, 2),
        "distributions": distributions,
        "members_paid": len(distributions)
    }


def get_hive_member(username: str) -> Dict[str, Any]:
    """Get member details"""
    member = _HIVE_MEMBERS.get(username)
    if not member:
        return {"ok": False, "error": "not_member"}
    return {"ok": True, "member": member}


def list_hive_members(status: str = None) -> Dict[str, Any]:
    """List hive members"""
    members = list(_HIVE_MEMBERS.values())
    
    if status:
        members = [m for m in members if m["status"] == status.upper()]
    
    members.sort(key=lambda m: m["contribution_credits"], reverse=True)
    
    return {"ok": True, "members": members, "count": len(members)}


def get_hive_treasury_stats() -> Dict[str, Any]:
    """Get hive treasury statistics"""
    
    active_count = len([m for m in _HIVE_MEMBERS.values() if m["status"] == "ACTIVE"])
    total_credits = sum(m["contribution_credits"] for m in _HIVE_MEMBERS.values() if m["status"] == "ACTIVE")
    
    return {
        "ok": True,
        "treasury": {
            "total_revenue": round(_HIVE_TREASURY["total_revenue"], 2),
            "distributed": round(_HIVE_TREASURY["distributed"], 2),
            "pending": round(_HIVE_TREASURY["pending"], 2),
            "last_distribution": _HIVE_TREASURY["last_distribution"]
        },
        "members": {
            "active": active_count,
            "total": len(_HIVE_MEMBERS),
            "total_contribution_credits": total_credits
        }
    }


def get_member_projected_earnings(username: str) -> Dict[str, Any]:
    """Calculate member's share of pending rewards"""
    
    member = _HIVE_MEMBERS.get(username)
    if not member:
        return {"ok": False, "error": "not_member"}
    
    if member["status"] != "ACTIVE":
        return {"ok": False, "error": "member_not_active"}
    
    # Calculate weight
    active_members = [m for m in _HIVE_MEMBERS.values() if m["status"] == "ACTIVE"]
    
    total_weight = 0.0
    for m in active_members:
        credits = m["contribution_credits"]
        outcome_multiplier = 1.0 + (m["outcome_score"] / 200.0)
        weight = credits * outcome_multiplier
        total_weight += weight
    
    if total_weight == 0:
        return {"ok": True, "projected": 0.0}
    
    credits = member["contribution_credits"]
    outcome_multiplier = 1.0 + (member["outcome_score"] / 200.0)
    weight = credits * outcome_multiplier
    
    share = weight / total_weight
    projected = round(_HIVE_TREASURY["pending"] * share, 2)
    
    return {
        "ok": True,
        "projected_earnings": projected,
        "your_weight": round(weight, 2),
        "total_weight": round(total_weight, 2),
        "share_pct": round(share * 100, 2)
    }
