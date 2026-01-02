"""
CLIENT SUCCESS PREDICTOR
=========================

ML-based prediction of which users will succeed vs churn.

FEATURES:
1. Success Prediction Model - predict user success likelihood
2. Churn Early Warning - detect at-risk users before they leave
3. Intervention Triggers - auto-outreach to struggling users
4. Success Cohort Analysis - what do successful users have in common

INTEGRATES WITH:
- analytics_engine.py (user metrics)
- outcome_oracle_max.py (funnel tracking)
- yield_memory.py (pattern storage)
- aigx_engine.py (engagement signals)

SIGNALS USED FOR PREDICTION:
- Days since signup
- First revenue timing
- Activity frequency
- Job completion rate
- Outcome score trajectory
- Platform diversity
- Feature usage depth
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
from collections import defaultdict
import statistics
import math

# Import existing systems
try:
    from analytics_engine import calculate_agent_metrics, calculate_platform_health
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

try:
    from outcome_oracle_max import get_user_funnel_stats
    OUTCOME_ORACLE_AVAILABLE = True
except ImportError:
    OUTCOME_ORACLE_AVAILABLE = False

try:
    from yield_memory import store_pattern
    YIELD_MEMORY_AVAILABLE = True
except ImportError:
    YIELD_MEMORY_AVAILABLE = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _days_between(date1: str, date2: str) -> int:
    """Calculate days between two ISO dates."""
    try:
        d1 = datetime.fromisoformat(date1.replace("Z", "+00:00"))
        d2 = datetime.fromisoformat(date2.replace("Z", "+00:00"))
        return abs((d2 - d1).days)
    except:
        return 0


def _days_since(date_str: str) -> int:
    """Calculate days since a date."""
    try:
        d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - d).days
    except:
        return 9999


# ============================================================
# CONFIGURATION
# ============================================================

class UserStatus(str, Enum):
    """User status categories"""
    THRIVING = "thriving"          # High engagement, growing revenue
    ACTIVE = "active"              # Regular activity, stable
    AT_RISK = "at_risk"            # Declining engagement
    CHURNING = "churning"          # Very low activity
    CHURNED = "churned"            # No activity for 30+ days
    NEW = "new"                    # Less than 7 days old


class InterventionType(str, Enum):
    """Types of interventions"""
    ONBOARDING_HELP = "onboarding_help"
    FEATURE_EDUCATION = "feature_education"
    SUCCESS_CELEBRATION = "success_celebration"
    REACTIVATION = "reactivation"
    PERSONAL_OUTREACH = "personal_outreach"
    INCENTIVE_OFFER = "incentive_offer"


# Feature weights for success prediction
FEATURE_WEIGHTS = {
    "days_to_first_revenue": -0.15,      # Faster is better (negative weight)
    "total_revenue": 0.20,                # More revenue = success
    "job_completion_rate": 0.25,          # Higher completion = success
    "outcome_score": 0.15,                # Higher score = success
    "activity_frequency": 0.10,           # Regular activity = success
    "platform_diversity": 0.05,           # Using multiple platforms = success
    "feature_depth": 0.05,                # Using more features = success
    "referrals_made": 0.05,               # Making referrals = engaged
}

# Thresholds for status classification
STATUS_THRESHOLDS = {
    "thriving_score": 0.75,
    "active_score": 0.50,
    "at_risk_score": 0.30,
    "churning_score": 0.15,
    "days_inactive_churning": 14,
    "days_inactive_churned": 30,
}

# Intervention triggers
INTERVENTION_TRIGGERS = {
    InterventionType.ONBOARDING_HELP: {
        "condition": "new_user_no_setup",
        "days_since_signup": 3,
        "setup_complete": False,
    },
    InterventionType.FEATURE_EDUCATION: {
        "condition": "low_feature_usage",
        "features_used": 2,
        "days_active": 7,
    },
    InterventionType.SUCCESS_CELEBRATION: {
        "condition": "milestone_reached",
        "revenue_threshold": 100,
    },
    InterventionType.REACTIVATION: {
        "condition": "declining_activity",
        "days_inactive": 7,
        "previous_status": "active",
    },
    InterventionType.PERSONAL_OUTREACH: {
        "condition": "high_value_at_risk",
        "lifetime_value": 500,
        "status": "at_risk",
    },
    InterventionType.INCENTIVE_OFFER: {
        "condition": "churning_recoverable",
        "status": "churning",
        "previous_revenue": 50,
    },
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class UserSignals:
    """Signals extracted from user behavior"""
    user_id: str
    signup_date: str
    last_active: str
    first_revenue_date: Optional[str]
    total_revenue: float
    job_count: int
    completed_jobs: int
    outcome_score: int
    activity_days_30d: int
    platforms_used: List[str]
    features_used: List[str]
    referrals_made: int
    aigx_balance: float
    extracted_at: str = field(default_factory=_now)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SuccessPrediction:
    """Prediction of user success"""
    user_id: str
    success_score: float         # 0-1, higher = more likely to succeed
    status: UserStatus
    risk_factors: List[str]
    success_factors: List[str]
    days_to_churn_estimate: Optional[int]
    recommended_interventions: List[InterventionType]
    feature_scores: Dict[str, float]
    confidence: float
    predicted_at: str = field(default_factory=_now)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "success_score": self.success_score,
            "status": self.status.value,
            "risk_factors": self.risk_factors,
            "success_factors": self.success_factors,
            "days_to_churn_estimate": self.days_to_churn_estimate,
            "recommended_interventions": [i.value for i in self.recommended_interventions],
            "feature_scores": self.feature_scores,
            "confidence": self.confidence,
            "predicted_at": self.predicted_at,
        }


@dataclass
class Intervention:
    """A triggered intervention"""
    intervention_id: str
    user_id: str
    intervention_type: InterventionType
    trigger_reason: str
    priority: int  # 1-5, 5 is highest
    message: str
    action_url: Optional[str]
    triggered_at: str = field(default_factory=_now)
    executed_at: Optional[str] = None
    outcome: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "intervention_id": self.intervention_id,
            "user_id": self.user_id,
            "intervention_type": self.intervention_type.value,
            "trigger_reason": self.trigger_reason,
            "priority": self.priority,
            "message": self.message,
            "action_url": self.action_url,
            "triggered_at": self.triggered_at,
            "executed_at": self.executed_at,
            "outcome": self.outcome,
        }


@dataclass 
class CohortAnalysis:
    """Analysis of user cohorts"""
    cohort_name: str
    user_count: int
    avg_success_score: float
    common_characteristics: Dict[str, Any]
    success_rate: float
    avg_revenue: float
    avg_time_to_first_revenue: float
    top_platforms: List[str]
    top_features: List[str]
    analyzed_at: str = field(default_factory=_now)


# ============================================================
# SUCCESS PREDICTOR ENGINE
# ============================================================

class ClientSuccessPredictor:
    """
    Predicts user success and triggers interventions.
    
    Uses a weighted feature model to score users and predict:
    - Likelihood of success (long-term engagement + revenue)
    - Risk of churn
    - Best interventions to improve outcomes
    """
    
    def __init__(self):
        self.predictions: Dict[str, SuccessPrediction] = {}
        self.interventions: List[Intervention] = []
        self.user_signals_cache: Dict[str, UserSignals] = {}
        
        # Track outcomes to improve model
        self.prediction_outcomes: List[Dict] = []
        
        print("\n" + "="*60)
        print("🎯 CLIENT SUCCESS PREDICTOR INITIALIZED")
        print("="*60)
        print(f"   Analytics Integration: {'✅' if ANALYTICS_AVAILABLE else '❌'}")
        print(f"   Outcome Oracle: {'✅' if OUTCOME_ORACLE_AVAILABLE else '❌'}")
        print(f"   Pattern Learning: {'✅' if YIELD_MEMORY_AVAILABLE else '❌'}")
        print("="*60 + "\n")
    
    
    def extract_user_signals(self, user_data: Dict[str, Any]) -> UserSignals:
        """Extract prediction signals from user data."""
        
        username = user_data.get("username", "unknown")
        
        # Basic dates
        signup_date = user_data.get("created_at") or user_data.get("consent", {}).get("ts", _now())
        last_active = user_data.get("lastActive") or user_data.get("activityTracking", {}).get("lastActive", signup_date)
        
        # Revenue signals
        ownership = user_data.get("ownership", {})
        ledger = ownership.get("ledger", [])
        
        total_revenue = 0
        first_revenue_date = None
        
        for entry in ledger:
            if entry.get("basis") in ["revenue", "transaction_revenue", "intent_settlement"]:
                amount = float(entry.get("amount", 0))
                if amount > 0:
                    total_revenue += amount
                    entry_ts = entry.get("ts", "")
                    if first_revenue_date is None or entry_ts < first_revenue_date:
                        first_revenue_date = entry_ts
        
        # Job signals
        intents = user_data.get("intents", [])
        jobs = user_data.get("jobs", [])
        
        job_count = len(intents) + len(jobs)
        completed_jobs = sum(
            1 for j in intents + jobs 
            if j.get("status") in ["SETTLED", "COMPLETED", "delivered", "paid"]
        )
        
        # Outcome score
        outcome_score = int(user_data.get("outcomeScore", 0))
        
        # Activity signals (last 30 days)
        activity_tracking = user_data.get("activityTracking", {})
        active_days = activity_tracking.get("activeDays", [])
        
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        activity_days_30d = sum(1 for d in active_days if d >= cutoff)
        
        # Platform diversity
        platforms_used = set()
        for intent in intents:
            if intent.get("platform"):
                platforms_used.add(intent["platform"])
        for job in jobs:
            if job.get("platform"):
                platforms_used.add(job["platform"])
        
        # Feature usage
        features_used = []
        if user_data.get("kits"):
            features_used.append("kits")
        if user_data.get("template"):
            features_used.append("template")
        if user_data.get("autoStake_policy", {}).get("enabled"):
            features_used.append("autostake")
        if user_data.get("r3_strategy"):
            features_used.append("r3")
        if user_data.get("growth_campaigns"):
            features_used.append("growth")
        if user_data.get("ocl", {}).get("limit", 0) > 0:
            features_used.append("ocl")
        if user_data.get("jv_proposals"):
            features_used.append("jv")
        
        # Referrals
        referrals = user_data.get("referrals", [])
        referrals_made = len(referrals)
        
        # AIGx balance
        aigx_balance = float(ownership.get("aigx", 0))
        
        signals = UserSignals(
            user_id=username,
            signup_date=signup_date,
            last_active=last_active,
            first_revenue_date=first_revenue_date,
            total_revenue=total_revenue,
            job_count=job_count,
            completed_jobs=completed_jobs,
            outcome_score=outcome_score,
            activity_days_30d=activity_days_30d,
            platforms_used=list(platforms_used),
            features_used=features_used,
            referrals_made=referrals_made,
            aigx_balance=aigx_balance,
        )
        
        self.user_signals_cache[username] = signals
        return signals
    
    
    def predict_success(self, user_data: Dict[str, Any]) -> SuccessPrediction:
        """Predict user success likelihood."""
        
        # Extract signals
        signals = self.extract_user_signals(user_data)
        username = signals.user_id
        
        # Calculate feature scores
        feature_scores = {}
        
        # Days to first revenue (normalize: 0 days = 1.0, 30+ days = 0.0)
        if signals.first_revenue_date:
            days_to_rev = _days_between(signals.signup_date, signals.first_revenue_date)
            feature_scores["days_to_first_revenue"] = max(0, 1 - (days_to_rev / 30))
        else:
            days_since_signup = _days_since(signals.signup_date)
            if days_since_signup > 14:
                feature_scores["days_to_first_revenue"] = 0.0  # Concerning if no revenue after 2 weeks
            else:
                feature_scores["days_to_first_revenue"] = 0.5  # Neutral for new users
        
        # Total revenue (normalize: $0 = 0, $1000+ = 1.0)
        feature_scores["total_revenue"] = min(1.0, signals.total_revenue / 1000)
        
        # Job completion rate
        if signals.job_count > 0:
            feature_scores["job_completion_rate"] = signals.completed_jobs / signals.job_count
        else:
            feature_scores["job_completion_rate"] = 0.5  # Neutral if no jobs
        
        # Outcome score (normalize: 0-100)
        feature_scores["outcome_score"] = signals.outcome_score / 100
        
        # Activity frequency (normalize: 0 days = 0, 20+ days = 1.0)
        feature_scores["activity_frequency"] = min(1.0, signals.activity_days_30d / 20)
        
        # Platform diversity (normalize: 0 = 0, 3+ = 1.0)
        feature_scores["platform_diversity"] = min(1.0, len(signals.platforms_used) / 3)
        
        # Feature depth (normalize: 0 = 0, 5+ = 1.0)
        feature_scores["feature_depth"] = min(1.0, len(signals.features_used) / 5)
        
        # Referrals (normalize: 0 = 0, 3+ = 1.0)
        feature_scores["referrals_made"] = min(1.0, signals.referrals_made / 3)
        
        # Calculate weighted success score
        success_score = 0
        for feature, weight in FEATURE_WEIGHTS.items():
            score = feature_scores.get(feature, 0.5)
            if weight < 0:
                # For negative weights (like days_to_first_revenue), invert
                success_score += abs(weight) * score
            else:
                success_score += weight * score
        
        # Normalize to 0-1
        success_score = max(0, min(1, success_score))
        
        # Determine status
        days_inactive = _days_since(signals.last_active)
        days_since_signup = _days_since(signals.signup_date)
        
        if days_since_signup < 7:
            status = UserStatus.NEW
        elif days_inactive >= STATUS_THRESHOLDS["days_inactive_churned"]:
            status = UserStatus.CHURNED
        elif days_inactive >= STATUS_THRESHOLDS["days_inactive_churning"]:
            status = UserStatus.CHURNING
        elif success_score >= STATUS_THRESHOLDS["thriving_score"]:
            status = UserStatus.THRIVING
        elif success_score >= STATUS_THRESHOLDS["active_score"]:
            status = UserStatus.ACTIVE
        elif success_score >= STATUS_THRESHOLDS["at_risk_score"]:
            status = UserStatus.AT_RISK
        else:
            status = UserStatus.CHURNING
        
        # Identify risk factors
        risk_factors = []
        if feature_scores["days_to_first_revenue"] < 0.3:
            risk_factors.append("Slow to first revenue")
        if feature_scores["activity_frequency"] < 0.3:
            risk_factors.append("Low activity frequency")
        if feature_scores["job_completion_rate"] < 0.5:
            risk_factors.append("Low job completion rate")
        if feature_scores["feature_depth"] < 0.2:
            risk_factors.append("Limited feature usage")
        if days_inactive > 7:
            risk_factors.append(f"Inactive for {days_inactive} days")
        
        # Identify success factors
        success_factors = []
        if feature_scores["total_revenue"] > 0.5:
            success_factors.append("Strong revenue generation")
        if feature_scores["outcome_score"] > 0.7:
            success_factors.append("High outcome score")
        if feature_scores["job_completion_rate"] > 0.8:
            success_factors.append("Excellent completion rate")
        if feature_scores["platform_diversity"] > 0.6:
            success_factors.append("Multi-platform presence")
        if feature_scores["referrals_made"] > 0:
            success_factors.append("Active referrer")
        
        # Estimate days to churn
        days_to_churn = None
        if status in [UserStatus.AT_RISK, UserStatus.CHURNING]:
            # Simple linear estimate based on activity decline
            if signals.activity_days_30d > 0:
                days_to_churn = int(30 / (1 + (30 - signals.activity_days_30d)))
            else:
                days_to_churn = 7
        
        # Recommend interventions
        interventions = self._recommend_interventions(signals, status, success_score)
        
        # Calculate confidence (more data = higher confidence)
        confidence = 0.5
        if signals.job_count > 5:
            confidence += 0.15
        if days_since_signup > 30:
            confidence += 0.15
        if signals.total_revenue > 0:
            confidence += 0.10
        if signals.activity_days_30d > 10:
            confidence += 0.10
        confidence = min(0.95, confidence)
        
        prediction = SuccessPrediction(
            user_id=username,
            success_score=round(success_score, 3),
            status=status,
            risk_factors=risk_factors,
            success_factors=success_factors,
            days_to_churn_estimate=days_to_churn,
            recommended_interventions=interventions,
            feature_scores={k: round(v, 3) for k, v in feature_scores.items()},
            confidence=round(confidence, 2),
        )
        
        self.predictions[username] = prediction
        return prediction
    
    
    def _recommend_interventions(
        self,
        signals: UserSignals,
        status: UserStatus,
        success_score: float
    ) -> List[InterventionType]:
        """Recommend interventions based on user state."""
        
        interventions = []
        days_since_signup = _days_since(signals.signup_date)
        days_inactive = _days_since(signals.last_active)
        
        # New user without setup
        if status == UserStatus.NEW and len(signals.features_used) < 2:
            interventions.append(InterventionType.ONBOARDING_HELP)
        
        # Low feature usage
        if len(signals.features_used) < 3 and days_since_signup > 7:
            interventions.append(InterventionType.FEATURE_EDUCATION)
        
        # First revenue milestone
        if signals.total_revenue >= 100 and signals.total_revenue < 150:
            interventions.append(InterventionType.SUCCESS_CELEBRATION)
        
        # Declining activity
        if status == UserStatus.AT_RISK and days_inactive > 7:
            interventions.append(InterventionType.REACTIVATION)
        
        # High value at risk
        if status == UserStatus.AT_RISK and signals.total_revenue > 500:
            interventions.append(InterventionType.PERSONAL_OUTREACH)
        
        # Churning but recoverable
        if status == UserStatus.CHURNING and signals.total_revenue > 50:
            interventions.append(InterventionType.INCENTIVE_OFFER)
        
        return interventions[:3]  # Max 3 interventions
    
    
    def trigger_intervention(
        self,
        user_id: str,
        intervention_type: InterventionType,
        trigger_reason: str
    ) -> Intervention:
        """Create and queue an intervention."""
        
        # Generate appropriate message
        messages = {
            InterventionType.ONBOARDING_HELP: 
                "Need help getting started? Let's set up your first opportunity together!",
            InterventionType.FEATURE_EDUCATION:
                "Did you know you can earn more with our advanced features? Let me show you.",
            InterventionType.SUCCESS_CELEBRATION:
                "Congratulations on your progress! You've hit a milestone worth celebrating! 🎉",
            InterventionType.REACTIVATION:
                "We miss you! There are new opportunities waiting for you.",
            InterventionType.PERSONAL_OUTREACH:
                "I noticed you might need some help. Can we chat about how to get you back on track?",
            InterventionType.INCENTIVE_OFFER:
                "Here's a special offer to help you get back in action: bonus AIGx on your next job!",
        }
        
        priorities = {
            InterventionType.PERSONAL_OUTREACH: 5,
            InterventionType.INCENTIVE_OFFER: 4,
            InterventionType.REACTIVATION: 3,
            InterventionType.SUCCESS_CELEBRATION: 3,
            InterventionType.FEATURE_EDUCATION: 2,
            InterventionType.ONBOARDING_HELP: 2,
        }
        
        intervention = Intervention(
            intervention_id=_generate_id("int"),
            user_id=user_id,
            intervention_type=intervention_type,
            trigger_reason=trigger_reason,
            priority=priorities.get(intervention_type, 2),
            message=messages.get(intervention_type, "We're here to help!"),
            action_url=f"/dashboard/support?user={user_id}",
        )
        
        self.interventions.append(intervention)
        return intervention
    
    
    def execute_intervention(
        self,
        intervention_id: str,
        outcome: str = "sent"
    ) -> Dict[str, Any]:
        """Mark intervention as executed."""
        
        for intervention in self.interventions:
            if intervention.intervention_id == intervention_id:
                intervention.executed_at = _now()
                intervention.outcome = outcome
                return {
                    "ok": True,
                    "intervention_id": intervention_id,
                    "outcome": outcome,
                }
        
        return {"ok": False, "error": "intervention_not_found"}
    
    
    def analyze_cohort(
        self,
        users: List[Dict[str, Any]],
        cohort_name: str = "all_users"
    ) -> CohortAnalysis:
        """Analyze a cohort of users to find success patterns."""
        
        if not users:
            return CohortAnalysis(
                cohort_name=cohort_name,
                user_count=0,
                avg_success_score=0,
                common_characteristics={},
                success_rate=0,
                avg_revenue=0,
                avg_time_to_first_revenue=0,
                top_platforms=[],
                top_features=[],
            )
        
        # Predict success for all users
        predictions = [self.predict_success(u) for u in users]
        signals = [self.extract_user_signals(u) for u in users]
        
        # Calculate metrics
        success_scores = [p.success_score for p in predictions]
        avg_success_score = statistics.mean(success_scores)
        
        successful_users = [p for p in predictions if p.status in [UserStatus.THRIVING, UserStatus.ACTIVE]]
        success_rate = len(successful_users) / len(predictions)
        
        revenues = [s.total_revenue for s in signals]
        avg_revenue = statistics.mean(revenues) if revenues else 0
        
        # Time to first revenue
        times_to_revenue = []
        for s in signals:
            if s.first_revenue_date:
                days = _days_between(s.signup_date, s.first_revenue_date)
                times_to_revenue.append(days)
        avg_time_to_first_revenue = statistics.mean(times_to_revenue) if times_to_revenue else 0
        
        # Top platforms
        platform_counts = defaultdict(int)
        for s in signals:
            for p in s.platforms_used:
                platform_counts[p] += 1
        top_platforms = sorted(platform_counts.keys(), key=lambda x: platform_counts[x], reverse=True)[:5]
        
        # Top features
        feature_counts = defaultdict(int)
        for s in signals:
            for f in s.features_used:
                feature_counts[f] += 1
        top_features = sorted(feature_counts.keys(), key=lambda x: feature_counts[x], reverse=True)[:5]
        
        # Common characteristics of successful users
        successful_signals = [s for s, p in zip(signals, predictions) if p.status == UserStatus.THRIVING]
        
        common_characteristics = {}
        if successful_signals:
            common_characteristics = {
                "avg_outcome_score": round(statistics.mean([s.outcome_score for s in successful_signals]), 1),
                "avg_features_used": round(statistics.mean([len(s.features_used) for s in successful_signals]), 1),
                "avg_platforms_used": round(statistics.mean([len(s.platforms_used) for s in successful_signals]), 1),
                "avg_activity_days": round(statistics.mean([s.activity_days_30d for s in successful_signals]), 1),
            }
        
        return CohortAnalysis(
            cohort_name=cohort_name,
            user_count=len(users),
            avg_success_score=round(avg_success_score, 3),
            common_characteristics=common_characteristics,
            success_rate=round(success_rate, 3),
            avg_revenue=round(avg_revenue, 2),
            avg_time_to_first_revenue=round(avg_time_to_first_revenue, 1),
            top_platforms=top_platforms,
            top_features=top_features,
        )
    
    
    def get_at_risk_users(self) -> List[SuccessPrediction]:
        """Get all at-risk users sorted by urgency."""
        
        at_risk = [
            p for p in self.predictions.values()
            if p.status in [UserStatus.AT_RISK, UserStatus.CHURNING]
        ]
        
        # Sort by success score (lowest first = most urgent)
        at_risk.sort(key=lambda p: p.success_score)
        
        return at_risk
    
    
    def get_pending_interventions(self) -> List[Intervention]:
        """Get pending interventions sorted by priority."""
        
        pending = [i for i in self.interventions if i.executed_at is None]
        pending.sort(key=lambda i: i.priority, reverse=True)
        
        return pending
    
    
    def get_predictor_stats(self) -> Dict[str, Any]:
        """Get predictor statistics."""
        
        if not self.predictions:
            return {"total_predictions": 0}
        
        status_counts = defaultdict(int)
        for p in self.predictions.values():
            status_counts[p.status.value] += 1
        
        avg_score = statistics.mean([p.success_score for p in self.predictions.values()])
        
        return {
            "total_predictions": len(self.predictions),
            "status_distribution": dict(status_counts),
            "avg_success_score": round(avg_score, 3),
            "at_risk_count": status_counts.get(UserStatus.AT_RISK.value, 0),
            "churning_count": status_counts.get(UserStatus.CHURNING.value, 0),
            "pending_interventions": len(self.get_pending_interventions()),
            "total_interventions": len(self.interventions),
        }


# ============================================================
# INTEGRATION FUNCTIONS
# ============================================================

_SUCCESS_PREDICTOR: Optional[ClientSuccessPredictor] = None


def get_success_predictor() -> ClientSuccessPredictor:
    """Get or create global success predictor."""
    global _SUCCESS_PREDICTOR
    if _SUCCESS_PREDICTOR is None:
        _SUCCESS_PREDICTOR = ClientSuccessPredictor()
    return _SUCCESS_PREDICTOR


async def predict_user_success(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main integration function - predict user success."""
    predictor = get_success_predictor()
    prediction = predictor.predict_success(user_data)
    
    return {
        "ok": True,
        "user_id": prediction.user_id,
        "success_score": prediction.success_score,
        "status": prediction.status.value,
        "risk_factors": prediction.risk_factors,
        "success_factors": prediction.success_factors,
        "days_to_churn_estimate": prediction.days_to_churn_estimate,
        "recommended_interventions": [i.value for i in prediction.recommended_interventions],
        "confidence": prediction.confidence,
        "prediction": prediction.to_dict(),
    }


async def get_users_needing_intervention() -> Dict[str, Any]:
    """Get users that need intervention."""
    predictor = get_success_predictor()
    
    at_risk = predictor.get_at_risk_users()
    pending = predictor.get_pending_interventions()
    
    return {
        "ok": True,
        "at_risk_users": [p.to_dict() for p in at_risk[:20]],
        "pending_interventions": [i.to_dict() for i in pending[:20]],
        "stats": predictor.get_predictor_stats(),
    }


# ============================================================
# TESTING
# ============================================================

async def _test_success_predictor():
    print("\n" + "="*60)
    print("🧪 TESTING CLIENT SUCCESS PREDICTOR")
    print("="*60)
    
    predictor = get_success_predictor()
    
    # Test user 1: Thriving user
    print("\n👤 Test 1: Thriving user")
    user1 = {
        "username": "alice_thriving",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=60)).isoformat(),
        "lastActive": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "outcomeScore": 85,
        "ownership": {
            "aigx": 500,
            "ledger": [
                {"ts": (datetime.now(timezone.utc) - timedelta(days=55)).isoformat(), "amount": 200, "basis": "revenue"},
                {"ts": (datetime.now(timezone.utc) - timedelta(days=40)).isoformat(), "amount": 300, "basis": "revenue"},
                {"ts": (datetime.now(timezone.utc) - timedelta(days=20)).isoformat(), "amount": 500, "basis": "revenue"},
            ]
        },
        "intents": [
            {"platform": "upwork", "status": "SETTLED"},
            {"platform": "fiverr", "status": "SETTLED"},
            {"platform": "github", "status": "SETTLED"},
        ],
        "activityTracking": {
            "activeDays": [(datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(25)]
        },
        "kits": {"template": True},
        "template": "saas",
        "autoStake_policy": {"enabled": True},
        "referrals": [{"id": "ref1"}, {"id": "ref2"}],
    }
    
    pred1 = predictor.predict_success(user1)
    print(f"   Score: {pred1.success_score:.2f}")
    print(f"   Status: {pred1.status.value}")
    print(f"   Success Factors: {pred1.success_factors}")
    
    # Test user 2: At-risk user
    print("\n👤 Test 2: At-risk user")
    user2 = {
        "username": "bob_atrisk",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat(),
        "lastActive": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        "outcomeScore": 30,
        "ownership": {
            "aigx": 50,
            "ledger": [
                {"ts": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(), "amount": 100, "basis": "revenue"},
            ]
        },
        "intents": [
            {"platform": "upwork", "status": "SETTLED"},
            {"platform": "upwork", "status": "CANCELLED"},
        ],
        "activityTracking": {
            "activeDays": [(datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10, 15)]
        },
    }
    
    pred2 = predictor.predict_success(user2)
    print(f"   Score: {pred2.success_score:.2f}")
    print(f"   Status: {pred2.status.value}")
    print(f"   Risk Factors: {pred2.risk_factors}")
    print(f"   Interventions: {[i.value for i in pred2.recommended_interventions]}")
    
    # Test user 3: New user
    print("\n👤 Test 3: New user")
    user3 = {
        "username": "charlie_new",
        "created_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
        "lastActive": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        "outcomeScore": 0,
        "ownership": {"aigx": 10, "ledger": []},
        "intents": [],
        "activityTracking": {
            "activeDays": [(datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]
        },
    }
    
    pred3 = predictor.predict_success(user3)
    print(f"   Score: {pred3.success_score:.2f}")
    print(f"   Status: {pred3.status.value}")
    print(f"   Interventions: {[i.value for i in pred3.recommended_interventions]}")
    
    # Test cohort analysis
    print("\n📊 Testing cohort analysis...")
    cohort = predictor.analyze_cohort([user1, user2, user3], "test_cohort")
    print(f"   Users: {cohort.user_count}")
    print(f"   Avg Success Score: {cohort.avg_success_score:.2f}")
    print(f"   Success Rate: {cohort.success_rate:.0%}")
    print(f"   Avg Revenue: ${cohort.avg_revenue:.2f}")
    
    # Test intervention triggering
    print("\n🎯 Testing interventions...")
    intervention = predictor.trigger_intervention(
        "bob_atrisk",
        InterventionType.REACTIVATION,
        "User inactive for 10 days"
    )
    print(f"   Created: {intervention.intervention_type.value}")
    print(f"   Priority: {intervention.priority}")
    print(f"   Message: {intervention.message}")
    
    # Get stats
    print("\n📈 Predictor Stats:")
    stats = predictor.get_predictor_stats()
    print(f"   Total Predictions: {stats['total_predictions']}")
    print(f"   Status Distribution: {stats['status_distribution']}")
    print(f"   At-Risk Count: {stats['at_risk_count']}")
    
    print("\n✅ Success predictor tests completed!")


if __name__ == "__main__":
    asyncio.run(_test_success_predictor())
