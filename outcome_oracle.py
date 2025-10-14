"""Outcome Oracle (stub)
- Consumes external conversion signals (e.g., Shopify order webhook payload)
- Emits ATTRIBUTED event with confidence
- On settlement, emits PAID and credits AIGx in JSONBin
"""
from typing import Dict, Any
from datetime import datetime, timezone

from log_to_jsonbin_aam_patched import log_event, _get as jb_get, _put as jb_put
from events import emit

def emit_both(kind: str, data: dict):
    try: emit(kind, data)
    except Exception: pass
    try: log_event({"kind": kind, **(data or {})})
    except Exception: pass

def _find_user_record(username: str):
    data = jb_get()
    for r in data.get("record", []):
        uname = (r.get("consent") or {}).get("username") or r.get("username")
        if uname == username:
            return r
    return None

def _save_user_record(updated):
    data = jb_get()
    out = []
    uid = updated.get("id")
    uname = (updated.get("consent") or {}).get("username") or updated.get("username")
    for r in data.get("record", []):
        ru = (r.get("consent") or {}).get("username") or r.get("username")
        if r.get("id") == uid or ru == uname:
            out.append(updated)
        else:
            out.append(r)
    jb_put(out)
    return True

def credit_aigx(username: str, amount: float, meta: Dict[str, Any]) -> bool:
    rec = _find_user_record(username)
    if not rec:
        emit_both("ERROR", {"flow":"oracle","reason":"user_not_found","user_id":username}); return False
    y = rec.get("yield") or {}
    y["aigxEarned"] = float(y.get("aigxEarned", 0)) + float(amount)
    # append transaction
    tx = rec.get("transactions") or {}
    events = tx.get("yieldEvents") or []
    events.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "amount": amount,
        "meta": meta
    })
    tx["yieldEvents"] = events
    rec["yield"] = y
    rec["transactions"] = tx
    _save_user_record(rec)
    return True

def attribute_shopify_order(username: str, order_id: str, rev_usd: float, cid: str = "") -> Dict[str, Any]:
    # lazy heuristic: attribute full order revenue to last INTENDED with same user/app within time window (stub)
    emit_both("ATTRIBUTED", {
        "flow":"oracle","user_id": username,"app": "shopify","attribution":{"orders":1,"rev_usd": rev_usd,"confidence": 0.85},
        "cid": cid
    })
    return {"ok": True, "orders": 1, "rev_usd": rev_usd, "confidence": 0.85}

def settle_payout(username: str, order_id: str, payout_usd: float, cid: str = "") -> Dict[str, Any]:
    emit_both("PAID", {"flow":"oracle","user_id": username,"amount_usd": payout_usd,"cid": cid})
    credit_aigx(username, payout_usd, {"source":"shopify","order_id": order_id, "cid": cid})
    return {"ok": True, "paid": payout_usd}
