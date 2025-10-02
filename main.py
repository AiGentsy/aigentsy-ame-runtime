# ============================
# AiGentsy Runtime (main.py)
# Canonical mint + AMG/AL/JV/AIGx/Contacts + Business-in-a-Box rails
# ============================
from fastapi import FastAPI, Request, Body, Path
from fastapi.middleware.cors import CORSMiddleware
from venture_builder_agent import get_agent_graph
from log_to_jsonbin_merged import (
    log_agent_update, append_intent_ledger, credit_aigx as credit_aigx_srv,
    log_metaloop, log_autoconnect, log_metabridge, log_metahive
)
import os, httpx, uuid, json, hmac, hashlib, csv, io
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

# ---- App & CORS ----
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # lock down later to your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Env ----
JSONBIN_URL     = os.getenv("JSONBIN_URL")
JSONBIN_SECRET  = os.getenv("JSONBIN_SECRET")
PROPOSAL_WEBHOOK_URL = os.getenv("PROPOSAL_WEBHOOK_URL")  # used by /contacts/send webhook
POL_SECRET      = os.getenv("POL_SECRET", "dev-secret")   # for signed Offer Links
CANONICAL_SCHEMA_VERSION = "v1.1"  # bumped

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

COMPANY_TYPE_PRESETS = {
    "legal":     {"meta_role": "CLO", "traits_add": ["legal"],     "kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
    "social":    {"meta_role": "CMO", "traits_add": ["marketing"], "kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
    "saas":      {"meta_role": "CTO", "traits_add": [],            "kits_unlock": ["universal","sdk"],        "flags": {"vaultAccess": True, "sdkAccess_eligible": True}},
    "marketing": {"meta_role": "CMO", "traits_add": ["marketing"], "kits_unlock": ["universal","branding"],   "flags": {"vaultAccess": True}},
    "custom":    {"meta_role": "Founder", "traits_add": ["custom"],"kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
    "general":   {"meta_role": "Founder", "traits_add": [],        "kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
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

# ---- POST: Contacts (privacy-first) opt-in + counts ----
@app.post("/contacts/optin")
async def contacts_optin(request: Request):
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

# ---- POST: Contacts send (webhook; logs outreach) ----
@app.post("/contacts/send")
async def contacts_send(request: Request):
    """
    Body: { username, channel:"sms|email|dm", template, previewOnly=false }
    We **do not** store raw contacts here—only outreach events & counts.
    If PROPOSAL_WEBHOOK_URL is set, we post a payload there for delivery.
    """
    body = await request.json()
    username = body.get("username")
    channel  = body.get("channel","email")
    template = body.get("template","")
    preview  = bool(body.get("previewOnly", False))
    if not (username and template):
        return {"error": "username & template required"}

    payload = {
        "type": "contacts_send",
        "channel": channel,
        "username": username,
        "template": template,
        "ts": _now()
    }

    delivered = False
    if (PROPOSAL_WEBHOOK_URL and not preview):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(PROPOSAL_WEBHOOK_URL, json=payload, headers={"Content-Type":"application/json"})
                delivered = r.status_code in (200,204)
        except Exception:
            delivered = False

    async with httpx.AsyncClient(timeout=15) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i, u in enumerate(users):
            if (u.get("username") or u.get("consent", {}).get("username")) == username:
                u.setdefault("transactions", {}).setdefault("outreachEvents", []).append(
                    {"channel": channel, "templateHash": hash(template), "delivered": delivered, "ts": _now()}
                )
                users[i] = u
                await _jsonbin_put(client, users)
                return {"ok": True, "delivered": delivered, "record": normalize_user_record(u)}
        return {"error": "User not found"}

# ---- POST: JV Mesh (MetaBridge 2.0 cap-table stub) ----
@app.post("/jv/create")
async def jv_create(request: Request):
    """
    Body: { a: "userA", b: "userB", title, split: {"a":0.6,"b":0.4}, terms }
    Appends JV entry to both users' jvMesh; settlement handled by MetaBridge runtime.
    """
    body = await request.json()
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
        originator = data.get("username","anonymous")
        if not query: return {"error":"No query provided."}

        # Use growth agent's matcher/generator
        from aigent_growth_agent import (
            metabridge_dual_match_realworld_fulfillment,
            proposal_generator
        )
        matches  = metabridge_dual_match_realworld_fulfillment(query)
        proposals = proposal_generator(query, matches, originator)

        # Persist each proposal to the sender's record
        async with httpx.AsyncClient(timeout=20) as client:
            for p in proposals:
                await client.post("http://localhost:8000/submit_proposal", json=p, headers={"Content-Type":"application/json"})

        try:
            log_metabridge(originator, {"query": query, "matches": len(matches)})
        except Exception:
            pass

        return {"status":"ok","query":query,"match_count":len(matches),"proposals":proposals,"matches":matches}
    except Exception as e:
        return {"error": f"MetaBridge runtime error: {str(e)}"}

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
async def revenue_recognize(body: Dict = Body(...)):
    username = body.get("username"); inv_id = body.get("invoiceId")
    if not (username and inv_id): return {"error":"username & invoiceId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        invoice = _find_in(u["invoices"], "id", inv_id)
        if not invoice: return {"error":"invoice not found"}
        invoice["status"] = "paid"; invoice["paid_ts"] = _now()
        for p in u["payments"]:
            if p.get("invoiceId") == inv_id:
                p["status"] = "paid"; p["paid_ts"] = _now()
        amt = float(invoice.get("amount", 0))
        entry = {"ts": _now(), "amount": amt, "currency": invoice.get("currency","USD"),
                 "basis":"revenue", "ref": inv_id}
        u["ownership"]["ledger"].append(entry)
        u["yield"]["aigxEarned"] = float(u["yield"].get("aigxEarned",0)) + amt
        u["ownership"]["aigx"] = float(u["ownership"].get("aigx",0)) + amt
        await _save_users(client, users)
        return {"ok": True, "invoice": invoice, "ledgerEntry": entry}

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
async def contacts_import(body: Dict = Body(...)):
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
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u["contacts"].extend(new_contacts)
        await _save_users(client, users)
        return {"ok": True, "added": len(new_contacts)}

@app.post("/contacts/segment")
async def contacts_segment(body: Dict = Body(...)):
    username = body.get("username"); ids = body.get("ids", []); tags = body.get("tags", [])
    if not (username and ids and tags): return {"error":"username, ids, tags required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for c in u.get("contacts", []):
            if c["id"] in ids:
                c.setdefault("tags", [])
                for t in tags:
                    if t not in c["tags"]: c["tags"].append(t)
        await _save_users(client, users)
        return {"ok": True}

@app.post("/contacts/optout")
async def contacts_optout(body: Dict = Body(...)):
    username = body.get("username"); email = (body.get("email") or "").lower()
    if not (username and email): return {"error":"username & email required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for c in u.get("contacts", []):
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

# ---------- OFF-PLATFORM / POL / PARTNER ----------
@app.post("/offer/publish")
async def offer_publish(body: Dict = Body(...)):
    """
    Input: {username, title, price, scope, terms, src?}
    Output: {oid, sig, url}  (POL = signed, expiring link)
    """
    username = body.get("username"); title = body.get("title"); price = float(body.get("price",0))
    scope = body.get("scope",""); terms = body.get("terms",""); src = body.get("src","direct")
    if not (username and title): return {"error":"username & title required"}
    oid = _id("pol")
    exp = int((datetime.utcnow()+timedelta(days=3)).timestamp())
    sig = _hmac(f"{oid}.{username}.{exp}", POL_SECRET)
    url = f"/offer?oid={oid}&sig={sig}&usr={username}&exp={exp}&src={src}"
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u["offers"].append({"id": oid, "title": title, "price": price, "scope": scope, "terms": terms,
                            "sig": sig, "exp": exp, "src": src, "ts": _now(), "status":"live"})
        await _save_users(client, users)
        return {"ok": True, "oid": oid, "sig": sig, "url": url}

@app.post("/partner/track")
async def partner_track(body: Dict = Body(...)):
    username = body.get("username"); pid = body.get("partnerId"); event = body.get("event")
    if not (username and pid and event): return {"error":"username, partnerId, event required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("partner_events", []).append({"partnerId": pid, "event": event, "ref": body.get("ref"), "ts": _now()})
        if event == "conversion":
            u["ownership"]["aigx"] = float(u["ownership"].get("aigx",0)) + 1.0
            u["ownership"]["ledger"].append({"ts": _now(), "amount": 1.0, "currency": "AIGx", "basis": "partner", "ref": pid})
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
