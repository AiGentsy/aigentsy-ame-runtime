"""
AME Pitch Queue - Approval workflow for autonomous outreach
Sits between pitch generation and AAM execution
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

# In-memory store (replace with DB/JSONBin in production)
_pitch_queue: Dict[str, Dict[str, Any]] = {}
_pitch_stats: Dict[str, int] = {
    "generated": 0,
    "approved": 0,
    "skipped": 0,
    "sent": 0,
    "opened": 0,
    "responded": 0,
    "converted": 0
}

def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _uuid() -> str:
    return str(uuid.uuid4())


# ========== Pitch Generation ==========

def generate_pitch(
    recipient: str,
    channel: str,
    context: Dict[str, Any],
    originator: str = "system"
) -> Dict[str, Any]:
    """
    Generate a pitch and add to approval queue.
    Does NOT send - waits for approval.
    
    Args:
        recipient: Target username/email/handle
        channel: "email" | "dm" | "linkedin" | "fiverr" | "webhook"
        context: Match data, offer details, personalization
        originator: Who/what triggered the pitch
    
    Returns:
        Pitch object with status "pending"
    """
    pitch_id = _uuid()
    
    # Build pitch message (customize based on channel/context)
    message = _build_pitch_message(recipient, channel, context)
    
    pitch = {
        "id": pitch_id,
        "status": "pending",
        "recipient": recipient,
        "channel": channel,
        "message": message,
        "context": context,
        "originator": originator,
        "created_at": _now(),
        "updated_at": _now(),
        "approved_at": None,
        "sent_at": None,
        "opened_at": None,
        "responded_at": None
    }
    
    _pitch_queue[pitch_id] = pitch
    _pitch_stats["generated"] += 1
    
    return pitch


def _build_pitch_message(recipient: str, channel: str, context: Dict[str, Any]) -> str:
    """
    Build personalized pitch message based on context.
    Override this with your AI-generated copy.
    """
    offer = context.get("offer", "our services")
    match_reason = context.get("match_reason", "your profile matches what we offer")
    
    # Channel-specific formatting
    if channel == "email":
        return f"""Subject: Quick question about {offer}

Hi {recipient},

I noticed {match_reason} and thought you might be interested.

Would you be open to a quick chat this week?

Best,
AiGentsy"""
    
    elif channel in ("dm", "linkedin", "fiverr"):
        return f"""Hi {recipient}! 👋

{match_reason}

I think {offer} could be a great fit. Open to connecting?"""
    
    else:
        return f"""Pitch to {recipient}: {offer} - {match_reason}"""


# ========== Queue Management ==========

def get_pending_pitches(limit: int = 20) -> List[Dict[str, Any]]:
    """Get all pending pitches awaiting approval."""
    pending = [p for p in _pitch_queue.values() if p["status"] == "pending"]
    # Sort by created_at (oldest first)
    pending.sort(key=lambda x: x["created_at"])
    return pending[:limit]


def get_pitch(pitch_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific pitch by ID."""
    return _pitch_queue.get(pitch_id)


def approve_pitch(pitch_id: str) -> Dict[str, Any]:
    """
    Approve a pitch for sending.
    Returns the pitch ready for execution.
    """
    pitch = _pitch_queue.get(pitch_id)
    if not pitch:
        return {"ok": False, "error": "pitch_not_found"}
    
    if pitch["status"] != "pending":
        return {"ok": False, "error": f"pitch_already_{pitch['status']}"}
    
    pitch["status"] = "approved"
    pitch["approved_at"] = _now()
    pitch["updated_at"] = _now()
    _pitch_stats["approved"] += 1
    
    # Execute the send
    result = _execute_pitch(pitch)
    
    return {"ok": True, "pitch": pitch, "send_result": result}


def skip_pitch(pitch_id: str, reason: str = "") -> Dict[str, Any]:
    """
    Skip/dismiss a pitch without sending.
    """
    pitch = _pitch_queue.get(pitch_id)
    if not pitch:
        return {"ok": False, "error": "pitch_not_found"}
    
    if pitch["status"] != "pending":
        return {"ok": False, "error": f"pitch_already_{pitch['status']}"}
    
    pitch["status"] = "skipped"
    pitch["skip_reason"] = reason
    pitch["updated_at"] = _now()
    _pitch_stats["skipped"] += 1
    
    return {"ok": True, "pitch": pitch}


def edit_pitch(pitch_id: str, new_message: str) -> Dict[str, Any]:
    """
    Edit pitch message before approving.
    """
    pitch = _pitch_queue.get(pitch_id)
    if not pitch:
        return {"ok": False, "error": "pitch_not_found"}
    
    if pitch["status"] != "pending":
        return {"ok": False, "error": "can_only_edit_pending"}
    
    pitch["message"] = new_message
    pitch["updated_at"] = _now()
    pitch["edited"] = True
    
    return {"ok": True, "pitch": pitch}


# ========== Execution ==========

def _execute_pitch(pitch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send the approved pitch via appropriate channel.
    Integrates with your existing delivery system.
    """
    try:
        # Import your existing delivery
        from proposal_generator import deliver_proposal
        
        # Build delivery payload
        query = pitch["context"].get("offer", "")
        matches = [{"username": pitch["recipient"], "venture": pitch["channel"]}]
        originator = pitch["originator"]
        
        result = deliver_proposal(query, matches, originator)
        
        pitch["status"] = "sent"
        pitch["sent_at"] = _now()
        pitch["updated_at"] = _now()
        pitch["delivery_result"] = result
        _pitch_stats["sent"] += 1
        
        return {"ok": True, "delivery": result}
    
    except Exception as e:
        pitch["status"] = "send_failed"
        pitch["error"] = str(e)
        pitch["updated_at"] = _now()
        return {"ok": False, "error": str(e)}


# ========== Tracking Events ==========

def track_event(pitch_id: str, event: str) -> Dict[str, Any]:
    """
    Track pitch lifecycle events: opened, responded, converted
    Called by webhooks or manual updates.
    """
    pitch = _pitch_queue.get(pitch_id)
    if not pitch:
        return {"ok": False, "error": "pitch_not_found"}
    
    now = _now()
    
    if event == "opened":
        pitch["opened_at"] = now
        _pitch_stats["opened"] += 1
    elif event == "responded":
        pitch["responded_at"] = now
        _pitch_stats["responded"] += 1
    elif event == "converted":
        pitch["converted_at"] = now
        pitch["status"] = "converted"
        _pitch_stats["converted"] += 1
    
    pitch["updated_at"] = now
    
    return {"ok": True, "pitch": pitch}


# ========== Stats ==========

def get_stats() -> Dict[str, Any]:
    """Get AME performance stats for dashboard."""
    pending_count = len([p for p in _pitch_queue.values() if p["status"] == "pending"])
    
    return {
        "queue_size": pending_count,
        "total_generated": _pitch_stats["generated"],
        "approved": _pitch_stats["approved"],
        "skipped": _pitch_stats["skipped"],
        "sent": _pitch_stats["sent"],
        "opened": _pitch_stats["opened"],
        "responded": _pitch_stats["responded"],
        "converted": _pitch_stats["converted"],
        "response_rate": round(_pitch_stats["responded"] / max(1, _pitch_stats["sent"]) * 100, 1),
        "conversion_rate": round(_pitch_stats["converted"] / max(1, _pitch_stats["responded"]) * 100, 1)
    }


def get_all_pitches(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Get pitches with optional status filter."""
    pitches = list(_pitch_queue.values())
    
    if status:
        pitches = [p for p in pitches if p["status"] == status]
    
    pitches.sort(key=lambda x: x["created_at"], reverse=True)
    return pitches[:limit]


# ========== Bulk Generation (for autonomous mode) ==========

def generate_pitches_from_matches(
    matches: List[Dict[str, Any]],
    channel: str = "email",
    originator: str = "ame_auto"
) -> List[Dict[str, Any]]:
    """
    Bulk generate pitches from MetaBridge matches.
    All go to pending queue for approval.
    """
    pitches = []
    
    for match in matches:
        recipient = match.get("username") or match.get("email") or match.get("handle")
        if not recipient:
            continue
        
        context = {
            "offer": match.get("venture") or match.get("offer"),
            "match_reason": match.get("match_reason") or match.get("reason"),
            "score": match.get("score"),
            "source": match.get("source")
        }
        
        pitch = generate_pitch(recipient, channel, context, originator)
        pitches.append(pitch)
    
    return pitches
