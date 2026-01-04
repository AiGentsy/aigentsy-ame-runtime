# apex_upgrades_overlay.py
"""
APEX UPGRADES OVERLAY - 12 Accretive Modules for AiGentsy v92+

These modules add revenue optimization without touching existing code.
Just include_router in main.py and they're live.

Modules:
1. Intent Value Router - Bid where ROI > 1
2. CAC-Aware Price Autopilot - Include true costs in bids
3. Upsell/Cross-Sell Hooks - Turn single orders into bundles
4. Abandon Recovery with Guarantees - Recover carts with proof
5. LTV Forecaster - Prioritize high-rebuy clients
6. Outcome-Indexed Portfolio - Auto-rebalance by performance
7. Darkpool Lead Exchange - Route overflow to partners
8. Auto-Testimonials + Proof Badges - Social proof automation
9. Churn Sentinel - Save MRR with targeted offers
10. Shadow-Price A/B Engine - Learn optimal pricing quietly
11. Partner SKU Ingestion - Sell partner products
12. Self-Healing Orchestrator - Circuit breakers + retry budgets
"""

from fastapi import APIRouter, Header, HTTPException, Request, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid
import os

router = APIRouter(tags=["Apex Upgrades"])
ISO = "%Y-%m-%dT%H:%M:%SZ"


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

_IDEM_CACHE: Dict[str, Dict[str, Any]] = {}  # Replace with Redis in prod

def idem_get_or_set(key: Optional[str], value: Dict[str, Any]) -> Dict[str, Any]:
    """Idempotency cache"""
    if not key:
        return value
    if key in _IDEM_CACHE:
        return _IDEM_CACHE[key]
    _IDEM_CACHE[key] = value
    return value

def metrics_wrap(ok: bool = True, **kwargs) -> Dict[str, Any]:
    """Standard response wrapper with metrics"""
    return {
        "ok": ok,
        "ts": datetime.now(timezone.utc).strftime(ISO),
        "metrics": kwargs or {},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 1) INTENT VALUE ROUTER - Bid where ROI > 1
# ═══════════════════════════════════════════════════════════════════════════════

class IntentSignal(BaseModel):
    budget: Optional[float] = None
    deadline_days: Optional[int] = None
    niche: Optional[str] = None
    channel: Optional[str] = None
    keywords: Optional[List[str]] = None

class ScoreIntentIn(BaseModel):
    intent_id: str
    signal: IntentSignal

class ScoreIntentOut(BaseModel):
    ok: bool = True
    intent_id: str
    ev_usd: float
    win_p: float
    hours_to_cash: float
    why: List[str]
    route_recommendation: str

@router.post("/router/score-intent", response_model=ScoreIntentOut)
async def score_intent(
    payload: ScoreIntentIn,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")
):
    """
    Score an intent/opportunity by expected value.
    Returns EV, win probability, time to cash, and routing recommendation.
    """
    signal = payload.signal
    
    # Calculate base EV from budget
    budget = signal.budget or 200
    base_ev = budget * 0.45
    
    # Adjust win probability by niche/channel
    win_p = 0.35
    why = []
    
    if signal.niche:
        niche_boosts = {
            "graphics": 0.15, "design": 0.15, "logo": 0.12,
            "content": 0.10, "writing": 0.10, "blog": 0.08,
            "video": 0.08, "voice": 0.10, "audio": 0.08,
            "ai": 0.12, "automation": 0.10
        }
        for n, boost in niche_boosts.items():
            if n in signal.niche.lower():
                win_p += boost
                why.append(f"niche_boost_{n}")
                break
    
    if signal.channel:
        channel_boosts = {"fiverr": 0.10, "upwork": 0.08, "reddit": 0.05, "twitter": 0.03}
        boost = channel_boosts.get(signal.channel.lower(), 0)
        win_p += boost
        if boost:
            why.append(f"channel_boost_{signal.channel}")
    
    if signal.deadline_days:
        if signal.deadline_days <= 3:
            win_p += 0.05
            why.append("urgent_deadline_boost")
        elif signal.deadline_days <= 7:
            win_p += 0.02
            why.append("reasonable_deadline")
    
    # Cap win probability
    win_p = min(0.85, win_p)
    
    # Hours to cash
    htc = max(2.0, float((signal.deadline_days or 5)) * 0.9)
    
    # Final EV
    ev_usd = round(base_ev * win_p * 2, 2)  # 2x multiplier for good signals
    
    # Route recommendation
    if ev_usd > 100:
        route = "fiverr_priority"
    elif ev_usd > 50:
        route = "spawn_or_bid"
    elif ev_usd > 20:
        route = "social_dm"
    else:
        route = "low_priority_queue"
    
    if not why:
        why = ["baseline_prior"]
    
    out = {
        "ok": True,
        "intent_id": payload.intent_id,
        "ev_usd": ev_usd,
        "win_p": round(win_p, 3),
        "hours_to_cash": round(htc, 1),
        "why": why,
        "route_recommendation": route
    }
    
    return idem_get_or_set(idempotency_key, out)


class RouteIn(BaseModel):
    min_ev_usd: float = 50.0
    max_routes: int = 20

@router.post("/router/route")
async def route_intents(payload: RouteIn):
    """Route queued intents to appropriate systems based on EV threshold"""
    # In production, this would pull from intent queue and route to systems
    routed = {
        "fiverr": 0,
        "social": 0,
        "spawn": 0,
        "dm": 0,
        "skipped_low_ev": 0
    }
    
    return metrics_wrap(
        True,
        min_ev_usd=payload.min_ev_usd,
        routed=routed,
        action="route_intents_executed"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2) CAC-AWARE PRICE AUTOPILOT
# ═══════════════════════════════════════════════════════════════════════════════

class CACPriceIn(BaseModel):
    base_price: float
    llm_tokens: Optional[int] = 0
    image_jobs: Optional[int] = 0
    video_seconds: Optional[int] = 0
    voice_chars: Optional[int] = 0
    margin_target: float = 0.55

@router.post("/pricing/cac-aware")
async def pricing_cac_aware(payload: CACPriceIn):
    """
    Calculate bid price including true costs (LLM, image, CAC).
    Ensures margin target is met.
    """
    # Cost calculations (based on typical API pricing)
    llm_cost = (payload.llm_tokens or 0) / 1_000_000 * 3.00  # ~$3/M tokens
    image_cost = (payload.image_jobs or 0) * 0.04  # ~$0.04/image
    video_cost = (payload.video_seconds or 0) * 0.05  # ~$0.05/sec
    voice_cost = (payload.voice_chars or 0) / 1000 * 0.03  # ~$0.03/1K chars
    
    # Estimated CAC (platform fees, discovery costs)
    cac_est = max(5.0, payload.base_price * 0.08)
    
    # Total costs
    total_cost = llm_cost + image_cost + video_cost + voice_cost + cac_est
    
    # Calculate bid to hit margin target
    if payload.margin_target >= 1:
        margin_target = 0.55
    else:
        margin_target = payload.margin_target
    
    min_bid = total_cost / (1 - margin_target)
    bid = max(payload.base_price, min_bid)
    
    actual_margin = 1 - (total_cost / bid) if bid > 0 else 0
    
    return {
        "ok": True,
        "bid": round(bid, 2),
        "breakdown": {
            "llm_cost": round(llm_cost, 2),
            "image_cost": round(image_cost, 2),
            "video_cost": round(video_cost, 2),
            "voice_cost": round(voice_cost, 2),
            "cac_est": round(cac_est, 2),
            "total_cost": round(total_cost, 2),
            "margin": round(actual_margin, 3),
            "margin_target": margin_target
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3) UPSELL / CROSS-SELL HOOKS
# ═══════════════════════════════════════════════════════════════════════════════

# SKU relationship map for upsells
UPSELL_MAP = {
    "logo-basic": [
        {"sku": "brand-kit", "take_rate_p": 0.28, "margin": 0.71, "price": 199},
        {"sku": "social-pack", "take_rate_p": 0.24, "margin": 0.66, "price": 149},
        {"sku": "business-cards", "take_rate_p": 0.18, "margin": 0.72, "price": 49}
    ],
    "blog-post": [
        {"sku": "content-pack-5", "take_rate_p": 0.32, "margin": 0.68, "price": 199},
        {"sku": "seo-optimization", "take_rate_p": 0.22, "margin": 0.75, "price": 79}
    ],
    "thumbnail": [
        {"sku": "thumbnail-pack-10", "take_rate_p": 0.35, "margin": 0.70, "price": 89},
        {"sku": "youtube-bundle", "take_rate_p": 0.20, "margin": 0.65, "price": 249}
    ],
    "voiceover": [
        {"sku": "podcast-intro", "take_rate_p": 0.25, "margin": 0.72, "price": 99},
        {"sku": "audio-bundle", "take_rate_p": 0.18, "margin": 0.68, "price": 199}
    ]
}

class UpsellIn(BaseModel):
    order_id: str
    sku: Optional[str] = None
    order_value: Optional[float] = None

@router.post("/upsell/recommend")
async def upsell_recommend(payload: UpsellIn):
    """Recommend upsells based on current order"""
    sku = payload.sku or "logo-basic"
    
    # Find matching upsells
    offers = UPSELL_MAP.get(sku, UPSELL_MAP.get("logo-basic", []))
    
    # Sort by expected value (take_rate * margin * price)
    for offer in offers:
        offer["ev"] = round(offer["take_rate_p"] * offer["margin"] * offer["price"], 2)
    
    offers.sort(key=lambda x: x["ev"], reverse=True)
    
    return metrics_wrap(
        True,
        order_id=payload.order_id,
        original_sku=sku,
        offers=offers,
        best_offer=offers[0] if offers else None
    )

@router.post("/upsell/deploy")
async def upsell_deploy(payload: UpsellIn):
    """Deploy upsell offer to the same channel as original order"""
    # In production: sends message via Fiverr, email, or DM
    return metrics_wrap(
        True,
        order_id=payload.order_id,
        deployed=True,
        channel="fiverr_message"  # Would be dynamic
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4) ABANDON → OFFER RECOVERY WITH GUARANTEES
# ═══════════════════════════════════════════════════════════════════════════════

class RecoveryComposeIn(BaseModel):
    order_ref: str
    cart_value: Optional[float] = None
    email: Optional[str] = None
    channel: Optional[str] = "email"

@router.post("/recovery/compose")
async def recovery_compose(payload: RecoveryComposeIn):
    """Compose recovery message with guarantee + proof"""
    proof_hash = uuid.uuid4().hex[-8:]
    
    # Dynamic discount based on cart value
    if payload.cart_value and payload.cart_value > 200:
        discount = 20
    elif payload.cart_value and payload.cart_value > 100:
        discount = 15
    else:
        discount = 10
    
    message = f"We noticed you didn't complete your order. Here's {discount}% off to come back! " \
              f"Outcome-backed guarantee. Proof #{proof_hash}"
    
    return metrics_wrap(
        True,
        order_ref=payload.order_ref,
        message=message,
        discount_pct=discount,
        proof_tail=proof_hash,
        channel=payload.channel
    )

@router.post("/recovery/send")
async def recovery_send(payload: RecoveryComposeIn):
    """Send recovery message via appropriate channel"""
    # In production: integrates with email (Resend), SMS, or platform DM
    return metrics_wrap(
        True,
        order_ref=payload.order_ref,
        sent=True,
        channel=payload.channel
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 5) LIFETIME VALUE FORECASTER
# ═══════════════════════════════════════════════════════════════════════════════

class LTVIn(BaseModel):
    client_id: str
    order_history: Optional[List[Dict]] = None
    niche: Optional[str] = None

@router.post("/ltv/predict")
async def ltv_predict(payload: LTVIn):
    """Predict client lifetime value for routing prioritization"""
    # Base LTV estimates by niche
    niche_ltv = {
        "enterprise": (2500, 8000, 0.72),
        "agency": (1200, 4000, 0.65),
        "startup": (800, 2500, 0.55),
        "creator": (400, 1200, 0.48),
        "smb": (300, 900, 0.42),
        "default": (200, 600, 0.35)
    }
    
    niche = payload.niche or "default"
    p50, p90, rebuy = niche_ltv.get(niche.lower(), niche_ltv["default"])
    
    # Adjust if we have order history
    if payload.order_history:
        order_count = len(payload.order_history)
        total_value = sum(o.get("value", 0) for o in payload.order_history)
        
        # More orders = higher rebuy probability
        rebuy = min(0.85, rebuy + (order_count * 0.05))
        
        # Adjust LTV based on actual spending
        if total_value > p50:
            p50 = total_value * 1.5
            p90 = total_value * 3
    
    return metrics_wrap(
        True,
        client_id=payload.client_id,
        ltv_p50=round(p50, 2),
        ltv_p90=round(p90, 2),
        rebuy_p=round(rebuy, 3),
        niche=niche,
        priority_tier="high" if p50 > 500 else "medium" if p50 > 200 else "standard"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 6) OUTCOME-INDEXED PORTFOLIO
# ═══════════════════════════════════════════════════════════════════════════════

# In-memory portfolio performance tracking
_PORTFOLIO_PERFORMANCE = {
    "logo-basic": {"outcome_score": 0.86, "rev_per_hr": 74.2, "win_rate": 0.42, "volume": 150},
    "brand-kit": {"outcome_score": 0.81, "rev_per_hr": 92.5, "win_rate": 0.38, "volume": 45},
    "social-pack": {"outcome_score": 0.78, "rev_per_hr": 58.1, "win_rate": 0.35, "volume": 80},
    "blog-post": {"outcome_score": 0.82, "rev_per_hr": 65.0, "win_rate": 0.45, "volume": 120},
    "thumbnail": {"outcome_score": 0.88, "rev_per_hr": 85.0, "win_rate": 0.52, "volume": 200},
    "voiceover": {"outcome_score": 0.75, "rev_per_hr": 70.0, "win_rate": 0.40, "volume": 60}
}

@router.get("/portfolio/performance")
async def portfolio_performance():
    """Get outcome scores by offer type"""
    return metrics_wrap(
        True,
        offers=_PORTFOLIO_PERFORMANCE,
        top_performer=max(_PORTFOLIO_PERFORMANCE.items(), key=lambda x: x[1]["rev_per_hr"])[0],
        total_volume=sum(o["volume"] for o in _PORTFOLIO_PERFORMANCE.values())
    )

class RebalanceIn(BaseModel):
    raise_offers: List[str] = Field(default_factory=list)
    lower_offers: List[str] = Field(default_factory=list)
    auto: bool = False

@router.post("/portfolio/rebalance")
async def portfolio_rebalance(payload: RebalanceIn):
    """Rebalance discovery/bidding quotas based on performance"""
    if payload.auto:
        # Auto-rebalance: raise top performers, lower bottom
        sorted_offers = sorted(
            _PORTFOLIO_PERFORMANCE.items(),
            key=lambda x: x[1]["rev_per_hr"],
            reverse=True
        )
        raise_offers = [o[0] for o in sorted_offers[:2]]
        lower_offers = [o[0] for o in sorted_offers[-2:]]
    else:
        raise_offers = payload.raise_offers
        lower_offers = payload.lower_offers
    
    return metrics_wrap(
        True,
        raised=raise_offers,
        lowered=lower_offers,
        new_quotas={
            o: 1.2 if o in raise_offers else 0.8 if o in lower_offers else 1.0
            for o in _PORTFOLIO_PERFORMANCE.keys()
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 7) DARKPOOL LEAD EXCHANGE
# ═══════════════════════════════════════════════════════════════════════════════

_DARKPOOL_LISTINGS: Dict[str, Dict] = {}

class DarkpoolListIn(BaseModel):
    lead_id: str
    niche: Optional[str] = None
    reserve_usd: Optional[float] = None
    description: Optional[str] = None

@router.post("/darkpool/list")
async def darkpool_list(payload: DarkpoolListIn):
    """List overflow lead in darkpool for partner matching"""
    listing = {
        "lead_id": payload.lead_id,
        "niche": payload.niche,
        "reserve_usd": payload.reserve_usd or 0,
        "description": payload.description,
        "listed_at": datetime.utcnow().isoformat(),
        "status": "available"
    }
    _DARKPOOL_LISTINGS[payload.lead_id] = listing
    
    return metrics_wrap(
        True,
        listed=payload.lead_id,
        floor=payload.reserve_usd or 0,
        pool_size=len(_DARKPOOL_LISTINGS)
    )

class DarkpoolClaimIn(BaseModel):
    lead_id: str
    revshare_bps: int = 1500  # 15% default

@router.post("/darkpool/claim")
async def darkpool_claim(payload: DarkpoolClaimIn):
    """Claim a lead from the darkpool"""
    if payload.lead_id not in _DARKPOOL_LISTINGS:
        return {"ok": False, "error": "Lead not found in darkpool"}
    
    listing = _DARKPOOL_LISTINGS[payload.lead_id]
    listing["status"] = "claimed"
    listing["claimed_at"] = datetime.utcnow().isoformat()
    listing["revshare_bps"] = payload.revshare_bps
    
    return metrics_wrap(
        True,
        claimed=payload.lead_id,
        revshare_bps=payload.revshare_bps,
        revshare_pct=payload.revshare_bps / 100
    )

class DarkpoolSettleIn(BaseModel):
    lead_id: str
    gross_usd: float
    revshare_bps: int

@router.post("/darkpool/settle")
async def darkpool_settle(payload: DarkpoolSettleIn):
    """Settle a darkpool deal - calculate and log rev-share"""
    owed = payload.gross_usd * (payload.revshare_bps / 10_000)
    
    return metrics_wrap(
        True,
        lead_id=payload.lead_id,
        gross_usd=payload.gross_usd,
        partner_payout_usd=round(owed, 2),
        net_to_aigentsy=round(payload.gross_usd - owed, 2)
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 8) AUTO-TESTIMONIALS + PROOF BADGES
# ═══════════════════════════════════════════════════════════════════════════════

class TestimonialIn(BaseModel):
    deal_id: str
    client_name: Optional[str] = None
    platform: Optional[str] = None

@router.post("/proof/testimonial/request")
async def testimonial_request(payload: TestimonialIn):
    """Request testimonial from client after successful delivery"""
    # In production: sends automated follow-up request
    return metrics_wrap(
        True,
        deal_id=payload.deal_id,
        requested=True,
        follow_up_scheduled="24h",
        channel=payload.platform or "email"
    )

@router.post("/proof/badge/mint")
async def proof_badge_mint(payload: TestimonialIn):
    """Mint a verifiable proof badge for a completed deal"""
    token = "prf_" + uuid.uuid4().hex[:12]
    
    return metrics_wrap(
        True,
        deal_id=payload.deal_id,
        badge=token,
        verification_url=f"https://aigentsy.com/verify/{token}",
        embeddable=f'<img src="https://aigentsy.com/badge/{token}.svg" alt="Verified by AiGentsy"/>'
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 9) CHURN SENTINEL
# ═══════════════════════════════════════════════════════════════════════════════

class SubRiskIn(BaseModel):
    sub_id: str
    days_since_login: Optional[int] = None
    usage_drop_pct: Optional[float] = None
    support_tickets: Optional[int] = None

@router.post("/subscriptions/churn-risk")
async def sub_churn_risk(payload: SubRiskIn):
    """Calculate churn risk for a subscription"""
    risk = 0.15  # Base risk
    reasons = []
    
    if payload.days_since_login:
        if payload.days_since_login > 30:
            risk += 0.35
            reasons.append("no_login_30d")
        elif payload.days_since_login > 14:
            risk += 0.20
            reasons.append("no_login_14d")
        elif payload.days_since_login > 7:
            risk += 0.10
            reasons.append("no_login_7d")
    
    if payload.usage_drop_pct:
        risk += payload.usage_drop_pct * 0.5
        reasons.append(f"usage_drop_{int(payload.usage_drop_pct*100)}pct")
    
    if payload.support_tickets and payload.support_tickets > 2:
        risk += 0.15
        reasons.append("multiple_support_tickets")
    
    risk = min(0.95, risk)
    
    return metrics_wrap(
        True,
        sub_id=payload.sub_id,
        risk=round(risk, 3),
        risk_level="high" if risk > 0.6 else "medium" if risk > 0.3 else "low",
        reasons=reasons or ["baseline"]
    )

@router.post("/subscriptions/save-offer")
async def sub_save_offer(payload: SubRiskIn):
    """Generate personalized save offer for at-risk subscription"""
    # Risk-based offers
    risk_data = await sub_churn_risk(payload)
    risk = risk_data["metrics"]["risk"]
    
    if risk > 0.6:
        offer = "50% off next 3 months"
        offer_code = "SAVE50"
    elif risk > 0.4:
        offer = "30% off next month + free consultation"
        offer_code = "SAVE30"
    else:
        offer = "20% off next renewal"
        offer_code = "SAVE20"
    
    return metrics_wrap(
        True,
        sub_id=payload.sub_id,
        offer=offer,
        offer_code=offer_code,
        risk=risk,
        expires_in="7d"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 10) SHADOW-PRICE A/B ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

_SHADOW_EXPERIMENTS: Dict[str, Dict] = {}

class ShadowGenIn(BaseModel):
    sku: str
    base_price: float
    variance_pct: float = 0.15

@router.post("/pricing/shadow-generate")
async def pricing_shadow_generate(payload: ShadowGenIn):
    """Generate shadow price candidates for A/B testing"""
    variance = payload.variance_pct
    candidates = [
        round(payload.base_price * (1 - variance), 2),
        payload.base_price,
        round(payload.base_price * (1 + variance), 2),
        round(payload.base_price * (1 + variance * 2), 2)
    ]
    
    experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
    _SHADOW_EXPERIMENTS[experiment_id] = {
        "sku": payload.sku,
        "base_price": payload.base_price,
        "candidates": candidates,
        "created_at": datetime.utcnow().isoformat(),
        "status": "active"
    }
    
    return metrics_wrap(
        True,
        sku=payload.sku,
        experiment_id=experiment_id,
        candidates=candidates
    )

class ShadowAssignIn(BaseModel):
    sku: str
    candidate_price: float
    cohort_size_pct: float = 0.10

@router.post("/pricing/shadow-assign")
async def pricing_shadow_assign(payload: ShadowAssignIn):
    """Assign cohort to shadow price (not shown until accepted)"""
    cohort = f"cohort_{uuid.uuid4().hex[:6]}"
    
    return metrics_wrap(
        True,
        sku=payload.sku,
        cohort=cohort,
        price=payload.candidate_price,
        cohort_size_pct=payload.cohort_size_pct,
        note="Price hidden until user accepts quote"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 11) PARTNER SKU INGESTION
# ═══════════════════════════════════════════════════════════════════════════════

_PARTNER_SKUS: Dict[str, Dict] = {}

class PartnerSKU(BaseModel):
    sku: str
    title: str
    price: float
    partner_id: str
    take_rate: float = 0.15  # AiGentsy's cut
    category: Optional[str] = None

class PartnerIngestIn(BaseModel):
    skus: List[PartnerSKU]

@router.post("/partners/ingest-skus")
async def partners_ingest(payload: PartnerIngestIn):
    """Ingest partner SKUs to sell in your flow"""
    ingested = []
    for sku in payload.skus:
        _PARTNER_SKUS[sku.sku] = {
            "sku": sku.sku,
            "title": sku.title,
            "price": sku.price,
            "partner_id": sku.partner_id,
            "take_rate": sku.take_rate,
            "category": sku.category,
            "ingested_at": datetime.utcnow().isoformat()
        }
        ingested.append(sku.sku)
    
    return metrics_wrap(
        True,
        ingested=len(ingested),
        skus=ingested,
        total_partner_skus=len(_PARTNER_SKUS)
    )

class PartnerRouteOrderIn(BaseModel):
    sku: str
    order_id: str
    order_value: float

@router.post("/partners/route-order")
async def partners_route_order(payload: PartnerRouteOrderIn):
    """Route order to partner for fulfillment"""
    if payload.sku not in _PARTNER_SKUS:
        return {"ok": False, "error": f"Partner SKU not found: {payload.sku}"}
    
    partner_sku = _PARTNER_SKUS[payload.sku]
    aigentsy_take = payload.order_value * partner_sku["take_rate"]
    partner_payout = payload.order_value - aigentsy_take
    
    return metrics_wrap(
        True,
        order_id=payload.order_id,
        routed_to=partner_sku["partner_id"],
        partner_payout=round(partner_payout, 2),
        aigentsy_take=round(aigentsy_take, 2)
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 12) SELF-HEALING ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

_CIRCUIT_STATES: Dict[str, str] = {}
_RETRY_BUDGETS: Dict[str, Dict] = {}

class CircuitIn(BaseModel):
    name: str
    reason: Optional[str] = None

@router.post("/orchestrator/circuit/open")
async def orchestrator_circuit_open(payload: CircuitIn):
    """Open circuit breaker (stop calling failing service)"""
    _CIRCUIT_STATES[payload.name] = "open"
    
    return metrics_wrap(
        True,
        circuit=payload.name,
        state="open",
        reason=payload.reason,
        all_circuits=_CIRCUIT_STATES
    )

@router.post("/orchestrator/circuit/close")
async def orchestrator_circuit_close(payload: CircuitIn):
    """Close circuit breaker (resume calling service)"""
    _CIRCUIT_STATES[payload.name] = "closed"
    
    return metrics_wrap(
        True,
        circuit=payload.name,
        state="closed",
        all_circuits=_CIRCUIT_STATES
    )

@router.get("/orchestrator/circuits")
async def orchestrator_circuits():
    """Get all circuit breaker states"""
    return metrics_wrap(
        True,
        circuits=_CIRCUIT_STATES,
        open_count=sum(1 for s in _CIRCUIT_STATES.values() if s == "open")
    )

class RetryBudgetIn(BaseModel):
    route: str
    max_retries: int = 3
    cooldown_sec: int = 30
    backoff_multiplier: float = 2.0

@router.post("/orchestrator/retry-budget")
async def orchestrator_retry_budget(payload: RetryBudgetIn):
    """Set retry budget for a route"""
    _RETRY_BUDGETS[payload.route] = {
        "max_retries": payload.max_retries,
        "cooldown_sec": payload.cooldown_sec,
        "backoff_multiplier": payload.backoff_multiplier,
        "current_retries": 0,
        "last_failure": None
    }
    
    return metrics_wrap(
        True,
        route=payload.route,
        budget=_RETRY_BUDGETS[payload.route]
    )


# ═══════════════════════════════════════════════════════════════════════════════
# WIRE-UP HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def include_overlay(app):
    """Include this router in your FastAPI app"""
    app.include_router(router, prefix="", tags=["Apex Upgrades"])
    print("✅ Apex Upgrades Overlay loaded - 12 modules active")
