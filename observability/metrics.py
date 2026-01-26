"""
METRICS: OTEL-Compatible Metrics Collection

Features:
- Counter, Gauge, Histogram types
- Labels/dimensions support
- Prometheus-compatible export
- In-memory aggregation
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timezone
import threading

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """Monotonically increasing counter"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._values: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment counter"""
        key = self._labels_key(labels)
        with self._lock:
            self._values[key] += value

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current value"""
        key = self._labels_key(labels)
        return self._values.get(key, 0.0)

    def _labels_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Convert labels to key"""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Gauge:
    """Value that can go up or down"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._values: Dict[str, float] = {}
        self._lock = threading.Lock()

    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge value"""
        key = self._labels_key(labels)
        with self._lock:
            self._values[key] = value

    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment gauge"""
        key = self._labels_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + value

    def dec(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Decrement gauge"""
        self.inc(-value, labels)

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current value"""
        key = self._labels_key(labels)
        return self._values.get(key, 0.0)

    def _labels_key(self, labels: Optional[Dict[str, str]]) -> str:
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Histogram:
    """Distribution of values"""

    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(self, name: str, description: str = "", buckets: Optional[List[float]] = None):
        self.name = name
        self.description = description
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: Dict[str, List[int]] = defaultdict(lambda: [0] * len(self.buckets))
        self._sums: Dict[str, float] = defaultdict(float)
        self._totals: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Record observation"""
        key = self._labels_key(labels)
        with self._lock:
            self._sums[key] += value
            self._totals[key] += 1
            for i, bucket in enumerate(self.buckets):
                if value <= bucket:
                    self._counts[key][i] += 1

    def get_percentile(self, percentile: float, labels: Optional[Dict[str, str]] = None) -> float:
        """Approximate percentile from histogram"""
        key = self._labels_key(labels)
        if key not in self._totals or self._totals[key] == 0:
            return 0.0

        target = percentile * self._totals[key]
        cumulative = 0
        for i, count in enumerate(self._counts[key]):
            cumulative += count
            if cumulative >= target:
                return self.buckets[i]

        return self.buckets[-1]

    def _labels_key(self, labels: Optional[Dict[str, str]]) -> str:
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))


class Metrics:
    """
    Centralized metrics collection.

    Provides OTEL-compatible metrics for:
    - Discovery (opportunities found, platforms scraped)
    - Enrichment (processing time, scores)
    - Routing (decisions, tiers)
    - Execution (attempts, successes, failures)
    """

    def __init__(self):
        # Discovery metrics
        self.opportunities_discovered = Counter(
            "opportunities_discovered_total",
            "Total opportunities discovered"
        )
        self.platforms_scraped = Counter(
            "platforms_scraped_total",
            "Total platform scrape attempts"
        )
        self.discovery_duration = Histogram(
            "discovery_duration_seconds",
            "Discovery duration in seconds"
        )

        # Enrichment metrics
        self.enrichment_duration = Histogram(
            "enrichment_duration_seconds",
            "Enrichment processing time"
        )
        self.routing_scores = Histogram(
            "routing_score",
            "Distribution of routing scores",
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )

        # Routing metrics
        self.routing_decisions = Counter(
            "routing_decisions_total",
            "Total routing decisions by tier"
        )
        self.fast_path_eligible = Counter(
            "fast_path_eligible_total",
            "Total fast-path eligible opportunities"
        )

        # Execution metrics
        self.execution_attempts = Counter(
            "execution_attempts_total",
            "Total execution attempts"
        )
        self.execution_successes = Counter(
            "execution_successes_total",
            "Total successful executions"
        )
        self.execution_failures = Counter(
            "execution_failures_total",
            "Total failed executions"
        )
        self.execution_duration = Histogram(
            "execution_duration_seconds",
            "Execution duration in seconds"
        )

        # Risk metrics
        self.blocked_opportunities = Counter(
            "blocked_opportunities_total",
            "Total opportunities blocked by risk"
        )

        # Active opportunities gauge
        self.active_opportunities = Gauge(
            "active_opportunities",
            "Currently active opportunities"
        )

        # Start time for uptime
        self._start_time = time.time()

    def record_discovery(self, platform: str, count: int, duration: float):
        """Record discovery metrics"""
        self.platforms_scraped.inc(labels={'platform': platform})
        self.opportunities_discovered.inc(count, labels={'platform': platform})
        self.discovery_duration.observe(duration, labels={'platform': platform})

    def record_routing(self, tier: str, score: float):
        """Record routing decision"""
        self.routing_decisions.inc(labels={'tier': tier})
        self.routing_scores.observe(score)
        if tier == 'fast_path':
            self.fast_path_eligible.inc()

    def record_execution(self, success: bool, duration: float, platform: str = ""):
        """Record execution metrics"""
        labels = {'platform': platform} if platform else {}
        self.execution_attempts.inc(labels=labels)
        if success:
            self.execution_successes.inc(labels=labels)
        else:
            self.execution_failures.inc(labels=labels)
        self.execution_duration.observe(duration, labels=labels)

    def record_blocked(self, reason: str):
        """Record blocked opportunity"""
        self.blocked_opportunities.inc(labels={'reason': reason})

    def get_summary(self) -> Dict:
        """Get metrics summary"""
        return {
            'uptime_seconds': time.time() - self._start_time,
            'opportunities_discovered': self.opportunities_discovered.get(),
            'platforms_scraped': self.platforms_scraped.get(),
            'execution_attempts': self.execution_attempts.get(),
            'execution_successes': self.execution_successes.get(),
            'execution_failures': self.execution_failures.get(),
            'blocked_opportunities': self.blocked_opportunities.get(),
            'active_opportunities': self.active_opportunities.get(),
            'routing_p50': self.routing_scores.get_percentile(0.50),
            'routing_p90': self.routing_scores.get_percentile(0.90),
            'execution_p50': self.execution_duration.get_percentile(0.50),
            'execution_p95': self.execution_duration.get_percentile(0.95),
        }

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []

        # Helper to format metric
        def format_counter(counter: Counter):
            lines.append(f"# HELP {counter.name} {counter.description}")
            lines.append(f"# TYPE {counter.name} counter")
            for key, value in counter._values.items():
                labels = f"{{{key}}}" if key else ""
                lines.append(f"{counter.name}{labels} {value}")

        def format_gauge(gauge: Gauge):
            lines.append(f"# HELP {gauge.name} {gauge.description}")
            lines.append(f"# TYPE {gauge.name} gauge")
            for key, value in gauge._values.items():
                labels = f"{{{key}}}" if key else ""
                lines.append(f"{gauge.name}{labels} {value}")

        # Export all metrics
        format_counter(self.opportunities_discovered)
        format_counter(self.platforms_scraped)
        format_counter(self.execution_attempts)
        format_counter(self.execution_successes)
        format_counter(self.execution_failures)
        format_counter(self.blocked_opportunities)
        format_gauge(self.active_opportunities)

        return "\n".join(lines)


# Singleton
_metrics: Optional[Metrics] = None


def get_metrics() -> Metrics:
    """Get or create metrics instance"""
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics
