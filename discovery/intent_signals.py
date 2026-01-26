"""
INTENT SIGNALS: Payment Proximity & Contactability Scoring

Score buyer intent with focus on:
- Payment proximity (how close to paying)
- Contactability (can we reach them)
- Urgency signals
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class IntentScorer:
    """
    Score buyer intent with focus on payment proximity.

    High-intent keywords indicate ready-to-pay buyers.
    Contactability signals indicate reachability.
    """

    def __init__(self):
        # High-intent keywords (indicate ready to pay)
        self.high_intent_keywords = [
            # Budget signals
            'budget', 'paid', 'pay', 'payment', 'compensation', 'salary', 'rate',
            'hourly', 'fixed price', 'per hour', 'per project', 'retainer',

            # Urgency signals
            'asap', 'urgent', 'immediately', 'today', 'this week', 'deadline',
            'rush', 'fast turnaround', 'quick', 'time sensitive',

            # Hiring signals
            'hire', 'hiring', 'looking for', 'need', 'seeking', 'want to hire',
            'recruiting', 'job', 'position', 'role', 'opening',

            # Contract signals
            'contract', 'project', 'gig', 'freelance', 'contractor', 'consultant',
            'quote', 'rfp', 'proposal', 'bid', 'estimate',

            # Action signals
            'start', 'begin', 'launch', 'kick off', 'ready to start',
        ]

        # Contact signals (indicate reachability)
        self.contact_signals = [
            'email', 'dm', 'message', 'contact', 'reach out', 'apply',
            'send', 'reply', 'respond', 'get in touch', 'inbox',
            '@', 'gmail', 'outlook', 'proton',
        ]

        # Negative signals (reduce intent)
        self.negative_signals = [
            'volunteer', 'unpaid', 'free', 'exposure', 'portfolio',
            'rev share', 'equity only', 'no budget', 'pro bono',
            'learning', 'hobby', 'side project', 'just exploring',
        ]

        # Platform-specific base scores
        self.platform_base_scores = {
            'upwork': {'payment_proximity': 0.8, 'contactability': 0.9},
            'fiverr': {'payment_proximity': 0.7, 'contactability': 0.8},
            'freelancer': {'payment_proximity': 0.75, 'contactability': 0.9},
            'reddit': {'payment_proximity': 0.4, 'contactability': 0.6},
            'hackernews': {'payment_proximity': 0.3, 'contactability': 0.4},
            'craigslist': {'payment_proximity': 0.6, 'contactability': 0.95},
            'linkedin': {'payment_proximity': 0.5, 'contactability': 0.7},
            'twitter': {'payment_proximity': 0.3, 'contactability': 0.5},
            'producthunt': {'payment_proximity': 0.4, 'contactability': 0.5},
            'indiehackers': {'payment_proximity': 0.5, 'contactability': 0.6},
            'remoteok': {'payment_proximity': 0.6, 'contactability': 0.7},
        }

    def _count_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """Count how many keywords match in text"""
        text_lower = text.lower()
        count = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                count += 1
        return count

    def _has_email(self, text: str) -> bool:
        """Check if text contains an email address"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return bool(re.search(email_pattern, text))

    def _has_budget_amount(self, text: str) -> Optional[float]:
        """Extract budget amount from text"""
        # Match patterns like $500, $1,000, $50k, etc.
        patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $1,000.00
            r'\$(\d+)k',  # $50k
            r'(\d+)\s*(?:dollars|usd|USD)',  # 500 dollars
            r'budget[:\s]+\$?(\d+)',  # budget: 500
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                if 'k' in text[match.end()-2:match.end()].lower():
                    return float(value) * 1000
                return float(value)

        return None

    def _has_org_domain(self, text: str) -> bool:
        """Check if text mentions an organizational domain"""
        # Look for company websites
        org_pattern = r'\b[a-zA-Z0-9-]+\.(com|io|co|net|org|tech|dev|app)\b'
        return bool(re.search(org_pattern, text))

    def enrich_intent(self, opp: Dict) -> Dict:
        """
        Add intent signals to opportunity.

        Adds:
        - payment_proximity: 0-1 score (how close to paying)
        - contactability: 0-1 score (how reachable)
        - urgency: low/medium/high
        - has_budget: bool
        - budget_amount: float (if detected)
        """
        # Get text for analysis
        title = opp.get('title_en') or opp.get('title', '') or ''
        body = opp.get('body_en') or opp.get('body', '') or opp.get('description', '') or ''
        text = f"{title} {body}".lower()

        platform = (opp.get('platform', '') or '').lower()

        # Get platform base scores
        base = self.platform_base_scores.get(platform, {
            'payment_proximity': 0.4,
            'contactability': 0.5
        })

        # Calculate payment proximity
        intent_matches = self._count_keyword_matches(text, self.high_intent_keywords)
        negative_matches = self._count_keyword_matches(text, self.negative_signals)

        intent_boost = min(0.4, intent_matches * 0.05)  # Max 0.4 boost
        negative_penalty = min(0.3, negative_matches * 0.1)  # Max 0.3 penalty

        # Budget detection boosts payment proximity
        budget = self._has_budget_amount(text)
        budget_boost = 0.2 if budget else 0

        payment_proximity = max(0.1, min(1.0,
            base['payment_proximity'] + intent_boost + budget_boost - negative_penalty
        ))

        # Calculate contactability
        contact_matches = self._count_keyword_matches(text, self.contact_signals)
        contact_boost = min(0.3, contact_matches * 0.1)

        has_email = self._has_email(text)
        email_boost = 0.2 if has_email else 0

        has_profile = opp.get('author_url') or opp.get('author_profile')
        profile_boost = 0.1 if has_profile else 0

        has_org = self._has_org_domain(text)
        org_boost = 0.15 if has_org else 0

        contactability = max(0.1, min(1.0,
            base['contactability'] + contact_boost + email_boost + profile_boost + org_boost
        ))

        # Determine urgency
        urgency_keywords = ['asap', 'urgent', 'immediately', 'today', 'rush', 'deadline']
        urgency_count = self._count_keyword_matches(text, urgency_keywords)
        if urgency_count >= 2:
            urgency = 'high'
        elif urgency_count == 1:
            urgency = 'medium'
        else:
            urgency = 'low'

        # Update opportunity
        opp['payment_proximity'] = round(payment_proximity, 3)
        opp['contactability'] = round(contactability, 3)
        opp['urgency'] = urgency
        opp['has_budget'] = budget is not None
        if budget:
            opp['budget_amount'] = budget

        return opp

    def enrich_batch(self, opportunities: list) -> list:
        """Enrich intent for batch of opportunities"""
        return [self.enrich_intent(opp) for opp in opportunities]

    def should_fast_path(self, opp: Dict) -> bool:
        """
        Check if opportunity qualifies for fast-path execution.

        Fast-path: High intent + High contactability + Low risk
        """
        return (
            opp.get('payment_proximity', 0) >= 0.7 and
            opp.get('contactability', 0) >= 0.6 and
            opp.get('risk_score', 0) < 0.5
        )


# Singleton instance
_intent_scorer: Optional[IntentScorer] = None


def get_intent_scorer() -> IntentScorer:
    """Get or create intent scorer instance"""
    global _intent_scorer
    if _intent_scorer is None:
        _intent_scorer = IntentScorer()
    return _intent_scorer
