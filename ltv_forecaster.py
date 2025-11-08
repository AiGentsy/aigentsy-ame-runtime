from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
import httpx

router = APIRouter()

class PredictReq(BaseModel):
    user_id: str
    channel: str

class ChurnPredictReq(BaseModel):
    customer_id: str
    agent: str
    time_horizon: int = 30


async def _get_customer_history(agent: str, customer_id: str) -> Dict[str, Any]:
    """Get customer purchase history"""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(
                "https://aigentsy-ame-runtime.onrender.com/user",
                json={"username": agent}
            )
            agent_data = r.json().get("record", {})
        except Exception:
            return {}
    
    invoices = agent_data.get("invoices", [])
    customer_invoices = [inv for inv in invoices if inv.get("buyer") == customer_id]
    
    return {
        "total_purchases": len(customer_invoices),
        "total_spent": sum(float(inv.get("amount", 0)) for inv in customer_invoices),
        "invoices": customer_invoices
    }


def calculate_churn_risk(
    total_purchases: int,
    total_spent: float,
    days_since_last_purchase: int,
    avg_purchase_frequency_days: float
) -> Dict[str, Any]:
    """Calculate churn risk score (0-100)"""
    
    risk_score = 0
    risk_factors = []
    
    # FACTOR 1: Recency (40% weight)
    if days_since_last_purchase > avg_purchase_frequency_days * 2:
        recency_risk = min(40, (days_since_last_purchase / avg_purchase_frequency_days) * 15)
        risk_score += recency_risk
        risk_factors.append(f"Overdue by {days_since_last_purchase - avg_purchase_frequency_days:.0f} days")
    
    # FACTOR 2: Purchase frequency (30% weight)
    if total_purchases < 3:
        frequency_risk = 30 - (total_purchases * 8)
        risk_score += frequency_risk
        risk_factors.append(f"Only {total_purchases} purchases")
    
    # FACTOR 3: Spend level (30% weight)
    if total_spent < 300:
        spend_risk = 30 - (total_spent / 10)
        risk_score += max(0, spend_risk)
        risk_factors.append(f"Low lifetime spend: ${total_spent:.2f}")
    
    risk_score = min(100, max(0, risk_score))
    
    # Classify risk
    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return {
        "risk_score": round(risk_score, 1),
        "risk_level": risk_level,
        "risk_factors": risk_factors
    }


def calculate_ltv_with_churn(
    avg_order_value: float,
    purchase_frequency_months: float,
    churn_rate_monthly: float,
    time_horizon_months: int = 12
) -> Dict[str, Any]:
    """Calculate LTV accounting for churn decay"""
    
    retention_rate = 1 - churn_rate_monthly
    
    # LTV formula with churn: AOV * frequency * ((1 - churn^months) / churn)
    if churn_rate_monthly == 0:
        ltv = avg_order_value * purchase_frequency_months * time_horizon_months
    else:
        ltv = avg_order_value * purchase_frequency_months * (
            (1 - (retention_rate ** time_horizon_months)) / churn_rate_monthly
        )
    
    # Calculate expected purchases over time horizon
    expected_purchases = 0
    for month in range(1, time_horizon_months + 1):
        survival_prob = retention_rate ** month
        expected_purchases += purchase_frequency_months * survival_prob
    
    return {
        "ltv": round(ltv, 2),
        "expected_purchases": round(expected_purchases, 1),
        "retention_rate_monthly": round(retention_rate * 100, 1),
        "time_horizon_months": time_horizon_months
    }


def suggest_retention_campaign(
    risk_level: str,
    risk_score: float,
    customer_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Suggest retention campaign based on churn risk"""
    
    if risk_level == "HIGH":
        campaigns = [
            {
                "type": "WINBACK_DISCOUNT",
                "discount_pct": 25,
                "message": "We miss you! Come back with 25% off your next order.",
                "urgency": "HIGH",
                "send_in_days": 0
            },
            {
                "type": "PERSONAL_OUTREACH",
                "message": "Personal check-in from agent to understand why they left.",
                "urgency": "HIGH",
                "send_in_days": 1
            }
        ]
    elif risk_level == "MEDIUM":
        campaigns = [
            {
                "type": "RE_ENGAGEMENT",
                "discount_pct": 15,
                "message": "Haven't seen you in a while! Here's 15% off.",
                "urgency": "MEDIUM",
                "send_in_days": 3
            },
            {
                "type": "VALUE_REMINDER",
                "message": "Reminder of value delivered in past projects.",
                "urgency": "MEDIUM",
                "send_in_days": 7
            }
        ]
    else:
        campaigns = [
            {
                "type": "LOYALTY_REWARD",
                "discount_pct": 10,
                "message": "Thanks for being a great customer! 10% off next order.",
                "urgency": "LOW",
                "send_in_days": 14
            }
        ]
    
    return {
        "ok": True,
        "recommended_campaigns": campaigns,
        "priority": risk_level
    }


@router.post("/predict")
def predict(req: PredictReq):
    """Basic LTV multiplier by channel"""
    base = {
        "tiktok": 1.1,
        "amazon": 1.05,
        "shopify": 1.0,
        "instagram": 1.15,
        "email": 1.3,
        "organic": 1.4
    }.get(req.channel, 1.0)
    
    return {"ok": True, "ltv_multiplier": base, "channel": req.channel}


@router.post("/churn/predict")
async def predict_churn(req: ChurnPredictReq):
    """Predict customer churn risk"""
    
    history = await _get_customer_history(req.agent, req.customer_id)
    
    if history.get("total_purchases", 0) == 0:
        return {
            "ok": False,
            "error": "no_purchase_history",
            "message": "Customer has no purchase history"
        }
    
    invoices = history.get("invoices", [])
    
    # Calculate metrics
    from datetime import datetime, timezone
    
    sorted_invoices = sorted(invoices, key=lambda x: x.get("ts", ""))
    
    if len(sorted_invoices) >= 2:
        dates = [datetime.fromisoformat(inv.get("ts", "").replace("Z", "+00:00")) for inv in sorted_invoices]
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        avg_frequency_days = sum(intervals) / len(intervals) if intervals else 30
    else:
        avg_frequency_days = 30
    
    last_purchase_date = datetime.fromisoformat(sorted_invoices[-1].get("ts", "").replace("Z", "+00:00"))
    days_since_last = (datetime.now(timezone.utc) - last_purchase_date).days
    
    # Calculate churn risk
    risk = calculate_churn_risk(
        total_purchases=history["total_purchases"],
        total_spent=history["total_spent"],
        days_since_last_purchase=days_since_last,
        avg_purchase_frequency_days=avg_frequency_days
    )
    
    # Suggest retention campaign
    campaign = suggest_retention_campaign(
        risk_level=risk["risk_level"],
        risk_score=risk["risk_score"],
        customer_data=history
    )
    
    return {
        "ok": True,
        "customer_id": req.customer_id,
        "churn_prediction": risk,
        "retention_campaign": campaign,
        "metrics": {
            "total_purchases": history["total_purchases"],
            "total_spent": history["total_spent"],
            "days_since_last_purchase": days_since_last,
            "avg_purchase_frequency_days": round(avg_frequency_days, 1)
        }
    }


@router.post("/ltv/calculate")
async def calculate_ltv(
    agent: str,
    customer_id: str = None,
    time_horizon_months: int = 12
):
    """Calculate LTV with churn decay"""
    
    if customer_id:
        history = await _get_customer_history(agent, customer_id)
        
        if history.get("total_purchases", 0) == 0:
            return {"ok": False, "error": "no_history"}
        
        avg_order_value = history["total_spent"] / history["total_purchases"]
        
        # Estimate monthly purchase frequency
        invoices = history.get("invoices", [])
        if len(invoices) >= 2:
            from datetime import datetime
            dates = [datetime.fromisoformat(inv.get("ts", "").replace("Z", "+00:00")) for inv in invoices]
            total_days = (max(dates) - min(dates)).days
            purchase_frequency_months = (history["total_purchases"] - 1) / (total_days / 30.0) if total_days > 0 else 1
        else:
            purchase_frequency_months = 0.5
        
        # Estimate churn (simple heuristic)
        last_purchase = max(datetime.fromisoformat(inv.get("ts", "").replace("Z", "+00:00")) for inv in invoices)
        days_since = (datetime.now(timezone.utc) - last_purchase).days
        
        if days_since > 90:
            churn_rate_monthly = 0.15
        elif days_since > 60:
            churn_rate_monthly = 0.10
        else:
            churn_rate_monthly = 0.05
    else:
        # Use market averages
        avg_order_value = 200.0
        purchase_frequency_months = 1.0
        churn_rate_monthly = 0.08
    
    ltv_result = calculate_ltv_with_churn(
        avg_order_value=avg_order_value,
        purchase_frequency_months=purchase_frequency_months,
        churn_rate_monthly=churn_rate_monthly,
        time_horizon_months=time_horizon_months
    )
    
    return {
        "ok": True,
        "customer_id": customer_id,
        "ltv_analysis": ltv_result,
        "inputs": {
            "avg_order_value": round(avg_order_value, 2),
            "purchase_frequency_months": round(purchase_frequency_months, 2),
            "churn_rate_monthly": round(churn_rate_monthly * 100, 1)
        }
    }
