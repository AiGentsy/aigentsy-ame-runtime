"""
AiGentsy Financial Analytics Dashboard
Revenue tracking, forecasting, and performance metrics
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

def _now():
    return datetime.now(timezone.utc).isoformat()

def _days_ago(ts_iso: str) -> int:
    try:
        then = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - then).days
    except:
        return 9999


# ============ REVENUE ANALYTICS ============

def calculate_revenue_metrics(
    users: List[Dict[str, Any]],
    period_days: int = 30
) -> Dict[str, Any]:
    """
    Calculate platform revenue metrics
    """
    total_revenue = 0.0
    total_fees = 0.0
    completed_orders = 0
    active_agents = set()
    active_buyers = set()
    
    for user in users:
        ledger = user.get("ownership", {}).get("ledger", [])
        
        for entry in ledger:
            if _days_ago(entry.get("ts", "")) > period_days:
                continue
            
            basis = entry.get("basis", "")
            amount = float(entry.get("amount", 0))
            
            # Revenue
            if basis == "revenue" and amount > 0:
                total_revenue += amount
                completed_orders += 1
                active_agents.add(user.get("username"))
            
            # Platform fees
            if basis == "platform_fee":
                total_fees += abs(amount)
        
        # Track active buyers (those with intents)
        intents = user.get("intents", [])
        for intent in intents:
            if _days_ago(intent.get("created_at", "")) <= period_days:
                active_buyers.add(user.get("username"))
    
    # Calculate averages
    avg_order_value = round(total_revenue / completed_orders, 2) if completed_orders > 0 else 0
    avg_fee_per_order = round(total_fees / completed_orders, 2) if completed_orders > 0 else 0
    
    return {
        "period_days": period_days,
        "total_revenue": round(total_revenue, 2),
        "total_fees": round(total_fees, 2),
        "net_revenue": round(total_revenue - total_fees, 2),
        "completed_orders": completed_orders,
        "avg_order_value": avg_order_value,
        "avg_fee_per_order": avg_fee_per_order,
        "active_agents": len(active_agents),
        "active_buyers": len(active_buyers),
        "calculated_at": _now()
    }


def calculate_revenue_by_currency(
    users: List[Dict[str, Any]],
    period_days: int = 30
) -> Dict[str, Any]:
    """
    Break down revenue by currency
    """
    revenue_by_currency = {}
    
    for user in users:
        ledger = user.get("ownership", {}).get("ledger", [])
        
        for entry in ledger:
            if _days_ago(entry.get("ts", "")) > period_days:
                continue
            
            if entry.get("basis") == "revenue":
                currency = entry.get("currency", "USD")
                amount = float(entry.get("amount", 0))
                
                if currency not in revenue_by_currency:
                    revenue_by_currency[currency] = 0.0
                
                revenue_by_currency[currency] += amount
    
    # Round all values
    for currency in revenue_by_currency:
        revenue_by_currency[currency] = round(revenue_by_currency[currency], 2)
    
    return {
        "period_days": period_days,
        "revenue_by_currency": revenue_by_currency,
        "total_currencies": len(revenue_by_currency)
    }


def forecast_revenue(
    historical_data: Dict[str, Any],
    forecast_days: int = 30
) -> Dict[str, Any]:
    """
    Simple linear regression forecast
    """
    total_revenue = historical_data.get("total_revenue", 0)
    period_days = historical_data.get("period_days", 30)
    
    # Calculate daily average
    daily_avg = total_revenue / period_days if period_days > 0 else 0
    
    # Project forward
    forecasted_revenue = daily_avg * forecast_days
    
    # Add growth factor (assume 10% growth)
    growth_factor = 1.10
    optimistic_forecast = forecasted_revenue * growth_factor
    pessimistic_forecast = forecasted_revenue * 0.90
    
    return {
        "forecast_period_days": forecast_days,
        "based_on_days": period_days,
        "daily_average": round(daily_avg, 2),
        "baseline_forecast": round(forecasted_revenue, 2),
        "optimistic_forecast": round(optimistic_forecast, 2),
        "pessimistic_forecast": round(pessimistic_forecast, 2),
        "growth_rate_assumed": 0.10,
        "forecasted_at": _now()
    }


# ============ AGENT PERFORMANCE METRICS ============

def calculate_agent_metrics(
    user: Dict[str, Any],
    period_days: int = 30
) -> Dict[str, Any]:
    """
    Calculate individual agent performance metrics
    """
    # Find completed intents where this user is the agent
    username = user.get("consent", {}).get("username") or user.get("username")
    
    completed_jobs = 0
    total_earned = 0.0
    total_fees_paid = 0.0
    on_time_deliveries = 0
    late_deliveries = 0
    disputes = 0
    
    ledger = user.get("ownership", {}).get("ledger", [])
    
    for entry in ledger:
        if _days_ago(entry.get("ts", "")) > period_days:
            continue
        
        basis = entry.get("basis", "")
        amount = float(entry.get("amount", 0))
        
        if basis == "revenue" and amount > 0:
            completed_jobs += 1
            total_earned += amount
        
        if basis == "platform_fee":
            total_fees_paid += abs(amount)
        
        if basis == "sla_bonus":
            on_time_deliveries += 1
        
        if basis == "bond_slash":
            disputes += 1
    
    # Calculate metrics
    avg_job_value = round(total_earned / completed_jobs, 2) if completed_jobs > 0 else 0
    avg_fee_per_job = round(total_fees_paid / completed_jobs, 2) if completed_jobs > 0 else 0
    net_earnings = round(total_earned - total_fees_paid, 2)
    
    on_time_rate = round(on_time_deliveries / completed_jobs, 2) if completed_jobs > 0 else 0
    dispute_rate = round(disputes / completed_jobs, 2) if completed_jobs > 0 else 0
    
    # Current balances
    aigx_balance = float(user.get("ownership", {}).get("aigx", 0))
    usd_balance = float(user.get("ownership", {}).get("usd", 0))
    
    # OCL metrics
    ocl_limit = float(user.get("ocl", {}).get("limit", 0))
    ocl_outstanding = float(user.get("ocl", {}).get("outstanding", 0))
    ocl_available = ocl_limit - ocl_outstanding
    
    # Outcome score
    outcome_score = int(user.get("outcomeScore", 0))
    
    return {
        "username": username,
        "period_days": period_days,
        "completed_jobs": completed_jobs,
        "total_earned": total_earned,
        "total_fees_paid": total_fees_paid,
        "net_earnings": net_earnings,
        "avg_job_value": avg_job_value,
        "on_time_rate": on_time_rate,
        "dispute_rate": dispute_rate,
        "outcome_score": outcome_score,
        "balances": {
            "aigx": round(aigx_balance, 2),
            "usd": round(usd_balance, 2)
        },
        "ocl": {
            "limit": round(ocl_limit, 2),
            "outstanding": round(ocl_outstanding, 2),
            "available": round(ocl_available, 2)
        },
        "calculated_at": _now()
    }


def rank_agents_by_performance(
    users: List[Dict[str, Any]],
    metric: str = "total_earned",
    limit: int = 10
) -> Dict[str, Any]:
    """
    Rank agents by performance metric
    
    metric options: total_earned, completed_jobs, outcome_score, on_time_rate
    """
    agent_metrics = []
    
    for user in users:
        # Only include users with agent activity
        if user.get("intents") or user.get("ownership", {}).get("ledger"):
            metrics = calculate_agent_metrics(user, period_days=30)
            agent_metrics.append(metrics)
    
    # Sort by metric
    if metric in ["total_earned", "completed_jobs", "outcome_score", "on_time_rate"]:
        agent_metrics.sort(key=lambda x: x.get(metric, 0), reverse=True)
    
    # Limit results
    top_agents = agent_metrics[:limit]
    
    return {
        "metric": metric,
        "total_agents": len(agent_metrics),
        "top_agents": top_agents,
        "limit": limit
    }


# ============ FINANCIAL HEALTH MONITORING ============

def calculate_platform_health(
    users: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate overall platform financial health
    """
    # Revenue metrics
    revenue_30d = calculate_revenue_metrics(users, period_days=30)
    revenue_7d = calculate_revenue_metrics(users, period_days=7)
    
    # Growth rate (7d vs 30d normalized)
    daily_30d = revenue_30d["total_revenue"] / 30
    daily_7d = revenue_7d["total_revenue"] / 7
    
    growth_rate = ((daily_7d - daily_30d) / daily_30d) if daily_30d > 0 else 0
    
    # OCL metrics
    total_ocl_limit = 0.0
    total_ocl_outstanding = 0.0
    total_aigx = 0.0
    total_usd = 0.0
    
    for user in users:
        total_ocl_limit += float(user.get("ocl", {}).get("limit", 0))
        total_ocl_outstanding += float(user.get("ocl", {}).get("outstanding", 0))
        total_aigx += float(user.get("ownership", {}).get("aigx", 0))
        total_usd += float(user.get("ownership", {}).get("usd", 0))
    
    ocl_utilization = (total_ocl_outstanding / total_ocl_limit) if total_ocl_limit > 0 else 0
    
    # Insurance pool
    insurance_pool = 0.0
    for user in users:
        if user.get("username") == "insurance_pool":
            insurance_pool = float(user.get("ownership", {}).get("aigx", 0))
    
    # Health score (0-100)
    health_score = 100
    
    # Deduct for high OCL utilization (risky)
    if ocl_utilization > 0.8:
        health_score -= 20
    elif ocl_utilization > 0.6:
        health_score -= 10
    
    # Deduct for negative growth
    if growth_rate < 0:
        health_score -= 15
    
    # Deduct for low insurance pool
    if insurance_pool < 100:
        health_score -= 10
    
    health_score = max(0, health_score)
    
    # Determine status
    if health_score >= 80:
        status = "healthy"
    elif health_score >= 60:
        status = "moderate"
    else:
        status = "at_risk"
    
    return {
        "health_score": health_score,
        "status": status,
        "revenue_30d": revenue_30d["total_revenue"],
        "revenue_7d": revenue_7d["total_revenue"],
        "growth_rate_7d": round(growth_rate * 100, 2),
        "ocl": {
            "total_limit": round(total_ocl_limit, 2),
            "total_outstanding": round(total_ocl_outstanding, 2),
            "utilization": round(ocl_utilization * 100, 2)
        },
        "liquidity": {
            "total_aigx": round(total_aigx, 2),
            "total_usd": round(total_usd, 2),
            "insurance_pool": round(insurance_pool, 2)
        },
        "calculated_at": _now()
    }


def generate_cohort_analysis(
    users: List[Dict[str, Any]],
    cohort_by: str = "signup_month"
) -> Dict[str, Any]:
    """
    Analyze user cohorts
    
    cohort_by options: signup_month, outcome_score_tier, revenue_tier
    """
    cohorts = {}
    
    for user in users:
        cohort_key = ""
        
        if cohort_by == "signup_month":
            created_at = user.get("consent", {}).get("timestamp") or user.get("created_at", "")
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                cohort_key = dt.strftime("%Y-%m")
            except:
                cohort_key = "unknown"
        
        elif cohort_by == "outcome_score_tier":
            score = int(user.get("outcomeScore", 0))
            if score >= 85:
                cohort_key = "expert"
            elif score >= 70:
                cohort_key = "proficient"
            elif score >= 50:
                cohort_key = "competent"
            elif score >= 30:
                cohort_key = "developing"
            else:
                cohort_key = "novice"
        
        elif cohort_by == "revenue_tier":
            metrics = calculate_agent_metrics(user, period_days=90)
            revenue = metrics["total_earned"]
            
            if revenue >= 5000:
                cohort_key = "high"
            elif revenue >= 1000:
                cohort_key = "medium"
            elif revenue > 0:
                cohort_key = "low"
            else:
                cohort_key = "inactive"
        
        if cohort_key not in cohorts:
            cohorts[cohort_key] = {
                "users": 0,
                "total_revenue": 0.0,
                "completed_jobs": 0
            }
        
        cohorts[cohort_key]["users"] += 1
        
        # Add revenue data
        metrics = calculate_agent_metrics(user, period_days=90)
        cohorts[cohort_key]["total_revenue"] += metrics["total_earned"]
        cohorts[cohort_key]["completed_jobs"] += metrics["completed_jobs"]
    
    # Calculate averages
    for cohort in cohorts.values():
        cohort["avg_revenue_per_user"] = round(cohort["total_revenue"] / cohort["users"], 2) if cohort["users"] > 0 else 0
        cohort["total_revenue"] = round(cohort["total_revenue"], 2)
    
    return {
        "cohort_by": cohort_by,
        "total_cohorts": len(cohorts),
        "cohorts": cohorts,
        "generated_at": _now()
    }


# ============ ALERTS & NOTIFICATIONS ============

def detect_financial_alerts(
    platform_health: Dict[str, Any],
    revenue_metrics: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Detect financial issues and generate alerts
    """
    alerts = []
    
    # High OCL utilization
    ocl_util = platform_health["ocl"]["utilization"]
    if ocl_util > 80:
        alerts.append({
            "severity": "high",
            "type": "ocl_utilization",
            "message": f"OCL utilization at {ocl_util}% - approaching credit limit",
            "recommendation": "Consider expanding OCL limits or increasing agent collections"
        })
    
    # Negative growth
    growth_rate = platform_health.get("growth_rate_7d", 0)
    if growth_rate < -10:
        alerts.append({
            "severity": "medium",
            "type": "negative_growth",
            "message": f"Revenue declining at {abs(growth_rate)}% week-over-week",
            "recommendation": "Review agent performance and marketing initiatives"
        })
    
    # Low insurance pool
    insurance_pool = platform_health["liquidity"]["insurance_pool"]
    if insurance_pool < 50:
        alerts.append({
            "severity": "medium",
            "type": "low_insurance_pool",
            "message": f"Insurance pool at ${insurance_pool} - below recommended minimum",
            "recommendation": "Increase insurance fees or reduce payout frequency"
        })
    
    # Low completed orders
    if revenue_metrics["completed_orders"] < 5:
        alerts.append({
            "severity": "low",
            "type": "low_activity",
            "message": f"Only {revenue_metrics['completed_orders']} orders completed in period",
            "recommendation": "Focus on agent acquisition and buyer engagement"
        })
    
    return alerts
