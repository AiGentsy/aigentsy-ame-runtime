from typing import Dict, Any
from aam_queue import AAMJob
from messaging_adapters import send_email_postmark, send_sms_twilio

# Replace these stubs with your real SDK adapter calls.
def _tiktok_adapter(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if action == "post_video":
        # TODO: upload video via TikTok API
        return {"status":"ok","kpi":{"views":0}}
    elif action == "reply_to_comments":
        return {"status":"ok","kpi":{"replies":payload.get("limit",0)}}
    return {"status":"noop"}

def _amazon_adapter(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if action == "detect_abandoned_cart":
        return {"status":"ok","kpi":{"carts_found": 3}}
    elif action == "send_nudge":
        return {"status":"ok","kpi":{"nudge_sent": True}}
    elif action == "retarget_ads":
        spend = float(payload.get("cap_usd", 0))
        return {"status":"ok","kpi":{"spend_usd": spend}}
    return {"status":"noop"}

def _shopify_adapter(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if action == "send_email_nudge" or action == "send_email_blast":
        # Required fields may include: to, subject, body
        to = payload.get("to") or "demo@example.com"
        subject = payload.get("subject") or "We saved your cart"
        body = payload.get("body") or "Tap to finish checkout."
        res = send_email_postmark(to, subject, body)
        return {"status":"ok","kpi":{"emails":1},"adapter":res}
    if action == "send_sms_nudge":
        to = payload.get("to") or "+10000000000"
        text = payload.get("text") or "Finish your checkout: https://example.com/c/abc"
        res = send_sms_twilio(to, text)
        return {"status":"ok","kpi":{"sms":1},"adapter":res}
    if action == "create_marketing_event":
        return {"status":"ok","kpi":{"event":"created"}}
    if action == "create_discount_code":
        return {"status":"ok","kpi":{"discount_pct": payload.get("amount_pct", 0)}}
    if action == "publish_blog_post":
        return {"status":"ok","kpi":{"post":"published"}}
    if action == "send_email_blast":
        return {"status":"ok","kpi":{"sent": True, "ab_test": bool(payload.get("ab_test"))}}
    return {"status":"noop"}
    if action == "create_marketing_event":
        return {"status":"ok","kpi":{"event":"created"}}
    if action == "create_discount_code":
        return {"status":"ok","kpi":{"discount_pct": payload.get("amount_pct", 0)}}
    if action == "publish_blog_post":
        return {"status":"ok","kpi":{"post":"published"}}
    if action == "send_email_blast":
        return {"status":"ok","kpi":{"sent": True, "ab_test": bool(payload.get("ab_test"))}}
    return {"status":"noop"}

def execute(job: AAMJob) -> Dict[str, Any]:
    if job.app == "tiktok":
        res = _tiktok_adapter(job.action_id, job.payload)
    elif job.app == "amazon":
        res = _amazon_adapter(job.action_id, job.payload)
    elif job.app == "shopify":
        res = _shopify_adapter(job.action_id, job.payload)
    else:
        res = {"status":"unknown_app"}
    return res
