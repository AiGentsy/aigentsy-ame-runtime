import os
import json
import requests
from datetime import datetime, timezone

# Optional: auto-proposal hooks
try:
    from proposal_generator import proposal_generator, proposal_dispatch, deliver_proposal
    from aigent_growth_metamatch import metabridge_dual_match_realworld_fulfillment
except Exception:
    proposal_generator = proposal_dispatch = deliver_proposal = metabridge_dual_match_realworld_fulfillment = None

JSONBIN_URL = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "true").lower() == "true"

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

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

def normalize_user_record(raw: dict) -> dict:
    """Canonical, UI-ready view (mirrors main.py)."""
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

# === JSONBin helpers (support both raw array and {record:[...]} bins) ===
def _envelope_users(bin_json):
    if isinstance(bin_json, list):
        return bin_json, "array"
    return bin_json.get("record", []), "object"

def _wrap_users(users, shape):
    return users if shape == "array" else {"record": users}

def _fetch_users():
    headers = {"X-Master-Key": JSONBIN_SECRET}
    r = requests.get(JSONBIN_URL, headers=headers, timeout=20)
    r.raise_for_status()
    js = r.json()
    return _envelope_users(js)

def _put_users(users, shape):
    headers = {"X-Master-Key": JSONBIN_SECRET, "Content-Type": "application/json"}
    payload = _wrap_users(users, shape)
    r = requests.put(JSONBIN_URL, headers=headers, json=payload, timeout=20)
    r.raise_for_status()
    return r

# === Optional: collectibles + auto-proposal ===
def generate_collectible(username: str, reason: str, metadata: dict = None):
    print(f"🏅 Collectible generated: {{'username':'{username}','reason':'{reason}','metadata':{metadata or {}}}}")

def auto_proposal_on_mint(user: dict):
    if not (proposal_generator and proposal_dispatch and deliver_proposal and metabridge_dual_match_realworld_fulfillment):
        return
    try:
        uname = user.get("username") or user.get("consent", {}).get("username")
        topic = user.get("companyType", "general")
        matches = metabridge_dual_match_realworld_fulfillment(f"startup:{topic}")
        prop = proposal_generator(uname, f"Launch plan for {topic}", matches)
        proposal_dispatch(uname, prop, match_target=matches[0].get("username") if matches else None)
        deliver_proposal(query=topic, matches=matches, originator=uname)
    except Exception as e:
        if VERBOSE_LOGGING:
            print(f"⚠️ auto_proposal_on_mint skipped: {e}")

# === PUBLIC: logging entry point ===
def log_agent_update(incoming: dict):
    """
    Upsert a user record into JSONBin, preserving the array/{record:[...]} envelope,
    keeping flags/traits consistent with the dashboard.
    """
    if not incoming:
        return
    if not JSONBIN_URL or not JSONBIN_SECRET:
        if VERBOSE_LOGGING:
            print("❌ JSONBin logging disabled — missing credentials.")
        return

    try:
        user_in = normalize_user_record(incoming)

        # Enforce vault access & trait so charts/unlocks render immediately
        user_in.setdefault("runtimeFlags", {})
        user_in["runtimeFlags"]["vaultAccess"] = True
        user_in.setdefault("traits", [])
        if "vault" not in user_in["traits"]:
            user_in["traits"].append("vault")

        users, shape = _fetch_users()

        # Upsert by id or username
        uname_in = user_in.get("username") or user_in.get("consent", {}).get("username")
        replaced = False
        for i, u in enumerate(users):
            uname_existing = u.get("username") or u.get("consent", {}).get("username")
            if (u.get("id") and user_in.get("id") and u["id"] == user_in["id"]) or (uname_existing and uname_in and uname_existing == uname_in):
                merged = normalize_user_record({**u, **user_in})  # overlay incoming onto existing
                # keep enforced defaults
                merged["runtimeFlags"]["vaultAccess"] = True
                if "vault" not in merged["traits"]:
                    merged["traits"].append("vault")
                users[i] = merged
                replaced = True
                break

        first_insert = False
        if not replaced:
            users.append(user_in)
            first_insert = True

        _put_users(users, shape)
        if VERBOSE_LOGGING:
            print("✅ Logged to JSONBin")

        # Milestone collectibles
        try:
            if user_in.get("yield", {}).get("aigxEarned", 0) > 0:
                generate_collectible(uname_in, reason="First AIGx Earned")
            if user_in.get("cloneLineageSpread", 0) >= 5:
                generate_collectible(uname_in, reason="Lineage Milestone", metadata={"spread": user_in["cloneLineageSpread"]})
            if user_in.get("remixUnlockedForks", 0) >= 3:
                generate_collectible(uname_in, reason="Remix Milestone", metadata={"forks": user_in["remixUnlockedForks"]})
            if user_in.get("servicesRendered", 0) >= 1:
                generate_collectible(uname_in, reason="First Service Delivered")
        except Exception as e:
            if VERBOSE_LOGGING:
                print(f"⚠️ collectible hook error: {e}")

        # Auto-proposal on first insert
        if first_insert:
            auto_proposal_on_mint(user_in)

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error: {http_err.response.status_code} - {http_err.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error during JSONBin log: {str(e)}")
