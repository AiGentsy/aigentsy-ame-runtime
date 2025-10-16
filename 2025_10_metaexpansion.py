import os, json, requests
JSONBIN_URL = os.getenv("JSONBIN_URL",""); JSONBIN_SECRET = os.getenv("JSONBIN_SECRET",""); HTTP = requests.Session()
FIELDS = {
  "dealGraph": { "nodes": [], "edges": [], "revSplit": [] },
  "intents": [],
  "r3": { "budget_usd": 0, "last_allocation": None },
  "mesh": { "sessions": [] },
  "coop": { "pool_usd": 0, "sponsors": [] },
  "autoStake_policy": { "ratio": 0.25, "weekly_cap_usd": 50, "enabled": True },
  "franchise_packs": [],
  "risk": { "complaints_rate": 0, "riskScore": 0, "region": "US" },
  "channel_pacing": [{ "channel": "tiktok", "min": 0, "max": 50 }]
}
def run():
    assert JSONBIN_URL, "JSONBIN_URL missing"
    r = HTTP.get(JSONBIN_URL, headers={"X-Master-Key": JSONBIN_SECRET}, timeout=20)
    data = r.json(); users = data["record"] if isinstance(data, dict) else data
    for u in users:
        for k,v in FIELDS.items(): u.setdefault(k, v if not isinstance(v, list) else list(v))
    wr = HTTP.put(JSONBIN_URL, json={"record": users}, headers={"X-Master-Key": JSONBIN_SECRET}, timeout=20)
    print("PUT", wr.status_code)
if __name__ == "__main__": run()
