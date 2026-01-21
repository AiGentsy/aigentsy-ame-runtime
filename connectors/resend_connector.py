"""
Resend Email Connector
======================

Email delivery via Resend API.
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


class ResendConnector(Connector):
    """
    Resend email connector - modern email API.

    Capabilities:
    - send_email: Send single email
    - send_email_batch: Send batch emails
    - send_email_template: Send templated email
    """

    name = "resend"
    capabilities = [
        "send_email",
        "send_email_nudge",
        "send_email_blast",
        "send_email_template",
        "send_email_batch",
        "resend_send"
    ]
    auth_schemes = [AuthScheme.API_KEY]

    avg_latency_ms = 500.0
    success_rate = 0.99
    max_rps = 10.0

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        config = config or {}

        self._api_key = config.get("api_key") or os.getenv("RESEND_API_KEY")
        self._from_email = config.get("from_email") or os.getenv("RESEND_FROM_EMAIL", "noreply@aigentsy.com")
        self._from_name = config.get("from_name", "AiGentsy")

    async def health(self) -> ConnectorHealth:
        if not self._api_key:
            return ConnectorHealth(healthy=False, latency_ms=0, error="resend_api_key_not_configured")
        if not HTTPX_AVAILABLE:
            return ConnectorHealth(healthy=False, latency_ms=0, error="httpx_not_installed")

        # Quick API check
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    "https://api.resend.com/domains",
                    headers={"Authorization": f"Bearer {self._api_key}"}
                )
                latency = (time.time() - start) * 1000
                return ConnectorHealth(
                    healthy=r.status_code in (200, 401),  # 401 means key exists but may need more perms
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
        timeout: int = 30
    ) -> ConnectorResult:
        if not HTTPX_AVAILABLE:
            return ConnectorResult(ok=False, error="httpx_not_installed", retryable=False)

        if not self._api_key:
            return ConnectorResult(ok=False, error="resend_api_key_not_configured", retryable=False)

        start = time.time()

        to = params.get("to")
        subject = params.get("subject", "Message from AiGentsy")
        body = params.get("body") or params.get("text", "")
        html = params.get("html")
        from_email = params.get("from") or f"{self._from_name} <{self._from_email}>"
        reply_to = params.get("reply_to")

        if not to:
            return ConnectorResult(ok=False, error="to_required", retryable=False)

        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }

            if idempotency_key:
                headers["Idempotency-Key"] = idempotency_key

            payload = {
                "from": from_email,
                "to": [to] if isinstance(to, str) else to,
                "subject": subject,
            }

            if html:
                payload["html"] = html
            if body:
                payload["text"] = body
            if reply_to:
                payload["reply_to"] = reply_to

            # Add tags for tracking
            if params.get("tags"):
                payload["tags"] = params["tags"]

            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers=headers
                )

                latency = (time.time() - start) * 1000
                self._record_call(r.is_success, latency)

                if r.is_success:
                    data = r.json()
                    return ConnectorResult(
                        ok=True,
                        data={
                            "message_id": data.get("id"),
                            "to": to
                        },
                        proofs=[{
                            "type": "email_sent",
                            "message_id": data.get("id"),
                            "to": to,
                            "provider": "resend",
                            "timestamp": time.time()
                        }],
                        latency_ms=latency,
                        idempotency_key=idempotency_key
                    )
                else:
                    error_data = {}
                    try:
                        error_data = r.json()
                    except:
                        pass

                    return ConnectorResult(
                        ok=False,
                        error=f"resend_error_{r.status_code}",
                        error_code=str(r.status_code),
                        data={"response": error_data or r.text[:500]},
                        latency_ms=latency,
                        retryable=r.status_code >= 500
                    )

        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record_call(False, latency)
            return ConnectorResult(ok=False, error=str(e), latency_ms=latency, retryable=True)

    async def cost_estimate(self, action: str, params: Dict[str, Any]) -> CostEstimate:
        # Resend: ~$0.80 per 1000 emails (after free tier)
        return CostEstimate(
            estimated_usd=0.0008,
            model="per_call",
            breakdown={"email_delivery": 0.0008}
        )
