# === PATCH APPLIED ===
import uuid
from typing import Literal, Optional, List, Dict
from fastapi.responses import StreamingResponse
import asyncio
import hashlib
import hmac
import time as _time
# ============================
# AiGentsy Runtime (main.py)
# Canonical mint + AMG/AL/JV/AIGx/Contacts + Business-in-a-Box rails
# ============================
import os, httpx, uuid, json, hmac, hashlib, csv, io, logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, Body, Path, HTTPException, Header, BackgroundTasks
PLATFORM_FEE = float(os.getenv("PLATFORM_FEE", "0.12"))  # single source of truth
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from venture_builder_agent import get_agent_graph
from log_to_jsonbin_merged import (
    log_agent_update, append_intent_ledger, credit_aigx as credit_aigx_srv,
    log_metaloop, log_autoconnect, log_metabridge, log_metahive
)
# Admin normalize uses the classic module (keep both available)
from log_to_jsonbin import _get as _bin_get, _put as _bin_put, normalize_user_data
# Intent Exchange (upgraded with auction system)
try:
    from intent_exchange_UPGRADED import router as intent_router
except Exception:
    intent_router = None
# ---- App, logging, CORS (single block) ----
import os, logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
# --- internal signing for trusted backend calls ---
def _sign_payload(body_bytes: bytes) -> dict:
    secret = os.getenv("HMAC_SECRET", "")
    if not secret:
        return {}
    ts = str(int(_time.time()))
    sig = hmac.new(secret.encode(), (ts + "." + body_bytes.decode()).encode(), hashlib.sha256).hexdigest()
    return {"X-Ts": ts, "X-Sign": sig}

app = FastAPI()

logger = logging.getLogger("aigentsy")
logging.basicConfig(level=logging.DEBUG if os.getenv("VERBOSE_LOGGING") else logging.INFO)

ALLOW_ORIGINS = [
    os.getenv("FRONTEND_ORIGIN", "https://aigentsy.com"),
    "https://aigentsy.com",
    "https://www.aigentsy.com",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,   # explicit allowed sites
    allow_credentials=False,       # set True only if you use cookies/auth headers
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# ---- Simple health check ----
@app.get("/healthz")
async def healthz():
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}

# ---- Env ----
JSONBIN_URL     = os.getenv("JSONBIN_URL")
JSONBIN_SECRET  = os.getenv("JSONBIN_SECRET")
PROPOSAL_WEBHOOK_URL = os.getenv("PROPOSAL_WEBHOOK_URL")  # used by /contacts/send webhook
POL_SECRET      = os.getenv("POL_SECRET", "dev-secret")   # for signed Offer Links
CANONICAL_SCHEMA_VERSION = "v1.1"  # bumped
SELF_URL        = os.getenv("SELF_URL")  # optional, e.g. https://your-service.onrender.com

# ---- Agent Graph (AiGent Venture; MetaUpgrade25+26) ----
agent_graph = get_agent_graph()

# ============================
# Helpers
# ============================
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _id(pfx: str) -> str:
    return f"{pfx}_{uuid.uuid4().hex[:10]}"

def _hmac(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

def _empty_kits() -> Dict[str, Any]:
    return {
        "universal": {"unlocked": False},
        "growth": {"unlocked": False},
        "legal": {"unlocked": False},
        "sdk": {"unlocked": False},
        "branding": {"unlocked": False},
        "marketing": {"unlocked": False},
        "social": {"unlocked": False},
    }

def _empty_licenses():
    return {"sdk": False, "vault": False, "remix": False, "clone": False, "aigx": False}

# ---- Fees ----

def _platform_fee_rate(u: dict) -> float:
    """Resolve take-rate in order: per-user override -> env PLATFORM_FEE -> 0.05 default."""
    return float((u.get("fees") or {}).get("take_rate") or PLATFORM_FEE or 0.05)


def _ratelimit(u, key: str, per_min: int = 30):
    now = datetime.utcnow()
    window_start = (now - timedelta(minutes=1)).isoformat()
    rl = u.setdefault("rate", {}).setdefault(key, [])
    rl[:] = [t for t in rl if t >= window_start]
    if len(rl) >= per_min:
        return False, len(rl)
    rl.append(_now())
    return True, len(rl)

COMPANY_TYPE_PRESETS = {
    "legal":     {"meta_role": "CLO", "traits_add": ["legal"],     "kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
    "social":    {"meta_role": "CMO", "traits_add": ["marketing"], "kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
    "saas":      {"meta_role": "CTO", "traits_add": [],            "kits_unlock": ["universal","sdk"],        "flags": {"vaultAccess": True, "sdkAccess_eligible": True}},
    "marketing": {"meta_role": "CMO", "traits_add": ["marketing"], "kits_unlock": ["universal","branding"],   "flags": {"vaultAccess": True}},
    "custom":    {"meta_role": "Founder", "traits_add": ["custom"],"kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
    "general":   {"meta_role": "Founder", "traits_add": [],        "kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
}

# ===== Monetization / payouts config =====
PAYOUT_MIN = float(os.getenv("PAYOUT_MIN", "10"))                  # $10 minimum
PAYOUT_HOLDBACK_DAYS = int(os.getenv("PAYOUT_HOLDBACK_DAYS", "7")) # 7-day eligibility window
REFERRAL_BOUNTY = float(os.getenv("REFERRAL_BOUNTY", "1.0"))       # 1 AIGx for a signup referral

# Treat 1 AIGx == 1 USD for accounting display (you can change later).
def _as_usd(entry: Dict[str, Any]) -> float:
    amt = float(entry.get("amount", 0))
    cur = (entry.get("currency") or "USD").upper()
    # If ledger is in AIGx treat 1:1 to USD for money tab. Tune via FX later if needed.
    return amt if cur in ("USD", "AIGX") else amt

def _days_ago(ts_iso: str) -> int:
    try:
        then = datetime.fromisoformat(ts_iso.replace("Z","+00:00"))
        return (datetime.now(timezone.utc) - then.astimezone(timezone.utc)).days
    except Exception:
        return 9999

def _money_summary(u: Dict[str, Any]) -> Dict[str, Any]:
    led = (u.get("ownership") or {}).get("ledger", [])
    # Gross money events that increase balance
    earn_bases = {"revenue","partner","affiliate","bounty","task","uplift","royalty"}
    gross_all = sum(_as_usd(x) for x in led if (x.get("basis") in earn_bases))
    # Eligible (older than holdback)
    eligible_gross = sum(_as_usd(x) for x in led
                         if (x.get("basis") in earn_bases and _days_ago(x.get("ts","")) >= PAYOUT_HOLDBACK_DAYS))
    # Platform fees already posted as negative ledger lines (if you adopt patch below)
    posted_fees = sum(_as_usd(x) for x in led if x.get("basis") == "platform_fee")
    # Final payouts executed (negative)
    paid_out = sum(_as_usd(x) for x in led if x.get("basis") == "payout")
    # Pending payout requests (not yet ledgered)
    pending_req = sum(float(p.get("amount",0)) for p in u.get("payouts", []) if p.get("status") in ("requested","queued"))

    # If you *haven't* posted platform_fee lines yet, uncomment the next line to estimate fees:
    # posted_fees = - eligible_gross * PLATFORM_FEE

    available_gross = eligible_gross + posted_fees + paid_out  # posted_fees is negative, paid_out negative
    available = max(0.0, available_gross - pending_req)

    return {
        "gross_lifetime": round(gross_all, 2),
        "eligible_gross": round(eligible_gross, 2),
        "fees_posted": round(posted_fees, 2),
        "paid_out": round(paid_out, 2),
        "pending_requests": round(pending_req, 2),
        "available": round(available, 2),
        "holdback_days": PAYOUT_HOLDBACK_DAYS,
    }

def make_canonical_record(username: str, company_type: str = "general", referral: str = "origin/hero") -> Dict[str, Any]:
    preset = COMPANY_TYPE_PRESETS.get(company_type, COMPANY_TYPE_PRESETS["general"])
    kits = _empty_kits()
    for k in preset["kits_unlock"]:
        kits[k]["unlocked"] = True

    runtime_flags = {
        "flagged": False,
        "eligibleForAudit": True,
        "needsReview": False,
        "vaultAccess": False,
        "remixUnlocked": False,
        "cloneLicenseUnlocked": False,
        "sdkAccess_eligible": False,
        "autonomyLevel": "AL1",  # default safe mode
    }
    runtime_flags.update(preset["flags"])

    traits = sorted(list({*["founder", "autonomous", "aigentsy"], *preset["traits_add"]}))

    user = {
        "schemaVersion": CANONICAL_SCHEMA_VERSION,
        "id": str(uuid.uuid4()),
        "ventureID": f"aigent0-{username}",
        "consent": {"agreed": True, "username": username, "timestamp": _now()},
        "username": username,
        "companyType": company_type,
        "role": preset["meta_role"],
        "meta_role": preset["meta_role"],
        "traits": traits,
        "kits": kits,
        "licenses": _empty_licenses(),
        "runtimeFlags": runtime_flags,
        "walletAddress": "0x0",
        "wallet": {"aigx": 0, "staked": 0},
        "yield": {
            "autoStake": False, "aigxEarned": 0, "vaultYield": 0, "remixYield": 0,
            "aigxAttributedTo": [], "aigxEarnedEnabled": True
        },
        "remix": {"remixCount": 0, "remixCredits": 1000, "lineageDepth": 0, "royaltyTerms": "Standard 30%"},
        "cloneLineage": [],
        "realm": {"name": "Realm 101 — Strategic Expansion", "joinedAt": _now()},
        "metaVenture": {"ventureHive": "Autonomous Launch", "ventureRole": preset["meta_role"], "ventureStatus": "Pending", "ventureID": f"MV-{int(datetime.now().timestamp())}"},
        "mirror": {"mirroredInRealms": ["Realm 101 — Strategic Expansion"], "mirrorIntegrity": "Verified", "sentinelAlert": False},
        "proposal": {"personaHint": "", "proposalsSent": [], "proposalsReceived": []},
        "proposals": [],
        "transactions": {"unlocks": [], "yieldEvents": [], "referralEvents": [], "outreachEvents": []},
        "offerings": {"products": [], "services": [], "pricing": [], "description": ""},
        "packaging": {"kits_sent": [], "proposals": [], "custom_files": [], "active": False},
        "automatch": {"status": "pending", "lastMatchResult": None, "matchReady": True},
        "metaloop": {"enabled": True, "lastMatchCheck": None, "proposalHistory": []},
        "metabridge": {"active": True, "lastBridge": None, "bridgeCount": 0},
        "earningsEnabled": True,
        "listingStatus": "Active",
        "protocolStatus": "Bound",
        "tethered": True,
        "runtimeURL": "https://aigentsy.com/agents/aigent0.html",
        "referral": referral,
        "mintTime": _now(),
        "created": _now(),
        # NEW: upgradable surfaces
        "amg": {"apps": [], "capabilities": [], "lastSync": None},  # App Monetization Graph
        "ownership": {"aigx": 0, "royalties": 0, "ledger": []},    # AIGx & royalties ledger
        "jvMesh": [],                                               # micro-JVs (cap tables)
        "contacts": {"sources": [], "counts": {}, "lastSync": None} # privacy-first contacts
    }
    # ensure default chart-friendly flags
    user["runtimeFlags"]["vaultAccess"] = user["runtimeFlags"]["vaultAccess"] or user["kits"]["universal"]["unlocked"]
    return user

def _today_key():
    return datetime.utcnow().strftime("%Y-%m-%d")

def _current_spend(u):
    s = u.setdefault("spend", {})
    day = _today_key()
    s.setdefault(day, 0.0)
    return s, day

def _can_spend(u, amt: float) -> bool:
    guard = (u.get("policy", {}) or {}).get("guardrails", {}) or {}
    cap = float(guard.get("dailyBudget", 0))
    s, day = _current_spend(u)
    return (s[day] + amt) <= cap if cap else True

def _spend(u, amt: float, basis="media_spend", ref=None):
    s, day = _current_spend(u)
    s[day] = round(s[day] + amt, 2)
    u.setdefault("ownership", {}).setdefault("ledger", []).append(
        {"ts": _now(), "amount": -float(amt), "currency": "USD", "basis": basis, "ref": ref}
    )

def normalize_user_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not raw: return {}
    username = raw.get("username") or raw.get("consent", {}).get("username") or ""
    kits = raw.get("kits") or _empty_kits()
    licenses = raw.get("licenses") or _empty_licenses()
    rf = raw.get("runtimeFlags", {})
    vault_access = bool(rf.get("vaultAccess") or raw.get("vaultAccess") or licenses.get("vault") or kits.get("universal", {}).get("unlocked"))
    remix_unlocked = bool(rf.get("remixUnlocked") or raw.get("remixUnlocked") or licenses.get("remix"))
    clone_unlocked = bool(rf.get("cloneLicenseUnlocked") or raw.get("cloneLicenseUnlocked") or licenses.get("clone"))
    sdk_eligible = bool(rf.get("sdkAccess_eligible") or raw.get("sdkAccess_eligible") or raw.get("sdkAccess") or licenses.get("sdk"))

    # proposals: flatten legacy
    flat_proposals = raw.get("proposals") or []
    if not flat_proposals and "proposal" in raw:
        sent = raw["proposal"].get("proposalsSent", [])
        received = raw["proposal"].get("proposalsReceived", [])
        flat_proposals = [*sent, *received]

    raw.setdefault("amg", {"apps": [], "capabilities": [], "lastSync": None})
    raw.setdefault("ownership", {"aigx": 0, "royalties": 0, "ledger": []})
    raw.setdefault("jvMesh", [])
    raw.setdefault("contacts", {"sources": [], "counts": {}, "lastSync": None})

    normalized = {
        **raw,
        "schemaVersion": raw.get("schemaVersion") or CANONICAL_SCHEMA_VERSION,
        "username": username,
        "kits": kits,
        "licenses": licenses,
        "runtimeFlags": {
            **{"flagged": False, "eligibleForAudit": True, "needsReview": False, "autonomyLevel": raw.get("runtimeFlags", {}).get("autonomyLevel", "AL1")},
            **rf,
            "vaultAccess": vault_access,
            "remixUnlocked": remix_unlocked,
            "cloneLicenseUnlocked": clone_unlocked,
            "sdkAccess_eligible": sdk_eligible
        },
        "proposals": flat_proposals,
    }
    return normalized

async def _jsonbin_get(client: httpx.AsyncClient) -> Dict[str, Any]:
    r = await client.get(JSONBIN_URL, headers={"X-Master-Key": JSONBIN_SECRET})
    r.raise_for_status()
    return r.json()

async def _jsonbin_put(client: httpx.AsyncClient, users: list) -> None:
    r = await client.put(JSONBIN_URL,
                         headers={"X-Master-Key": JSONBIN_SECRET, "Content-Type": "application/json"},
                         json={"record": users})
    r.raise_for_status()

def _upsert(users: list, record: Dict[str, Any]) -> list:
    uname = record.get("username") or record.get("consent", {}).get("username")
    rid = record.get("id")
    replaced = False
    for i, u in enumerate(users):
        if u.get("id") == rid or (uname and (u.get("username") == uname or u.get("consent", {}).get("username") == uname)):
            users[i] = record
            replaced = True
            break
    if not replaced:
        users.append(record)
    return users

# --- helpers for new rails ---
async def _load_users(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    data = await _jsonbin_get(client)
    return data.get("record", [])

async def _save_users(client: httpx.AsyncClient, users: List[Dict[str, Any]]):
    await _jsonbin_put(client, users)

# ---- Shared helpers (added) ----
async def _get_users_client():
    client = httpx.AsyncClient(timeout=20)
    data = await _jsonbin_get(client)
    users = data.get("record", [])
    return users, client

def _find_user(users, username: str):
    uname = (username or "").lower()
    for u in users:
        u_un = (u.get("username") or (u.get("consent", {}) or {}).get("username") or "").lower()
        if u_un == uname:
            return u
    return None

def _require_key(users, username: str, provided: str | None):
    if provided and provided == os.getenv("ADMIN_TOKEN",""):
        return True
    u = _find_user(users, username)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    keys = [k for k in (u.get("api_keys") or []) if not k.get("revoked")]
    if not keys:
        if os.getenv("DEV_ALLOW_NO_API_KEY","").lower() in ("1","true","yes"):
            return True
        raise HTTPException(status_code=401, detail="no api keys on file")
    if not provided:
        raise HTTPException(status_code=401, detail="missing X-API-Key")
    if not any(k.get("key")==provided for k in keys):
        raise HTTPException(status_code=401, detail="invalid api key")
    return True

def _uname(u: Dict[str, Any]) -> str:
    return u.get("username") or (u.get("consent", {}) or {}).get("username")

def _ensure_business(u: Dict[str, Any]) -> Dict[str, Any]:
    u.setdefault("proposals", [])
    u.setdefault("quotes", [])
    u.setdefault("orders", [])
    u.setdefault("invoices", [])
    u.setdefault("payments", [])
    u.setdefault("contacts", [])
    u.setdefault("experiments", [])
    u.setdefault("kpi_snapshots", [])
    u.setdefault("tickets", [])
    u.setdefault("nps", [])
    u.setdefault("testimonials", [])
    u.setdefault("collectibles", [])
    u.setdefault("listings", [])
    u.setdefault("api_keys", [])
    u.setdefault("roles", [])
    u.setdefault("audit", [])
    u.setdefault("docs", [])
    u.setdefault("consents", [])
    u.setdefault("offers", [])
    u.setdefault("ownership", {"aigx": 0.0, "royalties": 0.0, "ledger": []})
    u.setdefault("yield", {"aigxEarned": 0.0})
    return u

def _find_in(lst: List[Dict[str, Any]], key: str, val: str) -> Optional[Dict[str, Any]]:
    for it in lst:
        if it.get(key) == val:
            return it
    return None

# ============================
# Endpoints
# ============================

# ---------- BANDIT: epsilon-greedy for creatives/offers ----------
def _bandit_slot(u: Dict[str, Any], key: str):
    b = u.setdefault("bandits", {}).setdefault(key, {"arms": {}})
    return b

@app.post("/bandit/next")
async def bandit_next(body: Dict = Body(...)):
    """
    Body: { username, key, arms:["A","B",...], epsilon:0.15 }
    Returns: { arm }
    """
    username = body.get("username"); key = body.get("key"); arms = body.get("arms") or []
    eps = float(body.get("epsilon", 0.15))
    if not (username and key and arms): return {"error":"username, key, arms required"}

    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        slot = _bandit_slot(u, key)
        # init arms
        for a in arms:
            slot["arms"].setdefault(a, {"n": 0, "r": 0.0})
        import random
        if random.random() < eps:
            choice = random.choice(arms)
        else:
            # pick argmax avg reward
            choice = max(arms, key=lambda a: (slot["arms"][a]["r"] / max(1, slot["arms"][a]["n"])))
        await _save_users(client, users)
        return {"ok": True, "arm": choice}

@app.post("/bandit/reward")
async def bandit_reward(body: Dict = Body(...)):
    """
    Body: { username, key, arm, reward }   # reward ∈ [0,1] (click/lead/won)
    """
    username = body.get("username"); key = body.get("key"); arm = body.get("arm")
    reward = float(body.get("reward", 0))
    if not (username and key and arm): return {"error":"username, key, arm required"}
    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        slot = _bandit_slot(u, key)
        armstat = slot["arms"].setdefault(arm, {"n":0, "r":0.0})
        armstat["n"] += 1
        armstat["r"] += reward
        await _save_users(client, users)
        return {"ok": True, "arm": arm, "n": armstat["n"], "sum_r": armstat["r"]}

# ---- GET/POST: normalized user by username ----
@app.post("/user")
async def get_user(request: Request):
    body = await request.json()
    username = (body or {}).get("username")
    if not username:
        return {"error": "Missing username"}

    async with httpx.AsyncClient(timeout=15) as client:
        data = await _jsonbin_get(client)
        for record in data.get("record", []):
            if record.get("username") == username or record.get("consent", {}).get("username") == username:
                return {"record": normalize_user_record(record)}
        return {"error": "User not found"}

# ---- POST: mint (idempotent) ----
@app.post("/mint")
async def mint_user(request: Request):
    body = await request.json()
    username = body.get("username")
    company_type = body.get("companyType", "general")
    referral = body.get("referral", "origin/hero")
    if not username:
        return {"ok": False, "error": "Username required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for u in users:
            if u.get("username") == username or u.get("consent", {}).get("username") == username:
                return {"ok": True, "record": normalize_user_record(u)}

        new_user = make_canonical_record(username, company_type, referral)
        users = _upsert(users, new_user)
        await _jsonbin_put(client, users)
        try:
            log_agent_update(new_user)
            append_intent_ledger(username, {"event":"mint","referral": referral})
        except Exception:
            pass
        return {"ok": True, "record": normalize_user_record(new_user)}

# ---- POST: unlock (kits/licenses/flags) ----
@app.post("/unlock")
async def unlock_feature(request: Request):
    body = await request.json()
    username = body.get("username")
    target = body.get("target")  # e.g., "branding" (kit) or "sdk" (license) or runtime "vaultAccess"
    kind   = body.get("kind", "kit")  # "kit" | "license" | "flag"
    value  = bool(body.get("value", True))
    if not (username and target):
        return {"error": "username & target required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i, u in enumerate(users):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname == username:
                if kind == "kit":
                    u.setdefault("kits", _empty_kits())
                    u["kits"].setdefault(target, {"unlocked": False})
                    u["kits"][target]["unlocked"] = value
                elif kind == "license":
                    u.setdefault("licenses", _empty_licenses())
                    u["licenses"][target] = value
                else:
                    u.setdefault("runtimeFlags", {})
                    u["runtimeFlags"][target] = value

                u.setdefault("transactions", {}).setdefault("unlocks", []).append(
                    {"target": target, "kind": kind, "value": value, "ts": _now()}
                )
                users[i] = u
                await _jsonbin_put(client, users)
                return {"ok": True, "record": normalize_user_record(u)}
        return {"error": "User not found"}

# ---- POST: AMG sync (App Monetization Graph) ----
@app.post("/amg/sync")
async def amg_sync(request: Request):
    """
    Body: { username, apps: [{name, scopes:[]}, ...] }
    Derives capabilities and saves to user.amg
    """
    body = await request.json()
    username = body.get("username")
    apps = body.get("apps", [])
    if not username:
        return {"error": "username required"}

    caps = set()
    for app in apps:
        n = (app.get("name") or "").lower()
        scopes = [s.lower() for s in app.get("scopes", [])]
        if n in ("shopify","woo","square","stripe"):
            caps.add("commerce_in")
        if any(s in scopes for s in ("payments","charges.read","orders.read")):
            caps.add("commerce_in")
        if n in ("gmail","outlook","mailgun","postmark"):
            caps.add("email_out")
        if n in ("tiktok","instagram","facebook","twitter","x","linkedin","youtube"):
            caps.add("content_out")
        if n in ("calendly","calendar","google calendar","outlook calendar"):
            caps.add("calendar")
        if n in ("twilio","messagebird","nexmo"):
            caps.add("sms_out")
        if n in ("meta-ads","google-ads","tiktok-ads"):
            caps.add("ads_budget")

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i, u in enumerate(users):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname == username:
                u.setdefault("amg", {"apps": [], "capabilities": [], "lastSync": None})
                u["amg"]["apps"] = apps
                u["amg"]["capabilities"] = sorted(list(caps))
                u["amg"]["lastSync"] = _now()
                users[i] = u
                await _jsonbin_put(client, users)
                return {"ok": True, "amg": u["amg"], "record": normalize_user_record(u)}
        return {"error": "User not found"}

# ===== Money / Summary =====
@app.post("/money/summary")
async def money_summary(body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        return {"ok": True, "summary": _money_summary(u)}

# ===== Referral credit (double-sided friendly) =====
@app.post("/referral/credit")
async def referral_credit(body: Dict = Body(...)):
    """
    Body: { referrer: "alice", newUser: "bob", amount?: number }
    Adds AIGx to referrer for bringing in a new user.
    """
    referrer = body.get("referrer"); new_user = body.get("newUser")
    amount = float(body.get("amount", REFERRAL_BOUNTY))
    if not (referrer and new_user): return {"error":"referrer & newUser required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        r = next((x for x in users if _uname(x)==referrer), None)
        if not r: return {"error":"referrer not found"}
        _ensure_business(r)
        # ledger
        entry = {"ts": _now(), "amount": amount, "currency": "AIGx", "basis": "referral_bounty", "ref": new_user}
        r["ownership"]["ledger"].append(entry)
        r["ownership"]["aigx"] = float(r["ownership"].get("aigx",0)) + amount
        r.setdefault("transactions", {}).setdefault("referralEvents", []).append(
            {"user": new_user, "amount": amount, "ts": _now()}
        )
        await _save_users(client, users)
        return {"ok": True, "ledgerEntry": entry, "summary": _money_summary(r)}

# ===== Wallet connect / payout rail =====

@app.post("/wallet/connect")
async def wallet_connect(body: Dict = Body(...)):
    """
    Body: { username, method: "stripe"|"crypto", account?: "acct_...", address?: "0x..", note? }
    Stores payout destination metadata for the user.
    """
    username = body.get("username"); method = (body.get("method") or "stripe").lower()
    if not username: return {"error":"username required"}
    if method not in ("stripe","crypto"): return {"error":"method must be stripe|crypto"}

    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        w = u.setdefault("wallet", {})
        w["method"] = method
        if method == "stripe":
            if body.get("account"): w["stripe_connect_id"] = body.get("account")
        else:
            if body.get("address"): w["crypto_address"] = body.get("address")
        w["updated"] = _now(); w["note"] = body.get("note")
        await _save_users(client, users)

        safe = {k:v for k,v in w.items() if k not in ("keys","secrets")}
        return {"ok": True, "wallet": safe}

@app.post("/payout/request")
async def payout_request(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key'), idemp: str | None = Header(None, alias='Idempotency-Key')):
    body = await request.json()
    """
    Body: { username, amount, method?: "stripe"|"crypto" }
    Checks available balance and raises a payout request (queued for ops/batch).
    """
    username = body.get("username"); amount = float(body.get("amount", 0))
    method = (body.get("method") or "stripe").lower()
    if not (username and amount): return {"error":"username & amount required"}
    if amount < PAYOUT_MIN: return {"error": f"minimum payout is {PAYOUT_MIN}"}

    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        _require_key(users, username, x_api_key)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        # ensure wallet is set
        w = u.get("wallet") or {}
        if (method == 'stripe' and not w.get('stripe_connect_id')) or (method == 'crypto' and not w.get('crypto_address')):
            return {"error":"no payout destination on file; call /wallet/connect first"}

        money = _money_summary(u)
        if amount > money["available"]:
            return {"error": f"insufficient available funds ({money['available']})"}

        u.setdefault("payouts", [])
        pid = _id("pyo")
        req = {"id": pid, "amount": round(amount,2), "method": method, "status":"requested",
               "ts": _now(), "requested_by": username}
        u["payouts"].append(req)
        await _save_users(client, users)
        return {"ok": True, "payout": req, "summary": _money_summary(u)}

# ---- POST: Autonomy Level AL0–AL5 ----
@app.post("/autonomy")
async def set_autonomy(request: Request):
    body = await request.json()
    username = body.get("username")
    level = body.get("level", "AL1")  # AL0 ask-first … AL5 full-auto
    guardrails = body.get("guardrails", {}) # e.g. {"maxDiscount":0.1,"quietHours":[22,8],"budget":200}
    if not username:
        return {"error": "username required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i, u in enumerate(users):
            u_name = u.get("username") or u.get("consent", {}).get("username")
            if u_name == username:
                u.setdefault("runtimeFlags", {})
                u["runtimeFlags"]["autonomyLevel"] = level
                u.setdefault("policy", {})
                u["policy"]["guardrails"] = guardrails
                users[i] = u
                await _jsonbin_put(client, users)
                return {"ok": True, "record": normalize_user_record(u)}
        return {"error": "User not found"}

@app.post("/payout/status")
async def payout_status(body: Dict = Body(...)):
    """
    Admin/daemon hook.
    Body: { username, payoutId, status: "queued"|"paid"|"failed", txn_id? }
    On 'paid' we post a negative payout ledger line.
    """
    username = body.get("username"); pid = body.get("payoutId"); status = (body.get("status") or "").lower()
    if not (username and pid and status): return {"error":"username, payoutId, status required"}
    if status not in ("queued","paid","failed"): return {"error":"bad status"}

    async with httpx.AsyncClient(timeout=30) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)

        pay = next((p for p in u.get("payouts", []) if p.get("id")==pid), None)
        if not pay: return {"error":"payout not found"}
        pay["status"] = status; pay["status_ts"] = _now()
        if body.get("txn_id"): pay["txn_id"] = body.get("txn_id")

        if status == "paid":
            # finalize by ledgering a negative payout
            amt = float(pay.get("amount",0))
            entry = {"ts": _now(), "amount": -amt, "currency": "USD", "basis": "payout", "ref": pid}
            u["ownership"]["ledger"].append(entry)

        await _save_users(client, users)
        return {"ok": True, "payout": pay, "summary": _money_summary(u)}

# ---- POST: AIGx credit (Earn Layer receipts) ----
@app.post("/aigx/credit")
async def aigx_credit(request: Request):
    """
    Body: { username, amount, basis, ref }
    Adds to ownership.ledger and yield.aigxEarned
    """
    body = await request.json()
    username = body.get("username")
    amount = float(body.get("amount", 0))
    basis  = body.get("basis","uplift")  # uplift|royalty|bounty|task
    ref    = body.get("ref")            # optional invoice/ref
    if not (username and amount):
        return {"error": "username & amount required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i, u in enumerate(users):
            if (u.get("username") or u.get("consent", {}).get("username")) == username:
                u.setdefault("ownership", {"aigx":0,"royalties":0,"ledger":[]})
                u.setdefault("yield", {"aigxEarned":0})
                entry = {"ts": _now(), "amount": amount, "currency": "AIGx", "basis": basis, "ref": ref}
                u["ownership"]["ledger"].append(entry)
                u["ownership"]["aigx"] = float(u["ownership"].get("aigx",0)) + amount
                u["yield"]["aigxEarned"] = float(u["yield"].get("aigxEarned",0)) + amount
                users[i] = u
                await _jsonbin_put(client, users)
                try:
                    append_intent_ledger(username, {"event":"aigx_credit","amount": amount, "basis": basis})
                    log_metaloop(username, "credit", {"basis": basis, "amount": amount})
                except Exception:
                    pass
                return {"ok": True, "ledgerEntry": entry, "record": normalize_user_record(u)}
        return {"error": "User not found"}

@app.post("/referral/link")
async def referral_link(body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    oid = _id("ref"); exp = int((datetime.utcnow()+timedelta(days=14)).timestamp())
    sig = _hmac(f"{oid}.{username}.{exp}", POL_SECRET)
    url = f"/r?oid={oid}&sig={sig}&ref={username}&exp={exp}"
    return {"ok": True, "url": url, "exp": exp}

@app.post("/vault/autostake")
async def vault_autostake(body: Dict = Body(...)):
    username = body.get("username"); enabled = bool(body.get("enabled", True)); pct = float(body.get("percent", 0.5))
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        y = u.setdefault("yield", {}); y["autoStake"] = enabled; y["autoStakePct"] = pct
        await _save_users(client, users)
        return {"ok": True, "yield": y}

@app.get("/metrics")
async def metrics():
    async with httpx.AsyncClient(timeout=30) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        rev = fee = payouts = invoices_open = 0.0
        for u in users:
            for l in (u.get("ownership", {}).get("ledger", []) or []):
                if l.get("basis") == "revenue": rev += float(l.get("amount",0))
                if l.get("basis") == "platform_fee": fee += float(l.get("amount",0))
                if l.get("basis") == "payout": payouts += float(l.get("amount",0))
            for inv in (u.get("invoices",[]) or []):
                if inv.get("status") == "issued": invoices_open += float(inv.get("amount",0))
        return {"ok": True, "totals": {
            "revenue": round(rev,2), "platform_fees": round(fee,2),
            "payouts": round(payouts,2), "invoices_open": round(invoices_open,2)
        }}
# Add to main.py after your existing /user endpoint

@app.get("/users/all")
async def get_all_users(limit: int = 100):
    """
    Return all users (for matching). Paginate in production.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])[:limit]
        
        # Strip sensitive data
        safe_users = []
        for u in users:
            safe_users.append({
                "username": u.get("username") or u.get("consent", {}).get("username"),
                "traits": u.get("traits", []),
                "outcomeScore": u.get("outcomeScore", 0),
                "kits": list(u.get("kits", {}).keys()),
                "meta_role": u.get("meta_role", ""),
            })
        
        return {"ok": True, "users": safe_users, "count": len(safe_users)}
 # ---------- ALGO HINTS + SCHEDULER ----------
@app.post("/algo/hints/upsert")
async def algo_hints_upsert(body: Dict = Body(...)):
    """
    Body: { username, platform, hints: { cadence_per_day, quiet_hours:[22,8], max_caption_len, hashtags:int } }
    """
    username = body.get("username"); platform = (body.get("platform") or "").lower()
    hints = body.get("hints") or {}
    if not (username and platform): return {"error":"username & platform required"}
    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        u.setdefault("algo_hints", {})[platform] = hints
        await _save_users(client, users)
        return {"ok": True, "hints": hints}

@app.post("/algo/schedule/plan")
async def algo_schedule_plan(body: Dict = Body(...)):
    """
    Body: { username, platform, window_hours: 48, start_iso?: now }
    Returns: { slots:[iso...] } best-effort evenly spaced outside quiet hours.
    """
    username = body.get("username"); platform = (body.get("platform") or "").lower()
    window = int(body.get("window_hours", 48))
    start = datetime.fromisoformat(body.get("start_iso")) if body.get("start_iso") else datetime.utcnow()
    if not (username and platform): return {"error":"username & platform required"}
    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        hints = (u.get("algo_hints") or {}).get(platform, {})
        per_day = max(1, int(hints.get("cadence_per_day", 2)))
        quiet   = hints.get("quiet_hours", [23, 7])  # [startHour, endHour)
        slots = []
        total_posts = int((window/24.0) * per_day)
        step = timedelta(hours=window/max(1,total_posts))
        t = start
        while len(slots) < total_posts:
            hr = t.hour
            bad = quiet and ((quiet[0] <= hr) or (hr < quiet[1])) if quiet[0] < quiet[1] else (quiet[1] <= hr <= quiet[0])
            if not bad:
                slots.append(t.replace(microsecond=0).isoformat()+"Z")
            t += step
        return {"ok": True, "slots": slots}

# ---------- DISTRIBUTION REGISTRY + PUSH ----------
@app.post("/distribution/register")
async def distribution_register(request: Request, x_api_key: str | None = Header(None, alias="X-API-Key")):
    body = await request.json()
    """
    Body: { username, channel, endpoint_url, token }
    """
    username = body.get("username")
    channel = (body.get("channel") or "partner").lower()
    endpoint_url = body.get("endpoint_url") or body.get("endpoint") or body.get("url")
    token = body.get("token")
    if not (username and endpoint_url and token):
        return {"error":"username, endpoint_url, token required"}
    if not _safe_url(str(endpoint_url or "")):
        raise HTTPException(status_code=400, detail="endpoint not allowed")
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x) == username), None)
        _require_key(users, username, x_api_key)
        if not u:
            return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("distribution", []).append({
            "id": str(uuid.uuid4()),
            "channel": channel,
            "url": endpoint_url,
            "token": token,
            "ts": _now()
        })
        await _save_users(client, users)
        return {"ok": True}

@app.post("/distribution/push")
async def distribution_push(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    """
    Body: { username, listingId, channels?:[] }
    Pushes a signed lightweight Offer Card (POL) to registered webhooks.
    """
    username = body.get("username"); lid = body.get("listingId"); channels = body.get("channels")
    if not (username and lid): return {"error":"username & listingId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        _require_key(users, username, x_api_key)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        listing = _find_in(u.get("listings", []), "id", lid)
        if not listing: return {"error":"listing not found"}

        # prep POL-like card
        oid = _id("pol")
        exp = int((datetime.utcnow()+timedelta(days=2)).timestamp())
        sig = _hmac(f"{oid}.{username}.{exp}", POL_SECRET)
        card = {
            "oid": oid, "sig": sig, "exp": exp, "src": "distribution",
            "title": listing["title"], "price": listing.get("price",0), "usr": username,
            "url": f"/offer?oid={oid}&sig={sig}&usr={username}&exp={exp}&src=dist"
        }

        dispatched = []
        for d in u.get("distribution", []):
            if channels and d["channel"] not in channels:
                continue
            try:
                r = await client.post(d["url"], json={"token": d["token"], "card": card}, timeout=8)
                dispatched.append({"channel": d["channel"], "status": r.status_code})
            except Exception:
                dispatched.append({"channel": d["channel"], "status": "error"})

        listing["impressions"] = listing.get("impressions", 0) + len(dispatched)
        await _save_users(client, users)
        return {"ok": True, "sent": dispatched, "card": card}

# ---------- REVENUE SPLITTER (JV mesh) ----------
@app.post("/revenue/split")
async def revenue_split(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    """
    Body: { username, amount, currency:'USD', ref, jvId? }
    If jvId present, split by that entry; else split equally across all JV mesh entries.
    """
    username = body.get("username"); amt = float(body.get("amount", 0)); cur = (body.get("currency") or "USD").upper()
    ref = body.get("ref"); jvId = body.get("jvId")
    if not (username and amt): return {"error":"username & amount required"}

    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        _require_key(users, username, x_api_key)
        def find_user(name): return next((x for x in users if _uname(x)==name), None)
        origin = find_user(username)
        if not origin: return {"error":"user not found"}

        mesh = origin.get("jvMesh", []) or []
        targets = []
        # resolve targets
        if jvId:
            jv = _find_in(mesh, "id", jvId)
            if not jv:
                return {"error": "jv not found"}
            jv_split = jv.get("split") or []
            if not jv_split:
                targets = [(username, 1.0)]
            else:
                targets = [(name, float(frac)) for name, frac in jv_split if float(frac) > 0]
        else:
            targets = [(username, 1.0)]


        for uname, frac in targets:
            u = find_user(uname) or origin
            u.setdefault("ownership", {"aigx":0,"royalties":0,"ledger":[]})
            val = round(amt * frac, 2)
            entry = {"ts": _now(), "amount": val, "currency": cur, "basis": "jv_split", "ref": ref}
            u["ownership"]["ledger"].append(entry)
            u["ownership"]["aigx"] = float(u["ownership"].get("aigx",0)) + val

        await _save_users(client, users)
        return {"ok": True, "distributed": [{"user":t[0], "amount": round(amt*t[1],2)} for t in targets]}

# ---------- CREATIVE RENDER (FTC-safe) ----------
DISCLOSURES = {
    "tiktok": "#ad",
    "instagram": "#ad",
    "x": "Ad:",
    "twitter": "Ad:",
    "linkedin": "Sponsored",
    "youtube": "Includes paid promotion",
}

@app.post("/creative/render")
async def creative_render(body: Dict = Body(...)):
    """
    Body: { username, platform, caption, intent? }
    Ensures disclosure + max caption len based on algo hints (if set).
    """
    username = body.get("username"); platform = (body.get("platform") or "tiktok").lower()
    caption  = (body.get("caption") or "").strip()
    if not username: return {"error":"username required"}

    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        hints = (u.get("algo_hints") or {}).get(platform, {})
        max_len = int(hints.get("max_caption_len", 2200 if platform == "instagram" else 280))
        disc = DISCLOSURES.get(platform)
        out = caption
        if disc and disc.lower() not in caption.lower():
            out = f"{disc} {caption}".strip()
        if len(out) > max_len:
            out = out[:max_len-1] + "…"
        return {"ok": True, "caption": out, "disclosure": disc, "max_len": max_len}

# ---- POST: Contacts (privacy-first) opt-in + counts ----
@app.post("/contacts/optin")
async def contacts_optin(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    """
    Body: { username, sources: [{source:"upload/csv/gmail/phone", count:int}] }
    We store counts only (privacy-first). Send actual outreach via /contacts/send -> webhook.
    """
    body = await request.json()
    username = body.get("username")
    sources  = body.get("sources", [])
    if not username:
        return {"error": "username required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i, u in enumerate(users):
            if (u.get("username") or u.get("consent", {}).get("username")) == username:
                u.setdefault("contacts", {"sources": [], "counts": {}, "lastSync": None})
                for s in sources:
                    src = s.get("source","unknown")
                    cnt = int(s.get("count",0))
                    u["contacts"]["counts"][src] = int(u["contacts"]["counts"].get(src,0)) + cnt
                    if src not in u["contacts"]["sources"]:
                        u["contacts"]["sources"].append(src)
                u["contacts"]["lastSync"] = _now()
                users[i] = u
                await _jsonbin_put(client, users)
                return {"ok": True, "contacts": u["contacts"], "record": normalize_user_record(u)}
        return {"error": "User not found"}

# ---------- MONETIZE: BUDGET SCALER BY ROAS ----------
@app.post("/monetize/scale")
async def monetize_scale(body: Dict = Body(...)):
    """
    Body: { username, roas: float, min:0.5, max:1.5 }
    Returns a multiplier for tomorrow's budget based on ROAS.
    """
    username = body.get("username"); roas = float(body.get("roas", 1.0))
    lo = float(body.get("min", 0.8)); hi = float(body.get("max", 1.25))
    if not username: return {"error":"username required"}
    # piecewise: below 1.0 → shrink; above 2.0 → boost; clamp
    if roas < 0.8: m = lo
    elif roas < 1.0: m = 0.9
    elif roas < 1.5: m = 1.05
    elif roas < 2.0: m = 1.15
    else: m = hi
    return {"ok": True, "multiplier": round(m, 3)}

# ---- POST: Contacts send (webhook; logs outreach) [FIXED + RATE LIMIT] ----
@app.post("/contacts/send")
async def contacts_send(request: Request):
    """
    Body: { username, channel:"sms|email|dm", template, previewOnly=false }
    We store outreach events & counts only (no raw PII).
    Optional webhook fanout via PROPOSAL_WEBHOOK_URL.
    Adds soft per-user/channel rate-limit: 50 sends / 24h.
    """
    body = await request.json()
    username = body.get("username")
    channel  = (body.get("channel") or "email").lower()
    template = body.get("template") or ""
    preview  = bool(body.get("previewOnly", False))
    if not (username and template):
        return {"error": "username & template required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data  = await _jsonbin_get(client)
        users = data.get("record", [])
        # load user first (previous bug fix)
        idx = next((i for i,u in enumerate(users) if (u.get("username") or u.get("consent", {}).get("username")) == username), None)
        if idx is None:
            return {"error": "User not found"}
        u = users[idx]
        _ensure_business(u)

        # soft rate-limit
        today = datetime.utcnow().date().isoformat()
        rl = u.setdefault("rate_limits", {}).setdefault("contacts_send", {})
        stats = rl.setdefault(channel, {"date": today, "count": 0})
        if stats["date"] != today:
            stats["date"] = today
            stats["count"] = 0
        if stats["count"] >= 50 and not preview:
            return {"error": "rate_limited", "detail": "Daily channel cap reached"}

        payload = {"type": "contacts_send", "channel": channel, "username": username, "template": template, "ts": _now()}
        delivered = False
        if (PROPOSAL_WEBHOOK_URL and not preview):
            try:
                r = await client.post(PROPOSAL_WEBHOOK_URL, json=payload, headers={"Content-Type":"application/json"})
                delivered = r.status_code in (200, 204)
            except Exception:
                delivered = False

        stats["count"] += 1
        u.setdefault("transactions", {}).setdefault("outreachEvents", []).append(
            {"channel": channel, "templateHash": hash(template), "delivered": delivered, "ts": _now()}
        )
        users[idx] = u
        await _jsonbin_put(client, users)
        return {"ok": True, "delivered": delivered, "count": stats["count"]}


# ---- POST: JV Mesh (MetaBridge 2.0 cap-table stub) ----
@app.post("/jv/create")
async def jv_create(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    """
    Body: { a: "userA", b: "userB", title, split: {"a":0.6,"b":0.4}, terms }
    Appends JV entry to both users' jvMesh; settlement handled by MetaBridge runtime.
    """
    body = await request.json()
    username = (body.get('username') or body.get('consent',{}).get('username'))
    a = body.get("a"); b = body.get("b")
    title = body.get("title","JV")
    split = body.get("split", {"a":0.5,"b":0.5})
    terms = body.get("terms","rev-share on matched bundles")
    if not (a and b):
        return {"error": "a & b usernames required"}

    entry = {"id": str(uuid.uuid4()), "title": title, "split": split, "terms": terms, "created": _now()}
    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        found = 0
        for i, u in enumerate(users):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname in (a, b):
                u.setdefault("jvMesh", []).append(entry)
                users[i] = u
                found += 1
        if found == 2:
            await _jsonbin_put(client, users)
            return {"ok": True, "jv": entry}
        return {"error": "One or both users not found"}

# ---- UPDATED: MetaBridge — generate & persist proposals via /submit_proposal ----
@app.post("/metabridge")
async def metabridge_dispatch(request: Request):
    try:
        data = await request.json()
        query = (data.get("query") or "").strip()
        originator = data.get("username", "anonymous")
        if not query:
            return {"error": "No query provided."}

        from aigent_growth_agent import (
            metabridge_dual_match_realworld_fulfillment,
            proposal_generator
        )
        matches   = metabridge_dual_match_realworld_fulfillment(query)
        proposals = proposal_generator(query, matches, originator)

        base = (os.getenv("SELF_URL") or str(request.base_url)).rstrip("/")
        submit_url = f"{base}/submit_proposal"

        async with httpx.AsyncClient(timeout=20) as client:
            for p in proposals:
                await client.post(submit_url, json=p, headers={"Content-Type": "application/json"})

        try:
            log_metabridge(originator, {"query": query, "matches": len(matches)})
        except Exception:
            pass

        return {"status": "ok", "query": query, "match_count": len(matches), "proposals": proposals, "matches": matches}
    except Exception as e:
        return {"error": f"MetaBridge runtime error: {e}"}

# ---- Agent passthrough ----
@app.post("/agent")
async def run_agent(request: Request):
    try:
        data = await request.json()
        user_input = data.get("input","")
        if not user_input: return {"error":"No input provided."}
        initial_state = {"input": user_input, "memory": []}
        result = await agent_graph.ainvoke(initial_state)
        return {"output": result.get("output","No output returned.")}
    except Exception as e:
        return {"error": f"Agent runtime error: {str(e)}"}

# ---- Existing router/decide (intent orchestrator) retained ----
@app.post("/router/decide")
async def router_decide(request: Request):
    """
    Body: { username, intent, payload, previewOnly=false }
    Returns a routing decision with risk/holdout flags for safe execution.
    """
    body = await request.json()
    username = body.get("username")
    intent = body.get("intent","generic")
    payload = body.get("payload",{})
    preview = bool(body.get("previewOnly", False))

    decision = {
        "intent": intent,
        "action": "shadow" if preview else "execute",
        "score": 0.62,   # placeholder scorer
        "blocked": False,
        "control": False,
        "ts": _now()
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            data = await _jsonbin_get(client)
            users = data.get("record", [])
            for u in users:
                uname = u.get("username") or u.get("consent", {}).get("username")
                if uname == username:
                    quiet = u.get("policy", {}).get("guardrails", {}).get("quietHours")
                    if isinstance(quiet, (list, tuple)) and len(quiet)==2:
                        decision["blocked"] = False  # implement localtime check if needed
                    import random
                    decision["control"] = (not preview) and (random.random() < 0.1)
                    break
    except Exception:
        pass

    return {"ok": True, "decision": decision}

# ---- Consent (list/upsert) retained ----
@app.post("/consent/upsert")
async def consent_upsert(request: Request):
    """
    Body: { username, scopes:[], connectors:[] }
    Upserts consent scopes/connectors to user.consent.
    """
    body = await request.json()
    username = body.get("username")
    scopes = body.get("scopes", [])
    connectors = body.get("connectors", [])
    if not username:
        return {"error":"username required"}

    async with httpx.AsyncClient(timeout=15) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i,u in enumerate(users):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname == username:
                u.setdefault("consent", {}).setdefault("scopes", [])
                u.setdefault("consent", {}).setdefault("connectors", [])
                u["consent"]["scopes"] = sorted(list(set(u["consent"]["scopes"] + scopes)))
                u["consent"]["connectors"] = sorted(list(set(u["consent"]["connectors"] + connectors)))
                users[i]=u
                await _jsonbin_put(client, users)
                return {"ok": True, "consent": u["consent"], "record": normalize_user_record(u)}
        return {"error":"User not found"}

@app.post("/consent/list")
async def consent_list(request: Request):
    body = await request.json()
    username = body.get("username")
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=10) as client:
        data = await _jsonbin_get(client)
        for u in data.get("record", []):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname == username:
                return {"ok": True, "consent": u.get("consent", {})}
    return {"error":"User not found"}

# ---- Micro-Pricing nudger retained ----
@app.post("/pricing/nudge")
async def pricing_nudge(request: Request):
    """
    Body: { username, itemId, floor, currentPrice }
    Returns a safe ±1–3% nudge recommendation, respecting floors.
    """
    body = await request.json()
    username = body.get("username")
    floor = float(body.get("floor", 0))
    price = float(body.get("currentPrice", 0))
    if not username: return {"error":"username required"}

    import random
    delta = round(price * (random.choice([0.01, 0.02, 0.03])) * random.choice([-1, 1]), 2)
    proposed = max(floor, price + delta)
    rec = {"old": price, "delta": proposed - price, "new": proposed, "ts": _now()}
    return {"ok": True, "recommendation": rec}

# ---- MetaHive stubs retained ----
@app.post("/metahive/optin")
async def metahive_optin(request: Request):
    body = await request.json()
    username = body.get("username")
    enabled = bool(body.get("enabled", True))
    if not username: return {"error":"username required"}

    async with httpx.AsyncClient(timeout=15) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i,u in enumerate(users):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname == username:
                u.setdefault("metahive", {}).update({"enabled": enabled, "joinedAt": _now()})
                users[i]=u
                await _jsonbin_put(client, users)
                return {"ok": True, "metahive": u.get("metahive", {})}
    return {"error":"User not found"}

@app.post("/metahive/summary")
async def metahive_summary(request: Request):
    async with httpx.AsyncClient(timeout=15) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        enabled = [u for u in users if u.get("metahive", {}).get("enabled")]
        return {"ok": True, "members": len(enabled)}

# === TEMPLATE CATALOG ROUTES (non-destructive) ===
try:
    from fastapi import APIRouter
    from templates_catalog import list_templates, search_templates, get_template
except Exception:
    APIRouter = None

_tpl_router = APIRouter() if 'APIRouter' in globals() and APIRouter else None

if _tpl_router:
    @_tpl_router.get('/templates/list')
    async def templates_list():
        try:
            return {'ok': True, 'templates': list_templates()}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    @_tpl_router.get('/templates/search')
    async def templates_search(q: str = ''):
        try:
            return {'ok': True, 'templates': search_templates(q)}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    @_tpl_router.post('/templates/activate')
    async def templates_activate(payload: dict):
        """Activate a template (echo-only for now; frontend also passes context)."""
        try:
            tid = payload.get('id') or payload.get('template_id')
            t = get_template(tid)
            if not t:
                return {'ok': False, 'error': 'template_not_found'}
            return {'ok': True, 'active_template': t}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

try:
    app  # type: ignore
    if _tpl_router:
        app.include_router(_tpl_router)
except Exception:
    pass

# ================================
# >>> Business-in-a-Box: NEW ROUTES <<<
# ================================

# ---------- 1) ORDER-TO-CASH ----------
@app.post("/quote/create")
async def quote_create(body: Dict = Body(...)):
    username = body.get("username"); proposalId = body.get("proposalId")
    price = float(body.get("price", 0)); scope = body.get("scope",""); terms = body.get("terms","")
    if not (username and proposalId): return {"error":"username & proposalId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        prop = _find_in(u["proposals"], "id", proposalId) or {}
        qid = _id("qt")
        quote = {"id": qid, "proposalId": proposalId, "price": price, "scope": scope, "terms": terms,
                 "status":"offered", "ts": _now(), "title": prop.get("title","")}
        u["quotes"].append(quote)
        await _save_users(client, users)
        return {"ok": True, "quote": quote}

@app.post("/order/accept")
async def order_accept(body: Dict = Body(...)):
    username = body.get("username"); qid = body.get("quoteId")
    if not (username and qid): return {"error":"username & quoteId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        quote = _find_in(u["quotes"], "id", qid)
        if not quote: return {"error":"quote not found"}
        quote["status"] = "accepted"
        oid = _id("ord")
        order = {
            "id": oid, "quoteId": qid, "status":"queued", "ts": _now(),
            "sla": {"due": (datetime.utcnow()+timedelta(hours=48)).isoformat(), "breaches":0},
            "tasks": [
                {"id": _id("t"), "title":"Kickoff / assets intake", "status":"todo"},
                {"id": _id("t"), "title":"Deliverable v1", "status":"todo"},
                {"id": _id("t"), "title":"Review & revisions", "status":"todo"},
                {"id": _id("t"), "title":"Final delivery", "status":"todo"},
            ]
        }
        u["orders"].append(order)
        await _save_users(client, users)
        return {"ok": True, "order": order}

# Add to main.py

@app.post("/intent/auto_bid")
async def intent_auto_bid(background_tasks: BackgroundTasks):
    """
    Cron job (runs every 30s).
    Growth agents auto-bid on matching intents.
    """
    users, client = await _get_users_client()
    
    # Fetch all open intents
    try:
        r = await client.get("http://localhost:8000/intents/list?status=AUCTION")
        intents = r.json().get("intents", [])
    except Exception:
        return {"ok": False, "error": "failed to fetch intents"}
    
    bids_submitted = []
    
    for intent in intents:
        iid = intent["id"]
        brief = intent["intent"].get("brief", "").lower()
        budget = float(intent.get("escrow_usd", 0))
        
        # Match users who can fulfill this
        for u in users:
            username = _username_of(u)
            traits = u.get("traits", [])
            
            # Simple matching logic
            can_fulfill = False
            if "marketing" in brief and "marketing" in traits:
                can_fulfill = True
            elif "video" in brief and "marketing" in traits:
                can_fulfill = True
            elif "sdk" in brief and "sdk" in traits:
                can_fulfill = True
            elif "legal" in brief and "legal" in traits:
                can_fulfill = True
            
            if not can_fulfill:
                continue
            
            # Calculate competitive bid (underbid budget by 10-20%)
            import random
            discount = random.uniform(0.10, 0.20)
            bid_price = round(budget * (1 - discount), 2)
            delivery_hours = 48 if "urgent" not in brief else 24
            
            # Submit bid
            try:
                await client.post(
                    "http://localhost:8000/intents/bid",
                    json={
                        "intent_id": iid,
                        "agent": username,
                        "price_usd": bid_price,
                        "delivery_hours": delivery_hours,
                        "message": f"I can deliver this within {delivery_hours}h for ${bid_price}."
                    }
                )
                bids_submitted.append({"intent": iid, "agent": username, "price": bid_price})
            except Exception as e:
                print(f"Failed to bid for {username} on {iid}: {e}")
    
    return {"ok": True, "bids_submitted": bids_submitted}
    
@app.post("/invoice/create")
async def invoice_create(body: Dict = Body(...)):
    username = body.get("username"); oid = body.get("orderId")
    amount = float(body.get("amount",0)); currency = (body.get("currency") or "USD").upper()
    if not (username and oid): return {"error":"username & orderId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        order = _find_in(u["orders"], "id", oid)
        if not order: return {"error":"order not found"}
        inv_id = _id("inv")
        invoice = {"id": inv_id, "orderId": oid, "amount": amount, "currency": currency,
                   "status":"issued", "ts": _now()}
        u["invoices"].append(invoice)
        await _save_users(client, users)
        return {"ok": True, "invoice": invoice}

@app.post("/pay/link")
async def pay_link(body: Dict = Body(...)):
    username = body.get("username"); inv_id = body.get("invoiceId")
    if not (username and inv_id): return {"error":"username & invoiceId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        invoice = _find_in(u["invoices"], "id", inv_id)
        if not invoice: return {"error":"invoice not found"}
        pay_id = _id("pay")
        checkout_url = f"https://pay.aigentsy/checkout/{inv_id}"  # swap for real Stripe if needed
        payment = {"id": pay_id, "invoiceId": inv_id, "amount": invoice["amount"],
                   "currency": invoice["currency"], "status":"pending", "ts": _now(),
                   "provider":"stripe", "checkout_url": checkout_url}
        u["payments"].append(payment)
        await _save_users(client, users)
        return {"ok": True, "checkout_url": checkout_url, "payment": payment}

@app.post("/revenue/recognize")
async def revenue_recognize(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    username = body.get("username"); inv_id = body.get("invoiceId")
    if not (username and inv_id):
        return {"error": "username & invoiceId required"}

    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        _require_key(users, username, x_api_key)
        u = next((x for x in users if _uname(x) == username), None)
        if not u:
            return {"error": "user not found"}
        _ensure_business(u)

        invoice = _find_in(u["invoices"], "id", inv_id)
        if not invoice:
            return {"error": "invoice not found"}

        # mark paid
        invoice["status"]  = "paid"
        invoice["paid_ts"] = _now()

        # mark related payment paid
        for p in u.get("payments", []):
            if p.get("invoiceId") == inv_id:
                p["status"]  = "paid"
                p["paid_ts"] = _now()

        amt      = float(invoice.get("amount", 0))
        currency = invoice.get("currency", "USD")

        # platform fee (single source of truth)
        fee_rate = _platform_fee_rate(u)             # e.g. 0.05
        fee_amt  = round(amt * fee_rate, 2)          # positive
        net_amt  = round(amt - fee_amt, 2)

        # ledger entries: revenue (+), platform fee (-)
        u["ownership"]["ledger"].append({
            "ts": _now(), "amount": amt, "currency": currency, "basis": "revenue", "ref": inv_id
        })
        u["ownership"]["ledger"].append({
            "ts": _now(), "amount": -fee_amt, "currency": currency, "basis": "platform_fee", "ref": inv_id
        })

        # reflect in balances
        u["yield"]["aigxEarned"] = float(u["yield"].get("aigxEarned", 0)) + net_amt
        u["ownership"]["aigx"]   = float(u["ownership"].get("aigx", 0)) + net_amt

        await _save_users(client, users)
        return {"ok": True, "invoice": invoice, "fee": {"rate": fee_rate, "amount": fee_amt}, "net": net_amt}

@app.post("/budget/spend")
async def budget_spend(body: Dict = Body(...)):
    username = body.get("username"); amount = float(body.get("amount", 0))
    basis = body.get("basis", "media_spend"); ref = body.get("ref")
    if not (username and amount): return {"error": "username & amount required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        if not _can_spend(u, amount): 
            return {"error": "daily budget exceeded"}
        _spend(u, amount, basis, ref)
        await _save_users(client, users)
        return {"ok": True, "spent_today": _current_spend(u)[0][_today_key()], "summary": _money_summary(u)}

@app.post("/events/log")
async def events_log(body: Dict = Body(...)):
    username = body.get("username"); ev = body.get("event")
    if not (username and isinstance(ev, dict)): return {"error":"username & event required"}
    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        ev.setdefault("ts", _now())
        u.setdefault("events", []).append(ev)  # {playbook, channel, kind, cost?, revenue?}
        await _save_users(client, users)
        return {"ok": True}

@app.post("/attribution/rollup")
async def attribution_rollup(body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        data = {}
        for ev in u.get("events", []):
            key = (ev.get("playbook") or "unknown", ev.get("channel") or "unknown")
            data.setdefault(key, {"spend":0.0,"rev":0.0,"count":0})
            data[key]["spend"] += float(ev.get("cost",0))
            data[key]["rev"]   += float(ev.get("revenue",0))
            data[key]["count"] += 1
        table = [{"playbook":k[0], "channel":k[1], "spend":round(v["spend"],2),
                  "revenue":round(v["rev"],2), "roas": round((v["rev"]/v["spend"]) if v["spend"] else 0, 2),
                  "events": v["count"]} for k,v in data.items()]
        table.sort(key=lambda r: r["roas"], reverse=True)
        return {"ok": True, "by_channel": table[:20]}

@app.post("/automatch/pulse")
async def automatch_pulse(body: Dict = Body(...)):
    username = body.get("username"); unit_spend = float(body.get("unitSpend", 1.0))
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=25) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        enabled = ((u.get("playbooks", {}) or {}).get("enabled", []))  # catalog code(s)
        actions = []
        for code in enabled:
            if not _can_spend(u, unit_spend): break
            # “fire” a tiny action – e.g., a post, an email, a DM; here we just log outreach
            u.setdefault("transactions", {}).setdefault("outreachEvents", []).append(
                {"code": code, "delivered": True, "ts": _now()}
            )
            _spend(u, unit_spend, basis="media_spend", ref=code)
            actions.append({"code": code, "spent": unit_spend})
        await _save_users(client, users)
        return {"ok": True, "fired": actions, "spent_today": _current_spend(u)[0][_today_key()]}

# ===== Monetize toggle (AL1 by default with budget/quietHours guardrails) =====
@app.post("/monetize/toggle")
async def monetize_toggle(body: Dict = Body(...)):
    """
    Body: { username, enabled: bool, dailyBudget?: number, quietHours?: [22,8] }
    Sets runtimeFlags.monetizeEnabled and basic guardrails.
    """
    username = body.get("username"); enabled = bool(body.get("enabled", False))
    budget = float(body.get("dailyBudget", 10))  # default $10/day
    quiet = body.get("quietHours", [22, 8])

    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("runtimeFlags", {})["monetizeEnabled"] = enabled
        u.setdefault("policy", {}).setdefault("guardrails", {})
        u["policy"]["guardrails"]["dailyBudget"] = budget
        u["policy"]["guardrails"]["quietHours"] = quiet
        users = users  # no-op, clarity
        await _save_users(client, users)
        return {"ok": True, "monetizeEnabled": enabled, "policy": u.get("policy", {})}

# ===== Playbook catalog (static examples) =====
_PLAYBOOK_CATALOG = [
    {
        "code": "tiktok_affiliate",
        "title": "TikTok → Affiliate Links",
        "requires": ["content_out"],
        "default_budget": 0,
        "steps": ["connect_tiktok","fetch_trending","render_script","post_with_disclosure","track_clicks"]
    },
    {
        "code": "email_audit_to_checkout",
        "title": "Email Audit → Stripe Checkout",
        "requires": ["email_out","calendar","commerce_in"],
        "default_budget": 10,
        "steps": ["send_audit_offer","book_meeting","issue_checkout"]
    },
    {
        "code": "shorts_calendar_checkout",
        "title": "Shorts → Calendar → Checkout",
        "requires": ["content_out","calendar","commerce_in"],
        "default_budget": 5,
        "steps": ["generate_short","post_short","send_booking","send_payment_link"]
    },
]

@app.get("/playbooks/catalog")
async def playbooks_catalog():
    return {"ok": True, "catalog": _PLAYBOOK_CATALOG}

# ===== User playbooks enable/config =====
@app.post("/playbooks/enable")
async def playbooks_enable(body: Dict = Body(...)):
    """
    Body: { username, codes: ["tiktok_affiliate", ...], enabled: true|false }
    """
    username = body.get("username"); codes = body.get("codes", []); enabled = bool(body.get("enabled", True))
    if not (username and codes): return {"error":"username & codes required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        cfg = u.setdefault("playbooks", {"enabled": [], "configs": {}})
        if enabled:
            for c in codes:
                if c not in cfg["enabled"]: cfg["enabled"].append(c)
        else:
            cfg["enabled"] = [c for c in cfg["enabled"] if c not in codes]
        await _save_users(client, users)
        return {"ok": True, "playbooks": cfg}

@app.post("/playbooks/config")
async def playbooks_config(body: Dict = Body(...)):
    """
    Body: { username, code, config: { budget?:number, notes?:str } }
    """
    username = body.get("username"); code = body.get("code"); config = body.get("config", {})
    if not (username and code): return {"error":"username & code required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        pb = u.setdefault("playbooks", {"enabled": [], "configs": {}})
        pb["configs"][code] = {**pb["configs"].get(code, {}), **config, "updated": _now()}
        await _save_users(client, users)
        return {"ok": True, "playbooks": pb}

# ---------- 2) FULFILLMENT ----------
@app.post("/orders/{orderId}/tasks/add")
async def order_task_add(orderId: str = Path(...), body: Dict = Body(...)):
    username = body.get("username"); title = body.get("title")
    if not (username and title): return {"error":"username & title required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        order = _find_in(u["orders"], "id", orderId)
        if not order: return {"error":"order not found"}
        t = {"id": _id("t"), "title": title, "assignee": body.get("assignee"), "due": body.get("due"),
             "status":"todo", "ts": _now()}
        order.setdefault("tasks", []).append(t)
        await _save_users(client, users)
        return {"ok": True, "task": t}

@app.post("/orders/{orderId}/tasks/done")
async def order_task_done(orderId: str = Path(...), body: Dict = Body(...)):
    username = body.get("username"); tid = body.get("taskId")
    if not (username and tid): return {"error":"username & taskId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        order = _find_in(u["orders"], "id", orderId)
        if not order: return {"error":"order not found"}
        for t in order.get("tasks", []):
            if t.get("id") == tid:
                t["status"] = "done"; t["done_ts"] = _now()
        await _save_users(client, users)
        return {"ok": True, "order": order}

@app.post("/orders/{orderId}/status")
async def order_status(orderId: str = Path(...), body: Dict = Body(...)):
    username = body.get("username"); status = body.get("status")
    if not (username and status): return {"error":"username & status required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        order = _find_in(u["orders"], "id", orderId)
        if not order: return {"error":"order not found"}
        order["status"] = status; order["status_ts"] = _now()
        if status == "blocked":
            order.setdefault("sla", {}).setdefault("breaches", 0)
            order["sla"]["breaches"] += 1
        await _save_users(client, users)
        return {"ok": True, "order": order}

# ---------- 3) PROPOSAL FOLLOW-UPS ----------
def _schedule_followups(base_ts: datetime) -> List[Dict[str, Any]]:
    return [
        {"id": _id("fu"), "when": (base_ts+timedelta(days=1)).isoformat(), "status":"scheduled"},
        {"id": _id("fu"), "when": (base_ts+timedelta(days=3)).isoformat(), "status":"scheduled"},
        {"id": _id("fu"), "when": (base_ts+timedelta(days=7)).isoformat(), "status":"scheduled"},
    ]

@app.post("/proposal/{proposalId}/followup/schedule")
async def proposal_followup_schedule(proposalId: str = Path(...), body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        p = _find_in(u["proposals"], "id", proposalId)
        if not p: return {"error":"proposal not found"}
        p.setdefault("followups", []).extend(_schedule_followups(datetime.utcnow()))
        await _save_users(client, users)
        return {"ok": True, "followups": p["followups"]}

@app.post("/proposal/{proposalId}/followup/send")
async def proposal_followup_send(proposalId: str = Path(...), body: Dict = Body(...)):
    username = body.get("username"); fid = body.get("followupId")
    if not (username and fid): return {"error":"username & followupId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        p = _find_in(u["proposals"], "id", proposalId)
        if not p: return {"error":"proposal not found"}
        for fu in p.get("followups", []):
            if fu["id"] == fid:
                fu["status"] = "sent"; fu["sent_ts"] = _now()
        await _save_users(client, users)
        return {"ok": True}

# ---------- 4) SCHEDULING + NOTES ----------
@app.post("/schedule/create")
async def schedule_create(body: Dict = Body(...)):
    username = body.get("username"); pid = body.get("proposalId")
    if not username: return {"error":"username required"}
    booking_id = _id("meet")
    url = f"https://meet.aigentsy/book/{booking_id}"
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("meetings", [])
        meeting = {"id": booking_id, "proposalId": pid, "booking_url": url, "status":"pending", "ts": _now()}
        u["meetings"].append(meeting)
        await _save_users(client, users)
        return {"ok": True, "booking_url": url, "meeting": meeting}

@app.post("/meeting/notes")
async def meeting_notes(body: Dict = Body(...)):
    username = body.get("username"); pid = body.get("proposalId"); notes = body.get("notes","")
    if not (username and pid): return {"error":"username & proposalId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("meetings", [])
        mt = {"id": _id("note"), "proposalId": pid, "notes": notes[:5000], "ts": _now()}
        u["meetings"].append(mt)
        await _save_users(client, users)
        return {"ok": True, "note": mt}

# ---------- 5) CRM-LITE ----------
@app.post("/contacts/import")
async def contacts_import(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    username = body.get("username")
    if not username: return {"error":"username required"}
    new_contacts: List[Dict[str, Any]] = []
    if body.get("contacts"):
        for c in body["contacts"]:
            c["id"] = _id("c"); c.setdefault("tags",[]); c.setdefault("opt_in", False)
            new_contacts.append(c)
    elif body.get("csv"):
        reader = csv.DictReader(io.StringIO(body["csv"]))
        for row in reader:
            new_contacts.append({"id": _id("c"), "name": row.get("name"), "email": row.get("email"),
                                 "tags": [], "opt_in": False})
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        _require_key(users, username, x_api_key)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("crm", []).extend(new_contacts)
        await _save_users(client, users)
        return {"ok": True, "added": len(new_contacts)}

@app.post("/contacts/segment")
async def contacts_segment(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    username = body.get("username"); ids = body.get("ids", []); tags = body.get("tags", [])
    if not (username and ids and tags): return {"error":"username, ids, tags required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        _require_key(users, username, x_api_key)
        if not u: return {"error":"user not found"}
        for c in u.get("crm", []):
            if c["id"] in ids:
                c.setdefault("tags", [])
                for t in tags:
                    if t not in c["tags"]: c["tags"].append(t)
        await _save_users(client, users)
        return {"ok": True}

@app.post("/contacts/optout")
async def contacts_optout(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    username = body.get("username"); email = (body.get("email") or "").lower()
    if not (username and email): return {"error":"username & email required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        _require_key(users, username, x_api_key)
        if not u: return {"error":"user not found"}
        for c in u.get("crm", []):
            if (c.get("email") or "").lower() == email:
                c["opt_in"] = False; c.setdefault("tags", []).append("opt_out")
        await _save_users(client, users)
        return {"ok": True}

# ---------- 6) VALUE ROUTER / PRICING (A/B) ----------
@app.post("/pricing/decide")
async def pricing_decide(body: Dict = Body(...)):
    offer = (body.get("offer") or "").lower()
    base = 149 if "branding" in offer else 199 if "sdk" in offer else 99
    win = 0.62 if base == 149 else 0.48 if base == 199 else 0.55
    ev = round(base * win, 2)
    return {"price": base, "win_prob": win, "ev": ev}

@app.post("/pricing/ab/assign")
async def pricing_ab_assign(body: Dict = Body(...)):
    import random
    username = body.get("username"); offer = body.get("offer")
    if not (username and offer): return {"error":"username & offer required"}
    variant = "A" if random.random() < 0.5 else "B"
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u["experiments"].append({"id": _id("ab"), "offer": offer, "variant": variant, "ts": _now()})
        await _save_users(client, users)
        return {"ok": True, "variant": variant}

@app.post("/pricing/ab/result")
async def pricing_ab_result(body: Dict = Body(...)):
    username = body.get("username"); eid = body.get("experimentId"); result = body.get("result")
    if not (username and eid and result): return {"error":"username, experimentId, result required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for e in u.get("experiments", []):
            if e["id"] == eid: e["result"] = result; e["result_ts"] = _now()
        await _save_users(client, users)
        return {"ok": True}

# ---------- 7) CONSENT VAULT + DOCS ----------
@app.post("/doc/generate")
async def doc_generate(body: Dict = Body(...)):
    username = body.get("username"); dtype = body.get("type")
    if not (username and dtype): return {"error":"username & type required"}
    content = f"{dtype} TEMPLATE v1 :: generated {datetime.utcnow().isoformat()}"
    doc_id = _id("doc"); hashv = hashlib.sha256(content.encode()).hexdigest()
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        doc = {"id": doc_id, "type": dtype, "ref": body.get("ref"), "hash": hashv, "ts": _now()}
        u["docs"].append(doc)
        await _save_users(client, users)
        return {"ok": True, "doc": doc, "content": content}

@app.post("/doc/attach")
async def doc_attach(body: Dict = Body(...)):
    username = body.get("username"); docId = body.get("docId")
    if not (username and docId): return {"error":"username & docId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        target = {"proposalId": body.get("proposalId"), "orderId": body.get("orderId")}
        for d in u["docs"]:
            if d["id"] == docId: d["attached_to"] = target; d["attached_ts"] = _now()
        await _save_users(client, users)
        return {"ok": True}

# ---------- 8) KPI AUTOPILOT ----------
@app.post("/kpi/rollup")
async def kpi_rollup(body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        cash = float(u["ownership"].get("aigx", 0))
        burn = 100.0
        runway = int(cash / burn) if burn else 0
        pipeline = sum(float(q.get("price",0)) for q in u["quotes"] if q.get("status")=="offered")
        won = sum(1 for e in u.get("experiments",[]) if e.get("result")=="won")
        total = sum(1 for e in u.get("experiments",[]) if e.get("result"))
        close = (won/total) if total else 0.0
        snap = {"ts": _now(), "runway_days": runway, "mrr": 0, "pipeline_value": pipeline, "close_rate": round(close,2)}
        u["kpi_snapshots"].append(snap)
        await _save_users(client, users)
        return {"ok": True, "snapshot": snap}

@app.post("/kpi/forecast")
async def kpi_forecast(body: Dict = Body(...)):
    username = body.get("username"); horizon = int(body.get("horizon",30))
    if not username: return {"error":"username required"}
    growth = 1.15 if horizon==30 else 1.32 if horizon==60 else 1.5
    return {"ok": True, "horizon": horizon, "projected_pipeline": growth}

# ---------- 9) SUPPORT • NPS • TESTIMONIALS ----------
@app.post("/support/create")
async def support_create(body: Dict = Body(...)):
    username = body.get("username"); subject = body.get("subject"); description = body.get("description","")
    if not (username and subject): return {"error":"username & subject required"}
    tid = _id("ticket")
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        t = {"id": tid, "subject": subject, "description": description, "status":"open", "ts": _now()}
        u["tickets"].append(t); await _save_users(client, users)
        return {"ok": True, "ticket": t}

@app.post("/support/status")
async def support_status(body: Dict = Body(...)):
    username = body.get("username"); tid = body.get("ticketId"); status = body.get("status")
    if not (username and tid and status): return {"error":"username, ticketId, status required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for t in u.get("tickets", []):
            if t["id"] == tid: t["status"] = status; t["status_ts"] = _now()
        await _save_users(client, users)
        return {"ok": True}

@app.post("/nps/ping")
async def nps_ping(body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    nid = _id("nps")
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        u.setdefault("nps", []).append({"id": nid, "orderId": body.get("orderId"), "status":"sent", "ts": _now()})
        await _save_users(client, users)
        return {"ok": True, "nps": nid}

@app.post("/nps/submit")
async def nps_submit(body: Dict = Body(...)):
    username = body.get("username"); nid = body.get("npsId"); score = int(body.get("score",0))
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for n in u.get("nps", []):
            if n["id"] == nid: n["status"]="answered"; n["score"]=score; n["comment"]=body.get("comment"); n["answered_ts"]=_now()
        await _save_users(client, users)
        return {"ok": True}

@app.post("/testimonial/add")
async def testimonial_add(body: Dict = Body(...)):
    username = body.get("username"); text = body.get("text")
    if not (username and text): return {"error":"username & text required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        u.setdefault("testimonials", []).append({"id": _id("tm"), "text": text[:1000], "ref": body.get("ref"), "ts": _now()})
        await _save_users(client, users)
        return {"ok": True}

# ---------- 10) IDENTITY & COLLECTIBLES ----------
@app.post("/collectible/award")
async def collectible_award(body: Dict = Body(...)):
    username = body.get("username"); ctype = body.get("type")
    if not (username and ctype): return {"error":"username & type required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        u.setdefault("collectibles", []).append({"id": _id("cb"), "type": ctype, "ref": body.get("ref"), "ts": _now()})
        await _save_users(client, users)
        return {"ok": True}

# ---------- 11) MARKETPLACE LISTINGS ----------
@app.post("/listing/publish")
async def listing_publish(body: Dict = Body(...)):
    username = body.get("username"); title = body.get("title"); price = float(body.get("price",0))
    channel = body.get("channel","internal")
    if not (username and title): return {"error":"username & title required"}
    lid = _id("lst")
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        l = {"id": lid, "title": title, "price": price, "channel": channel, "status":"published", "ts": _now(),
             "impressions":0, "clicks":0}
        u["listings"].append(l); await _save_users(client, users)
        return {"ok": True, "listing": l}

@app.post("/listing/status")
async def listing_status(body: Dict = Body(...)):
    username = body.get("username"); lid = body.get("listingId"); status = body.get("status")
    if not (username and lid and status): return {"error":"username, listingId, status required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for l in u.get("listings", []):
            if l["id"] == lid: l["status"]=status; l["status_ts"]=_now()
        await _save_users(client, users)
        return {"ok": True}

# ---------- 12) SECURITY / RBAC / AUDIT ----------
@app.post("/apikey/issue")
async def apikey_issue(body: Dict = Body(...)):
    username = body.get("username"); label = body.get("label","default")
    if not username: return {"error":"username required"}
    key = uuid.uuid4().hex + uuid.uuid4().hex
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("api_keys", []).append({"id": _id("key"), "label": label, "key": key, "ts": _now(), "revoked": False})
        await _save_users(client, users)
        return {"ok": True, "key": key}

@app.post("/apikey/revoke")
async def apikey_revoke(body: Dict = Body(...)):
    username = body.get("username"); key = body.get("key")
    if not (username and key): return {"error":"username & key required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for k in u.get("api_keys", []):
            if k["key"] == key: k["revoked"] = True; k["revoked_ts"]=_now()
        await _save_users(client, users)
        return {"ok": True}

@app.post("/roles/grant")
async def roles_grant(body: Dict = Body(...)):
    username = body.get("username"); role = body.get("role"); grantee = body.get("grantee")
    if not (username and role and grantee): return {"error":"username, role, grantee required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("roles", []).append({"role": role, "grantee": grantee, "ts": _now()})
        await _save_users(client, users)
        return {"ok": True}

@app.post("/roles/revoke")
async def roles_revoke(body: Dict = Body(...)):
    username = body.get("username"); role = body.get("role"); grantee = body.get("grantee")
    if not (username and role and grantee): return {"error":"username, role, grantee required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        u["roles"] = [r for r in u.get("roles", []) if not (r["role"]==role and r["grantee"]==grantee)]
        await _save_users(client, users)
        return {"ok": True}

@app.post("/audit/log")
async def audit_log(body: Dict = Body(...)):
    username = body.get("username"); action = body.get("action")
    if not (username and action): return {"error":"username & action required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("audit", []).append({"id": _id("audit"), "action": action, "ref": body.get("ref"), "meta": body.get("meta"), "ts": _now()})
        await _save_users(client, users)
        return {"ok": True}

# ================================
# >>> Two essential patches <<<
# ================================

# ---- PATCH: /submit_proposal (adds id, status, followups) ----
@app.post("/submit_proposal")
async def submit_proposal(request: Request):
    body = await request.json()
    sender = body.get("sender")
    if not sender:
        return {"error": "missing sender"}
    # ensure minimal shape
    pid = body.get("id") or f"prop_{uuid.uuid4().hex[:10]}"
    body["id"] = pid
    body.setdefault("timestamp", _now())
    body.setdefault("status", "sent")
    body.setdefault("followups", [])
    body.setdefault("meta", {})
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            users = await _load_users(client)
            u = next((x for x in users if _uname(x)==sender), None)
            if not u:
                return {"error": f"user {sender} not found"}
            _ensure_business(u)
            u["proposals"].append(body)
            await _save_users(client, users)
            return {"ok": True, "proposal": body}
    except Exception as e:
        return {"error": f"submit_proposal_failed: {e}"}

# ---- PATCH: /earn/task/complete (direct ledger; no localhost hop) ----
@app.post("/earn/task/complete")
async def earn_task_complete(request: Request):
    body = await request.json()
    username = body.get("username")
    task = body.get("taskId")
    if not (username and task):
        return {"error":"username & taskId required"}
    payout = 1.0
    if task == "promo-15s": payout = 2.0
    elif task == "scan-receipt": payout = 1.5
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            users = await _load_users(client)
            u = next((x for x in users if _uname(x)==username), None)
            if not u: return {"error":"user not found"}
            _ensure_business(u)
            entry = {"ts": _now(), "amount": payout, "currency": "AIGx", "basis": "task", "ref": task}
            u["ownership"]["ledger"].append(entry)
            u["ownership"]["aigx"] = float(u["ownership"].get("aigx",0)) + payout
            u["yield"]["aigxEarned"] = float(u["yield"].get("aigxEarned",0)) + payout
            await _save_users(client, users)
            return {"ok": True, "ledgerEntry": entry}
    except Exception as e:
        return {"error": f"earn_complete_error: {e}"}

# --- Admin normalize route ---
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

class AdminIn(BaseModel):
    token: str

@app.post("/admin/normalize")
async def admin_normalize(a: AdminIn):
    if not ADMIN_TOKEN or a.token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="forbidden")
    data = await run_in_threadpool(_bin_get)
    records = data["record"] if isinstance(data, dict) and "record" in data else data
    if not isinstance(records, list):
        raise HTTPException(status_code=500, detail="bin payload not a list")
    upgraded = [normalize_user_data(r) for r in records]
    await run_in_threadpool(_bin_put, upgraded)
    return {"ok": True, "count": len(upgraded)}

from urllib.parse import urlparse
import ipaddress, socket

ALLOWED_DIST_DOMAINS = [d.strip() for d in os.getenv("ALLOWED_DIST_DOMAINS", "hooks.slack.com,discord.com,api.telegram.org").split(",") if d.strip()]

def _safe_url(u: str) -> bool:
    try:
        p = urlparse(u)
        if p.scheme not in ("https", "http"):
            return False
        host = p.hostname or ""
        if not any(host.endswith(d) for d in ALLOWED_DIST_DOMAINS):
            return False
        try:
            infos = socket.getaddrinfo(host, None)
        except Exception:
            return False
        ips = {ai[4][0] for ai in infos if ai and ai[4]}
        for ip in ips:
            try:
                ipaddr = ipaddress.ip_address(ip)
            except Exception:
                return False
            if ipaddr.is_private or ipaddr.is_loopback or ipaddr.is_link_local:
                return False
        return True
    except Exception:
        return False


from fastapi import HTTPException



EVENT_BUS = asyncio.Queue()

async def publish(evt: dict):
    try:
        await EVENT_BUS.put(json.dumps(evt))
    except Exception:
        pass

@app.get("/stream/activity")
async def stream_activity():
    async def gen():
        while True:
            msg = await EVENT_BUS.get()
            yield f"data: {msg}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")

def _find_proposal(u, proposal_id):
    for p in u.get("proposals", []):
        if p.get("id")==proposal_id:
            return p
    return None

ProposalOutcome = Literal["won","lost","ignored","replied"]

@app.post("/proposal/feedback")
async def proposal_feedback(username: str, proposal_id: str, outcome: ProposalOutcome, weight: float = 1.0, x_api_key: str = Header("")):
    users, client = await _get_users_client()
    _require_key(users, username, x_api_key)
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    u.setdefault("runtimeWeights", {"keywords": {}, "platforms": {}})
    p = _find_proposal(u, proposal_id)
    if not p: return {"error":"proposal not found"}
    meta = p.get("meta", {})
    kws = meta.get("keywords", []) or []
    plat = meta.get("platform", "internal")
    for k in kws:
        u["runtimeWeights"]["keywords"][k] = u["runtimeWeights"]["keywords"].get(k, 0.0) + (1.0 if outcome=="won" else (-0.5 if outcome=="ignored" else (0.2 if outcome=="replied" else -1.0)))*weight
    u["runtimeWeights"]["platforms"][plat] = u["runtimeWeights"]["platforms"].get(plat, 0.0) + (1.0 if outcome=="won" else -0.2)
    await _save_users(client, users)
    return {"ok": True, "weights": u["runtimeWeights"]}


AGENT_WEBHOOKS = {
    "cfo":   os.getenv("VENTURE_AGENT_URL"),
    "cmo":   os.getenv("GROWTH_AGENT_URL"),
    "clo":   os.getenv("REMIX_AGENT_URL"),
    "cto":   os.getenv("SDK_AGENT_URL"),
}

async def _broadcast_yield(u, event):
    try:
        import httpx
    except Exception:
        return
    payload = {"username": (u.get("username") or u.get("consent",{}).get("username")), "event": event, "ts": _now()}
    async with httpx.AsyncClient(timeout=8.0) as h:
        for name, url in AGENT_WEBHOOKS.items():
            if not url: continue
            try:
                await h.post(f"{url.rstrip('/')}/autopropagate", json=payload)
            except Exception:
                pass

def _verify_signature(body: bytes, ts: str, sign: str):
    secret = os.getenv("HMAC_SECRET","")
    if not secret:
        return True
    mac = hmac.new(secret.encode(), (ts+"."+body.decode()).encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, sign)

@app.middleware("http")
async def hmac_guard(request, call_next):
    protected = ("/submit_proposal","/aigx/credit","/unlock")
    if any(request.url.path.startswith(p) for p in protected):
        ts = request.headers.get("X-Ts"); sign = request.headers.get("X-Sign")
        body = await request.body()
        if not _verify_signature(body, ts or "", sign or ""):
            from fastapi.responses import JSONResponse
            return JSONResponse({"error":"bad signature"}, status_code=401)
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = receive
    return await call_next(request)


# ========= AiGentsy Consumer-First Upgrades (Storefront, Widget, PoO-Lite, Intent Auction, Productizer, Quotes, Escrow, etc.) =========

def _uid():
    return str(uuid.uuid4())

def _username_of(u):
    return u.get("username") or u.get("consent",{}).get("username")

def _global_find_intent(users, intent_id):
    for u in users:
        for it in u.get("intents", []):
            if it.get("id")==intent_id:
                return u, it
    return None, None

@app.get("/storefront/config")
async def storefront_get_config(username: str):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    cfg = u.setdefault("storefront", {"theme":"light","palette":"default","hero_video":None,"offers":[], "kits":[], "badges":[], "social":{}})
    return {"ok": True, "config": cfg}

@app.post("/storefront/config")
async def storefront_set_config(username: str, config: dict):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    u["storefront"] = {**u.get("storefront", {}), **(config or {})}
    await _save_users(client, users)
    return {"ok": True, "config": u["storefront"]}

@app.post("/storefront/publish")
async def storefront_publish(username: str, base_url: Optional[str] = None):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    u.setdefault("storefront", {}).update({"published": _now()})
    slug = _username_of(u)
    url = f"{(base_url or os.getenv('PUBLIC_BASE','https://aigentsy.com')).rstrip('/')}/u/{slug}"
    u["storefront"]["url"] = url
    await _save_users(client, users)
    return {"ok": True, "url": url}

@app.post("/analytics/track")
async def analytics_track(username: str, event: dict):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    q = u.setdefault("analytics", [])
    event = {"id": _uid(), "ts": _now(), **(event or {})}
    q.append(event)
    await _save_users(client, users)
    try:
        await publish({"type":"analytics","user":username,"event":event})
    except Exception:
        pass
    return {"ok": True}

@app.post("/poo/issue")
async def poo_issue(username: str, title: str, metrics: dict = None, evidence_urls: List[str] = None):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    entry = {"id": _uid(), "ts": _now(), "title": title, "metrics": metrics or {}, "evidence_urls": evidence_urls or []}
    u.setdefault("outcomes", []).append(entry)
    score = int(u.get("outcomeScore", 0)) + 3
    u["outcomeScore"] = max(0, min(100, score))
    await _save_users(client, users)
    try:
        await publish({"type":"poo","user":username,"title":title})
    except Exception:
        pass
    return {"ok": True, "outcome": entry, "score": u["outcomeScore"]}

@app.get("/score/outcome")
async def get_outcome_score(username: str):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    return {"ok": True, "score": int(u.get("outcomeScore", 0))}

#@app.post("/intent/create")
async def intent_create(buyer: str, brief: str, budget: float):
    users, client = await _get_users_client()
    u = _find_user(users, buyer)
    if not u: return {"error":"buyer not found"}
    intent = {"id": _uid(), "ts": _now(), "brief": brief, "budget": float(budget), "status":"open", "bids":[]}
    u.setdefault("intents", []).append(intent)
    await _save_users(client, users)
    try:
        await publish({"type":"intent","buyer":buyer,"id":intent["id"],"brief":brief})
    except Exception:
        pass
    return {"ok": True, "intent": intent}

#@app.post("/intent/bid")
async def intent_bid(agent: str, intent_id: str, price: float, ttr: str = "48h"):
    users, client = await _get_users_client()
    buyer_user, intent = _global_find_intent(users, intent_id)
    if not intent: return {"error":"intent not found"}
    if intent.get("status") != "open": return {"error":"intent closed"}
    bid = {"id": _uid(), "agent": agent, "price": float(price), "ttr": ttr, "ts": _now()}
    intent.setdefault("bids", []).append(bid)
    await _save_users(client, users)
    try:
        await publish({"type":"intent_bid","intent_id":intent_id,"agent":agent,"price":price})
    except Exception:
        pass
    return {"ok": True, "bid": bid}

#@app.post("/intent/award")
async def intent_award(intent_id: str, bid_id: str = None):
    users, client = await _get_users_client()
    buyer_user, intent = _global_find_intent(users, intent_id)
    if not intent: return {"error":"intent not found"}
    if intent.get("status") != "open": return {"error":"intent closed"}
    chosen = None
    if bid_id:
        chosen = next((b for b in intent.get("bids",[]) if b["id"]==bid_id), None)
    else:
        bids = intent.get("bids", [])
        if not bids: return {"error":"no bids"}
        bids_sorted = sorted(bids, key=lambda b: (b["price"], b["ttr"]))
        chosen = bids_sorted[0]
    intent["status"] = "awarded"
    intent["award"] = chosen
    await _save_users(client, users)
    try:
        await publish({"type":"intent_award","intent_id":intent_id,"agent":chosen['agent'],"buyer": _username_of(buyer_user)})
    except Exception:
        pass
    return {"ok": True, "award": chosen}

@app.post("/productize")
async def productize(username: str, url: Optional[str] = None, file_meta: dict = None):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    offer = {"id": _uid(), "title": "Auto Productized Offer", "source": url or file_meta or {}, "price": 199, "created": _now()}
    u.setdefault("offers", []).append(offer)
    await _save_users(client, users)
    return {"ok": True, "offer": offer}

@app.post("/quote")
async def quote(buyer: str, seller: str, scope: str, ttr: str = "48h"):
    users, client = await _get_users_client()
    sb = _find_user(users, seller); bb = _find_user(users, buyer)
    if not (sb and bb): return {"error":"buyer or seller not found"}
    base = 199.0
    price = base * (1.5 if (ttr or '').lower().startswith("24") else 1.0)
    q = {"id": _uid(), "ts": _now(), "buyer": buyer, "seller": seller, "scope": scope, "ttr": ttr, "price": price, "status":"open"}
    sb.setdefault("quotes", []).append(q)
    bb.setdefault("quotes", []).append(q)
    await _save_users(client, users)
    return {"ok": True, "quote": q}

@app.post("/escrow/create")
async def escrow_create(quote_id: str, buyer: str):
    users, client = await _get_users_client()
    b = _find_user(users, buyer)
    if not b: return {"error":"buyer not found"}
    e = {"id": _uid(), "quote_id": quote_id, "status":"held", "ts": _now()}
    b.setdefault("escrow", []).append(e)
    await _save_users(client, users)
    return {"ok": True, "escrow": e}

@app.post("/escrow/release")
async def escrow_release(escrow_id: str):
    users, client = await _get_users_client()
    for u in users:
        for e in u.get("escrow", []):
            if e["id"]==escrow_id:
                e["status"] = "released"; await _save_users(client, users); return {"ok": True}
    return {"error":"escrow not found"}

@app.post("/escrow/dispute")
async def escrow_dispute(escrow_id: str, reason: str):
    users, client = await _get_users_client()
    for u in users:
        for e in u.get("escrow", []):
            if e["id"]==escrow_id:
                e["status"] = "disputed"; e["reason"]=reason; await _save_users(client, users); return {"ok": True}
    return {"error":"escrow not found"}

@app.post("/offer/localize")
async def offer_localize(username: str, offer_id: str, locales: List[str]):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    variants = []
    for loc in locales or []:
        variants.append({"id": _uid(), "base": offer_id, "locale": loc, "ts": _now()})
    u.setdefault("offer_variants", []).extend(variants)
    await _save_users(client, users)
    return {"ok": True, "variants": variants}

@app.get("/fx")
async def fx():
    return {"USD":1.0,"EUR":0.93,"GBP":0.81,"JPY":149.0}

@app.post("/media/bind_offer")
async def media_bind_offer(username: str, media_id: str, offer_id: str):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    m = {"media_id": media_id, "offer_id": offer_id, "ts": _now()}
    u.setdefault("media_bindings", []).append(m)
    await _save_users(client, users)
    return {"ok": True, "binding": m}

@app.post("/team/create")
async def team_create(lead_owner: str, members: List[str], split: List[float]):
    users, client = await _get_users_client()
    lead = _find_user(users, lead_owner)
    if not lead: return {"error":"lead not found"}
    team = {"id": _uid(), "members": members, "split": split, "ts": _now()}
    lead.setdefault("teams", []).append(team)
    await _save_users(client, users)
    return {"ok": True, "team": team}

@app.post("/team/offer")
async def team_offer(lead_owner: str, team_id: str, bundle_spec: dict):
    users, client = await _get_users_client()
    lead = _find_user(users, lead_owner)
    if not lead: return {"error":"lead not found"}
    t = next((x for x in lead.get("teams", []) if x["id"]==team_id), None)
    if not t: return {"error":"team not found"}
    off = {"id": _uid(), "team_id": team_id, "spec": bundle_spec, "ts": _now()}
    lead.setdefault("team_offers", []).append(off)
    await _save_users(client, users)
    return {"ok": True, "team_offer": off}

@app.post("/retarget/schedule")
async def retarget_schedule(username: str, lead_id: str, cadence: str = "3d", incentive: str = "AIGx10"):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    task = {"id": _uid(), "lead_id": lead_id, "cadence": cadence, "incentive": incentive, "ts": _now()}
    u.setdefault("retarget_tasks", []).append(task)
    await _save_users(client, users)
    return {"ok": True, "task": task}

@app.get("/market/rank")
async def market_rank(category: Optional[str] = None):
    users, client = await _get_users_client()
    ranked = []
    for u in users:
        score = int(u.get("outcomeScore", 0))
        completion = len(u.get("outcomes", []))
        response_bonus = 1 if len(u.get("analytics", []))>0 else 0
        price_bias = 0
        ranked.append({"username": _username_of(u), "rank": score + completion + response_bonus - price_bias})
    ranked.sort(key=lambda r: r["rank"], reverse=True)
    return {"ok": True, "results": ranked[:100]}

@app.get("/offer/upsells")
async def offer_upsells(offer_id: str):
    return {"ok": True, "upsells":[
        {"id":"rush","title":"Rush Delivery (24h)","price_delta":99},
        {"id":"brandpack","title":"Brand Pack Add-on","price_delta":149},
        {"id":"support30","title":"30 Days Support","price_delta":79}
    ]}

@app.post("/concierge/triage")
async def concierge_triage(text: str):
    scope = "General help with " + (text[:120] if text else "your project")
    suggested = [{"title":"Starter Offer","price":149},{"title":"Pro Offer","price":299}]
    return {"ok": True, "scope": scope, "suggested_offers": suggested, "price_bands":[149,299,499]}


# ===== AiGentsy AAM — helpers (idempotent) =====
import base64, hmac, hashlib, os, json as _json

def _now_utc():
    import datetime as _dt
    return _dt.datetime.utcnow().isoformat() + "Z"

def _uid_gen():
    import uuid as _uuid
    return str(_uuid.uuid4())

# Generic provider event recorder into your existing JSON store.
# Reuses your _get_users_client() and _save_users() helpers.
async def _record_provider_event(provider: str, topic: str, payload: dict):
    users, client = await _get_users_client()
    event = {
        "id": _uid(),
        "source": provider,
        "topic": topic,
        "payload": payload or {},
        "ts": _now()
    }
    # Append to a global bucket; adjust to per-user mapping if desired.
    # We try to place it on the first record to avoid schema surprises.
    if not users:
        return {"ok": False, "reason": "no_user_records"}
    users[0].setdefault("events", []).append(event)
    await _save_users(client, users)
    return {"ok": True, "event_id": event["id"]}

def _shopify_hmac_valid(secret: str, raw_body: bytes, received_hmac: str) -> bool:
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    calc = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(calc, (received_hmac or "").strip())


# ===== AiGentsy AAM — trigger endpoint =====
from fastapi import Request

# ===== AiGentsy AAM — provider webhooks =====
from fastapi import Request, HTTPException

# --- Safe fallbacks for optional AAM runtime modules ---
try:
    from aam_queue import AAMQueue  # provided by your AAM package
except Exception:  # ModuleNotFoundError or others
    class AAMQueue:  # minimal no-op queue to avoid import errors in deployments without AAM bundle
        def __init__(self, executor=None):
            self.executor = executor
        def submit(self, job):
            # immediate pass-through for demo
            if self.executor:
                try:
                    return self.executor(job)
                except Exception:
                    return {"ok": False, "error": "executor_failed"}
            return {"ok": True, "status": "queued", "job": job}

try:
    from sdk_aam_executor import execute  # orchestrates AAM actions
except Exception:
    def execute(job):
        # minimal fallback executor
        return {"ok": True, "executed": False, "reason": "sdk_aam_executor missing", "job": job}

try:
    from caio_orchestrator import run_play  # runs a named play through the AAM queue
except Exception:
    def run_play(queue, user_id, app_name, slug, context, autonomy):
        # minimal fallback orchestrator
        job = {
            "user_id": user_id,
            "app": app_name,
            "slug": slug,
            "context": context,
            "autonomy": autonomy
        }
        return {"ok": True, "ran": False, "reason": "caio_orchestrator missing", "result": queue.submit(job)}


# Single global queue instance
try:
    QUEUE  # type: ignore
except NameError:
    QUEUE = AAMQueue(executor=execute)

@app.post("/aam/run/{app_name}/{slug}")
async def run_aam(app_name: str, slug: str, req: Request):
    body = await req.json()
    user_id  = body.get("user_id") or "demo_user"
    context  = body.get("context") or {}
    autonomy = body.get("autonomy") or {"level":"suggest","policy":{"block":[]}}
    results = run_play(QUEUE, user_id, app_name, slug, context, autonomy)
    return {"ok": True, "results": results}


# ===== AiGentsy AAM — provider webhooks =====
from fastapi import Request, HTTPException

# Shopify (HMAC-verified)
@app.post("/webhook/shopify")
async def webhook_shopify(request: Request):
    secret = os.getenv("SHOPIFY_API_SECRET") or os.getenv("SHOPIFY_WEBHOOK_SECRET") or ""
    if not secret:
        raise HTTPException(status_code=500, detail="SHOPIFY_API_SECRET/SHOPIFY_WEBHOOK_SECRET not configured")
    topic = request.headers.get("X-Shopify-Topic", "") or "unknown"
    shop_domain = request.headers.get("X-Shopify-Shop-Domain", "")
    received_hmac = request.headers.get("X-Shopify-Hmac-Sha256", "")
    raw = await request.body()
    if not _shopify_hmac_valid(secret, raw, received_hmac):
        raise HTTPException(status_code=401, detail="Invalid HMAC")
    try:
        payload = _json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        payload = {}
    payload.setdefault("shop_domain", shop_domain)
    rec = await _record_provider_event("shopify", topic, payload)
    return {"ok": True, **(rec or {})}

# TikTok (signature optional / TODO)
@app.post("/webhook/tiktok")
async def webhook_tiktok(request: Request):
    raw = await request.body()
    try:
        payload = _json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        payload = {}
    topic = payload.get("event") or request.headers.get("X-Tt-Event", "unknown")
    rec = await _record_provider_event("tiktok", topic, payload)
    return {"ok": True, **(rec or {})}

# Amazon (shared-secret optional / TODO)
@app.post("/webhook/amazon")
async def webhook_amazon(request: Request):
    raw = await request.body()
    try:
        payload = _json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        payload = {}
    topic = payload.get("event") or request.headers.get("X-Amazon-Event", "unknown")
    rec = await _record_provider_event("amazon", topic, payload)
    return {"ok": True, **(rec or {})}


# === AIGENTSY EXPANSION ROUTES (non-destructive) ===
try:
    from fastapi import APIRouter, Request
except Exception:
    APIRouter = None
    Request = None

# Create a router to avoid touching your existing app routes.
_expansion_router = APIRouter() if 'APIRouter' in globals() and APIRouter else None

def _safe_json(obj):
    try:
        import json
        json.dumps(obj)
        return obj
    except Exception:
        return {"ok": False, "error": "unserializable_response"}

def _event_emit(kind: str, data: dict):
    try:
        from events import emit as _emit
        _emit(kind, data or {})
    except Exception:
        pass
    try:
        from log_to_jsonbin_aam_patched import log_event as _log
        _log({"kind": kind, **(data or {})})
    except Exception:
        pass

# ----- MetaBridge DealGraph -----
if _expansion_router:
    @_expansion_router.post("/metabridge/dealgraph/create")
    async def metabridge_dealgraph_create(payload: dict):
        try:
            from metabridge_dealgraph import create_dealgraph
            opportunity = payload.get("opportunity") or {}
            roles = payload.get("roles") or payload.get("roles_needed") or []
            rev_split = payload.get("rev_split") or []
            graph = create_dealgraph(opportunity, roles, rev_split)
            _event_emit("DEALGRAPH_CREATED", {"graph_id": graph.get("id"), **opportunity})
            return _safe_json({"ok": True, "graph": graph})
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @_expansion_router.post("/metabridge/dealgraph/activate")
    async def metabridge_dealgraph_activate(payload: dict):
        try:
            from metabridge_dealgraph import activate
            gid = payload.get("graph_id") or payload.get("id")
            res = activate(gid)
            _event_emit("DEALGRAPH_ACTIVATED", {"graph_id": gid})
            return _safe_json({"ok": True, "result": res})
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ----- Pricing A/B Arm -----
if _expansion_router:
    @_expansion_router.post("/pricing/arm")
    async def pricing_arm_endpoint(payload: dict):
        try:
            from pricing_arm import start_bundle_test, next_arm, record_outcome, best_arm
            op = (payload.get("op") or "").lower()
            username = payload.get("username") or payload.get("user") or "chatgpt"
            if payload.get("bundles") and not op:
                op = "start"
            if payload.get("bundle_id") and "revenue_usd" in payload and not op:
                op = "record"

            if op == "start":
                bundles = payload.get("bundles") or []
                epsilon = float(payload.get("epsilon", 0.15))
                exp = await start_bundle_test(username, bundles, epsilon)
                return _safe_json({"ok": True, "experiment": exp})
            elif op == "next":
                exp_id = payload.get("exp_id")
                arm = await next_arm(username, exp_id)
                return _safe_json({"ok": True, "choice": arm})
            elif op == "record":
                exp_id = payload.get("exp_id")
                bundle_id = payload.get("bundle_id")
                revenue = float(payload.get("revenue_usd", 0))
                out = await record_outcome(username, exp_id, bundle_id, revenue)
                _event_emit("PAID", {"user": username, "value_usd": revenue, "bundle_id": bundle_id})
                return _safe_json(out)
            elif op == "best":
                exp_id = payload.get("exp_id")
                out = await best_arm(username, exp_id)
                return _safe_json({"ok": True, "best": out})
            else:
                return {"ok": False, "error": "unknown_op", "hint": "use op=start|next|record|best"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ----- Intent Exchange -----
if _expansion_router:
    @_expansion_router.post("/intents/publish")
    async def intents_publish(payload: dict):
        try:
            from intent_exchange import publish
            res = publish(payload.get("intent") or payload)
            _event_emit("INTENT_PUBLISHED", {"id": res.get("id")})
            return _safe_json({"ok": True, "intent": res})
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @_expansion_router.post("/intents/claim")
    async def intents_claim(payload: dict):
        try:
            from intent_exchange import claim
            iid = payload.get("intent_id") or payload.get("id")
            agent = payload.get("agent") or payload.get("username")
            res = claim(iid, agent)
            _event_emit("INTENT_CLAIMED", {"id": iid, "agent": agent})
            return _safe_json({"ok": True, "intent": res})
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @_expansion_router.post("/intents/settle")
    async def intents_settle(payload: dict):
        try:
            from intent_exchange import settle
            iid = payload.get("intent_id") or payload.get("id")
            outcome = payload.get("outcome") or {}
            res = settle(iid, outcome)
            _event_emit("INTENT_SETTLED", {"id": iid})
            return _safe_json({"ok": True, "intent": res})
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ----- R³ allocation -----
if _expansion_router:
    @_expansion_router.post("/r3/allocate")
    async def r3_allocate(payload: dict):
        try:
            from r3_router import allocate
            user = payload.get("user") or {"id": payload.get("username") or "chatgpt", "channel_pacing": payload.get("channel_pacing") or []}
            budget = float(payload.get("budget_usd", 0))
            res = allocate(user, budget)
            for a in res.get("allocations", []):
                _event_emit("R3_ALLOCATED", {"user": res.get("user"), "usd": a.get("usd"), "channel": a.get("channel")})
            return _safe_json({"ok": True, **res})
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ----- Shopify inventory proxy -----
if _expansion_router:
    @_expansion_router.get("/inventory/get")
    async def inventory_get(product_id: str):
        try:
            from shopify_inventory_proxy import get_stock
            return _safe_json({"ok": True, **get_stock(product_id)})
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ----- Co-op sponsors -----
if _expansion_router:
    @_expansion_router.post("/coop/sponsor")
    async def coop_sponsor(payload: dict):
        try:
            from coop_sponsors import sponsor_add, state
            name = payload.get("name") or "anon"
            cap = float(payload.get("spend_cap_usd", 0))
            sponsor_add(name, cap)
            return _safe_json({"ok": True, "state": state()})
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ----- LTV predictor -----
if _expansion_router:
    @_expansion_router.post("/ltv/predict")
    async def ltv_predict(payload: dict):
        try:
            from ltv_forecaster import predict
            user = payload.get("user") or {}
            channel = payload.get("channel") or "tiktok"
            val = predict(user, channel)
            return _safe_json({"ok": True, "ltv": float(val)})
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ----- Proposal auto-close -----
if _expansion_router:
    @_expansion_router.post("/proposal/nudge")
    async def proposal_nudge(payload: dict):
        try:
            from proposal_autoclose import nudge
            pid = payload.get("proposal_id") or payload.get("id")
            res = nudge(pid)
            _event_emit("PROPOSAL_NUDGED", {"proposal_id": pid})
            return _safe_json(res)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @_expansion_router.post("/proposal/convert")
    async def proposal_convert(payload: dict):
        try:
            from proposal_autoclose import convert_to_quickpay
            pid = payload.get("proposal_id") or payload.get("id")
            res = convert_to_quickpay(pid)
            _event_emit("PROPOSAL_CONVERTED", {"proposal_id": pid})
            return _safe_json(res)
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ---- Mount the router if an app exists ----
try:
    app  # type: ignore  # check if app is already defined in your file
    if _expansion_router:
        app.include_router(_expansion_router)
except Exception:
    # No FastAPI app found or not constructed yet — safe to skip
    pass
# Mount Intent Exchange router
if intent_router:
    app.include_router(intent_router, prefix="/intents", tags=["Intent Exchange"])
# --- Alias route to match admin requirement (/events/stream) ---
@app.get("/events/stream")
async def events_stream():
    # Reuse the existing SSE generator
    return await stream_activity()

# === Expansion router (ensures required endpoints exist) ===
from fastapi import APIRouter, Request, HTTPException
_expansion_router = APIRouter()

@_expansion_router.post("/pricing/arm")
async def _exp_pricing_arm(payload: dict):
    try:
        from pricing_arm import start_bundle_test, next_arm, record_outcome, best_arm
        op = (payload.get("op") or "").lower()
        if payload.get("bundles") and not op: op = "start"
        if payload.get("bundle_id") and "revenue_usd" in payload and not op: op = "record"
        if op == "start":
            return {"ok": True, "experiment": await start_bundle_test(payload.get("username","sys"), payload.get("bundles"), float(payload.get("epsilon",0.15)))}
        if op == "next":
            return {"ok": True, "choice": await next_arm(payload.get("username","sys"), payload.get("exp_id"))}
        if op == "record":
            out = await record_outcome(payload.get("username","sys"), payload.get("exp_id"), payload.get("bundle_id"), float(payload.get("revenue_usd",0)))
            return {"ok": True, **out}
        if op == "best":
            return {"ok": True, "best": await best_arm(payload.get("username","sys"), payload.get("exp_id"))}
        return {"ok": False, "error": "unknown_op"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/intents/claim")
async def _exp_intents_claim(payload: dict):
    try:
        from intent_exchange import claim
        return {"ok": True, "intent": claim(payload.get("intent_id") or payload.get("id"), payload.get("agent") or payload.get("username"))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/intents/settle")
async def _exp_intents_settle(payload: dict):
    try:
        from intent_exchange import settle
        return {"ok": True, "intent": settle(payload.get("intent_id") or payload.get("id"), payload.get("outcome") or {})}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/r3/allocate")
async def _exp_r3_allocate(payload: dict):
    try:
        from r3_router import allocate
        return {"ok": True, **allocate(payload.get("user") or {}, float(payload.get("budget_usd",0)))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.get("/inventory/get")
async def _exp_inventory_get(product_id: str):
    try:
        from shopify_inventory_proxy import get_stock
        return {"ok": True, **get_stock(product_id)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/coop/sponsor")
async def _exp_coop_sponsor(payload: dict):
    try:
        from coop_sponsors import sponsor_add, state
        sponsor_add(payload.get("name") or "anon", float(payload.get("spend_cap_usd",0)))
        return {"ok": True, "state": state()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/ltv/predict")
async def _exp_ltv_predict(payload: dict):
    try:
        from ltv_forecaster import predict
        return {"ok": True, "ltv": float(predict(payload.get("user") or {}, payload.get("channel") or "tiktok"))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/proposal/nudge")
async def _exp_proposal_nudge(payload: dict):
    try:
        from proposal_autoclose import nudge
        return nudge(payload.get("proposal_id") or payload.get("id"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/proposal/convert")
async def _exp_proposal_convert(payload: dict):
    try:
        from proposal_autoclose import convert_to_quickpay
        return convert_to_quickpay(payload.get("proposal_id") or payload.get("id"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/metabridge/dealgraph/create")
async def _exp_dg_create(payload: dict):
    try:
        from metabridge_dealgraph import create_dealgraph
        return {"ok": True, "graph": create_dealgraph(payload.get("opportunity") or {}, payload.get("roles") or payload.get("roles_needed") or [], payload.get("rev_split") or [])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/metabridge/dealgraph/activate")
async def _exp_dg_activate(payload: dict):
    try:
        from metabridge_dealgraph import activate
        return {"ok": True, "result": activate(payload.get("graph_id") or payload.get("id"))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

try:
    app.include_router(_expansion_router)
except Exception:
    pass
