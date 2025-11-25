"""
AME API Routes - FastAPI version
Add to your main.py after app = FastAPI()
"""

from fastapi import APIRouter, Body
from typing import Optional, Dict, Any, List

# Import pitch queue functions
from ame_pitches import (
    get_pending_pitches,
    get_pitch,
    approve_pitch,
    skip_pitch,
    edit_pitch,
    get_stats,
    get_all_pitches,
    track_event,
    generate_pitch,
    generate_pitches_from_matches
)

router = APIRouter(prefix="/ame", tags=["AME Auto-Sales"])


@router.get("/queue")
async def api_get_queue(limit: int = 20):
    """Get pending pitches awaiting approval."""
    pitches = get_pending_pitches(limit=limit)
    stats = get_stats()
    return {
        "ok": True,
        "pitches": pitches,
        "queue_size": stats["queue_size"],
        "stats": stats
    }


@router.get("/stats")
async def api_get_stats():
    """Get AME performance statistics."""
    return {
        "ok": True,
        "stats": get_stats()
    }


@router.post("/approve/{pitch_id}")
async def api_approve(pitch_id: str):
    """Approve a pitch and send it."""
    result = approve_pitch(pitch_id)
    return result


@router.post("/skip/{pitch_id}")
async def api_skip(pitch_id: str, body: Dict[str, Any] = Body(default={})):
    """Skip/dismiss a pitch."""
    reason = body.get('reason', '')
    result = skip_pitch(pitch_id, reason=reason)
    return result


@router.post("/edit/{pitch_id}")
async def api_edit(pitch_id: str, body: Dict[str, Any] = Body(...)):
    """Edit a pitch message before approving."""
    new_message = body.get('message', '')
    if not new_message:
        return {"ok": False, "error": "message_required"}
    result = edit_pitch(pitch_id, new_message)
    return result


@router.get("/pitch/{pitch_id}")
async def api_get_pitch(pitch_id: str):
    """Get a specific pitch."""
    pitch = get_pitch(pitch_id)
    if not pitch:
        return {"ok": False, "error": "not_found"}
    return {"ok": True, "pitch": pitch}


@router.get("/pitches")
async def api_get_all_pitches(status: Optional[str] = None, limit: int = 50):
    """Get all pitches with optional status filter."""
    pitches = get_all_pitches(status=status, limit=limit)
    return {
        "ok": True,
        "pitches": pitches,
        "count": len(pitches)
    }


@router.post("/track/{pitch_id}")
async def api_track_event(pitch_id: str, body: Dict[str, Any] = Body(...)):
    """Track pitch events (opened, responded, converted)."""
    event = body.get('event')
    if event not in ('opened', 'responded', 'converted'):
        return {"ok": False, "error": "invalid_event"}
    result = track_event(pitch_id, event)
    return result


@router.post("/generate")
async def api_generate_pitch(body: Dict[str, Any] = Body(...)):
    """Manually generate a pitch (goes to pending queue)."""
    recipient = body.get('recipient')
    channel = body.get('channel', 'email')
    context = body.get('context', {})
    originator = body.get('originator', 'manual')
    
    if not recipient:
        return {"ok": False, "error": "recipient_required"}
    
    pitch = generate_pitch(recipient, channel, context, originator)
    return {"ok": True, "pitch": pitch}


@router.post("/generate-from-matches")
async def api_generate_from_matches(body: Dict[str, Any] = Body(...)):
    """Bulk generate pitches from MetaBridge matches."""
    matches = body.get('matches', [])
    channel = body.get('channel', 'email')
    originator = body.get('originator', 'ame_auto')
    
    if not matches:
        return {"ok": False, "error": "matches_required"}
    
    pitches = generate_pitches_from_matches(matches, channel, originator)
    return {
        "ok": True,
        "generated": len(pitches),
        "pitches": pitches
    }


# ========== Registration helper ==========

def register_ame_routes(app):
    """Call this from main.py AFTER app = FastAPI()"""
    app.include_router(router)
    print("✅ AME routes registered at /ame/*")
