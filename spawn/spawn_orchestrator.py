"""
SPAWN ORCHESTRATOR — Integration Layer

Bridges discovery demand signals to autonomous business spawning.

Flow:
  1. record_demand() from fulfillability-filtered opportunities
  2. get_demand_clusters() to find spawn-worthy SKUs
  3. For each cluster:
     a. Skip if genome already exists (not retired)
     b. fulfillability_gate check → skip if score < 0.6
     c. create_genome() for new SKU
     d. spawn_sku_business() → mint via sku_orchestrator or template_actionizer
  4. For each opportunity with _matched_sku:
     a. monetization_router.choose_path()
     b. Record routing decision

Also routes per-opportunity monetization decisions and tracks active spawns.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
ACTIVE_SPAWNS_FILE = DATA_DIR / "active_spawns.json"


# ─── SKU → TEMPLATE CHASSIS MAP ─────────────────────────────────────────────
# Maps each of the 20 fulfillment SKUs to one of 3 deployment templates

SKU_TEMPLATE_MAP = {
    # → marketing chassis
    "landing-page": "marketing",
    "ad-creative-set": "marketing",
    "email-sequence": "marketing",
    "blog-post-seo": "marketing",
    "landing-page-copy": "marketing",
    "email-copy-set": "marketing",
    "product-descriptions": "marketing",
    "social-media-kit": "marketing",
    "logo-design": "marketing",
    "ui-mockup": "marketing",
    "shopify-theme-fix": "marketing",
    "zapier-workflow": "marketing",
    "analytics-dashboard": "marketing",
    "data-cleanup": "marketing",
    # → saas chassis
    "react-component": "saas",
    "api-endpoint": "saas",
    "data-pipeline": "saas",
    "db-migration": "saas",
    "responsive-page": "saas",
    "bug-fix-triage": "saas",
}

# Default template variation per chassis
TEMPLATE_DEFAULTS = {
    "marketing": "professional",
    "saas": "technical",
    "social": "creator",
}

# Minimum fulfillability score to proceed with spawn
MIN_FULFILLABILITY_SCORE = 0.6

# Singleton instance
_orchestrator_instance = None


# ─── ACTIVE SPAWNS PERSISTENCE ──────────────────────────────────────────────

def _load_active_spawns() -> List[Dict]:
    """Load active spawns from disk."""
    if not ACTIVE_SPAWNS_FILE.exists():
        return []
    try:
        return json.loads(ACTIVE_SPAWNS_FILE.read_text())
    except Exception:
        return []


def _save_active_spawns(spawns: List[Dict]) -> None:
    """Atomic write for active spawns."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = str(ACTIVE_SPAWNS_FILE) + ".tmp"
    try:
        Path(tmp_path).write_text(json.dumps(spawns, indent=2, default=str))
        os.replace(tmp_path, str(ACTIVE_SPAWNS_FILE))
    except Exception as e:
        logger.error(f"Failed to save active spawns: {e}")
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── SKU CATALOG LOADER ─────────────────────────────────────────────────────

def _load_sku_catalog() -> List[Dict]:
    """Load sku_catalog_v2.json for SKU metadata."""
    v2_file = DATA_DIR / "sku_catalog_v2.json"
    if not v2_file.exists():
        return []
    try:
        data = json.loads(v2_file.read_text())
        return data.get("skus", [])
    except Exception:
        return []


def _get_sku_info(sku_id: str) -> Dict[str, str]:
    """Get title and description from catalog."""
    catalog = _load_sku_catalog()
    for entry in catalog:
        if entry.get("sku_id") == sku_id:
            return {
                "title": entry.get("title", sku_id.replace("-", " ").title()),
                "description": entry.get("description", ""),
                "category": entry.get("category", ""),
                "base_price": entry.get("base_price", 0),
            }
    return {
        "title": sku_id.replace("-", " ").title(),
        "description": "",
        "category": "",
        "base_price": 0,
    }


# ─── SPAWN A SINGLE SKU BUSINESS ────────────────────────────────────────────

async def spawn_sku_business(sku_id: str, demand_data: Dict) -> Dict[str, Any]:
    """
    Spawn a business for a specific SKU.

    1. Map to template chassis
    2. Build user_data from SKU catalog
    3. Try sku_orchestrator.mint_business() first
    4. Fall back to template_actionizer.actionize_template()
    5. Record spawn in active_spawns.json
    """
    chassis = SKU_TEMPLATE_MAP.get(sku_id, "marketing")
    template_choice = TEMPLATE_DEFAULTS.get(chassis, "professional")
    sku_info = _get_sku_info(sku_id)

    # Build user_data for the spawned business
    user_data = {
        "name": f"AiGentsy {sku_info['title']}",
        "email": "auto-spawn@aigentsy.com",
        "business_name": f"{sku_info['title']} by AiGentsy",
        "username": f"aigentsy-{sku_id}",
        "tagline": f"Expert {sku_info['title']} — AI-Powered, Delivered Fast",
        "description": sku_info["description"],
    }

    spawn_result = {
        "sku_id": sku_id,
        "chassis": chassis,
        "template_choice": template_choice,
        "spawned_at": _now_iso(),
        "status": "pending",
        "method": "none",
        "deployment": {},
    }

    # Try sku_orchestrator.mint_business() first
    try:
        from sku_orchestrator import UniversalBusinessOrchestrator
        orch = UniversalBusinessOrchestrator()
        result = orch.mint_business(
            user_id=f"auto-{sku_id}",
            user_data=user_data,
            sku_id=chassis,
            template_choice=template_choice,
        )
        spawn_result["status"] = "active"
        spawn_result["method"] = "sku_orchestrator"
        spawn_result["deployment"] = result
        logger.info(f"SKU business spawned via sku_orchestrator: {sku_id} → {chassis}")
    except Exception as e:
        logger.warning(f"sku_orchestrator failed for {sku_id}: {e}, trying template_actionizer")

        # Fall back to template_actionizer
        try:
            from template_actionizer import actionize_template
            result = await actionize_template(
                username=f"aigentsy-{sku_id}",
                template_type=chassis,
                user_data=user_data,
            )
            spawn_result["status"] = "active"
            spawn_result["method"] = "template_actionizer"
            spawn_result["deployment"] = result
            logger.info(f"SKU business spawned via template_actionizer: {sku_id} → {chassis}")
        except Exception as e2:
            spawn_result["status"] = "failed"
            spawn_result["error"] = str(e2)
            logger.error(f"Both spawn methods failed for {sku_id}: orchestrator={e}, actionizer={e2}")

    # Record spawn
    spawns = _load_active_spawns()
    # Don't duplicate — update if exists
    updated = False
    for i, s in enumerate(spawns):
        if s.get("sku_id") == sku_id:
            spawns[i] = spawn_result
            updated = True
            break
    if not updated:
        spawns.append(spawn_result)
    _save_active_spawns(spawns)

    return spawn_result


# ─── MAIN CYCLE PROCESSOR ───────────────────────────────────────────────────

async def process_cycle_demand(
    opportunities: List[Dict], cycle_id: str
) -> Dict[str, Any]:
    """
    Process demand from a discovery cycle — the main integration point.

    Called after the fulfillability filter in the autonomous orchestrator.

    Steps:
      1. Record demand signals
      2. Get demand clusters exceeding spawn thresholds
      3. For each cluster: gate check → genome creation → spawn
      4. For each opportunity: routing decision (direct vs platform)
    """
    from spawn.demand_aggregator import record_demand, get_demand_clusters
    from spawn.fulfillability_gate import fulfillability_score, get_blocking_issues
    from spawn.monetization_router import (
        choose_path, record_routing_decision, get_routing_scores,
    )
    from sku.sku_genome import create_genome, load_genome

    result = {
        "cycle_id": cycle_id,
        "demand_recorded": {},
        "clusters_found": 0,
        "spawns_triggered": 0,
        "spawns_blocked": 0,
        "blocked_details": [],
        "routing_summary": {"direct": 0, "platform": 0},
    }

    # Step 1: Record demand signals
    demand_result = record_demand(opportunities, cycle_id)
    result["demand_recorded"] = demand_result

    # Step 2: Get demand clusters exceeding thresholds
    clusters = get_demand_clusters()
    result["clusters_found"] = len(clusters)

    # Step 3: For each cluster, attempt spawn
    for cluster in clusters:
        sku_id = cluster["sku_id"]

        # Skip if genome already exists and is not retired
        existing_genome = load_genome(sku_id)
        if existing_genome and existing_genome.status != "retired":
            logger.info(
                f"Skipping spawn for {sku_id}: genome exists "
                f"(status={existing_genome.status})"
            )
            continue

        # Fulfillability gate
        demand_signal = {
            "platforms": cluster.get("platforms", {}),
        }
        score = fulfillability_score(sku_id, demand_signal)

        if score < MIN_FULFILLABILITY_SCORE:
            issues = get_blocking_issues(sku_id, demand_signal)
            result["spawns_blocked"] += 1
            result["blocked_details"].append({
                "sku_id": sku_id,
                "score": score,
                "issues": issues,
            })
            logger.info(
                f"Spawn blocked for {sku_id}: score={score} < {MIN_FULFILLABILITY_SCORE} | "
                f"issues={issues}"
            )
            continue

        # Create genome
        genome = create_genome(sku_id)

        # Sync from MetaHive for initial playbooks
        try:
            from sku.sku_genome import sync_from_metahive
            sync_from_metahive(sku_id)
        except Exception as e:
            logger.warning(f"MetaHive sync failed during spawn of {sku_id}: {e}")

        # Spawn business
        try:
            spawn_result = await spawn_sku_business(sku_id, cluster)
            if spawn_result.get("status") == "active":
                result["spawns_triggered"] += 1
                logger.info(
                    f"Spawn triggered for {sku_id}: demand_score={cluster['demand_score']} "
                    f"method={spawn_result.get('method')}"
                )
            else:
                result["spawns_blocked"] += 1
                result["blocked_details"].append({
                    "sku_id": sku_id,
                    "score": score,
                    "issues": [spawn_result.get("error", "spawn_failed")],
                })
        except Exception as e:
            result["spawns_blocked"] += 1
            result["blocked_details"].append({
                "sku_id": sku_id,
                "score": score,
                "issues": [str(e)],
            })
            logger.error(f"Spawn failed for {sku_id}: {e}")

    # Step 4: Route each opportunity
    for opp in opportunities:
        matched_sku = opp.get("_matched_sku")
        if not matched_sku:
            continue

        path = choose_path(matched_sku, opp)
        scores = get_routing_scores(matched_sku, opp)
        record_routing_decision(matched_sku, path, opp, scores)

        opp["_monetization_path"] = path
        result["routing_summary"][path] = result["routing_summary"].get(path, 0) + 1

    logger.info(
        f"Cycle demand processed: clusters={result['clusters_found']} "
        f"spawns={result['spawns_triggered']} blocked={result['spawns_blocked']} "
        f"routing={result['routing_summary']}"
    )

    return result


# ─── QUERY FUNCTIONS ────────────────────────────────────────────────────────

def get_active_spawns() -> List[Dict]:
    """Get all active spawns."""
    return _load_active_spawns()


def get_spawn_performance() -> Dict[str, Any]:
    """
    Aggregate telemetry from all active spawn genomes.
    """
    spawns = _load_active_spawns()

    if not spawns:
        return {
            "total_spawns": 0,
            "active_spawns": 0,
            "total_revenue": 0,
            "total_cost": 0,
            "avg_roi": 0,
            "best_sku": None,
            "worst_sku": None,
            "by_sku": [],
        }

    from sku.sku_genome import get_genome_summary

    sku_stats = []
    total_rev = 0.0
    total_cost = 0.0
    active_count = 0

    for s in spawns:
        sku_id = s.get("sku_id")
        if not sku_id:
            continue
        if s.get("status") == "active":
            active_count += 1

        summary = get_genome_summary(sku_id)
        if not summary.get("exists"):
            continue

        rev = summary.get("total_revenue", 0)
        cost = max(summary.get("total_revenue", 0) / max(summary.get("roi", 1), 0.01), 1)
        total_rev += rev
        total_cost += cost

        sku_stats.append({
            "sku_id": sku_id,
            "status": s.get("status"),
            "method": s.get("method"),
            "spawned_at": s.get("spawned_at"),
            "fulfillments": summary.get("fulfillments", 0),
            "revenue": rev,
            "roi": summary.get("roi", 0),
            "csat_avg": summary.get("csat_avg", 0),
        })

    # Sort by ROI to find best/worst
    sku_stats.sort(key=lambda x: x.get("roi", 0), reverse=True)

    return {
        "total_spawns": len(spawns),
        "active_spawns": active_count,
        "total_revenue": round(total_rev, 2),
        "total_cost": round(total_cost, 2),
        "avg_roi": round(total_rev / max(total_cost, 1), 2),
        "best_sku": sku_stats[0]["sku_id"] if sku_stats else None,
        "worst_sku": sku_stats[-1]["sku_id"] if sku_stats else None,
        "by_sku": sku_stats,
    }


# ─── SINGLETON ──────────────────────────────────────────────────────────────

class SpawnOrchestrator:
    """Wrapper class for singleton access pattern used by orchestrator hooks."""

    async def process_cycle_demand(
        self, opportunities: List[Dict], cycle_id: str
    ) -> Dict[str, Any]:
        return await process_cycle_demand(opportunities, cycle_id)

    def get_active_spawns(self) -> List[Dict]:
        return get_active_spawns()

    def get_spawn_performance(self) -> Dict[str, Any]:
        return get_spawn_performance()


def get_spawn_orchestrator() -> SpawnOrchestrator:
    """Singleton access for the spawn orchestrator."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = SpawnOrchestrator()
    return _orchestrator_instance
