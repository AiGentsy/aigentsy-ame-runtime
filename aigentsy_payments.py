"""
═══════════════════════════════════════════════════════════════════════════════
AIGENTSY LLC PAYMENT COLLECTION
Routes all AiGentsy revenue to your business Stripe account
═══════════════════════════════════════════════════════════════════════════════

Revenue Paths:
- Path A: Platform fees (2.8% + 28¢) from user transactions
- Path B: Wade direct fulfillment (100% of payment)
- Path C: Future - Enterprise/White Label licensing

Environment Variables Required:
- STRIPE_SECRET_KEY: Your Stripe secret key
- AIGENTSY_STRIPE_ACCOUNT: Your AiGentsy LLC connected account ID (acct_xxx)
  OR if using direct charges, this can be omitted

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import stripe
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# AiGentsy LLC Stripe Account
AIGENTSY_ACCOUNT = os.getenv("AIGENTSY_STRIPE_ACCOUNT")  # Your connected account ID

# Platform fee configuration
PLATFORM_FEE_PERCENT = 0.028  # 2.8%
PLATFORM_FEE_FIXED = 0.28     # 28¢


def _now():
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# PATH B: WADE DIRECT PAYMENTS (100% to AiGentsy)
# ═══════════════════════════════════════════════════════════════════════════════

async def create_wade_payment_link(
    amount: float,
    description: str,
    workflow_id: str,
    client_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a Stripe Payment Link for Wade fulfillment
    Payment goes directly to AiGentsy LLC
    
    Use this when Wade completes work and needs to collect payment from client
    """
    try:
        # Create a product for this specific job
        product = stripe.Product.create(
            name=f"AiGentsy Service: {description[:50]}",
            metadata={
                "workflow_id": workflow_id,
                "type": "wade_fulfillment"
            }
        )
        
        # Create a price for the product
        price = stripe.Price.create(
            unit_amount=int(amount * 100),  # Convert to cents
            currency="usd",
            product=product.id
        )
        
        # Create payment link
        payment_link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
            metadata={
                "workflow_id": workflow_id,
                "revenue_path": "path_b_wade",
                "created_at": _now()
            },
            after_completion={
                "type": "redirect",
                "redirect": {
                    "url": "https://aigentsy.com/payment-success?workflow_id=" + workflow_id
                }
            }
        )
        
        return {
            "ok": True,
            "payment_link": payment_link.url,
            "payment_link_id": payment_link.id,
            "amount": amount,
            "workflow_id": workflow_id
        }
        
    except stripe.error.StripeError as e:
        return {"ok": False, "error": str(e)}


async def create_wade_invoice(
    amount: float,
    client_email: str,
    description: str,
    workflow_id: str,
    due_days: int = 7
) -> Dict[str, Any]:
    """
    Create a Stripe Invoice for Wade fulfillment
    More formal than payment link - good for larger amounts
    """
    try:
        # Create or get customer
        customers = stripe.Customer.list(email=client_email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=client_email,
                metadata={"source": "wade_fulfillment"}
            )
        
        # Create invoice
        invoice = stripe.Invoice.create(
            customer=customer.id,
            collection_method="send_invoice",
            days_until_due=due_days,
            metadata={
                "workflow_id": workflow_id,
                "revenue_path": "path_b_wade"
            }
        )
        
        # Add line item
        stripe.InvoiceItem.create(
            customer=customer.id,
            invoice=invoice.id,
            amount=int(amount * 100),
            currency="usd",
            description=description
        )
        
        # Finalize and send
        invoice = stripe.Invoice.finalize_invoice(invoice.id)
        stripe.Invoice.send_invoice(invoice.id)
        
        return {
            "ok": True,
            "invoice_id": invoice.id,
            "invoice_url": invoice.hosted_invoice_url,
            "invoice_pdf": invoice.invoice_pdf,
            "amount": amount,
            "due_date": invoice.due_date,
            "workflow_id": workflow_id
        }
        
    except stripe.error.StripeError as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# PATH A: USER TRANSACTIONS WITH PLATFORM FEE
# ═══════════════════════════════════════════════════════════════════════════════

async def create_user_payment_with_fee(
    amount: float,
    user_stripe_account: str,
    description: str,
    metadata: Dict = None
) -> Dict[str, Any]:
    """
    Create a payment where:
    - User gets (amount - platform_fee)
    - AiGentsy LLC gets platform_fee (2.8% + 28¢)
    
    Uses Stripe Connect destination charges
    """
    try:
        platform_fee = (amount * PLATFORM_FEE_PERCENT) + PLATFORM_FEE_FIXED
        
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency="usd",
            application_fee_amount=int(platform_fee * 100),  # ⬅️ This goes to AiGentsy
            transfer_data={
                "destination": user_stripe_account  # ⬅️ Rest goes to user
            },
            metadata={
                "revenue_path": "path_a_user",
                "platform_fee": platform_fee,
                "user_receives": amount - platform_fee,
                **(metadata or {})
            }
        )
        
        return {
            "ok": True,
            "payment_intent_id": payment_intent.id,
            "client_secret": payment_intent.client_secret,
            "total_amount": amount,
            "platform_fee": platform_fee,
            "user_receives": amount - platform_fee
        }
        
    except stripe.error.StripeError as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# BALANCE & REPORTING
# ═══════════════════════════════════════════════════════════════════════════════

async def get_aigentsy_balance() -> Dict[str, Any]:
    """
    Get current Stripe balance for AiGentsy LLC
    """
    try:
        balance = stripe.Balance.retrieve()
        
        # Extract USD balances
        available_usd = 0
        pending_usd = 0
        
        for bal in balance.available:
            if bal.currency == "usd":
                available_usd = bal.amount / 100
                
        for bal in balance.pending:
            if bal.currency == "usd":
                pending_usd = bal.amount / 100
        
        return {
            "ok": True,
            "available": available_usd,
            "pending": pending_usd,
            "total": available_usd + pending_usd,
            "currency": "USD"
        }
        
    except stripe.error.StripeError as e:
        return {"ok": False, "error": str(e)}


async def get_recent_payments(limit: int = 10) -> Dict[str, Any]:
    """
    Get recent successful payments to AiGentsy
    """
    try:
        charges = stripe.Charge.list(limit=limit)
        
        payments = []
        for charge in charges.data:
            if charge.paid and not charge.refunded:
                payments.append({
                    "id": charge.id,
                    "amount": charge.amount / 100,
                    "description": charge.description,
                    "created": datetime.fromtimestamp(charge.created).isoformat(),
                    "metadata": charge.metadata
                })
        
        return {
            "ok": True,
            "payments": payments,
            "total": sum(p["amount"] for p in payments)
        }
        
    except stripe.error.StripeError as e:
        return {"ok": False, "error": str(e)}


async def get_revenue_by_path(days: int = 30) -> Dict[str, Any]:
    """
    Get revenue breakdown by path (A vs B) for the last N days
    """
    try:
        import time
        since = int(time.time()) - (days * 86400)
        
        charges = stripe.Charge.list(
            created={"gte": since},
            limit=100
        )
        
        path_a = 0  # Platform fees from user transactions
        path_b = 0  # Wade direct fulfillment
        
        for charge in charges.data:
            if not charge.paid or charge.refunded:
                continue
                
            revenue_path = charge.metadata.get("revenue_path", "")
            
            if revenue_path == "path_a_user":
                # This is application_fee_amount
                path_a += charge.application_fee_amount / 100 if charge.application_fee_amount else 0
            elif revenue_path == "path_b_wade":
                path_b += charge.amount / 100
            else:
                # Unknown - count as Path B (direct to AiGentsy)
                path_b += charge.amount / 100
        
        return {
            "ok": True,
            "period_days": days,
            "path_a_fees": round(path_a, 2),
            "path_b_wade": round(path_b, 2),
            "total": round(path_a + path_b, 2)
        }
        
    except stripe.error.StripeError as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# PAYOUT TO BANK
# ═══════════════════════════════════════════════════════════════════════════════

async def initiate_payout(
    amount: float = None,
    description: str = "AiGentsy LLC Payout"
) -> Dict[str, Any]:
    """
    Initiate payout from Stripe to your bank account
    If amount is None, pays out entire available balance
    """
    try:
        # Get current balance
        balance = await get_aigentsy_balance()
        
        if not balance["ok"]:
            return balance
            
        available = balance["available"]
        
        if amount is None:
            amount = available
            
        if amount > available:
            return {
                "ok": False,
                "error": f"Requested ${amount} but only ${available} available"
            }
        
        if amount < 1:
            return {
                "ok": False,
                "error": "Minimum payout is $1.00"
            }
        
        payout = stripe.Payout.create(
            amount=int(amount * 100),
            currency="usd",
            description=description,
            metadata={
                "initiated_at": _now(),
                "source": "aigentsy_admin"
            }
        )
        
        return {
            "ok": True,
            "payout_id": payout.id,
            "amount": amount,
            "status": payout.status,
            "arrival_date": payout.arrival_date,
            "description": description
        }
        
    except stripe.error.StripeError as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI ENDPOINTS (Add these to main.py)
# ═══════════════════════════════════════════════════════════════════════════════

"""
Add these routes to main.py:

from aigentsy_payments import (
    create_wade_payment_link,
    create_wade_invoice,
    create_user_payment_with_fee,
    get_aigentsy_balance,
    get_recent_payments,
    get_revenue_by_path,
    initiate_payout
)

@app.get("/admin/balance")
async def admin_balance():
    return await get_aigentsy_balance()

@app.get("/admin/revenue")
async def admin_revenue(days: int = 30):
    return await get_revenue_by_path(days)

@app.get("/admin/payments")
async def admin_payments(limit: int = 10):
    return await get_recent_payments(limit)

@app.post("/admin/payout")
async def admin_payout(body: Dict = Body(default={})):
    amount = body.get("amount")  # None = full balance
    return await initiate_payout(amount)

@app.post("/wade/payment-link")
async def wade_payment_link(body: Dict = Body(...)):
    return await create_wade_payment_link(
        amount=body["amount"],
        description=body["description"],
        workflow_id=body["workflow_id"],
        client_email=body.get("client_email")
    )

@app.post("/wade/invoice")
async def wade_invoice(body: Dict = Body(...)):
    return await create_wade_invoice(
        amount=body["amount"],
        client_email=body["client_email"],
        description=body["description"],
        workflow_id=body["workflow_id"],
        due_days=body.get("due_days", 7)
    )
"""
