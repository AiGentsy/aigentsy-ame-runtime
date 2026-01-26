"""
ACCESS PANEL ADAPTER: Bridge to Existing Systems

Integrates the Access Panel with:
- AttentionRouter (Thompson Sampling)
- R3Allocator (Kelly Criterion)
- ExecutionManager (Universal Fabric)
- DiscoveryManager (17 sources)
- MetaHive Brain (platform patterns)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try to import existing systems
SYSTEMS_AVAILABLE = {}

try:
    from growth.attention_router import get_attention_router, AttentionRouter
    SYSTEMS_AVAILABLE['attention_router'] = True
except ImportError:
    SYSTEMS_AVAILABLE['attention_router'] = False
    logger.warning("AttentionRouter not available")

try:
    from allocation.r3_allocator import get_r3_allocator
    SYSTEMS_AVAILABLE['r3_allocator'] = True
except ImportError:
    SYSTEMS_AVAILABLE['r3_allocator'] = False
    logger.warning("R3Allocator not available")

try:
    from managers.execution_manager import get_execution_manager
    SYSTEMS_AVAILABLE['execution_manager'] = True
except ImportError:
    SYSTEMS_AVAILABLE['execution_manager'] = False
    logger.warning("ExecutionManager not available")

try:
    from managers.discovery_manager import get_discovery_manager
    SYSTEMS_AVAILABLE['discovery_manager'] = True
except ImportError:
    SYSTEMS_AVAILABLE['discovery_manager'] = False
    logger.warning("DiscoveryManager not available")

try:
    from metahive_brain import get_metahive_brain
    SYSTEMS_AVAILABLE['metahive_brain'] = True
except ImportError:
    SYSTEMS_AVAILABLE['metahive_brain'] = False
    logger.warning("MetaHive Brain not available")

try:
    from ai_family_brain import get_ai_family_brain
    SYSTEMS_AVAILABLE['ai_family_brain'] = True
except ImportError:
    SYSTEMS_AVAILABLE['ai_family_brain'] = False
    logger.warning("AI Family Brain not available")

# Import Access Panel components
try:
    from enrichment import get_enrichment_pipeline
    from routing import get_conversion_router, get_inventory_scorer
    from risk import get_anti_abuse, get_reputation_scorer
    from observability import get_metrics, get_audit_log
    from observability.audit_log import AuditEventType
    ACCESS_PANEL_AVAILABLE = True
except ImportError:
    ACCESS_PANEL_AVAILABLE = False
    logger.warning("Access Panel components not available")


class AccessPanelAdapter:
    """
    Bridge between Access Panel and existing AIGENTSY systems.

    Responsibilities:
    - Route opportunities through existing AttentionRouter
    - Allocate capital through R3Allocator
    - Execute through ExecutionManager
    - Learn from MetaHive patterns
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

        # Get existing system instances
        self.attention_router = get_attention_router() if SYSTEMS_AVAILABLE['attention_router'] else None
        self.r3_allocator = get_r3_allocator() if SYSTEMS_AVAILABLE['r3_allocator'] else None
        self.execution_manager = get_execution_manager() if SYSTEMS_AVAILABLE['execution_manager'] else None
        self.discovery_manager = get_discovery_manager() if SYSTEMS_AVAILABLE['discovery_manager'] else None
        self.metahive = get_metahive_brain() if SYSTEMS_AVAILABLE['metahive_brain'] else None
        self.ai_brain = get_ai_family_brain() if SYSTEMS_AVAILABLE['ai_family_brain'] else None

        # Get Access Panel components
        if ACCESS_PANEL_AVAILABLE:
            self.enrichment = get_enrichment_pipeline()
            self.conversion_router = get_conversion_router()
            self.inventory_scorer = get_inventory_scorer()
            self.anti_abuse = get_anti_abuse()
            self.reputation_scorer = get_reputation_scorer()
            self.metrics = get_metrics()
            self.audit_log = get_audit_log()
        else:
            self.enrichment = None
            self.conversion_router = None
            self.inventory_scorer = None
            self.anti_abuse = None
            self.reputation_scorer = None
            self.metrics = None
            self.audit_log = None

        self.stats = {
            'processed': 0,
            'routed_via_attention': 0,
            'allocated_via_r3': 0,
            'executed_via_manager': 0,
        }

    async def process_opportunity(self, opportunity: Dict) -> Dict:
        """
        Full opportunity processing pipeline.

        1. Enrich (Access Panel)
        2. Risk check (Access Panel)
        3. Route via AttentionRouter (existing)
        4. Allocate via R3 (existing)
        5. Execute via ExecutionManager (existing)
        """
        self.stats['processed'] += 1
        opp_id = opportunity.get('id', 'unknown')

        # Log discovery
        if self.audit_log:
            self.audit_log.log(
                AuditEventType.DISCOVERED,
                opp_id,
                data={'platform': opportunity.get('platform')},
            )

        # Step 1: Enrich
        if self.enrichment:
            opportunity = self.enrichment.enrich(opportunity)

            if self.audit_log:
                self.audit_log.log(
                    AuditEventType.ENRICHED,
                    opp_id,
                    data={'routing_score': opportunity.get('routing_score')},
                )

        # Step 2: Risk check
        if self.anti_abuse:
            opportunity = self.anti_abuse.enrich(opportunity)

            if opportunity.get('blocked'):
                if self.audit_log:
                    self.audit_log.log(
                        AuditEventType.BLOCKED,
                        opp_id,
                        data={'reason': opportunity.get('blocked_reason')},
                    )
                if self.metrics:
                    self.metrics.record_blocked(opportunity.get('blocked_reason', 'unknown'))
                return opportunity

        # Step 3: Reputation
        if self.reputation_scorer:
            opportunity = self.reputation_scorer.enrich(opportunity)

        # Step 4: Inventory fit
        if self.inventory_scorer:
            opportunity = self.inventory_scorer.enrich(opportunity)

        # Step 5: Route via existing AttentionRouter
        if self.attention_router:
            try:
                # Get Thompson Sampling recommendation
                ts_result = self.attention_router.recommend_action(opportunity)
                opportunity['ts_recommendation'] = ts_result
                self.stats['routed_via_attention'] += 1

                if self.audit_log:
                    self.audit_log.log(
                        AuditEventType.ROUTED,
                        opp_id,
                        data={'method': 'thompson_sampling', 'result': ts_result},
                    )
            except Exception as e:
                logger.warning(f"[adapter] AttentionRouter error: {e}")

        # Step 6: Capital allocation via R3
        if self.r3_allocator:
            try:
                allocation = self.r3_allocator.allocate(opportunity)
                opportunity['capital_allocation'] = allocation
                self.stats['allocated_via_r3'] += 1
            except Exception as e:
                logger.warning(f"[adapter] R3Allocator error: {e}")

        # Step 7: Access Panel routing score
        if self.conversion_router:
            opportunity = self.conversion_router.route(opportunity)

        # Record metrics
        if self.metrics:
            self.metrics.record_routing(
                opportunity.get('routing_tier', 'unknown'),
                opportunity.get('routing_score', 0),
            )

        return opportunity

    async def execute_opportunity(
        self,
        opportunity: Dict,
        dry_run: bool = False
    ) -> Dict:
        """
        Execute opportunity through existing ExecutionManager.
        """
        opp_id = opportunity.get('id', 'unknown')

        if self.audit_log:
            self.audit_log.log(
                AuditEventType.EXECUTION_STARTED,
                opp_id,
                data={'dry_run': dry_run},
            )

        if not self.execution_manager:
            logger.warning("[adapter] ExecutionManager not available")
            return {'success': False, 'error': 'ExecutionManager not available'}

        try:
            # Execute via existing manager
            result = await self.execution_manager.execute(
                opportunity=opportunity,
                dry_run=dry_run,
            )

            self.stats['executed_via_manager'] += 1

            if result.get('success'):
                if self.audit_log:
                    self.audit_log.log(
                        AuditEventType.EXECUTION_COMPLETED,
                        opp_id,
                        data={'execution_id': result.get('execution_id')},
                    )
                if self.metrics:
                    self.metrics.record_execution(
                        True,
                        result.get('duration', 0),
                        opportunity.get('platform', ''),
                    )
            else:
                if self.audit_log:
                    self.audit_log.log(
                        AuditEventType.EXECUTION_FAILED,
                        opp_id,
                        data={'error': result.get('error')},
                    )
                if self.metrics:
                    self.metrics.record_execution(
                        False,
                        result.get('duration', 0),
                        opportunity.get('platform', ''),
                    )

            return result

        except Exception as e:
            logger.error(f"[adapter] Execution error: {e}")
            if self.audit_log:
                self.audit_log.log(
                    AuditEventType.EXECUTION_FAILED,
                    opp_id,
                    data={'error': str(e)},
                )
            return {'success': False, 'error': str(e)}

    async def discover_and_process(
        self,
        platforms: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Discover opportunities and process through full pipeline.
        """
        if not self.discovery_manager:
            logger.warning("[adapter] DiscoveryManager not available")
            return []

        # Discover
        results = await self.discovery_manager.discover_all(platforms=platforms)
        opportunities = results.get('opportunities', [])

        # Process each
        processed = []
        for opp in opportunities:
            processed_opp = await self.process_opportunity(opp)
            processed.append(processed_opp)

        # Sort by routing score
        processed.sort(key=lambda x: x.get('routing_score', 0), reverse=True)

        return processed

    def learn_from_outcome(self, opportunity: Dict, outcome: str):
        """
        Feed outcome back to learning systems.

        Args:
            opportunity: The opportunity that was executed
            outcome: 'won', 'lost', 'expired'
        """
        opp_id = opportunity.get('id', 'unknown')

        # Log outcome
        if self.audit_log:
            event_type = {
                'won': AuditEventType.WON,
                'lost': AuditEventType.LOST,
                'expired': AuditEventType.EXPIRED,
            }.get(outcome, AuditEventType.LOST)

            self.audit_log.log(event_type, opp_id, data={'outcome': outcome})

        # Update AttentionRouter
        if self.attention_router:
            try:
                reward = 1.0 if outcome == 'won' else 0.0
                self.attention_router.update(opportunity, reward)
            except Exception as e:
                logger.warning(f"[adapter] AttentionRouter update error: {e}")

        # Update MetaHive
        if self.metahive:
            try:
                self.metahive.record_outcome(opportunity, outcome)
            except Exception as e:
                logger.warning(f"[adapter] MetaHive update error: {e}")

        # Update reputation
        if self.reputation_scorer:
            try:
                poster_id = self.reputation_scorer._get_poster_id(opportunity)
                if poster_id:
                    self.reputation_scorer.update_profile(poster_id, outcome)
            except Exception as e:
                logger.warning(f"[adapter] Reputation update error: {e}")

    def get_system_status(self) -> Dict:
        """Get status of all integrated systems"""
        return {
            'systems_available': SYSTEMS_AVAILABLE,
            'access_panel_available': ACCESS_PANEL_AVAILABLE,
            'stats': self.stats,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    def get_stats(self) -> Dict:
        """Get adapter stats"""
        stats = {**self.stats}

        if self.metrics:
            stats['metrics'] = self.metrics.get_summary()

        if self.audit_log:
            stats['audit'] = self.audit_log.get_stats()

        return stats


# Singleton
_adapter: Optional[AccessPanelAdapter] = None


def get_access_panel_adapter() -> AccessPanelAdapter:
    """Get or create adapter instance"""
    global _adapter
    if _adapter is None:
        _adapter = AccessPanelAdapter()
    return _adapter
