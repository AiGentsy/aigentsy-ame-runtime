"""
ENRICHMENT PIPELINE: Coordinate All Enrichment Steps

Orchestrates:
- Contact scoring
- PSP signal detection
- Intent scoring (from existing)
- Safety filtering (from existing)
- Language detection (from existing)
- Routing score computation
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Local imports
from .contact_scoring import get_contact_scorer
from .psp_signal import get_psp_detector

# Import existing enrichment components
try:
    from discovery.intent_signals import get_intent_scorer
    INTENT_AVAILABLE = True
except ImportError:
    INTENT_AVAILABLE = False
    logger.warning("intent_signals not available")

try:
    from discovery.safety_filter import get_safety_filter
    SAFETY_AVAILABLE = True
except ImportError:
    SAFETY_AVAILABLE = False
    logger.warning("safety_filter not available")

try:
    from discovery.i18n_normalizer import get_i18n_normalizer
    I18N_AVAILABLE = True
except ImportError:
    I18N_AVAILABLE = False
    logger.warning("i18n_normalizer not available")


class EnrichmentPipeline:
    """
    Orchestrate all enrichment steps for opportunities.

    Pipeline stages:
    1. Language detection & normalization
    2. Contact scoring
    3. PSP signal detection
    4. Intent scoring
    5. Safety filtering
    6. Routing score computation
    """

    # Routing weights (from spec)
    ROUTING_WEIGHTS = {
        'payment_proximity': 0.22,
        'contactability': 0.16,
        'inventory_fit': 0.10,
        'poster_reputation': 0.12,
        'intent_score': 0.15,
        'urgency_score': 0.10,
        'risk_penalty': -0.15,
    }

    def __init__(self, config: Optional[Dict] = None):
        config = config or {}

        # Initialize enrichment components
        self.contact_scorer = get_contact_scorer()
        self.psp_detector = get_psp_detector()

        # Existing components
        self.intent_scorer = get_intent_scorer() if INTENT_AVAILABLE else None
        self.safety_filter = get_safety_filter() if SAFETY_AVAILABLE else None
        self.i18n = get_i18n_normalizer() if I18N_AVAILABLE else None

        # Configuration
        self.fast_path_threshold = config.get('fast_path_threshold', 0.5)
        self.min_routing_score = config.get('min_routing_score', 0.1)

        # Stats
        self.stats = {
            'enriched': 0,
            'fast_path_eligible': 0,
            'blocked': 0,
            'total_time_ms': 0,
        }

    def enrich(self, opportunity: Dict) -> Dict:
        """
        Run full enrichment pipeline on opportunity.

        Returns enriched opportunity with all scores.
        """
        start = time.time()
        self.stats['enriched'] += 1

        # Ensure enrichment dict exists
        if 'enrichment' not in opportunity:
            opportunity['enrichment'] = {}

        try:
            # Stage 1: Language detection & normalization
            if self.i18n:
                opportunity = self.i18n.normalize_language(opportunity)

            # Stage 2: Contact scoring
            opportunity = self.contact_scorer.enrich(opportunity)

            # Stage 3: PSP signal detection
            opportunity = self.psp_detector.enrich(opportunity)

            # Stage 4: Intent scoring
            if self.intent_scorer:
                opportunity = self.intent_scorer.enrich_intent(opportunity)

            # Stage 5: Safety filtering
            if self.safety_filter:
                opportunity = self.safety_filter.risk_screen(opportunity)

            # Stage 6: Compute routing score
            opportunity = self._compute_routing_score(opportunity)

            # Stage 7: Check fast-path eligibility
            opportunity = self._check_fast_path(opportunity)

            # Mark as enriched
            opportunity['enrichment']['enriched_at'] = datetime.now(timezone.utc).isoformat()
            opportunity['status'] = 'enriched'

        except Exception as e:
            logger.error(f"[enrichment_pipeline] Error enriching opportunity: {e}")
            opportunity['enrichment']['error'] = str(e)

        elapsed_ms = (time.time() - start) * 1000
        self.stats['total_time_ms'] += elapsed_ms

        return opportunity

    def enrich_batch(self, opportunities: List[Dict]) -> List[Dict]:
        """Enrich batch of opportunities"""
        return [self.enrich(opp) for opp in opportunities]

    def _compute_routing_score(self, opportunity: Dict) -> Dict:
        """Compute weighted routing score"""
        enrichment = opportunity.get('enrichment', {})

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
            self.ROUTING_WEIGHTS['payment_proximity'] * payment_proximity +
            self.ROUTING_WEIGHTS['contactability'] * contactability +
            self.ROUTING_WEIGHTS['inventory_fit'] * inventory_fit +
            self.ROUTING_WEIGHTS['poster_reputation'] * poster_reputation +
            self.ROUTING_WEIGHTS['intent_score'] * intent_score +
            self.ROUTING_WEIGHTS['urgency_score'] * urgency_score +
            self.ROUTING_WEIGHTS['risk_penalty'] * risk_score
        )

        # Normalize to 0-1
        score = max(0.0, min(1.0, score))

        opportunity['routing_score'] = score
        opportunity['enrichment']['routing_score'] = score

        return opportunity

    def _check_fast_path(self, opportunity: Dict) -> Dict:
        """Check if opportunity qualifies for fast-path execution"""
        enrichment = opportunity.get('enrichment', {})

        # Fast-path criteria
        fast_path_eligible = (
            enrichment.get('payment_proximity', 0) >= 0.7 and
            enrichment.get('contact_score', 0) >= 0.6 and
            enrichment.get('risk_score', 1) <= 0.3 and
            opportunity.get('routing_score', 0) >= self.fast_path_threshold
        )

        if fast_path_eligible:
            self.stats['fast_path_eligible'] += 1

        opportunity['fast_path_eligible'] = fast_path_eligible
        opportunity['enrichment']['fast_path_eligible'] = fast_path_eligible

        return opportunity

    def filter_by_quality(
        self,
        opportunities: List[Dict],
        min_score: Optional[float] = None
    ) -> List[Dict]:
        """Filter opportunities by minimum routing score"""
        min_score = min_score or self.min_routing_score

        filtered = [
            opp for opp in opportunities
            if opp.get('routing_score', 0) >= min_score
        ]

        logger.info(
            f"[enrichment_pipeline] Filtered {len(opportunities)} -> {len(filtered)} "
            f"(min_score={min_score})"
        )

        return filtered

    def sort_by_routing_score(self, opportunities: List[Dict]) -> List[Dict]:
        """Sort opportunities by routing score (descending)"""
        return sorted(
            opportunities,
            key=lambda x: x.get('routing_score', 0),
            reverse=True
        )

    def get_fast_path_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Get only fast-path eligible opportunities"""
        return [opp for opp in opportunities if opp.get('fast_path_eligible')]

    def get_stats(self) -> Dict:
        """Get pipeline stats"""
        avg_time = (
            self.stats['total_time_ms'] / max(1, self.stats['enriched'])
        )

        return {
            **self.stats,
            'avg_time_ms': avg_time,
            'contact_scorer': self.contact_scorer.get_stats(),
            'psp_detector': self.psp_detector.get_stats(),
        }


# Singleton
_enrichment_pipeline: Optional[EnrichmentPipeline] = None


def get_enrichment_pipeline(config: Optional[Dict] = None) -> EnrichmentPipeline:
    """Get or create enrichment pipeline instance"""
    global _enrichment_pipeline
    if _enrichment_pipeline is None:
        _enrichment_pipeline = EnrichmentPipeline(config)
    return _enrichment_pipeline
