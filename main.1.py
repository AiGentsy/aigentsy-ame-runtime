# ============================
# AiGentsy Runtime (main.py)
# Canonical mint + AMG/AL/JV/AIGx/Contacts
# ============================
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from venture_builder_agent import get_agent_graph
import os, httpx, uuid, json
from datetime import datetime, timezone
from typing import Dict, Any

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
PROPOSAL_WEBHOOK_URL = os.getenv("PROPOSAL_WEBHOOK_URL")  # used by /metabridge passthru
CANONICAL_SCHEMA_VERSION = "v1.1"  # bumped

# ---- Agent Graph (AiGent Venture; MetaUpgrade25+26) ----
agent_graph = get_agent_graph()

# ============================
# Helpers
# ============================
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

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

        # de-dupe
        for u in users:
            if u.get("username") == username or u.get("consent", {}).get("username") == username:
                return {"ok": True, "record": normalize_user_record(u)}

        new_user = make_canonical_record(username, company_type, referral)
        users = _upsert(users, new_user)
        await _jsonbin_put(client, users)
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

    # derive capabilities from scopes (simple rules; expand later)
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
    basis  = body.get("basis","uplift")  # uplift|royalty|bounty
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
                # merge counts by source name
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

# ---- POST: Contacts send (uses webhook; logs outreach) ----
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

    # webhook fire-and-forget
    delivered = False
    if (PROPOSAL_WEBHOOK_URL and not preview):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(PROPOSAL_WEBHOOK_URL, json=payload, headers={"Content-Type":"application/json"})
                delivered = r.status_code in (200,204)
        except Exception:
            delivered = False

    # log outreach event
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

# ---- Existing passthroughs preserved (MetaBridge, Agent) ----
@app.post("/metabridge")
async def metabridge_dispatch(request: Request):
    try:
        data = await request.json()
        query = data.get("query")
        originator = data.get("username","anonymous")
        if not query: return {"error":"No query provided."}
        from aigent_growth_agent import (
            metabridge_dual_match_realworld_fulfillment,
            proposal_generator,
            proposal_dispatch,
            deliver_proposal
        )
        matches  = metabridge_dual_match_realworld_fulfillment(query)
        proposal = proposal_generator(originator, query, matches)
        proposal_dispatch(originator, proposal, match_target=matches[0].get("username") if matches else None)
        deliver_proposal(query=query, matches=matches, originator=originator)
        return {"status":"ok","query":query,"match_count":len(matches),"proposal":proposal,"matches":matches}
    except Exception as e:
        return {"error": f"MetaBridge runtime error: {str(e)}"}

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
