from typing import Dict, Any, Optional, List, Union
import os, requests

# ---------- Optional types / imports (safe fallbacks) ----------
try:
    from aam_queue import AAMJob  # your typed job
except Exception:
    class AAMJob:  # minimal shim for backward compatibility
        def __init__(self, app: str, action_id: str, payload: Dict[str, Any]):
            self.app = app
            self.action_id = action_id
            self.payload = payload

# Messaging adapters (email/SMS) used by Shopify nudge flows
try:
    from messaging_adapters import send_email_postmark, send_sms_twilio
except Exception:
    def send_email_postmark(to: str, subject: str, body: str) -> Dict[str, Any]:
        return {"ok": False, "mock": True, "reason": "postmark_missing"}
    def send_sms_twilio(to: str, text: str) -> Dict[str, Any]:
        return {"ok": False, "mock": True, "reason": "twilio_missing"}

# Backend base for new mesh-style actions routed via HTTP
HTTP = requests.Session()
BACKEND_BASE = (os.getenv("BACKEND_BASE") or "").rstrip("/")
def _u(path: str) -> str:
    return f"{BACKEND_BASE}{path}" if BACKEND_BASE else path

# ========== Legacy per-app adapters (kept from your working file) ==========
def _tiktok_adapter(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if action == "post_video":
        # TODO: upload video via TikTok API
        return {"status": "ok", "kpi": {"views": 0}}
    elif action == "reply_to_comments":
        return {"status": "ok", "kpi": {"replies": payload.get("limit", 0)}}
    return {"status": "noop"}

def _amazon_adapter(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if action == "detect_abandoned_cart":
        return {"status": "ok", "kpi": {"carts_found": 3}}
    elif action == "send_nudge":
        return {"status": "ok", "kpi": {"nudge_sent": True}}
    elif action == "retarget_ads":
        spend = float(payload.get("cap_usd", 0))
        return {"status": "ok", "kpi": {"spend_usd": spend}}
    return {"status": "noop"}

def _shopify_adapter(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # Normalize email args
    if action in ("send_email_nudge", "send_email_blast"):
        to = payload.get("to") or "demo@example.com"
        subject = payload.get("subject") or "We saved your cart"
        body = payload.get("body") or "Tap to finish checkout."
        res = send_email_postmark(to, subject, body)
        return {"status": "ok", "kpi": {"emails": 1}, "adapter": res}
    if action == "send_sms_nudge":
        to = payload.get("to") or "+10000000000"
        text = payload.get("text") or "Finish your checkout: https://example.com/c/abc"
        res = send_sms_twilio(to, text)
        return {"status": "ok", "kpi": {"sms": 1}, "adapter": res}
    if action == "create_marketing_event":
        return {"status": "ok", "kpi": {"event": "created"}}
    if action == "create_discount_code":
        return {"status": "ok", "kpi": {"discount_pct": payload.get("amount_pct", 0)}}
    if action == "publish_blog_post":
        return {"status": "ok", "kpi": {"post": "published"}}
    if action == "send_email_blast":
        return {"status": "ok", "kpi": {"sent": True, "ab_test": bool(payload.get("ab_test"))}}
    return {"status": "noop"}

# ========== New mesh-style executor API ==========
# Accepts a dict job with: {"actions":[{"type":"...", "params":{...}, "mesh_session_id":"...", "bundle_id":"...", "intent_id":"..."}]}
# Routes to thin HTTP endpoints in main.py (price.arm, r3.allocate, proposal.nudge|convert, inventory.get, coop.spend)
def _execute_mesh_actions(job: Dict[str, Any]) -> List[Dict[str, Any]]:
    actions = job.get("actions") or []
    results: List[Dict[str, Any]] = []
    for a in actions:
        t = a.get("type")
        p = a.get("params", {}) or {}
        # Attach pass-through IDs if present (for attribution)
        for k in ("mesh_session_id", "bundle_id", "intent_id"):
            if a.get(k) and k not in p:
                p[k] = a[k]
        try:
            if t == "mesh.start":
                results.append({"ok": True, "mesh_session_id": p.get("session_id")})
                continue
            # Map action -> endpoint
            ep = None
            method = "POST"
            if t == "price.arm":
                ep = "/pricing/arm"
            elif t == "r3.allocate":
                ep = "/r3/allocate"
            elif t == "proposal.nudge":
                ep = "/proposal/nudge"
            elif t == "proposal.convert":
                ep = "/proposal/convert"
            elif t == "inventory.check":
                ep = "/inventory/get"; method = "GET"
            elif t == "coop.spend":
                ep = "/coop/sponsor"  # placeholder spend
            else:
                results.append({"ok": False, "error": f"unknown_action:{t}"})
                continue

            if method == "GET":
                r = HTTP.get(_u(ep), params=p, timeout=20)
            else:
                r = HTTP.post(_u(ep), json=p, timeout=20)
            results.append({"ok": r.ok, "status": r.status_code, "resp": (r.json() if r.ok else r.text)})
        except Exception as e:
            results.append({"ok": False, "error": str(e)})
    return results

# ========== Public entrypoints ==========
def execute(job: Any) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Backward compatible:
      - Legacy path: job is AAMJob(app, action_id, payload) → routes to *_adapter
      - Mesh path:   job is dict with {"actions":[...]} → routes to HTTP endpoints
    """
    # Mesh path
    if isinstance(job, dict) and job.get("actions"):
        return _execute_mesh_actions(job)

    # Legacy typed path
    if hasattr(job, "app") and hasattr(job, "action_id") and hasattr(job, "payload"):
        if job.app == "tiktok":
            return _tiktok_adapter(job.action_id, job.payload)
        elif job.app == "amazon":
            return _amazon_adapter(job.action_id, job.payload)
        elif job.app == "shopify":
            return _shopify_adapter(job.action_id, job.payload)
        return {"status": "unknown_app"}

    # Unknown payload
    return {"ok": False, "error": "invalid_job_payload"}
