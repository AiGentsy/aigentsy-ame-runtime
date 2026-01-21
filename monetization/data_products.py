"""
DATA PRODUCTS
=============

Telemetry packs, benchmarks, and analytics as SKUs.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from .fee_schedule import get_fee
from .ledger import post_entry


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class DataProducts:
    """
    Data products engine.

    Products:
    - telemetry_pack: Anonymized outcome metrics
    - benchmark_report: Industry/vertical benchmarks
    - connector_health: Connector performance data
    - success_patterns: Winning patterns by category
    """

    PRODUCTS = {
        "telemetry_pack": {
            "unit": "1k_events",
            "price_per_unit": 0.75,
            "description": "Anonymized outcome telemetry (win rate, p95, latency)"
        },
        "benchmark_report": {
            "unit": "report",
            "price_base": 199,
            "description": "Industry benchmark report with percentile rankings"
        },
        "connector_health": {
            "unit": "connector",
            "price_per_connector": 29,
            "description": "Connector performance data (uptime, latency, success rate)"
        },
        "success_patterns": {
            "unit": "pack",
            "price_per_pack": 149,
            "description": "Top performing patterns by outcome type"
        }
    }

    BADGE_PRICES = {
        50: 49,    # 50th percentile
        75: 99,    # 75th percentile
        90: 149,   # 90th percentile
        95: 249,   # 95th percentile
        99: 399    # 99th percentile
    }

    def __init__(self):
        self._sales: List[Dict[str, Any]] = []
        self._generated: List[Dict[str, Any]] = []

    def telemetry_pack(self, rows: int) -> Dict[str, Any]:
        """
        Price a telemetry pack.

        Args:
            rows: Number of events/rows in pack

        Returns:
            Pricing info
        """
        k_units = max(1, rows // 1000)
        unit_price = get_fee("data_pack_per_k", self.PRODUCTS["telemetry_pack"]["price_per_unit"])
        price = round(k_units * unit_price, 2)

        return {
            "ok": True,
            "product": "telemetry_pack",
            "rows": rows,
            "units": k_units,
            "price": price,
            "contents": [
                "outcome_type_distribution",
                "success_rate_by_connector",
                "latency_percentiles",
                "hourly_volume_trends",
                "error_rate_analysis"
            ]
        }

    def benchmark_badge(self, outcome_type: str, percentile: int) -> Dict[str, Any]:
        """
        Price a benchmark badge.

        Args:
            outcome_type: Type of outcome (send_email, etc.)
            percentile: Performance percentile (50, 75, 90, 95, 99)

        Returns:
            Badge SKU with pricing
        """
        if percentile not in self.BADGE_PRICES:
            # Find closest
            percentile = min(self.BADGE_PRICES.keys(), key=lambda x: abs(x - percentile))

        price = get_fee(f"benchmark_badge_p{percentile}", self.BADGE_PRICES[percentile])

        sku = f"badge:{outcome_type}:p{percentile}"

        return {
            "ok": True,
            "sku": sku,
            "outcome_type": outcome_type,
            "percentile": percentile,
            "price": price,
            "benefits": [
                f"Top {100 - percentile}% performer badge",
                "Display on profile/storefront",
                "Priority in discovery results",
                "Trust signal for buyers"
            ]
        }

    def benchmark_report(
        self,
        vertical: str,
        include_competitors: bool = False
    ) -> Dict[str, Any]:
        """
        Price a benchmark report.

        Args:
            vertical: Industry vertical
            include_competitors: Include competitor analysis

        Returns:
            Report pricing
        """
        base_price = self.PRODUCTS["benchmark_report"]["price_base"]

        if include_competitors:
            base_price += 100

        return {
            "ok": True,
            "product": "benchmark_report",
            "vertical": vertical,
            "price": base_price,
            "include_competitors": include_competitors,
            "contents": [
                "vertical_success_rates",
                "pricing_benchmarks",
                "response_time_analysis",
                "seasonal_patterns",
                "top_performing_outcomes"
            ] + (["competitor_comparison"] if include_competitors else [])
        }

    def connector_health_report(self, connectors: List[str]) -> Dict[str, Any]:
        """
        Price connector health report.

        Args:
            connectors: List of connector names

        Returns:
            Report pricing
        """
        per_connector = self.PRODUCTS["connector_health"]["price_per_connector"]
        price = round(len(connectors) * per_connector, 2)

        return {
            "ok": True,
            "product": "connector_health",
            "connectors": connectors,
            "price": price,
            "contents_per_connector": [
                "uptime_history",
                "latency_percentiles",
                "error_rate_trends",
                "capacity_utilization",
                "cost_per_call"
            ]
        }

    def success_patterns_pack(self, outcome_types: List[str]) -> Dict[str, Any]:
        """
        Price success patterns pack.

        Args:
            outcome_types: List of outcome types to include

        Returns:
            Pack pricing
        """
        per_pack = self.PRODUCTS["success_patterns"]["price_per_pack"]
        packs = len(outcome_types)
        price = round(packs * per_pack, 2)

        # Bulk discount
        if packs >= 5:
            price = round(price * 0.85, 2)
        elif packs >= 3:
            price = round(price * 0.90, 2)

        return {
            "ok": True,
            "product": "success_patterns",
            "outcome_types": outcome_types,
            "packs": packs,
            "price": price,
            "contents_per_type": [
                "top_10_patterns",
                "optimal_timing",
                "best_connectors",
                "pricing_strategies",
                "common_pitfalls"
            ]
        }

    def purchase(
        self,
        buyer: str,
        product_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Purchase a data product.

        Args:
            buyer: Buyer entity
            product_type: Product type
            config: Product configuration

        Returns:
            Purchase confirmation
        """
        # Generate pricing
        if product_type == "telemetry_pack":
            quote = self.telemetry_pack(config.get("rows", 10000))
        elif product_type == "benchmark_badge":
            quote = self.benchmark_badge(
                config.get("outcome_type", "send_email"),
                config.get("percentile", 90)
            )
        elif product_type == "benchmark_report":
            quote = self.benchmark_report(
                config.get("vertical", "general"),
                config.get("include_competitors", False)
            )
        elif product_type == "connector_health":
            quote = self.connector_health_report(
                config.get("connectors", ["resend", "stripe"])
            )
        elif product_type == "success_patterns":
            quote = self.success_patterns_pack(
                config.get("outcome_types", ["send_email"])
            )
        else:
            return {"ok": False, "error": f"unknown_product:{product_type}"}

        if not quote.get("ok"):
            return quote

        price = quote["price"]
        purchase_id = f"data_{uuid4().hex[:10]}"

        sale = {
            "id": purchase_id,
            "buyer": buyer,
            "product": product_type,
            "config": config,
            "price": price,
            "purchased_at": _now_iso()
        }

        self._sales.append(sale)

        # Record in ledger
        post_entry(
            "data_product_sale",
            f"data:{purchase_id}",
            debit=0,
            credit=price,
            meta={"buyer": buyer, "product": product_type}
        )

        return {
            "ok": True,
            "purchase_id": purchase_id,
            "product": product_type,
            "price": price,
            "delivery": "immediate"  # Data products delivered instantly
        }

    def get_catalog(self) -> Dict[str, Any]:
        """Get full product catalog"""
        return {
            "ok": True,
            "products": self.PRODUCTS,
            "badges": self.BADGE_PRICES
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get data products stats"""
        total_revenue = sum(s.get("price", 0) for s in self._sales)
        by_product = {}
        for sale in self._sales:
            pt = sale.get("product", "unknown")
            by_product[pt] = by_product.get(pt, 0) + 1

        return {
            "total_sales": len(self._sales),
            "total_revenue": round(total_revenue, 2),
            "by_product": by_product
        }


# Module-level singleton
_default_data_products = DataProducts()


def telemetry_pack(rows: int) -> Dict[str, Any]:
    """Price telemetry pack"""
    return _default_data_products.telemetry_pack(rows)


def benchmark_badge(outcome_type: str, percentile: int) -> Dict[str, Any]:
    """Price benchmark badge"""
    return _default_data_products.benchmark_badge(outcome_type, percentile)


def purchase_data_product(buyer: str, product_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Purchase a data product"""
    return _default_data_products.purchase(buyer, product_type, config)
