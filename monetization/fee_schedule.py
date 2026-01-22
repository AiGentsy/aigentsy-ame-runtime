"""
FEE SCHEDULE
============

Global fee configuration for all monetization surfaces.
Integrates with existing revenue_flows.py base fees.
"""

from typing import Dict, Any, Optional
import os

# Global fee configuration
_FEE_SCHEDULE: Dict[str, float] = {
    # Platform fees (extend existing 2.8% + $0.28 from revenue_flows.py)
    "platform_fee_pct": 0.06,              # AiGentsy take on gross (total)
    "base_platform_pct": 0.028,            # Base platform % (existing)
    "base_platform_fixed": 0.28,           # Base platform fixed (existing)

    # Insurance skims
    "insurance_origination_pct": 0.02,     # Policy origination skim
    "reinsurance_pct": 0.01,               # Optional reinsure skim
    "insurance_base_pct": 0.005,           # From insurance_pool.py

    # Market maker
    "market_maker_spread_pct": 0.03,       # IFX/OAA spread capture
    "ifx_listing_fee": 0.50,               # Per-listing fee
    "oaa_placement_fee": 1.00,             # Per-placement fee

    # Data products
    "data_pack_per_k": 0.75,               # $/1k events for telemetry packs
    "benchmark_badge_p50": 49.0,           # 50th percentile badge
    "benchmark_badge_p90": 149.0,          # 90th percentile badge
    "benchmark_badge_p99": 399.0,          # 99th percentile badge

    # Sponsorships
    "sponsorship_slot_daily": 250.0,       # Featured placement/day
    "sponsorship_slot_weekly": 1500.0,     # Weekly rate (discounted)
    "sponsorship_slot_monthly": 5000.0,    # Monthly rate (discounted)

    # Referrals
    "referral_default_pct": 0.12,          # Default revshare for referrals
    "referral_decay_factor": 0.6,          # Geometric decay per hop
    "referral_max_hops": 5,                # Max hops in chain

    # Licensing
    "licensing_monthly_base": 299.0,       # OEM/white-label base
    "licensing_per_seat": 9.0,             # Per-seat addon
    "licensing_per_connector": 49.0,       # Per-connector beyond 3
    "licensing_intl_multiplier": 1.1,      # Non-US regions

    # API & Usage
    "api_overage_per_k": 1.50,             # $/1k calls beyond sub tier
    "burst_credit_price": 0.10,            # Per burst credit
    "priority_queue_multiplier": 1.5,      # Priority processing

    # Premium services (from revenue_flows.py)
    "dark_pool_pct": 0.05,                 # 5% dark pool fee
    "jv_admin_pct": 0.02,                  # 2% JV admin fee
    "factoring_7day_pct": 0.03,            # 3% for 7-day factoring
    "factoring_14day_pct": 0.02,           # 2% for 14-day factoring
    "factoring_30day_pct": 0.01,           # 1% for 30+ day factoring

    # Clone/Royalties
    "clone_royalty_pct": 0.30,             # 30% clone royalty (existing)
    "template_royalty_pct": 0.15,          # 15% template royalty

    # Staking
    "staking_return_pct": 0.10,            # 10% staking return (existing)

    # Reinvestment
    "auto_reinvest_pct": 0.20,             # 20% auto-reinvest (existing)
}


class FeeSchedule:
    """Fee schedule manager with dynamic overrides"""

    def __init__(self, overrides: Dict[str, float] = None):
        self._fees = {**_FEE_SCHEDULE}
        if overrides:
            self._fees.update(overrides)

        # Load env overrides
        self._load_env_overrides()

    def _load_env_overrides(self):
        """Load fee overrides from environment"""
        for key in self._fees:
            env_key = f"FEE_{key.upper()}"
            env_val = os.getenv(env_key)
            if env_val:
                try:
                    self._fees[key] = float(env_val)
                except ValueError:
                    pass

    def get(self, key: str, default: float = None) -> float:
        """Get a fee value"""
        return self._fees.get(key, default)

    def override(self, key: str, value: float) -> None:
        """Override a fee value"""
        self._fees[key] = value

    def get_all(self) -> Dict[str, float]:
        """Get all fees"""
        return {**self._fees}

    def calculate_platform_fee(self, amount: float) -> Dict[str, float]:
        """Calculate platform fee breakdown"""
        base_pct = self.get("base_platform_pct", 0.028)
        base_fixed = self.get("base_platform_fixed", 0.28)

        percent_fee = round(amount * base_pct, 2)
        fixed_fee = base_fixed
        total = round(percent_fee + fixed_fee, 2)

        return {
            "percent_fee": percent_fee,
            "fixed_fee": fixed_fee,
            "total": total,
            "effective_rate": round(total / amount * 100, 2) if amount > 0 else 0
        }

    def calculate_insurance_skim(self, amount: float, include_reinsure: bool = False) -> Dict[str, float]:
        """Calculate insurance origination/reinsurance skim"""
        orig_pct = self.get("insurance_origination_pct", 0.02)
        reins_pct = self.get("reinsurance_pct", 0.01) if include_reinsure else 0

        origination = round(amount * orig_pct, 2)
        reinsurance = round(amount * reins_pct, 2)

        return {
            "origination": origination,
            "reinsurance": reinsurance,
            "total": round(origination + reinsurance, 2)
        }

    def calculate_factoring_fee(self, amount: float, days: int = 30) -> Dict[str, float]:
        """Calculate factoring fee based on days"""
        if days <= 7:
            rate = self.get("factoring_7day_pct", 0.03)
        elif days <= 14:
            rate = self.get("factoring_14day_pct", 0.02)
        else:
            rate = self.get("factoring_30day_pct", 0.01)

        fee = round(amount * rate, 2)

        return {
            "days": days,
            "rate": rate,
            "fee": fee,
            "net_advance": round(amount - fee, 2)
        }


# Module-level convenience functions
_default_schedule = FeeSchedule()


def get_fee(key: str, default: float = None) -> float:
    """Get a fee value from default schedule"""
    return _default_schedule.get(key, default)


def override_fee(key: str, value: float) -> None:
    """Override a fee in default schedule"""
    _default_schedule.override(key, value)


def calculate_platform_fee(amount: float) -> Dict[str, float]:
    """Calculate platform fee"""
    return _default_schedule.calculate_platform_fee(amount)


def get_schedule() -> Dict[str, float]:
    """Get full fee schedule"""
    return _default_schedule.get_all()


def get_fee_schedule() -> Dict[str, float]:
    """Get full fee schedule (alias)"""
    return _default_schedule.get_all()
