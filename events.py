import os, datetime as dt
from helpers_net import http_post_json
BACKEND_BASE = os.getenv("BACKEND_BASE", "").rstrip("/")
EVENT_ENDPOINT = f"{BACKEND_BASE}/event" if BACKEND_BASE else None
def emit(kind: str, data: dict):
    if not EVENT_ENDPOINT: return
    payload = {"kind": kind, "ts": dt.datetime.utcnow().isoformat()}
    payload.update(data or {})
    http_post_json(EVENT_ENDPOINT, payload, retries=1, timeout=8)
