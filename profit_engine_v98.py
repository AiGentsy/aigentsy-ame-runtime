# profit_engine_v98.py
"""
🏦 AIGENTSY PROFIT ENGINE v98
==============================

ADDS ONLY WHAT'S MISSING - Integrates with:
- proof_pipe.py (Proof-Before-Pay ✅)
- real_signal_ingestion.py (Signal Detection ✅)  
- r3_router_UPGRADED.py (ROI Prediction ✅)
- r3_autopilot.py (Budget Allocation ✅)

THIS FILE ADDS:
1. ROI Kill Switch - Stop campaigns when ROI dips below threshold
2. Unified Idempotency - Single dedupe key across entire pipeline
3. Strict Ownership - Deterministic executor assignment (no races)
4. Backpressure + Priorities - Reserved slots for money-critical paths
5. Pricing Bandit - Thompson sampling across strategies
6. Recovery Cadence - T+15m / T+23h / T+3d sequence
7. Experiment Factory - Auto-create/retire 10 experiments per segment

USAGE:
    from profit_engine_v98 import include_profit_engine
    include_profit_engine(app)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from enum import Enum
import hashlib
import random
import uuid

router = APIRouter(tags=["Profit Engine v98"])


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION - THE GATES
# ═══════════════════════════════════════════════════════════════════════════════

class ProfitGates:
    """Day-1 suggested gates - tune based on actual performance"""
    ROI_GATE = 1.6           # Min ROI to START a campaign
    ROI_KILL = 1.2           # KILL campaign if ROI drops below
    GROSS_MARGIN_MIN = 0.55  # 55% minimum gross margin
    RECOVERY_RATE_MIN = 0.07 # 7% cart recovery target
    AUTO_CLOSE_MIN = 0.18    # 18% auto-close rate
    TIME_TO_CASH_MAX = 7     # Max 7 days to cash
    EXPERIMENT_WIN_RATE_MIN = 0.15


# ═══════════════════════════════════════════════════════════════════════════════
# IN-MEMORY STORES (Production: Redis with TTL)
# ═══════════════════════════════════════════════════════════════════════════════

_idempotency_cache: Dict[str, Dict] = {}
_ownership_registry: Dict[str, Dict] = {}
_campaign_tracker: Dict[str, Dict] = {}
_pricing_bandits: Dict[str, Dict] = {}
_recovery_queue: List[Dict] = []
_experiments: Dict[str, Dict] = {}
_slot_usage = {"critical": 0, "high": 0, "normal": 0, "low": 0}
_slot_limits = {"critical": 10, "high": 20, "normal": 50, "low": 20}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ROI KILL SWITCH (Extends r3_router/r3_autopilot)
# ═══════════════════════════════════════════════════════════════════════════════

class CampaignUpdate(BaseModel):
    campaign_id: str
    actual_revenue: float
    actual_cost: float

@router.post("/r3/campaign/start")
async def start_campaign(campaign_id: str, predicted_roi: float, budget: float):
    """
    Start tracking a campaign. Only allows start if predicted ROI >= gate.
    Integrates with r3_autopilot predictions.
    """
    if predicted_roi < ProfitGates.ROI_GATE:
        return {
            "ok": False,
            "started": False,
            "reason": f"Predicted ROI {predicted_roi:.2f} < gate {ProfitGates.ROI_GATE}",
            "action": "SKIP"
        }
    
    _campaign_tracker[campaign_id] = {
        "campaign_id": campaign_id,
        "predicted_roi": predicted_roi,
        "budget": budget,
        "actual_revenue": 0,
        "actual_cost": 0,
        "rolling_roi": 0,
        "status": "active",
        "started_at": datetime.utcnow().isoformat(),
        "checks": []
    }
    
    return {"ok": True, "started": True, "campaign_id": campaign_id}


@router.post("/r3/campaign/update")
async def update_campaign(update: CampaignUpdate):
    """
    Update campaign with actual performance. Kill if ROI drops below threshold.
    """
    if update.campaign_id not in _campaign_tracker:
        return {"ok": False, "error": "Campaign not found"}
    
    campaign = _campaign_tracker[update.campaign_id]
    
    if campaign["status"] == "killed":
        return {"ok": False, "error": "Campaign already killed", "killed_at": campaign.get("killed_at")}
    
    # Update actuals
    campaign["actual_revenue"] = update.actual_revenue
    campaign["actual_cost"] = update.actual_cost
    
    # Calculate rolling ROI
    if update.actual_cost > 0:
        rolling_roi = update.actual_revenue / update.actual_cost
        campaign["rolling_roi"] = round(rolling_roi, 3)
        
        # Check kill threshold
        if rolling_roi < ProfitGates.ROI_KILL:
            campaign["status"] = "killed"
            campaign["killed_at"] = datetime.utcnow().isoformat()
            campaign["kill_reason"] = f"ROI {rolling_roi:.2f} < kill threshold {ProfitGates.ROI_KILL}"
            
            return {
                "ok": True,
                "action": "KILLED",
                "rolling_roi": rolling_roi,
                "kill_threshold": ProfitGates.ROI_KILL,
                "reason": campaign["kill_reason"]
            }
    
    campaign["checks"].append({
        "ts": datetime.utcnow().isoformat(),
        "revenue": update.actual_revenue,
        "cost": update.actual_cost,
        "roi": campaign["rolling_roi"]
    })
    
    return {
        "ok": True,
        "action": "CONTINUE",
        "rolling_roi": campaign["rolling_roi"],
        "status": campaign["status"]
    }


@router.get("/r3/campaigns/active")
async def get_active_campaigns():
    """Get all active campaigns with their ROI status"""
    active = [c for c in _campaign_tracker.values() if c["status"] == "active"]
    killed = [c for c in _campaign_tracker.values() if c["status"] == "killed"]
    
    return {
        "ok": True,
        "active_count": len(active),
        "killed_count": len(killed),
        "active": active,
        "gates": {"roi_gate": ProfitGates.ROI_GATE, "roi_kill": ProfitGates.ROI_KILL}
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. UNIFIED IDEMPOTENCY (Single key across pipeline)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_idempotency_key(platform: str, opp_id: str, stage: str, day: str = None) -> str:
    """
    Generate deterministic idempotency key.
    sha256(platform|opp_id|stage|day)[:32]
    """
    if day is None:
        day = datetime.utcnow().strftime("%Y-%m-%d")
    raw = f"{platform}|{opp_id}|{stage}|{day}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@router.post("/idempotency/check")
async def check_idempotency(platform: str, opp_id: str, stage: str):
    """
    Check if this operation was already processed today.
    Use at: discovery → bidding → fulfillment → invoicing
    """
    key = generate_idempotency_key(platform, opp_id, stage)
    
    if key in _idempotency_cache:
        cached = _idempotency_cache[key]
        return {
            "ok": True,
            "is_duplicate": True,
            "idempotency_key": key,
            "original_stage": cached.get("stage"),
            "original_ts": cached.get("ts"),
            "action": "DROP"
        }
    
    return {
        "ok": True,
        "is_duplicate": False,
        "idempotency_key": key,
        "action": "PROCESS"
    }


@router.post("/idempotency/record")
async def record_idempotency(platform: str, opp_id: str, stage: str, result: Dict[str, Any] = None):
    """Record that this operation was processed"""
    key = generate_idempotency_key(platform, opp_id, stage)
    
    _idempotency_cache[key] = {
        "key": key,
        "platform": platform,
        "opp_id": opp_id,
        "stage": stage,
        "result": result,
        "ts": datetime.utcnow().isoformat()
    }
    
    return {"ok": True, "recorded": key}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. STRICT OWNERSHIP (Deterministic assignment - no races)
# ═══════════════════════════════════════════════════════════════════════════════

EXECUTOR_POOL = ["exec_alpha", "exec_beta", "exec_gamma", "exec_delta", "exec_epsilon"]

@router.post("/ownership/assign")
async def assign_ownership(opportunity_id: str):
    """
    Deterministically assign opportunity to exactly ONE executor.
    Consistent hash ensures same opp always goes to same executor.
    """
    # Consistent hash
    hash_int = int(hashlib.md5(opportunity_id.encode()).hexdigest(), 16)
    executor_idx = hash_int % len(EXECUTOR_POOL)
    executor = EXECUTOR_POOL[executor_idx]
    
    return {
        "ok": True,
        "opportunity_id": opportunity_id,
        "assigned_executor": executor,
        "hash_bucket": executor_idx
    }


@router.post("/ownership/claim")
async def claim_ownership(opportunity_id: str, executor_id: str):
    """
    Executor claims ownership. Rejects if already claimed by another.
    """
    if opportunity_id in _ownership_registry:
        existing = _ownership_registry[opportunity_id]
        if existing["executor"] != executor_id:
            return {
                "ok": False,
                "claimed": False,
                "reason": f"Already owned by {existing['executor']}",
                "claimed_at": existing["ts"]
            }
        return {"ok": True, "claimed": True, "reason": "Already yours"}
    
    _ownership_registry[opportunity_id] = {
        "executor": executor_id,
        "ts": datetime.utcnow().isoformat()
    }
    
    return {"ok": True, "claimed": True, "executor": executor_id}


@router.post("/ownership/release")
async def release_ownership(opportunity_id: str, executor_id: str):
    """Release ownership after completion"""
    if opportunity_id in _ownership_registry:
        if _ownership_registry[opportunity_id]["executor"] == executor_id:
            del _ownership_registry[opportunity_id]
            return {"ok": True, "released": True}
    return {"ok": False, "released": False, "reason": "Not owner"}


# ═══════════════════════════════════════════════════════════════════════════════
# 4. BACKPRESSURE + PRIORITIES
# ═══════════════════════════════════════════════════════════════════════════════

class Priority(str, Enum):
    CRITICAL = "critical"  # recovery, payments, escrow
    HIGH = "high"          # fulfillment, invoicing
    NORMAL = "normal"      # discovery, bidding
    LOW = "low"            # analytics, reporting

@router.post("/backpressure/request")
async def request_slot(task_id: str, priority: str = "normal"):
    """
    Request a runtime slot. Money-critical paths get reserved capacity.
    """
    if priority not in _slot_limits:
        priority = "normal"
    
    if _slot_usage[priority] >= _slot_limits[priority]:
        return {
            "ok": True,
            "granted": False,
            "queued": True,
            "reason": f"No {priority} slots ({_slot_usage[priority]}/{_slot_limits[priority]})",
            "retry_after_ms": 1000
        }
    
    _slot_usage[priority] += 1
    
    return {
        "ok": True,
        "granted": True,
        "task_id": task_id,
        "priority": priority,
        "slots_remaining": _slot_limits[priority] - _slot_usage[priority]
    }


@router.post("/backpressure/release")
async def release_slot(task_id: str, priority: str = "normal"):
    """Release slot when task completes"""
    if priority in _slot_usage and _slot_usage[priority] > 0:
        _slot_usage[priority] -= 1
    return {"ok": True, "released": True}


@router.get("/backpressure/status")
async def backpressure_status():
    """Get current slot utilization"""
    return {
        "ok": True,
        "slots": {
            p: {"used": _slot_usage[p], "limit": _slot_limits[p], "available": _slot_limits[p] - _slot_usage[p]}
            for p in _slot_limits
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PRICING BANDIT (Thompson Sampling)
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_STRATEGIES = ["baseline", "value_based", "surge", "discount"]

def _get_or_create_bandit(segment: str) -> Dict:
    """Get or create bandit for a segment"""
    if segment not in _pricing_bandits:
        _pricing_bandits[segment] = {
            strategy: {"alpha": 1, "beta": 1, "revenue": 0, "trials": 0}
            for strategy in DEFAULT_STRATEGIES
        }
    return _pricing_bandits[segment]


@router.post("/pricing/bandit/select")
async def bandit_select(segment: str = "default"):
    """
    Thompson Sampling to select pricing strategy.
    Returns highest-sampled strategy.
    """
    bandit = _get_or_create_bandit(segment)
    
    samples = {}
    for strategy, stats in bandit.items():
        # Thompson: sample from Beta(alpha, beta)
        sample = random.betavariate(stats["alpha"], stats["beta"])
        samples[strategy] = sample
    
    winner = max(samples, key=samples.get)
    
    return {
        "ok": True,
        "segment": segment,
        "selected": winner,
        "confidence": round(samples[winner], 3),
        "all_samples": {k: round(v, 3) for k, v in samples.items()}
    }


@router.post("/pricing/bandit/update")
async def bandit_update(segment: str, strategy: str, converted: bool, revenue: float = 0):
    """
    Update bandit with outcome.
    converted=True → increment alpha (success)
    converted=False → increment beta (failure)
    """
    bandit = _get_or_create_bandit(segment)
    
    if strategy not in bandit:
        return {"ok": False, "error": f"Unknown strategy: {strategy}"}
    
    stats = bandit[strategy]
    stats["trials"] += 1
    stats["revenue"] += revenue
    
    if converted:
        stats["alpha"] += 1
    else:
        stats["beta"] += 1
    
    win_rate = stats["alpha"] / (stats["alpha"] + stats["beta"])
    
    return {
        "ok": True,
        "segment": segment,
        "strategy": strategy,
        "win_rate": round(win_rate, 3),
        "trials": stats["trials"],
        "total_revenue": stats["revenue"]
    }


@router.get("/pricing/bandit/leaderboard")
async def bandit_leaderboard(segment: str = "default"):
    """Get strategy performance leaderboard"""
    bandit = _get_or_create_bandit(segment)
    
    leaderboard = []
    for strategy, stats in bandit.items():
        win_rate = stats["alpha"] / (stats["alpha"] + stats["beta"])
        leaderboard.append({
            "strategy": strategy,
            "win_rate": round(win_rate, 3),
            "trials": stats["trials"],
            "revenue": stats["revenue"]
        })
    
    leaderboard.sort(key=lambda x: x["win_rate"], reverse=True)
    
    return {"ok": True, "segment": segment, "leaderboard": leaderboard}


# ═══════════════════════════════════════════════════════════════════════════════
# 6. RECOVERY CADENCE (T+15m / T+23h / T+3d)
# ═══════════════════════════════════════════════════════════════════════════════

RECOVERY_SCHEDULE = [
    {"delay_minutes": 15, "incentive_pct": 0, "channel": "email"},
    {"delay_minutes": 23 * 60, "incentive_pct": 5, "channel": "email"},      # T+23h
    {"delay_minutes": 3 * 24 * 60, "incentive_pct": 10, "channel": "sms"},   # T+3d
]

class RecoveryItem(BaseModel):
    item_id: str
    item_type: str  # "cart" or "proposal"
    value: float
    email: Optional[str] = None
    phone: Optional[str] = None

@router.post("/recovery/enqueue")
async def enqueue_recovery(item: RecoveryItem):
    """
    Enqueue abandoned cart/proposal for recovery sequence.
    """
    recovery_id = f"rcv_{uuid.uuid4().hex[:8]}"
    
    entry = {
        "recovery_id": recovery_id,
        "item_id": item.item_id,
        "item_type": item.item_type,
        "value": item.value,
        "email": item.email,
        "phone": item.phone,
        "enqueued_at": datetime.utcnow().isoformat(),
        "current_step": 0,
        "touches": [],
        "status": "pending"  # pending, recovered, exhausted
    }
    
    _recovery_queue.append(entry)
    
    return {
        "ok": True,
        "recovery_id": recovery_id,
        "schedule": RECOVERY_SCHEDULE,
        "next_touch_minutes": RECOVERY_SCHEDULE[0]["delay_minutes"]
    }


@router.post("/recovery/process")
async def process_recovery():
    """
    Process recovery queue. Call this every 15 minutes.
    """
    now = datetime.utcnow()
    processed = 0
    touches_sent = 0
    
    for entry in _recovery_queue:
        if entry["status"] != "pending":
            continue
        
        enqueued = datetime.fromisoformat(entry["enqueued_at"])
        minutes_elapsed = (now - enqueued).total_seconds() / 60
        
        step = entry["current_step"]
        if step >= len(RECOVERY_SCHEDULE):
            entry["status"] = "exhausted"
            continue
        
        schedule = RECOVERY_SCHEDULE[step]
        
        if minutes_elapsed >= schedule["delay_minutes"]:
            # Time to send touch
            touch = {
                "step": step,
                "sent_at": now.isoformat(),
                "channel": schedule["channel"],
                "incentive_pct": schedule["incentive_pct"]
            }
            entry["touches"].append(touch)
            entry["current_step"] += 1
            touches_sent += 1
            
            # In production: Actually send email/SMS here
        
        processed += 1
    
    return {
        "ok": True,
        "processed": processed,
        "touches_sent": touches_sent,
        "queue_size": len(_recovery_queue),
        "pending": sum(1 for e in _recovery_queue if e["status"] == "pending")
    }


@router.post("/recovery/convert")
async def mark_recovered(recovery_id: str):
    """Mark item as recovered (converted)"""
    for entry in _recovery_queue:
        if entry["recovery_id"] == recovery_id:
            entry["status"] = "recovered"
            entry["recovered_at"] = datetime.utcnow().isoformat()
            return {"ok": True, "recovered": True, "value": entry["value"]}
    return {"ok": False, "error": "Not found"}


@router.get("/recovery/stats")
async def recovery_stats():
    """Get recovery statistics"""
    total = len(_recovery_queue)
    recovered = [e for e in _recovery_queue if e["status"] == "recovered"]
    pending = [e for e in _recovery_queue if e["status"] == "pending"]
    
    total_value = sum(e["value"] for e in _recovery_queue)
    recovered_value = sum(e["value"] for e in recovered)
    
    rate = recovered_value / total_value if total_value > 0 else 0
    
    return {
        "ok": True,
        "total": total,
        "recovered": len(recovered),
        "pending": len(pending),
        "total_value_at_risk": total_value,
        "recovered_value": recovered_value,
        "recovery_rate": round(rate, 3),
        "gate": ProfitGates.RECOVERY_RATE_MIN,
        "meets_gate": rate >= ProfitGates.RECOVERY_RATE_MIN
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 7. EXPERIMENT FACTORY (10 experiments/segment/day)
# ═══════════════════════════════════════════════════════════════════════════════

class ExperimentConfig(BaseModel):
    segment: str
    hypothesis: str
    metric: str = "conversion_rate"
    budget: float = 100
    duration_days: int = 7

@router.post("/experiments/create")
async def create_experiment(config: ExperimentConfig):
    """Create a new experiment"""
    exp_id = f"exp_{uuid.uuid4().hex[:8]}"
    
    experiment = {
        "id": exp_id,
        "segment": config.segment,
        "hypothesis": config.hypothesis,
        "metric": config.metric,
        "budget": config.budget,
        "spent": 0,
        "duration_days": config.duration_days,
        "status": "running",
        "created_at": datetime.utcnow().isoformat(),
        "ends_at": (datetime.utcnow() + timedelta(days=config.duration_days)).isoformat(),
        "results": {"control": {"trials": 0, "successes": 0}, "variant": {"trials": 0, "successes": 0}}
    }
    
    _experiments[exp_id] = experiment
    
    return {"ok": True, "experiment": experiment}


@router.post("/experiments/record")
async def record_experiment_result(exp_id: str, variant: str, success: bool):
    """Record experiment result"""
    if exp_id not in _experiments:
        return {"ok": False, "error": "Experiment not found"}
    
    exp = _experiments[exp_id]
    if variant not in exp["results"]:
        return {"ok": False, "error": "Invalid variant"}
    
    exp["results"][variant]["trials"] += 1
    if success:
        exp["results"][variant]["successes"] += 1
    
    return {"ok": True, "recorded": True}


@router.post("/experiments/evaluate")
async def evaluate_experiments():
    """
    Evaluate all running experiments.
    Retire losers, scale winners.
    """
    now = datetime.utcnow()
    evaluated = []
    
    for exp_id, exp in _experiments.items():
        if exp["status"] != "running":
            continue
        
        ends_at = datetime.fromisoformat(exp["ends_at"])
        if now < ends_at:
            continue  # Not finished yet
        
        control = exp["results"]["control"]
        variant = exp["results"]["variant"]
        
        # Calculate win rates
        control_rate = control["successes"] / control["trials"] if control["trials"] > 0 else 0
        variant_rate = variant["successes"] / variant["trials"] if variant["trials"] > 0 else 0
        
        # Determine winner
        if variant_rate > control_rate * 1.1:  # 10% improvement threshold
            exp["status"] = "winner"
            exp["action"] = "SCALE"
        elif variant_rate < control_rate * 0.9:
            exp["status"] = "loser"
            exp["action"] = "RETIRE"
        else:
            exp["status"] = "inconclusive"
            exp["action"] = "EXTEND"
        
        exp["control_rate"] = round(control_rate, 3)
        exp["variant_rate"] = round(variant_rate, 3)
        exp["lift"] = round((variant_rate - control_rate) / control_rate, 3) if control_rate > 0 else 0
        
        evaluated.append(exp)
    
    return {
        "ok": True,
        "evaluated": len(evaluated),
        "winners": sum(1 for e in evaluated if e["status"] == "winner"),
        "losers": sum(1 for e in evaluated if e["status"] == "loser"),
        "experiments": evaluated
    }


@router.post("/experiments/auto-create")
async def auto_create_experiments(segment: str, count: int = 10):
    """
    Auto-create experiments for a segment.
    Call daily to maintain 10 experiments/segment.
    """
    # Count existing running experiments for segment
    existing = sum(1 for e in _experiments.values() 
                   if e["segment"] == segment and e["status"] == "running")
    
    to_create = max(0, count - existing)
    created = []
    
    hypotheses = [
        "Higher price increases perceived value",
        "Urgency messaging improves conversion",
        "Social proof badge increases trust",
        "Simplified checkout reduces abandonment",
        "Bundle offer increases AOV",
        "Free shipping threshold increases cart size",
        "Exit intent popup captures leads",
        "Personalized recommendations improve CTR",
        "Video content increases engagement",
        "Testimonials improve conversion"
    ]
    
    for i in range(to_create):
        hypothesis = hypotheses[i % len(hypotheses)]
        exp = await create_experiment(ExperimentConfig(
            segment=segment,
            hypothesis=hypothesis,
            budget=100,
            duration_days=7
        ))
        created.append(exp["experiment"])
    
    return {
        "ok": True,
        "segment": segment,
        "existing": existing,
        "created": len(created),
        "total_running": existing + len(created),
        "experiments": created
    }


@router.get("/experiments/dashboard")
async def experiments_dashboard():
    """Get experiments dashboard"""
    running = [e for e in _experiments.values() if e["status"] == "running"]
    winners = [e for e in _experiments.values() if e["status"] == "winner"]
    losers = [e for e in _experiments.values() if e["status"] == "loser"]
    
    win_rate = len(winners) / (len(winners) + len(losers)) if (winners or losers) else 0
    
    return {
        "ok": True,
        "total": len(_experiments),
        "running": len(running),
        "winners": len(winners),
        "losers": len(losers),
        "win_rate": round(win_rate, 3),
        "gate": ProfitGates.EXPERIMENT_WIN_RATE_MIN,
        "meets_gate": win_rate >= ProfitGates.EXPERIMENT_WIN_RATE_MIN
    }


# ═══════════════════════════════════════════════════════════════════════════════
# WIRE-UP
# ═══════════════════════════════════════════════════════════════════════════════

def include_profit_engine(app):
    """Include profit engine in FastAPI app"""
    app.include_router(router, prefix="", tags=["Profit Engine v98"])
    print("🏦 Profit Engine v98 loaded")
    print("   ├─ /r3/campaign/* (ROI Kill Switch)")
    print("   ├─ /idempotency/* (Unified Dedupe)")
    print("   ├─ /ownership/* (Strict Assignment)")
    print("   ├─ /backpressure/* (Priority Slots)")
    print("   ├─ /pricing/bandit/* (Thompson Sampling)")
    print("   ├─ /recovery/* (T+15m/T+23h/T+3d)")
    print("   └─ /experiments/* (Auto Factory)")
