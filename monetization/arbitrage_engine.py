"""
ARBITRAGE ENGINE
================

Cross-platform, FX, and latency arbitrage for spread capture.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from .fee_schedule import get_fee


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class ArbitrageEngine:
    """
    Arbitrage opportunity detector and executor.

    Supported arbitrage types:
    - Price spread: Buy low on one platform, sell high on another
    - FX arbitrage: Currency conversion opportunities
    - Latency arbitrage: Time-based price differences
    - Service cross-listing: Same service, different marketplaces
    """

    def __init__(self):
        self.config = {
            "min_spread_pct": 0.12,       # Min 12% spread to act
            "min_profit_usd": 5.00,       # Min $5 profit
            "max_position_usd": 1000.00,  # Max single position
            "fx_refresh_seconds": 300,    # FX rate refresh interval
        }
        self._opportunities: List[Dict[str, Any]] = []
        self._executions: List[Dict[str, Any]] = []

    def spread_capture(
        self,
        bids: List[Tuple[float, str]],
        asks: List[Tuple[float, str]],
        min_pct: float = None
    ) -> Dict[str, Any]:
        """
        Find spread capture opportunity.

        Args:
            bids: List of (price, market) tuples - buyers
            asks: List of (price, market) tuples - sellers
            min_pct: Minimum spread percentage (default from config)

        Returns:
            Opportunity dict or {"ok": False} if none found
        """
        min_spread = min_pct or self.config["min_spread_pct"]

        if not bids or not asks:
            return {"ok": False, "error": "no_bids_or_asks"}

        # Find best bid (highest buyer) and best ask (lowest seller)
        best_bid = max(bids, key=lambda x: x[0])
        best_ask = min(asks, key=lambda x: x[0])

        if best_ask[0] <= 0 or best_bid[0] <= 0:
            return {"ok": False, "error": "invalid_prices"}

        # Calculate spread
        spread = best_bid[0] - best_ask[0]
        spread_pct = spread / best_ask[0]

        if spread_pct < min_spread:
            return {
                "ok": False,
                "spread_pct": round(spread_pct, 4),
                "required_pct": min_spread,
                "best_bid": best_bid,
                "best_ask": best_ask
            }

        # Calculate profit after platform fees
        platform_fee_pct = get_fee("market_maker_spread_pct", 0.03)
        gross_profit = spread
        platform_fee = round(gross_profit * platform_fee_pct, 2)
        net_profit = round(gross_profit - platform_fee, 2)

        opportunity = {
            "ok": True,
            "buy_at": {"price": best_ask[0], "market": best_ask[1]},
            "sell_at": {"price": best_bid[0], "market": best_bid[1]},
            "spread": round(spread, 2),
            "spread_pct": round(spread_pct, 4),
            "gross_profit": round(gross_profit, 2),
            "platform_fee": platform_fee,
            "net_profit": net_profit,
            "detected_at": _now_iso()
        }

        self._opportunities.append(opportunity)
        return opportunity

    def fx_arbitrage(
        self,
        amount_usd: float,
        rates: Dict[str, Dict[str, float]],
        path: List[str] = None
    ) -> Dict[str, Any]:
        """
        Find FX arbitrage opportunity.

        Args:
            amount_usd: Starting amount in USD
            rates: Dict of {currency: {to_currency: rate}}
            path: Optional currency path to evaluate

        Returns:
            Opportunity dict with profit if found
        """
        if not path:
            # Try common triangular paths
            paths = [
                ["USD", "EUR", "GBP", "USD"],
                ["USD", "GBP", "EUR", "USD"],
                ["USD", "EUR", "JPY", "USD"],
            ]
        else:
            paths = [path]

        best_opportunity = None
        best_profit = 0

        for p in paths:
            current = amount_usd
            for i in range(len(p) - 1):
                from_curr = p[i]
                to_curr = p[i + 1]

                if from_curr in rates and to_curr in rates.get(from_curr, {}):
                    rate = rates[from_curr][to_curr]
                    current *= rate
                else:
                    current = 0
                    break

            profit = current - amount_usd
            profit_pct = profit / amount_usd if amount_usd > 0 else 0

            if profit > best_profit and profit_pct >= self.config["min_spread_pct"]:
                best_profit = profit
                best_opportunity = {
                    "ok": True,
                    "path": p,
                    "start_amount": amount_usd,
                    "end_amount": round(current, 2),
                    "profit": round(profit, 2),
                    "profit_pct": round(profit_pct, 4)
                }

        if best_opportunity:
            self._opportunities.append(best_opportunity)
            return best_opportunity

        return {"ok": False, "error": "no_fx_opportunity"}

    def service_cross_listing(
        self,
        service: Dict[str, Any],
        platform_prices: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Find cross-listing arbitrage for services.

        Same service listed at different prices on different platforms.

        Args:
            service: Service description
            platform_prices: Dict of {platform: price}

        Returns:
            Opportunity to buy on cheapest, sell on most expensive
        """
        if len(platform_prices) < 2:
            return {"ok": False, "error": "need_multiple_platforms"}

        # Find min and max
        platforms = list(platform_prices.items())
        cheapest = min(platforms, key=lambda x: x[1])
        priciest = max(platforms, key=lambda x: x[1])

        if cheapest[0] == priciest[0]:
            return {"ok": False, "error": "same_platform"}

        spread = priciest[1] - cheapest[1]
        spread_pct = spread / cheapest[1] if cheapest[1] > 0 else 0

        if spread_pct < self.config["min_spread_pct"]:
            return {
                "ok": False,
                "spread_pct": round(spread_pct, 4),
                "required_pct": self.config["min_spread_pct"]
            }

        return {
            "ok": True,
            "service": service.get("id", "unknown"),
            "buy_on": {"platform": cheapest[0], "price": cheapest[1]},
            "sell_on": {"platform": priciest[0], "price": priciest[1]},
            "spread": round(spread, 2),
            "spread_pct": round(spread_pct, 4),
            "detected_at": _now_iso()
        }

    def get_opportunities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent opportunities"""
        return list(reversed(self._opportunities[-limit:]))

    def get_stats(self) -> Dict[str, Any]:
        """Get arbitrage engine stats"""
        opps = self._opportunities

        return {
            "total_opportunities": len(opps),
            "total_executions": len(self._executions),
            "avg_spread_pct": round(
                sum(o.get("spread_pct", 0) for o in opps) / len(opps), 4
            ) if opps else 0,
            "total_profit": round(
                sum(e.get("net_profit", 0) for e in self._executions), 2
            )
        }


# Module-level singleton
_default_engine = ArbitrageEngine()


def find_spread(
    bids: List[Tuple[float, str]],
    asks: List[Tuple[float, str]],
    **kwargs
) -> Dict[str, Any]:
    """Find spread opportunity using default engine"""
    return _default_engine.spread_capture(bids, asks, **kwargs)


def find_fx_arbitrage(amount_usd: float, rates: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """Find FX arbitrage using default engine"""
    return _default_engine.fx_arbitrage(amount_usd, rates)


def find_cross_listing(service: Dict[str, Any], platform_prices: Dict[str, float]) -> Dict[str, Any]:
    """Find cross-listing arbitrage using default engine"""
    return _default_engine.service_cross_listing(service, platform_prices)


def detect_spread_opportunity(
    bids: List[Dict[str, Any]],
    asks: List[Dict[str, Any]],
    min_pct: float = 0.12
) -> Dict[str, Any]:
    """Detect spread opportunity from bid/ask dicts"""
    # Convert dicts to tuples
    bid_tuples = [(b.get("price", 0), b.get("market", "unknown")) for b in bids]
    ask_tuples = [(a.get("price", 0), a.get("market", "unknown")) for a in asks]
    return _default_engine.spread_capture(bid_tuples, ask_tuples, min_pct=min_pct)


def detect_fx_arbitrage(amount_usd: float, rates: Dict[str, Dict[str, float]], path: List[str] = None) -> Dict[str, Any]:
    """Detect FX arbitrage opportunity"""
    return _default_engine.fx_arbitrage(amount_usd, rates, path=path)


def get_arbitrage_stats() -> Dict[str, Any]:
    """Get arbitrage engine statistics"""
    return {
        "ok": True,
        **_default_engine.get_stats()
    }
