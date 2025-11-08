from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import httpx

_KYC_RECORDS: Dict[str, Dict[str, Any]] = {}
_TRANSACTION_HISTORY: List[Dict[str, Any]] = []
_SAR_REPORTS: List[Dict[str, Any]] = []
_RESTRICTED_COUNTRIES: List[str] = ["KP", "IR", "SY", "CU"]

LIMITS = {
    "NONE": {"daily": 100, "monthly": 500, "per_transaction": 50},
    "BASIC": {"daily": 1000, "monthly": 5000, "per_transaction": 500},
    "VERIFIED": {"daily": 10000, "monthly": 50000, "per_transaction": 5000},
    "ENHANCED": {"daily": 100000, "monthly": 500000, "per_transaction": 50000}
}

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def submit_kyc(
    username: str,
    level: str,
    full_name: str,
    date_of_birth: str,
    country: str,
    documents: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Submit KYC verification"""
    
    if level.upper() not in ["BASIC", "VERIFIED", "ENHANCED"]:
        return {"ok": False, "error": "invalid_level", "valid_levels": ["BASIC", "VERIFIED", "ENHANCED"]}
    
    # Check geographic restrictions
    if country.upper() in _RESTRICTED_COUNTRIES:
        return {
            "ok": False,
            "error": "restricted_country",
            "message": f"Service not available in {country}"
        }
    
    kyc_id = f"kyc_{uuid4().hex[:8]}"
    
    kyc_record = {
        "id": kyc_id,
        "username": username,
        "level": level.upper(),
        "full_name": full_name,
        "date_of_birth": date_of_birth,
        "country": country,
        "documents": documents or [],
        "status": "PENDING",
        "submitted_at": now_iso(),
        "reviewed_at": None,
        "reviewer_notes": None
    }
    
    _KYC_RECORDS[username] = kyc_record
    
    return {
        "ok": True,
        "kyc_id": kyc_id,
        "status": "PENDING",
        "message": "KYC submitted for review. This may take 1-3 business days."
    }


def approve_kyc(
    username: str,
    reviewer: str,
    notes: str = ""
) -> Dict[str, Any]:
    """Approve KYC (admin only)"""
    
    kyc = _KYC_RECORDS.get(username)
    
    if not kyc:
        return {"ok": False, "error": "kyc_not_found"}
    
    if kyc["status"] != "PENDING":
        return {"ok": False, "error": f"kyc_already_{kyc['status'].lower()}"}
    
    kyc["status"] = "APPROVED"
    kyc["reviewed_at"] = now_iso()
    kyc["reviewer"] = reviewer
    kyc["reviewer_notes"] = notes
    
    # Notify user
    _notify_kyc_status(username, "APPROVED", kyc["level"])
    
    return {"ok": True, "kyc": kyc, "message": f"{kyc['level']} verification approved"}


def reject_kyc(
    username: str,
    reviewer: str,
    reason: str
) -> Dict[str, Any]:
    """Reject KYC (admin only)"""
    
    kyc = _KYC_RECORDS.get(username)
    
    if not kyc:
        return {"ok": False, "error": "kyc_not_found"}
    
    if kyc["status"] != "PENDING":
        return {"ok": False, "error": f"kyc_already_{kyc['status'].lower()}"}
    
    kyc["status"] = "REJECTED"
    kyc["reviewed_at"] = now_iso()
    kyc["reviewer"] = reviewer
    kyc["rejection_reason"] = reason
    
    # Notify user
    _notify_kyc_status(username, "REJECTED", kyc["level"], reason)
    
    return {"ok": True, "kyc": kyc, "message": "KYC rejected"}


async def check_transaction_allowed(
    username: str,
    transaction_type: str,
    amount: float,
    destination: str = None
) -> Dict[str, Any]:
    """Check if transaction is allowed under compliance rules"""
    
    # Get KYC level
    kyc = _KYC_RECORDS.get(username)
    kyc_level = kyc.get("level", "NONE") if kyc and kyc.get("status") == "APPROVED" else "NONE"
    
    limits = LIMITS[kyc_level]
    
    # Check per-transaction limit
    if amount > limits["per_transaction"]:
        return {
            "ok": False,
            "blocked": True,
            "reason": f"Exceeds {kyc_level} per-transaction limit of ${limits['per_transaction']}",
            "current_level": kyc_level,
            "required_level": _get_required_level(amount)
        }
    
    # Check daily limit
    today = datetime.now(timezone.utc).date()
    today_transactions = [
        t for t in _TRANSACTION_HISTORY
        if t["username"] == username
        and datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00")).date() == today
    ]
    today_total = sum(t["amount"] for t in today_transactions)
    
    if today_total + amount > limits["daily"]:
        return {
            "ok": False,
            "blocked": True,
            "reason": f"Exceeds {kyc_level} daily limit of ${limits['daily']}",
            "used_today": round(today_total, 2),
            "available_today": round(limits["daily"] - today_total, 2)
        }
    
    # Check monthly limit
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
    month_transactions = [
        t for t in _TRANSACTION_HISTORY
        if t["username"] == username
        and datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00")) >= month_start
    ]
    month_total = sum(t["amount"] for t in month_transactions)
    
    if month_total + amount > limits["monthly"]:
        return {
            "ok": False,
            "blocked": True,
            "reason": f"Exceeds {kyc_level} monthly limit of ${limits['monthly']}",
            "used_this_month": round(month_total, 2),
            "available_this_month": round(limits["monthly"] - month_total, 2)
        }
    
    # AML checks
    aml_result = await _check_aml_patterns(username, transaction_type, amount, destination)
    
    if not aml_result["ok"]:
        return aml_result
    
    # Log transaction
    _TRANSACTION_HISTORY.append({
        "username": username,
        "type": transaction_type,
        "amount": amount,
        "destination": destination,
        "kyc_level": kyc_level,
        "timestamp": now_iso()
    })
    
    return {
        "ok": True,
        "allowed": True,
        "kyc_level": kyc_level,
        "remaining_daily": round(limits["daily"] - today_total - amount, 2),
        "remaining_monthly": round(limits["monthly"] - month_total - amount, 2)
    }


async def _check_aml_patterns(
    username: str,
    transaction_type: str,
    amount: float,
    destination: str
) -> Dict[str, Any]:
    """Check for AML red flags"""
    
    red_flags = []
    
    # Pattern 1: Structuring (multiple transactions just under reporting threshold)
    recent_24h = [
        t for t in _TRANSACTION_HISTORY
        if t["username"] == username
        and (datetime.now(timezone.utc) - datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00"))).total_seconds() < 86400
    ]
    
    if len(recent_24h) >= 3 and all(9000 <= t["amount"] < 10000 for t in recent_24h):
        red_flags.append("Possible structuring: Multiple transactions just below $10k threshold")
    
    # Pattern 2: Rapid movement (deposit and immediate withdrawal)
    if transaction_type == "withdrawal":
        recent_deposits = [
            t for t in _TRANSACTION_HISTORY
            if t["username"] == username
            and t["type"] == "deposit"
            and (datetime.now(timezone.utc) - datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00"))).total_seconds() < 3600
        ]
        
        if recent_deposits:
            red_flags.append("Rapid movement: Withdrawal shortly after deposit")
    
    # Pattern 3: Large unusual transaction
    past_transactions = [t for t in _TRANSACTION_HISTORY if t["username"] == username]
    
    if past_transactions:
        avg_amount = sum(t["amount"] for t in past_transactions) / len(past_transactions)
        
        if amount > avg_amount * 10:
            red_flags.append(f"Unusual amount: ${amount} vs avg ${avg_amount:.2f}")
    
    # If red flags found, file SAR
    if red_flags:
        await _file_sar(username, transaction_type, amount, red_flags)
        
        # Block if high risk
        if len(red_flags) >= 2:
            return {
                "ok": False,
                "blocked": True,
                "reason": "Transaction blocked for AML review",
                "red_flags": red_flags,
                "message": "Your transaction has been flagged for compliance review. Support will contact you."
            }
    
    return {"ok": True}


async def _file_sar(
    username: str,
    transaction_type: str,
    amount: float,
    red_flags: List[str]
) -> None:
    """File Suspicious Activity Report"""
    
    sar_id = f"sar_{uuid4().hex[:8]}"
    
    sar = {
        "id": sar_id,
        "username": username,
        "transaction_type": transaction_type,
        "amount": amount,
        "red_flags": red_flags,
        "status": "FILED",
        "filed_at": now_iso(),
        "reviewed_at": None
    }
    
    _SAR_REPORTS.append(sar)


def _get_required_level(amount: float) -> str:
    """Get required KYC level for amount"""
    if amount <= 50:
        return "NONE"
    elif amount <= 500:
        return "BASIC"
    elif amount <= 5000:
        return "VERIFIED"
    else:
        return "ENHANCED"


def _notify_kyc_status(
    username: str,
    status: str,
    level: str,
    reason: str = ""
) -> None:
    """Notify user of KYC status (async fire-and-forget)"""
    import asyncio
    
    async def notify():
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                message = f"Your {level} KYC verification has been {status}."
                if reason:
                    message += f"\n\nReason: {reason}"
                
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                    json={
                        "id": f"kyc_notif_{uuid4().hex[:8]}",
                        "sender": "system",
                        "recipient": username,
                        "title": f"KYC {status}",
                        "body": message,
                        "meta": {"kyc_level": level},
                        "status": "sent",
                        "timestamp": now_iso()
                    }
                )
            except Exception as e:
                print(f"Failed to notify user: {e}")
    
    try:
        asyncio.create_task(notify())
    except Exception:
        pass


def get_kyc_status(username: str) -> Dict[str, Any]:
    """Get user's KYC status"""
    kyc = _KYC_RECORDS.get(username)
    
    if not kyc:
        return {
            "ok": True,
            "username": username,
            "kyc_level": "NONE",
            "status": "NOT_SUBMITTED",
            "limits": LIMITS["NONE"]
        }
    
    return {
        "ok": True,
        "username": username,
        "kyc": kyc,
        "limits": LIMITS[kyc.get("level", "NONE")] if kyc.get("status") == "APPROVED" else LIMITS["NONE"]
    }


def list_pending_kyc() -> Dict[str, Any]:
    """List pending KYC submissions (admin)"""
    pending = [kyc for kyc in _KYC_RECORDS.values() if kyc["status"] == "PENDING"]
    pending.sort(key=lambda k: k["submitted_at"])
    
    return {"ok": True, "pending": pending, "count": len(pending)}


def list_sars(status: str = None) -> Dict[str, Any]:
    """List SARs (admin)"""
    sars = _SAR_REPORTS
    
    if status:
        sars = [s for s in sars if s["status"] == status.upper()]
    
    sars = sorted(sars, key=lambda s: s["filed_at"], reverse=True)
    
    return {"ok": True, "sars": sars, "count": len(sars)}


def get_compliance_stats() -> Dict[str, Any]:
    """Get compliance statistics"""
    
    total_kyc = len(_KYC_RECORDS)
    approved = len([k for k in _KYC_RECORDS.values() if k["status"] == "APPROVED"])
    pending = len([k for k in _KYC_RECORDS.values() if k["status"] == "PENDING"])
    rejected = len([k for k in _KYC_RECORDS.values() if k["status"] == "REJECTED"])
    
    by_level = {}
    for kyc in _KYC_RECORDS.values():
        if kyc["status"] == "APPROVED":
            level = kyc["level"]
            by_level[level] = by_level.get(level, 0) + 1
    
    return {
        "ok": True,
        "kyc": {
            "total": total_kyc,
            "approved": approved,
            "pending": pending,
            "rejected": rejected,
            "by_level": by_level
        },
        "sars": {
            "total": len(_SAR_REPORTS),
            "filed": len([s for s in _SAR_REPORTS if s["status"] == "FILED"])
        },
        "transactions": {
            "total": len(_TRANSACTION_HISTORY),
            "last_24h": len([
                t for t in _TRANSACTION_HISTORY
                if (datetime.now(timezone.utc) - datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00"))).total_seconds() < 86400
            ])
        }
    }
