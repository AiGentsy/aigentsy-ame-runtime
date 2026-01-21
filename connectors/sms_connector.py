"""
SMS Connector
=============

SMS delivery via Twilio or compatible providers.
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


class SMSConnector(Connector):
    """
    SMS delivery connector via Twilio API.

    Capabilities:
    - send_sms: Send SMS message
    - send_sms_nudge: Send cart/follow-up nudge
    """

    name = "sms"
    capabilities = [
        "send_sms",
        "send_sms_nudge",
        "send_text_message"
    ]
    auth_schemes = [AuthScheme.BASIC]

    avg_latency_ms = 1200.0
    success_rate = 0.97
    max_rps = 5.0  # Respect rate limits

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        config = config or {}

        self._account_sid = config.get("account_sid") or os.getenv("TWILIO_ACCOUNT_SID")
        self._auth_token = config.get("auth_token") or os.getenv("TWILIO_AUTH_TOKEN")
        self._from_number = config.get("from_number") or os.getenv("TWILIO_FROM_NUMBER")

    async def health(self) -> ConnectorHealth:
        if not all([self._account_sid, self._auth_token, self._from_number]):
            return ConnectorHealth(healthy=False, latency_ms=0, error="twilio_not_configured")
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

        if not all([self._account_sid, self._auth_token, self._from_number]):
            return ConnectorResult(ok=False, error="twilio_not_configured", retryable=False)

        start = time.time()

        to = params.get("to") or params.get("phone")
        body = params.get("body") or params.get("text") or params.get("message", "")
        from_number = params.get("from") or self._from_number

        if not to:
            return ConnectorResult(ok=False, error="to_required", retryable=False)

        if not body:
            return ConnectorResult(ok=False, error="body_required", retryable=False)

        # Normalize phone number
        to = to.strip()
        if not to.startswith("+"):
            to = f"+1{to}"  # Assume US if no country code

        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self._account_sid}/Messages.json"

            data = {
                "To": to,
                "From": from_number,
                "Body": body[:1600]  # SMS limit
            }

            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(
                    url,
                    data=data,
                    auth=(self._account_sid, self._auth_token)
                )

                latency = (time.time() - start) * 1000
                self._record_call(r.is_success, latency)

                if r.is_success:
                    response = r.json()
                    return ConnectorResult(
                        ok=True,
                        data={
                            "message_sid": response.get("sid"),
                            "to": to,
                            "status": response.get("status")
                        },
                        proofs=[{
                            "type": "sms_sent",
                            "message_sid": response.get("sid"),
                            "to": to,
                            "provider": "twilio",
                            "timestamp": time.time()
                        }],
                        latency_ms=latency,
                        idempotency_key=idempotency_key
                    )
                else:
                    return ConnectorResult(
                        ok=False,
                        error=f"twilio_error_{r.status_code}",
                        data={"response": r.text[:500]},
                        latency_ms=latency,
                        retryable=r.status_code >= 500
                    )

        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record_call(False, latency)
            return ConnectorResult(ok=False, error=str(e), latency_ms=latency, retryable=True)

    async def cost_estimate(self, action: str, params: Dict[str, Any]) -> CostEstimate:
        # Twilio: ~$0.0079 per SMS (US)
        return CostEstimate(
            estimated_usd=0.008,
            model="per_call",
            breakdown={"sms_delivery": 0.008}
        )
