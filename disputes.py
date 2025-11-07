from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import httpx

_DISPUTES: Dict[str, Dict[str, Any]] = {}

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def open_dispute(
    intent_id: str,
    opener: str,
    reason: str,
    evidence_urls: List[str] = None,
    description: str = ""
) -> Dict[str, Any]:
    """Open a dispute on an intent"""
    
    dispute_id = f"disp_{uuid4().hex[:8]}"
    
    # Get intent details
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            intent_resp = await client.get(
                f"https://aigentsy-ame-runtime.onrender.com/intents/{intent_id}"
            )
            intent_data = intent_resp.json()
            intent = intent_data.get("intent", {})
            
            buyer = intent.get("from")
            agent = intent.get("claimed_by")
            escrow_usd = float(intent.get("escrow_usd", 0))
            
        except Exception as e:
            return {"ok": False, "error": f"failed to fetch intent: {e}"}
    
    # Determine dispute type
    if opener == buyer:
        dispute_type = "BUYER_DISPUTE"
        respondent = agent
    elif opener == agent:
        dispute_type = "AGENT_DISPUTE"
        respondent = buyer
    else:
        return {"ok": False, "error": "opener must be buyer or agent"}
    
    dispute = {
        "id": dispute_id,
        "intent_id": intent_id,
        "type": dispute_type,
        "opener": opener,
        "respondent": respondent,
        "reason": reason,
        "description": description,
        "evidence": {
            opener: evidence_urls or [],
            respondent: []
        },
        "status": "OPEN",
        "tier": "AUTO",
        "escrow_usd": escrow_usd,
        "opened_at": now_iso(),
        "response_deadline": (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat() + "Z",
        "resolution": None,
        "refund_pct": None,
        "events": [{"type": "DISPUTE_OPENED", "by": opener, "at": now_iso()}]
    }
    
    _DISPUTES[dispute_id] = dispute
    
    # Notify respondent
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                json={
                    "id": f"disp_notif_{uuid4().hex[:8]}",
                    "sender": "system",
                    "recipient": respondent,
                    "title": f"Dispute Opened: {reason}",
                    "body": f"""A dispute has been opened on intent {intent_id}.

Reason: {reason}
Description: {description}

You have 48 hours to respond with your evidence.

Dispute ID: {dispute_id}""",
                    "meta": {"dispute_id": dispute_id, "intent_id": intent_id},
                    "status": "sent",
                    "timestamp": now_iso()
                }
            )
        except Exception as e:
            print(f"Failed to notify respondent: {e}")
    
    # Update intent status
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/intents/dispute",
                json={"intent_id": intent_id, "reason": reason}
            )
        except Exception as e:
            print(f"Failed to update intent: {e}")
    
    return {"ok": True, "dispute_id": dispute_id, "dispute": dispute}


async def submit_evidence(
    dispute_id: str,
    party: str,
    evidence_urls: List[str],
    statement: str = ""
) -> Dict[str, Any]:
    """Party submits evidence to dispute"""
    
    dispute = _DISPUTES.get(dispute_id)
    if not dispute:
        return {"ok": False, "error": "dispute_not_found"}
    
    if dispute["status"] not in ["OPEN", "UNDER_REVIEW"]:
        return {"ok": False, "error": f"dispute is {dispute['status']}, cannot submit evidence"}
    
    if party not in [dispute["opener"], dispute["respondent"]]:
        return {"ok": False, "error": "party not involved in dispute"}
    
    # Add evidence
    dispute["evidence"][party] = evidence_urls
    dispute["events"].append({
        "type": "EVIDENCE_SUBMITTED",
        "by": party,
        "url_count": len(evidence_urls),
        "statement": statement,
        "at": now_iso()
    })
    
    # Check if both parties submitted
    opener_submitted = len(dispute["evidence"][dispute["opener"]]) > 0
    respondent_submitted = len(dispute["evidence"][dispute["respondent"]]) > 0
    
    if opener_submitted and respondent_submitted and dispute["tier"] == "AUTO":
        # Escalate to peer review
        dispute["tier"] = "PEER_REVIEW"
        dispute["status"] = "UNDER_REVIEW"
        dispute["events"].append({
            "type": "ESCALATED_TO_PEER_REVIEW",
            "at": now_iso()
        })
    
    return {"ok": True, "dispute": dispute}


async def auto_resolve_dispute(dispute_id: str) -> Dict[str, Any]:
    """Attempt automatic resolution based on evidence quality"""
    
    dispute = _DISPUTES.get(dispute_id)
    if not dispute:
        return {"ok": False, "error": "dispute_not_found"}
    
    if dispute["status"] != "UNDER_REVIEW":
        return {"ok": False, "error": "dispute not under review"}
    
    opener_evidence = len(dispute["evidence"][dispute["opener"]])
    respondent_evidence = len(dispute["evidence"][dispute["respondent"]])
    
    # Simple heuristic: more evidence = stronger case
    if opener_evidence > respondent_evidence * 2:
        refund_pct = 1.0  # Full refund to opener
    elif respondent_evidence > opener_evidence * 2:
        refund_pct = 0.0  # Full payment to respondent
    elif abs(opener_evidence - respondent_evidence) <= 1:
        refund_pct = 0.5  # Split 50/50
    else:
        # Escalate to admin
        dispute["tier"] = "ADMIN"
        dispute["events"].append({
            "type": "ESCALATED_TO_ADMIN",
            "reason": "auto_resolution_inconclusive",
            "at": now_iso()
        })
        return {"ok": True, "escalated": True, "dispute": dispute}
    
    # Apply resolution
    return await resolve_dispute(
        dispute_id=dispute_id,
        resolver="AUTO_SYSTEM",
        resolution=f"Auto-resolved based on evidence quality",
        refund_pct=refund_pct
    )


async def resolve_dispute(
    dispute_id: str,
    resolver: str,
    resolution: str,
    refund_pct: float
) -> Dict[str, Any]:
    """Admin or system resolves dispute"""
    
    dispute = _DISPUTES.get(dispute_id)
    if not dispute:
        return {"ok": False, "error": "dispute_not_found"}
    
    if dispute["status"] == "RESOLVED":
        return {"ok": False, "error": "dispute already resolved"}
    
    # Validate refund_pct
    if not (0.0 <= refund_pct <= 1.0):
        return {"ok": False, "error": "refund_pct must be between 0.0 and 1.0"}
    
    dispute["status"] = "RESOLVED"
    dispute["resolution"] = resolution
    dispute["refund_pct"] = refund_pct
    dispute["resolved_at"] = now_iso()
    dispute["resolved_by"] = resolver
    dispute["events"].append({
        "type": "DISPUTE_RESOLVED",
        "by": resolver,
        "refund_pct": refund_pct,
        "at": now_iso()
    })
    
    # Execute resolution via intent exchange
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/intents/resolve_dispute",
                json={
                    "intent_id": dispute["intent_id"],
                    "resolution": resolution,
                    "refund_pct": refund_pct
                }
            )
        except Exception as e:
            print(f"Failed to execute resolution: {e}")
    
    # Notify parties
    for party in [dispute["opener"], dispute["respondent"]]:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                json={
                    "id": f"disp_res_{uuid4().hex[:8]}",
                    "sender": "system",
                    "recipient": party,
                    "title": f"Dispute Resolved: {dispute['reason']}",
                    "body": f"""Your dispute has been resolved.

Resolution: {resolution}
Refund: {int(refund_pct * 100)}% to buyer

Dispute ID: {dispute_id}""",
                    "meta": {"dispute_id": dispute_id},
                    "status": "sent",
                    "timestamp": now_iso()
                }
            )
        except Exception as e:
            print(f"Failed to notify party: {e}")
    
    return {"ok": True, "dispute": dispute}


def get_dispute(dispute_id: str) -> Dict[str, Any]:
    """Get dispute details"""
    dispute = _DISPUTES.get(dispute_id)
    if not dispute:
        return {"ok": False, "error": "dispute_not_found"}
    return {"ok": True, "dispute": dispute}


def list_disputes(
    status: str = None,
    tier: str = None,
    party: str = None
) -> Dict[str, Any]:
    """List disputes with filters"""
    disputes = list(_DISPUTES.values())
    
    if status:
        disputes = [d for d in disputes if d["status"] == status.upper()]
    
    if tier:
        disputes = [d for d in disputes if d["tier"] == tier.upper()]
    
    if party:
        disputes = [d for d in disputes if party in [d["opener"], d["respondent"]]]
    
    disputes.sort(key=lambda x: x["opened_at"], reverse=True)
    
    return {"ok": True, "disputes": disputes, "count": len(disputes)}


def get_party_dispute_stats(party: str) -> Dict[str, Any]:
    """Get dispute statistics for a party"""
    party_disputes = [d for d in _DISPUTES.values() if party in [d["opener"], d["respondent"]]]
    
    total = len(party_disputes)
    opened = len([d for d in party_disputes if d["opener"] == party])
    responded = len([d for d in party_disputes if d["respondent"] == party])
    resolved = len([d for d in party_disputes if d["status"] == "RESOLVED"])
    
    # Win rate (disputes where party got favorable outcome)
    wins = 0
    for d in party_disputes:
        if d["status"] == "RESOLVED" and d["refund_pct"] is not None:
            if d["opener"] == party and d["refund_pct"] >= 0.5:
                wins += 1
            elif d["respondent"] == party and d["refund_pct"] < 0.5:
                wins += 1
    
    win_rate = round(wins / resolved * 100, 1) if resolved > 0 else 0.0
    
    return {
        "ok": True,
        "party": party,
        "stats": {
            "total": total,
            "opened": opened,
            "responded": responded,
            "resolved": resolved,
            "win_rate": win_rate
        }
    }
