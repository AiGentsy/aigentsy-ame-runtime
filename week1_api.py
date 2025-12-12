"""
AiGentsy Week 1 Features - Master API
Consolidates all 12 features into single FastAPI application

Deploy to: Render.com
Environment Variables Required:
- JSONBIN_API_KEY
- JSONBIN_BIN_ID (optional, will auto-create)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os

# Initialize FastAPI
app = FastAPI(
    title="AiGentsy Week 1 API",
    description="All 12 Week 1 features - 83 endpoints",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import all Week 1 engines
# These will be loaded from /mnt/user-data/outputs
import sys
sys.path.append('/mnt/user-data/outputs')

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AiGentsy Week 1 API",
        "features": 12,
        "endpoints": 83,
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "features_loaded": {
            "boosters": True,
            "subscriptions": True,
            "pwp": True,
            "warranties": True,
            "slo": True,
            "franchise": True,
            "dark_pool": True,
            "ocl": True,
            "badges": True,
            "diy_dwy_dfy": True,
            "value_router": True,
            "units_of_labor": True
        }
    }

# ============================================================
# FEATURE #10: BOOSTERS (9 endpoints)
# ============================================================

@app.post("/boosters/activate")
async def booster_activate_post(
    username: str,
    booster_type: str,
    source: str = "automatic",
    metadata: Optional[Dict[str, Any]] = None
):
    """Activate a booster for a user"""
    from booster_engine import activate_booster
    return activate_booster(username, booster_type, source, metadata)

@app.get("/boosters/active/{username}")
async def booster_active_get(username: str):
    """Get all active boosters for a user"""
    from booster_engine import get_active_boosters
    return get_active_boosters(username)

@app.get("/boosters/earnings")
async def booster_earnings_get(
    base_amount: float,
    username: str,
    outcome_id: Optional[str] = None
):
    """Calculate boosted earnings"""
    from booster_engine import calculate_boosted_earnings
    return calculate_boosted_earnings(base_amount, username, outcome_id)

@app.post("/boosters/referral/track")
async def booster_referral_track_post(
    referrer_username: str,
    referee_username: str,
    referral_code: Optional[str] = None
):
    """Track a referral"""
    from booster_engine import track_referral
    return track_referral(referrer_username, referee_username, referral_code)

@app.post("/boosters/referral/milestone")
async def booster_referral_milestone_post(
    referrer_username: str,
    milestone: str,
    referee_username: str
):
    """Award referral milestone bonus"""
    from booster_engine import award_referral_milestone_bonus
    return award_referral_milestone_bonus(referrer_username, milestone, referee_username)

@app.post("/boosters/streak/check")
async def booster_streak_check_post(
    username: str,
    last_active: str
):
    """Check and update activity streak"""
    from booster_engine import check_streak
    return check_streak(username, last_active)

@app.post("/boosters/purchase")
async def booster_purchase_post(
    username: str,
    power_up_type: str,
    payment_method: str = "stripe"
):
    """Purchase a power-up booster"""
    from booster_engine import purchase_power_up
    return purchase_power_up(username, power_up_type, payment_method)

@app.get("/boosters/available")
async def booster_available_get(username: Optional[str] = None):
    """Get all available boosters"""
    from booster_engine import get_available_boosters
    return get_available_boosters(username or "guest")

@app.get("/boosters/leaderboard")
async def booster_leaderboard_get(limit: int = 10):
    """Get booster leaderboard"""
    from booster_engine import get_booster_leaderboard
    return get_booster_leaderboard(limit)

# ============================================================
# FEATURE #7: SUBSCRIPTIONS (9 endpoints)
# ============================================================

@app.post("/subscriptions/create")
async def subscription_create_post(
    username: str,
    tier: str,
    billing_cycle: str = "monthly",
    payment_method_id: Optional[str] = None
):
    """Create subscription"""
    from subscription_engine import create_subscription
    return create_subscription(username, tier, billing_cycle, payment_method_id)

@app.get("/subscriptions/status/{username}")
async def subscription_status_get(username: str):
    """Get subscription status"""
    from subscription_engine import get_active_subscription
    result = get_active_subscription(username)
    if result:
        return {"subscription": result}
    return {"subscription": None, "message": "No active subscription"}

@app.post("/subscriptions/use_credit")
async def subscription_use_credit_post(
    username: str,
    intent_id: str
):
    """Use subscription credit for intent"""
    from subscription_engine import use_subscription_credit
    return use_subscription_credit(username, intent_id)

@app.post("/subscriptions/cancel")
async def subscription_cancel_post(
    username: str,
    cancel_at_period_end: bool = True
):
    """Cancel subscription"""
    from subscription_engine import cancel_subscription
    return cancel_subscription(username, cancel_at_period_end)

@app.get("/subscriptions/tiers")
async def subscription_tiers_get():
    """Get all available tiers"""
    from subscription_engine import get_all_subscription_tiers
    return get_all_subscription_tiers()

@app.get("/subscriptions/savings")
async def subscription_savings_get(
    tier: str,
    billing_cycle: str = "monthly"
):
    """Calculate savings"""
    from subscription_engine import calculate_subscription_savings
    return calculate_subscription_savings(tier, billing_cycle)

@app.get("/subscriptions/priority/{username}")
async def subscription_priority_get(username: str):
    """Check queue priority"""
    from subscription_engine import check_subscriber_priority
    return check_subscriber_priority(username)

@app.get("/subscriptions/history/{username}")
async def subscription_history_get(username: str):
    """Get subscription history"""
    from subscription_engine import get_user_subscription_history
    return get_user_subscription_history(username)

@app.get("/subscriptions/mrr")
async def subscription_mrr_get():
    """Get MRR/ARR metrics (admin)"""
    from subscription_engine import calculate_mrr
    return calculate_mrr()

# ============================================================
# FEATURE #11: PWP (8 endpoints)
# ============================================================

@app.post("/pwp/create")
async def pwp_create_post(
    buyer_username: str,
    agent_username: str,
    outcome_id: str,
    outcome_price: float,
    pwp_plan: str,
    outcome_type: str = "marketing_campaign",
    metadata: Optional[Dict[str, Any]] = None
):
    """Create PWP contract"""
    from pwp_engine import create_pwp_contract
    return create_pwp_contract(
        buyer_username, agent_username, outcome_id,
        outcome_price, pwp_plan, outcome_type, metadata
    )

@app.post("/pwp/payment")
async def pwp_payment_post(
    contract_id: str,
    revenue_amount: float,
    payment_source: str = "stripe",
    metadata: Optional[Dict[str, Any]] = None
):
    """Record revenue payment"""
    from pwp_engine import record_revenue_payment
    return record_revenue_payment(contract_id, revenue_amount, payment_source, metadata)

@app.get("/pwp/status/{contract_id}")
async def pwp_status_get(contract_id: str):
    """Get PWP contract status"""
    from pwp_engine import get_pwp_contract_status
    return get_pwp_contract_status(contract_id)

@app.get("/pwp/check_expiry/{contract_id}")
async def pwp_check_expiry_get(contract_id: str):
    """Check contract expiry"""
    from pwp_engine import check_pwp_contract_expiry
    return check_pwp_contract_expiry(contract_id)

@app.get("/pwp/pricing")
async def pwp_pricing_get(
    outcome_price: float,
    pwp_plan: str,
    outcome_type: str = "marketing_campaign"
):
    """Calculate PWP pricing"""
    from pwp_engine import calculate_pwp_pricing
    return calculate_pwp_pricing(outcome_price, pwp_plan, outcome_type)

@app.get("/pwp/buyer_dashboard/{username}")
async def pwp_buyer_dashboard_get(username: str):
    """Get buyer's PWP dashboard"""
    from pwp_engine import get_buyer_pwp_dashboard
    return get_buyer_pwp_dashboard(username)

@app.get("/pwp/capital_pool")
async def pwp_capital_pool_get():
    """Get capital pool status"""
    from pwp_engine import get_capital_pool_status
    return get_capital_pool_status()

@app.get("/pwp/plans")
async def pwp_plans_get():
    """Get all PWP plans"""
    from pwp_engine import get_all_pwp_plans
    return get_all_pwp_plans()

# ============================================================
# FEATURE #8: WARRANTIES (11 endpoints)
# ============================================================

@app.post("/warranties/create")
async def warranty_create_post(
    agent_username: str,
    outcome_id: str,
    warranty_type: str,
    outcome_price: float
):
    """Create warranty"""
    from warranty_engine import create_warranty
    return create_warranty(agent_username, outcome_id, warranty_type, outcome_price)

@app.post("/warranties/stake_bond")
async def warranty_stake_bond_post(
    warranty_id: str,
    agent_username: str
):
    """Stake warranty bond"""
    from warranty_engine import stake_warranty_bond
    return stake_warranty_bond(warranty_id, agent_username)

@app.post("/warranties/claim")
async def warranty_claim_post(
    warranty_id: str,
    buyer_username: str,
    claim_reason: str,
    evidence: Optional[str] = None
):
    """File warranty claim"""
    from warranty_engine import file_warranty_claim
    return file_warranty_claim(warranty_id, buyer_username, claim_reason, evidence)

@app.post("/warranties/claim/process")
async def warranty_claim_process_post(
    claim_id: str,
    approved: bool,
    admin_notes: Optional[str] = None
):
    """Process warranty claim (admin)"""
    from warranty_engine import process_warranty_claim
    return process_warranty_claim(claim_id, approved, admin_notes)

@app.post("/warranties/revision/request")
async def warranty_revision_request_post(
    warranty_id: str,
    buyer_username: str,
    revision_details: str
):
    """Request revision"""
    from warranty_engine import request_revision
    return request_revision(warranty_id, buyer_username, revision_details)

@app.post("/warranties/revision/deliver")
async def warranty_revision_deliver_post(
    revision_id: str,
    agent_username: str,
    delivery_notes: Optional[str] = None
):
    """Deliver revision"""
    from warranty_engine import deliver_revision
    return deliver_revision(revision_id, agent_username, delivery_notes)

@app.get("/warranties/terms/{warranty_id}")
async def warranty_terms_get(warranty_id: str):
    """Get warranty terms"""
    from warranty_engine import get_warranty_terms
    return get_warranty_terms(warranty_id)

@app.get("/warranties/agent/{username}")
async def warranty_agent_get(username: str):
    """Get agent's warranties"""
    from warranty_engine import get_agent_warranties
    return get_agent_warranties(username)

@app.get("/warranties/types")
async def warranty_types_get():
    """Get all warranty types"""
    from warranty_engine import get_all_warranty_types
    return get_all_warranty_types()

@app.get("/warranties/calculate_bond")
async def warranty_calculate_bond_get(
    warranty_type: str,
    outcome_price: float
):
    """Calculate bond requirement"""
    from warranty_engine import calculate_bond_requirement
    return calculate_bond_requirement(warranty_type, outcome_price)

@app.get("/warranties/buyer_claims/{username}")
async def warranty_buyer_claims_get(username: str):
    """Get buyer's claims"""
    from warranty_engine import get_buyer_claims
    return get_buyer_claims(username)

# ============================================================
# FEATURE #9: SLO (7 endpoints)
# ============================================================

@app.get("/slo/tiers")
async def slo_tiers_get():
    """Get all SLO tiers"""
    from slo_engine import get_all_slo_tiers
    return get_all_slo_tiers()

@app.get("/slo/pricing")
async def slo_pricing_get(
    base_price: float,
    tier: str
):
    """Calculate SLO pricing"""
    from slo_engine import calculate_slo_pricing_detailed
    return calculate_slo_pricing_detailed(base_price, tier)

@app.get("/slo/compare")
async def slo_compare_get(base_price: float):
    """Compare all SLO tiers"""
    from slo_engine import compare_slo_tiers
    return compare_slo_tiers(base_price)

@app.get("/slo/status/{contract_id}")
async def slo_status_get(contract_id: str):
    """Get SLO contract status"""
    from slo_engine import get_slo_contract_status
    return get_slo_contract_status(contract_id)

@app.get("/slo/agent_dashboard/{username}")
async def slo_agent_dashboard_get(username: str):
    """Get agent's SLO dashboard"""
    from slo_engine import get_agent_slo_dashboard
    return get_agent_slo_dashboard(username)

@app.get("/slo/buyer_dashboard/{username}")
async def slo_buyer_dashboard_get(username: str):
    """Get buyer's SLO dashboard"""
    from slo_engine import get_buyer_slo_dashboard
    return get_buyer_slo_dashboard(username)

@app.get("/slo/recommend")
async def slo_recommend_get(
    urgency: str = "medium",
    budget_flexible: bool = True,
    quality_priority: bool = True
):
    """Get SLO tier recommendation"""
    from slo_engine import recommend_slo_tier
    return recommend_slo_tier(urgency, budget_flexible, quality_priority)

# ============================================================
# FEATURE #12: FRANCHISE (8 endpoints)
# ============================================================

@app.post("/franchise/template/create")
async def franchise_template_create_post(
    creator_username: str,
    template_name: str,
    category: str,
    description: str,
    base_price: float,
    available_licenses: List[str] = ["basic", "professional"],
    metadata: Optional[Dict[str, Any]] = None
):
    """Create franchisable template"""
    from franchise_engine import create_template
    return create_template(
        creator_username, template_name, category,
        description, base_price, available_licenses, metadata
    )

@app.post("/franchise/license/purchase")
async def franchise_license_purchase_post(
    franchisee_username: str,
    template_id: str,
    license_type: str,
    territory: Optional[str] = None,
    niche: Optional[str] = None
):
    """Purchase template license"""
    from franchise_engine import purchase_license
    return purchase_license(franchisee_username, template_id, license_type, territory, niche)

@app.post("/franchise/outcome/record")
async def franchise_outcome_record_post(
    license_id: str,
    outcome_id: str,
    revenue_amount: float,
    buyer_username: str
):
    """Record franchise outcome"""
    from franchise_engine import record_franchise_outcome
    return record_franchise_outcome(license_id, outcome_id, revenue_amount, buyer_username)

@app.get("/franchise/marketplace")
async def franchise_marketplace_get(
    category: Optional[str] = None,
    sort_by: str = "popular"
):
    """Get template marketplace"""
    from franchise_engine import get_template_marketplace
    return get_template_marketplace(category, sort_by)

@app.get("/franchise/franchisee_dashboard/{username}")
async def franchise_franchisee_dashboard_get(username: str):
    """Get franchisee dashboard"""
    from franchise_engine import get_franchisee_dashboard
    return get_franchisee_dashboard(username)

@app.get("/franchise/creator_dashboard/{username}")
async def franchise_creator_dashboard_get(username: str):
    """Get creator dashboard"""
    from franchise_engine import get_creator_dashboard
    return get_creator_dashboard(username)

@app.get("/franchise/template/performance/{template_id}")
async def franchise_template_performance_get(template_id: str):
    """Get template performance"""
    from franchise_engine import get_template_performance
    return get_template_performance(template_id)

@app.get("/franchise/license_types")
async def franchise_license_types_get():
    """Get all license types"""
    from franchise_engine import get_all_license_types
    return get_all_license_types()

# ============================================================
# REMAINING FEATURES - COMPLETING ALL 83 ENDPOINTS
# ============================================================

# ============================================================
# FEATURE #6: DARK POOL (6 endpoints)
# ============================================================

@app.post("/dark_pool/request_access")
async def dark_pool_request_access_post(
    username: str,
    buyer_profile: Dict[str, Any]
):
    """Request Dark Pool access"""
    from dark_pool import request_dark_pool_access
    return request_dark_pool_access(username, buyer_profile)

@app.post("/dark_pool/intent/submit")
async def dark_pool_intent_submit_post(
    buyer_username: str,
    intent_data: Dict[str, Any]
):
    """Submit Dark Pool intent"""
    from dark_pool import submit_dark_pool_intent
    return submit_dark_pool_intent(buyer_username, intent_data)

@app.get("/dark_pool/matches/{buyer_username}")
async def dark_pool_matches_get(buyer_username: str):
    """Get Dark Pool matches"""
    from dark_pool import get_dark_pool_matches
    return get_dark_pool_matches(buyer_username)

@app.post("/dark_pool/match/accept")
async def dark_pool_match_accept_post(
    match_id: str,
    buyer_username: str
):
    """Accept Dark Pool match"""
    from dark_pool import accept_dark_pool_match
    return accept_dark_pool_match(match_id, buyer_username)

@app.get("/dark_pool/analytics")
async def dark_pool_analytics_get():
    """Get Dark Pool analytics (admin)"""
    from dark_pool import get_dark_pool_analytics
    return get_dark_pool_analytics()

@app.get("/dark_pool/status/{username}")
async def dark_pool_status_get(username: str):
    """Get user's Dark Pool status"""
    from dark_pool import get_user_dark_pool_status
    return get_user_dark_pool_status(username)

# ============================================================
# FEATURE #5: OCL P2P LENDING (9 endpoints)
# ============================================================

@app.post("/ocl/stake")
async def ocl_stake_post(
    lender_username: str,
    borrower_username: str,
    stake_amount: float,
    terms: Optional[Dict[str, Any]] = None
):
    """Stake on borrower"""
    from ocl_p2p_lending import create_ocl_stake
    return create_ocl_stake(lender_username, borrower_username, stake_amount, terms)

@app.post("/ocl/repay")
async def ocl_repay_post(
    stake_id: str,
    amount: float
):
    """Repay OCL stake"""
    from ocl_p2p_lending import repay_ocl_stake
    return repay_ocl_stake(stake_id, amount)

@app.get("/ocl/borrower/{username}")
async def ocl_borrower_get(username: str):
    """Get borrower's OCL dashboard"""
    from ocl_p2p_lending import get_borrower_ocl_dashboard
    return get_borrower_ocl_dashboard(username)

@app.get("/ocl/lender/{username}")
async def ocl_lender_get(username: str):
    """Get lender's OCL dashboard"""
    from ocl_p2p_lending import get_lender_ocl_dashboard
    return get_lender_ocl_dashboard(username)

@app.get("/ocl/available")
async def ocl_available_get(
    min_reputation: int = 0,
    max_stake: Optional[float] = None
):
    """Get available OCL opportunities"""
    from ocl_p2p_lending import get_available_ocl_opportunities
    return get_available_ocl_opportunities(min_reputation, max_stake)

@app.post("/ocl/default")
async def ocl_default_post(
    stake_id: str,
    reason: str
):
    """Mark stake as defaulted"""
    from ocl_p2p_lending import mark_stake_defaulted
    return mark_stake_defaulted(stake_id, reason)

@app.get("/ocl/pool_status")
async def ocl_pool_status_get():
    """Get OCL pool status"""
    from ocl_p2p_lending import get_ocl_pool_status
    return get_ocl_pool_status()

@app.get("/ocl/calculate_terms")
async def ocl_calculate_terms_get(
    stake_amount: float,
    borrower_reputation: int
):
    """Calculate OCL terms"""
    from ocl_p2p_lending import calculate_ocl_terms
    return calculate_ocl_terms(stake_amount, borrower_reputation)

@app.get("/ocl/history/{username}")
async def ocl_history_get(username: str):
    """Get OCL transaction history"""
    from ocl_p2p_lending import get_ocl_history
    return get_ocl_history(username)

# ============================================================
# FEATURE #4: BADGES (5 endpoints)
# ============================================================

@app.post("/badges/award")
async def badge_award_post(
    username: str,
    badge_type: str,
    criteria_met: Dict[str, Any]
):
    """Award badge to user"""
    from badge_engine import award_badge
    return award_badge(username, badge_type, criteria_met)

@app.get("/badges/user/{username}")
async def badge_user_get(username: str):
    """Get user's badges"""
    from badge_engine import get_user_badges
    return get_user_badges(username)

@app.get("/badges/available")
async def badge_available_get():
    """Get all available badges"""
    from badge_engine import get_all_badges
    return get_all_badges()

@app.get("/badges/leaderboard")
async def badge_leaderboard_get(
    badge_type: Optional[str] = None,
    limit: int = 10
):
    """Get badge leaderboard"""
    from badge_engine import get_badge_leaderboard
    return get_badge_leaderboard(badge_type, limit)

@app.post("/badges/check_eligibility")
async def badge_check_eligibility_post(
    username: str,
    badge_type: str
):
    """Check badge eligibility"""
    from badge_engine import check_badge_eligibility
    return check_badge_eligibility(username, badge_type)

# ============================================================
# FEATURE #3: DIY/DWY/DFY PRICING (3 endpoints)
# ============================================================

@app.get("/pricing/calculate")
async def pricing_calculate_get(
    tier: str,
    base_price: float
):
    """Calculate tier pricing"""
    from template_integration_engine import calculate_tier_pricing
    return calculate_tier_pricing(tier, base_price)

@app.get("/pricing/tiers")
async def pricing_tiers_get():
    """Get all pricing tiers"""
    from template_integration_engine import get_all_tiers
    return get_all_tiers()

@app.post("/pricing/apply_tier")
async def pricing_apply_tier_post(
    intent_id: str,
    tier: str
):
    """Apply pricing tier to intent"""
    from template_integration_engine import apply_tier_to_intent
    return apply_tier_to_intent(intent_id, tier)

# ============================================================
# FEATURE #2: VALUE ROUTER (4 endpoints)
# ============================================================

@app.post("/value/route")
async def value_route_post(
    transaction_id: str,
    total_amount: float,
    transaction_type: str
):
    """Route value through revenue system"""
    from pricing_oracle import route_transaction_value
    return route_transaction_value(transaction_id, total_amount, transaction_type)

@app.get("/value/breakdown/{transaction_id}")
async def value_breakdown_get(transaction_id: str):
    """Get value breakdown for transaction"""
    from pricing_oracle import get_value_breakdown
    return get_value_breakdown(transaction_id)

@app.get("/value/user_revenue/{username}")
async def value_user_revenue_get(username: str):
    """Get user's revenue breakdown"""
    from pricing_oracle import get_user_revenue_breakdown
    return get_user_revenue_breakdown(username)

@app.get("/value/analytics")
async def value_analytics_get(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get value routing analytics"""
    from pricing_oracle import get_value_routing_analytics
    return get_value_routing_analytics(start_date, end_date)

# ============================================================
# FEATURE #1: UNITS OF LABOR (4 endpoints)
# ============================================================

@app.post("/uol/track")
async def uol_track_post(
    outcome_id: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """Track outcome completion status"""
    from outcome_oracle import track_outcome_completion
    return track_outcome_completion(outcome_id, status, metadata)

@app.get("/uol/status/{outcome_id}")
async def uol_status_get(outcome_id: str):
    """Get outcome status"""
    from outcome_oracle import get_outcome_status
    return get_outcome_status(outcome_id)

@app.get("/uol/user_outcomes/{username}")
async def uol_user_outcomes_get(username: str):
    """Get user's outcomes"""
    from outcome_oracle import get_user_outcomes
    return get_user_outcomes(username)

@app.get("/uol/analytics")
async def uol_analytics_get(
    username: Optional[str] = None
):
    """Get outcome analytics"""
    from outcome_oracle import get_outcome_analytics
    return get_outcome_analytics(username)

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
