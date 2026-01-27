"""
MONETIZATION FABRIC v1.0
========================

Comprehensive monetization layer that turns every action into revenue.

Modules:
- fee_schedule: Global fee configuration
- pricing_arm: Dynamic pricing with surge, FX, wave-aware uplift
- revenue_router: Revenue splits (platform/user/pool/partner)
- ledger: Double-entry accounting for every event
- settlements: Stripe/Bank/Wallet payouts
- arbitrage_engine: Cross-platform spread capture
- sponsorships: Featured placement, ad slots
- referrals: Multi-hop attribution with decay
- subscriptions: Tiers, SLAs, burst credits
- licensing: White-label, OEM, network fees
- data_products: Telemetry packs, benchmarks as SKUs
- proof_badges: Proof-of-Outcome badges for SKU uplift

Usage:
    from monetization import MonetizationFabric

    fabric = MonetizationFabric()

    # Price an outcome
    quoted = fabric.price_outcome(base_price=100, context={...})

    # Split revenue
    splits = fabric.split_revenue(gross=100, referral_chain=[...])

    # Record to ledger
    fabric.record_sale(coi_id="...", gross=100, splits=splits)
"""

from .fee_schedule import FeeSchedule, get_fee, override_fee, get_schedule
from .pricing_arm import PricingArm, suggest_price
from .revenue_router import RevenueRouter, split_revenue
from .ledger import Ledger, post_entry, get_balance
from .settlements import Settlements, payout
from .arbitrage_engine import ArbitrageEngine, find_spread
from .sponsorships import Sponsorships, sell_slot
from .referrals import Referrals, allocate_referrals
from .subscriptions import Subscriptions, get_tier, check_quota
from .licensing import Licensing, quote_oem
from .data_products import DataProducts, telemetry_pack, benchmark_badge
from .proof_badges import ProofBadges, mint_badge
from .proof_ledger import get_proof_ledger, create_proof

__all__ = [
    "FeeSchedule", "get_fee", "override_fee", "get_schedule",
    "PricingArm", "suggest_price",
    "RevenueRouter", "split_revenue",
    "Ledger", "post_entry", "get_balance",
    "Settlements", "payout",
    "ArbitrageEngine", "find_spread",
    "Sponsorships", "sell_slot",
    "Referrals", "allocate_referrals",
    "Subscriptions", "get_tier", "check_quota",
    "Licensing", "quote_oem",
    "DataProducts", "telemetry_pack", "benchmark_badge",
    "ProofBadges", "mint_badge",
    "get_proof_ledger", "create_proof",
    "MonetizationFabric"
]

__version__ = "1.0.0"


class MonetizationFabric:
    """
    Unified monetization interface that wires all modules together.
    """

    def __init__(self):
        self.fees = FeeSchedule()
        self.pricing = PricingArm()
        self.router = RevenueRouter()
        self.ledger = Ledger()
        self.settlements = Settlements()
        self.arbitrage = ArbitrageEngine()
        self.sponsorships = Sponsorships()
        self.referrals = Referrals()
        self.subscriptions = Subscriptions()
        self.licensing = Licensing()
        self.data_products = DataProducts()
        self.proof_badges = ProofBadges()

    def price_outcome(
        self,
        base_price: float,
        *,
        fx_rate: float = 1.0,
        load_pct: float = 0.3,
        wave_score: float = 0.2,
        cogs: float = 0.0,
        min_margin: float = 0.25
    ) -> float:
        """Price an outcome with all dynamic factors"""
        return self.pricing.suggest(
            base_price,
            fx_rate=fx_rate,
            load_pct=load_pct,
            wave_score=wave_score,
            cogs=cogs,
            min_margin=min_margin
        )

    def split_revenue(
        self,
        gross: float,
        *,
        user_pct: float = 0.70,
        pool_pct: float = 0.10,
        partner_pct: float = 0.05,
        referral_chain: list = None
    ) -> dict:
        """Split revenue across all parties"""
        splits = self.router.split(
            gross,
            user_pct=user_pct,
            pool_pct=pool_pct,
            partner_pct=partner_pct
        )

        if referral_chain:
            ref_alloc = self.referrals.allocate(gross, referral_chain)
            splits["referrals"] = ref_alloc["splits"]
            splits["remainder"] -= sum(ref_alloc["splits"].values())

        return splits

    def record_sale(
        self,
        coi_id: str,
        gross: float,
        splits: dict,
        metadata: dict = None
    ) -> dict:
        """Record a sale to the ledger"""
        # Main sale entry
        self.ledger.post(
            "sale",
            f"coi:{coi_id}",
            debit=0,
            credit=gross,
            meta={"coi_id": coi_id, **(metadata or {})}
        )

        # Credit each party
        for party, amount in splits.items():
            if isinstance(amount, dict):
                for ref_id, ref_amt in amount.items():
                    self.ledger.post(
                        "entity_credit",
                        f"entity:{ref_id}",
                        debit=0,
                        credit=ref_amt,
                        meta={"coi_id": coi_id, "type": "referral"}
                    )
            elif isinstance(amount, (int, float)) and amount > 0:
                self.ledger.post(
                    "entity_credit",
                    f"entity:{party}",
                    debit=0,
                    credit=amount,
                    meta={"coi_id": coi_id}
                )

        return {"ok": True, "coi_id": coi_id, "gross": gross, "splits": splits}

    def mint_proof_badge(self, attestation: dict) -> dict:
        """Mint a proof badge from an attestation"""
        return self.proof_badges.mint(attestation)

    def get_summary(self) -> dict:
        """Get monetization fabric summary"""
        return {
            "fees": self.fees.get_all(),
            "ledger_entries": len(self.ledger._entries),
            "pending_settlements": self.settlements.pending_count(),
            "active_sponsorships": self.sponsorships.active_count(),
            "subscription_tiers": list(self.subscriptions.TIERS.keys())
        }
