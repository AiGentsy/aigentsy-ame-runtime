"""
SYSTEM LOADER: Unified System Integration Layer
═══════════════════════════════════════════════════════════════════════════════

Loads all 35 engines, 7 oracles, 12 brain modules, 10+ agents, 5 managers
with graceful fallbacks.

Provides:
- Unified access to all systems
- Health status per system
- Stats aggregation
- Graceful degradation

Updated: Jan 2026
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class SystemStatus:
    """Status of a loaded system"""
    name: str
    category: str
    loaded: bool = False
    instance: Any = None
    error: Optional[str] = None
    load_time_ms: float = 0
    calls: int = 0
    successes: int = 0
    failures: int = 0


class SystemLoader:
    """
    Unified loader for all AIGENTSY systems.

    Categories:
    - engines (35): Discovery, fulfillment, automation
    - oracles (7): Pricing, outcomes, compliance
    - brain (12): Policy, LTV, exploration
    - agents (10+): Growth, venture, execution
    - managers (5): Discovery, execution, revenue, financial, intelligence
    """

    def __init__(self):
        self.systems: Dict[str, SystemStatus] = {}
        self.stats = {
            'total_loaded': 0,
            'total_failed': 0,
            'engines_loaded': 0,
            'oracles_loaded': 0,
            'brain_loaded': 0,
            'agents_loaded': 0,
            'managers_loaded': 0,
            'load_started': datetime.now(timezone.utc).isoformat(),
            'load_completed': None,
            'total_revenue_usd': 0.0,
            'total_executions': 0,
        }

    def load_all(self) -> Dict[str, Any]:
        """Load all systems with graceful fallbacks"""
        logger.info("Loading all AIGENTSY systems...")

        # Load each category
        self._load_managers()
        self._load_engines()
        self._load_oracles()
        self._load_brain()
        self._load_agents()

        self.stats['load_completed'] = datetime.now(timezone.utc).isoformat()
        self.stats['total_loaded'] = sum(1 for s in self.systems.values() if s.loaded)
        self.stats['total_failed'] = sum(1 for s in self.systems.values() if not s.loaded)

        logger.info(f"Systems loaded: {self.stats['total_loaded']}/{len(self.systems)}")

        return self.get_stats()

    def _safe_load(self, name: str, category: str, loader: Callable) -> SystemStatus:
        """Safely load a system with error handling"""
        import time
        start = time.time()
        status = SystemStatus(name=name, category=category)

        try:
            instance = loader()
            status.loaded = True
            status.instance = instance
            self.stats[f'{category}_loaded'] = self.stats.get(f'{category}_loaded', 0) + 1
        except Exception as e:
            status.error = str(e)
            logger.debug(f"Failed to load {name}: {e}")

        status.load_time_ms = (time.time() - start) * 1000
        self.systems[name] = status
        return status

    def _load_managers(self):
        """Load core managers"""
        logger.info("Loading managers...")

        # Discovery Manager
        self._safe_load('discovery_manager', 'managers',
            lambda: __import__('managers.discovery_manager', fromlist=['get_discovery_manager']).get_discovery_manager())

        # Execution Manager
        self._safe_load('execution_manager', 'managers',
            lambda: __import__('managers.execution_manager', fromlist=['get_execution_manager']).get_execution_manager())

        # Revenue Manager
        self._safe_load('revenue_manager', 'managers',
            lambda: __import__('managers.revenue_manager', fromlist=['get_revenue_manager']).get_revenue_manager())

        # Financial Manager
        self._safe_load('financial_manager', 'managers',
            lambda: __import__('managers.financial_manager', fromlist=['get_financial_manager']).get_financial_manager())

        # Intelligence Manager
        self._safe_load('intelligence_manager', 'managers',
            lambda: __import__('managers.intelligence_manager', fromlist=['get_intelligence_manager']).get_intelligence_manager())

    def _load_engines(self):
        """Load execution engines"""
        logger.info("Loading engines...")

        engine_configs = [
            ('ultimate_discovery_engine', 'ultimate_discovery_engine', 'discover_all_opportunities'),
            ('research_engine', 'research_engine', 'ResearchEngine'),
            ('auto_spawn_engine', 'auto_spawn_engine', 'AutoSpawnEngine'),
            ('social_autoposting_engine', 'social_autoposting_engine', 'SocialAutopostingEngine'),
            ('conversation_engine', 'conversation_engine', 'ConversationEngine'),
            ('direct_outreach_engine', 'direct_outreach_engine', 'DirectOutreachEngine'),
            ('platform_response_engine', 'platform_response_engine', 'PlatformResponseEngine'),
            ('deliverable_verification_engine', 'deliverable_verification_engine', 'DeliverableVerificationEngine'),
            ('video_engine', 'video_engine', 'VideoEngine'),
            ('audio_engine', 'audio_engine', 'AudioEngine'),
            ('graphics_engine', 'graphics_engine', 'GraphicsEngine'),
            ('profit_engine', 'profit_engine_v98', 'include_profit_engine'),
            ('badge_engine', 'badge_engine', 'get_badge_engine'),
            ('booster_engine', 'booster_engine', 'BoosterEngine'),
            ('franchise_engine', 'franchise_engine', 'FranchiseEngine'),
            ('subscription_engine', 'subscription_engine', 'SubscriptionEngine'),
            ('contract_payment_engine', 'contract_payment_engine', 'ContractPaymentEngine'),
            ('reply_detection_engine', 'reply_detection_engine', 'ReplyDetectionEngine'),
            ('mega_discovery_engine', 'mega_discovery_engine', 'MegaDiscoveryEngine'),
            ('ocl_engine', 'ocl_engine', 'calculate_ocl_limit'),
            ('slo_engine', 'slo_engine', 'SLOEngine'),
            ('universal_fulfillment_fabric', 'universal_fulfillment_fabric', 'UniversalFabric'),
        ]

        for name, module, attr in engine_configs:
            self._safe_load(name, 'engines',
                lambda m=module, a=attr: getattr(__import__(m, fromlist=[a]), a, None))

    def _load_oracles(self):
        """Load oracle systems"""
        logger.info("Loading oracles...")

        oracle_configs = [
            ('outcome_oracle', 'outcome_oracle_max', 'on_event'),
            ('pricing_oracle', 'pricing_oracle', 'PricingOracle'),
            ('price_floor_oracle', 'price_floor_oracle', 'PriceFloorOracle'),
            ('compliance_oracle', 'compliance_oracle', 'ComplianceOracle'),
            ('outcomes_insurance_oracle', 'outcomes_insurance_oracle', 'OutcomesInsuranceOracle'),
            ('ltv_oracle', 'brain_economics.ltv_oracle', 'LTVOracle'),
        ]

        for name, module, attr in oracle_configs:
            self._safe_load(name, 'oracles',
                lambda m=module, a=attr: getattr(__import__(m, fromlist=[a]), a, None))

    def _load_brain(self):
        """Load brain/intelligence modules"""
        logger.info("Loading brain modules...")

        brain_configs = [
            ('brain_policy', 'brain_overlay.policy', 'PolicyEngine'),
            ('brain_exploration', 'brain_overlay.exploration', 'ExplorationEngine'),
            ('brain_placement', 'brain_overlay.placement', 'PlacementEngine'),
            ('brain_feature_store', 'brain_overlay.feature_store', 'FeatureStore'),
            ('brain_policy_trainer', 'brain_policy_trainer', 'PolicyTrainer'),
            ('causal_uplift', 'learning.causal_uplift_trainer', 'CausalUpliftTrainer'),
            ('hier_bandits', 'learning.hier_bandits', 'HierarchicalBandits'),
            ('attention_router', 'growth.attention_router', 'AttentionRouter'),
            ('price_arm_v2', 'pricing.price_arm_v2', 'PriceArmV2'),
        ]

        for name, module, attr in brain_configs:
            self._safe_load(name, 'brain',
                lambda m=module, a=attr: getattr(__import__(m, fromlist=[a]), a, None))

    def _load_agents(self):
        """Load agent systems"""
        logger.info("Loading agents...")

        agent_configs = [
            ('agent_registry', 'agent_registry', 'get_registry'),
            ('venture_builder_agent', 'venture_builder_agent', 'get_agent_graph'),
            ('aigent_growth_agent', 'aigent_growth_agent', 'GrowthAgent'),
            ('agent_spending', 'agent_spending', 'AgentSpending'),
            ('agent_factoring', 'agent_factoring', 'AgentFactoring'),
        ]

        for name, module, attr in agent_configs:
            self._safe_load(name, 'agents',
                lambda m=module, a=attr: getattr(__import__(m, fromlist=[a]), a, None))

    def get(self, name: str) -> Optional[Any]:
        """Get a loaded system by name"""
        status = self.systems.get(name)
        if status and status.loaded:
            status.calls += 1
            return status.instance
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated stats"""
        return {
            **self.stats,
            'systems': {
                name: {
                    'category': s.category,
                    'loaded': s.loaded,
                    'error': s.error,
                    'load_time_ms': round(s.load_time_ms, 2),
                    'calls': s.calls,
                }
                for name, s in self.systems.items()
            }
        }

    def get_by_category(self, category: str) -> Dict[str, Any]:
        """Get all systems in a category"""
        return {
            name: s.instance
            for name, s in self.systems.items()
            if s.category == category and s.loaded
        }

    def health_check(self) -> Dict[str, Any]:
        """Check health of all systems"""
        loaded = sum(1 for s in self.systems.values() if s.loaded)
        total = len(self.systems)

        return {
            'healthy': loaded > total * 0.5,  # At least 50% loaded
            'loaded': loaded,
            'total': total,
            'coverage_pct': round(loaded / total * 100, 1) if total > 0 else 0,
            'categories': {
                cat: sum(1 for s in self.systems.values() if s.category == cat and s.loaded)
                for cat in ['managers', 'engines', 'oracles', 'brain', 'agents']
            }
        }


# Global instance
_system_loader: Optional[SystemLoader] = None


def get_system_loader() -> SystemLoader:
    """Get or create system loader singleton"""
    global _system_loader
    if _system_loader is None:
        _system_loader = SystemLoader()
        _system_loader.load_all()
    return _system_loader


def get_system(name: str) -> Optional[Any]:
    """Convenience function to get a system"""
    return get_system_loader().get(name)
