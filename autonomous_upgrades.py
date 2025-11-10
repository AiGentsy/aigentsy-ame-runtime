"""
AiGentsy Autonomous Logic Upgrades
Self-improving agent logic with A/B testing and auto-deployment
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import random
import hashlib

def _now():
    return datetime.now(timezone.utc).isoformat()

def _days_ago(ts_iso: str) -> int:
    try:
        then = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - then).days
    except:
        return 9999


# Logic upgrade types
UPGRADE_TYPES = {
    "pricing_strategy": {
        "name": "Pricing Strategy",
        "description": "Optimize bid pricing logic",
        "metrics": ["win_rate", "avg_margin", "conversion_rate"]
    },
    "response_speed": {
        "name": "Response Speed",
        "description": "Optimize time to respond to intents",
        "metrics": ["response_time", "win_rate", "engagement_rate"]
    },
    "proposal_quality": {
        "name": "Proposal Quality",
        "description": "Improve proposal templates and messaging",
        "metrics": ["acceptance_rate", "buyer_feedback", "repeat_rate"]
    },
    "delivery_optimization": {
        "name": "Delivery Optimization",
        "description": "Optimize work sequencing and delivery",
        "metrics": ["on_time_rate", "quality_score", "rework_rate"]
    },
    "client_selection": {
        "name": "Client Selection",
        "description": "Better targeting of ideal clients",
        "metrics": ["satisfaction_rate", "dispute_rate", "repeat_rate"]
    }
}


def create_logic_variant(
    upgrade_type: str,
    base_logic: Dict[str, Any],
    mutation_level: float = 0.2
) -> Dict[str, Any]:
    """
    Create a variant of existing logic for A/B testing
    
    mutation_level: 0.1 = conservative, 0.5 = aggressive changes
    """
    from uuid import uuid4
    
    variant_id = f"var_{uuid4().hex[:12]}"
    
    # Clone base logic
    variant_logic = base_logic.copy()
    
    # Apply mutations based on upgrade type
    if upgrade_type == "pricing_strategy":
        # Mutate pricing parameters
        if "pricing" in variant_logic:
            base_multiplier = variant_logic["pricing"].get("multiplier", 1.0)
            mutation = random.uniform(-mutation_level, mutation_level)
            variant_logic["pricing"]["multiplier"] = round(base_multiplier * (1 + mutation), 2)
            
            base_discount = variant_logic["pricing"].get("max_discount", 0.1)
            variant_logic["pricing"]["max_discount"] = round(base_discount * (1 + mutation/2), 2)
    
    elif upgrade_type == "response_speed":
        # Mutate response timing
        if "response" in variant_logic:
            base_delay = variant_logic["response"].get("target_minutes", 30)
            mutation = random.uniform(-mutation_level, mutation_level)
            variant_logic["response"]["target_minutes"] = max(5, int(base_delay * (1 + mutation)))
    
    elif upgrade_type == "proposal_quality":
        # Mutate proposal parameters
        if "proposal" in variant_logic:
            templates = variant_logic["proposal"].get("templates", [])
            if templates:
                # Shuffle template priority
                random.shuffle(templates)
                variant_logic["proposal"]["templates"] = templates
    
    elif upgrade_type == "delivery_optimization":
        # Mutate delivery parameters
        if "delivery" in variant_logic:
            base_buffer = variant_logic["delivery"].get("time_buffer", 0.2)
            mutation = random.uniform(-mutation_level, mutation_level)
            variant_logic["delivery"]["time_buffer"] = max(0.05, round(base_buffer * (1 + mutation), 2))
    
    elif upgrade_type == "client_selection":
        # Mutate selection criteria
        if "selection" in variant_logic:
            base_min_score = variant_logic["selection"].get("min_buyer_score", 50)
            mutation = random.uniform(-mutation_level, mutation_level)
            variant_logic["selection"]["min_buyer_score"] = max(0, int(base_min_score * (1 + mutation)))
    
    variant = {
        "id": variant_id,
        "upgrade_type": upgrade_type,
        "parent_logic_id": base_logic.get("id", "base"),
        "logic": variant_logic,
        "mutation_level": mutation_level,
        "status": "testing",
        "created_at": _now(),
        "test_sample_size": 0,
        "metrics": {},
        "confidence": 0.0
    }
    
    return variant


def create_ab_test(
    upgrade_type: str,
    control_logic: Dict[str, Any],
    test_duration_days: int = 14,
    sample_size: int = 100
) -> Dict[str, Any]:
    """
    Create an A/B test for a logic upgrade
    """
    from uuid import uuid4
    
    test_id = f"test_{uuid4().hex[:12]}"
    
    # Create variant
    variant = create_logic_variant(upgrade_type, control_logic, mutation_level=0.3)
    
    ab_test = {
        "id": test_id,
        "upgrade_type": upgrade_type,
        "status": "active",
        "created_at": _now(),
        "end_date": (datetime.now(timezone.utc) + timedelta(days=test_duration_days)).isoformat(),
        "test_duration_days": test_duration_days,
        "target_sample_size": sample_size,
        "control": {
            "id": "control",
            "logic": control_logic,
            "sample_count": 0,
            "metrics": {}
        },
        "variant": {
            "id": variant["id"],
            "logic": variant["logic"],
            "sample_count": 0,
            "metrics": {}
        },
        "results": None,
        "winner": None
    }
    
    return ab_test


def assign_to_test_group(
    ab_test: Dict[str, Any],
    agent_id: str
) -> str:
    """
    Assign agent to control or variant group (50/50 split)
    """
    # Use hash for consistent assignment
    hash_val = int(hashlib.md5(f"{ab_test['id']}{agent_id}".encode()).hexdigest(), 16)
    
    if hash_val % 2 == 0:
        return "control"
    else:
        return "variant"


def record_test_outcome(
    ab_test: Dict[str, Any],
    group: str,
    metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Record outcome for a test sample
    """
    if group not in ["control", "variant"]:
        return {"ok": False, "error": "invalid_group"}
    
    test_group = ab_test[group]
    
    # Increment sample count
    test_group["sample_count"] += 1
    
    # Update metrics (running average)
    for metric_name, metric_value in metrics.items():
        if metric_name not in test_group["metrics"]:
            test_group["metrics"][metric_name] = metric_value
        else:
            # Running average
            current_avg = test_group["metrics"][metric_name]
            sample_count = test_group["sample_count"]
            new_avg = ((current_avg * (sample_count - 1)) + metric_value) / sample_count
            test_group["metrics"][metric_name] = round(new_avg, 4)
    
    return {"ok": True, "group": group, "sample_count": test_group["sample_count"]}


def analyze_ab_test(
    ab_test: Dict[str, Any],
    min_sample_size: int = 30
) -> Dict[str, Any]:
    """
    Analyze A/B test results and determine winner
    """
    control = ab_test["control"]
    variant = ab_test["variant"]
    
    # Check if we have enough samples
    if control["sample_count"] < min_sample_size or variant["sample_count"] < min_sample_size:
        return {
            "ok": False,
            "status": "insufficient_samples",
            "control_samples": control["sample_count"],
            "variant_samples": variant["sample_count"],
            "min_required": min_sample_size
        }
    
    # Compare key metrics
    upgrade_type = ab_test["upgrade_type"]
    key_metrics = UPGRADE_TYPES[upgrade_type]["metrics"]
    
    comparison = {}
    variant_wins = 0
    control_wins = 0
    
    for metric in key_metrics:
        control_val = control["metrics"].get(metric, 0)
        variant_val = variant["metrics"].get(metric, 0)
        
        improvement = ((variant_val - control_val) / control_val * 100) if control_val > 0 else 0
        
        comparison[metric] = {
            "control": control_val,
            "variant": variant_val,
            "improvement_pct": round(improvement, 2),
            "winner": "variant" if variant_val > control_val else "control"
        }
        
        if variant_val > control_val:
            variant_wins += 1
        else:
            control_wins += 1
    
    # Determine overall winner (majority of metrics)
    overall_winner = "variant" if variant_wins > control_wins else "control"
    
    # Calculate confidence (based on sample size and consistency)
    confidence = min(100, (min(control["sample_count"], variant["sample_count"]) / 100) * 100)
    
    # Statistical significance (simplified)
    is_significant = variant_wins > control_wins and confidence > 70
    
    results = {
        "ok": True,
        "test_id": ab_test["id"],
        "upgrade_type": upgrade_type,
        "comparison": comparison,
        "variant_wins": variant_wins,
        "control_wins": control_wins,
        "overall_winner": overall_winner,
        "confidence": round(confidence, 2),
        "is_significant": is_significant,
        "recommendation": "deploy_variant" if is_significant else "continue_testing",
        "analyzed_at": _now()
    }
    
    # Update test
    ab_test["results"] = results
    ab_test["winner"] = overall_winner if is_significant else None
    
    return results


def deploy_logic_upgrade(
    ab_test: Dict[str, Any],
    users: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Deploy winning logic to all agents
    """
    if not ab_test.get("winner"):
        return {
            "ok": False,
            "error": "no_winner_determined",
            "message": "Run analyze_ab_test first"
        }
    
    winner = ab_test["winner"]
    winning_logic = ab_test[winner]["logic"]
    upgrade_type = ab_test["upgrade_type"]
    
    deployed_count = 0
    
    for user in users:
        # Only update agents (not buyers)
        if user.get("role") != "agent" and not user.get("intents"):
            continue
        
        # Update agent logic
        user.setdefault("logic", {})
        user["logic"][upgrade_type] = winning_logic
        
        # Track upgrade
        user.setdefault("logic_upgrades", []).append({
            "upgrade_type": upgrade_type,
            "test_id": ab_test["id"],
            "deployed_at": _now(),
            "version": ab_test[winner]["id"]
        })
        
        deployed_count += 1
    
    # Mark test as deployed
    ab_test["status"] = "deployed"
    ab_test["deployed_at"] = _now()
    ab_test["deployed_count"] = deployed_count
    
    return {
        "ok": True,
        "test_id": ab_test["id"],
        "upgrade_type": upgrade_type,
        "winner": winner,
        "deployed_to": deployed_count,
        "deployed_at": _now()
    }


def rollback_logic_upgrade(
    upgrade_type: str,
    users: List[Dict[str, Any]],
    rollback_to_version: str = None
) -> Dict[str, Any]:
    """
    Rollback a logic upgrade to previous version
    """
    rollback_count = 0
    
    for user in users:
        if upgrade_type not in user.get("logic", {}):
            continue
        
        # Remove current version
        if rollback_to_version:
            # Rollback to specific version (would need version history)
            pass
        else:
            # Remove upgrade entirely (revert to default)
            user["logic"].pop(upgrade_type, None)
        
        # Track rollback
        user.setdefault("logic_upgrades", []).append({
            "upgrade_type": upgrade_type,
            "action": "rollback",
            "rolled_back_at": _now()
        })
        
        rollback_count += 1
    
    return {
        "ok": True,
        "upgrade_type": upgrade_type,
        "rollback_count": rollback_count,
        "rolled_back_at": _now()
    }


def get_active_tests(
    tests: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Get all active A/B tests
    """
    active = []
    
    for test in tests:
        if test.get("status") == "active":
            # Check if test has expired
            end_date = test.get("end_date")
            if end_date and end_date < _now():
                test["status"] = "expired"
            else:
                active.append(test)
    
    return active


def suggest_next_upgrade(
    users: List[Dict[str, Any]],
    existing_tests: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Suggest next logic upgrade to test based on platform needs
    """
    # Calculate platform metrics
    total_agents = len([u for u in users if u.get("intents") or u.get("role") == "agent"])
    
    # Count what's already being tested
    types_in_test = set([t["upgrade_type"] for t in existing_tests if t.get("status") == "active"])
    
    # Calculate needs
    needs = {}
    
    for user in users:
        ledger = user.get("ownership", {}).get("ledger", [])
        
        # Check dispute rate (need delivery optimization)
        disputes = len([e for e in ledger if e.get("basis") == "bond_slash"])
        total_jobs = len([e for e in ledger if e.get("basis") == "revenue"])
        
        if total_jobs > 0 and disputes / total_jobs > 0.1:
            needs["delivery_optimization"] = needs.get("delivery_optimization", 0) + 1
        
        # Check win rate (need pricing strategy)
        bids = len([e for e in ledger if e.get("basis") == "bid_submitted"])
        wins = len([e for e in ledger if e.get("basis") == "intent_awarded"])
        
        if bids > 0 and wins / bids < 0.3:
            needs["pricing_strategy"] = needs.get("pricing_strategy", 0) + 1
    
    # Sort by need
    sorted_needs = sorted(needs.items(), key=lambda x: x[1], reverse=True)
    
    # Find highest priority not being tested
    for upgrade_type, affected_count in sorted_needs:
        if upgrade_type not in types_in_test:
            return {
                "ok": True,
                "recommended_upgrade": upgrade_type,
                "description": UPGRADE_TYPES[upgrade_type]["description"],
                "affected_agents": affected_count,
                "total_agents": total_agents,
                "rationale": f"{affected_count} agents would benefit from this upgrade"
            }
    
    return {
        "ok": True,
        "recommended_upgrade": None,
        "message": "All critical upgrades are being tested or deployed"
    }
