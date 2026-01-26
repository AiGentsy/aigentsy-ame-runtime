"""
INTERNET-WIDE SCRAPER: Production-Grade 55+ Platform Discovery

Features:
- Legal-safe collection (CollectorRuntime)
- Multilingual support
- Intent scoring
- Safety filtering
- Deduplication
- SLO enforcement
"""

import asyncio
import time
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

# Import discovery components
from .real_time_sources import REAL_TIME_SOURCES, get_platform_freshness_hours, get_platform_metadata
from .collector_runtime import get_collector, CollectorRuntime
from .i18n_normalizer import get_i18n_normalizer, I18nNormalizer
from .intent_signals import get_intent_scorer, IntentScorer
from .safety_filter import get_safety_filter, SafetyFilter
from .entity_resolution import get_entity_resolver, EntityResolver

# Try to import BeautifulSoup
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup not installed")


def stable_id(platform: str, url: str) -> str:
    """Generate stable, idempotent ID from platform and URL"""
    key = f"{platform}:{url}".lower()
    return hashlib.sha256(key.encode()).hexdigest()[:16]


class InternetWideScraper:
    """
    Production-grade internet-wide scraper with all safety guards.

    Pipeline:
    1. Fetch (CollectorRuntime)
    2. Parse (BeautifulSoup)
    3. i18n normalization
    4. Intent scoring
    5. Safety filtering
    6. Deduplication
    """

    def __init__(self, config: Optional[Dict] = None):
        config = config or {}

        self.collector = get_collector(config)
        self.i18n = get_i18n_normalizer()
        self.intent_scorer = get_intent_scorer()
        self.safety = get_safety_filter()
        self.entity_resolver = get_entity_resolver()

        self.timeout = config.get('timeout', 10)
        self.max_concurrent = config.get('max_concurrent', 20)

        # Stats
        self.stats = {
            'platforms_attempted': 0,
            'platforms_succeeded': 0,
            'platforms_failed': 0,
            'opportunities_found': 0,
            'opportunities_after_dedup': 0,
            'total_time_seconds': 0,
        }

        # Debug: Track parsing results per platform
        self.parsing_debug = []

    async def scrape_all_platforms(self, platforms: Optional[Dict[str, str]] = None) -> List[Dict]:
        """
        Scrape all platforms in parallel with rate limiting.

        Args:
            platforms: Optional dict of platform_name -> url. Uses REAL_TIME_SOURCES by default.

        Returns:
            List of discovered opportunities
        """
        platforms = platforms or REAL_TIME_SOURCES

        # Reset deduplication state for fresh run (singleton accumulates across calls)
        self.entity_resolver.reset()
        self.parsing_debug = []

        logger.info(f"[scraper] Starting scrape of {len(platforms)} platforms")
        start_time = time.time()

        # Semaphore for concurrent limiting
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def scrape_with_limit(platform: str, url: str) -> List[Dict]:
            async with semaphore:
                return await self.scrape_platform(platform, url)

        # Create tasks for all platforms
        tasks = [
            scrape_with_limit(platform, url)
            for platform, url in platforms.items()
        ]

        # Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        all_opportunities = []
        for i, result in enumerate(results):
            platform = list(platforms.keys())[i]
            self.stats['platforms_attempted'] += 1

            if isinstance(result, Exception):
                logger.warning(f"[scraper] {platform} failed: {result}")
                self.stats['platforms_failed'] += 1
                continue

            if result:
                self.stats['platforms_succeeded'] += 1
                all_opportunities.extend(result)

        # NOTE: Deduplication already happens per-platform in scrape_platform()
        # via self.entity_resolver.is_duplicate(). No need for final deduplicate_batch()
        # which would mark all opportunities as duplicates (since they were already added).
        unique_opportunities = all_opportunities

        elapsed = time.time() - start_time
        self.stats['opportunities_found'] = len(all_opportunities)
        self.stats['opportunities_after_dedup'] = len(unique_opportunities)
        self.stats['total_time_seconds'] = elapsed

        logger.info(f"""
[scraper] INTERNET-WIDE DISCOVERY COMPLETE:
   Platforms scraped: {self.stats['platforms_succeeded']}/{self.stats['platforms_attempted']}
   Opportunities found: {len(all_opportunities)}
   After dedup: {len(unique_opportunities)}
   Time elapsed: {elapsed:.1f}s
   Avg per platform: {elapsed/max(1,len(platforms)):.2f}s
        """)

        return unique_opportunities

    async def scrape_platform(self, platform: str, url: str) -> List[Dict]:
        """
        Scrape single platform with full enrichment pipeline.
        """
        opportunities = []
        debug_info = {
            'platform': platform,
            'url': url,
            'content_length': 0,
            'parser_used': 'none',
            'raw_opportunities': 0,
            'enriched_opportunities': 0,
            'error': None
        }

        try:
            # Extract host for rate limiting
            host = urlparse(url).netloc

            # Fetch with CollectorRuntime (legal-safe)
            html = await self.collector.fetch(url, host)

            # Fallback to JS rendering if needed
            if not html or len(html) < 500:
                html = await self.collector.fetch_rendered(url)

            if not html:
                debug_info['error'] = 'no_content'
                self.parsing_debug.append(debug_info)
                logger.debug(f"[scraper] {platform}: No content")
                return []

            debug_info['content_length'] = len(html)

            # Parse based on content type
            # Detect JSON by URL or content inspection (many APIs don't have .json in URL)
            content_stripped = html.strip()
            is_json = (
                url.endswith('.json') or
                'json' in url or
                '/api/' in url or
                '/api' in url or
                (content_stripped.startswith('{') or content_stripped.startswith('['))
            )
            is_rss = url.endswith('.rss') or 'rss' in url or content_stripped.startswith('<?xml')

            if is_json:
                debug_info['parser_used'] = 'json'
                opportunities = await self._parse_json(html, platform, url)
            elif is_rss:
                debug_info['parser_used'] = 'rss'
                opportunities = await self._parse_rss(html, platform, url)
            else:
                debug_info['parser_used'] = 'html'
                opportunities = await self._parse_html(html, platform, url)

            debug_info['raw_opportunities'] = len(opportunities)

            # Enrich each opportunity
            enriched = []
            for opp in opportunities:
                # Skip if already duplicate
                if self.entity_resolver.is_duplicate(opp):
                    continue

                # i18n normalization
                opp = self.i18n.normalize_language(opp)

                # Intent scoring
                opp = self.intent_scorer.enrich_intent(opp)

                # Safety filtering
                opp = self.safety.risk_screen(opp)

                # Generate stable ID if not present
                if not opp.get('id'):
                    opp['id'] = stable_id(platform, opp.get('url', ''))

                enriched.append(opp)

            debug_info['enriched_opportunities'] = len(enriched)
            self.parsing_debug.append(debug_info)
            logger.info(f"[scraper] {platform}: {len(enriched)} opportunities")
            return enriched

        except asyncio.TimeoutError:
            debug_info['error'] = 'timeout'
            self.parsing_debug.append(debug_info)
            logger.warning(f"[scraper] {platform}: timeout")
            return []
        except Exception as e:
            debug_info['error'] = str(e)
            self.parsing_debug.append(debug_info)
            logger.warning(f"[scraper] {platform}: {e}")
            return []

    async def _parse_html(self, html: str, platform: str, base_url: str) -> List[Dict]:
        """Parse HTML page for opportunities"""
        if not BS4_AVAILABLE:
            return []

        opportunities = []
        soup = BeautifulSoup(html, 'html.parser')

        # Generic selectors for common patterns
        selectors = [
            'article',
            '.job', '.job-listing', '.job-item',
            '.listing', '.listing-item',
            '.post', '.post-item',
            '.item', '.story',
            '.opportunity', '.gig',
            'tr.athing',  # HackerNews
            '.thing',  # Reddit
        ]

        found = set()  # Track URLs to avoid duplicates

        for selector in selectors:
            for element in soup.select(selector)[:50]:  # Limit per selector
                opp = self._extract_opportunity_from_element(element, platform, base_url)
                if opp and opp.get('url') and opp['url'] not in found:
                    found.add(opp['url'])
                    opportunities.append(opp)

        return opportunities

    async def _parse_json(self, content: str, platform: str, base_url: str) -> List[Dict]:
        """Parse JSON API response"""
        import json

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return []

        opportunities = []

        # Handle different JSON structures
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Reddit format
            if 'data' in data and 'children' in data['data']:
                items = [child['data'] for child in data['data']['children']]
            # RemoteOK format
            elif 'jobs' in data:
                items = data['jobs']
            # Generic
            elif 'items' in data:
                items = data['items']
            elif 'results' in data:
                items = data['results']

        for item in items[:100]:
            opp = self._normalize_json_item(item, platform, base_url)
            if opp:
                opportunities.append(opp)

        return opportunities

    async def _parse_rss(self, content: str, platform: str, base_url: str) -> List[Dict]:
        """Parse RSS feed"""
        if not BS4_AVAILABLE:
            return []

        opportunities = []
        soup = BeautifulSoup(content, 'xml')

        for item in soup.find_all('item')[:50]:
            title = item.find('title')
            link = item.find('link')
            description = item.find('description')
            pub_date = item.find('pubDate')

            if not title or not link:
                continue

            opp = {
                'platform': platform,
                'url': link.get_text(strip=True),
                'title': title.get_text(strip=True)[:200],
                'body': description.get_text(strip=True)[:1000] if description else '',
                'type': 'opportunity',
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'freshness_score': 1.0,
            }

            if pub_date:
                opp['posted_at'] = pub_date.get_text(strip=True)

            opportunities.append(opp)

        return opportunities

    def _extract_opportunity_from_element(
        self,
        element,
        platform: str,
        base_url: str
    ) -> Optional[Dict]:
        """Extract opportunity from HTML element"""
        try:
            # Find link
            link = element.select_one('a[href]')
            if not link:
                link = element.find('a')

            if not link:
                return None

            href = link.get('href', '')
            if not href or href.startswith('#') or href.startswith('javascript:'):
                return None

            # Make absolute URL
            if not href.startswith('http'):
                href = urljoin(base_url, href)

            # Get title
            title = link.get_text(strip=True)
            if not title or len(title) < 5:
                # Try element text
                title = element.get_text(strip=True)[:200]

            if not title or len(title) < 5:
                return None

            # Get body text
            body = element.get_text(strip=True)[:1000]

            # Get metadata
            metadata = get_platform_metadata(platform)

            return {
                'platform': platform,
                'url': href,
                'title': title,
                'body': body if body != title else '',
                'type': 'opportunity',
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'freshness_score': 1.0,
                'win_probability': metadata.get('win_rate', 0.1),
                'value': metadata.get('avg_value', 500),
            }

        except Exception as e:
            logger.debug(f"[scraper] Element extraction failed: {e}")
            return None

    def _normalize_json_item(self, item: Dict, platform: str, base_url: str) -> Optional[Dict]:
        """Normalize JSON item to opportunity format"""
        if not isinstance(item, dict):
            return None

        # Extract URL
        url = (
            item.get('url') or
            item.get('link') or
            item.get('permalink') or
            item.get('application_url') or
            ''
        )

        # Reddit URLs
        if platform.startswith('reddit') and not url and item.get('permalink'):
            url = f"https://www.reddit.com{item['permalink']}"

        if not url:
            return None

        # Extract title
        title = (
            item.get('title') or
            item.get('name') or
            item.get('position') or
            item.get('headline') or
            ''
        )[:200]

        if not title:
            return None

        # Extract body
        body = (
            item.get('body') or
            item.get('selftext') or
            item.get('description') or
            item.get('content') or
            ''
        )[:1000]

        # Get metadata
        metadata = get_platform_metadata(platform)

        # Extract value if present
        value = (
            item.get('budget') or
            item.get('salary') or
            item.get('compensation') or
            metadata.get('avg_value', 500)
        )
        if isinstance(value, str):
            # Try to extract number
            import re
            match = re.search(r'(\d+)', value.replace(',', ''))
            value = int(match.group(1)) if match else metadata.get('avg_value', 500)

        return {
            'platform': platform,
            'url': url,
            'title': title,
            'body': body,
            'type': 'opportunity',
            'discovered_at': datetime.now(timezone.utc).isoformat(),
            'freshness_score': 1.0,
            'win_probability': metadata.get('win_rate', 0.1),
            'value': value,
            'source_data': {
                'author': item.get('author'),
                'created_utc': item.get('created_utc'),
                'score': item.get('score'),
            }
        }

    def get_stats(self) -> Dict:
        """Get scraper stats"""
        # Get top 10 platforms with issues (0 opportunities despite content)
        problematic = [
            p for p in self.parsing_debug
            if p.get('content_length', 0) > 500 and p.get('raw_opportunities', 0) == 0
        ][:10]

        # Get successful platforms
        successful = [
            p for p in self.parsing_debug
            if p.get('raw_opportunities', 0) > 0
        ][:10]

        return {
            **self.stats,
            'collector': self.collector.get_stats(),
            'entity_resolver': self.entity_resolver.get_stats(),
            'i18n': self.i18n.get_stats(),
            'parsing_debug': {
                'total_platforms': len(self.parsing_debug),
                'problematic_platforms': problematic,
                'successful_platforms': successful,
            }
        }

    def reset_stats(self):
        """Reset stats for new run"""
        self.stats = {k: 0 for k in self.stats}
        self.parsing_debug = []
        self.entity_resolver.reset()


# Singleton instance
_scraper_instance: Optional[InternetWideScraper] = None


def get_internet_wide_scraper(config: Optional[Dict] = None) -> InternetWideScraper:
    """Get or create scraper instance"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = InternetWideScraper(config)
    return _scraper_instance


async def scrape_internet(platforms: Optional[Dict[str, str]] = None) -> List[Dict]:
    """Convenience function to scrape all platforms"""
    scraper = get_internet_wide_scraper()
    return await scraper.scrape_all_platforms(platforms)
