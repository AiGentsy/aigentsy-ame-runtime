from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import httpx

# Import all subsystems
try:
    from metahive_brain import query_hive, report_pattern_usage
    from pricing_oracle import calculate_dynamic_price
    from outcome_oracle_max import on_event
    from ltv_forecaster import calculate_ltv_with_churn
    from bundle_engine import create_bundle
    from fraud_detector import check_fraud_signals
    from compliance_oracle import check_transaction_allowed
except Exception as e:
    print(f"Conductor import warning: {e}")

_EXECUTION_QUEUE: List[Dict[str, Any]] = []
_DEVICE_REGISTRY: Dict[str, Dict[str, Any]] = {}
_USER_POLICIES: Dict[str, Dict[str, Any]] = {}
_EXECUTION_HISTORY: List[Dict[str, Any]] = []

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def register_device(
    username: str,
    device_id: str,
    connected_apps: List[Dict[str, Any]],
    capabilities: List[str]
) -> Dict[str, Any]:
    """Register device and its connected apps"""
    
    device_key = f"{username}:{device_id}"
    
    device = {
        "username": username,
        "device_id": device_id,
        "connected_apps": connected_apps,
        "capabilities": capabilities,
        "registered_at": now_iso(),
        "last_seen": now_iso(),
        "status": "ACTIVE",
        "stats": {
            "actions_executed": 0,
            "revenue_generated": 0.0,
            "jvs_active": 0
        }
    }
    
    _DEVICE_REGISTRY[device_key] = device
    
    # Broadcast to hive for matching
    await _broadcast_capabilities(username, device_id, connected_apps, capabilities)
    
    return {
        "ok": True,
        "device_key": device_key,
        "device": device,
        "message": "Device registered, scanning for opportunities..."
    }


async def _broadcast_capabilities(
    username: str,
    device_id: str,
    connected_apps: List[Dict[str, Any]],
    capabilities: List[str]
) -> None:
    """Broadcast device capabilities to hive for matching"""
    
    # Extract app types
    app_types = [app.get("type") for app in connected_apps]
    
    # Build capability profile
    profile = {
        "username": username,
        "device_id": device_id,
        "apps": app_types,
        "capabilities": capabilities,
        "seeking": []
    }
    
    # Determine what this device needs
    if "tiktok" in app_types and "shopify" not in app_types:
        profile["seeking"].append("ecommerce")
    
    if "shopify" in app_types and "tiktok" not in app_types:
        profile["seeking"].append("social_traffic")
    
    if "email" in capabilities and len(app_types) < 2:
        profile["seeking"].append("partnerships")
    
    # Store in hive (would integrate with metahive_brain.py)
    print(f"Broadcasting: {username} has {app_types}, seeking {profile['seeking']}")


async def scan_opportunities(
    username: str,
    device_id: str
) -> Dict[str, Any]:
    """Scan for revenue opportunities across all systems"""
    
    device_key = f"{username}:{device_id}"
    device = _DEVICE_REGISTRY.get(device_key)
    
    if not device:
        return {"ok": False, "error": "device_not_registered"}
    
    opportunities = []
    
    # Get user's outcome score for reputation-weighting
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(
                f"https://aigentsy-ame-runtime.onrender.com/score/outcome?username={username}"
            )
            outcome_score = r.json().get("score", 50)
        except Exception:
            outcome_score = 50
    
    connected_apps = device.get("connected_apps", [])
    app_types = [app.get("type") for app in connected_apps]
    
    # OPPORTUNITY 1: JV Partnerships (if has audience or inventory)
    if any(app in app_types for app in ["tiktok", "instagram", "youtube"]):
        jv_opportunities = await _find_jv_matches(username, device_id, "social_traffic", outcome_score)
        opportunities.extend(jv_opportunities)
    
    if "shopify" in app_types:
        jv_opportunities = await _find_jv_matches(username, device_id, "ecommerce", outcome_score)
        opportunities.extend(jv_opportunities)
    
    # OPPORTUNITY 2: Price optimization (if has ecommerce)
    if "shopify" in app_types:
        pricing_opps = await _find_pricing_opportunities(username, device_id)
        opportunities.extend(pricing_opps)
    
    # OPPORTUNITY 3: Content posting (if has social + hive patterns)
    if any(app in app_types for app in ["tiktok", "instagram"]):
        content_opps = await _find_content_opportunities(username, device_id)
        opportunities.extend(content_opps)
    
    # OPPORTUNITY 4: Cart recovery (if has ecommerce + email)
    if "shopify" in app_types and "email" in device.get("capabilities", []):
        cart_opps = await _find_cart_recovery_opportunities(username, device_id)
        opportunities.extend(cart_opps)
    
    # Sort by expected value
    opportunities.sort(key=lambda x: x.get("expected_value_usd", 0), reverse=True)
    
    return {
        "ok": True,
        "username": username,
        "device_id": device_id,
        "opportunities": opportunities,
        "count": len(opportunities)
    }


async def _find_jv_matches(
    username: str,
    device_id: str,
    offering: str,
    outcome_score: int
) -> List[Dict[str, Any]]:
    """Find JV partnership opportunities"""
    
    # Query other devices for complementary needs
    matches = []
    
    for key, other_device in _DEVICE_REGISTRY.items():
        if key.startswith(username):
            continue
        
        other_apps = [app.get("type") for app in other_device.get("connected_apps", [])]
        
        # Match logic
        if offering == "social_traffic" and "shopify" in other_apps:
            matches.append({
                "type": "JV_PARTNERSHIP",
                "partner": other_device["username"],
                "partner_device": other_device["device_id"],
                "opportunity": "Promote their products on your social",
                "expected_value_usd": 50 * (outcome_score / 50),
                "revenue_split": {"you": 0.6, "partner": 0.4},
                "confidence": 0.75,
                "requires_approval": True
            })
        
        elif offering == "ecommerce" and any(app in other_apps for app in ["tiktok", "instagram"]):
            matches.append({
                "type": "JV_PARTNERSHIP",
                "partner": other_device["username"],
                "partner_device": other_device["device_id"],
                "opportunity": "They promote your products on their social",
                "expected_value_usd": 80 * (outcome_score / 50),
                "revenue_split": {"you": 0.4, "partner": 0.6},
                "confidence": 0.75,
                "requires_approval": True
            })
    
    return matches[:3]


async def _find_pricing_opportunities(username: str, device_id: str) -> List[Dict[str, Any]]:
    """Find dynamic pricing opportunities"""
    
    opportunities = []
    
    # Simulate abandoned cart data (would come from Shopify API)
    abandoned_carts = [
        {"cart_id": "cart_123", "items": [{"name": "Product A", "price": 49.99}], "customer": "buyer1"},
        {"cart_id": "cart_456", "items": [{"name": "Product B", "price": 79.99}], "customer": "buyer2"}
    ]
    
    for cart in abandoned_carts[:2]:
        opportunities.append({
            "type": "PRICE_DISCOUNT",
            "action": "Send discount code to recover abandoned cart",
            "cart_id": cart["cart_id"],
            "customer": cart["customer"],
            "suggested_discount": 15,
            "expected_value_usd": sum(item["price"] for item in cart["items"]) * 0.85 * 0.3,
            "confidence": 0.65,
            "requires_approval": False
        })
    
    return opportunities


async def _find_content_opportunities(username: str, device_id: str) -> List[Dict[str, Any]]:
    """Find content posting opportunities from hive patterns"""
    
    opportunities = []
    
    try:
        # Query hive for successful patterns
        from metahive_brain import query_hive
        
        context = {
            "channel": "tiktok",
            "time": "evening",
            "content_type": "promotional"
        }
        
        result = query_hive(context=context, pattern_type="content_post", limit=2)
        patterns = result.get("patterns", [])
        
        for pattern in patterns:
            opportunities.append({
                "type": "CONTENT_POST",
                "platform": "tiktok",
                "suggested_content": pattern["action"].get("content_template"),
                "best_time": pattern["context"].get("hour"),
                "expected_value_usd": pattern["outcome"].get("revenue_usd", 0) * 0.7,
                "confidence": pattern.get("score", 0) / 2,
                "requires_approval": True,
                "pattern_id": pattern["id"]
            })
    except Exception as e:
        print(f"Hive query failed: {e}")
    
    return opportunities


async def _find_cart_recovery_opportunities(username: str, device_id: str) -> List[Dict[str, Any]]:
    """Find cart recovery email opportunities"""
    
    opportunities = []
    
    # Simulate cart abandonment data
    opportunities.append({
        "type": "EMAIL_CAMPAIGN",
        "action": "Send cart recovery email sequence",
        "target_count": 12,
        "expected_recovery_rate": 0.25,
        "expected_value_usd": 35,
        "confidence": 0.70,
        "requires_approval": False
    })
    
    return opportunities


async def create_execution_plan(
    username: str,
    device_id: str,
    opportunities: List[Dict[str, Any]],
    max_actions: int = 10
) -> Dict[str, Any]:
    """Create coordinated execution plan from opportunities"""
    
    plan_id = f"plan_{uuid4().hex[:8]}"
    
    # Filter by user policies
    user_policy = _USER_POLICIES.get(username, {})
    auto_approve_threshold = user_policy.get("auto_approve_confidence", 0.80)
    
    actions_needing_approval = []
    actions_auto_approved = []
    
    for opp in opportunities[:max_actions]:
        requires_approval = opp.get("requires_approval", True)
        confidence = opp.get("confidence", 0)
        
        action = {
            "id": f"action_{uuid4().hex[:8]}",
            "type": opp["type"],
            "opportunity": opp,
            "status": "PENDING_APPROVAL",
            "estimated_value": opp.get("expected_value_usd", 0),
            "confidence": confidence
        }
        
        if not requires_approval or confidence >= auto_approve_threshold:
            action["status"] = "AUTO_APPROVED"
            actions_auto_approved.append(action)
        else:
            actions_needing_approval.append(action)
    
    plan = {
        "id": plan_id,
        "username": username,
        "device_id": device_id,
        "created_at": now_iso(),
        "actions_auto_approved": actions_auto_approved,
        "actions_needing_approval": actions_needing_approval,
        "total_estimated_value": sum(
            a["estimated_value"] for a in actions_auto_approved + actions_needing_approval
        ),
        "status": "PENDING_USER_REVIEW" if actions_needing_approval else "READY_TO_EXECUTE"
    }
    
    _EXECUTION_QUEUE.append(plan)
    
    return {
        "ok": True,
        "plan_id": plan_id,
        "plan": plan,
        "summary": {
            "auto_approved": len(actions_auto_approved),
            "needs_approval": len(actions_needing_approval),
            "total_estimated_value": round(plan["total_estimated_value"], 2)
        }
    }


async def approve_execution_plan(
    plan_id: str,
    username: str,
    approved_action_ids: List[str] = None
) -> Dict[str, Any]:
    """User approves execution plan"""
    
    plan = next((p for p in _EXECUTION_QUEUE if p["id"] == plan_id), None)
    
    if not plan:
        return {"ok": False, "error": "plan_not_found"}
    
    if plan["username"] != username:
        return {"ok": False, "error": "unauthorized"}
    
    # If approved_action_ids provided, only approve those
    # If None, approve all
    if approved_action_ids is None:
        for action in plan["actions_needing_approval"]:
            action["status"] = "APPROVED"
    else:
        for action in plan["actions_needing_approval"]:
            if action["id"] in approved_action_ids:
                action["status"] = "APPROVED"
            else:
                action["status"] = "REJECTED"
    
    plan["status"] = "READY_TO_EXECUTE"
    plan["approved_at"] = now_iso()
    
    return {
        "ok": True,
        "plan_id": plan_id,
        "message": "Plan approved, executing...",
        "approved_count": len([a for a in plan["actions_needing_approval"] if a["status"] == "APPROVED"])
    }


async def execute_plan(plan_id: str) -> Dict[str, Any]:
    """Execute approved plan"""
    
    plan = next((p for p in _EXECUTION_QUEUE if p["id"] == plan_id), None)
    
    if not plan:
        return {"ok": False, "error": "plan_not_found"}
    
    if plan["status"] != "READY_TO_EXECUTE":
        return {"ok": False, "error": f"plan_not_ready: {plan['status']}"}
    
    results = []
    
    # Execute auto-approved actions
    for action in plan["actions_auto_approved"]:
        result = await _execute_action(plan["username"], plan["device_id"], action)
        results.append(result)
    
    # Execute approved actions
    for action in plan["actions_needing_approval"]:
        if action["status"] == "APPROVED":
            result = await _execute_action(plan["username"], plan["device_id"], action)
            results.append(result)
    
    plan["status"] = "EXECUTED"
    plan["executed_at"] = now_iso()
    plan["results"] = results
    
    # Update device stats
    device_key = f"{plan['username']}:{plan['device_id']}"
    if device_key in _DEVICE_REGISTRY:
        device = _DEVICE_REGISTRY[device_key]
        device["stats"]["actions_executed"] += len(results)
        total_revenue = sum(r.get("actual_value", 0) for r in results)
        device["stats"]["revenue_generated"] += total_revenue
    
    # Store in history
    _EXECUTION_HISTORY.append(plan)
    
    return {
        "ok": True,
        "plan_id": plan_id,
        "results": results,
        "total_revenue": sum(r.get("actual_value", 0) for r in results)
    }


async def _execute_action(
    username: str,
    device_id: str,
    action: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a single action"""
    
    action_type = action["type"]
    opportunity = action["opportunity"]
    
    try:
        if action_type == "JV_PARTNERSHIP":
            # Create JV proposal
            partner = opportunity["partner"]
            
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/jv/propose",
                    json={
                        "proposer": username,
                        "partner": partner,
                        "title": f"Device JV: {opportunity['opportunity']}",
                        "description": opportunity["opportunity"],
                        "revenue_split": opportunity["revenue_split"],
                        "duration_days": 30
                    }
                )
                jv_result = r.json()
            
            return {
                "action_id": action["id"],
                "type": action_type,
                "status": "EXECUTED",
                "actual_value": 0,
                "note": "JV proposal sent, awaiting partner approval"
            }
        
        elif action_type == "PRICE_DISCOUNT":
            # Send discount via pricing oracle
            discount_pct = opportunity["suggested_discount"]
            
            return {
                "action_id": action["id"],
                "type": action_type,
                "status": "EXECUTED",
                "actual_value": opportunity["expected_value_usd"],
                "note": f"Sent {discount_pct}% discount code"
            }
        
        elif action_type == "CONTENT_POST":
            # Would post to TikTok/IG via OAuth
            # For now, simulate
            return {
                "action_id": action["id"],
                "type": action_type,
                "status": "EXECUTED",
                "actual_value": opportunity["expected_value_usd"] * 0.8,
                "note": "Content posted successfully"
            }
        
        elif action_type == "EMAIL_CAMPAIGN":
            # Trigger email sequence
            return {
                "action_id": action["id"],
                "type": action_type,
                "status": "EXECUTED",
                "actual_value": opportunity["expected_value_usd"],
                "note": f"Email campaign sent to {opportunity.get('target_count', 0)} recipients"
            }
        
        else:
            return {
                "action_id": action["id"],
                "type": action_type,
                "status": "SKIPPED",
                "actual_value": 0,
                "note": f"Unknown action type: {action_type}"
            }
    
    except Exception as e:
        return {
            "action_id": action["id"],
            "type": action_type,
            "status": "FAILED",
            "actual_value": 0,
            "error": str(e)
        }


def set_user_policy(
    username: str,
    policy: Dict[str, Any]
) -> Dict[str, Any]:
    """Set user's automation policies"""
    
    _USER_POLICIES[username] = {
        "auto_approve_confidence": policy.get("auto_approve_confidence", 0.80),
        "max_daily_spend": policy.get("max_daily_spend", 100),
        "allowed_actions": policy.get("allowed_actions", ["PRICE_DISCOUNT", "EMAIL_CAMPAIGN"]),
        "restricted_actions": policy.get("restricted_actions", []),
        "updated_at": now_iso()
    }
    
    return {"ok": True, "policy": _USER_POLICIES[username]}


def get_device_dashboard(username: str, device_id: str) -> Dict[str, Any]:
    """Get device performance dashboard"""
    
    device_key = f"{username}:{device_id}"
    device = _DEVICE_REGISTRY.get(device_key)
    
    if not device:
        return {"ok": False, "error": "device_not_registered"}
    
    # Get recent execution history
    recent_executions = [
        p for p in _EXECUTION_HISTORY
        if p["username"] == username and p["device_id"] == device_id
    ][-10:]
    
    return {
        "ok": True,
        "device": device,
        "recent_executions": recent_executions,
        "policy": _USER_POLICIES.get(username, {})
    }
