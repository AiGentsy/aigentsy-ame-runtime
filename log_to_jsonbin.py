# log_to_jsonbin.py
"""
AiGentsy JSONBin adapter (sync, robust, schema-aware).

Exports:
- JSONBIN_URL, JSONBIN_SECRET
- normalize_user_data(record) -> dict
- _get()  -> raw JSONBin response (dict with 'record' or a list)
- _put(records: list) -> True/False
- log_agent_update(record: dict) -> dict (normalized & upserted)
- append_intent_ledger(username: str, entry: dict) -> bool
- credit_aigx(username: str, amount: float, meta: dict = None) -> bool
- get_user(username: str) -> dict | None
- list_users() -> list[dict]
"""

from __future__ import annotations
import os
import json
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime, timezone

# Prefer httpx, fallback to requests
try:
    import httpx as _http
    _USE_HTTPX = True
except Exception:  # pragma: no cover
    import requests as _http  # type: ignore
    _USE_HTTPX = False

# --------- ENV ---------
JSONBIN_URL: str = os.getenv("JSONBIN_URL", "")
JSONBIN_SECRET: str = os.getenv("JSONBIN_SECRET", "")

# Local cache (used when JSONBin is missing/unreachable)
_CACHE: List[Dict[str, Any]] = []

# --------- Time helpers ---------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# --------- Schema normalizer (v3) ---------
SCHEMA_VERSION = 3

def normalize_user_data(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Idempotent, safe normalizer. Fills all fields the UI & API expect."""
    r = dict(rec or {})
    u = (r.get("consent") or {}).get("username") or r.get("username") or "guest"

    # version
    r.setdefault("schemaVersion", 0)
    try:
        r["schemaVersion"] = max(int(r["schemaVersion"] or 0), SCHEMA_VERSION)
    except Exception:
        r["schemaVersion"] = SCHEMA_VERSION

    # identity/consent
    r["username"] = u
    r.setdefault("companyType", r.get("companyType") or "general")
    r.setdefault("created", r.get("created") or _now_iso())
    r.setdefault("consent", {})
    r["consent"].setdefault("agreed", bool(r["consent"].get("agreed")))
    r["consent"].setdefault("username", u)
    r["consent"].setdefault("timestamp", r["consent"].get("timestamp") or _now_iso())

    # traits / flags
    r.setdefault("traits", list(r.get("traits") or []))
    r.setdefault("runtimeFlags", {})
    rf = r["runtimeFlags"]
    rf.setdefault("vaultAccess", True)
    rf.setdefault("remixUnlocked", r.get("remixUnlocked") or False)
    rf.setdefault("cloneLicenseUnlocked", r.get("cloneLicenseUnlocked") or False)

    # wallet / yield
    r.setdefault("wallet", {})
    r["wallet"].setdefault("staked", r.get("staked") or 0)
    r.setdefault("yield", {})
    ry = r["yield"]
    ry.setdefault("aigxEarned", float(ry.get("aigxEarned") or 0))
    ry.setdefault("vaultYield", float(ry.get("vaultYield") or 0))
    ry.setdefault("remixYield", float(ry.get("remixYield") or 0))

    # proposals (+ followups)
    r.setdefault("proposals", list(r.get("proposals") or []))
    for p in r["proposals"]:
        p.setdefault("id", p.get("id") or f"p_{uuid4().hex[:8]}")
        p.setdefault("sender", p.get("sender") or "")
        p.setdefault("recipient", p.get("recipient") or u)
        p.setdefault("title", p.get("title") or "")
        p.setdefault("details", p.get("details") or "")
        # tolerate 'price' legacy key
        amt = p.get("amount", p.get("price", 0))
        try:
            p["amount"] = float(amt or 0)
        except Exception:
            p["amount"] = 0.0
        p.setdefault("timestamp", p.get("timestamp") or _now_iso())
        p.setdefault("link", p.get("link") or "")
        p.setdefault("followups", list(p.get("followups") or []))

    # Order-to-Cash rails
    r.setdefault("orders", list(r.get("orders") or []))
    for o in r["orders"]:
        o.setdefault("id", o.get("id") or f"o_{uuid4().hex[:8]}")
        o.setdefault("quoteId", o.get("quoteId") or "")
        o.setdefault("proposalId", o.get("proposalId") or "")
        o.setdefault("status", o.get("status") or "queued")  # queued|doing|blocked|done
        o.setdefault("createdAt", o.get("createdAt") or _now_iso())
        o.setdefault("sla", o.get("sla") or {"due": None, "started": None, "completed": None})
        o.setdefault("tasks", list(o.get("tasks") or []))     # [{title,assignee,due,doneAt}]

    r.setdefault("invoices", list(r.get("invoices") or []))
    for i in r["invoices"]:
        i.setdefault("id", i.get("id") or f"inv_{uuid4().hex[:8]}")
        i.setdefault("orderId", i.get("orderId") or "")
        try:
            i["amount"] = float(i.get("amount") or 0)
        except Exception:
            i["amount"] = 0.0
        i.setdefault("currency", i.get("currency") or "USD")
        i.setdefault("status", i.get("status") or "draft")    # draft|sent|paid|void
        i.setdefault("issuedAt", i.get("issuedAt") or _now_iso())
        i.setdefault("dueAt", i.get("dueAt") or None)
        i.setdefault("paidAt", i.get("paidAt") or None)

    r.setdefault("payments", list(r.get("payments") or []))
    for pmt in r["payments"]:
        pmt.setdefault("id", pmt.get("id") or f"pay_{uuid4().hex[:8]}")
        pmt.setdefault("invoiceId", pmt.get("invoiceId") or "")
        try:
            pmt["amount"] = float(pmt.get("amount") or 0)
        except Exception:
            pmt["amount"] = 0.0
        pmt.setdefault("currency", pmt.get("currency") or "USD")
        pmt.setdefault("status", pmt.get("status") or "initiated")  # initiated|succeeded|failed
        pmt.setdefault("provider", pmt.get("provider") or "stripe")
        pmt.setdefault("receiptUrl", pmt.get("receiptUrl") or "")
        pmt.setdefault("createdAt", pmt.get("createdAt") or _now_iso())

    # CRM-lite / meetings / KPIs / docs
    r.setdefault("contacts", list(r.get("contacts") or []))
    r.setdefault("meetings", list(r.get("meetings") or []))
    r.setdefault("kpi_snapshots", list(r.get("kpi_snapshots") or []))
    r.setdefault("docs", list(r.get("docs") or []))

    # ownership + ledger (for audit & AIGx credit)
    r.setdefault("ownership", {})
    r["ownership"].setdefault("ledger", list(r["ownership"].get("ledger") or []))

    # Convenience mirrors
    if r["wallet"]["staked"] and not r.get("staked"):
        r["staked"] = r["wallet"]["staked"]

    # Ensure ID
    r.setdefault("id", r.get("id") or f"user_{uuid4().hex[:8]}")

    return r

# --------- Low-level JSONBin I/O (sync) ---------
def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if JSONBIN_SECRET:
        h["X-Master-Key"] = JSONBIN_SECRET
    return h

def _ok_jsonbin() -> bool:
    return bool(JSONBIN_URL and JSONBIN_SECRET)

def _read_jsonbin() -> Tuple[Optional[List[Dict[str, Any]]], Optional[Any]]:
    """Returns (records_list_or_none, raw_response_or_error)."""
    if not _ok_jsonbin():
        return None, "jsonbin-not-configured"
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
        if isinstance(data, dict) and "record" in data:
            return list(data["record"] or []), data
        if isinstance(data, list):
            return data, data
        # Unknown shape; do not crash
        return None, data
    except Exception as e:  # pragma: no cover
        return None, e

def _write_jsonbin(records: List[Dict[str, Any]]) -> Tuple[bool, Optional[Any]]:
    if not _ok_jsonbin():
        return False, "jsonbin-not-configured"
    try:
        payload = records  # v3: PUT the raw JSON you want stored; response wraps it as {'record': ...}
        if _USE_HTTPX:
            with _http.Client(timeout=20) as cx:  # type: ignore[attr-defined]
                r = cx.put(JSONBIN_URL, headers=_headers(), json=payload)
                r.raise_for_status()
        else:
            r = _http.put(JSONBIN_URL, headers=_headers(), json=payload, timeout=20)
            r.raise_for_status()
        return True, None
    except Exception as e:  # pragma: no cover
        return False, e

# Public low-level API (kept to match your existing imports)
def _get() -> Any:
    """Raw JSONBin GET. Returns dict with 'record' (preferred) or a list (legacy)."""
    recs, raw = _read_jsonbin()
    if isinstance(raw, Exception):
        # Fallback to cache
        return {"record": _CACHE}
    if isinstance(raw, list):
        return {"record": raw}
    if isinstance(raw, dict):
        return raw
    # Unknown → wrap cache
    return {"record": _CACHE}

def _put(records: List[Dict[str, Any]]) -> bool:
    """Raw JSONBin PUT. Overwrites the bin with given records list."""
    ok, _err = _write_jsonbin(records)
    if ok:
        # refresh cache
        global _CACHE
        _CACHE = list(records)
    return ok

# --------- High-level helpers ---------
def _merge_into_list(records: List[Dict[str, Any]], user_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Upsert by consent.username or username."""
    target = normalize_user_data(user_record)
    uname = (target.get("consent") or {}).get("username") or target.get("username")
    replaced = False
    out: List[Dict[str, Any]] = []
    for rec in (records or []):
        u = (rec.get("consent") or {}).get("username") or rec.get("username")
        if u == uname and not replaced:
            out.append(target)
            replaced = True
        else:
            out.append(rec)
    if not replaced:
        out.append(target)
    return out

def log_agent_update(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize & upsert a user record into JSONBin.
    Falls back to in-process cache if JSONBin is unavailable.
    """
    global _CACHE
    # Load existing
    existing, _raw = _read_jsonbin()
    if existing is None:
        # work on cache if bin is down
        existing = list(_CACHE)
    # Merge
    merged = _merge_into_list(existing, record)
    # Write
    ok, _err = _write_jsonbin(merged)
    if not ok:
        # keep cache updated even if bin failed
        _CACHE = merged
    else:
        _CACHE = merged
    # Return the normalized upserted record
    uname = (record.get("consent") or {}).get("username") or record.get("username")
    for rec in merged:
        u = (rec.get("consent") or {}).get("username") or rec.get("username")
        if u == uname:
            return normalize_user_data(rec)
    return normalize_user_data(record)

def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Fetch one user (JSONBin first, then cache)."""
    existing, _raw = _read_jsonbin()
    pool = existing if existing is not None else _CACHE
    for rec in pool:
        u = (rec.get("consent") or {}).get("username") or rec.get("username")
        if u == username:
            return normalize_user_data(rec)
    return None

def list_users() -> List[Dict[str, Any]]:
    """List all users (normalized)."""
    existing, _raw = _read_jsonbin()
    pool = existing if existing is not None else _CACHE
    return [normalize_user_data(r) for r in pool]

def append_intent_ledger(username: str, entry: Dict[str, Any]) -> bool:
    """
    Append an event to ownership.ledger for audit/attribution.
    Entry is augmented with a timestamp.
    """
    if not isinstance(entry, dict):
        entry = {"event": str(entry)}
    entry = dict(entry)
    entry.setdefault("ts", _now_iso())

    # Load all
    existing, _raw = _read_jsonbin()
    if existing is None:
        existing = list(_CACHE)

    updated = False
    out: List[Dict[str, Any]] = []
    for rec in existing:
        u = (rec.get("consent") or {}).get("username") or rec.get("username")
        if u == username:
            rec = normalize_user_data(rec)
            rec.setdefault("ownership", {})
            rec["ownership"].setdefault("ledger", [])
            rec["ownership"]["ledger"].append(entry)
            out.append(rec)
            updated = True
        else:
            out.append(rec)

    if not updated:
        # Create user if not found
        fresh = normalize_user_data({"username": username})
        fresh.setdefault("ownership", {"ledger": [entry]})
        out.append(fresh)

    ok, _err = _write_jsonbin(out)
    if ok:
        global _CACHE
        _CACHE = out
    return ok

def credit_aigx(username: str, amount: float, meta: Optional[Dict[str, Any]] = None) -> bool:
    """
    Credit AIGx and add a ledger entry. Safe math & normalization.
    """
    try:
        amt = float(amount)
    except Exception:
        amt = 0.0

    existing, _raw = _read_jsonbin()
    if existing is None:
        existing = list(_CACHE)

    updated = False
    out: List[Dict[str, Any]] = []
    for rec in existing:
        u = (rec.get("consent") or {}).get("username") or rec.get("username")
        if u == username:
            rec = normalize_user_data(rec)
            ry = rec.setdefault("yield", {})
            ry["aigxEarned"] = float(ry.get("aigxEarned") or 0) + amt
            # ledger note
            rec.setdefault("ownership", {})
            rec["ownership"].setdefault("ledger", [])
            rec["ownership"]["ledger"].append({
                "event": "aigx_credit",
                "amount": amt,
                "meta": meta or {},
                "ts": _now_iso()
            })
            out.append(rec)
            updated = True
        else:
            out.append(rec)

    if not updated:
        fresh = normalize_user_data({"username": username})
        fresh["yield"]["aigxEarned"] = float(fresh["yield"].get("aigxEarned") or 0) + amt
        fresh.setdefault("ownership", {"ledger": [{
            "event": "aigx_credit", "amount": amt, "meta": meta or {}, "ts": _now_iso()
        }]})
        out.append(fresh)

    ok, _err = _write_jsonbin(out)
    if ok:
        global _CACHE
        _CACHE = out
    return ok

# Convenience: upgrade all cached users to current schema (used by admin route)
def _upgrade_all_local_cache() -> None:
    global _CACHE
    _CACHE = [normalize_user_data(r) for r in _CACHE]

__all__ = [
    "JSONBIN_URL",
    "JSONBIN_SECRET",
    "normalize_user_data",
    "_get",
    "_put",
    "log_agent_update",
    "append_intent_ledger",
    "credit_aigx",
    "get_user",
    "list_users",
]
