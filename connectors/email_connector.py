"""
Email Connector
===============

SMTP/API email delivery via Postmark, SendGrid, or SMTP.
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


class EmailConnector(Connector):
    """
    Email delivery connector supporting multiple providers.

    Providers:
    - Postmark (default)
    - SendGrid
    - Generic SMTP (via API gateway)

    Capabilities:
    - send_email: Send single email
    - send_email_template: Send templated email
    - send_email_batch: Send batch emails
    """

    name = "email"
    capabilities = [
        "send_email",
        "send_email_nudge",
        "send_email_blast",
        "send_email_template",
        "send_email_batch"
    ]
    auth_schemes = [AuthScheme.API_KEY]

    avg_latency_ms = 800.0
    success_rate = 0.99
    max_rps = 10.0

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        config = config or {}

        self._provider = config.get("provider", "postmark")
        self._api_key = config.get("api_key") or os.getenv("POSTMARK_API_KEY") or os.getenv("SENDGRID_API_KEY")
        self._from_email = config.get("from_email", "noreply@aigentsy.com")
        self._from_name = config.get("from_name", "AiGentsy")

    async def health(self) -> ConnectorHealth:
        if not self._api_key:
            return ConnectorHealth(healthy=False, latency_ms=0, error="api_key_not_configured")
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

        if not self._api_key:
            return ConnectorResult(ok=False, error="api_key_not_configured", retryable=False)

        start = time.time()

        to = params.get("to")
        subject = params.get("subject", "Message from AiGentsy")
        body = params.get("body") or params.get("text") or params.get("html", "")
        html_body = params.get("html")

        if not to:
            return ConnectorResult(ok=False, error="to_required", retryable=False)

        try:
            if self._provider == "postmark":
                result = await self._send_postmark(to, subject, body, html_body, idempotency_key, timeout)
            elif self._provider == "sendgrid":
                result = await self._send_sendgrid(to, subject, body, html_body, idempotency_key, timeout)
            else:
                result = await self._send_postmark(to, subject, body, html_body, idempotency_key, timeout)

            latency = (time.time() - start) * 1000
            self._record_call(result.ok, latency)
            result.latency_ms = latency
            return result

        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record_call(False, latency)
            return ConnectorResult(ok=False, error=str(e), latency_ms=latency, retryable=True)

    async def _send_postmark(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str],
        idempotency_key: Optional[str],
        timeout: int
    ) -> ConnectorResult:
        """Send via Postmark API"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self._api_key
        }

        payload = {
            "From": f"{self._from_name} <{self._from_email}>",
            "To": to,
            "Subject": subject,
            "TextBody": body
        }

        if html_body:
            payload["HtmlBody"] = html_body

        if idempotency_key:
            payload["Tag"] = idempotency_key[:50]

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                "https://api.postmarkapp.com/email",
                json=payload,
                headers=headers
            )

            if r.is_success:
                data = r.json()
                return ConnectorResult(
                    ok=True,
                    data={"message_id": data.get("MessageID"), "to": to},
                    proofs=[{
                        "type": "email_sent",
                        "message_id": data.get("MessageID"),
                        "to": to,
                        "provider": "postmark",
                        "timestamp": time.time()
                    }],
                    idempotency_key=idempotency_key
                )
            else:
                return ConnectorResult(
                    ok=False,
                    error=f"postmark_error_{r.status_code}",
                    data={"response": r.text[:500]},
                    retryable=r.status_code >= 500
                )

    async def _send_sendgrid(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str],
        idempotency_key: Optional[str],
        timeout: int
    ) -> ConnectorResult:
        """Send via SendGrid API"""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        content = [{"type": "text/plain", "value": body}]
        if html_body:
            content.append({"type": "text/html", "value": html_body})

        payload = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": self._from_email, "name": self._from_name},
            "subject": subject,
            "content": content
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers=headers
            )

            if r.status_code in (200, 202):
                message_id = r.headers.get("X-Message-Id", "")
                return ConnectorResult(
                    ok=True,
                    data={"message_id": message_id, "to": to},
                    proofs=[{
                        "type": "email_sent",
                        "message_id": message_id,
                        "to": to,
                        "provider": "sendgrid",
                        "timestamp": time.time()
                    }],
                    idempotency_key=idempotency_key
                )
            else:
                return ConnectorResult(
                    ok=False,
                    error=f"sendgrid_error_{r.status_code}",
                    retryable=r.status_code >= 500
                )

    async def cost_estimate(self, action: str, params: Dict[str, Any]) -> CostEstimate:
        # Postmark: ~$1.25 per 1000 emails = $0.00125 each
        # SendGrid: ~$0.50 per 1000 emails = $0.0005 each
        return CostEstimate(
            estimated_usd=0.001,
            model="per_call",
            breakdown={"email_delivery": 0.001}
        )
