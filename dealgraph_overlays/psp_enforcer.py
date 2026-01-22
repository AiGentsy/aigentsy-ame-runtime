"""
PSP ENFORCER
============

Enforces Payment Service Provider (PSP) only fund flows.
Blocks any "direct funds" path; requires Stripe/PayPal/Upwork/Shopify links
on DealGraph state transitions (CONTRACTED → FUNDED).

AiGentsy is NOT a money transmitter - all funds flow through licensed PSPs.

Usage:
    from dealgraph_overlays.psp_enforcer import enforce_psp

    ok, err = enforce_psp(payment_meta)
    if not ok:
        return {"ok": False, "error": err}
"""

from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import re


# Allowed Payment Service Providers (licensed, compliant)
ALLOWED_PSP = {
    "stripe",
    "paypal",
    "upwork",
    "shopify",
    "fiverr",
    "toptal",
    "square",
    "braintree",
    "adyen",
    "wise",
    "payoneer",
    "paddle",
    "gumroad",
    "lemonsqueezy"
}

# Payment link patterns for validation
PSP_LINK_PATTERNS = {
    "stripe": [
        r"https?://(checkout\.)?stripe\.com",
        r"https?://[a-z0-9-]+\.stripe\.com",
        r"https?://pay\.stripe\.com",
        r"https?://invoice\.stripe\.com"
    ],
    "paypal": [
        r"https?://(www\.)?paypal\.(com|me)",
        r"https?://checkout\.paypal\.com"
    ],
    "upwork": [
        r"https?://(www\.)?upwork\.com",
    ],
    "shopify": [
        r"https?://[a-z0-9-]+\.myshopify\.com",
        r"https?://checkout\.shopify\.com"
    ],
    "fiverr": [
        r"https?://(www\.)?fiverr\.com"
    ],
    "toptal": [
        r"https?://(www\.)?toptal\.com"
    ],
    "square": [
        r"https?://squareup\.com",
        r"https?://checkout\.square\.site"
    ],
    "wise": [
        r"https?://(www\.)?wise\.com"
    ],
    "payoneer": [
        r"https?://(www\.)?payoneer\.com"
    ],
    "paddle": [
        r"https?://[a-z0-9-]+\.paddle\.com",
        r"https?://checkout\.paddle\.com"
    ],
    "gumroad": [
        r"https?://(www\.)?gumroad\.com",
        r"https?://[a-z0-9-]+\.gumroad\.com"
    ],
    "lemonsqueezy": [
        r"https?://[a-z0-9-]+\.lemonsqueezy\.com"
    ]
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def validate_payment_link(psp: str, link: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a payment link matches expected PSP patterns.

    Args:
        psp: Payment service provider name
        link: Payment link URL

    Returns:
        (valid, error_message)
    """
    if not link:
        return False, "payment_link_required"

    psp_lower = psp.lower()
    patterns = PSP_LINK_PATTERNS.get(psp_lower, [])

    if not patterns:
        # Unknown PSP, allow if it has https
        if link.startswith("https://"):
            return True, None
        return False, "https_required"

    for pattern in patterns:
        if re.match(pattern, link, re.IGNORECASE):
            return True, None

    return False, f"link_does_not_match_{psp}_pattern"


def validate_payment_meta(payment_meta: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate complete payment metadata structure.

    Args:
        payment_meta: Payment metadata dict with psp, payment_link, etc.

    Returns:
        (valid, error_message, normalized_meta)
    """
    if not payment_meta:
        return False, "payment_meta_required", {}

    psp = (payment_meta.get("psp") or "").lower().strip()
    link = (payment_meta.get("payment_link") or "").strip()
    charge_id = payment_meta.get("charge_id") or payment_meta.get("payment_intent_id")

    # Validate PSP
    if not psp:
        return False, "psp_required", {}

    if psp not in ALLOWED_PSP:
        return False, f"psp_not_allowed:{psp}", {}

    # Validate link
    if not link:
        return False, "payment_link_required", {}

    link_valid, link_err = validate_payment_link(psp, link)
    if not link_valid:
        return False, link_err, {}

    # Build normalized metadata
    normalized = {
        "psp": psp,
        "payment_link": link,
        "charge_id": charge_id,
        "validated_at": _now_iso(),
        "psp_verified": True
    }

    return True, None, normalized


def enforce_psp(payment_meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Enforce PSP-only fund flow for DealGraph FUNDED transition.

    This is the main guard function to call before transitioning
    a deal to FUNDED state.

    Args:
        payment_meta: Dict with psp, payment_link, and optionally charge_id

    Returns:
        (allowed, error_message)

    Example:
        ok, err = enforce_psp({
            "psp": "stripe",
            "payment_link": "https://checkout.stripe.com/xxx",
            "charge_id": "ch_xxx"
        })
        if not ok:
            return {"ok": False, "error": err}
    """
    valid, err, _ = validate_payment_meta(payment_meta)
    return valid, err


def get_psp_config(psp: str) -> Dict[str, Any]:
    """Get configuration for a specific PSP"""
    configs = {
        "stripe": {
            "name": "Stripe",
            "supports_escrow": True,
            "supports_connect": True,
            "instant_payout": True,
            "currencies": ["USD", "EUR", "GBP", "CAD", "AUD"]
        },
        "paypal": {
            "name": "PayPal",
            "supports_escrow": False,
            "supports_connect": True,
            "instant_payout": False,
            "currencies": ["USD", "EUR", "GBP", "CAD", "AUD"]
        },
        "upwork": {
            "name": "Upwork",
            "supports_escrow": True,
            "supports_connect": False,
            "instant_payout": False,
            "currencies": ["USD"]
        },
        "shopify": {
            "name": "Shopify Payments",
            "supports_escrow": False,
            "supports_connect": True,
            "instant_payout": True,
            "currencies": ["USD", "EUR", "GBP", "CAD"]
        },
        "fiverr": {
            "name": "Fiverr",
            "supports_escrow": True,
            "supports_connect": False,
            "instant_payout": False,
            "currencies": ["USD"]
        }
    }
    return configs.get(psp.lower(), {
        "name": psp.title(),
        "supports_escrow": False,
        "supports_connect": False,
        "instant_payout": False,
        "currencies": ["USD"]
    })


def list_allowed_psp() -> Dict[str, Any]:
    """List all allowed PSPs with their configurations"""
    return {
        "allowed_psp": list(ALLOWED_PSP),
        "configs": {psp: get_psp_config(psp) for psp in ALLOWED_PSP}
    }


def create_multi_rail_pack(primary_psp: str, primary_link: str, fallbacks: list = None) -> Dict[str, Any]:
    """
    Create a multi-rail payment pack for improved conversion.

    Args:
        primary_psp: Primary PSP name
        primary_link: Primary payment link
        fallbacks: List of {"psp": str, "link": str} fallback options

    Returns:
        Payment pack with validated rails
    """
    rails = []

    # Validate primary
    ok, err = enforce_psp({"psp": primary_psp, "payment_link": primary_link})
    if ok:
        rails.append({
            "psp": primary_psp,
            "link": primary_link,
            "priority": 1,
            "config": get_psp_config(primary_psp)
        })

    # Validate fallbacks
    for i, fb in enumerate(fallbacks or []):
        ok, err = enforce_psp({"psp": fb.get("psp", ""), "payment_link": fb.get("link", "")})
        if ok:
            rails.append({
                "psp": fb["psp"],
                "link": fb["link"],
                "priority": i + 2,
                "config": get_psp_config(fb["psp"])
            })

    return {
        "ok": len(rails) > 0,
        "rails": rails,
        "primary": rails[0] if rails else None,
        "fallback_count": len(rails) - 1 if rails else 0
    }
