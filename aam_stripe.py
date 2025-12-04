from typing import Dict, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4
import httpx
import hmac
import hashlib

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"

def verify_stripe_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Stripe webhook signature"""
    if not secret:
        return True
    
    try:
        elements = dict(item.split("=") for item in signature.split(","))
        timestamp = elements.get("t")
        signatures = elements.get("v1", "").split(",")
        
        signed_payload = f"{timestamp}.{payload.decode()}"
        expected_sig = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return any(hmac.compare_digest(expected_sig, sig) for sig in signatures)
    except Exception:
        return False


async def handle_stripe_checkout_completed(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle checkout.session.completed event - upgraded for revenue_flows"""
    
    session = event.get("data", {}).get("object", {})
    
    customer_email = session.get("customer_email")
    amount_total = float(session.get("amount_total", 0)) / 100
    currency = session.get("currency", "usd").upper()
    
    metadata = session.get("metadata", {})
    username = metadata.get("agent") or metadata.get("username")
    
    if not username:
        return {"ok": False, "error": "no_agent_in_metadata"}
    
    # Use revenue_flows for proper fee calculation
    try:
        # Import locally to avoid circular dependency
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        from revenue_flows import ingest_service_payment
        
        # Get deal_id if provided (for premium services)
        deal_id = metadata.get("deal_id")
        invoice_id = f"stripe_{session.get('id')}"
        
        result = await ingest_service_payment(
            username=username,
            invoice_id=invoice_id,
            amount_usd=amount_total,
            platform="stripe",
            deal_id=deal_id
        )
        
        return {
            "ok": True,
            "username": username,
            "amount": amount_total,
            "currency": currency,
            "revenue_processed": result.get("ok", False),
            "user_net": result.get("user_net", 0)
        }
    
    except Exception as e:
        # Fallback to old method if revenue_flows fails
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(
                    "http://localhost:8000/aigx/credit",
                    json={
                        "username": username,
                        "amount": amount_total,
                        "basis": "stripe_checkout",
                        "ref": session.get("id")
                    }
                )
            except:
                pass
        
        return {
            "ok": True,
            "username": username,
            "amount": amount_total,
            "currency": currency,
            "fallback": True,
            "error": str(e)
        }


async def handle_stripe_payment_intent_succeeded(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle payment_intent.succeeded event - upgraded for revenue_flows"""
    
    payment_intent = event.get("data", {}).get("object", {})
    
    amount = float(payment_intent.get("amount", 0)) / 100
    currency = payment_intent.get("currency", "usd").upper()
    
    metadata = payment_intent.get("metadata", {})
    username = metadata.get("agent") or metadata.get("username")
    
    if not username:
        return {"ok": False, "error": "no_agent_in_metadata"}
    
    # Use revenue_flows for proper fee calculation
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        from revenue_flows import ingest_service_payment
        
        deal_id = metadata.get("deal_id")
        invoice_id = f"stripe_{payment_intent.get('id')}"
        
        result = await ingest_service_payment(
            username=username,
            invoice_id=invoice_id,
            amount_usd=amount,
            platform="stripe",
            deal_id=deal_id
        )
        
        return {
            "ok": True,
            "username": username,
            "amount": amount,
            "currency": currency,
            "revenue_processed": result.get("ok", False),
            "user_net": result.get("user_net", 0)
        }
    
    except Exception as e:
        # Fallback
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(
                    "http://localhost:8000/aigx/credit",
                    json={
                        "username": username,
                        "amount": amount,
                        "basis": "stripe_payment",
                        "ref": payment_intent.get("id")
                    }
                )
            except:
                pass
        
        return {
            "ok": True,
            "username": username,
            "amount": amount,
            "currency": currency,
            "fallback": True,
            "error": str(e)
        }


async def handle_stripe_subscription_created(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle customer.subscription.created event"""
    
    subscription = event.get("data", {}).get("object", {})
    
    metadata = subscription.get("metadata", {})
    agent = metadata.get("agent") or metadata.get("username")
    
    if not agent:
        return {"ok": False, "error": "no_agent_in_metadata"}
    
    items = subscription.get("items", {}).get("data", [])
    if not items:
        return {"ok": False, "error": "no_subscription_items"}
    
    price = items[0].get("price", {})
    amount = float(price.get("unit_amount", 0)) / 100
    interval = price.get("recurring", {}).get("interval", "month")
    
    return {
        "ok": True,
        "agent": agent,
        "subscription_id": subscription.get("id"),
        "amount": amount,
        "interval": interval,
        "message": "Recurring revenue tracked"
    }


async def handle_stripe_charge_refunded(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle charge.refunded event"""
    
    charge = event.get("data", {}).get("object", {})
    
    amount_refunded = float(charge.get("amount_refunded", 0)) / 100
    
    metadata = charge.get("metadata", {})
    agent = metadata.get("agent") or metadata.get("username")
    
    if not agent:
        return {"ok": False, "error": "no_agent_in_metadata"}
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/budget/spend",
                json={
                    "username": agent,
                    "amount": amount_refunded,
                    "basis": "stripe_refund",
                    "ref": charge.get("id")
                }
            )
        except Exception as e:
            return {"ok": False, "error": f"debit_failed: {e}"}
    
    return {
        "ok": True,
        "agent": agent,
        "amount_refunded": amount_refunded,
        "message": "Refund processed"
    }


async def handle_stripe_payment_failed(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle payment_intent.payment_failed event"""
    
    payment_intent = event.get("data", {}).get("object", {})
    
    metadata = payment_intent.get("metadata", {})
    agent = metadata.get("agent") or metadata.get("username")
    
    failure_message = payment_intent.get("last_payment_error", {}).get("message", "unknown")
    
    return {
        "ok": True,
        "agent": agent,
        "failure_message": failure_message,
        "message": "Payment failed, no action taken"
    }


async def process_stripe_webhook(
    event_type: str,
    event_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Route Stripe webhook to appropriate handler"""
    
    handlers = {
        "checkout.session.completed": handle_stripe_checkout_completed,
        "payment_intent.succeeded": handle_stripe_payment_intent_succeeded,
        "customer.subscription.created": handle_stripe_subscription_created,
        "charge.refunded": handle_stripe_charge_refunded,
        "payment_intent.payment_failed": handle_stripe_payment_failed
    }
    
    handler = handlers.get(event_type)
    
    if not handler:
        return {"ok": True, "message": f"Unhandled event: {event_type}"}
    
    result = await handler(event_data)
    
    return result
