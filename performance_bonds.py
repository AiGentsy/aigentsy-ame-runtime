"""
AiGentsy Performance Bonds + SLA Bonus
Stake-based trust system with auto-rewards
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional

def _now():
    return datetime.now(timezone.utc).isoformat()

def _hours_between(start_iso: str, end_iso: str) -> float:
    """Calculate hours between two ISO timestamps"""
    try:
        start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        return (end - start).total_seconds() / 3600
    except:
        return 0


# Bond tiers based on order value
BOND_TIERS = {
    "micro": {"max_value": 50, "bond_amount": 1.0},      # < $50
    "small": {"max_value": 200, "bond_amount": 3.0},     # $50-200
    "medium": {"max_value": 500, "bond_amount": 5.0},    # $200-500
    "large": {"max_value": 1000, "bond_amount": 10.0},   # $500-1000
    "enterprise": {"max_value": 999999, "bond_amount": 20.0}  # > $1000
}

# SLA bonus rates
SLA_BONUS = {
    "early": 3.0,      # Delivered in <50% of SLA
    "on_time": 1.5,    # Delivered in 50-80% of SLA
    "standard": 0.0    # Delivered in 80-100% of SLA
}

# Dispute slash rates
DISPUTE_SLASH = {
    "minor": 0.25,      # 25% slash - minor quality issues
    "moderate": 0.50,   # 50% slash - significant issues
    "major": 1.0        # 100% slash - complete failure
}


def calculate_bond_amount(order_value: float) -> Dict[str, Any]:
    """Determine required bond based on order value"""
    for tier_name, tier in BOND_TIERS.items():
        if order_value <= tier["max_value"]:
            return {
                "tier": tier_name,
                "amount": tier["bond_amount"],
                "order_value": order_value
            }
    
    # Fallback to enterprise
    return {
        "tier": "enterprise",
        "amount": BOND_TIERS["enterprise"]["bond_amount"],
        "order_value": order_value
    }


async def stake_bond(user: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stake performance bond when accepting intent
    """
    order_value = float(intent.get("price_usd", 0) or intent.get("budget", 0))
    bond_info = calculate_bond_amount(order_value)
    bond_amount = bond_info["amount"]
    
    # Check if agent has enough AIGx
    current_aigx = float(user.get("ownership", {}).get("aigx", 0))
    
    if current_aigx < bond_amount:
        return {
            "ok": False,
            "error": "insufficient_aigx",
            "required": bond_amount,
            "available": current_aigx
        }
    
    # Deduct bond from balance
    user["ownership"]["aigx"] = current_aigx - bond_amount
    
    # Add bond entry to ledger
    bond_entry = {
        "ts": _now(),
        "amount": -bond_amount,
        "currency": "AIGx",
        "basis": "performance_bond",
        "ref": intent.get("id"),
        "status": "staked",
        "tier": bond_info["tier"]
    }
    
    user.setdefault("ownership", {}).setdefault("ledger", []).append(bond_entry)
    
    # Track bond in intent
    intent["bond"] = {
        "amount": bond_amount,
        "tier": bond_info["tier"],
        "agent": user.get("consent", {}).get("username") or user.get("username"),
        "staked_at": _now(),
        "status": "active"
    }
    
    return {
        "ok": True,
        "bond_amount": bond_amount,
        "tier": bond_info["tier"],
        "remaining_aigx": user["ownership"]["aigx"]
    }


async def return_bond(user: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return full bond on successful delivery (no disputes)
    """
    bond = intent.get("bond", {})
    bond_amount = float(bond.get("amount", 0))
    
    if bond_amount == 0:
        return {"ok": False, "error": "no_bond_found"}
    
    # Return bond
    user["ownership"]["aigx"] = float(user["ownership"].get("aigx", 0)) + bond_amount
    
    # Add return entry
    return_entry = {
        "ts": _now(),
        "amount": bond_amount,
        "currency": "AIGx",
        "basis": "bond_return",
        "ref": intent.get("id"),
        "status": "returned"
    }
    
    user["ownership"]["ledger"].append(return_entry)
    
    # Update bond status
    bond["status"] = "returned"
    bond["returned_at"] = _now()
    
    return {
        "ok": True,
        "returned": bond_amount,
        "new_balance": user["ownership"]["aigx"]
    }


async def calculate_sla_bonus(intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate SLA bonus based on delivery speed
    """
    accepted_at = intent.get("accepted_at")
    delivered_at = intent.get("delivered_at")
    sla_hours = float(intent.get("delivery_hours", 48))
    
    if not (accepted_at and delivered_at):
        return {"ok": False, "error": "missing_timestamps"}
    
    actual_hours = _hours_between(accepted_at, delivered_at)
    completion_rate = actual_hours / sla_hours
    
    # Determine bonus tier
    if completion_rate <= 0.5:
        bonus_amount = SLA_BONUS["early"]
        tier = "early"
    elif completion_rate <= 0.8:
        bonus_amount = SLA_BONUS["on_time"]
        tier = "on_time"
    else:
        bonus_amount = 0.0
        tier = "standard"
    
    return {
        "ok": True,
        "bonus_amount": bonus_amount,
        "tier": tier,
        "sla_hours": sla_hours,
        "actual_hours": round(actual_hours, 1),
        "completion_rate": round(completion_rate, 2)
    }


async def award_sla_bonus(user: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Award SLA bonus for early/on-time delivery
    """
    bonus_calc = await calculate_sla_bonus(intent)
    
    if not bonus_calc["ok"] or bonus_calc["bonus_amount"] == 0:
        return {"ok": True, "bonus": 0, "tier": "standard"}
    
    bonus_amount = bonus_calc["bonus_amount"]
    
    # Credit bonus
    user["ownership"]["aigx"] = float(user["ownership"].get("aigx", 0)) + bonus_amount
    
    # Add bonus entry
    bonus_entry = {
        "ts": _now(),
        "amount": bonus_amount,
        "currency": "AIGx",
        "basis": "sla_bonus",
        "ref": intent.get("id"),
        "tier": bonus_calc["tier"],
        "actual_hours": bonus_calc["actual_hours"],
        "sla_hours": bonus_calc["sla_hours"]
    }
    
    user["ownership"]["ledger"].append(bonus_entry)
    
    # Track in intent
    intent["sla_bonus"] = {
        "amount": bonus_amount,
        "tier": bonus_calc["tier"],
        "awarded_at": _now()
    }
    
    return {
        "ok": True,
        "bonus": bonus_amount,
        "tier": bonus_calc["tier"],
        "new_balance": user["ownership"]["aigx"]
    }


async def slash_bond(
    user: Dict[str, Any],
    intent: Dict[str, Any],
    severity: str = "moderate"
) -> Dict[str, Any]:
    """
    Slash bond on dispute loss
    """
    bond = intent.get("bond", {})
    bond_amount = float(bond.get("amount", 0))
    
    if bond_amount == 0:
        return {"ok": False, "error": "no_bond_to_slash"}
    
    # Calculate slash amount
    slash_rate = DISPUTE_SLASH.get(severity, DISPUTE_SLASH["moderate"])
    slash_amount = bond_amount * slash_rate
    return_amount = bond_amount - slash_amount
    
    # Return unslashed portion
    if return_amount > 0:
        user["ownership"]["aigx"] = float(user["ownership"].get("aigx", 0)) + return_amount
        
        user["ownership"]["ledger"].append({
            "ts": _now(),
            "amount": return_amount,
            "currency": "AIGx",
            "basis": "bond_return_partial",
            "ref": intent.get("id")
        })
    
    # Record slash
    user["ownership"]["ledger"].append({
        "ts": _now(),
        "amount": -slash_amount,
        "currency": "AIGx",
        "basis": "bond_slash",
        "ref": intent.get("id"),
        "severity": severity,
        "slash_rate": slash_rate
    })
    
    # Update bond status
    bond["status"] = "slashed"
    bond["slashed_at"] = _now()
    bond["slash_amount"] = slash_amount
    bond["return_amount"] = return_amount
    bond["severity"] = severity
    
    return {
        "ok": True,
        "slashed": slash_amount,
        "returned": return_amount,
        "severity": severity,
        "new_balance": user["ownership"]["aigx"]
    }
