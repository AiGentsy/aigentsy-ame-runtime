"""
APEX UPGRADES API ENDPOINTS
============================

FastAPI endpoints for the 4 new upgrade systems:
1. Deliverable Verification Engine
2. Intelligent Pricing Autopilot
3. Client Success Predictor
4. Revenue Reconciliation Engine

Add to main.py:
    from apex_upgrades_api import create_apex_upgrade_routes
    create_apex_upgrade_routes(app)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

# Import upgrade engines
from deliverable_verification_engine import (
    verify_before_buyer_sees,
    get_verification_engine,
    DeliverableType
)

from intelligent_pricing_autopilot import (
    get_smart_bid_price,
    get_pricing_autopilot,
    record_bid_result
)

from client_success_predictor import (
    predict_user_success,
    get_users_needing_intervention,
    get_success_predictor
)

from revenue_reconciliation_engine import (
    record_platform_revenue,
    record_platform_payout,
    get_revenue_report,
    get_reconciliation_engine
)


router = APIRouter(prefix="/apex/upgrades", tags=["Apex Upgrades"])


# ============================================================
# PYDANTIC MODELS
# ============================================================

class VerifyDeliverableRequest(BaseModel):
    intent: Dict[str, Any]
    deliverable: Dict[str, Any]
    real_world_proofs: Optional[List[Dict]] = None


class PriceRecommendationRequest(BaseModel):
    opportunity_id: str
    category: str
    estimated_hours: float
    platform: str
    buyer_budget: Optional[float] = None
    competitor_count: int = 0
    agent_reputation: float = 0.5
    urgency: str = "normal"


class BidOutcomeRequest(BaseModel):
    bid_id: str
    won: bool
    winning_price: Optional[float] = None


class PredictSuccessRequest(BaseModel):
    user_data: Dict[str, Any]


class RecordRevenueRequest(BaseModel):
    user_id: str
    platform: str
    amount: float
    reference_id: str
    description: str = "Platform revenue"


class RecordPayoutRequest(BaseModel):
    user_id: str
    platform: str
    amount: float
    reference_id: str
    description: str = "Platform payout"


# ============================================================
# DELIVERABLE VERIFICATION ENDPOINTS
# ============================================================

@router.post("/verify/deliverable")
async def api_verify_deliverable(request: VerifyDeliverableRequest):
    """
    Verify a deliverable before buyer sees it.
    
    Returns verification score, pass/fail decision, and improvement suggestions.
    """
    try:
        result = await verify_before_buyer_sees(
            intent_data=request.intent,
            deliverable_data=request.deliverable,
            real_world_proofs=request.real_world_proofs
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/stats")
async def api_verification_stats():
    """Get verification statistics."""
    engine = get_verification_engine()
    return {"ok": True, "stats": engine.get_verification_stats()}


# ============================================================
# PRICING AUTOPILOT ENDPOINTS
# ============================================================

@router.post("/pricing/recommend")
async def api_recommend_price(request: PriceRecommendationRequest):
    """
    Get intelligent price recommendation for a bid.
    
    Considers market data, competition, demand, and learned patterns.
    """
    try:
        result = await get_smart_bid_price(
            opportunity_id=request.opportunity_id,
            category=request.category,
            estimated_hours=request.estimated_hours,
            platform=request.platform,
            buyer_budget=request.buyer_budget,
            competitor_count=request.competitor_count,
            agent_reputation=request.agent_reputation,
            urgency=request.urgency
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pricing/bid-outcome")
async def api_record_bid_outcome(request: BidOutcomeRequest):
    """
    Record bid outcome for learning.
    
    Improves future price recommendations based on win/loss data.
    """
    try:
        result = record_bid_result(
            bid_id=request.bid_id,
            won=request.won,
            winning_price=request.winning_price
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pricing/stats")
async def api_pricing_stats():
    """Get pricing autopilot statistics."""
    autopilot = get_pricing_autopilot()
    return {"ok": True, "stats": autopilot.get_pricing_stats()}


# ============================================================
# CLIENT SUCCESS PREDICTION ENDPOINTS
# ============================================================

@router.post("/success/predict")
async def api_predict_success(request: PredictSuccessRequest):
    """
    Predict user success likelihood.
    
    Returns success score, status, risk factors, and recommended interventions.
    """
    try:
        result = await predict_user_success(request.user_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/success/interventions")
async def api_get_interventions():
    """
    Get users needing intervention.
    
    Returns at-risk users and pending interventions sorted by priority.
    """
    try:
        result = await get_users_needing_intervention()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/success/stats")
async def api_success_stats():
    """Get success predictor statistics."""
    predictor = get_success_predictor()
    return {"ok": True, "stats": predictor.get_predictor_stats()}


# ============================================================
# REVENUE RECONCILIATION ENDPOINTS
# ============================================================

@router.post("/revenue/record")
async def api_record_revenue(request: RecordRevenueRequest):
    """
    Record revenue in the unified ledger.
    
    Automatically calculates fees and tracks expected payout.
    """
    try:
        result = await record_platform_revenue(
            user_id=request.user_id,
            platform=request.platform,
            amount=request.amount,
            reference_id=request.reference_id,
            description=request.description
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revenue/payout")
async def api_record_payout(request: RecordPayoutRequest):
    """
    Record a payout received.
    
    Automatically reconciles with expected amount and detects discrepancies.
    """
    try:
        result = await record_platform_payout(
            user_id=request.user_id,
            platform=request.platform,
            amount=request.amount,
            reference_id=request.reference_id,
            description=request.description
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue/report")
async def api_revenue_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    Get revenue reconciliation report.
    
    Includes totals by source, reconciliation status, and discrepancies.
    """
    try:
        result = await get_revenue_report(start_date, end_date, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue/user/{user_id}")
async def api_user_ledger(user_id: str, limit: int = 100):
    """Get ledger entries for a specific user."""
    engine = get_reconciliation_engine()
    return {"ok": True, "ledger": engine.get_user_ledger(user_id, limit)}


@router.get("/revenue/export")
async def api_export_audit(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export revenue data for audit purposes."""
    engine = get_reconciliation_engine()
    return {"ok": True, "export": engine.export_for_audit(start_date, end_date)}


@router.get("/revenue/stats")
async def api_reconciliation_stats():
    """Get reconciliation statistics."""
    engine = get_reconciliation_engine()
    return {"ok": True, "stats": engine.get_reconciliation_stats()}


# ============================================================
# COMBINED DASHBOARD ENDPOINT
# ============================================================

@router.get("/dashboard")
async def api_upgrades_dashboard():
    """
    Combined dashboard for all upgrade systems.
    
    Returns stats from all 4 systems in one call.
    """
    try:
        verification_engine = get_verification_engine()
        pricing_autopilot = get_pricing_autopilot()
        success_predictor = get_success_predictor()
        reconciliation_engine = get_reconciliation_engine()
        
        return {
            "ok": True,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "systems": {
                "verification": verification_engine.get_verification_stats(),
                "pricing": pricing_autopilot.get_pricing_stats(),
                "success_prediction": success_predictor.get_predictor_stats(),
                "reconciliation": reconciliation_engine.get_reconciliation_stats(),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ROUTER REGISTRATION
# ============================================================

def create_apex_upgrade_routes(app):
    """
    Add all apex upgrade routes to the app.
    
    Usage in main.py:
        from apex_upgrades_api import create_apex_upgrade_routes
        create_apex_upgrade_routes(app)
    """
    app.include_router(router)
    print("✅ Apex Upgrades API routes registered at /apex/upgrades")
