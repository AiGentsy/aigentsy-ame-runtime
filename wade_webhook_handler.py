"""
═══════════════════════════════════════════════════════════════════════════════
WADE WEBHOOK HANDLER - PATH B REVENUE
Handles Stripe webhooks for Wade's direct harvesting revenue
═══════════════════════════════════════════════════════════════════════════════

PATH B: Wade/AiGentsy direct harvesting
- U-ACR, Receivables, Payments, Gap Harvesters, Market Maker
- Money goes directly to Wade's Stripe account
- No AIGx awarded (Wade's 100% revenue)
- Logged in revenue_reconciliation_engine (path_b_wade)

EVENTS HANDLED:
- payment_intent.succeeded: Payment completed
- charge.succeeded: Charge succeeded
- invoice.paid: Invoice paid
- payout.paid: Payout to bank completed

USAGE:
    from wade_webhook_handler import handle_wade_webhook
    
    @app.post("/webhooks/wade")
    async def wade_webhook(request: Request):
        return await handle_wade_webhook(request)
"""

import os
import stripe
import json
from fastapi import Request, HTTPException
from datetime import datetime, timezone
from typing import Dict, Any

# Initialize Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# Try to import reconciliation engine
try:
    from revenue_reconciliation_engine import reconciliation_engine
    RECONCILIATION_AVAILABLE = True
except ImportError:
    RECONCILIATION_AVAILABLE = False
    print("⚠️ revenue_reconciliation_engine not available - revenue won't be logged")


def _now():
    return datetime.now(timezone.utc).isoformat()


async def parse_stripe_event(request: Request) -> Dict[str, Any]:
    """
    Parse and verify Stripe webhook event
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not STRIPE_WEBHOOK_SECRET:
        print("⚠️ Webhook signature verification skipped (no STRIPE_WEBHOOK_SECRET)")
        return json.loads(payload)
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        return event
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def handle_payment_intent_succeeded(payment_intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle successful PaymentIntent
    This is the main revenue collection event for Path B
    """
    amount = payment_intent.get("amount", 0) / 100  # Convert cents to dollars
    payment_id = payment_intent.get("id")
    metadata = payment_intent.get("metadata", {})
    
    # Extract details
    workflow_id = metadata.get("workflow_id") or metadata.get("opportunity_id")
    revenue_engine = metadata.get("revenue_engine", "unknown")
    description = payment_intent.get("description", "")
    
    print(f"💰 Payment succeeded: ${amount}")
    print(f"   Payment ID: {payment_id}")
    print(f"   Revenue Engine: {revenue_engine}")
    print(f"   Workflow ID: {workflow_id}")
    
    # Log to reconciliation engine
    if RECONCILIATION_AVAILABLE:
        try:
            reconciliation_engine.record_activity(
                activity_type="wade_direct_revenue",
                endpoint="/webhooks/wade/payment",
                owner="wade",
                revenue_path="path_b_wade",
                opportunity_id=workflow_id or payment_id,
                amount=amount,
                details={
                    "payment_intent_id": payment_id,
                    "revenue_engine": revenue_engine,
                    "description": description,
                    "metadata": metadata,
                    "recorded_at": _now()
                }
            )
            print(f"✅ Revenue logged to reconciliation engine: ${amount}")
        except Exception as e:
            print(f"❌ Failed to log revenue: {e}")
    
    return {
        "ok": True,
        "event": "payment_intent.succeeded",
        "amount": amount,
        "payment_id": payment_id,
        "revenue_engine": revenue_engine,
        "workflow_id": workflow_id,
        "revenue_logged": RECONCILIATION_AVAILABLE
    }


async def handle_charge_succeeded(charge: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle successful Charge
    Alternative revenue event (some integrations use charge instead of payment_intent)
    """
    amount = charge.get("amount", 0) / 100
    charge_id = charge.get("id")
    metadata = charge.get("metadata", {})
    
    print(f"💰 Charge succeeded: ${amount}")
    print(f"   Charge ID: {charge_id}")
    
    # Check if this is a duplicate of a payment_intent
    payment_intent_id = charge.get("payment_intent")
    if payment_intent_id:
        print(f"   Linked to PaymentIntent: {payment_intent_id}")
        # Don't double-log - payment_intent.succeeded will handle it
        return {
            "ok": True,
            "event": "charge.succeeded",
            "amount": amount,
            "charge_id": charge_id,
            "note": "Linked to payment_intent - not double-logged"
        }
    
    # Standalone charge - log it
    if RECONCILIATION_AVAILABLE:
        try:
            reconciliation_engine.record_activity(
                activity_type="wade_direct_revenue",
                endpoint="/webhooks/wade/charge",
                owner="wade",
                revenue_path="path_b_wade",
                opportunity_id=charge_id,
                amount=amount,
                details={
                    "charge_id": charge_id,
                    "description": charge.get("description", ""),
                    "metadata": metadata,
                    "recorded_at": _now()
                }
            )
            print(f"✅ Revenue logged: ${amount}")
        except Exception as e:
            print(f"❌ Failed to log revenue: {e}")
    
    return {
        "ok": True,
        "event": "charge.succeeded",
        "amount": amount,
        "charge_id": charge_id,
        "revenue_logged": RECONCILIATION_AVAILABLE
    }


async def handle_invoice_paid(invoice: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle paid Invoice
    Used for Wade direct invoicing (e.g., larger deals)
    """
    amount = invoice.get("amount_paid", 0) / 100
    invoice_id = invoice.get("id")
    metadata = invoice.get("metadata", {})
    
    print(f"💰 Invoice paid: ${amount}")
    print(f"   Invoice ID: {invoice_id}")
    
    if RECONCILIATION_AVAILABLE:
        try:
            reconciliation_engine.record_activity(
                activity_type="wade_invoice_revenue",
                endpoint="/webhooks/wade/invoice",
                owner="wade",
                revenue_path="path_b_wade",
                opportunity_id=invoice_id,
                amount=amount,
                details={
                    "invoice_id": invoice_id,
                    "invoice_number": invoice.get("number"),
                    "description": invoice.get("description", ""),
                    "metadata": metadata,
                    "recorded_at": _now()
                }
            )
            print(f"✅ Invoice revenue logged: ${amount}")
        except Exception as e:
            print(f"❌ Failed to log revenue: {e}")
    
    return {
        "ok": True,
        "event": "invoice.paid",
        "amount": amount,
        "invoice_id": invoice_id,
        "revenue_logged": RECONCILIATION_AVAILABLE
    }


async def handle_payout_paid(payout: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle completed Payout
    Tracks when money moves from Stripe to bank account
    """
    amount = payout.get("amount", 0) / 100
    payout_id = payout.get("id")
    
    print(f"🏦 Payout completed: ${amount}")
    print(f"   Payout ID: {payout_id}")
    print(f"   Arrival date: {payout.get('arrival_date')}")
    
    # Log payout (informational, not revenue)
    if RECONCILIATION_AVAILABLE:
        try:
            reconciliation_engine.record_activity(
                activity_type="wade_payout_to_bank",
                endpoint="/webhooks/wade/payout",
                owner="wade",
                revenue_path="path_b_wade",
                opportunity_id=payout_id,
                amount=amount,
                details={
                    "payout_id": payout_id,
                    "arrival_date": payout.get("arrival_date"),
                    "status": payout.get("status"),
                    "recorded_at": _now()
                }
            )
            print(f"✅ Payout logged")
        except Exception as e:
            print(f"❌ Failed to log payout: {e}")
    
    return {
        "ok": True,
        "event": "payout.paid",
        "amount": amount,
        "payout_id": payout_id
    }


async def handle_wade_webhook(request: Request) -> Dict[str, Any]:
    """
    Main webhook handler for Wade's Path B revenue
    
    Routes events to appropriate handlers:
    - payment_intent.succeeded → Main revenue event
    - charge.succeeded → Alternative revenue event
    - invoice.paid → Invoice revenue
    - payout.paid → Payout tracking
    """
    
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    
    # Parse event
    event = await parse_stripe_event(request)
    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})
    
    print("=" * 80)
    print(f"📨 Wade Webhook: {event_type}")
    print("=" * 80)
    
    # Route to handler
    if event_type == "payment_intent.succeeded":
        result = await handle_payment_intent_succeeded(event_data)
    
    elif event_type == "charge.succeeded":
        result = await handle_charge_succeeded(event_data)
    
    elif event_type == "invoice.paid":
        result = await handle_invoice_paid(event_data)
    
    elif event_type == "payout.paid":
        result = await handle_payout_paid(event_data)
    
    else:
        print(f"ℹ️  Unhandled event type: {event_type}")
        result = {
            "ok": True,
            "event": event_type,
            "handled": False,
            "note": "Event logged but not processed"
        }
    
    print("=" * 80)
    return result
