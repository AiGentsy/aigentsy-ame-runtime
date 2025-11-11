"""
AiGentsy Real-World Proof Pipe
POS/Booking integration for physical + digital unified outcomes
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4
import hashlib

def _now():
    return datetime.now(timezone.utc).isoformat()


# Proof types
PROOF_TYPES = {
    "pos_receipt": {
        "name": "POS Receipt",
        "description": "Point-of-sale transaction receipt",
        "sources": ["square", "stripe_terminal", "clover"],
        "required_fields": ["transaction_id", "amount", "timestamp", "merchant_id"],
        "icon": "🧾"
    },
    "booking_confirmation": {
        "name": "Booking Confirmation",
        "description": "Service booking confirmation",
        "sources": ["calendly", "acuity", "booking_com"],
        "required_fields": ["booking_id", "service", "timestamp", "duration"],
        "icon": "📅"
    },
    "delivery_signature": {
        "name": "Delivery Signature",
        "description": "Physical delivery confirmation",
        "sources": ["manual", "ups", "fedex"],
        "required_fields": ["delivery_id", "recipient", "timestamp", "signature"],
        "icon": "✍️"
    },
    "completion_photo": {
        "name": "Completion Photo",
        "description": "Visual proof of work completion",
        "sources": ["manual"],
        "required_fields": ["photo_url", "timestamp", "location"],
        "icon": "📸"
    },
    "invoice_paid": {
        "name": "Invoice Paid",
        "description": "Invoice payment confirmation",
        "sources": ["quickbooks", "xero", "freshbooks"],
        "required_fields": ["invoice_id", "amount", "paid_at"],
        "icon": "💳"
    }
}

# Outcome event types
OUTCOME_EVENTS = {
    "PAID_POS": "Payment received via POS",
    "DELIVERED_SERVICE": "Service delivered and confirmed",
    "BOOKING_COMPLETED": "Booking attended and completed",
    "WORK_VERIFIED": "Work verified with proof",
    "INVOICE_SETTLED": "Invoice payment received"
}


def create_proof(
    proof_type: str,
    source: str,
    agent_username: str,
    job_id: str = None,
    deal_id: str = None,
    proof_data: Dict[str, Any] = None,
    attachment_url: str = None
) -> Dict[str, Any]:
    """
    Create a proof record
    """
    if proof_type not in PROOF_TYPES:
        return {
            "ok": False,
            "error": "invalid_proof_type",
            "valid_types": list(PROOF_TYPES.keys())
        }
    
    proof_config = PROOF_TYPES[proof_type]
    
    # Validate source
    if source not in proof_config["sources"]:
        return {
            "ok": False,
            "error": "invalid_source",
            "valid_sources": proof_config["sources"]
        }
    
    # Validate required fields
    if proof_data:
        missing_fields = [
            field for field in proof_config["required_fields"]
            if field not in proof_data
        ]
        
        if missing_fields:
            return {
                "ok": False,
                "error": "missing_required_fields",
                "missing": missing_fields
            }
    
    proof_id = f"proof_{uuid4().hex[:12]}"
    
    # Generate proof hash for verification
    proof_string = f"{proof_type}:{source}:{agent_username}:{proof_data}"
    proof_hash = hashlib.sha256(proof_string.encode()).hexdigest()[:16]
    
    proof = {
        "id": proof_id,
        "type": proof_type,
        "source": source,
        "agent": agent_username,
        "job_id": job_id,
        "deal_id": deal_id,
        "proof_data": proof_data or {},
        "attachment_url": attachment_url,
        "proof_hash": proof_hash,
        "verified": False,
        "verified_at": None,
        "created_at": _now(),
        "status": "pending_verification"
    }
    
    return {
        "ok": True,
        "proof": proof
    }


def process_square_webhook(
    webhook_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process Square POS webhook
    
    Expected webhook payload from Square:
    {
        "merchant_id": "...",
        "type": "payment.created",
        "data": {
            "object": {
                "payment": {
                    "id": "...",
                    "amount_money": {"amount": 5000, "currency": "USD"},
                    "created_at": "...",
                    "receipt_url": "..."
                }
            }
        }
    }
    """
    event_type = webhook_payload.get("type")
    
    if event_type != "payment.created":
        return {
            "ok": False,
            "error": "unsupported_event_type",
            "type": event_type
        }
    
    payment = webhook_payload.get("data", {}).get("object", {}).get("payment", {})
    
    transaction_id = payment.get("id")
    amount_money = payment.get("amount_money", {})
    amount = amount_money.get("amount", 0) / 100  # Square uses cents
    currency = amount_money.get("currency", "USD")
    timestamp = payment.get("created_at")
    receipt_url = payment.get("receipt_url")
    merchant_id = webhook_payload.get("merchant_id")
    
    proof_data = {
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": currency,
        "timestamp": timestamp,
        "merchant_id": merchant_id,
        "receipt_url": receipt_url
    }
    
    return {
        "ok": True,
        "event": "PAID_POS",
        "proof_type": "pos_receipt",
        "source": "square",
        "proof_data": proof_data,
        "amount": amount,
        "currency": currency
    }


def process_calendly_webhook(
    webhook_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process Calendly booking webhook
    
    Expected webhook payload from Calendly:
    {
        "event": "invitee.created",
        "payload": {
            "event": {
                "uuid": "...",
                "name": "30 Minute Meeting"
            },
            "invitee": {
                "uuid": "...",
                "email": "...",
                "name": "..."
            },
            "scheduled_event": {
                "start_time": "...",
                "end_time": "...",
                "status": "active"
            }
        }
    }
    """
    event_type = webhook_payload.get("event")
    
    if event_type not in ["invitee.created", "invitee.canceled"]:
        return {
            "ok": False,
            "error": "unsupported_event_type",
            "type": event_type
        }
    
    payload = webhook_payload.get("payload", {})
    
    event_data = payload.get("event", {})
    scheduled_event = payload.get("scheduled_event", {})
    invitee = payload.get("invitee", {})
    
    booking_id = event_data.get("uuid")
    service = event_data.get("name")
    start_time = scheduled_event.get("start_time")
    end_time = scheduled_event.get("end_time")
    status = scheduled_event.get("status")
    
    # Calculate duration
    if start_time and end_time:
        from datetime import datetime
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        duration_minutes = int((end - start).total_seconds() / 60)
    else:
        duration_minutes = 0
    
    proof_data = {
        "booking_id": booking_id,
        "service": service,
        "timestamp": start_time,
        "duration": duration_minutes,
        "status": status,
        "invitee_email": invitee.get("email")
    }
    
    outcome_event = "BOOKING_COMPLETED" if event_type == "invitee.created" else "BOOKING_CANCELLED"
    
    return {
        "ok": True,
        "event": outcome_event,
        "proof_type": "booking_confirmation",
        "source": "calendly",
        "proof_data": proof_data,
        "duration_minutes": duration_minutes
    }


def verify_proof(
    proof: Dict[str, Any],
    verifier: str = "system"
) -> Dict[str, Any]:
    """
    Verify a proof record
    """
    if proof.get("verified"):
        return {
            "ok": False,
            "error": "already_verified",
            "verified_at": proof.get("verified_at")
        }
    
    # In production, would perform actual verification:
    # - Check receipt against payment processor API
    # - Verify booking exists in calendar system
    # - Validate signature authenticity
    # For now, auto-verify
    
    proof["verified"] = True
    proof["verified_at"] = _now()
    proof["verified_by"] = verifier
    proof["status"] = "verified"
    
    return {
        "ok": True,
        "proof_id": proof["id"],
        "verified": True,
        "verified_at": proof["verified_at"]
    }


def create_outcome_from_proof(
    proof: Dict[str, Any],
    agent_user: Dict[str, Any],
    outcome_event: str
) -> Dict[str, Any]:
    """
    Create outcome record from verified proof
    """
    if not proof.get("verified"):
        return {
            "ok": False,
            "error": "proof_not_verified",
            "proof_id": proof["id"]
        }
    
    if outcome_event not in OUTCOME_EVENTS:
        return {
            "ok": False,
            "error": "invalid_outcome_event",
            "valid_events": list(OUTCOME_EVENTS.keys())
        }
    
    outcome_id = f"outcome_{uuid4().hex[:12]}"
    
    outcome = {
        "id": outcome_id,
        "agent": proof["agent"],
        "event": outcome_event,
        "proof_id": proof["id"],
        "proof_type": proof["type"],
        "proof_source": proof["source"],
        "job_id": proof.get("job_id"),
        "deal_id": proof.get("deal_id"),
        "created_at": _now(),
        "metadata": proof.get("proof_data", {})
    }
    
    # Update agent's outcome score
    current_score = int(agent_user.get("outcomeScore", 0))
    
    # Different proof types have different score impacts
    score_impact = {
        "PAID_POS": 5,
        "DELIVERED_SERVICE": 3,
        "BOOKING_COMPLETED": 2,
        "WORK_VERIFIED": 4,
        "INVOICE_SETTLED": 3
    }
    
    score_increase = score_impact.get(outcome_event, 1)
    new_score = min(100, current_score + score_increase)
    
    agent_user["outcomeScore"] = new_score
    
    # Add to ledger
    agent_user.setdefault("ownership", {}).setdefault("ledger", []).append({
        "ts": _now(),
        "amount": 0,  # No direct payment, just proof
        "currency": "N/A",
        "basis": "outcome_verified",
        "outcome_id": outcome_id,
        "outcome_event": outcome_event,
        "proof_id": proof["id"],
        "score_increase": score_increase
    })
    
    return {
        "ok": True,
        "outcome": outcome,
        "score_increase": score_increase,
        "new_score": new_score
    }


def get_agent_proofs(
    agent_username: str,
    proofs: List[Dict[str, Any]],
    verified_only: bool = False
) -> Dict[str, Any]:
    """
    Get all proofs for an agent
    """
    agent_proofs = [p for p in proofs if p.get("agent") == agent_username]
    
    if verified_only:
        agent_proofs = [p for p in agent_proofs if p.get("verified")]
    
    # Count by type
    by_type = {}
    for proof in agent_proofs:
        proof_type = proof.get("type")
        by_type[proof_type] = by_type.get(proof_type, 0) + 1
    
    # Count by source
    by_source = {}
    for proof in agent_proofs:
        source = proof.get("source")
        by_source[source] = by_source.get(source, 0) + 1
    
    return {
        "agent": agent_username,
        "total_proofs": len(agent_proofs),
        "verified_proofs": len([p for p in agent_proofs if p.get("verified")]),
        "proofs_by_type": by_type,
        "proofs_by_source": by_source,
        "proofs": agent_proofs
    }


def attach_proof_to_deal(
    proof: Dict[str, Any],
    deal: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Attach proof to a DealGraph entry
    """
    if not proof.get("verified"):
        return {
            "ok": False,
            "error": "proof_must_be_verified",
            "proof_id": proof["id"]
        }
    
    # Add proof reference to deal
    deal.setdefault("proofs", []).append({
        "proof_id": proof["id"],
        "proof_type": proof["type"],
        "source": proof["source"],
        "attached_at": _now()
    })
    
    # Update proof with deal reference
    proof["deal_id"] = deal["id"]
    
    return {
        "ok": True,
        "deal_id": deal["id"],
        "proof_id": proof["id"],
        "attached": True
    }


def generate_proof_report(
    proofs: List[Dict[str, Any]],
    start_date: str = None,
    end_date: str = None
) -> Dict[str, Any]:
    """
    Generate proof verification report
    """
    filtered_proofs = proofs
    
    # Filter by date range if provided
    if start_date:
        filtered_proofs = [p for p in filtered_proofs if p.get("created_at", "") >= start_date]
    
    if end_date:
        filtered_proofs = [p for p in filtered_proofs if p.get("created_at", "") <= end_date]
    
    total_proofs = len(filtered_proofs)
    verified_proofs = len([p for p in filtered_proofs if p.get("verified")])
    pending_proofs = total_proofs - verified_proofs
    
    verification_rate = (verified_proofs / total_proofs) if total_proofs > 0 else 0
    
    # Top agents by proof count
    agent_counts = {}
    for proof in filtered_proofs:
        agent = proof.get("agent")
        agent_counts[agent] = agent_counts.get(agent, 0) + 1
    
    top_agents = sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Proofs by type
    type_counts = {}
    for proof in filtered_proofs:
        proof_type = proof.get("type")
        type_counts[proof_type] = type_counts.get(proof_type, 0) + 1
    
    # Proofs by source
    source_counts = {}
    for proof in filtered_proofs:
        source = proof.get("source")
        source_counts[source] = source_counts.get(source, 0) + 1
    
    return {
        "report_period": {
            "start": start_date,
            "end": end_date
        },
        "total_proofs": total_proofs,
        "verified_proofs": verified_proofs,
        "pending_proofs": pending_proofs,
        "verification_rate": round(verification_rate, 2),
        "proofs_by_type": type_counts,
        "proofs_by_source": source_counts,
        "top_agents": [{"agent": a, "proof_count": c} for a, c in top_agents],
        "generated_at": _now()
    }
