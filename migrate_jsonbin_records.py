"""
migrate_jsonbin_records.py
- Backfills minimal AAM fields and creates global streams (__events__, __manifests__) if missing.
- Safe to re-run.
"""
from __future__ import annotations
from typing import Any, Dict, List
from copy import deepcopy
import json

try:
    from log_to_jsonbin import _get as jb_get, _put as jb_put, normalize_user_data
except Exception:
    from log_to_jsonbin_aam_patched import _get as jb_get, _put as jb_put  # type: ignore
    def normalize_user_data(x): return x

REQUIRED_TOP = ["earningsEnabled","runtimeFlags","yield","metabridge","automatch","proposal"]
GLOBAL_EVENTS_ID = "__events__"
GLOBAL_MANIFESTS_ID = "__manifests__"

def ensure_globals(records: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
    found_e = any(r.get("id")==GLOBAL_EVENTS_ID for r in records)
    found_m = any(r.get("id")==GLOBAL_MANIFESTS_ID for r in records)
    if not found_e: records.append({"id": GLOBAL_EVENTS_ID, "events": []})
    if not found_m: records.append({"id": GLOBAL_MANIFESTS_ID, "items": []})
    return records

def main():
    data = jb_get()
    recs = list(data.get("record") or [])
    new_recs: List[Dict[str,Any]] = []
    for r in recs:
        if r.get("id") in (GLOBAL_EVENTS_ID, GLOBAL_MANIFESTS_ID):
            new_recs.append(r); continue
        rr = normalize_user_data(r)
        # Backfill required collections
        rr.setdefault("earningsEnabled", True)
        rr.setdefault("runtimeFlags", rr.get("runtimeFlags") or {"vaultAccess": True})
        rr.setdefault("yield", rr.get("yield") or {"aigxEarned": 0, "autoStake": False})
        rr.setdefault("metabridge", rr.get("metabridge") or {"active": True, "bridgeCount": 0})
        rr.setdefault("automatch", rr.get("automatch") or {"status":"pending","matchReady": True})
        rr.setdefault("proposal", rr.get("proposal") or {"personaHint":"","proposalsSent":[],"proposalsReceived":[]})
        new_recs.append(rr)
    new_recs = ensure_globals(new_recs)
    ok = jb_put(new_recs)
    print("Migration write:", ok, "records:", len(new_recs))

if __name__ == "__main__":
    main()
