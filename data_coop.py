"""
CONSENT-NATIVE DATA CO-OP
=========================

Aggregate anonymized outcome data and sell insights to partners.
Users opt-in and earn rev share from their contributed data.

Data products:
- Benchmark reports (pricing, completion rates, SLAs)
- Demand forecasts
- Skill-gap analysis
- Market intelligence

Revenue:
- 30% to data contributors
- 10% to platform
- 60% to production/analysis

Usage:
    from data_coop import opt_in_contributor, contribute_data, query_insights, get_contributor_earnings
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4
from collections import defaultdict
import hashlib

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Revenue split for data products
CONTRIBUTOR_SHARE_PCT = 0.30  # 30% to contributors
PLATFORM_SHARE_PCT = 0.10  # 10% to platform
PRODUCTION_SHARE_PCT = 0.60  # 60% to production

# Data product pricing
DATA_PRODUCTS = {
    "benchmark_report": {
        "name": "Benchmark Report",
        "description": "Pricing, completion rates, SLAs by category",
        "price": 499.00,
        "min_data_points": 100
    },
    "demand_forecast": {
        "name": "Demand Forecast",
        "description": "30-day demand projection by category",
        "price": 799.00,
        "min_data_points": 500
    },
    "skill_gap_analysis": {
        "name": "Skill Gap Analysis",
        "description": "Unfulfilled demand vs available supply",
        "price": 999.00,
        "min_data_points": 200
    },
    "market_intelligence": {
        "name": "Market Intelligence",
        "description": "Competitive landscape and opportunity sizing",
        "price": 1499.00,
        "min_data_points": 1000
    },
    "custom_query": {
        "name": "Custom Query",
        "description": "Custom data query (price varies)",
        "price": 299.00,  # Base price
        "min_data_points": 50
    }
}

# Storage
_CONTRIBUTORS: Dict[str, Dict[str, Any]] = {}
_DATA_POOL: List[Dict[str, Any]] = []
_QUERIES: Dict[str, Dict[str, Any]] = {}
_EARNINGS: Dict[str, float] = defaultdict(float)


class DataCoop:
    """
    Consent-native data cooperative for outcome intelligence.
    """

    def __init__(self):
        self.contributor_share = CONTRIBUTOR_SHARE_PCT
        self.platform_share = PLATFORM_SHARE_PCT
        self.products = DATA_PRODUCTS

    def opt_in_contributor(
        self,
        contributor_id: str,
        *,
        consent_level: str = "anonymized",
        data_categories: list = None,
        payout_method: str = "credit",
        payout_threshold: float = 10.0,
        metadata: dict = None
    ) -> Dict[str, Any]:
        """
        Opt-in as a data contributor.

        Args:
            contributor_id: Unique contributor ID
            consent_level: anonymized, aggregated, or full
            data_categories: Categories willing to contribute
            payout_method: credit (account credit) or withdrawal
            payout_threshold: Minimum earnings before payout
            metadata: Additional contributor info

        Returns:
            Contributor registration details
        """
        if consent_level not in ["anonymized", "aggregated", "full"]:
            return {"ok": False, "error": "invalid_consent_level"}

        if contributor_id in _CONTRIBUTORS:
            return {"ok": False, "error": "already_opted_in"}

        contributor = {
            "id": contributor_id,
            "consent_level": consent_level,
            "data_categories": data_categories or ["all"],
            "payout_method": payout_method,
            "payout_threshold": payout_threshold,
            "metadata": metadata or {},
            "status": "ACTIVE",
            "opted_in_at": _now(),
            "data_points_contributed": 0,
            "earnings_total": 0.0,
            "earnings_pending": 0.0,
            "earnings_paid": 0.0,
            "events": [{"type": "OPTED_IN", "consent_level": consent_level, "at": _now()}]
        }

        _CONTRIBUTORS[contributor_id] = contributor

        return {
            "ok": True,
            "contributor": contributor,
            "message": f"Opted in with {consent_level} consent. You'll earn {self.contributor_share*100:.0f}% of data product revenue."
        }

    def contribute_data(
        self,
        contributor_id: str,
        data_type: str,
        data: Dict[str, Any],
        *,
        category: str = "general"
    ) -> Dict[str, Any]:
        """
        Contribute data to the co-op.

        Args:
            contributor_id: Contributor ID
            data_type: Type of data (outcome, pricing, sla, etc.)
            data: The data to contribute
            category: Data category

        Returns:
            Contribution receipt
        """
        contributor = _CONTRIBUTORS.get(contributor_id)
        if not contributor:
            return {"ok": False, "error": "not_opted_in"}

        if contributor["status"] != "ACTIVE":
            return {"ok": False, "error": f"contributor_is_{contributor['status'].lower()}"}

        # Check category consent
        if "all" not in contributor["data_categories"] and category not in contributor["data_categories"]:
            return {"ok": False, "error": "category_not_consented"}

        # Anonymize based on consent level
        anonymized_data = self._anonymize_data(data, contributor["consent_level"])

        # Generate data point ID
        data_hash = hashlib.sha256(str(anonymized_data).encode()).hexdigest()[:12]
        data_point_id = f"dp_{data_hash}_{uuid4().hex[:6]}"

        data_point = {
            "id": data_point_id,
            "contributor_id": contributor_id if contributor["consent_level"] == "full" else None,
            "contributor_hash": hashlib.sha256(contributor_id.encode()).hexdigest()[:16],
            "data_type": data_type,
            "category": category,
            "data": anonymized_data,
            "consent_level": contributor["consent_level"],
            "contributed_at": _now()
        }

        _DATA_POOL.append(data_point)
        contributor["data_points_contributed"] += 1

        return {
            "ok": True,
            "data_point_id": data_point_id,
            "anonymized": contributor["consent_level"] != "full",
            "total_contributed": contributor["data_points_contributed"]
        }

    def _anonymize_data(self, data: Dict[str, Any], consent_level: str) -> Dict[str, Any]:
        """Anonymize data based on consent level"""
        if consent_level == "full":
            return data

        # Remove PII fields
        pii_fields = ["email", "name", "phone", "address", "ip", "user_id", "entity_id"]
        anonymized = {k: v for k, v in data.items() if k.lower() not in pii_fields}

        if consent_level == "aggregated":
            # Round numeric values
            for k, v in anonymized.items():
                if isinstance(v, (int, float)):
                    anonymized[k] = round(v, -1)  # Round to nearest 10

        return anonymized

    def query_insights(
        self,
        buyer_id: str,
        product: str,
        *,
        category: str = None,
        date_range_days: int = 30,
        custom_filters: dict = None
    ) -> Dict[str, Any]:
        """
        Query data insights (purchase a data product).

        Args:
            buyer_id: Buyer ID
            product: Product name
            category: Filter by category
            date_range_days: Days of data to include
            custom_filters: Additional filters

        Returns:
            Query results with insights
        """
        if product not in self.products:
            return {"ok": False, "error": "invalid_product", "valid_products": list(self.products.keys())}

        product_config = self.products[product]

        # Filter data pool
        cutoff = (datetime.now(timezone.utc) - timedelta(days=date_range_days)).isoformat()
        filtered_data = [
            dp for dp in _DATA_POOL
            if dp["contributed_at"] >= cutoff
            and (category is None or dp["category"] == category)
        ]

        if len(filtered_data) < product_config["min_data_points"]:
            return {
                "ok": False,
                "error": "insufficient_data",
                "available": len(filtered_data),
                "required": product_config["min_data_points"]
            }

        # Generate insights based on product type
        insights = self._generate_insights(product, filtered_data, custom_filters)

        # Calculate revenue split
        price = product_config["price"]
        contributor_pool = round(price * self.contributor_share, 2)
        platform_fee = round(price * self.platform_share, 2)

        # Distribute to contributors
        contributing_hashes = set(dp["contributor_hash"] for dp in filtered_data)
        per_contributor = contributor_pool / len(contributing_hashes) if contributing_hashes else 0

        for contributor in _CONTRIBUTORS.values():
            contributor_hash = hashlib.sha256(contributor["id"].encode()).hexdigest()[:16]
            if contributor_hash in contributing_hashes:
                contributor["earnings_pending"] += per_contributor
                contributor["earnings_total"] += per_contributor
                _EARNINGS[contributor["id"]] += per_contributor

        # Create query record
        query_id = f"query_{uuid4().hex[:8]}"
        query = {
            "id": query_id,
            "buyer_id": buyer_id,
            "product": product,
            "category": category,
            "date_range_days": date_range_days,
            "data_points_used": len(filtered_data),
            "price": price,
            "contributor_pool": contributor_pool,
            "platform_fee": platform_fee,
            "created_at": _now()
        }

        _QUERIES[query_id] = query

        # Post fees to ledger
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="data_coop_fee",
                ref=f"data_coop:{query_id}",
                debit=0,
                credit=platform_fee,
                meta={
                    "product": product,
                    "buyer_id": buyer_id,
                    "data_points": len(filtered_data)
                }
            )
        except ImportError:
            pass

        return {
            "ok": True,
            "query_id": query_id,
            "product": product_config["name"],
            "insights": insights,
            "data_points_analyzed": len(filtered_data),
            "price": price,
            "contributors_rewarded": len(contributing_hashes)
        }

    def _generate_insights(
        self,
        product: str,
        data: List[Dict[str, Any]],
        filters: dict = None
    ) -> Dict[str, Any]:
        """Generate insights from data"""
        # Extract numeric values for analysis
        values = defaultdict(list)
        for dp in data:
            for k, v in dp.get("data", {}).items():
                if isinstance(v, (int, float)):
                    values[k].append(v)

        insights = {
            "data_points": len(data),
            "date_range": {
                "start": min(dp["contributed_at"] for dp in data),
                "end": max(dp["contributed_at"] for dp in data)
            },
            "categories": list(set(dp["category"] for dp in data))
        }

        # Add metric summaries
        for metric, vals in values.items():
            if vals:
                insights[f"{metric}_stats"] = {
                    "min": round(min(vals), 2),
                    "max": round(max(vals), 2),
                    "avg": round(sum(vals) / len(vals), 2),
                    "count": len(vals)
                }

        # Product-specific insights
        if product == "benchmark_report":
            insights["type"] = "benchmark"
            insights["summary"] = "Pricing and performance benchmarks"
        elif product == "demand_forecast":
            insights["type"] = "forecast"
            insights["forecast_period"] = "30_days"
        elif product == "skill_gap_analysis":
            insights["type"] = "gap_analysis"
        elif product == "market_intelligence":
            insights["type"] = "market_intel"

        return insights

    def get_contributor_earnings(self, contributor_id: str) -> Dict[str, Any]:
        """Get contributor earnings details"""
        contributor = _CONTRIBUTORS.get(contributor_id)
        if not contributor:
            return {"ok": False, "error": "not_opted_in"}

        return {
            "contributor_id": contributor_id,
            "data_points_contributed": contributor["data_points_contributed"],
            "earnings_total": round(contributor["earnings_total"], 2),
            "earnings_pending": round(contributor["earnings_pending"], 2),
            "earnings_paid": round(contributor["earnings_paid"], 2),
            "payout_threshold": contributor["payout_threshold"],
            "ready_for_payout": contributor["earnings_pending"] >= contributor["payout_threshold"]
        }

    def process_payout(self, contributor_id: str) -> Dict[str, Any]:
        """Process payout to contributor"""
        contributor = _CONTRIBUTORS.get(contributor_id)
        if not contributor:
            return {"ok": False, "error": "not_opted_in"}

        if contributor["earnings_pending"] < contributor["payout_threshold"]:
            return {
                "ok": False,
                "error": "below_threshold",
                "pending": contributor["earnings_pending"],
                "threshold": contributor["payout_threshold"]
            }

        payout_amount = contributor["earnings_pending"]
        contributor["earnings_paid"] += payout_amount
        contributor["earnings_pending"] = 0.0

        contributor["events"].append({
            "type": "PAYOUT_PROCESSED",
            "amount": payout_amount,
            "at": _now()
        })

        return {
            "ok": True,
            "contributor_id": contributor_id,
            "payout_amount": round(payout_amount, 2),
            "total_paid": round(contributor["earnings_paid"], 2)
        }

    def opt_out_contributor(self, contributor_id: str) -> Dict[str, Any]:
        """Opt-out of data co-op"""
        contributor = _CONTRIBUTORS.get(contributor_id)
        if not contributor:
            return {"ok": False, "error": "not_opted_in"}

        contributor["status"] = "OPTED_OUT"
        contributor["opted_out_at"] = _now()

        contributor["events"].append({
            "type": "OPTED_OUT",
            "at": _now()
        })

        return {
            "ok": True,
            "contributor_id": contributor_id,
            "final_earnings": round(contributor["earnings_pending"], 2),
            "message": "Opted out. Existing contributed data remains (anonymized)."
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get data co-op statistics"""
        total_contributors = len(_CONTRIBUTORS)
        active_contributors = len([c for c in _CONTRIBUTORS.values() if c["status"] == "ACTIVE"])
        total_data_points = len(_DATA_POOL)
        total_queries = len(_QUERIES)
        total_revenue = sum(q["price"] for q in _QUERIES.values())
        total_contributor_earnings = sum(c["earnings_total"] for c in _CONTRIBUTORS.values())

        return {
            "total_contributors": total_contributors,
            "active_contributors": active_contributors,
            "total_data_points": total_data_points,
            "data_points_by_category": dict(defaultdict(int, {
                dp["category"]: sum(1 for d in _DATA_POOL if d["category"] == dp["category"])
                for dp in _DATA_POOL[:100]  # Sample
            })),
            "total_queries": total_queries,
            "total_revenue": round(total_revenue, 2),
            "total_contributor_earnings": round(total_contributor_earnings, 2),
            "platform_fees_collected": round(total_revenue * self.platform_share, 2)
        }


# Module-level singleton
_coop = DataCoop()


def opt_in_contributor(contributor_id: str, **kwargs) -> Dict[str, Any]:
    """Opt-in as data contributor"""
    return _coop.opt_in_contributor(contributor_id, **kwargs)


def contribute_data(contributor_id: str, data_type: str, data: dict, **kwargs) -> Dict[str, Any]:
    """Contribute data to co-op"""
    return _coop.contribute_data(contributor_id, data_type, data, **kwargs)


def query_insights(buyer_id: str, product: str, **kwargs) -> Dict[str, Any]:
    """Query insights (purchase data product)"""
    return _coop.query_insights(buyer_id, product, **kwargs)


def get_contributor_earnings(contributor_id: str) -> Dict[str, Any]:
    """Get contributor earnings"""
    return _coop.get_contributor_earnings(contributor_id)


def process_contributor_payout(contributor_id: str) -> Dict[str, Any]:
    """Process payout to contributor"""
    return _coop.process_payout(contributor_id)


def opt_out_contributor(contributor_id: str) -> Dict[str, Any]:
    """Opt-out of data co-op"""
    return _coop.opt_out_contributor(contributor_id)


def get_data_coop_stats() -> Dict[str, Any]:
    """Get data co-op statistics"""
    return _coop.get_stats()
