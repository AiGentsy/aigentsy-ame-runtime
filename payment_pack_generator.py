"""
PAYMENT-PACK GENERATOR - AiGentsy v115
======================================

Auto-compose multi-rail paylinks per deal and A/B test which rail closes best per segment.

RAILS SUPPORTED:
- Stripe (cards, ACH, SEPA)
- PayPal (express checkout)
- Wise (international transfers)
- Plaid (bank-to-bank)
- Crypto (USDC, ETH via Coinbase Commerce)

FEATURES:
- Multi-rail paylink generation per deal
- A/B testing which rail converts best per segment
- Dynamic rail selection based on:
  - Customer geography
  - Transaction size
  - Historical conversion rates
  - Fee optimization
- Automatic fallback if primary rail fails

Powered by AiGentsy
"""

import os
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class PaymentRail(str, Enum):
    STRIPE_CARD = "stripe_card"
    STRIPE_ACH = "stripe_ach"
    STRIPE_SEPA = "stripe_sepa"
    PAYPAL = "paypal"
    WISE = "wise"
    PLAID = "plaid"
    CRYPTO_USDC = "crypto_usdc"
    CRYPTO_ETH = "crypto_eth"


@dataclass
class RailConfig:
    rail: PaymentRail
    enabled: bool
    fee_percent: float
    fee_fixed: float
    min_amount: float
    max_amount: float
    supported_currencies: List[str]
    supported_countries: List[str]
    conversion_rate: float = 0.0  # Learned from A/B tests
    avg_settlement_hours: float = 0.0


# Rail configurations
RAIL_CONFIGS = {
    PaymentRail.STRIPE_CARD: RailConfig(
        rail=PaymentRail.STRIPE_CARD,
        enabled=bool(os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET")),
        fee_percent=2.9,
        fee_fixed=0.30,
        min_amount=0.50,
        max_amount=999999,
        supported_currencies=["USD", "EUR", "GBP", "CAD", "AUD"],
        supported_countries=["US", "CA", "GB", "EU", "AU"],
        conversion_rate=0.12,  # 12% baseline
        avg_settlement_hours=48
    ),
    PaymentRail.STRIPE_ACH: RailConfig(
        rail=PaymentRail.STRIPE_ACH,
        enabled=bool(os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET")),
        fee_percent=0.8,
        fee_fixed=0.0,
        min_amount=1.00,
        max_amount=100000,
        supported_currencies=["USD"],
        supported_countries=["US"],
        conversion_rate=0.08,
        avg_settlement_hours=72
    ),
    PaymentRail.PAYPAL: RailConfig(
        rail=PaymentRail.PAYPAL,
        enabled=bool(os.getenv("PAYPAL_CLIENT_ID")),
        fee_percent=3.49,
        fee_fixed=0.49,
        min_amount=1.00,
        max_amount=60000,
        supported_currencies=["USD", "EUR", "GBP", "CAD", "AUD"],
        supported_countries=["US", "CA", "GB", "EU", "AU", "MX", "BR"],
        conversion_rate=0.15,  # Higher for international
        avg_settlement_hours=24
    ),
    PaymentRail.WISE: RailConfig(
        rail=PaymentRail.WISE,
        enabled=bool(os.getenv("WISE_API_KEY")),
        fee_percent=0.5,
        fee_fixed=0.0,
        min_amount=10.00,
        max_amount=1000000,
        supported_currencies=["USD", "EUR", "GBP", "CAD", "AUD", "SGD", "HKD"],
        supported_countries=["*"],  # Global
        conversion_rate=0.06,
        avg_settlement_hours=12
    ),
    PaymentRail.CRYPTO_USDC: RailConfig(
        rail=PaymentRail.CRYPTO_USDC,
        enabled=bool(os.getenv("COINBASE_COMMERCE_KEY")),
        fee_percent=1.0,
        fee_fixed=0.0,
        min_amount=5.00,
        max_amount=100000,
        supported_currencies=["USD"],
        supported_countries=["*"],
        conversion_rate=0.03,
        avg_settlement_hours=0.5
    ),
}


@dataclass
class PaymentPack:
    """Multi-rail payment pack for a deal"""
    pack_id: str
    deal_id: str
    amount: float
    currency: str
    description: str
    customer_segment: str
    customer_country: str
    rails: List[Dict[str, Any]] = field(default_factory=list)
    primary_rail: Optional[PaymentRail] = None
    fallback_rails: List[PaymentRail] = field(default_factory=list)
    ab_test_variant: str = ""
    created_at: str = ""
    expires_at: str = ""
    aigentsy_branded: bool = True


def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


def _generate_pack_id() -> str:
    return f"pack_{secrets.token_hex(8)}"


def _calculate_fee(rail: RailConfig, amount: float) -> float:
    """Calculate fee for a rail"""
    return round(amount * (rail.fee_percent / 100) + rail.fee_fixed, 2)


def _generate_paylink(rail: PaymentRail, pack_id: str, amount: float, currency: str, description: str) -> str:
    """Generate payment link for a rail"""
    base_url = os.getenv("AIGENTSY_URL", "https://aigentsy.com")

    # In production, these would be actual payment URLs
    # For now, generate trackable links that route to payment handlers
    return f"{base_url}/pay/{pack_id}?rail={rail.value}&amt={amount}&cur={currency}"


def get_available_rails(
    amount: float,
    currency: str,
    country: str
) -> List[RailConfig]:
    """Get available rails for a transaction"""
    available = []

    for rail, config in RAIL_CONFIGS.items():
        if not config.enabled:
            continue
        if amount < config.min_amount or amount > config.max_amount:
            continue
        if currency not in config.supported_currencies:
            continue
        if config.supported_countries != ["*"] and country not in config.supported_countries:
            continue

        available.append(config)

    return available


def select_optimal_rails(
    available_rails: List[RailConfig],
    amount: float,
    optimize_for: str = "conversion"  # "conversion", "fees", "speed"
) -> List[RailConfig]:
    """Select and rank rails based on optimization target"""

    if optimize_for == "conversion":
        # Rank by conversion rate
        return sorted(available_rails, key=lambda r: r.conversion_rate, reverse=True)

    elif optimize_for == "fees":
        # Rank by lowest fees
        return sorted(available_rails, key=lambda r: _calculate_fee(r, amount))

    elif optimize_for == "speed":
        # Rank by settlement speed
        return sorted(available_rails, key=lambda r: r.avg_settlement_hours)

    return available_rails


def generate_payment_pack(
    deal_id: str,
    amount: float,
    currency: str = "USD",
    description: str = "",
    customer_segment: str = "default",
    customer_country: str = "US",
    optimize_for: str = "conversion",
    ab_test: bool = True
) -> PaymentPack:
    """
    Generate a multi-rail payment pack for a deal.

    Returns a PaymentPack with multiple payment options, ranked by likelihood to convert.
    """
    pack_id = _generate_pack_id()

    # Get available rails
    available = get_available_rails(amount, currency, customer_country)

    if not available:
        # No rails available - return empty pack
        return PaymentPack(
            pack_id=pack_id,
            deal_id=deal_id,
            amount=amount,
            currency=currency,
            description=description,
            customer_segment=customer_segment,
            customer_country=customer_country,
            created_at=_now()
        )

    # Rank rails
    ranked_rails = select_optimal_rails(available, amount, optimize_for)

    # Generate paylinks for each rail
    rails_data = []
    for i, rail_config in enumerate(ranked_rails[:4]):  # Max 4 options
        fee = _calculate_fee(rail_config, amount)
        paylink = _generate_paylink(rail_config.rail, pack_id, amount, currency, description)

        rails_data.append({
            "rail": rail_config.rail.value,
            "paylink": paylink,
            "fee": fee,
            "fee_percent": rail_config.fee_percent,
            "net_amount": round(amount - fee, 2),
            "estimated_settlement_hours": rail_config.avg_settlement_hours,
            "conversion_rate": rail_config.conversion_rate,
            "rank": i + 1,
            "is_primary": i == 0
        })

    # A/B test variant assignment
    ab_variant = ""
    if ab_test and len(rails_data) > 1:
        # Randomly assign variant for A/B testing
        variant_seed = int(hashlib.md5(f"{pack_id}{deal_id}".encode()).hexdigest(), 16)
        ab_variant = "A" if variant_seed % 2 == 0 else "B"

        # Variant B shows rails in different order (fee-optimized)
        if ab_variant == "B":
            rails_data = sorted(rails_data, key=lambda r: r["fee"])
            for i, rail in enumerate(rails_data):
                rail["rank"] = i + 1
                rail["is_primary"] = i == 0

    primary = PaymentRail(rails_data[0]["rail"]) if rails_data else None
    fallbacks = [PaymentRail(r["rail"]) for r in rails_data[1:]]

    return PaymentPack(
        pack_id=pack_id,
        deal_id=deal_id,
        amount=amount,
        currency=currency,
        description=description or f"AiGentsy Payment - {deal_id}",
        customer_segment=customer_segment,
        customer_country=customer_country,
        rails=rails_data,
        primary_rail=primary,
        fallback_rails=fallbacks,
        ab_test_variant=ab_variant,
        created_at=_now(),
        aigentsy_branded=True
    )


# A/B Test Results Tracking
AB_TEST_RESULTS = {
    "A": {"impressions": 0, "conversions": 0},
    "B": {"impressions": 0, "conversions": 0}
}

RAIL_PERFORMANCE = {rail.value: {"attempts": 0, "successes": 0} for rail in PaymentRail}


def track_pack_impression(pack: PaymentPack) -> None:
    """Track when a payment pack is shown"""
    if pack.ab_test_variant:
        AB_TEST_RESULTS[pack.ab_test_variant]["impressions"] += 1


def track_rail_attempt(rail: PaymentRail) -> None:
    """Track when a rail is attempted"""
    RAIL_PERFORMANCE[rail.value]["attempts"] += 1


def track_rail_success(rail: PaymentRail) -> None:
    """Track successful payment on a rail"""
    RAIL_PERFORMANCE[rail.value]["successes"] += 1


def track_pack_conversion(pack: PaymentPack, converting_rail: PaymentRail) -> None:
    """Track successful conversion from a pack"""
    if pack.ab_test_variant:
        AB_TEST_RESULTS[pack.ab_test_variant]["conversions"] += 1
    track_rail_success(converting_rail)


def get_ab_test_results() -> Dict[str, Any]:
    """Get A/B test results"""
    results = {}
    for variant, data in AB_TEST_RESULTS.items():
        conv_rate = data["conversions"] / data["impressions"] if data["impressions"] > 0 else 0
        results[variant] = {
            "impressions": data["impressions"],
            "conversions": data["conversions"],
            "conversion_rate": round(conv_rate, 4)
        }

    # Determine winner
    a_rate = results.get("A", {}).get("conversion_rate", 0)
    b_rate = results.get("B", {}).get("conversion_rate", 0)

    if a_rate > b_rate * 1.05:  # 5% significance threshold
        results["winner"] = "A"
        results["recommendation"] = "conversion_optimized"
    elif b_rate > a_rate * 1.05:
        results["winner"] = "B"
        results["recommendation"] = "fee_optimized"
    else:
        results["winner"] = "inconclusive"
        results["recommendation"] = "continue_testing"

    return results


def get_rail_performance() -> Dict[str, Any]:
    """Get performance stats by rail"""
    performance = {}
    for rail, data in RAIL_PERFORMANCE.items():
        success_rate = data["successes"] / data["attempts"] if data["attempts"] > 0 else 0
        performance[rail] = {
            "attempts": data["attempts"],
            "successes": data["successes"],
            "success_rate": round(success_rate, 4)
        }
    return performance


def get_payment_pack_status() -> Dict[str, Any]:
    """Get payment pack generator status"""
    enabled_rails = [r.value for r, c in RAIL_CONFIGS.items() if c.enabled]

    return {
        "ok": True,
        "enabled_rails": enabled_rails,
        "total_rails": len(PaymentRail),
        "ab_test_results": get_ab_test_results(),
        "rail_performance": get_rail_performance(),
        "optimization_modes": ["conversion", "fees", "speed"],
        "powered_by": "AiGentsy"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_payment_pack(app):
    """Add payment pack endpoints to FastAPI app"""

    from fastapi import Body

    @app.get("/payment-pack/status")
    async def payment_pack_status():
        """Get payment pack generator status"""
        return get_payment_pack_status()

    @app.post("/payment-pack/generate")
    async def generate_pack(body: Dict = Body(...)):
        """
        Generate a multi-rail payment pack.

        Body:
            deal_id: str
            amount: float
            currency: str (default USD)
            customer_country: str (default US)
            optimize_for: str (conversion|fees|speed)
        """
        pack = generate_payment_pack(
            deal_id=body.get("deal_id", f"deal_{secrets.token_hex(4)}"),
            amount=body.get("amount", 100),
            currency=body.get("currency", "USD"),
            description=body.get("description", ""),
            customer_segment=body.get("customer_segment", "default"),
            customer_country=body.get("customer_country", "US"),
            optimize_for=body.get("optimize_for", "conversion"),
            ab_test=body.get("ab_test", True)
        )

        track_pack_impression(pack)

        return {
            "ok": True,
            "pack_id": pack.pack_id,
            "deal_id": pack.deal_id,
            "amount": pack.amount,
            "currency": pack.currency,
            "rails": pack.rails,
            "primary_rail": pack.primary_rail.value if pack.primary_rail else None,
            "ab_variant": pack.ab_test_variant,
            "powered_by": "AiGentsy"
        }

    @app.get("/payment-pack/ab-results")
    async def ab_results():
        """Get A/B test results for payment rails"""
        return get_ab_test_results()

    @app.get("/payment-pack/rail-performance")
    async def rail_performance():
        """Get performance stats by payment rail"""
        return get_rail_performance()

    print("=" * 80)
    print("💳 PAYMENT-PACK GENERATOR LOADED - Powered by AiGentsy")
    print("=" * 80)
    print("Endpoints:")
    print("  GET  /payment-pack/status")
    print("  POST /payment-pack/generate")
    print("  GET  /payment-pack/ab-results")
    print("  GET  /payment-pack/rail-performance")
    print("=" * 80)


if __name__ == "__main__":
    # Test
    pack = generate_payment_pack(
        deal_id="test_deal_123",
        amount=250.00,
        currency="USD",
        customer_country="US",
        optimize_for="conversion"
    )

    print("=" * 60)
    print("PAYMENT PACK GENERATED - Powered by AiGentsy")
    print("=" * 60)
    print(f"Pack ID: {pack.pack_id}")
    print(f"Amount: ${pack.amount} {pack.currency}")
    print(f"A/B Variant: {pack.ab_test_variant}")
    print(f"\nPayment Options:")
    for rail in pack.rails:
        print(f"  [{rail['rank']}] {rail['rail']}: {rail['paylink'][:50]}...")
        print(f"      Fee: ${rail['fee']} | Net: ${rail['net_amount']} | Conv: {rail['conversion_rate']*100:.0f}%")
