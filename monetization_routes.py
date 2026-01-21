"""
MONETIZATION API ROUTES
=======================

Exposes monetization fabric capabilities via HTTP endpoints.

Routes:
- /money/capabilities: List all monetization capabilities
- /money/quote/*: Pricing quotes for various services
- /money/data/*: Data product purchases
- /money/badge/*: Badge management
- /money/license/*: Licensing quotes
- /money/subscription/*: Subscription management
- /money/referral/*: Referral chain management
- /money/ledger/*: Ledger queries
- /money/settlement/*: Settlement/payout operations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORT MONETIZATION MODULES
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from monetization import MonetizationFabric
    from monetization.fee_schedule import (
        get_fee, override_fee, calculate_platform_fee, get_schedule
    )
    from monetization.pricing_arm import (
        suggest as price_suggest, get_pricing_arm
    )
    from monetization.revenue_router import (
        split as revenue_split, split_with_premium
    )
    from monetization.ledger import (
        post_entry, get_entity_balance, get_entity_ledger, get_ledger_stats
    )
    from monetization.settlements import (
        queue_settlement, process_settlements, get_pending_settlements
    )
    from monetization.arbitrage_engine import (
        detect_spread_opportunity, detect_fx_arbitrage, get_arbitrage_stats
    )
    from monetization.sponsorships import (
        sell_slot, get_active_sponsorships, get_available_slots
    )
    from monetization.referrals import (
        allocate_referrals, register_chain, record_attribution
    )
    from monetization.subscriptions import (
        subscribe, get_tier, check_quota, record_usage
    )
    from monetization.licensing import (
        quote_oem, quote_white_label, quote_network, issue_license
    )
    from monetization.data_products import (
        telemetry_pack, benchmark_badge, purchase_data_product
    )
    from monetization.proof_badges import (
        mint_badge, get_entity_badges, calculate_conversion_boost, verify_badge
    )
    MONETIZATION_AVAILABLE = True
except ImportError as e:
    MONETIZATION_AVAILABLE = False
    print(f"Monetization routes: modules not available - {e}")


router = APIRouter(prefix="/money", tags=["monetization"])


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class PriceQuoteRequest(BaseModel):
    base_price: float
    fx_rate: float = 1.0
    load_pct: float = 0.3
    wave_score: float = 0.2
    cogs: float = 0.0
    min_margin: float = 0.25


class RevenueSplitRequest(BaseModel):
    gross: float
    user_pct: float = 0.70
    pool_pct: float = 0.10
    partner_pct: float = 0.05
    referral_chain: List[str] = []


class LedgerEntryRequest(BaseModel):
    entry_type: str
    ref: str
    debit: float = 0
    credit: float = 0
    meta: Dict[str, Any] = {}


class SubscribeRequest(BaseModel):
    user: str
    tier: str
    billing_period: str = "monthly"


class LicenseQuoteRequest(BaseModel):
    license_type: str  # oem, white_label, network
    seats: int = 10
    connectors: int = 5
    region: str = "us"
    custom_domain: bool = False
    custom_branding: bool = False
    nodes: int = 10
    expected_monthly_revenue: float = 50000


class DataProductRequest(BaseModel):
    buyer: str
    product_type: str
    config: Dict[str, Any] = {}


class SponsorshipRequest(BaseModel):
    slot_type: str
    buyer: str
    days: int = 1
    content: Dict[str, Any] = {}


class ReferralChainRequest(BaseModel):
    user: str
    chain: List[str]


class BadgeAttestationRequest(BaseModel):
    outcome_id: str
    outcome_type: str
    outcome_hash: str
    sla_verdict: str = "pass"
    proofs: List[Dict[str, Any]] = []
    entity: str


class SettlementRequest(BaseModel):
    entity: str
    stripe_account_id: Optional[str] = None
    method: str = "stripe"


# ═══════════════════════════════════════════════════════════════════════════════
# CAPABILITIES ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/capabilities")
async def get_monetization_capabilities():
    """List all monetization capabilities and fee schedule"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return {
        "ok": True,
        "capabilities": [
            "pricing_arm",
            "revenue_routing",
            "double_entry_ledger",
            "settlements",
            "arbitrage_detection",
            "sponsorships",
            "referrals",
            "subscriptions",
            "licensing",
            "data_products",
            "proof_badges"
        ],
        "fee_schedule": get_schedule(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PRICING ARM ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/quote/price")
async def quote_dynamic_price(req: PriceQuoteRequest):
    """Get dynamic price with surge, FX, wave uplift"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    suggested = price_suggest(
        req.base_price,
        fx_rate=req.fx_rate,
        load_pct=req.load_pct,
        wave_score=req.wave_score,
        cogs=req.cogs,
        min_margin=req.min_margin
    )

    return {
        "ok": True,
        "base_price": req.base_price,
        "suggested_price": suggested,
        "uplift_pct": round((suggested - req.base_price) / req.base_price * 100, 2) if req.base_price > 0 else 0
    }


@router.get("/quote/platform-fee")
async def quote_platform_fee(amount: float = Query(...)):
    """Calculate platform fee for amount"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return calculate_platform_fee(amount)


# ═══════════════════════════════════════════════════════════════════════════════
# REVENUE ROUTING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/revenue/split")
async def split_revenue(req: RevenueSplitRequest):
    """Split revenue across platform, user, pool, partner"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    splits = revenue_split(
        req.gross,
        user_pct=req.user_pct,
        pool_pct=req.pool_pct,
        partner_pct=req.partner_pct
    )

    # Add referral allocation if chain provided
    if req.referral_chain:
        ref_alloc = allocate_referrals(req.gross, req.referral_chain)
        splits["referrals"] = ref_alloc["splits"]
        splits["referral_total"] = ref_alloc["total_allocated"]

    return {"ok": True, **splits}


# ═══════════════════════════════════════════════════════════════════════════════
# LEDGER ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ledger/entry")
async def create_ledger_entry(req: LedgerEntryRequest):
    """Post a double-entry ledger entry"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return post_entry(
        req.entry_type,
        req.ref,
        debit=req.debit,
        credit=req.credit,
        meta=req.meta
    )


@router.get("/ledger/balance/{entity}")
async def get_balance(entity: str):
    """Get entity balance"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return get_entity_balance(entity)


@router.get("/ledger/history/{entity}")
async def get_ledger_history(entity: str, limit: int = Query(100)):
    """Get entity ledger history"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return get_entity_ledger(entity, limit=limit)


@router.get("/ledger/stats")
async def get_stats():
    """Get ledger statistics"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return get_ledger_stats()


# ═══════════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/subscription/subscribe")
async def create_subscription(req: SubscribeRequest):
    """Subscribe user to a tier"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return subscribe(req.user, req.tier, billing_period=req.billing_period)


@router.get("/subscription/tier/{tier_name}")
async def get_tier_info(tier_name: str):
    """Get tier details"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return get_tier(tier_name)


@router.get("/subscription/quota/{user}")
async def check_user_quota(user: str, calls_needed: int = Query(1)):
    """Check user API quota"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return check_quota(user, calls_needed)


# ═══════════════════════════════════════════════════════════════════════════════
# LICENSING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/license/quote")
async def get_license_quote(req: LicenseQuoteRequest):
    """Get licensing quote"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    if req.license_type == "oem":
        return quote_oem(
            seats=req.seats,
            connectors=req.connectors,
            region=req.region
        )
    elif req.license_type == "white_label":
        return quote_white_label(
            seats=req.seats,
            connectors=req.connectors,
            custom_domain=req.custom_domain,
            custom_branding=req.custom_branding,
            region=req.region
        )
    elif req.license_type == "network":
        return quote_network(
            nodes=req.nodes,
            expected_monthly_revenue=req.expected_monthly_revenue,
            region=req.region
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown license type: {req.license_type}")


@router.post("/license/issue")
async def create_license(
    license_type: str = Body(...),
    licensee: str = Body(...),
    config: Dict[str, Any] = Body({}),
    billing_period: str = Body("monthly")
):
    """Issue a license"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return issue_license(license_type, licensee, config, billing_period=billing_period)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA PRODUCTS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/data/telemetry-pack")
async def quote_telemetry_pack(rows: int = Query(10000)):
    """Quote telemetry pack pricing"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return telemetry_pack(rows)


@router.get("/data/benchmark-badge")
async def quote_benchmark_badge(outcome_type: str = Query(...), percentile: int = Query(90)):
    """Quote benchmark badge pricing"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return benchmark_badge(outcome_type, percentile)


@router.post("/data/purchase")
async def purchase_product(req: DataProductRequest):
    """Purchase a data product"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return purchase_data_product(req.buyer, req.product_type, req.config)


# ═══════════════════════════════════════════════════════════════════════════════
# SPONSORSHIP ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/sponsorship/slots")
async def list_available_slots():
    """List available sponsorship slots"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return get_available_slots()


@router.get("/sponsorship/active")
async def list_active_sponsorships():
    """List active sponsorships"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return get_active_sponsorships()


@router.post("/sponsorship/purchase")
async def purchase_sponsorship(req: SponsorshipRequest):
    """Purchase a sponsorship slot"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return sell_slot(req.slot_type, req.buyer, days=req.days, content=req.content)


# ═══════════════════════════════════════════════════════════════════════════════
# REFERRAL ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/referral/register")
async def register_referral_chain(req: ReferralChainRequest):
    """Register a referral chain for a user"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return register_chain(req.user, req.chain)


@router.post("/referral/allocate")
async def allocate_referral_revenue(
    gross: float = Body(...),
    chain: List[str] = Body(...)
):
    """Allocate referral revenue across chain"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return allocate_referrals(gross, chain)


@router.post("/referral/attribute")
async def attribute_revenue(
    user: str = Body(...),
    gross: float = Body(...),
    source: str = Body("purchase")
):
    """Record attribution for user revenue event"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return record_attribution(user, gross, source=source)


# ═══════════════════════════════════════════════════════════════════════════════
# PROOF BADGE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/badge/mint")
async def mint_proof_badge(req: BadgeAttestationRequest):
    """Mint a proof-of-outcome badge"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    attestation = {
        "outcome_id": req.outcome_id,
        "outcome_type": req.outcome_type,
        "outcome_hash": req.outcome_hash,
        "sla_verdict": req.sla_verdict,
        "proofs": req.proofs,
        "entity": req.entity
    }

    return mint_badge(attestation)


@router.get("/badge/entity/{entity}")
async def get_badges_for_entity(entity: str):
    """Get all badges for an entity"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return {
        "ok": True,
        "entity": entity,
        "badges": get_entity_badges(entity),
        "conversion_boost": calculate_conversion_boost(entity)
    }


@router.get("/badge/verify/{badge_id}")
async def verify_proof_badge(badge_id: str):
    """Verify a badge is authentic"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return verify_badge(badge_id)


# ═══════════════════════════════════════════════════════════════════════════════
# ARBITRAGE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/arbitrage/detect-spread")
async def detect_spread(
    bids: List[Dict[str, Any]] = Body(...),
    asks: List[Dict[str, Any]] = Body(...),
    min_pct: float = Body(0.12)
):
    """Detect spread arbitrage opportunity"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return detect_spread_opportunity(bids, asks, min_pct=min_pct)


@router.get("/arbitrage/stats")
async def arbitrage_stats():
    """Get arbitrage engine statistics"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return get_arbitrage_stats()


# ═══════════════════════════════════════════════════════════════════════════════
# SETTLEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/settlement/queue")
async def queue_payout(req: SettlementRequest):
    """Queue a settlement/payout"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return queue_settlement(req.entity, req.stripe_account_id, method=req.method)


@router.get("/settlement/pending")
async def list_pending_settlements():
    """List pending settlements"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return get_pending_settlements()


@router.post("/settlement/process")
async def process_pending_settlements():
    """Process all pending settlements"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return await process_settlements()


# ═══════════════════════════════════════════════════════════════════════════════
# FEE SCHEDULE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/fees")
async def get_fee_schedule():
    """Get current fee schedule"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    return {"ok": True, "schedule": get_schedule()}


@router.get("/fees/{key}")
async def get_specific_fee(key: str, default: float = Query(None)):
    """Get a specific fee value"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    value = get_fee(key, default)
    return {"ok": True, "key": key, "value": value}


@router.post("/fees/{key}")
async def set_fee(key: str, value: float = Body(..., embed=True)):
    """Override a fee value (admin)"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization fabric not available")

    override_fee(key, value)
    return {"ok": True, "key": key, "value": value}
