"""
Base Connector Interface
========================

Every connector implements this interface to enable universal outcome execution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json


class AuthScheme(Enum):
    """Supported authentication schemes"""
    NONE = "none"
    API_KEY = "apikey"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    BEARER = "bearer"
    SESSION_COOKIE = "session_cookie"
    HMAC = "hmac"


@dataclass
class ConnectorHealth:
    """Health check result for a connector"""
    healthy: bool
    latency_ms: float
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ConnectorResult:
    """Standard result from connector execution"""
    ok: bool
    data: Dict[str, Any] = field(default_factory=dict)
    proofs: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    error_code: Optional[str] = None
    latency_ms: float = 0.0
    retryable: bool = False
    idempotency_key: Optional[str] = None
    executed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "data": self.data,
            "proofs": self.proofs,
            "error": self.error,
            "error_code": self.error_code,
            "latency_ms": self.latency_ms,
            "retryable": self.retryable,
            "idempotency_key": self.idempotency_key,
            "executed_at": self.executed_at
        }


@dataclass
class CostEstimate:
    """Cost estimate for an action"""
    estimated_usd: float
    model: str  # "per_call", "per_unit", "tiered", "subscription"
    breakdown: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.9


class Connector(ABC):
    """
    Base class for all connectors in the Universal Connector Bus.

    Every connector must implement:
    - health(): Check if the connector is operational
    - execute(): Perform an action with given parameters
    - cost_estimate(): Estimate cost for an action

    Properties:
    - name: Unique identifier for the connector
    - capabilities: List of actions this connector can perform
    - auth_schemes: Supported authentication methods
    """

    name: str = "base"
    capabilities: List[str] = []
    auth_schemes: List[AuthScheme] = [AuthScheme.NONE]

    # Performance characteristics
    avg_latency_ms: float = 1000.0
    success_rate: float = 0.95
    max_rps: float = 10.0  # Rate limit (requests per second)

    # Configuration
    _config: Dict[str, Any] = {}
    _metrics: Dict[str, Any] = {}

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize connector with optional configuration"""
        self._config = config or {}
        self._metrics = {
            "calls": 0,
            "successes": 0,
            "failures": 0,
            "total_latency_ms": 0.0,
            "last_call": None
        }

    @abstractmethod
    async def health(self) -> ConnectorHealth:
        """
        Check if the connector is healthy and operational.

        Returns:
            ConnectorHealth with status and latency
        """
        pass

    @abstractmethod
    async def execute(
        self,
        action: str,
        params: Dict[str, Any],
        files: Optional[Dict[str, bytes]] = None,
        *,
        idempotency_key: Optional[str] = None,
        timeout: int = 60
    ) -> ConnectorResult:
        """
        Execute an action with the given parameters.

        Args:
            action: The action to perform (must be in self.capabilities)
            params: Action-specific parameters
            files: Optional file attachments
            idempotency_key: Key for exactly-once semantics
            timeout: Maximum execution time in seconds

        Returns:
            ConnectorResult with data, proofs, and status
        """
        pass

    @abstractmethod
    async def cost_estimate(
        self,
        action: str,
        params: Dict[str, Any]
    ) -> CostEstimate:
        """
        Estimate the cost of executing an action.

        Args:
            action: The action to estimate
            params: Action parameters (may affect cost)

        Returns:
            CostEstimate with USD amount and breakdown
        """
        pass

    def can_perform(self, action: str) -> bool:
        """Check if this connector can perform the given action"""
        return action in self.capabilities

    def get_metrics(self) -> Dict[str, Any]:
        """Get connector performance metrics"""
        calls = self._metrics.get("calls", 0)
        return {
            "name": self.name,
            "calls": calls,
            "success_rate": self._metrics.get("successes", 0) / max(calls, 1),
            "avg_latency_ms": self._metrics.get("total_latency_ms", 0) / max(calls, 1),
            "last_call": self._metrics.get("last_call")
        }

    def _record_call(self, success: bool, latency_ms: float):
        """Record metrics for a call"""
        self._metrics["calls"] = self._metrics.get("calls", 0) + 1
        if success:
            self._metrics["successes"] = self._metrics.get("successes", 0) + 1
        else:
            self._metrics["failures"] = self._metrics.get("failures", 0) + 1
        self._metrics["total_latency_ms"] = self._metrics.get("total_latency_ms", 0) + latency_ms
        self._metrics["last_call"] = datetime.now(timezone.utc).isoformat()

    def _generate_proof_hash(self, data: Any) -> str:
        """Generate a hash proof for data"""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name} capabilities={len(self.capabilities)}>"
