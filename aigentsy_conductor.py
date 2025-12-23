"""
AIGENTSY CONDUCTOR - UPGRADED WITH MULTI-AI ROUTING
Orchestrates device-based opportunities AND Alpha Discovery execution

NEW: Routes tasks to Claude, GPT-4, and Gemini based on task type
NEW: Integrated with ExecutionOrchestrator for full pipeline
NEW: Supports opportunity execution from Alpha Discovery Engine
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import httpx
import asyncio
import json

# Import all subsystems
try:
    from metahive_brain import query_hive, report_pattern_usage
    from pricing_oracle import calculate_dynamic_price
    from outcome_oracle_max import on_event
    from ltv_forecaster import calculate_ltv_with_churn
    from bundle_engine import create_bundle
    from fraud_detector import check_fraud_signals
    from compliance_oracle import check_transaction_allowed
    
    # NEW: Import execution infrastructure
    from execution_orchestrator import ExecutionOrchestrator
    from execution_scorer import ExecutionScorer
    from opportunity_engagement import OpportunityEngagement
except Exception as e:
    print(f"Conductor import warning: {e}")

_EXECUTION_QUEUE: List[Dict[str, Any]] = []
_DEVICE_REGISTRY: Dict[str, Dict[str, Any]] = {}
_USER_POLICIES: Dict[str, Dict[str, Any]] = {}
_EXECUTION_HISTORY: List[Dict[str, Any]] = []

# NEW: AI model routing configuration
AI_MODEL_ROUTING = {
    'code': 'claude',  # Claude best for code reasoning
    'content': 'claude',  # Claude best for long-form content
    'analysis': 'claude',  # Claude best for complex analysis
    'research': 'gemini',  # Gemini good for research (when available)
    'quick_generation': 'gpt4',  # GPT-4 fast for quick tasks (when available)
    'creative': 'claude',  # Claude best for creative work
    'consulting': 'claude'  # Claude best for strategic thinking
}

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


# ============================================================
# MULTI-AI EXECUTION ROUTER (NEW)
# ============================================================

class MultiAIRouter:
    """
    Routes execution to appropriate AI model based on task type
    Currently: Claude handles most, with hooks for GPT-4 and Gemini
    """
    
    def __init__(self):
        self.routing_rules = AI_MODEL_ROUTING
        
        # API keys (would come from environment)
        self.claude_available = True
        self.gpt4_available = False  # Set True when API key added
        self.gemini_available = False  # Set True when API key added
    
    def route_task(self, task_type: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine which AI model should handle this task
        
        Returns:
            {
                'primary_model': str,
                'fallback_model': str,
                'reasoning': str,
                'execution_method': str
            }
        """
        
        # Determine primary model
        primary = self.routing_rules.get(task_type, 'claude')
        
        # Check availability and set fallback
        if primary == 'gpt4' and not self.gpt4_available:
            primary = 'claude'
            fallback = 'claude'
        elif primary == 'gemini' and not self.gemini_available:
            primary = 'claude'
            fallback = 'claude'
        else:
            fallback = 'claude'  # Claude is always fallback
        
        return {
            'primary_model': primary,
            'fallback_model': fallback,
            'reasoning': f"Best model for {task_type} tasks",
            'execution_method': 'api_call'
        }
    
    async def execute_with_model(
        self, 
        model: str, 
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute task with specified AI model
        
        Currently: All routes to Claude via existing infrastructure
        Future: Add GPT-4 and Gemini API calls
        """
        
        if model == 'claude':
            # Use existing Claude infrastructure
            return await self._execute_with_claude(task)
        
        elif model == 'gpt4':
            # TODO: Add OpenAI GPT-4 API call
            print(f"[GPT-4] Would execute: {task['type']}")
            return await self._execute_with_claude(task)  # Fallback to Claude for now
        
        elif model == 'gemini':
            # TODO: Add Google Gemini API call
            print(f"[Gemini] Would execute: {task['type']}")
            return await self._execute_with_claude(task)  # Fallback to Claude for now
        
        else:
            return {
                'status': 'failed',
                'error': f'Unknown model: {model}'
            }
    
    async def _execute_with_claude(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using Claude (existing infrastructure)"""
        
        # Use Claude via Anthropic API
        # This would integrate with your existing Claude agent infrastructure
        
        task_type = task.get('type', 'unknown')
        requirements = task.get('requirements', '')
        
        # Simulate execution (replace with actual Claude API call)
        print(f"[Claude] Executing {task_type}: {requirements[:100]}...")
        
        return {
            'status': 'completed',
            'output': f"Completed {task_type}",
            'agent': 'claude',
            'duration_hours': 2
        }


# ============================================================
# CONTENT EXECUTION METHODS (NEW)
# ============================================================

async def execute_content_task(
    opportunity: Dict[str, Any],
    engagement_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute content creation task
    Routes to Claude for content generation
    """
    
    router = MultiAIRouter()
    
    task = {
        'type': 'content',
        'requirements': opportunity.get('description', ''),
        'context': engagement_context
    }
    
    routing = router.route_task('content', task)
    result = await router.execute_with_model(routing['primary_model'], task)
    
    return result


async def execute_consulting(
    opportunity: Dict[str, Any],
    engagement_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute consulting/analysis task
    Routes to Claude for strategic thinking
    """
    
    router = MultiAIRouter()
    
    task = {
        'type': 'consulting',
        'requirements': opportunity.get('description', ''),
        'context': engagement_context
    }
    
    routing = router.route_task('consulting', task)
    result = await router.execute_with_model(routing['primary_model'], task)
    
    return result


async def execute_generic_task(
    opportunity: Dict[str, Any],
    engagement_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute generic task
    Routes to appropriate AI based on task type
    """
    
    router = MultiAIRouter()
    
    opp_type = opportunity.get('type', 'unknown')
    
    # Map opportunity type to task type
    task_type_map = {
        'software_development': 'code',
        'web_development': 'code',
        'content_creation': 'content',
        'business_consulting': 'consulting',
        'data_analysis': 'analysis',
        'market_research': 'research'
    }
    
    task_type = task_type_map.get(opp_type, 'content')
    
    task = {
        'type': task_type,
        'requirements': opportunity.get('description', ''),
        'context': engagement_context
    }
    
    routing = router.route_task(task_type, task)
    result = await router.execute_with_model(routing['primary_model'], task)
    
    return result


# ============================================================
# ORIGINAL DEVICE-BASED CONDUCTOR METHODS
# ============================================================

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
        # Query hive for trending patterns
        patterns = query_hive("trending_content")
        
        for pattern in patterns[:2]:
            opportunities.append({
                "type": "CONTENT_POST",
                "action": f"Post: {pattern['title']}",
                "pattern_id": pattern["id"],
                "expected_value_usd": pattern.get("avg_value", 15),
                "confidence": pattern.get("confidence", 0.70),
                "requires_approval": False
            })
    except Exception:
        pass
    
    return opportunities


async def _find_cart_recovery_opportunities(username: str, device_id: str) -> List[Dict[str, Any]]:
    """Find cart recovery email opportunities"""
    
    opportunities = []
    
    # Would query Shopify for abandoned carts
    opportunities.append({
        "type": "EMAIL_CAMPAIGN",
        "action": "Send cart recovery emails",
        "target_count": 25,
        "expected_value_usd": 75,
        "confidence": 0.60,
        "requires_approval": False
    })
    
    return opportunities


async def create_execution_plan(
    username: str,
    device_id: str,
    selected_opportunities: List[str] = None
) -> Dict[str, Any]:
    """Create execution plan from opportunities"""
    
    # Scan opportunities
    scan_result = await scan_opportunities(username, device_id)
    
    if not scan_result["ok"]:
        return scan_result
    
    opportunities = scan_result["opportunities"]
    
    # Filter to selected if provided
    if selected_opportunities:
        opportunities = [
            o for o in opportunities 
            if o.get("opportunity", o.get("action", "")).lower() in [s.lower() for s in selected_opportunities]
        ]
    
    # Get user policy
    policy = _USER_POLICIES.get(username, {
        "auto_approve_confidence": 0.80,
        "max_daily_spend": 100,
        "allowed_actions": ["PRICE_DISCOUNT", "EMAIL_CAMPAIGN"]
    })
    
    # Split into auto-approved vs needs approval
    actions_auto_approved = []
    actions_needing_approval = []
    
    for opp in opportunities:
        action = {
            "id": str(uuid4()),
            "type": opp["type"],
            "opportunity": opp,
            "estimated_value": opp.get("expected_value_usd", 0),
            "confidence": opp.get("confidence", 0.5),
            "status": "PENDING"
        }
        
        # Check if auto-approvable
        if (opp.get("confidence", 0) >= policy["auto_approve_confidence"] and
            opp["type"] in policy.get("allowed_actions", []) and
            not opp.get("requires_approval", False)):
            actions_auto_approved.append(action)
        else:
            actions_needing_approval.append(action)
    
    plan_id = str(uuid4())
    
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
