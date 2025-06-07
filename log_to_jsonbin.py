import os
import requests
import json

# Load environment variables
JSONBIN_URL = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "true").lower() == "true"

def log_agent_update(data: dict):
    if not JSONBIN_URL or not JSONBIN_SECRET:
        if VERBOSE_LOGGING:
            print("❌ JSONBin logging disabled — missing credentials.")
        return

    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSONBIN_SECRET
    }

    try:
        response = requests.put(JSONBIN_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        if VERBOSE_LOGGING:
            print(f"✅ Logged to JSONBin: {response.status_code}")
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error: {http_err.response.status_code} - {http_err.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error during JSONBin log: {str(e)}")
