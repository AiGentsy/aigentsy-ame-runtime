"""
Adversarial Guard - Sybil/Bot/Low-intent Filtering
===================================================

Tier 4 Quality & Trust Module

Features:
- Sybil attack detection
- Bot/automation detection
- Low-intent signal filtering
- Fraud pattern recognition

Impact: Protect margins from bad actors
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass
import hashlib
import logging

logger = logging.getLogger("adversarial_guard")


@dataclass
class AdversarialScore:
    """Adversarial risk assessment"""
    risk_score: float  # 0-1, higher is riskier
    flags: List[str]
    require_escrow: bool
    require_verification: bool
    block: bool


# Detection thresholds
THRESHOLDS = {
    "sybil_similarity": 0.8,       # Similar patterns threshold
    "bot_speed": 0.5,              # Response time too fast
    "low_intent_threshold": 0.3,   # Low engagement signals
    "fraud_pattern_match": 0.6,    # Known fraud patterns
}

# Known fraud patterns (simplified)
FRAUD_PATTERNS = [
    {"pattern": "urgency_extreme", "weight": 0.3},
    {"pattern": "value_inflated", "weight": 0.2},
    {"pattern": "new_account", "weight": 0.15},
    {"pattern": "no_verification", "weight": 0.25},
    {"pattern": "suspicious_contact", "weight": 0.4},
]


class AdversarialGuard:
    """
    Protects against adversarial actors

    Detects:
    - Sybil attacks (fake multiple accounts)
    - Bots/automation
    - Low-intent leads
    - Fraud patterns
    """

    def __init__(self):
        self._seen_fingerprints: Dict[str, int] = {}
        self._blocked_count: int = 0
        self._flagged_count: int = 0

    def score(self, opportunity: Dict[str, Any]) -> float:
        """
        Calculate adversarial risk score (0-1)

        Args:
            opportunity: Opportunity data

        Returns:
            Risk score (higher = more risky)
        """
        assessment = self.assess(opportunity)
        return assessment.risk_score

    def assess(self, opportunity: Dict[str, Any]) -> AdversarialScore:
        """
        Full adversarial assessment

        Returns:
            AdversarialScore with risk details
        """
        flags = []
        risk_score = 0.0

        # Check sybil patterns
        fingerprint = self._calculate_fingerprint(opportunity)
        sybil_count = self._seen_fingerprints.get(fingerprint, 0)
        self._seen_fingerprints[fingerprint] = sybil_count + 1

        if sybil_count > 3:
            flags.append("sybil_suspected")
            risk_score += 0.3

        # Check for bot signals
        bot_score = self._detect_bot(opportunity)
        if bot_score > THRESHOLDS["bot_speed"]:
            flags.append("bot_suspected")
            risk_score += bot_score * 0.25

        # Check low intent
        intent_score = self._assess_intent(opportunity)
        if intent_score < THRESHOLDS["low_intent_threshold"]:
            flags.append("low_intent")
            risk_score += (1 - intent_score) * 0.2

        # Check fraud patterns
        fraud_score = self._check_fraud_patterns(opportunity)
        if fraud_score > THRESHOLDS["fraud_pattern_match"]:
            flags.append("fraud_pattern_match")
            risk_score += fraud_score * 0.3

        # Normalize
        risk_score = min(1.0, risk_score)

        # Determine actions
        require_escrow = risk_score > 0.5
        require_verification = risk_score > 0.3
        block = risk_score > 0.85

        if block:
            self._blocked_count += 1
        if flags:
            self._flagged_count += 1

        result = AdversarialScore(
            risk_score=round(risk_score, 3),
            flags=flags,
            require_escrow=require_escrow,
            require_verification=require_verification,
            block=block
        )

        if flags:
            logger.warning(f"Adversarial flags: {flags}, score={risk_score:.2f}")

        return result

    def _calculate_fingerprint(self, opportunity: Dict[str, Any]) -> str:
        """Calculate fingerprint for sybil detection"""
        # Use key fields to create fingerprint
        fingerprint_data = f"{opportunity.get('platform', '')}:{opportunity.get('segment', '')}:{opportunity.get('value', '')}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()[:8]

    def _detect_bot(self, opportunity: Dict[str, Any]) -> float:
        """Detect bot/automation signals"""
        score = 0.0

        # Check for templated description
        desc = opportunity.get("description", "")
        if len(desc) < 20:
            score += 0.2
        if desc.isupper():
            score += 0.3

        # Check for suspicious patterns
        if "asap" in desc.lower() and "urgent" in desc.lower():
            score += 0.2

        return min(1.0, score)

    def _assess_intent(self, opportunity: Dict[str, Any]) -> float:
        """Assess genuine intent level"""
        intent = 0.5  # Base intent

        # Higher value = higher intent
        value = float(opportunity.get("value", 0) or 0)
        if value > 500:
            intent += 0.2
        elif value < 50:
            intent -= 0.2

        # Description length indicates effort
        desc_len = len(opportunity.get("description", ""))
        if desc_len > 200:
            intent += 0.15
        elif desc_len < 50:
            intent -= 0.15

        # Platform quality
        platform = opportunity.get("platform", "").lower()
        if platform in ["linkedin", "direct", "referral"]:
            intent += 0.1
        elif platform in ["fiverr"]:
            intent -= 0.1

        return max(0.0, min(1.0, intent))

    def _check_fraud_patterns(self, opportunity: Dict[str, Any]) -> float:
        """Check for known fraud patterns"""
        score = 0.0
        desc = opportunity.get("description", "").lower()

        # Check urgency
        if any(w in desc for w in ["asap", "immediately", "right now", "emergency"]):
            score += FRAUD_PATTERNS[0]["weight"]

        # Check value inflation
        value = float(opportunity.get("value", 0) or 0)
        if value > 10000:
            score += FRAUD_PATTERNS[1]["weight"]

        # Check for new/unverified source
        if not opportunity.get("verified", False):
            score += FRAUD_PATTERNS[3]["weight"]

        return min(1.0, score)

    def get_stats(self) -> Dict[str, Any]:
        """Get guard statistics"""
        return {
            "blocked_count": self._blocked_count,
            "flagged_count": self._flagged_count,
            "fingerprints_tracked": len(self._seen_fingerprints),
            "thresholds": THRESHOLDS
        }


# Singleton
_adversarial_guard: Optional[AdversarialGuard] = None

def get_adversarial_guard() -> AdversarialGuard:
    global _adversarial_guard
    if _adversarial_guard is None:
        _adversarial_guard = AdversarialGuard()
    return _adversarial_guard

def score_adversarial(opportunity: Dict[str, Any]) -> float:
    return get_adversarial_guard().score(opportunity)
