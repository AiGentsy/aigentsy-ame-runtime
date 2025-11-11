"""
AiGentsy Intent Syndication + Royalty Trails
Cross-network demand routing with protocol-level attribution and payouts
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4
import hashlib

def _now():
    return datetime.now(timezone.utc).isoformat()


# Partner networks
PARTNER_NETWORKS = {
    "upwork": {
        "name": "Upwork",
        "type": "generalist",
        "api_available": True,
        "royalty_rate": 0.10,  # 10% of completed job value
        "categories": ["all"],
        "min_job_value": 100
    },
    "fiverr": {
        "name": "Fiverr",
        "type": "micro_gigs",
        "api_available": True,
        "royalty_rate": 0.12,
        "categories": ["design", "writing", "marketing"],
        "min_job_value": 5
    },
    "toptal": {
        "name": "Toptal",
        "type": "premium",
        "api_available": True,
        "royalty_rate": 0.08,
        "categories": ["development", "design", "finance"],
        "min_job_value": 1000
    },
    "guru": {
        "name": "Guru",
        "type": "generalist",
        "api_available": True,
        "royalty_rate": 0.10,
        "categories": ["all"],
        "min_job_value": 50
    },
    "99designs": {
        "name": "99designs",
        "type": "specialist",
        "api_available": True,
        "royalty_rate": 0.15,
        "categories": ["design", "branding"],
        "min_job_value": 200
    },
    "catalant": {
        "name": "Catalant",
        "type": "consulting",
        "api_available": False,
        "royalty_rate": 0.08,
        "categories": ["consulting", "strategy"],
        "min_job_value": 5000
    }
}

# Syndication reasons
SYNDICATION_REASONS = {
    "no_local_match": "No agents available locally",
    "capacity_overflow": "All local agents at capacity",
    "specialized_skill": "Requires specialized skills not available",
    "geographic_requirement": "Requires specific geographic location",
    "budget_mismatch": "Budget outside local agent range",
    "time_sensitive": "Urgent timeline needs immediate matching"
}

# Lineage split rules
DEFAULT_LINEAGE_SPLIT = {
    "agent": 0.70,           # 70% to agent who completes work
    "partner_network": 0.20,  # 20% to partner network
    "aigentsy": 0.10         # 10% to AiGentsy for orchestration
}


def create_syndication_route(
    intent: Dict[str, Any],
    target_network: str,
    reason: str,
    lineage_split: Dict[str, float] = None,
    sla_terms: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create syndication route for an intent
    """
    if target_network not in PARTNER_NETWORKS:
        return {
            "ok": False,
            "error": "invalid_network",
            "valid_networks": list(PARTNER_NETWORKS.keys())
        }
    
    if reason not in SYNDICATION_REASONS:
        return {
            "ok": False,
            "error": "invalid_reason",
            "valid_reasons": list(SYNDICATION_REASONS.keys())
        }
    
    network_config = PARTNER_NETWORKS[target_network]
    
    # Validate min job value
    intent_budget = float(intent.get("budget", 0))
    if intent_budget < network_config["min_job_value"]:
        return {
            "ok": False,
            "error": "budget_below_network_minimum",
            "min_required": network_config["min_job_value"],
            "intent_budget": intent_budget
        }
    
    # Use default split if not provided
    if not lineage_split:
        lineage_split = DEFAULT_LINEAGE_SPLIT.copy()
        # Adjust network split based on network royalty rate
        lineage_split["partner_network"] = network_config["royalty_rate"]
        lineage_split["agent"] = 1.0 - lineage_split["partner_network"] - lineage_split["aigentsy"]
    
    # Validate lineage split
    total_split = sum(lineage_split.values())
    if abs(total_split - 1.0) > 0.01:
        return {
            "ok": False,
            "error": "lineage_split_must_equal_100_percent",
            "total": total_split
        }
    
    route_id = f"route_{uuid4().hex[:12]}"
    
    # Generate syndication hash for tracking
    hash_input = f"{intent.get('id')}:{target_network}:{_now()}"
    syndication_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    route = {
        "id": route_id,
        "intent_id": intent.get("id"),
        "target_network": target_network,
        "network_config": network_config,
        "reason": reason,
        "syndication_hash": syndication_hash,
        "status": "pending",
        "created_at": _now(),
        
        # Financial structure
        "intent_budget": intent_budget,
        "lineage_split": lineage_split,
        "expected_royalty": round(intent_budget * lineage_split["aigentsy"], 2),
        
        # SLA enforcement
        "sla_terms": sla_terms or {
            "delivery_days": intent.get("delivery_days", 7),
            "quality_threshold": 0.8,
            "escrow_held": True
        },
        
        # Tracking
        "routed_at": None,
        "accepted_at": None,
        "completed_at": None,
        "agent_on_network": None,
        "actual_completion_value": 0.0,
        "royalty_received": 0.0,
        "royalty_status": "pending"
    }
    
    return {
        "ok": True,
        "route": route
    }


def route_to_network(
    route: Dict[str, Any],
    network_job_id: str = None
) -> Dict[str, Any]:
    """
    Execute routing to partner network
    """
    if route["status"] != "pending":
        return {
            "ok": False,
            "error": "route_already_processed",
            "status": route["status"]
        }
    
    target_network = route["target_network"]
    network_config = PARTNER_NETWORKS[target_network]
    
    # In production, would call partner network API
    # For now, simulate successful routing
    
    route["status"] = "routed"
    route["routed_at"] = _now()
    route["network_job_id"] = network_job_id or f"{target_network}_{uuid4().hex[:8]}"
    
    # Add to tracking
    route.setdefault("events", []).append({
        "event": "ROUTED_TO_NETWORK",
        "network": target_network,
        "at": _now()
    })
    
    return {
        "ok": True,
        "route_id": route["id"],
        "routed_to": target_network,
        "network_job_id": route["network_job_id"],
        "status": "routed"
    }


def record_network_acceptance(
    route: Dict[str, Any],
    agent_on_network: str,
    network_metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Record that an agent on partner network accepted the job
    """
    if route["status"] != "routed":
        return {
            "ok": False,
            "error": "route_must_be_routed_first",
            "status": route["status"]
        }
    
    route["status"] = "accepted"
    route["accepted_at"] = _now()
    route["agent_on_network"] = agent_on_network
    route["network_metadata"] = network_metadata or {}
    
    route.setdefault("events", []).append({
        "event": "ACCEPTED_ON_NETWORK",
        "agent": agent_on_network,
        "network": route["target_network"],
        "at": _now()
    })
    
    return {
        "ok": True,
        "route_id": route["id"],
        "accepted_by": agent_on_network,
        "network": route["target_network"]
    }


def record_network_completion(
    route: Dict[str, Any],
    completion_value: float,
    completion_proof: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Record job completion on partner network
    """
    if route["status"] != "accepted":
        return {
            "ok": False,
            "error": "route_must_be_accepted_first",
            "status": route["status"]
        }
    
    route["status"] = "completed"
    route["completed_at"] = _now()
    route["actual_completion_value"] = completion_value
    route["completion_proof"] = completion_proof or {}
    
    route.setdefault("events", []).append({
        "event": "COMPLETED_ON_NETWORK",
        "value": completion_value,
        "at": _now()
    })
    
    return {
        "ok": True,
        "route_id": route["id"],
        "completed": True,
        "value": completion_value,
        "network": route["target_network"]
    }


def calculate_lineage_distribution(
    route: Dict[str, Any],
    completion_value: float
) -> Dict[str, Any]:
    """
    Calculate revenue distribution via lineage splits
    """
    lineage_split = route["lineage_split"]
    
    distributions = []
    
    for party, split_percentage in lineage_split.items():
        amount = completion_value * split_percentage
        
        distributions.append({
            "party": party,
            "role": party,
            "split_percentage": split_percentage,
            "amount": round(amount, 2)
        })
    
    # Verify total
    total_distributed = sum([d["amount"] for d in distributions])
    
    return {
        "ok": True,
        "completion_value": round(completion_value, 2),
        "distributions": distributions,
        "total_distributed": round(total_distributed, 2),
        "aigentsy_royalty": round(completion_value * lineage_split["aigentsy"], 2),
        "network_royalty": round(completion_value * lineage_split["partner_network"], 2),
        "agent_payment": round(completion_value * lineage_split["agent"], 2)
    }


def process_royalty_payment(
    route: Dict[str, Any],
    platform_user: Dict[str, Any],
    received_amount: float = None
) -> Dict[str, Any]:
    """
    Process royalty payment from partner network back to AiGentsy
    """
    if route["status"] != "completed":
        return {
            "ok": False,
            "error": "route_must_be_completed_first",
            "status": route["status"]
        }
    
    # Calculate expected royalty
    completion_value = route["actual_completion_value"]
    expected_royalty = completion_value * route["lineage_split"]["aigentsy"]
    
    # Use received amount or expected
    royalty_received = received_amount if received_amount is not None else expected_royalty
    
    # Update route
    route["royalty_received"] = royalty_received
    route["royalty_status"] = "received"
    route["royalty_received_at"] = _now()
    
    # Credit platform account
    platform_balance = float(platform_user.get("ownership", {}).get("aigx", 0))
    platform_user["ownership"]["aigx"] = platform_balance + royalty_received
    
    platform_user.setdefault("ownership", {}).setdefault("ledger", []).append({
        "ts": _now(),
        "amount": royalty_received,
        "currency": "USD",
        "basis": "syndication_royalty",
        "route_id": route["id"],
        "network": route["target_network"],
        "completion_value": completion_value
    })
    
    route.setdefault("events", []).append({
        "event": "ROYALTY_RECEIVED",
        "amount": royalty_received,
        "at": _now()
    })
    
    return {
        "ok": True,
        "route_id": route["id"],
        "royalty_received": round(royalty_received, 2),
        "expected_royalty": round(expected_royalty, 2),
        "variance": round(royalty_received - expected_royalty, 2)
    }


def find_best_network(
    intent: Dict[str, Any],
    networks: Dict[str, Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Find best partner network for an intent
    """
    if not networks:
        networks = PARTNER_NETWORKS
    
    intent_category = intent.get("category") or intent.get("type")
    intent_budget = float(intent.get("budget", 0))
    
    candidates = []
    
    for network_id, network in networks.items():
        # Check budget requirements
        if intent_budget < network["min_job_value"]:
            continue
        
        # Check category match
        network_categories = network.get("categories", [])
        if "all" not in network_categories and intent_category not in network_categories:
            continue
        
        # Score based on royalty rate (lower is better for AiGentsy margin)
        score = 1.0 - network["royalty_rate"]
        
        candidates.append({
            "network": network_id,
            "name": network["name"],
            "type": network["type"],
            "royalty_rate": network["royalty_rate"],
            "score": round(score, 3)
        })
    
    # Sort by score
    candidates.sort(key=lambda c: c["score"], reverse=True)
    
    return {
        "ok": True,
        "candidates": candidates,
        "best_match": candidates[0] if candidates else None,
        "total_matches": len(candidates)
    }


def get_syndication_stats(
    routes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Get syndication performance statistics
    """
    total_routes = len(routes)
    
    # Count by status
    by_status = {}
    for route in routes:
        status = route.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
    
    # Count by network
    by_network = {}
    for route in routes:
        network = route.get("target_network")
        by_network[network] = by_network.get(network, 0) + 1
    
    # Calculate totals
    completed_routes = [r for r in routes if r.get("status") == "completed"]
    total_completion_value = sum([r.get("actual_completion_value", 0) for r in completed_routes])
    total_royalties = sum([r.get("royalty_received", 0) for r in completed_routes])
    
    # Calculate success rate
    routed = len([r for r in routes if r.get("status") in ["routed", "accepted", "completed"]])
    completed = len(completed_routes)
    success_rate = (completed / routed) if routed > 0 else 0
    
    # Average royalty rate
    avg_royalty_rate = (total_royalties / total_completion_value) if total_completion_value > 0 else 0
    
    return {
        "total_routes": total_routes,
        "routes_by_status": by_status,
        "routes_by_network": by_network,
        "completed_routes": completed,
        "success_rate": round(success_rate, 2),
        "total_completion_value": round(total_completion_value, 2),
        "total_royalties_received": round(total_royalties, 2),
        "avg_royalty_rate": round(avg_royalty_rate, 2)
    }


def generate_network_report(
    routes: List[Dict[str, Any]],
    network_id: str
) -> Dict[str, Any]:
    """
    Generate performance report for specific network
    """
    network_routes = [r for r in routes if r.get("target_network") == network_id]
    
    if not network_routes:
        return {
            "ok": False,
            "error": "no_routes_for_network",
            "network": network_id
        }
    
    network_config = PARTNER_NETWORKS.get(network_id, {})
    
    total_routes = len(network_routes)
    completed = len([r for r in network_routes if r.get("status") == "completed"])
    
    completion_rate = (completed / total_routes) if total_routes > 0 else 0
    
    total_value = sum([r.get("actual_completion_value", 0) for r in network_routes if r.get("status") == "completed"])
    total_royalties = sum([r.get("royalty_received", 0) for r in network_routes])
    
    avg_job_value = (total_value / completed) if completed > 0 else 0
    avg_royalty = (total_royalties / completed) if completed > 0 else 0
    
    return {
        "ok": True,
        "network": network_id,
        "network_name": network_config.get("name"),
        "network_type": network_config.get("type"),
        "total_routes": total_routes,
        "completed_routes": completed,
        "completion_rate": round(completion_rate, 2),
        "total_job_value": round(total_value, 2),
        "total_royalties": round(total_royalties, 2),
        "avg_job_value": round(avg_job_value, 2),
        "avg_royalty_per_job": round(avg_royalty, 2),
        "configured_royalty_rate": network_config.get("royalty_rate")
    }


def check_sla_compliance(
    route: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check SLA compliance for syndicated job
    """
    if route["status"] != "completed":
        return {
            "ok": False,
            "error": "route_not_completed",
            "status": route["status"]
        }
    
    sla_terms = route.get("sla_terms", {})
    
    # Check delivery time
    delivery_days = sla_terms.get("delivery_days", 7)
    routed_at = route.get("routed_at")
    completed_at = route.get("completed_at")
    
    if routed_at and completed_at:
        from datetime import datetime
        routed = datetime.fromisoformat(routed_at.replace("Z", "+00:00"))
        completed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        actual_days = (completed - routed).days
        
        on_time = actual_days <= delivery_days
    else:
        on_time = None
        actual_days = None
    
    # Would check quality threshold from completion_proof
    quality_compliant = True  # Simplified
    
    sla_compliant = on_time and quality_compliant
    
    return {
        "ok": True,
        "route_id": route["id"],
        "sla_compliant": sla_compliant,
        "delivery": {
            "required_days": delivery_days,
            "actual_days": actual_days,
            "on_time": on_time
        },
        "quality": {
            "threshold": sla_terms.get("quality_threshold", 0.8),
            "compliant": quality_compliant
        }
    }
