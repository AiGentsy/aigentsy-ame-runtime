from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import httpx

_FRAUD_CASES: Dict[str, Dict[str, Any]] = {}
_BLOCKLIST: List[str] = []
_ACTION_LOG: List[Dict[str, Any]] = []

MAX_ACTIONS_PER_HOUR = 50
MAX_FAILED_PAYMENTS = 3
MIN_REPUTATION_SCORE = 20

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def check_fraud_signals(
    username: str,
    action_type: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Check for fraud signals before allowing action"""
    
    metadata = metadata or {}
    signals = []
    risk_score = 0
    
    # Check if user is blocklisted
    if username in _BLOCKLIST:
        return {
            "ok": False,
            "blocked": True,
            "reason": "User is blocklisted",
            "risk_score": 100
        }
    
    # Get user data
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(
                "https://aigentsy-ame-runtime.onrender.com/user",
                json={"username": username}
            )
            user_data = r.json().get("record", {})
        except Exception:
            user_data = {}
    
    # SIGNAL 1: Velocity check (30 points)
    recent_actions = [
        a for a in _ACTION_LOG
        if a["username"] == username
        and (datetime.now(timezone.utc) - datetime.fromisoformat(a["timestamp"].replace("Z", "+00:00"))).seconds < 3600
    ]
    
    if len(recent_actions) > MAX_ACTIONS_PER_HOUR:
        risk_score += 30
        signals.append(f"High velocity: {len(recent_actions)} actions in last hour")
    
    # SIGNAL 2: Failed payments (25 points)
    failed_payments = sum(1 for a in _ACTION_LOG if a["username"] == username and a.get("failed_payment"))
    
    if failed_payments >= MAX_FAILED_PAYMENTS:
        risk_score += 25
        signals.append(f"Multiple failed payments: {failed_payments}")
    
    # SIGNAL 3: Low reputation (20 points)
    outcome_score = int(user_data.get("outcomeScore", 50))
    
    if outcome_score < MIN_REPUTATION_SCORE:
        risk_score += 20
        signals.append(f"Low reputation score: {outcome_score}")
    
    # SIGNAL 4: New account doing high-value actions (15 points)
    account_age_days = 999
    if user_data.get("created"):
        created = datetime.fromisoformat(user_data["created"].replace("Z", "+00:00"))
        account_age_days = (datetime.now(timezone.utc) - created).days
    
    if account_age_days < 7 and action_type in ["withdrawal", "large_purchase"]:
        risk_score += 15
        signals.append(f"New account ({account_age_days} days) attempting high-value action")
    
    # SIGNAL 5: Unusual patterns (10 points each)
    if action_type == "withdrawal":
        amount = float(metadata.get("amount", 0))
        
        # Check if withdrawal is much larger than normal
        past_withdrawals = [
            a for a in _ACTION_LOG
            if a["username"] == username and a["action_type"] == "withdrawal"
        ]
        
        if past_withdrawals:
            avg_withdrawal = sum(float(a.get("metadata", {}).get("amount", 0)) for a in past_withdrawals) / len(past_withdrawals)
            
            if amount > avg_withdrawal * 5:
                risk_score += 10
                signals.append(f"Unusual withdrawal: ${amount:.2f} vs avg ${avg_withdrawal:.2f}")
    
    # Log this action
    _ACTION_LOG.append({
        "username": username,
        "action_type": action_type,
        "metadata": metadata,
        "timestamp": now_iso(),
        "risk_score": risk_score
    })
    
    # Determine if action should be blocked
    blocked = risk_score >= 60
    requires_review = risk_score >= 40
    
    # Auto-suspend if very high risk
    if risk_score >= 80:
        await suspend_account(username, "Automatic suspension due to high fraud risk", signals)
    
    return {
        "ok": not blocked,
        "blocked": blocked,
        "requires_review": requires_review,
        "risk_score": risk_score,
        "signals": signals,
        "action_type": action_type
    }


async def suspend_account(
    username: str,
    reason: str,
    evidence: List[str]
) -> Dict[str, Any]:
    """Suspend account due to fraud"""
    
    case_id = f"fraud_{uuid4().hex[:8]}"
    
    case = {
        "id": case_id,
        "username": username,
        "status": "SUSPENDED",
        "reason": reason,
        "evidence": evidence,
        "suspended_at": now_iso(),
        "resolved_at": None,
        "resolution": None
    }
    
    _FRAUD_CASES[case_id] = case
    _BLOCKLIST.append(username)
    
    # Notify user
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                json={
                    "id": f"fraud_notif_{uuid4().hex[:8]}",
                    "sender": "system",
                    "recipient": username,
                    "title": "Account Suspended - Fraud Investigation",
                    "body": f"""Your account has been suspended due to suspicious activity.

Reason: {reason}

Evidence:
{chr(10).join(f'- {e}' for e in evidence)}

Case ID: {case_id}

If you believe this is an error, please contact support with your case ID.""",
                    "meta": {"fraud_case_id": case_id},
                    "status": "sent",
                    "timestamp": now_iso()
                }
            )
        except Exception as e:
            print(f"Failed to notify user: {e}")
    
    return {"ok": True, "case_id": case_id, "case": case}


def report_fraud(
    reporter: str,
    reported_user: str,
    fraud_type: str,
    description: str,
    evidence: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Report suspected fraud"""
    
    case_id = f"fraud_{uuid4().hex[:8]}"
    
    case = {
        "id": case_id,
        "reporter": reporter,
        "reported_user": reported_user,
        "fraud_type": fraud_type,
        "description": description,
        "evidence": evidence or {},
        "status": "UNDER_REVIEW",
        "reported_at": now_iso(),
        "resolved_at": None,
        "resolution": None
    }
    
    _FRAUD_CASES[case_id] = case
    
    return {"ok": True, "case_id": case_id, "message": "Fraud report submitted for review"}


def resolve_fraud_case(
    case_id: str,
    resolution: str,
    action: str,
    notes: str = ""
) -> Dict[str, Any]:
    """Resolve fraud case"""
    
    case = _FRAUD_CASES.get(case_id)
    
    if not case:
        return {"ok": False, "error": "case_not_found"}
    
    case["status"] = "RESOLVED"
    case["resolution"] = resolution
    case["action_taken"] = action
    case["notes"] = notes
    case["resolved_at"] = now_iso()
    
    # Take action based on resolution
    if action == "UNBLOCK" and case["username"] in _BLOCKLIST:
        _BLOCKLIST.remove(case["username"])
    elif action == "PERMANENT_BAN":
        if case["username"] not in _BLOCKLIST:
            _BLOCKLIST.append(case["username"])
    
    return {"ok": True, "case": case}


def get_fraud_case(case_id: str) -> Dict[str, Any]:
    """Get fraud case details"""
    case = _FRAUD_CASES.get(case_id)
    
    if not case:
        return {"ok": False, "error": "case_not_found"}
    
    return {"ok": True, "case": case}


def list_fraud_cases(
    username: str = None,
    status: str = None
) -> Dict[str, Any]:
    """List fraud cases"""
    cases = list(_FRAUD_CASES.values())
    
    if username:
        cases = [c for c in cases if c.get("username") == username or c.get("reported_user") == username]
    
    if status:
        cases = [c for c in cases if c["status"] == status.upper()]
    
    cases.sort(key=lambda c: c.get("reported_at") or c.get("suspended_at", ""), reverse=True)
    
    return {"ok": True, "cases": cases, "count": len(cases)}


def get_user_risk_profile(username: str) -> Dict[str, Any]:
    """Get comprehensive risk profile for user"""
    
    user_actions = [a for a in _ACTION_LOG if a["username"] == username]
    user_cases = [c for c in _FRAUD_CASES.values() if c.get("username") == username or c.get("reported_user") == username]
    
    # Calculate average risk score
    if user_actions:
        avg_risk = sum(a.get("risk_score", 0) for a in user_actions) / len(user_actions)
    else:
        avg_risk = 0
    
    # Count high-risk actions
    high_risk_actions = len([a for a in user_actions if a.get("risk_score", 0) >= 40])
    
    # Current status
    is_blocked = username in _BLOCKLIST
    active_cases = len([c for c in user_cases if c["status"] in ["SUSPENDED", "UNDER_REVIEW"]])
    
    return {
        "ok": True,
        "username": username,
        "is_blocked": is_blocked,
        "active_cases": active_cases,
        "total_actions": len(user_actions),
        "high_risk_actions": high_risk_actions,
        "avg_risk_score": round(avg_risk, 1),
        "recent_signals": [
            a.get("signals", [])
            for a in sorted(user_actions, key=lambda x: x["timestamp"], reverse=True)[:5]
            if a.get("risk_score", 0) >= 40
        ]
    }


def get_fraud_stats() -> Dict[str, Any]:
    """Get fraud detection statistics"""
    
    total_cases = len(_FRAUD_CASES)
    suspended = len([c for c in _FRAUD_CASES.values() if c["status"] == "SUSPENDED"])
    resolved = len([c for c in _FRAUD_CASES.values() if c["status"] == "RESOLVED"])
    under_review = len([c for c in _FRAUD_CASES.values() if c["status"] == "UNDER_REVIEW"])
    
    total_actions = len(_ACTION_LOG)
    high_risk_actions = len([a for a in _ACTION_LOG if a.get("risk_score", 0) >= 40])
    
    return {
        "ok": True,
        "cases": {
            "total": total_cases,
            "suspended": suspended,
            "under_review": under_review,
            "resolved": resolved
        },
        "blocklist_size": len(_BLOCKLIST),
        "actions": {
            "total": total_actions,
            "high_risk": high_risk_actions,
            "high_risk_pct": round((high_risk_actions / total_actions * 100), 1) if total_actions > 0 else 0
        }
    }
