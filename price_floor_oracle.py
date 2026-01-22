"""
PRICE-FLOOR ORACLE - AiGentsy v115
==================================

Dynamic pricing constraints to ensure profitability and market health.

FEATURES:
- Minimum price enforcement per outcome type
- Dynamic floor adjustment based on:
  - Cost of fulfillment
  - Market conditions
  - Demand/supply balance
  - Quality requirements
- Anti-dumping protection
- Margin preservation

PRICING MODELS:
- Cost-plus: Floor = Cost + Minimum Margin
- Market-based: Floor = Market Average * Factor
- Quality-adjusted: Floor varies by quality tier
- Dynamic: Floor adjusts in real-time

Powered by AiGentsy
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


AIGENTSY_URL = os.getenv("AIGENTSY_URL", "https://aigentsy.com")


def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


class OutcomeCategory(str, Enum):
    AI_CONTENT = "ai_content"
    AI_ART = "ai_art"
    AI_CODE = "ai_code"
    AI_RESEARCH = "ai_research"
    AI_VIDEO = "ai_video"
    AI_AUDIO = "ai_audio"
    HUMAN_SERVICE = "human_service"
    HYBRID = "hybrid"
    PHYSICAL_PRODUCT = "physical_product"
    DIGITAL_PRODUCT = "digital_product"


class QualityTier(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PricingModel(str, Enum):
    COST_PLUS = "cost_plus"
    MARKET_BASED = "market_based"
    QUALITY_ADJUSTED = "quality_adjusted"
    DYNAMIC = "dynamic"


@dataclass
class PriceFloor:
    """Price floor configuration for an outcome type"""
    category: OutcomeCategory
    base_floor: float
    minimum_margin_percent: float
    quality_multipliers: Dict[str, float] = field(default_factory=dict)
    market_adjustment: float = 1.0
    last_updated: str = ""
    active: bool = True


@dataclass
class CostStructure:
    """Cost structure for fulfillment"""
    category: OutcomeCategory
    ai_cost_per_unit: float  # API costs
    human_cost_per_hour: float  # If applicable
    avg_time_minutes: float
    overhead_percent: float = 0.15
    platform_fee_percent: float = 0.028


# Default price floors by category
DEFAULT_FLOORS: Dict[OutcomeCategory, PriceFloor] = {
    OutcomeCategory.AI_CONTENT: PriceFloor(
        category=OutcomeCategory.AI_CONTENT,
        base_floor=5.00,
        minimum_margin_percent=0.40,
        quality_multipliers={
            QualityTier.BASIC.value: 1.0,
            QualityTier.STANDARD.value: 1.5,
            QualityTier.PREMIUM.value: 2.5,
            QualityTier.ENTERPRISE.value: 5.0
        },
        last_updated=_now()
    ),
    OutcomeCategory.AI_ART: PriceFloor(
        category=OutcomeCategory.AI_ART,
        base_floor=3.00,
        minimum_margin_percent=0.50,
        quality_multipliers={
            QualityTier.BASIC.value: 1.0,
            QualityTier.STANDARD.value: 2.0,
            QualityTier.PREMIUM.value: 4.0,
            QualityTier.ENTERPRISE.value: 10.0
        },
        last_updated=_now()
    ),
    OutcomeCategory.AI_CODE: PriceFloor(
        category=OutcomeCategory.AI_CODE,
        base_floor=15.00,
        minimum_margin_percent=0.35,
        quality_multipliers={
            QualityTier.BASIC.value: 1.0,
            QualityTier.STANDARD.value: 2.0,
            QualityTier.PREMIUM.value: 4.0,
            QualityTier.ENTERPRISE.value: 8.0
        },
        last_updated=_now()
    ),
    OutcomeCategory.AI_RESEARCH: PriceFloor(
        category=OutcomeCategory.AI_RESEARCH,
        base_floor=10.00,
        minimum_margin_percent=0.45,
        quality_multipliers={
            QualityTier.BASIC.value: 1.0,
            QualityTier.STANDARD.value: 1.8,
            QualityTier.PREMIUM.value: 3.5,
            QualityTier.ENTERPRISE.value: 7.0
        },
        last_updated=_now()
    ),
    OutcomeCategory.AI_VIDEO: PriceFloor(
        category=OutcomeCategory.AI_VIDEO,
        base_floor=20.00,
        minimum_margin_percent=0.30,
        quality_multipliers={
            QualityTier.BASIC.value: 1.0,
            QualityTier.STANDARD.value: 2.0,
            QualityTier.PREMIUM.value: 5.0,
            QualityTier.ENTERPRISE.value: 10.0
        },
        last_updated=_now()
    ),
    OutcomeCategory.AI_AUDIO: PriceFloor(
        category=OutcomeCategory.AI_AUDIO,
        base_floor=8.00,
        minimum_margin_percent=0.40,
        quality_multipliers={
            QualityTier.BASIC.value: 1.0,
            QualityTier.STANDARD.value: 1.5,
            QualityTier.PREMIUM.value: 3.0,
            QualityTier.ENTERPRISE.value: 6.0
        },
        last_updated=_now()
    ),
    OutcomeCategory.HUMAN_SERVICE: PriceFloor(
        category=OutcomeCategory.HUMAN_SERVICE,
        base_floor=25.00,
        minimum_margin_percent=0.20,
        quality_multipliers={
            QualityTier.BASIC.value: 1.0,
            QualityTier.STANDARD.value: 1.5,
            QualityTier.PREMIUM.value: 2.5,
            QualityTier.ENTERPRISE.value: 4.0
        },
        last_updated=_now()
    ),
    OutcomeCategory.HYBRID: PriceFloor(
        category=OutcomeCategory.HYBRID,
        base_floor=15.00,
        minimum_margin_percent=0.25,
        quality_multipliers={
            QualityTier.BASIC.value: 1.0,
            QualityTier.STANDARD.value: 1.8,
            QualityTier.PREMIUM.value: 3.0,
            QualityTier.ENTERPRISE.value: 5.0
        },
        last_updated=_now()
    ),
}


# Cost structures
DEFAULT_COSTS: Dict[OutcomeCategory, CostStructure] = {
    OutcomeCategory.AI_CONTENT: CostStructure(
        category=OutcomeCategory.AI_CONTENT,
        ai_cost_per_unit=0.50,
        human_cost_per_hour=0,
        avg_time_minutes=5
    ),
    OutcomeCategory.AI_ART: CostStructure(
        category=OutcomeCategory.AI_ART,
        ai_cost_per_unit=0.30,
        human_cost_per_hour=0,
        avg_time_minutes=2
    ),
    OutcomeCategory.AI_CODE: CostStructure(
        category=OutcomeCategory.AI_CODE,
        ai_cost_per_unit=2.00,
        human_cost_per_hour=0,
        avg_time_minutes=15
    ),
    OutcomeCategory.HUMAN_SERVICE: CostStructure(
        category=OutcomeCategory.HUMAN_SERVICE,
        ai_cost_per_unit=0,
        human_cost_per_hour=25.00,
        avg_time_minutes=60
    ),
    OutcomeCategory.HYBRID: CostStructure(
        category=OutcomeCategory.HYBRID,
        ai_cost_per_unit=1.00,
        human_cost_per_hour=15.00,
        avg_time_minutes=30
    ),
}


# Market data tracking
MARKET_DATA: Dict[OutcomeCategory, Dict[str, Any]] = {}


def get_price_floor(
    category: OutcomeCategory,
    quality_tier: QualityTier = QualityTier.STANDARD,
    pricing_model: PricingModel = PricingModel.QUALITY_ADJUSTED
) -> Dict[str, Any]:
    """
    Get the current price floor for an outcome type.

    Returns the minimum acceptable price to ensure profitability.
    """

    floor_config = DEFAULT_FLOORS.get(category)
    if not floor_config:
        return {
            "ok": False,
            "error": f"Unknown category: {category}",
            "powered_by": "AiGentsy"
        }

    base = floor_config.base_floor
    quality_mult = floor_config.quality_multipliers.get(quality_tier.value, 1.0)
    market_adj = floor_config.market_adjustment

    # Calculate floor based on pricing model
    if pricing_model == PricingModel.COST_PLUS:
        cost = _calculate_cost(category)
        floor = cost * (1 + floor_config.minimum_margin_percent)

    elif pricing_model == PricingModel.MARKET_BASED:
        market_avg = _get_market_average(category)
        floor = market_avg * 0.7 * market_adj  # 70% of market average

    elif pricing_model == PricingModel.QUALITY_ADJUSTED:
        floor = base * quality_mult * market_adj

    elif pricing_model == PricingModel.DYNAMIC:
        # Combine all factors
        cost = _calculate_cost(category)
        market_avg = _get_market_average(category)
        floor = max(
            cost * (1 + floor_config.minimum_margin_percent),
            base * quality_mult,
            market_avg * 0.5
        ) * market_adj

    else:
        floor = base * quality_mult

    return {
        "ok": True,
        "category": category.value,
        "quality_tier": quality_tier.value,
        "pricing_model": pricing_model.value,
        "price_floor": round(floor, 2),
        "base_floor": base,
        "quality_multiplier": quality_mult,
        "market_adjustment": market_adj,
        "minimum_margin": f"{floor_config.minimum_margin_percent * 100:.0f}%",
        "recommendation": f"Do not price below ${floor:.2f}",
        "powered_by": "AiGentsy"
    }


def validate_price(
    category: OutcomeCategory,
    proposed_price: float,
    quality_tier: QualityTier = QualityTier.STANDARD
) -> Dict[str, Any]:
    """
    Validate if a proposed price meets the floor requirements.

    Returns approval status and any adjustments needed.
    """

    floor_data = get_price_floor(category, quality_tier)
    floor = floor_data.get("price_floor", 0)

    if proposed_price >= floor:
        margin = (proposed_price - _calculate_cost(category)) / proposed_price if proposed_price > 0 else 0

        return {
            "ok": True,
            "approved": True,
            "proposed_price": proposed_price,
            "price_floor": floor,
            "margin_above_floor": round(proposed_price - floor, 2),
            "estimated_margin": f"{margin * 100:.1f}%",
            "status": "approved",
            "powered_by": "AiGentsy"
        }

    else:
        return {
            "ok": True,
            "approved": False,
            "proposed_price": proposed_price,
            "price_floor": floor,
            "shortfall": round(floor - proposed_price, 2),
            "recommended_price": floor,
            "status": "rejected",
            "reason": f"Price ${proposed_price:.2f} is below floor ${floor:.2f}",
            "powered_by": "AiGentsy"
        }


def _calculate_cost(category: OutcomeCategory) -> float:
    """Calculate cost of fulfillment for a category"""

    cost_struct = DEFAULT_COSTS.get(category)
    if not cost_struct:
        return 5.00  # Default minimum cost

    # AI costs
    ai_cost = cost_struct.ai_cost_per_unit

    # Human costs (if applicable)
    human_cost = (cost_struct.human_cost_per_hour / 60) * cost_struct.avg_time_minutes

    # Total with overhead
    subtotal = ai_cost + human_cost
    overhead = subtotal * cost_struct.overhead_percent
    platform_fee = subtotal * cost_struct.platform_fee_percent

    return subtotal + overhead + platform_fee


def _get_market_average(category: OutcomeCategory) -> float:
    """Get market average price for a category"""

    market = MARKET_DATA.get(category, {})
    return market.get("average_price", DEFAULT_FLOORS.get(category, PriceFloor(
        category=category, base_floor=10.0, minimum_margin_percent=0.3
    )).base_floor * 2)


def update_market_data(
    category: OutcomeCategory,
    average_price: float,
    volume: int,
    trend: str = "stable"
) -> Dict[str, Any]:
    """Update market data for dynamic pricing"""

    MARKET_DATA[category] = {
        "average_price": average_price,
        "volume": volume,
        "trend": trend,
        "updated_at": _now()
    }

    # Adjust floor based on market conditions
    if category in DEFAULT_FLOORS:
        floor = DEFAULT_FLOORS[category]

        if trend == "rising":
            floor.market_adjustment = 1.1
        elif trend == "falling":
            floor.market_adjustment = 0.95
        else:
            floor.market_adjustment = 1.0

        floor.last_updated = _now()

    return {
        "ok": True,
        "category": category.value,
        "market_data": MARKET_DATA[category],
        "floor_adjustment": DEFAULT_FLOORS.get(category, PriceFloor(
            category=category, base_floor=10.0, minimum_margin_percent=0.3
        )).market_adjustment,
        "powered_by": "AiGentsy"
    }


def get_all_floors() -> Dict[str, Any]:
    """Get all price floors"""

    floors = {}
    for category, floor in DEFAULT_FLOORS.items():
        floors[category.value] = {
            "base_floor": floor.base_floor,
            "minimum_margin": f"{floor.minimum_margin_percent * 100:.0f}%",
            "quality_tiers": {
                k: round(floor.base_floor * v, 2)
                for k, v in floor.quality_multipliers.items()
            },
            "market_adjustment": floor.market_adjustment,
            "last_updated": floor.last_updated
        }

    return {
        "ok": True,
        "floors": floors,
        "total_categories": len(floors),
        "powered_by": "AiGentsy"
    }


def get_oracle_status() -> Dict[str, Any]:
    """Get price floor oracle status"""

    return {
        "ok": True,
        "categories": len(DEFAULT_FLOORS),
        "pricing_models": [m.value for m in PricingModel],
        "quality_tiers": [t.value for t in QualityTier],
        "market_data_tracked": len(MARKET_DATA),
        "active": True,
        "powered_by": "AiGentsy"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_price_oracle(app):
    """Add price oracle endpoints to FastAPI app"""

    from fastapi import Body

    @app.get("/price-oracle/status")
    async def oracle_status():
        """Get oracle status"""
        return get_oracle_status()

    @app.get("/price-oracle/floors")
    async def all_floors():
        """Get all price floors"""
        return get_all_floors()

    @app.get("/price-oracle/floor/{category}")
    async def get_floor(
        category: str,
        quality: str = "standard",
        model: str = "quality_adjusted"
    ):
        """Get price floor for a category"""
        try:
            cat = OutcomeCategory(category)
            tier = QualityTier(quality)
            pricing = PricingModel(model)
            return get_price_floor(cat, tier, pricing)
        except ValueError as e:
            return {"ok": False, "error": str(e)}

    @app.post("/price-oracle/validate")
    async def validate(body: Dict = Body(...)):
        """Validate a proposed price"""
        try:
            cat = OutcomeCategory(body.get("category", "ai_content"))
            tier = QualityTier(body.get("quality", "standard"))
            price = body.get("price", 0)
            return validate_price(cat, price, tier)
        except ValueError as e:
            return {"ok": False, "error": str(e)}

    @app.post("/price-oracle/market-update")
    async def market_update(body: Dict = Body(...)):
        """Update market data"""
        try:
            cat = OutcomeCategory(body.get("category", "ai_content"))
            return update_market_data(
                category=cat,
                average_price=body.get("average_price", 10),
                volume=body.get("volume", 100),
                trend=body.get("trend", "stable")
            )
        except ValueError as e:
            return {"ok": False, "error": str(e)}

    print("=" * 80)
    print("💰 PRICE-FLOOR ORACLE LOADED - Powered by AiGentsy")
    print("=" * 80)
    print("Endpoints:")
    print("  GET  /price-oracle/status")
    print("  GET  /price-oracle/floors")
    print("  GET  /price-oracle/floor/{category}")
    print("  POST /price-oracle/validate")
    print("  POST /price-oracle/market-update")
    print("=" * 80)


if __name__ == "__main__":
    print("=" * 60)
    print("PRICE-FLOOR ORACLE TEST - Powered by AiGentsy")
    print("=" * 60)

    # Test price floors
    for category in [OutcomeCategory.AI_CONTENT, OutcomeCategory.AI_CODE, OutcomeCategory.HUMAN_SERVICE]:
        print(f"\n{category.value.upper()}:")
        for tier in QualityTier:
            floor = get_price_floor(category, tier)
            print(f"  {tier.value}: ${floor['price_floor']:.2f}")

    # Test validation
    print("\n" + "=" * 60)
    print("PRICE VALIDATION")
    print("=" * 60)

    test_cases = [
        (OutcomeCategory.AI_CONTENT, 10.00),  # Should pass
        (OutcomeCategory.AI_CONTENT, 2.00),   # Should fail
        (OutcomeCategory.AI_CODE, 50.00),     # Should pass
        (OutcomeCategory.AI_CODE, 5.00),      # Should fail
    ]

    for cat, price in test_cases:
        result = validate_price(cat, price)
        status = "✅" if result["approved"] else "❌"
        print(f"{status} {cat.value} @ ${price:.2f}: {result['status']}")
