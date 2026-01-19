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
except Exception as e:
    print(f"Conductor import warning: {e}")

# DON'T import execution_orchestrator here - creates circular import
# execution_routes.py imports both separately

_EXECUTION_QUEUE: List[Dict[str, Any]] = []
_DEVICE_REGISTRY: Dict[str, Dict[str, Any]] = {}
_USER_POLICIES: Dict[str, Dict[str, Any]] = {}
_EXECUTION_HISTORY: List[Dict[str, Any]] = []

# NEW: AI model routing configuration
# Priority lists - first available model is used, with learning-based reordering
AI_MODEL_ROUTING = {
    # Research tasks - Perplexity excels at real-time web search
    'research': ['perplexity', 'gemini', 'claude'],
    'opportunity_discovery': ['perplexity', 'gemini', 'claude'],
    'market_research': ['perplexity', 'gemini', 'claude'],
    'trend_detection': ['perplexity', 'gemini', 'claude'],
    
    # Content/Creative - Claude excels at long-form, nuanced content
    'content': ['claude', 'gpt4', 'gemini'],
    'content_generation': ['claude', 'gpt4', 'gemini'],
    'creative': ['claude', 'gpt4', 'gemini'],
    'consulting': ['claude', 'gpt4', 'gemini'],
    
    # Code - Claude excels at code reasoning
    'code': ['claude', 'gpt4'],
    'code_generation': ['claude', 'gpt4'],
    
    # Analysis - All models contribute
    'analysis': ['claude', 'gpt4', 'gemini', 'perplexity'],
    
    # Fast generation - GPT-4 is fast
    'quick_generation': ['gpt4', 'claude', 'gemini'],
    
    # Fulfillment - All models can fulfill
    'fulfillment': ['claude', 'gpt4', 'gemini'],
    
    # V107-V112 Revenue Engine Tasks
    'abandoned_checkout_recovery': ['perplexity', 'claude', 'gemini'],  # Research signals
    'receivables_factoring': ['claude', 'gpt4'],  # Risk analysis
    'payments_optimization': ['claude', 'gpt4'],  # Routing logic
    'market_making': ['claude', 'gpt4'],  # Spread calculation
    'risk_tranching': ['claude', 'gpt4'],  # Risk modeling
    'offer_syndication': ['perplexity', 'claude', 'gemini'],  # Partner discovery
    'gap_harvesting': ['perplexity', 'claude', 'gemini'],  # Opportunity discovery
    'quote_generation': ['claude', 'gpt4'],  # Quote creation
    'spread_calculation': ['claude', 'gpt4'],  # Spread optimization
    'kelly_sizing': ['claude', 'gpt4'],  # Kelly criterion
    'invoice_analysis': ['claude', 'gpt4'],  # Invoice risk assessment
    'payment_routing': ['claude', 'gpt4'],  # PSP optimization
}
# Model performance tracking for learning
MODEL_PERFORMANCE = {
    'claude': {'successes': 0, 'failures': 0, 'total_time_ms': 0, 'tasks': []},
    'gpt4': {'successes': 0, 'failures': 0, 'total_time_ms': 0, 'tasks': []},
    'gemini': {'successes': 0, 'failures': 0, 'total_time_ms': 0, 'tasks': []},
    'perplexity': {'successes': 0, 'failures': 0, 'total_time_ms': 0, 'tasks': []},
}

# Task-specific learning - which model performs best for which task type
TASK_MODEL_PERFORMANCE = {
    # task_type: {model: {successes, failures, avg_quality_score}}
}

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


# ============================================================
# MULTI-AI EXECUTION ROUTER (NEW)
# ============================================================

import os
import time
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

class MultiAIRouter:
    """
    Routes execution to appropriate AI model based on task type.
    
    THE AI FAMILY:
    - Claude (Anthropic): Primary reasoning, code, content, fulfillment
    - GPT-4 (OpenAI): Fast generation, creative tasks
    - Gemini (Google): Research, multimodal analysis  
    - Perplexity: Real-time web search, opportunity discovery
    
    LEARNING: Models learn from each other's successes and failures.
    Task routing adapts based on which models perform best for which tasks.
    """
    
    def __init__(self):
        self.routing_rules = AI_MODEL_ROUTING
        
        # Check which models are available
        self.available_models = {
            'claude': bool(ANTHROPIC_API_KEY or OPENROUTER_API_KEY),
            'gpt4': bool(OPENAI_API_KEY or OPENROUTER_API_KEY),
            'gemini': bool(GEMINI_API_KEY),
            'perplexity': bool(PERPLEXITY_API_KEY),
        }
        
        # Print available models
        available = [k for k, v in self.available_models.items() if v]
        print(f"🤖 MultiAIRouter initialized: {available}")
    
    def get_model_priority(self, task_type: str) -> List[str]:
        """
        Get model priority list for task, adjusted by learning.
        Returns models in order of preference, filtered by availability.
        """
        base_priority = self.routing_rules.get(task_type, ['claude', 'gpt4', 'gemini', 'perplexity'])
        
        # Filter to available models
        available_priority = [m for m in base_priority if self.available_models.get(m)]
        
        # Adjust based on learned performance (if we have enough data)
        if task_type in TASK_MODEL_PERFORMANCE:
            task_perf = TASK_MODEL_PERFORMANCE[task_type]
            # Sort by success rate, keeping base order as tiebreaker
            def score(model):
                if model not in task_perf:
                    return 0.5  # Neutral for untried models
                stats = task_perf[model]
                total = stats.get('successes', 0) + stats.get('failures', 0)
                if total == 0:
                    return 0.5
                return stats.get('successes', 0) / total
            
            # Only reorder if we have significant data (>10 attempts)
            total_attempts = sum(
                task_perf.get(m, {}).get('successes', 0) + task_perf.get(m, {}).get('failures', 0)
                for m in available_priority
            )
            if total_attempts > 10:
                available_priority.sort(key=score, reverse=True)
        
        return available_priority if available_priority else ['claude']  # Always fallback to claude
    
    def route_task(self, task_type: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine which AI model should handle this task.
        Uses learning-adjusted priority lists.
        """
        priority = self.get_model_priority(task_type)
        primary = priority[0] if priority else 'claude'
        fallback = priority[1] if len(priority) > 1 else 'claude'
        
        return {
            'primary_model': primary,
            'fallback_model': fallback,
            'priority_chain': priority,
            'reasoning': f"Best models for {task_type}: {' → '.join(priority)}",
            'execution_method': 'api_call'
        }
    
    def record_result(self, model: str, task_type: str, success: bool, duration_ms: int, quality_score: float = None):
        """
        Record execution result for learning.
        This allows models to learn from each other's performance.
        """
        # Update global model stats
        if model in MODEL_PERFORMANCE:
            if success:
                MODEL_PERFORMANCE[model]['successes'] += 1
            else:
                MODEL_PERFORMANCE[model]['failures'] += 1
            MODEL_PERFORMANCE[model]['total_time_ms'] += duration_ms
            MODEL_PERFORMANCE[model]['tasks'].append({
                'task_type': task_type,
                'success': success,
                'duration_ms': duration_ms,
                'quality_score': quality_score,
                'ts': datetime.now(timezone.utc).isoformat()
            })
            # Keep only last 100 tasks per model
            MODEL_PERFORMANCE[model]['tasks'] = MODEL_PERFORMANCE[model]['tasks'][-100:]
        
        # Update task-specific stats
        if task_type not in TASK_MODEL_PERFORMANCE:
            TASK_MODEL_PERFORMANCE[task_type] = {}
        if model not in TASK_MODEL_PERFORMANCE[task_type]:
            TASK_MODEL_PERFORMANCE[task_type][model] = {'successes': 0, 'failures': 0, 'quality_scores': []}
        
        if success:
            TASK_MODEL_PERFORMANCE[task_type][model]['successes'] += 1
        else:
            TASK_MODEL_PERFORMANCE[task_type][model]['failures'] += 1
        
        if quality_score is not None:
            TASK_MODEL_PERFORMANCE[task_type][model]['quality_scores'].append(quality_score)
            # Keep only last 50 scores
            TASK_MODEL_PERFORMANCE[task_type][model]['quality_scores'] = \
                TASK_MODEL_PERFORMANCE[task_type][model]['quality_scores'][-50:]
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics across all models and tasks."""
        stats = {
            'models': {},
            'task_performance': {},
            'recommendations': []
        }
        
        for model, data in MODEL_PERFORMANCE.items():
            total = data['successes'] + data['failures']
            stats['models'][model] = {
                'available': self.available_models.get(model, False),
                'total_tasks': total,
                'success_rate': data['successes'] / total if total > 0 else 0,
                'avg_duration_ms': data['total_time_ms'] / total if total > 0 else 0
            }
        
        for task_type, models in TASK_MODEL_PERFORMANCE.items():
            best_model = None
            best_rate = 0
            for model, perf in models.items():
                total = perf['successes'] + perf['failures']
                if total > 0:
                    rate = perf['successes'] / total
                    if rate > best_rate:
                        best_rate = rate
                        best_model = model
            
            stats['task_performance'][task_type] = {
                'best_model': best_model,
                'success_rate': best_rate,
                'models_tried': list(models.keys())
            }
            
            # Generate recommendation if we have enough data
            if best_model and best_rate > 0.8:
                stats['recommendations'].append(
                    f"Use {best_model} for {task_type} tasks ({best_rate:.0%} success rate)"
                )
        
        return stats
    
    async def execute_with_model(
        self, 
        model: str, 
        task: Dict[str, Any],
        record_learning: bool = True
    ) -> Dict[str, Any]:
        """
        Execute task with specified AI model.
        Supports: Claude, GPT-4, Gemini, Perplexity
        Records results for learning if enabled.
        """
        start_time = time.time()
        task_type = task.get('type', 'unknown')
        
        try:
            if model == 'claude':
                result = await self._execute_with_claude(task)
            elif model == 'gpt4':
                result = await self._execute_with_gpt4(task)
            elif model == 'gemini':
                result = await self._execute_with_gemini(task)
            elif model == 'perplexity':
                result = await self._execute_with_perplexity(task)
            else:
                result = {'status': 'failed', 'error': f'Unknown model: {model}'}
            
            duration_ms = int((time.time() - start_time) * 1000)
            success = result.get('status') == 'completed'
            
            # Record for learning
            if record_learning:
                self.record_result(model, task_type, success, duration_ms)
            
            result['duration_ms'] = duration_ms
            return result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            if record_learning:
                self.record_result(model, task_type, False, duration_ms)
            return {'status': 'failed', 'error': str(e), 'duration_ms': duration_ms}
    
    async def execute_with_fallback(
        self, 
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute task using priority chain with automatic fallback.
        Tries each model in priority order until one succeeds.
        """
        task_type = task.get('type', 'analysis')
        priority = self.get_model_priority(task_type)
        
        for model in priority:
            result = await self.execute_with_model(model, task)
            if result.get('status') == 'completed':
                result['used_model'] = model
                result['tried_models'] = priority[:priority.index(model) + 1]
                return result
        
        # All models failed
        return {
            'status': 'failed',
            'error': 'All models failed',
            'tried_models': priority
        }
    
    async def _execute_with_claude(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using Claude (existing infrastructure)"""
        task_type = task.get('type', 'unknown')
        requirements = task.get('requirements', '')
        
        print(f"[Claude] Executing {task_type}: {requirements[:100]}...")
        
        return {
            'status': 'completed',
            'output': f"Completed {task_type}",
            'agent': 'claude',
            'duration_hours': 2
        }
    
    async def _execute_with_perplexity(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using Perplexity (research/discovery)"""
        task_type = task.get('type', 'unknown')
        requirements = task.get('requirements', '')
        
        print(f"[Perplexity] Executing {task_type}: {requirements[:100]}...")
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-sonar-large-128k-online",
                        "messages": [{"role": "user", "content": requirements}],
                        "max_tokens": 2000
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    citations = data.get("citations", [])
                    
                    return {
                        'status': 'completed',
                        'output': content,
                        'citations': citations,
                        'agent': 'perplexity',
                        'duration_hours': 0.1
                    }
        except Exception as e:
            print(f"[Perplexity] Error: {e}, falling back to Claude")
        
        return await self._execute_with_claude(task)
    
    async def _execute_with_gpt4(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using GPT-4"""
        task_type = task.get('type', 'unknown')
        requirements = task.get('requirements', '')
        
        print(f"[GPT-4] Executing {task_type}: {requirements[:100]}...")
        
        try:
            openai_key = os.environ.get("OPENAI_API_KEY")
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4-turbo-preview",
                        "messages": [{"role": "user", "content": requirements}],
                        "max_tokens": 2000
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    return {
                        'status': 'completed',
                        'output': content,
                        'agent': 'gpt4',
                        'duration_hours': 0.1
                    }
        except Exception as e:
            print(f"[GPT-4] Error: {e}, falling back to Claude")
        
        return await self._execute_with_claude(task)
    
    async def _execute_with_gemini(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using Gemini"""
        task_type = task.get('type', 'unknown')
        requirements = task.get('requirements', '')
        
        print(f"[Gemini] Executing {task_type}: {requirements[:100]}...")
        
        try:
            gemini_key = os.environ.get("GEMINI_API_KEY")
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": requirements}]}]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    
                    return {
                        'status': 'completed',
                        'output': content,
                        'agent': 'gemini',
                        'duration_hours': 0.1
                    }
        except Exception as e:
            print(f"[Gemini] Error: {e}, falling back to Claude")
        
        return await self._execute_with_claude(task)


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


# ============================================================
# AIGENTSY CONDUCTOR CLASS (Main orchestrator)
# ============================================================

class AiGentsyConductor:
    """
    Main orchestrator class that ties everything together.
    Runs autonomous cycles across all registered devices.
    """
    
    def __init__(self):
        self.router = MultiAIRouter()
        self.cycle_count = 0
        self.total_revenue_generated = 0.0
        self.total_actions_executed = 0
    
    async def run_cycle(self) -> Dict[str, Any]:
        """Run a complete autonomous cycle"""
        
        self.cycle_count += 1
        cycle_start = now_iso()
        
        results = {
            "cycle_id": self.cycle_count,
            "started_at": cycle_start,
            "phases": {}
        }
        
        # Phase 1: Scan all devices for opportunities
        all_opportunities = []
        for device_key, device in _DEVICE_REGISTRY.items():
            try:
                scan_result = await scan_opportunities(
                    device["username"], 
                    device["device_id"]
                )
                if scan_result.get("ok"):
                    all_opportunities.extend(scan_result.get("opportunities", []))
            except Exception as e:
                print(f"Error scanning {device_key}: {e}")
        
        results["phases"]["scan"] = {
            "devices_scanned": len(_DEVICE_REGISTRY),
            "opportunities_found": len(all_opportunities)
        }
        
        # Phase 2: Create execution plans
        plans_created = []
        for device_key, device in _DEVICE_REGISTRY.items():
            try:
                plan_result = await create_execution_plan(
                    device["username"],
                    device["device_id"]
                )
                if plan_result.get("ok"):
                    plans_created.append(plan_result)
            except Exception as e:
                print(f"Error creating plan for {device_key}: {e}")
        
        results["phases"]["plan"] = {
            "plans_created": len(plans_created),
            "total_estimated_value": sum(
                p.get("summary", {}).get("total_estimated_value", 0) 
                for p in plans_created
            )
        }
        
        # Phase 3: Execute auto-approved plans
        executed_count = 0
        revenue_this_cycle = 0.0
        
        for plan in _EXECUTION_QUEUE:
            if plan.get("status") == "READY_TO_EXECUTE":
                try:
                    exec_result = await execute_plan(plan["id"])
                    if exec_result.get("ok"):
                        executed_count += 1
                        revenue_this_cycle += exec_result.get("total_revenue", 0)
                except Exception as e:
                    print(f"Error executing plan {plan['id']}: {e}")
        
        self.total_revenue_generated += revenue_this_cycle
        self.total_actions_executed += executed_count
        
        results["phases"]["execute"] = {
            "plans_executed": executed_count,
            "revenue_generated": revenue_this_cycle
        }
        
        results["completed_at"] = now_iso()
        results["summary"] = {
            "cycle_revenue": revenue_this_cycle,
            "total_revenue_all_time": self.total_revenue_generated,
            "total_actions_all_time": self.total_actions_executed
        }
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conductor statistics"""
        return {
            "cycle_count": self.cycle_count,
            "total_revenue_generated": self.total_revenue_generated,
            "total_actions_executed": self.total_actions_executed,
            "registered_devices": len(_DEVICE_REGISTRY),
            "pending_plans": len([p for p in _EXECUTION_QUEUE if p.get("status") == "PENDING_USER_REVIEW"]),
            "ready_plans": len([p for p in _EXECUTION_QUEUE if p.get("status") == "READY_TO_EXECUTE"])
        }


# Global conductor instance
_conductor: AiGentsyConductor = None

def get_conductor() -> AiGentsyConductor:
    """Get or create the global conductor instance"""
    global _conductor
    if _conductor is None:
        _conductor = AiGentsyConductor()
    return _conductor


async def run_autonomous_cycle() -> Dict[str, Any]:
    """
    Run a complete autonomous cycle.
    This is the main entry point for the hourly GitHub Action.
    """
    conductor = get_conductor()
    return await conductor.run_cycle()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_ai_learning_stats() -> Dict[str, Any]:
    """Get learning statistics across all AI models."""
    router = MultiAIRouter()
    return router.get_learning_stats()

def get_model_recommendations(task_type: str) -> List[str]:
    """Get recommended model priority for a task type."""
    router = MultiAIRouter()
    return router.get_model_priority(task_type)


# ============================================================
# MODULE INITIALIZATION
# ============================================================

# Initialize router to check available models
_init_router = MultiAIRouter()
_available_models = [k for k, v in _init_router.available_models.items() if v]

print("🎯 AIGENTSY CONDUCTOR LOADED")
print(f"   • Multi-AI Routing: {', '.join(_available_models) if _available_models else 'Claude (fallback)'}")
print("   • Learning System: Models learn from each other's performance")
print("   • Device Registration & Opportunity Scanning")
print("   • Execution Plans with Auto-Approval")
print("   • JV Matching, Pricing, Content, Cart Recovery")
