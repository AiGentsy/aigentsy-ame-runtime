"""
CONVERSION ROUTER: Unified Routing with Existing Systems

Integrates with:
- AttentionRouter (Thompson Sampling)
- R3 Allocator (Kelly Criterion)
- Inventory Fit Scorer

Routing weights (from spec):
- payment_proximity: 0.22
- contactability: 0.16
- inventory_fit: 0.10
- poster_reputation: 0.12
- intent_score: 0.15
- urgency_score: 0.10
- risk_penalty: -0.15
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try to import existing routing systems
try:
    from growth.attention_router import get_attention_router
    ATTENTION_ROUTER_AVAILABLE = True
except ImportError:
    ATTENTION_ROUTER_AVAILABLE = False
    logger.warning("AttentionRouter not available")

try:
    from allocation.r3_allocator import get_r3_allocator
    R3_ALLOCATOR_AVAILABLE = True
except ImportError:
    R3_ALLOCATOR_AVAILABLE = False
    logger.warning("R3Allocator not available")

from .inventory_fit import get_inventory_scorer


class ConversionRouter:
    """
    Route opportunities for maximum conversion.

    Combines:
    - Enrichment scores (payment proximity, contactability, etc.)
    - Inventory fit
    - Thompson Sampling from AttentionRouter
    - Capital allocation from R3 Allocator
    """

    # Routing weights from spec
    WEIGHTS = {
        'payment_proximity': 0.22,
        'contactability': 0.16,
        'inventory_fit': 0.10,
        'poster_reputation': 0.12,
        'intent_score': 0.15,
        'urgency_score': 0.10,
        'risk_penalty': -0.15,
    }

    # Thresholds
    FAST_PATH_THRESHOLD = 0.5
    MIN_ROUTING_SCORE = 0.1
    HIGH_PRIORITY_THRESHOLD = 0.7

    def __init__(self, config: Optional[Dict] = None):
        config = config or {}

        self.weights = config.get('weights', self.WEIGHTS)
        self.fast_path_threshold = config.get('fast_path_threshold', self.FAST_PATH_THRESHOLD)
        self.min_routing_score = config.get('min_routing_score', self.MIN_ROUTING_SCORE)

        # Initialize scorers
        self.inventory_scorer = get_inventory_scorer()

        # Get existing routers if available
        self.attention_router = get_attention_router() if ATTENTION_ROUTER_AVAILABLE else None
        self.r3_allocator = get_r3_allocator() if R3_ALLOCATOR_AVAILABLE else None

        # Stats
        self.stats = {
            'routed': 0,
            'fast_path': 0,
            'high_priority': 0,
            'low_priority': 0,
            'rejected': 0,
        }

    def compute_routing_score(self, opportunity: Dict) -> float:
        """Compute weighted routing score"""
        enrichment = opportunity.get('enrichment', {})

        # HARD GATE 1: Capacity check - don't accept what we can't fulfill
        if not self._check_capacity(opportunity):
            logger.debug(f"Hard gate: No capacity for {opportunity.get('id')}")
            return 0.0

        # HARD GATE 2: SLO health check
        slo_health = enrichment.get('slo_health', 1.0)
        if slo_health < 0.6:
            logger.debug(f"Hard gate: SLO unhealthy ({slo_health}) for {opportunity.get('id')}")
            return 0.0

        # HARD GATE 3: Anti-abuse block
        if enrichment.get('risk_block', False):
            logger.debug(f"Hard gate: Risk blocked for {opportunity.get('id')}")
            return 0.0

        # Get individual scores
        payment_proximity = enrichment.get('payment_proximity', 0.0)
        contactability = enrichment.get('contact_score', 0.0)
        inventory_fit = enrichment.get('inventory_fit', 0.0)
        poster_reputation = enrichment.get('poster_reputation', 0.5)
        intent_score = enrichment.get('intent_score', 0.0)
        urgency_score = enrichment.get('urgency_score', 0.0)
        risk_score = enrichment.get('risk_score', 0.0)

        # Compute weighted score
        score = (
            self.weights['payment_proximity'] * payment_proximity +
            self.weights['contactability'] * contactability +
            self.weights['inventory_fit'] * inventory_fit +
            self.weights['poster_reputation'] * poster_reputation +
            self.weights['intent_score'] * intent_score +
            self.weights['urgency_score'] * urgency_score +
            self.weights['risk_penalty'] * risk_score
        )

        # Apply capacity multiplier (prefer opps we can fulfill now)
        capacity_mult = enrichment.get('capacity_multiplier', 1.0)
        score *= capacity_mult

        return max(0.0, min(1.0, score))

    def _check_capacity(self, opportunity: Dict) -> bool:
        """Check if we have capacity to fulfill this opportunity"""
        try:
            from workforce.dispatcher import get_workforce_dispatcher
            dispatcher = get_workforce_dispatcher()
            capacity = dispatcher.get_capacity()

            # Check if at least one tier has availability
            for tier, data in capacity.items():
                if data.get('available', 0) > 0:
                    return True

            return False
        except Exception:
            # If dispatcher not available, assume capacity
            return True

    def route(self, opportunity: Dict) -> Dict:
        """
        Route single opportunity.

        Returns opportunity with routing decision.
        """
        self.stats['routed'] += 1

        # Ensure inventory fit is computed
        if 'inventory_fit' not in opportunity.get('enrichment', {}):
            opportunity = self.inventory_scorer.enrich(opportunity)

        # Compute routing score
        routing_score = self.compute_routing_score(opportunity)
        opportunity['routing_score'] = routing_score

        if 'enrichment' not in opportunity:
            opportunity['enrichment'] = {}
        opportunity['enrichment']['routing_score'] = routing_score

        # Determine routing tier
        if routing_score < self.min_routing_score:
            opportunity['routing_tier'] = 'rejected'
            opportunity['routing_reason'] = 'below_minimum_score'
            self.stats['rejected'] += 1
        elif routing_score >= self.HIGH_PRIORITY_THRESHOLD:
            opportunity['routing_tier'] = 'high_priority'
            self.stats['high_priority'] += 1
        elif routing_score >= self.fast_path_threshold:
            opportunity['routing_tier'] = 'fast_path'
            self.stats['fast_path'] += 1
        else:
            opportunity['routing_tier'] = 'standard'
            self.stats['low_priority'] += 1

        # Check fast-path eligibility
        opportunity['fast_path_eligible'] = self._is_fast_path_eligible(opportunity)

        # Get Thompson Sampling recommendation if available
        if self.attention_router:
            try:
                ts_recommendation = self.attention_router.recommend(opportunity)
                opportunity['ts_recommendation'] = ts_recommendation
            except:
                pass

        # Get capital allocation if available
        if self.r3_allocator:
            try:
                allocation = self.r3_allocator.allocate(opportunity)
                opportunity['capital_allocation'] = allocation
            except:
                pass

        opportunity['routed_at'] = datetime.now(timezone.utc).isoformat()

        return opportunity

    def route_batch(self, opportunities: List[Dict]) -> List[Dict]:
        """Route batch of opportunities"""
        routed = []
        for opp in opportunities:
            routed_opp = self.route(opp)
            routed.append(routed_opp)

        # Sort by routing score
        routed.sort(key=lambda x: x.get('routing_score', 0), reverse=True)

        return routed

    def _is_fast_path_eligible(self, opportunity: Dict) -> bool:
        """Check if opportunity qualifies for fast-path execution"""
        enrichment = opportunity.get('enrichment', {})

        return (
            enrichment.get('payment_proximity', 0) >= 0.7 and
            enrichment.get('contact_score', 0) >= 0.6 and
            enrichment.get('risk_score', 1) <= 0.3 and
            opportunity.get('routing_score', 0) >= self.fast_path_threshold
        )

    def filter_by_tier(
        self,
        opportunities: List[Dict],
        tiers: List[str]
    ) -> List[Dict]:
        """Filter opportunities by routing tier"""
        return [
            opp for opp in opportunities
            if opp.get('routing_tier') in tiers
        ]

    def get_fast_path_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Get fast-path eligible opportunities"""
        return [
            opp for opp in opportunities
            if opp.get('fast_path_eligible')
        ]

    def get_high_priority(self, opportunities: List[Dict]) -> List[Dict]:
        """Get high priority opportunities"""
        return self.filter_by_tier(opportunities, ['high_priority'])

    def get_actionable(self, opportunities: List[Dict]) -> List[Dict]:
        """Get all actionable opportunities (non-rejected)"""
        return [
            opp for opp in opportunities
            if opp.get('routing_tier') != 'rejected'
        ]

    def get_stats(self) -> Dict:
        """Get routing stats"""
        return {
            **self.stats,
            'acceptance_rate': (
                (self.stats['routed'] - self.stats['rejected']) /
                max(1, self.stats['routed'])
            ),
            'fast_path_rate': self.stats['fast_path'] / max(1, self.stats['routed']),
        }


# Singleton
_conversion_router: Optional[ConversionRouter] = None


def get_conversion_router(config: Optional[Dict] = None) -> ConversionRouter:
    """Get or create conversion router instance"""
    global _conversion_router
    if _conversion_router is None:
        _conversion_router = ConversionRouter(config)
    return _conversion_router
