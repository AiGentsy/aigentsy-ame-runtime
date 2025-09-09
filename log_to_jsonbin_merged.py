
import os, json, requests
from datetime import datetime, timezone

# External growth agent hooks (if present in runtime)
try:
    from aigent_growth_agent import (
        metabridge_dual_match_realworld_fulfillment,
        proposal_generator,
        proposal_dispatch,
        deliver_proposal
    )
    GROWTH_OK = True
except Exception:
    GROWTH_OK = False

JSONBIN_URL    = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")
VERBOSE        = os.getenv("VERBOSE_LOGGING","true").lower()=="true"

def _now(): 
    return datetime.now(timezone.utc).isoformat()

def _get():
    r = requests.get(JSONBIN_URL, headers={"X-Master-Key": JSONBIN_SECRET}, timeout=15)
    r.raise_for_status()
    return r.json()

def _put(users):
    r = requests.put(JSONBIN_URL,
                     headers={"X-Master-Key": JSONBIN_SECRET, "Content-Type":"application/json"},
                     data=json.dumps({"record": users}), timeout=20)
    r.raise_for_status()
    return True

def _upsert(users, rec):
    uname = rec.get("username") or rec.get("consent",{}).get("username")
    rid = rec.get("id")
    replaced = False
    for i,u in enumerate(users):
        if u.get("id")==rid or (uname and (u.get("username")==uname or u.get("consent",{}).get("username")==uname)):
            users[i]=rec; replaced=True; break
    if not replaced: users.append(rec)
    return users

# ---------- Normalizer (v1.1 shape) ----------
def normalize_user_data(raw: dict) -> dict:
    raw = dict(raw or {})
    runtime = raw.get("runtimeFlags", {}) or {}
    kits    = raw.get("kits", {}) or {}
    licenses= raw.get("licenses", {}) or {}
    raw.setdefault("ownership", {}).setdefault("ledger", [])
    raw.setdefault("transactions", {}).setdefault("outreachEvents", [])
    raw.setdefault("amg", {"apps": [], "capabilities": [], "lastSync": None})
    raw.setdefault("contacts", {"sources": [], "counts": {}, "lastSync": None})
    normalized = {
        "username": raw.get("username") or raw.get("consent",{}).get("username") or "",
        "traits": raw.get("traits", []),
        "walletStats": raw.get("walletStats", {"aigxEarned": 0, "staked": 0}),
        "referralCount": raw.get("referralCount", 0),
        "proposals": raw.get("proposals", []),
        "runtimeFlags": {
            "sdkAccess_eligible": runtime.get("sdkAccess_eligible", False) or licenses.get("sdk", False),
            "vaultAccess": runtime.get("vaultAccess", False) or licenses.get("vault", False) or kits.get("universal", {}).get("unlocked", False),
            "remixUnlocked": runtime.get("remixUnlocked", False) or licenses.get("remix", False),
            "brandingKitUnlocked": runtime.get("brandingKitUnlocked", False) or kits.get("branding", {}).get("unlocked", False),
            "cloneLicenseUnlocked": runtime.get("cloneLicenseUnlocked", False) or licenses.get("clone", False),
            "autonomyLevel": runtime.get("autonomyLevel", "AL1")
        },
        **raw
    }
    return normalized

# ---------- Collectibles ----------
def generate_collectible(username: str, reason: str, metadata: dict = None):
    collectible = {"username": username, "reason": reason, "metadata": metadata or {}, "ts": _now()}
    if VERBOSE: print(f"🏅 Collectible generated:", collectible)
    # Future: persist collectibles under ownership.playbooks or a collectibles array

def _collectible_milestones(data: dict):
    y = (data.get("yield") or {})
    if y.get("aigxEarned", 0) > 0:
        generate_collectible(data["username"], reason="First AIGx Earned")
    if (data.get("cloneLineageSpread") or 0) >= 5:
        generate_collectible(data["username"], reason="Lineage Milestone", metadata={"spread": data["cloneLineageSpread"]})
    if (data.get("remixUnlockedForks") or 0) >= 3:
        generate_collectible(data["username"], reason="Remix Milestone", metadata={"forks": data["remixUnlockedForks"]})
    if (data.get("servicesRendered") or 0) >= 1:
        generate_collectible(data["username"], reason="First Service Delivered")

# ---------- Intent Ledger ----------
def append_intent_ledger(username: str, entry: dict) -> bool:
    if not (JSONBIN_URL and JSONBIN_SECRET): return False
    try:
        data = _get()
        users = data.get("record", [])
        for i,u in enumerate(users):
            uname = u.get("username") or u.get("consent",{}).get("username")
            if uname == username:
                u.setdefault("ownership", {}).setdefault("ledger", [])
                entry = {"ts": _now(), "type":"intent", **(entry or {})}
                u["ownership"]["ledger"].append(entry)
                users[i]=u
                _put(users)
                return True
        return False
    except Exception:
        return False

# ---------- Event hooks (MetaLoop, AutoConnect, MetaBridge/Hive) ----------
def log_metaloop(username: str, kind: str, meta: dict=None):
    return append_intent_ledger(username, {"event":"metaloop", "kind":kind, "meta": meta or {}})

def log_autoconnect(username: str, connector: str, scopes: list=None):
    return append_intent_ledger(username, {"event":"autoconnect", "connector":connector, "scopes": scopes or []})

def log_metabridge(username: str, action: str, payload: dict=None):
    return append_intent_ledger(username, {"event":"metabridge", "action":action, "payload": payload or {}})

def log_metahive(username: str, action: str, payload: dict=None):
    return append_intent_ledger(username, {"event":"metahive", "action":action, "payload": payload or {}})

# ---------- Canonical update (upsert) ----------
def log_agent_update(record: dict):
    """Merge a normalized record into JSONBin. Keeps vaultAccess true; triggers milestones and optional auto-proposal."""
    if not (JSONBIN_URL and JSONBIN_SECRET):
        if VERBOSE: print("❌ JSONBin creds missing"); 
        return
    data = normalize_user_data(record)

    # Force vault access true by default
    data.setdefault("runtimeFlags", {})
    if not data["runtimeFlags"].get("vaultAccess"):
        data["runtimeFlags"]["vaultAccess"] = True
    # Ensure trait is injected
    data["traits"] = list(set(data.get("traits", []) + ["vault"]))

    bin_data = _get()
    users = bin_data.get("record", [])
    users = _upsert(users, data)
    _put(users)
    if VERBOSE: print("✅ JSONBin upsert complete")

    # Milestone collectibles
    try:
        _collectible_milestones(data)
    except Exception as e:
        if VERBOSE: print("Collectible check error:", e)

    # Optional: auto-proposal on mint (requires growth agent functions)
    if GROWTH_OK and data.get("username") and data.get("created"):
        try:
            query = f"auto-proposal for {data['username']}"
            matches  = metabridge_dual_match_realworld_fulfillment(query)
            proposal = proposal_generator(data["username"], query, matches)
            proposal_dispatch(data["username"], proposal, match_target=matches[0].get("username") if matches else None)
            deliver_proposal(query=query, matches=matches, originator=data["username"])
            append_intent_ledger(data["username"], {"event":"auto_proposal_on_mint","matches":len(matches)})
        except Exception as e:
            if VERBOSE: print("Auto-proposal error:", e)

# ---------- Server-side AIGx credit ----------
def credit_aigx(username: str, amount: float, basis="uplift", ref=None):
    if not (JSONBIN_URL and JSONBIN_SECRET): return False
    data = _get()
    users = data.get("record", [])
    for i,u in enumerate(users):
        uname = u.get("username") or u.get("consent",{}).get("username")
        if uname == username:
            u.setdefault("ownership", {"aigx":0,"royalties":0,"ledger":[]})
            u.setdefault("yield", {"aigxEarned":0})
            entry = {"ts": _now(), "amount": float(amount), "currency":"AIGx", "basis": basis, "ref": ref}
            u["ownership"]["ledger"].append(entry)
            u["ownership"]["aigx"] = float(u["ownership"].get("aigx",0)) + float(amount)
            u["yield"]["aigxEarned"] = float(u["yield"].get("aigxEarned",0)) + float(amount)
            users[i]=u
            _put(users)
            return True
    return False
