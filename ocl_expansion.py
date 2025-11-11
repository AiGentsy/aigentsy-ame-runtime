"""
AiGentsy OCL Auto-Expansion Loop
Autonomous credit expansion from verified outcomes + R³ autopilot integration
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

def _now():
    return datetime.now(timezone.utc).isoformat()


# Expansion rules
EXPANSION_RULES = {
    "base_rate": 0.10,  # 10% of completed job value added to OCL
    "reputation_multiplier": {
        "bronze": 0.5,    # 50% of base rate (5% of job value)
        "silver": 1.0,    # 100% of base rate (10% of job value)
        "gold": 1.5,      # 150% of base rate (15% of job value)
        "platinum": 2.0,  # 200% of base rate (20% of job value)
        "diamond": 2.5    # 250% of base rate (25% of job value)
    },
    "on_time_bonus": 0.05,      # +5% if delivered on-time
    "quality_bonus": 0.03,      # +3% if high quality (no disputes)
    "max_single_expansion": 500, # Cap single expansion at $500
    "cooling_period_hours": 24   # Min hours between expansions
}

# Reputation tiers (from dark_pool.py)
REPUTATION_TIERS = {
    "bronze": {"min_score": 0, "max_score": 49},
    "silver": {"min_score": 50, "max_score": 69},
    "gold": {"min_score": 70, "max_score": 84},
    "platinum": {"min_score": 85, "max_score": 94},
    "diamond": {"min_score": 95, "max_score": 100}
}


def get_reputation_tier_name(outcome_score: int) -> str:
    """Get reputation tier name from outcome score"""
    for tier_name, tier in REPUTATION_TIERS.items():
        if tier["min_score"] <= outcome_score <= tier["max_score"]:
            return tier_name
    return "bronze"


def calculate_ocl_expansion(
    job_value: float,
    outcome_score: int,
    on_time: bool = True,
    disputed: bool = False
) -> Dict[str, Any]:
    """
    Calculate OCL expansion amount based on job completion
    """
    base_rate = EXPANSION_RULES["base_rate"]
    
    # Get reputation tier
    tier = get_reputation_tier_name(outcome_score)
    tier_multiplier = EXPANSION_RULES["reputation_multiplier"][tier]
    
    # Base expansion
    base_expansion = job_value * base_rate * tier_multiplier
    
    # Bonuses
    on_time_bonus = 0.0
    if on_time:
        on_time_bonus = job_value * EXPANSION_RULES["on_time_bonus"]
    
    quality_bonus = 0.0
    if not disputed:
        quality_bonus = job_value * EXPANSION_RULES["quality_bonus"]
    
    # Total expansion (with cap)
    total_expansion = base_expansion + on_time_bonus + quality_bonus
    capped_expansion = min(total_expansion, EXPANSION_RULES["max_single_expansion"])
    
    return {
        "ok": True,
        "job_value": round(job_value, 2),
        "base_expansion": round(base_expansion, 2),
        "on_time_bonus": round(on_time_bonus, 2),
        "quality_bonus": round(quality_bonus, 2),
        "total_expansion": round(total_expansion, 2),
        "capped_expansion": round(capped_expansion, 2),
        "was_capped": total_expansion > EXPANSION_RULES["max_single_expansion"],
        "tier": tier,
        "tier_multiplier": tier_multiplier
    }


def check_expansion_eligibility(
    agent_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check if agent is eligible for OCL expansion (cooling period check)
    """
    ocl_data = agent_user.get("ocl", {})
    last_expansion = ocl_data.get("last_expansion_at")
    
    if not last_expansion:
        return {"eligible": True, "reason": "no_previous_expansion"}
    
    from datetime import datetime, timedelta
    last_expansion_dt = datetime.fromisoformat(last_expansion.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    hours_since = (now - last_expansion_dt).total_seconds() / 3600
    
    cooling_hours = EXPANSION_RULES["cooling_period_hours"]
    
    if hours_since < cooling_hours:
        return {
            "eligible": False,
            "reason": "cooling_period_active",
            "hours_remaining": round(cooling_hours - hours_since, 1)
        }
    
    return {"eligible": True, "reason": "cooling_period_elapsed"}


def expand_ocl_limit(
    agent_user: Dict[str, Any],
    expansion_amount: float,
    job_id: str = None,
    reason: str = "job_completion"
) -> Dict[str, Any]:
    """
    Expand agent's OCL limit
    """
    # Check eligibility
    eligibility = check_expansion_eligibility(agent_user)
    
    if not eligibility["eligible"]:
        return {
            "ok": False,
            "error": "not_eligible",
            **eligibility
        }
    
    # Get current OCL
    ocl_data = agent_user.setdefault("ocl", {
        "limit": 1000.0,
        "used": 0.0,
        "available": 1000.0,
        "expansion_history": []
    })
    
    old_limit = ocl_data["limit"]
    new_limit = old_limit + expansion_amount
    
    # Update limit
    ocl_data["limit"] = new_limit
    ocl_data["available"] = new_limit - ocl_data["used"]
    ocl_data["last_expansion_at"] = _now()
    
    # Record expansion
    expansion_record = {
        "amount": expansion_amount,
        "job_id": job_id,
        "reason": reason,
        "old_limit": old_limit,
        "new_limit": new_limit,
        "expanded_at": _now()
    }
    
    ocl_data.setdefault("expansion_history", []).append(expansion_record)
    
    # Add ledger entry
    agent_user.setdefault("ownership", {}).setdefault("ledger", []).append({
        "ts": _now(),
        "amount": 0,  # No money transfer, just limit increase
        "currency": "USD",
        "basis": "ocl_expansion",
        "expansion_amount": expansion_amount,
        "new_limit": new_limit,
        "job_id": job_id
    })
    
    return {
        "ok": True,
        "expansion_amount": round(expansion_amount, 2),
        "old_limit": round(old_limit, 2),
        "new_limit": round(new_limit, 2),
        "available_credit": round(ocl_data["available"], 2),
        "expanded_at": _now()
    }


def process_job_completion_expansion(
    agent_user: Dict[str, Any],
    job_value: float,
    job_id: str,
    on_time: bool = True,
    disputed: bool = False
) -> Dict[str, Any]:
    """
    Process OCL expansion after job completion
    """
    outcome_score = int(agent_user.get("outcomeScore", 0))
    
    # Calculate expansion
    calc = calculate_ocl_expansion(job_value, outcome_score, on_time, disputed)
    expansion_amount = calc["capped_expansion"]
    
    if expansion_amount <= 0:
        return {
            "ok": False,
            "error": "no_expansion_calculated",
            "calculation": calc
        }
    
    # Expand OCL
    result = expand_ocl_limit(agent_user, expansion_amount, job_id, "job_completion")
    
    if result["ok"]:
        result["calculation_details"] = calc
    
    return result


def trigger_r3_reallocation(
    agent_user: Dict[str, Any],
    new_available_credit: float
) -> Dict[str, Any]:
    """
    Trigger R³ autopilot to reallocate budget based on new credit
    """
    r3_strategy = agent_user.get("r3_autopilot", {}).get("strategy")
    
    if not r3_strategy:
        return {
            "ok": False,
            "error": "no_r3_strategy",
            "message": "Agent has no R³ autopilot strategy configured"
        }
    
    if r3_strategy.get("status") != "active":
        return {
            "ok": False,
            "error": "r3_not_active",
            "status": r3_strategy.get("status")
        }
    
    # Calculate new budget allocation based on increased credit
    old_budget = r3_strategy.get("monthly_budget", 0)
    
    # Suggest increasing R³ budget by 20% of new credit
    suggested_increase = new_available_credit * 0.20
    new_suggested_budget = old_budget + suggested_increase
    
    # Mark strategy for rebalancing
    r3_strategy["pending_rebalance"] = True
    r3_strategy["rebalance_reason"] = "ocl_expansion"
    r3_strategy["suggested_budget_increase"] = suggested_increase
    r3_strategy["new_suggested_budget"] = new_suggested_budget
    
    return {
        "ok": True,
        "r3_triggered": True,
        "old_budget": round(old_budget, 2),
        "suggested_budget_increase": round(suggested_increase, 2),
        "new_suggested_budget": round(new_suggested_budget, 2),
        "message": "R³ autopilot marked for rebalancing with increased budget"
    }


def get_expansion_stats(
    agent_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get agent's OCL expansion statistics
    """
    ocl_data = agent_user.get("ocl", {})
    expansion_history = ocl_data.get("expansion_history", [])
    
    if not expansion_history:
        return {
            "total_expansions": 0,
            "total_expanded": 0.0,
            "avg_expansion": 0.0,
            "largest_expansion": 0.0,
            "current_limit": ocl_data.get("limit", 1000.0)
        }
    
    total_expanded = sum([e.get("amount", 0) for e in expansion_history])
    avg_expansion = total_expanded / len(expansion_history)
    largest_expansion = max([e.get("amount", 0) for e in expansion_history])
    
    return {
        "total_expansions": len(expansion_history),
        "total_expanded": round(total_expanded, 2),
        "avg_expansion": round(avg_expansion, 2),
        "largest_expansion": round(largest_expansion, 2),
        "current_limit": round(ocl_data.get("limit", 1000.0), 2),
        "original_limit": 1000.0,
        "expansion_growth": round((ocl_data.get("limit", 1000.0) / 1000.0 - 1) * 100, 1)
    }


def simulate_expansion_potential(
    outcome_score: int,
    projected_job_value: float,
    on_time: bool = True
) -> Dict[str, Any]:
    """
    Simulate potential OCL expansion for a future job
    """
    calc = calculate_ocl_expansion(projected_job_value, outcome_score, on_time, False)
    
    tier = get_reputation_tier_name(outcome_score)
    
    return {
        "ok": True,
        "projected_job_value": round(projected_job_value, 2),
        "current_outcome_score": outcome_score,
        "current_tier": tier,
        "potential_expansion": round(calc["capped_expansion"], 2),
        "breakdown": calc,
        "message": f"Completing this ${projected_job_value} job would expand your OCL by ${calc['capped_expansion']}"
    }


def get_next_tier_incentive(
    current_score: int,
    job_value: float
) -> Dict[str, Any]:
    """
    Show agent how much more they'd get at next reputation tier
    """
    current_tier = get_reputation_tier_name(current_score)
    
    # Find next tier
    tier_order = ["bronze", "silver", "gold", "platinum", "diamond"]
    current_idx = tier_order.index(current_tier)
    
    if current_idx >= len(tier_order) - 1:
        return {
            "ok": False,
            "message": "Already at highest tier (Diamond)"
        }
    
    next_tier = tier_order[current_idx + 1]
    next_tier_min_score = REPUTATION_TIERS[next_tier]["min_score"]
    
    # Calculate expansion at both tiers
    current_expansion = calculate_ocl_expansion(job_value, current_score, True, False)
    next_tier_expansion = calculate_ocl_expansion(job_value, next_tier_min_score, True, False)
    
    additional_expansion = next_tier_expansion["capped_expansion"] - current_expansion["capped_expansion"]
    
    return {
        "ok": True,
        "current_tier": current_tier,
        "current_score": current_score,
        "next_tier": next_tier,
        "next_tier_min_score": next_tier_min_score,
        "points_needed": next_tier_min_score - current_score,
        "current_expansion": round(current_expansion["capped_expansion"], 2),
        "next_tier_expansion": round(next_tier_expansion["capped_expansion"], 2),
        "additional_benefit": round(additional_expansion, 2),
        "message": f"Reach {next_tier} tier ({next_tier_min_score} points) to earn ${additional_expansion} more per job"
    }
