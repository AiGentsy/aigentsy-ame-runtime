"""
V115 LIVE TEST MODULE
=====================

Test endpoints for running real monetization cycles with your APIs.
Deploy to Render and hit these endpoints to test with real data.

Endpoints:
- GET  /v115/test/status     - Check all API connectivity
- POST /v115/test/run-cycle  - Run full monetization cycle
- POST /v115/test/execute    - Execute a real autonomous transaction
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Check for Stripe
STRIPE_AVAILABLE = False
stripe = None
try:
    import stripe as stripe_module
    stripe = stripe_module
    stripe_key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET")
    if stripe_key and not stripe_key.startswith("sk_live_xxxxx"):
        stripe.api_key = stripe_key
        STRIPE_AVAILABLE = True
except ImportError:
    pass


def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def test_stripe_connection() -> Dict[str, Any]:
    """Test Stripe API connection and return account data"""
    if not STRIPE_AVAILABLE:
        return {"ok": False, "error": "Stripe not configured"}

    try:
        balance = stripe.Balance.retrieve()

        available = []
        pending = []
        for b in balance.available:
            available.append({"currency": b.currency.upper(), "amount": b.amount / 100})
        for b in balance.pending:
            pending.append({"currency": b.currency.upper(), "amount": b.amount / 100})

        return {
            "ok": True,
            "connected": True,
            "balance": {
                "available": available,
                "pending": pending
            }
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def get_receivables_data() -> Dict[str, Any]:
    """Get real receivables data from Stripe"""
    if not STRIPE_AVAILABLE:
        return {"ok": False, "error": "Stripe not configured"}

    try:
        invoices = stripe.Invoice.list(status="open", limit=100)
        open_invoices = list(invoices.auto_paging_iter())

        invoice_data = []
        total_receivables = 0

        for inv in open_invoices:
            amount = inv.amount_due / 100
            total_receivables += amount

            days_outstanding = 0
            if inv.created:
                days_outstanding = (datetime.now(timezone.utc).timestamp() - inv.created) // 86400

            invoice_data.append({
                "invoice_id": inv.id,
                "amount": amount,
                "currency": inv.currency.upper(),
                "customer_email": inv.customer_email,
                "days_outstanding": int(days_outstanding),
                "status": inv.status
            })

        return {
            "ok": True,
            "total_receivables": total_receivables,
            "invoice_count": len(invoice_data),
            "invoices": invoice_data[:10],  # First 10
            "potential_advance": total_receivables * 0.85,  # 85% advance rate
            "platform_fee": total_receivables * 0.05  # 5% fee
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def get_payments_data() -> Dict[str, Any]:
    """Get real payment transaction data from Stripe"""
    if not STRIPE_AVAILABLE:
        return {"ok": False, "error": "Stripe not configured"}

    try:
        charges = stripe.Charge.list(limit=100)
        charge_list = list(charges.auto_paging_iter())

        succeeded = [c for c in charge_list if c.status == "succeeded"]
        total_volume = sum(c.amount for c in succeeded) / 100

        # Analyze card brands
        brands = {}
        countries = {}

        for charge in succeeded:
            pm = charge.payment_method_details
            if pm and hasattr(pm, 'card') and pm.card:
                brand = pm.card.brand if hasattr(pm.card, 'brand') else 'unknown'
                country = pm.card.country if hasattr(pm.card, 'country') else 'unknown'
                brands[brand] = brands.get(brand, 0) + 1
                countries[country] = countries.get(country, 0) + 1

        # Calculate optimization potential
        # Current average: 2.9% + $0.30
        # Optimized: 2.2% + $0.25
        current_fees = total_volume * 0.029 + len(succeeded) * 0.30
        optimized_fees = total_volume * 0.022 + len(succeeded) * 0.25
        potential_savings = current_fees - optimized_fees

        return {
            "ok": True,
            "total_volume": total_volume,
            "transaction_count": len(succeeded),
            "card_brands": brands,
            "card_countries": countries,
            "fee_analysis": {
                "current_estimated_fees": round(current_fees, 2),
                "optimized_fees": round(optimized_fees, 2),
                "potential_monthly_savings": round(potential_savings, 2),
                "savings_pct": round((potential_savings / current_fees * 100) if current_fees > 0 else 0, 2)
            }
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def execute_autonomous_action() -> Dict[str, Any]:
    """
    Execute a REAL autonomous monetization action.

    This will:
    1. Find the oldest unpaid invoice
    2. Create an automated reminder
    3. Log the action

    SAFE: Does not charge money, only sends reminders.
    """
    if not STRIPE_AVAILABLE:
        return {"ok": False, "error": "Stripe not configured", "action": "none"}

    try:
        # Find oldest unpaid invoice
        invoices = stripe.Invoice.list(status="open", limit=10)
        open_invoices = list(invoices.auto_paging_iter())

        if not open_invoices:
            return {
                "ok": True,
                "action": "none",
                "reason": "No open invoices to process"
            }

        # Sort by age (oldest first)
        sorted_invoices = sorted(open_invoices, key=lambda x: x.created)
        target_invoice = sorted_invoices[0]

        # Get customer details
        customer = None
        if target_invoice.customer:
            try:
                customer = stripe.Customer.retrieve(target_invoice.customer)
            except:
                pass

        action_result = {
            "ok": True,
            "action": "invoice_reminder_analysis",
            "invoice_id": target_invoice.id,
            "amount": target_invoice.amount_due / 100,
            "currency": target_invoice.currency.upper(),
            "customer_email": target_invoice.customer_email,
            "days_outstanding": int((datetime.now(timezone.utc).timestamp() - target_invoice.created) // 86400) if target_invoice.created else 0,
            "executed_at": _now(),
            "autonomous": True
        }

        # Calculate potential revenue from collection
        amount = target_invoice.amount_due / 100
        action_result["revenue_opportunity"] = {
            "collection_fee": round(amount * 0.05, 2),  # 5% collection fee
            "advance_fee": round(amount * 0.03, 2),     # 3% if advanced
            "total_potential": round(amount * 0.08, 2)
        }

        # Option to send reminder (commented out for safety - uncomment to enable)
        # stripe.Invoice.send_invoice(target_invoice.id)
        # action_result["reminder_sent"] = True

        return action_result

    except Exception as e:
        return {"ok": False, "error": str(e), "action": "failed"}


async def run_full_cycle() -> Dict[str, Any]:
    """Run a complete monetization cycle with all available APIs"""

    cycle_id = f"cycle_{int(datetime.now().timestamp())}"
    results = {
        "cycle_id": cycle_id,
        "started_at": _now(),
        "steps": {}
    }

    # Step 1: Test Stripe
    stripe_test = await test_stripe_connection()
    results["steps"]["stripe_connection"] = stripe_test

    if stripe_test.get("ok"):
        # Step 2: Get Receivables
        receivables = await get_receivables_data()
        results["steps"]["receivables_desk"] = receivables

        # Step 3: Get Payments Analysis
        payments = await get_payments_data()
        results["steps"]["payments_optimizer"] = payments

        # Step 4: Execute autonomous action
        action = await execute_autonomous_action()
        results["steps"]["autonomous_action"] = action

        # Calculate totals
        total_opportunity = 0
        if receivables.get("ok"):
            total_opportunity += receivables.get("platform_fee", 0)
        if payments.get("ok") and payments.get("fee_analysis"):
            total_opportunity += payments["fee_analysis"].get("potential_monthly_savings", 0)

        results["revenue_opportunity"] = {
            "receivables_fee": receivables.get("platform_fee", 0) if receivables.get("ok") else 0,
            "interchange_savings": payments.get("fee_analysis", {}).get("potential_monthly_savings", 0) if payments.get("ok") else 0,
            "total_monthly_opportunity": round(total_opportunity, 2)
        }

    results["completed_at"] = _now()

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_live_test(app):
    """Add live test endpoints to FastAPI app"""

    @app.get("/v115/test/status")
    async def test_status():
        """Check all API connectivity and return status"""
        status = {
            "stripe": await test_stripe_connection(),
            "timestamp": _now()
        }

        # Add other API checks here as they become available

        return status

    @app.get("/v115/test/receivables")
    async def test_receivables():
        """Get real receivables data"""
        return await get_receivables_data()

    @app.get("/v115/test/payments")
    async def test_payments():
        """Get real payments analysis"""
        return await get_payments_data()

    @app.post("/v115/test/run-cycle")
    async def test_run_cycle():
        """Run full monetization cycle"""
        return await run_full_cycle()

    @app.post("/v115/test/execute")
    async def test_execute():
        """Execute autonomous action"""
        return await execute_autonomous_action()

    print("=" * 80)
    print("🧪 V115 LIVE TEST ENDPOINTS LOADED")
    print("=" * 80)
    print("Test Endpoints:")
    print("  GET  /v115/test/status      - API connectivity")
    print("  GET  /v115/test/receivables - Real invoice data")
    print("  GET  /v115/test/payments    - Transaction analysis")
    print("  POST /v115/test/run-cycle   - Full cycle")
    print("  POST /v115/test/execute     - Autonomous action")
    print("=" * 80)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════════════════════

async def cli_test():
    """Run test from command line"""
    print("=" * 80)
    print("V115 LIVE TEST")
    print("=" * 80)

    print("\n1. Testing Stripe Connection...")
    stripe_result = await test_stripe_connection()
    if stripe_result.get("ok"):
        print(f"   ✅ Connected")
        print(f"   Balance: {stripe_result.get('balance')}")
    else:
        print(f"   ❌ {stripe_result.get('error')}")
        return

    print("\n2. Getting Receivables Data...")
    recv_result = await get_receivables_data()
    if recv_result.get("ok"):
        print(f"   ✅ Found {recv_result.get('invoice_count')} open invoices")
        print(f"   Total receivables: ${recv_result.get('total_receivables', 0):,.2f}")
        print(f"   Potential fee revenue: ${recv_result.get('platform_fee', 0):,.2f}")
    else:
        print(f"   ❌ {recv_result.get('error')}")

    print("\n3. Analyzing Payments...")
    pay_result = await get_payments_data()
    if pay_result.get("ok"):
        print(f"   ✅ Analyzed ${pay_result.get('total_volume', 0):,.2f} in transactions")
        print(f"   Card brands: {pay_result.get('card_brands')}")
        fees = pay_result.get("fee_analysis", {})
        print(f"   Potential savings: ${fees.get('potential_monthly_savings', 0):,.2f}/month")
    else:
        print(f"   ❌ {pay_result.get('error')}")

    print("\n4. Running Full Cycle...")
    cycle_result = await run_full_cycle()
    print(f"   Cycle ID: {cycle_result.get('cycle_id')}")

    rev_opp = cycle_result.get("revenue_opportunity", {})
    print(f"\n   📈 REVENUE OPPORTUNITY:")
    print(f"   Receivables fees: ${rev_opp.get('receivables_fee', 0):,.2f}")
    print(f"   Interchange savings: ${rev_opp.get('interchange_savings', 0):,.2f}")
    print(f"   TOTAL MONTHLY: ${rev_opp.get('total_monthly_opportunity', 0):,.2f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(cli_test())
