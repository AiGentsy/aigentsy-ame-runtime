# slo_engine.py
"""
AiGentsy SLO Engine - Feature #9

Dashboard wrapper and analytics for the SLO tiers system.
Provides user-friendly APIs, performance tracking, and reporting.

Integrates with:
- slo_tiers.py (existing SLO tier system)
- outcome_oracle.py (SLO outcome tracking)
- analytics_engine.py (SLO performance metrics)
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
import json

# Import existing SLO tiers module
try:
    from slo_tiers import (
        SLO_TIERS,
        get_slo_tier,
        calculate_slo_requirements,
        create_slo_contract,
        stake_slo_bond,
        check_slo_breach,
        enforce_slo_breach,
        process_slo_delivery,
        get_agent_slo_stats
    )
    HAS_SLO_TIERS = True
except ImportError:
    HAS_SLO_TIERS = False
    # Fallback tier definitions if module not available
    SLO_TIERS = {
        "premium": {
            "name": "Premium SLA",
            "delivery_days": 3,
            "bond_percentage": 0.30,
            "protection_fee": 0.05,
            "early_bonus_percentage": 0.15,
            "price_multiplier": 1.3,
            "description": "Guaranteed 3-day delivery with highest priority",
            "badge": "⚡"
        },
        "standard": {
            "name": "Standard SLA",
            "delivery_days": 7,
            "bond_percentage": 0.20,
            "protection_fee": 0.03,
            "early_bonus_percentage": 0.10,
            "price_multiplier": 1.0,
            "description": "Standard 7-day delivery with quality guarantee",
            "badge": "✓"
        },
        "economy": {
            "name": "Economy SLA",
            "delivery_days": 14,
            "bond_percentage": 0.10,
            "protection_fee": 0.01,
            "early_bonus_percentage": 0.05,
            "price_multiplier": 0.8,
            "description": "Budget-friendly 14-day delivery",
            "badge": "○"
        },
        "express": {
            "name": "Express SLA",
            "delivery_days": 1,
            "bond_percentage": 0.40,
            "protection_fee": 0.08,
            "early_bonus_percentage": 0.20,
            "price_multiplier": 1.8,
            "description": "Rush 24-hour delivery with maximum commitment",
            "badge": "🚀"
        }
    }

# In-memory contract storage (use JSONBin in production)
SLO_CONTRACTS_DB = {}
SLO_PERFORMANCE_DB = {}


def get_all_slo_tiers() -> Dict[str, Any]:
    """
    Get all available SLO tiers with detailed pricing information.
    
    Returns:
        All SLO tiers with pricing, bonds, and bonuses
    """
    tiers = {}
    
    for tier_key, tier_config in SLO_TIERS.items():
        # Example calculations with $1,000 base
        example_base = 1000.0
        example_adjusted = example_base * tier_config["price_multiplier"]
        example_bond = example_base * tier_config["bond_percentage"]
        example_protection = example_base * tier_config["protection_fee"]
        example_bonus = example_base * tier_config["early_bonus_percentage"]
        
        tiers[tier_key] = {
            "tier_id": tier_key,
            "name": tier_config["name"],
            "badge": tier_config["badge"],
            "description": tier_config["description"],
            "delivery_days": tier_config["delivery_days"],
            "delivery_hours": tier_config["delivery_days"] * 24,
            "pricing": {
                "price_multiplier": tier_config["price_multiplier"],
                "price_multiplier_display": f"{tier_config['price_multiplier']}x",
                "premium_percent": (tier_config["price_multiplier"] - 1.0) * 100 if tier_config["price_multiplier"] >= 1.0 else 0,
                "discount_percent": (1.0 - tier_config["price_multiplier"]) * 100 if tier_config["price_multiplier"] < 1.0 else 0
            },
            "bonds_and_fees": {
                "agent_bond_percent": tier_config["bond_percentage"] * 100,
                "buyer_protection_fee_percent": tier_config["protection_fee"] * 100,
                "early_bonus_percent": tier_config["early_bonus_percentage"] * 100
            },
            "example_calculation": {
                "base_price": example_base,
                "adjusted_price": round(example_adjusted, 2),
                "agent_bond_required": round(example_bond, 2),
                "buyer_protection_fee": round(example_protection, 2),
                "total_buyer_payment": round(example_adjusted + example_protection, 2),
                "early_delivery_bonus": round(example_bonus, 2)
            }
        }
    
    return {
        "tiers": tiers,
        "total_tiers": len(tiers),
        "fastest_tier": "express",
        "economy_tier": "economy",
        "recommended_tier": "standard"
    }


def calculate_slo_pricing_detailed(
    base_price: float,
    tier: str
) -> Dict[str, Any]:
    """
    Calculate detailed SLO pricing breakdown.
    
    Args:
        base_price: Base outcome price
        tier: SLO tier (express/premium/standard/economy)
    
    Returns:
        Complete pricing breakdown
    """
    if tier not in SLO_TIERS:
        return {
            "ok": False,
            "error": f"Invalid SLO tier: {tier}",
            "valid_tiers": list(SLO_TIERS.keys())
        }
    
    tier_config = SLO_TIERS[tier]
    
    # Calculate all amounts
    adjusted_price = base_price * tier_config["price_multiplier"]
    agent_bond = base_price * tier_config["bond_percentage"]
    protection_fee = base_price * tier_config["protection_fee"]
    early_bonus = base_price * tier_config["early_bonus_percentage"]
    total_buyer_payment = adjusted_price + protection_fee
    
    # Calculate savings/premium vs standard
    standard_price = base_price * SLO_TIERS["standard"]["price_multiplier"]
    price_difference = adjusted_price - standard_price
    
    return {
        "ok": True,
        "tier": tier,
        "tier_name": tier_config["name"],
        "badge": tier_config["badge"],
        "base_price": round(base_price, 2),
        "adjusted_price": round(adjusted_price, 2),
        "price_difference_vs_standard": round(price_difference, 2),
        "agent_bond_required": round(agent_bond, 2),
        "buyer_protection_fee": round(protection_fee, 2),
        "total_buyer_payment": round(total_buyer_payment, 2),
        "early_delivery_bonus": round(early_bonus, 2),
        "delivery_deadline_days": tier_config["delivery_days"],
        "delivery_deadline_hours": tier_config["delivery_days"] * 24,
        "breakdown": {
            "what_buyer_pays": {
                "outcome_price": round(adjusted_price, 2),
                "protection_insurance": round(protection_fee, 2),
                "total": round(total_buyer_payment, 2)
            },
            "what_agent_stakes": {
                "bond_amount": round(agent_bond, 2),
                "bond_returned_if_on_time": True,
                "bond_slashed_if_late": True
            },
            "what_agent_earns": {
                "base_payment": round(adjusted_price, 2),
                "potential_bonus": round(early_bonus, 2),
                "maximum_payout": round(adjusted_price + early_bonus, 2),
                "bond_returned": round(agent_bond, 2)
            }
        }
    }


def compare_slo_tiers(base_price: float) -> Dict[str, Any]:
    """
    Compare all SLO tiers for a given base price.
    
    Args:
        base_price: Base outcome price
    
    Returns:
        Comparison table of all tiers
    """
    comparisons = []
    
    for tier_key in ["express", "premium", "standard", "economy"]:
        pricing = calculate_slo_pricing_detailed(base_price, tier_key)
        
        if pricing["ok"]:
            comparisons.append({
                "tier": tier_key,
                "name": pricing["tier_name"],
                "badge": pricing["badge"],
                "delivery_days": pricing["delivery_deadline_days"],
                "total_buyer_payment": pricing["total_buyer_payment"],
                "agent_bond_required": pricing["agent_bond_required"],
                "early_bonus_potential": pricing["early_delivery_bonus"],
                "max_agent_payout": pricing["breakdown"]["what_agent_earns"]["maximum_payout"]
            })
    
    # Sort by delivery speed (fastest first)
    comparisons.sort(key=lambda x: x["delivery_days"])
    
    return {
        "base_price": base_price,
        "tiers": comparisons,
        "fastest": comparisons[0],
        "slowest": comparisons[-1],
        "recommended": next((t for t in comparisons if t["tier"] == "standard"), comparisons[1])
    }


def track_slo_performance_event(
    contract_id: str,
    event_type: str,
    event_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Track SLO performance event for analytics.
    
    Args:
        contract_id: SLO contract ID
        event_type: Type of event (created/staked/delivered/breached)
        event_data: Event details
    
    Returns:
        Tracking confirmation
    """
    event_id = f"slo_event_{contract_id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    event = {
        "event_id": event_id,
        "contract_id": contract_id,
        "event_type": event_type,
        "event_data": event_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Store in performance DB
    if contract_id not in SLO_PERFORMANCE_DB:
        SLO_PERFORMANCE_DB[contract_id] = []
    
    SLO_PERFORMANCE_DB[contract_id].append(event)
    
    return {
        "success": True,
        "event_id": event_id,
        "event_type": event_type,
        "tracked_at": event["timestamp"]
    }


def get_slo_contract_status(contract_id: str) -> Dict[str, Any]:
    """
    Get comprehensive status of an SLO contract.
    
    Args:
        contract_id: Contract ID
    
    Returns:
        Contract status with timeline and metrics
    """
    if contract_id not in SLO_CONTRACTS_DB:
        return {
            "ok": False,
            "error": "Contract not found",
            "contract_id": contract_id
        }
    
    contract = SLO_CONTRACTS_DB[contract_id]
    
    # Calculate time metrics
    created_at = datetime.fromisoformat(contract["created_at"].replace("Z", "+00:00"))
    deadline = datetime.fromisoformat(contract["delivery_deadline"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    
    total_hours = (deadline - created_at).total_seconds() / 3600
    elapsed_hours = (now - created_at).total_seconds() / 3600
    remaining_hours = (deadline - now).total_seconds() / 3600
    
    progress_percent = min((elapsed_hours / total_hours) * 100, 100)
    
    status = {
        "ok": True,
        "contract_id": contract_id,
        "tier": contract["tier"],
        "tier_name": SLO_TIERS[contract["tier"]]["name"],
        "badge": SLO_TIERS[contract["tier"]]["badge"],
        "status": contract["status"],
        "timeline": {
            "created_at": contract["created_at"],
            "deadline": contract["delivery_deadline"],
            "current_time": now.isoformat(),
            "total_hours": round(total_hours, 1),
            "elapsed_hours": round(elapsed_hours, 1),
            "remaining_hours": round(max(remaining_hours, 0), 1),
            "progress_percent": round(progress_percent, 1),
            "is_overdue": remaining_hours < 0
        },
        "financials": {
            "job_value": contract["job_value"],
            "adjusted_price": contract["adjusted_price"],
            "agent_bond": contract["agent_bond"],
            "bond_staked": contract["bond_staked"],
            "protection_fee": contract["protection_fee"],
            "early_bonus_potential": contract["early_bonus"]
        },
        "parties": {
            "agent": contract["agent"],
            "buyer": contract["buyer"]
        }
    }
    
    # Add delivery info if delivered
    if contract.get("delivered_at"):
        delivered_at = datetime.fromisoformat(contract["delivered_at"].replace("Z", "+00:00"))
        delivery_hours = (delivered_at - created_at).total_seconds() / 3600
        
        status["delivery"] = {
            "delivered_at": contract["delivered_at"],
            "delivery_hours": round(delivery_hours, 1),
            "on_time": contract.get("on_time", False),
            "early_bonus_awarded": contract.get("early_bonus_awarded", False),
            "bonus_amount": contract.get("bonus_amount", 0)
        }
    
    # Add breach info if breached
    if contract.get("breach_detected"):
        status["breach"] = {
            "breached": True,
            "detected_at": contract.get("breach_detected_at"),
            "enforcement_actions": contract.get("enforcement_actions", [])
        }
    
    return status


def get_agent_slo_dashboard(agent_username: str) -> Dict[str, Any]:
    """
    Get agent's SLO performance dashboard.
    
    Args:
        agent_username: Agent username
    
    Returns:
        Dashboard with performance metrics and active contracts
    """
    # Get agent's contracts
    agent_contracts = [
        c for c in SLO_CONTRACTS_DB.values()
        if c.get("agent") == agent_username
    ]
    
    # Calculate metrics
    total_contracts = len(agent_contracts)
    active_contracts = [c for c in agent_contracts if c["status"] == "ACTIVE"]
    completed_contracts = [c for c in agent_contracts if c["status"] == "COMPLETED"]
    breached_contracts = [c for c in agent_contracts if c["status"] == "BREACHED"]
    
    # On-time delivery rate
    on_time_count = len([c for c in completed_contracts if c.get("on_time")])
    on_time_rate = (on_time_count / len(completed_contracts)) * 100 if completed_contracts else 0
    
    # Total bonuses earned
    total_bonuses = sum(c.get("bonus_amount", 0) for c in completed_contracts)
    
    # Total bonds at risk
    total_bonds_at_risk = sum(c.get("bond_stake_amount", 0) for c in active_contracts)
    
    # Tier breakdown
    tier_stats = {}
    for tier in SLO_TIERS.keys():
        tier_contracts = [c for c in agent_contracts if c["tier"] == tier]
        tier_completed = [c for c in tier_contracts if c["status"] == "COMPLETED"]
        tier_on_time = [c for c in tier_completed if c.get("on_time")]
        
        tier_stats[tier] = {
            "total": len(tier_contracts),
            "active": len([c for c in tier_contracts if c["status"] == "ACTIVE"]),
            "completed": len(tier_completed),
            "on_time": len(tier_on_time),
            "on_time_rate": (len(tier_on_time) / len(tier_completed)) * 100 if tier_completed else 0
        }
    
    return {
        "agent_username": agent_username,
        "summary": {
            "total_contracts": total_contracts,
            "active_contracts": len(active_contracts),
            "completed_contracts": len(completed_contracts),
            "breached_contracts": len(breached_contracts),
            "on_time_rate": round(on_time_rate, 1),
            "total_bonuses_earned": round(total_bonuses, 2),
            "total_bonds_at_risk": round(total_bonds_at_risk, 2)
        },
        "tier_performance": tier_stats,
        "active_contracts": [
            {
                "contract_id": c["id"],
                "tier": c["tier"],
                "deadline": c["delivery_deadline"],
                "bond_staked": c["bond_stake_amount"],
                "potential_bonus": c["early_bonus"]
            }
            for c in active_contracts
        ],
        "recent_completions": [
            {
                "contract_id": c["id"],
                "tier": c["tier"],
                "delivered_at": c.get("delivered_at"),
                "on_time": c.get("on_time"),
                "bonus_earned": c.get("bonus_amount", 0)
            }
            for c in sorted(completed_contracts, key=lambda x: x.get("delivered_at", ""), reverse=True)[:5]
        ]
    }


def get_buyer_slo_dashboard(buyer_username: str) -> Dict[str, Any]:
    """
    Get buyer's SLO contracts dashboard.
    
    Args:
        buyer_username: Buyer username
    
    Returns:
        Dashboard with active contracts and protections
    """
    # Get buyer's contracts
    buyer_contracts = [
        c for c in SLO_CONTRACTS_DB.values()
        if c.get("buyer") == buyer_username
    ]
    
    active_contracts = [c for c in buyer_contracts if c["status"] == "ACTIVE"]
    completed_contracts = [c for c in buyer_contracts if c["status"] == "COMPLETED"]
    breached_contracts = [c for c in buyer_contracts if c["status"] == "BREACHED"]
    
    # Calculate total protection
    total_protection_fees_paid = sum(c["protection_fee"] for c in buyer_contracts)
    total_refunds_received = sum(
        c.get("enforcement_actions", [{}])[-1].get("buyer_refunded", 0)
        for c in breached_contracts
    )
    
    return {
        "buyer_username": buyer_username,
        "summary": {
            "total_contracts": len(buyer_contracts),
            "active_contracts": len(active_contracts),
            "completed_on_time": len([c for c in completed_contracts if c.get("on_time")]),
            "breached_contracts": len(breached_contracts),
            "total_protection_paid": round(total_protection_fees_paid, 2),
            "total_refunds_received": round(total_refunds_received, 2),
            "net_protection_cost": round(total_protection_fees_paid - total_refunds_received, 2)
        },
        "active_contracts": [
            {
                "contract_id": c["id"],
                "agent": c["agent"],
                "tier": c["tier"],
                "deadline": c["delivery_deadline"],
                "hours_remaining": max(
                    (datetime.fromisoformat(c["delivery_deadline"].replace("Z", "+00:00")) - 
                     datetime.now(timezone.utc)).total_seconds() / 3600,
                    0
                ),
                "protection_fee_paid": c["protection_fee"]
            }
            for c in active_contracts
        ]
    }


def recommend_slo_tier(
    urgency: str,
    budget_flexible: bool,
    quality_priority: bool
) -> Dict[str, Any]:
    """
    Recommend SLO tier based on buyer preferences.
    
    Args:
        urgency: low/medium/high/critical
        budget_flexible: Can pay premium?
        quality_priority: Prioritize quality over speed?
    
    Returns:
        Recommended tier with reasoning
    """
    recommendations = {
        "critical": "express" if budget_flexible else "premium",
        "high": "premium",
        "medium": "standard",
        "low": "economy"
    }
    
    recommended_tier = recommendations.get(urgency, "standard")
    
    # Override if quality priority
    if quality_priority and not budget_flexible:
        recommended_tier = "standard"
    
    tier_config = SLO_TIERS[recommended_tier]
    
    return {
        "recommended_tier": recommended_tier,
        "tier_name": tier_config["name"],
        "badge": tier_config["badge"],
        "delivery_days": tier_config["delivery_days"],
        "reasoning": {
            "urgency_level": urgency,
            "budget_flexible": budget_flexible,
            "quality_priority": quality_priority,
            "why_recommended": _get_recommendation_reason(
                recommended_tier,
                urgency,
                budget_flexible,
                quality_priority
            )
        },
        "tier_details": tier_config
    }


def _get_recommendation_reason(
    tier: str,
    urgency: str,
    budget_flexible: bool,
    quality_priority: bool
) -> str:
    """Generate recommendation reasoning."""
    reasons = []
    
    if tier == "express":
        reasons.append("Critical urgency requires fastest delivery")
        if budget_flexible:
            reasons.append("Budget allows for premium 24-hour service")
    elif tier == "premium":
        reasons.append("High urgency with quality guarantee")
        reasons.append("3-day delivery balances speed and reliability")
    elif tier == "standard":
        reasons.append("Best value with proven quality")
        if quality_priority:
            reasons.append("7 days ensures thorough, quality work")
    else:  # economy
        reasons.append("Budget-conscious option for flexible timelines")
    
    return " • ".join(reasons)


# Example usage
if __name__ == "__main__":
    # Get all tiers
    tiers = get_all_slo_tiers()
    print(f"Available SLO tiers: {len(tiers['tiers'])}")
    
    # Calculate pricing
    pricing = calculate_slo_pricing_detailed(1000.0, "express")
    print(f"\nExpress tier for $1,000 outcome:")
    print(f"Buyer pays: ${pricing['total_buyer_payment']}")
    print(f"Agent bonds: ${pricing['agent_bond_required']}")
    print(f"Early bonus: ${pricing['early_delivery_bonus']}")
    
    # Compare tiers
    comparison = compare_slo_tiers(1000.0)
    print(f"\nTier comparison:")
    for tier in comparison['tiers']:
        print(f"  {tier['badge']} {tier['name']}: {tier['delivery_days']} days, ${tier['total_buyer_payment']}")
    
    # Recommend tier
    recommendation = recommend_slo_tier("high", True, True)
    print(f"\nRecommended: {recommendation['tier_name']}")
    print(f"Reason: {recommendation['reasoning']['why_recommended']}")
