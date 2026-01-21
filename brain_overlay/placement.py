"""
PLACEMENT MARKET
================

Sponsored intent marketplace with auction-based ranking.
Result lists in Discovery/IFX get sponsored slots (CPC or CPS).

Features:
- Category takeovers
- Wave-surge packages
- Fraud protection from proofs
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from collections import defaultdict
import random


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class PlacementMarket:
    """
    Sponsored placement marketplace.

    Auction types:
    - CPC: Cost per click
    - CPS: Cost per sale (success)
    - CPM: Cost per mille (1k impressions)
    """

    PLACEMENT_TYPES = {
        "featured": {
            "positions": [1, 2, 3],
            "min_bid_cpc": 0.50,
            "min_bid_cps": 2.00
        },
        "sidebar": {
            "positions": [1, 2, 3, 4, 5],
            "min_bid_cpc": 0.25,
            "min_bid_cps": 1.00
        },
        "category_takeover": {
            "positions": [1],
            "min_bid_daily": 100.00
        },
        "wave_surge": {
            "positions": [1, 2],
            "min_bid_hourly": 25.00
        }
    }

    def __init__(self):
        self._bids: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._auctions: List[Dict[str, Any]] = []
        self._clicks: List[Dict[str, Any]] = []
        self._conversions: List[Dict[str, Any]] = []

    def bid(
        self,
        entity_id: str,
        placement_type: str,
        bid_amount: float,
        bid_type: str = "cpc",
        target: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Place a bid for sponsored placement.

        Args:
            entity_id: Bidding entity
            placement_type: Type of placement (featured, sidebar, etc.)
            bid_amount: Bid amount
            bid_type: cpc, cps, or cpm
            target: Targeting criteria (category, keywords, etc.)
        """
        if placement_type not in self.PLACEMENT_TYPES:
            return {"ok": False, "error": f"unknown_placement_type:{placement_type}"}

        config = self.PLACEMENT_TYPES[placement_type]

        # Validate minimum bid
        min_key = f"min_bid_{bid_type}"
        min_bid = config.get(min_key, 0)
        if bid_amount < min_bid:
            return {
                "ok": False,
                "error": "bid_below_minimum",
                "min_bid": min_bid,
                "bid_type": bid_type
            }

        bid = {
            "id": f"bid_{entity_id}_{placement_type}_{_now_iso()[:19].replace(':', '')}",
            "entity_id": entity_id,
            "placement_type": placement_type,
            "bid_amount": bid_amount,
            "bid_type": bid_type,
            "target": target or {},
            "status": "active",
            "created_at": _now_iso()
        }

        self._bids[placement_type].append(bid)

        return {
            "ok": True,
            "bid": bid
        }

    def rank(
        self,
        results: List[Dict[str, Any]],
        sponsored_bids: Dict[str, float] = None,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """
        Rank results with sponsored placement factored in.

        Args:
            results: Organic results [{id, score, ...}]
            sponsored_bids: {entity_id: bid_amount}
            category: Category for targeting

        Returns:
            Ranked results with sponsored placements
        """
        if not results:
            return []

        # Get active bids for category
        if sponsored_bids is None:
            sponsored_bids = {}
            for placement_type, bids in self._bids.items():
                for bid in bids:
                    if bid["status"] == "active":
                        target = bid.get("target", {})
                        if not category or target.get("category") == category or not target.get("category"):
                            entity = bid.get("entity_id")
                            if entity not in sponsored_bids or bid["bid_amount"] > sponsored_bids[entity]:
                                sponsored_bids[entity] = bid["bid_amount"]

        # Calculate final scores
        ranked = []
        for r in results:
            entity_id = r.get("id") or r.get("entity_id")
            organic_score = r.get("score", 0)

            # Bid lift (0.1 per dollar bid, capped at 50% boost)
            bid = sponsored_bids.get(entity_id, 0)
            bid_lift = min(0.5, bid * 0.1)

            # Quality floor (bad actors can't buy their way to top)
            quality = r.get("quality_score", 0.5)
            if quality < 0.3:
                bid_lift = 0  # No sponsored boost for low quality

            final_score = organic_score * (1 + bid_lift)

            ranked.append({
                **r,
                "organic_score": organic_score,
                "bid": bid,
                "bid_lift": round(bid_lift, 3),
                "final_score": round(final_score, 4),
                "sponsored": bid > 0
            })

        # Sort by final score
        ranked.sort(key=lambda x: x["final_score"], reverse=True)

        # Add rank positions
        for i, r in enumerate(ranked):
            r["rank"] = i + 1

        return ranked

    def record_click(
        self,
        entity_id: str,
        placement_type: str,
        position: int
    ) -> Dict[str, Any]:
        """Record a click on sponsored placement"""
        click = {
            "entity_id": entity_id,
            "placement_type": placement_type,
            "position": position,
            "clicked_at": _now_iso()
        }
        self._clicks.append(click)

        # Find and charge bid
        for bid in self._bids.get(placement_type, []):
            if bid.get("entity_id") == entity_id and bid.get("bid_type") == "cpc":
                # Would charge here
                pass

        return {"ok": True, "click": click}

    def record_conversion(
        self,
        entity_id: str,
        placement_type: str,
        value: float
    ) -> Dict[str, Any]:
        """Record a conversion from sponsored placement"""
        conversion = {
            "entity_id": entity_id,
            "placement_type": placement_type,
            "value": value,
            "converted_at": _now_iso()
        }
        self._conversions.append(conversion)

        # Find and charge CPS bid
        for bid in self._bids.get(placement_type, []):
            if bid.get("entity_id") == entity_id and bid.get("bid_type") == "cps":
                # Would charge here
                pass

        return {"ok": True, "conversion": conversion}

    def get_entity_stats(self, entity_id: str) -> Dict[str, Any]:
        """Get placement stats for entity"""
        clicks = [c for c in self._clicks if c.get("entity_id") == entity_id]
        conversions = [c for c in self._conversions if c.get("entity_id") == entity_id]

        return {
            "entity_id": entity_id,
            "total_clicks": len(clicks),
            "total_conversions": len(conversions),
            "ctr": len(conversions) / len(clicks) if clicks else 0,
            "total_value": sum(c.get("value", 0) for c in conversions)
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics"""
        total_bids = sum(len(bids) for bids in self._bids.values())
        active_bids = sum(
            len([b for b in bids if b["status"] == "active"])
            for bids in self._bids.values()
        )

        return {
            "total_bids": total_bids,
            "active_bids": active_bids,
            "total_clicks": len(self._clicks),
            "total_conversions": len(self._conversions),
            "conversion_rate": len(self._conversions) / len(self._clicks) if self._clicks else 0,
            "total_conversion_value": sum(c.get("value", 0) for c in self._conversions)
        }


# Module-level singleton
_placement_market = PlacementMarket()


def rank_with_sponsors(results: List[Dict], sponsored_bids: Dict[str, float] = None, **kwargs) -> List[Dict]:
    """Rank results with sponsored placement"""
    return _placement_market.rank(results, sponsored_bids, **kwargs)


def bid_on_placement(entity_id: str, placement_type: str, bid_amount: float, **kwargs) -> Dict[str, Any]:
    """Place a bid"""
    return _placement_market.bid(entity_id, placement_type, bid_amount, **kwargs)


def record_placement_click(entity_id: str, placement_type: str, position: int) -> Dict[str, Any]:
    """Record click"""
    return _placement_market.record_click(entity_id, placement_type, position)


def record_placement_conversion(entity_id: str, placement_type: str, value: float) -> Dict[str, Any]:
    """Record conversion"""
    return _placement_market.record_conversion(entity_id, placement_type, value)
