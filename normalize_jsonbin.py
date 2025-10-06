#!/usr/bin/env python3
"""
normalize_jsonbin.py
Bulk-upgrades all records in your JSONBin to the latest AiGentsy schema
(Order→Invoice→Pay arrays, KPI snapshots, consent mirrors, etc.).

Defaults to DRY RUN. Use --write to commit changes.
Requires:
  - JSONBIN_URL   (env)  e.g. https://api.jsonbin.io/v3/b/xxxxxxxx
  - JSONBIN_SECRET(env)  your Master Key
"""

from __future__ import annotations
import os, sys, json, argparse, datetime
from typing import Any, Dict, List, Tuple

# Prefer httpx, fallback to requests
try:
    import httpx as _http
    _USE_HTTPX = True
except Exception:
    import requests as _http  # type: ignore
    _USE_HTTPX = False

# Use your shared normalizer (from the file I sent earlier)
try:
    from log_to_jsonbin import normalize_user_data
except Exception as e:
    print("ERROR: Could not import normalize_user_data from log_to_jsonbin.py\n", e, file=sys.stderr)
    sys.exit(1)

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def headers(secret: str) -> Dict[str,str]:
    return {"Content-Type": "application/json", "X-Master-Key": secret}

def load_bin(url: str, secret: str) -> Tuple[List[Dict[str,Any]], Any]:
    if _USE_HTTPX:
        with _http.Client(timeout=20) as cx:  # type: ignore[attr-defined]
            r = cx.get(url, headers=headers(secret))
            r.raise_for_status()
            data = r.json()
    else:
        r = _http.get(url, headers=headers(secret), timeout=20)
        r.raise_for_status()
        data = r.json()
    if isinstance(data, dict) and "record" in data:
        recs = data["record"] or []
    elif isinstance(data, list):
        recs = data
    else:
        raise RuntimeError("JSONBin payload not in expected shape (dict with 'record' or list).")
    if not isinstance(recs, list):
        raise RuntimeError("JSONBin 'record' is not a list.")
    return recs, data

def put_bin(url: str, secret: str, records: List[Dict[str,Any]]) -> None:
    if _USE_HTTPX:
        with _http.Client(timeout=30) as cx:  # type: ignore[attr-defined]
            r = cx.put(url, headers=headers(secret), json=records)
            r.raise_for_status()
    else:
        r = _http.put(url, headers=headers(secret), json=records, timeout=30)
        r.raise_for_status()

def summarize_changes(before: Dict[str,Any], after: Dict[str,Any]) -> List[str]:
    """
    Quick, human-readable deltas (not exhaustive diff).
    """
    msgs = []
    # Top-level keys we care about
    keys = [
        "schemaVersion","companyType","created","traits","runtimeFlags",
        "wallet","yield","proposals","orders","invoices","payments",
        "contacts","meetings","kpi_snapshots","docs","ownership"
    ]
    for k in keys:
        b = before.get(k)
        a = after.get(k)
        if k in ("traits",):
            if len(b or []) != len(a or []):
                msgs.append(f"{k}: {len(b or [])} → {len(a or [])}")
        elif k in ("proposals","orders","invoices","payments","contacts","meetings","kpi_snapshots","docs"):
            if len(b or []) != len(a or []):
                msgs.append(f"{k}: {len(b or [])} → {len(a or [])}")
        elif isinstance(b, dict) and isinstance(a, dict):
            # spot-check a couple
            if k == "yield":
                if (b.get("aigxEarned") or 0) != (a.get("aigxEarned") or 0):
                    msgs.append(f"yield.aigxEarned: {b.get('aigxEarned')} → {a.get('aigxEarned')}")
            if k == "runtimeFlags":
                for subk in ("vaultAccess","remixUnlocked","cloneLicenseUnlocked"):
                    if (b.get(subk) != a.get(subk)):
                        msgs.append(f"runtimeFlags.{subk}: {b.get(subk)} → {a.get(subk)}")
        else:
            if b != a:
                msgs.append(f"{k}: {b} → {a}")
    # Consent quick check
    bc = before.get("consent") or {}
    ac = after.get("consent") or {}
    if (bc.get("agreed") != ac.get("agreed")) or (bc.get("timestamp") != ac.get("timestamp")):
        msgs.append(f"consent.agreed/timestamp updated")
    return msgs

def main():
    ap = argparse.ArgumentParser(description="Normalize all records in JSONBin to latest AiGentsy schema.")
    ap.add_argument("--url", default=os.getenv("JSONBIN_URL",""), help="JSONBin URL (default: env JSONBIN_URL)")
    ap.add_argument("--secret", default=os.getenv("JSONBIN_SECRET",""), help="JSONBin Master Key (default: env JSONBIN_SECRET)")
    ap.add_argument("--backup", default=f"jsonbin_backup_{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json",
                    help="Path to write a local backup before any write (default: jsonbin_backup_UTC.json)")
    ap.add_argument("--write", action="store_true", help="Actually PUT normalized records back to JSONBin.")
    ap.add_argument("--limit", type=int, default=0, help="Only process first N records (dry-run or write). 0 = all.")
    args = ap.parse_args()

    url = args.url.strip()
    secret = args.secret.strip()
    if not url or not secret:
        print("ERROR: JSONBIN_URL / JSONBIN_SECRET are required (pass via env or --url/--secret).", file=sys.stderr)
        sys.exit(2)

    print(f"→ Fetching JSONBin from {url} …")
    try:
        records, raw = load_bin(url, secret)
    except Exception as e:
        print("ERROR: Could not read JSONBin:", e, file=sys.stderr)
        sys.exit(3)

    total = len(records)
    limit = args.limit if args.limit and args.limit > 0 else total
    print(f"✓ Loaded {total} records. Normalizing {limit}/{total} …")

    changed = 0
    normalized: List[Dict[str,Any]] = []
    previews = []

    for idx, rec in enumerate(records):
        if idx < limit:
            before = json.loads(json.dumps(rec))  # deep copy
            after = normalize_user_data(rec)
            normalized.append(after)
            if json.dumps(before, sort_keys=True) != json.dumps(after, sort_keys=True):
                changed += 1
                # keep small preview for console
                uname = (after.get("consent") or {}).get("username") or after.get("username") or f"idx_{idx}"
                previews.append((uname, summarize_changes(before, after)[:6]))
        else:
            # beyond limit: keep as-is
            normalized.append(rec)

    print(f"→ Normalized {limit} records. Changed: {changed}.")
    if previews:
        print("\nSample changes:")
        for uname, msgs in previews[:8]:
            print(f" - {uname}:")
            for m in msgs:
                print(f"     • {m}")

    # Always write a local backup of the original payload
    try:
        with open(args.backup, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        print(f"\n🛟 Backup of original data saved to: {args.backup}")
    except Exception as e:
        print("WARNING: Could not write backup file:", e, file=sys.stderr)

    if not args.write:
        print("\n(DRY RUN) No changes written. Run again with --write to commit.")
        return

    print("\n→ Writing normalized records back to JSONBin …")
    try:
        put_bin(url, secret, normalized)
        print("✓ Write complete.")
    except Exception as e:
        print("ERROR: Write failed:", e, file=sys.stderr)
        print("Original backup preserved at:", args.backup)
        sys.exit(4)

if __name__ == "__main__":
    main()
