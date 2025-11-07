# revenue_flows.py — AiGentsy Autonomous Money Flows
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import httpx
from log_to_jsonbin import get_user, log_agent_update, credit_aigx, append_intent_ledger

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
        
        # Credit AIGx
        credit_aigx(username, user_net, {"source": "shopify", "order_id": order_id})
        
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
    """Pay 30% royalty to original owner when clone earns"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        # Find original owner in cloneLineage
        lineage = user.get("cloneLineage", [])
        original_owner = None
        
        for entry in lineage:
            if entry.get("cloneId") == clone_id:
                original_owner = entry.get("originalOwner")
                break
        
        if not original_owner:
            return {"ok": False, "error": "original_owner_not_found"}
        
        # Calculate 30% royalty
        royalty = round(amount_usd * CLONE_ROYALTY, 2)
        user_keeps = round(amount_usd - royalty, 2)
        
        # Credit original owner
        credit_aigx(original_owner, royalty, {
            "source": "clone_royalty",
            "clone_id": clone_id,
            "clone_owner": username
        })
        
        # Credit clone owner (keeps 70%)
        credit_aigx(username, user_keeps, {
            "source": "clone_earnings",
            "clone_id": clone_id
        })
        
        # Post ledger
        append_intent_ledger(username, {
            "event": "clone_royalty_paid",
            "clone_id": clone_id,
            "total": amount_usd,
            "royalty_to_owner": royalty,
            "clone_keeps": user_keeps,
            "original_owner": original_owner,
            "ts": now_iso()
        })
        
        return {
            "ok": True,
            "royalty": royalty,
            "clone_keeps": user_keeps,
            "original_owner": original_owner
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============ EARNINGS SUMMARY ============

def get_earnings_summary(username: str) -> Dict[str, Any]:
    """Get breakdown of all earnings sources"""
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        ledger = user.get("ownership", {}).get("ledger", [])
        
        # Aggregate by source
        sources = {
            "shopify": 0.0,
            "tiktok_affiliate": 0.0,
            "amazon_affiliate": 0.0,
            "youtube_cpm": 0.0,
            "tiktok_cpm": 0.0,
            "service": 0.0,
            "staking": 0.0,
            "jv": 0.0,
            "clone_royalty": 0.0
        }
        
        for entry in ledger:
            event = entry.get("event", "")
            amount = entry.get("user_net") or entry.get("amount") or 0
            
            if "shopify" in event:
                sources["shopify"] += amount
            elif "tiktok_affiliate" in event:
                sources["tiktok_affiliate"] += amount
            elif "amazon_affiliate" in event:
                sources["amazon_affiliate"] += amount
            elif "youtube_cpm" in event:
                sources["youtube_cpm"] += amount
            elif "tiktok_cpm" in event:
                sources["tiktok_cpm"] += amount
            elif "service" in event:
                sources["service"] += amount
            elif "staking" in event:
                sources["staking"] += amount
            elif "jv" in event:
                sources["jv"] += amount
            elif "clone_royalty" in event:
                sources["clone_royalty"] += amount
        
        total = sum(sources.values())
        
        # Merge affiliate sources
        affiliate_total = sources["tiktok_affiliate"] + sources["amazon_affiliate"]
        
        # Merge CPM sources
        content_cpm_total = sources["youtube_cpm"] + sources["tiktok_cpm"]
        
        return {
            "ok": True,
            "username": username,
            "total_earned": round(total, 2),
            "sources": {
                "service": round(sources["service"], 2),
                "shopify": round(sources["shopify"], 2),
                "affiliate": round(affiliate_total, 2),
                "content_cpm": round(content_cpm_total, 2),
                "staking": round(sources["staking"], 2),
                "jv": round(sources["jv"], 2),
                "clone_royalty": round(sources["clone_royalty"], 2)
            },
            "aigx_balance": user.get("yield", {}).get("aigxEarned", 0)
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
