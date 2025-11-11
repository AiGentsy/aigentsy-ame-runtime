"""
AiGentsy State-Driven Money
Production-safe escrow bound to DealGraph states with webhook idempotency
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import hashlib

def _now():
    return datetime.now(timezone.utc).isoformat()

def _parse_iso(ts_iso: str) -> datetime:
    try:
        return datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
    except:
        return datetime.now(timezone.utc)


# State transition rules
STATE_TRANSITIONS = {
    "ACCEPTED": {
        "money_action": "authorize",
        "next_states": ["ESCROW_HELD", "CANCELLED"]
    },
    "ESCROW_HELD": {
        "money_action": "hold",
        "next_states": ["BONDS_STAKED", "CANCELLED"]
    },
    "BONDS_STAKED": {
        "money_action": "locked",
        "next_states": ["IN_PROGRESS"]
    },
    "IN_PROGRESS": {
        "money_action": "locked",
        "next_states": ["DELIVERED", "DISPUTED", "TIMEOUT"]
    },
    "DELIVERED": {
        "money_action": "capture",
        "next_states": ["COMPLETED", "DISPUTED"]
    },
    "DISPUTED": {
        "money_action": "pause",
        "next_states": ["COMPLETED", "REFUNDED"]
    },
    "TIMEOUT": {
        "money_action": "auto_release",
        "next_states": ["COMPLETED", "DISPUTED"]
    },
    "COMPLETED": {
        "money_action": "settled",
        "next_states": []
    },
    "REFUNDED": {
        "money_action": "refunded",
        "next_states": []
    },
    "CANCELLED": {
        "money_action": "void",
        "next_states": []
    }
}

# Timeout rules
TIMEOUT_RULES = {
    "default_timeout_hours": 168,  # 7 days default
    "require_poo_for_release": True,
    "grace_period_hours": 24,
    "auto_release_enabled": True
}


def generate_idempotency_key(
    deal_id: str,
    action: str,
    timestamp: str = None
) -> str:
    """
    Generate idempotency key for Stripe operations
    """
    if not timestamp:
        timestamp = _now()
    
    # Truncate timestamp to second precision safely
    ts_truncated = timestamp[:19] if len(timestamp) >= 19 else timestamp
    
    # Create deterministic hash
    key_input = f"{deal_id}:{action}:{ts_truncated}"
    key_hash = hashlib.sha256(key_input.encode()).hexdigest()[:32]
    
    return f"aigentsy_{deal_id}_{action}_{key_hash}"


def validate_state_transition(
    current_state: str,
    new_state: str
) -> Dict[str, Any]:
    """
    Validate if state transition is allowed
    """
    if current_state not in STATE_TRANSITIONS:
        return {
            "valid": False,
            "error": "invalid_current_state",
            "current_state": current_state
        }
    
    allowed_next = STATE_TRANSITIONS[current_state]["next_states"]
    
    if new_state not in allowed_next:
        return {
            "valid": False,
            "error": "invalid_transition",
            "current_state": current_state,
            "attempted_state": new_state,
            "allowed_states": allowed_next
        }
    
    return {
        "valid": True,
        "current_state": current_state,
        "new_state": new_state,
        "money_action": STATE_TRANSITIONS[new_state].get("money_action")
    }


def record_money_event(
    deal: Dict[str, Any],
    event_type: str,
    payment_intent_id: str = None,
    amount: float = None,
    idempotency_key: str = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Record money event with idempotency tracking
    """
    event_id = f"evt_{hashlib.sha256(f"{deal['id']}:{event_type}:{_now()}".encode()).hexdigest()[:12]}"
    
    # Check for duplicate events (idempotency)
    existing_events = deal.setdefault("money_events", [])
    
    if idempotency_key:
        duplicate = next(
            (e for e in existing_events if e.get("idempotency_key") == idempotency_key),
            None
        )
        
        if duplicate:
            return {
                "ok": False,
                "error": "duplicate_event",
                "idempotency_key": idempotency_key,
                "existing_event": duplicate,
                "message": "Event already processed - idempotency check passed"
            }
    
    # Record event
    event = {
        "id": event_id,
        "type": event_type,
        "payment_intent_id": payment_intent_id,
        "amount": amount,
        "idempotency_key": idempotency_key,
        "metadata": metadata or {},
        "state_at_event": deal.get("state"),
        "created_at": _now()
    }
    
    existing_events.append(event)
    
    return {
        "ok": True,
        "event": event,
        "is_duplicate": False
    }


def authorize_payment(
    deal: Dict[str, Any],
    payment_intent_id: str,
    amount: float
) -> Dict[str, Any]:
    """
    Authorize payment (Stripe payment intent)
    """
    # Validate state
    if deal["state"] != "ACCEPTED":
        return {
            "ok": False,
            "error": "invalid_state_for_authorize",
            "current_state": deal["state"],
            "required_state": "ACCEPTED"
        }
    
    # Generate idempotency key
    idempotency_key = generate_idempotency_key(deal["id"], "authorize")
    
    # Record event
    event_result = record_money_event(
        deal,
        "PAYMENT_AUTHORIZED",
        payment_intent_id,
        amount,
        idempotency_key
    )
    
    if not event_result["ok"]:
        return event_result  # Duplicate detected
    
    # Update escrow tracking
    deal["escrow"]["status"] = "authorized"
    deal["escrow"]["amount"] = amount
    deal["escrow"]["payment_intent_id"] = payment_intent_id
    deal["escrow"]["authorized_at"] = _now()
    deal["escrow"]["idempotency_key"] = idempotency_key
    
    return {
        "ok": True,
        "action": "authorized",
        "payment_intent_id": payment_intent_id,
        "amount": round(amount, 2),
        "idempotency_key": idempotency_key,
        "event": event_result["event"]
    }


def capture_payment(
    deal: Dict[str, Any],
    capture_amount: float = None
) -> Dict[str, Any]:
    """
    Capture payment (when delivered)
    """
    # Validate state
    if deal["state"] != "DELIVERED":
        return {
            "ok": False,
            "error": "invalid_state_for_capture",
            "current_state": deal["state"],
            "required_state": "DELIVERED"
        }
    
    # Check escrow
    if deal["escrow"]["status"] != "authorized":
        return {
            "ok": False,
            "error": "payment_not_authorized",
            "escrow_status": deal["escrow"]["status"]
        }
    
    payment_intent_id = deal["escrow"]["payment_intent_id"]
    authorized_amount = deal["escrow"]["amount"]
    
    # Use authorized amount if not specified
    if not capture_amount:
        capture_amount = authorized_amount
    
    # Validate amount
    if capture_amount > authorized_amount:
        return {
            "ok": False,
            "error": "capture_exceeds_authorization",
            "authorized": authorized_amount,
            "attempted": capture_amount
        }
    
    # Generate idempotency key
    idempotency_key = generate_idempotency_key(deal["id"], "capture")
    
    # Record event
    event_result = record_money_event(
        deal,
        "PAYMENT_CAPTURED",
        payment_intent_id,
        capture_amount,
        idempotency_key
    )
    
    if not event_result["ok"]:
        return event_result  # Duplicate detected
    
    # Update escrow
    deal["escrow"]["status"] = "captured"
    deal["escrow"]["captured_amount"] = capture_amount
    deal["escrow"]["captured_at"] = _now()
    deal["escrow"]["capture_idempotency_key"] = idempotency_key
    
    return {
        "ok": True,
        "action": "captured",
        "payment_intent_id": payment_intent_id,
        "captured_amount": round(capture_amount, 2),
        "idempotency_key": idempotency_key,
        "event": event_result["event"]
    }


def pause_on_dispute(
    deal: Dict[str, Any],
    dispute_reason: str = ""
) -> Dict[str, Any]:
    """
    Pause money flow when dispute raised
    """
    # Validate state
    if deal["state"] not in ["IN_PROGRESS", "DELIVERED"]:
        return {
            "ok": False,
            "error": "invalid_state_for_dispute",
            "current_state": deal["state"]
        }
    
    # Generate idempotency key
    idempotency_key = generate_idempotency_key(deal["id"], "dispute_pause")
    
    # Record event
    event_result = record_money_event(
        deal,
        "PAYMENT_PAUSED_DISPUTE",
        deal["escrow"].get("payment_intent_id"),
        metadata={"dispute_reason": dispute_reason},
        idempotency_key=idempotency_key
    )
    
    if not event_result["ok"]:
        return event_result
    
    # Update escrow
    deal["escrow"]["status"] = "paused_dispute"
    deal["escrow"]["paused_at"] = _now()
    deal["escrow"]["pause_reason"] = dispute_reason
    
    # Add dispute tracking
    deal.setdefault("dispute", {})
    deal["dispute"]["status"] = "active"
    deal["dispute"]["raised_at"] = _now()
    deal["dispute"]["reason"] = dispute_reason
    
    return {
        "ok": True,
        "action": "paused",
        "reason": dispute_reason,
        "payment_paused": True,
        "event": event_result["event"]
    }


def check_timeout(
    deal: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check if deal has timed out
    """
    if deal["state"] != "IN_PROGRESS":
        return {
            "timed_out": False,
            "reason": "not_in_progress",
            "current_state": deal["state"]
        }
    
    # Get timeout rules
    sla_terms = deal.get("sla_terms", {})
    timeout_hours = sla_terms.get("timeout_hours", TIMEOUT_RULES["default_timeout_hours"])
    
    # Check deadline
    deadline = deal["delivery"].get("deadline")
    if not deadline:
        return {
            "timed_out": False,
            "reason": "no_deadline_set"
        }
    
    deadline_dt = _parse_iso(deadline)
    grace_period = timedelta(hours=TIMEOUT_RULES["grace_period_hours"])
    timeout_threshold = deadline_dt + grace_period
    
    now = datetime.now(timezone.utc)
    
    if now > timeout_threshold:
        hours_overdue = (now - timeout_threshold).total_seconds() / 3600
        
        return {
            "timed_out": True,
            "deadline": deadline,
            "grace_period_hours": TIMEOUT_RULES["grace_period_hours"],
            "hours_overdue": round(hours_overdue, 1),
            "timeout_threshold": timeout_threshold.isoformat()
        }
    
    return {
        "timed_out": False,
        "deadline": deadline,
        "hours_remaining": round((timeout_threshold - now).total_seconds() / 3600, 1)
    }


def auto_release_on_timeout(
    deal: Dict[str, Any],
    proof_verified: bool = False
) -> Dict[str, Any]:
    """
    Auto-release payment on timeout (with optional PoO verification)
    """
    # Check timeout
    timeout_check = check_timeout(deal)
    
    if not timeout_check.get("timed_out"):
        return {
            "ok": False,
            "error": "not_timed_out",
            "timeout_check": timeout_check
        }
    
    # Check if PoO required
    require_poo = TIMEOUT_RULES["require_poo_for_release"]
    
    if require_poo and not proof_verified:
        return {
            "ok": False,
            "error": "poo_verification_required",
            "message": "Proof-of-Outcome required for auto-release on timeout"
        }
    
    # Generate idempotency key
    idempotency_key = generate_idempotency_key(deal["id"], "auto_release")
    
    # Record event
    event_result = record_money_event(
        deal,
        "PAYMENT_AUTO_RELEASED",
        deal["escrow"].get("payment_intent_id"),
        deal["escrow"].get("amount"),
        idempotency_key,
        metadata={
            "timeout_hours": timeout_check.get("hours_overdue"),
            "proof_verified": proof_verified
        }
    )
    
    if not event_result["ok"]:
        return event_result
    
    # Trigger capture
    capture_result = capture_payment(deal)
    
    if not capture_result["ok"]:
        return capture_result
    
    # Update deal state
    deal["state"] = "TIMEOUT"
    deal["timeout_released"] = True
    deal["timeout_released_at"] = _now()
    
    return {
        "ok": True,
        "action": "auto_released",
        "reason": "timeout_with_poo" if proof_verified else "timeout",
        "hours_overdue": timeout_check.get("hours_overdue"),
        "proof_verified": proof_verified,
        "captured": True,
        "event": event_result["event"]
    }


def void_authorization(
    deal: Dict[str, Any],
    reason: str = "cancelled"
) -> Dict[str, Any]:
    """
    Void authorization (when deal cancelled)
    """
    if deal["escrow"]["status"] != "authorized":
        return {
            "ok": False,
            "error": "cannot_void_non_authorized",
            "escrow_status": deal["escrow"]["status"]
        }
    
    # Generate idempotency key
    idempotency_key = generate_idempotency_key(deal["id"], "void")
    
    # Record event
    event_result = record_money_event(
        deal,
        "PAYMENT_VOIDED",
        deal["escrow"].get("payment_intent_id"),
        metadata={"reason": reason},
        idempotency_key=idempotency_key
    )
    
    if not event_result["ok"]:
        return event_result
    
    # Update escrow
    deal["escrow"]["status"] = "voided"
    deal["escrow"]["voided_at"] = _now()
    deal["escrow"]["void_reason"] = reason
    
    return {
        "ok": True,
        "action": "voided",
        "reason": reason,
        "event": event_result["event"]
    }


def process_webhook(
    webhook_payload: Dict[str, Any],
    deal: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process Stripe webhook with idempotency
    """
    event_type = webhook_payload.get("type")
    event_id = webhook_payload.get("id")
    
    # Check for duplicate webhook
    processed_webhooks = deal.setdefault("processed_webhooks", [])
    
    if event_id in processed_webhooks:
        return {
            "ok": False,
            "error": "webhook_already_processed",
            "event_id": event_id,
            "message": "Webhook idempotency check - already processed"
        }
    
    # Process based on type
    result = {"ok": False, "error": "unhandled_event_type"}
    
    if event_type == "payment_intent.succeeded":
        # Payment authorized successfully
        result = {
            "ok": True,
            "action": "payment_authorized",
            "message": "Payment intent succeeded"
        }
    
    elif event_type == "payment_intent.payment_failed":
        result = {
            "ok": True,
            "action": "payment_failed",
            "message": "Payment authorization failed"
        }
    
    elif event_type == "charge.captured":
        result = {
            "ok": True,
            "action": "payment_captured",
            "message": "Payment captured successfully"
        }
    
    elif event_type == "charge.refunded":
        result = {
            "ok": True,
            "action": "payment_refunded",
            "message": "Payment refunded"
        }
    
    # Mark webhook as processed
    processed_webhooks.append(event_id)
    
    # Record in money events
    record_money_event(
        deal,
        f"WEBHOOK_{event_type.upper()}",
        webhook_payload.get("data", {}).get("object", {}).get("id"),
        metadata={"webhook_id": event_id}
    )
    
    return result


def get_money_timeline(
    deal: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get complete money event timeline for a deal
    """
    money_events = deal.get("money_events", [])
    
    # Sort by timestamp
    timeline = sorted(money_events, key=lambda e: e.get("created_at", ""))
    
    # Calculate totals
    total_authorized = sum([
        e.get("amount", 0) for e in money_events 
        if e.get("type") == "PAYMENT_AUTHORIZED"
    ])
    
    total_captured = sum([
        e.get("amount", 0) for e in money_events 
        if e.get("type") == "PAYMENT_CAPTURED"
    ])
    
    return {
        "deal_id": deal["id"],
        "current_state": deal["state"],
        "escrow_status": deal["escrow"].get("status"),
        "total_events": len(money_events),
        "total_authorized": round(total_authorized, 2),
        "total_captured": round(total_captured, 2),
        "timeline": timeline,
        "processed_webhooks": deal.get("processed_webhooks", [])
    }
