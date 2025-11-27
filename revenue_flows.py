# revenue_flows.py — AiGentsy Autonomous Money Flows
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import httpx
from log_to_jsonbin import get_user, log_agent_update, credit_aigx, append_intent_ledger
from outcome_oracle_max import on_event

# Platform fee (5%)
PLATFORM_FEE = 0.05
# Auto-reinvestment rate (20%)
REINVEST_RATE = 0.20
# Clone royalty rate (30%)
CLONE_ROYALTY = 0.30
# Staking return rate (10%)
STAKING_RETURN = 0.10

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# ============ REVENUE INGESTION ============

async def ingest_shopify_order(username: str, order_id: str, revenue_usd: float, cid: str = None):
    """Ingest Shopify order revenue and auto-split"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        # Calculate splits
        platform_cut = round(revenue_usd * PLATFORM_FEE, 2)
        reinvest_amount = round(revenue_usd * REINVEST_RATE, 2)
        user_net = round(revenue_usd - platform_cut - reinvest_amount, 2)
        
        # Update user earnings
        user.setdefault("yield", {})
        user["yield"]["aigxEarned"] = user["yield"].get("aigxEarned", 0) + user_net
        
        # Update revenue tracking
        user.setdefault("revenue", {"total": 0.0, "bySource": {}})
        user["revenue"]["total"] = round(user["revenue"]["total"] + user_net, 2)
        user["revenue"]["bySource"]["shopify"] = round(
            user["revenue"]["bySource"].get("shopify", 0.0) + user_net, 2
        )
        
        # Save updated user
        log_agent_update(user)

        # Post ledger entry
        append_intent_ledger(username, {
            "event": "shopify_revenue",
            "order_id": order_id,
            "revenue_usd": revenue_usd,
            "platform_fee": platform_cut,
            "reinvestment": reinvest_amount,
            "user_net": user_net,
            "cid": cid,
            "ts": now_iso()
        })

        # Check unlock milestones
        await check_revenue_milestones(username, user["revenue"]["total"])
        # Credit AIGx
        credit_aigx(username, user_net, {"source": "shopify", "order_id": order_id})
        
        # ✅ ADD THIS BLOCK:
        # Track PAID outcome
        on_event({
            "kind": "PAID",
            "username": username,
            "amount_usd": user_net,
            "source": "shopify",
            "order_id": order_id
        })
        
        # Trigger R³ reinvestment
        await trigger_r3_reinvestment(username, reinvest_amount)
        
        return {
            "ok": True,
            "revenue": revenue_usd,
            "splits": {
                "platform": platform_cut,
                "reinvest": reinvest_amount,
                "user": user_net
            }
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def ingest_affiliate_commission(username: str, source: str, revenue_usd: float, product_id: str = None):
    """Ingest TikTok/Amazon affiliate commission"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        # Calculate splits
        platform_cut = round(revenue_usd * PLATFORM_FEE, 2)
        reinvest_amount = round(revenue_usd * REINVEST_RATE, 2)
        user_net = round(revenue_usd - platform_cut - reinvest_amount, 2)
        
        # Update earnings
        user.setdefault("yield", {})
        user["yield"]["aigxEarned"] = user["yield"].get("aigxEarned", 0) + user_net
        
        # Update revenue tracking
        user.setdefault("revenue", {"total": 0.0, "bySource": {}})
        user["revenue"]["total"] = round(user["revenue"]["total"] + user_net, 2)
        user["revenue"]["bySource"]["affiliate"] = round(
            user["revenue"]["bySource"].get("affiliate", 0.0) + user_net, 2
        )
        
        # Save updated user
        log_agent_update(user)
        
        # Post ledger
        append_intent_ledger(username, {
            "event": f"{source}_affiliate",
            "revenue_usd": revenue_usd,
            "product_id": product_id,
            "platform_fee": platform_cut,
            "reinvestment": reinvest_amount,
            "user_net": user_net,
            "ts": now_iso()
        })
        
        # Credit AIGx
        credit_aigx(username, user_net, {"source": source, "product_id": product_id})

        # Check unlock milestones
        await check_revenue_milestones(username, user["revenue"]["total"])
        
        # ✅ ADD THIS BLOCK:
        # Track PAID outcome
        on_event({
            "kind": "PAID",
            "username": username,
            "amount_usd": user_net,
            "source": f"{source}_affiliate",
            "product_id": product_id
        })
        
        # Trigger reinvestment
        await trigger_r3_reinvestment(username, reinvest_amount)
        
        return {"ok": True, "revenue": revenue_usd, "user_net": user_net}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def ingest_content_cpm(username: str, platform: str, views: int, cpm_rate: float):
    """Ingest YouTube/TikTok CPM revenue"""
    try:
        revenue_usd = round((views / 1000) * cpm_rate, 2)
        
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        # Calculate splits
        platform_cut = round(revenue_usd * PLATFORM_FEE, 2)
        reinvest_amount = round(revenue_usd * REINVEST_RATE, 2)
        user_net = round(revenue_usd - platform_cut - reinvest_amount, 2)
        
        # Update earnings
        user.setdefault("yield", {})
        user["yield"]["aigxEarned"] = user["yield"].get("aigxEarned", 0) + user_net
        
        # Update revenue tracking
        user.setdefault("revenue", {"total": 0.0, "bySource": {}})
        user["revenue"]["total"] = round(user["revenue"]["total"] + user_net, 2)
        user["revenue"]["bySource"]["contentCPM"] = round(
            user["revenue"]["bySource"].get("contentCPM", 0.0) + user_net, 2
        )
        
        # Save updated user
        log_agent_update(user)
        
        # Post ledger
        append_intent_ledger(username, {
            "event": f"{platform}_cpm",
            "views": views,
            "cpm_rate": cpm_rate,
            "revenue_usd": revenue_usd,
            "platform_fee": platform_cut,
            "reinvestment": reinvest_amount,
            "user_net": user_net,
            "ts": now_iso()
        })
        
        # Credit AIGx
        credit_aigx(username, user_net, {"source": platform, "views": views})

        # Check unlock milestones
        await check_revenue_milestones(username, user["revenue"]["total"])
        
        # ✅ ADD THIS BLOCK:
        # Track PAID outcome
        on_event({
            "kind": "PAID",
            "username": username,
            "amount_usd": user_net,
            "source": f"{platform}_cpm",
            "views": views
        })
        
        # Trigger reinvestment
        await trigger_r3_reinvestment(username, reinvest_amount)
        
        return {"ok": True, "revenue": revenue_usd, "views": views, "user_net": user_net}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def ingest_service_payment(username: str, invoice_id: str, amount_usd: float):
    """Ingest direct service payment (consulting, design, etc.)"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        # Calculate splits
        platform_cut = round(amount_usd * PLATFORM_FEE, 2)
        reinvest_amount = round(amount_usd * REINVEST_RATE, 2)
        user_net = round(amount_usd - platform_cut - reinvest_amount, 2)
        
        # Update earnings
        user.setdefault("yield", {})
        user["yield"]["aigxEarned"] = user["yield"].get("aigxEarned", 0) + user_net
        
        # Update revenue tracking
        user.setdefault("revenue", {"total": 0.0, "bySource": {}})
        user["revenue"]["total"] = round(user["revenue"]["total"] + user_net, 2)
        user["revenue"]["bySource"]["services"] = round(
            user["revenue"]["bySource"].get("services", 0.0) + user_net, 2
        )
        
        # Save updated user
        log_agent_update(user)
        
        # Post ledger
        append_intent_ledger(username, {
            "event": "service_payment",
            "invoice_id": invoice_id,
            "amount_usd": amount_usd,
            "platform_fee": platform_cut,
            "reinvestment": reinvest_amount,
            "user_net": user_net,
            "ts": now_iso()
        })
        
        # Credit AIGx
        credit_aigx(username, user_net, {"source": "service", "invoice_id": invoice_id})

        # Check unlock milestones
        await check_revenue_milestones(username, user["revenue"]["total"])
        
        # ✅ ADD THIS BLOCK:
        # Track PAID outcome
        on_event({
            "kind": "PAID",
            "username": username,
            "amount_usd": user_net,
            "source": "service_payment",
            "invoice_id": invoice_id
        })
        
        # Trigger reinvestment
        await trigger_r3_reinvestment(username, reinvest_amount)
        
        return {"ok": True, "amount": amount_usd, "user_net": user_net}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def distribute_staking_returns(username: str, amount_usd: float):
    """Distribute staking returns (10% of agent's earnings to stakers)"""
    try:
        from log_to_jsonbin import list_users
        
        # Find all users staking this agent
        all_users = list_users()
        stakers = []
        total_staked = 0
        
        for u in all_users:
            staked = u.get("wallet", {}).get("staked", 0)
            staking_target = u.get("staking_target")
            
            if staking_target == username and staked > 0:
                stakers.append({"username": u.get("username"), "staked": staked})
                total_staked += staked
        
        if total_staked == 0:
            return {"ok": True, "message": "no_stakers"}
        
        # Calculate 10% pool
        pool = round(amount_usd * STAKING_RETURN, 2)
        
        # Distribute proportionally
        distributions = []
        for staker in stakers:
            share = round((staker["staked"] / total_staked) * pool, 2)
            
            # Credit staker
            credit_aigx(staker["username"], share, {
                "source": "staking_return",
                "agent": username,
                "staked_amount": staker["staked"]
            })
            
            distributions.append({
                "username": staker["username"],
                "amount": share
            })
        
        # Post ledger for agent
        append_intent_ledger(username, {
            "event": "staking_distribution",
            "pool": pool,
            "stakers": len(stakers),
            "distributions": distributions,
            "ts": now_iso()
        })
        
        return {"ok": True, "pool": pool, "distributions": distributions}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============ AUTO-REINVESTMENT ============

async def trigger_r3_reinvestment(username: str, budget_usd: float):
    """Trigger R³ router to reallocate budget"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "http://localhost:8000/r3/allocate",
                json={"user_id": username, "budget_usd": budget_usd}
            )
            return r.json()
    except Exception as e:
        print(f"R³ reinvestment failed: {e}")
        return {"ok": False, "error": str(e)}


# ============ JV REVENUE SPLIT ============

async def split_jv_revenue(username: str, amount_usd: float, jv_id: str):
    """Split revenue with JV partners"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        # Find JV mesh entry
        jv_mesh = user.get("jvMesh", [])
        jv = next((j for j in jv_mesh if j.get("id") == jv_id), None)
        
        if not jv:
            return {"ok": False, "error": "jv_not_found"}
        
        # Get split ratios
        splits = jv.get("split", {})
        partner_a = jv.get("a")
        partner_b = jv.get("b")
        
        # Calculate amounts
        a_amount = round(amount_usd * splits.get("a", 0.5), 2)
        b_amount = round(amount_usd * splits.get("b", 0.5), 2)
        
        # Credit partners
        if partner_a:
            credit_aigx(partner_a, a_amount, {"source": "jv_split", "jv_id": jv_id})
        if partner_b:
            credit_aigx(partner_b, b_amount, {"source": "jv_split", "jv_id": jv_id})
        
        # Update revenue tracking for both partners
        if partner_a:
            a_user = get_user(partner_a)
            if a_user:
                a_user.setdefault("revenue", {"total": 0.0, "bySource": {}})
                a_user["revenue"]["total"] = round(a_user["revenue"]["total"] + a_amount, 2)
                a_user["revenue"]["bySource"]["jvMesh"] = round(
                    a_user["revenue"]["bySource"].get("jvMesh", 0.0) + a_amount, 2
                )
                log_agent_update(a_user)
                await check_revenue_milestones(partner_a, a_user["revenue"]["total"])
        
        if partner_b:
            b_user = get_user(partner_b)
            if b_user:
                b_user.setdefault("revenue", {"total": 0.0, "bySource": {}})
                b_user["revenue"]["total"] = round(b_user["revenue"]["total"] + b_amount, 2)
                b_user["revenue"]["bySource"]["jvMesh"] = round(
                    b_user["revenue"]["bySource"].get("jvMesh", 0.0) + b_amount, 2
                )
                log_agent_update(b_user)
                await check_revenue_milestones(partner_b, b_user["revenue"]["total"])
                
        # Post ledger
        append_intent_ledger(username, {
            "event": "jv_revenue_split",
            "jv_id": jv_id,
            "total": amount_usd,
            "splits": {
                partner_a: a_amount,
                partner_b: b_amount
            },
            "ts": now_iso()
        })
        
        return {
            "ok": True,
            "jv_id": jv_id,
            "splits": {
                partner_a: a_amount,
                partner_b: b_amount
            }
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============ CLONE ROYALTY ============

async def distribute_clone_royalty(username: str, amount_usd: float, clone_id: str):
    """Pay multi-generation royalties to clone lineage (30% → 10% → 3%)"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        lineage = user.get("cloneLineage", [])
        
        # Build lineage chain
        chain = []
        for entry in lineage:
            if entry.get("cloneId") == clone_id:
                chain.append({
                    "generation": 1,
                    "owner": entry.get("originalOwner"),
                    "rate": 0.30
                })
                
                # Check if original owner has lineage (grandparent)
                grandparent = entry.get("grandparent")
                if grandparent:
                    chain.append({
                        "generation": 2,
                        "owner": grandparent,
                        "rate": 0.10
                    })
                
                # Check for great-grandparent
                great_grandparent = entry.get("great_grandparent")
                if great_grandparent:
                    chain.append({
                        "generation": 3,
                        "owner": great_grandparent,
                        "rate": 0.03
                    })
                
                break
        
        if not chain:
            return {"ok": False, "error": "lineage_not_found"}
        
        # Calculate payouts
        distributions = []
        total_royalty = 0.0
        
        for ancestor in chain:
            royalty = round(amount_usd * ancestor["rate"], 2)
            total_royalty += royalty
            
            # Credit ancestor
            credit_aigx(ancestor["owner"], royalty, {
                "source": "clone_royalty",
                "clone_id": clone_id,
                "clone_owner": username,
                "generation": ancestor["generation"]
            })
            
            distributions.append({
                "generation": ancestor["generation"],
                "owner": ancestor["owner"],
                "royalty": royalty,
                "rate": ancestor["rate"]
            })
        
        # Clone owner keeps remainder
        clone_keeps = round(amount_usd - total_royalty, 2)
        credit_aigx(username, clone_keeps, {
            "source": "clone_earnings",
            "clone_id": clone_id
        })
        
        # Post ledger
        append_intent_ledger(username, {
            "event": "clone_royalty_paid_multi_gen",
            "clone_id": clone_id,
            "total": amount_usd,
            "distributions": distributions,
            "clone_keeps": clone_keeps,
            "ts": now_iso()
        })
        
        return {
            "ok": True,
            "total_royalty": round(total_royalty, 2),
            "clone_keeps": clone_keeps,
            "distributions": distributions
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def register_clone_lineage(
    clone_owner: str,
    clone_id: str,
    original_owner: str,
    generation: int = 1
) -> Dict[str, Any]:
    """Register clone with multi-generation lineage tracking"""
    try:
        from log_to_jsonbin import get_user, log_agent_update
        
        clone_user = get_user(clone_owner)
        if not clone_user:
            return {"ok": False, "error": "clone_owner_not_found"}
        
        # Get original owner's lineage to build chain
        original_user = get_user(original_owner)
        grandparent = None
        great_grandparent = None
        
        if original_user and generation == 1:
            # Check if original is also a clone (has lineage)
            orig_lineage = original_user.get("cloneLineage", [])
            if orig_lineage:
                # Original owner is a clone, so clone owner is generation 2+
                parent_entry = orig_lineage[0]  # First entry is immediate parent
                grandparent = parent_entry.get("originalOwner")
                great_grandparent = parent_entry.get("grandparent")
        
        # Add lineage entry
        lineage_entry = {
            "cloneId": clone_id,
            "originalOwner": original_owner,
            "generation": generation,
            "grandparent": grandparent,
            "great_grandparent": great_grandparent,
            "clonedAt": now_iso()
        }
        
        clone_user.setdefault("cloneLineage", []).append(lineage_entry)
        
        # Update clone user
        log_agent_update(clone_user)
        
        return {
            "ok": True,
            "lineage_entry": lineage_entry,
            "royalty_chain": [
                {"generation": 1, "owner": original_owner, "rate": 0.30},
                {"generation": 2, "owner": grandparent, "rate": 0.10} if grandparent else None,
                {"generation": 3, "owner": great_grandparent, "rate": 0.03} if great_grandparent else None
            ]
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
 # ============ AME REVENUE ============

async def ingest_ame_conversion(username: str, pitch_id: str, amount_usd: float, recipient: str):
    """Ingest revenue from AME auto-sales pitch conversion"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        # Calculate splits
        platform_cut = round(amount_usd * PLATFORM_FEE, 2)
        reinvest_amount = round(amount_usd * REINVEST_RATE, 2)
        user_net = round(amount_usd - platform_cut - reinvest_amount, 2)
        
        # Update earnings
        user.setdefault("yield", {})
        user["yield"]["aigxEarned"] = user["yield"].get("aigxEarned", 0) + user_net
        
        # Update revenue tracking
        user.setdefault("revenue", {"total": 0.0, "bySource": {}})
        user["revenue"]["total"] = round(user["revenue"]["total"] + user_net, 2)
        user["revenue"]["bySource"]["ame"] = round(
            user["revenue"]["bySource"].get("ame", 0.0) + user_net, 2
        )
        
        # Post ledger
        append_intent_ledger(username, {
            "event": "ame_conversion",
            "pitch_id": pitch_id,
            "recipient": recipient,
            "revenue_usd": amount_usd,
            "platform_fee": platform_cut,
            "reinvestment": reinvest_amount,
            "user_net": user_net,
            "ts": now_iso()
        })
        
        # Credit AIGx
        credit_aigx(username, user_net, {"source": "ame", "pitch_id": pitch_id})
        
        # Save updated user
        log_agent_update(user)
        
        # Trigger reinvestment
        await trigger_r3_reinvestment(username, reinvest_amount)
        
        # Check unlock milestones
        await check_revenue_milestones(username, user["revenue"]["total"])
        
        # ✅ ADD THIS BLOCK:
        # Track PAID outcome
        on_event({
            "kind": "PAID",
            "username": username,
            "amount_usd": user_net,
            "source": "ame_conversion",
            "pitch_id": pitch_id,
            "recipient": recipient
        })
        
        return {
            "ok": True,
            "revenue": amount_usd,
            "user_net": user_net,
            "total_revenue": user["revenue"]["total"]
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============ INTENT EXCHANGE REVENUE ============

async def ingest_intent_settlement(username: str, intent_id: str, amount_usd: float, buyer: str):
    """Ingest revenue from intent exchange contract settlement"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        # Calculate splits
        platform_cut = round(amount_usd * PLATFORM_FEE, 2)
        reinvest_amount = round(amount_usd * REINVEST_RATE, 2)
        user_net = round(amount_usd - platform_cut - reinvest_amount, 2)
        
        # Update earnings
        user.setdefault("yield", {})
        user["yield"]["aigxEarned"] = user["yield"].get("aigxEarned", 0) + user_net
        
        # Update revenue tracking
        user.setdefault("revenue", {"total": 0.0, "bySource": {}})
        user["revenue"]["total"] = round(user["revenue"]["total"] + user_net, 2)
        user["revenue"]["bySource"]["intentExchange"] = round(
            user["revenue"]["bySource"].get("intentExchange", 0.0) + user_net, 2
        )
        
        # Post ledger
        append_intent_ledger(username, {
            "event": "intent_settlement",
            "intent_id": intent_id,
            "buyer": buyer,
            "revenue_usd": amount_usd,
            "platform_fee": platform_cut,
            "reinvestment": reinvest_amount,
            "user_net": user_net,
            "ts": now_iso()
        })
        
        # Credit AIGx
        credit_aigx(username, user_net, {"source": "intent_exchange", "intent_id": intent_id})
        
        # Save updated user
        log_agent_update(user)
        
        # Trigger reinvestment
        await trigger_r3_reinvestment(username, reinvest_amount)
        
        # Check unlock milestones
        await check_revenue_milestones(username, user["revenue"]["total"])
        
        # ✅ ADD THIS BLOCK:
        # Track PAID outcome
        on_event({
            "kind": "PAID",
            "username": username,
            "amount_usd": user_net,
            "source": "intent_exchange",
            "intent_id": intent_id,
            "buyer": buyer
        })
        
        return {
            "ok": True,
            "revenue": amount_usd,
            "user_net": user_net,
            "total_revenue": user["revenue"]["total"]
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============ MILESTONE UNLOCK SYSTEM ============

async def check_revenue_milestones(username: str, total_revenue: float):
    """Check if user hit revenue milestones and trigger unlocks"""
    try:
        user = get_user(username)
        if not user:
            return
        
        unlocked = []
        
        # Milestone 1: First $100 → Unlock R³ Autopilot
        if total_revenue >= 100 and not user.get("runtimeFlags", {}).get("r3AutopilotEnabled"):
            user.setdefault("runtimeFlags", {})
            user["runtimeFlags"]["r3AutopilotEnabled"] = True
            unlocked.append("r3_autopilot")
        
        # Milestone 2: $500 → Unlock Advanced Analytics
        if total_revenue >= 500 and not user.get("runtimeFlags", {}).get("advancedAnalyticsEnabled"):
            user.setdefault("runtimeFlags", {})
            user["runtimeFlags"]["advancedAnalyticsEnabled"] = True
            unlocked.append("advanced_analytics")
        
        # Milestone 3: $1,000 → Unlock Template Publishing (Franchise)
        if total_revenue >= 1000 and not user.get("runtimeFlags", {}).get("templatePublishingEnabled"):
            user.setdefault("runtimeFlags", {})
            user["runtimeFlags"]["templatePublishingEnabled"] = True
            unlocked.append("template_publishing")
        
        # Milestone 4: $2,500 → Unlock MetaHive Premium
        if total_revenue >= 2500 and not user.get("runtimeFlags", {}).get("metaHivePremium"):
            user.setdefault("runtimeFlags", {})
            user["runtimeFlags"]["metaHivePremium"] = True
            unlocked.append("metahive_premium")
        
        # Milestone 5: $5,000 → Unlock White Label
        if total_revenue >= 5000 and not user.get("runtimeFlags", {}).get("whiteLabelEnabled"):
            user.setdefault("runtimeFlags", {})
            user["runtimeFlags"]["whiteLabelEnabled"] = True
            unlocked.append("white_label")
        
        if unlocked:
            # Save user with new unlocks
            log_agent_update(user)
            
            # Post unlock event
            append_intent_ledger(username, {
                "event": "milestone_unlocks",
                "total_revenue": total_revenue,
                "unlocked": unlocked,
                "ts": now_iso()
            })
            
            print(f"🎉 {username} unlocked: {', '.join(unlocked)}")
        
        return {"ok": True, "unlocked": unlocked}
    
    except Exception as e:
        print(f"Milestone check error: {e}")
        return {"ok": False, "error": str(e)}
        
# ============ EARNINGS SUMMARY ============

def get_earnings_summary(username: str) -> Dict[str, Any]:
    """Get breakdown of all earnings sources with 7-day holdback"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        ledger = user.get("ownership", {}).get("ledger", [])
        
        # Calculate holdback cutoff (7 days ago)
        from datetime import datetime, timedelta, timezone
        holdback_days = 7
        cutoff = datetime.now(timezone.utc) - timedelta(days=holdback_days)
        
        # Aggregate by source
        sources = {
            "shopify": {"total": 0.0, "eligible": 0.0},
            "tiktok_affiliate": {"total": 0.0, "eligible": 0.0},
            "amazon_affiliate": {"total": 0.0, "eligible": 0.0},
            "youtube_cpm": {"total": 0.0, "eligible": 0.0},
            "tiktok_cpm": {"total": 0.0, "eligible": 0.0},
            "service": {"total": 0.0, "eligible": 0.0},
            "staking": {"total": 0.0, "eligible": 0.0},
            "jv": {"total": 0.0, "eligible": 0.0},
            "clone_royalty": {"total": 0.0, "eligible": 0.0}
        }
        
        for entry in ledger:
            event = entry.get("event", "")
            amount = entry.get("user_net") or entry.get("amount") or 0
            
            # Parse timestamp
            ts_str = entry.get("ts", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except:
                ts = datetime.now(timezone.utc)
            
            is_eligible = ts < cutoff
            
            # Categorize by event type
            if "shopify" in event:
                sources["shopify"]["total"] += amount
                if is_eligible:
                    sources["shopify"]["eligible"] += amount
            elif "tiktok_affiliate" in event:
                sources["tiktok_affiliate"]["total"] += amount
                if is_eligible:
                    sources["tiktok_affiliate"]["eligible"] += amount
            elif "amazon_affiliate" in event:
                sources["amazon_affiliate"]["total"] += amount
                if is_eligible:
                    sources["amazon_affiliate"]["eligible"] += amount
            elif "youtube_cpm" in event:
                sources["youtube_cpm"]["total"] += amount
                if is_eligible:
                    sources["youtube_cpm"]["eligible"] += amount
            elif "tiktok_cpm" in event:
                sources["tiktok_cpm"]["total"] += amount
                if is_eligible:
                    sources["tiktok_cpm"]["eligible"] += amount
            elif "service" in event:
                sources["service"]["total"] += amount
                if is_eligible:
                    sources["service"]["eligible"] += amount
            elif "staking" in event:
                sources["staking"]["total"] += amount
                if is_eligible:
                    sources["staking"]["eligible"] += amount
            elif "jv" in event:
                sources["jv"]["total"] += amount
                if is_eligible:
                    sources["jv"]["eligible"] += amount
            elif "clone_royalty" in event:
                sources["clone_royalty"]["total"] += amount
                if is_eligible:
                    sources["clone_royalty"]["eligible"] += amount
        
        # Calculate totals
        total_earned = sum(s["total"] for s in sources.values())
        eligible_earned = sum(s["eligible"] for s in sources.values())
        held_back = total_earned - eligible_earned
        
        # Merge affiliate sources
        affiliate_total = sources["tiktok_affiliate"]["total"] + sources["amazon_affiliate"]["total"]
        affiliate_eligible = sources["tiktok_affiliate"]["eligible"] + sources["amazon_affiliate"]["eligible"]
        
        # Merge CPM sources
        content_cpm_total = sources["youtube_cpm"]["total"] + sources["tiktok_cpm"]["total"]
        content_cpm_eligible = sources["youtube_cpm"]["eligible"] + sources["tiktok_cpm"]["eligible"]
        
        return {
            "ok": True,
            "username": username,
            "total_earned": round(total_earned, 2),
            "eligible_earned": round(eligible_earned, 2),
            "held_back": round(held_back, 2),
            "holdback_days": holdback_days,
            "sources": {
                "service": round(sources["service"]["eligible"], 2),
                "shopify": round(sources["shopify"]["eligible"], 2),
                "affiliate": round(affiliate_eligible, 2),
                "content_cpm": round(content_cpm_eligible, 2),
                "staking": round(sources["staking"]["eligible"], 2),
                "jv": round(sources["jv"]["eligible"], 2),
                "clone_royalty": round(sources["clone_royalty"]["eligible"], 2)
            },
            "sources_total": {
                "service": round(sources["service"]["total"], 2),
                "shopify": round(sources["shopify"]["total"], 2),
                "affiliate": round(affiliate_total, 2),
                "content_cpm": round(content_cpm_total, 2),
                "staking": round(sources["staking"]["total"], 2),
                "jv": round(sources["jv"]["total"], 2),
                "clone_royalty": round(sources["clone_royalty"]["total"], 2)
            },
            "aigx_balance": user.get("yield", {}).get("aigxEarned", 0)
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
