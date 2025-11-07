from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import httpx

_HIVE_MEMORY: List[Dict[str, Any]] = []
MAX_HIVE_PATTERNS = 1000

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def contribute_to_hive(
    username: str,
    pattern_type: str,
    context: Dict[str, Any],
    action: Dict[str, Any],
    outcome: Dict[str, Any],
    anonymize: bool = True
) -> Dict[str, Any]:
    """Contribute a successful pattern to the hive"""
    
    # Only accept successful patterns (ROAS > 1.5)
    roas = float(outcome.get("roas", 0))
    if roas < 1.5:
        return {"ok": False, "error": "pattern_not_successful", "min_roas": 1.5}
    
    # Get contributor's OutcomeScore for weighting
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(
                f"https://aigentsy-ame-runtime.onrender.com/score/outcome?username={username}"
            )
            outcome_score = r.json().get("score", 50)
        except Exception:
            outcome_score = 50
    
    pattern_id = f"hive_{uuid4().hex[:8]}"
    
    # Anonymize if requested
    contributor = "anonymous" if anonymize else username
    
    # Strip PII from context
    safe_context = {
        k: v for k, v in context.items()
        if k not in ["email", "phone", "name", "address", "ip"]
    }
    
    pattern = {
        "id": pattern_id,
        "contributor": contributor,
        "contributor_score": outcome_score,
        "type": pattern_type,
        "context": safe_context,
        "action": action,
        "outcome": {
            "roas": roas,
            "revenue_usd": outcome.get("revenue_usd"),
            "cost_usd": outcome.get("cost_usd")
        },
        "weight": calculate_pattern_weight(outcome_score, roas),
        "contributed_at": now_iso(),
        "usage_count": 0,
        "avg_success_rate": 0.0
    }
    
    _HIVE_MEMORY.append(pattern)
    
    # Compress if over limit
    if len(_HIVE_MEMORY) > MAX_HIVE_PATTERNS:
        compress_hive()
    
    # Reward contributor
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                json={
                    "username": username,
                    "amount": 0.5,
                    "basis": "hive_contribution",
                    "ref": pattern_id
                }
            )
        except Exception:
            pass
    
    return {"ok": True, "pattern_id": pattern_id, "reward": 0.5}


def calculate_pattern_weight(outcome_score: int, roas: float) -> float:
    """Weight pattern by contributor reputation and performance"""
    # Normalize outcome score (0-100) to 0.5-1.5 multiplier
    score_weight = 0.5 + (outcome_score / 100.0)
    
    # ROAS weight (capped at 5x)
    roas_weight = min(roas, 5.0)
    
    return round(score_weight * roas_weight, 2)


def compress_hive():
    """Keep top 1000 patterns by weight and usage"""
    global _HIVE_MEMORY
    
    # Sort by combined score
    _HIVE_MEMORY.sort(
        key=lambda p: (p["weight"] * 0.6 + p["usage_count"] * 0.4),
        reverse=True
    )
    
    _HIVE_MEMORY = _HIVE_MEMORY[:MAX_HIVE_PATTERNS]


def query_hive(
    context: Dict[str, Any],
    pattern_type: str = None,
    min_weight: float = 1.0,
    limit: int = 5
) -> Dict[str, Any]:
    """Query hive for matching patterns"""
    
    # Filter by type and weight
    filtered = [
        p for p in _HIVE_MEMORY
        if (not pattern_type or p["type"] == pattern_type)
        and p["weight"] >= min_weight
    ]
    
    if not filtered:
        return {"ok": True, "patterns": [], "count": 0}
    
    # Score by context similarity
    scored = []
    for pattern in filtered:
        similarity = calculate_context_similarity(context, pattern["context"])
        scored.append({
            "pattern": pattern,
            "similarity": similarity,
            "combined_score": pattern["weight"] * similarity
        })
    
    # Sort and return top matches
    scored.sort(key=lambda x: x["combined_score"], reverse=True)
    results = [s["pattern"] for s in scored[:limit]]
    
    return {"ok": True, "patterns": results, "count": len(results)}


def calculate_context_similarity(ctx1: Dict[str, Any], ctx2: Dict[str, Any]) -> float:
    """Calculate similarity (0.0 to 1.0)"""
    matches = 0
    total = 0
    
    shared_keys = set(ctx1.keys()) & set(ctx2.keys())
    
    for key in shared_keys:
        total += 1
        if ctx1[key] == ctx2[key]:
            matches += 1
        elif isinstance(ctx1[key], (int, float)) and isinstance(ctx2[key], (int, float)):
            # Numeric similarity (within 20%)
            diff = abs(float(ctx1[key]) - float(ctx2[key]))
            avg = (float(ctx1[key]) + float(ctx2[key])) / 2
            if avg > 0 and diff / avg < 0.2:
                matches += 0.5
    
    return round(matches / total, 2) if total > 0 else 0.0


def report_pattern_usage(
    pattern_id: str,
    success: bool,
    actual_roas: float = None
) -> Dict[str, Any]:
    """Report pattern usage and outcome"""
    
    pattern = next((p for p in _HIVE_MEMORY if p["id"] == pattern_id), None)
    
    if not pattern:
        return {"ok": False, "error": "pattern_not_found"}
    
    # Update usage stats
    pattern["usage_count"] += 1
    
    if actual_roas is not None:
        # Update rolling average success rate
        old_avg = pattern["avg_success_rate"]
        old_count = pattern["usage_count"] - 1
        
        if old_count > 0:
            pattern["avg_success_rate"] = round(
                (old_avg * old_count + actual_roas) / pattern["usage_count"],
                2
            )
        else:
            pattern["avg_success_rate"] = actual_roas
    
    # Adjust weight based on actual performance
    if actual_roas is not None:
        expected_roas = pattern["outcome"]["roas"]
        if actual_roas >= expected_roas * 0.8:
            # Performed well, boost weight
            pattern["weight"] = round(pattern["weight"] * 1.1, 2)
        else:
            # Underperformed, reduce weight
            pattern["weight"] = round(pattern["weight"] * 0.9, 2)
    
    return {"ok": True, "pattern": pattern}


def get_hive_stats() -> Dict[str, Any]:
    """Get hive statistics"""
    
    if not _HIVE_MEMORY:
        return {
            "ok": True,
            "total_patterns": 0,
            "avg_weight": 0.0,
            "total_usage": 0
        }
    
    total_usage = sum(p["usage_count"] for p in _HIVE_MEMORY)
    avg_weight = sum(p["weight"] for p in _HIVE_MEMORY) / len(_HIVE_MEMORY)
    
    # Pattern type distribution
    types = {}
    for p in _HIVE_MEMORY:
        ptype = p["type"]
        types[ptype] = types.get(ptype, 0) + 1
    
    # Top contributors
    contributors = {}
    for p in _HIVE_MEMORY:
        contrib = p["contributor"]
        if contrib != "anonymous":
            contributors[contrib] = contributors.get(contrib, 0) + 1
    
    top_contributors = sorted(contributors.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "ok": True,
        "total_patterns": len(_HIVE_MEMORY),
        "avg_weight": round(avg_weight, 2),
        "total_usage": total_usage,
        "pattern_types": types,
        "top_contributors": [{"username": u, "contributions": c} for u, c in top_contributors],
        "most_used": sorted(_HIVE_MEMORY, key=lambda p: p["usage_count"], reverse=True)[:10]
    }


def get_top_patterns(
    pattern_type: str = None,
    sort_by: str = "weight",
    limit: int = 20
) -> Dict[str, Any]:
    """Get top patterns from hive"""
    
    patterns = _HIVE_MEMORY
    
    if pattern_type:
        patterns = [p for p in patterns if p["type"] == pattern_type]
    
    if sort_by == "weight":
        patterns = sorted(patterns, key=lambda p: p["weight"], reverse=True)
    elif sort_by == "usage":
        patterns = sorted(patterns, key=lambda p: p["usage_count"], reverse=True)
    elif sort_by == "success_rate":
        patterns = sorted(patterns, key=lambda p: p["avg_success_rate"], reverse=True)
    
    return {"ok": True, "patterns": patterns[:limit], "count": len(patterns)}
