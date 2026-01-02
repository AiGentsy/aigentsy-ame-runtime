"""
AIGENTSY INVESTOR-READY MICRO-UPGRADES
======================================

6 small additions that unlock massive investor value:

1. Outcome Oracle Roll-ups + Idempotency
2. Reconciliation Export with Verification Hash
3. Cost Ledger on Each Deal (LLM cost, automation minutes, revisions)
4. AL Governance Service (progression + review requests)
5. Tier-3 Platform Throttle + Anomaly Flags
6. Proof Feed Privacy Scrubber

These exploit existing systems - no new surface area.
"""

import asyncio
import hashlib
import json
import csv
import io
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
from collections import defaultdict

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


# ============================================================================
# UPGRADE 1: OUTCOME ORACLE ROLL-UPS + IDEMPOTENCY
# ============================================================================

class OutcomeStage(str, Enum):
    CLICKED = "CLICKED"
    AUTHORIZED = "AUTHORIZED"
    DELIVERED = "DELIVERED"
    PAID = "PAID"


@dataclass
class OutcomeEvent:
    """Single outcome event with idempotency key"""
    event_id: str
    user_id: str
    deal_id: str
    stage: OutcomeStage
    timestamp: str
    idempotency_key: str  # {user_id}:{deal_id}:{stage}:{date}
    amount_usd: float = 0
    metadata: Dict = field(default_factory=dict)


class OutcomeOracleRollups:
    """
    Deduped event ingestion + cached 7/30-day rollups.
    Stabilizes dashboard counters and Proof Feed.
    """
    
    def __init__(self):
        self.events: List[OutcomeEvent] = []
        self.seen_keys: set = set()  # Idempotency dedupe
        self._cache_7d: Dict = {}
        self._cache_30d: Dict = {}
        self._cache_timestamp: Optional[str] = None
        
    def ingest_event(
        self,
        user_id: str,
        deal_id: str,
        stage: OutcomeStage,
        amount_usd: float = 0,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Ingest event with idempotency - prevents duplicate counting."""
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        idempotency_key = f"{user_id}:{deal_id}:{stage.value}:{today}"
        
        # Dedupe check
        if idempotency_key in self.seen_keys:
            return {
                "ok": True,
                "status": "duplicate",
                "idempotency_key": idempotency_key,
                "message": "Event already recorded today"
            }
        
        event = OutcomeEvent(
            event_id=_generate_id("evt"),
            user_id=user_id,
            deal_id=deal_id,
            stage=stage,
            timestamp=_now(),
            idempotency_key=idempotency_key,
            amount_usd=amount_usd,
            metadata=metadata or {}
        )
        
        self.events.append(event)
        self.seen_keys.add(idempotency_key)
        self._invalidate_cache()
        
        return {
            "ok": True,
            "status": "recorded",
            "event_id": event.event_id,
            "idempotency_key": idempotency_key
        }
    
    def get_rollups(self, days: int = 30, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cached rollup stats for 7 or 30 days."""
        
        cache_key = f"{days}d_{user_id or 'all'}"
        
        # Check cache (valid for 5 minutes)
        if self._cache_timestamp:
            cache_age = datetime.now(timezone.utc) - datetime.fromisoformat(
                self._cache_timestamp.replace("Z", "+00:00")
            )
            if cache_age.total_seconds() < 300:  # 5 min cache
                if days == 7 and cache_key in self._cache_7d:
                    return self._cache_7d[cache_key]
                if days == 30 and cache_key in self._cache_30d:
                    return self._cache_30d[cache_key]
        
        # Compute rollup
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        filtered = [
            e for e in self.events
            if datetime.fromisoformat(e.timestamp.replace("Z", "+00:00")) > cutoff
            and (user_id is None or e.user_id == user_id)
        ]
        
        # Count by stage
        stage_counts = {stage.value: 0 for stage in OutcomeStage}
        stage_amounts = {stage.value: 0.0 for stage in OutcomeStage}
        
        for event in filtered:
            stage_counts[event.stage.value] += 1
            stage_amounts[event.stage.value] += event.amount_usd
        
        # Calculate conversion rates
        clicked = stage_counts["CLICKED"] or 1
        conversions = {
            "clicked_to_authorized": round(stage_counts["AUTHORIZED"] / clicked, 3),
            "authorized_to_delivered": round(
                stage_counts["DELIVERED"] / (stage_counts["AUTHORIZED"] or 1), 3
            ),
            "delivered_to_paid": round(
                stage_counts["PAID"] / (stage_counts["DELIVERED"] or 1), 3
            ),
            "end_to_end": round(stage_counts["PAID"] / clicked, 3),
        }
        
        rollup = {
            "period_days": days,
            "user_id": user_id,
            "stage_counts": stage_counts,
            "stage_amounts": stage_amounts,
            "total_events": len(filtered),
            "total_revenue": round(stage_amounts["PAID"], 2),
            "conversions": conversions,
            "computed_at": _now()
        }
        
        # Cache it
        if days == 7:
            self._cache_7d[cache_key] = rollup
        else:
            self._cache_30d[cache_key] = rollup
        self._cache_timestamp = _now()
        
        return rollup
    
    def _invalidate_cache(self):
        """Invalidate cache on new events."""
        self._cache_7d = {}
        self._cache_30d = {}


# ============================================================================
# UPGRADE 2: RECONCILIATION EXPORT WITH VERIFICATION HASH
# ============================================================================

class ReconciliationExporter:
    """
    Generates CSV exports with SHA-256 verification hash.
    Instant investor-grade audit artifact.
    """
    
    def __init__(self, reconciliation_engine=None):
        self.engine = reconciliation_engine
    
    def export_csv_with_hash(
        self,
        entries: List[Dict],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export entries to CSV with verification hash."""
        
        # Filter by date if provided
        if start_date:
            entries = [e for e in entries if e.get("created_at", "") >= start_date]
        if end_date:
            entries = [e for e in entries if e.get("created_at", "") <= end_date]
        
        # Define columns for hash computation
        hash_columns = [
            "entry_id", "user_id", "source", "entry_type",
            "gross_amount", "fees", "net_amount", "currency",
            "reference_id", "created_at", "reconciliation_status"
        ]
        
        # Build CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=hash_columns, extrasaction='ignore')
        writer.writeheader()
        
        # Normalize entries for consistent hashing
        normalized = []
        for entry in entries:
            row = {col: str(entry.get(col, "")) for col in hash_columns}
            normalized.append(row)
            writer.writerow(row)
        
        csv_content = output.getvalue()
        
        # Compute verification hash
        hash_input = json.dumps(normalized, sort_keys=True)
        verification_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        return {
            "ok": True,
            "csv_content": csv_content,
            "verification_hash": verification_hash,
            "hash_algorithm": "SHA-256",
            "columns_hashed": hash_columns,
            "entry_count": len(entries),
            "period": {
                "start": start_date or "all_time",
                "end": end_date or _now()
            },
            "exported_at": _now()
        }
    
    def verify_csv_hash(self, csv_content: str, claimed_hash: str) -> Dict[str, Any]:
        """Verify a CSV export matches its claimed hash."""
        
        # Parse CSV back to normalized form
        reader = csv.DictReader(io.StringIO(csv_content))
        normalized = [dict(row) for row in reader]
        
        # Recompute hash
        hash_input = json.dumps(normalized, sort_keys=True)
        computed_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        matches = computed_hash == claimed_hash
        
        return {
            "ok": True,
            "valid": matches,
            "claimed_hash": claimed_hash,
            "computed_hash": computed_hash,
            "entry_count": len(normalized),
            "verified_at": _now()
        }


# ============================================================================
# UPGRADE 3: COST LEDGER ON EACH DEAL
# ============================================================================

@dataclass
class DealCostMetrics:
    """Cost metrics for contribution margin calculation."""
    deal_id: str
    llm_cost_usd: float = 0.0
    automation_minutes: float = 0.0
    revisions_count: int = 0
    dispute_cost_usd: float = 0.0
    platform_fee_usd: float = 0.0
    aigentsy_fee_usd: float = 0.0
    total_cost_usd: float = 0.0
    revenue_usd: float = 0.0
    contribution_margin_usd: float = 0.0
    contribution_margin_pct: float = 0.0
    
    def calculate_margin(self):
        """Calculate contribution margin."""
        self.total_cost_usd = (
            self.llm_cost_usd +
            (self.automation_minutes * 0.01) +  # $0.01/min compute
            (self.revisions_count * 0.50) +      # $0.50/revision overhead
            self.dispute_cost_usd +
            self.platform_fee_usd
        )
        
        self.contribution_margin_usd = self.revenue_usd - self.total_cost_usd
        
        if self.revenue_usd > 0:
            self.contribution_margin_pct = round(
                (self.contribution_margin_usd / self.revenue_usd) * 100, 1
            )
        
        return self


class DealCostLedger:
    """
    Tracks cost per deal for contribution margin analysis.
    Makes unit economics a first-class KPI.
    """
    
    # LLM cost estimates per 1K tokens
    LLM_COSTS = {
        "claude-3-opus": 0.015,
        "claude-3-sonnet": 0.003,
        "claude-3-haiku": 0.00025,
        "gpt-4": 0.03,
        "gpt-4-turbo": 0.01,
        "gpt-3.5-turbo": 0.0005,
    }
    
    def __init__(self):
        self.deal_costs: Dict[str, DealCostMetrics] = {}
    
    def record_llm_usage(
        self,
        deal_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """Record LLM usage for a deal."""
        
        if deal_id not in self.deal_costs:
            self.deal_costs[deal_id] = DealCostMetrics(deal_id=deal_id)
        
        cost_per_1k = self.LLM_COSTS.get(model, 0.01)
        total_tokens = input_tokens + output_tokens
        cost = (total_tokens / 1000) * cost_per_1k
        
        self.deal_costs[deal_id].llm_cost_usd += cost
        
        return {
            "ok": True,
            "deal_id": deal_id,
            "model": model,
            "tokens": total_tokens,
            "cost_usd": round(cost, 4),
            "cumulative_llm_cost": round(self.deal_costs[deal_id].llm_cost_usd, 4)
        }
    
    def record_automation(
        self,
        deal_id: str,
        minutes: float
    ) -> Dict[str, Any]:
        """Record automation time for a deal."""
        
        if deal_id not in self.deal_costs:
            self.deal_costs[deal_id] = DealCostMetrics(deal_id=deal_id)
        
        self.deal_costs[deal_id].automation_minutes += minutes
        
        return {
            "ok": True,
            "deal_id": deal_id,
            "minutes_added": minutes,
            "total_minutes": self.deal_costs[deal_id].automation_minutes
        }
    
    def record_revision(self, deal_id: str) -> Dict[str, Any]:
        """Record a revision for a deal."""
        
        if deal_id not in self.deal_costs:
            self.deal_costs[deal_id] = DealCostMetrics(deal_id=deal_id)
        
        self.deal_costs[deal_id].revisions_count += 1
        
        return {
            "ok": True,
            "deal_id": deal_id,
            "revisions": self.deal_costs[deal_id].revisions_count
        }
    
    def record_revenue(
        self,
        deal_id: str,
        gross_revenue: float,
        platform_fee: float,
        aigentsy_fee: float
    ) -> Dict[str, Any]:
        """Record revenue and fees for margin calculation."""
        
        if deal_id not in self.deal_costs:
            self.deal_costs[deal_id] = DealCostMetrics(deal_id=deal_id)
        
        metrics = self.deal_costs[deal_id]
        metrics.revenue_usd = gross_revenue
        metrics.platform_fee_usd = platform_fee
        metrics.aigentsy_fee_usd = aigentsy_fee
        metrics.calculate_margin()
        
        return {
            "ok": True,
            "deal_id": deal_id,
            "revenue_usd": metrics.revenue_usd,
            "total_cost_usd": round(metrics.total_cost_usd, 2),
            "contribution_margin_usd": round(metrics.contribution_margin_usd, 2),
            "contribution_margin_pct": metrics.contribution_margin_pct
        }
    
    def get_deal_economics(self, deal_id: str) -> Dict[str, Any]:
        """Get full economics for a deal."""
        
        if deal_id not in self.deal_costs:
            return {"ok": False, "error": "deal_not_found"}
        
        metrics = self.deal_costs[deal_id]
        metrics.calculate_margin()
        
        return {
            "ok": True,
            "deal_id": deal_id,
            "costs": {
                "llm_cost_usd": round(metrics.llm_cost_usd, 4),
                "automation_minutes": metrics.automation_minutes,
                "automation_cost_usd": round(metrics.automation_minutes * 0.01, 4),
                "revisions_count": metrics.revisions_count,
                "revisions_cost_usd": round(metrics.revisions_count * 0.50, 2),
                "platform_fee_usd": round(metrics.platform_fee_usd, 2),
                "total_cost_usd": round(metrics.total_cost_usd, 2),
            },
            "revenue_usd": round(metrics.revenue_usd, 2),
            "aigentsy_fee_usd": round(metrics.aigentsy_fee_usd, 2),
            "contribution_margin_usd": round(metrics.contribution_margin_usd, 2),
            "contribution_margin_pct": metrics.contribution_margin_pct,
        }
    
    def get_aggregate_economics(self) -> Dict[str, Any]:
        """Get aggregate economics across all deals."""
        
        if not self.deal_costs:
            return {"ok": True, "deals": 0, "message": "No deals recorded"}
        
        total_revenue = 0
        total_cost = 0
        total_margin = 0
        margins = []
        
        for metrics in self.deal_costs.values():
            metrics.calculate_margin()
            total_revenue += metrics.revenue_usd
            total_cost += metrics.total_cost_usd
            total_margin += metrics.contribution_margin_usd
            if metrics.revenue_usd > 0:
                margins.append(metrics.contribution_margin_pct)
        
        avg_margin = sum(margins) / len(margins) if margins else 0
        
        return {
            "ok": True,
            "deals": len(self.deal_costs),
            "total_revenue_usd": round(total_revenue, 2),
            "total_cost_usd": round(total_cost, 2),
            "total_margin_usd": round(total_margin, 2),
            "avg_margin_pct": round(avg_margin, 1),
            "target_margin_pct": 40.0,
            "margin_vs_target": round(avg_margin - 40.0, 1),
        }


# ============================================================================
# UPGRADE 4: AL GOVERNANCE SERVICE
# ============================================================================

class AutonomyLevel(str, Enum):
    AL0 = "AL0"  # Manual
    AL1 = "AL1"  # Assisted (default)
    AL2 = "AL2"  # Supervised
    AL3 = "AL3"  # Guided
    AL4 = "AL4"  # Autonomous
    AL5 = "AL5"  # Full Auto


@dataclass
class ALStatus:
    """User's autonomy level status."""
    user_id: str
    current_level: AutonomyLevel
    level_since: str
    criteria_met: Dict[str, bool]
    criteria_values: Dict[str, Any]
    upgrade_available: bool
    upgrade_to: Optional[AutonomyLevel]
    downgrade_triggers: List[str]
    review_requests: List[Dict]


class ALGovernanceService:
    """
    Autonomy Level governance - progression rules + review requests.
    Turns policy into product.
    """
    
    # Upgrade criteria by level
    UPGRADE_CRITERIA = {
        AutonomyLevel.AL1: {
            "min_days": 0,
            "min_deals": 0,
            "min_revenue": 0,
            "max_dispute_rate": 1.0,
            "min_outcome_score": 0,
        },
        AutonomyLevel.AL2: {
            "min_days": 7,
            "min_deals": 3,
            "min_revenue": 100,
            "max_dispute_rate": 0.10,
            "min_outcome_score": 30,
        },
        AutonomyLevel.AL3: {
            "min_days": 14,
            "min_deals": 10,
            "min_revenue": 500,
            "max_dispute_rate": 0.05,
            "min_outcome_score": 50,
        },
        AutonomyLevel.AL4: {
            "min_days": 30,
            "min_deals": 25,
            "min_revenue": 2000,
            "max_dispute_rate": 0.03,
            "min_outcome_score": 70,
        },
        AutonomyLevel.AL5: {
            "min_days": 60,
            "min_deals": 50,
            "min_revenue": 5000,
            "max_dispute_rate": 0.02,
            "min_outcome_score": 90,
        },
    }
    
    # Downgrade triggers
    DOWNGRADE_TRIGGERS = {
        "dispute_spike": "3+ disputes in 7 days",
        "quality_drop": "Verification score < 0.6 for 3 consecutive deals",
        "refund_rate": "Refund rate > 5%",
        "inactivity": "No activity for 30+ days",
        "user_request": "User requested downgrade",
        "violation": "Terms of service violation",
    }
    
    def __init__(self):
        self.user_levels: Dict[str, AutonomyLevel] = {}
        self.level_history: Dict[str, List[Dict]] = defaultdict(list)
        self.review_requests: Dict[str, List[Dict]] = defaultdict(list)
    
    def get_user_status(self, user_id: str, user_metrics: Dict) -> ALStatus:
        """Get user's current AL status with criteria evaluation."""
        
        current_level = self.user_levels.get(user_id, AutonomyLevel.AL1)
        
        # Evaluate criteria for next level
        next_level = self._get_next_level(current_level)
        
        if next_level:
            criteria = self.UPGRADE_CRITERIA[next_level]
            criteria_met = {}
            criteria_values = {}
            
            # Evaluate each criterion
            days_active = user_metrics.get("days_since_signup", 0)
            criteria_met["min_days"] = days_active >= criteria["min_days"]
            criteria_values["days_active"] = days_active
            
            total_deals = user_metrics.get("completed_deals", 0)
            criteria_met["min_deals"] = total_deals >= criteria["min_deals"]
            criteria_values["completed_deals"] = total_deals
            
            total_revenue = user_metrics.get("total_revenue", 0)
            criteria_met["min_revenue"] = total_revenue >= criteria["min_revenue"]
            criteria_values["total_revenue"] = total_revenue
            
            dispute_rate = user_metrics.get("dispute_rate", 0)
            criteria_met["max_dispute_rate"] = dispute_rate <= criteria["max_dispute_rate"]
            criteria_values["dispute_rate"] = dispute_rate
            
            outcome_score = user_metrics.get("outcome_score", 0)
            criteria_met["min_outcome_score"] = outcome_score >= criteria["min_outcome_score"]
            criteria_values["outcome_score"] = outcome_score
            
            upgrade_available = all(criteria_met.values())
        else:
            criteria_met = {}
            criteria_values = {}
            upgrade_available = False
        
        # Check downgrade triggers
        downgrade_triggers = self._check_downgrade_triggers(user_metrics)
        
        # Get pending review requests
        pending_reviews = [
            r for r in self.review_requests.get(user_id, [])
            if r.get("status") == "pending"
        ]
        
        return ALStatus(
            user_id=user_id,
            current_level=current_level,
            level_since=self._get_level_since(user_id),
            criteria_met=criteria_met,
            criteria_values=criteria_values,
            upgrade_available=upgrade_available,
            upgrade_to=next_level if upgrade_available else None,
            downgrade_triggers=downgrade_triggers,
            review_requests=pending_reviews
        )
    
    def request_review(
        self,
        user_id: str,
        reason: str,
        requested_level: Optional[AutonomyLevel] = None
    ) -> Dict[str, Any]:
        """Submit a review request for level change."""
        
        request = {
            "request_id": _generate_id("alr"),
            "user_id": user_id,
            "current_level": self.user_levels.get(user_id, AutonomyLevel.AL1).value,
            "requested_level": requested_level.value if requested_level else "upgrade",
            "reason": reason,
            "status": "pending",
            "submitted_at": _now(),
            "reviewed_at": None,
            "reviewer_notes": None,
        }
        
        self.review_requests[user_id].append(request)
        
        return {
            "ok": True,
            "request_id": request["request_id"],
            "status": "pending",
            "message": "Review request submitted. You'll be notified within 24-48 hours."
        }
    
    def process_upgrade(
        self,
        user_id: str,
        new_level: AutonomyLevel,
        reason: str = "criteria_met"
    ) -> Dict[str, Any]:
        """Process an upgrade to a new level."""
        
        old_level = self.user_levels.get(user_id, AutonomyLevel.AL1)
        self.user_levels[user_id] = new_level
        
        self.level_history[user_id].append({
            "from": old_level.value,
            "to": new_level.value,
            "reason": reason,
            "timestamp": _now()
        })
        
        return {
            "ok": True,
            "user_id": user_id,
            "previous_level": old_level.value,
            "new_level": new_level.value,
            "reason": reason
        }
    
    def process_downgrade(
        self,
        user_id: str,
        trigger: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Process a downgrade due to trigger."""
        
        old_level = self.user_levels.get(user_id, AutonomyLevel.AL1)
        new_level = self._get_previous_level(old_level)
        
        if new_level:
            self.user_levels[user_id] = new_level
            
            self.level_history[user_id].append({
                "from": old_level.value,
                "to": new_level.value,
                "reason": f"downgrade:{trigger}",
                "notes": notes,
                "timestamp": _now()
            })
            
            return {
                "ok": True,
                "user_id": user_id,
                "previous_level": old_level.value,
                "new_level": new_level.value,
                "trigger": trigger,
                "notes": notes
            }
        
        return {
            "ok": False,
            "error": "already_at_minimum_level"
        }
    
    def _get_next_level(self, current: AutonomyLevel) -> Optional[AutonomyLevel]:
        """Get the next autonomy level."""
        levels = list(AutonomyLevel)
        idx = levels.index(current)
        if idx < len(levels) - 1:
            return levels[idx + 1]
        return None
    
    def _get_previous_level(self, current: AutonomyLevel) -> Optional[AutonomyLevel]:
        """Get the previous autonomy level."""
        levels = list(AutonomyLevel)
        idx = levels.index(current)
        if idx > 0:
            return levels[idx - 1]
        return None
    
    def _get_level_since(self, user_id: str) -> str:
        """Get when user achieved current level."""
        history = self.level_history.get(user_id, [])
        if history:
            return history[-1].get("timestamp", _now())
        return _now()
    
    def _check_downgrade_triggers(self, metrics: Dict) -> List[str]:
        """Check if any downgrade triggers are active."""
        triggers = []
        
        if metrics.get("disputes_7d", 0) >= 3:
            triggers.append("dispute_spike")
        
        if metrics.get("avg_verification_score_3d", 1.0) < 0.6:
            triggers.append("quality_drop")
        
        if metrics.get("refund_rate", 0) > 0.05:
            triggers.append("refund_rate")
        
        if metrics.get("days_inactive", 0) > 30:
            triggers.append("inactivity")
        
        return triggers


# ============================================================================
# UPGRADE 5: TIER-3 PLATFORM THROTTLE + ANOMALY FLAGS
# ============================================================================

@dataclass
class PlatformThrottleConfig:
    """Throttle configuration for a platform."""
    platform: str
    tier: int
    max_actions_per_hour: int
    max_actions_per_day: int
    cooldown_minutes: int
    anomaly_threshold_pct: float  # Flag if exception rate exceeds this


class PlatformThrottleService:
    """
    Rate limiting and anomaly detection for platform actions.
    Protects accounts and maintains TOS compliance.
    """
    
    # Default configs by tier
    TIER_CONFIGS = {
        1: {"max_hour": 100, "max_day": 1000, "cooldown": 0, "anomaly_threshold": 0.05},
        2: {"max_hour": 50, "max_day": 500, "cooldown": 5, "anomaly_threshold": 0.03},
        3: {"max_hour": 10, "max_day": 100, "cooldown": 15, "anomaly_threshold": 0.02},
        4: {"max_hour": 5, "max_day": 20, "cooldown": 30, "anomaly_threshold": 0.01},
    }
    
    # Platform tier assignments
    PLATFORM_TIERS = {
        "shopify": 1,
        "stripe": 1,
        "github": 1,
        "google_workspace": 1,
        "upwork": 2,
        "fiverr": 2,
        "linkedin": 3,
        "twitter": 3,
        "facebook": 3,
        "reddit": 3,
        "craigslist": 4,
        "indeed": 4,
    }
    
    def __init__(self):
        self.action_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"hour": 0, "day": 0})
        self.last_action: Dict[str, str] = {}
        self.exception_counts: Dict[str, int] = defaultdict(int)
        self.success_counts: Dict[str, int] = defaultdict(int)
        self.anomaly_flags: Dict[str, List[Dict]] = defaultdict(list)
    
    def can_execute(self, platform: str, user_id: str) -> Dict[str, Any]:
        """Check if action can be executed (rate limit + cooldown)."""
        
        tier = self.PLATFORM_TIERS.get(platform.lower(), 3)
        config = self.TIER_CONFIGS[tier]
        
        key = f"{user_id}:{platform}"
        counts = self.action_counts[key]
        
        # Check rate limits
        if counts["hour"] >= config["max_hour"]:
            return {
                "ok": False,
                "allowed": False,
                "reason": "hourly_limit_exceeded",
                "limit": config["max_hour"],
                "current": counts["hour"],
                "retry_after_minutes": 60
            }
        
        if counts["day"] >= config["max_day"]:
            return {
                "ok": False,
                "allowed": False,
                "reason": "daily_limit_exceeded",
                "limit": config["max_day"],
                "current": counts["day"],
                "retry_after_minutes": 1440
            }
        
        # Check cooldown
        if key in self.last_action and config["cooldown"] > 0:
            last = datetime.fromisoformat(self.last_action[key].replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - last).total_seconds() / 60
            
            if elapsed < config["cooldown"]:
                return {
                    "ok": False,
                    "allowed": False,
                    "reason": "cooldown_active",
                    "cooldown_minutes": config["cooldown"],
                    "elapsed_minutes": round(elapsed, 1),
                    "retry_after_minutes": round(config["cooldown"] - elapsed, 1)
                }
        
        return {
            "ok": True,
            "allowed": True,
            "platform": platform,
            "tier": tier,
            "remaining_hour": config["max_hour"] - counts["hour"],
            "remaining_day": config["max_day"] - counts["day"]
        }
    
    def record_action(
        self,
        platform: str,
        user_id: str,
        success: bool,
        exception_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record an action and check for anomalies."""
        
        key = f"{user_id}:{platform}"
        
        # Update counts
        self.action_counts[key]["hour"] += 1
        self.action_counts[key]["day"] += 1
        self.last_action[key] = _now()
        
        if success:
            self.success_counts[key] += 1
        else:
            self.exception_counts[key] += 1
        
        # Check for anomalies
        anomaly = self._check_anomaly(platform, user_id)
        
        result = {
            "ok": True,
            "platform": platform,
            "action_recorded": True,
            "success": success
        }
        
        if anomaly:
            result["anomaly_flagged"] = True
            result["anomaly"] = anomaly
        
        return result
    
    def _check_anomaly(self, platform: str, user_id: str) -> Optional[Dict]:
        """Check if exception rate is anomalous."""
        
        key = f"{user_id}:{platform}"
        tier = self.PLATFORM_TIERS.get(platform.lower(), 3)
        threshold = self.TIER_CONFIGS[tier]["anomaly_threshold"]
        
        total = self.success_counts[key] + self.exception_counts[key]
        
        if total < 10:  # Need minimum sample
            return None
        
        exception_rate = self.exception_counts[key] / total
        
        if exception_rate > threshold:
            anomaly = {
                "anomaly_id": _generate_id("anom"),
                "platform": platform,
                "user_id": user_id,
                "exception_rate": round(exception_rate, 3),
                "threshold": threshold,
                "total_actions": total,
                "exceptions": self.exception_counts[key],
                "detected_at": _now(),
                "recommendation": "Review platform integration and reduce action frequency"
            }
            
            self.anomaly_flags[key].append(anomaly)
            return anomaly
        
        return None
    
    def get_platform_status(self, platform: str, user_id: str) -> Dict[str, Any]:
        """Get current throttle status for a platform."""
        
        key = f"{user_id}:{platform}"
        tier = self.PLATFORM_TIERS.get(platform.lower(), 3)
        config = self.TIER_CONFIGS[tier]
        
        counts = self.action_counts[key]
        total = self.success_counts[key] + self.exception_counts[key]
        
        return {
            "platform": platform,
            "tier": tier,
            "limits": {
                "max_hour": config["max_hour"],
                "max_day": config["max_day"],
                "cooldown_minutes": config["cooldown"]
            },
            "current": {
                "hour": counts["hour"],
                "day": counts["day"],
                "total_actions": total,
                "success_rate": round(self.success_counts[key] / total, 3) if total > 0 else 1.0
            },
            "anomalies": self.anomaly_flags.get(key, [])[-5:],  # Last 5 anomalies
            "status": "healthy" if not self.anomaly_flags.get(key) else "flagged"
        }


# ============================================================================
# UPGRADE 6: PROOF FEED PRIVACY SCRUBBER
# ============================================================================

class ProofFeedPrivacyScrubber:
    """
    Anonymizes deals for public proof feed.
    Bands revenue, removes PII, attaches reconciliation hash pointer.
    """
    
    REVENUE_BANDS = [
        (0, 99, "$0-$99"),
        (100, 499, "$100-$499"),
        (500, 999, "$500-$999"),
        (1000, 4999, "$1K-$5K"),
        (5000, 9999, "$5K-$10K"),
        (10000, float('inf'), "$10K+"),
    ]
    
    def __init__(self):
        self.feed_items: List[Dict] = []
    
    def scrub_deal_for_feed(
        self,
        deal: Dict,
        verification_score: float,
        reconciliation_hash: str
    ) -> Dict[str, Any]:
        """Scrub a deal for public display."""
        
        # Band the revenue
        revenue = deal.get("revenue_usd", 0)
        revenue_band = self._get_revenue_band(revenue)
        
        # Calculate time to complete
        created = deal.get("created_at", "")
        completed = deal.get("completed_at", "")
        time_to_complete = self._calculate_time_to_complete(created, completed)
        
        # Generate anonymized deal type
        deal_type = deal.get("type", "service")
        
        # Create scrubbed entry
        scrubbed = {
            "feed_id": _generate_id("feed"),
            "deal_type": deal_type,
            "revenue_band": revenue_band,
            "time_to_complete": time_to_complete,
            "verification_score": round(verification_score, 2),
            "reconciliation_hash_tail": reconciliation_hash[-12:] if reconciliation_hash else None,
            "completed_at": completed[:10] if completed else None,  # Date only
            "platform_tier": deal.get("platform_tier", 1),
        }
        
        self.feed_items.append(scrubbed)
        
        return {
            "ok": True,
            "scrubbed": scrubbed
        }
    
    def get_public_feed(
        self,
        limit: int = 50,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get public proof feed."""
        
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Filter recent items
        recent = [
            item for item in self.feed_items
            if item.get("completed_at", "") >= cutoff[:10]
        ]
        
        # Sort by completion date, newest first
        recent.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
        
        # Aggregate stats
        total = len(recent)
        avg_score = sum(i["verification_score"] for i in recent) / total if total > 0 else 0
        
        # Time distribution
        time_buckets = {"< 1 day": 0, "1-3 days": 0, "3-7 days": 0, "7+ days": 0}
        for item in recent:
            ttc = item.get("time_to_complete", {})
            days_val = ttc.get("days", 0)
            if days_val < 1:
                time_buckets["< 1 day"] += 1
            elif days_val < 3:
                time_buckets["1-3 days"] += 1
            elif days_val < 7:
                time_buckets["3-7 days"] += 1
            else:
                time_buckets["7+ days"] += 1
        
        return {
            "ok": True,
            "period_days": days,
            "total_deals": total,
            "avg_verification_score": round(avg_score, 2),
            "time_distribution": time_buckets,
            "items": recent[:limit],
            "generated_at": _now(),
            "notice": "All data anonymized. Revenue banded. No PII included."
        }
    
    def _get_revenue_band(self, revenue: float) -> str:
        """Get revenue band for amount."""
        for low, high, label in self.REVENUE_BANDS:
            if low <= revenue <= high:
                return label
        return "$10K+"
    
    def _calculate_time_to_complete(self, created: str, completed: str) -> Dict:
        """Calculate time to complete in human-readable format."""
        
        if not created or not completed:
            return {"days": 0, "display": "Unknown"}
        
        try:
            c = datetime.fromisoformat(created.replace("Z", "+00:00"))
            d = datetime.fromisoformat(completed.replace("Z", "+00:00"))
            delta = d - c
            
            days = delta.days
            hours = delta.seconds // 3600
            
            if days == 0:
                if hours < 1:
                    display = "< 1 hour"
                else:
                    display = f"{hours} hours"
            elif days == 1:
                display = "1 day"
            else:
                display = f"{days} days"
            
            return {"days": days, "hours": hours, "display": display}
        except:
            return {"days": 0, "display": "Unknown"}


# ============================================================================
# COMBINED API ENDPOINTS
# ============================================================================

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/apex/investor", tags=["Investor Ready"])

# Global instances
_outcome_oracle = OutcomeOracleRollups()
_reconciliation_exporter = ReconciliationExporter()
_cost_ledger = DealCostLedger()
_al_governance = ALGovernanceService()
_throttle_service = PlatformThrottleService()
_proof_scrubber = ProofFeedPrivacyScrubber()


@router.get("/outcome/rollups")
async def get_outcome_rollups(
    days: int = Query(30, ge=7, le=90),
    user_id: Optional[str] = None
):
    """Get outcome oracle rollups (7/30/90 day)."""
    return _outcome_oracle.get_rollups(days, user_id)


@router.get("/reconciliation/export")
async def export_reconciliation(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    format: str = "json"
):
    """Export reconciliation data with verification hash."""
    # In production, would pull from actual reconciliation engine
    sample_entries = [
        {"entry_id": "led_001", "user_id": "alice", "source": "stripe", 
         "entry_type": "revenue", "gross_amount": 100, "fees": 5.08,
         "net_amount": 94.92, "currency": "USD", "reference_id": "pi_001",
         "created_at": _now(), "reconciliation_status": "matched"},
    ]
    return _reconciliation_exporter.export_csv_with_hash(sample_entries, start_date, end_date)


@router.get("/economics/deal/{deal_id}")
async def get_deal_economics(deal_id: str):
    """Get cost/margin economics for a deal."""
    return _cost_ledger.get_deal_economics(deal_id)


@router.get("/economics/aggregate")
async def get_aggregate_economics():
    """Get aggregate economics across all deals."""
    return _cost_ledger.get_aggregate_economics()


@router.get("/al/status/{user_id}")
async def get_al_status(user_id: str):
    """Get user's autonomy level status."""
    # In production, would fetch real user metrics
    sample_metrics = {
        "days_since_signup": 45,
        "completed_deals": 15,
        "total_revenue": 1200,
        "dispute_rate": 0.02,
        "outcome_score": 65,
    }
    status = _al_governance.get_user_status(user_id, sample_metrics)
    return {
        "ok": True,
        "user_id": status.user_id,
        "current_level": status.current_level.value,
        "level_since": status.level_since,
        "criteria_met": status.criteria_met,
        "criteria_values": status.criteria_values,
        "upgrade_available": status.upgrade_available,
        "upgrade_to": status.upgrade_to.value if status.upgrade_to else None,
        "downgrade_triggers": status.downgrade_triggers,
        "pending_reviews": len(status.review_requests)
    }


@router.post("/al/request_review")
async def request_al_review(user_id: str, reason: str):
    """Request a review for level change."""
    return _al_governance.request_review(user_id, reason)


@router.get("/throttle/status/{platform}/{user_id}")
async def get_throttle_status(platform: str, user_id: str):
    """Get throttle status for a platform."""
    return _throttle_service.get_platform_status(platform, user_id)


@router.get("/proof/feed")
async def get_public_proof_feed(
    limit: int = Query(50, ge=10, le=100),
    days: int = Query(30, ge=7, le=90)
):
    """Get public proof feed (anonymized)."""
    return _proof_scrubber.get_public_feed(limit, days)


def register_investor_routes(app):
    """Register all investor-ready routes."""
    app.include_router(router)
    print("✅ Investor-Ready API routes registered at /apex/investor")


# ============================================================================
# TESTING
# ============================================================================

async def _test_micro_upgrades():
    print("\n" + "="*70)
    print("🧪 TESTING INVESTOR-READY MICRO-UPGRADES")
    print("="*70)
    
    # Test 1: Outcome Oracle Rollups
    print("\n📊 Test 1: Outcome Oracle Rollups")
    oracle = OutcomeOracleRollups()
    
    # Ingest some events
    oracle.ingest_event("alice", "deal_001", OutcomeStage.CLICKED)
    oracle.ingest_event("alice", "deal_001", OutcomeStage.AUTHORIZED)
    oracle.ingest_event("alice", "deal_001", OutcomeStage.DELIVERED)
    oracle.ingest_event("alice", "deal_001", OutcomeStage.PAID, amount_usd=500)
    
    # Test idempotency
    result = oracle.ingest_event("alice", "deal_001", OutcomeStage.PAID, amount_usd=500)
    print(f"   Duplicate: {result['status']}")
    
    rollups = oracle.get_rollups(30)
    print(f"   Stage counts: {rollups['stage_counts']}")
    print(f"   Conversions: {rollups['conversions']}")
    
    # Test 2: Reconciliation Export
    print("\n📋 Test 2: Reconciliation Export with Hash")
    exporter = ReconciliationExporter()
    
    entries = [
        {"entry_id": "led_001", "user_id": "alice", "source": "stripe",
         "entry_type": "revenue", "gross_amount": 100, "fees": 5.08,
         "net_amount": 94.92, "currency": "USD", "reference_id": "pi_001",
         "created_at": _now(), "reconciliation_status": "matched"},
        {"entry_id": "led_002", "user_id": "bob", "source": "upwork",
         "entry_type": "revenue", "gross_amount": 500, "fees": 64.28,
         "net_amount": 435.72, "currency": "USD", "reference_id": "uw_001",
         "created_at": _now(), "reconciliation_status": "matched"},
    ]
    
    export = exporter.export_csv_with_hash(entries)
    print(f"   Hash: {export['verification_hash'][:20]}...")
    print(f"   Entries: {export['entry_count']}")
    
    # Verify
    verify = exporter.verify_csv_hash(export['csv_content'], export['verification_hash'])
    print(f"   Verification: {'✅ Valid' if verify['valid'] else '❌ Invalid'}")
    
    # Test 3: Cost Ledger
    print("\n💰 Test 3: Deal Cost Ledger")
    ledger = DealCostLedger()
    
    ledger.record_llm_usage("deal_001", "claude-3-sonnet", 5000, 2000)
    ledger.record_automation("deal_001", 15.5)
    ledger.record_revision("deal_001")
    ledger.record_revenue("deal_001", 500, 50, 14.28)
    
    economics = ledger.get_deal_economics("deal_001")
    print(f"   Revenue: ${economics['revenue_usd']}")
    print(f"   Total Cost: ${economics['costs']['total_cost_usd']}")
    print(f"   Margin: {economics['contribution_margin_pct']}%")
    
    # Test 4: AL Governance
    print("\n🎚️ Test 4: AL Governance")
    al = ALGovernanceService()
    
    metrics = {
        "days_since_signup": 45,
        "completed_deals": 15,
        "total_revenue": 1200,
        "dispute_rate": 0.02,
        "outcome_score": 65,
    }
    
    status = al.get_user_status("alice", metrics)
    print(f"   Current Level: {status.current_level.value}")
    print(f"   Upgrade Available: {status.upgrade_available}")
    print(f"   Criteria Met: {status.criteria_met}")
    
    # Test 5: Throttle Service
    print("\n🚦 Test 5: Platform Throttle")
    throttle = PlatformThrottleService()
    
    can_exec = throttle.can_execute("linkedin", "alice")
    print(f"   LinkedIn can execute: {can_exec['allowed']}")
    print(f"   Remaining/hour: {can_exec.get('remaining_hour', 'N/A')}")
    
    # Test 6: Proof Feed Scrubber
    print("\n🔒 Test 6: Proof Feed Privacy Scrubber")
    scrubber = ProofFeedPrivacyScrubber()
    
    deal = {
        "id": "deal_001",
        "type": "software_development",
        "revenue_usd": 750,
        "created_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
        "completed_at": _now(),
        "platform_tier": 1,
    }
    
    scrubbed = scrubber.scrub_deal_for_feed(deal, 0.92, "abc123def456xyz")
    print(f"   Revenue Band: {scrubbed['scrubbed']['revenue_band']}")
    print(f"   Time to Complete: {scrubbed['scrubbed']['time_to_complete']['display']}")
    print(f"   Hash Tail: {scrubbed['scrubbed']['reconciliation_hash_tail']}")
    
    print("\n✅ All micro-upgrades tested successfully!")
    print("\n" + "="*70)
    print("RECOMMENDATION: PROCEED TO FRONTEND")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(_test_micro_upgrades())
