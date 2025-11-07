from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import json

_YIELD_MEMORY: Dict[str, List[Dict[str, Any]]] = {}
MAX_PATTERNS_PER_USER = 100
SUCCESS_THRESHOLD = 1.5  # ROAS > 1.5 = success
FAILURE_THRESHOLD = 0.5  # ROAS < 0.5 = failure

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


def store_pattern(
    username: str,
    pattern_type: str,
    context: Dict[str, Any],
    action: Dict[str, Any],
    outcome: Dict[str, Any]
) -> Dict[str, Any]:
    """Store a pattern (success or failure)"""
    
    pattern_id = f"pat_{uuid4().hex[:8]}"
    
    # Calculate success score
    roas = float(outcome.get("roas", 0))
    revenue = float(outcome.get("revenue_usd", 0))
    cost = float(outcome.get("cost_usd", 0))
    
    if roas >= SUCCESS_THRESHOLD:
        category = "SUCCESS"
        score = roas
    elif roas <= FAILURE_THRESHOLD:
        category = "FAILURE"
        score = roas
    else:
        category = "NEUTRAL"
        score = roas
    
    pattern = {
        "id": pattern_id,
        "type": pattern_type,
        "category": category,
        "score": round(score, 2),
        "context": context,
        "action": action,
        "outcome": outcome,
        "created_at": now_iso(),
        "replay_count": 0,
        "last_replayed": None
    }
    
    # Add to user's memory
    if username not in _YIELD_MEMORY:
        _YIELD_MEMORY[username] = []
    
    _YIELD_MEMORY[username].append(pattern)
    
    # Compress if over limit
    if len(_YIELD_MEMORY[username]) > MAX_PATTERNS_PER_USER:
        compress_memory(username)
    
    return {"ok": True, "pattern_id": pattern_id, "pattern": pattern}


def compress_memory(username: str):
    """Keep only top 100 patterns by score"""
    if username not in _YIELD_MEMORY:
        return
    
    patterns = _YIELD_MEMORY[username]
    
    # Sort by score (success) and replay_count (proven utility)
    patterns.sort(
        key=lambda p: (p["score"] * 0.7 + p["replay_count"] * 0.3),
        reverse=True
    )
    
    # Keep top 100
    _YIELD_MEMORY[username] = patterns[:MAX_PATTERNS_PER_USER]
    
    return {"ok": True, "kept": len(_YIELD_MEMORY[username]), "discarded": len(patterns) - MAX_PATTERNS_PER_USER}


def find_similar_patterns(
    username: str,
    context: Dict[str, Any],
    pattern_type: str = None,
    category: str = "SUCCESS",
    limit: int = 5
) -> Dict[str, Any]:
    """Find patterns similar to current context"""
    
    if username not in _YIELD_MEMORY:
        return {"ok": True, "patterns": []}
    
    patterns = _YIELD_MEMORY[username]
    
    # Filter by type and category
    filtered = [
        p for p in patterns
        if (not pattern_type or p["type"] == pattern_type)
        and p["category"] == category
    ]
    
    # Score similarity
    scored = []
    for pattern in filtered:
        similarity = calculate_context_similarity(context, pattern["context"])
        scored.append({
            "pattern": pattern,
            "similarity": similarity,
            "combined_score": pattern["score"] * similarity
        })
    
    # Sort by combined score
    scored.sort(key=lambda x: x["combined_score"], reverse=True)
    
    # Return top matches
    results = [s["pattern"] for s in scored[:limit]]
    
    return {"ok": True, "patterns": results, "count": len(results)}


def calculate_context_similarity(ctx1: Dict[str, Any], ctx2: Dict[str, Any]) -> float:
    """Calculate similarity between two contexts (0.0 to 1.0)"""
    
    # Simple heuristic: match on key dimensions
    matches = 0
    total = 0
    
    # Channel match
    if ctx1.get("channel") and ctx2.get("channel"):
        total += 1
        if ctx1["channel"] == ctx2["channel"]:
            matches += 1
    
    # Audience match
    if ctx1.get("audience") and ctx2.get("audience"):
        total += 1
        if ctx1["audience"] == ctx2["audience"]:
            matches += 1
    
    # Time of day match (within 3 hours)
    if ctx1.get("hour") and ctx2.get("hour"):
        total += 1
        if abs(int(ctx1["hour"]) - int(ctx2["hour"])) <= 3:
            matches += 1
    
    # Budget tier match
    if ctx1.get("budget_tier") and ctx2.get("budget_tier"):
        total += 1
        if ctx1["budget_tier"] == ctx2["budget_tier"]:
            matches += 1
    
    # Day of week match
    if ctx1.get("day_of_week") and ctx2.get("day_of_week"):
        total += 1
        if ctx1["day_of_week"] == ctx2["day_of_week"]:
            matches += 1
    
    return round(matches / total, 2) if total > 0 else 0.0


def get_best_action(
    username: str,
    context: Dict[str, Any],
    pattern_type: str = None
) -> Dict[str, Any]:
    """Get recommended action based on memory"""
    
    result = find_similar_patterns(
        username=username,
        context=context,
        pattern_type=pattern_type,
        category="SUCCESS",
        limit=3
    )
    
    patterns = result.get("patterns", [])
    
    if not patterns:
        return {"ok": False, "error": "no_patterns_found"}
    
    # Return top pattern's action
    best_pattern = patterns[0]
    
    # Increment replay count
    best_pattern["replay_count"] += 1
    best_pattern["last_replayed"] = now_iso()
    
    return {
        "ok": True,
        "recommended_action": best_pattern["action"],
        "pattern_id": best_pattern["id"],
        "expected_roas": best_pattern["score"],
        "confidence": calculate_context_similarity(context, best_pattern["context"]),
        "replay_count": best_pattern["replay_count"]
    }


def get_patterns_to_avoid(
    username: str,
    context: Dict[str, Any],
    pattern_type: str = None
) -> Dict[str, Any]:
    """Get patterns to avoid based on failures"""
    
    result = find_similar_patterns(
        username=username,
        context=context,
        pattern_type=pattern_type,
        category="FAILURE",
        limit=5
    )
    
    patterns = result.get("patterns", [])
    
    avoid_actions = []
    for pattern in patterns:
        avoid_actions.append({
            "action": pattern["action"],
            "reason": f"Failed with ROAS {pattern['score']}",
            "context": pattern["context"]
        })
    
    return {"ok": True, "avoid": avoid_actions, "count": len(avoid_actions)}


def get_memory_stats(username: str) -> Dict[str, Any]:
    """Get user's yield memory statistics"""
    
    if username not in _YIELD_MEMORY:
        return {
            "ok": True,
            "total_patterns": 0,
            "success_patterns": 0,
            "failure_patterns": 0,
            "avg_success_roas": 0.0
        }
    
    patterns = _YIELD_MEMORY[username]
    
    success = [p for p in patterns if p["category"] == "SUCCESS"]
    failure = [p for p in patterns if p["category"] == "FAILURE"]
    
    avg_success_roas = sum(p["score"] for p in success) / len(success) if success else 0.0
    
    # Pattern types breakdown
    types = {}
    for p in patterns:
        ptype = p["type"]
        types[ptype] = types.get(ptype, 0) + 1
    
    return {
        "ok": True,
        "total_patterns": len(patterns),
        "success_patterns": len(success),
        "failure_patterns": len(failure),
        "neutral_patterns": len(patterns) - len(success) - len(failure),
        "avg_success_roas": round(avg_success_roas, 2),
        "pattern_types": types,
        "most_replayed": sorted(patterns, key=lambda p: p["replay_count"], reverse=True)[:5]
    }


def export_memory(username: str) -> str:
    """Export memory as JSON"""
    if username not in _YIELD_MEMORY:
        return json.dumps({"patterns": []})
    
    return json.dumps({"patterns": _YIELD_MEMORY[username]}, indent=2)


def import_me
