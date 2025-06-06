import os
import stripe
import json
import requests
from fastapi.responses import JSONResponse

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# JSONBin setup
JSONBIN_URL = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")

def log_agent_update(data: dict):
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSONBIN_SECRET
    }
    response = requests.put(JSONBIN_URL, headers=headers, data=json.dumps(data))
    print("✅ Logged to JSONBin:", response.status_code)

# Optional agent activation logic stub
def activate_agent(agent_id):
    print(f"🟢 Activating agent {agent_id}...")
    # Implement actual activation logic here
    # Could update local DB, trigger background job, etc.

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

        # Log to JSONBin
        log_agent_update({
            "email": customer_email,
            "agent_id": metadata.get("agent_id"),
            "product": metadata.get("product"),
            "payment_status": "paid",
            "timestamp": session.get("created")
        })

        # Optionally trigger agent activation
        if metadata.get("agent_id"):
            activate_agent(metadata["agent_id"])

    return JSONResponse(status_code=200, content={"status": "success"})
