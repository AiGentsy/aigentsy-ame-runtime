"""
FULFILLABILITY GATE

Pre-spawn feasibility check — verifies the system can actually operate a SKU
before committing to spawn a business around it.

Four dimensions (weighted):
  1. Token health (0.4) — required API keys/tokens present for this SKU
  2. Engine availability (0.3) — critical Python modules importable
  3. Capacity check (0.2) — active spawns below maximum
  4. Risk policy (0.1) — no blocklisted platforms in demand signal

Score: 0.0 - 1.0, spawn only if >= 0.6
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
ACTIVE_SPAWNS_FILE = DATA_DIR / "active_spawns.json"

MAX_ACTIVE_SPAWNS = 15


# ─── TOKEN REQUIREMENTS PER SKU ─────────────────────────────────────────────
# Pipe-separated values mean "any one of these" (OR logic)

SKU_TOKEN_REQUIREMENTS: Dict[str, List[str]] = {
    # All SKUs need at least one AI provider
    "_base": ["OPENAI_API_KEY|ANTHROPIC_API_KEY|OPENROUTER_API_KEY"],

    # Code SKUs need GitHub
    "react-component": ["GITHUB_TOKEN"],
    "api-endpoint": ["GITHUB_TOKEN"],
    "bug-fix-triage": ["GITHUB_TOKEN"],
    "data-pipeline": ["GITHUB_TOKEN"],
    "db-migration": ["GITHUB_TOKEN"],
    "responsive-page": [],

    # Email SKUs need Resend
    "email-sequence": ["RESEND_API_KEY"],
    "email-copy-set": ["RESEND_API_KEY"],

    # Design/content SKUs — AI-only, no extra tokens
    "logo-design": [],
    "ui-mockup": [],
    "social-media-kit": [],
    "blog-post-seo": [],
    "product-descriptions": [],
    "landing-page-copy": [],
    "ad-creative-set": [],

    # Marketing/automation
    "landing-page": ["VERCEL_TOKEN"],
    "shopify-theme-fix": [],
    "zapier-workflow": [],
    "analytics-dashboard": [],
    "data-cleanup": [],
}

# Blocklisted platforms — don't auto-spawn if demand comes only from these
BLOCKLISTED_PLATFORMS = {
    "darkweb",
    "tor",
    "paste_sites",
}

# Critical engines that must be importable
CRITICAL_ENGINES = [
    "polymorphic_execution_engine",
    "sku_orchestrator",
]


# ─── TOKEN HEALTH ────────────────────────────────────────────────────────────

def check_token_health(sku_id: str) -> Dict[str, Any]:
    """
    Check if required API tokens are present for this SKU.

    Returns: {"healthy": bool, "present": [], "missing": [], "score": 0-1}
    """
    requirements = SKU_TOKEN_REQUIREMENTS.get("_base", []) + \
                   SKU_TOKEN_REQUIREMENTS.get(sku_id, [])

    present = []
    missing = []

    for req in requirements:
        # Pipe-separated = OR logic (any one present is fine)
        alternatives = req.split("|")
        found = False
        for alt in alternatives:
            if os.environ.get(alt.strip()):
                found = True
                present.append(alt.strip())
                break

        if not found:
            missing.append(req)

    total = len(requirements)
    score = len(present) / max(total, 1) if total > 0 else 1.0

    return {
        "healthy": len(missing) == 0,
        "present": present,
        "missing": missing,
        "score": round(score, 2),
    }


# ─── ENGINE AVAILABILITY ────────────────────────────────────────────────────

def _check_engine_availability() -> Dict[str, Any]:
    """
    Check if critical Python modules can be imported.

    Returns: {"available": bool, "engines": dict, "score": 0-1}
    """
    results = {}
    for engine in CRITICAL_ENGINES:
        try:
            __import__(engine)
            results[engine] = True
        except ImportError:
            results[engine] = False

    available_count = sum(1 for v in results.values() if v)
    total = len(results)

    return {
        "available": all(results.values()),
        "engines": results,
        "score": round(available_count / max(total, 1), 2),
    }


# ─── CAPACITY CHECK ─────────────────────────────────────────────────────────

def _get_active_spawn_count() -> int:
    """Count currently active spawns."""
    if not ACTIVE_SPAWNS_FILE.exists():
        return 0
    try:
        data = json.loads(ACTIVE_SPAWNS_FILE.read_text())
        active = [s for s in data if s.get("status") == "active"]
        return len(active)
    except Exception:
        return 0


def _check_capacity() -> Dict[str, Any]:
    """
    Check if spawn capacity is available.

    Returns: {"available": bool, "active": int, "max": int, "score": 0-1}
    """
    active = _get_active_spawn_count()
    available = active < MAX_ACTIVE_SPAWNS

    # Score: linear decay as we approach max
    score = max(0.0, 1.0 - (active / MAX_ACTIVE_SPAWNS))

    return {
        "available": available,
        "active": active,
        "max": MAX_ACTIVE_SPAWNS,
        "score": round(score, 2),
    }


# ─── RISK POLICY ─────────────────────────────────────────────────────────────

def _check_risk_policy(demand_signal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if demand comes from acceptable platforms.

    Returns: {"safe": bool, "blocklisted": [], "score": 0-1}
    """
    platforms = demand_signal.get("platforms", {})
    if not platforms:
        return {"safe": True, "blocklisted": [], "score": 1.0}

    blocklisted_found = [p for p in platforms.keys() if p in BLOCKLISTED_PLATFORMS]
    total_demand = sum(platforms.values())
    blocklisted_demand = sum(platforms.get(p, 0) for p in blocklisted_found)

    if total_demand == 0:
        return {"safe": True, "blocklisted": [], "score": 1.0}

    # If >50% of demand is from blocklisted sources, fail
    blocklisted_pct = blocklisted_demand / total_demand
    safe = blocklisted_pct < 0.5

    return {
        "safe": safe,
        "blocklisted": blocklisted_found,
        "blocklisted_pct": round(blocklisted_pct, 4),
        "score": round(1.0 - blocklisted_pct, 2),
    }


# ─── COMPOSITE SCORE ─────────────────────────────────────────────────────────

def fulfillability_score(sku_id: str, demand_signal: Optional[Dict] = None) -> float:
    """
    Compute composite fulfillability score (0.0 - 1.0).

    Weighted components:
      - token_health: 0.4
      - engine_availability: 0.3
      - capacity: 0.2
      - risk_policy: 0.1

    Spawn only if score >= 0.6
    """
    demand_signal = demand_signal or {}

    token = check_token_health(sku_id)
    engine = _check_engine_availability()
    capacity = _check_capacity()
    risk = _check_risk_policy(demand_signal)

    score = (
        token["score"] * 0.4
        + engine["score"] * 0.3
        + capacity["score"] * 0.2
        + risk["score"] * 0.1
    )

    return round(score, 2)


def get_blocking_issues(sku_id: str, demand_signal: Optional[Dict] = None) -> List[str]:
    """Get human-readable list of issues blocking this SKU from spawning."""
    demand_signal = demand_signal or {}
    issues = []

    token = check_token_health(sku_id)
    if not token["healthy"]:
        for m in token["missing"]:
            alternatives = m.split("|")
            if len(alternatives) > 1:
                issues.append(f"Missing one of: {', '.join(alternatives)}")
            else:
                issues.append(f"Missing {m}")

    engine = _check_engine_availability()
    if not engine["available"]:
        for eng, ok in engine["engines"].items():
            if not ok:
                issues.append(f"Engine not importable: {eng}")

    capacity = _check_capacity()
    if not capacity["available"]:
        issues.append(f"Capacity full: {capacity['active']}/{capacity['max']} active spawns")

    risk = _check_risk_policy(demand_signal)
    if not risk["safe"]:
        issues.append(
            f"High-risk demand sources: {', '.join(risk['blocklisted'])} "
            f"({risk.get('blocklisted_pct', 0)*100:.0f}% of demand)"
        )

    return issues


def get_full_assessment(sku_id: str, demand_signal: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Full assessment with all sub-scores and blocking issues.
    Used for API responses and debugging.
    """
    demand_signal = demand_signal or {}

    token = check_token_health(sku_id)
    engine = _check_engine_availability()
    capacity = _check_capacity()
    risk = _check_risk_policy(demand_signal)
    score = fulfillability_score(sku_id, demand_signal)
    issues = get_blocking_issues(sku_id, demand_signal)

    return {
        "sku_id": sku_id,
        "score": score,
        "can_spawn": score >= 0.6,
        "blocking_issues": issues,
        "components": {
            "token_health": token,
            "engine_availability": engine,
            "capacity": capacity,
            "risk_policy": risk,
        },
    }
