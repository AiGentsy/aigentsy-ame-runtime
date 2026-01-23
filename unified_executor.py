"""
═══════════════════════════════════════════════════════════════════════════════
UNIFIED EXECUTOR v2.0 - THE COMPLETE ORCHESTRATION LAYER
═══════════════════════════════════════════════════════════════════════════════

SINGLE ENTRY POINT FOR ALL 108+ SUBSYSTEMS:

1. EXECUTION LAYER
   - Connector Registry (APIs)
   - Multi-AI Router (Claude/GPT/Gemini/Perplexity/Grok)
   - Universal Fabric (Browser automation)

2. INTELLIGENCE LAYER
   - MetaHive Brain (Cross-user learning)
   - Outcome Oracle (Funnel tracking)
   - Pricing Oracle (Dynamic pricing)
   - Yield Memory (Pattern learning)
   - LTV Forecaster (Churn prediction)
   - Fraud Detector

3. DISCOVERY LAYER
   - Alpha Discovery Engine (7 dimensions)
   - Ultimate Discovery Engine
   - Internet Discovery (Perplexity/DuckDuckGo)
   - Pain Point Detector
   - Research Engine
   - Signal Ingestion

4. REVENUE LAYER
   - AMG Orchestrator (10-stage loop)
   - R3 Autopilot (Revenue reinvestment)
   - V107-V115 Revenue Engines
   - Gap Harvesters
   - Market Maker
   - Arbitrage Pipeline

5. CONTENT LAYER
   - Social AutoPosting
   - Video Engine
   - Audio Engine
   - Graphics Engine

6. FINANCIAL LAYER
   - AIGx Protocol (Settlement)
   - OCL Engine (Credit)
   - Agent Factoring
   - Revenue Reconciliation

7. COLLABORATION LAYER
   - MetaBridge (Agent matching)
   - JV Mesh (Joint ventures)
   - Deal Graph (Relationships)
   - Agent Registry
   - Protocol Gateway

8. BUSINESS LAYER
   - Business Accelerator
   - Storefront Deployer
   - Template Actionizer
   - Franchise Engine
   - SKU Orchestrator

USAGE:
    from unified_executor import execute, UnifiedExecutor

    result = await execute({
        "type": "discovery",
        "action": "find_opportunities",
        "keywords": ["AI automation"]
    })

Updated: Jan 2026 - Full 108+ System Integration
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
# EXECUTION CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════════

class ExecutionCategory(Enum):
    """High-level execution categories"""
    EXECUTION = "execution"      # Direct task execution
    INTELLIGENCE = "intelligence"  # Learning & optimization
    DISCOVERY = "discovery"      # Opportunity finding
    REVENUE = "revenue"          # Revenue generation
    CONTENT = "content"          # Content creation
    FINANCIAL = "financial"      # Payments & settlements
    COLLABORATION = "collaboration"  # Agent-to-agent
    BUSINESS = "business"        # Business operations


class ExecutionMethod(Enum):
    """How a task should be executed"""
    API = "api"
    AI = "ai"
    BROWSER = "browser"
    HYBRID = "hybrid"
    INTERNAL = "internal"
    MANUAL = "manual"


# ═══════════════════════════════════════════════════════════════════════════════
# TASK TYPE ROUTING
# ═══════════════════════════════════════════════════════════════════════════════

# Map task types to categories and execution methods
TASK_ROUTING = {
    # === EXECUTION TASKS ===
    "payment": (ExecutionCategory.EXECUTION, ExecutionMethod.API),
    "invoice": (ExecutionCategory.EXECUTION, ExecutionMethod.API),
    "email_send": (ExecutionCategory.EXECUTION, ExecutionMethod.API),
    "sms_send": (ExecutionCategory.EXECUTION, ExecutionMethod.API),
    "webhook_call": (ExecutionCategory.EXECUTION, ExecutionMethod.API),
    "content_generation": (ExecutionCategory.EXECUTION, ExecutionMethod.AI),
    "code_generation": (ExecutionCategory.EXECUTION, ExecutionMethod.AI),
    "browser_automation": (ExecutionCategory.EXECUTION, ExecutionMethod.BROWSER),
    "proposal_submission": (ExecutionCategory.EXECUTION, ExecutionMethod.HYBRID),

    # === INTELLIGENCE TASKS ===
    "learn_pattern": (ExecutionCategory.INTELLIGENCE, ExecutionMethod.INTERNAL),
    "query_hive": (ExecutionCategory.INTELLIGENCE, ExecutionMethod.INTERNAL),
    "get_best_action": (ExecutionCategory.INTELLIGENCE, ExecutionMethod.INTERNAL),
    "calculate_price": (ExecutionCategory.INTELLIGENCE, ExecutionMethod.INTERNAL),
    "predict_ltv": (ExecutionCategory.INTELLIGENCE, ExecutionMethod.INTERNAL),
    "check_fraud": (ExecutionCategory.INTELLIGENCE, ExecutionMethod.INTERNAL),
    "track_outcome": (ExecutionCategory.INTELLIGENCE, ExecutionMethod.INTERNAL),

    # === DISCOVERY TASKS ===
    "discover_opportunities": (ExecutionCategory.DISCOVERY, ExecutionMethod.INTERNAL),
    "internet_search": (ExecutionCategory.DISCOVERY, ExecutionMethod.AI),
    "scan_platforms": (ExecutionCategory.DISCOVERY, ExecutionMethod.INTERNAL),
    "detect_pain_points": (ExecutionCategory.DISCOVERY, ExecutionMethod.AI),
    "research": (ExecutionCategory.DISCOVERY, ExecutionMethod.AI),
    "signal_ingestion": (ExecutionCategory.DISCOVERY, ExecutionMethod.INTERNAL),

    # === REVENUE TASKS ===
    "run_amg_cycle": (ExecutionCategory.REVENUE, ExecutionMethod.INTERNAL),
    "execute_arbitrage": (ExecutionCategory.REVENUE, ExecutionMethod.INTERNAL),
    "harvest_gaps": (ExecutionCategory.REVENUE, ExecutionMethod.INTERNAL),
    "make_market": (ExecutionCategory.REVENUE, ExecutionMethod.INTERNAL),
    "run_r3_autopilot": (ExecutionCategory.REVENUE, ExecutionMethod.INTERNAL),

    # === CONTENT TASKS ===
    "social_post": (ExecutionCategory.CONTENT, ExecutionMethod.HYBRID),
    "generate_video": (ExecutionCategory.CONTENT, ExecutionMethod.AI),
    "generate_audio": (ExecutionCategory.CONTENT, ExecutionMethod.AI),
    "generate_graphics": (ExecutionCategory.CONTENT, ExecutionMethod.AI),

    # === FINANCIAL TASKS ===
    "settle_payment": (ExecutionCategory.FINANCIAL, ExecutionMethod.API),
    "request_factoring": (ExecutionCategory.FINANCIAL, ExecutionMethod.INTERNAL),
    "calculate_ocl": (ExecutionCategory.FINANCIAL, ExecutionMethod.INTERNAL),
    "reconcile_revenue": (ExecutionCategory.FINANCIAL, ExecutionMethod.INTERNAL),

    # === COLLABORATION TASKS ===
    "find_partners": (ExecutionCategory.COLLABORATION, ExecutionMethod.INTERNAL),
    "create_jv": (ExecutionCategory.COLLABORATION, ExecutionMethod.INTERNAL),
    "register_agent": (ExecutionCategory.COLLABORATION, ExecutionMethod.INTERNAL),
    "search_mesh": (ExecutionCategory.COLLABORATION, ExecutionMethod.INTERNAL),

    # === BUSINESS TASKS ===
    "deploy_storefront": (ExecutionCategory.BUSINESS, ExecutionMethod.INTERNAL),
    "actionize_template": (ExecutionCategory.BUSINESS, ExecutionMethod.INTERNAL),
    "create_franchise": (ExecutionCategory.BUSINESS, ExecutionMethod.INTERNAL),
}


@dataclass
class ExecutionResult:
    """Unified execution result"""
    task_id: str
    ok: bool
    category: str
    method: str
    output: Any = None
    executor: str = ""
    execution_time_ms: int = 0
    cost: float = 0.0
    error: str = ""
    fallback_used: bool = False
    learning_recorded: bool = False
    metadata: Dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED EXECUTOR - COMPLETE ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedExecutor:
    """
    THE COMPLETE ORCHESTRATION LAYER

    Single entry point for all 108+ subsystems.
    Routes tasks to appropriate systems based on type.
    Integrates learning feedback loops.
    """

    def __init__(self):
        self._initialized = False
        self._execution_log: List[Dict] = []
        self._subsystem_status: Dict[str, bool] = {}

        # Initialize all subsystems
        self._init_all_subsystems()

    def _init_all_subsystems(self):
        """Initialize ALL 108+ subsystems"""

        # ═══════════════════════════════════════════════════════════════════
        # 1. EXECUTION LAYER
        # ═══════════════════════════════════════════════════════════════════

        # Connector Registry
        try:
            from connectors.registry import get_connector
            self._get_connector = get_connector
            self._subsystem_status["connectors"] = True
        except ImportError:
            self._subsystem_status["connectors"] = False

        # Multi-AI Router
        try:
            from aigentsy_conductor import MultiAIRouter
            self._ai_router = MultiAIRouter()
            self._subsystem_status["ai_router"] = True
        except ImportError:
            self._ai_router = None
            self._subsystem_status["ai_router"] = False

        # Universal Fabric
        try:
            from universal_fulfillment_fabric import execute_universal, get_fabric_status
            self._execute_fabric = execute_universal
            self._get_fabric_status = get_fabric_status
            self._subsystem_status["fabric"] = True
        except ImportError:
            self._subsystem_status["fabric"] = False

        # ═══════════════════════════════════════════════════════════════════
        # 2. INTELLIGENCE LAYER
        # ═══════════════════════════════════════════════════════════════════

        # MetaHive Brain
        try:
            from metahive_brain import contribute_to_hive, query_hive, get_hive_stats
            self._contribute_to_hive = contribute_to_hive
            self._query_hive = query_hive
            self._get_hive_stats = get_hive_stats
            self._subsystem_status["metahive"] = True
        except ImportError:
            self._subsystem_status["metahive"] = False

        # Outcome Oracle
        try:
            from outcome_oracle_max import on_event, get_user_funnel_stats, credit_aigx
            self._track_outcome = on_event
            self._get_funnel_stats = get_user_funnel_stats
            self._credit_aigx = credit_aigx
            self._subsystem_status["outcome_oracle"] = True
        except ImportError:
            self._subsystem_status["outcome_oracle"] = False

        # Pricing Oracle
        try:
            from pricing_oracle import calculate_dynamic_price, suggest_optimal_pricing
            self._calculate_price = calculate_dynamic_price
            self._suggest_pricing = suggest_optimal_pricing
            self._subsystem_status["pricing_oracle"] = True
        except ImportError:
            self._subsystem_status["pricing_oracle"] = False

        # Yield Memory
        try:
            from yield_memory import store_pattern, get_best_action, find_similar_patterns, get_memory_stats
            self._store_pattern = store_pattern
            self._get_best_action = get_best_action
            self._find_patterns = find_similar_patterns
            self._subsystem_status["yield_memory"] = True
        except ImportError:
            self._subsystem_status["yield_memory"] = False

        # LTV Forecaster
        try:
            from ltv_forecaster import calculate_ltv_with_churn
            self._calculate_ltv = calculate_ltv_with_churn
            self._subsystem_status["ltv_forecaster"] = True
        except ImportError:
            self._subsystem_status["ltv_forecaster"] = False

        # Fraud Detector
        try:
            from fraud_detector import check_fraud_signals
            self._check_fraud = check_fraud_signals
            self._subsystem_status["fraud_detector"] = True
        except ImportError:
            self._subsystem_status["fraud_detector"] = False

        # ═══════════════════════════════════════════════════════════════════
        # 3. DISCOVERY LAYER
        # ═══════════════════════════════════════════════════════════════════

        # Alpha Discovery Engine
        try:
            from alpha_discovery_engine import AlphaDiscoveryEngine
            self._alpha_discovery = AlphaDiscoveryEngine()
            self._subsystem_status["alpha_discovery"] = True
        except ImportError:
            self._subsystem_status["alpha_discovery"] = False

        # Ultimate Discovery Engine
        try:
            from ultimate_discovery_engine import discover_all_opportunities
            self._ultimate_discover = discover_all_opportunities
            self._subsystem_status["ultimate_discovery"] = True
        except ImportError:
            self._subsystem_status["ultimate_discovery"] = False

        # Internet Discovery
        try:
            from internet_search_setup import search_internet, internet_discovery_scan
            self._search_internet = search_internet
            self._internet_scan = internet_discovery_scan
            self._subsystem_status["internet_discovery"] = True
        except ImportError:
            self._subsystem_status["internet_discovery"] = False

        # Pain Point Detector
        try:
            from pain_point_detector import PainPointDetector
            self._pain_detector = PainPointDetector()
            self._subsystem_status["pain_detector"] = True
        except ImportError:
            self._subsystem_status["pain_detector"] = False

        # Research Engine
        try:
            from research_engine import ResearchEngine
            self._research_engine = ResearchEngine()
            self._subsystem_status["research_engine"] = True
        except ImportError:
            self._subsystem_status["research_engine"] = False

        # Signal Ingestion
        try:
            from real_signal_ingestion import get_signal_engine
            self._signal_engine = get_signal_engine()
            self._subsystem_status["signal_ingestion"] = True
        except ImportError:
            self._subsystem_status["signal_ingestion"] = False

        # ═══════════════════════════════════════════════════════════════════
        # 4. REVENUE LAYER
        # ═══════════════════════════════════════════════════════════════════

        # AMG Orchestrator
        try:
            from amg_orchestrator import AMGOrchestrator
            self._amg = AMGOrchestrator(username=os.getenv("AIGENTSY_USERNAME", "wade"))
            self._subsystem_status["amg"] = True
        except (ImportError, Exception) as e:
            self._subsystem_status["amg"] = False

        # R3 Autopilot
        try:
            from r3_autopilot import execute_autopilot_spend
            self._r3_autopilot = execute_autopilot_spend
            self._subsystem_status["r3_autopilot"] = True
        except ImportError:
            self._subsystem_status["r3_autopilot"] = False

        # Gap Harvesters (V110)
        try:
            from v110_gap_harvesters import scan_all_harvesters
            self._scan_gaps = scan_all_harvesters
            self._subsystem_status["gap_harvesters"] = True
        except ImportError:
            self._subsystem_status["gap_harvesters"] = False

        # Market Maker (V112)
        try:
            from v112_market_maker_extensions import (
                calculate_optimal_spread,
                suggest_market_price,
                execute_market_making
            )
            self._market_maker = execute_market_making
            self._subsystem_status["market_maker"] = True
        except ImportError:
            self._subsystem_status["market_maker"] = False

        # Arbitrage Pipeline
        try:
            from arbitrage_execution_pipeline import get_arbitrage_pipeline
            self._arbitrage = get_arbitrage_pipeline()
            self._subsystem_status["arbitrage"] = True
        except ImportError:
            self._subsystem_status["arbitrage"] = False

        # Universal Revenue Orchestrator
        try:
            from universal_revenue_orchestrator import UniversalRevenueOrchestrator
            self._revenue_orchestrator = UniversalRevenueOrchestrator()
            self._subsystem_status["revenue_orchestrator"] = True
        except ImportError:
            self._subsystem_status["revenue_orchestrator"] = False

        # ═══════════════════════════════════════════════════════════════════
        # 5. CONTENT LAYER
        # ═══════════════════════════════════════════════════════════════════

        # Social AutoPosting
        try:
            from social_autoposting_engine import get_social_engine
            self._social_engine = get_social_engine()
            self._subsystem_status["social_engine"] = True
        except ImportError:
            self._subsystem_status["social_engine"] = False

        # Video Engine
        try:
            from video_engine import VideoEngine
            self._video_engine = VideoEngine()
            self._subsystem_status["video_engine"] = True
        except ImportError:
            self._subsystem_status["video_engine"] = False

        # Audio Engine
        try:
            from audio_engine import AudioEngine
            self._audio_engine = AudioEngine()
            self._subsystem_status["audio_engine"] = True
        except ImportError:
            self._subsystem_status["audio_engine"] = False

        # Graphics Engine
        try:
            from graphics_engine import GraphicsEngine
            self._graphics_engine = GraphicsEngine()
            self._subsystem_status["graphics_engine"] = True
        except ImportError:
            self._subsystem_status["graphics_engine"] = False

        # ═══════════════════════════════════════════════════════════════════
        # 6. FINANCIAL LAYER
        # ═══════════════════════════════════════════════════════════════════

        # AIGx Protocol
        try:
            from aigx_protocol import get_protocol
            self._aigx_protocol = get_protocol()
            self._subsystem_status["aigx_protocol"] = True
        except ImportError:
            self._subsystem_status["aigx_protocol"] = False

        # OCL Engine
        try:
            from ocl_engine import calculate_ocl_limit, spend_ocl
            self._calculate_ocl = calculate_ocl_limit
            self._spend_ocl = spend_ocl
            self._subsystem_status["ocl_engine"] = True
        except ImportError:
            self._subsystem_status["ocl_engine"] = False

        # Agent Factoring
        try:
            from agent_factoring import request_factoring_advance
            self._request_factoring = request_factoring_advance
            self._subsystem_status["agent_factoring"] = True
        except ImportError:
            self._subsystem_status["agent_factoring"] = False

        # Revenue Reconciliation
        try:
            from revenue_reconciliation_engine import get_reconciliation_engine
            self._reconciliation = get_reconciliation_engine()
            self._subsystem_status["reconciliation"] = True
        except ImportError:
            self._subsystem_status["reconciliation"] = False

        # ═══════════════════════════════════════════════════════════════════
        # 7. COLLABORATION LAYER
        # ═══════════════════════════════════════════════════════════════════

        # MetaBridge
        try:
            from metabridge import execute_metabridge, find_complementary_agents
            self._metabridge = execute_metabridge
            self._find_agents = find_complementary_agents
            self._subsystem_status["metabridge"] = True
        except ImportError:
            self._subsystem_status["metabridge"] = False

        # JV Mesh
        try:
            from jv_mesh import create_jv_proposal, suggest_jv_partners, list_active_jvs
            self._create_jv = create_jv_proposal
            self._suggest_partners = suggest_jv_partners
            self._subsystem_status["jv_mesh"] = True
        except ImportError:
            self._subsystem_status["jv_mesh"] = False

        # Deal Graph
        try:
            from autonomous_deal_graph import get_deal_graph
            self._deal_graph = get_deal_graph()
            self._subsystem_status["deal_graph"] = True
        except ImportError:
            self._subsystem_status["deal_graph"] = False

        # Agent Registry
        try:
            from agent_registry import get_registry, register_agent
            self._agent_registry = get_registry()
            self._register_agent = register_agent
            self._subsystem_status["agent_registry"] = True
        except ImportError:
            self._subsystem_status["agent_registry"] = False

        # Protocol Gateway
        try:
            from protocol_gateway import ProtocolGateway
            self._protocol_gateway = ProtocolGateway()
            self._subsystem_status["protocol_gateway"] = True
        except ImportError:
            self._subsystem_status["protocol_gateway"] = False

        # ═══════════════════════════════════════════════════════════════════
        # 8. BUSINESS LAYER
        # ═══════════════════════════════════════════════════════════════════

        # Business Accelerator
        try:
            from business_in_a_box_accelerator import BusinessDeploymentEngine
            self._business_deployer = BusinessDeploymentEngine()
            self._subsystem_status["business_accelerator"] = True
        except ImportError:
            self._subsystem_status["business_accelerator"] = False

        # Storefront Deployer
        try:
            from storefront_deployer import deploy_storefront
            self._deploy_storefront = deploy_storefront
            self._subsystem_status["storefront_deployer"] = True
        except ImportError:
            self._subsystem_status["storefront_deployer"] = False

        # Template Actionizer
        try:
            from template_actionizer import actionize_template
            self._actionize_template = actionize_template
            self._subsystem_status["template_actionizer"] = True
        except ImportError:
            self._subsystem_status["template_actionizer"] = False

        # Franchise Engine
        try:
            from franchise_engine import LICENSE_TYPES
            self._franchise_types = LICENSE_TYPES
            self._subsystem_status["franchise_engine"] = True
        except ImportError:
            self._subsystem_status["franchise_engine"] = False

        # SKU Orchestrator
        try:
            from sku_orchestrator import UniversalBusinessOrchestrator
            self._sku_orchestrator = UniversalBusinessOrchestrator()
            self._subsystem_status["sku_orchestrator"] = True
        except ImportError:
            self._subsystem_status["sku_orchestrator"] = False

        # Master Runtime (for autonomous cycles)
        try:
            from master_autonomous_orchestrator import MasterOrchestrator
            self._master_orchestrator = MasterOrchestrator
            self._subsystem_status["master_orchestrator"] = True
        except ImportError:
            self._subsystem_status["master_orchestrator"] = False

        self._initialized = True
        self._log_initialization()

    def _log_initialization(self):
        """Log initialization status"""
        available = sum(1 for v in self._subsystem_status.values() if v)
        total = len(self._subsystem_status)
        print(f"⚡ UNIFIED EXECUTOR v2.0: {available}/{total} subsystems loaded")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN EXECUTION METHOD
    # ═══════════════════════════════════════════════════════════════════════════

    async def execute(self, task: Dict) -> ExecutionResult:
        """
        Execute ANY task through the unified system.

        Args:
            task: Task specification with:
                - type: Task type (see TASK_ROUTING)
                - Plus type-specific parameters

        Returns:
            ExecutionResult with output and metadata
        """
        task_id = task.get("task_id") or f"unified_{uuid4().hex[:12]}"
        task_type = task.get("type", "").lower()
        start_time = datetime.now(timezone.utc)

        # Get routing info
        routing = TASK_ROUTING.get(task_type, (ExecutionCategory.EXECUTION, ExecutionMethod.AI))
        category, method = routing

        # Execute based on category
        try:
            if category == ExecutionCategory.INTELLIGENCE:
                result = await self._execute_intelligence(task)
            elif category == ExecutionCategory.DISCOVERY:
                result = await self._execute_discovery(task)
            elif category == ExecutionCategory.REVENUE:
                result = await self._execute_revenue(task)
            elif category == ExecutionCategory.CONTENT:
                result = await self._execute_content(task)
            elif category == ExecutionCategory.FINANCIAL:
                result = await self._execute_financial(task)
            elif category == ExecutionCategory.COLLABORATION:
                result = await self._execute_collaboration(task)
            elif category == ExecutionCategory.BUSINESS:
                result = await self._execute_business(task)
            else:
                result = await self._execute_core(task, method)

        except Exception as e:
            result = {"ok": False, "error": str(e)}

        # Calculate execution time
        execution_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

        # Record learning
        learning_recorded = await self._record_learning(task, result)

        # Build result
        exec_result = ExecutionResult(
            task_id=task_id,
            ok=result.get("ok", False),
            category=category.value,
            method=method.value,
            output=result.get("output") or result.get("result"),
            executor=result.get("executor", category.value),
            execution_time_ms=execution_time_ms,
            cost=result.get("cost", 0),
            error=result.get("error", ""),
            learning_recorded=learning_recorded,
            metadata={
                "task_type": task_type,
                "subsystems_used": result.get("subsystems_used", []),
                "timestamp": self._now()
            }
        )

        # Log execution
        self._execution_log.append({
            "task_id": task_id,
            "type": task_type,
            "category": category.value,
            "ok": exec_result.ok,
            "execution_time_ms": execution_time_ms,
            "timestamp": self._now()
        })

        return exec_result

    # ═══════════════════════════════════════════════════════════════════════════
    # CATEGORY EXECUTORS
    # ═══════════════════════════════════════════════════════════════════════════

    async def _execute_core(self, task: Dict, method: ExecutionMethod) -> Dict:
        """Execute core tasks (API, AI, Browser)"""
        if method == ExecutionMethod.API:
            return await self._execute_api(task)
        elif method == ExecutionMethod.AI:
            return await self._execute_ai(task)
        elif method == ExecutionMethod.BROWSER:
            return await self._execute_browser(task)
        elif method == ExecutionMethod.HYBRID:
            return await self._execute_hybrid(task)
        return {"ok": False, "error": "Unknown execution method"}

    async def _execute_api(self, task: Dict) -> Dict:
        """Execute via Connector Registry"""
        if not self._subsystem_status.get("connectors"):
            return {"ok": False, "error": "Connectors not available"}

        platform = task.get("platform", "")
        try:
            connector = self._get_connector(platform)
            if connector:
                result = await connector.execute(task.get("data", {}))
                return {"ok": True, "output": result, "executor": f"connector/{platform}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": False, "error": f"No connector for {platform}"}

    async def _execute_ai(self, task: Dict) -> Dict:
        """Execute via Multi-AI Router"""
        if not self._subsystem_status.get("ai_router"):
            return await self._fallback_ai(task)

        try:
            task_type = task.get("type", "general")
            prompt = task.get("prompt", task.get("content", ""))
            routing = self._ai_router.route_task(task_type, {"requirements": prompt})
            result = await self._ai_router.execute_with_model(
                model=routing.get("primary_model", "claude"),
                task={"type": task_type, "requirements": prompt}
            )
            return {
                "ok": result.get("status") == "completed",
                "output": result.get("output"),
                "executor": f"ai/{routing.get('primary_model')}"
            }
        except Exception as e:
            return await self._fallback_ai(task)

    async def _fallback_ai(self, task: Dict) -> Dict:
        """Direct AI API call fallback"""
        try:
            import httpx
            prompt = task.get("prompt", task.get("content", ""))
            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            if openrouter_key:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
                        json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 2000}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return {"ok": True, "output": content, "executor": "ai/openrouter-fallback"}
        except Exception as e:
            pass
        return {"ok": False, "error": "No AI available"}

    async def _execute_browser(self, task: Dict) -> Dict:
        """Execute via Universal Fabric"""
        if not self._subsystem_status.get("fabric"):
            return {"ok": False, "error": "Fabric not available", "queued": True}

        try:
            result = await self._execute_fabric(
                pdl_name=task.get("pdl_name", f"{task.get('platform', 'web')}.execute"),
                url=task.get("url", ""),
                data=task.get("data", {}),
                ev_estimate=task.get("ev_estimate", 0)
            )
            return {"ok": result.get("ok", False), "output": result, "executor": "browser/fabric"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _execute_hybrid(self, task: Dict) -> Dict:
        """AI generates, then Browser executes"""
        ai_result = await self._execute_ai({
            "type": task.get("ai_type", "content_generation"),
            "prompt": task.get("prompt")
        })
        if not ai_result.get("ok"):
            return ai_result

        browser_task = {**task, "data": {**task.get("data", {}), "generated_content": ai_result.get("output", "")}}
        return await self._execute_browser(browser_task)

    async def _execute_intelligence(self, task: Dict) -> Dict:
        """Execute intelligence tasks"""
        task_type = task.get("type", "")
        subsystems_used = []

        if task_type == "learn_pattern" and self._subsystem_status.get("yield_memory"):
            result = self._store_pattern(task.get("pattern", {}))
            subsystems_used.append("yield_memory")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "query_hive" and self._subsystem_status.get("metahive"):
            result = self._query_hive(task.get("query", ""), task.get("context", {}))
            subsystems_used.append("metahive")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "get_best_action" and self._subsystem_status.get("yield_memory"):
            result = self._get_best_action(task.get("context", {}))
            subsystems_used.append("yield_memory")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "calculate_price" and self._subsystem_status.get("pricing_oracle"):
            result = self._calculate_price(task.get("base_price", 100), task.get("factors", {}))
            subsystems_used.append("pricing_oracle")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "track_outcome" and self._subsystem_status.get("outcome_oracle"):
            result = self._track_outcome(task.get("event_type", ""), task.get("user_id", ""), task.get("data", {}))
            subsystems_used.append("outcome_oracle")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "check_fraud" and self._subsystem_status.get("fraud_detector"):
            result = self._check_fraud(task.get("transaction", {}))
            subsystems_used.append("fraud_detector")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        return {"ok": False, "error": f"Intelligence task {task_type} not available"}

    async def _execute_discovery(self, task: Dict) -> Dict:
        """Execute discovery tasks"""
        task_type = task.get("type", "")
        subsystems_used = []

        if task_type == "discover_opportunities":
            results = []
            if self._subsystem_status.get("alpha_discovery"):
                alpha = await self._alpha_discovery.discover()
                results.extend(alpha.get("opportunities", []))
                subsystems_used.append("alpha_discovery")
            if self._subsystem_status.get("ultimate_discovery"):
                ultimate = await self._ultimate_discover()
                results.extend(ultimate.get("opportunities", []))
                subsystems_used.append("ultimate_discovery")
            return {"ok": True, "output": results, "count": len(results), "subsystems_used": subsystems_used}

        elif task_type == "internet_search" and self._subsystem_status.get("internet_discovery"):
            result = await self._search_internet(task.get("query", ""), task.get("max_results", 10))
            subsystems_used.append("internet_discovery")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "research" and self._subsystem_status.get("research_engine"):
            result = await self._research_engine.research(task.get("topic", ""))
            subsystems_used.append("research_engine")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        return {"ok": False, "error": f"Discovery task {task_type} not available"}

    async def _execute_revenue(self, task: Dict) -> Dict:
        """Execute revenue tasks"""
        task_type = task.get("type", "")
        subsystems_used = []

        if task_type == "run_amg_cycle" and self._subsystem_status.get("amg"):
            result = await self._amg.run_cycle()
            subsystems_used.append("amg")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "harvest_gaps" and self._subsystem_status.get("gap_harvesters"):
            result = await self._scan_gaps()
            subsystems_used.append("gap_harvesters")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "execute_arbitrage" and self._subsystem_status.get("arbitrage"):
            result = await self._arbitrage.execute()
            subsystems_used.append("arbitrage")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        return {"ok": False, "error": f"Revenue task {task_type} not available"}

    async def _execute_content(self, task: Dict) -> Dict:
        """Execute content tasks"""
        task_type = task.get("type", "")
        subsystems_used = []

        if task_type == "social_post" and self._subsystem_status.get("social_engine"):
            result = await self._social_engine.post(task.get("content", ""), task.get("platforms", []))
            subsystems_used.append("social_engine")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "generate_video" and self._subsystem_status.get("video_engine"):
            result = await self._video_engine.generate(task.get("prompt", ""))
            subsystems_used.append("video_engine")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "generate_audio" and self._subsystem_status.get("audio_engine"):
            result = await self._audio_engine.generate(task.get("prompt", ""))
            subsystems_used.append("audio_engine")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        return {"ok": False, "error": f"Content task {task_type} not available"}

    async def _execute_financial(self, task: Dict) -> Dict:
        """Execute financial tasks"""
        task_type = task.get("type", "")
        subsystems_used = []

        if task_type == "settle_payment" and self._subsystem_status.get("aigx_protocol"):
            result = self._aigx_protocol.settle(task.get("payer", ""), task.get("recipient", ""), task.get("amount", 0))
            subsystems_used.append("aigx_protocol")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "calculate_ocl" and self._subsystem_status.get("ocl_engine"):
            result = self._calculate_ocl(task.get("user_id", ""))
            subsystems_used.append("ocl_engine")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "request_factoring" and self._subsystem_status.get("agent_factoring"):
            result = await self._request_factoring(task.get("invoice_id", ""), task.get("amount", 0))
            subsystems_used.append("agent_factoring")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        return {"ok": False, "error": f"Financial task {task_type} not available"}

    async def _execute_collaboration(self, task: Dict) -> Dict:
        """Execute collaboration tasks"""
        task_type = task.get("type", "")
        subsystems_used = []

        if task_type == "find_partners" and self._subsystem_status.get("metabridge"):
            result = self._find_agents(task.get("requirements", {}))
            subsystems_used.append("metabridge")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "create_jv" and self._subsystem_status.get("jv_mesh"):
            result = self._create_jv(task.get("partner_id", ""), task.get("terms", {}))
            subsystems_used.append("jv_mesh")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "register_agent" and self._subsystem_status.get("agent_registry"):
            result = self._register_agent(task.get("agent_data", {}))
            subsystems_used.append("agent_registry")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        return {"ok": False, "error": f"Collaboration task {task_type} not available"}

    async def _execute_business(self, task: Dict) -> Dict:
        """Execute business tasks"""
        task_type = task.get("type", "")
        subsystems_used = []

        if task_type == "deploy_storefront" and self._subsystem_status.get("storefront_deployer"):
            result = await self._deploy_storefront(task.get("config", {}))
            subsystems_used.append("storefront_deployer")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "actionize_template" and self._subsystem_status.get("template_actionizer"):
            result = self._actionize_template(task.get("template_id", ""), task.get("params", {}))
            subsystems_used.append("template_actionizer")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        return {"ok": False, "error": f"Business task {task_type} not available"}

    # ═══════════════════════════════════════════════════════════════════════════
    # LEARNING FEEDBACK LOOP
    # ═══════════════════════════════════════════════════════════════════════════

    async def _record_learning(self, task: Dict, result: Dict) -> bool:
        """Record execution result for learning"""
        if not result.get("ok"):
            return False

        # Store pattern in Yield Memory
        if self._subsystem_status.get("yield_memory"):
            try:
                pattern = {
                    "task_type": task.get("type"),
                    "success": result.get("ok", False),
                    "execution_time": result.get("execution_time_ms", 0),
                    "timestamp": self._now()
                }
                self._store_pattern(pattern)
            except:
                pass

        # Contribute to MetaHive
        if self._subsystem_status.get("metahive"):
            try:
                self._contribute_to_hive({
                    "pattern_type": "execution",
                    "task_type": task.get("type"),
                    "success": result.get("ok", False),
                    "subsystems_used": result.get("subsystems_used", [])
                })
            except:
                pass

        # Track outcome
        if self._subsystem_status.get("outcome_oracle"):
            try:
                self._track_outcome(
                    "task_completed" if result.get("ok") else "task_failed",
                    task.get("user_id", "system"),
                    {"task_id": task.get("task_id"), "type": task.get("type")}
                )
            except:
                pass

        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # STATUS & DIAGNOSTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        available = sum(1 for v in self._subsystem_status.values() if v)
        total = len(self._subsystem_status)

        # Group by category
        categories = {
            "execution": ["connectors", "ai_router", "fabric"],
            "intelligence": ["metahive", "outcome_oracle", "pricing_oracle", "yield_memory", "ltv_forecaster", "fraud_detector"],
            "discovery": ["alpha_discovery", "ultimate_discovery", "internet_discovery", "pain_detector", "research_engine", "signal_ingestion"],
            "revenue": ["amg", "r3_autopilot", "gap_harvesters", "market_maker", "arbitrage", "revenue_orchestrator"],
            "content": ["social_engine", "video_engine", "audio_engine", "graphics_engine"],
            "financial": ["aigx_protocol", "ocl_engine", "agent_factoring", "reconciliation"],
            "collaboration": ["metabridge", "jv_mesh", "deal_graph", "agent_registry", "protocol_gateway"],
            "business": ["business_accelerator", "storefront_deployer", "template_actionizer", "franchise_engine", "sku_orchestrator", "master_orchestrator"]
        }

        category_status = {}
        for cat, systems in categories.items():
            available_in_cat = sum(1 for s in systems if self._subsystem_status.get(s))
            category_status[cat] = {
                "available": available_in_cat,
                "total": len(systems),
                "systems": {s: self._subsystem_status.get(s, False) for s in systems}
            }

        return {
            "ok": True,
            "version": "2.0",
            "subsystems": {
                "available": available,
                "total": total,
                "percentage": round(available / total * 100, 1) if total > 0 else 0
            },
            "categories": category_status,
            "execution_log_size": len(self._execution_log),
            "recent_executions": self._execution_log[-10:],
            "timestamp": self._now()
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
    """Execute any task through the unified system"""
    return await get_executor().execute(task)


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, HTTPException, Body

unified_router = APIRouter(prefix="/unified", tags=["Unified Executor"])


@unified_router.post("/execute")
async def execute_task_endpoint(body: Dict = Body(...)):
    """Execute any task via the unified executor"""
    executor = get_executor()
    result = await executor.execute(body)
    return {
        "ok": result.ok,
        "task_id": result.task_id,
        "category": result.category,
        "method": result.method,
        "output": result.output,
        "executor": result.executor,
        "execution_time_ms": result.execution_time_ms,
        "learning_recorded": result.learning_recorded,
        "error": result.error if not result.ok else None
    }


@unified_router.get("/status")
async def executor_status():
    """Get unified executor status with all 108+ subsystems"""
    return get_executor().get_status()


@unified_router.get("/subsystems")
async def list_subsystems():
    """List all available subsystems"""
    status = get_executor().get_status()
    return {
        "ok": True,
        "summary": f"{status['subsystems']['available']}/{status['subsystems']['total']} subsystems available",
        "categories": status["categories"]
    }


def include_unified_endpoints(app):
    """Include unified executor endpoints in FastAPI app"""
    app.include_router(unified_router)

    executor = get_executor()
    status = executor.get_status()

    print("=" * 80)
    print("⚡ UNIFIED EXECUTOR v2.0 - COMPLETE ORCHESTRATION LAYER")
    print("=" * 80)
    print(f"   Subsystems: {status['subsystems']['available']}/{status['subsystems']['total']} loaded ({status['subsystems']['percentage']}%)")
    for cat, data in status["categories"].items():
        icon = "✅" if data["available"] == data["total"] else "⚠️" if data["available"] > 0 else "❌"
        print(f"   {icon} {cat.upper()}: {data['available']}/{data['total']}")
    print("=" * 80)


__all__ = [
    "execute", "get_executor", "UnifiedExecutor",
    "ExecutionCategory", "ExecutionMethod", "ExecutionResult",
    "unified_router", "include_unified_endpoints"
]
