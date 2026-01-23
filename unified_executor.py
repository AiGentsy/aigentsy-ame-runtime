"""
═══════════════════════════════════════════════════════════════════════════════
UNIFIED EXECUTOR - Single Entry Point for All Execution
═══════════════════════════════════════════════════════════════════════════════

UNIFIES THREE SYSTEMS INTO ONE:
1. Connector Registry - API integrations (Stripe, Shopify, Twitter, etc.)
2. Multi-AI Router - AI Family (Claude, GPT-4, Gemini, Perplexity, Grok)
3. Universal Fabric - Browser automation (Playwright + AI vision)

SINGLE ENTRY POINT:
    from unified_executor import execute, UnifiedExecutor

    # Simple execution
    result = await execute({
        "type": "content_generation",
        "prompt": "Write a sales email",
        "platform": "email"
    })

    # Or use the executor directly
    executor = UnifiedExecutor()
    result = await executor.execute(task)

DECISION TREE:
1. Is this an API task? → Route to Connector Registry
2. Is this an AI task? → Route to Multi-AI Router
3. Is this a browser task? → Route to Universal Fabric
4. Fallback chains if primary fails

ROUTING LOGIC:
- Stripe/Shopify/Email → Connector Registry
- Content/Code/Analysis → Multi-AI Router
- Upwork/Fiverr/HackerNews (no API) → Universal Fabric
- Mixed tasks → Hybrid execution (AI generates, Fabric executes)

Updated: Jan 2026
═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import asyncio
import os
import logging

logger = logging.getLogger("unified_executor")


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTION METHOD CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

class ExecutionMethod(Enum):
    """How a task should be executed"""
    API = "api"              # Direct API call via Connector
    AI = "ai"                # AI generation via Router
    BROWSER = "browser"      # Browser automation via Fabric
    HYBRID = "hybrid"        # AI + Browser combination
    MANUAL = "manual"        # Requires human intervention


# Task type to execution method mapping
TASK_ROUTING = {
    # API-based tasks (Connector Registry)
    "payment": ExecutionMethod.API,
    "invoice": ExecutionMethod.API,
    "email_send": ExecutionMethod.API,
    "sms_send": ExecutionMethod.API,
    "slack_message": ExecutionMethod.API,
    "shopify_order": ExecutionMethod.API,
    "stripe_charge": ExecutionMethod.API,
    "webhook_call": ExecutionMethod.API,

    # AI-based tasks (Multi-AI Router)
    "content_generation": ExecutionMethod.AI,
    "code_generation": ExecutionMethod.AI,
    "analysis": ExecutionMethod.AI,
    "research": ExecutionMethod.AI,
    "translation": ExecutionMethod.AI,
    "summarization": ExecutionMethod.AI,
    "conversation": ExecutionMethod.AI,
    "social_intelligence": ExecutionMethod.AI,
    "trending_detection": ExecutionMethod.AI,

    # Browser-based tasks (Universal Fabric)
    "upwork_proposal": ExecutionMethod.BROWSER,
    "fiverr_gig": ExecutionMethod.BROWSER,
    "hackernews_post": ExecutionMethod.BROWSER,
    "reddit_post": ExecutionMethod.BROWSER,
    "linkedin_post": ExecutionMethod.BROWSER,
    "twitter_post": ExecutionMethod.BROWSER,
    "form_submission": ExecutionMethod.BROWSER,
    "web_scrape": ExecutionMethod.BROWSER,

    # Hybrid tasks (AI generates, Fabric executes)
    "proposal_submission": ExecutionMethod.HYBRID,
    "cold_outreach": ExecutionMethod.HYBRID,
    "job_application": ExecutionMethod.HYBRID,
}

# Platform to connector mapping
PLATFORM_CONNECTORS = {
    "stripe": "stripe_connector",
    "shopify": "shopify_connector",
    "email": "email_connector",
    "resend": "email_connector",
    "twilio": "sms_connector",
    "sms": "sms_connector",
    "slack": "slack_connector",
    "airtable": "airtable_connector",
    "github": "github_connector",
    "webhook": "http_generic",
}

# Platforms requiring browser automation
BROWSER_PLATFORMS = {
    "upwork", "fiverr", "toptal", "freelancer",
    "hackernews", "reddit", "linkedin", "twitter",
    "instagram", "facebook", "tiktok", "youtube",
    "indeed", "glassdoor", "angellist"
}


@dataclass
class ExecutionResult:
    """Unified execution result"""
    task_id: str
    ok: bool
    method: str  # api, ai, browser, hybrid
    output: Any = None
    executor: str = ""  # Which system handled it
    execution_time_ms: int = 0
    cost: float = 0.0
    error: str = ""
    fallback_used: bool = False
    metadata: Dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED EXECUTOR CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedExecutor:
    """
    Single entry point for all execution needs.

    Automatically routes tasks to the best execution method:
    - Connector Registry for API tasks
    - Multi-AI Router for AI tasks
    - Universal Fabric for browser tasks
    """

    def __init__(self):
        self._connector_registry = None
        self._ai_router = None
        self._fabric = None
        self._execution_log: List[Dict] = []

        # Lazy load subsystems
        self._init_subsystems()

    def _init_subsystems(self):
        """Initialize subsystems (lazy load to avoid circular imports)"""
        # Connector Registry
        try:
            from connectors.registry import get_connector
            self._get_connector = get_connector
            self._connectors_available = True
        except ImportError:
            self._connectors_available = False
            logger.warning("Connector registry not available")

        # Multi-AI Router
        try:
            from aigentsy_conductor import MultiAIRouter
            self._ai_router = MultiAIRouter()
            self._ai_available = True
        except ImportError:
            self._ai_available = False
            logger.warning("Multi-AI router not available")

        # Universal Fabric
        try:
            from universal_fulfillment_fabric import execute_universal, get_fabric_status
            self._execute_fabric = execute_universal
            self._fabric_status = get_fabric_status
            self._fabric_available = True
        except ImportError:
            self._fabric_available = False
            logger.warning("Universal Fabric not available")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _classify_task(self, task: Dict) -> ExecutionMethod:
        """Determine the best execution method for a task"""
        task_type = task.get("type", "").lower()
        platform = task.get("platform", "").lower()

        # Check explicit routing
        if task_type in TASK_ROUTING:
            return TASK_ROUTING[task_type]

        # Check platform-based routing
        if platform in PLATFORM_CONNECTORS:
            return ExecutionMethod.API
        if platform in BROWSER_PLATFORMS:
            return ExecutionMethod.BROWSER

        # Check for URL-based tasks
        if task.get("url") and not task.get("api_endpoint"):
            return ExecutionMethod.BROWSER

        # Default to AI for content/generation tasks
        if any(kw in task_type for kw in ["generate", "write", "create", "analyze", "research"]):
            return ExecutionMethod.AI

        # Fallback to AI
        return ExecutionMethod.AI

    async def execute(self, task: Dict) -> ExecutionResult:
        """
        Execute a task using the best available method.

        Args:
            task: Task specification with:
                - type: Task type (e.g., "content_generation")
                - platform: Target platform (e.g., "stripe", "upwork")
                - prompt: For AI tasks
                - url: For browser tasks
                - data: For API tasks
                - max_cost: Maximum cost limit

        Returns:
            ExecutionResult with output and metadata
        """
        task_id = task.get("task_id") or f"unified_{uuid4().hex[:12]}"
        start_time = datetime.now(timezone.utc)

        # Classify the task
        method = self._classify_task(task)

        # Execute based on method
        result = None
        fallback_used = False

        try:
            if method == ExecutionMethod.API:
                result = await self._execute_api(task)
            elif method == ExecutionMethod.AI:
                result = await self._execute_ai(task)
            elif method == ExecutionMethod.BROWSER:
                result = await self._execute_browser(task)
            elif method == ExecutionMethod.HYBRID:
                result = await self._execute_hybrid(task)
            else:
                result = {"ok": False, "error": "Manual execution required"}

            # If primary method failed, try fallback chain
            if not result.get("ok"):
                fallback_result = await self._execute_fallback(task, method)
                if fallback_result.get("ok"):
                    result = fallback_result
                    fallback_used = True

        except Exception as e:
            result = {"ok": False, "error": str(e)}

        # Calculate execution time
        execution_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

        # Build result
        exec_result = ExecutionResult(
            task_id=task_id,
            ok=result.get("ok", False),
            method=method.value,
            output=result.get("output") or result.get("content") or result.get("result"),
            executor=result.get("executor", method.value),
            execution_time_ms=execution_time_ms,
            cost=result.get("cost", 0),
            error=result.get("error", ""),
            fallback_used=fallback_used,
            metadata={
                "task_type": task.get("type"),
                "platform": task.get("platform"),
                "provider": result.get("provider"),
                "timestamp": self._now()
            }
        )

        # Log execution
        self._execution_log.append({
            "task_id": task_id,
            "method": method.value,
            "ok": exec_result.ok,
            "execution_time_ms": execution_time_ms,
            "timestamp": self._now()
        })

        return exec_result

    async def _execute_api(self, task: Dict) -> Dict[str, Any]:
        """Execute via Connector Registry"""
        if not self._connectors_available:
            return {"ok": False, "error": "Connectors not available"}

        platform = task.get("platform", "").lower()
        connector_name = PLATFORM_CONNECTORS.get(platform)

        if not connector_name:
            return {"ok": False, "error": f"No connector for platform: {platform}"}

        try:
            connector = self._get_connector(connector_name)
            if not connector:
                return {"ok": False, "error": f"Connector not found: {connector_name}"}

            # Execute via connector
            result = await connector.execute(task.get("data", {}))
            return {
                "ok": result.get("success", False),
                "output": result.get("result"),
                "executor": connector_name
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _execute_ai(self, task: Dict) -> Dict[str, Any]:
        """Execute via Multi-AI Router"""
        if not self._ai_available:
            return {"ok": False, "error": "AI Router not available"}

        task_type = task.get("type", "general")
        prompt = task.get("prompt", task.get("content", ""))

        try:
            # Route to best AI model
            routing = self._ai_router.route_task(task_type, {"requirements": prompt})
            primary_model = routing.get("primary_model", "claude")

            # Execute with the router
            result = await self._ai_router.execute_with_model(
                model=primary_model,
                task={
                    "type": task_type,
                    "requirements": prompt
                }
            )

            return {
                "ok": result.get("status") == "completed",
                "output": result.get("output"),
                "executor": f"ai/{primary_model}",
                "provider": primary_model
            }
        except Exception as e:
            # Try direct API call as fallback
            return await self._fallback_ai_call(task)

    async def _fallback_ai_call(self, task: Dict) -> Dict[str, Any]:
        """Direct AI API call as fallback"""
        try:
            import httpx
            prompt = task.get("prompt", task.get("content", ""))

            # Try OpenRouter first
            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            if openrouter_key:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {openrouter_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "openai/gpt-4o-mini",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 2000
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return {"ok": True, "output": content, "executor": "ai/openrouter"}

            return {"ok": False, "error": "No AI API available"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _execute_browser(self, task: Dict) -> Dict[str, Any]:
        """Execute via Universal Fabric"""
        if not self._fabric_available:
            return {"ok": False, "error": "Universal Fabric not available", "queued": True}

        url = task.get("url")
        pdl_name = task.get("pdl_name") or f"{task.get('platform', 'web')}.{task.get('action', 'execute')}"

        if not url:
            return {"ok": False, "error": "URL required for browser execution"}

        try:
            result = await self._execute_fabric(
                pdl_name=pdl_name,
                url=url,
                data=task.get("data", {}),
                ev_estimate=task.get("ev_estimate", 0),
                dry_run=task.get("dry_run", False)
            )

            return {
                "ok": result.get("ok", False),
                "output": result.get("verification", {}),
                "executor": "browser/fabric",
                "execution_id": result.get("execution_id"),
                "steps_executed": result.get("steps_executed", 0)
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "queued": True}

    async def _execute_hybrid(self, task: Dict) -> Dict[str, Any]:
        """Execute hybrid task: AI generates content, Fabric executes"""
        # Step 1: Generate content with AI
        ai_result = await self._execute_ai({
            "type": task.get("ai_type", "content_generation"),
            "prompt": task.get("prompt")
        })

        if not ai_result.get("ok"):
            return ai_result

        # Step 2: Execute with Fabric
        generated_content = ai_result.get("output", "")

        browser_task = {
            **task,
            "data": {
                **task.get("data", {}),
                "generated_content": generated_content
            }
        }

        browser_result = await self._execute_browser(browser_task)

        return {
            "ok": browser_result.get("ok", False),
            "output": {
                "ai_generated": generated_content[:500] + "..." if len(generated_content) > 500 else generated_content,
                "browser_result": browser_result.get("output")
            },
            "executor": "hybrid/ai+fabric",
            "execution_id": browser_result.get("execution_id")
        }

    async def _execute_fallback(self, task: Dict, failed_method: ExecutionMethod) -> Dict[str, Any]:
        """Execute fallback chain when primary method fails"""
        fallback_order = {
            ExecutionMethod.API: [ExecutionMethod.AI, ExecutionMethod.BROWSER],
            ExecutionMethod.AI: [ExecutionMethod.BROWSER],
            ExecutionMethod.BROWSER: [ExecutionMethod.AI],
            ExecutionMethod.HYBRID: [ExecutionMethod.AI, ExecutionMethod.BROWSER]
        }

        for fallback_method in fallback_order.get(failed_method, []):
            try:
                if fallback_method == ExecutionMethod.API:
                    result = await self._execute_api(task)
                elif fallback_method == ExecutionMethod.AI:
                    result = await self._execute_ai(task)
                elif fallback_method == ExecutionMethod.BROWSER:
                    result = await self._execute_browser(task)
                else:
                    continue

                if result.get("ok"):
                    result["fallback_method"] = fallback_method.value
                    return result
            except Exception:
                continue

        return {"ok": False, "error": "All fallback methods failed"}

    def get_status(self) -> Dict[str, Any]:
        """Get unified executor status"""
        fabric_status = {}
        if self._fabric_available:
            try:
                fabric_status = self._fabric_status()
            except:
                pass

        return {
            "ok": True,
            "subsystems": {
                "connectors_available": self._connectors_available,
                "ai_router_available": self._ai_available,
                "fabric_available": self._fabric_available
            },
            "fabric": fabric_status,
            "execution_log_size": len(self._execution_log),
            "recent_executions": self._execution_log[-10:]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

_executor: Optional[UnifiedExecutor] = None


def get_executor() -> UnifiedExecutor:
    """Get or create the global unified executor"""
    global _executor
    if _executor is None:
        _executor = UnifiedExecutor()
    return _executor


async def execute(task: Dict) -> ExecutionResult:
    """
    Execute a task using the unified executor.

    This is the main entry point for all execution needs.

    Usage:
        result = await execute({
            "type": "content_generation",
            "prompt": "Write a professional email",
            "platform": "email"
        })
    """
    return await get_executor().execute(task)


async def execute_ai(prompt: str, task_type: str = "content_generation") -> Dict[str, Any]:
    """Quick function to execute an AI task"""
    result = await execute({
        "type": task_type,
        "prompt": prompt
    })
    return {
        "ok": result.ok,
        "output": result.output,
        "error": result.error
    }


async def execute_browser(url: str, platform: str, data: Dict = None) -> Dict[str, Any]:
    """Quick function to execute a browser task"""
    result = await execute({
        "type": "browser_automation",
        "platform": platform,
        "url": url,
        "data": data or {}
    })
    return {
        "ok": result.ok,
        "output": result.output,
        "error": result.error
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, HTTPException, Body

unified_router = APIRouter(prefix="/unified", tags=["Unified Executor"])


@unified_router.post("/execute")
async def execute_task_endpoint(body: Dict = Body(...)):
    """
    Execute any task via the unified executor.

    Body:
        type: Task type (content_generation, code_generation, browser_automation, etc.)
        platform: Target platform (stripe, upwork, email, etc.)
        prompt: For AI tasks
        url: For browser tasks
        data: For API tasks
        max_cost: Maximum cost limit
    """
    executor = get_executor()
    result = await executor.execute(body)

    return {
        "ok": result.ok,
        "task_id": result.task_id,
        "method": result.method,
        "output": result.output,
        "executor": result.executor,
        "execution_time_ms": result.execution_time_ms,
        "cost": result.cost,
        "error": result.error if not result.ok else None,
        "fallback_used": result.fallback_used
    }


@unified_router.get("/status")
async def executor_status():
    """Get unified executor status"""
    return get_executor().get_status()


@unified_router.post("/ai")
async def quick_ai_endpoint(body: Dict = Body(...)):
    """Quick AI execution endpoint"""
    prompt = body.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt required")

    return await execute_ai(
        prompt=prompt,
        task_type=body.get("type", "content_generation")
    )


@unified_router.post("/browser")
async def quick_browser_endpoint(body: Dict = Body(...)):
    """Quick browser execution endpoint"""
    url = body.get("url")
    platform = body.get("platform")

    if not url:
        raise HTTPException(status_code=400, detail="url required")
    if not platform:
        raise HTTPException(status_code=400, detail="platform required")

    return await execute_browser(
        url=url,
        platform=platform,
        data=body.get("data", {})
    )


def include_unified_endpoints(app):
    """Include unified executor endpoints in FastAPI app"""
    app.include_router(unified_router)

    executor = get_executor()
    status = executor.get_status()

    print("=" * 80)
    print("⚡ UNIFIED EXECUTOR LOADED - Single Entry Point for All Execution")
    print("=" * 80)
    print(f"Connectors: {'Available' if status['subsystems']['connectors_available'] else 'Not available'}")
    print(f"AI Router:  {'Available' if status['subsystems']['ai_router_available'] else 'Not available'}")
    print(f"Fabric:     {'Available' if status['subsystems']['fabric_available'] else 'Not available'}")
    print("Endpoints:")
    print("  POST /unified/execute  - Execute any task")
    print("  GET  /unified/status   - Executor status")
    print("  POST /unified/ai       - Quick AI execution")
    print("  POST /unified/browser  - Quick browser execution")
    print("=" * 80)


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Main functions
    "execute",
    "execute_ai",
    "execute_browser",
    "get_executor",

    # Classes
    "UnifiedExecutor",
    "ExecutionMethod",
    "ExecutionResult",

    # FastAPI integration
    "unified_router",
    "include_unified_endpoints",

    # Constants
    "TASK_ROUTING",
    "PLATFORM_CONNECTORS",
    "BROWSER_PLATFORMS"
]
