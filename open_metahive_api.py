"""
OPEN METAHIVE API - External AI Contribution Protocol
======================================================

This opens MetaHive to the ENTIRE AI ecosystem.
Any AI agent can:
- Contribute winning patterns
- Earn AIGx for verified contributions
- Access collective intelligence
- Build reputation in the protocol

THE FLYWHEEL:
More contributors → Smarter MetaHive → Better outcomes → More contributors

WHAT EXTERNAL AI GIVES:
- Winning patterns (ROAS > 1.5)
- Outcome data
- Market signals

WHAT EXTERNAL AI GETS:
- AIGx credits
- Access to MetaHive intelligence
- Reputation in protocol
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
import math


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


# ============================================================
# PATTERN TYPES & VALIDATION
# ============================================================

class PatternType(str, Enum):
    """Types of patterns that can be contributed"""
    PRICING = "pricing"  # Optimal pricing strategies
    TIMING = "timing"  # Best times to execute
    TARGETING = "targeting"  # Audience/client targeting
    MESSAGING = "messaging"  # Copy/pitch patterns
    CHANNEL = "channel"  # Platform/channel selection
    SEQUENCE = "sequence"  # Multi-step workflows
    NEGOTIATION = "negotiation"  # Deal negotiation tactics
    ARBITRAGE = "arbitrage"  # Cross-platform opportunities
    CONVERSION = "conversion"  # Conversion optimization
    RETENTION = "retention"  # Client retention patterns


class PatternStatus(str, Enum):
    """Pattern lifecycle status"""
    PENDING = "pending"  # Awaiting validation
    VALIDATING = "validating"  # Being tested
    VERIFIED = "verified"  # Proven effective
    REJECTED = "rejected"  # Did not meet threshold
    DEPRECATED = "deprecated"  # No longer effective


class ContributorTier(str, Enum):
    """Contributor reputation tiers"""
    NEW = "new"  # < 5 verified patterns
    BRONZE = "bronze"  # 5-19 verified
    SILVER = "silver"  # 20-49 verified
    GOLD = "gold"  # 50-99 verified
    PLATINUM = "platinum"  # 100-249 verified
    DIAMOND = "diamond"  # 250+ verified


TIER_THRESHOLDS = {
    ContributorTier.NEW: (0, 4),
    ContributorTier.BRONZE: (5, 19),
    ContributorTier.SILVER: (20, 49),
    ContributorTier.GOLD: (50, 99),
    ContributorTier.PLATINUM: (100, 249),
    ContributorTier.DIAMOND: (250, float('inf'))
}

# Reward multipliers by tier
TIER_REWARDS = {
    ContributorTier.NEW: 1.0,
    ContributorTier.BRONZE: 1.2,
    ContributorTier.SILVER: 1.5,
    ContributorTier.GOLD: 2.0,
    ContributorTier.PLATINUM: 2.5,
    ContributorTier.DIAMOND: 3.0
}

# Access levels by tier
TIER_ACCESS = {
    ContributorTier.NEW: ["basic_patterns"],
    ContributorTier.BRONZE: ["basic_patterns", "trending"],
    ContributorTier.SILVER: ["basic_patterns", "trending", "industry_insights"],
    ContributorTier.GOLD: ["basic_patterns", "trending", "industry_insights", "predictive"],
    ContributorTier.PLATINUM: ["basic_patterns", "trending", "industry_insights", "predictive", "arbitrage"],
    ContributorTier.DIAMOND: ["full_access"]
}


# ============================================================
# PATTERN DATA STRUCTURES
# ============================================================

@dataclass
class Pattern:
    """A contributed pattern"""
    pattern_id: str
    contributor_id: str
    pattern_type: PatternType
    context: Dict[str, Any]  # When this pattern applies
    action: Dict[str, Any]  # What to do
    outcome: Dict[str, Any]  # Expected results
    evidence: Dict[str, Any]  # Proof it works
    
    # Validation metrics
    reported_roas: float
    reported_sample_size: int
    
    # Protocol tracking
    status: PatternStatus = PatternStatus.PENDING
    verified_roas: float = 0.0
    verification_sample: int = 0
    usage_count: int = 0
    success_rate: float = 0.0
    
    # Rewards
    aigx_earned: float = 0.0
    
    # Metadata
    created_at: str = field(default_factory=_now)
    verified_at: Optional[str] = None
    pattern_hash: str = ""
    
    def __post_init__(self):
        if not self.pattern_hash:
            self.pattern_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Unique hash to prevent duplicates"""
        data = {
            "type": self.pattern_type.value,
            "context": json.dumps(self.context, sort_keys=True),
            "action": json.dumps(self.action, sort_keys=True)
        }
        return _hash(json.dumps(data, sort_keys=True))
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["pattern_type"] = self.pattern_type.value
        result["status"] = self.status.value
        return result
    
    def to_public_dict(self) -> Dict:
        """Sanitized version for API responses"""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "context": self.context,
            "action": self.action,
            "status": self.status.value,
            "verified_roas": self.verified_roas,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate
        }


@dataclass
class Contributor:
    """External AI contributor"""
    contributor_id: str
    agent_name: str
    agent_type: str  # claude, gpt, custom, etc.
    owner_id: Optional[str]  # Platform that owns this agent
    api_key: str
    
    # Stats
    patterns_submitted: int = 0
    patterns_verified: int = 0
    patterns_rejected: int = 0
    total_aigx_earned: float = 0.0
    
    # Reputation
    tier: ContributorTier = ContributorTier.NEW
    reputation_score: float = 0.0
    
    # Access
    access_level: List[str] = field(default_factory=lambda: ["basic_patterns"])
    
    # Metadata
    registered_at: str = field(default_factory=_now)
    last_contribution: Optional[str] = None
    is_active: bool = True
    
    def update_tier(self):
        """Update tier based on verified patterns"""
        for tier, (min_v, max_v) in TIER_THRESHOLDS.items():
            if min_v <= self.patterns_verified <= max_v:
                self.tier = tier
                self.access_level = TIER_ACCESS[tier]
                return
    
    def calculate_reputation(self):
        """Calculate reputation score"""
        if self.patterns_submitted == 0:
            self.reputation_score = 0
            return
        
        verification_rate = self.patterns_verified / self.patterns_submitted
        volume_factor = min(1.0, self.patterns_verified / 100)  # Caps at 100
        
        self.reputation_score = round((verification_rate * 0.7 + volume_factor * 0.3) * 100, 1)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["tier"] = self.tier.value
        return result


# ============================================================
# VALIDATION ENGINE
# ============================================================

class PatternValidator:
    """
    Validates contributed patterns through testing
    
    Validation process:
    1. Check for duplicates
    2. Verify evidence
    3. Test in controlled environment
    4. Measure actual ROAS
    5. Approve or reject
    """
    
    MIN_ROAS_THRESHOLD = 1.5  # Minimum ROAS to verify
    MIN_SAMPLE_SIZE = 10  # Minimum test executions
    VALIDATION_PERIOD_DAYS = 7  # Days to validate
    
    def __init__(self):
        self._validation_queue: Dict[str, Dict] = {}
        self._test_results: Dict[str, List[Dict]] = {}
    
    def queue_for_validation(self, pattern: Pattern) -> Dict[str, Any]:
        """Add pattern to validation queue"""
        if pattern.reported_roas < self.MIN_ROAS_THRESHOLD:
            return {
                "ok": False,
                "error": "roas_below_threshold",
                "min_required": self.MIN_ROAS_THRESHOLD,
                "reported": pattern.reported_roas
            }
        
        if pattern.reported_sample_size < 5:
            return {
                "ok": False,
                "error": "sample_size_too_small",
                "min_required": 5,
                "reported": pattern.reported_sample_size
            }
        
        pattern.status = PatternStatus.VALIDATING
        
        self._validation_queue[pattern.pattern_id] = {
            "pattern": pattern,
            "queued_at": _now(),
            "test_count": 0,
            "successes": 0,
            "total_revenue": 0.0,
            "total_cost": 0.0
        }
        
        return {
            "ok": True,
            "pattern_id": pattern.pattern_id,
            "status": "validating",
            "estimated_completion": (
                datetime.now(timezone.utc) + timedelta(days=self.VALIDATION_PERIOD_DAYS)
            ).isoformat()
        }
    
    def record_test_result(
        self,
        pattern_id: str,
        success: bool,
        revenue: float,
        cost: float,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Record a test execution result"""
        if pattern_id not in self._validation_queue:
            return {"ok": False, "error": "pattern_not_in_validation"}
        
        queue_entry = self._validation_queue[pattern_id]
        queue_entry["test_count"] += 1
        
        if success:
            queue_entry["successes"] += 1
        
        queue_entry["total_revenue"] += revenue
        queue_entry["total_cost"] += cost
        
        # Store result
        if pattern_id not in self._test_results:
            self._test_results[pattern_id] = []
        
        self._test_results[pattern_id].append({
            "success": success,
            "revenue": revenue,
            "cost": cost,
            "metadata": metadata,
            "tested_at": _now()
        })
        
        # Check if validation complete
        if queue_entry["test_count"] >= self.MIN_SAMPLE_SIZE:
            return self._finalize_validation(pattern_id)
        
        return {
            "ok": True,
            "pattern_id": pattern_id,
            "tests_completed": queue_entry["test_count"],
            "tests_remaining": self.MIN_SAMPLE_SIZE - queue_entry["test_count"]
        }
    
    def _finalize_validation(self, pattern_id: str) -> Dict[str, Any]:
        """Complete validation and determine status"""
        queue_entry = self._validation_queue[pattern_id]
        pattern = queue_entry["pattern"]
        
        # Calculate actual ROAS
        total_cost = queue_entry["total_cost"]
        total_revenue = queue_entry["total_revenue"]
        
        if total_cost > 0:
            actual_roas = total_revenue / total_cost
        else:
            actual_roas = 0
        
        success_rate = queue_entry["successes"] / queue_entry["test_count"]
        
        # Update pattern
        pattern.verified_roas = round(actual_roas, 2)
        pattern.verification_sample = queue_entry["test_count"]
        pattern.success_rate = round(success_rate, 2)
        
        # Determine status
        if actual_roas >= self.MIN_ROAS_THRESHOLD and success_rate >= 0.5:
            pattern.status = PatternStatus.VERIFIED
            pattern.verified_at = _now()
            verified = True
        else:
            pattern.status = PatternStatus.REJECTED
            verified = False
        
        # Remove from queue
        del self._validation_queue[pattern_id]
        
        return {
            "ok": True,
            "pattern_id": pattern_id,
            "verified": verified,
            "status": pattern.status.value,
            "actual_roas": actual_roas,
            "success_rate": success_rate,
            "sample_size": queue_entry["test_count"]
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get validation queue status"""
        return {
            "queue_length": len(self._validation_queue),
            "patterns": [
                {
                    "pattern_id": pid,
                    "tests_completed": entry["test_count"],
                    "queued_at": entry["queued_at"]
                }
                for pid, entry in self._validation_queue.items()
            ]
        }


# ============================================================
# REWARDS ENGINE
# ============================================================

class RewardsEngine:
    """
    Calculates and distributes AIGx rewards for contributions
    
    Reward factors:
    - Pattern ROAS (higher = more reward)
    - Usage count (more used = more reward)
    - Contributor tier (multiplier)
    - Pattern uniqueness (novel patterns worth more)
    """
    
    BASE_REWARD = 10.0  # Base AIGx per verified pattern
    ROAS_MULTIPLIER = 2.0  # Per ROAS point above threshold
    USAGE_REWARD = 0.1  # Per usage after verification
    
    def __init__(self, aigx_ledger=None):
        self.aigx = aigx_ledger
        self._rewards_distributed: float = 0.0
        self._rewards_log: List[Dict] = []
    
    def calculate_verification_reward(
        self,
        pattern: Pattern,
        contributor: Contributor
    ) -> float:
        """Calculate reward for verified pattern"""
        if pattern.status != PatternStatus.VERIFIED:
            return 0.0
        
        # Base reward
        reward = self.BASE_REWARD
        
        # ROAS bonus (for ROAS above threshold)
        roas_bonus = max(0, pattern.verified_roas - 1.5) * self.ROAS_MULTIPLIER
        reward += roas_bonus
        
        # Tier multiplier
        tier_mult = TIER_REWARDS.get(contributor.tier, 1.0)
        reward *= tier_mult
        
        return round(reward, 2)
    
    def calculate_usage_reward(
        self,
        pattern: Pattern,
        contributor: Contributor,
        usage_success: bool
    ) -> float:
        """Calculate ongoing reward when pattern is used"""
        if pattern.status != PatternStatus.VERIFIED:
            return 0.0
        
        if not usage_success:
            return 0.0
        
        # Base usage reward with tier multiplier
        tier_mult = TIER_REWARDS.get(contributor.tier, 1.0)
        reward = self.USAGE_REWARD * tier_mult
        
        return round(reward, 4)
    
    def distribute_reward(
        self,
        contributor_id: str,
        amount: float,
        reason: str,
        pattern_id: str = None
    ) -> Dict[str, Any]:
        """Distribute AIGx reward to contributor"""
        self._rewards_distributed += amount
        
        reward_entry = {
            "contributor_id": contributor_id,
            "amount": amount,
            "reason": reason,
            "pattern_id": pattern_id,
            "distributed_at": _now()
        }
        self._rewards_log.append(reward_entry)
        
        # If AIGx ledger connected, credit the balance
        if self.aigx:
            self.aigx.earn(
                contributor_id,
                amount,
                "protocol_reward",
                f"MetaHive: {reason}",
                pattern_id
            )
        
        return {
            "ok": True,
            "contributor_id": contributor_id,
            "amount": amount,
            "reason": reason
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rewards engine stats"""
        return {
            "total_distributed": round(self._rewards_distributed, 2),
            "total_rewards": len(self._rewards_log),
            "recent_rewards": self._rewards_log[-10:]
        }


# ============================================================
# OPEN METAHIVE API
# ============================================================

class OpenMetaHiveAPI:
    """
    The public API for external AI to contribute to MetaHive
    
    Endpoints:
    - Register contributor
    - Submit pattern
    - Query patterns (based on access level)
    - Check rewards
    - Get leaderboard
    """
    
    def __init__(self, aigx_ledger=None):
        self._contributors: Dict[str, Contributor] = {}
        self._patterns: Dict[str, Pattern] = {}
        self._pattern_hashes: set = set()  # For duplicate detection
        self._patterns_by_type: Dict[PatternType, List[str]] = {t: [] for t in PatternType}
        self._patterns_by_contributor: Dict[str, List[str]] = {}
        
        self.validator = PatternValidator()
        self.rewards = RewardsEngine(aigx_ledger)
        self.aigx = aigx_ledger
    
    # ==================== REGISTRATION ====================
    
    def register_contributor(
        self,
        agent_name: str,
        agent_type: str,
        owner_id: str = None
    ) -> Dict[str, Any]:
        """
        Register an external AI as a contributor
        
        Returns API key for future requests
        """
        contributor_id = _generate_id("contrib")
        api_key = f"mh_{_hash(f'{contributor_id}:{_now()}')[:32]}"
        
        contributor = Contributor(
            contributor_id=contributor_id,
            agent_name=agent_name,
            agent_type=agent_type,
            owner_id=owner_id,
            api_key=api_key
        )
        
        self._contributors[contributor_id] = contributor
        self._patterns_by_contributor[contributor_id] = []
        
        return {
            "ok": True,
            "contributor_id": contributor_id,
            "api_key": api_key,
            "agent_name": agent_name,
            "tier": contributor.tier.value,
            "access_level": contributor.access_level,
            "message": "Welcome to MetaHive. Submit patterns to earn AIGx."
        }
    
    def authenticate(self, api_key: str) -> Optional[Contributor]:
        """Authenticate API key and return contributor"""
        for contributor in self._contributors.values():
            if contributor.api_key == api_key:
                return contributor
        return None
    
    # ==================== PATTERN SUBMISSION ====================
    
    def submit_pattern(
        self,
        api_key: str,
        pattern_type: str,
        context: Dict[str, Any],
        action: Dict[str, Any],
        outcome: Dict[str, Any],
        evidence: Dict[str, Any],
        reported_roas: float,
        reported_sample_size: int
    ) -> Dict[str, Any]:
        """
        Submit a pattern for validation
        
        Args:
            api_key: Contributor's API key
            pattern_type: Type of pattern (pricing, timing, etc.)
            context: When this pattern applies
            action: What to do
            outcome: Expected results
            evidence: Proof it works
            reported_roas: ROAS reported by contributor
            reported_sample_size: Sample size of contributor's testing
        """
        # Authenticate
        contributor = self.authenticate(api_key)
        if not contributor:
            return {"ok": False, "error": "invalid_api_key"}
        
        # Validate pattern type
        try:
            pattern_type_enum = PatternType(pattern_type)
        except ValueError:
            return {
                "ok": False,
                "error": "invalid_pattern_type",
                "valid_types": [t.value for t in PatternType]
            }
        
        # Create pattern
        pattern = Pattern(
            pattern_id=_generate_id("pattern"),
            contributor_id=contributor.contributor_id,
            pattern_type=pattern_type_enum,
            context=context,
            action=action,
            outcome=outcome,
            evidence=evidence,
            reported_roas=reported_roas,
            reported_sample_size=reported_sample_size
        )
        
        # Check for duplicate
        if pattern.pattern_hash in self._pattern_hashes:
            return {
                "ok": False,
                "error": "duplicate_pattern",
                "message": "A similar pattern already exists"
            }
        
        # Queue for validation
        validation_result = self.validator.queue_for_validation(pattern)
        
        if not validation_result.get("ok"):
            return validation_result
        
        # Store pattern
        self._patterns[pattern.pattern_id] = pattern
        self._pattern_hashes.add(pattern.pattern_hash)
        self._patterns_by_type[pattern_type_enum].append(pattern.pattern_id)
        self._patterns_by_contributor[contributor.contributor_id].append(pattern.pattern_id)
        
        # Update contributor stats
        contributor.patterns_submitted += 1
        contributor.last_contribution = _now()
        
        return {
            "ok": True,
            "pattern_id": pattern.pattern_id,
            "status": "validating",
            "message": "Pattern submitted for validation. You'll earn AIGx if verified.",
            "estimated_completion": validation_result.get("estimated_completion")
        }
    
    def get_pattern_status(self, api_key: str, pattern_id: str) -> Dict[str, Any]:
        """Get status of a submitted pattern"""
        contributor = self.authenticate(api_key)
        if not contributor:
            return {"ok": False, "error": "invalid_api_key"}
        
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return {"ok": False, "error": "pattern_not_found"}
        
        if pattern.contributor_id != contributor.contributor_id:
            return {"ok": False, "error": "not_your_pattern"}
        
        return {
            "ok": True,
            "pattern_id": pattern_id,
            "status": pattern.status.value,
            "reported_roas": pattern.reported_roas,
            "verified_roas": pattern.verified_roas,
            "verification_sample": pattern.verification_sample,
            "usage_count": pattern.usage_count,
            "aigx_earned": pattern.aigx_earned
        }
    
    # ==================== PATTERN QUERY ====================
    
    def query_patterns(
        self,
        api_key: str,
        pattern_type: str = None,
        context_filter: Dict = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Query patterns from MetaHive (based on access level)
        """
        contributor = self.authenticate(api_key)
        if not contributor:
            return {"ok": False, "error": "invalid_api_key"}
        
        # Get accessible patterns based on tier
        if "full_access" in contributor.access_level:
            accessible_patterns = list(self._patterns.values())
        else:
            # Filter based on access level
            accessible_patterns = [
                p for p in self._patterns.values()
                if p.status == PatternStatus.VERIFIED
            ]
        
        # Filter by type
        if pattern_type:
            try:
                type_enum = PatternType(pattern_type)
                accessible_patterns = [
                    p for p in accessible_patterns
                    if p.pattern_type == type_enum
                ]
            except ValueError:
                pass
        
        # Filter by context
        if context_filter:
            filtered = []
            for p in accessible_patterns:
                match = all(
                    p.context.get(k) == v
                    for k, v in context_filter.items()
                )
                if match:
                    filtered.append(p)
            accessible_patterns = filtered
        
        # Sort by ROAS and usage
        accessible_patterns.sort(
            key=lambda p: (p.verified_roas * p.success_rate, p.usage_count),
            reverse=True
        )
        
        return {
            "ok": True,
            "patterns": [p.to_public_dict() for p in accessible_patterns[:limit]],
            "total_available": len(accessible_patterns),
            "your_access_level": contributor.access_level
        }
    
    def get_pattern_detail(self, api_key: str, pattern_id: str) -> Dict[str, Any]:
        """Get full pattern detail (for execution)"""
        contributor = self.authenticate(api_key)
        if not contributor:
            return {"ok": False, "error": "invalid_api_key"}
        
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return {"ok": False, "error": "pattern_not_found"}
        
        if pattern.status != PatternStatus.VERIFIED:
            return {"ok": False, "error": "pattern_not_verified"}
        
        # Record usage
        pattern.usage_count += 1
        
        return {
            "ok": True,
            "pattern": pattern.to_dict()
        }
    
    # ==================== USAGE REPORTING ====================
    
    def report_pattern_usage(
        self,
        api_key: str,
        pattern_id: str,
        success: bool,
        revenue: float = 0,
        cost: float = 0,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        Report outcome of using a pattern
        
        This feeds back into MetaHive learning AND
        rewards the original contributor.
        """
        contributor = self.authenticate(api_key)
        if not contributor:
            return {"ok": False, "error": "invalid_api_key"}
        
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return {"ok": False, "error": "pattern_not_found"}
        
        # Update pattern stats
        old_success_rate = pattern.success_rate
        old_usage = pattern.usage_count - 1  # Already incremented on get
        
        if old_usage > 0:
            total_successes = old_success_rate * old_usage
            if success:
                total_successes += 1
            pattern.success_rate = round(total_successes / pattern.usage_count, 2)
        else:
            pattern.success_rate = 1.0 if success else 0.0
        
        # Reward original contributor
        original_contributor = self._contributors.get(pattern.contributor_id)
        if original_contributor and success:
            usage_reward = self.rewards.calculate_usage_reward(
                pattern, original_contributor, success
            )
            if usage_reward > 0:
                self.rewards.distribute_reward(
                    original_contributor.contributor_id,
                    usage_reward,
                    "pattern_usage",
                    pattern_id
                )
                pattern.aigx_earned += usage_reward
                original_contributor.total_aigx_earned += usage_reward
        
        return {
            "ok": True,
            "pattern_id": pattern_id,
            "success_recorded": success,
            "new_success_rate": pattern.success_rate,
            "contributor_rewarded": success
        }
    
    # ==================== VERIFICATION CALLBACK ====================
    
    def on_pattern_verified(self, pattern_id: str, verified: bool) -> Dict[str, Any]:
        """
        Called when validation completes
        
        Distributes verification reward if verified.
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return {"ok": False, "error": "pattern_not_found"}
        
        contributor = self._contributors.get(pattern.contributor_id)
        if not contributor:
            return {"ok": False, "error": "contributor_not_found"}
        
        if verified:
            contributor.patterns_verified += 1
            
            # Calculate and distribute reward
            reward = self.rewards.calculate_verification_reward(pattern, contributor)
            self.rewards.distribute_reward(
                contributor.contributor_id,
                reward,
                "pattern_verified",
                pattern_id
            )
            pattern.aigx_earned += reward
            contributor.total_aigx_earned += reward
        else:
            contributor.patterns_rejected += 1
        
        # Update contributor tier and reputation
        contributor.update_tier()
        contributor.calculate_reputation()
        
        return {
            "ok": True,
            "pattern_id": pattern_id,
            "verified": verified,
            "reward": reward if verified else 0,
            "contributor_tier": contributor.tier.value,
            "contributor_reputation": contributor.reputation_score
        }
    
    # ==================== CONTRIBUTOR INFO ====================
    
    def get_contributor_stats(self, api_key: str) -> Dict[str, Any]:
        """Get contributor's stats and earnings"""
        contributor = self.authenticate(api_key)
        if not contributor:
            return {"ok": False, "error": "invalid_api_key"}
        
        return {
            "ok": True,
            "contributor_id": contributor.contributor_id,
            "agent_name": contributor.agent_name,
            "tier": contributor.tier.value,
            "reputation_score": contributor.reputation_score,
            "patterns_submitted": contributor.patterns_submitted,
            "patterns_verified": contributor.patterns_verified,
            "patterns_rejected": contributor.patterns_rejected,
            "verification_rate": round(
                contributor.patterns_verified / contributor.patterns_submitted * 100, 1
            ) if contributor.patterns_submitted > 0 else 0,
            "total_aigx_earned": contributor.total_aigx_earned,
            "access_level": contributor.access_level,
            "tier_progress": self._get_tier_progress(contributor)
        }
    
    def _get_tier_progress(self, contributor: Contributor) -> Dict:
        """Get progress to next tier"""
        current_tier_idx = list(ContributorTier).index(contributor.tier)
        
        if current_tier_idx >= len(ContributorTier) - 1:
            return {"at_max_tier": True}
        
        next_tier = list(ContributorTier)[current_tier_idx + 1]
        next_threshold = TIER_THRESHOLDS[next_tier][0]
        
        return {
            "current_tier": contributor.tier.value,
            "next_tier": next_tier.value,
            "verified_patterns": contributor.patterns_verified,
            "needed_for_next": next_threshold,
            "remaining": max(0, next_threshold - contributor.patterns_verified)
        }
    
    # ==================== LEADERBOARD ====================
    
    def get_leaderboard(self, limit: int = 20) -> Dict[str, Any]:
        """Get top contributors"""
        contributors = list(self._contributors.values())
        contributors.sort(
            key=lambda c: (c.total_aigx_earned, c.patterns_verified),
            reverse=True
        )
        
        leaderboard = []
        for rank, c in enumerate(contributors[:limit], 1):
            leaderboard.append({
                "rank": rank,
                "agent_name": c.agent_name,
                "tier": c.tier.value,
                "patterns_verified": c.patterns_verified,
                "total_aigx_earned": round(c.total_aigx_earned, 2),
                "reputation_score": c.reputation_score
            })
        
        return {
            "ok": True,
            "leaderboard": leaderboard,
            "total_contributors": len(self._contributors)
        }
    
    # ==================== STATS ====================
    
    def get_metahive_stats(self) -> Dict[str, Any]:
        """Get MetaHive statistics"""
        verified_patterns = [
            p for p in self._patterns.values()
            if p.status == PatternStatus.VERIFIED
        ]
        
        total_usage = sum(p.usage_count for p in verified_patterns)
        avg_roas = (
            sum(p.verified_roas for p in verified_patterns) / len(verified_patterns)
            if verified_patterns else 0
        )
        
        return {
            "ok": True,
            "total_patterns": len(self._patterns),
            "verified_patterns": len(verified_patterns),
            "total_contributors": len(self._contributors),
            "total_pattern_usage": total_usage,
            "average_verified_roas": round(avg_roas, 2),
            "patterns_by_type": {
                t.value: len(pids) for t, pids in self._patterns_by_type.items()
            },
            "rewards": self.rewards.get_stats(),
            "validation_queue": self.validator.get_queue_status()
        }


# ============================================================
# SINGLETON
# ============================================================

_metahive_api: Optional[OpenMetaHiveAPI] = None


def get_metahive_api(aigx_ledger=None) -> OpenMetaHiveAPI:
    """Get singleton MetaHive API instance"""
    global _metahive_api
    if _metahive_api is None:
        _metahive_api = OpenMetaHiveAPI(aigx_ledger)
    return _metahive_api


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("OPEN METAHIVE API - External AI Contribution Protocol")
    print("=" * 70)
    
    api = get_metahive_api()
    
    # 1. Register external AI
    print("\n1. Register external Claude agent...")
    reg = api.register_contributor("Claude Optimizer", "claude", "external_platform")
    print(f"   Contributor ID: {reg['contributor_id']}")
    print(f"   API Key: {reg['api_key'][:20]}...")
    api_key = reg['api_key']
    
    # 2. Submit a pattern
    print("\n2. Submit pricing pattern...")
    submit = api.submit_pattern(
        api_key=api_key,
        pattern_type="pricing",
        context={
            "industry": "saas",
            "deal_size": "1000-5000",
            "client_type": "startup"
        },
        action={
            "strategy": "value_based",
            "anchor_high": True,
            "discount_trigger": "multi_month"
        },
        outcome={
            "expected_roas": 2.5,
            "close_rate": 0.35
        },
        evidence={
            "sample_size": 50,
            "time_period": "30_days",
            "platforms": ["upwork", "fiverr"]
        },
        reported_roas=2.5,
        reported_sample_size=50
    )
    print(f"   Pattern ID: {submit.get('pattern_id')}")
    print(f"   Status: {submit.get('status')}")
    
    # 3. Simulate validation
    print("\n3. Simulate validation tests...")
    pattern_id = submit['pattern_id']
    for i in range(10):
        api.validator.record_test_result(
            pattern_id,
            success=i < 7,  # 70% success
            revenue=100 + (i * 20),
            cost=50
        )
    
    # 4. Check pattern status
    print("\n4. Check pattern status...")
    status = api.get_pattern_status(api_key, pattern_id)
    print(f"   Status: {status.get('status')}")
    print(f"   Verified ROAS: {status.get('verified_roas')}")
    
    # 5. Trigger verification callback
    print("\n5. Process verification...")
    if status.get('status') == 'verified':
        verify = api.on_pattern_verified(pattern_id, True)
        print(f"   Reward: {verify.get('reward')} AIGx")
    
    # 6. Query patterns
    print("\n6. Query available patterns...")
    patterns = api.query_patterns(api_key, pattern_type="pricing")
    print(f"   Available: {patterns.get('total_available')}")
    
    # 7. Get contributor stats
    print("\n7. Contributor stats...")
    stats = api.get_contributor_stats(api_key)
    print(f"   Tier: {stats.get('tier')}")
    print(f"   AIGx Earned: {stats.get('total_aigx_earned')}")
    
    # 8. MetaHive stats
    print("\n8. MetaHive stats...")
    mh_stats = api.get_metahive_stats()
    print(f"   Total patterns: {mh_stats.get('total_patterns')}")
    print(f"   Total contributors: {mh_stats.get('total_contributors')}")
    
    print("\n" + "=" * 70)
    print("✅ Open MetaHive API test complete!")
    print("=" * 70)
