"""
SKU GENOME — Per-SKU Brain

Each of the 20 fulfillment SKUs gets a genome that accumulates operational wisdom:
- Pricing intelligence (floor/target/ceiling, reputation bands, seasonality)
- Playbooks (outreach, fulfillment, objection handling — versioned)
- Routing (best channels, conversion rates per channel)
- Telemetry (wins, fails, revenue, CSAT, time-to-close)
- Quality gates (QA checks before delivery)
- MetaHive pattern sync (top patterns pulled from collective intelligence)

The genome is the bridge between discovery demand signals and intelligent fulfillment.
It does NOT duplicate existing brain systems — it AGGREGATES from them:
- MetaHive → top patterns for this SKU's domain
- Yield Memory → user-specific success patterns
- Reputation Pricing → dynamic price multipliers
- Outcome Oracle → proof-backed telemetry
"""

import json
import logging
import os
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
GENOMES_DIR = DATA_DIR / "genomes"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── SKU GENOME DATACLASS ───────────────────────────────────────────────────

@dataclass
class SKUGenome:
    sku_id: str
    version: str = "0.1.0"
    status: str = "incubating"  # incubating | graduated | retired
    created_at: str = ""
    graduated_at: Optional[str] = None

    # Market segments this SKU serves (learned over time)
    segments: List[str] = field(default_factory=list)

    # Versioned playbooks — accumulated from fulfillment cycles
    playbooks: Dict[str, Any] = field(default_factory=lambda: {
        "outreach": [],
        "fulfillment": [],
        "objection_handling": [],
    })

    # Dynamic pricing — initialized from sku_catalog_v2.json, refined via outcomes
    pricing: Dict[str, Any] = field(default_factory=lambda: {
        "floor": 0.0,
        "target": 0.0,
        "ceiling": 0.0,
        "reputation_bands": {},
        "seasonality": {},
    })

    # Channel routing — learned from execution outcomes
    routing: Dict[str, Any] = field(default_factory=lambda: {
        "best_channels": [],
        "fallback_channels": [],
        "channel_conversion_rates": {},
    })

    # QA gates required before delivery
    quality_gates: List[Dict[str, Any]] = field(default_factory=list)

    # Telemetry — accumulated stats from real fulfillment
    telemetry: Dict[str, Any] = field(default_factory=lambda: {
        "wins": 0,
        "fails": 0,
        "total_revenue": 0.0,
        "total_cost": 0.0,
        "median_ttc_minutes": 0,
        "preview_to_deposit_rate": 0.0,
        "csat_scores": [],
        "refund_count": 0,
        "defect_count": 0,
        "fulfillment_count": 0,
        "previews_sent": 0,
        "deposits_received": 0,
    })

    # Success definitions — thresholds for graduation
    success_definitions: Dict[str, float] = field(default_factory=lambda: {
        "min_roi": 1.6,
        "min_csat": 4.5,
        "max_refund_rate": 0.03,
        "max_defect_rate": 0.02,
    })

    # Top MetaHive pattern IDs relevant to this SKU
    top_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── PERSISTENCE ─────────────────────────────────────────────────────────────

def _genome_path(sku_id: str) -> Path:
    return GENOMES_DIR / f"{sku_id}.json"


def load_genome(sku_id: str) -> Optional[SKUGenome]:
    """Load genome from data/genomes/{sku_id}.json"""
    path = _genome_path(sku_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return SKUGenome(**data)
    except Exception as e:
        logger.error(f"Failed to load genome {sku_id}: {e}")
        return None


def save_genome(genome: SKUGenome) -> bool:
    """Atomic write: .tmp → os.replace()"""
    GENOMES_DIR.mkdir(parents=True, exist_ok=True)
    path = _genome_path(genome.sku_id)
    tmp_path = str(path) + ".tmp"
    try:
        data = genome.to_dict()
        Path(tmp_path).write_text(json.dumps(data, indent=2, default=str))
        os.replace(tmp_path, str(path))
        logger.info(f"Genome saved: {genome.sku_id} v{genome.version} ({genome.status})")

        # Also persist to JSONBin for cross-deploy survival
        try:
            from brain_persistence import get_persistence
            bp = get_persistence()
            bp._save_to_jsonbin(f"genome_{genome.sku_id}", data)
        except Exception:
            pass  # JSONBin is best-effort

        return True
    except Exception as e:
        logger.error(f"Failed to save genome {genome.sku_id}: {e}")
        # Clean up tmp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False


def list_all_genomes() -> List[SKUGenome]:
    """Load all genomes from disk."""
    genomes = []
    if not GENOMES_DIR.exists():
        return genomes
    for f in GENOMES_DIR.glob("*.json"):
        g = load_genome(f.stem)
        if g:
            genomes.append(g)
    return genomes


# ─── GENOME CREATION ─────────────────────────────────────────────────────────

def _load_sku_catalog() -> List[Dict]:
    """Load the v2 SKU catalog for base prices."""
    v2_file = DATA_DIR / "sku_catalog_v2.json"
    if not v2_file.exists():
        return []
    try:
        data = json.loads(v2_file.read_text())
        return data.get("skus", [])
    except Exception:
        return []


def _get_arm_multipliers() -> Dict[str, Dict]:
    """Pull ARM multipliers from reputation_knobs for pricing bands."""
    try:
        from reputation_knobs import ARM_MULTIPLIERS
        return ARM_MULTIPLIERS
    except ImportError:
        # Hardcoded fallback matching reputation_knobs.py
        return {
            "bronze": {"floor": 0.80, "ceiling": 1.00, "recommended": 0.90},
            "silver": {"floor": 0.90, "ceiling": 1.10, "recommended": 1.00},
            "gold": {"floor": 1.00, "ceiling": 1.30, "recommended": 1.15},
            "platinum": {"floor": 1.20, "ceiling": 1.50, "recommended": 1.35},
            "diamond": {"floor": 1.40, "ceiling": 1.80, "recommended": 1.60},
        }


def create_genome(sku_id: str) -> SKUGenome:
    """
    Create a new genome for a fulfillment SKU.
    Initializes pricing from sku_catalog_v2.json and reputation bands from ARM.
    """
    # Check if genome already exists
    existing = load_genome(sku_id)
    if existing:
        logger.info(f"Genome already exists for {sku_id}, returning existing")
        return existing

    # Load catalog for base price
    catalog = _load_sku_catalog()
    base_price = 0.0
    sku_title = sku_id.replace("-", " ").title()
    sku_category = ""
    sku_description = ""
    sla_minutes = 60

    for entry in catalog:
        if entry.get("sku_id") == sku_id:
            base_price = float(entry.get("base_price", 0))
            sku_title = entry.get("title", sku_title)
            sku_category = entry.get("category", "")
            sku_description = entry.get("description", "")
            sla_minutes = int(entry.get("sla_minutes", 60))
            break

    # Build pricing with reputation bands
    arm = _get_arm_multipliers()
    reputation_bands = {}
    for tier_name, multipliers in arm.items():
        reputation_bands[tier_name] = multipliers.get("recommended", 1.0)

    genome = SKUGenome(
        sku_id=sku_id,
        created_at=_now(),
        segments=[sku_category] if sku_category else [],
        pricing={
            "floor": round(base_price * 0.7, 2),
            "target": round(base_price, 2),
            "ceiling": round(base_price * 1.5, 2),
            "reputation_bands": reputation_bands,
            "seasonality": {},
        },
        quality_gates=[
            {"gate": "deliverable_complete", "required": True},
            {"gate": "client_preview_approved", "required": True},
        ],
    )

    save_genome(genome)
    logger.info(
        f"Created genome: {sku_id} | base_price=${base_price} | "
        f"floor=${genome.pricing['floor']} | ceiling=${genome.pricing['ceiling']}"
    )
    return genome


# ─── TELEMETRY UPDATE ─────────────────────────────────────────────────────────

def update_telemetry(sku_id: str, outcome: Dict[str, Any]) -> Optional[SKUGenome]:
    """
    Update genome telemetry after a fulfillment outcome.

    outcome keys:
        success: bool
        revenue: float
        cost: float
        csat: Optional[float]  (1-5 scale)
        time_to_close_minutes: int
        refund: bool
        defect: bool
    """
    genome = load_genome(sku_id)
    if not genome:
        # Auto-create genome if it doesn't exist
        genome = create_genome(sku_id)

    t = genome.telemetry
    t["fulfillment_count"] = t.get("fulfillment_count", 0) + 1

    if outcome.get("success"):
        t["wins"] = t.get("wins", 0) + 1
    else:
        t["fails"] = t.get("fails", 0) + 1

    t["total_revenue"] = t.get("total_revenue", 0.0) + float(outcome.get("revenue", 0))
    t["total_cost"] = t.get("total_cost", 0.0) + float(outcome.get("cost", 0))

    if outcome.get("csat") is not None:
        scores = t.get("csat_scores", [])
        scores.append(float(outcome["csat"]))
        # Keep last 200 CSAT scores
        if len(scores) > 200:
            scores = scores[-200:]
        t["csat_scores"] = scores

    if outcome.get("refund"):
        t["refund_count"] = t.get("refund_count", 0) + 1

    if outcome.get("defect"):
        t["defect_count"] = t.get("defect_count", 0) + 1

    # Update time-to-close median
    ttc = outcome.get("time_to_close_minutes", 0)
    if ttc > 0:
        # Running median approximation: weighted average
        old_median = t.get("median_ttc_minutes", 0)
        count = t["fulfillment_count"]
        if old_median == 0:
            t["median_ttc_minutes"] = ttc
        else:
            # Exponential moving average
            alpha = min(0.3, 2.0 / (count + 1))
            t["median_ttc_minutes"] = round(old_median * (1 - alpha) + ttc * alpha)

    # Update preview-to-deposit rate
    previews = t.get("previews_sent", 0)
    deposits = t.get("deposits_received", 0)
    if outcome.get("revenue", 0) > 0:
        t["deposits_received"] = deposits + 1
    if previews > 0:
        t["preview_to_deposit_rate"] = round(t["deposits_received"] / previews, 4)

    # Update channel conversion rates from outcome
    channel = outcome.get("channel")
    if channel:
        rates = genome.routing.get("channel_conversion_rates", {})
        ch_data = rates.get(channel, {"attempts": 0, "conversions": 0})
        ch_data["attempts"] = ch_data.get("attempts", 0) + 1
        if outcome.get("success"):
            ch_data["conversions"] = ch_data.get("conversions", 0) + 1
        ch_data["rate"] = round(
            ch_data["conversions"] / max(ch_data["attempts"], 1), 4
        )
        rates[channel] = ch_data
        genome.routing["channel_conversion_rates"] = rates

        # Update best_channels based on conversion rates
        sorted_channels = sorted(
            rates.items(),
            key=lambda x: x[1].get("rate", 0),
            reverse=True,
        )
        genome.routing["best_channels"] = [ch for ch, _ in sorted_channels[:5]]

    genome.telemetry = t
    save_genome(genome)

    logger.info(
        f"Genome telemetry updated: {sku_id} | "
        f"fulfillments={t['fulfillment_count']} | "
        f"wins={t['wins']} | revenue=${t['total_revenue']:.2f}"
    )
    return genome


# ─── PRICING ─────────────────────────────────────────────────────────────────

def get_pricing(sku_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Get dynamic pricing for a SKU using genome data + reputation system.

    context keys (optional):
        outcome_score: int (0-100)
        season: str (q1/q2/q3/q4)
        urgency: str (immediate/short_term/normal)
    """
    context = context or {}
    genome = load_genome(sku_id)
    if not genome:
        return {"price": 0, "tier": "unknown", "multiplier": 1.0, "basis": "no_genome"}

    base_price = genome.pricing.get("target", 0)
    if base_price == 0:
        return {"price": 0, "tier": "unknown", "multiplier": 1.0, "basis": "no_base_price"}

    # Apply reputation pricing if available
    outcome_score = context.get("outcome_score", 50)
    try:
        from reputation_pricing import calculate_reputation_price
        result = calculate_reputation_price(base_price, outcome_score)
        adjusted_price = result.get("adjusted_price", base_price)
        tier = result.get("tier", "competent")
        multiplier = result.get("multiplier", 1.0)
    except ImportError:
        adjusted_price = base_price
        tier = "competent"
        multiplier = 1.0

    # Apply seasonality
    season = context.get("season", "")
    seasonality = genome.pricing.get("seasonality", {})
    if season and season in seasonality:
        season_mult = seasonality[season]
        adjusted_price = round(adjusted_price * season_mult, 2)

    # Apply urgency premium
    urgency = context.get("urgency", "normal")
    if urgency == "immediate":
        adjusted_price = round(adjusted_price * 1.2, 2)  # 20% rush premium
    elif urgency == "short_term":
        adjusted_price = round(adjusted_price * 1.1, 2)  # 10% rush premium

    # Enforce floor/ceiling
    floor = genome.pricing.get("floor", 0)
    ceiling = genome.pricing.get("ceiling", float("inf"))
    adjusted_price = max(floor, min(ceiling, adjusted_price))

    return {
        "price": round(adjusted_price, 2),
        "base_price": base_price,
        "tier": tier,
        "multiplier": multiplier,
        "urgency": urgency,
        "floor": floor,
        "ceiling": ceiling,
        "basis": "genome_pricing",
    }


# ─── PLAYBOOK RETRIEVAL ──────────────────────────────────────────────────────

def get_best_playbook(sku_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Get the best playbook for a SKU, checking genome first then MetaHive.
    """
    context = context or {}
    genome = load_genome(sku_id)

    result = {
        "sku_id": sku_id,
        "source": "default",
        "playbook": {},
    }

    # Check genome playbooks first
    if genome and genome.playbooks:
        # Return the most recent playbook entries
        pb = {}
        for category in ["outreach", "fulfillment", "objection_handling"]:
            entries = genome.playbooks.get(category, [])
            if entries:
                # Return the latest entry
                pb[category] = entries[-1] if isinstance(entries[-1], dict) else {"strategy": entries[-1]}
        if pb:
            result["source"] = "genome"
            result["playbook"] = pb
            return result

    # Fall back to MetaHive
    try:
        from metahive_brain import query_hive
        hive_context = {"sku_id": sku_id}
        if genome and genome.segments:
            hive_context["segments"] = genome.segments
        hive_context.update(context)

        hive_result = query_hive(
            context=hive_context,
            pattern_type="fulfillment_workflow",
            min_weight=0.3,
            limit=5,
        )
        patterns = hive_result.get("patterns", [])
        if patterns:
            result["source"] = "metahive"
            result["playbook"] = {
                "fulfillment": patterns[0].get("action", {}),
                "pattern_ids": [p.get("id") for p in patterns],
                "confidence": patterns[0].get("weight", 0),
            }
            return result
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"MetaHive query failed for {sku_id}: {e}")

    # Default playbook
    result["playbook"] = {
        "outreach": {"strategy": "direct_response", "channel": "email"},
        "fulfillment": {"strategy": "standard_delivery", "sla": "24h"},
        "objection_handling": {"strategy": "value_reframe"},
    }
    return result


# ─── BRAIN SYNC ──────────────────────────────────────────────────────────────

def sync_from_metahive(sku_id: str) -> int:
    """
    Pull top fulfillment patterns from MetaHive matching this SKU's domain.
    Stores pattern IDs in genome.top_patterns for fast lookup.
    """
    genome = load_genome(sku_id)
    if not genome:
        return 0

    synced = 0
    try:
        from metahive_brain import get_top_patterns
        result = get_top_patterns(
            pattern_type="fulfillment_workflow",
            sort_by="success_rate",
            limit=20,
        )
        patterns = result.get("patterns", [])

        # Filter to patterns whose context overlaps with this SKU's segments
        matched_ids = []
        for p in patterns:
            p_context = p.get("context", {})
            p_sku = p_context.get("sku_id", "")
            p_segments = p_context.get("segments", [])

            # Match by sku_id or overlapping segments
            if p_sku == sku_id:
                matched_ids.append(p.get("id"))
                synced += 1
            elif genome.segments and any(s in p_segments for s in genome.segments):
                matched_ids.append(p.get("id"))
                synced += 1

        if matched_ids:
            genome.top_patterns = matched_ids[:20]
            save_genome(genome)

    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"MetaHive sync failed for {sku_id}: {e}")

    logger.info(f"MetaHive sync for {sku_id}: {synced} patterns matched")
    return synced


def sync_from_yield_memory(sku_id: str) -> int:
    """
    Pull user-specific success patterns from Yield Memory.
    Merges successful patterns into genome playbooks.
    """
    genome = load_genome(sku_id)
    if not genome:
        return 0

    synced = 0
    try:
        from yield_memory import find_similar_patterns
        result = find_similar_patterns(
            username="system",
            context={"sku_id": sku_id},
            limit=10,
        )
        patterns = result.get("patterns", [])

        for p in patterns:
            category = p.get("pattern_type", "fulfillment")
            if category not in genome.playbooks:
                genome.playbooks[category] = []

            action = p.get("action", {})
            if action and action not in genome.playbooks[category]:
                genome.playbooks[category].append(action)
                synced += 1

        if synced > 0:
            save_genome(genome)

    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Yield Memory sync failed for {sku_id}: {e}")

    logger.info(f"Yield Memory sync for {sku_id}: {synced} patterns merged")
    return synced


def get_genome_summary(sku_id: str) -> Dict[str, Any]:
    """Return a concise summary of a genome's state."""
    genome = load_genome(sku_id)
    if not genome:
        return {"sku_id": sku_id, "exists": False}

    t = genome.telemetry
    csat_scores = t.get("csat_scores", [])
    fulfillments = t.get("fulfillment_count", 0)
    total_rev = t.get("total_revenue", 0)
    total_cost = t.get("total_cost", 0)

    return {
        "sku_id": sku_id,
        "exists": True,
        "version": genome.version,
        "status": genome.status,
        "created_at": genome.created_at,
        "graduated_at": genome.graduated_at,
        "segments": genome.segments,
        "pricing_target": genome.pricing.get("target", 0),
        "fulfillments": fulfillments,
        "wins": t.get("wins", 0),
        "fails": t.get("fails", 0),
        "total_revenue": total_rev,
        "roi": round(total_rev / max(total_cost, 1), 2),
        "csat_avg": round(statistics.mean(csat_scores), 2) if csat_scores else 0,
        "refund_rate": round(t.get("refund_count", 0) / max(fulfillments, 1), 4),
        "defect_rate": round(t.get("defect_count", 0) / max(fulfillments, 1), 4),
        "best_channels": genome.routing.get("best_channels", []),
        "top_patterns_count": len(genome.top_patterns),
    }
