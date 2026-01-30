"""
SKU FLYWHEEL API ROUTES

Endpoints for viewing genomes, demand signals, spawns, and the graduated library.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/sku", tags=["SKU Flywheel"])


class GraduateRequest(BaseModel):
    sku_id: str


# ─── GENOME ─────────────────────────────────────────────────────────────────

@router.get("/genome/{sku_id}")
async def get_genome(sku_id: str):
    """View a SKU genome — pricing, telemetry, playbooks, routing."""
    from sku.sku_genome import get_genome_summary
    summary = get_genome_summary(sku_id)
    if not summary.get("exists"):
        raise HTTPException(status_code=404, detail=f"No genome found for {sku_id}")
    return summary


@router.get("/genome/{sku_id}/full")
async def get_genome_full(sku_id: str):
    """View full genome data including all playbooks and patterns."""
    from sku.sku_genome import load_genome
    genome = load_genome(sku_id)
    if not genome:
        raise HTTPException(status_code=404, detail=f"No genome found for {sku_id}")
    return genome.to_dict()


# ─── GRADUATION ─────────────────────────────────────────────────────────────

@router.post("/graduate")
async def graduate_sku_endpoint(req: GraduateRequest):
    """Manually trigger graduation check + promotion for a SKU."""
    from sku.graduation import check_graduation, graduate_sku
    check = check_graduation(req.sku_id)
    if not check["eligible"]:
        return {
            "ok": False,
            "sku_id": req.sku_id,
            "eligible": False,
            "missing": check["missing"],
            "metrics": check["metrics"],
            "status": check["status"],
        }

    result = await graduate_sku(req.sku_id)
    return result


@router.get("/graduation/{sku_id}")
async def get_graduation_status(sku_id: str):
    """Check graduation eligibility for a SKU."""
    from sku.graduation import check_graduation
    return check_graduation(sku_id)


# ─── DEMAND ─────────────────────────────────────────────────────────────────

@router.get("/demand")
async def get_demand_overview():
    """Get demand clusters and summary across all SKUs."""
    from spawn.demand_aggregator import get_demand_clusters, get_all_demand_summary
    clusters = get_demand_clusters()
    summary = get_all_demand_summary()
    return {
        "spawn_ready_clusters": clusters,
        "summary": summary,
    }


@router.get("/demand/{sku_id}")
async def get_sku_demand(sku_id: str):
    """Get detailed demand stats for a specific SKU (24h, 7d, 30d)."""
    from spawn.demand_aggregator import get_sku_demand
    return get_sku_demand(sku_id)


# ─── SPAWNS ─────────────────────────────────────────────────────────────────

@router.get("/spawns")
async def get_spawns():
    """Get all active auto-spawned businesses."""
    from spawn.spawn_orchestrator import get_active_spawns
    return {
        "spawns": get_active_spawns(),
    }


@router.get("/spawns/performance")
async def get_spawn_performance():
    """Get aggregate telemetry from all active spawns."""
    from spawn.spawn_orchestrator import get_spawn_performance
    return get_spawn_performance()


# ─── LIBRARY ────────────────────────────────────────────────────────────────

@router.get("/library")
async def get_library():
    """Get graduated SKUs available as Business-in-a-Box templates."""
    from sku.graduation import get_graduated_skus, get_incubating_skus
    graduated = get_graduated_skus()
    incubating = get_incubating_skus()
    return {
        "graduated": graduated,
        "graduated_count": len(graduated),
        "incubating_count": len(incubating),
        "incubating_ids": incubating,
    }


# ─── FULFILLABILITY GATE ───────────────────────────────────────────────────

@router.get("/gate/{sku_id}")
async def get_gate_assessment(sku_id: str):
    """Get fulfillability gate assessment for a SKU."""
    from spawn.fulfillability_gate import get_full_assessment
    return get_full_assessment(sku_id)


# ─── ROUTING ────────────────────────────────────────────────────────────────

@router.get("/routing")
async def get_routing_stats():
    """Get monetization routing stats (direct vs platform decisions)."""
    from spawn.monetization_router import get_routing_stats
    return get_routing_stats()


# ─── AGGREGATE STATS ────────────────────────────────────────────────────────

@router.get("/stats")
async def get_flywheel_stats():
    """
    Aggregate SKU Flywheel stats — demand, spawns, graduation, routing
    all in one view.
    """
    from spawn.demand_aggregator import get_demand_clusters, get_all_demand_summary
    from spawn.spawn_orchestrator import get_active_spawns, get_spawn_performance
    from spawn.monetization_router import get_routing_stats
    from sku.graduation import get_graduated_skus, get_incubating_skus
    from sku.sku_genome import list_all_genomes

    genomes = list_all_genomes()
    clusters = get_demand_clusters()
    spawns = get_active_spawns()
    graduated = get_graduated_skus()
    incubating = get_incubating_skus()
    performance = get_spawn_performance()
    routing = get_routing_stats()
    demand_summary = get_all_demand_summary()

    return {
        "genomes": {
            "total": len(genomes),
            "incubating": len(incubating),
            "graduated": len(graduated),
        },
        "demand": {
            "tracked_skus": demand_summary.get("total_skus_tracked", 0),
            "spawn_ready": demand_summary.get("spawn_ready_count", 0),
            "top_clusters": clusters[:5],
        },
        "spawns": {
            "total": len(spawns),
            "active": sum(1 for s in spawns if s.get("status") == "active"),
            "total_revenue": performance.get("total_revenue", 0),
            "avg_roi": performance.get("avg_roi", 0),
        },
        "routing": {
            "total_decisions": routing.get("total_decisions", 0),
            "by_path": routing.get("by_path", {}),
            "auto_spin_candidates": routing.get("auto_spin_candidates", []),
        },
    }
