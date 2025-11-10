"""
AiGentsy Agent Factoring Line
Immediate advances on accepted work with reputation-based rates
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional

def _now():
    return datetime.now(timezone.utc).isoformat()

def _days_ago(ts_iso: str) -> int:
    try:
        then = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - then).days
    except:
        return 9999


# Factoring rates based on agent reputation
FACTORING_TIERS = {
    "new": {
        "rate": 0.70,           # 70% advance
        "min_jobs": 0,
        "max_jobs": 4,
        "min_outcome_score": 0
    },
    "developing": {
        "rate": 0.75,           # 75% advance
        "min_jobs": 5,
        "max_jobs": 14,
        "min_outcome_score": 50
    },
    "established": {
        "rate": 0.80,           # 80% advance
        "min_jobs": 15,
        "max_jobs": 49,
        "min_outcome_score": 70
    },
    "elite": {
        "rate": 0.85,           # 85% advance
        "min_jobs": 50,
        "max_jobs": 99,
        "min_outcome_score": 85
    },
    "platinum": {
        "rate": 0.90,           # 90% advance
        "min_jobs": 100,
        "max_jobs": 999999,
        "min_outcome_score": 90
    }
}

# Factoring limits
MAX_OUTSTANDING_FACTORING = 5000.0  # Max $5k outstanding advances per agent
FACTORING_FEE_RATE = 0.02           # 2% factoring fee


def calculate_completed_jobs(user: Dict[str, Any]) -> int:
    """Count successfully completed jobs"""
    intents = user.get("intents", [])
    
    completed = [
        i for i in intents
        if i.get("status") in ["SETTLED", "DELIVERED"] and i.get("agent") == (user.get("consent", {}).get("username") or user.get("username"))
    ]
    
    return len(completed)


def calculate_factoring_tier(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine agent's factoring tier based on history
    """
    completed_jobs = calculate_completed_jobs(user)
    outcome_score = int(user.get("outcomeScore", 0))
    
    # Find matching tier
    for tier_name, tier in FACTORING_TIERS.items():
        if (completed_jobs >= tier["min_jobs"] and 
            completed_jobs <= tier["max_jobs"] and
            outcome_score >= tier["min_outcome_score"]):
            return {
                "tier": tier_name,
                "rate": tier["rate"],
                "completed_jobs": completed_jobs,
                "outcome_score": outcome_score
            }
    
    # Fallback to "new"
    return {
        "tier": "new",
        "rate": FACTORING_TIERS["new"]["rate"],
        "completed_jobs": completed_jobs,
        "outcome_score": outcome_score
    }


def calculate_outstanding_factoring(user: Dict[str, Any]) -> float:
    """
    Calculate total outstanding factoring advances
    """
    ledger = user.get("ownership", {}).get("ledger", [])
    
    # Sum all advances
    advances = sum([
        abs(float(e.get("amount", 0)))
        for e in ledger
        if e.get("basis") == "factoring_advance" and not e.get("settled")
    ])
    
    # Subtract repayments
    repayments = sum([
        float(e.get("amount", 0))
        for e in ledger
        if e.get("basis") == "factoring_repayment"
    ])
    
    outstanding = advances - repayments
    
    return round(max(0, outstanding), 2)


async def request_factoring_advance(
    user: Dict[str, Any],
    intent: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Request factoring advance when intent is awarded
    """
    order_value = float(intent.get("price_usd", 0))
    
    if order_value <= 0:
        return {
            "ok": False,
            "error": "invalid_order_value",
            "order_value": order_value
        }
    
    # Calculate factoring tier
    tier_info = calculate_factoring_tier(user)
    factoring_rate = tier_info["rate"]
    
    # Calculate advance amount
    advance_amount = round(order_value * factoring_rate, 2)
    holdback = round(order_value - advance_amount, 2)
    
    # Calculate factoring fee (charged on advance, not full amount)
    factoring_fee = round(advance_amount * FACTORING_FEE_RATE, 2)
    net_advance = round(advance_amount - factoring_fee, 2)
    
    # Check outstanding factoring limit
    outstanding = calculate_outstanding_factoring(user)
    
    if (outstanding + advance_amount) > MAX_OUTSTANDING_FACTORING:
        return {
            "ok": False,
            "error": "factoring_limit_exceeded",
            "outstanding": outstanding,
            "limit": MAX_OUTSTANDING_FACTORING,
            "requested": advance_amount
        }
    
    # Credit agent with net advance
    current_aigx = float(user.get("ownership", {}).get("aigx", 0))
    user["ownership"]["aigx"] = current_aigx + net_advance
    
    # Add factoring advance entry
    advance_entry = {
        "ts": _now(),
        "amount": net_advance,
        "currency": "USD",
        "basis": "factoring_advance",
        "ref": intent.get("id"),
        "order_value": order_value,
        "factoring_rate": factoring_rate,
        "factoring_tier": tier_info["tier"],
        "gross_advance": advance_amount,
        "factoring_fee": factoring_fee,
        "holdback": holdback,
        "settled": False
    }
    
    user["ownership"]["ledger"].append(advance_entry)
    
    # Add factoring fee entry
    fee_entry = {
        "ts": _now(),
        "amount": -factoring_fee,
        "currency": "USD",
        "basis": "factoring_fee",
        "ref": intent.get("id")
    }
    
    user["ownership"]["ledger"].append(fee_entry)
    
    # Track factoring in intent
    intent["factoring"] = {
        "advance_amount": advance_amount,
        "net_advance": net_advance,
        "factoring_fee": factoring_fee,
        "holdback": holdback,
        "factoring_rate": factoring_rate,
        "factoring_tier": tier_info["tier"],
        "advanced_at": _now(),
        "status": "advanced"
    }
    
    return {
        "ok": True,
        "advance_amount": advance_amount,
        "net_advance": net_advance,
        "factoring_fee": factoring_fee,
        "holdback": holdback,
        "factoring_rate": factoring_rate,
        "factoring_tier": tier_info["tier"],
        "new_balance": user["ownership"]["aigx"],
        "outstanding_factoring": outstanding + advance_amount
    }


async def settle_factoring(
    user: Dict[str, Any],
    intent: Dict[str, Any],
    payment_received: float
) -> Dict[str, Any]:
    """
    Settle factoring when buyer pays
    Deduct advance from payment, give agent the remainder
    """
    factoring = intent.get("factoring", {})
    
    if not factoring:
        return {
            "ok": False,
            "error": "no_factoring_on_intent"
        }
    
    advance_amount = float(factoring.get("advance_amount", 0))
    holdback = float(factoring.get("holdback", 0))
    
    # Payment should equal order value
    order_value = float(intent.get("price_usd", 0))
    
    if payment_received < order_value:
        return {
            "ok": False,
            "error": "partial_payment",
            "expected": order_value,
            "received": payment_received
        }
    
    # Agent gets the holdback amount
    agent_payout = holdback
    
    # Credit agent
    current_aigx = float(user.get("ownership", {}).get("aigx", 0))
    user["ownership"]["aigx"] = current_aigx + agent_payout
    
    # Add settlement entry
    settlement_entry = {
        "ts": _now(),
        "amount": agent_payout,
        "currency": "USD",
        "basis": "factoring_settlement",
        "ref": intent.get("id"),
        "payment_received": payment_received,
        "advance_repaid": advance_amount
    }
    
    user["ownership"]["ledger"].append(settlement_entry)
    
    # Mark advance as settled in ledger
    for entry in user["ownership"]["ledger"]:
        if (entry.get("basis") == "factoring_advance" and 
            entry.get("ref") == intent.get("id") and
            not entry.get("settled")):
            entry["settled"] = True
            entry["settled_at"] = _now()
    
    # Update factoring status in intent
    factoring["status"] = "settled"
    factoring["settled_at"] = _now()
    factoring["agent_payout"] = agent_payout
    
    return {
        "ok": True,
        "agent_payout": agent_payout,
        "advance_repaid": advance_amount,
        "new_balance": user["ownership"]["aigx"],
        "outstanding_factoring": calculate_outstanding_factoring(user)
    }


async def calculate_factoring_eligibility(user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if agent is eligible for factoring and show available capacity
    """
    tier_info = calculate_factoring_tier(user)
    outstanding = calculate_outstanding_factoring(user)
    available_capacity = MAX_OUTSTANDING_FACTORING - outstanding
    
    # Calculate next tier requirements
    completed_jobs = calculate_completed_jobs(user)
    outcome_score = int(user.get("outcomeScore", 0))
    
    next_tier = None
    for tier_name, tier in FACTORING_TIERS.items():
        if tier["rate"] > tier_info["rate"]:
            next_tier = {
                "name": tier_name,
                "rate": tier["rate"],
                "jobs_needed": max(0, tier["min_jobs"] - completed_jobs),
                "score_needed": max(0, tier["min_outcome_score"] - outcome_score)
            }
            break
    
    return {
        "ok": True,
        "eligible": available_capacity > 0,
        "current_tier": tier_info["tier"],
        "factoring_rate": tier_info["rate"],
        "completed_jobs": completed_jobs,
        "outcome_score": outcome_score,
        "outstanding_factoring": outstanding,
        "available_capacity": available_capacity,
        "max_factoring": MAX_OUTSTANDING_FACTORING,
        "next_tier": next_tier
    }
