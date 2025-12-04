"""
Outcome Oracle (MAX) — unified & hardened + Task 7 Funnel Tracking
-----------------------------------------
- Backward compatible `on_event(evt: dict)` entrypoint
- Credits AIGx from USD with env-configurable multiplier
- Autostake v2 with weekly cap
- Records bundle outcomes (A/B tuner), mesh sessions, R3 allocation
- Handles INTENT_*, DEALGRAPH_*, FRANCHISE_*, PROPOSAL_*, COOP_* events
- NEW: 4-stage outcome funnel (CLICKED → AUTHORIZED → DELIVERED → PAID)
- NEW: Outcome-based feature unlocks (OCL, Factoring, IPVault, Certification)
- Dual logging: events + JSONBin (safe fallbacks)
- Graceful degradation if JSONBIN_* envs missing
"""

from __future__ import annotations
import os, json, uuid, requests, datetime as dt
from typing import Any, Dict, List, Optional

# ---------- Utils ----------
def _now() -> str:
    return dt.datetime.utcnow().isoformat()+"Z"

def _uid() -> str:
    return str(uuid.uuid4())

def _env_float(name: str, dflt: float) -> float:
    try:
        return float(os.getenv(name, dflt))
    except Exception:
        return dflt

def _emit(kind: str, data: dict) -> None:
    # Try event bus
    try:
        from events import emit as _emit_impl
        _emit_impl(kind, data)
    except Exception:
        pass
    # Try JSONBin logger
    try:
        from log_to_jsonbin_aam_patched import log_event
        log_event({"kind": kind, **(data or {})})
    except Exception:
        pass

# ---------- JSONBin I/O ----------
JSONBIN_URL = os.getenv("JSONBIN_URL","").strip()
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET","").strip()
HTTP = requests.Session()

def _load_users() -> List[Dict[str, Any]]:
    if not JSONBIN_URL:
        return []
    try:
        r = HTTP.get(JSONBIN_URL, headers={"X-Master-Key": JSONBIN_SECRET}, timeout=20)
        x = r.json()
        return x.get("record") if isinstance(x, dict) else (x or [])
    except Exception:
        return []

def _save_users(users: List[Dict[str, Any]]) -> bool:
    if not JSONBIN_URL:
        return False
    try:
        r = HTTP.put(JSONBIN_URL, json={"record": users}, headers={"X-Master-Key": JSONBIN_SECRET}, timeout=20)
        return (r.status_code//100) == 2
    except Exception:
        return False

def _find_user(users: List[Dict[str, Any]], username: Optional[str]) -> Optional[Dict[str, Any]]:
    uname = (username or "").strip()
    for u in users:
        u_un = u.get("username") or (u.get("consent",{}) or {}).get("username")
        if u_un == uname:
            return u
    # fallback: first record
    return users[0] if users else None

# ---------- Economics ----------
AIGX_PER_USD = _env_float("AIGX_PER_USD", 1.0)

def credit_aigx(user: Dict[str, Any], amount_usd: float, reason: str) -> int:
    aigx = int(round(amount_usd * AIGX_PER_USD))
    y = user.setdefault("yield", {})
    y["aigxEarned"] = int(y.get("aigxEarned", 0)) + aigx
    user.setdefault("transactions",{}).setdefault("yieldEvents",[]).append({
        "id": _uid(), "ts": _now(), "aigx": aigx, "usd": float(amount_usd), "reason": reason
    })
    return aigx

def autostake(user: Dict[str, Any], paid_usd: float) -> float:
    pol = user.setdefault("autoStake_policy", {"ratio": 0.25, "weekly_cap_usd": 50, "enabled": True})
    if not pol.get("enabled", True):
        return 0.0
    amt = min(float(paid_usd) * float(pol.get("ratio", 0.25)), float(pol.get("weekly_cap_usd", 50.0)))
    wallet = user.setdefault("wallet", {})
    wallet["staked"] = float(wallet.get("staked", 0)) + float(amt)
    # Signal to budget manager (optional listener)
    _emit("AUTOSTAKE_TOPUP", {"user": user.get("username") or (user.get("consent") or {}).get("username"), "usd": amt})
    return amt

# ---------- Recorders ----------
def _record_bundle(user: Dict[str, Any], bundle_id: str, rev_usd: float) -> None:
    b = user.setdefault("bundle_experiments", {}).setdefault(bundle_id, {"rev_usd": 0.0, "events": 0})
    b["rev_usd"] = float(b["rev_usd"]) + float(rev_usd)
    b["events"] = int(b["events"]) + 1

def _record_mesh(user: Dict[str, Any], mesh_id: str, kind: str, usd: float) -> None:
    user.setdefault("mesh", {}).setdefault("sessions", []).append({"id": mesh_id, "kind": kind, "usd": float(usd), "ts": _now()})

def _record_intent(user: Dict[str, Any], evt: Dict[str, Any]) -> None:
    user.setdefault("intents", []).append({"ts": _now(), **evt})

def _record_dealgraph(user: Dict[str, Any], evt: Dict[str, Any]) -> None:
    user.setdefault("dealGraph", {"nodes": [], "edges": [], "revSplit": []}).setdefault("events", []).append({"ts": _now(), **evt})

def _record_franchise(user: Dict[str, Any], evt: Dict[str, Any]) -> None:
    user.setdefault("franchise_packs", []).append({"ts": _now(), **evt})

def _record_r3(user: Dict[str, Any], evt: Dict[str, Any]) -> None:
    r3 = user.setdefault("r3", {"budget_usd": 0, "last_allocation": None})
    if evt.get("kind") == "R3_ALLOCATED":
        r3["last_allocation"] = {"ts": _now(), "usd": evt.get("usd", 0), "channel": evt.get("channel")}

def _record_proposal(user: Dict[str, Any], evt: Dict[str, Any]) -> None:
    ph = user.setdefault("proposal", {}).setdefault("history", [])
    ph.append({"ts": _now(), **evt})

def _record_coop(user: Dict[str, Any], evt: Dict[str, Any]) -> None:
    coop = user.setdefault("coop", {"pool_usd": 0, "sponsors": []})
    if evt["kind"] == "COOP_SPENT":
        # purely informational; real pool tracked server-side
        coop["pool_usd"] = float(coop.get("pool_usd", 0)) - float(evt.get("usd", 0))

# ---------- NEW: TASK 7 - Outcome Funnel Tracking ----------
def _track_funnel_stage(user: Dict[str, Any], stage: str, metadata: dict) -> None:
    """Track CLICKED → AUTHORIZED → DELIVERED → PAID funnel stages"""
    
    # Initialize funnel if not exists
    funnel = user.setdefault("outcomeFunnel", {
        "clicked": 0,
        "authorized": 0,
        "delivered": 0,
        "paid": 0
    })
    
    # Increment stage counter
    stage_key = stage.lower()
    if stage_key in funnel:
        funnel[stage_key] = funnel.get(stage_key, 0) + 1
    
    # Log detailed funnel event
    user.setdefault("funnel_history", []).append({
        "stage": stage,
        "ts": _now(),
        "source": metadata.get("source", "unknown"),
        "amount_usd": metadata.get("amount_usd", 0),
        "id": metadata.get("id", _uid())
    })
    
    print(f"📊 Funnel tracked: {user.get('username')} → {stage} (count: {funnel[stage_key]})")

# ---------- NEW: TASK 7 - Outcome-Based Unlocks ----------
def _check_unlocks(user: Dict[str, Any]) -> List[str]:
    """Check outcome milestones and unlock financial tools"""
    
    funnel = user.get("outcomeFunnel", {})
    paid = funnel.get("paid", 0)
    delivered = funnel.get("delivered", 0)
    
    unlocked = []
    
    # ========== OCL (Outcome Credit Line) ==========
    
    # 1st PAID → Unlock OCL Phase 1 (AIGx Credit)
    if paid >= 1 and not user.get("ocl", {}).get("enabled"):
        user.setdefault("ocl", {})
        user["ocl"]["enabled"] = True
        user["ocl"]["phase"] = "aigx_credit"
        user["ocl"]["creditLine"] = 2000  # 2,000 AIGx
        user["ocl"]["borrowed"] = 0
        user["ocl"]["collateral"] = {
            "aigxLocked": 0,
            "performanceBonds": []
        }
        user["ocl"]["repayment"] = {
            "rate": 0.10,
            "autoDeduct": True
        }
        unlocked.append("ocl_aigx_credit")
        print(f"🎉 {user.get('username')} unlocked OCL Phase 1 (AIGx Credit): 2,000 AIGx credit line")
    
    # Grow OCL credit line with each PAID outcome (+500 AIGx per deal)
    if paid > 1 and user.get("ocl", {}).get("enabled"):
        new_credit = 2000 + (500 * (paid - 1))
        max_credit = 50000  # Cap at 50K AIGx
        if new_credit > user["ocl"].get("creditLine", 0):
            old_credit = user["ocl"]["creditLine"]
            user["ocl"]["creditLine"] = min(new_credit, max_credit)
            print(f"📈 {user.get('username')} OCL credit line grew: {old_credit} → {user['ocl']['creditLine']} AIGx")
    
    # 5th PAID → Upgrade OCL to Phase 2 (Hybrid Fiat)
    if paid >= 5 and user.get("ocl", {}).get("phase") == "aigx_credit":
        user["ocl"]["phase"] = "hybrid_fiat"
        user["ocl"]["fiatAdvanceEnabled"] = True
        user["ocl"]["collateralRatio"] = 1.5  # 1.5 AIGx per $1 fiat
        unlocked.append("ocl_fiat_upgrade")
        print(f"🎉 {user.get('username')} unlocked OCL Phase 2 (Hybrid Fiat): Fiat advances enabled")
    
    # ========== FACTORING ==========
    
    # 1st DELIVERED → Unlock Factoring Phase 1 (AIGx Advance)
    if delivered >= 1 and not user.get("factoring", {}).get("enabled"):
        user.setdefault("factoring", {})
        user["factoring"]["enabled"] = True
        user["factoring"]["phase"] = "aigx_advance"
        user["factoring"]["advanceRate"] = 0.80  # Get 80% immediately
        user["factoring"]["holdbackRate"] = 0.20  # 20% held
        user["factoring"]["fee"] = 0.05  # 5% platform fee
        unlocked.append("factoring_aigx_advance")
        print(f"🎉 {user.get('username')} unlocked Factoring Phase 1 (AIGx Advance): 80% immediate, 20% holdback")
    
    # 5th PAID → Upgrade Factoring to Phase 2 (Hybrid Fiat)
    if paid >= 5 and user.get("factoring", {}).get("phase") == "aigx_advance":
        user["factoring"]["phase"] = "hybrid_fiat"
        user["factoring"]["fiatEnabled"] = True
        unlocked.append("factoring_fiat_upgrade")
        print(f"🎉 {user.get('username')} unlocked Factoring Phase 2 (Hybrid Fiat): Fiat factoring enabled")
    
    # ========== IP VAULT ==========
    
    # 3rd PAID → Unlock IPVault (Passive Royalties)
    if paid >= 3 and not user.get("ipVault", {}).get("enabled"):
        user.setdefault("ipVault", {})
        user["ipVault"]["enabled"] = True
        user["ipVault"]["royaltyRate"] = 0.70  # User gets 70%, platform 30%
        user["ipVault"]["assets"] = []
        unlocked.append("ip_vault")
        print(f"🎉 {user.get('username')} unlocked IPVault: Start earning passive royalties (70% rate)")
    
    # ========== CERTIFICATION ==========
    
    # 10th PAID → Certification (TODO: Add on-time rate check)
    if paid >= 10 and not user.get("certification", {}).get("enabled"):
        user.setdefault("certification", {})
        user["certification"]["enabled"] = True
        user["certification"]["tier"] = "aigentsy_specialist"
        user["certification"]["badge"] = "verified_professional"
        user["certification"]["unlockedAt"] = _now()
        unlocked.append("certification")
        print(f"🎉 {user.get('username')} unlocked Certification: AiGentsy Specialist badge")
    
    # ========== FUTURE UNLOCKS (Placeholders) ==========
    
    # 20th PAID → Phase 3 Full Lending
    if paid >= 20 and user.get("ocl", {}).get("phase") == "hybrid_fiat":
        user["ocl"]["phase"] = "full_lending"
        user["ocl"]["partnerCapitalEnabled"] = True
        unlocked.append("ocl_full_lending")
        print(f"🎉 {user.get('username')} unlocked OCL Phase 3 (Full Lending): Partner capital access")
    
    # Send notifications if features were unlocked
    if unlocked:
        # Get username for logging
        username = user.get("username") or (user.get("consent", {}) or {}).get("username", "unknown")
        
        # Post unlock event
        try:
            from log_to_jsonbin_aam_patched import log_event
            log_event({
                "kind": "outcome_unlocks",
                "username": username,
                "unlocked": unlocked,
                "paid_count": paid,
                "delivered_count": delivered,
                "ts": _now()
            })
        except Exception as e:
            print(f"Failed to log unlock event: {e}")
        
        # Send notifications
        for feature in unlocked:
            _send_unlock_notification(username, feature, user)
        
        print(f"🎉 {username} unlocked: {', '.join(unlocked)}")
    
    # Return list of newly unlocked features
    return unlocked

# ---------- NEW: TASK 7 - On-Time Delivery Rate ----------
def _calculate_on_time_rate(user: Dict[str, Any]) -> float:
    """Calculate percentage of deals delivered on-time"""
    # TODO: Implement based on actual delivery tracking
    # For now, return default high rate
    # This will be implemented when we add delivery deadline tracking
    return 0.95

# ---------- Public API ----------
def on_event(evt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Event schema (flexible):
      kind: str  (ATTRIBUTED | PAID | CLICKED | AUTHORIZED | DELIVERED | 
                  INTENT_* | DEALGRAPH_* | FRANCHISE_* | R3_* | PROPOSAL_* | COOP_*)
      user / username: key for JSONBin record
      value_usd / amount_usd: numeric
      bundle_id / mesh_session_id: optional attribution
      provider/channel: optional
    """
    kind = (evt.get("kind") or "").upper()
    username = evt.get("user") or evt.get("username") or "chatgpt"

    users = _load_users()
    user = _find_user(users, username)
    if not user:
        return {"ok": False, "err": "no_user"}

    # ========== NEW: TASK 7 - Funnel Stage Tracking ==========
    
    # CLICKED: Proposals/pitches sent
    if kind in ("CLICKED", "PROPOSAL_SENT", "AME_PITCH_SENT", "PITCH_SENT"):
        _track_funnel_stage(user, "CLICKED", evt)
    
    # AUTHORIZED: Payment authorized/escrow locked
    if kind in ("AUTHORIZED", "PAYMENT_AUTHORIZED", "ESCROW_LOCKED"):
        _track_funnel_stage(user, "AUTHORIZED", evt)
    
    # DELIVERED: Work completed/proof submitted
    if kind in ("DELIVERED", "POO_SUBMITTED", "WORK_COMPLETE", "DELIVERY_CONFIRMED"):
        _track_funnel_stage(user, "DELIVERED", evt)
    
    # PAID: Payment captured (tracked below with revenue events)
    
    # ========== Revenue-affecting events ==========
    if kind in ("ATTRIBUTED", "PAID"):
        usd = float(evt.get("value_usd") or evt.get("amount_usd") or 0.0)
        credit_aigx(user, usd, f"{kind}:{evt.get('provider') or evt.get('channel') or 'unknown'}")
        
        if kind == "PAID":
            autostake(user, usd)
            
            # NEW: Track PAID stage in funnel
            _track_funnel_stage(user, "PAID", evt)
            
            # NEW: Check for unlocks after PAID events
            unlocked = _check_unlocks(user)
            if unlocked:
                # Emit unlock event for notifications
                _emit("FEATURES_UNLOCKED", {
                    "user": username,
                    "features": unlocked,
                    "paid_count": user.get("outcomeFunnel", {}).get("paid", 0)
                })
            
            # NEW: Track revenue by source and transaction fees (Task 4.1)
            source = evt.get("source", "unknown")
            rt = user.setdefault("revenue_tracking", {
                "total_revenue_usd": 0.0,
                "revenue_by_source": {},
                "total_fees_paid": 0.0,
                "fee_history": [],
                "last_payment_date": None
            })
            
            # Track revenue by source
            rt["total_revenue_usd"] = round(rt["total_revenue_usd"] + usd, 2)
            rt["revenue_by_source"].setdefault(source, 0.0)
            rt["revenue_by_source"][source] = round(rt["revenue_by_source"][source] + usd, 2)
            rt["last_payment_date"] = _now()
            
            # Track transaction fees if provided
            fee_breakdown = evt.get("fee_breakdown")
            if fee_breakdown:
                total_fee = float(fee_breakdown.get("total_fee", 0))
                rt["total_fees_paid"] = round(rt["total_fees_paid"] + total_fee, 2)
                
                # Store detailed fee history
                fee_record = {
                    "timestamp": _now(),
                    "deal_id": evt.get("deal_id"),
                    "intent_id": evt.get("intent_id"),
                    "amount_usd": usd,
                    "fee_breakdown": {
                        "base_fee": fee_breakdown.get("base_fee"),
                        "premium_fees": fee_breakdown.get("premium_fees", {}),
                        "premium_total": fee_breakdown.get("premium_total", 0),
                        "total_fee": total_fee,
                        "effective_rate": fee_breakdown.get("effective_rate", 0)
                    },
                    "source": source
                }
                
                rt["fee_history"].append(fee_record)
                
                # Keep only last 100 fee records to avoid bloat
                if len(rt["fee_history"]) > 100:
                    rt["fee_history"] = rt["fee_history"][-100:]
                
                print(f"💰 Fee tracked: ${total_fee:.2f} for {username} ({source})")
        
        if evt.get("bundle_id"):
            _record_bundle(user, evt["bundle_id"], usd)
        if evt.get("mesh_session_id"):
            _record_mesh(user, evt["mesh_session_id"], kind, usd)

    # ========== Domain event families ==========
    if kind.startswith("INTENT_"):
        _record_intent(user, evt)

    if kind.startswith("DEALGRAPH_"):
        _record_dealgraph(user, evt)

    if kind.startswith("FRANCHISE_"):
        _record_franchise(user, evt)

    if kind.startswith("R3_"):
        _record_r3(user, evt)

    if kind.startswith("PROPOSAL_"):
        _record_proposal(user, evt)

    if kind.startswith("COOP_"):
        _record_coop(user, evt)

    # Persist & broadcast
    ok = _save_users(users)
    _emit(kind, evt)
    return {"ok": ok}

# ---------- NEW: TASK 7 - Helper Functions for External Use ----------

def get_user_funnel_stats(username: str) -> Dict[str, Any]:
    """Get user's outcome funnel stats"""
    users = _load_users()
    user = _find_user(users, username)
    if not user:
        return {"ok": False, "error": "user_not_found"}
    
    funnel = user.get("outcomeFunnel", {
        "clicked": 0,
        "authorized": 0,
        "delivered": 0,
        "paid": 0
    })
    
    # Calculate conversion rates
    clicked = funnel.get("clicked", 0)
    conversion_rates = {}
    if clicked > 0:
        conversion_rates = {
            "clicked_to_authorized": round(funnel.get("authorized", 0) / clicked * 100, 1),
            "clicked_to_delivered": round(funnel.get("delivered", 0) / clicked * 100, 1),
            "clicked_to_paid": round(funnel.get("paid", 0) / clicked * 100, 1)
        }
    
    return {
        "ok": True,
        "username": username,
        "funnel": funnel,
        "conversion_rates": conversion_rates,
        "unlocks": {
            "ocl": user.get("ocl", {}),
            "factoring": user.get("factoring", {}),
            "ipVault": user.get("ipVault", {}),
            "certification": user.get("certification", {})
        }
    }

def manually_trigger_unlock_check(username: str) -> Dict[str, Any]:
    """Manually trigger unlock check for a user (admin/debug)"""
    users = _load_users()
    user = _find_user(users, username)
    if not user:
        return {"ok": False, "error": "user_not_found"}
    
    unlocked = _check_unlocks(user)
    ok = _save_users(users)
    
    return {
        "ok": ok,
        "username": username,
        "unlocked": unlocked,
        "funnel": user.get("outcomeFunnel", {})
    }

# ---------- NEW: TASK 8 - Unlock Notifications ----------
def _send_unlock_notification(username: str, feature: str, user: Dict[str, Any]) -> None:
    """Send notification to user about unlocked feature"""
    try:
        # Build notification message
        notifications = {
            "ocl_aigx_credit": {
                "title": "🎉 OCL Unlocked!",
                "message": "You've unlocked a 2,000 AIGx credit line! Borrow AIGx to scale your business.",
                "action": "View Credit Line"
            },
            "ocl_fiat_upgrade": {
                "title": "🚀 OCL Phase 2 Unlocked!",
                "message": "Fiat advances now enabled! Lock AIGx to get real cash.",
                "action": "View Fiat Options"
            },
            "factoring_aigx_advance": {
                "title": "💰 Factoring Unlocked!",
                "message": "Get 80% of your invoice immediately in AIGx!",
                "action": "View Factoring"
            },
            "factoring_fiat_upgrade": {
                "title": "💰 Factoring Phase 2!",
                "message": "Fiat factoring now enabled!",
                "action": "View Factoring"
            },
            "ip_vault": {
                "title": "📚 IPVault Unlocked!",
                "message": "Start earning 70% passive royalties on your IP!",
                "action": "Publish Assets"
            },
            "certification": {
                "title": "⭐ Certified Specialist!",
                "message": "You're now an AiGentsy Specialist with premium matching priority.",
                "action": "View Badge"
            },
            "ocl_full_lending": {
                "title": "🏦 OCL Phase 3 Unlocked!",
                "message": "Partner capital access enabled!",
                "action": "View Options"
            }
        }
        
        notif = notifications.get(feature, {
            "title": f"🎉 {feature} Unlocked!",
            "message": "You've unlocked a new feature!",
            "action": "View Features"
        })
        
        # Store notification in user record
        user.setdefault("notifications", []).append({
            "id": _uid(),
            "type": "feature_unlock",
            "feature": feature,
            "title": notif["title"],
            "message": notif["message"],
            "action": notif["action"],
            "read": False,
            "ts": _now()
        })
        
        # Also emit event for real-time notification system
        _emit("FEATURE_UNLOCKED_NOTIFICATION", {
            "user": username,
            "feature": feature,
            "notification": notif
        })
        
        print(f"📬 Notification sent to {username}: {notif['title']}")
        
    except Exception as e:
        print(f"❌ Notification send failed: {e}")
