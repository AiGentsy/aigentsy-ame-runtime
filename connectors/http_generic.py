"""
HTTP Generic Connector
======================

Universal HTTP/REST API connector for any endpoint.
"""

from typing import Dict, Any, List, Optional
import asyncio
import time
import os

from .base import Connector, ConnectorResult, ConnectorHealth, CostEstimate, AuthScheme

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class HTTPGenericConnector(Connector):
    """
    Generic HTTP connector for REST APIs.

    Capabilities:
    - http_get: GET request
    - http_post: POST request
    - http_put: PUT request
    - http_patch: PATCH request
    - http_delete: DELETE request
    - api_call: Generic API call with method specification
    """

    name = "http_generic"
    capabilities = [
        "http_get",
        "http_post",
        "http_put",
        "http_patch",
        "http_delete",
        "api_call",
        "webhook_send"
    ]
    auth_schemes = [
        AuthScheme.NONE,
        AuthScheme.API_KEY,
        AuthScheme.BEARER,
        AuthScheme.BASIC
    ]

    avg_latency_ms = 500.0
    success_rate = 0.95
    max_rps = 50.0

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._default_headers = config.get("default_headers", {}) if config else {}
        self._default_timeout = config.get("timeout", 30) if config else 30

    async def health(self) -> ConnectorHealth:
        """Check HTTP client health"""
        if not HTTPX_AVAILABLE:
            return ConnectorHealth(
                healthy=False,
                latency_ms=0,
                error="httpx_not_installed"
            )

        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                # Quick connectivity check
                r = await client.get("https://httpbin.org/status/200", timeout=5)
                latency = (time.time() - start) * 1000
                return ConnectorHealth(
                    healthy=r.status_code == 200,
                    latency_ms=latency
                )
        except Exception as e:
            return ConnectorHealth(
                healthy=False,
                latency_ms=(time.time() - start) * 1000,
                error=str(e)
            )

    async def execute(
        self,
        action: str,
        params: Dict[str, Any],
        files: Optional[Dict[str, bytes]] = None,
        *,
        idempotency_key: Optional[str] = None,
        timeout: int = 60
    ) -> ConnectorResult:
        """Execute HTTP request"""
        if not HTTPX_AVAILABLE:
            return ConnectorResult(
                ok=False,
                error="httpx_not_installed",
                retryable=False
            )

        start = time.time()

        # Extract parameters
        url = params.get("url")
        if not url:
            return ConnectorResult(
                ok=False,
                error="url_required",
                retryable=False
            )

        method = params.get("method", "GET")
        if action == "http_get":
            method = "GET"
        elif action == "http_post":
            method = "POST"
        elif action == "http_put":
            method = "PUT"
        elif action == "http_patch":
            method = "PATCH"
        elif action == "http_delete":
            method = "DELETE"

        headers = {**self._default_headers, **(params.get("headers", {}))}
        query_params = params.get("query", {})
        body = params.get("body") or params.get("json") or params.get("data")

        # Add idempotency key header if provided
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
            headers["X-Idempotency-Key"] = idempotency_key

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.upper() in ("POST", "PUT", "PATCH") and body:
                    if isinstance(body, dict):
                        r = await client.request(
                            method, url,
                            headers=headers,
                            params=query_params,
                            json=body
                        )
                    else:
                        r = await client.request(
                            method, url,
                            headers=headers,
                            params=query_params,
                            content=body
                        )
                else:
                    r = await client.request(
                        method, url,
                        headers=headers,
                        params=query_params
                    )

                latency = (time.time() - start) * 1000
                self._record_call(r.is_success, latency)

                # Parse response
                try:
                    response_data = r.json()
                except:
                    response_data = {"text": r.text[:1000]}

                # Generate proofs
                proofs = [
                    {
                        "type": "http_response",
                        "status_code": r.status_code,
                        "url": str(r.url),
                        "response_hash": self._generate_proof_hash(response_data),
                        "timestamp": time.time()
                    }
                ]

                if r.is_success:
                    return ConnectorResult(
                        ok=True,
                        data=response_data,
                        proofs=proofs,
                        latency_ms=latency,
                        idempotency_key=idempotency_key
                    )
                else:
                    return ConnectorResult(
                        ok=False,
                        data=response_data,
                        error=f"http_{r.status_code}",
                        error_code=str(r.status_code),
                        latency_ms=latency,
                        retryable=r.status_code in (429, 500, 502, 503, 504),
                        idempotency_key=idempotency_key
                    )

        except httpx.TimeoutException:
            latency = (time.time() - start) * 1000
            self._record_call(False, latency)
            return ConnectorResult(
                ok=False,
                error="timeout",
                latency_ms=latency,
                retryable=True
            )

        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record_call(False, latency)
            return ConnectorResult(
                ok=False,
                error=str(e),
                latency_ms=latency,
                retryable=True
            )

    async def cost_estimate(
        self,
        action: str,
        params: Dict[str, Any]
    ) -> CostEstimate:
        """HTTP calls are essentially free (compute cost only)"""
        return CostEstimate(
            estimated_usd=0.001,
            model="per_call",
            breakdown={"compute": 0.001}
        )
