import os, json, requests
JSONBIN_URL = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")
class JSONBinClient:
    def __init__(self, base=JSONBIN_URL, secret=JSONBIN_SECRET):
        if not base or not secret:
            raise RuntimeError("JSONBIN_URL/SECRET missing")
        self.base = base.rstrip('/')
        self.secret = secret
    def get_latest(self):
        r = requests.get(self.base, headers={"X-Master-Key": self.secret}); r.raise_for_status(); return r.json()
    def put_record(self, record):
        payload = {"record": record}
        r = requests.put(self.base, headers={"Content-Type":"application/json","X-Master-Key": self.secret}, json=payload)
        r.raise_for_status(); return r.json()
