"""
REVENUE ROUTER
==============

Splits revenue across platform, user, pool, and partners.
Integrates with existing revenue_flows.py splits.
"""

from typing import Dict, Any, Optional
from .fee_schedule import get_fee


class RevenueRouter:
    """
    Revenue distribution engine.

    Default split:
    - Platform: 6% (configurable via fee_schedule)
    - User: 70% of remainder
    - Pool: 10% of remainder (MetaHive/co-op)
    - Partner: 5% of remainder (JV/affiliate)
    - Remainder: stays in treasury for ops
    """

    def __init__(self):
        self.default_splits = {
            "user_pct": 0.70,
            "pool_pct": 0.10,
            "partner_pct": 0.05
        }

    def split(
        self,
        gross: float,
        *,
        user_pct: float = None,
        pool_pct: float = None,
        partner_pct: float = None,
        custom_platform_pct: float = None
    ) -> Dict[str, float]:
        """
        Split gross revenue across parties.

        Returns dict with platform, user, pool, partner, remainder.
        """
        # Platform take
        platform_pct = custom_platform_pct or get_fee("platform_fee_pct", 0.06)
        platform = round(gross * platform_pct, 2)

        # Net after platform
        net = gross - platform

        # Apply splits to net
        u_pct = user_pct if user_pct is not None else self.default_splits["user_pct"]
        p_pct = pool_pct if pool_pct is not None else self.default_splits["pool_pct"]
        pt_pct = partner_pct if partner_pct is not None else self.default_splits["partner_pct"]

        user = round(net * u_pct, 2)
        pool = round(net * p_pct, 2)
        partner = round(net * pt_pct, 2)
        remainder = round(net - user - pool - partner, 2)

        return {
            "gross": round(gross, 2),
            "platform": platform,
            "net_after_platform": round(net, 2),
            "user": user,
            "pool": pool,
            "partner": partner,
            "remainder": remainder,
            "splits_applied": {
                "platform_pct": platform_pct,
                "user_pct": u_pct,
                "pool_pct": p_pct,
                "partner_pct": pt_pct
            }
        }

    def split_with_premium(
        self,
        gross: float,
        premium_config: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, float]:
        """
        Split with premium service fees deducted first.

        Integrates with revenue_flows.py calculate_full_fee_with_premium pattern.
        """
        premium_config = premium_config or {}
        premium_total = 0.0
        premium_breakdown = {}

        # Dark pool fee
        if premium_config.get("dark_pool"):
            fee = round(gross * get_fee("dark_pool_pct", 0.05), 2)
            premium_breakdown["dark_pool"] = fee
            premium_total += fee

        # JV admin fee
        if premium_config.get("jv_admin"):
            fee = round(gross * get_fee("jv_admin_pct", 0.02), 2)
            premium_breakdown["jv_admin"] = fee
            premium_total += fee

        # Insurance fee
        if premium_config.get("insurance"):
            rate = 0.02 if gross < 1000 else 0.01
            fee = round(gross * rate, 2)
            premium_breakdown["insurance"] = fee
            premium_total += fee

        # Factoring fee
        if premium_config.get("factoring"):
            days = premium_config.get("factoring_days", 30)
            if days <= 7:
                rate = get_fee("factoring_7day_pct", 0.03)
            elif days <= 14:
                rate = get_fee("factoring_14day_pct", 0.02)
            else:
                rate = get_fee("factoring_30day_pct", 0.01)
            fee = round(gross * rate, 2)
            premium_breakdown["factoring"] = fee
            premium_total += fee

        # Adjusted gross after premium
        adjusted_gross = gross - premium_total

        # Apply standard split
        splits = self.split(adjusted_gross, **kwargs)

        # Add premium info
        splits["premium_fees"] = premium_breakdown
        splits["premium_total"] = round(premium_total, 2)
        splits["original_gross"] = round(gross, 2)

        return splits

    def split_jv(
        self,
        gross: float,
        jv_parties: Dict[str, float],
        *,
        platform_pct: float = None
    ) -> Dict[str, float]:
        """
        Split revenue for JV deals with custom party allocations.

        jv_parties: {"username1": 0.6, "username2": 0.4}
        """
        # Platform take first
        pf_pct = platform_pct or get_fee("platform_fee_pct", 0.06)
        platform = round(gross * pf_pct, 2)
        net = gross - platform

        # Split among JV parties
        party_splits = {}
        for party, pct in jv_parties.items():
            party_splits[party] = round(net * pct, 2)

        # Remainder check
        allocated = sum(party_splits.values())
        remainder = round(net - allocated, 2)

        return {
            "gross": round(gross, 2),
            "platform": platform,
            "net_after_platform": round(net, 2),
            "parties": party_splits,
            "remainder": remainder,
            "jv_split": jv_parties
        }

    def split_clone_royalty(
        self,
        gross: float,
        clone_chain: list,
        *,
        royalty_pct: float = None
    ) -> Dict[str, float]:
        """
        Split revenue with clone lineage royalties.

        Clone creators get royalty_pct of gross before standard split.
        """
        royalty = royalty_pct or get_fee("clone_royalty_pct", 0.30)

        royalty_splits = {}
        if clone_chain:
            # First in chain gets full royalty, subsequent get decay
            for i, creator in enumerate(clone_chain[:3]):
                decay = 0.6 ** i
                amt = round(gross * royalty * decay, 2)
                royalty_splits[creator] = amt

        total_royalty = sum(royalty_splits.values())
        net = gross - total_royalty

        # Standard split on remainder
        splits = self.split(net)
        splits["clone_royalties"] = royalty_splits
        splits["total_royalty"] = round(total_royalty, 2)

        return splits


# Module-level convenience
_default_router = RevenueRouter()


def split_revenue(gross: float, **kwargs) -> Dict[str, float]:
    """Split revenue using default router"""
    return _default_router.split(gross, **kwargs)


def split_with_premium(gross: float, premium_config: Dict[str, Any] = None, **kwargs) -> Dict[str, float]:
    """Split with premium services"""
    return _default_router.split_with_premium(gross, premium_config, **kwargs)


def split_jv(gross: float, jv_parties: Dict[str, float], **kwargs) -> Dict[str, float]:
    """Split for JV deals"""
    return _default_router.split_jv(gross, jv_parties, **kwargs)
