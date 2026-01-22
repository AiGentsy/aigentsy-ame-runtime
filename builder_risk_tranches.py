"""
BUILDER RISK TRANCHES (BRT)
===========================

Risk-sharing for third-party builders who want to build on AiGentsy rails.
Extends the Outcome Reinsurance Exchange (ORE) with tiered risk coverage.

Tiers:
- Starter: 50% risk retention, 50% ceded → 2% premium
- Growth: 30% risk retention, 70% ceded → 3.5% premium
- Scale: 10% risk retention, 90% ceded → 5% premium

Flow:
1. Builder registers and picks tier
2. Premium deducted from each transaction
3. On dispute/failure, risk shared per tier
4. Clean exits after 90-day seasoning

Revenue:
- Premium spread (difference between collected and expected loss)
- 0.25% admin fee on all claims

Usage:
    from builder_risk_tranches import register_builder, get_builder_coverage, file_builder_claim
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4
from collections import defaultdict

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Risk tier definitions
RISK_TIERS = {
    "starter": {
        "name": "Starter",
        "retention_pct": 0.50,  # Builder keeps 50% of risk
        "ceded_pct": 0.50,      # AiGentsy takes 50%
        "premium_pct": 0.02,   # 2% of transaction value
        "max_coverage": 10000,  # Max single claim
        "min_ocs": 0,          # No OCS requirement
        "seasoning_days": 90,   # Days before clean exit
    },
    "growth": {
        "name": "Growth",
        "retention_pct": 0.30,
        "ceded_pct": 0.70,
        "premium_pct": 0.035,
        "max_coverage": 50000,
        "min_ocs": 50,
        "seasoning_days": 90,
    },
    "scale": {
        "name": "Scale",
        "retention_pct": 0.10,
        "ceded_pct": 0.90,
        "premium_pct": 0.05,
        "max_coverage": 250000,
        "min_ocs": 70,
        "seasoning_days": 90,
    }
}

# Fee structure
ADMIN_FEE_PCT = 0.0025  # 0.25% on claims
EXPECTED_LOSS_RATIO = 0.60  # Target 60% loss ratio (premium > expected loss)

# Storage
_BUILDERS: Dict[str, Dict[str, Any]] = {}
_BUILDER_TRANSACTIONS: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
_CLAIMS: Dict[str, Dict[str, Any]] = {}
_RISK_POOL: float = 100000.0  # Starting pool


class BuilderRiskTranches:
    """
    Manages risk-sharing tiers for third-party builders.
    """

    def __init__(self):
        self.tiers = RISK_TIERS
        self.admin_fee_pct = ADMIN_FEE_PCT
        self.risk_pool = _RISK_POOL

    def register_builder(
        self,
        builder_id: str,
        *,
        tier: str = "starter",
        app_name: str = "",
        contact_email: str = "",
        webhook_url: str = None,
        metadata: dict = None
    ) -> Dict[str, Any]:
        """
        Register a third-party builder for risk coverage.

        Args:
            builder_id: Unique builder identifier
            tier: Risk tier (starter, growth, scale)
            app_name: Builder's application name
            contact_email: Contact email
            webhook_url: Webhook for claim notifications
            metadata: Additional builder info

        Returns:
            Builder registration details
        """
        if tier not in self.tiers:
            return {"ok": False, "error": "invalid_tier", "valid_tiers": list(self.tiers.keys())}

        tier_config = self.tiers[tier]

        # Check OCS requirement
        builder_ocs = 50  # Default, would check actual OCS
        try:
            from brain_overlay.ocs import OCSEngine
            ocs_engine = OCSEngine()
            details = ocs_engine.get_entity_details(builder_id)
            builder_ocs = details.get("ocs", 50)
        except:
            pass

        if builder_ocs < tier_config["min_ocs"]:
            return {
                "ok": False,
                "error": "ocs_too_low_for_tier",
                "your_ocs": builder_ocs,
                "required_ocs": tier_config["min_ocs"],
                "suggested_tier": self._suggest_tier(builder_ocs)
            }

        if builder_id in _BUILDERS:
            return {"ok": False, "error": "builder_already_registered"}

        builder = {
            "id": builder_id,
            "tier": tier,
            "tier_name": tier_config["name"],
            "app_name": app_name,
            "contact_email": contact_email,
            "webhook_url": webhook_url,
            "metadata": metadata or {},
            "ocs_at_registration": builder_ocs,
            "status": "ACTIVE",
            "created_at": _now(),
            "seasoning_ends_at": (datetime.now(timezone.utc) + timedelta(days=tier_config["seasoning_days"])).isoformat() + "Z",
            "coverage": {
                "retention_pct": tier_config["retention_pct"],
                "ceded_pct": tier_config["ceded_pct"],
                "premium_pct": tier_config["premium_pct"],
                "max_single_claim": tier_config["max_coverage"]
            },
            "stats": {
                "transactions": 0,
                "total_volume": 0.0,
                "premiums_paid": 0.0,
                "claims_filed": 0,
                "claims_paid": 0.0,
                "loss_ratio": 0.0
            },
            "events": [{"type": "BUILDER_REGISTERED", "tier": tier, "at": _now()}]
        }

        _BUILDERS[builder_id] = builder

        return {
            "ok": True,
            "builder_id": builder_id,
            "builder": builder,
            "message": f"Registered for {tier_config['name']} tier with {tier_config['ceded_pct']*100:.0f}% risk coverage"
        }

    def _suggest_tier(self, ocs: int) -> str:
        """Suggest appropriate tier based on OCS"""
        if ocs >= 70:
            return "scale"
        elif ocs >= 50:
            return "growth"
        return "starter"

    def record_transaction(
        self,
        builder_id: str,
        transaction_id: str,
        amount: float,
        *,
        outcome_type: str = "general",
        buyer_id: str = None,
        metadata: dict = None
    ) -> Dict[str, Any]:
        """
        Record a transaction and collect premium.

        Args:
            builder_id: Builder ID
            transaction_id: Unique transaction ID
            amount: Transaction amount
            outcome_type: Type of outcome
            buyer_id: End buyer ID
            metadata: Additional transaction info

        Returns:
            Transaction record with premium deducted
        """
        builder = _BUILDERS.get(builder_id)
        if not builder:
            return {"ok": False, "error": "builder_not_registered"}

        if builder["status"] != "ACTIVE":
            return {"ok": False, "error": f"builder_is_{builder['status'].lower()}"}

        # Calculate premium
        premium = round(amount * builder["coverage"]["premium_pct"], 2)

        transaction = {
            "id": transaction_id,
            "builder_id": builder_id,
            "amount": amount,
            "premium": premium,
            "outcome_type": outcome_type,
            "buyer_id": buyer_id,
            "metadata": metadata or {},
            "status": "COVERED",
            "created_at": _now(),
            "coverage_details": {
                "builder_retention": round(amount * builder["coverage"]["retention_pct"], 2),
                "aigentsy_coverage": round(amount * builder["coverage"]["ceded_pct"], 2),
                "max_claim": min(amount, builder["coverage"]["max_single_claim"])
            }
        }

        _BUILDER_TRANSACTIONS[builder_id].append(transaction)

        # Update builder stats
        builder["stats"]["transactions"] += 1
        builder["stats"]["total_volume"] += amount
        builder["stats"]["premiums_paid"] += premium

        # Add premium to risk pool
        self.risk_pool += premium

        # Post premium to ledger
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="brt_premium",
                ref=f"brt:{transaction_id}",
                debit=0,
                credit=premium,
                meta={
                    "builder_id": builder_id,
                    "tier": builder["tier"],
                    "transaction_amount": amount
                }
            )
        except ImportError:
            pass

        return {
            "ok": True,
            "transaction": transaction,
            "premium_collected": premium,
            "coverage": transaction["coverage_details"]
        }

    def file_claim(
        self,
        builder_id: str,
        transaction_id: str,
        *,
        claim_amount: float,
        reason: str,
        evidence: list = None
    ) -> Dict[str, Any]:
        """
        File a claim against covered transaction.

        Args:
            builder_id: Builder ID
            transaction_id: Transaction being claimed
            claim_amount: Amount being claimed
            reason: Reason for claim
            evidence: Supporting evidence

        Returns:
            Claim result with payout details
        """
        builder = _BUILDERS.get(builder_id)
        if not builder:
            return {"ok": False, "error": "builder_not_registered"}

        # Find transaction
        transaction = None
        for t in _BUILDER_TRANSACTIONS[builder_id]:
            if t["id"] == transaction_id:
                transaction = t
                break

        if not transaction:
            return {"ok": False, "error": "transaction_not_found"}

        if transaction["status"] != "COVERED":
            return {"ok": False, "error": f"transaction_is_{transaction['status'].lower()}"}

        # Validate claim amount
        max_claim = transaction["coverage_details"]["max_claim"]
        if claim_amount > max_claim:
            return {
                "ok": False,
                "error": "claim_exceeds_coverage",
                "max_claim": max_claim
            }

        claim_id = f"brtclaim_{uuid4().hex[:8]}"

        # Calculate payout per risk sharing
        aigentsy_payout = round(claim_amount * builder["coverage"]["ceded_pct"], 2)
        builder_retention = round(claim_amount * builder["coverage"]["retention_pct"], 2)

        # Deduct admin fee from AiGentsy portion
        admin_fee = round(aigentsy_payout * self.admin_fee_pct, 2)
        net_payout = aigentsy_payout - admin_fee

        # Check pool capacity
        if net_payout > self.risk_pool:
            return {
                "ok": False,
                "error": "insufficient_pool_capacity",
                "available": self.risk_pool
            }

        claim = {
            "id": claim_id,
            "builder_id": builder_id,
            "transaction_id": transaction_id,
            "claim_amount": claim_amount,
            "reason": reason,
            "evidence": evidence or [],
            "payout_breakdown": {
                "total_claim": claim_amount,
                "builder_retention": builder_retention,
                "aigentsy_coverage": aigentsy_payout,
                "admin_fee": admin_fee,
                "net_payout": net_payout
            },
            "status": "APPROVED",  # Auto-approve for now
            "created_at": _now(),
            "paid_at": _now(),
            "events": [
                {"type": "CLAIM_FILED", "at": _now()},
                {"type": "CLAIM_APPROVED", "at": _now()},
                {"type": "CLAIM_PAID", "at": _now()}
            ]
        }

        _CLAIMS[claim_id] = claim
        transaction["status"] = "CLAIMED"

        # Update stats
        builder["stats"]["claims_filed"] += 1
        builder["stats"]["claims_paid"] += net_payout

        # Calculate loss ratio
        if builder["stats"]["premiums_paid"] > 0:
            builder["stats"]["loss_ratio"] = round(
                builder["stats"]["claims_paid"] / builder["stats"]["premiums_paid"], 4
            )

        # Deduct from pool
        self.risk_pool -= net_payout

        # Post claim payout to ledger
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="brt_claim_payout",
                ref=f"brt:{claim_id}",
                debit=net_payout,
                credit=0,
                meta={
                    "builder_id": builder_id,
                    "transaction_id": transaction_id,
                    "reason": reason
                }
            )
            # Post admin fee
            post_entry(
                entry_type="brt_admin_fee",
                ref=f"brt:{claim_id}",
                debit=0,
                credit=admin_fee,
                meta={"claim_id": claim_id}
            )
        except ImportError:
            pass

        return {
            "ok": True,
            "claim": claim,
            "message": f"Claim approved. ${net_payout:.2f} paid from AiGentsy coverage."
        }

    def upgrade_tier(
        self,
        builder_id: str,
        new_tier: str
    ) -> Dict[str, Any]:
        """
        Upgrade builder to a higher tier.
        """
        builder = _BUILDERS.get(builder_id)
        if not builder:
            return {"ok": False, "error": "builder_not_registered"}

        if new_tier not in self.tiers:
            return {"ok": False, "error": "invalid_tier"}

        tier_config = self.tiers[new_tier]

        # Check OCS
        builder_ocs = builder.get("ocs_at_registration", 50)
        try:
            from brain_overlay.ocs import OCSEngine
            ocs_engine = OCSEngine()
            details = ocs_engine.get_entity_details(builder_id)
            builder_ocs = details.get("ocs", builder_ocs)
        except:
            pass

        if builder_ocs < tier_config["min_ocs"]:
            return {
                "ok": False,
                "error": "ocs_too_low_for_tier",
                "your_ocs": builder_ocs,
                "required_ocs": tier_config["min_ocs"]
            }

        old_tier = builder["tier"]
        builder["tier"] = new_tier
        builder["tier_name"] = tier_config["name"]
        builder["coverage"] = {
            "retention_pct": tier_config["retention_pct"],
            "ceded_pct": tier_config["ceded_pct"],
            "premium_pct": tier_config["premium_pct"],
            "max_single_claim": tier_config["max_coverage"]
        }

        builder["events"].append({
            "type": "TIER_UPGRADED",
            "from": old_tier,
            "to": new_tier,
            "at": _now()
        })

        return {
            "ok": True,
            "builder_id": builder_id,
            "old_tier": old_tier,
            "new_tier": new_tier,
            "new_coverage": builder["coverage"]
        }

    def get_builder(self, builder_id: str) -> Optional[Dict[str, Any]]:
        """Get builder details"""
        return _BUILDERS.get(builder_id)

    def get_builder_coverage(self, builder_id: str) -> Dict[str, Any]:
        """Get builder's current coverage details"""
        builder = _BUILDERS.get(builder_id)
        if not builder:
            return {"ok": False, "error": "builder_not_registered"}

        return {
            "builder_id": builder_id,
            "tier": builder["tier"],
            "tier_name": builder["tier_name"],
            "coverage": builder["coverage"],
            "stats": builder["stats"],
            "status": builder["status"],
            "seasoning_ends_at": builder["seasoning_ends_at"]
        }

    def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get claim details"""
        return _CLAIMS.get(claim_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get BRT program statistics"""
        total_builders = len(_BUILDERS)
        total_volume = sum(b["stats"]["total_volume"] for b in _BUILDERS.values())
        total_premiums = sum(b["stats"]["premiums_paid"] for b in _BUILDERS.values())
        total_claims_paid = sum(b["stats"]["claims_paid"] for b in _BUILDERS.values())

        return {
            "total_builders": total_builders,
            "builders_by_tier": {
                tier: len([b for b in _BUILDERS.values() if b["tier"] == tier])
                for tier in self.tiers.keys()
            },
            "total_transaction_volume": round(total_volume, 2),
            "total_premiums_collected": round(total_premiums, 2),
            "total_claims_paid": round(total_claims_paid, 2),
            "loss_ratio": round(total_claims_paid / total_premiums, 4) if total_premiums > 0 else 0,
            "risk_pool_balance": round(self.risk_pool, 2),
            "total_claims": len(_CLAIMS)
        }


# Module-level singleton
_brt = BuilderRiskTranches()


def register_builder(builder_id: str, **kwargs) -> Dict[str, Any]:
    """Register builder for risk coverage"""
    return _brt.register_builder(builder_id, **kwargs)


def record_builder_transaction(builder_id: str, transaction_id: str, amount: float, **kwargs) -> Dict[str, Any]:
    """Record transaction and collect premium"""
    return _brt.record_transaction(builder_id, transaction_id, amount, **kwargs)


def file_builder_claim(builder_id: str, transaction_id: str, **kwargs) -> Dict[str, Any]:
    """File claim against covered transaction"""
    return _brt.file_claim(builder_id, transaction_id, **kwargs)


def upgrade_builder_tier(builder_id: str, new_tier: str) -> Dict[str, Any]:
    """Upgrade builder to higher tier"""
    return _brt.upgrade_tier(builder_id, new_tier)


def get_builder(builder_id: str) -> Optional[Dict[str, Any]]:
    """Get builder details"""
    return _brt.get_builder(builder_id)


def get_builder_coverage(builder_id: str) -> Dict[str, Any]:
    """Get builder coverage details"""
    return _brt.get_builder_coverage(builder_id)


def get_brt_claim(claim_id: str) -> Optional[Dict[str, Any]]:
    """Get claim details"""
    return _brt.get_claim(claim_id)


def get_brt_stats() -> Dict[str, Any]:
    """Get BRT program statistics"""
    return _brt.get_stats()


def get_tranche_portfolio() -> Dict[str, Any]:
    """Get tranche portfolio (alias for BRT stats with portfolio view)"""
    stats = _brt.get_stats()
    return {
        "ok": True,
        "tranches": list(RISK_TIERS.keys()),
        "builders_by_tier": stats.get("builders_by_tier", {}),
        "total_volume": stats.get("total_transaction_volume", 0),
        "risk_pool_balance": stats.get("risk_pool_balance", 0)
    }


def get_tranche_yields() -> Dict[str, Any]:
    """Get tranche yields by tier"""
    return {
        tier: {
            "name": config["name"],
            "premium_pct": config["premium_pct"],
            "retention_pct": config["retention_pct"],
            "ceded_pct": config["ceded_pct"],
            "max_coverage": config["max_coverage"]
        }
        for tier, config in RISK_TIERS.items()
    }


def issue_tranche(builder_id: str, tier: str = "starter", **kwargs) -> Dict[str, Any]:
    """Issue a tranche (register builder for tier)"""
    return register_builder(builder_id, tier=tier, **kwargs)


def price_tranche(amount: float, tier: str = "starter") -> Dict[str, Any]:
    """Price a tranche (calculate premium for amount at tier)"""
    tier_config = RISK_TIERS.get(tier)
    if not tier_config:
        return {"ok": False, "error": "invalid_tier"}
    premium = round(amount * tier_config["premium_pct"], 2)
    return {
        "ok": True,
        "tier": tier,
        "amount": amount,
        "premium": premium,
        "premium_pct": tier_config["premium_pct"],
        "coverage_pct": tier_config["ceded_pct"]
    }
