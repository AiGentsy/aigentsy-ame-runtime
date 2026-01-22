"""
IDLE-TIME ARBITRAGE
===================

Monetizes provider idle capacity during off-peak hours.
Lower-priced outcomes fill dead time, increasing provider utilization.

Strategy:
- Detect off-peak windows (provider-specific or global)
- Offer discounted rates to fill capacity
- Match low-urgency outcomes to idle slots
- Split the savings between platform and provider

Revenue:
- 2% arbitrage fee on idle-time transactions
- Provider gets better utilization
- Buyers get discounts (10-40%)

Usage:
    from idle_time_arbitrage import register_availability, find_idle_slots, book_idle_slot, get_arbitrage_savings
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4
from collections import defaultdict

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Discount tiers based on time until deadline
DISCOUNT_TIERS = {
    "urgent": {"min_hours": 0, "max_hours": 4, "discount": 0.0},      # No discount
    "standard": {"min_hours": 4, "max_hours": 24, "discount": 0.10},   # 10% off
    "flexible": {"min_hours": 24, "max_hours": 72, "discount": 0.25},  # 25% off
    "anytime": {"min_hours": 72, "max_hours": 168, "discount": 0.40},  # 40% off
}

# Time of day pricing multipliers (inverse - lower = cheaper)
TIME_MULTIPLIERS = {
    "peak": 1.0,      # 9am-5pm
    "shoulder": 0.85,  # 6am-9am, 5pm-9pm
    "off_peak": 0.70,  # 9pm-6am
    "weekend": 0.80,   # Saturday, Sunday
}

# Arbitrage fee
ARBITRAGE_FEE_PCT = 0.02  # 2%

# Storage
_PROVIDER_AVAILABILITY: Dict[str, Dict[str, Any]] = {}
_IDLE_SLOTS: Dict[str, Dict[str, Any]] = {}
_BOOKINGS: Dict[str, Dict[str, Any]] = {}
_SAVINGS_LEDGER: List[Dict[str, Any]] = []


class IdleTimeArbitrage:
    """
    Monetizes idle capacity through time-based pricing.
    """

    def __init__(self):
        self.discount_tiers = DISCOUNT_TIERS
        self.time_multipliers = TIME_MULTIPLIERS
        self.arbitrage_fee = ARBITRAGE_FEE_PCT

    def register_availability(
        self,
        provider_id: str,
        *,
        available_hours: dict = None,
        timezone_str: str = "UTC",
        categories: list = None,
        max_concurrent: int = 3,
        min_outcome_value: float = 10.0,
        auto_accept_idle: bool = True
    ) -> Dict[str, Any]:
        """
        Register provider availability for idle-time matching.

        Args:
            provider_id: Provider ID
            available_hours: Dict of day -> [start_hour, end_hour]
            timezone_str: Provider's timezone
            categories: Categories provider handles
            max_concurrent: Max concurrent idle outcomes
            min_outcome_value: Minimum outcome value to accept
            auto_accept_idle: Auto-accept idle-time outcomes

        Returns:
            Availability registration
        """
        if available_hours is None:
            # Default: 6am-10pm every day
            available_hours = {
                day: [6, 22]
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            }

        availability = {
            "provider_id": provider_id,
            "available_hours": available_hours,
            "timezone": timezone_str,
            "categories": categories or ["all"],
            "max_concurrent": max_concurrent,
            "min_outcome_value": min_outcome_value,
            "auto_accept_idle": auto_accept_idle,
            "current_load": 0,
            "status": "ACTIVE",
            "registered_at": _now(),
            "stats": {
                "idle_slots_offered": 0,
                "idle_slots_booked": 0,
                "idle_revenue": 0.0,
                "regular_revenue": 0.0,
                "utilization_improvement": 0.0
            }
        }

        _PROVIDER_AVAILABILITY[provider_id] = availability

        return {
            "ok": True,
            "provider_id": provider_id,
            "availability": availability,
            "message": "Registered for idle-time matching"
        }

    def find_idle_slots(
        self,
        *,
        category: str = None,
        min_discount: float = 0.10,
        delivery_window_hours: int = 72,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Find available idle-time slots with discounts.

        Args:
            category: Filter by category
            min_discount: Minimum discount required
            delivery_window_hours: How flexible is delivery
            max_results: Max slots to return

        Returns:
            Available idle slots with pricing
        """
        # Determine discount tier based on flexibility
        discount_tier = None
        for tier_name, tier in self.discount_tiers.items():
            if tier["min_hours"] <= delivery_window_hours < tier["max_hours"]:
                discount_tier = tier_name
                break

        if not discount_tier:
            discount_tier = "anytime"

        base_discount = self.discount_tiers[discount_tier]["discount"]

        if base_discount < min_discount:
            return {
                "ok": False,
                "error": "no_slots_at_requested_discount",
                "available_discount": base_discount,
                "suggestion": f"Extend delivery window to {self.discount_tiers['flexible']['min_hours']}+ hours for {self.discount_tiers['flexible']['discount']*100:.0f}% discount"
            }

        # Find available providers
        slots = []
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        current_day = now.strftime("%A").lower()

        for provider_id, avail in _PROVIDER_AVAILABILITY.items():
            if avail["status"] != "ACTIVE":
                continue

            if avail["current_load"] >= avail["max_concurrent"]:
                continue

            if "all" not in avail["categories"] and category and category not in avail["categories"]:
                continue

            # Check if currently in available hours
            day_hours = avail["available_hours"].get(current_day, [0, 24])
            if not (day_hours[0] <= current_hour < day_hours[1]):
                continue

            # Determine time-of-day multiplier
            time_mult = self._get_time_multiplier(current_hour, current_day)

            # Calculate total discount
            total_discount = base_discount + (1 - time_mult) * 0.5  # Blend
            total_discount = min(0.50, total_discount)  # Cap at 50%

            slot_id = f"slot_{provider_id}_{uuid4().hex[:6]}"

            slot = {
                "slot_id": slot_id,
                "provider_id": provider_id,
                "discount_pct": round(total_discount, 3),
                "discount_tier": discount_tier,
                "time_multiplier": time_mult,
                "delivery_window_hours": delivery_window_hours,
                "categories": avail["categories"],
                "available_capacity": avail["max_concurrent"] - avail["current_load"],
                "min_outcome_value": avail["min_outcome_value"],
                "valid_until": (now + timedelta(hours=1)).isoformat() + "Z"
            }

            _IDLE_SLOTS[slot_id] = slot
            slots.append(slot)

            avail["stats"]["idle_slots_offered"] += 1

        # Sort by discount (best first)
        slots.sort(key=lambda x: x["discount_pct"], reverse=True)

        return {
            "ok": True,
            "slots": slots[:max_results],
            "discount_tier": discount_tier,
            "base_discount": base_discount,
            "total_available": len(slots)
        }

    def _get_time_multiplier(self, hour: int, day: str) -> float:
        """Get time-of-day pricing multiplier"""
        if day in ["saturday", "sunday"]:
            return self.time_multipliers["weekend"]

        if 9 <= hour < 17:
            return self.time_multipliers["peak"]
        elif 6 <= hour < 9 or 17 <= hour < 21:
            return self.time_multipliers["shoulder"]
        else:
            return self.time_multipliers["off_peak"]

    def book_idle_slot(
        self,
        slot_id: str,
        buyer_id: str,
        *,
        outcome_id: str,
        base_price: float,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Book an idle-time slot.

        Args:
            slot_id: Slot ID from find_idle_slots
            buyer_id: Buyer ID
            outcome_id: Outcome being booked
            base_price: Regular price
            description: Outcome description

        Returns:
            Booking confirmation with discounted price
        """
        slot = _IDLE_SLOTS.get(slot_id)
        if not slot:
            return {"ok": False, "error": "slot_not_found_or_expired"}

        avail = _PROVIDER_AVAILABILITY.get(slot["provider_id"])
        if not avail:
            return {"ok": False, "error": "provider_not_available"}

        if base_price < avail["min_outcome_value"]:
            return {
                "ok": False,
                "error": "below_minimum_value",
                "min_value": avail["min_outcome_value"]
            }

        # Calculate discounted price
        discount = slot["discount_pct"]
        discounted_price = round(base_price * (1 - discount), 2)
        savings = round(base_price - discounted_price, 2)

        # Calculate arbitrage fee
        arb_fee = round(discounted_price * self.arbitrage_fee, 2)

        # Provider gets discounted price minus fee
        provider_payout = discounted_price - arb_fee

        booking_id = f"ibook_{uuid4().hex[:8]}"

        booking = {
            "id": booking_id,
            "slot_id": slot_id,
            "provider_id": slot["provider_id"],
            "buyer_id": buyer_id,
            "outcome_id": outcome_id,
            "description": description,
            "pricing": {
                "base_price": base_price,
                "discount_pct": discount,
                "discounted_price": discounted_price,
                "buyer_savings": savings,
                "arbitrage_fee": arb_fee,
                "provider_payout": provider_payout
            },
            "discount_tier": slot["discount_tier"],
            "delivery_window_hours": slot["delivery_window_hours"],
            "status": "BOOKED",
            "booked_at": _now(),
            "deadline": (datetime.now(timezone.utc) + timedelta(hours=slot["delivery_window_hours"])).isoformat() + "Z"
        }

        _BOOKINGS[booking_id] = booking

        # Update provider stats
        avail["current_load"] += 1
        avail["stats"]["idle_slots_booked"] += 1
        avail["stats"]["idle_revenue"] += provider_payout

        # Record savings
        _SAVINGS_LEDGER.append({
            "booking_id": booking_id,
            "buyer_id": buyer_id,
            "savings": savings,
            "at": _now()
        })

        # Remove slot
        del _IDLE_SLOTS[slot_id]

        # Post fee to ledger
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="idle_arbitrage_fee",
                ref=f"idle:{booking_id}",
                debit=0,
                credit=arb_fee,
                meta={
                    "provider_id": slot["provider_id"],
                    "buyer_id": buyer_id,
                    "discount_pct": discount,
                    "base_price": base_price
                }
            )
        except ImportError:
            pass

        return {
            "ok": True,
            "booking": booking,
            "message": f"Booked at {discount*100:.0f}% discount. You saved ${savings:.2f}!"
        }

    def complete_booking(
        self,
        booking_id: str,
        *,
        success: bool = True
    ) -> Dict[str, Any]:
        """Complete an idle-time booking"""
        booking = _BOOKINGS.get(booking_id)
        if not booking:
            return {"ok": False, "error": "booking_not_found"}

        if booking["status"] != "BOOKED":
            return {"ok": False, "error": f"booking_is_{booking['status'].lower()}"}

        avail = _PROVIDER_AVAILABILITY.get(booking["provider_id"])
        if avail:
            avail["current_load"] = max(0, avail["current_load"] - 1)

        booking["status"] = "COMPLETED" if success else "FAILED"
        booking["completed_at"] = _now()

        return {
            "ok": True,
            "booking_id": booking_id,
            "status": booking["status"],
            "provider_payout": booking["pricing"]["provider_payout"]
        }

    def get_arbitrage_savings(
        self,
        *,
        buyer_id: str = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get arbitrage savings summary"""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        if buyer_id:
            savings = [
                s for s in _SAVINGS_LEDGER
                if s["buyer_id"] == buyer_id and s["at"] >= cutoff
            ]
        else:
            savings = [s for s in _SAVINGS_LEDGER if s["at"] >= cutoff]

        total_savings = sum(s["savings"] for s in savings)

        return {
            "ok": True,
            "buyer_id": buyer_id,
            "days": days,
            "bookings": len(savings),
            "total_savings": round(total_savings, 2),
            "avg_savings_per_booking": round(total_savings / len(savings), 2) if savings else 0
        }

    def get_provider_idle_stats(self, provider_id: str) -> Dict[str, Any]:
        """Get provider's idle-time statistics"""
        avail = _PROVIDER_AVAILABILITY.get(provider_id)
        if not avail:
            return {"ok": False, "error": "provider_not_registered"}

        bookings = [b for b in _BOOKINGS.values() if b["provider_id"] == provider_id]

        return {
            "provider_id": provider_id,
            "status": avail["status"],
            "current_load": avail["current_load"],
            "max_concurrent": avail["max_concurrent"],
            "utilization": round(avail["current_load"] / avail["max_concurrent"], 2) if avail["max_concurrent"] > 0 else 0,
            "stats": avail["stats"],
            "total_idle_bookings": len([b for b in bookings if b["status"] in ["COMPLETED", "BOOKED"]]),
            "idle_revenue": round(sum(b["pricing"]["provider_payout"] for b in bookings if b["status"] == "COMPLETED"), 2)
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get overall idle-time arbitrage statistics"""
        total_providers = len(_PROVIDER_AVAILABILITY)
        active_providers = len([p for p in _PROVIDER_AVAILABILITY.values() if p["status"] == "ACTIVE"])

        total_bookings = len(_BOOKINGS)
        completed_bookings = len([b for b in _BOOKINGS.values() if b["status"] == "COMPLETED"])

        total_savings = sum(s["savings"] for s in _SAVINGS_LEDGER)
        total_arb_fees = sum(b["pricing"]["arbitrage_fee"] for b in _BOOKINGS.values())

        avg_discount = 0
        if _BOOKINGS:
            avg_discount = sum(b["pricing"]["discount_pct"] for b in _BOOKINGS.values()) / len(_BOOKINGS)

        return {
            "total_providers": total_providers,
            "active_providers": active_providers,
            "total_bookings": total_bookings,
            "completed_bookings": completed_bookings,
            "completion_rate": round(completed_bookings / total_bookings, 3) if total_bookings > 0 else 0,
            "total_buyer_savings": round(total_savings, 2),
            "total_arbitrage_fees": round(total_arb_fees, 2),
            "avg_discount": round(avg_discount, 3),
            "discount_tiers": list(self.discount_tiers.keys())
        }


# Module-level singleton
_arbitrage = IdleTimeArbitrage()


def register_availability(provider_id: str, **kwargs) -> Dict[str, Any]:
    """Register provider availability"""
    return _arbitrage.register_availability(provider_id, **kwargs)


def find_idle_slots(**kwargs) -> Dict[str, Any]:
    """Find available idle slots"""
    return _arbitrage.find_idle_slots(**kwargs)


def book_idle_slot(slot_id: str, buyer_id: str, **kwargs) -> Dict[str, Any]:
    """Book an idle slot"""
    return _arbitrage.book_idle_slot(slot_id, buyer_id, **kwargs)


def complete_idle_booking(booking_id: str, **kwargs) -> Dict[str, Any]:
    """Complete idle booking"""
    return _arbitrage.complete_booking(booking_id, **kwargs)


def get_arbitrage_savings(**kwargs) -> Dict[str, Any]:
    """Get arbitrage savings"""
    return _arbitrage.get_arbitrage_savings(**kwargs)


def get_provider_idle_stats(provider_id: str) -> Dict[str, Any]:
    """Get provider idle stats"""
    return _arbitrage.get_provider_idle_stats(provider_id)


def get_idle_arbitrage_stats() -> Dict[str, Any]:
    """Get overall idle arbitrage stats"""
    return _arbitrage.get_stats()


def detect_idle_capacity() -> Dict[str, Any]:
    """Detect current idle capacity across providers"""
    slots = _arbitrage.find_idle_slots(min_discount=0.0)
    return {
        "ok": True,
        "idle_slots": slots.get("slots", []),
        "total_available": slots.get("total_available", 0),
        "base_discount": slots.get("base_discount", 0)
    }


def get_idle_stats() -> Dict[str, Any]:
    """Get idle time arbitrage stats (alias with friendly format)"""
    stats = _arbitrage.get_stats()
    return {
        "ok": True,
        "value_captured": stats.get("total_arbitrage_fees", 0),
        "total_savings": stats.get("total_buyer_savings", 0),
        "bookings": stats.get("total_bookings", 0),
        "avg_discount": stats.get("avg_discount", 0),
        "active_providers": stats.get("active_providers", 0)
    }


def assign_micro_task(slot_id: str, task_id: str, value: float) -> Dict[str, Any]:
    """Assign a micro-task to an idle slot"""
    return book_idle_slot(slot_id, "micro_task_system", outcome_id=task_id, base_price=value)


def optimize_scheduling() -> Dict[str, Any]:
    """Optimize provider scheduling for idle time"""
    stats = _arbitrage.get_stats()
    return {
        "ok": True,
        "providers_analyzed": stats.get("total_providers", 0),
        "utilization_opportunity": round((1 - stats.get("completion_rate", 0.9)) * 100, 1),
        "recommendations": [
            "Expand off-peak discounts to increase bookings",
            "Target flexible-deadline outcomes for idle slots",
            "Monitor provider availability patterns"
        ]
    }
