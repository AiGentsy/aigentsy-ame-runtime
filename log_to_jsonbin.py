
import os
import requests
import json

JSONBIN_URL = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")

def log_agent_update(data: dict):
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSONBIN_SECRET
    }
    response = requests.put(JSONBIN_URL, headers=headers, data=json.dumps(data))
    print("✅ Logged to JSONBin:", response.status_code)
