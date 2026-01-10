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
    from alpha_discovery_engine import discover_all_opportunities, AlphaDiscoveryEngine
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
    from advanced_discovery_dimensions import (
        PredictiveIntelligenceEngine,
        NetworkAmplificationEngine,
        OpportunityCreationEngine,
        EmergentPatternEngine
    )
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
    from real_signal_ingestion import get_signal_engine, ingest_all_signals
    SYSTEMS['signal_ingestion'] = True
    print("✅ real_signal_ingestion")
except ImportError as e:
    SYSTEMS['signal_ingestion'] = False
    print(f"❌ real_signal_ingestion: {e}")

try:
    from pain_point_detector import detect_pain_points
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
    from aigentsy_conductor import AigentsyConductor, get_conductor
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
    from r3_autopilot import execute_autopilot_spend, get_autopilot_status
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
    from ocl_p2p_lending import request_loan, get_available_stakes
    SYSTEMS['ocl'] = True
    print("✅ ocl_p2p_lending")
except ImportError as e:
    SYSTEMS['ocl'] = False
    print(f"❌ ocl_p2p_lending: {e}")

try:
    from agent_factoring import request_factoring_advance
    SYSTEMS['factoring'] = True
    print("✅ agent_factoring")
except ImportError as e:
    SYSTEMS['factoring'] = False
    print(f"❌ agent_factoring: {e}")

try:
    from aigx_engine import get_aigx_balance, credit_aigx as aigx_credit
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
    from value_chain_engine import discover_value_chain, execute_value_chain
    SYSTEMS['value_chain'] = True
    print("✅ value_chain_engine")
except ImportError as e:
    SYSTEMS['value_chain'] = False
    print(f"❌ value_chain_engine: {e}")

# ----- MONETIZATION -----
try:
    from third_party_monetization import ThirdPartyMonetizationEngine, process_traffic_event
    SYSTEMS['third_party_monetization'] = True
    print("✅ third_party_monetization")
except ImportError as e:
    SYSTEMS['third_party_monetization'] = False
    print(f"❌ third_party_monetization: {e}")

try:
    from revenue_reconciliation_engine import RevenueReconciliationEngine, reconcile_entries
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
    from booster_engine import apply_booster, get_active_boosters, calculate_total_multiplier
    SYSTEMS['booster_engine'] = True
    print("✅ booster_engine")
except ImportError as e:
    SYSTEMS['booster_engine'] = False
    print(f"❌ booster_engine: {e}")

try:
    from platform_recruitment_engine import PlatformRecruitmentEngine, generate_recruitment_cta
    SYSTEMS['recruitment_engine'] = True
    print("✅ platform_recruitment_engine")
except ImportError as e:
    SYSTEMS['recruitment_engine'] = False
    print(f"❌ platform_recruitment_engine: {e}")

# ----- ARBITRAGE -----
try:
    from arbitrage_execution_pipeline import ArbitrageExecutor, execute_arbitrage
    SYSTEMS['arbitrage_pipeline'] = True
    print("✅ arbitrage_execution_pipeline")
except ImportError as e:
    SYSTEMS['arbitrage_pipeline'] = False
    print(f"❌ arbitrage_execution_pipeline: {e}")

# ----- FRANCHISE & BUSINESS -----
try:
    from franchise_engine import create_franchise_license, get_franchise_stats
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
    from aigx_protocol import AIGxProtocol, get_protocol
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
    from autonomous_reconciliation_engine import AutonomousReconciliationEngine, get_reconciliation_summary
    SYSTEMS['autonomous_reconciliation'] = True
    print("✅ autonomous_reconciliation_engine")
except ImportError as e:
    SYSTEMS['autonomous_reconciliation'] = False
    print(f"❌ autonomous_reconciliation_engine: {e}")

# ----- PRICING & PROFIT -----
try:
    from intelligent_pricing_autopilot import PricingAutopilot, optimize_bid_price
    SYSTEMS['pricing_autopilot'] = True
    print("✅ intelligent_pricing_autopilot")
except ImportError as e:
    SYSTEMS['pricing_autopilot'] = False
    print(f"❌ intelligent_pricing_autopilot: {e}")

try:
    from profit_engine_v98 import ProfitGates, check_roi_gate
    SYSTEMS['profit_engine'] = True
    print("✅ profit_engine_v98")
except ImportError as e:
    SYSTEMS['profit_engine'] = False
    print(f"❌ profit_engine_v98: {e}")

# ----- METAHIVE PUBLIC API -----
try:
    from open_metahive_api import OpenMetaHiveAPI, contribute_pattern, get_patterns
    SYSTEMS['open_metahive_api'] = True
    print("✅ open_metahive_api (External AI contributions)")
except ImportError as e:
    SYSTEMS['open_metahive_api'] = False
    print(f"❌ open_metahive_api: {e}")

# ----- INDUSTRY & KNOWLEDGE -----
try:
    from industry_knowledge import INDUSTRY_TEMPLATES, get_industry_config
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
    from diagnostic_tracer import check_environment, trace_full_cycle
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
    from ame_amg_endpoints import track_visit_handler, track_conversion_handler, amg_optimize_handler
    SYSTEMS['ame_amg_endpoints'] = True
    print("✅ ame_amg_endpoints")
except ImportError as e:
    SYSTEMS['ame_amg_endpoints'] = False
    print(f"❌ ame_amg_endpoints: {e}")

# ----- SYNDICATION & CROSS-NETWORK -----
try:
    from syndication import syndicate_intent, create_royalty_trail, PARTNER_NETWORKS
    SYSTEMS['syndication'] = True
    print("✅ syndication (Cross-network routing)")
except ImportError as e:
    SYSTEMS['syndication'] = False
    print(f"❌ syndication: {e}")

# ----- STATE MONEY (ESCROW) -----
try:
    from state_money import transition_deal_state, create_escrow_hold, release_escrow, STATE_TRANSITIONS
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
    from metabridge import analyze_intent_complexity, find_complementary_agents, form_team
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
    from wade_bidding_system import generate_bid_proposal, submit_bid, monitor_bids, OpportunityStatus
    SYSTEMS['wade_bidding'] = True
    print("✅ wade_bidding_system")
except ImportError as e:
    SYSTEMS['wade_bidding'] = False
    print(f"❌ wade_bidding_system: {e}")

# ----- TEMPLATE SYSTEMS -----
try:
    from template_library import LEGAL_TEMPLATES, SAAS_TEMPLATES, MARKETING_TEMPLATES, get_template
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
        
        for opp in high_confidence[:self.config.max_parallel_executions]:
            try:
                exec_result = await router.execute_opportunity(opp)
                
                if exec_result.get('ok'):
                    results['executed'] += 1
                    
                    # Track outcome
                    if SYSTEMS.get('outcome_oracle'):
                        on_event({
                            'kind': 'OPPORTUNITY_EXECUTED',
                            'username': 'aigentsy',
                            'opportunity_id': opp.get('id'),
                            'platform': exec_result.get('platform'),
                            'timestamp': _now()
                        })
                    
                    # Store learning pattern
                    if SYSTEMS.get('yield_memory'):
                        store_pattern(
                            username='aigentsy',
                            pattern_type='execution',
                            context={'platform': exec_result.get('platform'), 'type': opp.get('type')},
                            action={'executed': True},
                            outcome={'status': 'pending'}
                        )
                        self.stats['patterns_learned'] += 1
                else:
                    results['failed'] += 1
                
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
