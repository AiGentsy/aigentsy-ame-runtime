import os
import stripe
from fastapi import Request, HTTPException

# Load Stripe secrets
STRIPE_SECRET = os.getenv("STRIPE_SECRET")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Only configure Stripe if secret exists
if STRIPE_SECRET:
    stripe.api_key = STRIPE_SECRET
else:
    print("⚠️ Stripe secret key not found — webhook handler is inactive.")

async def handle_stripe_webhook(request: Request):
    if not STRIPE_SECRET or not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe not configured.")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature.")

    # ⚠️ Stub logic — expand when Stripe goes live
    print(f"🔔 Received Stripe event: {event['type']}")

    # Example: unlock vault, remix, clone, etc.
    # if event["type"] == "checkout.session.completed":
    #     session = event["data"]["object"]
    #     # your_logic(session)

    return {"status": "ok"}
