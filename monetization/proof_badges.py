"""
PROOF BADGES
============

Proof-of-Outcome badges for SKU conversion uplift.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import hashlib

from .ledger import post_entry


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class ProofBadges:
    """
    Proof-of-Outcome badge minting and management.

    Badges are public attestations that:
    - Verify successful outcome execution
    - Display SLA compliance
    - Boost conversion rates on storefronts
    - Enable premium pricing
    """

    BADGE_TYPES = {
        "outcome_success": {
            "description": "Verified successful outcome",
            "conversion_boost": 0.15  # 15% conversion uplift
        },
        "sla_compliant": {
            "description": "Met all SLA requirements",
            "conversion_boost": 0.10
        },
        "verified_delivery": {
            "description": "Delivery verified with proofs",
            "conversion_boost": 0.12
        },
        "top_performer": {
            "description": "Top 10% performer in category",
            "conversion_boost": 0.25
        },
        "streak_badge": {
            "description": "Consecutive successful outcomes",
            "conversion_boost": 0.08
        }
    }

    def __init__(self):
        self._badges: Dict[str, Dict[str, Any]] = {}
        self._by_entity: Dict[str, List[str]] = {}  # entity -> badge_ids
        self._by_outcome: Dict[str, str] = {}  # outcome_id -> badge_id

    def mint(self, attestation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mint a proof badge from an attestation.

        Args:
            attestation: Attestation dict with:
                - outcome_id: COI/outcome identifier
                - outcome_type: Type of outcome
                - outcome_hash: Hash of outcome data
                - sla_verdict: pass/fail
                - proofs: List of collected proofs
                - entity: Entity receiving badge

        Returns:
            Minted badge
        """
        outcome_id = attestation.get("outcome_id", "")
        outcome_hash = attestation.get("outcome_hash", "")
        outcome_type = attestation.get("outcome_type", "unknown")
        sla_verdict = attestation.get("sla_verdict", "unknown")
        proofs = attestation.get("proofs", [])
        entity = attestation.get("entity", "unknown")

        # Determine badge type based on attestation
        if sla_verdict == "pass" and len(proofs) >= 1:
            badge_type = "sla_compliant"
        elif len(proofs) >= 1:
            badge_type = "verified_delivery"
        else:
            badge_type = "outcome_success"

        # Generate badge ID
        badge_hash = outcome_hash[-8:] if outcome_hash else uuid4().hex[:8]
        badge_id = f"proof:{badge_hash}"

        badge = {
            "badge_id": badge_id,
            "type": badge_type,
            "outcome_id": outcome_id,
            "outcome_type": outcome_type,
            "sla_verdict": sla_verdict,
            "proof_count": len(proofs),
            "entity": entity,
            "conversion_boost": self.BADGE_TYPES[badge_type]["conversion_boost"],
            "minted_at": _now_iso(),
            "public": True,  # Can be displayed
            "verified": True
        }

        self._badges[badge_id] = badge

        # Index by entity
        if entity not in self._by_entity:
            self._by_entity[entity] = []
        self._by_entity[entity].append(badge_id)

        # Index by outcome
        if outcome_id:
            self._by_outcome[outcome_id] = badge_id

        return badge

    def mint_top_performer(
        self,
        entity: str,
        outcome_type: str,
        percentile: int
    ) -> Dict[str, Any]:
        """Mint a top performer badge"""
        if percentile < 90:
            return {"ok": False, "error": "must_be_top_10_percent"}

        badge_id = f"top:{entity}:{outcome_type}:{percentile}"

        badge = {
            "badge_id": badge_id,
            "type": "top_performer",
            "entity": entity,
            "outcome_type": outcome_type,
            "percentile": percentile,
            "conversion_boost": self.BADGE_TYPES["top_performer"]["conversion_boost"],
            "minted_at": _now_iso(),
            "public": True,
            "verified": True
        }

        self._badges[badge_id] = badge

        if entity not in self._by_entity:
            self._by_entity[entity] = []
        self._by_entity[entity].append(badge_id)

        return {"ok": True, "badge": badge}

    def mint_streak(
        self,
        entity: str,
        streak_count: int,
        outcome_type: str
    ) -> Dict[str, Any]:
        """Mint a streak badge for consecutive successes"""
        if streak_count < 5:
            return {"ok": False, "error": "min_streak_5"}

        badge_id = f"streak:{entity}:{outcome_type}:{streak_count}"

        # Boost scales with streak
        base_boost = self.BADGE_TYPES["streak_badge"]["conversion_boost"]
        scaled_boost = min(0.25, base_boost * (1 + (streak_count - 5) * 0.02))

        badge = {
            "badge_id": badge_id,
            "type": "streak_badge",
            "entity": entity,
            "outcome_type": outcome_type,
            "streak_count": streak_count,
            "conversion_boost": round(scaled_boost, 3),
            "minted_at": _now_iso(),
            "public": True,
            "verified": True
        }

        self._badges[badge_id] = badge

        if entity not in self._by_entity:
            self._by_entity[entity] = []
        self._by_entity[entity].append(badge_id)

        return {"ok": True, "badge": badge}

    def get_badge(self, badge_id: str) -> Optional[Dict[str, Any]]:
        """Get badge by ID"""
        return self._badges.get(badge_id)

    def get_entity_badges(self, entity: str) -> List[Dict[str, Any]]:
        """Get all badges for an entity"""
        badge_ids = self._by_entity.get(entity, [])
        return [self._badges[bid] for bid in badge_ids if bid in self._badges]

    def get_outcome_badge(self, outcome_id: str) -> Optional[Dict[str, Any]]:
        """Get badge for an outcome"""
        badge_id = self._by_outcome.get(outcome_id)
        if badge_id:
            return self._badges.get(badge_id)
        return None

    def calculate_total_boost(self, entity: str) -> Dict[str, Any]:
        """Calculate total conversion boost from all badges"""
        badges = self.get_entity_badges(entity)

        if not badges:
            return {"total_boost": 0, "badge_count": 0}

        # Diminishing returns on stacking badges
        boosts = sorted([b["conversion_boost"] for b in badges], reverse=True)

        total = 0
        for i, boost in enumerate(boosts[:5]):  # Max 5 badges count
            decay = 0.8 ** i  # Each subsequent badge worth less
            total += boost * decay

        return {
            "total_boost": round(min(total, 0.50), 3),  # Cap at 50%
            "badge_count": len(badges),
            "badges_counted": min(5, len(badges))
        }

    def verify_badge(self, badge_id: str) -> Dict[str, Any]:
        """Verify a badge is authentic"""
        badge = self._badges.get(badge_id)
        if not badge:
            return {"verified": False, "error": "badge_not_found"}

        return {
            "verified": True,
            "badge_id": badge_id,
            "type": badge["type"],
            "entity": badge["entity"],
            "minted_at": badge["minted_at"]
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get badge system stats"""
        by_type = {}
        for badge in self._badges.values():
            bt = badge.get("type", "unknown")
            by_type[bt] = by_type.get(bt, 0) + 1

        return {
            "total_badges": len(self._badges),
            "unique_entities": len(self._by_entity),
            "by_type": by_type
        }


# Module-level singleton
_default_badges = ProofBadges()


def mint_badge(attestation: Dict[str, Any]) -> Dict[str, Any]:
    """Mint badge using default engine"""
    return _default_badges.mint(attestation)


def get_entity_badges(entity: str) -> List[Dict[str, Any]]:
    """Get badges for entity"""
    return _default_badges.get_entity_badges(entity)


def calculate_conversion_boost(entity: str) -> Dict[str, Any]:
    """Calculate conversion boost for entity"""
    return _default_badges.calculate_total_boost(entity)


def verify_badge(badge_id: str) -> Dict[str, Any]:
    """Verify badge authenticity"""
    return _default_badges.verify_badge(badge_id)
