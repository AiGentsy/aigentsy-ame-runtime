"""
HACKER NEWS PACK: YCombinator News Integration

Features:
- Firebase API support
- Who's Hiring thread parsing
- Comment thread extraction
"""

import logging
import json
import re
from typing import Dict, List, Optional
from datetime import datetime, timezone

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext

logger = logging.getLogger(__name__)


class HackerNewsPack(PlatformPack):
    """Platform pack for Hacker News"""

    PLATFORM = "hackernews"
    BASE_URL = "https://news.ycombinator.com"
    RATE_LIMIT = 1.0  # HN is generous
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.API

    # Firebase API (official)
    API_BASE = "https://hacker-news.firebaseio.com/v0"

    SELECTORS = {
        'listing': 'tr.athing',
        'title': 'span.titleline > a, .storylink',
        'url': 'span.titleline > a, .storylink',
        'score': '.score',
        'subtext': '.subtext',
        'comment': '.commtext',
    }

    # Known "Who's Hiring" thread patterns
    HIRING_PATTERNS = [
        r"who.*hiring",
        r"ask hn.*hiring",
        r"freelancer.*seeking",
        r"looking.*work",
    ]

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        """Main discovery - use API for best results"""
        self.stats['extractions'] += 1

        # Check if we have API response
        if context.api_response:
            opportunities = await self._parse_api_response(context.api_response)
            if opportunities:
                self.stats['api_successes'] += 1
                return opportunities

        # Fallback to HTML selectors
        opportunities = await self.extract_via_selectors(context)

        if opportunities:
            self.stats['selector_successes'] += 1
        else:
            self.stats['failures'] += 1

        return opportunities

    async def extract_via_api(self, context: ExtractionContext) -> Optional[List[Dict]]:
        """Extract via HN Firebase API"""
        try:
            import aiohttp

            opportunities = []

            # Get top stories
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.API_BASE}/topstories.json",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return None
                    story_ids = await response.json()

                # Get details for top 30 stories
                for story_id in story_ids[:30]:
                    async with session.get(
                        f"{self.API_BASE}/item/{story_id}.json",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            item = await response.json()
                            opp = self._parse_api_item(item)
                            if opp:
                                opportunities.append(opp)

            return opportunities if opportunities else None

        except Exception as e:
            logger.error(f"[hackernews] API extraction failed: {e}")
            return None

    async def _parse_api_response(self, data: Dict) -> List[Dict]:
        """Parse API response data"""
        opportunities = []

        if isinstance(data, list):
            for item in data:
                opp = self._parse_api_item(item)
                if opp:
                    opportunities.append(opp)

        elif isinstance(data, dict):
            opp = self._parse_api_item(data)
            if opp:
                opportunities.append(opp)

        return opportunities

    def _parse_api_item(self, item: Dict) -> Optional[Dict]:
        """Parse single HN API item"""
        if not item or item.get('deleted') or item.get('dead'):
            return None

        item_type = item.get('type', '')
        title = item.get('title', '')

        # Skip non-story items unless they're job posts
        if item_type not in ['story', 'job'] and not self._is_hiring_post(title):
            return None

        url = item.get('url', f"{self.BASE_URL}/item?id={item.get('id', '')}")

        return {
            'platform': self.PLATFORM,
            'title': title[:200],
            'url': url,
            'body': item.get('text', '')[:1000],
            'type': 'job' if item_type == 'job' else 'opportunity',
            'discovered_at': datetime.now(timezone.utc).isoformat(),
            'source_data': {
                'hn_id': item.get('id'),
                'score': item.get('score', 0),
                'author': item.get('by'),
                'time': item.get('time'),
                'descendants': item.get('descendants', 0),
            }
        }

    def _is_hiring_post(self, title: str) -> bool:
        """Check if title indicates a hiring post"""
        title_lower = title.lower()
        return any(
            re.search(pattern, title_lower)
            for pattern in self.HIRING_PATTERNS
        )

    async def extract_via_selectors(self, context: ExtractionContext) -> List[Dict]:
        """Extract using CSS selectors from HTML"""
        opportunities = []

        if not context.html:
            return opportunities

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context.html, 'html.parser')

            # Find story rows
            items = soup.select(self.SELECTORS['listing'])[:50]

            for item in items:
                opp = self._extract_story_row(item, soup)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"[hackernews] Selector extraction failed: {e}")

        return opportunities

    def _extract_story_row(self, row, soup) -> Optional[Dict]:
        """Extract story from HN table row"""
        try:
            # Get ID
            item_id = row.get('id')

            # Get title and URL
            title_elem = row.select_one(self.SELECTORS['title'])
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')

            if not title:
                return None

            # Make URL absolute
            if url and not url.startswith('http'):
                url = f"{self.BASE_URL}/{url}"

            # Get subtext row (next sibling)
            subtext_row = row.find_next_sibling('tr')
            score = 0
            author = ''

            if subtext_row:
                score_elem = subtext_row.select_one('.score')
                if score_elem:
                    score_text = score_elem.get_text(strip=True)
                    try:
                        score = int(re.search(r'\d+', score_text).group())
                    except:
                        pass

                author_elem = subtext_row.select_one('.hnuser')
                if author_elem:
                    author = author_elem.get_text(strip=True)

            return {
                'platform': self.PLATFORM,
                'title': title[:200],
                'url': url or f"{self.BASE_URL}/item?id={item_id}",
                'body': '',
                'type': 'opportunity',
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'source_data': {
                    'hn_id': item_id,
                    'score': score,
                    'author': author,
                }
            }

        except Exception as e:
            logger.debug(f"[hackernews] Row extraction failed: {e}")
            return None

    async def extract_hiring_comments(self, thread_id: int) -> List[Dict]:
        """Extract job posts from Who's Hiring thread comments"""
        opportunities = []

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                # Get thread
                async with session.get(
                    f"{self.API_BASE}/item/{thread_id}.json",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return opportunities

                    thread = await response.json()
                    comment_ids = thread.get('kids', [])

                # Get top-level comments (job posts)
                for comment_id in comment_ids[:100]:
                    async with session.get(
                        f"{self.API_BASE}/item/{comment_id}.json",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            comment = await response.json()
                            opp = self._parse_hiring_comment(comment)
                            if opp:
                                opportunities.append(opp)

        except Exception as e:
            logger.error(f"[hackernews] Hiring thread extraction failed: {e}")

        return opportunities

    def _parse_hiring_comment(self, comment: Dict) -> Optional[Dict]:
        """Parse job post from hiring thread comment"""
        if not comment or comment.get('deleted') or comment.get('dead'):
            return None

        text = comment.get('text', '')
        if not text or len(text) < 50:
            return None

        # Extract company name (usually first line)
        lines = text.split('<p>')
        company = lines[0][:100] if lines else 'Unknown'
        company = re.sub(r'<[^>]+>', '', company).strip()

        return {
            'platform': self.PLATFORM,
            'title': f"[Hiring] {company}"[:200],
            'url': f"{self.BASE_URL}/item?id={comment.get('id', '')}",
            'body': re.sub(r'<[^>]+>', ' ', text)[:1000],
            'company': company,
            'type': 'job',
            'discovered_at': datetime.now(timezone.utc).isoformat(),
            'source_data': {
                'hn_id': comment.get('id'),
                'author': comment.get('by'),
                'time': comment.get('time'),
            }
        }
