"""
AIGENTSY MASTER RUNTIME - COMPLETE SYSTEM ORCHESTRATION
========================================================
The central nervous system that makes ALL engines FIRE.

WIRED SYSTEMS (48 files, 8 subsystems):

DISCOVERY LAYER:
- alpha_discovery_engine (7 dimensions, 27 platforms)
- real_signal_ingestion (Funding/Hiring/Launch signals)
- pain_point_detector (Twitter/Reddit/GitHub complaints)
- industry_knowledge (50+ industry templates)
- research_engine (Universal Intelligence Mesh)

EXECUTION LAYER:
- execution_orchestrator (7-stage pipeline)
- universal_executor (autonomous execution)
- platform_apis (Twitter, Email, Instagram, LinkedIn, SMS, GitHub)
- aigentsy_conductor (Claude/GPT/Gemini routing)
- deliverable_verification_engine (5-dimension quality check)

LEARNING LAYER:
- yield_memory (per-user pattern learning)
- metahive_brain (cross-AI shared learning)
- pricing_oracle (dynamic pricing)
- outcome_oracle_max (funnel tracking)

MONETIZATION LAYER:
- amg_orchestrator (10-stage revenue loop)
- r3_autopilot (revenue reinvestment)
- revenue_flows (fee calculation)
- revenue_reconciliation_engine (cross-platform tracking)

CONTENT LAYER:
- social_autoposting_engine (multi-platform posting)
- video_engine (Runway, Synthesia)
- audio_engine (ElevenLabs, Murf)
- graphics_engine (Stability AI)
- ame_pitches (outreach queue)

DEPLOYMENT LAYER:
- template_actionizer (SaaS/Marketing/Social templates)
- storefront_deployer (Vercel auto-deploy)
- metabridge (team formation)

FINANCIAL LAYER:
- ocl_p2p_lending (peer-to-peer credit)
- agent_factoring (invoice advances)
- performance_bonds (escrow)
- aigx_engine (internal currency)

SCHEDULES:
- Every 15 min: Discovery scan
- Every 30 min: Execute high-confidence opportunities
- Every 1 hour: Social content + AMG cycle
- Every 6 hours: R3 reallocation + learning sync
- Daily: MetaHive sync + pattern compression

USAGE:
    python aigentsy_master_runtime.py              # Run continuously
    python aigentsy_master_runtime.py --once       # Single cycle
    python aigentsy_master_runtime.py --status     # Show system status
    python aigentsy_master_runtime.py --discovery  # Discovery only
    python aigentsy_master_runtime.py --execute    # Execute only
    python aigentsy_master_runtime.py --social     # Social posting only
"""

import asyncio
import os
import sys
import json
import argparse
import signal
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


def _now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class RuntimeConfig:
    # Discovery
    discovery_interval_minutes: int = 15
    discovery_platforms: List[str] = field(default_factory=lambda: ['github', 'reddit', 'twitter', 'upwork', 'producthunt', 'hackernews'])
    
    # Execution
    auto_execute_threshold: float = 0.70
    max_parallel_executions: int = 5
    execution_interval_minutes: int = 30
    
    # Social
    social_interval_minutes: int = 60
    social_platforms: List[str] = field(default_factory=lambda: ['twitter', 'linkedin'])
    posts_per_cycle: int = 2
    
    # AMG/Revenue
    amg_interval_minutes: int = 60
    r3_interval_hours: int = 6
    
    # Learning
    learning_sync_interval_hours: int = 6
    metahive_sync_interval_hours: int = 24
    
    # ===== V106 MODE (NEW) =====
    use_v106_mode: bool = True  # Use integrated market-maker + risk-tranche
    v106_min_cash_floor: float = 50.0
    v106_kelly_budget: float = 10000.0
    # ===== V107-V112 REVENUE ENGINES =====
    # V111 Super-Harvesters
    uacr_scan_interval_minutes: int = 15  # Twitter/Instagram abandoned checkout signals
    receivables_scan_interval_minutes: int = 60  # Stripe invoice advances
    payments_optimization_interval_minutes: int = 30  # Payment routing optimization
    
    # V112 Market Maker
    market_maker_interval_minutes: int = 5  # High-frequency market making
    tranche_settlement_check_minutes: int = 60  # Tranche settlements
    
    # V110 Gap Harvesters
    gap_harvester_scan_minutes: int = 30  # 15 waste monetization engines


DEFAULT_CONFIG = RuntimeConfig()


# =============================================================================
# SYSTEM IMPORTS - ALL SUBSYSTEMS
# =============================================================================

print("\n" + "=" * 70)
print("🔌 LOADING AIGENTSY SUBSYSTEMS")
print("=" * 70)

# Track what's available
SYSTEMS = {}

# ----- DISCOVERY -----
try:
    from alpha_discovery_engine import AlphaDiscoveryEngine
    SYSTEMS['alpha_discovery'] = True
    print("✅ alpha_discovery_engine")
except ImportError as e:
    SYSTEMS['alpha_discovery'] = False
    print(f"❌ alpha_discovery_engine: {e}")

try:
    from ultimate_discovery_engine import discover_all_opportunities as ultimate_discover, get_wade_fulfillment_queue
    SYSTEMS['ultimate_discovery'] = True
    print("✅ ultimate_discovery_engine (27 platforms)")
except ImportError as e:
    SYSTEMS['ultimate_discovery'] = False
    print(f"❌ ultimate_discovery_engine: {e}")

try:
    from advanced_discovery_dimensions import PredictiveIntelligenceEngine
    SYSTEMS['advanced_discovery'] = True
    print("✅ advanced_discovery_dimensions (Dims 4-7)")
except ImportError as e:
    SYSTEMS['advanced_discovery'] = False
    print(f"❌ advanced_discovery_dimensions: {e}")

try:
    from discovery_to_queue_connector import auto_discover_and_queue, process_discovery_results
    SYSTEMS['discovery_connector'] = True
    print("✅ discovery_to_queue_connector")
except ImportError as e:
    SYSTEMS['discovery_connector'] = False
    print(f"❌ discovery_to_queue_connector: {e}")

try:
    from real_signal_ingestion import get_signal_engine
    SYSTEMS['signal_ingestion'] = True
    print("✅ real_signal_ingestion")
except ImportError as e:
    SYSTEMS['signal_ingestion'] = False
    print(f"❌ real_signal_ingestion: {e}")

try:
    from pain_point_detector import PainPointDetector
    SYSTEMS['pain_detector'] = True
    print("✅ pain_point_detector")
except ImportError as e:
    SYSTEMS['pain_detector'] = False
    print(f"❌ pain_point_detector: {e}")

try:
    from research_engine import ResearchEngine, UniversalIntelligenceMesh
    SYSTEMS['research_engine'] = True
    print("✅ research_engine")
except ImportError as e:
    SYSTEMS['research_engine'] = False
    print(f"❌ research_engine: {e}")

try:
    from internet_discovery_expansion import (
        InternetDiscoveryExpansion,
        expand_discovery_dimensions,
        SearchEngineScanner,
        ContactExtractor
    )
    SYSTEMS['internet_discovery'] = True
    print("✅ internet_discovery_expansion (search engines + contact extraction)")
except ImportError as e:
    SYSTEMS['internet_discovery'] = False
    print(f"❌ internet_discovery_expansion: {e}")

# ----- DIRECT OUTREACH ENGINE -----
try:
    from direct_outreach_engine import (
        DirectOutreachEngine,
        get_outreach_engine,
        send_direct_outreach,
        OutreachChannel
    )
    SYSTEMS['direct_outreach'] = True
    print("✅ direct_outreach_engine (DM/email proposals)")
except ImportError as e:
    SYSTEMS['direct_outreach'] = False
    print(f"❌ direct_outreach_engine: {e}")

# ----- PROOF & VERIFICATION -----
try:
    from proof_pipe import create_proof, verify_proof, create_outcome_from_proof, process_square_webhook, process_calendly_webhook
    SYSTEMS['proof_pipe'] = True
    print("✅ proof_pipe (POS/Booking verification)")
except ImportError as e:
    SYSTEMS['proof_pipe'] = False
    print(f"❌ proof_pipe: {e}")

# ----- EXECUTION -----
try:
    from execution_orchestrator import ExecutionOrchestrator, get_orchestrator
    SYSTEMS['execution_orchestrator'] = True
    print("✅ execution_orchestrator")
except ImportError as e:
    SYSTEMS['execution_orchestrator'] = False
    print(f"❌ execution_orchestrator: {e}")

try:
    from universal_executor import UniversalAutonomousExecutor, get_executor
    SYSTEMS['universal_executor'] = True
    print("✅ universal_executor")
except ImportError as e:
    SYSTEMS['universal_executor'] = False
    print(f"❌ universal_executor: {e}")

try:
    from platform_apis import PlatformExecutorRouter
    SYSTEMS['platform_apis'] = True
    print("✅ platform_apis")
    
    def get_platform_router():
        return PlatformExecutorRouter()
except ImportError as e:
    SYSTEMS['platform_apis'] = False
    print(f"❌ platform_apis: {e}")

try:
    from aigentsy_conductor import MultiAIRouter
    SYSTEMS['conductor'] = True
    print("✅ aigentsy_conductor")
except ImportError as e:
    SYSTEMS['conductor'] = False
    print(f"❌ aigentsy_conductor: {e}")

# ----- LEARNING -----
try:
    from yield_memory import store_pattern, get_best_action, get_memory_stats, find_similar_patterns
    SYSTEMS['yield_memory'] = True
    print("✅ yield_memory")
except ImportError as e:
    SYSTEMS['yield_memory'] = False
    print(f"❌ yield_memory: {e}")

try:
    from metahive_brain import contribute_to_hive, query_hive, get_hive_stats
    SYSTEMS['metahive'] = True
    print("✅ metahive_brain")
except ImportError as e:
    SYSTEMS['metahive'] = False
    print(f"❌ metahive_brain: {e}")

try:
    from pricing_oracle import calculate_dynamic_price, suggest_optimal_pricing
    SYSTEMS['pricing_oracle'] = True
    print("✅ pricing_oracle")
except ImportError as e:
    SYSTEMS['pricing_oracle'] = False
    print(f"❌ pricing_oracle: {e}")

try:
    from outcome_oracle_max import on_event, get_user_funnel_stats, credit_aigx
    SYSTEMS['outcome_oracle'] = True
    print("✅ outcome_oracle_max")
except ImportError as e:
    SYSTEMS['outcome_oracle'] = False
    print(f"❌ outcome_oracle_max: {e}")

# ----- MONETIZATION -----
try:
    from amg_orchestrator import AMGOrchestrator
    SYSTEMS['amg'] = True
    print("✅ amg_orchestrator")
except ImportError as e:
    SYSTEMS['amg'] = False
    print(f"❌ amg_orchestrator: {e}")

try:
    from r3_autopilot import execute_autopilot_spend
    SYSTEMS['r3'] = True
    print("✅ r3_autopilot")
except ImportError as e:
    SYSTEMS['r3'] = False
    print(f"❌ r3_autopilot: {e}")

try:
    from revenue_flows import calculate_base_fee, ingest_service_payment
    SYSTEMS['revenue_flows'] = True
    print("✅ revenue_flows")
except ImportError as e:
    SYSTEMS['revenue_flows'] = False
    print(f"❌ revenue_flows: {e}")

# ----- CONTENT -----
try:
    from social_autoposting_engine import get_social_engine, SocialAutoPostingEngine
    SYSTEMS['social_engine'] = True
    print("✅ social_autoposting_engine")
except ImportError as e:
    SYSTEMS['social_engine'] = False
    print(f"❌ social_autoposting_engine: {e}")

try:
    from video_engine import VideoEngine
    SYSTEMS['video_engine'] = True
    print("✅ video_engine")
except ImportError as e:
    SYSTEMS['video_engine'] = False
    print(f"❌ video_engine: {e}")

try:
    from audio_engine import AudioEngine
    SYSTEMS['audio_engine'] = True
    print("✅ audio_engine")
except ImportError as e:
    SYSTEMS['audio_engine'] = False
    print(f"❌ audio_engine: {e}")

try:
    from graphics_engine import GraphicsEngine
    SYSTEMS['graphics_engine'] = True
    print("✅ graphics_engine")
except ImportError as e:
    SYSTEMS['graphics_engine'] = False
    print(f"❌ graphics_engine: {e}")

try:
    from ame_pitches import generate_pitch, get_pending_pitches, approve_pitch
    SYSTEMS['ame_pitches'] = True
    print("✅ ame_pitches")
except ImportError as e:
    SYSTEMS['ame_pitches'] = False
    print(f"❌ ame_pitches: {e}")

# ----- DEPLOYMENT -----
try:
    from template_actionizer import actionize_template
    SYSTEMS['template_actionizer'] = True
    print("✅ template_actionizer")
except ImportError as e:
    SYSTEMS['template_actionizer'] = False
    print(f"❌ template_actionizer: {e}")

try:
    from storefront_deployer import deploy_storefront
    SYSTEMS['storefront_deployer'] = True
    print("✅ storefront_deployer")
except ImportError as e:
    SYSTEMS['storefront_deployer'] = False
    print(f"❌ storefront_deployer: {e}")

try:
    from metabridge import execute_metabridge, find_complementary_agents
    SYSTEMS['metabridge'] = True
    print("✅ metabridge")
except ImportError as e:
    SYSTEMS['metabridge'] = False
    print(f"❌ metabridge: {e}")

# ----- FINANCIAL -----
try:
    from ocl_engine import calculate_ocl_limit, spend_ocl
    SYSTEMS['ocl'] = True
    print("✅ ocl_engine")
except ImportError as e:
    SYSTEMS['ocl'] = False
    print(f"❌ ocl_engine: {e}")

try:
    from agent_factoring import request_factoring_advance
    SYSTEMS['factoring'] = True
    print("✅ agent_factoring")
except ImportError as e:
    SYSTEMS['factoring'] = False
    print(f"❌ agent_factoring: {e}")

try:
    from aigx_engine import create_activity_endpoints
    SYSTEMS['aigx'] = True
    print("✅ aigx_engine")
except ImportError as e:
    SYSTEMS['aigx'] = False
    print(f"❌ aigx_engine: {e}")

# ----- JV & VALUE CHAIN -----
try:
    from jv_mesh import create_jv_proposal, suggest_jv_partners, list_active_jvs
    SYSTEMS['jv_mesh'] = True
    print("✅ jv_mesh")
except ImportError as e:
    SYSTEMS['jv_mesh'] = False
    print(f"❌ jv_mesh: {e}")

try:
    from value_chain_engine import discover_value_chain
    SYSTEMS['value_chain'] = True
    print("✅ value_chain_engine")
except ImportError as e:
    SYSTEMS['value_chain'] = False
    print(f"❌ value_chain_engine: {e}")

# ----- MONETIZATION -----
try:
    from third_party_monetization import get_monetization_engine
    SYSTEMS['third_party_monetization'] = True
    print("✅ third_party_monetization")
except ImportError as e:
    SYSTEMS['third_party_monetization'] = False
    print(f"❌ third_party_monetization: {e}")

try:
    from revenue_reconciliation_engine import get_reconciliation_engine
    SYSTEMS['revenue_reconciliation'] = True
    print("✅ revenue_reconciliation_engine")
except ImportError as e:
    SYSTEMS['revenue_reconciliation'] = False
    print(f"❌ revenue_reconciliation_engine: {e}")

try:
    from universal_revenue_orchestrator import UniversalRevenueOrchestrator
    SYSTEMS['universal_revenue'] = True
    print("✅ universal_revenue_orchestrator")
except ImportError as e:
    SYSTEMS['universal_revenue'] = False
    print(f"❌ universal_revenue_orchestrator: {e}")

# ----- MARKETPLACE AUTOMATION -----
try:
    from week2_master_orchestrator import Week2MasterOrchestrator
    SYSTEMS['week2_orchestrator'] = True
    print("✅ week2_master_orchestrator")
except ImportError as e:
    SYSTEMS['week2_orchestrator'] = False
    print(f"❌ week2_master_orchestrator: {e}")

try:
    from fiverr_automation_engine import FiverrAutomationEngine
    SYSTEMS['fiverr_automation'] = True
    print("✅ fiverr_automation_engine")
except ImportError as e:
    SYSTEMS['fiverr_automation'] = False
    print(f"❌ fiverr_automation_engine: {e}")

# ----- V107-V112 REVENUE ENGINES -----
try:
    from v107_accretive_overlays import include_v107_overlays
    SYSTEMS['v107'] = True
    print("✅ v107_accretive_overlays (20 engines)")
except ImportError as e:
    SYSTEMS['v107'] = False
    print(f"❌ v107_accretive_overlays: {e}")

try:
    from v110_gap_harvesters import include_gap_harvesters, scan_all_harvesters
    SYSTEMS['v110'] = True
    print("✅ v110_gap_harvesters (15 engines)")
except ImportError as e:
    SYSTEMS['v110'] = False
    print(f"❌ v110_gap_harvesters: {e}")

try:
    from v111_gapharvester_ii import (
        include_gapharvester_ii,
        uacr_scan_twitter,
        uacr_scan_instagram,
        uacr_batch_quote,
        receivables_scan_stripe,
        payments_optimize_routing
    )
    SYSTEMS['v111'] = True
    print("✅ v111_gapharvester_ii ($4.6T U-ACR + Receivables + Payments)")
except ImportError as e:
    SYSTEMS['v111'] = False
    print(f"❌ v111_gapharvester_ii: {e}")

try:
    from v112_market_maker_extensions import (
        include_market_maker,
        ifx_market_making_cycle,
        tranche_check_settlements
    )
    SYSTEMS['v112'] = True
    print("✅ v112_market_maker_extensions (IFX/OAA + Tranching)")
except ImportError as e:
    SYSTEMS['v112'] = False
    print(f"❌ v112_market_maker_extensions: {e}")

# ----- PREDICTION & SCORING -----
try:
    from execution_scorer import ExecutionScorer
    SYSTEMS['execution_scorer'] = True
    print("✅ execution_scorer")
except ImportError as e:
    SYSTEMS['execution_scorer'] = False
    print(f"❌ execution_scorer: {e}")

try:
    from client_success_predictor import ClientSuccessPredictor, predict_user_success
    SYSTEMS['success_predictor'] = True
    print("✅ client_success_predictor")
except ImportError as e:
    SYSTEMS['success_predictor'] = False
    print(f"❌ client_success_predictor: {e}")

# ----- DISCOVERY SCRAPERS -----
try:
    from explicit_marketplace_scrapers import ExplicitMarketplaceScrapers
    SYSTEMS['marketplace_scrapers'] = True
    print("✅ explicit_marketplace_scrapers")
except ImportError as e:
    SYSTEMS['marketplace_scrapers'] = False
    print(f"❌ explicit_marketplace_scrapers: {e}")

# ----- GROWTH & BOOSTERS -----
try:
    from booster_engine import get_active_boosters
    SYSTEMS['booster_engine'] = True
    print("✅ booster_engine")
except ImportError as e:
    SYSTEMS['booster_engine'] = False
    print(f"❌ booster_engine: {e}")

try:
    from platform_recruitment_engine import get_recruitment_engine
    SYSTEMS['recruitment_engine'] = True
    print("✅ platform_recruitment_engine")
except ImportError as e:
    SYSTEMS['recruitment_engine'] = False
    print(f"❌ platform_recruitment_engine: {e}")

# ----- ARBITRAGE -----
try:
    from arbitrage_execution_pipeline import get_arbitrage_pipeline
    SYSTEMS['arbitrage_pipeline'] = True
    print("✅ arbitrage_execution_pipeline")
except ImportError as e:
    SYSTEMS['arbitrage_pipeline'] = False
    print(f"❌ arbitrage_execution_pipeline: {e}")

# ----- FRANCHISE & BUSINESS -----
try:
    from franchise_engine import LICENSE_TYPES
    SYSTEMS['franchise_engine'] = True
    print("✅ franchise_engine")
except ImportError as e:
    SYSTEMS['franchise_engine'] = False
    print(f"❌ franchise_engine: {e}")

try:
    from business_in_a_box_accelerator import MarketIntelligenceEngine, BusinessDeploymentEngine
    SYSTEMS['business_accelerator'] = True
    print("✅ business_in_a_box_accelerator")
except ImportError as e:
    SYSTEMS['business_accelerator'] = False
    print(f"❌ business_in_a_box_accelerator: {e}")

try:
    from sku_orchestrator import UniversalBusinessOrchestrator
    SYSTEMS['sku_orchestrator'] = True
    print("✅ sku_orchestrator")
except ImportError as e:
    SYSTEMS['sku_orchestrator'] = False
    print(f"❌ sku_orchestrator: {e}")

# ----- PROTOCOL & REGISTRY -----
try:
    from aigx_protocol import get_protocol
    SYSTEMS['aigx_protocol'] = True
    print("✅ aigx_protocol")
except ImportError as e:
    SYSTEMS['aigx_protocol'] = False
    print(f"❌ aigx_protocol: {e}")

try:
    from agent_registry import AgentRegistry, get_registry, register_agent
    SYSTEMS['agent_registry'] = True
    print("✅ agent_registry")
except ImportError as e:
    SYSTEMS['agent_registry'] = False
    print(f"❌ agent_registry: {e}")

# ----- RECONCILIATION -----
try:
    from autonomous_reconciliation_engine import AutonomousReconciliationEngine
    SYSTEMS['autonomous_reconciliation'] = True
    print("✅ autonomous_reconciliation_engine")
except ImportError as e:
    SYSTEMS['autonomous_reconciliation'] = False
    print(f"❌ autonomous_reconciliation_engine: {e}")

# ----- PRICING & PROFIT -----
try:
    from intelligent_pricing_autopilot import get_pricing_autopilot
    SYSTEMS['pricing_autopilot'] = True
    print("✅ intelligent_pricing_autopilot")
except ImportError as e:
    SYSTEMS['pricing_autopilot'] = False
    print(f"❌ intelligent_pricing_autopilot: {e}")

try:
    from profit_engine_v98 import include_profit_engine
    SYSTEMS['profit_engine'] = True
    print("✅ profit_engine_v98")
except ImportError as e:
    SYSTEMS['profit_engine'] = False
    print(f"❌ profit_engine_v98: {e}")

# ----- METAHIVE PUBLIC API -----
try:
    from open_metahive_api import get_metahive_api
    SYSTEMS['open_metahive_api'] = True
    print("✅ open_metahive_api (External AI contributions)")
except ImportError as e:
    SYSTEMS['open_metahive_api'] = False
    print(f"❌ open_metahive_api: {e}")

# ----- INDUSTRY & KNOWLEDGE -----
try:
    from industry_knowledge import INDUSTRY_TEMPLATES
    SYSTEMS['industry_knowledge'] = True
    print("✅ industry_knowledge (50+ industries)")
except ImportError as e:
    SYSTEMS['industry_knowledge'] = False
    print(f"❌ industry_knowledge: {e}")

# ----- OPPORTUNITY FILTERS -----
try:
    from opportunity_filters import filter_opportunities, get_execute_now_opportunities, is_outlier, should_skip, is_stale
    SYSTEMS['opportunity_filters'] = True
    print("✅ opportunity_filters")
except ImportError as e:
    SYSTEMS['opportunity_filters'] = False
    print(f"❌ opportunity_filters: {e}")

# ----- DIAGNOSTICS -----
try:
    from diagnostic_tracer import include_diagnostic_tracer
    SYSTEMS['diagnostic_tracer'] = True
    print("✅ diagnostic_tracer")
except ImportError as e:
    SYSTEMS['diagnostic_tracer'] = False
    print(f"❌ diagnostic_tracer: {e}")

# ----- APEX UPGRADES -----
try:
    from apex_upgrades_overlay import router as apex_router
    SYSTEMS['apex_upgrades'] = True
    print("✅ apex_upgrades_overlay (12 modules)")
except ImportError as e:
    SYSTEMS['apex_upgrades'] = False
    print(f"❌ apex_upgrades_overlay: {e}")

# ----- AME/AMG ENDPOINTS -----
try:
    from ame_amg_endpoints import (
        track_visit_handler,
        track_conversion_handler,
        amg_optimize_handler
    )
    SYSTEMS['ame_amg_endpoints'] = True
    print("✅ ame_amg_endpoints")
except ImportError as e:
    SYSTEMS['ame_amg_endpoints'] = False
    print(f"❌ ame_amg_endpoints: {e}")

# ----- SYNDICATION & CROSS-NETWORK -----
try:
    from syndication import (
        create_syndication_route,
        find_best_network,
        PARTNER_NETWORKS,
        SYNDICATION_REASONS
    )
    SYSTEMS['syndication'] = True
    print("✅ syndication (Cross-network routing)")
except ImportError as e:
    SYSTEMS['syndication'] = False
    print(f"❌ syndication: {e}")

# ----- STATE MONEY (ESCROW) -----
try:
    from state_money import STATE_TRANSITIONS
    SYSTEMS['state_money'] = True
    print("✅ state_money (State-driven escrow)")
except ImportError as e:
    SYSTEMS['state_money'] = False
    print(f"❌ state_money: {e}")

# ----- PROTOCOL GATEWAY -----
try:
    from protocol_gateway import ProtocolGateway, APIKeyManager
    SYSTEMS['protocol_gateway'] = True
    print("✅ protocol_gateway (External AI API)")
except ImportError as e:
    SYSTEMS['protocol_gateway'] = False
    print(f"❌ protocol_gateway: {e}")

# ----- METABRIDGE (TEAM FORMATION) -----
try:
    from metabridge import analyze_intent_complexity, find_complementary_agents
    SYSTEMS['metabridge'] = True
    print("✅ metabridge (Team formation)")
except ImportError as e:
    SYSTEMS['metabridge'] = False
    print(f"❌ metabridge: {e}")

try:
    from metabridge_dealgraph_UPGRADED import router as dealgraph_router
    SYSTEMS['metabridge_dealgraph'] = True
    print("✅ metabridge_dealgraph_UPGRADED")
except ImportError as e:
    SYSTEMS['metabridge_dealgraph'] = False
    print(f"❌ metabridge_dealgraph_UPGRADED: {e}")

# ----- WADE BIDDING SYSTEM -----
try:
    from auto_bidding_orchestrator import auto_bid_on_opportunity
    SYSTEMS['wade_bidding'] = True
    print("✅ auto_bidding_orchestrator")
except ImportError as e:
    SYSTEMS['wade_bidding'] = False
    print(f"❌ auto_bidding_orchestrator: {e}")

# ----- TEMPLATE SYSTEMS -----
try:
    from template_library import KIT_SUMMARY
    SYSTEMS['template_library'] = True
    print("✅ template_library")
except ImportError as e:
    SYSTEMS['template_library'] = False
    print(f"❌ template_library: {e}")

try:
    from template_integration_coordinator import coordinate_template_activation, auto_trigger_on_mint
    SYSTEMS['template_integration'] = True
    print("✅ template_integration_coordinator")
except ImportError as e:
    SYSTEMS['template_integration'] = False
    print(f"❌ template_integration_coordinator: {e}")

try:
    from template_variations import generate_unique_variations, apply_variations_to_html, COLOR_PALETTES, FONT_PAIRS
    SYSTEMS['template_variations'] = True
    print("✅ template_variations (750 unique combos)")
except ImportError as e:
    SYSTEMS['template_variations'] = False
    print(f"❌ template_variations: {e}")

# ----- INTERNET DOMINATION ENGINE -----
try:
    from internet_domination_engine import router as internet_domination_router
    SYSTEMS['internet_domination'] = True
    print("✅ internet_domination_engine (27+ platforms)")
except ImportError as e:
    SYSTEMS['internet_domination'] = False
    print(f"❌ internet_domination_engine: {e}")

# ----- AUTO-SPAWN ENGINE -----
try:
    from auto_spawn_engine import get_engine as get_spawn_engine
    SYSTEMS['auto_spawn'] = True
    print("✅ auto_spawn_engine (AI Venture Factory)")
except ImportError as e:
    SYSTEMS['auto_spawn'] = False
    print(f"❌ auto_spawn_engine: {e}")

# ----- DRIBBBLE PORTFOLIO -----
try:
    from dribbble_portfolio_automation import DribbbleAutomation, TrendAnalyzer
    SYSTEMS['dribbble_automation'] = True
    print("✅ dribbble_portfolio_automation")
except ImportError as e:
    SYSTEMS['dribbble_automation'] = False
    print(f"❌ dribbble_portfolio_automation: {e}")

# ----- ESCROW LITE -----
try:
    from escrow_lite import create_payment_intent, capture_payment, cancel_payment, auto_capture_on_delivered
    SYSTEMS['escrow_lite'] = True
    print("✅ escrow_lite (Auth→Capture)")
except ImportError as e:
    SYSTEMS['escrow_lite'] = False
    print(f"❌ escrow_lite: {e}")

# ----- OPENAI AGENT DEPLOYER -----
try:
    from openai_agent_deployer import deploy_ai_agents, AGENT_CONFIGS
    SYSTEMS['openai_agent_deployer'] = True
    print("✅ openai_agent_deployer (4 agents per user)")
except ImportError as e:
    SYSTEMS['openai_agent_deployer'] = False
    print(f"❌ openai_agent_deployer: {e}")

# ----- CURRENCY ENGINE -----
try:
    from currency_engine import convert_currency, credit_currency, debit_currency, transfer_with_conversion
    SYSTEMS['currency_engine'] = True
    print("✅ currency_engine (AIGx, USD, EUR, GBP)")
except ImportError as e:
    SYSTEMS['currency_engine'] = False
    print(f"❌ currency_engine: {e}")

# ----- SPONSOR POOLS -----
try:
    from sponsor_pools import create_sponsor_pool
    SYSTEMS['sponsor_pools'] = True
    print("✅ sponsor_pools (Co-Op Outcome Pools)")
except ImportError as e:
    SYSTEMS['sponsor_pools'] = False
    print(f"❌ sponsor_pools: {e}")

# ----- 99DESIGNS AUTOMATION -----
try:
    from ninety_nine_designs_automation import DesignContestAutomation
    SYSTEMS['99designs_automation'] = True
    print("✅ ninety_nine_designs_automation")
except ImportError as e:
    SYSTEMS['99designs_automation'] = False
    print(f"❌ ninety_nine_designs_automation: {e}")

# ----- DEVICE OAUTH CONNECTOR -----
try:
    from device_oauth_connector import initiate_oauth, complete_oauth
    SYSTEMS['device_oauth'] = True
    print("✅ device_oauth_connector")
except ImportError as e:
    SYSTEMS['device_oauth'] = False
    print(f"❌ device_oauth_connector: {e}")

# ----- DARK POOL AUCTIONS -----
try:
    from dark_pool import create_dark_pool_auction, submit_dark_pool_bid
    SYSTEMS['dark_pool'] = True
    print("✅ dark_pool (Anonymous auctions)")
except ImportError as e:
    SYSTEMS['dark_pool'] = False
    print(f"❌ dark_pool: {e}")

# ----- OPPORTUNITY ENGAGEMENT -----
try:
    from opportunity_engagement import OpportunityEngagement
    SYSTEMS['opportunity_engagement'] = True
    print("✅ opportunity_engagement")
except ImportError as e:
    SYSTEMS['opportunity_engagement'] = False
    print(f"❌ opportunity_engagement: {e}")

# ----- MINT GENERATOR -----
try:
    from mint_generator import MintGenerator, get_mint_generator
    SYSTEMS['mint_generator'] = True
    print("✅ mint_generator")
except ImportError as e:
    SYSTEMS['mint_generator'] = False
    print(f"❌ mint_generator: {e}")

# ----- DEALGRAPH (Core State Machine) -----
try:
    from dealgraph import create_deal, DealState
    SYSTEMS['dealgraph'] = True
    print("✅ dealgraph (Unified state machine)")
except ImportError as e:
    SYSTEMS['dealgraph'] = False
    print(f"❌ dealgraph: {e}")

# ----- EXECUTION ROUTES -----
try:
    from execution_routes import router as execution_router
    SYSTEMS['execution_routes'] = True
    print("✅ execution_routes")
except ImportError as e:
    SYSTEMS['execution_routes'] = False
    print(f"❌ execution_routes: {e}")

# ----- INTENT EXCHANGE -----
try:
    from intent_exchange import router as intent_router
    SYSTEMS['intent_exchange'] = True
    print("✅ intent_exchange (90-second auctions)")
except ImportError as e:
    SYSTEMS['intent_exchange'] = False
    print(f"❌ intent_exchange: {e}")

# ----- LTV FORECASTER -----
try:
    from ltv_forecaster import calculate_ltv_with_churn, calculate_churn_risk, suggest_retention_campaign
    SYSTEMS['ltv_forecaster'] = True
    print("✅ ltv_forecaster")
except ImportError as e:
    SYSTEMS['ltv_forecaster'] = False
    print(f"❌ ltv_forecaster: {e}")

# ----- APEX ULTRA (Master Integration) -----
try:
    from aigentsy_apex_ultra import activate_apex_ultra
    SYSTEMS['apex_ultra'] = True
    print("✅ aigentsy_apex_ultra (50+ systems integrated)")
except ImportError as e:
    SYSTEMS['apex_ultra'] = False
    print(f"❌ aigentsy_apex_ultra: {e}")

# ----- SUPABASE PROVISIONER -----
try:
    from supabase_provisioner import provision_database, delete_database, DATABASE_SCHEMAS
    SYSTEMS['supabase_provisioner'] = True
    print("✅ supabase_provisioner")
except ImportError as e:
    SYSTEMS['supabase_provisioner'] = False
    print(f"❌ supabase_provisioner: {e}")

# ----- AGENT SPENDING -----
try:
    from agent_spending import check_spending_capacity, execute_agent_spend, agent_to_agent_payment, get_spending_summary, AL_LIMITS
    SYSTEMS['agent_spending'] = True
    print("✅ agent_spending (AL0-AL5 budgets)")
except ImportError as e:
    SYSTEMS['agent_spending'] = False
    print(f"❌ agent_spending: {e}")

# ----- AAM STRIPE WEBHOOKS -----
try:
    from aam_stripe import process_stripe_webhook, verify_stripe_signature
    SYSTEMS['aam_stripe'] = True
    print("✅ aam_stripe (webhook handlers)")
except ImportError as e:
    SYSTEMS['aam_stripe'] = False
    print(f"❌ aam_stripe: {e}")

# ----- IPVAULT (Auto-Royalties) -----
try:
    from ipvault import create_ip_asset, license_ip_asset, record_asset_usage, calculate_royalty_payment, ASSET_TYPES
    SYSTEMS['ipvault'] = True
    print("✅ ipvault (playbook royalties)")
except ImportError as e:
    SYSTEMS['ipvault'] = False
    print(f"❌ ipvault: {e}")

# ----- DASHBOARD CONNECTOR -----
try:
    from dashboard_connector import DashboardConnector
    SYSTEMS['dashboard_connector'] = True
    print("✅ dashboard_connector")
except ImportError as e:
    SYSTEMS['dashboard_connector'] = False
    print(f"❌ dashboard_connector: {e}")

# ----- DASHBOARD API -----
try:
    from dashboard_api import get_dashboard_data, create_dashboard_endpoints, get_discovery_stats
    SYSTEMS['dashboard_api'] = True
    print("✅ dashboard_api")
except ImportError as e:
    SYSTEMS['dashboard_api'] = False
    print(f"❌ dashboard_api: {e}")

# ----- AUTONOMOUS DEAL GRAPH -----
try:
    from autonomous_deal_graph import get_deal_graph, RelationshipType, RELATIONSHIP_WEIGHTS
    SYSTEMS['autonomous_deal_graph'] = True
    print("✅ autonomous_deal_graph (relationship memory)")
except ImportError as e:
    SYSTEMS['autonomous_deal_graph'] = False
    print(f"❌ autonomous_deal_graph: {e}")

# ----- UNIVERSAL PLATFORM ADAPTER -----
try:
    from universal_platform_adapter import get_platform_registry, PlatformConfig, PlatformCategory, IntentType, MonetizationMethod
    SYSTEMS['universal_platform_adapter'] = True
    print("✅ universal_platform_adapter (unlimited platforms)")
except ImportError as e:
    SYSTEMS['universal_platform_adapter'] = False
    print(f"❌ universal_platform_adapter: {e}")

# ----- AIGENTSY PAYMENTS -----
try:
    from aigentsy_payments import (
        create_wade_payment_link, 
        create_wade_invoice,
        create_user_payment_with_fee,
        get_aigentsy_balance,
        get_revenue_by_path,
        initiate_payout
    )
    SYSTEMS['aigentsy_payments'] = True
    print("✅ aigentsy_payments (Path A + Path B)")
except ImportError as e:
    SYSTEMS['aigentsy_payments'] = False
    print(f"❌ aigentsy_payments: {e}")

# ----- INTEGRATION -----
try:
    from universal_integration_layer import RevenueIntelligenceMesh, UniversalAIRouter
    SYSTEMS['revenue_mesh'] = True
    print("✅ universal_integration_layer")
except ImportError as e:
    SYSTEMS['revenue_mesh'] = False
    print(f"❌ universal_integration_layer: {e}")

print("=" * 70)
available = sum(1 for v in SYSTEMS.values() if v)
print(f"📊 SYSTEMS LOADED: {available}/{len(SYSTEMS)}")
print("=" * 70 + "\n")


# =============================================================================
# MASTER RUNTIME CLASS
# =============================================================================

class AiGentsyMasterRuntime:
    """
    Central orchestrator for all AiGentsy systems.
    """
    
    def __init__(self, config: RuntimeConfig = None):
        self.config = config or DEFAULT_CONFIG
        
        # Timestamps
        self.last_discovery = None
        self.last_execution = None
        self.last_social = None
        self.last_amg = None
        self.last_r3 = None
        self.last_learning_sync = None
        
        # Stats
        self.cycle_count = 0
        self.stats = {
            'opportunities_discovered': 0,
            'opportunities_executed': 0,
            'revenue_generated': 0.0,
            'posts_made': 0,
            'patterns_learned': 0,
            'started_at': _now()
        }
        
        # State
        self._running = False
        self._shutdown = asyncio.Event()
        
        print("\n🚀 AIGENTSY MASTER RUNTIME INITIALIZED")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all systems"""
        return {
            'systems': SYSTEMS,
            'available': sum(1 for v in SYSTEMS.values() if v),
            'total': len(SYSTEMS),
            'stats': self.stats,
            'last_discovery': self.last_discovery,
            'last_execution': self.last_execution,
            'last_social': self.last_social,
            'last_amg': self.last_amg,
            'running': self._running
        }

    async def run_internet_discovery(self) -> Dict[str, Any]:
        """
        Run internet-wide discovery scan.
        Expands beyond 27 platforms to search engines, RSS, forums.
        """
        
        if not SYSTEMS.get('internet_discovery'):
            return {'status': 'skipped', 'reason': 'Internet discovery not available'}
        
        print("\n🌐 Running internet-wide discovery...")
        
        try:
            expansion = InternetDiscoveryExpansion()
            opportunities = await expansion.run_full_scan()
            
            # Process opportunities through direct outreach
            if SYSTEMS.get('direct_outreach') and opportunities:
                outreach = get_outreach_engine()
                results = await outreach.process_batch([
                    {
                        'opportunity_id': opp.opportunity_id,
                        'title': opp.title,
                        'description': opp.description,
                        'pain_point': opp.pain_point,
                        'estimated_value': opp.estimated_value,
                        'contact': opp.contact
                    }
                    for opp in opportunities
                    if opp.contact and opp.contact.extraction_confidence >= 0.3
                ])
                
                print(f"   📧 Sent {len([r for r in results if r.status.value == 'sent'])} outreach messages")
            
            return {
                'status': 'success',
                'opportunities_found': len(opportunities),
                'with_contact': len([o for o in opportunities if o.contact]),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"   ❌ Internet discovery error: {e}")
            return {'status': 'error', 'error': str(e)}

    async def run_direct_outreach(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """
        Run direct outreach for a batch of opportunities.
        Sends DMs/emails instead of posting to restricted platforms.
        """
        
        if not SYSTEMS.get('direct_outreach'):
            return {'status': 'skipped', 'reason': 'Direct outreach not available'}
        
        print("\n📧 Running direct outreach...")
        
        try:
            outreach = get_outreach_engine()
            results = await outreach.process_batch(opportunities)
            
            stats = outreach.get_stats()
            
            print(f"   Sent: {stats['sent']}")
            print(f"   Daily count: {stats['daily_count']}/{stats['daily_limit']}")
            
            return {
                'status': 'success',
                'sent': stats['sent'],
                'stats': stats,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"   ❌ Direct outreach error: {e}")
            return {'status': 'error', 'error': str(e)}

    # =========================================================================
    # DISCOVERY - ALL 7 DIMENSIONS
    # =========================================================================
    
    async def run_discovery(self) -> Dict[str, Any]:
        """Run opportunity discovery across ALL 7 dimensions and 27+ platforms"""
        
        print("\n" + "=" * 70)
        print("🔍 DISCOVERY CYCLE - 7 DIMENSIONS")
        print("=" * 70)
        
        results = {
            'opportunities': [],
            'total': 0,
            'by_dimension': {},
            'by_platform': {}
        }
        
        # DIMENSION 1-3: Ultimate Discovery (27 platforms)
        if SYSTEMS.get('ultimate_discovery'):
            try:
                discovery = await ultimate_discover(
                    username='aigentsy',
                    user_profile={'skills': [], 'kits': []},
                    platforms=self.config.discovery_platforms
                )
                
                opps = discovery.get('opportunities', [])
                results['opportunities'].extend(opps)
                results['by_dimension']['explicit_marketplace'] = len(opps)
                
                print(f"   Dims 1-3 (27 platforms): {len(opps)} opportunities")
            except Exception as e:
                print(f"   ❌ Ultimate Discovery error: {e}")
        
        # DIMENSION 4-7: Advanced Discovery
        if SYSTEMS.get('advanced_discovery'):
            try:
                # Dimension 4: Predictive Intelligence
                predictive = PredictiveIntelligenceEngine()
                pred_opps = await predictive.predict_all_opportunities()
                results['opportunities'].extend(pred_opps)
                results['by_dimension']['predictive'] = len(pred_opps)
                print(f"   Dim 4 (Predictive): {len(pred_opps)} opportunities")
                
                # Dimension 5: Network Amplification
                network = NetworkAmplificationEngine()
                net_opps = await network.find_network_opportunities()
                results['opportunities'].extend(net_opps)
                results['by_dimension']['network'] = len(net_opps)
                print(f"   Dim 5 (Network): {len(net_opps)} opportunities")
                
                # Dimension 6: Opportunity Creation
                creation = OpportunityCreationEngine()
                created_opps = await creation.create_opportunities()
                results['opportunities'].extend(created_opps)
                results['by_dimension']['created'] = len(created_opps)
                print(f"   Dim 6 (Created): {len(created_opps)} opportunities")
                
                # Dimension 7: Emergent Patterns
                emergent = EmergentPatternEngine()
                pattern_opps = await emergent.detect_patterns()
                results['opportunities'].extend(pattern_opps)
                results['by_dimension']['emergent'] = len(pattern_opps)
                print(f"   Dim 7 (Emergent): {len(pattern_opps)} opportunities")
                
            except Exception as e:
                print(f"   ❌ Advanced Discovery error: {e}")
        
        # Alpha Discovery (fallback)
        elif SYSTEMS.get('alpha_discovery'):
            try:
                engine = AlphaDiscoveryEngine()
                discovery = await engine.discover(
                    platforms=self.config.discovery_platforms,
                    max_per_platform=20
                )
                
                opps = discovery.get('opportunities', [])
                results['opportunities'].extend(opps)
                results['by_dimension']['alpha'] = len(opps)
                
                print(f"   Alpha Discovery: {len(opps)} opportunities")
            except Exception as e:
                print(f"   ❌ Alpha Discovery error: {e}")
        
        # Signal Ingestion
        if SYSTEMS.get('signal_ingestion'):
            try:
                signals = await ingest_all_signals()
                actionable = signals.get('actionable_now', [])
                
                for signal in actionable[:10]:
                    results['opportunities'].append({
                        'id': f"signal_{signal.get('type', 'unknown')}_{len(results['opportunities'])}",
                        'title': signal.get('title', 'Signal opportunity'),
                        'source': 'signal_ingestion',
                        'type': signal.get('type'),
                        'value': signal.get('predicted_value', 500),
                        'confidence': signal.get('confidence', 0.7)
                    })
                
                results['by_dimension']['signals'] = len(actionable)
                print(f"   Signals: {len(actionable)} actionable")
            except Exception as e:
                print(f"   ❌ Signal Ingestion error: {e}")
        
        # Pain Point Detection
        if SYSTEMS.get('pain_detector'):
            try:
                pain_points = await detect_pain_points(limit=10)
                pp_opps = pain_points.get('opportunities', [])
                
                for pp in pp_opps[:5]:
                    results['opportunities'].append(pp)
                
                results['by_dimension']['pain_points'] = len(pp_opps)
                print(f"   Pain Points: {len(pp_opps)} detected")
            except Exception as e:
                print(f"   ❌ Pain Detection error: {e}")
        
        # Route to queue if connector available
        if SYSTEMS.get('discovery_connector') and results['opportunities']:
            try:
                queue_result = await process_discovery_results({
                    'ok': True,
                    'opportunities': results['opportunities'],
                    'total_found': len(results['opportunities'])
                })
                results['queued'] = queue_result.get('processed', 0)
                print(f"   Queued for approval: {results['queued']}")
            except Exception as e:
                print(f"   ❌ Queue connector error: {e}")
        
        results['total'] = len(results['opportunities'])
        self.last_discovery = _now()
        self.stats['opportunities_discovered'] += results['total']
        
        print(f"\n✅ Discovery complete: {results['total']} total opportunities")
        
        return results
    
    # =========================================================================
    # EXECUTION
    # =========================================================================
    
    async def run_execution(self, opportunities: List[Dict] = None) -> Dict[str, Any]:
        """Execute opportunities through platform APIs with smart filtering"""
        
        print("\n" + "=" * 70)
        print("⚡ EXECUTION CYCLE")
        print("=" * 70)
        
        if not opportunities:
            print("   No opportunities to execute")
            return {'executed': 0, 'skipped': 0, 'failed': 0}
        
        results = {'executed': 0, 'skipped': 0, 'failed': 0, 'filtered': 0, 'details': []}
        
        # Apply opportunity filters if available
        if SYSTEMS.get('opportunity_filters'):
            try:
                # Filter outliers and stale opportunities
                filtered = []
                for opp in opportunities:
                    if not is_outlier(opp, 50000) and not is_stale(opp, 30):
                        filtered.append(opp)
                    else:
                        results['filtered'] += 1
                
                print(f"   Filtered: {results['filtered']} (outliers/stale)")
                opportunities = filtered
            except Exception as e:
                print(f"   ⚠️ Filter error: {e}")
        
        # Filter by confidence threshold
        high_confidence = [o for o in opportunities if o.get('confidence', 0) >= self.config.auto_execute_threshold]
        
        print(f"   {len(high_confidence)}/{len(opportunities)} above threshold ({self.config.auto_execute_threshold})")
        
        # Get execute-now priorities if available
        if SYSTEMS.get('opportunity_filters') and high_confidence:
            try:
                execute_now = get_execute_now_opportunities({
                    'user_routed': {'opportunities': [{'opportunity': o, 'routing': {'execution_score': {'win_probability': o.get('confidence', 0.5), 'expected_value': o.get('value', 0) * o.get('confidence', 0.5), 'recommendation': 'EXECUTE'}}} for o in high_confidence]},
                    'aigentsy_routed': {'opportunities': []}
                })
                if execute_now:
                    high_confidence = [e['opportunity'] for e in execute_now[:self.config.max_parallel_executions]]
                    print(f"   Prioritized: {len(high_confidence)} high-value opportunities")
            except Exception as e:
                print(f"   ⚠️ Priority filter error: {e}")
        
        if not SYSTEMS.get('platform_apis'):
            print("   ⚠️ Platform APIs not available")
            return results
        
        router = get_platform_router()
        
        # ===== V106 INTEGRATED EXECUTION MODE (NEW) =====
        try:
            from v106_integration_orchestrator import v106_integrated_execution
            v106_mode_available = True
        except:
            v106_mode_available = False
        
        for opp in high_confidence[:self.config.max_parallel_executions]:
            try:
                # ===== V106: Use integrated market-maker + risk-tranche mode =====
                if v106_mode_available and self.config.use_v106_mode:
                    exec_result = await v106_integrated_execution(opp, auto_execute=True)
                    
                    if exec_result.get('ok'):
                        results['executed'] += 1
                    else:
                        results['failed'] += 1
                else:
                    # Standard execution
                    exec_result = await router.execute_opportunity(opp)
                    
                    if exec_result.get('ok'):
                        results['executed'] += 1
                    else:
                        results['failed'] += 1
                
                # Track outcome (common to both modes)
                if SYSTEMS.get('outcome_oracle'):
                    on_event({
                        'kind': 'OPPORTUNITY_EXECUTED',
                        'username': 'aigentsy',
                        'opportunity_id': opp.get('id'),
                        'platform': exec_result.get('platform'),
                        'timestamp': _now()
                    })
                
                # Store learning pattern (common to both modes)
                if SYSTEMS.get('yield_memory'):
                    store_pattern(
                        username='aigentsy',
                        pattern_type='execution',
                        context={'platform': exec_result.get('platform'), 'type': opp.get('type')},
                        action={'executed': True},
                        outcome={'status': 'pending'}
                    )
                    self.stats['patterns_learned'] += 1
                
                results['details'].append(exec_result)
                
            except Exception as e:
                print(f"   ❌ Execution error: {e}")
                results['failed'] += 1
        
        results['skipped'] = len(opportunities) - len(high_confidence)
        
        self.last_execution = _now()
        self.stats['opportunities_executed'] += results['executed']
        
        print(f"\n✅ Execution complete: {results['executed']} executed, {results['failed']} failed, {results['skipped']} skipped, {results['filtered']} filtered")
        
        return results
    
    # =========================================================================
    # SOCIAL POSTING
    # =========================================================================
    
    async def run_social(self) -> Dict[str, Any]:
        """Generate and post content to social platforms"""
        
        print("\n" + "=" * 70)
        print("📱 SOCIAL POSTING CYCLE")
        print("=" * 70)
        
        results = {'posted': 0, 'failed': 0, 'platforms': []}
        
        if not SYSTEMS.get('social_engine'):
            print("   ⚠️ Social engine not available")
            return results
        
        try:
            engine = get_social_engine()
            
            topics = [
                "AI automation saves businesses 10+ hours/week",
                "The future of work is autonomous",
                "How AI agents are transforming freelancing",
            ]
            
            for i, topic in enumerate(topics[:self.config.posts_per_cycle]):
                for platform in self.config.social_platforms:
                    try:
                        result = await engine.create_and_post(
                            user_id='aigentsy',
                            platform=platform,
                            content_type='text',
                            topic=topic,
                            style='engaging'
                        )
                        
                        if result.get('success'):
                            results['posted'] += 1
                            results['platforms'].append(platform)
                        else:
                            results['failed'] += 1
                            
                    except Exception as e:
                        print(f"   ❌ {platform} error: {e}")
                        results['failed'] += 1
            
            self.last_social = _now()
            self.stats['posts_made'] += results['posted']
            
        except Exception as e:
            print(f"   ❌ Social engine error: {e}")
        
        print(f"\n✅ Social complete: {results['posted']} posted")
        
        return results
    
    # =========================================================================
    # AMG CYCLE
    # =========================================================================
    
    async def run_amg(self) -> Dict[str, Any]:
        """Run AMG revenue optimization cycle"""
        
        print("\n" + "=" * 70)
        print("💰 AMG CYCLE")
        print("=" * 70)
        
        if not SYSTEMS.get('amg'):
            print("   ⚠️ AMG not available")
            return {'ok': False}
        
        try:
            orchestrator = AMGOrchestrator()
            result = await orchestrator.run_cycle()
            
            self.last_amg = _now()
            
            print(f"✅ AMG cycle complete")
            return result
            
        except Exception as e:
            print(f"   ❌ AMG error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # R3 REALLOCATION
    # =========================================================================
    
    async def run_r3(self, username: str = 'aigentsy') -> Dict[str, Any]:
        """Run R3 revenue reinvestment"""
        
        print("\n" + "=" * 70)
        print("📊 R3 REALLOCATION")
        print("=" * 70)
        
        if not SYSTEMS.get('r3'):
            print("   ⚠️ R3 not available")
            return {'ok': False}
        
        try:
            result = execute_autopilot_spend(username, budget=100)
            
            self.last_r3 = _now()
            
            print(f"✅ R3 reallocation complete")
            return result
            
        except Exception as e:
            print(f"   ❌ R3 error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # TEAM FORMATION (METABRIDGE)
    # =========================================================================
    
    async def run_team_formation(self) -> Dict[str, Any]:
        """Form teams for complex jobs via MetaBridge"""
        
        print("\n" + "=" * 70)
        print("👥 TEAM FORMATION (METABRIDGE)")
        print("=" * 70)
        
        if not SYSTEMS.get('metabridge'):
            print("   ⚠️ MetaBridge not available")
            return {'ok': False}
        
        try:
            # Get pending complex intents
            # In production, would query from intent queue
            teams_formed = 0
            
            print(f"   Teams formed: {teams_formed}")
            print("   MetaBridge ready for complex job routing")
            
            return {'ok': True, 'teams_formed': teams_formed}
            
        except Exception as e:
            print(f"   ❌ Team formation error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # SYNDICATION CYCLE
    # =========================================================================
    
    async def run_syndication(self) -> Dict[str, Any]:
        """Syndicate overflow to partner networks"""
        
        print("\n" + "=" * 70)
        print("🔄 SYNDICATION (CROSS-NETWORK)")
        print("=" * 70)
        
        if not SYSTEMS.get('syndication'):
            print("   ⚠️ Syndication not available")
            return {'ok': False}
        
        try:
            partners = list(PARTNER_NETWORKS.keys())
            print(f"   Partner networks: {len(partners)} ({', '.join(partners[:3])}...)")
            
            # Would syndicate overflow intents to partner networks
            syndicated = 0
            
            print(f"   Intents syndicated: {syndicated}")
            
            return {'ok': True, 'syndicated': syndicated, 'partners': len(partners)}
            
        except Exception as e:
            print(f"   ❌ Syndication error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # PROOF VERIFICATION CYCLE
    # =========================================================================
    
    async def run_proof_verification(self) -> Dict[str, Any]:
        """Process and verify pending proofs"""
        
        print("\n" + "=" * 70)
        print("✅ PROOF VERIFICATION")
        print("=" * 70)
        
        if not SYSTEMS.get('proof_pipe'):
            print("   ⚠️ Proof pipe not available")
            return {'ok': False}
        
        try:
            # Get pending proofs (would come from database in production)
            # For now, just report system status
            print("   Proof types supported: POS, Booking, Delivery, Photo, Invoice")
            print("   Integrations: Square, Calendly, QuickBooks, Xero")
            
            return {
                'ok': True,
                'proof_types': ['pos_receipt', 'booking_confirmation', 'delivery_signature', 'completion_photo', 'invoice_paid'],
                'integrations': ['square', 'calendly', 'quickbooks', 'xero', 'freshbooks']
            }
            
        except Exception as e:
            print(f"   ❌ Proof verification error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # ARBITRAGE CYCLE
    # =========================================================================
    
    async def run_arbitrage_scan(self) -> Dict[str, Any]:
        """Scan for and execute arbitrage opportunities"""
        
        print("\n" + "=" * 70)
        print("💱 ARBITRAGE SCAN")
        print("=" * 70)
        
        if not SYSTEMS.get('arbitrage_pipeline'):
            print("   ⚠️ Arbitrage pipeline not available")
            return {'ok': False}
        
        try:
            # Execute arbitrage opportunities
            result = await execute_arbitrage(auto_execute=True, max_opportunities=5)
            
            print(f"   Opportunities found: {result.get('found', 0)}")
            print(f"   Executed: {result.get('executed', 0)}")
            print(f"   Profit: ${result.get('profit', 0):.2f}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Arbitrage error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # CLIENT SUCCESS PREDICTION
    # =========================================================================
    
    async def run_success_prediction(self) -> Dict[str, Any]:
        """Predict user success and trigger interventions"""
        
        print("\n" + "=" * 70)
        print("🎯 SUCCESS PREDICTION")
        print("=" * 70)
        
        if not SYSTEMS.get('success_predictor'):
            print("   ⚠️ Success predictor not available")
            return {'ok': False}
        
        try:
            # Get at-risk users
            predictor = ClientSuccessPredictor()
            at_risk = await predictor.get_at_risk_users(threshold=0.3)
            
            print(f"   At-risk users: {len(at_risk)}")
            
            # Trigger interventions
            interventions = []
            for user in at_risk[:10]:
                intervention = await predictor.trigger_intervention(user['username'])
                interventions.append(intervention)
            
            print(f"   Interventions triggered: {len(interventions)}")
            
            return {'ok': True, 'at_risk': len(at_risk), 'interventions': len(interventions)}
            
        except Exception as e:
            print(f"   ❌ Prediction error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # BOOSTER APPLICATION
    # =========================================================================
    
    async def run_booster_cycle(self) -> Dict[str, Any]:
        """Apply and update user boosters"""
        
        print("\n" + "=" * 70)
        print("🚀 BOOSTER CYCLE")
        print("=" * 70)
        
        if not SYSTEMS.get('booster_engine'):
            print("   ⚠️ Booster engine not available")
            return {'ok': False}
        
        try:
            # Get active boosters for platform
            active = get_active_boosters('aigentsy')
            total_mult = calculate_total_multiplier('aigentsy')
            
            print(f"   Active boosters: {len(active)}")
            print(f"   Total multiplier: {total_mult:.2f}x")
            
            return {'ok': True, 'active_boosters': len(active), 'multiplier': total_mult}
            
        except Exception as e:
            print(f"   ❌ Booster error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # JV MESH CYCLE
    # =========================================================================
    
    async def run_jv_matching(self) -> Dict[str, Any]:
        """Run JV partner matching cycle"""
        
        print("\n" + "=" * 70)
        print("🤝 JV MESH MATCHING")
        print("=" * 70)
        
        if not SYSTEMS.get('jv_mesh'):
            print("   ⚠️ JV Mesh not available")
            return {'ok': False}
        
        try:
            # Get active JVs
            active = list_active_jvs()
            print(f"   Active JVs: {active.get('count', 0)}")
            
            return {'ok': True, 'active_jvs': active.get('count', 0)}
            
        except Exception as e:
            print(f"   ❌ JV Mesh error: {e}")
            return {'ok': False, 'error': str(e)}

    # =========================================================================
    # V107-V112 REVENUE ENGINES
    # =========================================================================
    
    async def run_uacr_scan(self) -> Dict[str, Any]:
        """
        V111 - Universal Abandoned Checkout Reclaimer (U-ACR)
        Scan Twitter/Instagram for abandoned checkout signals
        Generate quotes and track potential revenue
        """
        
        if not SYSTEMS.get('v111'):
            return {"ok": False, "error": "V111 not available"}
        
        print("\n🔍 V111 U-ACR SCAN")
        
        try:
            results = {
                "timestamp": _now(),
                "twitter_signals": 0,
                "instagram_signals": 0,
                "quotes_generated": 0,
                "potential_revenue": 0.0
            }
            
            # Scan Twitter for abandoned checkout signals
            twitter_result = await uacr_scan_twitter(max_signals=50)
            results["twitter_signals"] = len(twitter_result.get("signals", []))
            
            # Scan Instagram for shopping signals
            instagram_result = await uacr_scan_instagram(max_signals=50)
            results["instagram_signals"] = len(instagram_result.get("signals", []))
            
            # Generate quotes for high-confidence signals
            quotes_result = await uacr_batch_quote(min_confidence=0.7)
            quotes = quotes_result.get("quotes", [])
            results["quotes_generated"] = len(quotes)
            results["potential_revenue"] = sum(q.get("spread_amount", 0) for q in quotes)
            
            print(f"   📊 Twitter: {results['twitter_signals']} signals")
            print(f"   📊 Instagram: {results['instagram_signals']} signals")
            print(f"   💰 Quotes: {results['quotes_generated']} (${results['potential_revenue']:.2f} potential)")
            
            self.last_uacr = _now()
            
            return {"ok": True, **results}
            
        except Exception as e:
            print(f"   ❌ U-ACR scan failed: {e}")
            return {"ok": False, "error": str(e)}
    
    async def run_receivables_scan(self) -> Dict[str, Any]:
        """
        V111 - Receivables Desk
        Scan Stripe for unpaid invoices and create Kelly-sized advances
        """
        
        if not SYSTEMS.get('v111'):
            return {"ok": False, "error": "V111 not available"}
        
        print("\n💸 V111 RECEIVABLES SCAN")
        
        try:
            # Scan Stripe for overdue invoices
            result = await receivables_scan_stripe(days_overdue=7)
            
            invoices_found = result.get("invoices_found", 0)
            advances_created = result.get("advances_created", 0)
            total_advanced = result.get("total_advanced", 0.0)
            
            print(f"   📊 Invoices: {invoices_found} overdue")
            print(f"   💰 Advances: {advances_created} created (${total_advanced:.2f})")
            
            self.last_receivables = _now()
            
            return {"ok": True, **result}
            
        except Exception as e:
            print(f"   ❌ Receivables scan failed: {e}")
            return {"ok": False, "error": str(e)}
    
    async def run_payments_optimization(self) -> Dict[str, Any]:
        """
        V111 - Payments Interchange Optimizer
        Analyze payment flows and optimize routing to cheapest PSP
        """
        
        if not SYSTEMS.get('v111'):
            return {"ok": False, "error": "V111 not available"}
        
        print("\n💳 V111 PAYMENTS OPTIMIZATION")
        
        try:
            result = await payments_optimize_routing()
            
            routes_analyzed = result.get("routes_analyzed", 0)
            savings = result.get("potential_savings", 0.0)
            
            print(f"   📊 Routes analyzed: {routes_analyzed}")
            print(f"   💰 Potential savings: ${savings:.2f}")
            
            self.last_payments = _now()
            
            return {"ok": True, **result}
            
        except Exception as e:
            print(f"   ❌ Payments optimization failed: {e}")
            return {"ok": False, "error": str(e)}
    
    async def run_market_maker_cycle(self) -> Dict[str, Any]:
        """
        V112 - IFX/OAA Market Maker
        Execute high-frequency market making cycles
        Collect spread revenue (10-30 bps)
        """
        
        if not SYSTEMS.get('v112'):
            return {"ok": False, "error": "V112 not available"}
        
        print("\n📈 V112 MARKET MAKER CYCLE")
        
        try:
            result = await ifx_market_making_cycle()
            
            spreads_collected = result.get("spreads_collected", 0)
            revenue = result.get("revenue", 0.0)
            
            print(f"   📊 Spreads: {spreads_collected} collected")
            print(f"   💰 Revenue: ${revenue:.2f}")
            
            self.last_market_maker = _now()
            
            return {"ok": True, **result}
            
        except Exception as e:
            print(f"   ❌ Market maker failed: {e}")
            return {"ok": False, "error": str(e)}
    
    async def run_tranche_settlements(self) -> Dict[str, Any]:
        """
        V112 - Risk Tranching Settlements
        Check for tranche settlements and distribute returns
        Collect AiGentsy carry (15% of profits)
        """
        
        if not SYSTEMS.get('v112'):
            return {"ok": False, "error": "V112 not available"}
        
        print("\n🏦 V112 TRANCHE SETTLEMENTS")
        
        try:
            result = await tranche_check_settlements()
            
            settlements = result.get("settlements", 0)
            carry = result.get("aigentsy_carry", 0.0)
            
            print(f"   📊 Settlements: {settlements}")
            print(f"   💰 AiGentsy carry: ${carry:.2f}")
            
            self.last_tranches = _now()
            
            return {"ok": True, **result}
            
        except Exception as e:
            print(f"   ❌ Tranche settlements failed: {e}")
            return {"ok": False, "error": str(e)}
    
    async def run_gap_harvesters(self) -> Dict[str, Any]:
        """
        V110 - Gap Harvesters (15 Engines)
        Scan for waste monetization opportunities across all harvesters
        """
        
        if not SYSTEMS.get('v110'):
            return {"ok": False, "error": "V110 not available"}
        
        print("\n🔍 V110 GAP HARVESTERS SCAN")
        
        try:
            result = await scan_all_harvesters()
            
            opportunities = result.get("opportunities_found", 0)
            potential_revenue = result.get("potential_revenue", 0.0)
            
            print(f"   📊 Opportunities: {opportunities} found")
            print(f"   💰 Potential: ${potential_revenue:.2f}")
            
            self.last_gap_harvesters = _now()
            
            return {"ok": True, **result}
            
        except Exception as e:
            print(f"   ❌ Gap harvesters failed: {e}")
            return {"ok": False, "error": str(e)}
    
    # =========================================================================
    # VALUE CHAIN CYCLE
    # =========================================================================
    
    async def run_value_chain(self) -> Dict[str, Any]:
        """Run value chain discovery"""
        
        print("\n" + "=" * 70)
        print("🔗 VALUE CHAIN DISCOVERY")
        print("=" * 70)
        
        if not SYSTEMS.get('value_chain'):
            print("   ⚠️ Value Chain not available")
            return {'ok': False}
        
        try:
            # Discover value chains for e-commerce
            chains = await discover_value_chain(
                initiator='aigentsy',
                initiator_capability='ai_automation',
                target_outcome='ecommerce_sales',
                max_hops=3
            )
            
            print(f"   Chains discovered: {len(chains.get('chains', []))}")
            
            return {'ok': True, 'chains': len(chains.get('chains', []))}
            
        except Exception as e:
            print(f"   ❌ Value Chain error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # REVENUE RECONCILIATION
    # =========================================================================
    
    async def run_reconciliation(self) -> Dict[str, Any]:
        """Run revenue reconciliation"""
        
        print("\n" + "=" * 70)
        print("📊 REVENUE RECONCILIATION")
        print("=" * 70)
        
        if not SYSTEMS.get('revenue_reconciliation'):
            print("   ⚠️ Revenue Reconciliation not available")
            return {'ok': False}
        
        try:
            result = await reconcile_entries('aigentsy')
            
            print(f"   Reconciled: {result.get('matched', 0)} entries")
            print(f"   Discrepancies: {result.get('discrepancies', 0)}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Reconciliation error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # LEARNING SYNC
    # =========================================================================
    
    async def run_learning_sync(self) -> Dict[str, Any]:
        """Sync learnings to MetaHive"""
        
        print("\n" + "=" * 70)
        print("🧠 LEARNING SYNC")
        print("=" * 70)
        
        results = {'yield_memory': None, 'metahive': None}
        
        if SYSTEMS.get('yield_memory'):
            try:
                stats = get_memory_stats('aigentsy')
                results['yield_memory'] = stats
                print(f"   Yield Memory: {stats.get('total_patterns', 0)} patterns")
            except Exception as e:
                print(f"   ❌ Yield Memory error: {e}")
        
        if SYSTEMS.get('metahive'):
            try:
                stats = get_hive_stats()
                results['metahive'] = stats
                print(f"   MetaHive: {stats.get('total_patterns', 0)} shared patterns")
            except Exception as e:
                print(f"   ❌ MetaHive error: {e}")
        
        self.last_learning_sync = _now()
        
        print(f"✅ Learning sync complete")
        
        return results
    
    # =========================================================================
    # FULL CYCLE
    # =========================================================================
    
    async def run_full_cycle(self) -> Dict[str, Any]:
        """Run complete cycle of all systems"""
        
        self.cycle_count += 1
        
        print("\n" + "=" * 70)
        print(f"🔄 FULL CYCLE #{self.cycle_count}")
        print("=" * 70)
        
        results = {'cycle': self.cycle_count, 'started_at': _now(), 'phases': {}}
        
        # 1. Discovery
        discovery = await self.run_discovery()
        results['phases']['discovery'] = {'opportunities': len(discovery.get('opportunities', []))}
        
        # 2. Execution
        if discovery.get('opportunities'):
            execution = await self.run_execution(discovery['opportunities'])
            results['phases']['execution'] = execution
        
        # 3. Social (if interval elapsed)
        if self._should_run('social', self.config.social_interval_minutes):
            social = await self.run_social()
            results['phases']['social'] = social
        
        # 4. AMG (if interval elapsed)
        if self._should_run('amg', self.config.amg_interval_minutes):
            amg = await self.run_amg()
            results['phases']['amg'] = {'ran': True}
        
        # 5. R3 (if interval elapsed)
        if self._should_run('r3', self.config.r3_interval_hours * 60):
            r3 = await self.run_r3()
            results['phases']['r3'] = {'ran': True}
        
        # 6. Learning sync (if interval elapsed)
        if self._should_run('learning', self.config.learning_sync_interval_hours * 60):
            learning = await self.run_learning_sync()
            results['phases']['learning'] = learning
        
        # 7. JV Matching (daily)
        if self._should_run('jv', 24 * 60):
            jv = await self.run_jv_matching()
            results['phases']['jv_mesh'] = jv
        
        # 8. Value Chain Discovery (every 6 hours)
        if self._should_run('value_chain', 6 * 60):
            vc = await self.run_value_chain()
            results['phases']['value_chain'] = vc
        
        # 9. Revenue Reconciliation (daily)
        if self._should_run('reconciliation', 24 * 60):
            recon = await self.run_reconciliation()
            results['phases']['reconciliation'] = recon
        
        # 10. Arbitrage Scan (every 2 hours)
        if self._should_run('arbitrage', 2 * 60):
            arb = await self.run_arbitrage_scan()
            results['phases']['arbitrage'] = arb
        
        # 11. Success Prediction (daily)
        if self._should_run('success_pred', 24 * 60):
            pred = await self.run_success_prediction()
            results['phases']['success_prediction'] = pred
        
        # 12. Booster Cycle (every 6 hours)
        if self._should_run('boosters', 6 * 60):
            boost = await self.run_booster_cycle()
            results['phases']['boosters'] = boost
        
        # 13. Proof Verification (every 2 hours)
        if self._should_run('proofs', 2 * 60):
            proofs = await self.run_proof_verification()
            results['phases']['proof_verification'] = proofs
        
        # 14. Team Formation (every 4 hours)
        if self._should_run('teams', 4 * 60):
            teams = await self.run_team_formation()
            results['phases']['team_formation'] = teams
        
        # 15. Syndication (daily)
        if self._should_run('syndication', 24 * 60):
            synd = await self.run_syndication()
            results['phases']['syndication'] = synd
        
        # 16. Internet-Wide Discovery (every 30 min) - searches entire internet
        if self._should_run('internet_discovery', 30):
            internet = await self.run_internet_discovery()
            results['phases']['internet_discovery'] = internet

        # 17. V111 U-ACR (every 15 min) - $4.6T TAM
        if self._should_run('uacr', self.config.uacr_scan_interval_minutes):
            uacr = await self.run_uacr_scan()
            results['phases']['uacr'] = uacr
        
        # 18. V111 Receivables (every 60 min)
        if self._should_run('receivables', self.config.receivables_scan_interval_minutes):
            recv = await self.run_receivables_scan()
            results['phases']['receivables'] = recv
        
        # 19. V111 Payments (every 30 min)
        if self._should_run('payments', self.config.payments_optimization_interval_minutes):
            pay = await self.run_payments_optimization()
            results['phases']['payments'] = pay
        
        # 20. V112 Market Maker (every 5 min) - High frequency
        if self._should_run('market_maker', self.config.market_maker_interval_minutes):
            mm = await self.run_market_maker_cycle()
            results['phases']['market_maker'] = mm
        
        # 21. V112 Tranche Settlements (every 60 min)
        if self._should_run('tranches', self.config.tranche_settlement_check_minutes):
            tranches = await self.run_tranche_settlements()
            results['phases']['tranches'] = tranches
        
        # 22. V110 Gap Harvesters (every 30 min) - 15 engines
        if self._should_run('gap_harvesters', self.config.gap_harvester_scan_minutes):
            gap = await self.run_gap_harvesters()
            results['phases']['gap_harvesters'] = gap
        
        results['completed_at'] = _now()
        results['stats'] = self.stats
        
        print("\n" + "=" * 70)
        print(f"✅ CYCLE #{self.cycle_count} COMPLETE")
        print(f"   Opportunities: {self.stats['opportunities_discovered']} discovered, {self.stats['opportunities_executed']} executed")
        print(f"   Posts: {self.stats['posts_made']}")
        print(f"   Patterns: {self.stats['patterns_learned']}")
        print("=" * 70)
        
        return results
    
    def _should_run(self, phase: str, interval_minutes: int) -> bool:
        """Check if phase interval has elapsed"""
        timestamps = {
            'social': self.last_social,
            'amg': self.last_amg,
            'r3': self.last_r3,
            'learning': self.last_learning_sync,
            'jv': getattr(self, 'last_jv', None),
            'value_chain': getattr(self, 'last_value_chain', None),
            'reconciliation': getattr(self, 'last_reconciliation', None),
            'arbitrage': getattr(self, 'last_arbitrage', None),
            'success_pred': getattr(self, 'last_success_pred', None),
            'boosters': getattr(self, 'last_boosters', None),
            'proofs': getattr(self, 'last_proofs', None),
            'teams': getattr(self, 'last_teams', None),
            'syndication': getattr(self, 'last_syndication', None)
            'uacr': getattr(self, 'last_uacr', None),
            'receivables': getattr(self, 'last_receivables', None),
            'payments': getattr(self, 'last_payments', None),
            'market_maker': getattr(self, 'last_market_maker', None),
            'tranches': getattr(self, 'last_tranches', None),
            'gap_harvesters': getattr(self, 'last_gap_harvesters', None),
        }
        
        last = timestamps.get(phase)
        if not last:
            return True
        
        try:
            last_dt = datetime.fromisoformat(last.replace('Z', '+00:00'))
            elapsed = (_now_dt() - last_dt).total_seconds() / 60
            return elapsed >= interval_minutes
        except:
            return True

    
    
    # =========================================================================
    # CONTINUOUS RUNNING
    # =========================================================================
    
    async def run_continuous(self):
        """Run continuously"""
        
        print("\n🚀 STARTING CONTINUOUS RUNTIME")
        print(f"   Discovery: every {self.config.discovery_interval_minutes} min")
        print(f"   Social: every {self.config.social_interval_minutes} min")
        print(f"   AMG: every {self.config.amg_interval_minutes} min")
        print("   Press Ctrl+C to stop\n")
        print(f"   V111 U-ACR: every {self.config.uacr_scan_interval_minutes} min")
        print(f"   V111 Receivables: every {self.config.receivables_scan_interval_minutes} min")
        print(f"   V111 Payments: every {self.config.payments_optimization_interval_minutes} min")
        print(f"   V112 Market Maker: every {self.config.market_maker_interval_minutes} min")
        print(f"   V110 Gap Harvesters: every {self.config.gap_harvester_scan_minutes} min")
        
        self._running = True
        
        while self._running:
            try:
                await self.run_full_cycle()
                
                print(f"\n⏳ Next cycle in {self.config.discovery_interval_minutes} minutes...")
                
                try:
                    await asyncio.wait_for(
                        self._shutdown.wait(),
                        timeout=self.config.discovery_interval_minutes * 60
                    )
                    break
                except asyncio.TimeoutError:
                    pass
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n❌ Cycle error: {e}")
                await asyncio.sleep(60)
        
        self._running = False
        print("\n👋 Runtime stopped.")
    
    def stop(self):
        """Stop the runtime"""
        self._running = False
        self._shutdown.set()


# =============================================================================
# SINGLETON
# =============================================================================

_runtime: Optional[AiGentsyMasterRuntime] = None

def get_master_runtime(config: RuntimeConfig = None) -> AiGentsyMasterRuntime:
    global _runtime
    if _runtime is None:
        _runtime = AiGentsyMasterRuntime(config)
    return _runtime


# =============================================================================
# CLI
# =============================================================================

async def main():
    parser = argparse.ArgumentParser(description='AiGentsy Master Runtime')
    parser.add_argument('--once', action='store_true', help='Run single cycle')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--discovery', action='store_true', help='Run discovery only')
    parser.add_argument('--social', action='store_true', help='Run social only')
    parser.add_argument('--amg', action='store_true', help='Run AMG only')
    parser.add_argument('--learning', action='store_true', help='Run learning sync only')
    parser.add_argument('--internet', action='store_true', help='Run internet-wide discovery only')
    parser.add_argument('--outreach', action='store_true', help='Show outreach stats')
    
    args = parser.parse_args()
    
    runtime = get_master_runtime()
    
    if args.status:
        status = runtime.get_system_status()
        print(f"\n📊 SYSTEM STATUS")
        print(f"   Available: {status['available']}/{status['total']} systems")
        print(f"\n   Systems:")
        for name, available in status['systems'].items():
            print(f"   {'✅' if available else '❌'} {name}")
        return
    
    if args.internet:
        result = await runtime.run_internet_discovery()
        print(f"\n🌐 Internet Discovery Result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Opportunities: {result.get('opportunities_found', 0)}")
        print(f"   With Contact: {result.get('with_contact', 0)}")
        return
    
    if args.outreach:
        if SYSTEMS.get('direct_outreach'):
            outreach = get_outreach_engine()
            stats = outreach.get_stats()
            print(f"\n📧 OUTREACH STATS")
            print(f"   Total attempts: {stats['total_attempts']}")
            print(f"   Sent: {stats['sent']}")
            print(f"   Reply rate: {stats['reply_rate']:.1%}")
            print(f"   Daily: {stats['daily_count']}/{stats['daily_limit']}")
            print(f"\n   Channels:")
            for channel, configured in stats['channels_configured'].items():
                print(f"   {'✅' if configured else '❌'} {channel}")
        else:
            print("❌ Direct outreach not available")
        return
    
    if args.discovery:
        await runtime.run_discovery()
        return
    
    if args.social:
        await runtime.run_social()
        return
    
    if args.amg:
        await runtime.run_amg()
        return
    
    if args.learning:
        await runtime.run_learning_sync()
        return
    
    if args.once:
        await runtime.run_full_cycle()
        return
    
    # Default: run continuously
    def signal_handler(sig, frame):
        print("\n🛑 Shutdown signal...")
        runtime.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await runtime.run_continuous()


if __name__ == "__main__":
    asyncio.run(main())
