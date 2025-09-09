import os, json, requests
from datetime import datetime, timezone

JSONBIN_URL    = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")
VERBOSE        = os.getenv("VERBOSE_LOGGING","true").lower()=="true"

def _now(): return datetime.now(timezone.utc).isoformat()

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
    for i,u in enumerate(users):
        if u.get("id")==rid or (uname and (u.get("username")==uname or u.get("consent",{}).get("username")==uname)):
            users[i]=rec; return users
    users.append(rec); return users

def log_agent_update(record: dict):
    """Merge a record back into JSONBin (no clobber), keep vaultAccess true by default."""
    if not (JSONBIN_URL and JSONBIN_SECRET): 
        if VERBOSE: print("❌ JSONBin creds missing"); 
        return

    # minimal normalization
    record.setdefault("runtimeFlags", {})
    if not record["runtimeFlags"].get("vaultAccess"):
        record["runtimeFlags"]["vaultAccess"] = True

    data = _get()
    users = data.get("record", [])
    users = _upsert(users, record)
    _put(users)
    if VERBOSE: print("✅ JSONBin upsert complete")

def credit_aigx(username: str, amount: float, basis="uplift", ref=None):
    """Server-side helper to award AIGx & append ledger entry."""
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


def append_intent_ledger(username: str, entry: dict) -> bool:
    """Append an intent ledger entry under ownership.ledger with type='intent' (lightweight)."""
    if not (JSONBIN_URL and JSONBIN_SECRET): return False
    try:
        data = _get()
        users = data.get("record", [])
        for i,u in enumerate(users):
            uname = u.get("username") or u.get("consent",{}).get("username")
            if uname == username:
                u.setdefault("ownership", {}).setdefault("ledger", [])
                entry = {"ts": _now(), "type":"intent", **entry}
                u["ownership"]["ledger"].append(entry)
                users[i]=u
                _put(users)
                return True
        return False
    except Exception:
        return False
