"""
SKU GRADUATION GATE

Auto-graduates SKUs from "incubating" to "graduated" when quality thresholds are met.

Graduation criteria (ALL must be met):
  - >= 10 paid fulfillments
  - ROI >= 1.6 (total_revenue / total_cost)
  - Average CSAT >= 4.5 (on 1-5 scale)
  - Refund rate <= 3%
  - Defect rate <= 2%

Graduated SKUs:
  - Get version bumped to 1.0.0
  - Enter the user-facing library as deployable Business-in-a-Box templates
  - Have their graduation event contributed to MetaHive for collective learning
"""

import logging
import statistics
from typing import Any, Dict, List

from sku.sku_genome import (
    load_genome,
    save_genome,
    list_all_genomes,
    GENOMES_DIR,
)

logger = logging.getLogger(__name__)


# ─── GRADUATION THRESHOLDS ──────────────────────────────────────────────────

GRADUATION_THRESHOLDS = {
    "paid_fulfillments": 10,
    "roi": 1.6,
    "csat_avg": 4.5,
    "max_refund_rate": 0.03,
    "max_defect_rate": 0.02,
}


# ─── METRICS COMPUTATION ────────────────────────────────────────────────────

def _compute_metrics(telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """Compute graduation metrics from raw telemetry."""
    fulfillments = telemetry.get("fulfillment_count", 0)
    total_rev = telemetry.get("total_revenue", 0.0)
    total_cost = telemetry.get("total_cost", 0.0)
    csat_scores = telemetry.get("csat_scores", [])
    refund_count = telemetry.get("refund_count", 0)
    defect_count = telemetry.get("defect_count", 0)

    # Only count fulfillments with revenue as "paid"
    paid = telemetry.get("wins", 0)

    return {
        "paid_fulfillments": paid,
        "total_fulfillments": fulfillments,
        "roi": round(total_rev / max(total_cost, 1), 2),
        "csat_avg": round(statistics.mean(csat_scores), 2) if csat_scores else 0.0,
        "refund_rate": round(refund_count / max(fulfillments, 1), 4),
        "defect_rate": round(defect_count / max(fulfillments, 1), 4),
        "total_revenue": total_rev,
        "total_cost": total_cost,
        "wins": telemetry.get("wins", 0),
        "fails": telemetry.get("fails", 0),
    }


# ─── GRADUATION CHECK ────────────────────────────────────────────────────────

def check_graduation(sku_id: str) -> Dict[str, Any]:
    """
    Check if a SKU is eligible for graduation.

    Returns:
        {
            "eligible": bool,
            "metrics": dict,    # Current computed metrics
            "missing": list,    # Criteria not yet met
            "sku_id": str,
            "status": str,      # Current genome status
        }
    """
    genome = load_genome(sku_id)
    if not genome:
        return {
            "eligible": False,
            "metrics": {},
            "missing": ["genome_not_found"],
            "sku_id": sku_id,
            "status": "not_found",
        }

    # Already graduated or retired
    if genome.status == "graduated":
        metrics = _compute_metrics(genome.telemetry)
        return {
            "eligible": False,
            "metrics": metrics,
            "missing": [],
            "sku_id": sku_id,
            "status": "already_graduated",
        }

    if genome.status == "retired":
        return {
            "eligible": False,
            "metrics": _compute_metrics(genome.telemetry),
            "missing": ["sku_retired"],
            "sku_id": sku_id,
            "status": "retired",
        }

    metrics = _compute_metrics(genome.telemetry)
    missing = []

    if metrics["paid_fulfillments"] < GRADUATION_THRESHOLDS["paid_fulfillments"]:
        missing.append(
            f"paid_fulfillments: {metrics['paid_fulfillments']}/{GRADUATION_THRESHOLDS['paid_fulfillments']}"
        )

    if metrics["roi"] < GRADUATION_THRESHOLDS["roi"]:
        missing.append(
            f"roi: {metrics['roi']}/{GRADUATION_THRESHOLDS['roi']}"
        )

    if metrics["csat_avg"] < GRADUATION_THRESHOLDS["csat_avg"]:
        missing.append(
            f"csat_avg: {metrics['csat_avg']}/{GRADUATION_THRESHOLDS['csat_avg']}"
        )

    if metrics["refund_rate"] > GRADUATION_THRESHOLDS["max_refund_rate"]:
        missing.append(
            f"refund_rate: {metrics['refund_rate']} > {GRADUATION_THRESHOLDS['max_refund_rate']}"
        )

    if metrics["defect_rate"] > GRADUATION_THRESHOLDS["max_defect_rate"]:
        missing.append(
            f"defect_rate: {metrics['defect_rate']} > {GRADUATION_THRESHOLDS['max_defect_rate']}"
        )

    return {
        "eligible": len(missing) == 0,
        "metrics": metrics,
        "missing": missing,
        "sku_id": sku_id,
        "status": genome.status,
    }


# ─── GRADUATE SKU ─────────────────────────────────────────────────────────────

async def graduate_sku(sku_id: str) -> Dict[str, Any]:
    """
    Graduate a SKU if eligible.

    - Sets status to "graduated", version to "1.0.0"
    - Records graduated_at timestamp
    - Contributes graduation event to MetaHive
    """
    check = check_graduation(sku_id)
    if not check["eligible"]:
        return {
            "ok": False,
            "sku_id": sku_id,
            "reason": "not_eligible",
            "missing": check["missing"],
            "status": check["status"],
        }

    genome = load_genome(sku_id)
    if not genome:
        return {"ok": False, "sku_id": sku_id, "reason": "genome_not_found"}

    # Promote
    from sku.sku_genome import _now
    genome.status = "graduated"
    genome.version = "1.0.0"
    genome.graduated_at = _now()
    save_genome(genome)

    metrics = check["metrics"]
    logger.info(
        f"SKU GRADUATED: {sku_id} | "
        f"paid={metrics['paid_fulfillments']} | "
        f"ROI={metrics['roi']} | "
        f"CSAT={metrics['csat_avg']} | "
        f"revenue=${metrics['total_revenue']:.2f}"
    )

    # Contribute graduation event to MetaHive for collective learning
    try:
        from metahive_brain import contribute_to_hive
        await contribute_to_hive(
            username="system",
            pattern_type="fulfillment_workflow",
            context={
                "sku_id": sku_id,
                "event": "graduation",
                "fulfillments": metrics["paid_fulfillments"],
            },
            action={
                "genome_version": "1.0.0",
                "pricing_target": genome.pricing.get("target", 0),
                "best_channels": genome.routing.get("best_channels", []),
            },
            outcome={
                "roas": max(metrics["roi"], 0.01),
                "quality_score": min(metrics["csat_avg"] / 5.0, 1.0),
            },
        )
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"MetaHive contribution on graduation failed: {e}")

    return {
        "ok": True,
        "sku_id": sku_id,
        "version": genome.version,
        "status": genome.status,
        "graduated_at": genome.graduated_at,
        "metrics": metrics,
    }


# ─── QUERY FUNCTIONS ────────────────────────────────────────────────────────

def get_incubating_skus() -> List[str]:
    """Return sku_ids of all genomes with status == 'incubating'."""
    genomes = list_all_genomes()
    return [g.sku_id for g in genomes if g.status == "incubating"]


def get_graduated_skus() -> List[Dict[str, Any]]:
    """Return summaries of all graduated SKUs (the user-facing library)."""
    genomes = list_all_genomes()
    results = []
    for g in genomes:
        if g.status != "graduated":
            continue

        t = g.telemetry
        csat_scores = t.get("csat_scores", [])
        results.append({
            "sku_id": g.sku_id,
            "version": g.version,
            "graduated_at": g.graduated_at,
            "segments": g.segments,
            "pricing_target": g.pricing.get("target", 0),
            "pricing_floor": g.pricing.get("floor", 0),
            "pricing_ceiling": g.pricing.get("ceiling", 0),
            "total_fulfillments": t.get("fulfillment_count", 0),
            "total_revenue": t.get("total_revenue", 0),
            "roi": round(t.get("total_revenue", 0) / max(t.get("total_cost", 1), 1), 2),
            "csat_avg": round(statistics.mean(csat_scores), 2) if csat_scores else 0,
            "best_channels": g.routing.get("best_channels", []),
            "top_patterns_count": len(g.top_patterns),
        })

    return sorted(results, key=lambda x: x.get("total_revenue", 0), reverse=True)


def get_retirement_candidates() -> List[Dict[str, Any]]:
    """
    Identify SKUs that are underperforming and may need retirement.
    Criteria: >= 5 fulfillments AND (ROI < 0.5 OR refund_rate > 0.15)
    """
    genomes = list_all_genomes()
    candidates = []
    for g in genomes:
        if g.status == "retired":
            continue
        t = g.telemetry
        fulfillments = t.get("fulfillment_count", 0)
        if fulfillments < 5:
            continue

        total_rev = t.get("total_revenue", 0)
        total_cost = t.get("total_cost", 0)
        roi = total_rev / max(total_cost, 1)
        refund_rate = t.get("refund_count", 0) / max(fulfillments, 1)

        if roi < 0.5 or refund_rate > 0.15:
            candidates.append({
                "sku_id": g.sku_id,
                "status": g.status,
                "fulfillments": fulfillments,
                "roi": round(roi, 2),
                "refund_rate": round(refund_rate, 4),
                "reason": "low_roi" if roi < 0.5 else "high_refunds",
            })

    return candidates
