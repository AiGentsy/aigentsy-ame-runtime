"""
log_to_jsonbin_aam_patched (PATCHED)
- Backward compatible
- FIX: PUT payload shape is now {"record": records}
- Hardened fallbacks and small correctness tweaks
"""

from __future__ import annotations
import os, json, hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

# ---- Try to import your original helpers (if present) ----
try:
    from log_to_jsonbin import _get as _orig_get, _put as _orig_put, normalize_user_data as _orig_normalize
    HAVE_ORIG = True
except Exception:
    HAVE_ORIG = False

# ---- HTTP client shim ----
try:
    import httpx as _http
    _USE_HTTPX = True
except Exception:
    import requests as _http  # type: ignore
    _USE_HTTPX = False

JSONBIN_URL: str = os.getenv("JSONBIN_URL", "").strip()
JSONBIN_SECRET: str = os.getenv("JSONBIN_SECRET", "").strip()

def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if JSONBIN_SECRET:
        h["X-Master-Key"] = JSONBIN_SECRET
    return h

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _sha1(obj: Any) -> str:
    try:
        raw = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    except Exception:
        raw = repr(obj).encode("utf-8")
    import hashlib as _hl
    return _hl.sha1(raw).hexdigest()

# ---------------- Schema helpers ----------------
def normalize_user_data(rec: dict) -> dict:
    if HAVE_ORIG:
        return _orig_normalize(rec)
    return rec

def _get() -> Dict[str, Any]:
    if HAVE_ORIG:
        return _orig_get()
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
    except Exception:
        return {"record": []}

def _put(records: List[Dict[str, Any]]) -> bool:
    if HAVE_ORIG:
        return _orig_put(records)
    if not (JSONBIN_URL and JSONBIN_SECRET):
        return False
    try:
        payload = {"record": records}  # << FIXED SHAPE
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

# ---------------- Event Log helpers ----------------
def _ensure_event_log(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    found = False
    for rec in records or []:
        if rec.get("id") == "__events__":
            found = True
            if not isinstance(rec.get("events"), list):
                rec["events"] = []
            break
    if not found:
        records = list(records or []) + [{"id": "__events__", "events": []}]
    return records

def log_event(event: Dict[str, Any]) -> bool:
    data = _get()
    recs = list(data.get("record") or [])
    recs = _ensure_event_log(recs)

    e = dict(event or {})
    e.setdefault("ts", _now())
    e.setdefault("kind", "INTENDED")
    e.setdefault("flow", "aam")

    # Append to global event stream
    for i, r in enumerate(recs):
        if r.get("id") == "__events__":
            r.setdefault("events", []).append(e)
            recs[i] = r
            break

    return _put(recs)

# ---------------- Manifest Hosting (optional) ----------------
def upsert_manifest(manifest: Dict[str, Any]) -> bool:
    data = _get()
    recs = list(data.get("record") or [])
    host = None
    for r in recs:
        if r.get("id") == "__manifests__":
            host = r; break
    if host is None:
        host = {"id": "__manifests__", "items": []}
        recs.append(host)

    items = host.get("items") or []
    app = manifest.get("app") or "unknown"
    slug = manifest.get("slug") or manifest.get("version") or "v1"
    key = f"{app}:{slug}"
    manifest = dict(manifest)
    manifest["key"] = key
    manifest["checksum"] = _sha1(manifest)

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

    return _put(recs)

def get_manifest(app: str, slug: str) -> Optional[Dict[str, Any]]:
    data = _get()
    for r in data.get("record", []):
        if r.get("id") == "__manifests__":
            for it in r.get("items") or []:
                if it.get("key") == f"{app}:{slug}":
                    return it
    return None

__all__ = ["log_event", "upsert_manifest", "get_manifest", "normalize_user_data"]
