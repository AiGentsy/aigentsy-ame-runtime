"""
AiGentsy Reputation-Indexed Knobs
Dynamic adjustment of OCL, factoring, pricing, and ranking based on reputation

Now integrated with Brain Overlay OCS (Outcome Credit Score) for unified reputation.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Integration with brain overlay OCS
try:
    from integration_hooks import IntegrationHooks
    from brain_overlay.ocs import OCSEngine
    _hooks = IntegrationHooks("reputation_knobs")
    _ocs = OCSEngine()
except ImportError:
    _hooks = None
    _ocs = None


def _now():
    return datetime.now(timezone.utc).isoformat()


# Reputation tiers (consistent across platform)
REPUTATION_TIERS = {
    "bronze": {"min_score": 0, "max_score": 49, "badge": "🥉"},
    "silver": {"min_score": 50, "max_score": 69, "badge": "🥈"},
    "gold": {"min_score": 70, "max_score": 84, "badge": "🥇"},
    "platinum": {"min_score": 85, "max_score": 94, "badge": "💎"},
    "diamond": {"min_score": 95, "max_score": 100, "badge": "💠"}
}

# OCL limit adjustments by tier
OCL_LIMITS = {
    "bronze": {"base_limit": 500, "max_limit": 2000},
    "silver": {"base_limit": 1000, "max_limit": 5000},
    "gold": {"base_limit": 2000, "max_limit": 10000},
    "platinum": {"base_limit": 5000, "max_limit": 25000},
    "diamond": {"base_limit": 10000, "max_limit": 50000}
}

# Factoring advance percentages by tier
FACTORING_RATES = {
    "bronze": {"min_advance": 0.50, "max_advance": 0.70},
    "silver": {"min_advance": 0.65, "max_advance": 0.80},
    "gold": {"min_advance": 0.75, "max_advance": 0.85},
    "platinum": {"min_advance": 0.80, "max_advance": 0.90},
    "diamond": {"min_advance": 0.85, "max_advance": 0.95}
}

# ARM pricing multipliers by tier
ARM_MULTIPLIERS = {
    "bronze": {"floor": 0.80, "ceiling": 1.00, "recommended": 0.90},
    "silver": {"floor": 0.90, "ceiling": 1.10, "recommended": 1.00},
    "gold": {"floor": 1.00, "ceiling": 1.30, "recommended": 1.15},
    "platinum": {"floor": 1.20, "ceiling": 1.50, "recommended": 1.35},
    "diamond": {"floor": 1.40, "ceiling": 1.80, "recommended": 1.60}
}

# Dark pool rank weights by tier
DARK_POOL_WEIGHTS = {
    "bronze": {"base_weight": 1.0},
    "silver": {"base_weight": 1.2},
    "gold": {"base_weight": 1.5},
    "platinum": {"base_weight": 2.0},
    "diamond": {"base_weight": 3.0}
}


def get_reputation_tier(outcome_score: int) -> str:
    """Get reputation tier name from outcome score"""
    for tier_name, tier in REPUTATION_TIERS.items():
        if tier["min_score"] <= outcome_score <= tier["max_score"]:
            return tier_name
    return "bronze"


def calculate_reputation_metrics(
    agent_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate comprehensive reputation metrics from ledger.
    Now synced with brain overlay OCS for unified reputation.
    """
    entity_id = agent_user.get("username") or agent_user.get("id")
    ledger = agent_user.get("ownership", {}).get("ledger", [])

    # Count outcomes
    completed_jobs = len([e for e in ledger if e.get("basis") == "revenue"])
    on_time_deliveries = len([e for e in ledger if e.get("basis") == "sla_bonus"])
    disputes = len([e for e in ledger if e.get("basis") == "bond_slash"])

    # Count PoO verifications
    poo_count = len([e for e in ledger if e.get("basis") == "outcome_verified"])

    # Calculate rates
    on_time_rate = (on_time_deliveries / completed_jobs) if completed_jobs > 0 else 0
    dispute_rate = (disputes / completed_jobs) if completed_jobs > 0 else 0
    quality_score = max(0, 1.0 - dispute_rate)  # Quality = inverse of disputes

    # Try to get OCS from brain overlay (unified score)
    outcome_score = int(agent_user.get("outcomeScore", 0))
    ocs_synced = False
    if _ocs and entity_id:
        try:
            ocs_data = _ocs.get_ocs(entity_id)
            if ocs_data.get("ocs", 0) > 0:
                outcome_score = ocs_data.get("ocs")
                ocs_synced = True
        except Exception:
            pass

    tier = get_reputation_tier(outcome_score)

    return {
        "outcome_score": outcome_score,
        "tier": tier,
        "tier_badge": REPUTATION_TIERS[tier]["badge"],
        "completed_jobs": completed_jobs,
        "poo_count": poo_count,
        "on_time_rate": round(on_time_rate, 3),
        "dispute_rate": round(dispute_rate, 3),
        "quality_score": round(quality_score, 3),
        "ocs_synced": ocs_synced
    }


def calculate_ocl_limit(
    reputation_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate OCL limit based on reputation
    """
    tier = reputation_metrics["tier"]
    tier_config = OCL_LIMITS[tier]
    
    base_limit = tier_config["base_limit"]
    max_limit = tier_config["max_limit"]
    
    # Adjust based on performance
    on_time_rate = reputation_metrics["on_time_rate"]
    quality_score = reputation_metrics["quality_score"]
    
    # Performance multiplier (0.8 to 1.2)
    performance_multiplier = 0.8 + (on_time_rate * 0.2) + (quality_score * 0.2)
    
    # Calculate limit
    calculated_limit = base_limit * performance_multiplier
    final_limit = min(calculated_limit, max_limit)
    
    return {
        "tier": tier,
        "base_limit": base_limit,
        "max_limit": max_limit,
        "performance_multiplier": round(performance_multiplier, 2),
        "calculated_limit": round(calculated_limit, 2),
        "final_limit": round(final_limit, 2),
        "at_cap": calculated_limit >= max_limit
    }


def calculate_factoring_rate(
    reputation_metrics: Dict[str, Any],
    job_value: float
) -> Dict[str, Any]:
    """
    Calculate factoring advance percentage based on reputation
    """
    tier = reputation_metrics["tier"]
    tier_config = FACTORING_RATES[tier]
    
    min_advance = tier_config["min_advance"]
    max_advance = tier_config["max_advance"]
    
    # Adjust based on performance
    on_time_rate = reputation_metrics["on_time_rate"]
    quality_score = reputation_metrics["quality_score"]
    
    # Performance adjustment within tier range
    performance_factor = (on_time_rate + quality_score) / 2
    
    advance_rate = min_advance + (performance_factor * (max_advance - min_advance))
    
    # Calculate amounts
    advance_amount = job_value * advance_rate
    holdback = job_value - advance_amount
    
    return {
        "tier": tier,
        "min_advance_rate": min_advance,
        "max_advance_rate": max_advance,
        "calculated_advance_rate": round(advance_rate, 3),
        "job_value": round(job_value, 2),
        "advance_amount": round(advance_amount, 2),
        "holdback_amount": round(holdback, 2),
        "performance_factor": round(performance_factor, 3)
    }


def calculate_arm_pricing(
    reputation_metrics: Dict[str, Any],
    base_price: float
) -> Dict[str, Any]:
    """
    Calculate ARM pricing bounds based on reputation
    """
    tier = reputation_metrics["tier"]
    tier_config = ARM_MULTIPLIERS[tier]
    
    floor_multiplier = tier_config["floor"]
    ceiling_multiplier = tier_config["ceiling"]
    recommended_multiplier = tier_config["recommended"]
    
    # Adjust recommended based on recent performance
    on_time_rate = reputation_metrics["on_time_rate"]
    
    # Bonus for exceptional performance
    if on_time_rate >= 0.95:
        recommended_multiplier = min(ceiling_multiplier, recommended_multiplier * 1.1)
    elif on_time_rate < 0.7:
        recommended_multiplier = max(floor_multiplier, recommended_multiplier * 0.9)
    
    # Calculate prices
    floor_price = base_price * floor_multiplier
    ceiling_price = base_price * ceiling_multiplier
    recommended_price = base_price * recommended_multiplier
    
    return {
        "tier": tier,
        "base_price": round(base_price, 2),
        "floor_multiplier": floor_multiplier,
        "ceiling_multiplier": ceiling_multiplier,
        "recommended_multiplier": round(recommended_multiplier, 2),
        "floor_price": round(floor_price, 2),
        "ceiling_price": round(ceiling_price, 2),
        "recommended_price": round(recommended_price, 2),
        "pricing_range": round(ceiling_price - floor_price, 2)
    }


def calculate_dark_pool_rank(
    reputation_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate dark pool ranking score based on reputation
    """
    tier = reputation_metrics["tier"]
    tier_config = DARK_POOL_WEIGHTS[tier]
    
    base_weight = tier_config["base_weight"]
    
    # Component scores
    outcome_score = reputation_metrics["outcome_score"] / 100  # Normalize to 0-1
    on_time_rate = reputation_metrics["on_time_rate"]
    quality_score = reputation_metrics["quality_score"]
    poo_count = min(reputation_metrics["poo_count"] / 50, 1.0)  # Cap at 50 PoO
    
    # Weighted composite
    composite_score = (
        (outcome_score * 0.30) +
        (on_time_rate * 0.30) +
        (quality_score * 0.25) +
        (poo_count * 0.15)
    )
    
    # Apply tier weight
    final_rank = composite_score * base_weight * 1000  # Scale to 0-3000 range
    
    return {
        "tier": tier,
        "base_weight": base_weight,
        "component_scores": {
            "outcome_score": round(outcome_score, 3),
            "on_time_rate": round(on_time_rate, 3),
            "quality_score": round(quality_score, 3),
            "poo_count_factor": round(poo_count, 3)
        },
        "composite_score": round(composite_score, 3),
        "final_rank": round(final_rank, 1),
        "max_possible_rank": 3000
    }


def recompute_all_knobs(
    agent_user: Dict[str, Any],
    job_value: float = 1000.0,
    base_price: float = 500.0
) -> Dict[str, Any]:
    """
    Recompute all reputation-indexed knobs for an agent
    """
    # Calculate reputation metrics
    metrics = calculate_reputation_metrics(agent_user)
    
    # Calculate all knobs
    ocl = calculate_ocl_limit(metrics)
    factoring = calculate_factoring_rate(metrics, job_value)
    arm = calculate_arm_pricing(metrics, base_price)
    dark_pool = calculate_dark_pool_rank(metrics)
    
    return {
        "ok": True,
        "agent": agent_user.get("username"),
        "reputation_metrics": metrics,
        "ocl_limit": ocl,
        "factoring_rate": factoring,
        "arm_pricing": arm,
        "dark_pool_rank": dark_pool,
        "recomputed_at": _now()
    }


def apply_knob_updates(
    agent_user: Dict[str, Any],
    knob_calculations: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply calculated knob values to agent record
    """
    # Update OCL limit
    ocl_data = agent_user.setdefault("ocl", {})
    new_limit = knob_calculations["ocl_limit"]["final_limit"]
    old_limit = ocl_data.get("limit", 1000.0)
    
    ocl_data["limit"] = new_limit
    ocl_data["limit_updated_at"] = _now()
    ocl_data["limit_source"] = "reputation_indexed"
    
    # Update ARM pricing
    arm_data = agent_user.setdefault("arm_pricing", {})
    arm_calc = knob_calculations["arm_pricing"]
    
    arm_data["floor_multiplier"] = arm_calc["floor_multiplier"]
    arm_data["ceiling_multiplier"] = arm_calc["ceiling_multiplier"]
    arm_data["recommended_multiplier"] = arm_calc["recommended_multiplier"]
    arm_data["updated_at"] = _now()
    
    # Update dark pool rank
    agent_user["dark_pool_rank"] = knob_calculations["dark_pool_rank"]["final_rank"]
    agent_user["dark_pool_rank_updated_at"] = _now()
    
    # Record in ledger
    agent_user.setdefault("ownership", {}).setdefault("ledger", []).append({
        "ts": _now(),
        "amount": 0,
        "currency": "N/A",
        "basis": "reputation_knobs_update",
        "old_ocl_limit": old_limit,
        "new_ocl_limit": new_limit,
        "tier": knob_calculations["reputation_metrics"]["tier"]
    })
    
    return {
        "ok": True,
        "updates_applied": {
            "ocl_limit_changed": old_limit != new_limit,
            "old_ocl_limit": round(old_limit, 2),
            "new_ocl_limit": round(new_limit, 2),
            "arm_pricing_updated": True,
            "dark_pool_rank_updated": True
        },
        "applied_at": _now()
    }


def get_tier_comparison(
    current_score: int
) -> Dict[str, Any]:
    """
    Show agent their current tier vs all tiers
    """
    current_tier = get_reputation_tier(current_score)
    
    comparisons = []
    
    for tier_name, tier_config in REPUTATION_TIERS.items():
        ocl = OCL_LIMITS[tier_name]
        factoring = FACTORING_RATES[tier_name]
        arm = ARM_MULTIPLIERS[tier_name]
        
        is_current = tier_name == current_tier
        
        comparisons.append({
            "tier": tier_name,
            "badge": tier_config["badge"],
            "min_score": tier_config["min_score"],
            "max_score": tier_config["max_score"],
            "is_current_tier": is_current,
            "benefits": {
                "ocl_limit_range": f"${ocl['base_limit']}-${ocl['max_limit']}",
                "factoring_rate_range": f"{int(factoring['min_advance']*100)}-{int(factoring['max_advance']*100)}%",
                "pricing_multiplier_range": f"{arm['floor']}-{arm['ceiling']}x"
            }
        })
    
    return {
        "ok": True,
        "current_score": current_score,
        "current_tier": current_tier,
        "tier_comparison": comparisons
    }


def simulate_reputation_change(
    agent_user: Dict[str, Any],
    new_outcome_score: int
) -> Dict[str, Any]:
    """
    Simulate what would happen if reputation changed
    """
    # Current state
    current_metrics = calculate_reputation_metrics(agent_user)
    current_knobs = recompute_all_knobs(agent_user)
    
    # Simulate new score
    simulated_user = agent_user.copy()
    simulated_user["outcomeScore"] = new_outcome_score
    
    simulated_metrics = calculate_reputation_metrics(simulated_user)
    simulated_knobs = recompute_all_knobs(simulated_user)
    
    # Calculate deltas
    ocl_delta = simulated_knobs["ocl_limit"]["final_limit"] - current_knobs["ocl_limit"]["final_limit"]
    rank_delta = simulated_knobs["dark_pool_rank"]["final_rank"] - current_knobs["dark_pool_rank"]["final_rank"]
    
    return {
        "ok": True,
        "current_score": current_metrics["outcome_score"],
        "simulated_score": new_outcome_score,
        "tier_change": {
            "from": current_metrics["tier"],
            "to": simulated_metrics["tier"],
            "changed": current_metrics["tier"] != simulated_metrics["tier"]
        },
        "impact": {
            "ocl_limit_delta": round(ocl_delta, 2),
            "dark_pool_rank_delta": round(rank_delta, 1),
            "new_ocl_limit": round(simulated_knobs["ocl_limit"]["final_limit"], 2),
            "new_dark_pool_rank": round(simulated_knobs["dark_pool_rank"]["final_rank"], 1)
        }
    }
