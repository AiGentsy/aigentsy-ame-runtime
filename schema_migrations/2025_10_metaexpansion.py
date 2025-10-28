#!/usr/bin/env python3
"""
schema_migrations/2025_10_metaexpansion.py

One-off migration script to add AiGentsy v2025-10 fields to every record in your JSONBin.
Safe, idempotent: it only adds fields that are missing and leaves existing data untouched.

ENV required:
  - JSONBIN_URL     (e.g., https://api.jsonbin.io/v3/b/<BIN_ID>)
  - JSONBIN_SECRET  (X-Master-Key)

Usage:
  DRY_RUN=1 python 2025_10_metaexpansion.py   # prints what it would change
  python 2025_10_metaexpansion.py             # performs the PUT update
"""

import os, json, copy, sys, time
import requests

JSONBIN_URL    = os.environ.get("JSONBIN_URL")
JSONBIN_SECRET = os.environ.get("JSONBIN_SECRET")
DRY_RUN        = os.environ.get("DRY_RUN") == "1"

if not JSONBIN_URL or not JSONBIN_SECRET:
    print("ERROR: Missing JSONBIN_URL and/or JSONBIN_SECRET in environment.")
    sys.exit(1)

HEADERS = {
    "X-Master-Key": JSONBIN_SECRET,
    "Content-Type": "application/json",
}

# --- Target default blocks (added if missing) ---
DEFAULTS = {
    "dealGraph": {"nodes": [], "edges": [], "revSplit": []},
    "intents": [],
    "r3": {"budget_usd": 0, "last_allocation": None},
    "mesh": {"sessions": []},
    "coop": {"pool_usd": 0, "sponsors": []},
    "autoStake_policy": {"ratio": 0.25, "weekly_cap_usd": 50, "enabled": True},
    "franchise_packs": [],
    "risk": {"complaints_rate": 0, "riskScore": 0, "region": "US"},
    "channel_pacing": [{"channel": "tiktok", "min": 0, "max": 50}],
    "skills": [],
    "bounties_seen": [],
    "assets_published": [],
    "reactivation": {"last_run": None, "outcomes": []},
}

def apply_defaults(record: dict):
    """Return (new_record, diff) where diff lists keys we added."""
    updated = json.loads(json.dumps(record))  # deep-copy
    diff = {}
    for k, v in DEFAULTS.items():
        if k not in updated:
            updated[k] = v
            diff[k] = "added"
    return updated, diff

def main():
    print("Fetching current JSONBin data...")
    r = requests.get(JSONBIN_URL, headers=HEADERS, timeout=30)
    try:
        data = r.json()
    except Exception as e:
        print("ERROR: Could not parse JSON from JSONBin:", e)
        sys.exit(1)

    # Support both shapes: { record: [...] } or raw list
    records = data.get("record") if isinstance(data, dict) else None
    if records is None:
        if isinstance(data, list):
            records = data
        else:
            print("ERROR: JSONBin payload not understood.")
            sys.exit(1)

    if not isinstance(records, list):
        print("ERROR: 'record' is not a list.")
        sys.exit(1)

    # Apply migrations
    new_records = []
    total_added = 0
    all_diffs = []
    for rec in records:
        if not isinstance(rec, dict):
            new_records.append(rec)
            continue
        new_rec, diff = apply_defaults(rec)
        new_records.append(new_rec)
        if diff:
            total_added += len(diff)
            all_diffs.append({"id": rec.get("id"), "added": list(diff.keys())})

    if not all_diffs:
        print("No changes needed. Schema already up to date.")
        return

    # Backup locally
    backup_name = f"jsonbin_backup_{int(time.time())}.json"
    with open(backup_name, "w", encoding="utf-8") as f:
        json.dump({"record": records}, f, indent=2)
    print(f"Backup written: {backup_name}")

    # Dry run only?
    if DRY_RUN:
        print("=== DRY RUN (no remote PUT) ===")
        print(json.dumps({"changes": all_diffs[:25], "total_keys_added": total_added}, indent=2))
        return

    # PUT updated data
    print("Putting updated records back to JSONBin...")
    put = requests.put(JSONBIN_URL, headers=HEADERS, json={"record": new_records}, timeout=60)
    try:
        result = put.json()
    except Exception as e:
        print("ERROR: PUT failed; could not parse response:", e)
        print("Status:", put.status_code, "Text:", put.text[:500])
        sys.exit(1)

    if put.status_code // 100 != 2:
        print("ERROR: PUT failed:", put.status_code, result)
        sys.exit(1)

    # Report
    report_name = f"jsonbin_migration_report_{int(time.time())}.json"
    with open(report_name, "w", encoding="utf-8") as f:
        json.dump({"changes": all_diffs, "total_keys_added": total_added}, f, indent=2)

    print("Migration complete.")
    print(f"Report: {report_name}")
    print("Summary: records touched:", len(all_diffs), "| total keys added:", total_added)

if __name__ == "__main__":
    main()
