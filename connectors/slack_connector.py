"""
Slack Connector
===============

Slack messaging and workflow automation.
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


class SlackConnector(Connector):
    """
    Slack integration connector.

    Capabilities:
    - send_slack_message: Send message to channel/DM
    - send_slack_dm: Send direct message
    - post_to_channel: Post to Slack channel
    """

    name = "slack"
    capabilities = [
        "send_slack_message",
        "send_slack_dm",
        "post_to_channel",
        "slack_notify"
    ]
    auth_schemes = [AuthScheme.BEARER, AuthScheme.API_KEY]

    avg_latency_ms = 400.0
    success_rate = 0.99
    max_rps = 20.0

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        config = config or {}
        self._token = config.get("token") or os.getenv("SLACK_BOT_TOKEN")
        self._webhook_url = config.get("webhook_url") or os.getenv("SLACK_WEBHOOK_URL")

    async def health(self) -> ConnectorHealth:
        if not (self._token or self._webhook_url):
            return ConnectorHealth(healthy=False, latency_ms=0, error="slack_not_configured")
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

        channel = params.get("channel")
        text = params.get("text") or params.get("message", "")
        blocks = params.get("blocks")
        webhook_url = params.get("webhook_url", self._webhook_url)

        if not text and not blocks:
            return ConnectorResult(ok=False, error="text_or_blocks_required", retryable=False)

        try:
            # Use webhook if available, otherwise API
            if webhook_url:
                result = await self._send_webhook(webhook_url, text, blocks, timeout)
            elif self._token and channel:
                result = await self._send_api(channel, text, blocks, timeout)
            else:
                return ConnectorResult(ok=False, error="channel_or_webhook_required", retryable=False)

            latency = (time.time() - start) * 1000
            self._record_call(result.ok, latency)
            result.latency_ms = latency
            result.idempotency_key = idempotency_key
            return result

        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record_call(False, latency)
            return ConnectorResult(ok=False, error=str(e), latency_ms=latency, retryable=True)

    async def _send_webhook(
        self,
        webhook_url: str,
        text: str,
        blocks: Optional[list],
        timeout: int
    ) -> ConnectorResult:
        """Send via incoming webhook"""
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(webhook_url, json=payload)

            if r.is_success:
                return ConnectorResult(
                    ok=True,
                    data={"delivered": True},
                    proofs=[{
                        "type": "slack_webhook",
                        "status": "delivered",
                        "timestamp": time.time()
                    }]
                )
            else:
                return ConnectorResult(
                    ok=False,
                    error=f"slack_webhook_error_{r.status_code}",
                    retryable=r.status_code >= 500
                )

    async def _send_api(
        self,
        channel: str,
        text: str,
        blocks: Optional[list],
        timeout: int
    ) -> ConnectorResult:
        """Send via Slack API"""
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

        payload = {
            "channel": channel,
            "text": text
        }
        if blocks:
            payload["blocks"] = blocks

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                headers=headers
            )

            data = r.json()
            if data.get("ok"):
                return ConnectorResult(
                    ok=True,
                    data={
                        "channel": data.get("channel"),
                        "ts": data.get("ts"),
                        "message": data.get("message", {})
                    },
                    proofs=[{
                        "type": "slack_message",
                        "channel": data.get("channel"),
                        "ts": data.get("ts"),
                        "timestamp": time.time()
                    }]
                )
            else:
                return ConnectorResult(
                    ok=False,
                    error=data.get("error", "unknown"),
                    retryable=data.get("error") in ("rate_limited", "service_unavailable")
                )

    async def cost_estimate(self, action: str, params: Dict[str, Any]) -> CostEstimate:
        return CostEstimate(
            estimated_usd=0.0001,
            model="per_call",
            breakdown={"api_call": 0.0001}
        )
