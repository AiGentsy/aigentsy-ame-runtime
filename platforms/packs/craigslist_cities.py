"""
CRAIGSLIST: 5 Major US Cities

Cities:
- craigslist_sf (San Francisco Bay Area)
- craigslist_nyc (New York City)
- craigslist_la (Los Angeles)
- craigslist_chicago (Chicago)
- craigslist_boston (Boston)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext


# Craigslist city configurations
CRAIGSLIST_CONFIGS = {
    'craigslist_sf': {
        'url': 'https://sfbay.craigslist.org/search/cpg',
        'priority': 75,
        'city': 'San Francisco',
        'selectors': {'item': '.result-row', 'link': 'a.result-title', 'title': 'a.result-title'},
        'value': 1000,
    },
    'craigslist_nyc': {
        'url': 'https://newyork.craigslist.org/search/cpg',
        'priority': 75,
        'city': 'New York',
        'selectors': {'item': '.result-row', 'link': 'a.result-title', 'title': 'a.result-title'},
        'value': 1200,
    },
    'craigslist_la': {
        'url': 'https://losangeles.craigslist.org/search/cpg',
        'priority': 70,
        'city': 'Los Angeles',
        'selectors': {'item': '.result-row', 'link': 'a.result-title', 'title': 'a.result-title'},
        'value': 1000,
    },
    'craigslist_chicago': {
        'url': 'https://chicago.craigslist.org/search/cpg',
        'priority': 70,
        'city': 'Chicago',
        'selectors': {'item': '.result-row', 'link': 'a.result-title', 'title': 'a.result-title'},
        'value': 900,
    },
    'craigslist_boston': {
        'url': 'https://boston.craigslist.org/search/cpg',
        'priority': 70,
        'city': 'Boston',
        'selectors': {'item': '.result-row', 'link': 'a.result-title', 'title': 'a.result-title'},
        'value': 1000,
    },
}


class CraigslistPack(PlatformPack):
    """Generic Craigslist city pack"""

    RATE_LIMIT = 0.2  # Be respectful
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.SELECTORS

    CL_CITY = "generic"

    def __init__(self):
        super().__init__()
        config = CRAIGSLIST_CONFIGS.get(self.CL_CITY, {})
        self.base_url = config.get('url', '')
        self.selectors = config.get('selectors', {})
        self.value_estimate = config.get('value', 800)
        self.city = config.get('city', 'Unknown')

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        self.stats['extractions'] += 1

        opportunities = await self.extract_via_selectors(context)

        if opportunities:
            self.stats['selector_successes'] += 1
        else:
            self.stats['failures'] += 1

        return opportunities

    async def extract_via_selectors(self, context: ExtractionContext) -> List[Dict]:
        """Extract gigs using CSS selectors"""
        opportunities = []

        if not context.html:
            return opportunities

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context.html, 'html.parser')

            item_selector = self.selectors.get('item', '.result-row')
            items = soup.select(item_selector)[:50]

            for item in items:
                opp = self._extract_gig(item, context.url)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"[{self.PLATFORM}] Extraction failed: {e}")

        return opportunities

    def _extract_gig(self, element, base_url: str) -> Optional[Dict]:
        """Extract gig from Craigslist row"""
        try:
            link_selector = self.selectors.get('link', 'a.result-title')
            link_elem = element.select_one(link_selector)

            if not link_elem:
                return None

            title = link_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None

            url = link_elem.get('href', '')
            if url and not url.startswith('http'):
                url = urljoin(base_url, url)

            # Get price if available
            price_elem = element.select_one('.result-price')
            price = price_elem.get_text(strip=True) if price_elem else ''

            # Get date
            date_elem = element.select_one('.result-date')
            posted_date = date_elem.get('datetime', '') if date_elem else ''

            return {
                'id': f"{self.PLATFORM}_{hash(url) % 10**8}",
                'platform': self.PLATFORM,
                'url': url or base_url,
                'canonical_url': url or base_url,
                'title': title[:200],
                'body': '',
                'type': 'gig',
                'value': self.value_estimate,
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'posted_at': posted_date,
                'metadata': {
                    'city': self.city,
                    'price_text': price,
                },
                'enrichment': {
                    # Craigslist is lower trust
                    'poster_reputation': 0.3,
                    'risk_score': 0.4,
                }
            }

        except Exception as e:
            logger.debug(f"[{self.PLATFORM}] Extraction failed: {e}")
            return None


# Generate pack classes
def _create_cl_class(name: str):
    class_name = ''.join(word.title() for word in name.split('_')) + 'Pack'

    class NewPack(CraigslistPack):
        PLATFORM = name
        CL_CITY = name

    NewPack.__name__ = class_name
    return NewPack


CRAIGSLIST_PACK_CLASSES = {
    name: _create_cl_class(name)
    for name in CRAIGSLIST_CONFIGS.keys()
}

CRAIGSLIST_PACKS = [
    cls() for cls in CRAIGSLIST_PACK_CLASSES.values()
]
