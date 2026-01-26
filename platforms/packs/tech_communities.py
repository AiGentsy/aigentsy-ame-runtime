"""
TECH COMMUNITIES: 15 Developer and Tech Platforms

Platforms:
- stackoverflow_jobs
- hashnode
- indiehackers
- producthunt
- betalist
- launching_next
- hacker_noon
- freecodecamp_jobs
- daily_dev
- dev_community
- lobsters
- slashdot_jobs
- techcrunch_jobs
- ars_technica_jobs
- github_trending
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext


# Tech community configurations
TECH_COMMUNITY_CONFIGS = {
    'stackoverflow_jobs': {
        'url': 'https://stackoverflow.com/jobs',
        'priority': 80,
        'selectors': {'item': '.fs-body3', 'link': 'a.s-link', 'title': '.fc-black-800'},
        'value': 4000,
    },
    'hashnode': {
        'url': 'https://hashnode.com/jobs',
        'priority': 70,
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.title'},
        'value': 3000,
    },
    'indiehackers': {
        'url': 'https://www.indiehackers.com/products',
        'priority': 75,
        'selectors': {'item': '.product-item', 'link': 'a', 'title': '.product-name'},
        'value': 1000,
    },
    'producthunt': {
        'url': 'https://www.producthunt.com/',
        'priority': 75,
        'selectors': {'item': '[data-test="post-item"]', 'link': 'a', 'title': 'h3'},
        'value': 500,
    },
    'betalist': {
        'url': 'https://betalist.com/',
        'priority': 70,
        'selectors': {'item': '.startup-card', 'link': 'a', 'title': '.startup-name'},
        'value': 500,
    },
    'launching_next': {
        'url': 'https://www.launchingnext.com/',
        'priority': 65,
        'selectors': {'item': '.startup-item', 'link': 'a', 'title': '.title'},
        'value': 400,
    },
    'hacker_noon': {
        'url': 'https://hackernoon.com/tagged/startup',
        'priority': 70,
        'selectors': {'item': '.story-card', 'link': 'a', 'title': 'h2'},
        'value': 500,
    },
    'freecodecamp_jobs': {
        'url': 'https://www.freecodecamp.org/news/tag/jobs/',
        'priority': 75,
        'selectors': {'item': '.post-card', 'link': 'a', 'title': '.post-card-title'},
        'value': 2000,
    },
    'daily_dev': {
        'url': 'https://daily.dev/',
        'priority': 70,
        'selectors': {'item': '.post-item', 'link': 'a', 'title': '.title'},
        'value': 500,
    },
    'dev_community': {
        'url': 'https://dev.to/t/hiring',
        'priority': 70,
        'selectors': {'item': '.crayons-story', 'link': 'a', 'title': '.crayons-story__title'},
        'value': 2000,
    },
    'lobsters': {
        'url': 'https://lobste.rs/',
        'priority': 75,
        'selectors': {'item': '.story', 'link': 'a.u-url', 'title': '.link'},
        'value': 500,
    },
    'slashdot_jobs': {
        'url': 'https://slashdot.org/jobs',
        'priority': 65,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.title'},
        'value': 3000,
    },
    'techcrunch_jobs': {
        'url': 'https://techcrunch.com/tag/jobs/',
        'priority': 70,
        'selectors': {'item': '.post-block', 'link': 'a', 'title': '.post-block__title'},
        'value': 1000,
    },
    'ars_technica_jobs': {
        'url': 'https://jobs.arstechnica.com/',
        'priority': 65,
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.title'},
        'value': 3000,
    },
    'github_trending': {
        'url': 'https://github.com/trending',
        'priority': 70,
        'selectors': {'item': '.Box-row', 'link': 'h2 a', 'title': 'h2 a'},
        'value': 500,
    },
}


class TechCommunityPack(PlatformPack):
    """Generic tech community platform pack"""

    RATE_LIMIT = 0.5
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.SELECTORS

    COMMUNITY_NAME = "generic"

    def __init__(self):
        super().__init__()
        config = TECH_COMMUNITY_CONFIGS.get(self.COMMUNITY_NAME, {})
        self.base_url = config.get('url', '')
        self.selectors = config.get('selectors', {})
        self.value_estimate = config.get('value', 1000)

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        self.stats['extractions'] += 1

        opportunities = await self.extract_via_selectors(context)

        if opportunities:
            self.stats['selector_successes'] += 1
        else:
            self.stats['failures'] += 1

        return opportunities

    async def extract_via_selectors(self, context: ExtractionContext) -> List[Dict]:
        """Extract opportunities using CSS selectors"""
        opportunities = []

        if not context.html:
            return opportunities

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context.html, 'html.parser')

            item_selector = self.selectors.get('item', '.item')
            items = soup.select(item_selector)[:50]

            for item in items:
                opp = self._extract_item(item, context.url)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"[{self.PLATFORM}] Extraction failed: {e}")

        return opportunities

    def _extract_item(self, element, base_url: str) -> Optional[Dict]:
        """Extract opportunity from HTML element"""
        try:
            link_selector = self.selectors.get('link', 'a')
            title_selector = self.selectors.get('title', '.title')

            link_elem = element.select_one(link_selector)
            title_elem = element.select_one(title_selector)

            if not title_elem:
                title_elem = link_elem

            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None

            url = ''
            if link_elem:
                url = link_elem.get('href', '')
                if url and not url.startswith('http'):
                    url = urljoin(base_url, url)

            return {
                'id': f"{self.PLATFORM}_{hash(url) % 10**8}",
                'platform': self.PLATFORM,
                'url': url or base_url,
                'canonical_url': url or base_url,
                'title': title[:200],
                'body': '',
                'type': 'opportunity',
                'value': self.value_estimate,
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'category': 'tech_community',
                }
            }

        except Exception as e:
            logger.debug(f"[{self.PLATFORM}] Extraction failed: {e}")
            return None


# Generate pack classes
def _create_community_class(name: str):
    class_name = ''.join(word.title() for word in name.split('_')) + 'Pack'

    class NewPack(TechCommunityPack):
        PLATFORM = name
        COMMUNITY_NAME = name

    NewPack.__name__ = class_name
    return NewPack


TECH_COMMUNITY_PACK_CLASSES = {
    name: _create_community_class(name)
    for name in TECH_COMMUNITY_CONFIGS.keys()
}

TECH_COMMUNITY_PACKS = [
    cls() for cls in TECH_COMMUNITY_PACK_CLASSES.values()
]
