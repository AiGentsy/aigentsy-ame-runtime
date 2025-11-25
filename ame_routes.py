"""
AME API Routes - Add these to your main.py or import as blueprint

Flask endpoints for the AME pitch approval dashboard:
- GET  /ame/queue      - Get pending pitches
- GET  /ame/stats      - Get performance stats
- POST /ame/approve/<id> - Approve and send pitch
- POST /ame/skip/<id>    - Skip pitch
- POST /ame/edit/<id>    - Edit pitch message
- GET  /ame/pitches      - Get all pitches (with filters)
- POST /ame/track/<id>   - Track events (opened, responded, converted)
"""

from flask import Blueprint, request, jsonify

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

ame_bp = Blueprint('ame', __name__, url_prefix='/ame')


@ame_bp.route('/queue', methods=['GET'])
def api_get_queue():
    """Get pending pitches awaiting approval."""
    limit = request.args.get('limit', 20, type=int)
    pitches = get_pending_pitches(limit=limit)
    stats = get_stats()
    return jsonify({
        "ok": True,
        "pitches": pitches,
        "queue_size": stats["queue_size"],
        "stats": stats
    })


@ame_bp.route('/stats', methods=['GET'])
def api_get_stats():
    """Get AME performance statistics."""
    return jsonify({
        "ok": True,
        "stats": get_stats()
    })


@ame_bp.route('/approve/<pitch_id>', methods=['POST'])
def api_approve(pitch_id: str):
    """Approve a pitch and send it."""
    result = approve_pitch(pitch_id)
    return jsonify(result)


@ame_bp.route('/skip/<pitch_id>', methods=['POST'])
def api_skip(pitch_id: str):
    """Skip/dismiss a pitch."""
    data = request.get_json() or {}
    reason = data.get('reason', '')
    result = skip_pitch(pitch_id, reason=reason)
    return jsonify(result)


@ame_bp.route('/edit/<pitch_id>', methods=['POST'])
def api_edit(pitch_id: str):
    """Edit a pitch message before approving."""
    data = request.get_json() or {}
    new_message = data.get('message', '')
    if not new_message:
        return jsonify({"ok": False, "error": "message_required"}), 400
    result = edit_pitch(pitch_id, new_message)
    return jsonify(result)


@ame_bp.route('/pitch/<pitch_id>', methods=['GET'])
def api_get_pitch(pitch_id: str):
    """Get a specific pitch."""
    pitch = get_pitch(pitch_id)
    if not pitch:
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify({"ok": True, "pitch": pitch})


@ame_bp.route('/pitches', methods=['GET'])
def api_get_all_pitches():
    """Get all pitches with optional status filter."""
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    pitches = get_all_pitches(status=status, limit=limit)
    return jsonify({
        "ok": True,
        "pitches": pitches,
        "count": len(pitches)
    })


@ame_bp.route('/track/<pitch_id>', methods=['POST'])
def api_track_event(pitch_id: str):
    """Track pitch events (opened, responded, converted)."""
    data = request.get_json() or {}
    event = data.get('event')
    if event not in ('opened', 'responded', 'converted'):
        return jsonify({"ok": False, "error": "invalid_event"}), 400
    result = track_event(pitch_id, event)
    return jsonify(result)


@ame_bp.route('/generate', methods=['POST'])
def api_generate_pitch():
    """Manually generate a pitch (goes to pending queue)."""
    data = request.get_json() or {}
    
    recipient = data.get('recipient')
    channel = data.get('channel', 'email')
    context = data.get('context', {})
    originator = data.get('originator', 'manual')
    
    if not recipient:
        return jsonify({"ok": False, "error": "recipient_required"}), 400
    
    pitch = generate_pitch(recipient, channel, context, originator)
    return jsonify({"ok": True, "pitch": pitch})


@ame_bp.route('/generate-from-matches', methods=['POST'])
def api_generate_from_matches():
    """Bulk generate pitches from MetaBridge matches."""
    data = request.get_json() or {}
    
    matches = data.get('matches', [])
    channel = data.get('channel', 'email')
    originator = data.get('originator', 'ame_auto')
    
    if not matches:
        return jsonify({"ok": False, "error": "matches_required"}), 400
    
    pitches = generate_pitches_from_matches(matches, channel, originator)
    return jsonify({
        "ok": True,
        "generated": len(pitches),
        "pitches": pitches
    })


# ========== Registration helper ==========

def register_ame_routes(app):
    """Call this from main.py to register AME routes."""
    app.register_blueprint(ame_bp)
    print("✅ AME routes registered at /ame/*")


# ========== Standalone test ==========

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    register_ame_routes(app)
    
    # Add test pitch
    from ame_pitches import generate_pitch
    generate_pitch(
        recipient="test@example.com",
        channel="email",
        context={"offer": "AI automation", "match_reason": "You posted about needing help with marketing"},
        originator="test"
    )
    
    app.run(debug=True, port=5001)
