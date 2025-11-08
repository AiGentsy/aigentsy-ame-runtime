from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import httpx

_VALUE_CHAINS: Dict[str, Dict[str, Any]] = {}
_CHAIN_PERFORMANCE: Dict[str, List[Dict[str, Any]]] = {}

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def discover_value_chain(
    initiator: str,
    initiator_capability: str,
    target_outcome: str,
    max_hops: int = 4
) -> Dict[str, Any]:
    """Discover optimal multi-device value chain"""
    
    # Get all registered devices
    from aigentsy_conductor import _DEVICE_REGISTRY
    
    # Build capability graph
    devices_by_capability = {}
    
    for key, device in _DEVICE_REGISTRY.items():
        username = device["username"]
        if username == initiator:
            continue
        
        apps = [app.get("type") for app in device.get("connected_apps", [])]
        capabilities = device.get("capabilities", [])
        
        # Map apps to capabilities
        if "tiktok" in apps or "instagram" in apps:
            devices_by_capability.setdefault("social_traffic", []).append({
                "username": username,
                "device_id": device["device_id"],
                "apps": apps,
                "outcome_score": device.get("outcome_score", 50)
            })
        
        if "shopify" in apps:
            devices_by_capability.setdefault("ecommerce", []).append({
                "username": username,
                "device_id": device["device_id"],
                "apps": apps,
                "outcome_score": device.get("outcome_score", 50)
            })
        
        if "email" in capabilities:
            devices_by_capability.setdefault("email_marketing", []).append({
                "username": username,
                "device_id": device["device_id"],
                "apps": apps,
                "outcome_score": device.get("outcome_score", 50)
            })
        
        if "sms" in capabilities:
            devices_by_capability.setdefault("sms_marketing", []).append({
                "username": username,
                "device_id": device["device_id"],
                "apps": apps,
                "outcome_score": device.get("outcome_score", 50)
            })
    
    # Find optimal chain
    chains = []
    
    if target_outcome == "ecommerce_sales":
        # Example chain: Social Traffic → E-commerce → Email Retention
        
        # Get social traffic partners
        social_devices = devices_by_capability.get("social_traffic", [])
        ecommerce_devices = devices_by_capability.get("ecommerce", [])
        email_devices = devices_by_capability.get("email_marketing", [])
        
        if social_devices and ecommerce_devices:
            # Sort by outcome score
            social_devices.sort(key=lambda d: d["outcome_score"], reverse=True)
            ecommerce_devices.sort(key=lambda d: d["outcome_score"], reverse=True)
            email_devices.sort(key=lambda d: d["outcome_score"], reverse=True)
            
            # Build chain
            chain_nodes = [
                {
                    "position": 1,
                    "role": "traffic_generator",
                    "username": social_devices[0]["username"],
                    "device_id": social_devices[0]["device_id"],
                    "capability": "social_traffic",
                    "revenue_share": 0.30
                },
                {
                    "position": 2,
                    "role": "merchant",
                    "username": ecommerce_devices[0]["username"],
                    "device_id": ecommerce_devices[0]["device_id"],
                    "capability": "ecommerce",
                    "revenue_share": 0.50
                }
            ]
            
            # Add email if available
            if email_devices:
                chain_nodes.append({
                    "position": 3,
                    "role": "retention",
                    "username": email_devices[0]["username"],
                    "device_id": email_devices[0]["device_id"],
                    "capability": "email_marketing",
                    "revenue_share": 0.20
                })
            
            chains.append({
                "chain_type": "social_to_ecommerce",
                "nodes": chain_nodes,
                "expected_roas": 2.8,
                "confidence": 0.75
            })
    
    elif target_outcome == "content_monetization":
        # Example chain: Content Creator → Affiliate → Payment Processor
        
        social_devices = devices_by_capability.get("social_traffic", [])
        
        if social_devices:
            chains.append({
                "chain_type": "content_affiliate",
                "nodes": [
                    {
                        "position": 1,
                        "role": "content_creator",
                        "username": initiator,
                        "capability": initiator_capability,
                        "revenue_share": 0.70
                    },
                    {
                        "position": 2,
                        "role": "affiliate_network",
                        "username": social_devices[0]["username"],
                        "device_id": social_devices[0]["device_id"],
                        "capability": "social_traffic",
                        "revenue_share": 0.30
                    }
                ],
                "expected_roas": 3.2,
                "confidence": 0.65
            })
    
    # Sort chains by expected value
    chains.sort(key=lambda c: c["expected_roas"] * c["confidence"], reverse=True)
    
    return {
        "ok": True,
        "initiator": initiator,
        "target_outcome": target_outcome,
        "chains": chains,
        "count": len(chains)
    }


async def create_value_chain(
    initiator: str,
    chain_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Create and activate value chain"""
    
    chain_id = f"chain_{uuid4().hex[:8]}"
    
    nodes = chain_config.get("nodes", [])
    
    if len(nodes) < 2:
        return {"ok": False, "error": "chain_requires_at_least_2_nodes"}
    
    # Validate revenue split adds to 1.0
    total_split = sum(node.get("revenue_share", 0) for node in nodes)
    if abs(total_split - 1.0) > 0.01:
        return {"ok": False, "error": "revenue_split_must_equal_100_percent"}
    
    chain = {
        "id": chain_id,
        "initiator": initiator,
        "chain_type": chain_config.get("chain_type"),
        "nodes": nodes,
        "status": "PENDING_APPROVAL",
        "created_at": now_iso(),
        "approved_by": [],
        "performance": {
            "total_revenue": 0.0,
            "total_conversions": 0,
            "avg_roas": 0.0
        },
        "events": [
            {"type": "CHAIN_CREATED", "by": initiator, "at": now_iso()}
        ]
    }
    
    _VALUE_CHAINS[chain_id] = chain
    
    # Send approval requests to all nodes
    await _request_chain_approvals(chain_id, nodes)
    
    return {
        "ok": True,
        "chain_id": chain_id,
        "chain": chain,
        "message": f"Chain created, awaiting approval from {len(nodes)} participants"
    }


async def _request_chain_approvals(chain_id: str, nodes: List[Dict[str, Any]]) -> None:
    """Request approval from all chain participants"""
    
    async with httpx.AsyncClient(timeout=10) as client:
        for node in nodes:
            username = node.get("username")
            role = node.get("role")
            revenue_share = node.get("revenue_share", 0)
            
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                    json={
                        "id": f"chain_approval_{uuid4().hex[:8]}",
                        "sender": "aigentsy_conductor",
                        "recipient": username,
                        "title": f"Join Value Chain: {role}",
                        "body": f"""You've been invited to join a multi-device value chain.

Your Role: {role}
Your Revenue Share: {int(revenue_share * 100)}%

Chain ID: {chain_id}

Approve at: /chains/{chain_id}/approve""",
                        "meta": {"chain_id": chain_id, "role": role},
                        "status": "sent",
                        "timestamp": now_iso()
                    }
                )
            except Exception as e:
                print(f"Failed to notify {username}: {e}")


async def approve_chain_participation(
    chain_id: str,
    username: str
) -> Dict[str, Any]:
    """Approve participation in value chain"""
    
    chain = _VALUE_CHAINS.get(chain_id)
    
    if not chain:
        return {"ok": False, "error": "chain_not_found"}
    
    # Check if user is a node
    user_node = next((n for n in chain["nodes"] if n.get("username") == username), None)
    
    if not user_node:
        return {"ok": False, "error": "not_chain_participant"}
    
    if username in chain["approved_by"]:
        return {"ok": False, "error": "already_approved"}
    
    chain["approved_by"].append(username)
    chain["events"].append({
        "type": "NODE_APPROVED",
        "by": username,
        "at": now_iso()
    })
    
    # Check if all nodes approved
    all_usernames = [n.get("username") for n in chain["nodes"]]
    
    if set(chain["approved_by"]) == set(all_usernames):
        chain["status"] = "ACTIVE"
        chain["activated_at"] = now_iso()
        chain["events"].append({
            "type": "CHAIN_ACTIVATED",
            "at": now_iso()
        })
        
        return {
            "ok": True,
            "chain_id": chain_id,
            "status": "ACTIVE",
            "message": "Chain activated! All nodes approved."
        }
    
    return {
        "ok": True,
        "chain_id": chain_id,
        "status": "PENDING_APPROVAL",
        "approved_count": len(chain["approved_by"]),
        "total_nodes": len(chain["nodes"])
    }


async def execute_chain_action(
    chain_id: str,
    action_type: str,
    action_data: Dict[str, Any],
    executed_by: str
) -> Dict[str, Any]:
    """Execute action within value chain"""
    
    chain = _VALUE_CHAINS.get(chain_id)
    
    if not chain:
        return {"ok": False, "error": "chain_not_found"}
    
    if chain["status"] != "ACTIVE":
        return {"ok": False, "error": "chain_not_active"}
    
    # Record action
    action_id = f"action_{uuid4().hex[:8]}"
    
    action_record = {
        "id": action_id,
        "chain_id": chain_id,
        "type": action_type,
        "executed_by": executed_by,
        "data": action_data,
        "executed_at": now_iso(),
        "results": {}
    }
    
    # Execute based on action type
    if action_type == "generate_traffic":
        # Node 1: Generate social traffic
        action_record["results"] = {
            "impressions": action_data.get("impressions", 0),
            "clicks": action_data.get("clicks", 0),
            "ctr": action_data.get("ctr", 0)
        }
    
    elif action_type == "convert_sale":
        # Node 2: Convert to sale
        revenue = float(action_data.get("revenue", 0))
        
        action_record["results"] = {
            "revenue": revenue,
            "conversions": action_data.get("conversions", 1)
        }
        
        # Distribute revenue across chain
        await _distribute_chain_revenue(chain_id, revenue)
    
    elif action_type == "retention_email":
        # Node 3: Retention
        action_record["results"] = {
            "emails_sent": action_data.get("emails_sent", 0),
            "opens": action_data.get("opens", 0),
            "clicks": action_data.get("clicks", 0)
        }
    
    # Store in chain performance history
    _CHAIN_PERFORMANCE.setdefault(chain_id, []).append(action_record)
    
    chain["events"].append({
        "type": f"ACTION_{action_type.upper()}",
        "by": executed_by,
        "action_id": action_id,
        "at": now_iso()
    })
    
    return {
        "ok": True,
        "action_id": action_id,
        "action": action_record
    }


async def _distribute_chain_revenue(chain_id: str, revenue: float) -> None:
    """Distribute revenue across chain nodes"""
    
    chain = _VALUE_CHAINS.get(chain_id)
    
    if not chain:
        return
    
    # Update chain performance
    chain["performance"]["total_revenue"] += revenue
    chain["performance"]["total_conversions"] += 1
    
    async with httpx.AsyncClient(timeout=10) as client:
        for node in chain["nodes"]:
            username = node.get("username")
            share = node.get("revenue_share", 0)
            amount = round(revenue * share, 2)
            
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                    json={
                        "username": username,
                        "amount": amount,
                        "basis": "value_chain",
                        "ref": chain_id
                    }
                )
            except Exception as e:
                print(f"Failed to credit {username}: {e}")


def get_chain(chain_id: str) -> Dict[str, Any]:
    """Get value chain details"""
    
    chain = _VALUE_CHAINS.get(chain_id)
    
    if not chain:
        return {"ok": False, "error": "chain_not_found"}
    
    return {"ok": True, "chain": chain}


def get_user_chains(username: str) -> Dict[str, Any]:
    """Get all chains user participates in"""
    
    chains = []
    
    for chain in _VALUE_CHAINS.values():
        # Check if user is in any node
        if any(n.get("username") == username for n in chain.get("nodes", [])):
            chains.append(chain)
    
    chains.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    
    return {
        "ok": True,
        "username": username,
        "chains": chains,
        "count": len(chains)
    }


def get_chain_performance(chain_id: str) -> Dict[str, Any]:
    """Get chain performance analytics"""
    
    chain = _VALUE_CHAINS.get(chain_id)
    
    if not chain:
        return {"ok": False, "error": "chain_not_found"}
    
    actions = _CHAIN_PERFORMANCE.get(chain_id, [])
    
    # Calculate per-node contribution
    node_contributions = {}
    
    for action in actions:
        executor = action.get("executed_by")
        revenue = action.get("results", {}).get("revenue", 0)
        
        node_contributions.setdefault(executor, {"actions": 0, "revenue_generated": 0})
        node_contributions[executor]["actions"] += 1
        node_contributions[executor]["revenue_generated"] += revenue
    
    return {
        "ok": True,
        "chain_id": chain_id,
        "performance": chain["performance"],
        "node_contributions": node_contributions,
        "total_actions": len(actions),
        "recent_actions": actions[-10:]
    }


def get_chain_stats() -> Dict[str, Any]:
    """Get overall value chain statistics"""
    
    total_chains = len(_VALUE_CHAINS)
    active_chains = len([c for c in _VALUE_CHAINS.values() if c["status"] == "ACTIVE"])
    pending_chains = len([c for c in _VALUE_CHAINS.values() if c["status"] == "PENDING_APPROVAL"])
    
    total_revenue = sum(c["performance"]["total_revenue"] for c in _VALUE_CHAINS.values())
    
    return {
        "ok": True,
        "chains": {
            "total": total_chains,
            "active": active_chains,
            "pending": pending_chains
        },
        "total_revenue_generated": round(total_revenue, 2),
        "avg_revenue_per_chain": round(total_revenue / total_chains, 2) if total_chains > 0 else 0
    }
