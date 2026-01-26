"""
REDDIT PACK: Reddit Integration

Features:
- JSON API support
- Subreddit-specific parsing
- Multiple hiring subreddits
"""

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime, timezone

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext

logger = logging.getLogger(__name__)


class RedditPack(PlatformPack):
    """Platform pack for Reddit"""

    PLATFORM = "reddit"
    BASE_URL = "https://www.reddit.com"
    RATE_LIMIT = 0.5
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.API

    # Reddit JSON API (no auth needed for public)
    API_SUFFIX = ".json"

    # Relevant subreddits
    HIRING_SUBREDDITS = [
        'forhire',
        'hiring',
        'remotejobs',
        'freelance',
        'jobbit',
        'jobs4bitcoins',
        'slavelabour',
        'workonline',
    ]

    SELECTORS = {
        'listing': '.thing, [data-testid="post-container"], .Post',
        'title': 'a.title, [data-testid="post-title"], h3',
        'url': 'a.title, [data-testid="post-title"] a',
        'author': '.author, [data-testid="post_author_link"]',
        'score': '.score, [data-testid="post_karma"]',
    }

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        """Main discovery - use JSON API"""
        self.stats['extractions'] += 1

        # Check for API response
        if context.api_response:
            opportunities = self._parse_reddit_json(context.api_response)
            if opportunities:
                self.stats['api_successes'] += 1
                return opportunities

        # Check if HTML contains JSON
        if context.html:
            json_opportunities = self._try_parse_json_from_html(context.html)
            if json_opportunities:
                self.stats['api_successes'] += 1
                return json_opportunities

        # Fallback to selectors
        opportunities = await self.extract_via_selectors(context)

        if opportunities:
            self.stats['selector_successes'] += 1
        else:
            self.stats['failures'] += 1

        return opportunities

    def _try_parse_json_from_html(self, html: str) -> Optional[List[Dict]]:
        """Try to parse JSON API response from HTML/text"""
        import json

        # Check if it's actually JSON
        html_stripped = html.strip()
        if html_stripped.startswith('{') or html_stripped.startswith('['):
            try:
                data = json.loads(html_stripped)
                return self._parse_reddit_json(data)
            except:
                pass

        return None

    def _parse_reddit_json(self, data: Dict) -> List[Dict]:
        """Parse Reddit JSON API response"""
        opportunities = []

        try:
            # Handle listing response
            if isinstance(data, dict):
                if 'data' in data and 'children' in data['data']:
                    children = data['data']['children']
                    for child in children:
                        post = child.get('data', {})
                        opp = self._parse_reddit_post(post)
                        if opp:
                            opportunities.append(opp)

            elif isinstance(data, list):
                # Multiple listings (e.g., post + comments)
                for item in data:
                    if isinstance(item, dict) and 'data' in item:
                        opportunities.extend(self._parse_reddit_json(item))

        except Exception as e:
            logger.error(f"[reddit] JSON parsing failed: {e}")

        return opportunities

    def _parse_reddit_post(self, post: Dict) -> Optional[Dict]:
        """Parse single Reddit post"""
        if not post:
            return None

        # Skip removed/deleted
        if post.get('removed') or post.get('removed_by_category'):
            return None

        title = post.get('title', '')
        if not title or len(title) < 10:
            return None

        # Build URL
        permalink = post.get('permalink', '')
        url = f"{self.BASE_URL}{permalink}" if permalink else post.get('url', '')

        # Get body
        body = post.get('selftext', '') or post.get('body', '')

        # Determine if it's a hiring post
        post_type = self._determine_post_type(title, post.get('link_flair_text', ''))

        return {
            'platform': self.PLATFORM,
            'title': title[:200],
            'url': url,
            'body': body[:1000],
            'type': post_type,
            'discovered_at': datetime.now(timezone.utc).isoformat(),
            'source_data': {
                'reddit_id': post.get('id'),
                'subreddit': post.get('subreddit'),
                'author': post.get('author'),
                'score': post.get('score', 0),
                'upvote_ratio': post.get('upvote_ratio', 0),
                'num_comments': post.get('num_comments', 0),
                'created_utc': post.get('created_utc'),
                'flair': post.get('link_flair_text'),
            }
        }

    def _determine_post_type(self, title: str, flair: str) -> str:
        """Determine opportunity type from title/flair"""
        title_lower = title.lower()
        flair_lower = (flair or '').lower()

        # Check flair first
        if 'hiring' in flair_lower:
            return 'job'
        if 'for hire' in flair_lower:
            return 'gig'

        # Check title patterns
        if re.search(r'\[hiring\]|\(hiring\)|hiring:', title_lower):
            return 'job'
        if re.search(r'\[for hire\]|\(for hire\)|for hire:', title_lower):
            return 'gig'

        return 'opportunity'

    async def extract_via_selectors(self, context: ExtractionContext) -> List[Dict]:
        """Extract using CSS selectors (old Reddit format)"""
        opportunities = []

        if not context.html:
            return opportunities

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context.html, 'html.parser')

            # Find posts
            items = soup.select(self.SELECTORS['listing'])[:50]

            for item in items:
                opp = self._extract_post_element(item)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"[reddit] Selector extraction failed: {e}")

        return opportunities

    def _extract_post_element(self, element) -> Optional[Dict]:
        """Extract post from HTML element"""
        try:
            # Get title and URL
            title_elem = element.select_one(self.SELECTORS['title'])
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')

            if not title:
                return None

            # Make URL absolute
            if url and not url.startswith('http'):
                url = f"{self.BASE_URL}{url}"

            # Get author
            author_elem = element.select_one(self.SELECTORS['author'])
            author = author_elem.get_text(strip=True) if author_elem else ''

            # Get score
            score_elem = element.select_one(self.SELECTORS['score'])
            score_text = score_elem.get_text(strip=True) if score_elem else '0'
            try:
                score = int(re.sub(r'[^\d-]', '', score_text) or 0)
            except:
                score = 0

            # Get data attributes
            reddit_id = element.get('data-fullname', '').replace('t3_', '')

            return {
                'platform': self.PLATFORM,
                'title': title[:200],
                'url': url,
                'body': '',
                'type': self._determine_post_type(title, ''),
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'source_data': {
                    'reddit_id': reddit_id,
                    'author': author,
                    'score': score,
                }
            }

        except Exception as e:
            logger.debug(f"[reddit] Post extraction failed: {e}")
            return None

    def get_subreddit_url(self, subreddit: str, sort: str = 'new') -> str:
        """Get URL for subreddit listing"""
        return f"{self.BASE_URL}/r/{subreddit}/{sort}.json?limit=100"
