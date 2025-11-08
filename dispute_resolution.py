from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import httpx

_DISPUTES: Dict[str, Dict[str, Any]] = {}
_ESCROW: Dict[str, float] = {}

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def file_dispute(
    claimant: str,
    respondent: str,
    dispute_type: str,
    amount_usd: float,
    description: str,
    evidence: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """File a dispute"""
    
    dispute_id = f"dispute_{uuid4().hex[:8]}"
    
    dispute = {
        "id": dispute_id,
        "claimant": claimant,
        "respondent": respondent,
        "dispute_type": dispute_type,
        "amount_usd": amount_usd,
        "description": description,
        "evidence": evidence or [],
        "status": "FILED",
        "stage": "NEGOTIATION",
        "filed_at": now_iso(),
        "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat() + "Z",
        "messages": [],
        "offers": [],
        "resolution": None,
        "events": [
            {"type": "DISPUTE_FILED", "by": claimant, "at": now_iso()}
        ]
    }
    
    _DISPUTES[dispute_id] = dispute
    
    # Place amount in escrow
    _ESCROW[dispute_id] = amount_usd
    
    # Notify respondent
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                json={
                    "id": f"dispute_notif_{uuid4().hex[:8]}",
                    "sender": "system",
                    "recipient": respondent,
                    "title": f"Dispute Filed: {dispute_type}",
                    "body": f"""{claimant} has filed a dispute against you.

Type: {dispute_type}
Amount: ${amount_usd}

Description: {description}

You have 7 days to respond. Funds are in escrow.

Dispute ID: {dispute_id}""",
                    "meta": {"dispute_id": dispute_id},
                    "status": "sent",
                    "timestamp": now_iso()
                }
            )
        except Exception as e:
            print(f"Failed to notify respondent: {e}")
    
    return {"ok": True, "dispute_id": dispute_id, "dispute": dispute}


def respond_to_dispute(
    dispute_id: str,
    respondent: str,
    response: str,
    counter_evidence: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Respond to a dispute"""
    
    dispute = _DISPUTES.get(dispute_id)
    
    if not dispute:
        return {"ok": False, "error": "dispute_not_found"}
    
    if dispute["respondent"] != respondent:
        return {"ok": False, "error": "not_respondent"}
    
    if dispute["status"] != "FILED":
        return {"ok": False, "error": f"dispute_already_{dispute['status'].lower()}"}
    
    # Add response
    dispute["response"] = response
    
    if counter_evidence:
        dispute["evidence"].extend(counter_evidence)
    
    dispute["status"] = "RESPONDED"
    dispute["events"].append({
        "type": "RESPONSE_SUBMITTED",
        "by": respondent,
        "at": now_iso()
    })
    
    return {"ok": True, "dispute": dispute, "message": "Response submitted, entering mediation"}


def make_settlement_offer(
    dispute_id: str,
    offerer: str,
    offer_type: str,
    offer_amount: float = None,
    offer_terms: str = ""
) -> Dict[str, Any]:
    """Make settlement offer"""
    
    dispute = _DISPUTES.get(dispute_id)
    
    if not dispute:
        return {"ok": False, "error": "dispute_not_found"}
    
    if offerer not in [dispute["claimant"], dispute["respondent"]]:
        return {"ok": False, "error": "not_party_to_dispute"}
    
    offer_id = f"offer_{uuid4().hex[:8]}"
    
    offer = {
        "id": offer_id,
        "offerer": offerer,
        "type": offer_type,
        "amount": offer_amount,
        "terms": offer_terms,
        "status": "PENDING",
        "created_at": now_iso(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat() + "Z"
    }
    
    dispute["offers"].append(offer)
    dispute["events"].append({
        "type": "SETTLEMENT_OFFER",
        "by": offerer,
        "offer_id": offer_id,
        "at": now_iso()
    })
    
    # Notify other party
    other_party = dispute["respondent"] if offerer == dispute["claimant"] else dispute["claimant"]
    
    return {
        "ok": True,
        "offer_id": offer_id,
        "offer": offer,
        "message": f"Settlement offer sent to {other_party}"
    }


async def accept_settlement(
    dispute_id: str,
    offer_id: str,
    accepter: str
) -> Dict[str, Any]:
    """Accept settlement offer"""
    
    dispute = _DISPUTES.get(dispute_id)
    
    if not dispute:
        return {"ok": False, "error": "dispute_not_found"}
    
    offer = next((o for o in dispute["offers"] if o["id"] == offer_id), None)
    
    if not offer:
        return {"ok": False, "error": "offer_not_found"}
    
    if offer["status"] != "PENDING":
        return {"ok": False, "error": f"offer_already_{offer['status'].lower()}"}
    
    # Mark offer accepted
    offer["status"] = "ACCEPTED"
    offer["accepted_by"] = accepter
    offer["accepted_at"] = now_iso()
    
    # Resolve dispute
    dispute["status"] = "SETTLED"
    dispute["resolution"] = {
        "type": "SETTLEMENT",
        "offer_id": offer_id,
        "amount": offer.get("amount"),
        "terms": offer.get("terms"),
        "resolved_at": now_iso()
    }
    
    # Release escrow
    escrow_amount = _ESCROW.get(dispute_id, 0)
    settlement_amount = offer.get("amount", 0)
    
    if settlement_amount and escrow_amount:
        # Distribute settlement
        await _distribute_settlement(
            dispute_id=dispute_id,
            claimant=dispute["claimant"],
            respondent=dispute["respondent"],
            claimant_amount=settlement_amount,
            respondent_amount=escrow_amount - settlement_amount
        )
    
    return {"ok": True, "dispute": dispute, "message": "Settlement accepted, dispute resolved"}


def escalate_to_arbitration(dispute_id: str) -> Dict[str, Any]:
    """Escalate dispute to arbitration"""
    
    dispute = _DISPUTES.get(dispute_id)
    
    if not dispute:
        return {"ok": False, "error": "dispute_not_found"}
    
    if dispute["status"] in ["SETTLED", "ARBITRATED"]:
        return {"ok": False, "error": "dispute_already_resolved"}
    
    dispute["stage"] = "ARBITRATION"
    dispute["status"] = "PENDING_ARBITRATION"
    dispute["events"].append({
        "type": "ESCALATED_TO_ARBITRATION",
        "at": now_iso()
    })
    
    return {
        "ok": True,
        "dispute": dispute,
        "message": "Dispute escalated to arbitration. Outcome oracle will review."
    }


async def arbitrate_dispute(
    dispute_id: str,
    ruling: str,
    claimant_award: float,
    respondent_award: float,
    rationale: str
) -> Dict[str, Any]:
    """Arbitrate dispute (admin/oracle only)"""
    
    dispute = _DISPUTES.get(dispute_id)
    
    if not dispute:
        return {"ok": False, "error": "dispute_not_found"}
    
    if dispute["status"] != "PENDING_ARBITRATION":
        return {"ok": False, "error": "not_in_arbitration"}
    
    # Record ruling
    dispute["status"] = "ARBITRATED"
    dispute["resolution"] = {
        "type": "ARBITRATION",
        "ruling": ruling,
        "claimant_award": claimant_award,
        "respondent_award": respondent_award,
        "rationale": rationale,
        "resolved_at": now_iso()
    }
    
    dispute["events"].append({
        "type": "ARBITRATION_COMPLETE",
        "at": now_iso()
    })
    
    # Distribute awards
    await _distribute_settlement(
        dispute_id=dispute_id,
        claimant=dispute["claimant"],
        respondent=dispute["respondent"],
        claimant_amount=claimant_award,
        respondent_amount=respondent_award
    )
    
    # Notify both parties
    async with httpx.AsyncClient(timeout=10) as client:
        for party, award in [(dispute["claimant"], claimant_award), (dispute["respondent"], respondent_award)]:
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                    json={
                        "id": f"arbitration_{uuid4().hex[:8]}",
                        "sender": "system",
                        "recipient": party,
                        "title": f"Arbitration Complete: {dispute_id}",
                        "body": f"""The arbitration is complete.

Ruling: {ruling}

Your Award: ${award}

Rationale: {rationale}

This decision is final and binding.""",
                        "meta": {"dispute_id": dispute_id},
                        "status": "sent",
                        "timestamp": now_iso()
                    }
                )
            except Exception as e:
                print(f"Failed to notify {party}: {e}")
    
    return {"ok": True, "dispute": dispute, "message": "Arbitration complete"}


async def _distribute_settlement(
    dispute_id: str,
    claimant: str,
    respondent: str,
    claimant_amount: float,
    respondent_amount: float
) -> None:
    """Distribute settlement from escrow"""
    
    async with httpx.AsyncClient(timeout=10) as client:
        # Credit claimant
        if claimant_amount > 0:
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                    json={
                        "username": claimant,
                        "amount": claimant_amount,
                        "basis": "dispute_settlement",
                        "ref": dispute_id
                    }
                )
            except Exception as e:
                print(f"Failed to credit claimant: {e}")
        
        # Credit respondent
        if respondent_amount > 0:
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                    json={
                        "username": respondent,
                        "amount": respondent_amount,
                        "basis": "dispute_settlement",
                        "ref": dispute_id
                    }
                )
            except Exception as e:
                print(f"Failed to credit respondent: {e}")
    
    # Release escrow
    if dispute_id in _ESCROW:
        del _ESCROW[dispute_id]


def get_dispute(dispute_id: str) -> Dict[str, Any]:
    """Get dispute details"""
    dispute = _DISPUTES.get(dispute_id)
    
    if not dispute:
        return {"ok": False, "error": "dispute_not_found"}
    
    return {"ok": True, "dispute": dispute}


def list_disputes(
    username: str = None,
    status: str = None
) -> Dict[str, Any]:
    """List disputes"""
    disputes = list(_DISPUTES.values())
    
    if username:
        disputes = [d for d in disputes if username in [d["claimant"], d["respondent"]]]
    
    if status:
        disputes = [d for d in disputes if d["status"] == status.upper()]
    
    disputes.sort(key=lambda d: d["filed_at"], reverse=True)
    
    return {"ok": True, "disputes": disputes, "count": len(disputes)}


def get_dispute_stats() -> Dict[str, Any]:
    """Get dispute statistics"""
    
    total = len(_DISPUTES)
    filed = len([d for d in _DISPUTES.values() if d["status"] == "FILED"])
    settled = len([d for d in _DISPUTES.values() if d["status"] == "SETTLED"])
    arbitrated = len([d for d in _DISPUTES.values() if d["status"] == "ARBITRATED"])
    
    total_escrow = sum(_ESCROW.values())
    
    return {
        "ok": True,
        "disputes": {
            "total": total,
            "filed": filed,
            "settled": settled,
            "arbitrated": arbitrated
        },
        "escrow_held": round(total_escrow, 2)
    }
