# agent_spending.py — Agent Operating Budgets & Spending
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from log_to_jsonbin import get_user, credit_aigx, append_intent_ledger

# Governor integration for global spend caps
try:
    from governors.governor_runtime import guard_spend as governor_guard_spend
    GOVERNOR_ENABLED = True
except ImportError:
    GOVERNOR_ENABLED = False
    def governor_guard_spend(*args, **kwargs): return True

# Daily spending limits by autonomy level
AL_LIMITS = {
    "AL0": 0,      # No autonomous spending
    "AL1": 10,     # $10/day
    "AL2": 50,     # $50/day
    "AL3": 200,    # $200/day
    "AL4": 1000,   # $1k/day
    "AL5": 10000   # $10k/day (full autonomy)
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()


async def check_spending_capacity(username: str, amount_usd: float) -> Dict[str, Any]:
    """Check if agent can spend this amount"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        # Get autonomy level
        al = user.get("runtimeFlags", {}).get("autonomyLevel", "AL1")
        daily_limit = AL_LIMITS.get(al, 10)
        
        # Get today's spending
        ledger = user.get("ownership", {}).get("ledger", [])
        today = datetime.now(timezone.utc).date().isoformat()
        
        today_spending = sum(
            entry.get("amount", 0)
            for entry in ledger
            if entry.get("event") == "agent_spend" and entry.get("ts", "").startswith(today)
        )
        
        # Check capacity
        remaining = daily_limit - today_spending
        can_spend = amount_usd <= remaining
        
        return {
            "ok": True,
            "can_spend": can_spend,
            "autonomy_level": al,
            "daily_limit": daily_limit,
            "spent_today": round(today_spending, 2),
            "remaining": round(remaining, 2),
            "requested": amount_usd
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def execute_agent_spend(username: str, amount_usd: float, basis: str, ref: str = None) -> Dict[str, Any]:
    """Execute agent spending (checks limits first)"""
    try:
        # Check global governor caps first
        if GOVERNOR_ENABLED:
            if not governor_guard_spend("agent_spend", amount_usd, module="agent_spending"):
                return {
                    "ok": False,
                    "error": "governor_cap_exceeded",
                    "message": "Global spend cap reached for agent operations"
                }

        # Check capacity
        check = await check_spending_capacity(username, amount_usd)
        if not check.get("ok"):
            return check

        if not check.get("can_spend"):
            return {
                "ok": False,
                "error": "spending_limit_exceeded",
                "remaining": check.get("remaining")
            }
        
        # Deduct from balance
        user = get_user(username)
        current_balance = user.get("yield", {}).get("aigxEarned", 0)
        
        if current_balance < amount_usd:
            return {"ok": False, "error": "insufficient_balance"}
        
        # Post spend
        user["yield"]["aigxEarned"] = current_balance - amount_usd
        
        # Log to ledger
        append_intent_ledger(username, {
            "event": "agent_spend",
            "amount": amount_usd,
            "basis": basis,
            "ref": ref,
            "ts": now_iso()
        })
        
        return {
            "ok": True,
            "spent": amount_usd,
            "new_balance": round(user["yield"]["aigxEarned"], 2)
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def agent_to_agent_payment(from_user: str, to_user: str, amount_usd: float, reason: str) -> Dict[str, Any]:
    """Agent-to-agent payment (e.g., hiring another agent)"""
    try:
        # Check sender has funds
        check = await check_spending_capacity(from_user, amount_usd)
        if not check.get("ok") or not check.get("can_spend"):
            return {"ok": False, "error": "sender_insufficient_capacity"}
        
        sender = get_user(from_user)
        if sender.get("yield", {}).get("aigxEarned", 0) < amount_usd:
            return {"ok": False, "error": "sender_insufficient_balance"}
        
        # Deduct from sender
        sender["yield"]["aigxEarned"] -= amount_usd
        append_intent_ledger(from_user, {
            "event": "agent_payment_sent",
            "to": to_user,
            "amount": amount_usd,
            "reason": reason,
            "ts": now_iso()
        })
        
        # Credit receiver
        credit_aigx(to_user, amount_usd, {
            "source": "agent_payment",
            "from": from_user,
            "reason": reason
        })
        
        return {
            "ok": True,
            "from": from_user,
            "to": to_user,
            "amount": amount_usd,
            "reason": reason
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_spending_summary(username: str) -> Dict[str, Any]:
    """Get agent's spending analytics"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        ledger = user.get("ownership", {}).get("ledger", [])
        
        # Total spent
        total_spent = sum(
            entry.get("amount", 0)
            for entry in ledger
            if entry.get("event") == "agent_spend"
        )
        
        # Today's spending
        today = datetime.now(timezone.utc).date().isoformat()
        today_spent = sum(
            entry.get("amount", 0)
            for entry in ledger
            if entry.get("event") == "agent_spend" and entry.get("ts", "").startswith(today)
        )
        
        # Get limits
        al = user.get("runtimeFlags", {}).get("autonomyLevel", "AL1")
        daily_limit = AL_LIMITS.get(al, 10)
        
        return {
            "ok": True,
            "username": username,
            "autonomy_level": al,
            "daily_limit": daily_limit,
            "spent_today": round(today_spent, 2),
            "remaining_today": round(daily_limit - today_spent, 2),
            "total_spent_alltime": round(total_spent, 2),
            "current_balance": user.get("yield", {}).get("aigxEarned", 0)
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
