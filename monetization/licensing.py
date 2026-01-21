"""
LICENSING
=========

White-label, OEM, and network licensing fees.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from .fee_schedule import get_fee
from .ledger import post_entry


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class Licensing:
    """
    Licensing engine for OEM, white-label, and network arrangements.

    License types:
    - oem: Full platform licensing for vertical SaaS
    - white_label: Branded instance for agencies/enterprises
    - api_reseller: API access for resale
    - network: Franchise/partner network license
    """

    LICENSE_TYPES = {
        "oem": {
            "base_monthly": 299,
            "per_seat": 9,
            "per_connector": 49,
            "free_connectors": 3,
            "description": "Full OEM platform license"
        },
        "white_label": {
            "base_monthly": 499,
            "per_seat": 15,
            "per_connector": 29,
            "free_connectors": 5,
            "description": "Branded white-label instance"
        },
        "api_reseller": {
            "base_monthly": 199,
            "per_1k_calls": 1.00,
            "min_commitment_calls": 100000,
            "description": "API reseller license"
        },
        "network": {
            "base_monthly": 999,
            "per_node": 49,
            "free_nodes": 5,
            "revenue_share_pct": 0.05,
            "description": "Franchise/partner network license"
        }
    }

    REGIONS = {
        "us": 1.0,
        "eu": 1.1,
        "apac": 1.15,
        "latam": 0.9,
        "other": 1.0
    }

    def __init__(self):
        self._licenses: Dict[str, Dict[str, Any]] = {}
        self._quotes: List[Dict[str, Any]] = []

    def quote_oem(
        self,
        seats: int = 10,
        connectors: int = 5,
        region: str = "us"
    ) -> Dict[str, Any]:
        """
        Generate OEM license quote.

        Args:
            seats: Number of seats
            connectors: Number of connectors
            region: Geographic region
        """
        config = self.LICENSE_TYPES["oem"]

        base = get_fee("licensing_monthly_base", config["base_monthly"])
        per_seat = get_fee("licensing_per_seat", config["per_seat"])
        per_connector = get_fee("licensing_per_connector", config["per_connector"])
        free_connectors = config["free_connectors"]

        # Calculate base
        seat_cost = seats * per_seat
        extra_connectors = max(0, connectors - free_connectors)
        connector_cost = extra_connectors * per_connector

        subtotal = base + seat_cost + connector_cost

        # Apply region multiplier
        region_mult = self.REGIONS.get(region, 1.0)
        if region != "us":
            region_mult = get_fee("licensing_intl_multiplier", region_mult)

        monthly = round(subtotal * region_mult, 2)
        annual = round(monthly * 12 * 0.85, 2)  # 15% annual discount

        quote = {
            "license_type": "oem",
            "seats": seats,
            "connectors": connectors,
            "free_connectors": free_connectors,
            "region": region,
            "breakdown": {
                "base": base,
                "seats": seat_cost,
                "connectors": connector_cost,
                "subtotal": subtotal,
                "region_multiplier": region_mult
            },
            "pricing": {
                "monthly": monthly,
                "annual": annual,
                "annual_savings": round(monthly * 12 - annual, 2)
            },
            "quoted_at": _now_iso()
        }

        self._quotes.append(quote)
        return {"ok": True, **quote}

    def quote_white_label(
        self,
        seats: int = 5,
        connectors: int = 5,
        custom_domain: bool = True,
        custom_branding: bool = True,
        region: str = "us"
    ) -> Dict[str, Any]:
        """Generate white-label license quote"""
        config = self.LICENSE_TYPES["white_label"]

        base = config["base_monthly"]
        seat_cost = seats * config["per_seat"]
        extra_connectors = max(0, connectors - config["free_connectors"])
        connector_cost = extra_connectors * config["per_connector"]

        # Add-ons
        addons = 0
        if custom_domain:
            addons += 29  # Custom domain
        if custom_branding:
            addons += 49  # Full branding

        subtotal = base + seat_cost + connector_cost + addons

        region_mult = self.REGIONS.get(region, 1.0)
        monthly = round(subtotal * region_mult, 2)

        return {
            "ok": True,
            "license_type": "white_label",
            "seats": seats,
            "connectors": connectors,
            "addons": {
                "custom_domain": custom_domain,
                "custom_branding": custom_branding
            },
            "pricing": {
                "monthly": monthly,
                "annual": round(monthly * 12 * 0.85, 2)
            }
        }

    def quote_network(
        self,
        nodes: int = 10,
        expected_monthly_revenue: float = 50000,
        region: str = "us"
    ) -> Dict[str, Any]:
        """Generate network/franchise license quote"""
        config = self.LICENSE_TYPES["network"]

        base = config["base_monthly"]
        extra_nodes = max(0, nodes - config["free_nodes"])
        node_cost = extra_nodes * config["per_node"]

        # Revenue share estimate
        rev_share_pct = config["revenue_share_pct"]
        estimated_rev_share = round(expected_monthly_revenue * rev_share_pct, 2)

        subtotal = base + node_cost

        region_mult = self.REGIONS.get(region, 1.0)
        monthly_fixed = round(subtotal * region_mult, 2)

        return {
            "ok": True,
            "license_type": "network",
            "nodes": nodes,
            "free_nodes": config["free_nodes"],
            "pricing": {
                "monthly_fixed": monthly_fixed,
                "revenue_share_pct": rev_share_pct,
                "estimated_rev_share": estimated_rev_share,
                "total_monthly": round(monthly_fixed + estimated_rev_share, 2)
            }
        }

    def issue_license(
        self,
        license_type: str,
        licensee: str,
        config: Dict[str, Any],
        billing_period: str = "monthly"
    ) -> Dict[str, Any]:
        """Issue a license to a licensee"""
        if license_type not in self.LICENSE_TYPES:
            return {"ok": False, "error": f"unknown_license_type:{license_type}"}

        # Generate quote for pricing
        if license_type == "oem":
            quote = self.quote_oem(**config)
        elif license_type == "white_label":
            quote = self.quote_white_label(**config)
        elif license_type == "network":
            quote = self.quote_network(**config)
        else:
            return {"ok": False, "error": "unsupported_license_type"}

        if not quote.get("ok"):
            return quote

        price = quote["pricing"]["annual" if billing_period == "annual" else "monthly"]

        license_id = f"lic_{uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)
        period_days = 365 if billing_period == "annual" else 30
        expires = now + timedelta(days=period_days)

        license_record = {
            "id": license_id,
            "type": license_type,
            "licensee": licensee,
            "config": config,
            "price": price,
            "billing_period": billing_period,
            "created_at": now.isoformat() + "Z",
            "expires_at": expires.isoformat() + "Z",
            "status": "active"
        }

        self._licenses[license_id] = license_record

        # Record in ledger
        post_entry(
            "license_fee",
            f"entity:{licensee}",
            debit=price,
            credit=0,
            meta={"license_id": license_id, "type": license_type}
        )

        post_entry(
            "license_revenue",
            "entity:aigentsy_platform",
            debit=0,
            credit=price,
            meta={"license_id": license_id, "licensee": licensee}
        )

        return {
            "ok": True,
            "license": license_record
        }

    def get_license(self, license_id: str) -> Dict[str, Any]:
        """Get license details"""
        license_record = self._licenses.get(license_id)
        if not license_record:
            return {"ok": False, "error": "license_not_found"}

        return {"ok": True, "license": license_record}

    def get_stats(self) -> Dict[str, Any]:
        """Get licensing stats"""
        total_revenue = sum(l.get("price", 0) for l in self._licenses.values())
        by_type = {}
        for lic in self._licenses.values():
            lt = lic.get("type", "unknown")
            by_type[lt] = by_type.get(lt, 0) + 1

        return {
            "total_licenses": len(self._licenses),
            "total_revenue": round(total_revenue, 2),
            "total_quotes": len(self._quotes),
            "by_type": by_type
        }


# Module-level singleton
_default_licensing = Licensing()


def quote_oem(**kwargs) -> Dict[str, Any]:
    """Generate OEM quote"""
    return _default_licensing.quote_oem(**kwargs)


def quote_white_label(**kwargs) -> Dict[str, Any]:
    """Generate white-label quote"""
    return _default_licensing.quote_white_label(**kwargs)


def quote_network(**kwargs) -> Dict[str, Any]:
    """Generate network license quote"""
    return _default_licensing.quote_network(**kwargs)


def issue_license(license_type: str, licensee: str, config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Issue a license"""
    return _default_licensing.issue_license(license_type, licensee, config, **kwargs)
