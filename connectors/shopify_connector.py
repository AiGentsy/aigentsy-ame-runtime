"""
Shopify Connector
=================

Shopify store automation for products, orders, customers.
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


class ShopifyConnector(Connector):
    """
    Shopify Admin API connector.

    Capabilities:
    - create_product: Create new product
    - update_product: Update existing product
    - create_order: Create draft order
    - get_orders: List orders
    - create_discount_code: Create discount code
    - send_email_nudge: Abandoned cart email
    """

    name = "shopify"
    capabilities = [
        "create_product",
        "update_product",
        "delete_product",
        "get_products",
        "create_order",
        "get_orders",
        "create_customer",
        "get_customers",
        "create_discount_code",
        "create_marketing_event",
        "publish_blog_post",
        "send_email_nudge",
        "shopify.create_product"
    ]
    auth_schemes = [AuthScheme.API_KEY]

    avg_latency_ms = 800.0
    success_rate = 0.98
    max_rps = 4.0  # Shopify rate limits

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        config = config or {}

        self._shop_url = config.get("shop_url") or os.getenv("SHOPIFY_SHOP_URL")
        self._access_token = config.get("access_token") or os.getenv("SHOPIFY_ACCESS_TOKEN")
        self._api_version = config.get("api_version", "2024-01")

    def _get_base_url(self) -> str:
        shop = self._shop_url.replace("https://", "").replace(".myshopify.com", "")
        return f"https://{shop}.myshopify.com/admin/api/{self._api_version}"

    async def health(self) -> ConnectorHealth:
        if not (self._shop_url and self._access_token):
            return ConnectorHealth(healthy=False, latency_ms=0, error="shopify_not_configured")
        if not HTTPX_AVAILABLE:
            return ConnectorHealth(healthy=False, latency_ms=0, error="httpx_not_installed")

        start = time.time()
        try:
            headers = {"X-Shopify-Access-Token": self._access_token}
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self._get_base_url()}/shop.json", headers=headers)
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

        if not (self._shop_url and self._access_token):
            return ConnectorResult(ok=False, error="shopify_not_configured", retryable=False)

        start = time.time()

        try:
            if action in ("create_product", "shopify.create_product"):
                result = await self._create_product(params, idempotency_key, timeout)
            elif action == "update_product":
                result = await self._update_product(params, timeout)
            elif action == "get_products":
                result = await self._get_products(params, timeout)
            elif action == "create_order":
                result = await self._create_order(params, idempotency_key, timeout)
            elif action == "get_orders":
                result = await self._get_orders(params, timeout)
            elif action == "create_discount_code":
                result = await self._create_discount(params, idempotency_key, timeout)
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

    async def _create_product(
        self,
        params: Dict[str, Any],
        idempotency_key: Optional[str],
        timeout: int
    ) -> ConnectorResult:
        """Create a new product"""
        headers = {
            "X-Shopify-Access-Token": self._access_token,
            "Content-Type": "application/json"
        }

        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        product_data = {
            "product": {
                "title": params.get("title", "New Product"),
                "body_html": params.get("description", ""),
                "vendor": params.get("vendor", ""),
                "product_type": params.get("product_type", ""),
                "variants": [{
                    "price": str(params.get("price", "0.00")),
                    "sku": params.get("sku", ""),
                    "inventory_quantity": params.get("inventory", 0)
                }]
            }
        }

        if params.get("images"):
            product_data["product"]["images"] = [{"src": url} for url in params["images"]]

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{self._get_base_url()}/products.json",
                json=product_data,
                headers=headers
            )

            if r.is_success:
                data = r.json()
                product = data.get("product", {})
                return ConnectorResult(
                    ok=True,
                    data={
                        "product_id": product.get("id"),
                        "handle": product.get("handle"),
                        "url": f"{self._shop_url}/products/{product.get('handle')}"
                    },
                    proofs=[{
                        "type": "shopify_product_created",
                        "product_id": product.get("id"),
                        "handle": product.get("handle"),
                        "timestamp": time.time()
                    }]
                )
            else:
                return ConnectorResult(
                    ok=False,
                    error=f"shopify_error_{r.status_code}",
                    data={"response": r.text[:500]},
                    retryable=r.status_code in (429, 500, 502, 503, 504)
                )

    async def _update_product(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """Update existing product"""
        product_id = params.get("product_id")
        if not product_id:
            return ConnectorResult(ok=False, error="product_id_required", retryable=False)

        headers = {
            "X-Shopify-Access-Token": self._access_token,
            "Content-Type": "application/json"
        }

        update_data = {"product": {"id": product_id}}
        for field in ["title", "body_html", "vendor", "product_type"]:
            if field in params:
                update_data["product"][field] = params[field]

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.put(
                f"{self._get_base_url()}/products/{product_id}.json",
                json=update_data,
                headers=headers
            )

            if r.is_success:
                return ConnectorResult(
                    ok=True,
                    data=r.json().get("product", {}),
                    proofs=[{"type": "shopify_product_updated", "product_id": product_id, "timestamp": time.time()}]
                )
            return ConnectorResult(ok=False, error=f"shopify_error_{r.status_code}", retryable=r.status_code >= 500)

    async def _get_products(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """List products"""
        headers = {"X-Shopify-Access-Token": self._access_token}
        query = {"limit": params.get("limit", 50)}

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(f"{self._get_base_url()}/products.json", headers=headers, params=query)

            if r.is_success:
                return ConnectorResult(ok=True, data=r.json(), proofs=[])
            return ConnectorResult(ok=False, error=f"shopify_error_{r.status_code}", retryable=r.status_code >= 500)

    async def _create_order(
        self,
        params: Dict[str, Any],
        idempotency_key: Optional[str],
        timeout: int
    ) -> ConnectorResult:
        """Create draft order"""
        headers = {
            "X-Shopify-Access-Token": self._access_token,
            "Content-Type": "application/json"
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        order_data = {
            "draft_order": {
                "line_items": params.get("line_items", []),
                "customer": params.get("customer", {}),
                "use_customer_default_address": True
            }
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{self._get_base_url()}/draft_orders.json",
                json=order_data,
                headers=headers
            )

            if r.is_success:
                data = r.json().get("draft_order", {})
                return ConnectorResult(
                    ok=True,
                    data={"order_id": data.get("id"), "invoice_url": data.get("invoice_url")},
                    proofs=[{"type": "shopify_order_created", "order_id": data.get("id"), "timestamp": time.time()}]
                )
            return ConnectorResult(ok=False, error=f"shopify_error_{r.status_code}", retryable=r.status_code >= 500)

    async def _get_orders(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """List orders"""
        headers = {"X-Shopify-Access-Token": self._access_token}
        query = {"limit": params.get("limit", 50), "status": params.get("status", "any")}

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(f"{self._get_base_url()}/orders.json", headers=headers, params=query)

            if r.is_success:
                return ConnectorResult(ok=True, data=r.json(), proofs=[])
            return ConnectorResult(ok=False, error=f"shopify_error_{r.status_code}", retryable=r.status_code >= 500)

    async def _create_discount(
        self,
        params: Dict[str, Any],
        idempotency_key: Optional[str],
        timeout: int
    ) -> ConnectorResult:
        """Create discount code"""
        headers = {
            "X-Shopify-Access-Token": self._access_token,
            "Content-Type": "application/json"
        }

        discount_data = {
            "price_rule": {
                "title": params.get("title", "Discount"),
                "target_type": "line_item",
                "target_selection": "all",
                "allocation_method": "across",
                "value_type": "percentage",
                "value": str(-abs(params.get("amount_pct", 10))),
                "customer_selection": "all",
                "starts_at": params.get("starts_at", time.strftime("%Y-%m-%dT%H:%M:%SZ"))
            }
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{self._get_base_url()}/price_rules.json",
                json=discount_data,
                headers=headers
            )

            if r.is_success:
                rule = r.json().get("price_rule", {})
                return ConnectorResult(
                    ok=True,
                    data={"price_rule_id": rule.get("id"), "discount_pct": params.get("amount_pct", 10)},
                    proofs=[{"type": "shopify_discount_created", "rule_id": rule.get("id"), "timestamp": time.time()}]
                )
            return ConnectorResult(ok=False, error=f"shopify_error_{r.status_code}", retryable=r.status_code >= 500)

    async def cost_estimate(self, action: str, params: Dict[str, Any]) -> CostEstimate:
        return CostEstimate(
            estimated_usd=0.002,
            model="per_call",
            breakdown={"api_call": 0.002}
        )
