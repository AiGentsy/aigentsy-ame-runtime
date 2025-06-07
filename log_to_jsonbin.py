import os
import requests
import json

JSONBIN_URL = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")

def log_agent_update(data: dict):
    if not JSONBIN_URL or not JSONBIN_SECRET:
        print("❌ Missing JSONBIN credentials.")
        return

    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSONBIN_SECRET
    }

    try:
        response = requests.put(JSONBIN_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        print("✅ Logged to JSONBin:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("❌ Failed to log to JSONBin:", str(e))
