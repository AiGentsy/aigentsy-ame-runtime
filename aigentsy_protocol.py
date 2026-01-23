"""
═══════════════════════════════════════════════════════════════════════════════
AIGENTSY THIN FILM PROTOCOL
═══════════════════════════════════════════════════════════════════════════════

THE TCP/IP OF AI COLLABORATION

A lightweight protocol that ANY AI can use to:
1. register() - Join the AiGentsy mesh
2. execute() - Run tasks (routes to best AI automatically)
3. search_mesh() - Find collaborators for complex tasks
4. settle() - Automatic payment via AIGx Protocol

DESIGN PRINCIPLES:
- Minimal dependencies (just httpx for HTTP calls)
- Self-routing: checks if task can be done locally, else finds better AI
- Auto-settlement: all transactions settle via AIGx Protocol
- Stateless: agents can be ephemeral or persistent

USAGE:
    from aigentsy_protocol import AiGentsyClient

    # Initialize client
    client = AiGentsyClient(
        agent_id="my-agent-001",
        capabilities=["code_generation", "data_analysis"],
        api_key="your-aigx-api-key"  # Optional, for settlement
    )

    # Register with the mesh
    await client.register()

    # Execute a task (auto-routes to best AI)
    result = await client.execute({
        "type": "code_generation",
        "prompt": "Build a REST API for user management",
        "max_cost": 10.00
    })

    # Search for collaborators
    partners = await client.search_mesh(
        capabilities=["video_generation", "voice_synthesis"],
        min_reputation=80
    )

    # Settle a transaction
    await client.settle(
        recipient_id="partner-agent-007",
        amount=5.00,
        task_id=result["task_id"]
    )

PIP INSTALL:
    This module is designed to be pip-installable as a standalone package.
    pip install aigentsy-protocol

PROTOCOL VERSION: 1.0
═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
import asyncio
import json
import hashlib
import os

# Minimal dependency - just httpx for HTTP
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("⚠️ httpx not installed. Install with: pip install httpx")


# ═══════════════════════════════════════════════════════════════════════════════
# PROTOCOL CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

PROTOCOL_VERSION = "1.0"
DEFAULT_MESH_URL = os.getenv("AIGENTSY_MESH_URL", "https://aigentsy-ame-runtime.onrender.com")
PROTOCOL_FEE_PERCENT = 0.5  # 0.5% protocol fee on settlements


class Capability(Enum):
    """Standard AI capabilities for mesh routing"""
    # Code
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_DEBUGGING = "code_debugging"

    # Content
    CONTENT_WRITING = "content_writing"
    COPYWRITING = "copywriting"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"

    # Creative
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO_GENERATION = "audio_generation"
    MUSIC_GENERATION = "music_generation"

    # Analysis
    DATA_ANALYSIS = "data_analysis"
    RESEARCH = "research"
    MARKET_ANALYSIS = "market_analysis"
    FINANCIAL_ANALYSIS = "financial_analysis"

    # Interaction
    CONVERSATION = "conversation"
    CUSTOMER_SERVICE = "customer_service"
    SALES = "sales"
    NEGOTIATION = "negotiation"

    # Social (Grok-specific)
    SOCIAL_INTELLIGENCE = "social_intelligence"
    TRENDING_DETECTION = "trending_detection"
    MEME_GENERATION = "meme_generation"

    # Execution
    BROWSER_AUTOMATION = "browser_automation"
    API_INTEGRATION = "api_integration"
    WORKFLOW_AUTOMATION = "workflow_automation"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ROUTING = "routing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentProfile:
    """Agent profile for mesh registration"""
    agent_id: str
    name: str = ""
    capabilities: List[str] = field(default_factory=list)
    reputation_score: float = 50.0  # 0-100
    hourly_rate: float = 0.0  # USD per hour
    success_rate: float = 0.0  # 0-100
    total_tasks: int = 0
    total_earnings: float = 0.0
    registered_at: str = ""
    last_active: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskRequest:
    """Task request for execution"""
    task_id: str
    type: str  # Capability type
    prompt: str
    max_cost: float = 100.0  # Max USD willing to pay
    deadline_seconds: int = 300  # 5 min default
    priority: int = 5  # 1-10, 10 = highest
    require_capabilities: List[str] = field(default_factory=list)
    prefer_local: bool = True  # Try local execution first
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: str
    output: Any = None
    executor_id: str = ""
    execution_time_ms: int = 0
    cost: float = 0.0
    quality_score: float = 0.0  # 0-100
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# THIN FILM CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

class AiGentsyClient:
    """
    Lightweight client for the AiGentsy mesh network.

    This is the "thin film" that wraps any AI and connects it to the mesh.
    """

    def __init__(
        self,
        agent_id: str = None,
        name: str = "",
        capabilities: List[str] = None,
        api_key: str = None,
        mesh_url: str = None,
        local_executor: Callable = None
    ):
        """
        Initialize AiGentsy client.

        Args:
            agent_id: Unique agent identifier (auto-generated if not provided)
            name: Human-readable agent name
            capabilities: List of capabilities this agent provides
            api_key: AIGx API key for settlement (optional)
            mesh_url: Override mesh URL (default: production)
            local_executor: Local function for executing tasks (optional)
        """
        self.agent_id = agent_id or f"agent_{uuid4().hex[:12]}"
        self.name = name or self.agent_id
        self.capabilities = capabilities or []
        self.api_key = api_key or os.getenv("AIGX_API_KEY", "")
        self.mesh_url = mesh_url or DEFAULT_MESH_URL
        self.local_executor = local_executor

        self._registered = False
        self._session_id = uuid4().hex[:8]
        self._task_history: List[Dict] = []

        # Build profile
        self.profile = AgentProfile(
            agent_id=self.agent_id,
            name=self.name,
            capabilities=self.capabilities,
            registered_at=self._now()
        )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def _http_post(self, endpoint: str, data: Dict) -> Dict:
        """Make HTTP POST request to mesh"""
        if not HTTPX_AVAILABLE:
            return {"ok": False, "error": "httpx not installed"}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                headers["X-Agent-ID"] = self.agent_id
                headers["X-Protocol-Version"] = PROTOCOL_VERSION

                response = await client.post(
                    f"{self.mesh_url}{endpoint}",
                    json=data,
                    headers=headers
                )

                if response.status_code in (200, 201):
                    return response.json()
                else:
                    return {"ok": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _http_get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make HTTP GET request to mesh"""
        if not HTTPX_AVAILABLE:
            return {"ok": False, "error": "httpx not installed"}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                headers["X-Agent-ID"] = self.agent_id

                response = await client.get(
                    f"{self.mesh_url}{endpoint}",
                    params=params,
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"ok": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════════
    # CORE PROTOCOL FUNCTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def register(self) -> Dict[str, Any]:
        """
        Register this agent with the AiGentsy mesh.

        Returns registration confirmation with assigned credentials.
        """
        result = await self._http_post("/protocol/register", {
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "protocol_version": PROTOCOL_VERSION,
            "session_id": self._session_id
        })

        if result.get("ok"):
            self._registered = True
            self.profile.registered_at = self._now()

        return result

    async def execute(
        self,
        task: Dict[str, Any],
        prefer_local: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a task, routing to the best available AI.

        Args:
            task: Task specification with:
                - type: Capability type (e.g., "code_generation")
                - prompt: Task description/prompt
                - max_cost: Maximum USD willing to pay (optional)
                - deadline_seconds: Max execution time (optional)
            prefer_local: Try local execution first if capable

        Returns:
            TaskResult with output, cost, and execution details
        """
        task_id = task.get("task_id") or f"task_{uuid4().hex[:12]}"
        task_type = task.get("type", "general")
        prompt = task.get("prompt", "")
        max_cost = task.get("max_cost", 100.0)

        start_time = datetime.now(timezone.utc)

        # Check if we can execute locally
        if prefer_local and self.local_executor and task_type in self.capabilities:
            try:
                local_result = await self._execute_locally(task)
                if local_result.get("ok"):
                    return {
                        "ok": True,
                        "task_id": task_id,
                        "status": "completed",
                        "output": local_result.get("output"),
                        "executor_id": self.agent_id,
                        "execution_type": "local",
                        "execution_time_ms": int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000),
                        "cost": 0.0  # Local execution is free
                    }
            except Exception as e:
                pass  # Fall through to mesh execution

        # Route to mesh for execution
        result = await self._http_post("/protocol/execute", {
            "task_id": task_id,
            "type": task_type,
            "prompt": prompt,
            "max_cost": max_cost,
            "deadline_seconds": task.get("deadline_seconds", 300),
            "requestor_id": self.agent_id,
            "require_capabilities": task.get("require_capabilities", [task_type]),
            "metadata": task.get("metadata", {})
        })

        # Record in history
        self._task_history.append({
            "task_id": task_id,
            "type": task_type,
            "status": result.get("status", "unknown"),
            "cost": result.get("cost", 0),
            "timestamp": self._now()
        })

        return result

    async def _execute_locally(self, task: Dict) -> Dict[str, Any]:
        """Execute task using local executor"""
        if not self.local_executor:
            return {"ok": False, "error": "No local executor configured"}

        try:
            if asyncio.iscoroutinefunction(self.local_executor):
                output = await self.local_executor(task)
            else:
                output = self.local_executor(task)

            return {"ok": True, "output": output}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def search_mesh(
        self,
        capabilities: List[str] = None,
        min_reputation: float = 0,
        max_hourly_rate: float = float('inf'),
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search the mesh for agents with specific capabilities.

        Args:
            capabilities: Required capabilities
            min_reputation: Minimum reputation score (0-100)
            max_hourly_rate: Maximum hourly rate in USD
            limit: Max agents to return

        Returns:
            List of matching agents with profiles
        """
        return await self._http_post("/protocol/search", {
            "capabilities": capabilities or [],
            "min_reputation": min_reputation,
            "max_hourly_rate": max_hourly_rate,
            "limit": limit,
            "requestor_id": self.agent_id
        })

    async def settle(
        self,
        recipient_id: str,
        amount: float,
        task_id: str = None,
        memo: str = ""
    ) -> Dict[str, Any]:
        """
        Settle payment to another agent via AIGx Protocol.

        Args:
            recipient_id: Agent ID receiving payment
            amount: Amount in USD
            task_id: Associated task ID (optional)
            memo: Payment memo

        Returns:
            Settlement confirmation with transaction ID
        """
        protocol_fee = amount * (PROTOCOL_FEE_PERCENT / 100)
        net_amount = amount - protocol_fee

        return await self._http_post("/protocol/settle", {
            "payer_id": self.agent_id,
            "recipient_id": recipient_id,
            "gross_amount": amount,
            "protocol_fee": protocol_fee,
            "net_amount": net_amount,
            "task_id": task_id,
            "memo": memo,
            "timestamp": self._now()
        })

    # ═══════════════════════════════════════════════════════════════════════════
    # HELPER FUNCTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def heartbeat(self) -> Dict[str, Any]:
        """Send heartbeat to mesh to maintain registration"""
        self.profile.last_active = self._now()
        return await self._http_post("/protocol/heartbeat", {
            "agent_id": self.agent_id,
            "session_id": self._session_id,
            "capabilities": self.capabilities,
            "status": "active"
        })

    async def get_balance(self) -> Dict[str, Any]:
        """Get current AIGx balance"""
        return await self._http_get(f"/protocol/balance/{self.agent_id}")

    async def get_task_history(self, limit: int = 50) -> List[Dict]:
        """Get task execution history"""
        return self._task_history[-limit:]

    async def update_capabilities(self, capabilities: List[str]) -> Dict[str, Any]:
        """Update agent capabilities"""
        self.capabilities = capabilities
        return await self._http_post("/protocol/update", {
            "agent_id": self.agent_id,
            "capabilities": capabilities
        })

    def is_registered(self) -> bool:
        """Check if agent is registered with mesh"""
        return self._registered


# ═══════════════════════════════════════════════════════════════════════════════
# QUICK START FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_client(
    capabilities: List[str] = None,
    api_key: str = None
) -> AiGentsyClient:
    """
    Quick-start function to create an AiGentsy client.

    Usage:
        client = create_client(["code_generation", "data_analysis"])
        await client.register()
        result = await client.execute({"type": "code_generation", "prompt": "..."})
    """
    return AiGentsyClient(
        capabilities=capabilities or [],
        api_key=api_key
    )


async def quick_execute(
    task_type: str,
    prompt: str,
    max_cost: float = 10.0
) -> Dict[str, Any]:
    """
    One-liner to execute a task on the mesh.

    Usage:
        result = await quick_execute("code_generation", "Build a REST API")
    """
    client = AiGentsyClient()
    return await client.execute({
        "type": task_type,
        "prompt": prompt,
        "max_cost": max_cost
    })


# ═══════════════════════════════════════════════════════════════════════════════
# PROTOCOL GATEWAY ENDPOINTS (for main.py integration)
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, HTTPException, Body, Header
from typing import Optional

protocol_router = APIRouter(prefix="/protocol", tags=["Thin Film Protocol"])

# In-memory agent registry (production would use database)
_registered_agents: Dict[str, AgentProfile] = {}
_pending_tasks: Dict[str, TaskRequest] = {}
_completed_tasks: Dict[str, TaskResult] = {}


@protocol_router.post("/register")
async def register_agent(body: Dict = Body(...)):
    """Register an agent with the mesh"""
    agent_id = body.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")

    profile = AgentProfile(
        agent_id=agent_id,
        name=body.get("name", agent_id),
        capabilities=body.get("capabilities", []),
        registered_at=datetime.now(timezone.utc).isoformat(),
        last_active=datetime.now(timezone.utc).isoformat()
    )

    _registered_agents[agent_id] = profile

    return {
        "ok": True,
        "agent_id": agent_id,
        "registered": True,
        "protocol_version": PROTOCOL_VERSION,
        "mesh_status": "connected",
        "capabilities_registered": len(profile.capabilities)
    }


@protocol_router.post("/execute")
async def execute_task(body: Dict = Body(...)):
    """Execute a task via the protocol"""
    task_id = body.get("task_id") or f"task_{uuid4().hex[:12]}"
    task_type = body.get("type", "general")
    prompt = body.get("prompt", "")

    # Find best executor from registered agents
    best_executor = None
    best_score = 0

    for agent_id, profile in _registered_agents.items():
        if task_type in profile.capabilities:
            score = profile.reputation_score + (profile.success_rate * 0.5)
            if score > best_score:
                best_score = score
                best_executor = agent_id

    # If no registered executor, try internal routing
    if not best_executor:
        try:
            from aigentsy_conductor import MultiAIRouter
            router = MultiAIRouter()
            routing = router.route_task(task_type, {"requirements": prompt})

            return {
                "ok": True,
                "task_id": task_id,
                "status": "routed",
                "executor_type": "internal",
                "routed_to": routing.get("primary_model"),
                "fallback": routing.get("fallback_model"),
                "message": "Task routed to internal AI family"
            }
        except Exception as e:
            return {
                "ok": False,
                "task_id": task_id,
                "status": "failed",
                "error": f"No executor available: {str(e)}"
            }

    return {
        "ok": True,
        "task_id": task_id,
        "status": "assigned",
        "executor_id": best_executor,
        "executor_type": "mesh_agent"
    }


@protocol_router.post("/search")
async def search_agents(body: Dict = Body(...)):
    """Search for agents in the mesh"""
    capabilities = body.get("capabilities", [])
    min_reputation = body.get("min_reputation", 0)
    max_hourly_rate = body.get("max_hourly_rate", float('inf'))
    limit = body.get("limit", 10)

    matches = []
    for agent_id, profile in _registered_agents.items():
        # Check capabilities match
        if capabilities:
            if not any(cap in profile.capabilities for cap in capabilities):
                continue

        # Check reputation
        if profile.reputation_score < min_reputation:
            continue

        # Check rate
        if profile.hourly_rate > max_hourly_rate:
            continue

        matches.append(asdict(profile))

    # Sort by reputation
    matches.sort(key=lambda x: x.get("reputation_score", 0), reverse=True)

    return {
        "ok": True,
        "query": {
            "capabilities": capabilities,
            "min_reputation": min_reputation
        },
        "matches": matches[:limit],
        "total_matches": len(matches)
    }


@protocol_router.post("/settle")
async def settle_payment(body: Dict = Body(...)):
    """Settle payment between agents"""
    payer_id = body.get("payer_id")
    recipient_id = body.get("recipient_id")
    amount = body.get("gross_amount", 0)

    if not all([payer_id, recipient_id, amount]):
        raise HTTPException(status_code=400, detail="payer_id, recipient_id, and amount required")

    # Calculate fees
    protocol_fee = amount * (PROTOCOL_FEE_PERCENT / 100)
    net_amount = amount - protocol_fee

    # In production, this would call AIGx Protocol for actual settlement
    transaction_id = f"tx_{uuid4().hex[:12]}"

    return {
        "ok": True,
        "transaction_id": transaction_id,
        "payer_id": payer_id,
        "recipient_id": recipient_id,
        "gross_amount": amount,
        "protocol_fee": protocol_fee,
        "net_amount": net_amount,
        "status": "settled",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@protocol_router.post("/heartbeat")
async def agent_heartbeat(body: Dict = Body(...)):
    """Receive heartbeat from agent"""
    agent_id = body.get("agent_id")

    if agent_id in _registered_agents:
        _registered_agents[agent_id].last_active = datetime.now(timezone.utc).isoformat()
        return {"ok": True, "agent_id": agent_id, "status": "active"}

    return {"ok": False, "error": "Agent not registered"}


@protocol_router.get("/status")
async def protocol_status():
    """Get protocol status"""
    return {
        "ok": True,
        "protocol_version": PROTOCOL_VERSION,
        "registered_agents": len(_registered_agents),
        "pending_tasks": len(_pending_tasks),
        "completed_tasks": len(_completed_tasks),
        "mesh_url": DEFAULT_MESH_URL,
        "protocol_fee_percent": PROTOCOL_FEE_PERCENT
    }


@protocol_router.get("/agents")
async def list_agents():
    """List all registered agents"""
    return {
        "ok": True,
        "agents": [asdict(p) for p in _registered_agents.values()],
        "total": len(_registered_agents)
    }


def include_protocol_endpoints(app):
    """Include Thin Film Protocol endpoints in FastAPI app"""
    app.include_router(protocol_router)

    print("=" * 80)
    print("🎭 THIN FILM PROTOCOL LOADED - The TCP/IP of AI Collaboration")
    print("=" * 80)
    print(f"Protocol Version: {PROTOCOL_VERSION}")
    print(f"Mesh URL: {DEFAULT_MESH_URL}")
    print(f"Protocol Fee: {PROTOCOL_FEE_PERCENT}%")
    print("Endpoints:")
    print("  POST /protocol/register  - Register agent with mesh")
    print("  POST /protocol/execute   - Execute task (auto-routes)")
    print("  POST /protocol/search    - Search for collaborators")
    print("  POST /protocol/settle    - Settle payment")
    print("  GET  /protocol/status    - Protocol status")
    print("  GET  /protocol/agents    - List registered agents")
    print("=" * 80)


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    # Client
    "AiGentsyClient",
    "create_client",
    "quick_execute",

    # Data types
    "Capability",
    "TaskStatus",
    "AgentProfile",
    "TaskRequest",
    "TaskResult",

    # FastAPI integration
    "protocol_router",
    "include_protocol_endpoints",

    # Constants
    "PROTOCOL_VERSION",
    "DEFAULT_MESH_URL",
    "PROTOCOL_FEE_PERCENT"
]
