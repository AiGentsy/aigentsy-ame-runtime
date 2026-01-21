"""
Storage Connector
=================

S3/GCS/Azure Blob compatible storage operations.
"""

from typing import Dict, Any, Optional
import time
import os
import hashlib

from .base import Connector, ConnectorResult, ConnectorHealth, CostEstimate, AuthScheme

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class StorageConnector(Connector):
    """
    Cloud storage connector for S3/GCS/Azure Blob.

    Capabilities:
    - upload_file: Upload file to storage
    - download_file: Download file from storage
    - delete_file: Delete file
    - list_files: List files in bucket/container
    - generate_presigned_url: Generate temporary access URL
    """

    name = "storage"
    capabilities = [
        "upload_file",
        "download_file",
        "delete_file",
        "list_files",
        "generate_presigned_url",
        "store_proof",
        "store_artifact"
    ]
    auth_schemes = [AuthScheme.API_KEY]

    avg_latency_ms = 500.0
    success_rate = 0.999
    max_rps = 100.0

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        config = config or {}

        self._provider = config.get("provider", "s3")
        self._bucket = config.get("bucket") or os.getenv("S3_BUCKET") or os.getenv("STORAGE_BUCKET")
        self._region = config.get("region") or os.getenv("AWS_REGION", "us-east-1")

        # AWS credentials (for S3)
        self._access_key = config.get("access_key") or os.getenv("AWS_ACCESS_KEY_ID")
        self._secret_key = config.get("secret_key") or os.getenv("AWS_SECRET_ACCESS_KEY")

        self._s3_client = None
        if BOTO3_AVAILABLE and self._access_key and self._secret_key:
            self._s3_client = boto3.client(
                "s3",
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                region_name=self._region
            )

    async def health(self) -> ConnectorHealth:
        if not self._bucket:
            return ConnectorHealth(healthy=False, latency_ms=0, error="bucket_not_configured")
        if self._provider == "s3" and not BOTO3_AVAILABLE:
            return ConnectorHealth(healthy=False, latency_ms=0, error="boto3_not_installed")
        return ConnectorHealth(healthy=True, latency_ms=0)

    async def execute(
        self,
        action: str,
        params: Dict[str, Any],
        files: Optional[Dict[str, bytes]] = None,
        *,
        idempotency_key: Optional[str] = None,
        timeout: int = 60
    ) -> ConnectorResult:
        start = time.time()

        try:
            if action in ("upload_file", "store_proof", "store_artifact"):
                result = await self._upload_file(params, files, idempotency_key)
            elif action == "download_file":
                result = await self._download_file(params)
            elif action == "delete_file":
                result = await self._delete_file(params)
            elif action == "list_files":
                result = await self._list_files(params)
            elif action == "generate_presigned_url":
                result = await self._generate_presigned_url(params)
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

    async def _upload_file(
        self,
        params: Dict[str, Any],
        files: Optional[Dict[str, bytes]],
        idempotency_key: Optional[str]
    ) -> ConnectorResult:
        """Upload file to storage"""
        key = params.get("key") or params.get("path")
        content = params.get("content")
        content_type = params.get("content_type", "application/octet-stream")

        if files:
            # Get first file from files dict
            filename, content = next(iter(files.items()))
            if not key:
                key = filename

        if not key or not content:
            return ConnectorResult(ok=False, error="key_and_content_required", retryable=False)

        if isinstance(content, str):
            content = content.encode()

        # Generate content hash for proof
        content_hash = hashlib.sha256(content).hexdigest()

        if self._provider == "s3" and self._s3_client:
            try:
                self._s3_client.put_object(
                    Bucket=self._bucket,
                    Key=key,
                    Body=content,
                    ContentType=content_type
                )

                url = f"s3://{self._bucket}/{key}"
                return ConnectorResult(
                    ok=True,
                    data={
                        "bucket": self._bucket,
                        "key": key,
                        "url": url,
                        "size": len(content),
                        "content_hash": content_hash
                    },
                    proofs=[{
                        "type": "storage_upload",
                        "provider": "s3",
                        "bucket": self._bucket,
                        "key": key,
                        "content_hash": content_hash,
                        "size": len(content),
                        "timestamp": time.time()
                    }]
                )
            except Exception as e:
                return ConnectorResult(ok=False, error=str(e), retryable=True)

        return ConnectorResult(ok=False, error="provider_not_supported", retryable=False)

    async def _download_file(self, params: Dict[str, Any]) -> ConnectorResult:
        """Download file from storage"""
        key = params.get("key") or params.get("path")
        if not key:
            return ConnectorResult(ok=False, error="key_required", retryable=False)

        if self._provider == "s3" and self._s3_client:
            try:
                response = self._s3_client.get_object(Bucket=self._bucket, Key=key)
                content = response["Body"].read()

                return ConnectorResult(
                    ok=True,
                    data={
                        "key": key,
                        "size": len(content),
                        "content_type": response.get("ContentType"),
                        "content": content.decode() if params.get("decode") else None
                    },
                    proofs=[{"type": "storage_download", "key": key, "size": len(content), "timestamp": time.time()}]
                )
            except Exception as e:
                return ConnectorResult(ok=False, error=str(e), retryable=True)

        return ConnectorResult(ok=False, error="provider_not_supported", retryable=False)

    async def _delete_file(self, params: Dict[str, Any]) -> ConnectorResult:
        """Delete file from storage"""
        key = params.get("key") or params.get("path")
        if not key:
            return ConnectorResult(ok=False, error="key_required", retryable=False)

        if self._provider == "s3" and self._s3_client:
            try:
                self._s3_client.delete_object(Bucket=self._bucket, Key=key)
                return ConnectorResult(
                    ok=True,
                    data={"key": key, "deleted": True},
                    proofs=[{"type": "storage_delete", "key": key, "timestamp": time.time()}]
                )
            except Exception as e:
                return ConnectorResult(ok=False, error=str(e), retryable=True)

        return ConnectorResult(ok=False, error="provider_not_supported", retryable=False)

    async def _list_files(self, params: Dict[str, Any]) -> ConnectorResult:
        """List files in bucket"""
        prefix = params.get("prefix", "")
        limit = params.get("limit", 100)

        if self._provider == "s3" and self._s3_client:
            try:
                response = self._s3_client.list_objects_v2(
                    Bucket=self._bucket,
                    Prefix=prefix,
                    MaxKeys=limit
                )

                files = [
                    {"key": obj["Key"], "size": obj["Size"], "modified": obj["LastModified"].isoformat()}
                    for obj in response.get("Contents", [])
                ]

                return ConnectorResult(
                    ok=True,
                    data={"files": files, "count": len(files)},
                    proofs=[]
                )
            except Exception as e:
                return ConnectorResult(ok=False, error=str(e), retryable=True)

        return ConnectorResult(ok=False, error="provider_not_supported", retryable=False)

    async def _generate_presigned_url(self, params: Dict[str, Any]) -> ConnectorResult:
        """Generate presigned URL for temporary access"""
        key = params.get("key") or params.get("path")
        expires_in = params.get("expires_in", 3600)  # Default 1 hour
        method = params.get("method", "get").lower()

        if not key:
            return ConnectorResult(ok=False, error="key_required", retryable=False)

        if self._provider == "s3" and self._s3_client:
            try:
                client_method = "get_object" if method == "get" else "put_object"
                url = self._s3_client.generate_presigned_url(
                    client_method,
                    Params={"Bucket": self._bucket, "Key": key},
                    ExpiresIn=expires_in
                )

                return ConnectorResult(
                    ok=True,
                    data={"url": url, "expires_in": expires_in, "key": key},
                    proofs=[{"type": "presigned_url", "key": key, "expires_in": expires_in, "timestamp": time.time()}]
                )
            except Exception as e:
                return ConnectorResult(ok=False, error=str(e), retryable=True)

        return ConnectorResult(ok=False, error="provider_not_supported", retryable=False)

    async def cost_estimate(self, action: str, params: Dict[str, Any]) -> CostEstimate:
        # S3 costs: ~$0.005 per 1000 requests, ~$0.023 per GB storage
        size_mb = params.get("size", 1) / (1024 * 1024) if params.get("size") else 0.001
        return CostEstimate(
            estimated_usd=0.00001 + (size_mb * 0.000023),
            model="per_call_plus_storage",
            breakdown={"request": 0.00001, "storage": size_mb * 0.000023}
        )
