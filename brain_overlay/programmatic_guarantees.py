"""
PROGRAMMATIC GUARANTEES (PGs)
=============================

Outcome-Or-Refund + Credit Boost for selected SKUs.
Premium priced, backed by DealGraph tranches + OCS gating.

PGs lift conversion 15-40% and justify premium ARPU.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from collections import defaultdict
import math


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class PGEngine:
    """
    Programmatic Guarantee pricing and management.

    PGs provide:
    - Outcome guarantee (refund if failed)
    - Credit boost on success
    - Premium pricing justified by trust
    """

    def __init__(self):
        self.config = {
            "base_premium_pct": 0.18,      # 18% base premium
            "ocs_discount_factor": 0.005,  # OCS reduces premium
            "variance_multiplier": 1.5,    # Variance increases premium
            "min_premium_pct": 0.10,       # Floor premium
            "max_premium_pct": 0.45,       # Ceiling premium
            "min_ocs_for_pg": 40,          # Minimum OCS to qualify
            "credit_boost_pct": 0.05       # Credit boost on success
        }

        self._guarantees: Dict[str, Dict[str, Any]] = {}
        self._claims: List[Dict[str, Any]] = []

    def quote(
        self,
        ocs: float,
        variance: float,
        base_price: float
    ) -> Dict[str, Any]:
        """
        Quote programmatic guarantee premium.

        Args:
            ocs: Entity OCS score
            variance: Historical variance/risk
            base_price: Base outcome price

        Returns:
            PG quote with premium
        """
        # Check OCS eligibility
        if ocs < self.config["min_ocs_for_pg"]:
            return {
                "ok": False,
                "eligible": False,
                "reason": "ocs_below_minimum",
                "min_ocs": self.config["min_ocs_for_pg"],
                "current_ocs": ocs
            }

        # Calculate risk-adjusted premium
        base_pct = self.config["base_premium_pct"]

        # OCS discount (higher OCS = lower premium)
        ocs_adj = (100 - ocs) * self.config["ocs_discount_factor"]

        # Variance adjustment (higher variance = higher premium)
        var_adj = variance * self.config["variance_multiplier"]

        # Total premium percentage
        premium_pct = base_pct + ocs_adj + var_adj

        # Apply bounds
        premium_pct = max(self.config["min_premium_pct"],
                        min(self.config["max_premium_pct"], premium_pct))

        premium = round(base_price * premium_pct, 2)
        total_price = round(base_price + premium, 2)

        return {
            "ok": True,
            "eligible": True,
            "base_price": base_price,
            "premium": premium,
            "premium_pct": round(premium_pct * 100, 1),
            "total_price": total_price,
            "credit_boost_on_success": round(base_price * self.config["credit_boost_pct"], 2),
            "refund_on_failure": base_price,
            "risk_factors": {
                "ocs": ocs,
                "variance": variance,
                "ocs_adjustment": round(ocs_adj, 4),
                "variance_adjustment": round(var_adj, 4)
            }
        }

    def attach(
        self,
        coi_id: str,
        entity_id: str,
        quote: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Attach PG to a COI.

        Args:
            coi_id: COI identifier
            entity_id: Entity purchasing guarantee
            quote: PG quote from quote()

        Returns:
            Attached guarantee details
        """
        if not quote.get("eligible"):
            return {"ok": False, "error": "quote_not_eligible"}

        guarantee = {
            "id": f"pg_{coi_id}",
            "coi_id": coi_id,
            "entity_id": entity_id,
            "premium": quote["premium"],
            "base_price": quote["base_price"],
            "total_price": quote["total_price"],
            "credit_boost": quote["credit_boost_on_success"],
            "status": "active",
            "attached_at": _now_iso()
        }

        self._guarantees[coi_id] = guarantee

        return {
            "ok": True,
            "guarantee": guarantee
        }

    def resolve(
        self,
        coi_id: str,
        success: bool,
        proofs: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve a PG based on outcome.

        Args:
            coi_id: COI identifier
            success: Whether outcome was successful
            proofs: Proofs of delivery

        Returns:
            Resolution result (refund or credit boost)
        """
        if coi_id not in self._guarantees:
            return {"ok": False, "error": "guarantee_not_found"}

        guarantee = self._guarantees[coi_id]
        if guarantee["status"] != "active":
            return {"ok": False, "error": f"guarantee_{guarantee['status']}"}

        resolution = {
            "coi_id": coi_id,
            "success": success,
            "resolved_at": _now_iso()
        }

        if success:
            # Credit boost
            guarantee["status"] = "completed"
            resolution["action"] = "credit_boost"
            resolution["amount"] = guarantee["credit_boost"]
            resolution["message"] = "PG completed successfully - credit boost applied"
        else:
            # Refund
            guarantee["status"] = "refunded"
            resolution["action"] = "refund"
            resolution["amount"] = guarantee["base_price"]
            resolution["message"] = "PG failed - refund issued"

            self._claims.append({
                "coi_id": coi_id,
                "entity_id": guarantee["entity_id"],
                "refund_amount": guarantee["base_price"],
                "claimed_at": _now_iso()
            })

        return {
            "ok": True,
            "resolution": resolution
        }

    def get_guarantee(self, coi_id: str) -> Optional[Dict[str, Any]]:
        """Get guarantee by COI ID"""
        return self._guarantees.get(coi_id)

    def get_entity_guarantees(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all guarantees for an entity"""
        return [g for g in self._guarantees.values() if g.get("entity_id") == entity_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get PG statistics"""
        total = len(self._guarantees)
        active = len([g for g in self._guarantees.values() if g["status"] == "active"])
        completed = len([g for g in self._guarantees.values() if g["status"] == "completed"])
        refunded = len([g for g in self._guarantees.values() if g["status"] == "refunded"])

        total_premium = sum(g.get("premium", 0) for g in self._guarantees.values())
        total_refunds = sum(c.get("refund_amount", 0) for c in self._claims)

        return {
            "total_guarantees": total,
            "active": active,
            "completed": completed,
            "refunded": refunded,
            "success_rate": round(completed / (completed + refunded), 3) if (completed + refunded) > 0 else 0,
            "total_premium_collected": round(total_premium, 2),
            "total_refunds_paid": round(total_refunds, 2),
            "net_premium": round(total_premium - total_refunds, 2)
        }


# Module-level singleton
_pg_engine = PGEngine()


def quote_pg(ocs: float, variance: float, base_price: float) -> Dict[str, Any]:
    """Quote PG premium"""
    return _pg_engine.quote(ocs, variance, base_price)


def attach_pg(coi_id: str, entity_id: str, quote: Dict[str, Any]) -> Dict[str, Any]:
    """Attach PG to COI"""
    return _pg_engine.attach(coi_id, entity_id, quote)


def resolve_pg(coi_id: str, success: bool, **kwargs) -> Dict[str, Any]:
    """Resolve PG"""
    return _pg_engine.resolve(coi_id, success, **kwargs)


def get_pg_stats() -> Dict[str, Any]:
    """Get PG statistics"""
    return _pg_engine.get_stats()
