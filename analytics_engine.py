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


# ============================================================
# UNIVERSAL OUTCOME LEDGER (UoL) ANALYTICS
# ============================================================

def get_uol_summary(username: str) -> Dict[str, Any]:
    """
    Get Universal Outcome Ledger summary for a user.
    
    Aggregates UoO from all verified PoO receipts.
    Calculates percentile ranking vs all users.
    
    Args:
        username: User to query
        
    Returns:
        dict: UoL summary with aggregates and percentile
    """
    from outcome_oracle import list_poos
    
    # Get all verified PoOs for this user
    poos_result = list_poos(agent=username, status="VERIFIED")
    poos = poos_result.get("poos", [])
    
    if not poos:
        return {
            "ok": True,
            "username": username,
            "total_outcomes": 0,
            "total_uoo": 0,
            "average_uoo": 0,
            "by_archetype": {},
            "by_difficulty": {},
            "by_value_band": {},
            "percentile": 0
        }
    
    # ============================================
    # AGGREGATE UoO TOTALS
    # ============================================
    
    total_uoo = sum(p.get("uoo", {}).get("uoo_score", 0) for p in poos)
    avg_uoo = total_uoo / len(poos) if poos else 0
    
    # ============================================
    # BY ARCHETYPE
    # ============================================
    
    by_archetype = {}
    for poo in poos:
        if "uoo" in poo:
            archetype = poo["uoo"]["archetype"]
            archetype_name = poo["uoo"]["archetype_name"]
            uoo_score = poo["uoo"]["uoo_score"]
            
            if archetype not in by_archetype:
                by_archetype[archetype] = {
                    "name": archetype_name,
                    "count": 0,
                    "total_uoo": 0
                }
            
            by_archetype[archetype]["count"] += 1
            by_archetype[archetype]["total_uoo"] += uoo_score
    
    # Round and add averages
    for archetype_data in by_archetype.values():
        archetype_data["total_uoo"] = round(archetype_data["total_uoo"], 3)
        archetype_data["avg_uoo"] = round(
            archetype_data["total_uoo"] / archetype_data["count"], 3
        ) if archetype_data["count"] > 0 else 0
    
    # ============================================
    # BY DIFFICULTY
    # ============================================
    
    by_difficulty = {}
    for poo in poos:
        if "uoo" in poo:
            difficulty = poo["uoo"]["difficulty"]
            uoo_score = poo["uoo"]["uoo_score"]
            
            if difficulty not in by_difficulty:
                by_difficulty[difficulty] = {"count": 0, "total_uoo": 0}
            
            by_difficulty[difficulty]["count"] += 1
            by_difficulty[difficulty]["total_uoo"] += uoo_score
    
    # Round
    for difficulty_data in by_difficulty.values():
        difficulty_data["total_uoo"] = round(difficulty_data["total_uoo"], 3)
    
    # ============================================
    # BY VALUE BAND
    # ============================================
    
    by_value_band = {}
    for poo in poos:
        if "uoo" in poo:
            value_band = poo["uoo"]["value_band"]
            uoo_score = poo["uoo"]["uoo_score"]
            
            if value_band not in by_value_band:
                by_value_band[value_band] = {"count": 0, "total_uoo": 0}
            
            by_value_band[value_band]["count"] += 1
            by_value_band[value_band]["total_uoo"] += uoo_score
    
    # Round
    for band_data in by_value_band.values():
        band_data["total_uoo"] = round(band_data["total_uoo"], 3)
    
    # ============================================
    # PERCENTILE CALCULATION
    # ============================================
    
    # Get all users and calculate their UoO totals
    from outcome_oracle import _POO_LEDGER
    
    # Get unique agents from ledger
    all_agents = set(p["agent"] for p in _POO_LEDGER.values() if p["status"] == "VERIFIED")
    
    # Calculate UoO for each agent
    agent_totals = []
    for agent in all_agents:
        agent_poos = [p for p in _POO_LEDGER.values() 
                      if p["agent"] == agent and p["status"] == "VERIFIED"]
        agent_uoo = sum(p.get("uoo", {}).get("uoo_score", 0) for p in agent_poos)
        agent_totals.append(agent_uoo)
    
    # Calculate percentile
    percentile = 0
    if agent_totals:
        agent_totals.sort()
        rank = sum(1 for t in agent_totals if t < total_uoo)
        percentile = round((rank / len(agent_totals)) * 100)
    
    return {
        "ok": True,
        "username": username,
        "total_outcomes": len(poos),
        "total_uoo": round(total_uoo, 3),
        "average_uoo": round(avg_uoo, 3),
        "by_archetype": by_archetype,
        "by_difficulty": by_difficulty,
        "by_value_band": by_value_band,
        "percentile": percentile
    }


def get_uol_by_date(username: str, days: int = 30) -> Dict[str, Any]:
    """
    Get UoO aggregates over time (daily buckets).
    
    Args:
        username: User to query
        days: Number of days to look back
        
    Returns:
        dict: Daily UoO time series
    """
    from outcome_oracle import list_poos
    
    # Get all verified PoOs for user
    poos_result = list_poos(agent=username, status="VERIFIED")
    poos = poos_result.get("poos", [])
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    # Group by date
    by_date = {}
    for poo in poos:
        verified_at = poo.get("verified_at")
        if not verified_at:
            continue
        
        try:
            poo_date = datetime.fromisoformat(verified_at.replace("Z", "+00:00"))
        except:
            continue
        
        if poo_date < start_date:
            continue
        
        date_key = poo_date.strftime("%Y-%m-%d")
        uoo_score = poo.get("uoo", {}).get("uoo_score", 0)
        
        if date_key not in by_date:
            by_date[date_key] = {"count": 0, "total_uoo": 0}
        
        by_date[date_key]["count"] += 1
        by_date[date_key]["total_uoo"] += uoo_score
    
    # Fill missing dates with zeros (create continuous series)
    date_series = []
    for i in range(days):
        date = now - timedelta(days=days - i - 1)
        date_key = date.strftime("%Y-%m-%d")
        
        if date_key in by_date:
            date_series.append({
                "date": date_key,
                "count": by_date[date_key]["count"],
                "total_uoo": round(by_date[date_key]["total_uoo"], 3)
            })
        else:
            date_series.append({
                "date": date_key,
                "count": 0,
                "total_uoo": 0
            })
    
    return {
        "ok": True,
        "username": username,
        "days": days,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": now.strftime("%Y-%m-%d"),
        "by_date": date_series,
        "total_outcomes": sum(d["count"] for d in date_series),
        "total_uoo": round(sum(d["total_uoo"] for d in date_series), 3)
    }


def export_uol_receipts(username: str, format: str = "json") -> Any:
    """
    Export all PoO receipts with UoO metadata.
    
    Args:
        username: User to export
        format: "json" or "csv"
        
    Returns:
        list (json) or str (csv): Exported receipts
    """
    from outcome_oracle import list_poos
    import csv
    import io
    
    # Get all verified PoOs for user
    poos_result = list_poos(agent=username, status="VERIFIED")
    poos = poos_result.get("poos", [])
    
    if format == "csv":
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "poo_id",
            "intent_id",
            "title",
            "submitted_at",
            "verified_at",
            "verified_by",
            "uoo_score",
            "archetype",
            "archetype_name",
            "difficulty",
            "value_band",
            "deal_value",
            "confidence",
            "verified",
            "metrics"
        ])
        
        # Rows
        for poo in poos:
            uoo = poo.get("uoo", {})
            writer.writerow([
                poo.get("id", ""),
                poo.get("intent_id", ""),
                poo.get("title", ""),
                poo.get("submitted_at", ""),
                poo.get("verified_at", ""),
                poo.get("verified_by", ""),
                uoo.get("uoo_score", 0),
                uoo.get("archetype", ""),
                uoo.get("archetype_name", ""),
                uoo.get("difficulty", ""),
                uoo.get("value_band", ""),
                uoo.get("deal_value", 0),
                uoo.get("confidence", 0),
                uoo.get("verified", False),
                str(poo.get("metrics", {}))
            ])
        
        return output.getvalue()
    
    else:  # JSON format
        # Clean up for export (remove internal fields)
        export_poos = []
        for poo in poos:
            export_poos.append({
                "poo_id": poo.get("id"),
                "intent_id": poo.get("intent_id"),
                "title": poo.get("title"),
                "description": poo.get("description"),
                "submitted_at": poo.get("submitted_at"),
                "verified_at": poo.get("verified_at"),
                "verified_by": poo.get("verified_by"),
                "buyer_feedback": poo.get("buyer_feedback"),
                "evidence_urls": poo.get("evidence_urls", []),
                "metrics": poo.get("metrics", {}),
                "uoo": poo.get("uoo", {})
            })
        
        return export_poos
