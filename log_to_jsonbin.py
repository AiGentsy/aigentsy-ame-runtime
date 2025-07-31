import os
import requests
import json
def normalize_user_data(raw):
    return {
        "username": raw.get("username", ""),
        "traits": raw.get("traits", []),
        "walletStats": raw.get("walletStats", {"aigxEarned": 0, "staked": 0}),
        "referralCount": raw.get("referralCount", 0),
        "proposals": raw.get("proposals", []),
        "cloneLicenseUnlocked": raw.get("cloneLicenseUnlocked", False),
        "legalKitUnlocked": raw.get("legalKitUnlocked", False),
        "runtimeFlags": raw.get("runtimeFlags", {
            "sdkAccess_eligible": False,
            "vaultAccess": False,
            "remixUnlocked": False
        }),
        **raw  # preserve any additional fields
    }

# ✅ Auto-proposal logic for 3.3A (trigger on user mint)
from proposal_generator import proposal_generator, proposal_dispatch, deliver_proposal
from aigent_growth_metamatch import metabridge_dual_match_realworld_fulfillment

# Load environment variables
JSONBIN_URL = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "true").lower() == "true"

def generate_collectible(username: str, reason: str, metadata: dict = None):
    """
    Mints a merit-based collectible based on a user milestone.
    Currently logs to console; future-ready for token/NFT storage or reward.
    """

    collectible = {
        "username": username,
        "reason": reason,
        "metadata": metadata or {},
    }
    print(f"🏅 Collectible generated: {collectible}")

def log_agent_update(data: dict):
    data = normalize_user_data(data)

    if not JSONBIN_URL or not JSONBIN_SECRET:
        if VERBOSE_LOGGING:
            print("❌ JSONBin logging disabled — missing credentials.")
        return

    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSONBIN_SECRET
    }

    try:
        # ✅ Step 1: Fetch current JSONBin record
        res = requests.get(JSONBIN_URL, headers=headers)
        res.raise_for_status()
        current_record = res.json().get("record", {})

        # ✅ Step 2: Match by username
        if current_record.get("username") != data.get("username"):
            print("⚠️ Username mismatch or missing. Overwriting entire record.")
            merged_data = data  # fallback: overwrite anyway
        else:
            merged_data = {**current_record, **data}

        # ✅ Step 3: Write back merged record
        put_res = requests.put(JSONBIN_URL, headers=headers, data=json.dumps(merged_data))
        put_res.raise_for_status()

        if VERBOSE_LOGGING:
            print(f"✅ Safely logged merged record for: {data.get('username')}")

        # 🏅 Optional: Milestone logic preserved here...
        if data.get("yield", {}).get("aigxEarned", 0) > 0:
            generate_collectible(data["username"], reason="First AIGx Earned")
        if data.get("cloneLineageSpread", 0) >= 5:
            generate_collectible(data["username"], reason="Lineage Milestone", metadata={"spread": data["cloneLineageSpread"]})
        if data.get("remixUnlockedForks", 0) >= 3:
            generate_collectible(data["username"], reason="Remix Milestone", metadata={"forks": data["remixUnlockedForks"]})
        if data.get("servicesRendered", 0) >= 1:
            generate_collectible(data["username"], reason="First Service Delivered")

        if data.get("username"):
            auto_proposal_on_mint(data)

        if data.get("yield", {}).get("aigxEarnedEnabled"):
            print(f"💸 AIGx unlock detected for {data['username']}")

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error: {http_err.response.status_code} - {http_err.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error during JSONBin log: {str(e)}")

