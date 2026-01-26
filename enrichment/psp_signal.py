"""
PSP SIGNAL DETECTION: Payment Proximity Scoring

Detect signals indicating how close an opportunity is to payment:
- Escrow mentions
- Payment processor mentions
- Budget confirmation signals
- Milestone/payment terms
- Platform escrow systems
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Payment processors and terms
PSP_SIGNALS = {
    # High confidence - escrow/milestone
    'escrow': ['escrow', 'milestone payment', 'milestone-based', 'payment milestones'],

    # Payment processors
    'processors': [
        'paypal', 'stripe', 'wise', 'transferwise', 'payoneer',
        'venmo', 'zelle', 'cashapp', 'square', 'braintree',
        'quickbooks', 'freshbooks', 'invoice',
    ],

    # Budget confirmation
    'budget': [
        'budget:', 'budget is', 'our budget', 'allocated budget',
        'pay rate', 'hourly rate', 'fixed price', 'per hour',
        'monthly rate', 'annual salary', 'compensation:',
        '$', 'usd', 'eur', 'gbp',
    ],

    # Payment terms
    'terms': [
        'net 30', 'net 15', 'upon completion', 'weekly payment',
        'bi-weekly', 'monthly payment', 'payment terms',
        'invoice on', '50% upfront', '50% deposit',
    ],

    # Contract signals
    'contract': [
        'contract ready', 'agreement ready', 'nda required',
        'sign contract', 'contract terms', 'sow ready',
        'statement of work',
    ],
}

# Platform escrow capabilities
PLATFORM_ESCROW: Dict[str, float] = {
    'upwork': 0.95,       # Built-in escrow
    'freelancer': 0.90,   # Milestone payments
    'fiverr': 0.90,       # Upfront payment
    'toptal': 0.85,       # Reliable payments
    '99designs': 0.85,    # Contest escrow
    'guru': 0.80,         # SafePay
    'peopleperhour': 0.80,
    'flexjobs': 0.70,
    'weworkremotely': 0.60,
    'remoteok': 0.60,
    'linkedin': 0.50,     # No payment system
    'angellist': 0.50,
    'indeed': 0.50,
    'hackernews': 0.30,   # No verification
    'reddit': 0.20,       # High risk
    'twitter': 0.20,
    'craigslist': 0.15,   # High risk
}

# Budget extraction patterns
BUDGET_PATTERNS = [
    # USD patterns
    re.compile(r'\$[\d,]+(?:\.\d{2})?(?:\s*[-/]\s*\$?[\d,]+(?:\.\d{2})?)?(?:\s*(?:per|/)\s*(?:hour|hr|h|month|mo|week|wk|year|yr))?', re.I),
    # Written amounts
    re.compile(r'(?:budget|pay|rate|salary|compensation)[:\s]+\$?[\d,]+(?:\.\d{2})?', re.I),
    # Range patterns
    re.compile(r'[\d,]+\s*[-–]\s*[\d,]+\s*(?:usd|eur|gbp|per\s+hour|/hr|/h)', re.I),
]


@dataclass
class PSPInfo:
    """Extracted PSP/payment information"""
    escrow_signals: List[str]
    processor_signals: List[str]
    budget_signals: List[str]
    term_signals: List[str]
    contract_signals: List[str]
    extracted_amounts: List[str]
    platform_escrow_score: float


class PSPDetector:
    """
    Detect Payment Service Provider signals.

    Factors:
    - Escrow/milestone mentions
    - Payment processor mentions
    - Budget confirmation
    - Payment terms
    - Platform escrow capability
    """

    def __init__(self):
        self.stats = {
            'scored': 0,
            'has_escrow': 0,
            'has_budget': 0,
            'has_processor': 0,
        }

    def extract_psp_info(self, opportunity: Dict) -> PSPInfo:
        """Extract all PSP-related information"""
        title = opportunity.get('title', '')
        body = opportunity.get('body', '') or opportunity.get('description', '')
        text = f"{title} {body}".lower()

        # Find signals in each category
        escrow_signals = [s for s in PSP_SIGNALS['escrow'] if s in text]
        processor_signals = [s for s in PSP_SIGNALS['processors'] if s in text]
        budget_signals = [s for s in PSP_SIGNALS['budget'] if s in text]
        term_signals = [s for s in PSP_SIGNALS['terms'] if s in text]
        contract_signals = [s for s in PSP_SIGNALS['contract'] if s in text]

        # Extract budget amounts
        extracted_amounts = []
        for pattern in BUDGET_PATTERNS:
            matches = pattern.findall(f"{title} {body}")  # Use original case
            extracted_amounts.extend(matches)
        extracted_amounts = list(set(extracted_amounts))[:5]  # Limit to 5

        # Get platform escrow score
        platform = opportunity.get('platform', '').lower()
        platform_escrow_score = PLATFORM_ESCROW.get(platform, 0.3)

        return PSPInfo(
            escrow_signals=escrow_signals,
            processor_signals=processor_signals,
            budget_signals=budget_signals,
            term_signals=term_signals,
            contract_signals=contract_signals,
            extracted_amounts=extracted_amounts,
            platform_escrow_score=platform_escrow_score,
        )

    def score(self, opportunity: Dict) -> Tuple[float, Dict]:
        """
        Score payment proximity.

        Returns:
            Tuple of (score 0-1, metadata dict)
        """
        self.stats['scored'] += 1

        psp_info = self.extract_psp_info(opportunity)

        score = 0.0
        reasons = []

        # Platform escrow (baseline)
        score += psp_info.platform_escrow_score * 0.3
        if psp_info.platform_escrow_score >= 0.8:
            reasons.append('platform_escrow')

        # Escrow/milestone signals (highest value)
        if psp_info.escrow_signals:
            score += 0.25
            reasons.append('escrow_mentioned')
            self.stats['has_escrow'] += 1

        # Budget confirmation
        if psp_info.budget_signals or psp_info.extracted_amounts:
            score += 0.2
            reasons.append('budget_confirmed')
            self.stats['has_budget'] += 1

        # Payment processor mentions
        if psp_info.processor_signals:
            score += 0.1
            reasons.append('processor_mentioned')
            self.stats['has_processor'] += 1

        # Payment terms
        if psp_info.term_signals:
            score += 0.1
            reasons.append('terms_specified')

        # Contract ready signals
        if psp_info.contract_signals:
            score += 0.1
            reasons.append('contract_ready')

        # Cap score
        score = max(0.0, min(1.0, score))

        metadata = {
            'escrow_signals': psp_info.escrow_signals,
            'processor_signals': psp_info.processor_signals,
            'budget_signals': psp_info.budget_signals,
            'term_signals': psp_info.term_signals,
            'contract_signals': psp_info.contract_signals,
            'extracted_amounts': psp_info.extracted_amounts,
            'platform_escrow_score': psp_info.platform_escrow_score,
            'reasons': reasons,
        }

        return score, metadata

    def extract_budget(self, opportunity: Dict) -> Optional[float]:
        """Extract budget amount from opportunity"""
        psp_info = self.extract_psp_info(opportunity)

        if not psp_info.extracted_amounts:
            return None

        # Try to parse the first amount
        for amount_str in psp_info.extracted_amounts:
            try:
                # Clean the string
                cleaned = re.sub(r'[^\d.]', '', amount_str.split('-')[0].split('/')[0])
                if cleaned:
                    return float(cleaned)
            except:
                continue

        return None

    def enrich(self, opportunity: Dict) -> Dict:
        """Enrich opportunity with PSP score"""
        score, metadata = self.score(opportunity)

        # Add to enrichment data
        if 'enrichment' not in opportunity:
            opportunity['enrichment'] = {}

        opportunity['enrichment']['payment_proximity'] = score
        opportunity['enrichment']['psp_metadata'] = metadata
        opportunity['payment_proximity'] = score  # Legacy field

        # Extract budget if available
        budget = self.extract_budget(opportunity)
        if budget:
            opportunity['enrichment']['budget_extracted'] = budget
            if 'pricing' not in opportunity:
                opportunity['pricing'] = {}
            opportunity['pricing']['estimated_value'] = budget
            opportunity['value'] = budget  # Legacy field

        return opportunity

    def get_stats(self) -> Dict:
        """Get scoring stats"""
        return self.stats.copy()


# Singleton
_psp_detector: Optional[PSPDetector] = None


def get_psp_detector() -> PSPDetector:
    """Get or create PSP detector instance"""
    global _psp_detector
    if _psp_detector is None:
        _psp_detector = PSPDetector()
    return _psp_detector
