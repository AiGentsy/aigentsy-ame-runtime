"""
SAFETY FILTER: Scam/Abuse Detection & Risk Screening

Filter out:
- Scams and fraudulent opportunities
- High-risk/abusive postings
- Low-quality "free work" requests
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SafetyFilter:
    """
    Filter scams, abuse, and high-risk opportunities.

    Risk scoring based on:
    - Scam indicators
    - Low-quality signals
    - Suspicious patterns
    - Missing organizational presence
    """

    def __init__(self):
        # High-risk scam indicators
        self.scam_indicators = [
            # Payment method red flags
            'telegram only', 'whatsapp only', 'crypto payment only',
            'upfront payment', 'advance payment', 'pay before',
            'wire transfer', 'western union', 'moneygram',
            'no escrow', 'off platform', 'direct payment',
            'bitcoin only', 'crypto only', 'usdt only',

            # Advance fee scams
            'training fee', 'registration fee', 'equipment fee',
            'background check fee', 'certification fee',

            # Too good to be true
            'guaranteed income', 'guaranteed earnings', 'easy money',
            'make money fast', 'get rich', 'passive income',
            'no experience needed', 'no skills required',

            # Personal info fishing
            'send your id', 'scan of passport', 'social security',
            'bank account details', 'credit card number',

            # Suspicious urgency
            'act now', 'limited time', 'only 3 spots', 'expires today',
        ]

        # Low quality signals (not scams, but bad opportunities)
        self.low_quality_signals = [
            # No pay
            'work for exposure', 'no budget', 'rev share only',
            'equity only', 'profit share only', 'free work',
            'volunteer', 'unpaid', 'for portfolio', 'for experience',
            'pro bono', 'internship unpaid', 'unpaid internship',

            # Vague/unrealistic
            'easy task', 'quick task', 'simple project',
            'build me an app like uber', 'next facebook',
            'revolutionary idea', 'million dollar idea',

            # Exploitative
            'unlimited revisions', 'changes until satisfied',
            'quick test project', 'trial project',
        ]

        # Suspicious budget patterns
        self.suspicious_budgets = {
            'too_low': 10,  # Less than $10 for any real work
            'too_high': 100000,  # Unrealistic single gig
        }

        # Platform-specific risk adjustments
        self.platform_risk = {
            'upwork': -0.2,  # Lower risk (verified)
            'fiverr': -0.1,
            'toptal': -0.3,  # Very low risk (vetted)
            'craigslist': 0.2,  # Higher risk
            'telegram': 0.4,  # High risk
            'whatsapp': 0.3,
            'reddit': 0.1,
        }

    def _count_indicator_matches(self, text: str, indicators: List[str]) -> int:
        """Count matching indicators"""
        text_lower = text.lower()
        return sum(1 for ind in indicators if ind.lower() in text_lower)

    def _has_suspicious_budget(self, opp: Dict) -> bool:
        """Check for suspicious budget patterns"""
        budget = opp.get('value', 0) or opp.get('budget', 0) or 0

        # No budget specified - neutral
        if budget == 0:
            return False

        # Too low for scope
        body = opp.get('body', '') or opp.get('description', '') or ''
        if budget < self.suspicious_budgets['too_low']:
            return True

        # Unrealistically high
        if budget > self.suspicious_budgets['too_high']:
            return True

        # Low budget with high scope (long description = complex project)
        if budget < 50 and len(body) > 500:
            return True

        return False

    def _has_org_presence(self, opp: Dict) -> bool:
        """Check for organizational presence (reduces risk)"""
        # Check metadata
        metadata = opp.get('metadata', {}) or {}
        if metadata.get('company_name') or metadata.get('website'):
            return True

        if metadata.get('verified', False):
            return True

        # Check for company indicators in text
        text = f"{opp.get('title', '')} {opp.get('body', '')}"
        company_patterns = [
            r'\b(?:inc|llc|ltd|corp|company|team|startup)\b',
            r'\bwe are\b',
            r'\bout team\b',
            r'\bour company\b',
        ]
        for pattern in company_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        # Check for LinkedIn/website
        url = opp.get('author_url', '') or ''
        if 'linkedin.com' in url or '.com' in url:
            return True

        return False

    def _has_contact_red_flags(self, text: str) -> bool:
        """Check for suspicious contact patterns"""
        red_flags = [
            r'telegram\s*:?\s*@',  # Telegram-only contact
            r'whatsapp\s*:?\s*\+',  # WhatsApp-only contact
            r'signal\s*:?\s*@',  # Signal-only (sometimes ok, but unusual for work)
            r'contact\s+off\s+platform',
            r'email\s+me\s+directly',  # Bypassing platform
        ]

        for pattern in red_flags:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def risk_screen(self, opp: Dict) -> Dict:
        """
        Add risk score to opportunity.

        Adds:
        - risk_score: 0-1 (higher = riskier)
        - risk_flag: none/low/medium/high
        - risk_reasons: list of reasons
        """
        text = f"{opp.get('title', '')} {opp.get('body', '')} {opp.get('description', '')}"
        platform = (opp.get('platform', '') or '').lower()

        # Base risk
        risk_score = 0.2

        risk_reasons = []

        # Platform adjustment
        platform_adj = 0
        for plat, adj in self.platform_risk.items():
            if plat in platform:
                platform_adj = adj
                break
        risk_score += platform_adj

        # Scam indicators (major risk)
        scam_count = self._count_indicator_matches(text, self.scam_indicators)
        if scam_count > 0:
            risk_score += min(0.5, scam_count * 0.15)
            risk_reasons.append(f"scam_indicators:{scam_count}")

        # Low quality signals (moderate risk)
        low_quality_count = self._count_indicator_matches(text, self.low_quality_signals)
        if low_quality_count > 0:
            risk_score += min(0.3, low_quality_count * 0.1)
            risk_reasons.append(f"low_quality:{low_quality_count}")

        # Suspicious budget
        if self._has_suspicious_budget(opp):
            risk_score += 0.2
            risk_reasons.append("suspicious_budget")

        # No organizational presence
        if not self._has_org_presence(opp):
            risk_score += 0.15
            risk_reasons.append("no_org_presence")

        # Contact red flags
        if self._has_contact_red_flags(text):
            risk_score += 0.25
            risk_reasons.append("contact_red_flags")

        # Clamp to 0-1
        risk_score = max(0.0, min(1.0, risk_score))

        # Determine risk flag
        if risk_score >= 0.8:
            risk_flag = 'high'
        elif risk_score >= 0.5:
            risk_flag = 'medium'
        elif risk_score >= 0.3:
            risk_flag = 'low'
        else:
            risk_flag = 'none'

        # Log high-risk opportunities
        if risk_flag == 'high':
            logger.warning(f"[safety] High risk opportunity: {opp.get('title', '')[:50]} - {risk_reasons}")

        # Update opportunity
        opp['risk_score'] = round(risk_score, 3)
        opp['risk_flag'] = risk_flag
        opp['risk_reasons'] = risk_reasons

        return opp

    def filter_high_risk(self, opportunities: list, max_risk: float = 0.8) -> list:
        """Filter out high-risk opportunities"""
        filtered = []
        blocked = 0

        for opp in opportunities:
            # Screen if not already done
            if 'risk_score' not in opp:
                opp = self.risk_screen(opp)

            if opp['risk_score'] <= max_risk:
                filtered.append(opp)
            else:
                blocked += 1
                logger.info(f"[safety] Blocked high-risk: {opp.get('title', '')[:50]}")

        if blocked > 0:
            logger.info(f"[safety] Blocked {blocked} high-risk opportunities")

        return filtered

    def screen_batch(self, opportunities: list) -> list:
        """Screen batch of opportunities for risk"""
        return [self.risk_screen(opp) for opp in opportunities]


# Singleton instance
_safety_filter: Optional[SafetyFilter] = None


def get_safety_filter() -> SafetyFilter:
    """Get or create safety filter instance"""
    global _safety_filter
    if _safety_filter is None:
        _safety_filter = SafetyFilter()
    return _safety_filter
