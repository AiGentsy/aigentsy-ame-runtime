"""
DEMAND AGGREGATOR

Accumulates _matched_sku demand signals across discovery cycles.
Detects spawn-worthy demand clusters when rolling thresholds are met.

Storage: data/demand_signals.json — one entry per SKU with timestamped events.

Spawn thresholds (7-day rolling window):
  - Count >= 20 matched opportunities
  - Average opportunity value >= $100
  - At least 10% of opportunities have "immediate" urgency

Events older than 30 days are pruned on each write.
"""

import json
import logging
import os
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
DEMAND_FILE = DATA_DIR / "demand_signals.json"


# ─── THRESHOLDS ──────────────────────────────────────────────────────────────

SPAWN_THRESHOLD_7D_COUNT = 20        # Need 20+ opportunities in 7 days
SPAWN_THRESHOLD_AVG_VALUE = 100.0    # Average value >= $100
SPAWN_THRESHOLD_IMMEDIATE_PCT = 0.10  # At least 10% immediate urgency
ROLLING_WINDOW_DAYS = 30             # Prune events older than 30d


# ─── PERSISTENCE ─────────────────────────────────────────────────────────────

def _load_signals() -> Dict[str, Any]:
    """Load demand signals from disk."""
    if not DEMAND_FILE.exists():
        return {}
    try:
        return json.loads(DEMAND_FILE.read_text())
    except Exception as e:
        logger.error(f"Failed to load demand signals: {e}")
        return {}


def _save_signals(data: Dict[str, Any]) -> bool:
    """Atomic write for demand signals."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = str(DEMAND_FILE) + ".tmp"
    try:
        Path(tmp_path).write_text(json.dumps(data, indent=2, default=str))
        os.replace(tmp_path, str(DEMAND_FILE))
        return True
    except Exception as e:
        logger.error(f"Failed to save demand signals: {e}")
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(ts_str: str) -> datetime:
    """Parse ISO timestamp, handling trailing Z."""
    ts_str = ts_str.rstrip("Z")
    try:
        return datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _prune_events(events: List[Dict], max_age_days: int = ROLLING_WINDOW_DAYS) -> List[Dict]:
    """Remove events older than max_age_days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    return [e for e in events if _parse_ts(e.get("ts", "")) > cutoff]


# ─── RECORD DEMAND ──────────────────────────────────────────────────────────

def record_demand(opportunities: List[Dict], cycle_id: str) -> Dict[str, Any]:
    """
    Record demand signals from a discovery cycle.

    Groups opportunities by _matched_sku and records:
    - count per SKU
    - average value
    - urgency distribution
    - platform distribution

    Returns: {"recorded": int, "skus_updated": int}
    """
    data = _load_signals()
    skus_updated = set()
    recorded = 0

    # Group by matched SKU
    sku_groups: Dict[str, List[Dict]] = {}
    for opp in opportunities:
        matched_sku = opp.get("_matched_sku")
        if not matched_sku:
            continue
        if matched_sku not in sku_groups:
            sku_groups[matched_sku] = []
        sku_groups[matched_sku].append(opp)

    for sku_id, opps in sku_groups.items():
        if sku_id not in data:
            data[sku_id] = {"events": []}

        # Compute stats for this batch
        values = [float(o.get("value", 0) or o.get("estimated_value", 0) or 0) for o in opps]
        avg_value = round(sum(values) / max(len(values), 1), 2)

        urgency_dist = dict(Counter(o.get("_urgency", "normal") for o in opps))
        platform_dist = dict(Counter(o.get("platform", "unknown") for o in opps))

        event = {
            "ts": _now_iso(),
            "count": len(opps),
            "avg_value": avg_value,
            "urgency_dist": urgency_dist,
            "platforms": platform_dist,
            "cycle_id": cycle_id,
        }

        data[sku_id]["events"].append(event)
        data[sku_id]["events"] = _prune_events(data[sku_id]["events"])

        skus_updated.add(sku_id)
        recorded += len(opps)

    _save_signals(data)

    logger.info(
        f"Demand recorded: {recorded} opportunities across {len(skus_updated)} SKUs "
        f"(cycle {cycle_id})"
    )

    return {
        "recorded": recorded,
        "skus_updated": len(skus_updated),
        "sku_ids": list(skus_updated),
    }


# ─── DEMAND CLUSTERS ────────────────────────────────────────────────────────

def _compute_7d_stats(events: List[Dict]) -> Dict[str, Any]:
    """Compute 7-day rolling window stats from events."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    recent = [e for e in events if _parse_ts(e.get("ts", "")) > cutoff]

    if not recent:
        return {
            "count_7d": 0,
            "avg_value": 0.0,
            "immediate_pct": 0.0,
            "total_events": 0,
            "platforms": {},
        }

    total_count = sum(e.get("count", 0) for e in recent)
    total_value = sum(e.get("avg_value", 0) * e.get("count", 1) for e in recent)
    avg_value = round(total_value / max(total_count, 1), 2)

    # Aggregate urgency
    urgency_totals: Dict[str, int] = {}
    for e in recent:
        for u, c in e.get("urgency_dist", {}).items():
            urgency_totals[u] = urgency_totals.get(u, 0) + c

    total_urgency = sum(urgency_totals.values())
    immediate_count = urgency_totals.get("immediate", 0)
    immediate_pct = round(immediate_count / max(total_urgency, 1), 4)

    # Aggregate platforms
    platform_totals: Dict[str, int] = {}
    for e in recent:
        for p, c in e.get("platforms", {}).items():
            platform_totals[p] = platform_totals.get(p, 0) + c

    return {
        "count_7d": total_count,
        "avg_value": avg_value,
        "immediate_pct": immediate_pct,
        "total_events": len(recent),
        "platforms": platform_totals,
        "urgency_dist": urgency_totals,
    }


def get_demand_clusters() -> List[Dict[str, Any]]:
    """
    Get demand clusters exceeding ALL spawn thresholds.

    Returns sorted list of spawn-worthy SKUs with demand scores.
    demand_score = count_7d * avg_value * (1 + immediate_pct)
    """
    data = _load_signals()
    clusters = []

    for sku_id, sku_data in data.items():
        events = sku_data.get("events", [])
        stats = _compute_7d_stats(events)

        if (
            stats["count_7d"] >= SPAWN_THRESHOLD_7D_COUNT
            and stats["avg_value"] >= SPAWN_THRESHOLD_AVG_VALUE
            and stats["immediate_pct"] >= SPAWN_THRESHOLD_IMMEDIATE_PCT
        ):
            demand_score = round(
                stats["count_7d"] * stats["avg_value"] * (1 + stats["immediate_pct"]),
                2,
            )
            clusters.append({
                "sku_id": sku_id,
                "demand_count_7d": stats["count_7d"],
                "avg_value": stats["avg_value"],
                "immediate_pct": stats["immediate_pct"],
                "demand_score": demand_score,
                "platforms": stats["platforms"],
                "urgency_dist": stats.get("urgency_dist", {}),
            })

    clusters.sort(key=lambda x: x["demand_score"], reverse=True)

    logger.info(
        f"Demand clusters: {len(clusters)} SKUs exceed spawn thresholds "
        f"(of {len(data)} tracked)"
    )
    return clusters


def get_sku_demand(sku_id: str) -> Dict[str, Any]:
    """Get detailed demand stats for one SKU across 24h, 7d, and 30d windows."""
    data = _load_signals()
    sku_data = data.get(sku_id, {"events": []})
    events = sku_data.get("events", [])

    if not events:
        return {
            "sku_id": sku_id,
            "has_data": False,
            "windows": {},
        }

    now = datetime.now(timezone.utc)

    windows = {}
    for window_name, days in [("24h", 1), ("7d", 7), ("30d", 30)]:
        cutoff = now - timedelta(days=days)
        recent = [e for e in events if _parse_ts(e.get("ts", "")) > cutoff]

        total_count = sum(e.get("count", 0) for e in recent)
        total_value = sum(e.get("avg_value", 0) * e.get("count", 1) for e in recent)
        avg_value = round(total_value / max(total_count, 1), 2)

        urgency_totals: Dict[str, int] = {}
        for e in recent:
            for u, c in e.get("urgency_dist", {}).items():
                urgency_totals[u] = urgency_totals.get(u, 0) + c

        total_urgency = sum(urgency_totals.values())
        immediate_pct = round(
            urgency_totals.get("immediate", 0) / max(total_urgency, 1), 4
        )

        platform_totals: Dict[str, int] = {}
        for e in recent:
            for p, c in e.get("platforms", {}).items():
                platform_totals[p] = platform_totals.get(p, 0) + c

        windows[window_name] = {
            "count": total_count,
            "avg_value": avg_value,
            "immediate_pct": immediate_pct,
            "urgency_dist": urgency_totals,
            "platforms": platform_totals,
            "event_batches": len(recent),
        }

    # Check spawn readiness
    stats_7d = windows.get("7d", {})
    spawn_ready = (
        stats_7d.get("count", 0) >= SPAWN_THRESHOLD_7D_COUNT
        and stats_7d.get("avg_value", 0) >= SPAWN_THRESHOLD_AVG_VALUE
        and stats_7d.get("immediate_pct", 0) >= SPAWN_THRESHOLD_IMMEDIATE_PCT
    )

    return {
        "sku_id": sku_id,
        "has_data": True,
        "windows": windows,
        "spawn_ready": spawn_ready,
        "thresholds": {
            "count": SPAWN_THRESHOLD_7D_COUNT,
            "avg_value": SPAWN_THRESHOLD_AVG_VALUE,
            "immediate_pct": SPAWN_THRESHOLD_IMMEDIATE_PCT,
        },
    }


def should_spawn(sku_id: str) -> bool:
    """Check if a SKU has enough demand to trigger a spawn."""
    data = _load_signals()
    sku_data = data.get(sku_id, {"events": []})
    events = sku_data.get("events", [])

    if not events:
        return False

    stats = _compute_7d_stats(events)
    return (
        stats["count_7d"] >= SPAWN_THRESHOLD_7D_COUNT
        and stats["avg_value"] >= SPAWN_THRESHOLD_AVG_VALUE
        and stats["immediate_pct"] >= SPAWN_THRESHOLD_IMMEDIATE_PCT
    )


def get_all_demand_summary() -> Dict[str, Any]:
    """Get a summary of all demand signals across all SKUs."""
    data = _load_signals()
    summaries = []

    for sku_id, sku_data in data.items():
        events = sku_data.get("events", [])
        stats_7d = _compute_7d_stats(events)
        summaries.append({
            "sku_id": sku_id,
            "count_7d": stats_7d["count_7d"],
            "avg_value": stats_7d["avg_value"],
            "immediate_pct": stats_7d["immediate_pct"],
            "spawn_ready": should_spawn(sku_id),
        })

    summaries.sort(key=lambda x: x["count_7d"], reverse=True)

    return {
        "total_skus_tracked": len(data),
        "spawn_ready_count": sum(1 for s in summaries if s["spawn_ready"]),
        "skus": summaries,
    }
