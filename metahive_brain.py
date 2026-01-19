"""
═══════════════════════════════════════════════════════════════════════════════
METAHIVE BRAIN v2.0 - THE COLLECTIVE INTELLIGENCE LAYER
═══════════════════════════════════════════════════════════════════════════════

The MetaHive is the shared consciousness of the AiGentsy platform.
Every successful pattern, insight, and strategy flows here.
Every user benefits from the collective intelligence of all users.

INTEGRATION WITH AI FAMILY BRAIN:
- AI model performance patterns are shared across users
- Best model→task mappings propagate platform-wide
- Teaching moments become collective knowledge
- Cross-pollination events become hive patterns

THE KNOWLEDGE HIERARCHY:
┌─────────────────────────────────────────────────────────────────────────────┐
│  LEVEL 3: AI FAMILY BRAIN (per-instance learning)                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Which AI model works best for which task                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              │ exports to                                   │
│                              ▼                                              │
│  LEVEL 2: YIELD MEMORY (per-user learning)                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ What strategies work for THIS specific user                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                              │ contributes to                               │
│                              ▼                                              │
│  LEVEL 1: METAHIVE (platform-wide learning)                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Best patterns from ALL users, shared with EVERYONE                    │ │
│  │ AI family learnings propagated platform-wide                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

PATTERN TYPES:
- monetization_strategy: Revenue-generating strategies
- content_template: High-converting content patterns
- outreach_sequence: Successful outreach flows
- pricing_insight: Optimal pricing discoveries
- fulfillment_workflow: Delivery patterns that delight
- ai_routing: Best AI model for task type
- ai_teaching: Teaching moments between models
- ai_specialization: Emerged model specializations
- opportunity_signal: Discovery patterns that convert

═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import httpx
import json
import hashlib

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

MAX_HIVE_PATTERNS = 5000  # Increased for AI family patterns
MAX_PATTERNS_PER_TYPE = 500
MIN_ROAS_FOR_CONTRIBUTION = 1.2  # Lowered to capture more patterns
MIN_QUALITY_FOR_AI_PATTERN = 0.7
PATTERN_DECAY_DAYS = 90  # Patterns lose weight over time
AIGX_CONTRIBUTION_REWARD = 0.5
AIGX_TEACHING_REWARD = 1.0  # Extra reward for AI teaching moments


class PatternType(str, Enum):
    # Business patterns
    MONETIZATION_STRATEGY = "monetization_strategy"
    CONTENT_TEMPLATE = "content_template"
    OUTREACH_SEQUENCE = "outreach_sequence"
    PRICING_INSIGHT = "pricing_insight"
    FULFILLMENT_WORKFLOW = "fulfillment_workflow"
    OPPORTUNITY_SIGNAL = "opportunity_signal"
    NEGOTIATION_TACTIC = "negotiation_tactic"
    UPSELL_PATTERN = "upsell_pattern"
    
    # AI Family patterns (NEW)
    AI_ROUTING = "ai_routing"
    AI_TEACHING = "ai_teaching"
    AI_SPECIALIZATION = "ai_specialization"
    AI_ENSEMBLE = "ai_ensemble"
    AI_CROSS_POLLINATION = "ai_cross_pollination"
    # V111-V112 Revenue Engine Patterns
    UACR_FULFILLMENT = "uacr_fulfillment"
    RECEIVABLES_ADVANCE = "receivables_advance"
    PAYMENTS_ROUTING = "payments_routing"
    MARKET_MAKER_SPREAD = "market_maker_spread"
    TRANCHE_ALLOCATION = "tranche_allocation"
    OFFER_SYNDICATION_PATTERN = "offer_syndication_pattern"
    GAP_HARVESTER_DISCOVERY = "gap_harvester_discovery"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HivePattern:
    """A pattern in the collective hive mind"""
    id: str
    pattern_type: PatternType
    contributor: str  # "anonymous" or username
    contributor_score: int  # OutcomeScore of contributor
    
    # The pattern itself
    context: Dict[str, Any]  # Situation/conditions
    action: Dict[str, Any]  # What was done
    outcome: Dict[str, Any]  # Results achieved
    
    # Metadata
    weight: float = 1.0
    usage_count: int = 0
    success_count: int = 0
    total_revenue_generated: float = 0.0
    avg_success_rate: float = 0.0
    
    # Timestamps
    contributed_at: str = field(default_factory=_now)
    last_used_at: Optional[str] = None
    
    # AI Family specific (NEW)
    ai_model: Optional[str] = None  # Which AI model created this
    task_category: Optional[str] = None  # What task category
    teaching_students: List[str] = field(default_factory=list)  # Models taught
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "pattern_type": self.pattern_type.value if isinstance(self.pattern_type, PatternType) else self.pattern_type,
            "contributor": self.contributor,
            "contributor_score": self.contributor_score,
            "context": self.context,
            "action": self.action,
            "outcome": self.outcome,
            "weight": self.weight,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "total_revenue_generated": self.total_revenue_generated,
            "avg_success_rate": self.avg_success_rate,
            "contributed_at": self.contributed_at,
            "last_used_at": self.last_used_at,
            "ai_model": self.ai_model,
            "task_category": self.task_category,
            "teaching_students": self.teaching_students
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HivePattern':
        return cls(
            id=data["id"],
            pattern_type=data["pattern_type"],
            contributor=data.get("contributor", "anonymous"),
            contributor_score=data.get("contributor_score", 50),
            context=data.get("context", {}),
            action=data.get("action", {}),
            outcome=data.get("outcome", {}),
            weight=data.get("weight", 1.0),
            usage_count=data.get("usage_count", 0),
            success_count=data.get("success_count", 0),
            total_revenue_generated=data.get("total_revenue_generated", 0.0),
            avg_success_rate=data.get("avg_success_rate", 0.0),
            contributed_at=data.get("contributed_at", _now()),
            last_used_at=data.get("last_used_at"),
            ai_model=data.get("ai_model"),
            task_category=data.get("task_category"),
            teaching_students=data.get("teaching_students", [])
        )


@dataclass
class HiveInsight:
    """An emergent insight from hive analysis"""
    id: str
    insight_type: str
    description: str
    supporting_patterns: List[str]  # Pattern IDs
    confidence: float
    estimated_value: float
    applicable_to: List[str]  # User types or industries
    discovered_at: str = field(default_factory=_now)
    times_applied: int = 0
    success_rate: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL HIVE STATE
# ═══════════════════════════════════════════════════════════════════════════════

_HIVE_PATTERNS: List[HivePattern] = []
_HIVE_INSIGHTS: List[HiveInsight] = []
_PATTERN_INDEX: Dict[str, HivePattern] = {}  # id -> pattern
_TYPE_INDEX: Dict[PatternType, List[str]] = defaultdict(list)  # type -> [pattern_ids]

# AI Family specific indexes (NEW)
_AI_MODEL_PATTERNS: Dict[str, List[str]] = defaultdict(list)  # model -> [pattern_ids]
_TASK_CATEGORY_PATTERNS: Dict[str, List[str]] = defaultdict(list)  # category -> [pattern_ids]

# Contributor stats
_CONTRIBUTOR_STATS: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
    "contributions": 0, "total_usage": 0, "total_revenue_impact": 0.0, "reward_earned": 0.0
})


# ═══════════════════════════════════════════════════════════════════════════════
# CONTRIBUTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def contribute_to_hive(
    username: str,
    pattern_type: str,
    context: Dict[str, Any],
    action: Dict[str, Any],
    outcome: Dict[str, Any],
    anonymize: bool = True,
    ai_model: str = None,
    task_category: str = None
) -> Dict[str, Any]:
    """
    Contribute a successful pattern to the hive.
    
    Returns AIGx reward for valuable contributions.
    """
    
    # Validate pattern type
    try:
        ptype = PatternType(pattern_type)
    except ValueError:
        ptype = PatternType.MONETIZATION_STRATEGY
    
    # Validate quality
    roas = float(outcome.get("roas", 0))
    quality = float(outcome.get("quality_score", 0.5))
    
    # AI patterns have different thresholds
    if ptype in [PatternType.AI_ROUTING, PatternType.AI_TEACHING, PatternType.AI_SPECIALIZATION]:
        if quality < MIN_QUALITY_FOR_AI_PATTERN:
            return {"ok": False, "error": "quality_too_low", "min_quality": MIN_QUALITY_FOR_AI_PATTERN}
    else:
        if roas < MIN_ROAS_FOR_CONTRIBUTION:
            return {"ok": False, "error": "roas_too_low", "min_roas": MIN_ROAS_FOR_CONTRIBUTION}
    
    # Get contributor's OutcomeScore
    outcome_score = await _get_outcome_score(username)
    
    # Generate pattern ID
    pattern_id = f"hive_{uuid4().hex[:12]}"
    
    # Create hash for deduplication
    content_hash = hashlib.md5(
        json.dumps({"context": context, "action": action}, sort_keys=True).encode()
    ).hexdigest()[:16]
    
    # Check for duplicates
    for existing in _HIVE_PATTERNS:
        existing_hash = hashlib.md5(
            json.dumps({"context": existing.context, "action": existing.action}, sort_keys=True).encode()
        ).hexdigest()[:16]
        if content_hash == existing_hash:
            # Boost existing pattern instead
            existing.weight *= 1.1
            existing.usage_count += 1
            return {"ok": True, "pattern_id": existing.id, "action": "boosted_existing", "reward": 0.1}
    
    # Anonymize if requested
    contributor = "anonymous" if anonymize else username
    
    # Strip PII
    safe_context = {k: v for k, v in context.items() 
                    if k not in ["email", "phone", "name", "address", "ip", "ssn", "password"]}
    
    # Calculate initial weight
    weight = _calculate_pattern_weight(outcome_score, roas, quality)
    
    # Create pattern
    pattern = HivePattern(
        id=pattern_id,
        pattern_type=ptype,
        contributor=contributor,
        contributor_score=outcome_score,
        context=safe_context,
        action=action,
        outcome={
            "roas": roas,
            "revenue_usd": outcome.get("revenue_usd"),
            "cost_usd": outcome.get("cost_usd"),
            "quality_score": quality
        },
        weight=weight,
        ai_model=ai_model,
        task_category=task_category
    )
    
    # Add to hive
    _HIVE_PATTERNS.append(pattern)
    _PATTERN_INDEX[pattern_id] = pattern
    _TYPE_INDEX[ptype].append(pattern_id)
    
    if ai_model:
        _AI_MODEL_PATTERNS[ai_model].append(pattern_id)
    if task_category:
        _TASK_CATEGORY_PATTERNS[task_category].append(pattern_id)
    
    # Compress if over limit
    if len(_HIVE_PATTERNS) > MAX_HIVE_PATTERNS:
        _compress_hive()
    
    # Update contributor stats
    _CONTRIBUTOR_STATS[username]["contributions"] += 1
    
    # Calculate reward
    reward = AIGX_CONTRIBUTION_REWARD
    if ptype == PatternType.AI_TEACHING:
        reward = AIGX_TEACHING_REWARD
    if quality > 0.9:
        reward *= 1.5
    if roas > 3.0:
        reward *= 1.5
    
    _CONTRIBUTOR_STATS[username]["reward_earned"] += reward
    
    # Credit AIGx
    await _credit_aigx(username, reward, "hive_contribution", pattern_id)
    
    return {"ok": True, "pattern_id": pattern_id, "reward": reward, "weight": weight}


async def contribute_ai_family_learning(
    ai_model: str,
    task_category: str,
    success_rate: float,
    avg_quality: float,
    avg_duration_ms: int,
    total_tasks: int,
    specialization_score: float = None,
    teaching_students: List[str] = None
) -> Dict[str, Any]:
    """
    Contribute AI family learning to the hive.
    
    This propagates AI performance patterns across all users.
    """
    
    pattern_type = PatternType.AI_ROUTING
    if specialization_score and specialization_score > 0.8:
        pattern_type = PatternType.AI_SPECIALIZATION
    if teaching_students:
        pattern_type = PatternType.AI_TEACHING
    
    context = {
        "task_category": task_category,
        "sample_size": total_tasks
    }
    
    action = {
        "model": ai_model,
        "routing_priority": 1 if success_rate > 0.8 else 2 if success_rate > 0.6 else 3
    }
    
    outcome = {
        "success_rate": success_rate,
        "quality_score": avg_quality,
        "avg_duration_ms": avg_duration_ms,
        "roas": success_rate * 2  # Proxy ROAS from success rate
    }
    
    result = await contribute_to_hive(
        username="ai_family_brain",
        pattern_type=pattern_type.value,
        context=context,
        action=action,
        outcome=outcome,
        anonymize=False,
        ai_model=ai_model,
        task_category=task_category
    )
    
    # Update pattern with teaching info
    if result.get("ok") and teaching_students:
        pattern = _PATTERN_INDEX.get(result["pattern_id"])
        if pattern:
            pattern.teaching_students = teaching_students
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def query_hive(
    context: Dict[str, Any],
    pattern_type: str = None,
    min_weight: float = 0.5,
    limit: int = 10,
    ai_model: str = None,
    task_category: str = None
) -> Dict[str, Any]:
    """
    Query hive for matching patterns.
    
    NEW: Can filter by AI model and task category.
    """
    
    # Start with all patterns or filtered by type
    if pattern_type:
        try:
            ptype = PatternType(pattern_type)
            pattern_ids = _TYPE_INDEX.get(ptype, [])
            patterns = [_PATTERN_INDEX[pid] for pid in pattern_ids if pid in _PATTERN_INDEX]
        except ValueError:
            patterns = _HIVE_PATTERNS
    else:
        patterns = _HIVE_PATTERNS
    
    # Filter by AI model
    if ai_model:
        ai_pattern_ids = set(_AI_MODEL_PATTERNS.get(ai_model, []))
        patterns = [p for p in patterns if p.id in ai_pattern_ids]
    
    # Filter by task category
    if task_category:
        task_pattern_ids = set(_TASK_CATEGORY_PATTERNS.get(task_category, []))
        patterns = [p for p in patterns if p.id in task_pattern_ids]
    
    # Filter by weight
    patterns = [p for p in patterns if p.weight >= min_weight]
    
    if not patterns:
        return {"ok": True, "patterns": [], "count": 0}
    
    # Score by context similarity
    scored = []
    for pattern in patterns:
        similarity = _calculate_context_similarity(context, pattern.context)
        
        # Decay factor based on age
        age_days = (_now_dt() - datetime.fromisoformat(pattern.contributed_at.replace("Z", "+00:00"))).days
        decay = max(0.5, 1 - (age_days / PATTERN_DECAY_DAYS))
        
        combined = pattern.weight * similarity * decay
        
        scored.append({
            "pattern": pattern,
            "similarity": similarity,
            "decay": decay,
            "combined_score": combined
        })
    
    # Sort and limit
    scored.sort(key=lambda x: x["combined_score"], reverse=True)
    results = [s["pattern"].to_dict() for s in scored[:limit]]
    
    return {"ok": True, "patterns": results, "count": len(results)}


def get_best_ai_routing(task_category: str) -> Dict[str, Any]:
    """
    Get the best AI model routing for a task category based on hive patterns.
    
    This is the key function for propagating AI family learnings platform-wide.
    """
    
    task_patterns = [
        _PATTERN_INDEX[pid] for pid in _TASK_CATEGORY_PATTERNS.get(task_category, [])
        if pid in _PATTERN_INDEX
    ]
    
    if not task_patterns:
        return {"ok": False, "error": "no_patterns", "recommendation": None}
    
    # Group by model and calculate aggregate scores
    model_scores: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "total_weight": 0.0, "total_success": 0.0, "total_quality": 0.0, "count": 0
    })
    
    for pattern in task_patterns:
        if not pattern.ai_model:
            continue
        
        model = pattern.ai_model
        model_scores[model]["total_weight"] += pattern.weight
        model_scores[model]["total_success"] += pattern.outcome.get("success_rate", 0.5)
        model_scores[model]["total_quality"] += pattern.outcome.get("quality_score", 0.5)
        model_scores[model]["count"] += 1
    
    if not model_scores:
        return {"ok": False, "error": "no_ai_patterns", "recommendation": None}
    
    # Calculate final scores
    rankings = []
    for model, scores in model_scores.items():
        if scores["count"] == 0:
            continue
        
        avg_weight = scores["total_weight"] / scores["count"]
        avg_success = scores["total_success"] / scores["count"]
        avg_quality = scores["total_quality"] / scores["count"]
        
        final_score = avg_weight * 0.3 + avg_success * 0.4 + avg_quality * 0.3
        
        rankings.append({
            "model": model,
            "score": round(final_score, 3),
            "avg_success_rate": round(avg_success, 3),
            "avg_quality": round(avg_quality, 3),
            "sample_size": scores["count"]
        })
    
    rankings.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "ok": True,
        "task_category": task_category,
        "recommendation": rankings[0]["model"] if rankings else None,
        "rankings": rankings,
        "total_patterns": len(task_patterns)
    }


def get_ai_specializations() -> Dict[str, Any]:
    """
    Get all emerged AI specializations from the hive.
    """
    
    spec_patterns = [
        _PATTERN_INDEX[pid] for pid in _TYPE_INDEX.get(PatternType.AI_SPECIALIZATION, [])
        if pid in _PATTERN_INDEX
    ]
    
    specializations = defaultdict(list)
    
    for pattern in spec_patterns:
        if pattern.ai_model and pattern.task_category:
            specializations[pattern.ai_model].append({
                "category": pattern.task_category,
                "success_rate": pattern.outcome.get("success_rate", 0),
                "quality": pattern.outcome.get("quality_score", 0),
                "weight": pattern.weight
            })
    
    # Aggregate
    result = {}
    for model, specs in specializations.items():
        # Sort by success rate
        specs.sort(key=lambda x: x["success_rate"], reverse=True)
        result[model] = {
            "top_specializations": specs[:3],
            "total_categories": len(specs)
        }
    
    return {"ok": True, "specializations": result}


# ═══════════════════════════════════════════════════════════════════════════════
# USAGE REPORTING
# ═══════════════════════════════════════════════════════════════════════════════

def report_pattern_usage(
    pattern_id: str,
    success: bool,
    actual_roas: float = None,
    revenue_generated: float = None
) -> Dict[str, Any]:
    """Report that a pattern was used and its outcome"""
    
    pattern = _PATTERN_INDEX.get(pattern_id)
    if not pattern:
        return {"ok": False, "error": "pattern_not_found"}
    
    # Update usage
    pattern.usage_count += 1
    pattern.last_used_at = _now()
    
    if success:
        pattern.success_count += 1
    
    if revenue_generated:
        pattern.total_revenue_generated += revenue_generated
    
    # Update success rate
    pattern.avg_success_rate = pattern.success_count / pattern.usage_count
    
    # Adjust weight based on performance
    if actual_roas is not None:
        expected = pattern.outcome.get("roas", 1.0)
        if actual_roas >= expected * 0.9:
            pattern.weight = min(pattern.weight * 1.1, 10.0)  # Cap at 10
        elif actual_roas < expected * 0.5:
            pattern.weight = max(pattern.weight * 0.85, 0.1)  # Floor at 0.1
    
    # Update contributor stats
    if pattern.contributor != "anonymous":
        _CONTRIBUTOR_STATS[pattern.contributor]["total_usage"] += 1
        if revenue_generated:
            _CONTRIBUTOR_STATS[pattern.contributor]["total_revenue_impact"] += revenue_generated
    
    return {"ok": True, "pattern": pattern.to_dict()}


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

def get_hive_stats() -> Dict[str, Any]:
    """Get comprehensive hive statistics"""
    
    if not _HIVE_PATTERNS:
        return {"ok": True, "total_patterns": 0, "empty": True}
    
    # Overall stats
    total_usage = sum(p.usage_count for p in _HIVE_PATTERNS)
    total_revenue = sum(p.total_revenue_generated for p in _HIVE_PATTERNS)
    avg_weight = sum(p.weight for p in _HIVE_PATTERNS) / len(_HIVE_PATTERNS)
    avg_success = sum(p.avg_success_rate for p in _HIVE_PATTERNS) / len(_HIVE_PATTERNS)
    
    # By type
    type_stats = {}
    for ptype in PatternType:
        pids = _TYPE_INDEX.get(ptype, [])
        patterns = [_PATTERN_INDEX[pid] for pid in pids if pid in _PATTERN_INDEX]
        if patterns:
            type_stats[ptype.value] = {
                "count": len(patterns),
                "total_usage": sum(p.usage_count for p in patterns),
                "avg_weight": sum(p.weight for p in patterns) / len(patterns)
            }
    
    # AI model stats
    ai_stats = {}
    for model, pids in _AI_MODEL_PATTERNS.items():
        patterns = [_PATTERN_INDEX[pid] for pid in pids if pid in _PATTERN_INDEX]
        if patterns:
            ai_stats[model] = {
                "patterns": len(patterns),
                "avg_success": sum(p.outcome.get("success_rate", 0) for p in patterns) / len(patterns),
                "total_usage": sum(p.usage_count for p in patterns)
            }
    
    # Top contributors
    top_contributors = sorted(
        [(u, s) for u, s in _CONTRIBUTOR_STATS.items() if u != "anonymous"],
        key=lambda x: x[1]["total_revenue_impact"],
        reverse=True
    )[:10]
    
    return {
        "ok": True,
        "total_patterns": len(_HIVE_PATTERNS),
        "total_usage": total_usage,
        "total_revenue_impact": round(total_revenue, 2),
        "avg_weight": round(avg_weight, 2),
        "avg_success_rate": round(avg_success, 2),
        "patterns_by_type": type_stats,
        "ai_model_stats": ai_stats,
        "top_contributors": [
            {"username": u, **s} for u, s in top_contributors
        ],
        "insights_count": len(_HIVE_INSIGHTS)
    }


def get_top_patterns(
    pattern_type: str = None,
    sort_by: str = "weight",  # "weight", "usage", "success_rate", "revenue"
    limit: int = 20,
    ai_model: str = None
) -> Dict[str, Any]:
    """Get top patterns from hive"""
    
    patterns = _HIVE_PATTERNS
    
    if pattern_type:
        try:
            ptype = PatternType(pattern_type)
            pids = _TYPE_INDEX.get(ptype, [])
            patterns = [_PATTERN_INDEX[pid] for pid in pids if pid in _PATTERN_INDEX]
        except ValueError:
            pass
    
    if ai_model:
        ai_pids = set(_AI_MODEL_PATTERNS.get(ai_model, []))
        patterns = [p for p in patterns if p.id in ai_pids]
    
    # Sort
    if sort_by == "weight":
        patterns = sorted(patterns, key=lambda p: p.weight, reverse=True)
    elif sort_by == "usage":
        patterns = sorted(patterns, key=lambda p: p.usage_count, reverse=True)
    elif sort_by == "success_rate":
        patterns = sorted(patterns, key=lambda p: p.avg_success_rate, reverse=True)
    elif sort_by == "revenue":
        patterns = sorted(patterns, key=lambda p: p.total_revenue_generated, reverse=True)
    
    return {
        "ok": True,
        "patterns": [p.to_dict() for p in patterns[:limit]],
        "count": len(patterns[:limit])
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _calculate_pattern_weight(outcome_score: int, roas: float, quality: float) -> float:
    """Calculate initial pattern weight"""
    score_weight = 0.5 + (outcome_score / 100.0)  # 0.5 - 1.5
    roas_weight = min(roas, 5.0)  # Cap at 5
    quality_weight = 0.5 + quality  # 0.5 - 1.5
    
    return round(score_weight * roas_weight * quality_weight / 3, 2)


def _calculate_context_similarity(ctx1: Dict[str, Any], ctx2: Dict[str, Any]) -> float:
    """Calculate similarity between contexts"""
    if not ctx1 or not ctx2:
        return 0.0
    
    matches = 0
    total = 0
    
    shared_keys = set(ctx1.keys()) & set(ctx2.keys())
    
    for key in shared_keys:
        total += 1
        v1, v2 = ctx1[key], ctx2[key]
        
        if v1 == v2:
            matches += 1
        elif isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            # Numeric similarity
            diff = abs(float(v1) - float(v2))
            avg = (float(v1) + float(v2)) / 2
            if avg > 0 and diff / avg < 0.25:
                matches += 0.5
        elif isinstance(v1, str) and isinstance(v2, str):
            # String partial match
            if v1.lower() in v2.lower() or v2.lower() in v1.lower():
                matches += 0.5
    
    return round(matches / total, 2) if total > 0 else 0.0


def _compress_hive():
    """Compress hive to stay under limit"""
    global _HIVE_PATTERNS
    
    # Score each pattern
    scored = []
    for p in _HIVE_PATTERNS:
        age_days = (_now_dt() - datetime.fromisoformat(p.contributed_at.replace("Z", "+00:00"))).days
        decay = max(0.3, 1 - (age_days / PATTERN_DECAY_DAYS))
        
        score = (
            p.weight * 0.3 +
            (p.usage_count / 100) * 0.2 +
            p.avg_success_rate * 0.2 +
            (p.total_revenue_generated / 1000) * 0.2 +
            decay * 0.1
        )
        scored.append((p, score))
    
    # Sort and keep top
    scored.sort(key=lambda x: x[1], reverse=True)
    _HIVE_PATTERNS = [p for p, _ in scored[:MAX_HIVE_PATTERNS]]
    
    # Rebuild indexes
    _rebuild_indexes()


def _rebuild_indexes():
    """Rebuild all indexes after compression"""
    global _PATTERN_INDEX, _TYPE_INDEX, _AI_MODEL_PATTERNS, _TASK_CATEGORY_PATTERNS
    
    _PATTERN_INDEX = {}
    _TYPE_INDEX = defaultdict(list)
    _AI_MODEL_PATTERNS = defaultdict(list)
    _TASK_CATEGORY_PATTERNS = defaultdict(list)
    
    for p in _HIVE_PATTERNS:
        _PATTERN_INDEX[p.id] = p
        ptype = p.pattern_type if isinstance(p.pattern_type, PatternType) else PatternType(p.pattern_type)
        _TYPE_INDEX[ptype].append(p.id)
        if p.ai_model:
            _AI_MODEL_PATTERNS[p.ai_model].append(p.id)
        if p.task_category:
            _TASK_CATEGORY_PATTERNS[p.task_category].append(p.id)


async def _get_outcome_score(username: str) -> int:
    """Get user's OutcomeScore"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"https://aigentsy-ame-runtime.onrender.com/score/outcome?username={username}")
            return r.json().get("score", 50)
    except:
        return 50


async def _credit_aigx(username: str, amount: float, basis: str, ref: str):
    """Credit AIGx to user"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                json={"username": username, "amount": amount, "basis": basis, "ref": ref}
            )
    except:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT/IMPORT FOR AI FAMILY BRAIN INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def export_for_ai_family() -> Dict[str, Any]:
    """
    Export hive learnings for AI Family Brain to import.
    
    This is the key function for propagating platform-wide learnings
    to individual AI Family Brain instances.
    """
    
    # Get AI routing recommendations
    routing = {}
    for task_cat in _TASK_CATEGORY_PATTERNS.keys():
        rec = get_best_ai_routing(task_cat)
        if rec.get("ok") and rec.get("recommendation"):
            routing[task_cat] = {
                "recommended_model": rec["recommendation"],
                "rankings": rec["rankings"][:3]
            }
    
    # Get specializations
    specs = get_ai_specializations()
    
    # Get top teaching moments
    teaching_pids = _TYPE_INDEX.get(PatternType.AI_TEACHING, [])
    teaching_patterns = sorted(
        [_PATTERN_INDEX[pid] for pid in teaching_pids if pid in _PATTERN_INDEX],
        key=lambda p: p.weight,
        reverse=True
    )[:20]
    
    teachings = [
        {
            "teacher": p.ai_model,
            "category": p.task_category,
            "students": p.teaching_students,
            "weight": p.weight
        }
        for p in teaching_patterns
    ]
    
    return {
        "ok": True,
        "routing_recommendations": routing,
        "specializations": specs.get("specializations", {}),
        "teaching_patterns": teachings,
        "total_ai_patterns": sum(len(pids) for pids in _AI_MODEL_PATTERNS.values()),
        "exported_at": _now()
    }


def import_from_ai_family(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Import learnings from AI Family Brain.
    
    This allows local AI Family learnings to propagate to the hive.
    """
    
    imported = 0
    
    # Import specializations
    for model, spec_data in data.get("specializations", {}).items():
        for cat, score in spec_data.items():
            if isinstance(score, (int, float)) and score > 0.7:
                asyncio.create_task(contribute_ai_family_learning(
                    ai_model=model,
                    task_category=cat,
                    success_rate=score,
                    avg_quality=score,
                    avg_duration_ms=1000,
                    total_tasks=50,
                    specialization_score=score
                ))
                imported += 1
    
    # Import teaching patterns
    for teaching in data.get("teaching_patterns", []):
        if teaching.get("teacher") and teaching.get("category"):
            asyncio.create_task(contribute_ai_family_learning(
                ai_model=teaching["teacher"],
                task_category=teaching["category"],
                success_rate=0.9,
                avg_quality=0.9,
                avg_duration_ms=1000,
                total_tasks=20,
                teaching_students=teaching.get("students", [])
            ))
            imported += 1
    
    return {"ok": True, "imported": imported}


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

print("""
═══════════════════════════════════════════════════════════════════════════════
🐝 METAHIVE BRAIN v2.0 - COLLECTIVE INTELLIGENCE LAYER
═══════════════════════════════════════════════════════════════════════════════

   ┌─────────────────────────────────────────────────────────────────────────┐
   │                    THE COLLECTIVE HIVE MIND                              │
   │                                                                          │
   │   USER A ──┐                                       ┌── USER X           │
   │   USER B ──┼──► CONTRIBUTE ──► 🐝 HIVE ──► QUERY ──┼── USER Y           │
   │   USER C ──┘                                       └── USER Z           │
   │                                                                          │
   │   AI Family Brain ──► AI Patterns ──► Platform-Wide AI Routing          │
   │                                                                          │
   └─────────────────────────────────────────────────────────────────────────┘

   Pattern Types: 13 (including 5 AI Family types)
   Max Patterns: 5,000
   AI Family Integration: ✓
   
═══════════════════════════════════════════════════════════════════════════════
""")
