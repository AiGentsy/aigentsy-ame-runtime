
import os, hmac, hashlib, base64, json
from datetime import datetime, timezone
from flask import Flask, request, abort, jsonify

# Outcome Oracle hooks (already dual-log to backend + JSONBin)
from outcome_oracle import attribute_shopify_order, settle_payout

# ---- Config via env ----
SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET", "changeme")
# Map shop domain to AiGentsy username in your JSONBin (e.g. {"my-shop.myshopify.com":"wade888"})
SHOPIFY_SHOP_TO_USER = os.getenv("SHOPIFY_SHOP_TO_USER", "{}")
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "demo_user")
# Commission rate: share of revenue credited to AIGx (0.05 = 5%)
COMMISSION_RATE = float(os.getenv("COMMISSION_RATE", "0.05"))

try:
    SHOP_MAP = json.loads(SHOPIFY_SHOP_TO_USER) if SHOPIFY_SHOP_TO_USER else {}
except Exception:
    SHOP_MAP = {}

app = Flask(__name__)

def verify_hmac(secret: str, body: bytes, received_hmac: str) -> bool:
    mac = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256).digest()
    calc = base64.b64encode(mac).decode("utf-8")
    # Use hmac.compare_digest to avoid timing side-channels
    return hmac.compare_digest(calc, received_hmac or "")

def resolve_username(shop_domain: str) -> str:
    if shop_domain in SHOP_MAP:
        return SHOP_MAP[shop_domain]
    return DEFAULT_USERNAME

def extract_correlation_id(payload: dict) -> str:
    # Try several common locations; fall back to cart/checkout tokens
    for key in ("cid", "correlation_id", "correlationId"):
        if key in payload:
            return str(payload.get(key))
    note = payload.get("note") or ""
    if isinstance(note, str) and "cid:" in note:
        try:
            return note.split("cid:")[1].split()[0].strip()
        except Exception:
            pass
    if "checkout_id" in payload:
        return str(payload.get("checkout_id"))
    if "cart_token" in payload:
        return str(payload.get("cart_token"))
    if "id" in payload:
        return f"shopify-{payload.get('id')}"
    return "cid-unknown"

@app.route("/webhooks/shopify", methods=["POST"])
def shopify_webhook():
    # Verify HMAC
    topic = request.headers.get("X-Shopify-Topic", "")
    shop_domain = request.headers.get("X-Shopify-Shop-Domain", "")
    received_hmac = request.headers.get("X-Shopify-Hmac-Sha256", "")
    raw = request.get_data()  # exact bytes
    if not verify_hmac(SHOPIFY_WEBHOOK_SECRET, raw, received_hmac):
        abort(401, description="invalid hmac")

    try:
        payload = request.get_json(force=True, silent=False) or {}
    except Exception:
        abort(400, description="invalid json")

    username = resolve_username(shop_domain)
    cid = extract_correlation_id(payload)

    # Interpret topics
    try:
        if topic == "orders/create":
            rev = float(payload.get("total_price") or payload.get("current_total_price") or 0.0)
            attribute_shopify_order(username=username, order_id=str(payload.get("id")), rev_usd=rev, cid=cid)
        elif topic in ("orders/paid", "orders/fulfilled"):
            rev = float(payload.get("current_total_price") or payload.get("total_price") or 0.0)
            payout = round(rev * COMMISSION_RATE, 2)
            settle_payout(username=username, order_id=str(payload.get("id")), payout_usd=payout, cid=cid)
        else:
            pass
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 200

    return jsonify({"ok": True, "topic": topic, "user": username}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","8080")))
