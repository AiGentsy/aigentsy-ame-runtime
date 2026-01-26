"""
HACKERNEWS VARIANTS: 4 Different HN Feeds

Feeds:
- hackernews_new: New stories
- hackernews_show: Show HN
- hackernews_ask: Ask HN
- hackernews_jobs: Job postings
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext


class HackerNewsVariantPack(PlatformPack):
    """Base class for HN variant packs"""

    API_BASE = "https://hacker-news.firebaseio.com/v0"
    RATE_LIMIT = 1.0
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.API

    # Override in subclass
    ENDPOINT = "topstories"
    VALUE_ESTIMATE = 500

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        self.stats['extractions'] += 1

        if HTTPX_AVAILABLE:
            opportunities = await self._fetch_via_api()
            if opportunities:
                self.stats['api_successes'] += 1
                return opportunities

        self.stats['failures'] += 1
        return []

    async def _fetch_via_api(self) -> List[Dict]:
        """Fetch stories via Firebase API"""
        opportunities = []

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Get story IDs
                response = await client.get(f"{self.API_BASE}/{self.ENDPOINT}.json")
                if response.status_code != 200:
                    return []

                story_ids = response.json()[:50]

                # Fetch each story
                for story_id in story_ids:
                    try:
                        story_resp = await client.get(f"{self.API_BASE}/item/{story_id}.json")
                        if story_resp.status_code == 200:
                            story = story_resp.json()
                            if story and not story.get('deleted') and not story.get('dead'):
                                opp = self._normalize_story(story)
                                if opp:
                                    opportunities.append(opp)
                    except:
                        continue

        except Exception as e:
            logger.error(f"[{self.PLATFORM}] API fetch error: {e}")

        return opportunities

    def _normalize_story(self, story: Dict) -> Optional[Dict]:
        """Normalize HN story to opportunity"""
        title = story.get('title', '')
        if not title:
            return None

        story_id = story.get('id', '')
        url = story.get('url', f"https://news.ycombinator.com/item?id={story_id}")

        return {
            'id': f"{self.PLATFORM}_{story_id}",
            'platform': self.PLATFORM,
            'url': url,
            'canonical_url': url,
            'title': title[:200],
            'body': story.get('text', '')[:1000] if story.get('text') else '',
            'type': 'job' if 'job' in self.PLATFORM else 'opportunity',
            'value': self.VALUE_ESTIMATE,
            'discovered_at': datetime.now(timezone.utc).isoformat(),
            'source_data': {
                'hn_id': story_id,
                'score': story.get('score', 0),
                'author': story.get('by'),
                'time': story.get('time'),
                'descendants': story.get('descendants', 0),
            }
        }


class HackerNewsNewPack(HackerNewsVariantPack):
    PLATFORM = "hackernews_new"
    ENDPOINT = "newstories"
    VALUE_ESTIMATE = 300


class HackerNewsShowPack(HackerNewsVariantPack):
    PLATFORM = "hackernews_show"
    ENDPOINT = "showstories"
    VALUE_ESTIMATE = 500


class HackerNewsAskPack(HackerNewsVariantPack):
    PLATFORM = "hackernews_ask"
    ENDPOINT = "askstories"
    VALUE_ESTIMATE = 400


class HackerNewsJobsPack(HackerNewsVariantPack):
    PLATFORM = "hackernews_jobs"
    ENDPOINT = "jobstories"
    VALUE_ESTIMATE = 2000

    def _normalize_story(self, story: Dict) -> Optional[Dict]:
        opp = super()._normalize_story(story)
        if opp:
            opp['type'] = 'job'
            opp['enrichment'] = {'payment_proximity': 0.6}
        return opp


# Export all packs
HN_VARIANT_PACKS = [
    HackerNewsNewPack(),
    HackerNewsShowPack(),
    HackerNewsAskPack(),
    HackerNewsJobsPack(),
]
