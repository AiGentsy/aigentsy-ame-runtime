"""
═══════════════════════════════════════════════════════════════════════════════
YIELD MEMORY v2.0 - PER-USER PATTERN LEARNING
═══════════════════════════════════════════════════════════════════════════════

Yield Memory is the personalized learning layer for each user.
It remembers what works for THIS specific user and adapts accordingly.

INTEGRATION WITH AI FAMILY BRAIN:
- Tracks which AI model works best for each user
- Remembers user-specific model preferences
- Feeds successful patterns back to the AI Family
- Receives optimizations from collective learning

THE KNOWLEDGE FLOW:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   USER INTERACTION                                                           │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────┐                                                       │
│   │  YIELD MEMORY   │◄─── What works for THIS user                          │
│   │  (Per-User)     │                                                       │
│   └────────┬────────┘                                                       │
│            │                                                                 │
│            │ successful patterns                                             │
│            ▼                                                                 │
│   ┌─────────────────┐                                                       │
│   │   METAHIVE      │◄─── What works for ALL users                          │
│   │  (Platform)     │                                                       │
│   └────────┬────────┘                                                       │
│            │                                                                 │
│            │ collective insights                                             │
│            ▼                                                                 │
│   ┌─────────────────┐                                                       │
│   │ AI FAMILY BRAIN │◄─── Which AI is best for what                         │
│   │  (Intelligence) │                                                       │
│   └─────────────────┘                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

PATTERN CATEGORIES:
- SUCCESS: ROAS >= 1.5 (strategies to replay)
- FAILURE: ROAS <= 0.5 (strategies to avoid)
- NEUTRAL: 0.5 < ROAS < 1.5 (learning opportunities)

NEW: AI-SPECIFIC PATTERNS
- Tracks which AI model was used for each pattern
- Learns user's preferred AI per task type
- Adapts AI routing to user's style

═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from collections import defaultdict
from dataclasses import dataclass, field
import json
import hashlib

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

MAX_PATTERNS_PER_USER = 200  # Increased for richer learning
SUCCESS_THRESHOLD = 1.5
FAILURE_THRESHOLD = 0.5
PATTERN_DECAY_DAYS = 60
MIN_REPLAYS_FOR_CONFIDENCE = 3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class YieldPattern:
    """A pattern in user's memory"""
    id: str
    pattern_type: str
    category: str  # SUCCESS, FAILURE, NEUTRAL
    
    # Pattern content
    context: Dict[str, Any]
    action: Dict[str, Any]
    outcome: Dict[str, Any]
    
    # Scoring
    score: float  # ROAS or quality
    confidence: float = 0.5
    
    # Usage tracking
    replay_count: int = 0
    success_on_replay: int = 0
    total_revenue: float = 0.0
    
    # AI Family tracking (NEW)
    ai_model: Optional[str] = None
    task_category: Optional[str] = None
    ai_quality_score: Optional[float] = None
    
    # Timestamps
    created_at: str = field(default_factory=_now)
    last_replayed: Optional[str] = None
    
    # Content hash for deduplication
    content_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "category": self.category,
            "context": self.context,
            "action": self.action,
            "outcome": self.outcome,
            "score": self.score,
            "confidence": self.confidence,
            "replay_count": self.replay_count,
            "success_on_replay": self.success_on_replay,
            "total_revenue": self.total_revenue,
            "ai_model": self.ai_model,
            "task_category": self.task_category,
            "ai_quality_score": self.ai_quality_score,
            "created_at": self.created_at,
            "last_replayed": self.last_replayed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'YieldPattern':
        return cls(
            id=data["id"],
            pattern_type=data["pattern_type"],
            category=data["category"],
            context=data.get("context", {}),
            action=data.get("action", {}),
            outcome=data.get("outcome", {}),
            score=data.get("score", 0),
            confidence=data.get("confidence", 0.5),
            replay_count=data.get("replay_count", 0),
            success_on_replay=data.get("success_on_replay", 0),
            total_revenue=data.get("total_revenue", 0.0),
            ai_model=data.get("ai_model"),
            task_category=data.get("task_category"),
            ai_quality_score=data.get("ai_quality_score"),
            created_at=data.get("created_at", _now()),
            last_replayed=data.get("last_replayed"),
            content_hash=data.get("content_hash", "")
        )


@dataclass
class UserAIPreferences:
    """User's learned AI model preferences (NEW)"""
    username: str
    
    # Per task category preferences
    category_preferences: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Format: {task_category: {"preferred_model": "claude", "success_rate": 0.9, "tasks": 50}}
    
    # Overall model performance for this user
    model_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Format: {model: {"tasks": 100, "successes": 90, "avg_quality": 0.85}}
    
    # User's style preferences (inferred)
    prefers_speed: bool = False
    prefers_quality: bool = True
    prefers_creativity: bool = False
    
    last_updated: str = field(default_factory=_now)


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════════════════════════

_YIELD_MEMORY: Dict[str, List[YieldPattern]] = {}
_USER_AI_PREFERENCES: Dict[str, UserAIPreferences] = {}
_PATTERN_INDEX: Dict[str, Dict[str, YieldPattern]] = defaultdict(dict)  # username -> {id: pattern}


# ═══════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def store_pattern(
    username: str,
    pattern_type: str,
    context: Dict[str, Any],
    action: Dict[str, Any],
    outcome: Dict[str, Any],
    ai_model: str = None,
    task_category: str = None
) -> Dict[str, Any]:
    """
    Store a pattern (success, failure, or neutral).
    
    NEW: Tracks AI model and task category for AI Family learning.
    """
    
    # Calculate ROAS and categorize
    roas = float(outcome.get("roas", 0))
    revenue = float(outcome.get("revenue_usd", 0))
    quality = float(outcome.get("quality_score", 0.5))
    
    if roas >= SUCCESS_THRESHOLD:
        category = "SUCCESS"
        score = roas
    elif roas <= FAILURE_THRESHOLD:
        category = "FAILURE"
        score = roas
    else:
        category = "NEUTRAL"
        score = roas
    
    # Generate ID and hash
    pattern_id = f"pat_{uuid4().hex[:12]}"
    content_hash = hashlib.md5(
        json.dumps({"context": context, "action": action}, sort_keys=True).encode()
    ).hexdigest()[:16]
    
    # Initialize user memory if needed
    if username not in _YIELD_MEMORY:
        _YIELD_MEMORY[username] = []
    
    # Check for duplicate
    for existing in _YIELD_MEMORY[username]:
        if existing.content_hash == content_hash:
            # Update existing instead of adding duplicate
            existing.replay_count += 1
            existing.last_replayed = _now()
            if roas >= SUCCESS_THRESHOLD:
                existing.success_on_replay += 1
            existing.total_revenue += revenue
            existing.confidence = existing.success_on_replay / existing.replay_count
            return {"ok": True, "pattern_id": existing.id, "action": "updated_existing"}
    
    # Create pattern
    pattern = YieldPattern(
        id=pattern_id,
        pattern_type=pattern_type,
        category=category,
        context=context,
        action=action,
        outcome=outcome,
        score=round(score, 2),
        ai_model=ai_model,
        task_category=task_category,
        ai_quality_score=quality,
        content_hash=content_hash
    )
    
    # Add to memory
    _YIELD_MEMORY[username].append(pattern)
    _PATTERN_INDEX[username][pattern_id] = pattern
    
    # Update AI preferences
    if ai_model and task_category:
        _update_ai_preferences(username, ai_model, task_category, roas >= SUCCESS_THRESHOLD, quality)
    
    # Compress if over limit
    if len(_YIELD_MEMORY[username]) > MAX_PATTERNS_PER_USER:
        compress_memory(username)
    
    return {"ok": True, "pattern_id": pattern_id, "category": category, "score": score}


def find_similar_patterns(
    username: str,
    context: Dict[str, Any],
    pattern_type: str = None,
    category: str = "SUCCESS",
    limit: int = 5,
    ai_model: str = None,
    task_category: str = None
) -> Dict[str, Any]:
    """
    Find patterns similar to current context.
    
    NEW: Can filter by AI model and task category.
    """
    
    if username not in _YIELD_MEMORY:
        return {"ok": True, "patterns": [], "count": 0}
    
    patterns = _YIELD_MEMORY[username]
    
    # Filter
    filtered = [
        p for p in patterns
        if (not pattern_type or p.pattern_type == pattern_type)
        and p.category == category
        and (not ai_model or p.ai_model == ai_model)
        and (not task_category or p.task_category == task_category)
    ]
    
    if not filtered:
        return {"ok": True, "patterns": [], "count": 0}
    
    # Score by similarity
    scored = []
    for pattern in filtered:
        similarity = _calculate_context_similarity(context, pattern.context)
        
        # Decay based on age
        age_days = (_now_dt() - datetime.fromisoformat(pattern.created_at.replace("Z", "+00:00"))).days
        decay = max(0.5, 1 - (age_days / PATTERN_DECAY_DAYS))
        
        # Confidence boost from replays
        conf_boost = min(pattern.confidence, 1.0) if pattern.replay_count >= MIN_REPLAYS_FOR_CONFIDENCE else 0.5
        
        combined = pattern.score * similarity * decay * conf_boost
        
        scored.append({
            "pattern": pattern,
            "similarity": similarity,
            "decay": decay,
            "combined_score": combined
        })
    
    # Sort and return
    scored.sort(key=lambda x: x["combined_score"], reverse=True)
    results = [s["pattern"].to_dict() for s in scored[:limit]]
    
    return {"ok": True, "patterns": results, "count": len(results)}


def get_best_action(
    username: str,
    context: Dict[str, Any],
    pattern_type: str = None,
    task_category: str = None
) -> Dict[str, Any]:
    """
    Get recommended action based on user's memory.
    
    NEW: Includes AI model recommendation.
    """
    
    result = find_similar_patterns(
        username=username,
        context=context,
        pattern_type=pattern_type,
        category="SUCCESS",
        limit=3,
        task_category=task_category
    )
    
    patterns = result.get("patterns", [])
    
    if not patterns:
        # Try getting recommendation from AI preferences
        ai_rec = get_user_ai_recommendation(username, task_category)
        return {
            "ok": False, 
            "error": "no_patterns_found",
            "ai_recommendation": ai_rec
        }
    
    best = patterns[0]
    
    # Update replay stats
    pattern = _PATTERN_INDEX[username].get(best["id"])
    if pattern:
        pattern.replay_count += 1
        pattern.last_replayed = _now()
    
    return {
        "ok": True,
        "recommended_action": best["action"],
        "pattern_id": best["id"],
        "expected_roas": best["score"],
        "confidence": best.get("confidence", 0.5),
        "replay_count": best["replay_count"],
        "recommended_ai_model": best.get("ai_model"),
        "similar_patterns": len(patterns)
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
    for p in patterns:
        avoid_actions.append({
            "action": p["action"],
            "reason": f"Failed with ROAS {p['score']}",
            "ai_model_used": p.get("ai_model"),
            "similarity": p.get("similarity", 0)
        })
    
    return {"ok": True, "avoid": avoid_actions, "count": len(avoid_actions)}


def report_pattern_replay(
    username: str,
    pattern_id: str,
    success: bool,
    actual_roas: float = None,
    revenue_generated: float = None
) -> Dict[str, Any]:
    """Report outcome of replaying a pattern"""
    
    pattern = _PATTERN_INDEX.get(username, {}).get(pattern_id)
    if not pattern:
        return {"ok": False, "error": "pattern_not_found"}
    
    pattern.replay_count += 1
    pattern.last_replayed = _now()
    
    if success:
        pattern.success_on_replay += 1
    
    if revenue_generated:
        pattern.total_revenue += revenue_generated
    
    # Update confidence
    pattern.confidence = pattern.success_on_replay / pattern.replay_count
    
    # Update score based on actual performance
    if actual_roas is not None:
        # Weighted average with original score
        pattern.score = round((pattern.score * 0.7 + actual_roas * 0.3), 2)
        
        # Reclassify if needed
        if pattern.score >= SUCCESS_THRESHOLD and pattern.category != "SUCCESS":
            pattern.category = "SUCCESS"
        elif pattern.score <= FAILURE_THRESHOLD and pattern.category != "FAILURE":
            pattern.category = "FAILURE"
    
    return {"ok": True, "pattern": pattern.to_dict()}


# ═══════════════════════════════════════════════════════════════════════════════
# AI PREFERENCES (NEW)
# ═══════════════════════════════════════════════════════════════════════════════

def _update_ai_preferences(
    username: str,
    ai_model: str,
    task_category: str,
    success: bool,
    quality: float
):
    """Update user's AI model preferences based on task outcome"""
    
    if username not in _USER_AI_PREFERENCES:
        _USER_AI_PREFERENCES[username] = UserAIPreferences(username=username)
    
    prefs = _USER_AI_PREFERENCES[username]
    
    # Update model performance
    if ai_model not in prefs.model_performance:
        prefs.model_performance[ai_model] = {"tasks": 0, "successes": 0, "total_quality": 0.0}
    
    mp = prefs.model_performance[ai_model]
    mp["tasks"] += 1
    if success:
        mp["successes"] += 1
    mp["total_quality"] += quality
    mp["avg_quality"] = mp["total_quality"] / mp["tasks"]
    mp["success_rate"] = mp["successes"] / mp["tasks"]
    
    # Update category preferences
    if task_category not in prefs.category_preferences:
        prefs.category_preferences[task_category] = {}
    
    cat_prefs = prefs.category_preferences[task_category]
    if ai_model not in cat_prefs:
        cat_prefs[ai_model] = {"tasks": 0, "successes": 0, "total_quality": 0.0}
    
    cp = cat_prefs[ai_model]
    cp["tasks"] += 1
    if success:
        cp["successes"] += 1
    cp["total_quality"] += quality
    
    # Determine preferred model for category
    best_model = None
    best_score = 0
    for model, stats in cat_prefs.items():
        if stats["tasks"] >= 3:  # Minimum tasks for preference
            score = (stats["successes"] / stats["tasks"]) * 0.6 + (stats["total_quality"] / stats["tasks"]) * 0.4
            if score > best_score:
                best_score = score
                best_model = model
    
    if best_model:
        prefs.category_preferences[task_category]["_preferred"] = {
            "model": best_model,
            "score": best_score,
            "tasks": cat_prefs[best_model]["tasks"]
        }
    
    prefs.last_updated = _now()


def get_user_ai_recommendation(
    username: str,
    task_category: str = None
) -> Dict[str, Any]:
    """
    Get AI model recommendation for user.
    
    Returns the best AI model for this user based on their history.
    """
    
    if username not in _USER_AI_PREFERENCES:
        return {"ok": False, "error": "no_preferences", "recommendation": None}
    
    prefs = _USER_AI_PREFERENCES[username]
    
    if task_category:
        # Category-specific recommendation
        cat_prefs = prefs.category_preferences.get(task_category, {})
        preferred = cat_prefs.get("_preferred")
        
        if preferred:
            return {
                "ok": True,
                "task_category": task_category,
                "recommended_model": preferred["model"],
                "confidence": min(preferred["score"], 1.0),
                "based_on_tasks": preferred["tasks"]
            }
    
    # Overall recommendation
    if prefs.model_performance:
        best = max(
            prefs.model_performance.items(),
            key=lambda x: x[1].get("success_rate", 0) if x[1].get("tasks", 0) >= 5 else 0
        )
        
        if best[1].get("tasks", 0) >= 5:
            return {
                "ok": True,
                "recommended_model": best[0],
                "success_rate": best[1].get("success_rate", 0),
                "avg_quality": best[1].get("avg_quality", 0),
                "based_on_tasks": best[1].get("tasks", 0)
            }
    
    return {"ok": False, "error": "insufficient_data", "recommendation": None}


def get_user_ai_stats(username: str) -> Dict[str, Any]:
    """Get user's AI model usage statistics"""
    
    if username not in _USER_AI_PREFERENCES:
        return {"ok": True, "stats": {}, "empty": True}
    
    prefs = _USER_AI_PREFERENCES[username]
    
    return {
        "ok": True,
        "model_performance": prefs.model_performance,
        "category_preferences": {
            cat: {
                "preferred": data.get("_preferred", {}).get("model"),
                "models_used": len([k for k in data.keys() if not k.startswith("_")])
            }
            for cat, data in prefs.category_preferences.items()
        },
        "last_updated": prefs.last_updated
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def compress_memory(username: str) -> Dict[str, Any]:
    """Keep only top patterns by combined score"""
    
    if username not in _YIELD_MEMORY:
        return {"ok": False, "error": "no_memory"}
    
    patterns = _YIELD_MEMORY[username]
    
    # Score each pattern
    scored = []
    for p in patterns:
        age_days = (_now_dt() - datetime.fromisoformat(p.created_at.replace("Z", "+00:00"))).days
        decay = max(0.3, 1 - (age_days / PATTERN_DECAY_DAYS))
        
        combined = (
            abs(p.score) * 0.3 +  # Higher ROAS or lower (for failures)
            p.confidence * 0.2 +
            (p.replay_count / 10) * 0.2 +
            (p.total_revenue / 1000) * 0.2 +
            decay * 0.1
        )
        
        # Boost successes, keep some failures for learning
        if p.category == "SUCCESS":
            combined *= 1.2
        elif p.category == "FAILURE":
            combined *= 0.8  # Keep some failures
        
        scored.append((p, combined))
    
    # Sort and keep top
    scored.sort(key=lambda x: x[1], reverse=True)
    
    kept = [p for p, _ in scored[:MAX_PATTERNS_PER_USER]]
    discarded = len(patterns) - len(kept)
    
    _YIELD_MEMORY[username] = kept
    
    # Rebuild index
    _PATTERN_INDEX[username] = {p.id: p for p in kept}
    
    return {"ok": True, "kept": len(kept), "discarded": discarded}


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

def get_memory_stats(username: str) -> Dict[str, Any]:
    """Get user's memory statistics"""
    
    if username not in _YIELD_MEMORY:
        return {"ok": True, "total_patterns": 0, "empty": True}
    
    patterns = _YIELD_MEMORY[username]
    
    success = [p for p in patterns if p.category == "SUCCESS"]
    failure = [p for p in patterns if p.category == "FAILURE"]
    neutral = [p for p in patterns if p.category == "NEUTRAL"]
    
    # Type distribution
    types = defaultdict(int)
    for p in patterns:
        types[p.pattern_type] += 1
    
    # AI model distribution
    ai_models = defaultdict(int)
    for p in patterns:
        if p.ai_model:
            ai_models[p.ai_model] += 1
    
    # Calculate averages
    avg_success_roas = sum(p.score for p in success) / len(success) if success else 0
    avg_confidence = sum(p.confidence for p in patterns) / len(patterns) if patterns else 0
    total_revenue = sum(p.total_revenue for p in patterns)
    
    return {
        "ok": True,
        "total_patterns": len(patterns),
        "success_patterns": len(success),
        "failure_patterns": len(failure),
        "neutral_patterns": len(neutral),
        "avg_success_roas": round(avg_success_roas, 2),
        "avg_confidence": round(avg_confidence, 2),
        "total_revenue_from_replays": round(total_revenue, 2),
        "pattern_types": dict(types),
        "ai_models_used": dict(ai_models),
        "most_replayed": sorted(
            [p.to_dict() for p in patterns],
            key=lambda x: x["replay_count"],
            reverse=True
        )[:5],
        "highest_confidence": sorted(
            [p.to_dict() for p in patterns if p.replay_count >= MIN_REPLAYS_FOR_CONFIDENCE],
            key=lambda x: x["confidence"],
            reverse=True
        )[:5]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT/IMPORT
# ═══════════════════════════════════════════════════════════════════════════════

def export_memory(username: str) -> str:
    """Export user's memory as JSON"""
    
    if username not in _YIELD_MEMORY:
        return json.dumps({"patterns": [], "ai_preferences": None})
    
    patterns = [p.to_dict() for p in _YIELD_MEMORY[username]]
    ai_prefs = None
    
    if username in _USER_AI_PREFERENCES:
        prefs = _USER_AI_PREFERENCES[username]
        ai_prefs = {
            "category_preferences": prefs.category_preferences,
            "model_performance": prefs.model_performance
        }
    
    return json.dumps({
        "patterns": patterns,
        "ai_preferences": ai_prefs,
        "exported_at": _now()
    }, indent=2)


def import_memory(username: str, json_data: str) -> Dict[str, Any]:
    """Import memory from JSON"""
    
    try:
        data = json.loads(json_data)
        
        patterns = [YieldPattern.from_dict(p) for p in data.get("patterns", [])]
        _YIELD_MEMORY[username] = patterns
        _PATTERN_INDEX[username] = {p.id: p for p in patterns}
        
        # Import AI preferences if present
        if data.get("ai_preferences"):
            prefs = UserAIPreferences(username=username)
            prefs.category_preferences = data["ai_preferences"].get("category_preferences", {})
            prefs.model_performance = data["ai_preferences"].get("model_performance", {})
            _USER_AI_PREFERENCES[username] = prefs
        
        return {"ok": True, "imported_patterns": len(patterns)}
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


def export_for_metahive(username: str, min_score: float = 2.0) -> List[Dict[str, Any]]:
    """
    Export high-quality patterns for MetaHive contribution.
    
    Only exports patterns that exceed min_score and have been validated through replays.
    """
    
    if username not in _YIELD_MEMORY:
        return []
    
    exportable = []
    for p in _YIELD_MEMORY[username]:
        if (p.category == "SUCCESS" and 
            p.score >= min_score and 
            p.replay_count >= MIN_REPLAYS_FOR_CONFIDENCE and
            p.confidence >= 0.6):
            
            exportable.append({
                "pattern_type": p.pattern_type,
                "context": p.context,
                "action": p.action,
                "outcome": p.outcome,
                "ai_model": p.ai_model,
                "task_category": p.task_category,
                "confidence": p.confidence
            })
    
    return exportable


def export_ai_learnings_for_family(username: str) -> Dict[str, Any]:
    """
    Export user's AI learnings for AI Family Brain.
    
    This allows user-specific AI performance data to flow back to the family.
    """
    
    if username not in _USER_AI_PREFERENCES:
        return {"ok": False, "error": "no_ai_data"}
    
    prefs = _USER_AI_PREFERENCES[username]
    
    return {
        "ok": True,
        "username": username,
        "model_performance": prefs.model_performance,
        "category_preferences": {
            cat: data.get("_preferred", {})
            for cat, data in prefs.category_preferences.items()
            if "_preferred" in data
        },
        "exported_at": _now()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _calculate_context_similarity(ctx1: Dict[str, Any], ctx2: Dict[str, Any]) -> float:
    """Calculate similarity between two contexts"""
    
    if not ctx1 or not ctx2:
        return 0.0
    
    matches = 0
    total = 0
    
    # Key importance weights
    key_weights = {
        "channel": 1.5,
        "audience": 1.5,
        "industry": 1.5,
        "budget_tier": 1.2,
        "task_category": 1.3,
        "hour": 0.8,
        "day_of_week": 0.8
    }
    
    shared_keys = set(ctx1.keys()) & set(ctx2.keys())
    
    for key in shared_keys:
        weight = key_weights.get(key, 1.0)
        total += weight
        
        v1, v2 = ctx1[key], ctx2[key]
        
        if v1 == v2:
            matches += weight
        elif isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            # Numeric similarity
            diff = abs(float(v1) - float(v2))
            avg = (float(v1) + float(v2)) / 2
            if avg > 0 and diff / avg < 0.25:
                matches += weight * 0.5
        elif isinstance(v1, str) and isinstance(v2, str):
            # String partial match
            if v1.lower() in v2.lower() or v2.lower() in v1.lower():
                matches += weight * 0.5
    
    return round(matches / total, 2) if total > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

print("""
═══════════════════════════════════════════════════════════════════════════════
🧠 YIELD MEMORY v2.0 - PER-USER PATTERN LEARNING
═══════════════════════════════════════════════════════════════════════════════

   ┌─────────────────────────────────────────────────────────────────────────┐
   │                    PERSONALIZED LEARNING                                 │
   │                                                                          │
   │   ACTION ──► OUTCOME ──► PATTERN ──► MEMORY ──► RECOMMENDATION          │
   │                                                                          │
   │   SUCCESS patterns: Replay for similar contexts                         │
   │   FAILURE patterns: Avoid in similar contexts                           │
   │   AI preferences: Learn which AI works best for this user               │
   │                                                                          │
   └─────────────────────────────────────────────────────────────────────────┘

   Max patterns per user: 200
   AI Family tracking: ✓
   MetaHive export: ✓
   
═══════════════════════════════════════════════════════════════════════════════
""")
