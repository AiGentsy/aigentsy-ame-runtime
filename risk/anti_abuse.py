"""
ANTI-ABUSE: Scam and Fraud Detection

Features:
- Pattern-based scam detection
- Red flag identification
- Risk scoring
- Blocking recommendations
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Scam indicators
SCAM_PATTERNS = {
    # Financial red flags
    'advance_payment': [
        r'pay\s*(?:fee|upfront|in\s*advance)',
        r'registration\s*fee',
        r'send\s*(?:money|payment|deposit)',
        r'western\s*union',
        r'money\s*gram',
        r'wire\s*transfer\s*(?:first|upfront)',
        r'crypto\s*(?:payment|deposit)',
    ],

    # Too good to be true
    'unrealistic': [
        r'earn\s*\$?\d+[kK]?\s*(?:per|a|each)\s*(?:day|hour|week)',
        r'guaranteed\s*(?:income|earnings|pay)',
        r'easy\s*money',
        r'work\s*from\s*(?:home|anywhere)\s*\$?\d+[kK]',
        r'no\s*experience\s*(?:needed|required).*\$?\d+',
        r'instant\s*(?:pay|cash|money)',
    ],

    # Urgency tactics
    'urgency': [
        r'act\s*(?:now|fast|immediately)',
        r'limited\s*(?:time|spots|positions)',
        r'(?:must|need\s*to)\s*apply\s*today',
        r'don\'?t\s*miss\s*(?:out|this)',
        r'last\s*chance',
    ],

    # Personal info requests
    'info_harvesting': [
        r'send\s*(?:your|us\s*your)\s*(?:id|passport|ssn|social)',
        r'bank\s*(?:details|account|info)',
        r'credit\s*card\s*(?:number|details|info)',
        r'full\s*(?:address|details)\s*(?:required|needed)',
    ],

    # MLM/Pyramid
    'mlm': [
        r'network\s*marketing',
        r'multi.?level',
        r'downline',
        r'recruit\s*(?:others|people|members)',
        r'passive\s*income\s*(?:opportunity|system)',
        r'be\s*your\s*own\s*boss',
    ],

    # Suspicious contact
    'suspicious_contact': [
        r'(?:whatsapp|telegram|signal)\s*(?:only|me)',
        r'text\s*(?:me|us)\s*(?:at|on)',
        r'contact\s*(?:via|through)\s*(?:whatsapp|telegram)',
        r'personal\s*email',
    ],
}

# Trusted platform indicators (reduce risk)
TRUSTED_INDICATORS = [
    'escrow', 'milestone payment', 'payment protection',
    'verified', 'established company', 'funded startup',
]

# Known scam domains
SCAM_DOMAINS = {
    'scam-jobs.com', 'get-rich-quick.net',
    # Add more as discovered
}


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    risk_score: float  # 0-1
    risk_level: str  # low, medium, high, critical
    flags: List[str]
    reasons: List[str]
    should_block: bool


class AntiAbuse:
    """
    Detect scams and fraudulent opportunities.

    Uses pattern matching and heuristics to identify:
    - Advance fee fraud
    - Too-good-to-be-true offers
    - MLM/pyramid schemes
    - Information harvesting
    """

    def __init__(self, config: Optional[Dict] = None):
        config = config or {}

        # Compile patterns
        self.patterns = {}
        for category, patterns in SCAM_PATTERNS.items():
            self.patterns[category] = [
                re.compile(p, re.IGNORECASE)
                for p in patterns
            ]

        # Thresholds
        self.block_threshold = config.get('block_threshold', 0.7)
        self.high_risk_threshold = config.get('high_risk_threshold', 0.5)

        # Stats
        self.stats = {
            'assessed': 0,
            'low_risk': 0,
            'medium_risk': 0,
            'high_risk': 0,
            'blocked': 0,
        }

    def assess(self, opportunity: Dict) -> RiskAssessment:
        """
        Assess opportunity for fraud risk.

        Returns:
            RiskAssessment with score and details
        """
        self.stats['assessed'] += 1

        title = opportunity.get('title', '')
        body = opportunity.get('body', '') or opportunity.get('description', '')
        url = opportunity.get('url', '')
        platform = opportunity.get('platform', '')

        text = f"{title} {body}".lower()
        flags = []
        reasons = []

        # Check each pattern category
        category_scores = {}
        for category, patterns in self.patterns.items():
            matches = []
            for pattern in patterns:
                if pattern.search(text):
                    matches.append(pattern.pattern[:30])

            if matches:
                flags.append(category)
                reasons.extend(matches[:2])  # Limit reasons
                category_scores[category] = min(1.0, len(matches) * 0.3)

        # Check URL/domain
        if url:
            from urllib.parse import urlparse
            try:
                host = urlparse(url).netloc.lower()
                if host in SCAM_DOMAINS:
                    flags.append('known_scam_domain')
                    category_scores['scam_domain'] = 1.0
            except:
                pass

        # Check for trusted indicators (reduce risk)
        trust_score = 0.0
        for indicator in TRUSTED_INDICATORS:
            if indicator in text:
                trust_score += 0.1

        # Platform trust modifier
        platform_trust = self._get_platform_trust(platform)

        # Calculate overall risk score
        if category_scores:
            raw_score = sum(category_scores.values()) / len(category_scores)
        else:
            raw_score = 0.0

        # Apply trust modifiers
        risk_score = raw_score - trust_score - (platform_trust * 0.2)
        risk_score = max(0.0, min(1.0, risk_score))

        # Determine risk level
        if risk_score >= self.block_threshold:
            risk_level = 'critical'
            should_block = True
            self.stats['blocked'] += 1
        elif risk_score >= self.high_risk_threshold:
            risk_level = 'high'
            should_block = False
            self.stats['high_risk'] += 1
        elif risk_score >= 0.3:
            risk_level = 'medium'
            should_block = False
            self.stats['medium_risk'] += 1
        else:
            risk_level = 'low'
            should_block = False
            self.stats['low_risk'] += 1

        return RiskAssessment(
            risk_score=risk_score,
            risk_level=risk_level,
            flags=flags,
            reasons=reasons,
            should_block=should_block,
        )

    def _get_platform_trust(self, platform: str) -> float:
        """Get platform trust score"""
        platform = platform.lower()

        # High trust platforms
        if platform in ['upwork', 'toptal', 'fiverr', 'freelancer']:
            return 0.8
        if platform in ['linkedin', 'indeed', 'glassdoor']:
            return 0.7
        if platform in ['github', 'weworkremotely', 'remoteok']:
            return 0.6
        if platform in ['hackernews', 'producthunt']:
            return 0.5
        if platform in ['reddit', 'twitter']:
            return 0.3
        if platform in ['craigslist']:
            return 0.1

        return 0.3  # Default

    def enrich(self, opportunity: Dict) -> Dict:
        """Enrich opportunity with risk assessment"""
        assessment = self.assess(opportunity)

        if 'enrichment' not in opportunity:
            opportunity['enrichment'] = {}

        opportunity['enrichment']['risk_score'] = assessment.risk_score
        opportunity['enrichment']['risk_level'] = assessment.risk_level
        opportunity['enrichment']['risk_flags'] = assessment.flags
        opportunity['risk_score'] = assessment.risk_score  # Legacy

        if assessment.should_block:
            opportunity['blocked'] = True
            opportunity['blocked_reason'] = f"High fraud risk: {', '.join(assessment.flags)}"

        return opportunity

    def filter_safe(self, opportunities: List[Dict]) -> List[Dict]:
        """Filter out high-risk opportunities"""
        safe = []
        for opp in opportunities:
            assessment = self.assess(opp)
            if not assessment.should_block:
                safe.append(opp)
        return safe

    def get_stats(self) -> Dict:
        """Get anti-abuse stats"""
        return {
            **self.stats,
            'block_rate': self.stats['blocked'] / max(1, self.stats['assessed']),
        }


# Singleton
_anti_abuse: Optional[AntiAbuse] = None


def get_anti_abuse() -> AntiAbuse:
    """Get or create anti-abuse instance"""
    global _anti_abuse
    if _anti_abuse is None:
        _anti_abuse = AntiAbuse()
    return _anti_abuse
