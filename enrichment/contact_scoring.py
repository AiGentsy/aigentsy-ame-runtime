"""
CONTACT SCORING: Assess Opportunity Contactability

Scores opportunities based on:
- Email presence and validity
- Phone presence
- Platform messaging capability
- Direct contact availability
- Response likelihood signals
"""

import re
import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Email patterns
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE
)

# Phone patterns (international)
PHONE_PATTERNS = [
    re.compile(r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'),  # US
    re.compile(r'\+?[0-9]{1,3}[-.\s]?[0-9]{2,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}'),  # International
]

# Platform messaging capabilities
PLATFORM_MESSAGING: Dict[str, float] = {
    'upwork': 0.9,       # Built-in messaging
    'freelancer': 0.85,  # Built-in messaging
    'fiverr': 0.85,      # Built-in messaging
    'toptal': 0.9,       # Direct contact
    'linkedin': 0.7,     # InMail (paid)
    'twitter': 0.6,      # DMs if open
    'reddit': 0.5,       # PMs available
    'hackernews': 0.3,   # No direct messaging
    'github': 0.6,       # Profile email often available
    'producthunt': 0.5,  # Limited messaging
    'crunchbase': 0.4,   # Mostly read-only
    'angellist': 0.8,    # Good for startups
}

# Contact signals in text
CONTACT_SIGNALS = {
    'positive': [
        'contact me', 'reach out', 'email me', 'dm me', 'message me',
        'send me', 'get in touch', 'reach me at', 'contact:',
        'apply at', 'apply to', 'send your', 'submit your',
        'interested? email', 'interested? contact',
    ],
    'negative': [
        'do not contact', 'no recruiters', 'no agencies',
        'closed', 'filled', 'no longer accepting',
    ],
}


@dataclass
class ContactInfo:
    """Extracted contact information"""
    emails: List[str]
    phones: List[str]
    has_platform_messaging: bool
    contact_signals: List[str]
    negative_signals: List[str]


class ContactScorer:
    """
    Score opportunities by contactability.

    Factors:
    - Direct contact info (email, phone)
    - Platform messaging capability
    - Contact invitation signals
    - Negative signals (closed, no recruiters)
    """

    def __init__(self):
        self.stats = {
            'scored': 0,
            'has_email': 0,
            'has_phone': 0,
            'has_signals': 0,
        }

    def extract_contact_info(self, opportunity: Dict) -> ContactInfo:
        """Extract all contact information from opportunity"""
        title = opportunity.get('title', '')
        body = opportunity.get('body', '') or opportunity.get('description', '')
        text = f"{title} {body}".lower()

        # Extract emails
        emails = list(set(EMAIL_PATTERN.findall(text)))
        # Filter out obvious non-personal emails
        emails = [e for e in emails if not any(
            x in e.lower() for x in ['noreply', 'no-reply', 'donotreply', 'example.com']
        )]

        # Extract phones
        phones = []
        for pattern in PHONE_PATTERNS:
            phones.extend(pattern.findall(text))
        phones = list(set(phones))

        # Check platform messaging
        platform = opportunity.get('platform', '').lower()
        has_platform_messaging = PLATFORM_MESSAGING.get(platform, 0.3) >= 0.6

        # Find contact signals
        contact_signals = [
            signal for signal in CONTACT_SIGNALS['positive']
            if signal in text
        ]

        # Find negative signals
        negative_signals = [
            signal for signal in CONTACT_SIGNALS['negative']
            if signal in text
        ]

        return ContactInfo(
            emails=emails,
            phones=phones,
            has_platform_messaging=has_platform_messaging,
            contact_signals=contact_signals,
            negative_signals=negative_signals,
        )

    def score(self, opportunity: Dict) -> Tuple[float, Dict]:
        """
        Score opportunity contactability.

        Returns:
            Tuple of (score 0-1, metadata dict)
        """
        self.stats['scored'] += 1

        contact_info = self.extract_contact_info(opportunity)
        platform = opportunity.get('platform', '').lower()

        score = 0.0
        reasons = []

        # Email presence (highest value)
        if contact_info.emails:
            score += 0.4
            reasons.append('has_email')
            self.stats['has_email'] += 1

        # Phone presence
        if contact_info.phones:
            score += 0.2
            reasons.append('has_phone')
            self.stats['has_phone'] += 1

        # Platform messaging capability
        platform_score = PLATFORM_MESSAGING.get(platform, 0.3)
        score += platform_score * 0.25
        if platform_score >= 0.7:
            reasons.append('good_platform_messaging')

        # Contact invitation signals
        if contact_info.contact_signals:
            score += 0.15
            reasons.append('contact_invitation')
            self.stats['has_signals'] += 1

        # Negative signal penalty
        if contact_info.negative_signals:
            score -= 0.3
            reasons.append('negative_signals')

        # Cap score
        score = max(0.0, min(1.0, score))

        metadata = {
            'emails': contact_info.emails,
            'phones': contact_info.phones,
            'platform_messaging_score': platform_score,
            'contact_signals': contact_info.contact_signals,
            'negative_signals': contact_info.negative_signals,
            'reasons': reasons,
        }

        return score, metadata

    def enrich(self, opportunity: Dict) -> Dict:
        """Enrich opportunity with contact score"""
        score, metadata = self.score(opportunity)

        # Add to enrichment data
        if 'enrichment' not in opportunity:
            opportunity['enrichment'] = {}

        opportunity['enrichment']['contact_score'] = score
        opportunity['enrichment']['contact_metadata'] = metadata
        opportunity['contactability'] = score  # Legacy field

        # Extract primary contact if available
        if metadata['emails']:
            if 'contact' not in opportunity:
                opportunity['contact'] = {}
            opportunity['contact']['email'] = metadata['emails'][0]

        if metadata['phones']:
            if 'contact' not in opportunity:
                opportunity['contact'] = {}
            opportunity['contact']['phone'] = metadata['phones'][0]

        return opportunity

    def get_stats(self) -> Dict:
        """Get scoring stats"""
        return self.stats.copy()


# Singleton
_contact_scorer: Optional[ContactScorer] = None


def get_contact_scorer() -> ContactScorer:
    """Get or create contact scorer instance"""
    global _contact_scorer
    if _contact_scorer is None:
        _contact_scorer = ContactScorer()
    return _contact_scorer
