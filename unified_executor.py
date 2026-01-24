"""
═══════════════════════════════════════════════════════════════════════════════
UNIFIED EXECUTOR v3.0 - MANAGER PATTERN ORCHESTRATION
═══════════════════════════════════════════════════════════════════════════════

NOW COORDINATING 60+ SUBSYSTEMS VIA 5 SPECIALIZED MANAGERS:

1. REVENUE MANAGER (11 subsystems)
   - OCL P2P Lending, Securitization Desk, Performance Bonds
   - Outcomes Insurance, OCL Expansion, Insurance Pool
   - Flow Arbitrage, Idle Arbitrage, Affiliate Matching
   - Lead Exchange, Auto Hedge

2. FINANCIAL MANAGER (8 subsystems) + OCL P2P
   - OCL P2P Lending (AI-to-AI internal lending)
   - OCL Engine, OCL Expansion, Performance Bonds
   - Securitization Desk, Outcomes Insurance, Insurance Pool
   - Agent Factoring

3. EXECUTION MANAGER (10 subsystems)
   - Fiverr Automation, Deliverable Verification, Compliance Oracle
   - One-Tap Widget, Direct Outreach, Proposal Generator
   - Platform APIs, Fabric, AI Router, Connectors

4. DISCOVERY MANAGER (15 subsystems)
   - Alpha Discovery, Ultimate Discovery, Spawn Engine
   - Internet Domination, Flow Arbitrage, Pain Detector
   - Signal Ingestion, Research Engine, Industry Knowledge
   - Advanced Dimensions, Deal Graph, Affiliate Matching
   - Direct Outreach, Internet Search, Idle Arbitrage

5. INTELLIGENCE MANAGER (10 subsystems)
   - MetaHive Brain, Outcome Oracle, Pricing Oracle
   - Yield Memory, LTV Forecaster, Fraud Detector
   - Pricing Autopilot, Success Predictor
   - Adaptive Aggression, SLO Policy

AUTONOMOUS CYCLE (10-PHASE):
1. DISCOVER → 15+ sources
2. ENRICH → Deal Graph network
3. SCORE → Intelligence scoring
4. FINANCE → OCL P2P if needed
5. REVENUE → Revenue opportunities
6. EXECUTE → Top 20 opportunities
7. VERIFY → Deliverable verification
8. REVENUE FLOWS → Execute revenue
9. RECONCILE → Financial tracking
10. LEARN → Pattern storage

Updated: Jan 2026 - v3.0 Manager Pattern Architecture
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
# MANAGER IMPORTS (60+ subsystems coordinated via 5 managers)
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from managers.revenue_manager import RevenueManager, get_revenue_manager
    REVENUE_MANAGER_AVAILABLE = True
except ImportError:
    REVENUE_MANAGER_AVAILABLE = False
    logger.warning("RevenueManager not available")

try:
    from managers.financial_manager import FinancialManager, get_financial_manager
    FINANCIAL_MANAGER_AVAILABLE = True
except ImportError:
    FINANCIAL_MANAGER_AVAILABLE = False
    logger.warning("FinancialManager not available")

try:
    from managers.execution_manager import ExecutionManager, get_execution_manager
    EXECUTION_MANAGER_AVAILABLE = True
except ImportError:
    EXECUTION_MANAGER_AVAILABLE = False
    logger.warning("ExecutionManager not available")

try:
    from managers.discovery_manager import DiscoveryManager, get_discovery_manager
    DISCOVERY_MANAGER_AVAILABLE = True
except ImportError:
    DISCOVERY_MANAGER_AVAILABLE = False
    logger.warning("DiscoveryManager not available")

try:
    from managers.intelligence_manager import IntelligenceManager, get_intelligence_manager
    INTELLIGENCE_MANAGER_AVAILABLE = True
except ImportError:
    INTELLIGENCE_MANAGER_AVAILABLE = False
    logger.warning("IntelligenceManager not available")


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
        self._manager_status: Dict[str, bool] = {}

        # Initialize 5 specialized managers (60+ subsystems)
        self._init_managers()

        # Initialize legacy subsystems (backward compatibility)
        self._init_all_subsystems()

    def _init_managers(self):
        """Initialize all 5 specialized managers"""

        # Revenue Manager (11 subsystems)
        if REVENUE_MANAGER_AVAILABLE:
            try:
                self.revenue_mgr = get_revenue_manager()
                self._manager_status["revenue_manager"] = True
            except Exception as e:
                logger.warning(f"Revenue manager init failed: {e}")
                self._manager_status["revenue_manager"] = False
        else:
            self._manager_status["revenue_manager"] = False

        # Financial Manager (8 subsystems + OCL P2P)
        if FINANCIAL_MANAGER_AVAILABLE:
            try:
                self.financial_mgr = get_financial_manager()
                self._manager_status["financial_manager"] = True
            except Exception as e:
                logger.warning(f"Financial manager init failed: {e}")
                self._manager_status["financial_manager"] = False
        else:
            self._manager_status["financial_manager"] = False

        # Execution Manager (10 subsystems)
        if EXECUTION_MANAGER_AVAILABLE:
            try:
                self.execution_mgr = get_execution_manager()
                self._manager_status["execution_manager"] = True
            except Exception as e:
                logger.warning(f"Execution manager init failed: {e}")
                self._manager_status["execution_manager"] = False
        else:
            self._manager_status["execution_manager"] = False

        # Discovery Manager (15 subsystems)
        if DISCOVERY_MANAGER_AVAILABLE:
            try:
                self.discovery_mgr = get_discovery_manager()
                self._manager_status["discovery_manager"] = True
            except Exception as e:
                logger.warning(f"Discovery manager init failed: {e}")
                self._manager_status["discovery_manager"] = False
        else:
            self._manager_status["discovery_manager"] = False

        # Intelligence Manager (10 subsystems)
        if INTELLIGENCE_MANAGER_AVAILABLE:
            try:
                self.intelligence_mgr = get_intelligence_manager()
                self._manager_status["intelligence_manager"] = True
            except Exception as e:
                logger.warning(f"Intelligence manager init failed: {e}")
                self._manager_status["intelligence_manager"] = False
        else:
            self._manager_status["intelligence_manager"] = False

        # Log manager status
        managers_loaded = sum(1 for v in self._manager_status.values() if v)
        logger.info(f"Managers initialized: {managers_loaded}/5")

        # Initialize 8 orchestrators (higher-level coordination)
        self._init_orchestrators()

    def _init_orchestrators(self):
        """Initialize 8 orchestrators for higher-level coordination"""
        self._orchestrators: Dict[str, Any] = {}

        # 1. V106 Integration Orchestrator
        try:
            from v106_integration_orchestrator import V106Integrator
            self._orchestrators["v106"] = V106Integrator()
            logger.info("V106 Integrator loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"V106 Integrator not available: {e}")

        # 2. Week2 Master Orchestrator (requires graphics_engine - skip for now)
        try:
            from week2_master_orchestrator import initialize_week2_system
            self._orchestrators["week2_master"] = {"init_func": initialize_week2_system}
            logger.info("Week2 Master Orchestrator registered (lazy init)")
        except (ImportError, Exception) as e:
            logger.warning(f"Week2 Master Orchestrator not available: {e}")

        # 3. Master Autonomous Orchestrator
        try:
            from master_autonomous_orchestrator import get_master_orchestrator
            self._orchestrators["master_autonomous"] = get_master_orchestrator()
            logger.info("Master Autonomous Orchestrator loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"Master Autonomous Orchestrator not available: {e}")

        # 4. Universal Revenue Orchestrator
        try:
            from universal_revenue_orchestrator import get_revenue_orchestrator
            self._orchestrators["revenue_orchestrator"] = get_revenue_orchestrator()
            logger.info("Universal Revenue Orchestrator loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"Universal Revenue Orchestrator not available: {e}")

        # 5. AMG Orchestrator
        try:
            from amg_orchestrator import AMGOrchestrator
            self._orchestrators["amg"] = AMGOrchestrator()
            logger.info("AMG Orchestrator loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"AMG Orchestrator not available: {e}")

        # 6. Execution Orchestrator
        try:
            from execution_orchestrator import get_orchestrator as get_exec_orchestrator
            self._orchestrators["execution_orch"] = get_exec_orchestrator()
            logger.info("Execution Orchestrator loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"Execution Orchestrator not available: {e}")

        # 7. R3 Autopilot
        try:
            from r3_autopilot import create_autopilot_strategy, execute_autopilot_spend
            self._orchestrators["r3"] = {
                "create_strategy": create_autopilot_strategy,
                "execute_spend": execute_autopilot_spend
            }
            logger.info("R3 Autopilot loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"R3 Autopilot not available: {e}")

        # 8. C-Suite Orchestrator
        try:
            from csuite_orchestrator import get_orchestrator as get_csuite_orchestrator
            self._orchestrators["csuite"] = get_csuite_orchestrator()
            logger.info("C-Suite Orchestrator loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"C-Suite Orchestrator not available: {e}")

        # Log orchestrator status
        orchestrators_loaded = len(self._orchestrators)
        logger.info(f"Orchestrators initialized: {orchestrators_loaded}/8")

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

        # Autonomous Upgrades (self-evolution)
        try:
            from autonomous_upgrades import (
                suggest_next_upgrade,
                create_ab_test,
                get_active_tests,
                deploy_logic_upgrade,
                UPGRADE_TYPES
            )
            self._suggest_upgrade = suggest_next_upgrade
            self._create_test = create_ab_test
            self._get_tests = get_active_tests
            self._deploy_upgrade = deploy_logic_upgrade
            self._upgrade_types = UPGRADE_TYPES
            self._upgrade_tests = []  # State storage for tests
            self._subsystem_status["auto_upgrades"] = True
        except (ImportError, Exception):
            self._subsystem_status["auto_upgrades"] = False

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

        # Auto-Spawn Engine (AI Venture Factory)
        try:
            from auto_spawn_engine import get_spawn_engine, AutoSpawnEngine
            self._spawn_engine = get_spawn_engine()
            self._subsystem_status["spawn_engine"] = True
        except (ImportError, Exception):
            self._subsystem_status["spawn_engine"] = False

        # Internet Domination Engine
        try:
            from internet_domination_engine import domination_scan_all, get_domination_opportunities
            self._domination_scan = domination_scan_all
            self._get_domination_opps = get_domination_opportunities
            self._subsystem_status["internet_domination"] = True
        except (ImportError, Exception):
            self._subsystem_status["internet_domination"] = False

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

        # Autonomous Reconciliation Engine (enhanced financial truth)
        try:
            from autonomous_reconciliation_engine import reconciliation_engine as auto_recon
            self._auto_reconciliation = auto_recon
            self._subsystem_status["auto_reconciliation"] = True
        except (ImportError, Exception):
            self._subsystem_status["auto_reconciliation"] = False

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
            from master_autonomous_orchestrator import MasterAutonomousOrchestrator
            self._master_orchestrator = MasterAutonomousOrchestrator
            self._subsystem_status["master_orchestrator"] = True
        except (ImportError, Exception):
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
            # Alpha Discovery
            if self._subsystem_status.get("alpha_discovery"):
                try:
                    alpha = await self._alpha_discovery.discover()
                    results.extend(alpha.get("opportunities", []))
                    subsystems_used.append("alpha_discovery")
                except Exception as e:
                    logger.warning(f"Alpha discovery error: {e}")
            # Ultimate Discovery
            if self._subsystem_status.get("ultimate_discovery"):
                try:
                    ultimate = await self._ultimate_discover()
                    results.extend(ultimate.get("opportunities", []))
                    subsystems_used.append("ultimate_discovery")
                except Exception as e:
                    logger.warning(f"Ultimate discovery error: {e}")
            # Spawn Engine (AI Venture Factory)
            if self._subsystem_status.get("spawn_engine"):
                try:
                    # Use detector to scan for trend signals (opportunities)
                    if hasattr(self._spawn_engine, 'detector'):
                        signals = await self._spawn_engine.detector.scan_all_sources()
                        for sig in signals[:20]:
                            results.append({
                                "type": "spawn_opportunity",
                                "source": "spawn_engine",
                                "ev": getattr(sig, 'opportunity_score', 50),
                                "query": getattr(sig, 'query', '')[:100],
                                "platform": getattr(sig, 'source', 'unknown')
                            })
                        subsystems_used.append("spawn_engine")
                except Exception as e:
                    logger.warning(f"Spawn engine error: {e}")
            # Internet Domination Engine
            if self._subsystem_status.get("internet_domination"):
                try:
                    inet_opps = await self._get_domination_opps(limit=30)
                    results.extend(inet_opps if isinstance(inet_opps, list) else [])
                    subsystems_used.append("internet_domination")
                except Exception as e:
                    logger.warning(f"Internet domination error: {e}")
            # Deal Graph (relationship-based opportunities)
            if self._subsystem_status.get("deal_graph"):
                try:
                    if hasattr(self._deal_graph, 'get_intro_opportunities'):
                        intro_opps = self._deal_graph.get_intro_opportunities(limit=20)
                        for intro in intro_opps:
                            results.append({
                                "type": "relationship_intro",
                                "source": "deal_graph",
                                "ev": getattr(intro, 'expected_value', 50),
                                "data": intro.__dict__ if hasattr(intro, '__dict__') else intro
                            })
                        subsystems_used.append("deal_graph")
                except Exception as e:
                    logger.warning(f"Deal graph error: {e}")
            return {"ok": True, "output": results, "count": len(results), "subsystems_used": subsystems_used}

        elif task_type == "spawn_business" and self._subsystem_status.get("spawn_engine"):
            result = await self._spawn_engine.run_full_cycle()
            subsystems_used.append("spawn_engine")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

        elif task_type == "internet_dominate" and self._subsystem_status.get("internet_domination"):
            result = await self._domination_scan()
            subsystems_used.append("internet_domination")
            return {"ok": True, "output": result, "subsystems_used": subsystems_used}

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
                self._store_pattern(
                    username=task.get("user_id", "system"),
                    pattern_type="task_execution",
                    context={"timestamp": self._now()},
                    action={"type": task.get("type"), "task_id": task.get("task_id")},
                    outcome={"success": result.get("ok", False), "execution_time": result.get("execution_time_ms", 0)}
                )
            except:
                pass

        # Contribute to MetaHive (async, but wrapped in try/except)
        if self._subsystem_status.get("metahive"):
            try:
                # Note: This is async but called without await in sync context
                # The contribution will happen in background
                asyncio.create_task(self._contribute_to_hive(
                    username=task.get("user_id", "system"),
                    pattern_type="task_execution",
                    context={"task_type": task.get("type")},
                    action={"subsystems_used": result.get("subsystems_used", [])},
                    outcome={"success": result.get("ok", False)}
                ))
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
    # AUTONOMOUS INTERCONNECTION - All systems feeding into each other
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_autonomous_cycle(self) -> Dict[str, Any]:
        """
        Run a complete autonomous cycle with all systems interconnected:

        1. DISCOVER → Find opportunities from all sources
        2. PRIORITIZE → Use MetaHive + Deal Graph for scoring
        3. EXECUTE → Run through Fabric + Connectors
        4. RECONCILE → Track finances through Reconciliation
        5. LEARN → Feed back to MetaHive + Yield Memory + Upgrades
        """
        cycle_id = f"cycle_{uuid4().hex[:8]}"
        start_time = datetime.now(timezone.utc)
        results = {
            "cycle_id": cycle_id,
            "phases": {},
            "total_opportunities": 0,
            "actions_taken": 0,
            "revenue_tracked": 0.0,
            "learnings_recorded": 0,
            "subsystems_used": []
        }

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 1: DISCOVERY (All sources)
        # ═══════════════════════════════════════════════════════════════════
        try:
            discovery_result = await self._execute_discovery({"type": "discover_opportunities"})
            opportunities = discovery_result.get("output", [])
            results["phases"]["discovery"] = {
                "ok": True,
                "count": len(opportunities),
                "sources": discovery_result.get("subsystems_used", [])
            }
            results["total_opportunities"] = len(opportunities)
            results["subsystems_used"].extend(discovery_result.get("subsystems_used", []))
        except Exception as e:
            results["phases"]["discovery"] = {"ok": False, "error": str(e)}
            opportunities = []

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 2: PRIORITIZATION (MetaHive + Deal Graph + Outcome Oracle)
        # ═══════════════════════════════════════════════════════════════════
        prioritized = []
        try:
            for opp in opportunities[:50]:  # Limit to top 50
                score = opp.get("ev", opp.get("expected_value", 0))

                # Enhance with MetaHive patterns
                if self._subsystem_status.get("metahive"):
                    try:
                        pattern = self._query_hive(opp.get("type", "unknown"))
                        if pattern:
                            score *= (1 + pattern.get("success_rate", 0))
                    except:
                        pass

                # Enhance with Deal Graph network multiplier
                if self._subsystem_status.get("deal_graph") and hasattr(self._deal_graph, 'get_network_multiplier'):
                    try:
                        network_mult = self._deal_graph.get_network_multiplier(opp.get("entity_id"))
                        score *= network_mult
                    except:
                        pass

                # Enhance with Outcome Oracle probability
                if self._subsystem_status.get("outcome_oracle"):
                    try:
                        funnel_stats = self._get_funnel_stats(opp.get("user_id", "system"))
                        if funnel_stats:
                            score *= funnel_stats.get("conversion_rate", 0.5) + 0.5
                    except:
                        pass

                prioritized.append({**opp, "priority_score": score})

            prioritized.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
            results["phases"]["prioritization"] = {"ok": True, "count": len(prioritized)}
            results["subsystems_used"].extend(["metahive", "deal_graph", "outcome_oracle"])
        except Exception as e:
            results["phases"]["prioritization"] = {"ok": False, "error": str(e)}
            prioritized = opportunities[:20]

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 3: EXECUTION (Fabric + Connectors)
        # ═══════════════════════════════════════════════════════════════════
        executed = []
        try:
            # Execute top opportunities
            for opp in prioritized[:10]:  # Execute top 10
                if self._subsystem_status.get("fabric"):
                    try:
                        exec_result = await self.execute({
                            "type": "execute_opportunity",
                            "category": ExecutionCategory.EXECUTION.value,
                            "opportunity": opp
                        })
                        if exec_result.ok:
                            executed.append({"opportunity": opp, "result": exec_result.output})
                            results["actions_taken"] += 1
                    except:
                        pass

            results["phases"]["execution"] = {"ok": True, "count": len(executed)}
            results["subsystems_used"].append("fabric")
        except Exception as e:
            results["phases"]["execution"] = {"ok": False, "error": str(e)}

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 4: RECONCILIATION (Track all financial activity)
        # ═══════════════════════════════════════════════════════════════════
        try:
            if self._subsystem_status.get("auto_reconciliation"):
                for exec_item in executed:
                    result = exec_item.get("result")
                    revenue = result.get("revenue", 0) if isinstance(result, dict) else 0
                    if revenue > 0:
                        self._auto_reconciliation.record_activity(
                            activity_type="execution",
                            gross_revenue=revenue,
                            path="path_a",
                            metadata={"cycle_id": cycle_id, "opportunity": exec_item.get("opportunity", {})}
                        )
                        results["revenue_tracked"] += revenue

                results["phases"]["reconciliation"] = {"ok": True, "revenue": results["revenue_tracked"]}
                results["subsystems_used"].append("auto_reconciliation")

                # Feed reconciliation data back to Outcome Oracle
                if self._subsystem_status.get("outcome_oracle") and results["revenue_tracked"] > 0:
                    self._credit_aigx("system", results["revenue_tracked"] * 0.1)  # 10% to AIGx
        except Exception as e:
            results["phases"]["reconciliation"] = {"ok": False, "error": str(e)}

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 5: LEARNING (MetaHive + Yield Memory + Upgrades)
        # ═══════════════════════════════════════════════════════════════════
        try:
            # Store patterns in Yield Memory
            if self._subsystem_status.get("yield_memory"):
                for exec_item in executed:
                    opp = exec_item.get("opportunity", {})
                    result = exec_item.get("result")
                    revenue = result.get("revenue", 0) if isinstance(result, dict) else 0
                    opp_type = opp.get("type") if isinstance(opp, dict) else "unknown"
                    self._store_pattern(
                        username="system",
                        pattern_type="autonomous_execution",
                        context={"cycle_id": cycle_id, "source": opp.get("source", "unknown") if isinstance(opp, dict) else "unknown"},
                        action={"type": opp_type, "opportunity": opp if isinstance(opp, dict) else str(opp)},
                        outcome={"success": True, "revenue": revenue}
                    )
                    results["learnings_recorded"] += 1

            # Contribute patterns to MetaHive
            if self._subsystem_status.get("metahive"):
                await self._contribute_to_hive(
                    username="system",
                    pattern_type="autonomous_cycle",
                    context={"cycle_id": cycle_id, "opportunities_found": len(opportunities)},
                    action={"actions_taken": len(executed)},
                    outcome={"revenue": results["revenue_tracked"], "success": True}
                )
                results["learnings_recorded"] += 1

            # Suggest upgrades based on outcomes
            if self._subsystem_status.get("auto_upgrades") and executed:
                try:
                    # Build user-like records from executed outcomes
                    simulated_users = [{
                        "intents": [exec_item.get("opportunity", {}).get("type", "unknown")],
                        "role": "agent",
                        "revenue": (exec_item.get("result") or {}).get("revenue", 0) if isinstance(exec_item.get("result"), dict) else 0
                    } for exec_item in executed]

                    suggestion = self._suggest_upgrade(simulated_users, self._upgrade_tests)
                    if suggestion:
                        results["phases"]["upgrade_suggestion"] = suggestion
                        results["learnings_recorded"] += 1
                except Exception as upgrade_err:
                    logger.warning(f"Upgrade suggestion skipped: {upgrade_err}")

            results["phases"]["learning"] = {"ok": True, "patterns_stored": results["learnings_recorded"]}
            results["subsystems_used"].extend(["yield_memory", "metahive", "auto_upgrades"])
        except Exception as e:
            results["phases"]["learning"] = {"ok": False, "error": str(e)}

        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        results["execution_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        results["timestamp"] = end_time.isoformat()
        results["subsystems_used"] = list(set(results["subsystems_used"]))

        return results

    # ═══════════════════════════════════════════════════════════════════════════
    # FULL AUTONOMOUS CYCLE (v3.0 - Using 5 Specialized Managers)
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_full_autonomous_cycle(self) -> Dict[str, Any]:
        """
        v3.0: Complete 10-phase autonomous cycle using ALL 60+ subsystems via managers.

        PHASES:
        1. DISCOVER → 15+ sources via DiscoveryManager
        2. ENRICH → Deal Graph network enrichment
        3. SCORE → Intelligence scoring via IntelligenceManager
        4. FINANCE → OCL P2P lending if needed via FinancialManager
        5. REVENUE → Revenue opportunities via RevenueManager
        6. EXECUTE → Execute top 20 via ExecutionManager
        7. VERIFY → Deliverable verification
        8. REVENUE FLOWS → Execute revenue streams
        9. RECONCILE → Financial tracking
        10. LEARN → Pattern storage and learning
        """
        cycle_id = f"full_cycle_{uuid4().hex[:8]}"
        start_time = datetime.now(timezone.utc)
        loan_id = None

        results = {
            "cycle_id": cycle_id,
            "version": "3.0",
            "phases": {},
            "total_opportunities": 0,
            "opportunities_scored": 0,
            "opportunities_executed": 0,
            "revenue_generated": 0.0,
            "revenue_streams": 0,
            "patterns_learned": 0,
            "internal_lending": None,
            "managers_used": [],
            "subsystems_used": 0
        }

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 1: DISCOVERY (15+ sources via DiscoveryManager)
        # ═══════════════════════════════════════════════════════════════════
        opportunities = []
        try:
            if self._manager_status.get("discovery_manager"):
                opportunities = await self.discovery_mgr.discover_all_sources()
                results["phases"]["discovery"] = {
                    "ok": True,
                    "count": len(opportunities),
                    "sources": self.discovery_mgr._sources_used
                }
                results["total_opportunities"] = len(opportunities)
                results["managers_used"].append("discovery_manager")
            else:
                # Fallback to legacy discovery
                discovery_result = await self._execute_discovery({"type": "discover_opportunities"})
                opportunities = discovery_result.get("output", [])
                results["phases"]["discovery"] = {"ok": True, "count": len(opportunities), "fallback": True}
        except Exception as e:
            results["phases"]["discovery"] = {"ok": False, "error": str(e)}

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 2: ENRICH (Deal Graph network enrichment)
        # ═══════════════════════════════════════════════════════════════════
        try:
            if self._manager_status.get("discovery_manager") and opportunities:
                opportunities = await self.discovery_mgr.enrich_with_network(opportunities)
                results["phases"]["enrichment"] = {"ok": True, "enriched": len(opportunities)}
            else:
                results["phases"]["enrichment"] = {"ok": True, "skipped": True}
        except Exception as e:
            results["phases"]["enrichment"] = {"ok": False, "error": str(e)}

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 3: SCORE (Intelligence scoring via IntelligenceManager)
        # ═══════════════════════════════════════════════════════════════════
        scored = []
        try:
            if self._manager_status.get("intelligence_manager") and opportunities:
                scored = await self.intelligence_mgr.score_opportunities(opportunities[:100])
                results["phases"]["scoring"] = {"ok": True, "scored": len(scored)}
                results["opportunities_scored"] = len(scored)
                results["managers_used"].append("intelligence_manager")
            else:
                # Fallback to simple scoring
                scored = sorted(opportunities[:50], key=lambda x: x.get("ev", 0), reverse=True)
                results["phases"]["scoring"] = {"ok": True, "count": len(scored), "fallback": True}
        except Exception as e:
            results["phases"]["scoring"] = {"ok": False, "error": str(e)}
            scored = opportunities[:20]

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 4: FINANCE (OCL P2P lending check via FinancialManager)
        # ═══════════════════════════════════════════════════════════════════
        try:
            if self._manager_status.get("financial_manager") and scored:
                # Estimate capital needed for top 20 opportunities
                capital_needed = sum(opp.get("budget", opp.get("ev", 50)) for opp in scored[:20])

                capital = await self.financial_mgr.check_capital_availability(capital_needed)
                results["phases"]["capital_check"] = {
                    "ok": True,
                    "needed": capital_needed,
                    "available": capital.get("direct_available", 0),
                    "can_fulfill": capital.get("can_fulfill", False)
                }

                # Arrange internal lending if needed
                if capital.get("needs_borrowing", 0) > 0:
                    loan = await self.financial_mgr.arrange_internal_lending(capital["needs_borrowing"])
                    loan_id = loan.get("id")
                    results["internal_lending"] = {
                        "borrowed": loan.get("total_borrowed", 0),
                        "loans": len(loan.get("loans", [])),
                        "facilitation_fees": loan.get("total_facilitation_fees", 0)
                    }
                    results["phases"]["internal_lending"] = {"ok": True, **results["internal_lending"]}

                results["managers_used"].append("financial_manager")
            else:
                results["phases"]["capital_check"] = {"ok": True, "skipped": True}
        except Exception as e:
            results["phases"]["capital_check"] = {"ok": False, "error": str(e)}

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 5: REVENUE OPPORTUNITIES (RevenueManager)
        # ═══════════════════════════════════════════════════════════════════
        revenue_opps = []
        try:
            if self._manager_status.get("revenue_manager"):
                revenue_opps = await self.revenue_mgr.discover_revenue_opportunities()
                results["phases"]["revenue_discovery"] = {"ok": True, "count": len(revenue_opps)}
                results["managers_used"].append("revenue_manager")
        except Exception as e:
            results["phases"]["revenue_discovery"] = {"ok": False, "error": str(e)}

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 6: EXECUTE (Top 20 via ExecutionManager with Fabric priority)
        # ═══════════════════════════════════════════════════════════════════
        executed = []
        execution_errors = []
        try:
            if self._manager_status.get("execution_manager") and scored:
                for opp in scored[:20]:
                    # Extract platform and URL from opportunity for fabric routing
                    platform = opp.get("platform") or opp.get("source", "").split("/")[0] or "unknown"
                    url = (opp.get("url") or opp.get("job_url") or opp.get("post_url") or
                           opp.get("link") or opp.get("data", {}).get("url", ""))

                    exec_result = await self.execution_mgr.execute_with_verification({
                        "type": opp.get("type", "opportunity"),
                        "platform": platform,
                        "url": url,
                        "action": opp.get("action", "execute"),
                        "title": opp.get("title", ""),
                        "description": opp.get("description", ""),
                        "content": opp.get("content", ""),
                        "ev": opp.get("ev", opp.get("value", 0)),
                        "data": opp,
                        "opportunity": opp,
                        "task_id": f"{cycle_id}_{uuid4().hex[:4]}"
                    })

                    method = exec_result.get("method", "unknown")
                    if exec_result.get("ok"):
                        executed.append({"opportunity": opp, "result": exec_result, "method": method})
                        results["opportunities_executed"] += 1
                        logger.info(f"✅ {platform} executed via {method}")
                    else:
                        execution_errors.append({
                            "platform": platform,
                            "error": exec_result.get("error", "Unknown"),
                            "method": method
                        })
                        logger.warning(f"❌ {platform} failed via {method}: {exec_result.get('error', '')[:50]}")

                results["phases"]["execution"] = {
                    "ok": True,
                    "attempted": min(20, len(scored)),
                    "succeeded": len(executed),
                    "failed": len(execution_errors),
                    "errors": execution_errors[:5]  # First 5 errors
                }
                results["managers_used"].append("execution_manager")
            else:
                results["phases"]["execution"] = {"ok": True, "skipped": True}
        except Exception as e:
            results["phases"]["execution"] = {"ok": False, "error": str(e)}

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 7: REVENUE FLOWS (Execute revenue streams)
        # ═══════════════════════════════════════════════════════════════════
        try:
            if self._manager_status.get("revenue_manager") and executed:
                for exec_item in executed:
                    flow_result = await self.revenue_mgr.execute_revenue_flow(exec_item.get("opportunity", {}))
                    if flow_result.get("ok"):
                        results["revenue_generated"] += flow_result.get("revenue", 0)
                        results["revenue_streams"] += 1

                # Track all revenue streams
                revenue_status = await self.revenue_mgr.track_revenue_streams()
                results["phases"]["revenue_flows"] = {
                    "ok": True,
                    "total_revenue": results["revenue_generated"],
                    "streams": results["revenue_streams"]
                }
        except Exception as e:
            results["phases"]["revenue_flows"] = {"ok": False, "error": str(e)}

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 8: LOAN SETTLEMENT (if internal lending was used)
        # ═══════════════════════════════════════════════════════════════════
        try:
            if loan_id and self._manager_status.get("financial_manager") and results["revenue_generated"] > 0:
                settlement = await self.financial_mgr.settle_loan(loan_id, results["revenue_generated"])
                results["phases"]["loan_settlement"] = {"ok": True, **settlement}
        except Exception as e:
            results["phases"]["loan_settlement"] = {"ok": False, "error": str(e)}

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 9: RECONCILIATION
        # ═══════════════════════════════════════════════════════════════════
        try:
            if self._subsystem_status.get("auto_reconciliation") and results["revenue_generated"] > 0:
                self._auto_reconciliation.record_activity(
                    activity_type="full_cycle",
                    gross_revenue=results["revenue_generated"],
                    path="path_a",
                    metadata={"cycle_id": cycle_id}
                )
                results["phases"]["reconciliation"] = {"ok": True, "revenue": results["revenue_generated"]}
        except Exception as e:
            results["phases"]["reconciliation"] = {"ok": False, "error": str(e)}

        # ═══════════════════════════════════════════════════════════════════
        # PHASE 10: LEARN (Pattern storage via IntelligenceManager)
        # ═══════════════════════════════════════════════════════════════════
        try:
            if self._manager_status.get("intelligence_manager") and executed:
                learning_results = await self.intelligence_mgr.learn_from_cycle(executed)
                results["patterns_learned"] = learning_results.get("patterns_learned", 0)
                results["phases"]["learning"] = {"ok": True, "patterns": results["patterns_learned"]}
        except Exception as e:
            results["phases"]["learning"] = {"ok": False, "error": str(e)}

        # Calculate totals
        end_time = datetime.now(timezone.utc)
        results["execution_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
        results["timestamp"] = end_time.isoformat()
        results["managers_used"] = list(set(results["managers_used"]))

        # Count total subsystems used
        subsystem_count = 0
        for mgr_name in results["managers_used"]:
            if mgr_name == "discovery_manager" and hasattr(self, 'discovery_mgr'):
                subsystem_count += sum(1 for v in self.discovery_mgr._subsystems.values() if v)
            elif mgr_name == "revenue_manager" and hasattr(self, 'revenue_mgr'):
                subsystem_count += sum(1 for v in self.revenue_mgr._subsystems.values() if v)
            elif mgr_name == "financial_manager" and hasattr(self, 'financial_mgr'):
                subsystem_count += sum(1 for v in self.financial_mgr._subsystems.values() if v)
            elif mgr_name == "execution_manager" and hasattr(self, 'execution_mgr'):
                subsystem_count += sum(1 for v in self.execution_mgr._subsystems.values() if v)
            elif mgr_name == "intelligence_manager" and hasattr(self, 'intelligence_mgr'):
                subsystem_count += sum(1 for v in self.intelligence_mgr._subsystems.values() if v)

        results["subsystems_used"] = subsystem_count

        return results

    # ═══════════════════════════════════════════════════════════════════════════
    # STATUS & DIAGNOSTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        available = sum(1 for v in self._subsystem_status.values() if v)
        total = len(self._subsystem_status)

        # Group by category (includes all autonomous subsystems)
        categories = {
            "execution": ["connectors", "ai_router", "fabric"],
            "intelligence": ["metahive", "outcome_oracle", "pricing_oracle", "yield_memory", "ltv_forecaster", "fraud_detector", "auto_upgrades"],
            "discovery": ["alpha_discovery", "ultimate_discovery", "internet_discovery", "pain_detector", "research_engine", "signal_ingestion", "spawn_engine", "internet_domination"],
            "revenue": ["amg", "r3_autopilot", "gap_harvesters", "market_maker", "arbitrage", "revenue_orchestrator"],
            "content": ["social_engine", "video_engine", "audio_engine", "graphics_engine"],
            "financial": ["aigx_protocol", "ocl_engine", "agent_factoring", "reconciliation", "auto_reconciliation"],
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

        # Get manager status
        manager_details = {}
        manager_subsystems = 0
        for mgr_name, available_flag in self._manager_status.items():
            if available_flag:
                mgr_attr = mgr_name.replace("_manager", "_mgr")
                if hasattr(self, mgr_attr):
                    mgr = getattr(self, mgr_attr)
                    if hasattr(mgr, '_subsystems'):
                        mgr_subs = sum(1 for v in mgr._subsystems.values() if v)
                        manager_subsystems += mgr_subs
                        manager_details[mgr_name] = {
                            "available": True,
                            "subsystems": mgr_subs,
                            "total": len(mgr._subsystems)
                        }
                    else:
                        manager_details[mgr_name] = {"available": True}
            else:
                manager_details[mgr_name] = {"available": False}

        return {
            "ok": True,
            "version": "3.0",
            "architecture": "Manager Pattern",
            "managers": {
                "available": sum(1 for v in self._manager_status.values() if v),
                "total": len(self._manager_status),
                "details": manager_details,
                "total_manager_subsystems": manager_subsystems
            },
            "legacy_subsystems": {
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


@unified_router.post("/autonomous-cycle")
async def run_autonomous_cycle_endpoint():
    """
    v2.0: Run a basic autonomous cycle with legacy subsystems:
    1. DISCOVER → All sources (Alpha, Ultimate, Spawn, Domination, DealGraph)
    2. PRIORITIZE → MetaHive + Deal Graph + Outcome Oracle scoring
    3. EXECUTE → Fabric + Connectors execution
    4. RECONCILE → Track finances through Auto-Reconciliation
    5. LEARN → Feed back to MetaHive + Yield Memory + Auto-Upgrades
    """
    executor = get_executor()
    result = await executor.run_autonomous_cycle()
    return result


@unified_router.post("/full-autonomous-cycle")
async def run_full_autonomous_cycle_endpoint():
    """
    v3.0: Run FULL 10-phase autonomous cycle using ALL 60+ subsystems via 5 managers:

    PHASES:
    1. DISCOVER → 15+ sources via DiscoveryManager
    2. ENRICH → Deal Graph network enrichment
    3. SCORE → Intelligence scoring via IntelligenceManager
    4. FINANCE → OCL P2P internal lending via FinancialManager
    5. REVENUE → Revenue opportunities via RevenueManager
    6. EXECUTE → Top 20 opportunities via ExecutionManager
    7. VERIFY → Deliverable verification
    8. REVENUE FLOWS → Execute revenue streams
    9. RECONCILE → Financial tracking
    10. LEARN → Pattern storage and learning

    MANAGERS USED:
    - RevenueManager (11 subsystems)
    - FinancialManager (8 subsystems + OCL P2P)
    - ExecutionManager (10 subsystems)
    - DiscoveryManager (15 subsystems)
    - IntelligenceManager (10 subsystems)
    """
    executor = get_executor()
    result = await executor.run_full_autonomous_cycle()
    return result


@unified_router.get("/managers/status")
async def get_managers_status():
    """Get status of all 5 specialized managers"""
    executor = get_executor()
    status = {}

    if hasattr(executor, 'revenue_mgr') and executor._manager_status.get("revenue_manager"):
        status["revenue_manager"] = executor.revenue_mgr.get_status()

    if hasattr(executor, 'financial_mgr') and executor._manager_status.get("financial_manager"):
        status["financial_manager"] = executor.financial_mgr.get_status()

    if hasattr(executor, 'execution_mgr') and executor._manager_status.get("execution_manager"):
        status["execution_manager"] = executor.execution_mgr.get_status()

    if hasattr(executor, 'discovery_mgr') and executor._manager_status.get("discovery_manager"):
        status["discovery_manager"] = executor.discovery_mgr.get_status()

    if hasattr(executor, 'intelligence_mgr') and executor._manager_status.get("intelligence_manager"):
        status["intelligence_manager"] = executor.intelligence_mgr.get_status()

    # Calculate totals
    total_subsystems = sum(
        s.get("subsystems", {}).get("available", 0)
        for s in status.values()
        if isinstance(s, dict)
    )

    return {
        "ok": True,
        "managers": status,
        "total_manager_subsystems": total_subsystems,
        "managers_available": len([s for s in status.values() if s.get("ok")])
    }


def include_unified_endpoints(app):
    """Include unified executor endpoints in FastAPI app"""
    app.include_router(unified_router)

    executor = get_executor()
    status = executor.get_status()

    print("=" * 80)
    print("⚡ UNIFIED EXECUTOR v3.0 - MANAGER PATTERN ORCHESTRATION")
    print("=" * 80)

    # Print manager status
    mgr_status = status.get("managers", {})
    mgr_available = mgr_status.get("available", 0)
    mgr_total = mgr_status.get("total", 5)
    mgr_subs = mgr_status.get("total_manager_subsystems", 0)
    print(f"   Managers: {mgr_available}/{mgr_total} ({mgr_subs} subsystems via managers)")

    for mgr_name, mgr_data in mgr_status.get("details", {}).items():
        if isinstance(mgr_data, dict):
            icon = "✅" if mgr_data.get("available") else "❌"
            subs = mgr_data.get("subsystems", 0)
            total = mgr_data.get("total", 0)
            print(f"   {icon} {mgr_name}: {subs}/{total} subsystems")

    print("-" * 80)

    # Print legacy status
    legacy = status.get("legacy_subsystems", {})
    print(f"   Legacy: {legacy.get('available', 0)}/{legacy.get('total', 0)} ({legacy.get('percentage', 0)}%)")

    for cat, data in status.get("categories", {}).items():
        icon = "✅" if data["available"] == data["total"] else "⚠️" if data["available"] > 0 else "❌"
        print(f"   {icon} {cat.upper()}: {data['available']}/{data['total']}")

    print("=" * 80)


__all__ = [
    "execute", "get_executor", "UnifiedExecutor",
    "ExecutionCategory", "ExecutionMethod", "ExecutionResult",
    "unified_router", "include_unified_endpoints"
]
