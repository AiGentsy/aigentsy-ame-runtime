"""
CONTINUOUS DISCOVERY: Always-Fresh Pipeline

Continuously scrape the internet every 15 minutes.
Always-fresh opportunities ready for the autonomous cycle.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

from .internet_wide_scraper import get_internet_wide_scraper, InternetWideScraper
from .real_time_sources import REAL_TIME_SOURCES, get_platform_freshness_hours


class ContinuousDiscovery:
    """
    Continuously scrape the internet every N minutes.

    Features:
    - Configurable interval
    - Persistent cache of fresh opportunities
    - Callbacks for new discoveries
    - Health monitoring
    """

    def __init__(
        self,
        config: Optional[Dict] = None,
        interval_minutes: int = 15
    ):
        config = config or {}

        self.scraper = get_internet_wide_scraper(config)
        self.interval = interval_minutes * 60
        self.running = False

        # Cache of current fresh opportunities
        self.opportunity_cache: List[Dict] = []
        self.last_discovery_time: Optional[datetime] = None
        self.cycle_count = 0

        # Callbacks
        self.on_discovery_callbacks: List[Callable] = []

        # Stats
        self.stats = {
            'cycles_completed': 0,
            'total_opportunities': 0,
            'last_cycle_count': 0,
            'last_cycle_duration': 0,
            'errors': 0,
        }

    def add_callback(self, callback: Callable):
        """Add callback for new discoveries"""
        self.on_discovery_callbacks.append(callback)

    async def start(self):
        """Start continuous discovery loop"""
        self.running = True
        logger.info(f"[continuous] Starting continuous discovery (every {self.interval/60}min)")

        while self.running:
            try:
                await self._run_discovery_cycle()
            except Exception as e:
                logger.error(f"[continuous] Discovery cycle failed: {e}")
                self.stats['errors'] += 1

            # Wait for next cycle
            await asyncio.sleep(self.interval)

    def stop(self):
        """Stop discovery loop"""
        self.running = False
        logger.info("[continuous] Stopping continuous discovery")

    async def _run_discovery_cycle(self):
        """Run single discovery cycle"""
        import time
        start_time = time.time()

        logger.info("[continuous] Starting discovery cycle...")

        # Scrape all platforms
        opportunities = await self.scraper.scrape_all_platforms()

        # Filter by freshness
        fresh_opportunities = self._filter_fresh(opportunities)

        # Update cache
        self.opportunity_cache = fresh_opportunities
        self.last_discovery_time = datetime.now(timezone.utc)
        self.cycle_count += 1

        # Update stats
        duration = time.time() - start_time
        self.stats['cycles_completed'] += 1
        self.stats['total_opportunities'] = len(self.opportunity_cache)
        self.stats['last_cycle_count'] = len(fresh_opportunities)
        self.stats['last_cycle_duration'] = duration

        logger.info(f"""
[continuous] DISCOVERY CYCLE #{self.cycle_count} COMPLETE:
   Fresh opportunities: {len(fresh_opportunities)}
   Cycle duration: {duration:.1f}s
   Next cycle in: {self.interval/60}min
        """)

        # Call callbacks
        for callback in self.on_discovery_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(fresh_opportunities)
                else:
                    callback(fresh_opportunities)
            except Exception as e:
                logger.warning(f"[continuous] Callback failed: {e}")

    def _filter_fresh(self, opportunities: List[Dict]) -> List[Dict]:
        """Filter opportunities by platform-specific freshness windows"""
        fresh = []
        now = datetime.now(timezone.utc)

        for opp in opportunities:
            platform = opp.get('platform', '').lower()
            max_age_hours = get_platform_freshness_hours(platform)

            # Check discovered_at or created_at
            timestamp = opp.get('discovered_at') or opp.get('created_at') or opp.get('posted_at')

            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp

                    age_hours = (now - dt).total_seconds() / 3600

                    if age_hours <= max_age_hours:
                        fresh.append(opp)
                    # Skip stale
                except Exception:
                    # Include if we can't parse (fail-open)
                    fresh.append(opp)
            else:
                # No timestamp - assume fresh
                fresh.append(opp)

        logger.info(f"[continuous] Freshness filter: {len(opportunities)} -> {len(fresh)}")
        return fresh

    def get_opportunities(self) -> List[Dict]:
        """Get current cached opportunities"""
        return self.opportunity_cache.copy()

    def get_fresh_count(self) -> int:
        """Get count of fresh opportunities"""
        return len(self.opportunity_cache)

    def get_stats(self) -> Dict:
        """Get discovery stats"""
        return {
            **self.stats,
            'running': self.running,
            'interval_minutes': self.interval / 60,
            'cycle_count': self.cycle_count,
            'last_discovery': self.last_discovery_time.isoformat() if self.last_discovery_time else None,
            'scraper': self.scraper.get_stats(),
        }

    def is_healthy(self) -> bool:
        """Check if discovery is healthy"""
        if not self.running:
            return False

        if not self.last_discovery_time:
            return True  # Not yet run

        # Healthy if last discovery was within 2x interval
        now = datetime.now(timezone.utc)
        age = (now - self.last_discovery_time).total_seconds()
        return age < self.interval * 2


# Singleton instance
_continuous_discovery: Optional[ContinuousDiscovery] = None


def get_continuous_discovery(
    config: Optional[Dict] = None,
    interval_minutes: int = 15
) -> ContinuousDiscovery:
    """Get or create continuous discovery instance"""
    global _continuous_discovery
    if _continuous_discovery is None:
        _continuous_discovery = ContinuousDiscovery(config, interval_minutes)
    return _continuous_discovery


async def start_continuous_discovery(
    config: Optional[Dict] = None,
    interval_minutes: int = 15
) -> ContinuousDiscovery:
    """Start continuous discovery and return instance"""
    discovery = get_continuous_discovery(config, interval_minutes)
    asyncio.create_task(discovery.start())
    return discovery
