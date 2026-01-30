"""
MONETIZATION ROUTER — Dual-Path Decision Engine

For each opportunity matched to a SKU, decides:
  - "direct": AiGentsy fulfills the opportunity directly (Rev Path 1)
  - "platform": Offer as Business-in-a-Box for users to deploy (Rev Path 2)

Scoring model:
  score_direct = 0.40 * payment_proximity
               + 0.25 * ltv
               + 0.20 * brand_lift
               + 0.15 * (1 - complexity)

  score_platform = 0.35 * library_slot
                 + 0.30 * ltv
                 + 0.20 * (1 - complexity)
                 + 0.15 * payment_proximity

Selects "direct" if score_direct >= score_platform, else "platform".

Auto-spin rule: if direct chosen >= 3 times for same SKU in 7d,
                recommend creating a library copy for parallel platform revenue.
"""

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
ROUTING_LOG_FILE = DATA_DIR / "routing_log.json"

# SKUs with high complexity scores (0.7+)
HIGH_COMPLEXITY_SKUS = {
    "data-pipeline", "db-migration", "analytics-dashboard",
    "api-endpoint", "react-component",
}

# SKUs with medium complexity (0.4-0.6)
MEDIUM_COMPLEXITY_SKUS = {
    "shopify-theme-fix", "zapier-workflow", "data-cleanup",
    "email-sequence", "responsive-page", "ui-mockup",
}

# Low complexity SKUs (0.1-0.3) — everything else (content, copy, design)

# Signals indicating recurring/retainer/subscription potential
LTV_SIGNALS = [
    "retainer", "monthly", "ongoing", "recurring", "subscription",
    "long-term", "long term", "continuous", "regular basis",
    "weekly", "biweekly", "quarterly",
]

# Signals indicating budget/bounty is attached
PAYMENT_SIGNALS = [
    "budget", "paying", "paid", "bounty", "reward", "$",
    "rate", "compensation", "fee", "willing to pay",
    "price range", "quote",
]

# Public platforms that provide brand visibility
HIGH_VISIBILITY_PLATFORMS = {
    "reddit", "hackernews", "twitter", "github",
    "producthunt", "indiehackers", "linkedin",
}


# ─── FEATURE EXTRACTION ─────────────────────────────────────────────────────

def _extract_payment_proximity(opportunity: Dict) -> float:
    """
    0-1 score: how close to payment is this opportunity?
    High if budget/bounty present + immediate urgency.
    """
    text = (
        f"{opportunity.get('title', '')} {opportunity.get('body', '')} "
        f"{opportunity.get('text_preview', '')} {opportunity.get('description', '')}"
    ).lower()

    score = 0.0

    # Direct payment signals
    payment_hits = sum(1 for s in PAYMENT_SIGNALS if s in text)
    score += min(payment_hits * 0.15, 0.45)

    # Has explicit value/budget
    value = float(opportunity.get("value", 0) or opportunity.get("estimated_value", 0) or 0)
    if value > 0:
        score += 0.3

    # Urgency boosts payment proximity
    urgency = opportunity.get("_urgency", "normal")
    if urgency == "immediate":
        score += 0.25
    elif urgency == "short_term":
        score += 0.15

    return min(round(score, 2), 1.0)


def _extract_complexity(sku_id: str) -> float:
    """0-1 score: how complex is this SKU to fulfill?"""
    if sku_id in HIGH_COMPLEXITY_SKUS:
        return 0.8
    elif sku_id in MEDIUM_COMPLEXITY_SKUS:
        return 0.5
    else:
        return 0.2


def _extract_brand_lift(opportunity: Dict) -> float:
    """0-1 score: how much brand visibility does fulfilling this give?"""
    platform = opportunity.get("platform", "").lower()
    score = 0.0

    if platform in HIGH_VISIBILITY_PLATFORMS:
        score += 0.5

    # Public engagement (comments, upvotes) indicates visibility
    engagement = int(opportunity.get("engagement", 0) or opportunity.get("score", 0) or 0)
    if engagement > 50:
        score += 0.3
    elif engagement > 10:
        score += 0.15

    # If the opportunity is a public post (not a DM), it has visibility
    if opportunity.get("is_public", True):
        score += 0.2

    return min(round(score, 2), 1.0)


def _extract_ltv(opportunity: Dict) -> float:
    """0-1 score: how likely is this to become recurring revenue?"""
    text = (
        f"{opportunity.get('title', '')} {opportunity.get('body', '')} "
        f"{opportunity.get('text_preview', '')} {opportunity.get('description', '')}"
    ).lower()

    hits = sum(1 for s in LTV_SIGNALS if s in text)
    score = min(hits * 0.2, 0.8)

    # Repeat buyer signal
    if opportunity.get("repeat_buyer"):
        score += 0.2

    return min(round(score, 2), 1.0)


def _check_library_slot(sku_id: str) -> float:
    """1.0 if genome is graduated (has a library slot), else 0.0"""
    try:
        from sku.sku_genome import load_genome
        genome = load_genome(sku_id)
        if genome and genome.status == "graduated":
            return 1.0
    except ImportError:
        pass
    return 0.0


# ─── ROUTING DECISION ────────────────────────────────────────────────────────

def choose_path(sku_id: str, opportunity: Dict) -> str:
    """
    Decide whether to fulfill directly or route to platform.

    Returns: "direct" or "platform"
    """
    payment_proximity = _extract_payment_proximity(opportunity)
    complexity = _extract_complexity(sku_id)
    brand_lift = _extract_brand_lift(opportunity)
    ltv = _extract_ltv(opportunity)
    library_slot = _check_library_slot(sku_id)

    score_direct = (
        0.40 * payment_proximity
        + 0.25 * ltv
        + 0.20 * brand_lift
        + 0.15 * (1 - complexity)
    )

    score_platform = (
        0.35 * library_slot
        + 0.30 * ltv
        + 0.20 * (1 - complexity)
        + 0.15 * payment_proximity
    )

    path = "direct" if score_direct >= score_platform else "platform"

    logger.debug(
        f"Routing {sku_id}: direct={score_direct:.2f} vs platform={score_platform:.2f} "
        f"→ {path} | pp={payment_proximity} cx={complexity} bl={brand_lift} "
        f"ltv={ltv} lib={library_slot}"
    )

    return path


def get_routing_scores(sku_id: str, opportunity: Dict) -> Dict[str, Any]:
    """Get detailed routing scores for debugging/API responses."""
    payment_proximity = _extract_payment_proximity(opportunity)
    complexity = _extract_complexity(sku_id)
    brand_lift = _extract_brand_lift(opportunity)
    ltv = _extract_ltv(opportunity)
    library_slot = _check_library_slot(sku_id)

    score_direct = round(
        0.40 * payment_proximity
        + 0.25 * ltv
        + 0.20 * brand_lift
        + 0.15 * (1 - complexity),
        4,
    )

    score_platform = round(
        0.35 * library_slot
        + 0.30 * ltv
        + 0.20 * (1 - complexity)
        + 0.15 * payment_proximity,
        4,
    )

    return {
        "sku_id": sku_id,
        "chosen_path": "direct" if score_direct >= score_platform else "platform",
        "score_direct": score_direct,
        "score_platform": score_platform,
        "features": {
            "payment_proximity": payment_proximity,
            "complexity": complexity,
            "brand_lift": brand_lift,
            "ltv": ltv,
            "library_slot": library_slot,
        },
    }


# ─── ROUTING LOG ─────────────────────────────────────────────────────────────

def _load_routing_log() -> List[Dict]:
    """Load routing log from disk."""
    if not ROUTING_LOG_FILE.exists():
        return []
    try:
        return json.loads(ROUTING_LOG_FILE.read_text())
    except Exception:
        return []


def _save_routing_log(log: List[Dict]) -> None:
    """Atomic write for routing log."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = str(ROUTING_LOG_FILE) + ".tmp"
    try:
        # Keep last 5000 entries
        if len(log) > 5000:
            log = log[-5000:]
        Path(tmp_path).write_text(json.dumps(log, indent=2, default=str))
        os.replace(tmp_path, str(ROUTING_LOG_FILE))
    except Exception as e:
        logger.error(f"Failed to save routing log: {e}")
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def record_routing_decision(
    sku_id: str, path: str, opportunity: Dict, scores: Optional[Dict] = None
) -> None:
    """Append routing decision to log for analytics."""
    log = _load_routing_log()
    log.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "sku_id": sku_id,
        "path": path,
        "platform": opportunity.get("platform", "unknown"),
        "value": float(opportunity.get("value", 0) or 0),
        "urgency": opportunity.get("_urgency", "normal"),
        "scores": scores or {},
    })
    _save_routing_log(log)


def check_auto_spin_rule(sku_id: str) -> bool:
    """
    If "direct" chosen >= 3 times for this SKU in last 7 days,
    return True — signal that a library copy should be created
    for parallel platform revenue.
    """
    log = _load_routing_log()
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    direct_count = 0
    for entry in log:
        ts_str = entry.get("ts", "").rstrip("Z")
        try:
            ts = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
        except Exception:
            continue

        if (
            ts > cutoff
            and entry.get("sku_id") == sku_id
            and entry.get("path") == "direct"
        ):
            direct_count += 1

    return direct_count >= 3


def get_routing_stats() -> Dict[str, Any]:
    """Aggregate routing stats from log for API responses."""
    log = _load_routing_log()

    if not log:
        return {
            "total_decisions": 0,
            "by_path": {},
            "by_sku": {},
            "auto_spin_candidates": [],
        }

    by_path: Dict[str, int] = {}
    by_sku: Dict[str, Dict[str, int]] = {}

    for entry in log:
        path = entry.get("path", "unknown")
        sku = entry.get("sku_id", "unknown")

        by_path[path] = by_path.get(path, 0) + 1

        if sku not in by_sku:
            by_sku[sku] = {"direct": 0, "platform": 0}
        by_sku[sku][path] = by_sku[sku].get(path, 0) + 1

    # Check auto-spin candidates
    auto_spin = []
    for sku in by_sku:
        if check_auto_spin_rule(sku):
            auto_spin.append(sku)

    return {
        "total_decisions": len(log),
        "by_path": by_path,
        "by_sku": by_sku,
        "auto_spin_candidates": auto_spin,
    }
