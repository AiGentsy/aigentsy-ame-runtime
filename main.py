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

JSONBIN_URL = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")

import httpx

def normalize_user_data(raw):
    runtime = raw.get("runtimeFlags", {})
    kits = raw.get("kits", {})
    licenses = raw.get("licenses", {})

    return {
        "username": raw.get("username", ""),
        "traits": raw.get("traits", []),
        "walletStats": raw.get("walletStats", {"aigxEarned": 0, "staked": 0}),
        "referralCount": raw.get("referralCount", 0),
        "proposals": raw.get("proposals", []),
        "cloneLicenseUnlocked": raw.get("cloneLicenseUnlocked") or licenses.get("clone", False),
        "legalKitUnlocked": raw.get("legalKitUnlocked") or kits.get("legal", {}).get("unlocked", False),
        "runtimeFlags": {
            "sdkAccess_eligible": runtime.get("sdkAccess_eligible", False) or licenses.get("sdk", False),
            "vaultAccess": runtime.get("vaultAccess", False) or licenses.get("vault", False) or kits.get("universal", {}).get("unlocked", False),
            "remixUnlocked": runtime.get("remixUnlocked", False) or licenses.get("remix", False),
            "brandingKitUnlocked": runtime.get("brandingKitUnlocked", False) or kits.get("branding", {}).get("unlocked", False)
        },
        **raw  # ✅ Preserve all other fields for dashboard usage
    }


def normalize_user_record(record):
    consent = record.get("consent", {})

    # Inject fallback team if missing
    default_team = {
        "CTO": "AiGent SDK",
        "CMO": "AiGent Growth",
        "CLO": "AiGent Remix",
        "CFO": "AiGent0"
    }

    record_team = record.get("team", {})
    for role in default_team:
        record_team.setdefault(role, default_team[role])

    return {
        "id": record.get("id", ""),
        "username": consent.get("username") or record.get("username", ""),
        "traits": record.get("traits", []),
        "vaultAccess": record.get("vaultAccess", False),
        "remixUnlocked": record.get("remixUnlocked", False),
        "sdkEligible": record.get("sdkEligible", False),
        "licenseUnlocked": record.get("licenseUnlocked", False),
        "mintTime": record.get("mintTime", ""),
        "runtimeURL": record.get("runtimeURL", ""),
        "metaVenture": record.get("metaVenture", {}),
        "yield": record.get("yield", 0),
        "realm": record.get("realm", {"name": "Unassigned Realm"}),
        "activity": record.get("activity", {}),
        "stats": record.get("stats", {"labels": [], "values": []}),
        "team": record_team,
        "wallet": record.get("wallet", {"aigx": 0, "staked": 0}),
        "achievements": record.get("achievements", []),
        "referrals": record.get("referrals", {"count": 0}),
        "status": record.get("status", "idle"),
        "agentType": record.get("agentType", "AiGent"),
    }

@app.post("/user")
async def get_agent_record(request: Request):
    body = await request.json()
    username = body.get("username")

    if not username:
        return {"error": "Missing username"}

    async with httpx.AsyncClient() as client:
        headers = {"X-Master-Key": JSONBIN_SECRET}
        try:
            res = await client.get(JSONBIN_URL, headers=headers)
            res.raise_for_status()
            data = res.json()
            all_users = data.get("record", [])

            for record in all_users:
                consent_username = record.get("consent", {}).get("username")
                direct_username = record.get("username")

                if consent_username == username or direct_username == username:
                    # ✅ Only normalize for aigent0.html compatibility
                    normalized = normalize_user_data(record)
                    return {"record": normalized}

            return {"error": "User not found"}

        except Exception as e:
            return {"error": f"Fetch error: {str(e)}"}


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
            data = res.json()
            all_users = data.get("record", [])

            for i, record in enumerate(all_users):
                username = record.get("consent", {}).get("username") or record.get("username")
                if username == match_source:
                    if "metaMatchEvents" not in record:
                        record["metaMatchEvents"] = []

                    body["timestamp"] = body.get("timestamp") or str(datetime.utcnow().isoformat())
                    record["metaMatchEvents"].append(body)

                    updated_data = {"record": all_users}
                    put_res = await client.put(JSONBIN_URL, headers=headers, json=updated_data)
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

        # ✅ Runtime modules from aigent_growth_agent
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

        return {
            "status": "ok",
            "query": query,
            "match_count": len(matches),
            "proposal": proposal,
            "matches": matches
        }

    except Exception as e:
        return {"error": f"MetaBridge runtime error: {str(e)}"}
        # === Smart Agent Endpoints ===
CFO_ENDPOINT = "https://aigentsy-ame-runtime.onrender.com"
CMO_ENDPOINT = "https://aigent-growth-runtime.onrender.com"
CTO_ENDPOINT = "https://aigent-sdk-runtime.onrender.com"
CLO_ENDPOINT = "https://aigent-remix-runtime.onrender.com"

# === Smart Router Function ===
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

        # Prepare input state for Venture Builder agent (MetaUpgrade25 logic)
        initial_state = {
            "input": user_input,
            "memory": []
        }

        # Invoke the agent graph
        result = await agent_graph.ainvoke(initial_state)

        return {"output": result.get("output", "No output returned.")}

    except Exception as e:
        return {"error": f"Agent runtime error: {str(e)}"}
