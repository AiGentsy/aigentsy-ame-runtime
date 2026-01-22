"""
LEAD OVERFLOW EXCHANGE (LOX)
============================

Dark-pool style exchange for leads that miss SLA or overflow capacity.

Flow:
1. Original provider can't fulfill within SLA
2. Lead posted to LOX with discount + context
3. Qualified takers bid (auction or first-come)
4. Winner fulfills, original provider gets referral cut
5. AiGentsy earns spread

Revenue:
- 3% exchange fee on LOX transactions
- Original provider gets 10-20% referral cut (from their share)

Usage:
    from lead_overflow_exchange import post_to_lox, bid_on_lox_lead, accept_lox_bid, get_lox_book
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4
from collections import defaultdict
import heapq

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Fee structure
LOX_EXCHANGE_FEE_PCT = 0.03  # 3% exchange fee
REFERRAL_CUT_PCT = 0.15  # 15% to original provider
MIN_DISCOUNT_PCT = 0.10  # Minimum 10% discount required
MAX_DISCOUNT_PCT = 0.50  # Maximum 50% discount

# OCS requirements
MIN_TAKER_OCS = 60  # Minimum OCS to take LOX leads

# Storage
_LOX_LISTINGS: Dict[str, Dict[str, Any]] = {}
_LOX_BIDS: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
_LOX_MATCHES: Dict[str, Dict[str, Any]] = {}
_PROVIDER_STATS: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
    "posted": 0, "sold": 0, "referral_earned": 0.0
})


class LeadOverflowExchange:
    """
    Dark-pool exchange for overflow/SLA-missed leads.
    """

    def __init__(self):
        self.exchange_fee_pct = LOX_EXCHANGE_FEE_PCT
        self.referral_cut_pct = REFERRAL_CUT_PCT
        self.min_discount_pct = MIN_DISCOUNT_PCT
        self.max_discount_pct = MAX_DISCOUNT_PCT
        self.min_taker_ocs = MIN_TAKER_OCS

    def post_to_lox(
        self,
        lead_id: str,
        original_provider_id: str,
        *,
        original_price: float,
        discount_pct: float,
        reason: str = "capacity_overflow",
        outcome_type: str = "general",
        description: str = "",
        deadline_hours: int = 24,
        required_ocs: int = None,
        metadata: dict = None
    ) -> Dict[str, Any]:
        """
        Post a lead to the LOX exchange.

        Args:
            lead_id: Original lead/COI ID
            original_provider_id: Provider who couldn't fulfill
            original_price: Original agreed price
            discount_pct: Discount offered (0.10-0.50)
            reason: Why lead is being posted (capacity_overflow, sla_miss, skill_gap)
            outcome_type: Type of outcome needed
            description: Brief description
            deadline_hours: Hours until LOX listing expires
            required_ocs: Minimum OCS required (default: 60)
            metadata: Additional context

        Returns:
            LOX listing details
        """
        # Validate discount
        if discount_pct < self.min_discount_pct:
            return {
                "ok": False,
                "error": "discount_too_low",
                "min_discount": self.min_discount_pct
            }

        if discount_pct > self.max_discount_pct:
            return {
                "ok": False,
                "error": "discount_too_high",
                "max_discount": self.max_discount_pct
            }

        lox_id = f"lox_{uuid4().hex[:8]}"
        discounted_price = round(original_price * (1 - discount_pct), 2)

        # Calculate fee structure
        exchange_fee = round(discounted_price * self.exchange_fee_pct, 2)
        referral_cut = round(discounted_price * self.referral_cut_pct, 2)
        taker_net = round(discounted_price - exchange_fee - referral_cut, 2)

        listing = {
            "id": lox_id,
            "lead_id": lead_id,
            "original_provider_id": original_provider_id,
            "original_price": original_price,
            "discount_pct": discount_pct,
            "discounted_price": discounted_price,
            "reason": reason,
            "outcome_type": outcome_type,
            "description": description,
            "required_ocs": required_ocs or self.min_taker_ocs,
            "metadata": metadata or {},
            "status": "OPEN",
            "auction_type": "first_qualified",  # or "best_bid"
            "created_at": _now(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=deadline_hours)).isoformat() + "Z",
            "fee_breakdown": {
                "discounted_price": discounted_price,
                "exchange_fee": exchange_fee,
                "referral_cut": referral_cut,
                "taker_net": taker_net
            },
            "bids": [],
            "matched_to": None,
            "events": [{"type": "LISTING_CREATED", "at": _now()}]
        }

        _LOX_LISTINGS[lox_id] = listing
        _PROVIDER_STATS[original_provider_id]["posted"] += 1

        return {
            "ok": True,
            "lox_id": lox_id,
            "listing": listing,
            "fee_breakdown": listing["fee_breakdown"]
        }

    def bid_on_lox_lead(
        self,
        lox_id: str,
        taker_id: str,
        *,
        taker_ocs: int = None,
        bid_amount: float = None,
        delivery_hours: int = None,
        message: str = ""
    ) -> Dict[str, Any]:
        """
        Bid on a LOX listing.

        Args:
            lox_id: LOX listing ID
            taker_id: Bidding provider ID
            taker_ocs: Taker's OCS score
            bid_amount: Optional bid amount (for best_bid auctions)
            delivery_hours: Promised delivery time
            message: Message to original provider

        Returns:
            Bid result (may be instant-match for first_qualified)
        """
        listing = _LOX_LISTINGS.get(lox_id)
        if not listing:
            return {"ok": False, "error": "listing_not_found"}

        if listing["status"] != "OPEN":
            return {"ok": False, "error": f"listing_is_{listing['status'].lower()}"}

        # Check OCS requirement
        if taker_ocs is None:
            # Try to get from OCS engine
            try:
                from brain_overlay.ocs import OCSEngine
                ocs_engine = OCSEngine()
                details = ocs_engine.get_entity_details(taker_id)
                taker_ocs = details.get("ocs", 50)
            except:
                taker_ocs = 50

        if taker_ocs < listing["required_ocs"]:
            return {
                "ok": False,
                "error": "ocs_too_low",
                "your_ocs": taker_ocs,
                "required_ocs": listing["required_ocs"]
            }

        # Can't bid on your own listing
        if taker_id == listing["original_provider_id"]:
            return {"ok": False, "error": "cannot_bid_on_own_listing"}

        bid_id = f"loxbid_{uuid4().hex[:8]}"

        bid = {
            "id": bid_id,
            "lox_id": lox_id,
            "taker_id": taker_id,
            "taker_ocs": taker_ocs,
            "bid_amount": bid_amount or listing["discounted_price"],
            "delivery_hours": delivery_hours or 24,
            "message": message,
            "status": "PENDING",
            "created_at": _now()
        }

        listing["bids"].append(bid)
        _LOX_BIDS[lox_id].append(bid)

        listing["events"].append({
            "type": "BID_RECEIVED",
            "bid_id": bid_id,
            "taker_id": taker_id,
            "at": _now()
        })

        # For first_qualified, auto-accept if meets criteria
        if listing["auction_type"] == "first_qualified":
            return self._accept_bid(listing, bid)

        return {
            "ok": True,
            "bid_id": bid_id,
            "status": "PENDING",
            "message": "Bid submitted, awaiting review"
        }

    def _accept_bid(
        self,
        listing: Dict[str, Any],
        bid: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Accept a bid and create match"""
        match_id = f"loxmatch_{uuid4().hex[:8]}"

        # Update listing
        listing["status"] = "MATCHED"
        listing["matched_to"] = bid["taker_id"]
        bid["status"] = "ACCEPTED"

        # Create match record
        match = {
            "id": match_id,
            "lox_id": listing["id"],
            "lead_id": listing["lead_id"],
            "original_provider_id": listing["original_provider_id"],
            "taker_id": bid["taker_id"],
            "price": bid["bid_amount"],
            "fee_breakdown": listing["fee_breakdown"],
            "status": "PENDING_FULFILLMENT",
            "created_at": _now(),
            "delivery_deadline": (datetime.now(timezone.utc) + timedelta(hours=bid["delivery_hours"])).isoformat() + "Z",
            "fulfilled_at": None,
            "events": [{"type": "MATCH_CREATED", "at": _now()}]
        }

        _LOX_MATCHES[match_id] = match
        _PROVIDER_STATS[listing["original_provider_id"]]["sold"] += 1

        listing["events"].append({
            "type": "LISTING_MATCHED",
            "match_id": match_id,
            "taker_id": bid["taker_id"],
            "at": _now()
        })

        # Post exchange fee to ledger
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="lox_exchange_fee",
                ref=f"lox:{match_id}",
                debit=0,
                credit=listing["fee_breakdown"]["exchange_fee"],
                meta={
                    "lox_id": listing["id"],
                    "original_provider": listing["original_provider_id"],
                    "taker": bid["taker_id"]
                }
            )
        except ImportError:
            pass

        return {
            "ok": True,
            "match_id": match_id,
            "status": "MATCHED",
            "match": match,
            "message": "Bid accepted - fulfill within deadline"
        }

    def accept_lox_bid(
        self,
        lox_id: str,
        bid_id: str,
        *,
        approver_id: str = None
    ) -> Dict[str, Any]:
        """
        Manually accept a bid (for best_bid auctions).
        """
        listing = _LOX_LISTINGS.get(lox_id)
        if not listing:
            return {"ok": False, "error": "listing_not_found"}

        if listing["status"] != "OPEN":
            return {"ok": False, "error": f"listing_is_{listing['status'].lower()}"}

        # Find bid
        bid = None
        for b in listing["bids"]:
            if b["id"] == bid_id:
                bid = b
                break

        if not bid:
            return {"ok": False, "error": "bid_not_found"}

        return self._accept_bid(listing, bid)

    def mark_fulfilled(
        self,
        match_id: str,
        *,
        proofs: list = None,
        success: bool = True
    ) -> Dict[str, Any]:
        """
        Mark a LOX match as fulfilled.
        """
        match = _LOX_MATCHES.get(match_id)
        if not match:
            return {"ok": False, "error": "match_not_found"}

        if match["status"] != "PENDING_FULFILLMENT":
            return {"ok": False, "error": f"match_is_{match['status'].lower()}"}

        listing = _LOX_LISTINGS.get(match["lox_id"])

        if success:
            match["status"] = "FULFILLED"
            match["fulfilled_at"] = _now()

            # Pay referral to original provider
            referral = match["fee_breakdown"]["referral_cut"]
            _PROVIDER_STATS[match["original_provider_id"]]["referral_earned"] += referral

            # Post referral to ledger
            try:
                from monetization.ledger import post_entry
                post_entry(
                    entry_type="lox_referral",
                    ref=f"lox:{match_id}",
                    debit=0,
                    credit=referral,
                    meta={
                        "to": match["original_provider_id"],
                        "from_taker": match["taker_id"]
                    }
                )
            except ImportError:
                pass

            match["events"].append({
                "type": "MATCH_FULFILLED",
                "success": True,
                "at": _now()
            })

            return {
                "ok": True,
                "match_id": match_id,
                "status": "FULFILLED",
                "referral_paid": referral,
                "taker_earned": match["fee_breakdown"]["taker_net"]
            }
        else:
            match["status"] = "FAILED"
            match["events"].append({
                "type": "MATCH_FAILED",
                "at": _now()
            })

            # Could reopen listing here
            return {
                "ok": True,
                "match_id": match_id,
                "status": "FAILED",
                "message": "Lead can be re-listed"
            }

    def get_lox_book(
        self,
        *,
        outcome_type: str = None,
        min_discount: float = None,
        max_price: float = None,
        taker_ocs: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get available LOX listings (the order book).

        Args:
            outcome_type: Filter by outcome type
            min_discount: Minimum discount percentage
            max_price: Maximum price
            taker_ocs: Filter to listings taker qualifies for

        Returns:
            List of available listings
        """
        listings = []

        for listing in _LOX_LISTINGS.values():
            if listing["status"] != "OPEN":
                continue

            # Apply filters
            if outcome_type and listing["outcome_type"] != outcome_type:
                continue

            if min_discount and listing["discount_pct"] < min_discount:
                continue

            if max_price and listing["discounted_price"] > max_price:
                continue

            if taker_ocs and taker_ocs < listing["required_ocs"]:
                continue

            # Return sanitized listing (hide some internal details)
            listings.append({
                "lox_id": listing["id"],
                "outcome_type": listing["outcome_type"],
                "description": listing["description"][:100] + "..." if len(listing["description"]) > 100 else listing["description"],
                "original_price": listing["original_price"],
                "discount_pct": listing["discount_pct"],
                "discounted_price": listing["discounted_price"],
                "required_ocs": listing["required_ocs"],
                "reason": listing["reason"],
                "expires_at": listing["expires_at"],
                "bid_count": len(listing["bids"]),
                "auction_type": listing["auction_type"]
            })

        # Sort by discount (best deals first)
        listings.sort(key=lambda x: x["discount_pct"], reverse=True)

        return listings

    def get_listing(self, lox_id: str) -> Optional[Dict[str, Any]]:
        """Get full listing details"""
        return _LOX_LISTINGS.get(lox_id)

    def get_match(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get match details"""
        return _LOX_MATCHES.get(match_id)

    def get_provider_stats(self, provider_id: str) -> Dict[str, Any]:
        """Get provider's LOX statistics"""
        stats = _PROVIDER_STATS[provider_id]
        return {
            "provider_id": provider_id,
            "leads_posted": stats["posted"],
            "leads_sold": stats["sold"],
            "conversion_rate": round(stats["sold"] / stats["posted"], 3) if stats["posted"] > 0 else 0,
            "referral_earned": round(stats["referral_earned"], 2)
        }

    def get_exchange_stats(self) -> Dict[str, Any]:
        """Get overall LOX statistics"""
        total_listings = len(_LOX_LISTINGS)
        open_listings = len([l for l in _LOX_LISTINGS.values() if l["status"] == "OPEN"])
        matched_listings = len([l for l in _LOX_LISTINGS.values() if l["status"] == "MATCHED"])

        total_volume = sum(
            m["price"] for m in _LOX_MATCHES.values()
            if m["status"] == "FULFILLED"
        )

        total_exchange_fees = sum(
            m["fee_breakdown"]["exchange_fee"] for m in _LOX_MATCHES.values()
            if m["status"] == "FULFILLED"
        )

        total_referrals = sum(
            m["fee_breakdown"]["referral_cut"] for m in _LOX_MATCHES.values()
            if m["status"] == "FULFILLED"
        )

        return {
            "total_listings": total_listings,
            "open_listings": open_listings,
            "matched_listings": matched_listings,
            "fulfilled_matches": len([m for m in _LOX_MATCHES.values() if m["status"] == "FULFILLED"]),
            "total_volume": round(total_volume, 2),
            "total_exchange_fees": round(total_exchange_fees, 2),
            "total_referrals_paid": round(total_referrals, 2),
            "avg_discount": round(
                sum(l["discount_pct"] for l in _LOX_LISTINGS.values()) / total_listings, 3
            ) if total_listings > 0 else 0
        }


# Module-level singleton
_lox = LeadOverflowExchange()


def post_to_lox(lead_id: str, original_provider_id: str, **kwargs) -> Dict[str, Any]:
    """Post lead to LOX exchange"""
    return _lox.post_to_lox(lead_id, original_provider_id, **kwargs)


def bid_on_lox_lead(lox_id: str, taker_id: str, **kwargs) -> Dict[str, Any]:
    """Bid on LOX listing"""
    return _lox.bid_on_lox_lead(lox_id, taker_id, **kwargs)


def accept_lox_bid(lox_id: str, bid_id: str, **kwargs) -> Dict[str, Any]:
    """Accept a LOX bid"""
    return _lox.accept_lox_bid(lox_id, bid_id, **kwargs)


def mark_lox_fulfilled(match_id: str, **kwargs) -> Dict[str, Any]:
    """Mark LOX match as fulfilled"""
    return _lox.mark_fulfilled(match_id, **kwargs)


def get_lox_book(**kwargs) -> List[Dict[str, Any]]:
    """Get available LOX listings"""
    return _lox.get_lox_book(**kwargs)


def get_lox_listing(lox_id: str) -> Optional[Dict[str, Any]]:
    """Get listing details"""
    return _lox.get_listing(lox_id)


def get_lox_match(match_id: str) -> Optional[Dict[str, Any]]:
    """Get match details"""
    return _lox.get_match(match_id)


def get_lox_provider_stats(provider_id: str) -> Dict[str, Any]:
    """Get provider LOX stats"""
    return _lox.get_provider_stats(provider_id)


def get_lox_exchange_stats() -> Dict[str, Any]:
    """Get exchange statistics"""
    return _lox.get_exchange_stats()


def get_lox_stats() -> Dict[str, Any]:
    """Get LOX stats (alias with friendly format)"""
    stats = _lox.get_exchange_stats()
    return {
        "ok": True,
        "book_size": stats.get("open_listings", 0),
        "total_volume": stats.get("total_volume", 0),
        "total_listings": stats.get("total_listings", 0),
        "matched_listings": stats.get("matched_listings", 0),
        "exchange_fees": stats.get("total_exchange_fees", 0),
        "referrals_paid": stats.get("total_referrals_paid", 0),
        "avg_discount": stats.get("avg_discount", 0)
    }
