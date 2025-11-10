"""
AiGentsy SLO Contract Tiers
Auto-enforced service levels with tiered bonds, fees, and bonuses
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

def _now():
    return datetime.now(timezone.utc).isoformat()

def _parse_iso(ts_iso: str) -> datetime:
    try:
        return datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
    except:
        return datetime.now(timezone.utc)


# SLO tier definitions
SLO_TIERS = {
    "premium": {
        "name": "Premium SLA",
        "delivery_days": 3,
        "bond_percentage": 0.30,        # 30% of job value
        "protection_fee": 0.05,          # 5% buyer insurance
        "early_bonus_percentage": 0.15,  # 15% bonus for early delivery
        "price_multiplier": 1.3,         # 30% premium pricing
        "description": "Guaranteed 3-day delivery with highest priority",
        "badge": "⚡"
    },
    "standard": {
        "name": "Standard SLA",
        "delivery_days": 7,
        "bond_percentage": 0.20,        # 20% of job value
        "protection_fee": 0.03,          # 3% buyer insurance
        "early_bonus_percentage": 0.10,  # 10% bonus for early delivery
        "price_multiplier": 1.0,         # Standard pricing
        "description": "Standard 7-day delivery with quality guarantee",
        "badge": "✓"
    },
    "economy": {
        "name": "Economy SLA",
        "delivery_days": 14,
        "bond_percentage": 0.10,        # 10% of job value
        "protection_fee": 0.01,          # 1% buyer insurance
        "early_bonus_percentage": 0.05,  # 5% bonus for early delivery
        "price_multiplier": 0.8,         # 20% discount
        "description": "Budget-friendly 14-day delivery",
        "badge": "○"
    },
    "express": {
        "name": "Express SLA",
        "delivery_days": 1,
        "bond_percentage": 0.40,        # 40% of job value
        "protection_fee": 0.08,          # 8% buyer insurance
        "early_bonus_percentage": 0.20,  # 20% bonus for same-day
        "price_multiplier": 1.8,         # 80% premium
        "description": "Rush 24-hour delivery with maximum commitment",
        "badge": "🚀"
    }
}


def get_slo_tier(tier_name: str) -> Dict[str, Any]:
    """Get SLO tier configuration"""
    if tier_name not in SLO_TIERS:
        return {
            "ok": False,
            "error": "invalid_tier",
            "valid_tiers": list(SLO_TIERS.keys())
        }
    
    return {
        "ok": True,
        "tier": tier_name,
        **SLO_TIERS[tier_name]
    }


def calculate_slo_requirements(
    job_value: float,
    tier_name: str = "standard"
) -> Dict[str, Any]:
    """Calculate bond, fees, and bonuses for a job under specific SLO"""
    if tier_name not in SLO_TIERS:
        return {"ok": False, "error": "invalid_tier"}
    
    tier = SLO_TIERS[tier_name]
    
    # Calculate amounts
    bond_amount = job_value * tier["bond_percentage"]
    protection_fee = job_value * tier["protection_fee"]
    early_bonus = job_value * tier["early_bonus_percentage"]
    adjusted_price = job_value * tier["price_multiplier"]
    
    # Total buyer pays (includes protection fee)
    total_buyer_payment = adjusted_price + protection_fee
    
    return {
        "ok": True,
        "tier": tier_name,
        "base_job_value": round(job_value, 2),
        "adjusted_price": round(adjusted_price, 2),
        "agent_bond_required": round(bond_amount, 2),
        "buyer_protection_fee": round(protection_fee, 2),
        "total_buyer_payment": round(total_buyer_payment, 2),
        "early_delivery_bonus": round(early_bonus, 2),
        "delivery_deadline_days": tier["delivery_days"],
        "tier_badge": tier["badge"]
    }


def create_slo_contract(
    intent: Dict[str, Any],
    agent_username: str,
    tier_name: str = "standard"
) -> Dict[str, Any]:
    """Create SLO contract when agent accepts intent"""
    from uuid import uuid4
    
    if tier_name not in SLO_TIERS:
        return {"ok": False, "error": "invalid_tier"}
    
    tier = SLO_TIERS[tier_name]
    job_value = float(intent.get("budget", 0))
    
    # Calculate requirements
    requirements = calculate_slo_requirements(job_value, tier_name)
    
    if not requirements["ok"]:
        return requirements
    
    # Create contract
    contract_id = f"slo_{uuid4().hex[:12]}"
    
    deadline = datetime.now(timezone.utc) + timedelta(days=tier["delivery_days"])
    
    contract = {
        "id": contract_id,
        "intent_id": intent.get("id"),
        "agent": agent_username,
        "buyer": intent.get("buyer"),
        "tier": tier_name,
        "tier_config": tier,
        "status": "ACTIVE",
        "created_at": _now(),
        "delivery_deadline": deadline.isoformat(),
        "job_value": requirements["base_job_value"],
        "adjusted_price": requirements["adjusted_price"],
        "agent_bond": requirements["agent_bond_required"],
        "protection_fee": requirements["buyer_protection_fee"],
        "total_payment": requirements["total_buyer_payment"],
        "early_bonus": requirements["early_delivery_bonus"],
        "bond_staked": False,
        "bond_stake_amount": 0.0,
        "delivered_at": None,
        "breach_detected": False,
        "enforcement_actions": []
    }
    
    return {
        "ok": True,
        "contract": contract
    }


def stake_slo_bond(
    contract: Dict[str, Any],
    agent_user: Dict[str, Any]
) -> Dict[str, Any]:
    """Agent stakes required bond for SLO contract"""
    if contract["bond_staked"]:
        return {
            "ok": False,
            "error": "bond_already_staked"
        }
    
    required_bond = contract["agent_bond"]
    agent_balance = float(agent_user.get("ownership", {}).get("aigx", 0))
    
    # Check if agent has sufficient balance
    if agent_balance < required_bond:
        return {
            "ok": False,
            "error": "insufficient_balance",
            "required": required_bond,
            "available": agent_balance
        }
    
    # Stake bond
    agent_user["ownership"]["aigx"] = agent_balance - required_bond
    
    # Add ledger entry
    agent_user.setdefault("ownership", {}).setdefault("ledger", []).append({
        "ts": _now(),
        "amount": -required_bond,
        "currency": "AIGx",
        "basis": "slo_bond_stake",
        "contract_id": contract["id"],
        "tier": contract["tier"]
    })
    
    # Update contract
    contract["bond_staked"] = True
    contract["bond_stake_amount"] = required_bond
    contract["bond_staked_at"] = _now()
    contract["enforcement_actions"].append({
        "action": "BOND_STAKED",
        "amount": required_bond,
        "at": _now()
    })
    
    return {
        "ok": True,
        "contract_id": contract["id"],
        "bond_staked": required_bond,
        "remaining_balance": round(agent_balance - required_bond, 2)
    }


def check_slo_breach(
    contract: Dict[str, Any]
) -> Dict[str, Any]:
    """Check if SLO has been breached"""
    if contract["status"] != "ACTIVE":
        return {"ok": False, "error": "contract_not_active"}
    
    # Check if delivered
    if contract.get("delivered_at"):
        return {"ok": True, "breached": False, "status": "delivered"}
    
    # Check deadline
    deadline = _parse_iso(contract["delivery_deadline"])
    now = datetime.now(timezone.utc)
    
    if now > deadline:
        return {
            "ok": True,
            "breached": True,
            "deadline": contract["delivery_deadline"],
            "current_time": _now(),
            "hours_overdue": round((now - deadline).total_seconds() / 3600, 1)
        }
    
    # Not breached yet
    hours_remaining = (deadline - now).total_seconds() / 3600
    
    return {
        "ok": True,
        "breached": False,
        "deadline": contract["delivery_deadline"],
        "hours_remaining": round(hours_remaining, 1)
    }


def enforce_slo_breach(
    contract: Dict[str, Any],
    agent_user: Dict[str, Any],
    buyer_user: Dict[str, Any]
) -> Dict[str, Any]:
    """Auto-enforce SLO breach: slash bond, refund protection fee"""
    breach_check = check_slo_breach(contract)
    
    if not breach_check.get("breached"):
        return {
            "ok": False,
            "error": "no_breach_detected",
            "contract_id": contract["id"]
        }
    
    if contract.get("breach_detected"):
        return {
            "ok": False,
            "error": "breach_already_enforced"
        }
    
    # Slash agent bond
    bond_amount = contract["bond_stake_amount"]
    
    # Bond goes to insurance pool (could also partial refund buyer)
    insurance_allocation = bond_amount * 0.7  # 70% to pool
    buyer_refund = bond_amount * 0.3          # 30% back to buyer
    
    # Refund buyer's protection fee
    protection_fee = contract["protection_fee"]
    
    # Credit buyer
    buyer_user.setdefault("ownership", {})
    buyer_balance = float(buyer_user["ownership"].get("aigx", 0))
    buyer_user["ownership"]["aigx"] = buyer_balance + buyer_refund + protection_fee
    
    buyer_user["ownership"].setdefault("ledger", []).append({
        "ts": _now(),
        "amount": buyer_refund + protection_fee,
        "currency": "USD",
        "basis": "slo_breach_refund",
        "contract_id": contract["id"],
        "bond_refund": buyer_refund,
        "protection_fee_refund": protection_fee
    })
    
    # Update agent ledger (bond already deducted, just record slash)
    agent_user.setdefault("ownership", {}).setdefault("ledger", []).append({
        "ts": _now(),
        "amount": -bond_amount,
        "currency": "AIGx",
        "basis": "slo_bond_slash",
        "contract_id": contract["id"],
        "reason": "delivery_deadline_breach"
    })
    
    # Update contract
    contract["status"] = "BREACHED"
    contract["breach_detected"] = True
    contract["breach_detected_at"] = _now()
    contract["enforcement_actions"].append({
        "action": "AUTO_ENFORCEMENT",
        "bond_slashed": bond_amount,
        "insurance_allocation": insurance_allocation,
        "buyer_refund": buyer_refund + protection_fee,
        "at": _now()
    })
    
    return {
        "ok": True,
        "contract_id": contract["id"],
        "enforcement": "AUTO_EXECUTED",
        "bond_slashed": round(bond_amount, 2),
        "buyer_refunded": round(buyer_refund + protection_fee, 2),
        "insurance_pool_credit": round(insurance_allocation, 2)
    }


def process_slo_delivery(
    contract: Dict[str, Any],
    agent_user: Dict[str, Any],
    delivery_timestamp: str = None
) -> Dict[str, Any]:
    """Process delivery under SLO contract"""
    if contract["status"] != "ACTIVE":
        return {"ok": False, "error": "contract_not_active"}
    
    if not delivery_timestamp:
        delivery_timestamp = _now()
    
    delivered_at = _parse_iso(delivery_timestamp)
    deadline = _parse_iso(contract["delivery_deadline"])
    
    # Check if on-time
    on_time = delivered_at <= deadline
    
    # Check if early (deserves bonus)
    created_at = _parse_iso(contract["created_at"])
    total_slo_hours = (deadline - created_at).total_seconds() / 3600
    actual_hours = (delivered_at - created_at).total_seconds() / 3600
    early_percentage = 1 - (actual_hours / total_slo_hours)
    
    # Early bonus if delivered in first 50% of time window
    earns_bonus = early_percentage > 0.5 and on_time
    
    # Return bond to agent
    bond_amount = contract["bond_stake_amount"]
    agent_balance = float(agent_user.get("ownership", {}).get("aigx", 0))
    agent_user["ownership"]["aigx"] = agent_balance + bond_amount
    
    agent_user["ownership"].setdefault("ledger", []).append({
        "ts": _now(),
        "amount": bond_amount,
        "currency": "AIGx",
        "basis": "slo_bond_return",
        "contract_id": contract["id"]
    })
    
    # Award early bonus if earned
    bonus_awarded = 0.0
    if earns_bonus:
        bonus_awarded = contract["early_bonus"]
        agent_user["ownership"]["aigx"] += bonus_awarded
        
        agent_user["ownership"]["ledger"].append({
            "ts": _now(),
            "amount": bonus_awarded,
            "currency": "USD",
            "basis": "sla_bonus",
            "contract_id": contract["id"],
            "early_percentage": round(early_percentage, 2)
        })
    
    # Update contract
    contract["status"] = "COMPLETED"
    contract["delivered_at"] = delivery_timestamp
    contract["on_time"] = on_time
    contract["early_bonus_awarded"] = earns_bonus
    contract["bonus_amount"] = bonus_awarded
    contract["enforcement_actions"].append({
        "action": "DELIVERY_PROCESSED",
        "on_time": on_time,
        "bonus_awarded": bonus_awarded,
        "bond_returned": bond_amount,
        "at": _now()
    })
    
    return {
        "ok": True,
        "contract_id": contract["id"],
        "on_time": on_time,
        "bond_returned": round(bond_amount, 2),
        "early_bonus_awarded": earns_bonus,
        "bonus_amount": round(bonus_awarded, 2),
        "total_agent_payout": round(contract["adjusted_price"] + bond_amount + bonus_awarded, 2)
    }


def get_agent_slo_stats(
    agent_user: Dict[str, Any]
) -> Dict[str, Any]:
    """Get agent's SLO performance statistics"""
    ledger = agent_user.get("ownership", {}).get("ledger", [])
    
    total_slo_contracts = 0
    on_time_deliveries = 0
    breaches = 0
    total_bonds_staked = 0.0
    total_bonds_slashed = 0.0
    total_bonuses_earned = 0.0
    
    tier_stats = {tier: {"count": 0, "on_time": 0} for tier in SLO_TIERS.keys()}
    
    for entry in ledger:
        basis = entry.get("basis", "")
        
        if basis == "slo_bond_stake":
            total_slo_contracts += 1
            total_bonds_staked += abs(float(entry.get("amount", 0)))
            tier = entry.get("tier", "standard")
            tier_stats[tier]["count"] += 1
        
        if basis == "slo_bond_return":
            on_time_deliveries += 1
            # Track tier performance (would need contract reference)
        
        if basis == "slo_bond_slash":
            breaches += 1
            total_bonds_slashed += abs(float(entry.get("amount", 0)))
        
        if basis == "sla_bonus":
            total_bonuses_earned += float(entry.get("amount", 0))
    
    on_time_rate = (on_time_deliveries / total_slo_contracts) if total_slo_contracts > 0 else 0
    breach_rate = (breaches / total_slo_contracts) if total_slo_contracts > 0 else 0
    
    return {
        "total_slo_contracts": total_slo_contracts,
        "on_time_deliveries": on_time_deliveries,
        "breaches": breaches,
        "on_time_rate": round(on_time_rate, 2),
        "breach_rate": round(breach_rate, 3),
        "total_bonds_staked": round(total_bonds_staked, 2),
        "total_bonds_slashed": round(total_bonds_slashed, 2),
        "total_bonuses_earned": round(total_bonuses_earned, 2),
        "tier_performance": tier_stats
    }
