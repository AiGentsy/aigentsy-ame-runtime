"""
AiGentsy IPVault - Auto-Royalties on Playbooks
Protocol-native IP marketplace where know-how earns passive yield
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4

def _now():
    return datetime.now(timezone.utc).isoformat()


# Asset types
ASSET_TYPES = {
    "playbook": {
        "name": "Playbook",
        "description": "Step-by-step process guides",
        "default_royalty": 0.10,  # 10%
        "icon": "📖"
    },
    "prompt_template": {
        "name": "Prompt Template",
        "description": "Reusable AI prompt patterns",
        "default_royalty": 0.05,  # 5%
        "icon": "💬"
    },
    "workflow": {
        "name": "Workflow",
        "description": "Automation sequences",
        "default_royalty": 0.08,  # 8%
        "icon": "⚙️"
    },
    "model_weights": {
        "name": "Model Weights",
        "description": "Fine-tuned AI models",
        "default_royalty": 0.15,  # 15%
        "icon": "🧠"
    },
    "design_system": {
        "name": "Design System",
        "description": "UI/UX component libraries",
        "default_royalty": 0.12,  # 12%
        "icon": "🎨"
    }
}


def create_ip_asset(
    owner_username: str,
    asset_type: str,
    title: str,
    description: str,
    royalty_percentage: float = None,
    metadata: Dict[str, Any] = None,
    price: float = 0.0,
    license_type: str = "per_use"
) -> Dict[str, Any]:
    """
    Create an IP asset (playbook, template, workflow, etc.)
    
    license_type options:
    - per_use: Royalty on each delivery
    - one_time: One-time purchase
    - subscription: Monthly access fee
    """
    if asset_type not in ASSET_TYPES:
        return {
            "ok": False,
            "error": "invalid_asset_type",
            "valid_types": list(ASSET_TYPES.keys())
        }
    
    asset_config = ASSET_TYPES[asset_type]
    
    # Use default royalty if not specified
    if royalty_percentage is None:
        royalty_percentage = asset_config["default_royalty"]
    
    # Validate royalty (max 25%)
    if royalty_percentage < 0 or royalty_percentage > 0.25:
        return {
            "ok": False,
            "error": "royalty_must_be_between_0_and_25_percent",
            "provided": royalty_percentage
        }
    
    asset_id = f"asset_{uuid4().hex[:12]}"
    
    asset = {
        "id": asset_id,
        "type": asset_type,
        "title": title,
        "description": description,
        "owner": owner_username,
        "royalty_percentage": royalty_percentage,
        "license_type": license_type,
        "price": price,
        "metadata": metadata or {},
        "status": "active",
        "created_at": _now(),
        "usage_count": 0,
        "total_royalties_earned": 0.0,
        "licensees": [],
        "usage_history": []
    }
    
    return {
        "ok": True,
        "asset": asset
    }


def license_ip_asset(
    asset: Dict[str, Any],
    licensee_username: str,
    licensee_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    License an IP asset to an agent
    """
    license_type = asset["license_type"]
    owner = asset["owner"]
    
    # Can't license your own asset
    if licensee_username == owner:
        return {
            "ok": False,
            "error": "cannot_license_own_asset"
        }
    
    # Check if already licensed
    existing_license = next(
        (l for l in asset.get("licensees", []) if l["username"] == licensee_username),
        None
    )
    
    if existing_license and license_type == "one_time":
        return {
            "ok": False,
            "error": "already_licensed",
            "license": existing_license
        }
    
    license_id = f"lic_{uuid4().hex[:8]}"
    
    # Handle payment based on license type
    if license_type == "one_time":
        price = asset["price"]
        
        # Check balance
        balance = float(licensee_user.get("ownership", {}).get("aigx", 0))
        if balance < price:
            return {
                "ok": False,
                "error": "insufficient_balance",
                "required": price,
                "available": balance
            }
        
        # Charge licensee
        licensee_user["ownership"]["aigx"] = balance - price
        licensee_user.setdefault("ownership", {}).setdefault("ledger", []).append({
            "ts": _now(),
            "amount": -price,
            "currency": "AIGx",
            "basis": "ip_license_purchase",
            "asset_id": asset["id"],
            "license_id": license_id
        })
    
    # Create license record
    license_record = {
        "license_id": license_id,
        "username": licensee_username,
        "licensed_at": _now(),
        "license_type": license_type,
        "price_paid": asset["price"] if license_type == "one_time" else 0,
        "usage_count": 0
    }
    
    asset.setdefault("licensees", []).append(license_record)
    
    return {
        "ok": True,
        "license": license_record,
        "asset_id": asset["id"]
    }


def record_asset_usage(
    asset: Dict[str, Any],
    user_username: str,
    job_id: str = None,
    context: str = ""
) -> Dict[str, Any]:
    """
    Record usage of an IP asset
    """
    # Find license
    license_record = next(
        (l for l in asset.get("licensees", []) if l["username"] == user_username),
        None
    )
    
    if not license_record:
        return {
            "ok": False,
            "error": "not_licensed",
            "asset_id": asset["id"],
            "message": "User must license asset before use"
        }
    
    # Record usage
    usage_record = {
        "used_by": user_username,
        "used_at": _now(),
        "job_id": job_id,
        "context": context
    }
    
    asset.setdefault("usage_history", []).append(usage_record)
    asset["usage_count"] += 1
    license_record["usage_count"] += 1
    
    return {
        "ok": True,
        "asset_id": asset["id"],
        "usage_recorded": True,
        "total_usage": asset["usage_count"]
    }


def calculate_royalty_payment(
    asset: Dict[str, Any],
    job_payment: float
) -> Dict[str, Any]:
    """
    Calculate royalty payment for asset usage on a job
    """
    royalty_percentage = asset["royalty_percentage"]
    royalty_amount = job_payment * royalty_percentage
    
    return {
        "asset_id": asset["id"],
        "job_payment": round(job_payment, 2),
        "royalty_percentage": royalty_percentage,
        "royalty_amount": round(royalty_amount, 2),
        "agent_keeps": round(job_payment - royalty_amount, 2)
    }


def process_delivery_with_royalty(
    asset: Dict[str, Any],
    job_payment: float,
    agent_user: Dict[str, Any],
    owner_user: Dict[str, Any],
    job_id: str = None
) -> Dict[str, Any]:
    """
    Process job delivery and automatically route royalty to asset owner
    """
    # Calculate royalty
    royalty_calc = calculate_royalty_payment(asset, job_payment)
    royalty_amount = royalty_calc["royalty_amount"]
    agent_payment = royalty_calc["agent_keeps"]
    
    # Credit agent (net of royalty)
    agent_balance = float(agent_user.get("ownership", {}).get("aigx", 0))
    agent_user["ownership"]["aigx"] = agent_balance + agent_payment
    
    agent_user.setdefault("ownership", {}).setdefault("ledger", []).append({
        "ts": _now(),
        "amount": agent_payment,
        "currency": "USD",
        "basis": "revenue",
        "job_id": job_id,
        "asset_id": asset["id"],
        "royalty_deducted": royalty_amount
    })
    
    # Credit owner (royalty)
    owner_balance = float(owner_user.get("ownership", {}).get("aigx", 0))
    owner_user["ownership"]["aigx"] = owner_balance + royalty_amount
    
    owner_user.setdefault("ownership", {}).setdefault("ledger", []).append({
        "ts": _now(),
        "amount": royalty_amount,
        "currency": "USD",
        "basis": "ip_royalty",
        "asset_id": asset["id"],
        "job_id": job_id,
        "licensee": agent_user.get("username")
    })
    
    # Update asset stats
    asset["total_royalties_earned"] += royalty_amount
    
    # Record usage
    record_asset_usage(asset, agent_user.get("username"), job_id, "delivery_with_royalty")
    
    return {
        "ok": True,
        "job_payment": round(job_payment, 2),
        "royalty_routed": round(royalty_amount, 2),
        "agent_received": round(agent_payment, 2),
        "owner_received": round(royalty_amount, 2),
        "asset_id": asset["id"],
        "total_asset_royalties": round(asset["total_royalties_earned"], 2)
    }


def get_asset_performance(
    asset: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get performance metrics for an IP asset
    """
    licensees = asset.get("licensees", [])
    active_licensees = len(licensees)
    
    # Calculate usage stats
    total_usage = asset.get("usage_count", 0)
    total_royalties = asset.get("total_royalties_earned", 0.0)
    
    # Calculate avg royalty per use
    avg_royalty = (total_royalties / total_usage) if total_usage > 0 else 0
    
    # Top users
    usage_by_user = {}
    for usage in asset.get("usage_history", []):
        user = usage.get("used_by")
        usage_by_user[user] = usage_by_user.get(user, 0) + 1
    
    top_users = sorted(usage_by_user.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "asset_id": asset["id"],
        "title": asset["title"],
        "type": asset["type"],
        "owner": asset["owner"],
        "status": asset["status"],
        "royalty_percentage": asset["royalty_percentage"],
        "active_licensees": active_licensees,
        "total_usage": total_usage,
        "total_royalties_earned": round(total_royalties, 2),
        "avg_royalty_per_use": round(avg_royalty, 2),
        "top_users": [{"username": u, "usage_count": c} for u, c in top_users],
        "created_at": asset["created_at"]
    }


def get_owner_portfolio(
    owner_username: str,
    assets: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Get owner's IP asset portfolio performance
    """
    owner_assets = [a for a in assets if a.get("owner") == owner_username]
    
    total_assets = len(owner_assets)
    total_licensees = sum([len(a.get("licensees", [])) for a in owner_assets])
    total_usage = sum([a.get("usage_count", 0) for a in owner_assets])
    total_royalties = sum([a.get("total_royalties_earned", 0) for a in owner_assets])
    
    # Asset breakdown by type
    by_type = {}
    for asset in owner_assets:
        asset_type = asset["type"]
        if asset_type not in by_type:
            by_type[asset_type] = {
                "count": 0,
                "royalties": 0,
                "usage": 0
            }
        by_type[asset_type]["count"] += 1
        by_type[asset_type]["royalties"] += asset.get("total_royalties_earned", 0)
        by_type[asset_type]["usage"] += asset.get("usage_count", 0)
    
    # Top performing assets
    top_assets = sorted(
        owner_assets,
        key=lambda a: a.get("total_royalties_earned", 0),
        reverse=True
    )[:5]
    
    return {
        "owner": owner_username,
        "total_assets": total_assets,
        "total_licensees": total_licensees,
        "total_usage": total_usage,
        "total_royalties_earned": round(total_royalties, 2),
        "assets_by_type": {
            t: {
                "count": stats["count"],
                "royalties": round(stats["royalties"], 2),
                "usage": stats["usage"]
            }
            for t, stats in by_type.items()
        },
        "top_performing_assets": [
            {
                "asset_id": a["id"],
                "title": a["title"],
                "type": a["type"],
                "royalties": round(a.get("total_royalties_earned", 0), 2),
                "usage": a.get("usage_count", 0)
            }
            for a in top_assets
        ]
    }


def get_licensee_library(
    licensee_username: str,
    assets: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Get agent's licensed asset library
    """
    licensed_assets = []
    
    for asset in assets:
        license_record = next(
            (l for l in asset.get("licensees", []) if l["username"] == licensee_username),
            None
        )
        
        if license_record:
            licensed_assets.append({
                "asset_id": asset["id"],
                "title": asset["title"],
                "type": asset["type"],
                "owner": asset["owner"],
                "royalty_percentage": asset["royalty_percentage"],
                "license_id": license_record["license_id"],
                "licensed_at": license_record["licensed_at"],
                "usage_count": license_record["usage_count"],
                "license_type": license_record["license_type"]
            })
    
    # Calculate total royalties paid
    total_royalties_paid = 0.0
    
    # Would need to scan ledger for ip_royalty entries
    # Simplified for now
    
    return {
        "licensee": licensee_username,
        "total_licensed_assets": len(licensed_assets),
        "licensed_assets": licensed_assets,
        "total_royalties_paid": round(total_royalties_paid, 2)
    }


def search_assets(
    assets: List[Dict[str, Any]],
    asset_type: str = None,
    query: str = None,
    min_usage: int = 0,
    sort_by: str = "royalties"
) -> Dict[str, Any]:
    """
    Search and filter IP assets
    
    sort_by options: royalties, usage, recent
    """
    filtered = assets
    
    # Filter by type
    if asset_type:
        filtered = [a for a in filtered if a.get("type") == asset_type]
    
    # Filter by query (title/description)
    if query:
        query_lower = query.lower()
        filtered = [
            a for a in filtered
            if query_lower in a.get("title", "").lower() or
               query_lower in a.get("description", "").lower()
        ]
    
    # Filter by minimum usage
    if min_usage > 0:
        filtered = [a for a in filtered if a.get("usage_count", 0) >= min_usage]
    
    # Sort
    if sort_by == "royalties":
        filtered.sort(key=lambda a: a.get("total_royalties_earned", 0), reverse=True)
    elif sort_by == "usage":
        filtered.sort(key=lambda a: a.get("usage_count", 0), reverse=True)
    elif sort_by == "recent":
        filtered.sort(key=lambda a: a.get("created_at", ""), reverse=True)
    
    return {
        "ok": True,
        "results": filtered,
        "count": len(filtered),
        "filters": {
            "asset_type": asset_type,
            "query": query,
            "min_usage": min_usage,
            "sort_by": sort_by
        }
    }


def update_asset_status(
    asset: Dict[str, Any],
    status: str,
    reason: str = ""
) -> Dict[str, Any]:
    """
    Update asset status (active, archived, deprecated)
    """
    valid_statuses = ["active", "archived", "deprecated"]
    
    if status not in valid_statuses:
        return {
            "ok": False,
            "error": "invalid_status",
            "valid_statuses": valid_statuses
        }
    
    old_status = asset["status"]
    asset["status"] = status
    asset["status_updated_at"] = _now()
    asset["status_reason"] = reason
    
    return {
        "ok": True,
        "asset_id": asset["id"],
        "old_status": old_status,
        "new_status": status,
        "reason": reason
    }
