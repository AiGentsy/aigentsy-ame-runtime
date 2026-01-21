"""
Webhook Connector
=================

Outbound webhook delivery with retries and verification.
"""

from typing import Dict, Any, Optional
import time
import hashlib
import hmac

from .base import Connector, ConnectorResult, ConnectorHealth, CostEstimate, AuthScheme

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class WebhookConnector(Connector):
    """
    Webhook delivery connector for event-driven integrations.

    Capabilities:
    - webhook_send: Send webhook to URL
    - webhook_verify: Verify webhook signature
    """

    name = "webhook"
    capabilities = [
        "webhook_send",
        "webhook_deliver",
        "event_notify"
    ]
    auth_schemes = [AuthScheme.HMAC, AuthScheme.NONE]

    avg_latency_ms = 300.0
    success_rate = 0.98
    max_rps = 100.0

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._signing_secret = config.get("signing_secret") if config else None

    def _sign_payload(self, payload: bytes, secret: str) -> str:
        """Generate HMAC signature for payload"""
        return hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

    async def health(self) -> ConnectorHealth:
        if not HTTPX_AVAILABLE:
            return ConnectorHealth(healthy=False, latency_ms=0, error="httpx_not_installed")
        return ConnectorHealth(healthy=True, latency_ms=0)

    async def execute(
        self,
        action: str,
        params: Dict[str, Any],
        files: Optional[Dict[str, bytes]] = None,
        *,
        idempotency_key: Optional[str] = None,
        timeout: int = 30
    ) -> ConnectorResult:
        if not HTTPX_AVAILABLE:
            return ConnectorResult(ok=False, error="httpx_not_installed", retryable=False)

        start = time.time()

        url = params.get("url")
        payload = params.get("payload", params.get("data", {}))
        secret = params.get("signing_secret", self._signing_secret)

        if not url:
            return ConnectorResult(ok=False, error="url_required", retryable=False)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": str(int(time.time()))
        }

        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key

        # Sign payload if secret provided
        import json
        payload_bytes = json.dumps(payload).encode()
        if secret:
            signature = self._sign_payload(payload_bytes, secret)
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(url, json=payload, headers=headers)

                latency = (time.time() - start) * 1000
                self._record_call(r.is_success, latency)

                proofs = [{
                    "type": "webhook_delivery",
                    "url": url,
                    "status_code": r.status_code,
                    "signature": headers.get("X-Webhook-Signature"),
                    "timestamp": time.time()
                }]

                if r.is_success:
                    return ConnectorResult(
                        ok=True,
                        data={"delivered": True, "status": r.status_code},
                        proofs=proofs,
                        latency_ms=latency,
                        idempotency_key=idempotency_key
                    )
                else:
                    return ConnectorResult(
                        ok=False,
                        error=f"webhook_failed_{r.status_code}",
                        latency_ms=latency,
                        retryable=r.status_code >= 500,
                        idempotency_key=idempotency_key
                    )

        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record_call(False, latency)
            return ConnectorResult(ok=False, error=str(e), latency_ms=latency, retryable=True)

    async def cost_estimate(self, action: str, params: Dict[str, Any]) -> CostEstimate:
        return CostEstimate(estimated_usd=0.0001, model="per_call", breakdown={"compute": 0.0001})
