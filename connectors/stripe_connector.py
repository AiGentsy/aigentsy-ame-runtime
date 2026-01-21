"""
Stripe Connector
================

Stripe payments, invoices, and subscriptions.
"""

from typing import Dict, Any, Optional
import time
import os

from .base import Connector, ConnectorResult, ConnectorHealth, CostEstimate, AuthScheme

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class StripeConnector(Connector):
    """
    Stripe API connector for payments and billing.

    Capabilities:
    - create_payment_link: Create payment link
    - create_invoice: Create and send invoice
    - create_customer: Create customer
    - charge: Create charge/payment intent
    - create_subscription: Create subscription
    - get_balance: Get account balance
    """

    name = "stripe"
    capabilities = [
        "create_payment_link",
        "create_invoice",
        "send_invoice",
        "create_customer",
        "charge",
        "create_payment_intent",
        "create_subscription",
        "get_balance",
        "get_payouts",
        "stripe_collect"
    ]
    auth_schemes = [AuthScheme.API_KEY]

    avg_latency_ms = 600.0
    success_rate = 0.99
    max_rps = 25.0

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        config = config or {}

        self._secret_key = config.get("secret_key") or os.getenv("STRIPE_SECRET_KEY")
        self._api_version = config.get("api_version", "2023-10-16")

    async def health(self) -> ConnectorHealth:
        if not self._secret_key:
            return ConnectorHealth(healthy=False, latency_ms=0, error="stripe_not_configured")
        if not HTTPX_AVAILABLE:
            return ConnectorHealth(healthy=False, latency_ms=0, error="httpx_not_installed")

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    "https://api.stripe.com/v1/balance",
                    auth=(self._secret_key, "")
                )
                latency = (time.time() - start) * 1000
                return ConnectorHealth(
                    healthy=r.is_success,
                    latency_ms=latency,
                    error=None if r.is_success else f"status_{r.status_code}"
                )
        except Exception as e:
            return ConnectorHealth(healthy=False, latency_ms=0, error=str(e))

    async def execute(
        self,
        action: str,
        params: Dict[str, Any],
        files: Optional[Dict[str, bytes]] = None,
        *,
        idempotency_key: Optional[str] = None,
        timeout: int = 60
    ) -> ConnectorResult:
        if not HTTPX_AVAILABLE:
            return ConnectorResult(ok=False, error="httpx_not_installed", retryable=False)

        if not self._secret_key:
            return ConnectorResult(ok=False, error="stripe_not_configured", retryable=False)

        start = time.time()

        try:
            if action == "create_payment_link":
                result = await self._create_payment_link(params, idempotency_key, timeout)
            elif action in ("create_invoice", "send_invoice"):
                result = await self._create_invoice(params, idempotency_key, timeout)
            elif action == "create_customer":
                result = await self._create_customer(params, idempotency_key, timeout)
            elif action in ("charge", "create_payment_intent"):
                result = await self._create_payment_intent(params, idempotency_key, timeout)
            elif action == "get_balance":
                result = await self._get_balance(timeout)
            else:
                result = ConnectorResult(ok=False, error=f"unsupported_action:{action}", retryable=False)

            latency = (time.time() - start) * 1000
            self._record_call(result.ok, latency)
            result.latency_ms = latency
            result.idempotency_key = idempotency_key
            return result

        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record_call(False, latency)
            return ConnectorResult(ok=False, error=str(e), latency_ms=latency, retryable=True)

    async def _create_payment_link(
        self,
        params: Dict[str, Any],
        idempotency_key: Optional[str],
        timeout: int
    ) -> ConnectorResult:
        """Create a Stripe payment link"""
        headers = {"Stripe-Version": self._api_version}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        # First create a price if needed
        amount = int(float(params.get("amount", 0)) * 100)  # Convert to cents
        currency = params.get("currency", "usd").lower()
        description = params.get("description", "Payment")

        async with httpx.AsyncClient(timeout=timeout) as client:
            # Create a price
            price_data = {
                "unit_amount": amount,
                "currency": currency,
                "product_data[name]": description
            }

            r = await client.post(
                "https://api.stripe.com/v1/prices",
                data=price_data,
                auth=(self._secret_key, ""),
                headers=headers
            )

            if not r.is_success:
                return ConnectorResult(
                    ok=False,
                    error=f"stripe_price_error_{r.status_code}",
                    data={"response": r.text[:500]},
                    retryable=r.status_code >= 500
                )

            price_id = r.json().get("id")

            # Create payment link
            link_data = {
                "line_items[0][price]": price_id,
                "line_items[0][quantity]": 1
            }

            if params.get("metadata"):
                for k, v in params["metadata"].items():
                    link_data[f"metadata[{k}]"] = str(v)

            r = await client.post(
                "https://api.stripe.com/v1/payment_links",
                data=link_data,
                auth=(self._secret_key, ""),
                headers=headers
            )

            if r.is_success:
                data = r.json()
                return ConnectorResult(
                    ok=True,
                    data={
                        "payment_link_id": data.get("id"),
                        "url": data.get("url"),
                        "amount": amount / 100,
                        "currency": currency
                    },
                    proofs=[{
                        "type": "stripe_payment_link",
                        "link_id": data.get("id"),
                        "url": data.get("url"),
                        "amount_cents": amount,
                        "timestamp": time.time()
                    }]
                )
            else:
                return ConnectorResult(
                    ok=False,
                    error=f"stripe_link_error_{r.status_code}",
                    data={"response": r.text[:500]},
                    retryable=r.status_code >= 500
                )

    async def _create_invoice(
        self,
        params: Dict[str, Any],
        idempotency_key: Optional[str],
        timeout: int
    ) -> ConnectorResult:
        """Create and optionally send an invoice"""
        headers = {"Stripe-Version": self._api_version}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        customer_id = params.get("customer_id")
        amount = int(float(params.get("amount", 0)) * 100)
        description = params.get("description", "Invoice")

        async with httpx.AsyncClient(timeout=timeout) as client:
            # Create invoice
            invoice_data = {
                "customer": customer_id,
                "auto_advance": str(params.get("auto_send", True)).lower(),
                "collection_method": "send_invoice",
                "days_until_due": params.get("days_due", 30)
            }

            r = await client.post(
                "https://api.stripe.com/v1/invoices",
                data=invoice_data,
                auth=(self._secret_key, ""),
                headers=headers
            )

            if not r.is_success:
                return ConnectorResult(
                    ok=False,
                    error=f"stripe_invoice_error_{r.status_code}",
                    retryable=r.status_code >= 500
                )

            invoice = r.json()
            invoice_id = invoice.get("id")

            # Add line item
            item_data = {
                "invoice": invoice_id,
                "amount": amount,
                "currency": params.get("currency", "usd"),
                "description": description
            }

            await client.post(
                "https://api.stripe.com/v1/invoiceitems",
                data=item_data,
                auth=(self._secret_key, "")
            )

            # Finalize invoice
            await client.post(
                f"https://api.stripe.com/v1/invoices/{invoice_id}/finalize",
                auth=(self._secret_key, "")
            )

            # Send invoice if requested
            if params.get("send", True):
                await client.post(
                    f"https://api.stripe.com/v1/invoices/{invoice_id}/send",
                    auth=(self._secret_key, "")
                )

            return ConnectorResult(
                ok=True,
                data={
                    "invoice_id": invoice_id,
                    "hosted_invoice_url": invoice.get("hosted_invoice_url"),
                    "amount": amount / 100
                },
                proofs=[{
                    "type": "stripe_invoice",
                    "invoice_id": invoice_id,
                    "amount_cents": amount,
                    "timestamp": time.time()
                }]
            )

    async def _create_customer(
        self,
        params: Dict[str, Any],
        idempotency_key: Optional[str],
        timeout: int
    ) -> ConnectorResult:
        """Create a Stripe customer"""
        headers = {"Stripe-Version": self._api_version}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        customer_data = {
            "email": params.get("email"),
            "name": params.get("name", ""),
            "description": params.get("description", "")
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                "https://api.stripe.com/v1/customers",
                data=customer_data,
                auth=(self._secret_key, ""),
                headers=headers
            )

            if r.is_success:
                data = r.json()
                return ConnectorResult(
                    ok=True,
                    data={"customer_id": data.get("id"), "email": data.get("email")},
                    proofs=[{"type": "stripe_customer", "customer_id": data.get("id"), "timestamp": time.time()}]
                )
            return ConnectorResult(ok=False, error=f"stripe_error_{r.status_code}", retryable=r.status_code >= 500)

    async def _create_payment_intent(
        self,
        params: Dict[str, Any],
        idempotency_key: Optional[str],
        timeout: int
    ) -> ConnectorResult:
        """Create a payment intent"""
        headers = {"Stripe-Version": self._api_version}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        amount = int(float(params.get("amount", 0)) * 100)
        intent_data = {
            "amount": amount,
            "currency": params.get("currency", "usd"),
            "automatic_payment_methods[enabled]": "true"
        }

        if params.get("customer_id"):
            intent_data["customer"] = params["customer_id"]

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                "https://api.stripe.com/v1/payment_intents",
                data=intent_data,
                auth=(self._secret_key, ""),
                headers=headers
            )

            if r.is_success:
                data = r.json()
                return ConnectorResult(
                    ok=True,
                    data={
                        "payment_intent_id": data.get("id"),
                        "client_secret": data.get("client_secret"),
                        "status": data.get("status")
                    },
                    proofs=[{
                        "type": "stripe_payment_intent",
                        "intent_id": data.get("id"),
                        "amount_cents": amount,
                        "timestamp": time.time()
                    }]
                )
            return ConnectorResult(ok=False, error=f"stripe_error_{r.status_code}", retryable=r.status_code >= 500)

    async def _get_balance(self, timeout: int) -> ConnectorResult:
        """Get Stripe account balance"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(
                "https://api.stripe.com/v1/balance",
                auth=(self._secret_key, "")
            )

            if r.is_success:
                data = r.json()
                available = data.get("available", [])
                pending = data.get("pending", [])

                return ConnectorResult(
                    ok=True,
                    data={
                        "available": available,
                        "pending": pending,
                        "total_available_usd": sum(
                            b.get("amount", 0) / 100 for b in available if b.get("currency") == "usd"
                        )
                    },
                    proofs=[]
                )
            return ConnectorResult(ok=False, error=f"stripe_error_{r.status_code}", retryable=r.status_code >= 500)

    async def cost_estimate(self, action: str, params: Dict[str, Any]) -> CostEstimate:
        # Stripe fees: 2.9% + $0.30 for payments
        amount = float(params.get("amount", 0))
        if action in ("charge", "create_payment_intent", "create_payment_link"):
            fee = (amount * 0.029) + 0.30
        else:
            fee = 0.002  # API call cost

        return CostEstimate(
            estimated_usd=fee,
            model="percentage_plus_fixed" if fee > 0.01 else "per_call",
            breakdown={"stripe_fee": fee}
        )
