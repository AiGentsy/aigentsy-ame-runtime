"""
Airtable/Notion Connector
=========================

Database/workspace operations for Airtable and Notion.
"""

from typing import Dict, Any, Optional, List
import time
import os

from .base import Connector, ConnectorResult, ConnectorHealth, CostEstimate, AuthScheme

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class AirtableConnector(Connector):
    """
    Airtable API connector for database operations.

    Capabilities:
    - create_record: Create new record
    - update_record: Update existing record
    - delete_record: Delete record
    - list_records: List/query records
    - get_record: Get single record
    """

    name = "airtable"
    capabilities = [
        "create_record",
        "update_record",
        "delete_record",
        "list_records",
        "get_record",
        "upsert_record",
        "airtable_create",
        "airtable_update",
        "notion_create_page"
    ]
    auth_schemes = [AuthScheme.BEARER]

    avg_latency_ms = 600.0
    success_rate = 0.98
    max_rps = 5.0  # Airtable rate limit

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        config = config or {}

        self._api_key = config.get("api_key") or os.getenv("AIRTABLE_API_KEY")
        self._base_id = config.get("base_id") or os.getenv("AIRTABLE_BASE_ID")

    async def health(self) -> ConnectorHealth:
        if not self._api_key:
            return ConnectorHealth(healthy=False, latency_ms=0, error="airtable_not_configured")
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
            return ConnectorResult(ok=False, error="airtable_not_configured", retryable=False)

        start = time.time()

        try:
            if action in ("create_record", "airtable_create"):
                result = await self._create_record(params, idempotency_key, timeout)
            elif action in ("update_record", "airtable_update"):
                result = await self._update_record(params, timeout)
            elif action == "delete_record":
                result = await self._delete_record(params, timeout)
            elif action == "list_records":
                result = await self._list_records(params, timeout)
            elif action == "get_record":
                result = await self._get_record(params, timeout)
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

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

    def _get_base_url(self, base_id: Optional[str] = None) -> str:
        base = base_id or self._base_id
        return f"https://api.airtable.com/v0/{base}"

    async def _create_record(
        self,
        params: Dict[str, Any],
        idempotency_key: Optional[str],
        timeout: int
    ) -> ConnectorResult:
        """Create a new record"""
        table = params.get("table")
        fields = params.get("fields", {})
        base_id = params.get("base_id", self._base_id)

        if not table:
            return ConnectorResult(ok=False, error="table_required", retryable=False)

        payload = {"fields": fields}

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{self._get_base_url(base_id)}/{table}",
                json=payload,
                headers=self._get_headers()
            )

            if r.is_success:
                data = r.json()
                return ConnectorResult(
                    ok=True,
                    data={
                        "record_id": data.get("id"),
                        "fields": data.get("fields"),
                        "created_time": data.get("createdTime")
                    },
                    proofs=[{
                        "type": "airtable_record_created",
                        "record_id": data.get("id"),
                        "table": table,
                        "timestamp": time.time()
                    }]
                )
            else:
                return ConnectorResult(
                    ok=False,
                    error=f"airtable_error_{r.status_code}",
                    data={"response": r.text[:500]},
                    retryable=r.status_code in (429, 500, 502, 503)
                )

    async def _update_record(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """Update existing record"""
        table = params.get("table")
        record_id = params.get("record_id")
        fields = params.get("fields", {})
        base_id = params.get("base_id", self._base_id)

        if not table or not record_id:
            return ConnectorResult(ok=False, error="table_and_record_id_required", retryable=False)

        payload = {"fields": fields}

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.patch(
                f"{self._get_base_url(base_id)}/{table}/{record_id}",
                json=payload,
                headers=self._get_headers()
            )

            if r.is_success:
                data = r.json()
                return ConnectorResult(
                    ok=True,
                    data={"record_id": data.get("id"), "fields": data.get("fields")},
                    proofs=[{"type": "airtable_record_updated", "record_id": record_id, "timestamp": time.time()}]
                )
            return ConnectorResult(ok=False, error=f"airtable_error_{r.status_code}", retryable=r.status_code >= 500)

    async def _delete_record(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """Delete a record"""
        table = params.get("table")
        record_id = params.get("record_id")
        base_id = params.get("base_id", self._base_id)

        if not table or not record_id:
            return ConnectorResult(ok=False, error="table_and_record_id_required", retryable=False)

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.delete(
                f"{self._get_base_url(base_id)}/{table}/{record_id}",
                headers=self._get_headers()
            )

            if r.is_success:
                return ConnectorResult(
                    ok=True,
                    data={"record_id": record_id, "deleted": True},
                    proofs=[{"type": "airtable_record_deleted", "record_id": record_id, "timestamp": time.time()}]
                )
            return ConnectorResult(ok=False, error=f"airtable_error_{r.status_code}", retryable=r.status_code >= 500)

    async def _list_records(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """List records with optional filtering"""
        table = params.get("table")
        base_id = params.get("base_id", self._base_id)
        max_records = params.get("limit", 100)
        view = params.get("view")
        filter_formula = params.get("filter")

        if not table:
            return ConnectorResult(ok=False, error="table_required", retryable=False)

        query_params = {"maxRecords": max_records}
        if view:
            query_params["view"] = view
        if filter_formula:
            query_params["filterByFormula"] = filter_formula

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(
                f"{self._get_base_url(base_id)}/{table}",
                params=query_params,
                headers=self._get_headers()
            )

            if r.is_success:
                data = r.json()
                records = data.get("records", [])
                return ConnectorResult(
                    ok=True,
                    data={
                        "records": [{"id": rec["id"], "fields": rec["fields"]} for rec in records],
                        "count": len(records)
                    },
                    proofs=[]
                )
            return ConnectorResult(ok=False, error=f"airtable_error_{r.status_code}", retryable=r.status_code >= 500)

    async def _get_record(self, params: Dict[str, Any], timeout: int) -> ConnectorResult:
        """Get single record by ID"""
        table = params.get("table")
        record_id = params.get("record_id")
        base_id = params.get("base_id", self._base_id)

        if not table or not record_id:
            return ConnectorResult(ok=False, error="table_and_record_id_required", retryable=False)

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(
                f"{self._get_base_url(base_id)}/{table}/{record_id}",
                headers=self._get_headers()
            )

            if r.is_success:
                data = r.json()
                return ConnectorResult(
                    ok=True,
                    data={"record_id": data.get("id"), "fields": data.get("fields")},
                    proofs=[]
                )
            return ConnectorResult(ok=False, error=f"airtable_error_{r.status_code}", retryable=r.status_code >= 500)

    async def cost_estimate(self, action: str, params: Dict[str, Any]) -> CostEstimate:
        return CostEstimate(
            estimated_usd=0.001,
            model="per_call",
            breakdown={"api_call": 0.001}
        )
