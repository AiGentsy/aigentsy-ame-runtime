"""
FREELANCE MARKETPLACES: 15 Platforms

Platforms:
- fiverr
- freelancer
- guru
- peopleperhour
- toptal
- contently
- codeable
- gigster
- crew
- folyo
- pilot
- x_team
- lemon
- braintrust
- a_team
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext


# Freelance marketplace configurations
FREELANCE_CONFIGS = {
    'fiverr': {
        'url': 'https://www.fiverr.com/categories/programming-tech',
        'priority': 85,
        'selectors': {'item': '[data-gig-card]', 'link': 'a', 'title': '.gig-title'},
        'value': 500,
        'requires_auth': True,
    },
    'freelancer': {
        'url': 'https://www.freelancer.com/jobs/',
        'priority': 85,
        'selectors': {'item': '.JobSearchCard-item', 'link': 'a', 'title': '.JobSearchCard-title'},
        'value': 1000,
    },
    'guru': {
        'url': 'https://www.guru.com/d/jobs/',
        'priority': 75,
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.job-title'},
        'value': 800,
    },
    'peopleperhour': {
        'url': 'https://www.peopleperhour.com/freelance-jobs',
        'priority': 75,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.title'},
        'value': 600,
    },
    'toptal': {
        'url': 'https://www.toptal.com/developers/job-listings',
        'priority': 90,
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.job-title'},
        'value': 5000,
        'requires_auth': True,
    },
    'contently': {
        'url': 'https://contently.com/jobs',
        'priority': 70,
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.title'},
        'value': 1000,
    },
    'codeable': {
        'url': 'https://codeable.io/developers/',
        'priority': 75,
        'selectors': {'item': '.project-card', 'link': 'a', 'title': '.project-title'},
        'value': 2000,
    },
    'gigster': {
        'url': 'https://gigster.com/',
        'priority': 80,
        'selectors': {'item': '.project-item', 'link': 'a', 'title': '.title'},
        'value': 5000,
        'requires_auth': True,
    },
    'crew': {
        'url': 'https://crew.co/',
        'priority': 70,
        'selectors': {'item': '.project-card', 'link': 'a', 'title': '.title'},
        'value': 3000,
    },
    'folyo': {
        'url': 'https://folyo.me/jobs',
        'priority': 70,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.title'},
        'value': 2000,
    },
    'pilot': {
        'url': 'https://pilot.co/',
        'priority': 75,
        'selectors': {'item': '.opportunity', 'link': 'a', 'title': '.title'},
        'value': 3000,
    },
    'x_team': {
        'url': 'https://x-team.com/developers/',
        'priority': 80,
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.job-title'},
        'value': 4000,
    },
    'lemon': {
        'url': 'https://lemon.io/',
        'priority': 75,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.title'},
        'value': 3500,
    },
    'braintrust': {
        'url': 'https://www.usebraintrust.com/jobs',
        'priority': 80,
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.job-title'},
        'value': 5000,
    },
    'a_team': {
        'url': 'https://www.a.team/',
        'priority': 85,
        'selectors': {'item': '.mission-card', 'link': 'a', 'title': '.title'},
        'value': 6000,
        'requires_auth': True,
    },
}


class FreelanceMarketplacePack(PlatformPack):
    """Generic freelance marketplace pack"""

    RATE_LIMIT = 0.3
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.SELECTORS

    # Override in subclass
    MARKETPLACE_NAME = "generic"

    def __init__(self):
        super().__init__()
        config = FREELANCE_CONFIGS.get(self.MARKETPLACE_NAME, {})
        self.base_url = config.get('url', '')
        self.selectors = config.get('selectors', {})
        self.value_estimate = config.get('value', 1000)
        self.REQUIRES_AUTH = config.get('requires_auth', False)

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

            item_selector = self.selectors.get('item', '.job-item')
            items = soup.select(item_selector)[:50]

            for item in items:
                opp = self._extract_gig(item, context.url)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"[{self.PLATFORM}] Extraction failed: {e}")

        return opportunities

    def _extract_gig(self, element, base_url: str) -> Optional[Dict]:
        """Extract gig from HTML element"""
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

            # Get budget if available
            budget_elem = element.select_one('.budget, .price, .rate')
            budget = budget_elem.get_text(strip=True) if budget_elem else ''

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
                'source_data': {
                    'budget_text': budget,
                }
            }

        except Exception as e:
            logger.debug(f"[{self.PLATFORM}] Gig extraction failed: {e}")
            return None


# Generate pack classes for each marketplace
def _create_freelance_class(name: str):
    """Factory to create freelance marketplace pack classes"""
    class_name = ''.join(word.title() for word in name.split('_')) + 'Pack'

    class NewPack(FreelanceMarketplacePack):
        PLATFORM = name
        MARKETPLACE_NAME = name

    NewPack.__name__ = class_name
    return NewPack


# Create all freelance pack classes
FREELANCE_PACK_CLASSES = {
    name: _create_freelance_class(name)
    for name in FREELANCE_CONFIGS.keys()
}

# Instantiate all packs
FREELANCE_MARKETPLACE_PACKS = [
    cls() for cls in FREELANCE_PACK_CLASSES.values()
]
