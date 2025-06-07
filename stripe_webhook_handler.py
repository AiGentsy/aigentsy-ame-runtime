import os
import stripe
import json
import requests
from fastapi.responses import JSONResponse
from datetime import datetime

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# JSONBin setup
JSONBIN_URL = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")

def log_agent_update(data: dict):
    if not JSONBIN_URL or not JSONBIN_SECRET:
        print("❌ Missing JSONBin credentials.")
        return

    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSONBIN_SECRET
    }

    try:
        response = requests.put(JSONBIN_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        print("✅ Logged to JSONBin:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("❌ Failed to log to JSONBin:", str(e))

def activate_agent(agent_id):
    print(f"🟢 Activating agent {agent_id}...")
    # Placeholder for real activation logic
    # You could: trigger background task, update DB, notify clone lineage, etc.

async def handle_stripe_webhook(payload, sig_header):
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        print("❌ Invalid payload:", e)
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})
    except stripe.error.SignatureVerificationError:
        print("❌ Invalid Stripe signature")
        return JSONResponse(status_code=400, content={"error": "Invalid signature"})

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_email")
        metadata = session.get("metadata", {})

        print(f"✅ Payment received for {customer_email}")

        # Log structured data to JSONBin
        log_agent_update({
            "email": customer_email,
            "agent_id": metadata.get("agent_id"),
            "product": metadata.get("product"),
            "payment_status": "paid",
            "timestamp": datetime.utcnow().isoformat()  # ISO format for easier analysis
        })

        # Trigger agent activation
        if metadata.get("agent_id"):
            activate_agent(metadata["agent_id"])

    return JSONResponse(status_code=200, content={"status": "success"})
