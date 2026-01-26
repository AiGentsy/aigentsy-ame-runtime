"""
PIPELINE: Ultra-Fast Queuing with Production SLOs

Features:
- Idempotency (process once)
- Backpressure management
- SLO enforcement
- Retry handling
"""

import asyncio
import time
import logging
from typing import Dict, Optional, Set, Callable, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SLOGuard:
    """
    SLO enforcement and backpressure management.

    Targets:
    - p95 discovery→first-touch: ≤120s
    - Throughput: 5000 opps/min sustained
    - Routing efficiency: ≥60%
    """

    def __init__(self, config: Optional[Dict] = None):
        config = config or {}

        # SLO targets
        self.max_p95_latency = config.get('max_p95_latency', 120)  # seconds
        self.max_throughput = config.get('max_throughput', 5000)  # per minute
        self.min_routing_efficiency = config.get('min_routing_efficiency', 0.60)

        # Current metrics
        self.current_load = 0
        self.processed_this_minute = 0
        self.last_minute_reset = time.time()

        # Latency tracking
        self.latencies: List[float] = []
        self.max_latency_samples = 1000

    def headroom(self) -> bool:
        """Check if we have SLO headroom for more work"""
        self._maybe_reset_minute()

        # Throughput check
        if self.processed_this_minute >= self.max_throughput * 0.8:
            logger.warning("[slo] Near throughput limit")
            return False

        # Latency check
        if self.latencies:
            p95 = self._calculate_p95()
            if p95 > self.max_p95_latency * 0.8:
                logger.warning(f"[slo] p95 latency high: {p95:.1f}s")
                return False

        return True

    def record_latency(self, latency_seconds: float):
        """Record a latency measurement"""
        self.latencies.append(latency_seconds)
        if len(self.latencies) > self.max_latency_samples:
            self.latencies = self.latencies[-self.max_latency_samples:]

    def record_processed(self, count: int = 1):
        """Record processed items"""
        self._maybe_reset_minute()
        self.processed_this_minute += count

    def _maybe_reset_minute(self):
        """Reset minute counter if needed"""
        now = time.time()
        if now - self.last_minute_reset >= 60:
            self.processed_this_minute = 0
            self.last_minute_reset = now

    def _calculate_p95(self) -> float:
        """Calculate p95 latency"""
        if not self.latencies:
            return 0

        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    def get_metrics(self) -> Dict:
        """Get current SLO metrics"""
        return {
            'p95_latency': self._calculate_p95() if self.latencies else None,
            'throughput_this_minute': self.processed_this_minute,
            'throughput_limit': self.max_throughput,
            'headroom': self.headroom(),
            'latency_samples': len(self.latencies),
        }


class Pipeline:
    """
    Ultra-fast opportunity pipeline with production guarantees.

    Features:
    - Idempotent processing (process each opportunity once)
    - Backpressure via SLO guard
    - Async queue processing
    - Configurable handlers
    """

    def __init__(self, config: Optional[Dict] = None):
        config = config or {}

        self.slo_guard = SLOGuard(config)

        # Idempotency tracking
        self.seen_ids: Set[str] = set()
        self.seen_ttl = config.get('seen_ttl', 72 * 3600)  # 72 hours

        # Processing queue
        self.queue: asyncio.Queue = asyncio.Queue()
        self.handlers: List[Callable] = []
        self.running = False

        # Stats
        self.stats = {
            'submitted': 0,
            'duplicates_skipped': 0,
            'backpressure_dropped': 0,
            'processed': 0,
            'errors': 0,
        }

    def add_handler(self, handler: Callable):
        """Add handler for processing opportunities"""
        self.handlers.append(handler)

    async def start(self):
        """Start pipeline processing"""
        self.running = True
        logger.info("[pipeline] Starting pipeline processor")
        asyncio.create_task(self._process_loop())

    def stop(self):
        """Stop pipeline"""
        self.running = False

    async def submit(self, opp: Dict) -> bool:
        """
        Submit opportunity to pipeline.

        Returns True if accepted, False if dropped.
        """
        self.stats['submitted'] += 1

        # Idempotency check
        opp_id = opp.get('id')
        if opp_id and opp_id in self.seen_ids:
            self.stats['duplicates_skipped'] += 1
            return False

        # Backpressure check
        if not self.slo_guard.headroom():
            self.stats['backpressure_dropped'] += 1
            logger.warning("[pipeline] Backpressure: dropping opportunity")
            return False

        # Mark as seen
        if opp_id:
            self.seen_ids.add(opp_id)

        # Add timestamp
        opp['pipeline_submitted_at'] = datetime.now(timezone.utc).isoformat()

        # Enqueue
        await self.queue.put(opp)
        return True

    async def submit_batch(self, opportunities: List[Dict]) -> int:
        """Submit batch of opportunities, returns count accepted"""
        accepted = 0
        for opp in opportunities:
            if await self.submit(opp):
                accepted += 1
        return accepted

    async def _process_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                opp = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=5.0
                )

                start_time = time.time()

                # Process through all handlers
                for handler in self.handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(opp)
                        else:
                            handler(opp)
                    except Exception as e:
                        logger.warning(f"[pipeline] Handler error: {e}")
                        self.stats['errors'] += 1

                # Record metrics
                latency = time.time() - start_time
                self.slo_guard.record_latency(latency)
                self.slo_guard.record_processed()
                self.stats['processed'] += 1

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[pipeline] Processing error: {e}")
                self.stats['errors'] += 1

    def clear_seen(self):
        """Clear seen IDs (useful for testing)"""
        self.seen_ids.clear()

    def get_stats(self) -> Dict:
        """Get pipeline stats"""
        return {
            **self.stats,
            'queue_size': self.queue.qsize(),
            'seen_count': len(self.seen_ids),
            'handlers_count': len(self.handlers),
            'slo': self.slo_guard.get_metrics(),
        }


# Singleton instance
_pipeline: Optional[Pipeline] = None


def get_pipeline(config: Optional[Dict] = None) -> Pipeline:
    """Get or create pipeline instance"""
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline(config)
    return _pipeline


# =============================================================================
# SLO TARGETS (for documentation)
# =============================================================================

SLOS = {
    'p95_discovery_to_first_touch': 120,  # seconds
    'discovery_throughput': 5000,  # opps/60s sustained
    'routing_efficiency': 0.60,  # 60%+ routed
    'executable_pdl_coverage': 30,  # 30+/55 platforms
    'freshness_guarantee': 48,  # hours (all opps <48h old)
}
