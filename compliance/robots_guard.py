"""
ROBOTS GUARD: robots.txt Compliance

Features:
- Parse and cache robots.txt files
- Respect Crawl-delay directives
- Block disallowed paths
- User-agent specific rules
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import aiohttp

logger = logging.getLogger(__name__)


class RobotsGuard:
    """
    Enforce robots.txt compliance.

    Features:
    - Cache parsed robots.txt files
    - Honor Crawl-delay directives
    - Block disallowed paths
    - Configurable user agent
    """

    DEFAULT_USER_AGENT = 'AiGentsyBot/1.0'
    CACHE_TTL = 3600  # 1 hour cache

    def __init__(self, user_agent: Optional[str] = None):
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.cache: Dict[str, Tuple[RobotFileParser, float, Optional[float]]] = {}  # host -> (parser, timestamp, crawl_delay)
        self.last_fetch: Dict[str, float] = {}  # host -> last fetch time
        self.stats = {
            'checked': 0,
            'allowed': 0,
            'blocked': 0,
            'cache_hits': 0,
            'fetch_errors': 0,
        }

    async def fetch_robots(self, host: str) -> Tuple[RobotFileParser, Optional[float]]:
        """Fetch and parse robots.txt for host"""
        robots_url = f"https://{host}/robots.txt"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    robots_url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={'User-Agent': self.user_agent}
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                    else:
                        # No robots.txt or error - allow all
                        content = ""
        except Exception as e:
            logger.debug(f"[robots_guard] Failed to fetch {robots_url}: {e}")
            self.stats['fetch_errors'] += 1
            content = ""

        # Parse robots.txt
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.parse(content.splitlines())
        except:
            pass

        # Extract crawl delay
        crawl_delay = self._extract_crawl_delay(content)

        return parser, crawl_delay

    def _extract_crawl_delay(self, content: str) -> Optional[float]:
        """Extract Crawl-delay directive from robots.txt"""
        for line in content.splitlines():
            line = line.strip().lower()
            if line.startswith('crawl-delay:'):
                try:
                    return float(line.split(':', 1)[1].strip())
                except:
                    pass
        return None

    async def get_parser(self, host: str) -> Tuple[RobotFileParser, Optional[float]]:
        """Get cached or fresh robots.txt parser"""
        now = time.time()

        # Check cache
        if host in self.cache:
            parser, timestamp, crawl_delay = self.cache[host]
            if now - timestamp < self.CACHE_TTL:
                self.stats['cache_hits'] += 1
                return parser, crawl_delay

        # Fetch fresh
        parser, crawl_delay = await self.fetch_robots(host)
        self.cache[host] = (parser, now, crawl_delay)

        return parser, crawl_delay

    async def can_fetch(self, url: str) -> Tuple[bool, Optional[float]]:
        """
        Check if URL can be fetched per robots.txt.

        Returns:
            Tuple of (allowed, crawl_delay)
        """
        self.stats['checked'] += 1

        try:
            parsed = urlparse(url)
            host = parsed.netloc

            if not host:
                self.stats['allowed'] += 1
                return True, None

            parser, crawl_delay = await self.get_parser(host)

            # Check if path is allowed
            allowed = parser.can_fetch(self.user_agent, url)

            if allowed:
                self.stats['allowed'] += 1
            else:
                self.stats['blocked'] += 1
                logger.info(f"[robots_guard] Blocked by robots.txt: {url}")

            return allowed, crawl_delay

        except Exception as e:
            logger.debug(f"[robots_guard] Error checking {url}: {e}")
            # Default to allowed on error
            self.stats['allowed'] += 1
            return True, None

    async def wait_for_crawl_delay(self, host: str):
        """Wait for crawl delay if specified"""
        if host in self.cache:
            _, _, crawl_delay = self.cache[host]
            if crawl_delay:
                last_fetch = self.last_fetch.get(host, 0)
                now = time.time()
                wait_time = crawl_delay - (now - last_fetch)
                if wait_time > 0:
                    logger.debug(f"[robots_guard] Waiting {wait_time:.1f}s for {host}")
                    await asyncio.sleep(wait_time)

        self.last_fetch[host] = time.time()

    def clear_cache(self):
        """Clear robots.txt cache"""
        self.cache.clear()
        self.last_fetch.clear()

    def get_stats(self) -> Dict:
        """Get guard stats"""
        return {
            **self.stats,
            'cached_hosts': len(self.cache),
        }


# Singleton
_robots_guard: Optional[RobotsGuard] = None


def get_robots_guard(user_agent: Optional[str] = None) -> RobotsGuard:
    """Get or create robots guard instance"""
    global _robots_guard
    if _robots_guard is None:
        _robots_guard = RobotsGuard(user_agent)
    return _robots_guard
