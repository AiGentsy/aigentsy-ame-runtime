from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import httpx

_BUNDLES: Dict[str, Dict[str, Any]] = {}

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def create_bundle(
    lead_agent: str,
    agents: List[str],
    title: str,
    description: str,
    services: List[Dict[str, Any]],
    pricing: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a multi-agent bundle"""
    
    if lead_agent not in agents:
        return {"ok": False, "error": "lead_agent_must_be_in_agents_list"}
    
    if len(agents) < 2:
        return {"ok": False, "error": "bundle_requires_at_least_2_agents"}
    
    bundle_id = f"bundle_{uuid4().hex[:8]}"
    
    # Calculate individual vs bundle pricing
    individual_total = sum(float(s.get("price", 0)) for s in services)
    bundle_price = float(pricing.get("bundle_price", individual_total * 0.85))
    discount_pct = round((1 - (bundle_price / individual_total)) * 100, 1) if individual_total > 0 else 0
    
    # Default revenue split (equal unless specified)
    revenue_split = pricing.get("revenue_split") or {agent: 1.0 / len(agents) for agent in agents}
    
    bundle = {
        "id": bundle_id,
        "lead_agent": lead_agent,
        "agents": agents,
        "title": title,
        "description": description,
        "services": services,
        "pricing": {
            "individual_total": round(individual_total, 2),
            "bundle_price": round(bundle_price, 2),
            "discount_pct": discount_pct,
            "revenue_split": revenue_split
        },
        "status": "ACTIVE",
        "performance": {
            "sales": 0,
            "total_revenue": 0.0,
            "avg_delivery_hours": 0,
            "customer_satisfaction": 0.0
        },
        "created_at": now_iso(),
        "events": [{"type": "BUNDLE_CREATED", "by": lead_agent, "at": now_iso()}]
    }
    
    _BUNDLES[bundle_id] = bundle
    
    # Notify all agents
    async with httpx.AsyncClient(timeout=10) as client:
        for agent in agents:
            if agent == lead_agent:
                continue
            
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                    json={
                        "id": f"bundle_notif_{uuid4().hex[:8]}",
                        "sender": lead_agent,
                        "recipient": agent,
                        "title": f"Bundle Created: {title}",
                        "body": f"""{lead_agent} created a bundle with you.

Services:
{chr(10).join(f'- {s.get("name")}' for s in services)}

Bundle Price: ${bundle_price} (Save {discount_pct}%)
Your Share: {int(revenue_split.get(agent, 0) * 100)}%

Bundle ID: {bundle_id}""",
                        "meta": {"bundle_id": bundle_id},
                        "status": "sent",
                        "timestamp": now_iso()
                    }
                )
            except Exception as e:
                print(f"Failed to notify {agent}: {e}")
    
    return {"ok": True, "bundle_id": bundle_id, "bundle": bundle}


async def record_bundle_sale(
    bundle_id: str,
    buyer: str,
    amount_usd: float,
    delivery_hours: int = None,
    satisfaction_score: float = None
) -> Dict[str, Any]:
    """Record a bundle sale and distribute revenue"""
    
    bundle = _BUNDLES.get(bundle_id)
    if not bundle:
        return {"ok": False, "error": "bundle_not_found"}
    
    # Update performance metrics
    bundle["performance"]["sales"] += 1
    bundle["performance"]["total_revenue"] += amount_usd
    
    if delivery_hours:
        old_avg = bundle["performance"]["avg_delivery_hours"]
        old_count = bundle["performance"]["sales"] - 1
        new_avg = ((old_avg * old_count) + delivery_hours) / bundle["performance"]["sales"]
        bundle["performance"]["avg_delivery_hours"] = round(new_avg, 1)
    
    if satisfaction_score:
        old_avg = bundle["performance"]["customer_satisfaction"]
        old_count = bundle["performance"]["sales"] - 1
        new_avg = ((old_avg * old_count) + satisfaction_score) / bundle["performance"]["sales"]
        bundle["performance"]["customer_satisfaction"] = round(new_avg, 2)
    
    # Distribute revenue
    distributions = []
    revenue_split = bundle["pricing"]["revenue_split"]
    
    async with httpx.AsyncClient(timeout=10) as client:
        for agent, share in revenue_split.items():
            agent_amount = round(amount_usd * share, 2)
            
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                    json={
                        "username": agent,
                        "amount": agent_amount,
                        "basis": "bundle_sale",
                        "ref": bundle_id
                    }
                )
                distributions.append({
                    "agent": agent,
                    "amount": agent_amount,
                    "share": share
                })
            except Exception as e:
                print(f"Failed to credit {agent}: {e}")
    
    bundle["events"].append({
        "type": "BUNDLE_SOLD",
        "buyer": buyer,
        "amount": amount_usd,
        "at": now_iso()
    })
    
    return {
        "ok": True,
        "sale_recorded": True,
        "distributions": distributions
    }


async def assign_bundle_roles(
    bundle_id: str,
    role_assignments: Dict[str, str]
) -> Dict[str, Any]:
    """Assign specific roles to agents in bundle"""
    
    bundle = _BUNDLES.get(bundle_id)
    if not bundle:
        return {"ok": False, "error": "bundle_not_found"}
    
    # Validate all agents are assigned
    assigned_agents = set(role_assignments.keys())
    bundle_agents = set(bundle["agents"])
    
    if assigned_agents != bundle_agents:
        return {"ok": False, "error": "must_assign_roles_to_all_agents"}
    
    bundle["role_assignments"] = role_assignments
    bundle["events"].append({
        "type": "ROLES_ASSIGNED",
        "assignments": role_assignments,
        "at": now_iso()
    })
    
    return {"ok": True, "role_assignments": role_assignments}


def update_bundle_status(
    bundle_id: str,
    status: str,
    reason: str = ""
) -> Dict[str, Any]:
    """Update bundle status (ACTIVE, PAUSED, DISSOLVED)"""
    
    bundle = _BUNDLES.get(bundle_id)
    if not bundle:
        return {"ok": False, "error": "bundle_not_found"}
    
    if status not in ["ACTIVE", "PAUSED", "DISSOLVED"]:
        return {"ok": False, "error": "status_must_be_ACTIVE_PAUSED_or_DISSOLVED"}
    
    old_status = bundle["status"]
    bundle["status"] = status
    bundle["events"].append({
        "type": f"STATUS_CHANGED_TO_{status}",
        "from": old_status,
        "reason": reason,
        "at": now_iso()
    })
    
    return {"ok": True, "status": status}


def get_bundle(bundle_id: str) -> Dict[str, Any]:
    """Get bundle details"""
    bundle = _BUNDLES.get(bundle_id)
    if not bundle:
        return {"ok": False, "error": "bundle_not_found"}
    return {"ok": True, "bundle": bundle}


def list_bundles(
    agent: str = None,
    status: str = None,
    sort_by: str = "performance"
) -> Dict[str, Any]:
    """List bundles with filters"""
    bundles = list(_BUNDLES.values())
    
    if agent:
        bundles = [b for b in bundles if agent in b["agents"]]
    
    if status:
        bundles = [b for b in bundles if b["status"] == status.upper()]
    
    if sort_by == "performance":
        bundles.sort(key=lambda b: b["performance"]["total_revenue"], reverse=True)
    elif sort_by == "sales":
        bundles.sort(key=lambda b: b["performance"]["sales"], reverse=True)
    elif sort_by == "satisfaction":
        bundles.sort(key=lambda b: b["performance"]["customer_satisfaction"], reverse=True)
    else:
        bundles.sort(key=lambda b: b["created_at"], reverse=True)
    
    return {"ok": True, "bundles": bundles, "count": len(bundles)}


def get_bundle_performance_stats(bundle_id: str) -> Dict[str, Any]:
    """Get detailed bundle performance statistics"""
    
    bundle = _BUNDLES.get(bundle_id)
    if not bundle:
        return {"ok": False, "error": "bundle_not_found"}
    
    perf = bundle["performance"]
    
    # Calculate per-agent earnings
    revenue_split = bundle["pricing"]["revenue_split"]
    total_revenue = perf["total_revenue"]
    
    agent_earnings = {
        agent: round(total_revenue * share, 2)
        for agent, share in revenue_split.items()
    }
    
    # ROI calculation
    individual_total = bundle["pricing"]["individual_total"]
    bundle_price = bundle["pricing"]["bundle_price"]
    savings_per_sale = individual_total - bundle_price
    total_savings_delivered = savings_per_sale * perf["sales"]
    
    return {
        "ok": True,
        "bundle_id": bundle_id,
        "performance": perf,
        "agent_earnings": agent_earnings,
        "economics": {
            "total_revenue": total_revenue,
            "total_savings_delivered": round(total_savings_delivered, 2),
            "avg_revenue_per_sale": round(total_revenue / perf["sales"], 2) if perf["sales"] > 0 else 0
        }
    }
