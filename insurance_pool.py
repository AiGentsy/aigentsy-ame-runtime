"""
AiGentsy Performance Insurance Pool
Community-funded safety net with reputation-based refunds
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

def _now():
    return datetime.now(timezone.utc).isoformat()

def _days_ago(ts_iso: str) -> int:
    try:
        then = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - then).days
    except:
        return 9999

# Insurance rates
INSURANCE_RATE = 0.005  # 0.5% of order value
REFUND_THRESHOLD_DISPUTE_RATE = 0.02  # < 2% dispute rate qualifies for refund
ANNUAL_REFUND_PERIOD_DAYS = 365

# Pool caps (prevent abuse)
MAX_PAYOUT_MULTIPLE = 10.0  # Max payout = 10x what agent paid in
MIN_POOL_RESERVE = 1000.0  # Never drain below $1000


async def calculate_insurance_fee(order_value: float) -> Dict[str, Any]:
    """Calculate insurance fee for an order"""
    fee = round(order_value * INSURANCE_RATE, 2)
    
    return {
        "order_value": order_value,
        "insurance_rate": INSURANCE_RATE,
        "insurance_fee": fee
    }


async def collect_insurance(
    user: Dict[str, Any],
    intent: Dict[str, Any],
    order_value: float
) -> Dict[str, Any]:
    """
    Collect insurance fee when intent is awarded
    Deducted from agent's balance
    """
    fee = round(order_value * INSURANCE_RATE, 2)
    
    # Check if agent has funds
    current_aigx = float(user.get("ownership", {}).get("aigx", 0))
    
    if current_aigx < fee:
        return {
            "ok": False,
            "error": "insufficient_funds_for_insurance",
            "required": fee,
            "available": current_aigx
        }
    
    # Deduct fee
    user["ownership"]["aigx"] = current_aigx - fee
    
    # Add to ledger
    insurance_entry = {
        "ts": _now(),
        "amount": -fee,
        "currency": "AIGx",
        "basis": "insurance_premium",
        "ref": intent.get("id"),
        "order_value": order_value
    }
    
    user.setdefault("ownership", {}).setdefault("ledger", []).append(insurance_entry)
    
    # Track in intent
    intent["insurance"] = {
        "fee": fee,
        "collected_at": _now(),
        "agent": user.get("consent", {}).get("username") or user.get("username")
    }
    
    # Update global pool (stored in a special "pool" user record)
    # We'll handle this in the endpoint
    
    return {
        "ok": True,
        "fee": fee,
        "remaining_balance": user["ownership"]["aigx"]
    }


async def get_pool_balance(pool_user: Dict[str, Any]) -> float:
    """Get current insurance pool balance"""
    ledger = pool_user.get("ownership", {}).get("ledger", [])
    
    balance = sum([
        float(entry.get("amount", 0))
        for entry in ledger
        if entry.get("basis") in ["insurance_premium", "insurance_payout"]
    ])
    
    return round(balance, 2)


async def payout_from_pool(
    pool_user: Dict[str, Any],
    dispute: Dict[str, Any],
    payout_amount: float
) -> Dict[str, Any]:
    """
    Pay out from insurance pool on verified dispute
    """
    pool_balance = await get_pool_balance(pool_user)
    
    # Check pool has funds
    if pool_balance < MIN_POOL_RESERVE:
        return {
            "ok": False,
            "error": "pool_depleted",
            "pool_balance": pool_balance,
            "min_reserve": MIN_POOL_RESERVE
        }
    
    # Check payout doesn't exceed reserve requirement
    if (pool_balance - payout_amount) < MIN_POOL_RESERVE:
        # Reduce payout to maintain reserve
        payout_amount = pool_balance - MIN_POOL_RESERVE
    
    # Cap payout at 10x agent's contributions
    agent = dispute.get("agent")
    if agent:
        # Calculate agent's lifetime contributions
        agent_contributions = sum([
            abs(float(e.get("amount", 0)))
            for e in pool_user.get("ownership", {}).get("ledger", [])
            if e.get("basis") == "insurance_premium" and e.get("agent") == agent
        ])
        
        max_payout = agent_contributions * MAX_PAYOUT_MULTIPLE
        if payout_amount > max_payout:
            payout_amount = max_payout
    
    # Deduct from pool
    payout_entry = {
        "ts": _now(),
        "amount": -payout_amount,
        "currency": "AIGx",
        "basis": "insurance_payout",
        "ref": dispute.get("dispute_id"),
        "intent_id": dispute.get("intent_id"),
        "buyer": dispute.get("buyer")
    }
    
    pool_user.setdefault("ownership", {}).setdefault("ledger", []).append(payout_entry)
    
    return {
        "ok": True,
        "payout": payout_amount,
        "pool_balance_after": await get_pool_balance(pool_user),
        "paid_to": dispute.get("buyer")
    }


async def calculate_dispute_rate(user: Dict[str, Any], days: int = 365) -> Dict[str, Any]:
    """
    Calculate agent's dispute rate over time period
    """
    # Get all intents this agent worked on
    intents = user.get("intents", [])
    
    # Filter to completed intents in time period
    completed = []
    disputed = []
    
    for intent in intents:
        if intent.get("status") not in ["SETTLED", "DISPUTED", "RESOLVED_SPLIT"]:
            continue
        
        completed_at = intent.get("delivered_at") or intent.get("awarded_at")
        if not completed_at:
            continue
        
        if _days_ago(completed_at) > days:
            continue
        
        completed.append(intent)
        
        if intent.get("status") in ["DISPUTED", "RESOLVED_SPLIT"]:
            disputed.append(intent)
    
    total_intents = len(completed)
    total_disputes = len(disputed)
    
    dispute_rate = (total_disputes / total_intents) if total_intents > 0 else 0.0
    
    return {
        "total_intents": total_intents,
        "total_disputes": total_disputes,
        "dispute_rate": round(dispute_rate, 4),
        "qualifies_for_refund": dispute_rate < REFUND_THRESHOLD_DISPUTE_RATE and total_intents >= 10
    }


async def calculate_annual_refund(
    user: Dict[str, Any],
    pool_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate annual refund for low-dispute agents
    """
    # Check dispute rate
    dispute_stats = await calculate_dispute_rate(user, days=ANNUAL_REFUND_PERIOD_DAYS)
    
    if not dispute_stats["qualifies_for_refund"]:
        return {
            "ok": False,
            "eligible": False,
            "reason": f"Dispute rate {dispute_stats['dispute_rate']*100:.1f}% exceeds {REFUND_THRESHOLD_DISPUTE_RATE*100}% threshold or < 10 orders",
            "dispute_rate": dispute_stats["dispute_rate"],
            "threshold": REFUND_THRESHOLD_DISPUTE_RATE
        }
    
    # Calculate total premiums paid in last 365 days
    ledger = user.get("ownership", {}).get("ledger", [])
    
    premiums_paid = sum([
        abs(float(e.get("amount", 0)))
        for e in ledger
        if e.get("basis") == "insurance_premium" and _days_ago(e.get("ts", "")) <= ANNUAL_REFUND_PERIOD_DAYS
    ])
    
    # Check if agent already got refund in last 365 days
    recent_refunds = [
        e for e in ledger
        if e.get("basis") == "insurance_refund" and _days_ago(e.get("ts", "")) <= ANNUAL_REFUND_PERIOD_DAYS
    ]
    
    if recent_refunds:
        return {
            "ok": False,
            "eligible": False,
            "reason": "Already received refund in last 365 days",
            "last_refund_date": recent_refunds[0].get("ts")
        }
    
    # Check pool has funds
    pool_balance = await get_pool_balance(pool_user)
    
    if pool_balance < MIN_POOL_RESERVE + premiums_paid:
        # Partial refund
        refund_amount = max(0, pool_balance - MIN_POOL_RESERVE)
    else:
        # Full refund
        refund_amount = premiums_paid
    
    return {
        "ok": True,
        "eligible": True,
        "premiums_paid": round(premiums_paid, 2),
        "refund_amount": round(refund_amount, 2),
        "dispute_rate": dispute_stats["dispute_rate"],
        "total_orders": dispute_stats["total_intents"]
    }


async def issue_annual_refund(
    user: Dict[str, Any],
    pool_user: Dict[str, Any],
    refund_amount: float
) -> Dict[str, Any]:
    """
    Issue annual insurance refund to qualifying agent
    """
    # Credit agent
    user["ownership"]["aigx"] = float(user["ownership"].get("aigx", 0)) + refund_amount
    
    user["ownership"]["ledger"].append({
        "ts": _now(),
        "amount": refund_amount,
        "currency": "AIGx",
        "basis": "insurance_refund",
        "ref": "annual_refund_low_dispute_rate"
    })
    
    # Deduct from pool
    pool_user["ownership"]["ledger"].append({
        "ts": _now(),
        "amount": -refund_amount,
        "currency": "AIGx",
        "basis": "insurance_refund_payout",
        "agent": user.get("consent", {}).get("username") or user.get("username")
    })
    
    return {
        "ok": True,
        "refunded": refund_amount,
        "new_balance": user["ownership"]["aigx"],
        "pool_balance": await get_pool_balance(pool_user)
    }
