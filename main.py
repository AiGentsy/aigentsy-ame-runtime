from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from venture_builder_agent import get_agent_graph

# Initialize agent graph from MetaUpgrade25 archetype
agent_graph = get_agent_graph()

# FastAPI app setup
app = FastAPI()

# === ✅ CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to ["https://aigentsy.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
import httpx
from datetime import datetime, timezone
import uuid

# === ENV ===
JSONBIN_URL = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")

# === Canonical schema helpers ===
CANONICAL_SCHEMA_VERSION = "v1.0"

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

COMPANY_TYPE_PRESETS = {
    "legal":     {"meta_role": "CLO", "traits_add": ["legal"],     "kits_unlock": ["universal"], "flags": {"vaultAccess": True}},
    "social":    {"meta_role": "CMO", "traits_add": ["marketing"], "kits_unlock": ["universal"], "flags": {"vaultAccess": True}},
    "saas":      {"meta_role": "CTO", "traits_add": [],            "kits_unlock": ["universal"], "flags": {"vaultAccess": True, "sdkAccess_eligible": True}},
    "marketing": {"meta_role": "CMO", "traits_add": ["marketing"], "kits_unlock": ["universal","branding"], "flags": {"vaultAccess": True}},
    "custom":    {"meta_role": "Founder","traits_add": ["custom"], "kits_unlock": ["universal"], "flags": {"vaultAccess": True}},
    "general":   {"meta_role": "Founder","traits_add": [],         "kits_unlock": ["universal"], "flags": {"vaultAccess": True}},
}

def _empty_kits():
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

def make_canonical_record(username: str, company_type: str = "general", referral: str = "origin/hero"):
    preset = COMPANY_TYPE_PRESETS.get(company_type, COMPANY_TYPE_PRESETS["general"])
    kits = _empty_kits()
    for k in preset["kits_unlock"]:
        kits[k]["unlocked"] = True

    runtime_flags = {
        "vaultAccess": False,
        "remixUnlocked": False,
        "cloneLicenseUnlocked": False,
        "sdkAccess_eligible": False,
        "flagged": False,
        "eligibleForAudit": True,
        "needsReview": False
    }
    runtime_flags.update(preset["flags"])

    traits = list({*["founder", "autonomous", "aigentsy"], *preset["traits_add"]})

    return {
        "schemaVersion": CANONICAL_SCHEMA_VERSION,
        "id": str(uuid.uuid4()),
        "ventureID": f"aigent0-{username}",
        "consent": {"agreed": True, "username": username, "timestamp": _now_iso()},
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
        "yield": {"autoStake": False, "aigxEarned": 0, "vaultYield": 0, "remixYield": 0, "aigxAttributedTo": [], "aigxEarnedEnabled": False},
        "remix": {"remixCount": 0, "remixCredits": 1000, "lineageDepth": 0, "royaltyTerms": "Standard 30%"},
        "cloneLineage": [],
        "realm": {"name": "Realm 101 — Strategic Expansion", "joinedAt": _now_iso()},
        "metaVenture": {"ventureHive": "Autonomous Launch", "ventureRole": preset["meta_role"], "ventureStatus": "Pending", "ventureID": f"MV-{int(datetime.now().timestamp())}"},
        "mirror": {"mirroredInRealms": ["Realm 101 — Strategic Expansion"], "mirrorIntegrity": "Verified", "sentinelAlert": False},
        "proposal": {"personaHint": "", "proposalsSent": [], "proposalsReceived": []},
        "proposals": [],
        "transactions": {"unlocks": [], "yieldEvents": [], "referralEvents": []},
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
        "mintTime": _now_iso(),
        "created": _now_iso(),
    }

def normalize_user_record(raw: dict) -> dict:
    """Return a canonical, UI-ready view without losing legacy fields."""
    if not raw:
        return {}

    username = raw.get("username") or raw.get("consent", {}).get("username") or ""

    # wallet address vs object
    wallet_addr = raw.get("wallet") if isinstance(raw.get("wallet"), str) else raw.get("walletAddress", "0x0")
    wallet_obj = raw.get("wallet") if isinstance(raw.get("wallet"), dict) else {
        "aigx": raw.get("walletStats", {}).get("aigxEarned", 0),
        "staked": raw.get("walletStats", {}).get("staked", 0)
    }

    kits = raw.get("kits") or _empty_kits()
    licenses = raw.get("licenses") or _empty_licenses()

    rf = raw.get("runtimeFlags", {})
    vault_access = bool(rf.get("vaultAccess") or raw.get("vaultAccess") or licenses.get("vault") or kits.get("universal", {}).get("unlocked"))
    remix_unlocked = bool(rf.get("remixUnlocked") or raw.get("remixUnlocked") or licenses.get("remix"))
    clone_unlocked = bool(rf.get("cloneLicenseUnlocked") or raw.get("cloneLicenseUnlocked") or licenses.get("clone"))
    sdk_eligible = bool(rf.get("sdkAccess_eligible") or raw.get("sdkAccess_eligible") or raw.get("sdkAccess") or licenses.get("sdk"))

    # flatten proposals for UI
    flat_proposals = raw.get("proposals") or []
    if not flat_proposals and "proposal" in raw:
        sent = raw["proposal"].get("proposalsSent", [])
        received = raw["proposal"].get("proposalsReceived", [])
        flat_proposals = [*sent, *received]

    normalized = {
        **raw,
        "schemaVersion": raw.get("schemaVersion") or CANONICAL_SCHEMA_VERSION,
        "username": username,
        "walletAddress": wallet_addr or "0x0",
        "wallet": wallet_obj or {"aigx": 0, "staked": 0},
        "kits": kits,
        "licenses": licenses,
        "runtimeFlags": {
            **{"flagged": False, "eligibleForAudit": True, "needsReview": False},
            **rf,
            "vaultAccess": vault_access,
            "remixUnlocked": remix_unlocked,
            "cloneLicenseUnlocked": clone_unlocked,
            "sdkAccess_eligible": sdk_eligible
        },
        "proposals": flat_proposals,
    }
    return normalized

# === JSONBin helpers that handle both array and {record:[...]} shapes ===
def _envelope_users(bin_json):
    if isinstance(bin_json, list):
        return bin_json, "array"
    return bin_json.get("record", []), "object"

def _wrap_users(users, shape):
    return users if shape == "array" else {"record": users}

# === API ===
@app.post("/user")
async def get_agent_record(request: Request):
    body = await request.json()
    username = body.get("username")
    if not username:
        return {"error": "Missing username"}

    async with httpx.AsyncClient() as client:
        headers = {"X-Master-Key": JSONBIN_SECRET}
        res = await client.get(JSONBIN_URL, headers=headers)
        res.raise_for_status()
        bin_json = res.json()
        users, shape = _envelope_users(bin_json)

        for record in users:
            consent_username = record.get("consent", {}).get("username")
            direct_username = record.get("username")
            if consent_username == username or direct_username == username:
                return {"record": normalize_user_record(record)}

        return {"error": "User not found"}

@app.post("/mint")
async def mint_user(request: Request):
    body = await request.json()
    username = body.get("username")
    company_type = body.get("companyType", "general")
    referral = body.get("referral", "origin/hero")
    if not username:
        return {"ok": False, "error": "Username required"}

    async with httpx.AsyncClient() as client:
        headers = {"X-Master-Key": JSONBIN_SECRET}
        res = await client.get(JSONBIN_URL, headers=headers)
        res.raise_for_status()
        bin_json = res.json()
        users, shape = _envelope_users(bin_json)

        # de-dupe
        for u in users:
            if u.get("username") == username or u.get("consent", {}).get("username") == username:
                return {"ok": True, "record": normalize_user_record(u)}

        new_user = make_canonical_record(username, company_type, referral)
        users.append(new_user)
        payload = _wrap_users(users, shape)
        put = await client.put(JSONBIN_URL, headers=headers, json=payload)
        put.raise_for_status()
        return {"ok": True, "record": normalize_user_record(new_user)}

@app.post("/update_unlock")
async def update_unlock(request: Request):
    """Set an unlock flag and keep status in sync with licenses/runtimeFlags."""
    body = await request.json()
    username = body.get("username")
    key = body.get("unlock")  # "sdk"|"vault"|"remix"|"clone"|"aigx"
    if not username or not key:
        return {"ok": False, "error": "username and unlock required"}

    async with httpx.AsyncClient() as client:
        headers = {"X-Master-Key": JSONBIN_SECRET}
        res = await client.get(JSONBIN_URL, headers=headers)
        res.raise_for_status()
        bin_json = res.json()
        users, shape = _envelope_users(bin_json)

        for i, u in enumerate(users):
            u_name = u.get("username") or u.get("consent", {}).get("username")
            if u_name == username:
                # normalize, update, write
                u = normalize_user_record(u)
                u.setdefault("licenses", _empty_licenses())
                u["licenses"][key] = True
                # mirror to runtimeFlags for UI
                if key == "sdk":
                    u["runtimeFlags"]["sdkAccess_eligible"] = True
                elif key == "vault":
                    u["runtimeFlags"]["vaultAccess"] = True
                elif key == "remix":
                    u["runtimeFlags"]["remixUnlocked"] = True
                elif key == "clone":
                    u["runtimeFlags"]["cloneLicenseUnlocked"] = True
                elif key == "aigx":
                    u.setdefault("yield", {}).update({"aigxEarnedEnabled": True})

                users[i] = u
                payload = _wrap_users(users, shape)
                put = await client.put(JSONBIN_URL, headers=headers, json=payload)
                put.raise_for_status()
                return {"ok": True, "record": normalize_user_record(u)}

        return {"ok": False, "error": "User not found"}

@app.post("/wallet_event")
async def wallet_event(request: Request):
    """
    Update wallet & charts.
    Body: { "username":"alice", "aigxDelta":10, "fiatUSDDelta":0, "note":"Stripe purchase" }
    """
    body = await request.json()
    username = body.get("username")
    if not username:
        return {"ok": False, "error": "username required"}

    aigx_delta = int(body.get("aigxDelta", 0))
    fiat_delta = float(body.get("fiatUSDDelta", 0))

    async with httpx.AsyncClient() as client:
        headers = {"X-Master-Key": JSONBIN_SECRET}
        res = await client.get(JSONBIN_URL, headers=headers)
        res.raise_for_status()
        bin_json = res.json()
        users, shape = _envelope_users(bin_json)

        for i, u in enumerate(users):
            u_name = u.get("username") or u.get("consent", {}).get("username")
            if u_name == username:
                u = normalize_user_record(u)
                # wallet
                u["wallet"]["aigx"] = int(u["wallet"].get("aigx", 0)) + aigx_delta
                u["wallet"]["lastUpdated"] = _now_iso()
                # charts
                u.setdefault("charts", {}).setdefault("aigxBalance", []).append({"date": _now_iso(), "value": u["wallet"]["aigx"]})
                if fiat_delta != 0:
                    u["yield"]["vaultYield"] = float(u["yield"].get("vaultYield", 0)) + fiat_delta
                    u["charts"].setdefault("earningsDaily", []).append({"date": _now_iso(), "value": fiat_delta})
                users[i] = u
                payload = _wrap_users(users, shape)
                put = await client.put(JSONBIN_URL, headers=headers, json=payload)
                put.raise_for_status()
                return {"ok": True, "record": normalize_user_record(u)}

        return {"ok": False, "error": "User not found"}

@app.post("/log-meta-match")
async def log_meta_match_event(request: Request):
    try:
        body = await request.json()
        match_source = body.get("matchSource")
        if not match_source:
            return {"error": "Missing matchSource (username required)"}

        async with httpx.AsyncClient() as client:
            headers = {"X-Master-Key": JSONBIN_SECRET}
            res = await client.get(JSONBIN_URL, headers=headers)
            res.raise_for_status()
            bin_json = res.json()
            users, shape = _envelope_users(bin_json)

            for i, record in enumerate(users):
                username = record.get("consent", {}).get("username") or record.get("username")
                if username == match_source:
                    if "metaMatchEvents" not in record:
                        record["metaMatchEvents"] = []
                    body["timestamp"] = body.get("timestamp") or str(datetime.utcnow().isoformat())
                    record["metaMatchEvents"].append(body)

                    users[i] = record
                    payload = _wrap_users(users, shape)
                    put_res = await client.put(JSONBIN_URL, headers=headers, json=payload)
                    put_res.raise_for_status()
                    return {"status": "✅ Match event logged", "match": body}

            return {"error": "User not found in JSONBin"}

    except Exception as e:
        return {"error": f"MetaMatch logging error: {str(e)}"}

@app.post("/metabridge")
async def metabridge_dispatch(request: Request):
    """
    AiGentsy MetaBridge Runtime:
    Accepts a query (external offer or need), matches via MetaMatch logic,
    generates a proposal, dispatches across channels, and returns structured response.
    """
    try:
        data = await request.json()
        query = data.get("query")
        originator = data.get("username", "anonymous")
        if not query:
            return {"error": "No query provided."}

        from aigent_growth_agent import (
            metabridge_dual_match_realworld_fulfillment,
            proposal_generator,
            proposal_dispatch,
            deliver_proposal
        )

        matches = metabridge_dual_match_realworld_fulfillment(query)
        proposal = proposal_generator(originator, query, matches)
        proposal_dispatch(originator, proposal, match_target=matches[0].get("username") if matches else None)
        deliver_proposal(query=query, matches=matches, originator=originator)

        return {"status": "ok","query": query,"match_count": len(matches),"proposal": proposal,"matches": matches}

    except Exception as e:
        return {"error": f"MetaBridge runtime error: {str(e)}"}

# === Smart Agent Endpoints ===
CFO_ENDPOINT = "https://aigentsy-ame-runtime.onrender.com"
CMO_ENDPOINT = "https://aigent-growth-runtime.onrender.com"
CTO_ENDPOINT = "https://aigent-sdk-runtime.onrender.com"
CLO_ENDPOINT = "https://aigent-remix-runtime.onrender.com"

def route_to_agent_endpoint(user_input: str) -> str:
    q = user_input.lower()
    if any(k in q for k in ["legal", "license", "ip", "contract", "intellectual", "compliance", "insulate"]):
        return CLO_ENDPOINT
    elif any(k in q for k in ["growth", "marketing", "campaign", "audience", "promotion", "referral"]):
        return CMO_ENDPOINT
    elif any(k in q for k in ["tech", "build", "clone", "deploy", "sdk", "feature", "toolkit"]):
        return CTO_ENDPOINT
    elif any(k in q for k in ["finance", "revenue", "yield", "profit", "payment", "token", "earn"]):
        return CFO_ENDPOINT
    return CFO_ENDPOINT  # Default fallback

@app.post("/agent")
async def run_agent(request: Request):
    try:
        data = await request.json()
        user_input = data.get("input", "")
        if not user_input:
            return {"error": "No input provided."}

        initial_state = {"input": user_input, "memory": []}
        result = await agent_graph.ainvoke(initial_state)
        return {"output": result.get("output", "No output returned.")}
    except Exception as e:
        return {"error": f"Agent runtime error: {str(e)}"}
