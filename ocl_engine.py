"""
AiGentsy OCL (Outcome-backed Credit Line) Engine
Auto-expands credit based on verified PoOs
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

def _now():
    return datetime.now(timezone.utc).isoformat()

def _days_ago(ts_iso: str) -> int:
    try:
        then = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - then).days
    except:
        return 9999

async def calculate_ocl_limit(user: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate OCL limit based on:
    1. Base credit ($10)
    2. Verified PoOs in last 30 days ($5 each)
    3. OutcomeScore multiplier
    4. Cap at $200
    """
    ocl = user.get("ocl", {})
    base = float(ocl.get("limit", 10.0))
    multiplier = float(ocl.get("poo_multiplier", 5.0))
    cap = float(ocl.get("max_limit", 200.0))
    
    # Count verified PoOs from last 30 days
    verified_poos = [
        p for p in user.get("outcomes", [])
        if p.get("status") == "verified" 
        and _days_ago(p.get("ts", "")) <= 30
    ]
    
    # OutcomeScore bonus (0-100 score → 0-1.0 multiplier)
    outcome_score = int(user.get("outcomeScore", 0))
    score_multiplier = 1.0 + (outcome_score / 100.0)
    
    # Calculate limit
    poo_credit = len(verified_poos) * multiplier
    total_limit = min(
        (base + poo_credit) * score_multiplier,
        cap
    )
    
    # Calculate used amount
    ledger = user.get("ownership", {}).get("ledger", [])
    used = sum([
        abs(float(e.get("amount", 0)))
        for e in ledger
        if e.get("basis") == "ocl_spend"
    ])
    
    # Calculate repaid amount
    repaid = sum([
        float(e.get("amount", 0))
        for e in ledger
        if e.get("basis") == "ocl_repay"
    ])
    
    available = max(0, total_limit - used + repaid)
    
    return {
        "limit": round(total_limit, 2),
        "used": round(used, 2),
        "repaid": round(repaid, 2),
        "available": round(available, 2),
        "verified_poos": len(verified_poos),
        "outcome_score": outcome_score,
        "expansion_rate": f"${multiplier}/PoO"
    }

async def spend_ocl(user: Dict[str, Any], amount: float, ref: str) -> Dict[str, Any]:
    """
    Spend from OCL if available
    Returns updated ledger entry
    """
    limits = await calculate_ocl_limit(user)
    
    if amount > limits["available"]:
        return {
            "ok": False,
            "error": "insufficient_credit",
            "available": limits["available"],
            "requested": amount
        }
    
    # Add OCL spend to ledger
    entry = {
        "ts": _now(),
        "amount": -float(amount),
        "currency": "USD",
        "basis": "ocl_spend",
        "ref": ref,
        "credit_limit": limits["limit"]
    }
    
    user.setdefault("ownership", {}).setdefault("ledger", []).append(entry)
    
    return {
        "ok": True,
        "entry": entry,
        "remaining_credit": limits["available"] - amount
    }

async def auto_repay_ocl(user: Dict[str, Any], earnings: float) -> Dict[str, Any]:
    """
    Auto-repay OCL from earnings
    Deducts 50% of earnings until OCL balance = 0
    """
    limits = await calculate_ocl_limit(user)
    outstanding = limits["used"] - limits["repaid"]
    
    if outstanding <= 0:
        return {"ok": True, "repaid": 0, "outstanding": 0}
    
    # Repay 50% of earnings (or full outstanding, whichever is less)
    repay_amount = min(earnings * 0.5, outstanding)
    
    if repay_amount > 0:
        entry = {
            "ts": _now(),
            "amount": float(repay_amount),
            "currency": "USD",
            "basis": "ocl_repay",
            "ref": "auto_repay",
            "outstanding_before": outstanding
        }
        
        user.setdefault("ownership", {}).setdefault("ledger", []).append(entry)
        
        return {
            "ok": True,
            "repaid": round(repay_amount, 2),
            "outstanding": round(outstanding - repay_amount, 2)
        }
    
    return {"ok": True, "repaid": 0, "outstanding": outstanding}

async def expand_ocl_on_poo(user: Dict[str, Any], poo_id: str) -> Dict[str, Any]:
    """
    Called when a PoO is verified
    Instantly expands OCL limit
    """
    # Recalculate limit (will include new PoO)
    new_limits = await calculate_ocl_limit(user)
    
    # Log expansion event
    event = {
        "ts": _now(),
        "type": "ocl_expansion",
        "poo_id": poo_id,
        "new_limit": new_limits["limit"],
        "new_available": new_limits["available"]
    }
    
    user.setdefault("ocl", {}).setdefault("expansion_events", []).append(event)
    
    return {
        "ok": True,
        "new_limit": new_limits["limit"],
        "expansion_amount": user.get("ocl", {}).get("poo_multiplier", 5.0)
    }
