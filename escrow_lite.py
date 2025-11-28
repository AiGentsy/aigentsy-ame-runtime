"""
AiGentsy Escrow-Lite (Auth→Capture)
State-driven payment capture with dispute protection
"""
import os
import stripe
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def _now():
    return datetime.now(timezone.utc).isoformat()

def _days_ago(ts_iso: str) -> int:
    try:
        then = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - then).days
    except:
        return 9999


async def create_payment_intent(
    amount: float,
    buyer_email: str,
    intent_id: str,
    metadata: dict = None
) -> Dict[str, Any]:
    """
    Create Stripe PaymentIntent (authorization only)
    Does NOT capture funds immediately
    """
    try:
        pi = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency="usd",
            capture_method="manual",  # ⬅️ KEY: Don't capture yet
            receipt_email=buyer_email,
            metadata={
                "intent_id": intent_id,
                "platform": "aigentsy",
                **(metadata or {})
            }
        )
        
        return {
            "ok": True,
            "payment_intent_id": pi.id,
            "client_secret": pi.client_secret,
            "status": pi.status,
            "amount": amount
        }
    except stripe.error.StripeError as e:
        return {
            "ok": False,
            "error": str(e)
        }


async def capture_payment(
    payment_intent_id: str,
    amount: Optional[float] = None
) -> Dict[str, Any]:
    """
    Capture authorized payment (triggered on DELIVERED)
    Can capture partial amount for disputes
    """
    try:
        capture_params = {}
        if amount:
            capture_params["amount_to_capture"] = int(amount * 100)
        
        pi = stripe.PaymentIntent.capture(
            payment_intent_id,
            **capture_params
        )
        
        return {
            "ok": True,
            "captured": pi.amount_received / 100,
            "status": pi.status,
            "captured_at": _now()
        }
    except stripe.error.StripeError as e:
        return {
            "ok": False,
            "error": str(e)
        }


async def capture_payment_intent(
    intent_id: str,
    amount: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Capture a payment intent - calls capture_payment internally
    Maintains compatibility with main.py imports
    """
    return await capture_payment(intent_id, amount)

    
async def cancel_payment(payment_intent_id: str) -> Dict[str, Any]:
    """
    Cancel authorized payment (if dispute or timeout)
    Releases funds back to buyer
    """
    try:
        pi = stripe.PaymentIntent.cancel(payment_intent_id)
        
        return {
            "ok": True,
            "status": pi.status,
            "cancelled_at": _now()
        }
    except stripe.error.StripeError as e:
        return {
            "ok": False,
            "error": str(e)
        }


async def get_payment_status(payment_intent_id: str) -> Dict[str, Any]:
    """
    Check payment intent status
    """
    try:
        pi = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        return {
            "ok": True,
            "status": pi.status,
            "amount": pi.amount / 100,
            "captured": pi.amount_received / 100 if pi.amount_received else 0,
            "capturable": pi.status == "requires_capture"
        }
    except stripe.error.StripeError as e:
        return {
            "ok": False,
            "error": str(e)
        }


async def auto_capture_on_delivered(intent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Called when intent moves to DELIVERED state
    Auto-captures payment if no active disputes
    """
    payment_intent_id = intent.get("payment_intent_id")
    if not payment_intent_id:
        return {"ok": False, "error": "no_payment_intent"}
    
    # Check for active disputes
    try:
        from disputes import list_disputes
        disputes = list_disputes(intent_id=intent.get("id"), status="open")
        
        if disputes.get("disputes"):
            return {
                "ok": False,
                "paused": "dispute_active",
                "dispute_count": len(disputes["disputes"])
            }
    except:
        # If disputes module not available, proceed with capture
        pass
    
    # Capture payment
    result = await capture_payment(payment_intent_id)
    
    if result["ok"]:
        # Update intent
        intent["payment_captured"] = True
        intent["payment_captured_at"] = _now()
        intent["escrow_status"] = "released"
    
    return result


async def auto_timeout_release(intent: Dict[str, Any], timeout_days: int = 7) -> Dict[str, Any]:
    """
    Auto-release payment if delivery confirmed and no disputes after timeout
    """
    if intent.get("status") != "DELIVERED":
        return {"ok": False, "error": "not_delivered"}
    
    delivered_at = intent.get("delivered_at")
    if not delivered_at:
        return {"ok": False, "error": "no_delivery_timestamp"}
    
    days_since_delivery = _days_ago(delivered_at)
    
    if days_since_delivery < timeout_days:
        return {
            "ok": False,
            "waiting": True,
            "days_remaining": timeout_days - days_since_delivery
        }
    
    # Check for disputes
    try:
        from disputes import list_disputes
        disputes = list_disputes(intent_id=intent.get("id"))
        
        if disputes.get("disputes"):
            return {
                "ok": False,
                "blocked": "dispute_exists"
            }
    except:
        # If disputes module not available, proceed with capture
        pass
    
    # Auto-capture
    return await auto_capture_on_delivered(intent)


async def partial_refund_on_dispute(
    payment_intent_id: str,
    refund_amount: float,
    reason: str
) -> Dict[str, Any]:
    """
    Issue partial refund for resolved disputes
    """
    try:
        # First ensure payment was captured
        pi = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if pi.status != "succeeded":
            return {"ok": False, "error": "payment_not_captured"}
        
        # Create refund
        refund = stripe.Refund.create(
            payment_intent=payment_intent_id,
            amount=int(refund_amount * 100),
            reason="requested_by_customer",
            metadata={"dispute_reason": reason}
        )
        
        return {
            "ok": True,
            "refund_id": refund.id,
            "amount": refund.amount / 100,
            "status": refund.status
        }
    except stripe.error.StripeError as e:
        return {
            "ok": False,
            "error": str(e)
        }
