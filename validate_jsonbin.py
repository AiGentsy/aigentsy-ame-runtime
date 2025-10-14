"""
validate_jsonbin.py
- Reads your JSONBin (via original adapter if present) and validates minimum AAM readiness.
- Prints a concise report.
"""
from __future__ import annotations
import json
from typing import Any, Dict, List

try:
    from log_to_jsonbin import _get as jb_get, normalize_user_data
except Exception:
    from log_to_jsonbin_aam_patched import _get as jb_get  # type: ignore
    def normalize_user_data(x): return x

REQUIRED_USER_FIELDS = [
    "username", "runtimeFlags", "yield", "earningsEnabled", "metabridge", "automatch"
]

def main():
    data = jb_get()
    recs = list(data.get("record") or [])
    total = 0; ok = 0; warn = 0
    for r in recs:
        if r.get("id") in ("__events__", "__manifests__"):
            continue
        total += 1
        missing = [f for f in REQUIRED_USER_FIELDS if f not in r]
        if missing:
            print(f"[-] {r.get('id') or r.get('username')} missing: {', '.join(missing)}")
            warn += 1
        else:
            print(f"[+] {r.get('id') or r.get('username')} OK")
            ok += 1
    print(f"\nSummary: {ok}/{total} users ready, {warn} with warnings.")
    # Check existence of global streams
    has_events = any(r.get("id")=="__events__" for r in recs)
    has_manifests = any(r.get("id")=="__manifests__" for r in recs)
    print(f"Events stream present: {has_events}; Manifests registry present: {has_manifests}")
if __name__ == "__main__":
    main()
