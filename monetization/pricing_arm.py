"""
PRICING ARM
===========

Dynamic pricing with surge, FX, wave-aware uplift, and margin guards.
Integrates with existing pricing_oracle.py for multiplier compatibility.
"""

from typing import Dict, Any, Optional
import math
from datetime import datetime, timezone


class PricingArm:
    """
    Multi-factor dynamic pricing engine.

    Factors:
    - FX adjustment (currency conversion)
    - Surge pricing (load-based)
    - Wave uplift (demand prediction)
    - Margin floor (protect COGS)
    - Time-of-day/week adjustments
    """

    def __init__(self):
        # Default configuration
        self.config = {
            "surge_threshold_low": 0.6,   # Load % where surge starts
            "surge_max_bump": 0.6,        # Max surge multiplier (60%)
            "wave_max_uplift": 0.35,      # Max wave uplift (35%)
            "min_margin_default": 0.25,   # Default 25% margin floor
            "price_floor_pct": 0.75,      # Never go below 75% of base
            "price_ceiling_pct": 2.0,     # Never exceed 200% of base
        }

    def fx_adjust(self, price_usd: float, fx_rate: float = 1.0) -> float:
        """Adjust price for currency conversion"""
        return round(price_usd * fx_rate, 2)

    def surge(self, price: float, load_pct: float) -> float:
        """
        Apply surge pricing based on system load.

        0-60% load → +0-20% linear
        >60% load → +20-60% non-linear acceleration
        """
        threshold = self.config["surge_threshold_low"]
        max_bump = self.config["surge_max_bump"]

        if load_pct <= 0:
            return price

        if load_pct <= threshold:
            # Linear ramp 0-20%
            bump = 0.2 * min(1, load_pct / threshold)
        else:
            # Non-linear acceleration 20-60%
            excess = (load_pct - threshold) / (1 - threshold)
            bump = 0.2 + (max_bump - 0.2) * min(1, excess)

        return round(price * (1 + bump), 2)

    def wave_uplift(self, price: float, wave_score: float) -> float:
        """
        Apply wave-based demand uplift.

        wave_score 0-1 lifts price up to 35%.
        """
        max_uplift = self.config["wave_max_uplift"]
        score = max(0, min(1, wave_score))

        return round(price * (1 + max_uplift * score), 2)

    def time_adjust(self, price: float, dt: datetime = None) -> float:
        """
        Apply time-of-day and day-of-week adjustments.

        - Weekend: +10%
        - Peak hours (9-17): +5%
        - Off hours (22-6): -5%
        """
        if dt is None:
            dt = datetime.now(timezone.utc)

        hour = dt.hour
        day_of_week = dt.weekday()

        multiplier = 1.0

        # Weekend premium
        if day_of_week >= 5:
            multiplier *= 1.10

        # Time-of-day
        if 9 <= hour <= 17:
            multiplier *= 1.05  # Peak hours
        elif hour < 6 or hour > 22:
            multiplier *= 0.95  # Off hours

        return round(price * multiplier, 2)

    def floor_margin(self, price: float, cogs: float, min_margin: float = None) -> float:
        """
        Ensure minimum margin over COGS.

        If price < cogs/(1-min_margin), bump to floor.
        """
        if min_margin is None:
            min_margin = self.config["min_margin_default"]

        if cogs <= 0 or min_margin >= 1:
            return price

        floor_price = cogs / (1 - min_margin)
        return max(price, round(floor_price, 2))

    def apply_bounds(self, price: float, base_price: float) -> float:
        """Apply floor/ceiling bounds relative to base price"""
        floor_pct = self.config["price_floor_pct"]
        ceiling_pct = self.config["price_ceiling_pct"]

        min_price = base_price * floor_pct
        max_price = base_price * ceiling_pct

        return round(max(min_price, min(max_price, price)), 2)

    def suggest(
        self,
        base_price: float,
        *,
        fx_rate: float = 1.0,
        load_pct: float = 0.3,
        wave_score: float = 0.2,
        cogs: float = 0.0,
        min_margin: float = 0.25,
        apply_time: bool = False
    ) -> float:
        """
        Suggest optimal price with all factors applied.

        Pipeline:
        1. FX adjustment
        2. Surge pricing
        3. Wave uplift
        4. Time adjustment (optional)
        5. Margin floor
        6. Bounds check
        """
        p = self.fx_adjust(base_price, fx_rate)
        p = self.surge(p, load_pct)
        p = self.wave_uplift(p, wave_score)

        if apply_time:
            p = self.time_adjust(p)

        p = self.floor_margin(p, cogs, min_margin)
        p = self.apply_bounds(p, base_price)

        return p

    def explain(
        self,
        base_price: float,
        *,
        fx_rate: float = 1.0,
        load_pct: float = 0.3,
        wave_score: float = 0.2,
        cogs: float = 0.0,
        min_margin: float = 0.25
    ) -> Dict[str, Any]:
        """Get detailed breakdown of price calculation"""
        p1 = self.fx_adjust(base_price, fx_rate)
        p2 = self.surge(p1, load_pct)
        p3 = self.wave_uplift(p2, wave_score)
        p4 = self.floor_margin(p3, cogs, min_margin)
        final = self.apply_bounds(p4, base_price)

        return {
            "base_price": base_price,
            "final_price": final,
            "steps": {
                "after_fx": p1,
                "after_surge": p2,
                "after_wave": p3,
                "after_margin_floor": p4,
                "after_bounds": final
            },
            "factors": {
                "fx_rate": fx_rate,
                "load_pct": load_pct,
                "wave_score": wave_score,
                "cogs": cogs,
                "min_margin": min_margin
            },
            "uplift_pct": round((final - base_price) / base_price * 100, 2) if base_price > 0 else 0
        }


# Module-level convenience
_default_arm = PricingArm()


def suggest_price(
    base_price: float,
    *,
    fx_rate: float = 1.0,
    load_pct: float = 0.3,
    wave_score: float = 0.2,
    cogs: float = 0.0,
    min_margin: float = 0.25
) -> float:
    """Suggest optimal price using default arm"""
    return _default_arm.suggest(
        base_price,
        fx_rate=fx_rate,
        load_pct=load_pct,
        wave_score=wave_score,
        cogs=cogs,
        min_margin=min_margin
    )


def explain_price(base_price: float, **kwargs) -> Dict[str, Any]:
    """Get price explanation using default arm"""
    return _default_arm.explain(base_price, **kwargs)
