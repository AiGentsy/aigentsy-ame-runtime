from typing import Dict, Any, Optional, List
import os, requests
from fastapi import APIRouter
try:
    from .event_bus import publish
except Exception:
    def publish(*a, **k): pass

# ---------- Optional types / imports (safe fallbacks) ----------
try:
    from .aam_queue import AAMJob  # your typed job
except Exception:
    class AAMJob:  # minimal shim
        def __init__(self, app: str, action_id: str, payload: Dict[str, Any]):
            self.app = app; self.action_id = action_id; self.payload = payload

HTTP = requests.Session()
BACKEND_BASE = (os.getenv("BACKEND_BASE") or "").rstrip("/")
def _u(path: str) -> str: return f"{BACKEND_BASE}{path}" if BACKEND_BASE else path

def _tiktok_adapter(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if action == "post_video": return {"status": "ok", "kpi": {"views": 0}}
    elif action == "reply_to_comments": return {"status": "ok", "kpi": {"replies": payload.get("limit", 0)}}
    return {"status": "noop"}

def _amazon_adapter(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if action == "detect_abandoned_cart": return {"status": "ok", "kpi": {"carts_found": 3}}
    elif action == "send_nudge": return {"status": "ok", "kpi": {"nudge_sent": True}}
    elif action == "retarget_ads": return {"status": "ok", "kpi": {"spend_usd": float(payload.get("cap_usd", 0))}}
    return {"status": "noop"}

def _shopify_adapter(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if action == "create_marketing_event": return {"status": "ok", "kpi": {"event": "created"}}
    if action == "create_discount_code": return {"status": "ok", "kpi": {"discount_pct": payload.get("amount_pct", 0)}}
    if action == "publish_blog_post": return {"status": "ok", "kpi": {"post": "published"}}
    if action == "send_email_blast": return {"status": "ok", "kpi": {"sent": True, "ab_test": bool(payload.get("ab_test"))}}
    return {"status": "noop"}

def _execute_mesh_actions(job: Dict[str, Any]) -> List[Dict[str, Any]]:
    actions = job.get("actions") or []; results: List[Dict[str, Any]] = []
    for a in actions:
        t = a.get("type"); p = a.get("params", {}) or {}
        for k in ("mesh_session_id","bundle_id","intent_id"):
            if a.get(k) and k not in p: p[k] = a[k]
        try:
            ep = None; method = "POST"
            if t == "price.arm": ep = "/pricing/arm"
            elif t == "r3.allocate": ep = "/r3/allocate"
            elif t == "proposal.nudge": ep = "/proposal/nudge"
            elif t == "proposal.convert": ep = "/proposal/convert"
            elif t == "inventory.check": ep = "/inventory/get"; method = "GET"
            elif t == "coop.spend": ep = "/coop/sponsor"
            else:
                results.append({"ok": False, "error": f"unknown_action:{t}"}); continue
            r = (HTTP.get(_u(ep), params=p, timeout=20) if method=="GET" else HTTP.post(_u(ep), json=p, timeout=20))
            results.append({"ok": r.ok, "status": r.status_code, "resp": (r.json() if r.ok else r.text)})
        except Exception as e:
            results.append({"ok": False, "error": str(e)})
    return results

def execute(job: Any) -> Dict[str, Any] | List[Dict[str, Any]]:
    if isinstance(job, dict) and job.get("actions"): return _execute_mesh_actions(job)
    if hasattr(job, "app") and hasattr(job, "action_id") and hasattr(job, "payload"):
        if job.app == "tiktok": return _tiktok_adapter(job.action_id, job.payload)
        elif job.app == "amazon": return _amazon_adapter(job.action_id, job.payload)
        elif job.app == "shopify": return _shopify_adapter(job.action_id, job.payload)
        return {"status": "unknown_app"}
    return {"ok": False, "error": "invalid_job_payload"}

router = APIRouter()
@router.post("/execute")
def execute_route(job: Dict[str, Any]):
    res = execute(job)
    publish("AAM_EXECUTED", {"job": job, "result": res})
    return {"ok": True, "result": res}
