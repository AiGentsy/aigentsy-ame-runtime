"""
log_to_jsonbin_aam_patched.py
- Extends your JSONBin adapter with AAM event logging, policy snapshotting, and manifest hosting.
- Backward compatible with your existing "record" array layout.
"""

from __future__ import annotations
import os, json, hashlib
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
from uuid import uuid4

# ---- Import your original module’s primitives if available ----
try:
    from log_to_jsonbin import _get as _orig_get, _put as _orig_put, normalize_user_data as _orig_normalize
    HAVE_ORIG = True
except Exception:
    HAVE_ORIG = False

# ---- Lightweight HTTP shim (only for future direct bin reads/writes if needed) ----
try:
    import httpx as _http
    _USE_HTTPX = True
except Exception:
    import requests as _http  # type: ignore
    _USE_HTTPX = False

JSONBIN_URL: str = os.getenv("JSONBIN_URL", "")
JSONBIN_SECRET: str = os.getenv("JSONBIN_SECRET", "")

def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if JSONBIN_SECRET:
        h["X-Master-Key"] = JSONBIN_SECRET
    return h

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _sha1(obj: Any) -> str:
    try:
        raw = json.dumps(obj, sort_keys=True).encode("utf-8")
    except Exception:
        raw = repr(obj).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()

# ---------------- Schema helpers ----------------
def normalize_user_data(rec: dict) -> dict:
    """Use original normalizer if present; otherwise pass-through."""
    if HAVE_ORIG:
        return _orig_normalize(rec)
    return rec

def _get() -> Dict[str, Any]:
    if HAVE_ORIG:
        return _orig_get()
    # Fallback GET
    if not (JSONBIN_URL and JSONBIN_SECRET):
        return {"record": []}
    try:
        if _USE_HTTPX:
            with _http.Client(timeout=15) as cx:  # type: ignore[attr-defined]
                r = cx.get(JSONBIN_URL, headers=_headers())
                r.raise_for_status()
                data = r.json()
        else:
            r = _http.get(JSONBIN_URL, headers=_headers(), timeout=15)
            r.raise_for_status()
            data = r.json()
        return data if isinstance(data, dict) else {"record": data}
    except Exception as e:
        return {"record": []}

def _put(records: List[Dict[str, Any]]) -> bool:
    if HAVE_ORIG:
        return _orig_put(records)
    if not (JSONBIN_URL and JSONBIN_SECRET):
        return False
    try:
        payload = records
        if _USE_HTTPX:
            with _http.Client(timeout=20) as cx:  # type: ignore[attr-defined]
                r = cx.put(JSONBIN_URL, headers=_headers(), json=payload)
                r.raise_for_status()
        else:
            r = _http.put(JSONBIN_URL, headers=_headers(), json=payload, timeout=20)
            r.raise_for_status()
        return True
    except Exception:
        return False

# ---------------- AAM Policy Snapshot ----------------
def _policy_from_record(r: dict) -> dict:
    """Derive a minimal AAM policy snapshot from the user record (consent/autonomy/blocks/caps)."""
    # Defaults
    policy = {
        "autonomy": "suggest",           # observe|suggest|act
        "spend_cap_usd": 0,
        "block": [],                     # brand blocks / prohibited terms
        "rate_limit_per_hour": 5
    }
    # Pull from record if present
    runtime_flags = r.get("runtimeFlags") or {}
    yield_obj = r.get("yield") or {}
    # Optional: read custom policy stored under r["policy"] if you decide to keep it
    policy_obj = r.get("policy") or {}
    policy.update({k:v for k,v in policy_obj.items() if k in policy})
    # If a user has autoStake true AND earningsEnabled true, we can safely suggest "act" later
    if r.get("earningsEnabled") and yield_obj.get("autoStake"):
        policy.setdefault("autonomy", "suggest")
    return policy

def policy_snapshot_hash(r: dict) -> str:
    return _sha1(_policy_from_record(r))

# ---------------- AAM Event Log in JSONBin ----------------
def _ensure_event_log(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure there is a top-level 'events' array (global stream)."""
    # We will store a virtual record with id='__events__'
    found = False
    out = []
    for rec in records or []:
        if rec.get("id") == "__events__":
            found = True
            if "events" not in rec or not isinstance(rec.get("events"), list):
                rec["events"] = []
            out.append(rec)
        else:
            out.append(rec)
    if not found:
        out.append({"id": "__events__", "events": []})
    return out

def log_event(event: Dict[str, Any]) -> bool:
    """Append an AAM event to the global event stream inside JSONBin (record id='__events__')."""
    data = _get()
    recs = list(data.get("record") or [])
    recs = _ensure_event_log(recs)
    # Minimal contract alignment and hashing
    e = dict(event or {})
    e.setdefault("ts", _now())
    e.setdefault("kind", "INTENDED")
    e.setdefault("flow", "aam")
    # attach policy snapshot hash if we can resolve user
    uid = e.get("user_id")
    if uid:
        # Try to find the user's record by username (consent.username)
        for r in recs:
            uname = (r.get("consent") or {}).get("username") or r.get("username")
            if uname == uid:
                e.setdefault("policy_snapshot_hash", policy_snapshot_hash(r))
                break
    # append
    for i, r in enumerate(recs):
        if r.get("id") == "__events__":
            r["events"].append(e)
            recs[i] = r
            break
    return _put(recs)

# ---------------- Manifest Hosting (optional in JSONBin) ----------------
def upsert_manifest(manifest: Dict[str, Any]) -> bool:
    """Store or replace an AAM manifest inside JSONBin (record id='__manifests__')."""
    data = _get()
    recs = list(data.get("record") or [])
    # find or create host record
    host = None
    for r in recs:
        if r.get("id") == "__manifests__":
            host = r; break
    if host is None:
        host = {"id": "__manifests__", "items": []}
        recs.append(host)
    items = host.get("items") or []
    # compute key
    app = manifest.get("app") or "unknown"
    slug = manifest.get("slug") or manifest.get("version") or "v1"
    key = f"{app}:{slug}"
    manifest["key"] = key
    manifest["checksum"] = _sha1(manifest)
    # upsert
    new_items = []
    replaced = False
    for it in items:
        if it.get("key") == key:
            new_items.append(manifest); replaced = True
        else:
            new_items.append(it)
    if not replaced:
        new_items.append(manifest)
    host["items"] = new_items
    # write
    return _put(recs)

def get_manifest(app: str, slug: str) -> Optional[Dict[str, Any]]:
    data = _get()
    for r in data.get("record", []):
        if r.get("id") == "__manifests__":
            for it in r.get("items") or []:
                if it.get("key") == f"{app}:{slug}":
                    return it
    return None

__all__ = ["log_event", "upsert_manifest", "get_manifest", "policy_snapshot_hash"]
