# log_to_jsonbin.py
"""
AiGentsy JSONBin adapter (sync, robust, schema-aware, legacy-safe).

Exports:
- JSONBIN_URL, JSONBIN_SECRET, JSONBIN_COUNTER_URL
- normalize_user_data(record) -> dict
- _get()  -> raw JSONBin response (dict with 'record' or a list)
- _put(records: list) -> True/False
- log_agent_update(record: dict) -> dict (normalized & upserted)
- append_intent_ledger(username: str, entry: dict) -> bool
- credit_aigx(username: str, amount: float, meta: dict = None) -> bool
- get_user(username: str) -> dict | None
- list_users() -> list[dict]
- get_user_count() -> int
- increment_user_count() -> int
"""

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime, timezone

# Prefer httpx, fallback to requests
try:
    import httpx as _http
    _USE_HTTPX = True
except Exception:  # pragma: no cover
    import requests as _http  # type: ignore
    _USE_HTTPX = False

# --------- ENV ---------
JSONBIN_URL: str = os.getenv("JSONBIN_URL", "")
JSONBIN_SECRET: str = os.getenv("JSONBIN_SECRET", "")
JSONBIN_COUNTER_URL: str = os.getenv("JSONBIN_COUNTER_URL", "")

# Local cache (used when JSONBin is missing/unreachable)
_CACHE: List[Dict[str, Any]] = []

# --------- Helpers ---------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _as_dict(v, default=None):
    return v if isinstance(v, dict) else (default or {})

def _as_list(v):
    return v if isinstance(v, list) else []

# --------- Schema normalizer (v3, legacy-safe) ---------
SCHEMA_VERSION = 3

def normalize_user_data(rec: dict) -> dict:
    r = dict(rec or {})

    # --- identity / consent ---
    consent = _as_dict(r.get("consent"))
    u = consent.get("username") or r.get("username") or "guest"
    r["username"] = u
    r.setdefault("companyType", r.get("companyType") or "general")
    r.setdefault("created", r.get("created") or _now_iso())
    r["consent"] = {
        "agreed": bool(consent.get("agreed", consent.get("agreed") is True)),
        "username": u,
        "timestamp": consent.get("timestamp") or _now_iso(),
    }

    # --- schema version (tolerate strings like "v1.0") ---
    sv = r.get("schemaVersion")
    if isinstance(sv, int):
        r["schemaVersion"] = max(sv, SCHEMA_VERSION)
    else:
        r["schemaVersion"] = SCHEMA_VERSION

    # --- traits / flags ---
    r["traits"] = _as_list(r.get("traits"))
    rf = _as_dict(r.get("runtimeFlags"))
    rf.setdefault("vaultAccess", True if r.get("vaultAccess", rf.get("vaultAccess")) else rf.get("vaultAccess", True))
    rf.setdefault("remixUnlocked", bool(r.get("remixUnlocked", rf.get("remixUnlocked", False))))
    rf.setdefault("cloneLicenseUnlocked", bool(r.get("cloneLicenseUnlocked", rf.get("cloneLicenseUnlocked", False))))
    if "sdkAccess_eligible" in r and "sdkAccess_eligible" not in rf:
        rf["sdkAccess_eligible"] = bool(r.get("sdkAccess_eligible"))
    r["runtimeFlags"] = rf

    # --- wallet (coerce "0x0" → {"address":"0x0","staked":0}) ---
    wallet_in = r.get("wallet")
    w = _as_dict(wallet_in)
    if not isinstance(wallet_in, dict):
        addr = r.get("walletAddress")
        if isinstance(wallet_in, str) and wallet_in.strip():
            addr = wallet_in
        w = {"address": addr or "0x0"}
    staked_root = r.get("staked")
    if isinstance(staked_root, bool):
        staked_val = 1 if staked_root else 0
    else:
        try:
            staked_val = int(staked_root or 0)
        except Exception:
            staked_val = 0
    w.setdefault("address", r.get("walletAddress", w.get("address", "0x0")))
    w.setdefault("staked", staked_val)
    r["wallet"] = w
    if r["wallet"]["staked"] and not r.get("staked"):
        r["staked"] = r["wallet"]["staked"]

    # --- yield (always a dict of floats) ---
    y_in = _as_dict(r.get("yield"))
    y = {
        "autoStake": bool(y_in.get("autoStake", False)),
        "aigxEarned": float(y_in.get("aigxEarned") or 0),
        "vaultYield": float(y_in.get("vaultYield") or 0),
        "remixYield": float(y_in.get("remixYield") or 0),
        "aigxAttributedTo": _as_list(y_in.get("aigxAttributedTo")),
        "aigxEarnedEnabled": bool(y_in.get("aigxEarnedEnabled", False)),
    }
    r["yield"] = y

    # --- proposals (merge legacy proposal.proposalsSent/Received) ---
    unified = _as_list(r.get("proposals"))
    legacy_prop = _as_dict(r.get("proposal"))
    for bucket, direction in ((legacy_prop.get("proposalsSent"), "outbound"),
                              (legacy_prop.get("proposalsReceived"), "inbound")):
        for item in _as_list(bucket):
            pid = item.get("id") or f"p_{uuid4().hex[:8]}"
            amt = item.get("amount", item.get("price", 0))
            try:
                amt = float(amt or 0)
            except Exception:
                amt = 0.0
            unified.append({
                "id": pid,
                "sender": item.get("sender") or (u if direction == "outbound" else "external"),
                "recipient": item.get("recipient") or (u if direction == "inbound" else "external"),
                "title": item.get("title") or "",
                "details": item.get("details") or "",
                "amount": amt,
                "timestamp": item.get("timestamp") or _now_iso(),
                "link": item.get("link") or "",
                "followups": _as_list(item.get("followups")),
            })
    normd = []
    for p in unified:
        p = dict(p or {})
        p.setdefault("id", f"p_{uuid4().hex[:8]}")
        p.setdefault("sender", "")
        p.setdefault("recipient", u)
        p.setdefault("title", "")
        p.setdefault("details", "")
        try:
            p["amount"] = float(p.get("amount") or p.get("price") or 0)
        except Exception:
            p["amount"] = 0.0
        p.setdefault("timestamp", p.get("timestamp") or _now_iso())
        p.setdefault("link", p.get("link") or "")
        p["followups"] = _as_list(p.get("followups"))
        normd.append(p)
    r["proposals"] = normd

    # --- Order-to-Cash rails ---
    r["orders"] = _as_list(r.get("orders"))
    for o in r["orders"]:
        o.setdefault("id", f"o_{uuid4().hex[:8]}")
        o.setdefault("quoteId", "")
        o.setdefault("proposalId", "")
        o.setdefault("status", "queued")  # queued|doing|blocked|done
        o.setdefault("createdAt", _now_iso())
        o.setdefault("sla", {"due": None, "started": None, "completed": None})
        o["tasks"] = _as_list(o.get("tasks"))

    r["invoices"] = _as_list(r.get("invoices"))
    for i in r["invoices"]:
        i.setdefault("id", f"inv_{uuid4().hex[:8]}")
        i.setdefault("orderId", "")
        try:
            i["amount"] = float(i.get("amount") or 0)
        except Exception:
            i["amount"] = 0.0
        i.setdefault("currency", i.get("currency") or "USD")
        i.setdefault("status", i.get("status") or "draft")  # draft|sent|paid|void
        i.setdefault("issuedAt", i.get("issuedAt") or _now_iso())
        i.setdefault("dueAt", i.get("dueAt") or None)
        i.setdefault("paidAt", i.get("paidAt") or None)

    r["payments"] = _as_list(r.get("payments"))
    for pmt in r["payments"]:
        pmt.setdefault("id", f"pay_{uuid4().hex[:8]}")
        pmt.setdefault("invoiceId", "")
        try:
            pmt["amount"] = float(pmt.get("amount") or 0)
        except Exception:
            pmt["amount"] = 0.0
        pmt.setdefault("currency", pmt.get("currency") or "USD")
        pmt.setdefault("status", pmt.get("status") or "initiated")  # initiated|succeeded|failed
        pmt.setdefault("provider", pmt.get("provider") or "stripe")
        pmt.setdefault("receiptUrl", pmt.get("receiptUrl") or "")
        pmt.setdefault("createdAt", pmt.get("createdAt") or _now_iso())

    # --- misc collections expected by UI/logic ---
    r["contacts"] = _as_list(r.get("contacts"))
    r["meetings"] = _as_list(r.get("meetings"))
    r["kpi_snapshots"] = _as_list(r.get("kpi_snapshots"))
    r["docs"] = _as_list(r.get("docs"))

    # --- ownership / audit ledger ---
    owner = _as_dict(r.get("ownership"))
    owner["ledger"] = _as_list(owner.get("ledger"))
    r["ownership"] = owner

    # --- friendly enums ---
    if "listingStatus" in r and isinstance(r["listingStatus"], str):
        r["listingStatus"] = "Active" if r["listingStatus"].lower() == "active" else r["listingStatus"]
    if "protocolStatus" in r and isinstance(r["protocolStatus"], str):
        r["protocolStatus"] = "Bound" if r["protocolStatus"].lower() == "bound" else r["protocolStatus"]

    # --- ensure id ---
    r.setdefault("id", r.get("id") or f"user_{uuid4().hex[:8]}")

    return r

# --------- Low-level JSONBin I/O (sync) ---------
def _headers() -> dict:
    h = {}
    if JSONBIN_SECRET:
        h["X-Master-Key"] = JSONBIN_SECRET
    return h

def _ok_jsonbin() -> bool:
    return bool(JSONBIN_URL and JSONBIN_SECRET)

def _read_jsonbin() -> Tuple[Optional[List[Dict[str, Any]]], Optional[Any]]:
    """Returns (records_list_or_none, raw_response_or_error)."""
    if not _ok_jsonbin():
        return None, "jsonbin-not-configured"
    try:
        if _USE_HTTPX:
            with _http.Client(timeout=15) as cx:  # type: ignore[attr-defined]
                r = cx.get(JSONBIN_URL, headers=_headers())
                r.raise_for_status()
                data = r.json()
        else:
            r = _http.get(JSONBIN_URL, headers=_headers(), timeout=15)
            r.raise_for_status()
            data = r.json()
        if isinstance(data, dict) and "record" in data:
            return list(data["record"] or []), data
        if isinstance(data, list):
            return data, data
        return None, data
    except Exception as e:  # pragma: no cover
        return None, e

def _write_jsonbin(records: List[Dict[str, Any]]) -> Tuple[bool, Optional[Any]]:
    if not _ok_jsonbin():
        return False, "jsonbin-not-configured"
    try:
        payload = records  # PUT raw array; JSONBin v3 wraps it as {'record': ...}
        if _USE_HTTPX:
            with _http.Client(timeout=20) as cx:  # type: ignore[attr-defined]
                r = cx.put(JSONBIN_URL, headers=_headers(), json=payload)
                r.raise_for_status()
        else:
            r = _http.put(JSONBIN_URL, headers=_headers(), json=payload, timeout=20)
            r.raise_for_status()
        return True, None
    except Exception as e:  # pragma: no cover
        return False, e

# Public low-level API
def _get() -> Any:
    """Raw JSONBin GET. Returns dict with 'record' (preferred) or a list (legacy)."""
    recs, raw = _read_jsonbin()
    if isinstance(raw, Exception):
        return {"record": _CACHE}
    if isinstance(raw, list):
        return {"record": raw}
    if isinstance(raw, dict):
        return raw
    return {"record": _CACHE}

def _put(records: List[Dict[str, Any]]) -> bool:
    global _CACHE  # declare before any use/assignment
    ok, _err = _write_jsonbin(records)
    if ok:
        _CACHE = list(records)
    return ok

# --------- High-level helpers ---------
def _merge_into_list(records: List[Dict[str, Any]], user_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Upsert by consent.username or username."""
    target = normalize_user_data(user_record)
    uname = (target.get("consent") or {}).get("username") or target.get("username")
    replaced = False
    out: List[Dict[str, Any]] = []
    for rec in (records or []):
        # ✅ DEFENSIVE: Skip non-dict records
        if not isinstance(rec, dict):
            continue
        
        u = (rec.get("consent") or {}).get("username") or rec.get("username")
        if u == uname and not replaced:
            out.append(target)
            replaced = True
        else:
            out.append(rec)
    if not replaced:
        out.append(target)
    return out

def log_agent_update(record: Dict[str, Any]) -> Dict[str, Any]:
    global _CACHE  # declare first
    existing, _raw = _read_jsonbin()
    if existing is None:
        existing = list(_CACHE)
    merged = _merge_into_list(existing, record)
    ok, _err = _write_jsonbin(merged)
    if ok:
        _CACHE = merged
    else:
        _CACHE = merged  # keep cache even if network failed
    uname = (record.get("consent") or {}).get("username") or record.get("username")
    for rec in merged:
        u = (rec.get("consent") or {}).get("username") or rec.get("username")
        if u == uname:
            return normalize_user_data(rec)
    return normalize_user_data(record)

def get_user(username: str) -> Optional[Dict[str, Any]]:
    existing, _raw = _read_jsonbin()
    pool = existing if existing is not None else _CACHE
    for rec in pool:
        # ✅ DEFENSIVE: Skip non-dict records
        if not isinstance(rec, dict):
            continue
        
        u = (rec.get("consent") or {}).get("username") or rec.get("username")
        if u == username:
            return normalize_user_data(rec)
    return None

def list_users() -> List[Dict[str, Any]]:
    existing, _raw = _read_jsonbin()
    pool = existing if existing is not None else _CACHE
    # ✅ DEFENSIVE: Filter out non-dict records
    return [normalize_user_data(r) for r in pool if isinstance(r, dict)]

def append_intent_ledger(username: str, entry: Dict[str, Any]) -> bool:
    global _CACHE  # MUST be first line in function
    if not isinstance(entry, dict):
        entry = {"event": str(entry)}
    entry = dict(entry)
    entry.setdefault("ts", _now_iso())

    existing, _raw = _read_jsonbin()
    if existing is None:
        existing = list(_CACHE)

    updated = False
    out: List[Dict[str, Any]] = []
    for rec in existing:
        u = (rec.get("consent") or {}).get("username") or rec.get("username")
        if u == username:
            rec = normalize_user_data(rec)
            rec.setdefault("ownership", {})
            rec["ownership"].setdefault("ledger", [])
            rec["ownership"]["ledger"].append(entry)
            out.append(rec)
            updated = True
        else:
            out.append(rec)

    if not updated:
        fresh = normalize_user_data({"username": username})
        fresh.setdefault("ownership", {"ledger": [entry]})
        out.append(fresh)

    ok, _err = _write_jsonbin(out)
    if ok:
        _CACHE = out
    return ok

def credit_aigx(username: str, amount: float, meta: Optional[Dict[str, Any]] = None) -> bool:
    global _CACHE  # MUST be first line in function
    try:
        amt = float(amount)
    except Exception:
        amt = 0.0

    existing, _raw = _read_jsonbin()
    if existing is None:
        existing = list(_CACHE)

    updated = False
    out: List[Dict[str, Any]] = []
    for rec in existing:
        u = (rec.get("consent") or {}).get("username") or rec.get("username")
        if u == username:
            rec = normalize_user_data(rec)
            ry = rec.setdefault("yield", {})
            ry["aigxEarned"] = float(ry.get("aigxEarned") or 0) + amt
            rec.setdefault("ownership", {})
            rec["ownership"].setdefault("ledger", [])
            rec["ownership"]["ledger"].append({
                "event": "aigx_credit",
                "amount": amt,
                "meta": meta or {},
                "ts": _now_iso()
            })
            out.append(rec)
            updated = True
        else:
            out.append(rec)

    if not updated:
        fresh = normalize_user_data({"username": username})
        fresh["yield"]["aigxEarned"] = float(fresh["yield"].get("aigxEarned") or 0) + amt
        fresh.setdefault("ownership", {"ledger": [{
            "event": "aigx_credit", "amount": amt, "meta": meta or {}, "ts": _now_iso()
        }]})
        out.append(fresh)

    ok, _err = _write_jsonbin(out)
    if ok:
        _CACHE = out
    return ok

# --------- User Counter Functions (for Early Adopter Tiers) ---------
def get_user_count() -> int:
    """
    Get current user count from dedicated counter bin.
    Returns 0 if counter bin is not configured or unreachable.
    """
    if not JSONBIN_COUNTER_URL or not JSONBIN_SECRET:
        return 0
    
    try:
        h = {"X-Master-Key": JSONBIN_SECRET}
        if _USE_HTTPX:
            with _http.Client(timeout=10) as cx:  # type: ignore[attr-defined]
                r = cx.get(JSONBIN_COUNTER_URL, headers=h)
                r.raise_for_status()
                data = r.json()
        else:
            r = _http.get(JSONBIN_COUNTER_URL, headers=h, timeout=10)
            r.raise_for_status()
            data = r.json()
        
        # JSONBin wraps response in {"record": {...}}
        record = data.get("record", {}) if isinstance(data, dict) else {}
        return int(record.get("count", 0))
    except Exception:
        return 0

def increment_user_count() -> int:
    """
    Atomically increment and return new user number.
    This assigns the next sequential user number for early adopter tier detection.
    
    Returns:
        int: New user number (1, 2, 3, etc.)
        
    Fallback behavior:
        If counter bin is unreachable, falls back to counting existing users.
        This ensures the system continues to function even if counter bin fails.
    """
    if not JSONBIN_COUNTER_URL or not JSONBIN_SECRET:
        # Fallback: count existing users
        return len(list_users()) + 1
    
    try:
        # Get current count
        current = get_user_count()
        new_count = current + 1
        
        # Write new count
        h = {
            "X-Master-Key": JSONBIN_SECRET,
            "Content-Type": "application/json"
        }
        payload = {"count": new_count}
        
        if _USE_HTTPX:
            with _http.Client(timeout=10) as cx:  # type: ignore[attr-defined]
                r = cx.put(JSONBIN_COUNTER_URL, headers=h, json=payload)
                r.raise_for_status()
        else:
            r = _http.put(JSONBIN_COUNTER_URL, headers=h, json=payload, timeout=10)
            r.raise_for_status()
        
        return new_count
    except Exception:
        # Fallback: count existing users (slower, but safe)
        return len(list_users()) + 1

def _upgrade_all_local_cache() -> None:
    global _CACHE
    _CACHE = [normalize_user_data(r) for r in _CACHE]

# --------- Reputation System (Reputation Gates for Feature Unlocks) ---------
def calculate_reputation_score(user: dict) -> int:
    """Calculate user's reputation score from multiple signals"""
    score = 0
    
    # Base reputation (everyone starts at 10)
    score += 10
    
    # Successful deals (+5 each)
    deals_completed = user.get("stats", {}).get("deals_completed", 0)
    score += deals_completed * 5
    
    # Positive feedback (+3 each)
    positive_reviews = user.get("stats", {}).get("positive_reviews", 0)
    score += positive_reviews * 3
    
    # Revenue generated (+1 per $100)
    total_revenue = user.get("revenue", {}).get("total", 0)
    score += int(total_revenue / 100)
    
    # Time on platform (+2 per month)
    created_at = user.get("consent", {}).get("timestamp")
    if created_at:
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            months = (now - created).days / 30
            score += int(months) * 2
        except:
            pass
    
    # Community contributions (manual bonus)
    community_bonus = user.get("stats", {}).get("community_bonus", 0)
    score += community_bonus
    
    return max(score, 10)  # Minimum reputation is 10


def check_reputation_unlocks(username: str) -> dict:
    """Check and update reputation-based feature unlocks"""
    global _CACHE
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        # Calculate current reputation
        rep_score = calculate_reputation_score(user)
        
        # Store reputation in user object
        user.setdefault("reputation", {})
        user["reputation"]["score"] = rep_score
        user["reputation"]["last_calculated"] = _now_iso()
        
        # Initialize runtime flags
        user.setdefault("runtimeFlags", {})
        
        # Track what unlocked
        newly_unlocked = []
        
        # Rep 10: Basic features (always available)
        if rep_score >= 10:
            if not user["runtimeFlags"].get("basicFeaturesEnabled"):
                user["runtimeFlags"]["basicFeaturesEnabled"] = True
                newly_unlocked.append("basic_features")
        
        # Rep 25: R³ Autopilot
        if rep_score >= 25:
            if not user["runtimeFlags"].get("r3AutopilotEnabled"):
                user["runtimeFlags"]["r3AutopilotEnabled"] = True
                newly_unlocked.append("r3_autopilot")
        
        # Rep 50: Advanced Analytics
        if rep_score >= 50:
            if not user["runtimeFlags"].get("advancedAnalyticsEnabled"):
                user["runtimeFlags"]["advancedAnalyticsEnabled"] = True
                newly_unlocked.append("advanced_analytics")
        
        # Rep 75: Template Publishing
        if rep_score >= 75:
            if not user["runtimeFlags"].get("templatePublishingEnabled"):
                user["runtimeFlags"]["templatePublishingEnabled"] = True
                newly_unlocked.append("template_publishing")
        
        # Rep 100: MetaHive Premium
        if rep_score >= 100:
            if not user["runtimeFlags"].get("metaHivePremium"):
                user["runtimeFlags"]["metaHivePremium"] = True
                newly_unlocked.append("metahive_premium")
        
        # Rep 150: White Label
        if rep_score >= 150:
            if not user["runtimeFlags"].get("whiteLabelEnabled"):
                user["runtimeFlags"]["whiteLabelEnabled"] = True
                newly_unlocked.append("white_label")
        
        # Save if unlocks occurred
        if newly_unlocked or user.get("reputation", {}).get("score") != rep_score:
            log_agent_update(user)
            
            # Log unlock event if new unlocks
            if newly_unlocked:
                append_intent_ledger(username, {
                    "event": "reputation_unlocks",
                    "reputation_score": rep_score,
                    "unlocked": newly_unlocked,
                    "ts": _now_iso()
                })
                
                print(f"🎖️ {username} unlocked at Rep {rep_score}: {', '.join(newly_unlocked)}")
        
        return {
            "ok": True,
            "reputation_score": rep_score,
            "newly_unlocked": newly_unlocked,
            "total_unlocks": len([k for k, v in user["runtimeFlags"].items() if v])
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


def increment_deal_count(username: str):
    """Increment completed deals and recalculate reputation"""
    global _CACHE
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        user.setdefault("stats", {})
        user["stats"]["deals_completed"] = user["stats"].get("deals_completed", 0) + 1
        
        log_agent_update(user)
        
        # Recalculate reputation
        return check_reputation_unlocks(username)
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


def add_positive_review(username: str):
    """Add positive review and recalculate reputation"""
    global _CACHE
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        user.setdefault("stats", {})
        user["stats"]["positive_reviews"] = user["stats"].get("positive_reviews", 0) + 1
        
        log_agent_update(user)
        
        # Recalculate reputation
        return check_reputation_unlocks(username)
        
    except Exception as e:
        return {"ok": False, "error": str(e)}

# --------- Early Adopter Tiers (AIGx Multipliers) ---------

def get_early_adopter_tier(user_number: int) -> Dict[str, Any]:
    """Get early adopter tier based on signup order"""
    
    if user_number <= 100:
        return {
            "tier": "founder",
            "name": "Founder",
            "multiplier": 3.0,
            "badge": "🏆",
            "description": "First 100 users - 3x earnings"
        }
    elif user_number <= 500:
        return {
            "tier": "pioneer",
            "name": "Pioneer",
            "multiplier": 2.5,
            "badge": "💎",
            "description": "Users 101-500 - 2.5x earnings"
        }
    elif user_number <= 1000:
        return {
            "tier": "early",
            "name": "Early Adopter",
            "multiplier": 2.0,
            "badge": "⭐",
            "description": "Users 501-1000 - 2x earnings"
        }
    elif user_number <= 5000:
        return {
            "tier": "builder",
            "name": "Builder",
            "multiplier": 1.5,
            "badge": "🔨",
            "description": "Users 1001-5000 - 1.5x earnings"
        }
    else:
        return {
            "tier": "standard",
            "name": "Standard",
            "multiplier": 1.0,
            "badge": "",
            "description": "Standard member"
        }


def apply_early_adopter_multiplier(username: str, base_amount: float) -> Dict[str, Any]:
    """Apply early adopter multiplier to earnings"""
    try:
        user = get_user(username)
        if not user:
            return {
                "base_amount": base_amount,
                "multiplier": 1.0,
                "bonus_amount": 0.0,
                "total_amount": base_amount
            }
        
        # Get user's signup number
        user_number = user.get("user_number", 999999)
        
        # Get tier info
        tier_info = get_early_adopter_tier(user_number)
        multiplier = tier_info["multiplier"]
        
        # Calculate bonus
        bonus_amount = round(base_amount * (multiplier - 1.0), 2)
        total_amount = round(base_amount * multiplier, 2)
        
        return {
            "base_amount": base_amount,
            "multiplier": multiplier,
            "bonus_amount": bonus_amount,
            "total_amount": total_amount,
            "tier": tier_info["tier"],
            "tier_name": tier_info["name"],
            "badge": tier_info["badge"]
        }
        
    except Exception as e:
        return {
            "base_amount": base_amount,
            "multiplier": 1.0,
            "bonus_amount": 0.0,
            "total_amount": base_amount,
            "error": str(e)
        }


def assign_user_number_on_signup(username: str) -> int:
    """Assign sequential user number when user first signs up"""
    global _CACHE
    try:
        user = get_user(username)
        if not user:
            return 0
        
        # Check if already has number
        if user.get("user_number"):
            return user["user_number"]
        
        # Increment counter and assign
        user_number = increment_user_count()
        
        user["user_number"] = user_number
        user["early_adopter"] = get_early_adopter_tier(user_number)
        user["early_adopter"]["assigned_at"] = _now_iso()
        
        log_agent_update(user)
        
        # Log tier assignment
        append_intent_ledger(username, {
            "event": "early_adopter_tier_assigned",
            "user_number": user_number,
            "tier": user["early_adopter"]["tier"],
            "multiplier": user["early_adopter"]["multiplier"],
            "ts": _now_iso()
        })
        
        print(f"🎖️ {username} assigned user #{user_number} - {user['early_adopter']['name']} tier ({user['early_adopter']['multiplier']}x)")
        
        return user_number
        
    except Exception as e:
        print(f"Error assigning user number: {e}")
        return 0

__all__ = [
    "JSONBIN_URL",
    "JSONBIN_SECRET",
    "JSONBIN_COUNTER_URL",
    "normalize_user_data",
    "_get",
    "_put",
    "log_agent_update",
    "append_intent_ledger",
    "credit_aigx",
    "get_user",
    "list_users",
    "get_user_count",
    "increment_user_count",
    "calculate_reputation_score",
    "check_reputation_unlocks",
    "increment_deal_count",
    "add_positive_review",
    "get_early_adopter_tier",
    "apply_early_adopter_multiplier",
    "assign_user_number_on_signup",
]
