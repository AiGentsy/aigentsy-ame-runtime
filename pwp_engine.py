# pwp_engine.py
"""
AiGentsy Pay-With-Performance (PWP) Engine - Feature #11

Standalone revenue-share financing system.
Buyers defer payment, agents get paid upfront from capital pool.

Features:
- Performance-based payment plans (pay only when outcome performs)
- Capital pool finances agent upfront
- Revenue share collection from buyer outcomes
- Risk-adjusted pricing based on outcome type
- Complementary to OCL (different use case - PWP = performance financing, OCL = working capital)

Example:
- Buyer orders $10k marketing campaign
- Chooses PWP: "Pay 20% of revenue until 1.5x recovered"
- Agent gets $10k upfront from capital pool
- AiGentsy collects 20% of buyer's revenue until $15k collected
- AiGentsy keeps $5k profit ($15k - $10k)
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal

# PWP plan definitions
PWP_PLANS = {
    "conservative": {
        "name": "Conservative Plan",
        "revenue_share_pct": 15.0,  # 15% of revenue
        "recovery_multiple": 1.3,    # Recover 1.3x
        "max_term_months": 24,       # 2 year max
        "min_outcome_size": 1000.0,  # $1k minimum
        "risk_tier": "low",
        "description": "15% revenue share until 1.3x recovered (24 month max)",
        "icon": "🛡️"
    },
    "balanced": {
        "name": "Balanced Plan",
        "revenue_share_pct": 20.0,  # 20% of revenue
        "recovery_multiple": 1.5,    # Recover 1.5x
        "max_term_months": 18,       # 18 month max
        "min_outcome_size": 5000.0,  # $5k minimum
        "risk_tier": "medium",
        "description": "20% revenue share until 1.5x recovered (18 month max)",
        "icon": "⚖️"
    },
    "aggressive": {
        "name": "Aggressive Plan",
        "revenue_share_pct": 25.0,  # 25% of revenue
        "recovery_multiple": 2.0,    # Recover 2x
        "max_term_months": 12,       # 12 month max
        "min_outcome_size": 10000.0, # $10k minimum
        "risk_tier": "high",
        "description": "25% revenue share until 2x recovered (12 month max)",
        "icon": "🚀"
    },
    "enterprise": {
        "name": "Enterprise Plan",
        "revenue_share_pct": 30.0,  # 30% of revenue
        "recovery_multiple": 2.5,    # Recover 2.5x
        "max_term_months": 24,       # 24 month max
        "min_outcome_size": 50000.0, # $50k minimum
        "risk_tier": "premium",
        "description": "30% revenue share until 2.5x recovered (24 month max)",
        "icon": "💎"
    }
}

# Outcome type risk multipliers
OUTCOME_RISK_TIERS = {
    "marketing_campaign": {
        "risk_level": "medium",
        "default_rate": 0.15,  # 15% default rate
        "multiplier_adjustment": 1.0
    },
    "software_development": {
        "risk_level": "low",
        "default_rate": 0.08,  # 8% default rate
        "multiplier_adjustment": 0.9
    },
    "content_creation": {
        "risk_level": "low",
        "default_rate": 0.10,  # 10% default rate
        "multiplier_adjustment": 0.95
    },
    "consulting": {
        "risk_level": "high",
        "default_rate": 0.25,  # 25% default rate
        "multiplier_adjustment": 1.2
    },
    "research": {
        "risk_level": "medium",
        "default_rate": 0.18,  # 18% default rate
        "multiplier_adjustment": 1.1
    }
}

# In-memory storage (use JSONBin in production)
PWP_CONTRACTS_DB = {}
PWP_PAYMENTS_DB = {}
CAPITAL_POOL = {
    "total_capital": 1000000.0,  # $1M pool
    "deployed": 0.0,
    "available": 1000000.0,
    "total_recovered": 0.0,
    "total_profit": 0.0
}

def create_pwp_contract(
    buyer_username: str,
    agent_username: str,
    outcome_id: str,
    outcome_price: float,
    pwp_plan: str,
    outcome_type: str = "marketing_campaign",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a Pay-With-Performance contract.
    
    Args:
        buyer_username: Buyer deferring payment
        agent_username: Agent receiving upfront payment
        outcome_id: Associated outcome
        outcome_price: Outcome price (agent's upfront payment)
        pwp_plan: PWP plan type
        outcome_type: Type of outcome (for risk assessment)
        metadata: Additional contract metadata
    
    Returns:
        Created PWP contract
    """
    if pwp_plan not in PWP_PLANS:
        raise ValueError(f"Invalid PWP plan: {pwp_plan}")
    
    plan = PWP_PLANS[pwp_plan]
    
    # Check minimum outcome size
    if outcome_price < plan["min_outcome_size"]:
        raise ValueError(f"Outcome too small. Minimum: ${plan['min_outcome_size']}")
    
    # Check capital availability
    if CAPITAL_POOL["available"] < outcome_price:
        raise ValueError(f"Insufficient capital. Available: ${CAPITAL_POOL['available']}")
    
    # Calculate recovery target
    recovery_target = outcome_price * plan["recovery_multiple"]
    
    # Apply risk adjustment
    risk_tier = OUTCOME_RISK_TIERS.get(outcome_type, OUTCOME_RISK_TIERS["marketing_campaign"])
    adjusted_multiple = plan["recovery_multiple"] * risk_tier["multiplier_adjustment"]
    adjusted_target = outcome_price * adjusted_multiple
    
    contract_id = f"pwp_{buyer_username}_{outcome_id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    contract = {
        "contract_id": contract_id,
        "buyer_username": buyer_username,
        "agent_username": agent_username,
        "outcome_id": outcome_id,
        "outcome_price": outcome_price,
        "outcome_type": outcome_type,
        "pwp_plan": pwp_plan,
        "plan_details": plan,
        "revenue_share_pct": plan["revenue_share_pct"],
        "recovery_multiple": plan["recovery_multiple"],
        "risk_adjusted_multiple": round(adjusted_multiple, 2),
        "recovery_target": round(recovery_target, 2),
        "risk_adjusted_target": round(adjusted_target, 2),
        "max_term_months": plan["max_term_months"],
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "term_end_date": (datetime.now(timezone.utc) + timedelta(days=plan["max_term_months"] * 30)).isoformat(),
        "agent_paid_at": None,
        "total_collected": 0.0,
        "payments_received": 0,
        "last_payment_at": None,
        "completed_at": None,
        "metadata": metadata or {}
    }
    
    PWP_CONTRACTS_DB[contract_id] = contract
    
    # Deploy capital to agent
    _deploy_capital_to_agent(contract_id, agent_username, outcome_price)
    
    return {
        "success": True,
        "contract": contract,
        "agent_payment": {
            "amount": outcome_price,
            "status": "disbursed",
            "message": f"Agent receives ${outcome_price:,.2f} upfront"
        },
        "buyer_terms": {
            "revenue_share": f"{plan['revenue_share_pct']}%",
            "recovery_target": f"${recovery_target:,.2f}",
            "max_term": f"{plan['max_term_months']} months",
            "message": f"Pay {plan['revenue_share_pct']}% of revenue until ${recovery_target:,.2f} collected"
        }
    }


def _deploy_capital_to_agent(
    contract_id: str,
    agent_username: str,
    amount: float
) -> None:
    """Deploy capital from pool to agent."""
    CAPITAL_POOL["deployed"] += amount
    CAPITAL_POOL["available"] -= amount
    
    # Record in contract
    contract = PWP_CONTRACTS_DB[contract_id]
    contract["agent_paid_at"] = datetime.now(timezone.utc).isoformat()
    contract["capital_deployed"] = amount


def record_revenue_payment(
    contract_id: str,
    revenue_amount: float,
    payment_source: str = "stripe",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Record a revenue payment from buyer.
    
    Args:
        contract_id: PWP contract ID
        revenue_amount: Buyer's revenue this period
        payment_source: Where payment came from
        metadata: Additional payment metadata
    
    Returns:
        Payment record and contract status
    """
    if contract_id not in PWP_CONTRACTS_DB:
        raise ValueError(f"Contract not found: {contract_id}")
    
    contract = PWP_CONTRACTS_DB[contract_id]
    
    if contract["status"] not in ["active", "collecting"]:
        raise ValueError(f"Contract not active: {contract['status']}")
    
    # Calculate payment amount (revenue share %)
    share_pct = contract["revenue_share_pct"] / 100
    payment_amount = revenue_amount * share_pct
    
    payment_id = f"pwp_payment_{contract_id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    payment = {
        "payment_id": payment_id,
        "contract_id": contract_id,
        "buyer_username": contract["buyer_username"],
        "revenue_amount": revenue_amount,
        "share_pct": contract["revenue_share_pct"],
        "payment_amount": payment_amount,
        "payment_source": payment_source,
        "paid_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {}
    }
    
    PWP_PAYMENTS_DB[payment_id] = payment
    
    # Update contract
    contract["total_collected"] += payment_amount
    contract["payments_received"] += 1
    contract["last_payment_at"] = datetime.now(timezone.utc).isoformat()
    contract["status"] = "collecting"
    
    # Check if recovery target met
    if contract["total_collected"] >= contract["recovery_target"]:
        _complete_pwp_contract(contract_id)
        
        return {
            "success": True,
            "payment": payment,
            "contract_status": "completed",
            "total_collected": contract["total_collected"],
            "recovery_target": contract["recovery_target"],
            "message": f"✅ Contract completed! Collected ${contract['total_collected']:,.2f}"
        }
    
    # Calculate progress
    progress_pct = (contract["total_collected"] / contract["recovery_target"]) * 100
    remaining = contract["recovery_target"] - contract["total_collected"]
    
    return {
        "success": True,
        "payment": payment,
        "contract_status": "collecting",
        "progress": {
            "collected": round(contract["total_collected"], 2),
            "target": contract["recovery_target"],
            "remaining": round(remaining, 2),
            "percent": round(progress_pct, 1)
        },
        "message": f"Payment recorded: ${payment_amount:,.2f} ({progress_pct:.1f}% complete)"
    }


def _complete_pwp_contract(contract_id: str) -> None:
    """Complete PWP contract and return capital to pool."""
    contract = PWP_CONTRACTS_DB[contract_id]
    
    contract["status"] = "completed"
    contract["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    # Calculate profit
    principal = contract["outcome_price"]
    collected = contract["total_collected"]
    profit = collected - principal
    
    contract["final_profit"] = profit
    contract["roi"] = (profit / principal) * 100
    
    # Return to capital pool
    CAPITAL_POOL["deployed"] -= principal
    CAPITAL_POOL["available"] += collected
    CAPITAL_POOL["total_recovered"] += collected
    CAPITAL_POOL["total_profit"] += profit


def check_pwp_contract_expiry(contract_id: str) -> Dict[str, Any]:
    """
    Check if PWP contract has expired.
    
    Args:
        contract_id: Contract to check
    
    Returns:
        Expiry status and actions
    """
    if contract_id not in PWP_CONTRACTS_DB:
        raise ValueError(f"Contract not found: {contract_id}")
    
    contract = PWP_CONTRACTS_DB[contract_id]
    
    if contract["status"] != "collecting":
        return {
            "expired": False,
            "status": contract["status"],
            "message": "Contract not in collection phase"
        }
    
    term_end = datetime.fromisoformat(contract["term_end_date"])
    now = datetime.now(timezone.utc)
    
    if now > term_end:
        # Contract expired
        _expire_pwp_contract(contract_id)
        
        principal = contract["outcome_price"]
        collected = contract["total_collected"]
        loss = principal - collected
        
        return {
            "expired": True,
            "status": "expired",
            "collected": collected,
            "target": contract["recovery_target"],
            "loss": round(loss, 2),
            "message": f"Contract expired. Loss: ${loss:,.2f}"
        }
    
    days_remaining = (term_end - now).days
    
    return {
        "expired": False,
        "status": "active",
        "days_remaining": days_remaining,
        "term_end_date": contract["term_end_date"],
        "message": f"{days_remaining} days remaining"
    }


def _expire_pwp_contract(contract_id: str) -> None:
    """Expire PWP contract and write off loss."""
    contract = PWP_CONTRACTS_DB[contract_id]
    
    contract["status"] = "expired"
    contract["expired_at"] = datetime.now(timezone.utc).isoformat()
    
    # Calculate loss
    principal = contract["outcome_price"]
    collected = contract["total_collected"]
    loss = principal - collected
    
    contract["final_loss"] = loss
    contract["recovery_rate"] = (collected / principal) * 100
    
    # Adjust capital pool
    CAPITAL_POOL["deployed"] -= principal
    CAPITAL_POOL["available"] += collected  # Only recovered amount
    CAPITAL_POOL["total_recovered"] += collected


def get_pwp_contract_status(contract_id: str) -> Dict[str, Any]:
    """
    Get comprehensive PWP contract status.
    
    Args:
        contract_id: Contract ID
    
    Returns:
        Full contract status
    """
    if contract_id not in PWP_CONTRACTS_DB:
        raise ValueError(f"Contract not found: {contract_id}")
    
    contract = PWP_CONTRACTS_DB[contract_id]
    
    # Calculate metrics
    progress_pct = 0
    remaining = contract["recovery_target"]
    
    if contract["total_collected"] > 0:
        progress_pct = (contract["total_collected"] / contract["recovery_target"]) * 100
        remaining = contract["recovery_target"] - contract["total_collected"]
    
    # Time metrics
    created = datetime.fromisoformat(contract["created_at"])
    term_end = datetime.fromisoformat(contract["term_end_date"])
    now = datetime.now(timezone.utc)
    
    days_elapsed = (now - created).days
    days_remaining = (term_end - now).days
    
    return {
        "contract_id": contract_id,
        "status": contract["status"],
        "buyer": contract["buyer_username"],
        "agent": contract["agent_username"],
        "outcome_id": contract["outcome_id"],
        "plan": contract["pwp_plan"],
        "financial": {
            "agent_paid": contract["outcome_price"],
            "revenue_share_pct": contract["revenue_share_pct"],
            "recovery_target": contract["recovery_target"],
            "total_collected": round(contract["total_collected"], 2),
            "remaining": round(remaining, 2),
            "progress_pct": round(progress_pct, 1)
        },
        "timeline": {
            "created_at": contract["created_at"],
            "term_end_date": contract["term_end_date"],
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "payments_received": contract["payments_received"],
            "last_payment_at": contract.get("last_payment_at")
        },
        "contract": contract
    }


def calculate_pwp_pricing(
    outcome_price: float,
    pwp_plan: str,
    outcome_type: str = "marketing_campaign"
) -> Dict[str, Any]:
    """
    Calculate PWP pricing for all scenarios.
    
    Args:
        outcome_price: Outcome price
        pwp_plan: PWP plan type
        outcome_type: Outcome type for risk adjustment
    
    Returns:
        Pricing breakdown
    """
    if pwp_plan not in PWP_PLANS:
        raise ValueError(f"Invalid PWP plan: {pwp_plan}")
    
    plan = PWP_PLANS[pwp_plan]
    risk_tier = OUTCOME_RISK_TIERS.get(outcome_type, OUTCOME_RISK_TIERS["marketing_campaign"])
    
    # Calculate targets
    base_target = outcome_price * plan["recovery_multiple"]
    adjusted_multiple = plan["recovery_multiple"] * risk_tier["multiplier_adjustment"]
    risk_adjusted_target = outcome_price * adjusted_multiple
    
    # Calculate monthly scenarios
    monthly_revenue_scenarios = [5000, 10000, 20000, 50000]
    payment_scenarios = []
    
    for monthly_revenue in monthly_revenue_scenarios:
        monthly_payment = monthly_revenue * (plan["revenue_share_pct"] / 100)
        months_to_recovery = base_target / monthly_payment if monthly_payment > 0 else float('inf')
        
        payment_scenarios.append({
            "monthly_revenue": monthly_revenue,
            "monthly_payment": round(monthly_payment, 2),
            "months_to_recovery": round(months_to_recovery, 1)
        })
    
    return {
        "outcome_price": outcome_price,
        "pwp_plan": pwp_plan,
        "plan_name": plan["name"],
        "outcome_type": outcome_type,
        "terms": {
            "revenue_share_pct": plan["revenue_share_pct"],
            "recovery_multiple": plan["recovery_multiple"],
            "risk_adjusted_multiple": round(adjusted_multiple, 2),
            "max_term_months": plan["max_term_months"]
        },
        "targets": {
            "base_recovery": round(base_target, 2),
            "risk_adjusted_recovery": round(risk_adjusted_target, 2)
        },
        "payment_scenarios": payment_scenarios,
        "risk_assessment": {
            "risk_level": risk_tier["risk_level"],
            "default_rate": f"{risk_tier['default_rate'] * 100}%",
            "multiplier_adjustment": risk_tier["multiplier_adjustment"]
        }
    }


def get_buyer_pwp_dashboard(buyer_username: str) -> Dict[str, Any]:
    """
    Get buyer's PWP dashboard.
    
    Args:
        buyer_username: Buyer's username
    
    Returns:
        Buyer's active contracts and totals
    """
    buyer_contracts = [
        c for c in PWP_CONTRACTS_DB.values()
        if c["buyer_username"] == buyer_username
    ]
    
    total_financed = sum(c["outcome_price"] for c in buyer_contracts)
    total_paid = sum(c["total_collected"] for c in buyer_contracts)
    total_remaining = sum(
        c["recovery_target"] - c["total_collected"]
        for c in buyer_contracts
        if c["status"] in ["active", "collecting"]
    )
    
    active_contracts = [
        {
            "contract_id": c["contract_id"],
            "outcome_id": c["outcome_id"],
            "agent": c["agent_username"],
            "financed": c["outcome_price"],
            "paid": c["total_collected"],
            "remaining": c["recovery_target"] - c["total_collected"],
            "progress_pct": (c["total_collected"] / c["recovery_target"]) * 100,
            "status": c["status"]
        }
        for c in buyer_contracts
        if c["status"] in ["active", "collecting"]
    ]
    
    return {
        "buyer_username": buyer_username,
        "summary": {
            "total_contracts": len(buyer_contracts),
            "active_contracts": len(active_contracts),
            "total_financed": round(total_financed, 2),
            "total_paid": round(total_paid, 2),
            "total_remaining": round(total_remaining, 2)
        },
        "active_contracts": active_contracts
    }


def get_capital_pool_status() -> Dict[str, Any]:
    """
    Get PWP capital pool status.
    
    Returns:
        Pool metrics and health
    """
    utilization_rate = (CAPITAL_POOL["deployed"] / CAPITAL_POOL["total_capital"]) * 100
    
    active_contracts = [
        c for c in PWP_CONTRACTS_DB.values()
        if c["status"] in ["active", "collecting"]
    ]
    
    avg_recovery = 0
    if PWP_CONTRACTS_DB:
        completed = [c for c in PWP_CONTRACTS_DB.values() if c["status"] == "completed"]
        if completed:
            avg_recovery = sum(c.get("recovery_rate", 0) for c in completed) / len(completed)
    
    return {
        "capital_pool": {
            "total_capital": CAPITAL_POOL["total_capital"],
            "deployed": round(CAPITAL_POOL["deployed"], 2),
            "available": round(CAPITAL_POOL["available"], 2),
            "utilization_rate": round(utilization_rate, 1)
        },
        "performance": {
            "total_recovered": round(CAPITAL_POOL["total_recovered"], 2),
            "total_profit": round(CAPITAL_POOL["total_profit"], 2),
            "roi": round((CAPITAL_POOL["total_profit"] / CAPITAL_POOL["total_capital"]) * 100, 2) if CAPITAL_POOL["total_capital"] > 0 else 0,
            "avg_recovery_rate": round(avg_recovery, 1)
        },
        "active_contracts": {
            "count": len(active_contracts),
            "total_deployed": sum(c["outcome_price"] for c in active_contracts)
        }
    }


def get_all_pwp_plans() -> Dict[str, Any]:
    """
    Get all available PWP plans.
    
    Returns:
        All plans with details
    """
    plans = []
    
    for plan_type, plan in PWP_PLANS.items():
        plans.append({
            "plan_type": plan_type,
            "name": plan["name"],
            "icon": plan["icon"],
            "description": plan["description"],
            "revenue_share_pct": plan["revenue_share_pct"],
            "recovery_multiple": plan["recovery_multiple"],
            "max_term_months": plan["max_term_months"],
            "min_outcome_size": plan["min_outcome_size"],
            "risk_tier": plan["risk_tier"]
        })
    
    return {
        "plans": plans,
        "total_plans": len(plans)
    }


# Example usage
if __name__ == "__main__":
    # Create PWP contract
    contract = create_pwp_contract(
        "buyer123",
        "agent456",
        "outcome_789",
        10000.0,
        "balanced",
        "marketing_campaign"
    )
    print(f"Contract created: {contract['contract']['contract_id']}")
    print(f"Agent receives: ${contract['agent_payment']['amount']:,.2f}")
    print(f"Buyer pays: {contract['buyer_terms']['revenue_share']}")
    
    # Record revenue payment
    payment = record_revenue_payment(
        contract['contract']['contract_id'],
        50000.0  # $50k revenue → 20% = $10k payment
    )
    print(f"\nPayment recorded: ${payment['payment']['payment_amount']:,.2f}")
    print(f"Progress: {payment['progress']['percent']}%")
