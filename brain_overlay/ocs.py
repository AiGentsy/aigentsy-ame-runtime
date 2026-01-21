"""
OUTCOME CREDIT SCORE (OCS)
==========================

First-class trust metric for every entity (user, vendor, connector, SKU).

OCS drives:
- Pricing: Higher OCS → lower premiums, lower spreads
- Priority: Higher OCS → higher search rank, faster payouts
- Access: Higher OCS → senior tranches, best-bid IFX access
- Trust: Leaving AiGentsy means losing OCS history → switching cost

Formula:
    base = min(1.0, proofs/100)^0.5 * 60
    reliability = max(0, sla_hits - disputes) * 0.2
    tenure = min(20, age_days * 0.05)
    penalty = min(25, disputes * 3)
    OCS = max(0, base + reliability + tenure - penalty)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class OCSEngine:
    """
    Outcome Credit Score calculation and tracking.

    Tracks per entity:
    - Proof count (successful deliveries with proofs)
    - SLA hits (on-time, quality met)
    - Disputes (chargebacks, complaints)
    - Age (tenure on platform)
    """

    # OCS thresholds for tier classification
    TIERS = {
        "elite": 90,      # Top performers
        "trusted": 75,    # Reliable
        "standard": 50,   # Normal
        "probation": 25,  # Needs improvement
        "restricted": 0   # Limited access
    }

    # Pricing multipliers by tier
    PRICING_MULTIPLIERS = {
        "elite": 0.85,      # 15% discount
        "trusted": 0.92,    # 8% discount
        "standard": 1.00,   # Base price
        "probation": 1.10,  # 10% premium
        "restricted": 1.25  # 25% premium
    }

    def __init__(self):
        self._scores: Dict[str, Dict[str, Any]] = {}

    def _get_record(self, entity_id: str) -> Dict[str, Any]:
        """Get or create entity record"""
        if entity_id not in self._scores:
            self._scores[entity_id] = {
                "entity_id": entity_id,
                "proofs": 0,
                "sla_hits": 0,
                "disputes": 0,
                "created_at": _now_iso(),
                "last_updated": _now_iso(),
                "ocs": 50,  # Default starting score
                "tier": "standard"
            }
        return self._scores[entity_id]

    def score(self, entity_id: str) -> float:
        """Calculate current OCS for entity"""
        record = self._get_record(entity_id)
        return self._calculate_score(record)

    def _calculate_score(self, record: Dict[str, Any]) -> float:
        """Calculate OCS from record"""
        proofs = record.get("proofs", 0)
        sla_hits = record.get("sla_hits", 0)
        disputes = record.get("disputes", 0)

        # Calculate age in days
        created = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - created).days

        # Formula components
        base = min(1.0, proofs / 100) ** 0.5 * 60
        reliability = max(0, (sla_hits - disputes)) * 0.2
        tenure = min(20, age_days * 0.05)
        penalty = min(25, disputes * 3)

        ocs = round(max(0, min(100, base + reliability + tenure - penalty)), 2)
        return ocs

    def _get_tier(self, ocs: float) -> str:
        """Get tier for OCS value"""
        for tier, threshold in sorted(self.TIERS.items(), key=lambda x: -x[1]):
            if ocs >= threshold:
                return tier
        return "restricted"

    def record_outcome(
        self,
        entity_id: str,
        success: bool = True,
        sla_met: bool = True,
        proofs: int = 0,
        dispute: bool = False
    ) -> Dict[str, Any]:
        """
        Record an outcome for OCS calculation.

        Args:
            entity_id: Entity identifier
            success: Whether outcome was successful
            sla_met: Whether SLA requirements were met
            proofs: Number of proofs collected
            dispute: Whether there was a dispute

        Returns:
            Updated OCS info
        """
        record = self._get_record(entity_id)
        old_ocs = record["ocs"]

        # Update counts
        if success and proofs > 0:
            record["proofs"] += proofs
        if sla_met:
            record["sla_hits"] += 1
        if dispute:
            record["disputes"] += 1

        # Recalculate
        record["ocs"] = self._calculate_score(record)
        record["tier"] = self._get_tier(record["ocs"])
        record["last_updated"] = _now_iso()

        delta = record["ocs"] - old_ocs

        return {
            "ok": True,
            "entity_id": entity_id,
            "ocs": record["ocs"],
            "delta": round(delta, 2),
            "tier": record["tier"],
            "pricing_multiplier": self.PRICING_MULTIPLIERS[record["tier"]]
        }

    def get_pricing_adjustment(self, entity_id: str) -> Dict[str, Any]:
        """
        Get pricing adjustment based on OCS.

        Higher OCS = lower prices (discount)
        Lower OCS = higher prices (premium/risk)
        """
        record = self._get_record(entity_id)
        ocs = record["ocs"]
        tier = self._get_tier(ocs)

        # Calculate continuous adjustment (not just tier buckets)
        # OCS 50 = 1.0x, OCS 100 = 0.85x, OCS 0 = 1.25x
        continuous_mult = 1.0 - (ocs - 50) / 200  # Range: 0.75 to 1.25

        # Blend with tier multiplier
        tier_mult = self.PRICING_MULTIPLIERS[tier]
        final_mult = (continuous_mult + tier_mult) / 2

        return {
            "ocs": ocs,
            "tier": tier,
            "tier_multiplier": tier_mult,
            "continuous_multiplier": round(continuous_mult, 3),
            "final_multiplier": round(final_mult, 3),
            "discount_pct": round((1 - final_mult) * 100, 1)
        }

    def get_access_level(self, entity_id: str) -> Dict[str, Any]:
        """
        Get access permissions based on OCS.

        Controls:
        - IFX best-bid access
        - Senior tranche eligibility
        - Prime placement
        - Fast payout
        """
        record = self._get_record(entity_id)
        ocs = record["ocs"]
        tier = self._get_tier(ocs)

        return {
            "ocs": ocs,
            "tier": tier,
            "permissions": {
                "ifx_best_bid": ocs >= 75,
                "senior_tranche": ocs >= 80,
                "prime_placement": ocs >= 70,
                "fast_payout": ocs >= 60,
                "pg_eligible": ocs >= 50,
                "standard_access": ocs >= 25
            }
        }

    def get_entity_details(self, entity_id: str) -> Dict[str, Any]:
        """Get full OCS details for entity"""
        record = self._get_record(entity_id)
        return {
            "ok": True,
            **record,
            "pricing": self.get_pricing_adjustment(entity_id),
            "access": self.get_access_level(entity_id)
        }

    def get_leaderboard(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top entities by OCS"""
        entities = sorted(
            self._scores.values(),
            key=lambda x: x.get("ocs", 0),
            reverse=True
        )
        return [{
            "entity_id": e["entity_id"],
            "ocs": e["ocs"],
            "tier": self._get_tier(e["ocs"]),
            "proofs": e["proofs"],
            "sla_hits": e["sla_hits"]
        } for e in entities[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        """Get OCS system statistics"""
        if not self._scores:
            return {"total_entities": 0}

        scores = [r["ocs"] for r in self._scores.values()]
        by_tier = defaultdict(int)
        for r in self._scores.values():
            by_tier[self._get_tier(r["ocs"])] += 1

        return {
            "total_entities": len(self._scores),
            "avg_ocs": round(sum(scores) / len(scores), 1),
            "median_ocs": round(sorted(scores)[len(scores) // 2], 1),
            "by_tier": dict(by_tier)
        }


# Module-level singleton
_ocs_engine = OCSEngine()


def score_entity(entity_id: str) -> float:
    """Get OCS for entity"""
    return _ocs_engine.score(entity_id)


def get_ocs(entity_id: str) -> float:
    """Alias for score_entity"""
    return _ocs_engine.score(entity_id)


def record_outcome(entity_id: str, **kwargs) -> Dict[str, Any]:
    """Record outcome for OCS"""
    return _ocs_engine.record_outcome(entity_id, **kwargs)


def get_pricing_adjustment(entity_id: str) -> Dict[str, Any]:
    """Get pricing adjustment from OCS"""
    return _ocs_engine.get_pricing_adjustment(entity_id)


def get_access_level(entity_id: str) -> Dict[str, Any]:
    """Get access permissions from OCS"""
    return _ocs_engine.get_access_level(entity_id)
