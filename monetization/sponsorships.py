"""
SPONSORSHIPS
============

Featured placement, ad slots, and co-op pool sponsorships.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from .fee_schedule import get_fee
from .ledger import post_entry


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class Sponsorships:
    """
    Sponsorship slot management.

    Slot types:
    - discovery_featured: Top of discovery feed
    - marketplace_banner: Marketplace banner ad
    - email_sponsor: Sponsored section in emails
    - coop_pool: Co-op pool participation
    """

    SLOT_TYPES = {
        "discovery_featured": {
            "daily_rate": 250.0,
            "max_slots": 3,
            "description": "Featured placement in discovery feed"
        },
        "marketplace_banner": {
            "daily_rate": 150.0,
            "max_slots": 5,
            "description": "Banner ad in marketplace"
        },
        "email_sponsor": {
            "daily_rate": 100.0,
            "max_slots": 2,
            "description": "Sponsored section in platform emails"
        },
        "coop_pool": {
            "daily_rate": 50.0,
            "max_slots": 20,
            "description": "Co-op advertising pool participation"
        }
    }

    def __init__(self):
        self._active_slots: Dict[str, Dict[str, Any]] = {}
        self._slot_history: List[Dict[str, Any]] = []

    def active_count(self) -> int:
        """Count of active sponsorships"""
        now = datetime.now(timezone.utc)
        return sum(
            1 for slot in self._active_slots.values()
            if datetime.fromisoformat(slot["expires_at"].replace("Z", "+00:00")) > now
        )

    def get_slot_pricing(self, slot_type: str) -> Dict[str, Any]:
        """Get pricing for a slot type"""
        if slot_type not in self.SLOT_TYPES:
            return {"ok": False, "error": f"unknown_slot_type:{slot_type}"}

        slot_info = self.SLOT_TYPES[slot_type]
        daily = slot_info["daily_rate"]

        # Discounts for longer terms
        return {
            "ok": True,
            "slot_type": slot_type,
            "description": slot_info["description"],
            "pricing": {
                "daily": daily,
                "weekly": round(daily * 7 * 0.85, 2),    # 15% discount
                "monthly": round(daily * 30 * 0.70, 2)  # 30% discount
            },
            "available_slots": slot_info["max_slots"] - self._count_active(slot_type)
        }

    def _count_active(self, slot_type: str) -> int:
        """Count active slots of a type"""
        now = datetime.now(timezone.utc)
        return sum(
            1 for slot in self._active_slots.values()
            if slot.get("slot_type") == slot_type and
            datetime.fromisoformat(slot["expires_at"].replace("Z", "+00:00")) > now
        )

    def sell_slot(
        self,
        slot_type: str,
        buyer: str,
        days: int = 1,
        content: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Sell a sponsorship slot.

        Args:
            slot_type: Type of slot
            buyer: Buyer entity/username
            days: Duration in days
            content: Sponsorship content (ad copy, links, etc.)

        Returns:
            Slot details or error
        """
        if slot_type not in self.SLOT_TYPES:
            return {"ok": False, "error": f"unknown_slot_type:{slot_type}"}

        slot_info = self.SLOT_TYPES[slot_type]

        # Check availability
        active = self._count_active(slot_type)
        if active >= slot_info["max_slots"]:
            return {"ok": False, "error": "no_slots_available", "active": active}

        # Calculate price
        daily_rate = get_fee("sponsorship_slot_daily", slot_info["daily_rate"])

        if days >= 30:
            price = round(daily_rate * days * 0.70, 2)  # 30% off
        elif days >= 7:
            price = round(daily_rate * days * 0.85, 2)  # 15% off
        else:
            price = round(daily_rate * days, 2)

        # Create slot
        slot_id = f"slot_{uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=days)

        slot = {
            "id": slot_id,
            "slot_type": slot_type,
            "buyer": buyer,
            "days": days,
            "price": price,
            "content": content or {},
            "created_at": now.isoformat() + "Z",
            "expires_at": expires.isoformat() + "Z",
            "status": "active"
        }

        self._active_slots[slot_id] = slot
        self._slot_history.append(slot)

        # Record in ledger
        post_entry(
            "sponsorship_sale",
            f"slot:{slot_id}",
            debit=0,
            credit=price,
            meta={"slot_type": slot_type, "buyer": buyer, "days": days}
        )

        return {
            "ok": True,
            "slot_id": slot_id,
            "slot_type": slot_type,
            "days": days,
            "price": price,
            "expires_at": slot["expires_at"]
        }

    def get_active_slots(self, slot_type: str = None) -> List[Dict[str, Any]]:
        """Get list of active slots"""
        now = datetime.now(timezone.utc)
        slots = [
            slot for slot in self._active_slots.values()
            if datetime.fromisoformat(slot["expires_at"].replace("Z", "+00:00")) > now
        ]

        if slot_type:
            slots = [s for s in slots if s["slot_type"] == slot_type]

        return slots

    def expire_slots(self) -> Dict[str, Any]:
        """Expire old slots"""
        now = datetime.now(timezone.utc)
        expired = []

        for slot_id, slot in list(self._active_slots.items()):
            expires = datetime.fromisoformat(slot["expires_at"].replace("Z", "+00:00"))
            if expires <= now:
                slot["status"] = "expired"
                expired.append(slot_id)

        return {"expired": len(expired), "slot_ids": expired}

    def get_stats(self) -> Dict[str, Any]:
        """Get sponsorship stats"""
        total_revenue = sum(s.get("price", 0) for s in self._slot_history)
        active = self.active_count()

        by_type = {}
        for slot_type in self.SLOT_TYPES:
            by_type[slot_type] = {
                "active": self._count_active(slot_type),
                "max": self.SLOT_TYPES[slot_type]["max_slots"]
            }

        return {
            "total_revenue": round(total_revenue, 2),
            "active_slots": active,
            "total_sold": len(self._slot_history),
            "by_type": by_type
        }


# Module-level singleton
_default_sponsorships = Sponsorships()


def sell_slot(slot_type: str, buyer: str, days: int = 1, **kwargs) -> Dict[str, Any]:
    """Sell slot using default sponsorships"""
    return _default_sponsorships.sell_slot(slot_type, buyer, days, **kwargs)


def get_slot_pricing(slot_type: str) -> Dict[str, Any]:
    """Get slot pricing"""
    return _default_sponsorships.get_slot_pricing(slot_type)


def get_active_slots(slot_type: str = None) -> List[Dict[str, Any]]:
    """Get active slots"""
    return _default_sponsorships.get_active_slots(slot_type)


def get_active_sponsorships() -> Dict[str, Any]:
    """Get all active sponsorships"""
    return {
        "ok": True,
        "active": _default_sponsorships.get_active_slots(),
        "count": _default_sponsorships.active_count()
    }


def get_available_slots() -> Dict[str, Any]:
    """Get available sponsorship slots with pricing"""
    available = []
    for slot_type, config in _default_sponsorships.SLOT_TYPES.items():
        active = _default_sponsorships._count_active(slot_type)
        max_slots = config["max_slots"]
        if active < max_slots:
            available.append({
                "slot_type": slot_type,
                "daily_rate": config["daily_rate"],
                "available": max_slots - active,
                "max_slots": max_slots,
                "conversion_boost": config["conversion_boost"]
            })

    return {
        "ok": True,
        "slots": available,
        "count": len(available)
    }


def get_sponsorship_stats() -> Dict[str, Any]:
    """Get sponsorship statistics"""
    stats = _default_sponsorships.get_stats()
    return {
        "ok": True,
        "active_sponsors": stats.get("active_slots", 0),
        "total_revenue": stats.get("total_revenue", 0),
        "total_sold": stats.get("total_sold", 0),
        "by_type": stats.get("by_type", {})
    }
