"""
Outcome Oracle (MAX) — unified & hardened
-----------------------------------------
- Backward compatible `on_event(evt: dict)` entrypoint
- Credits AIGx from USD with env-configurable multiplier
- Autostake v2 with weekly cap
- Records bundle outcomes (A/B tuner), mesh sessions, R3 allocation
- Handles INTENT_*, DEALGRAPH_*, FRANCHISE_*, PROPOSAL_*, COOP_* events
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

# ---------- Public API ----------
def on_event(evt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Event schema (flexible):
      kind: str  (ATTRIBUTED | PAID | INTENT_* | DEALGRAPH_* | FRANCHISE_* | R3_* | PROPOSAL_* | COOP_*)
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

    # Revenue-affecting events
    if kind in ("ATTRIBUTED", "PAID"):
        usd = float(evt.get("value_usd") or evt.get("amount_usd") or 0.0)
        credit_aigx(user, usd, f"{kind}:{evt.get('provider') or evt.get('channel') or 'unknown'}")
        if kind == "PAID":
            autostake(user, usd)
        if evt.get("bundle_id"):
            _record_bundle(user, evt["bundle_id"], usd)
        if evt.get("mesh_session_id"):
            _record_mesh(user, evt["mesh_session_id"], kind, usd)

    # Domain event families
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
