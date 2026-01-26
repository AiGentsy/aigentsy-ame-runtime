"""
INTERNATIONAL: 10 Regional Job Platforms

Regions:
- seek_au (Australia)
- totaljobs_uk (UK)
- xing_jobs (Germany)
- jobberman_africa (Africa)
- naukri_india (India)
- workopolis_canada (Canada)
- seek_nz (New Zealand)
- jobstreet_asia (Asia)
- europa_remotely (Europe)
- latam_jobs (Latin America)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext


# International platform configurations
INTERNATIONAL_CONFIGS = {
    'seek_au': {
        'url': 'https://www.seek.com.au/jobs?keywords=developer',
        'priority': 70,
        'region': 'Australia',
        'selectors': {'item': '[data-testid="job-card"]', 'link': 'a', 'title': 'h3'},
        'value': 4000,
        'currency': 'AUD',
    },
    'totaljobs_uk': {
        'url': 'https://www.totaljobs.com/jobs/developer',
        'priority': 70,
        'region': 'UK',
        'selectors': {'item': '.job-title', 'link': 'a', 'title': 'a'},
        'value': 3500,
        'currency': 'GBP',
    },
    'xing_jobs': {
        'url': 'https://www.xing.com/jobs/find?keywords=developer',
        'priority': 65,
        'region': 'Germany',
        'selectors': {'item': '.job-posting', 'link': 'a', 'title': '.job-title'},
        'value': 4000,
        'currency': 'EUR',
    },
    'jobberman_africa': {
        'url': 'https://www.jobberman.com/jobs?q=developer',
        'priority': 65,
        'region': 'Africa',
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.job-title'},
        'value': 1500,
        'currency': 'NGN',
    },
    'naukri_india': {
        'url': 'https://www.naukri.com/developer-jobs',
        'priority': 70,
        'region': 'India',
        'selectors': {'item': '.srp-jobtuple-wrapper', 'link': 'a.title', 'title': 'a.title'},
        'value': 2000,
        'currency': 'INR',
    },
    'workopolis_canada': {
        'url': 'https://www.workopolis.com/jobsearch/developer-jobs',
        'priority': 70,
        'region': 'Canada',
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.job-title'},
        'value': 4000,
        'currency': 'CAD',
    },
    'seek_nz': {
        'url': 'https://www.seek.co.nz/developer-jobs',
        'priority': 70,
        'region': 'New Zealand',
        'selectors': {'item': '[data-testid="job-card"]', 'link': 'a', 'title': 'h3'},
        'value': 3500,
        'currency': 'NZD',
    },
    'jobstreet_asia': {
        'url': 'https://www.jobstreet.com.sg/en/job-search/developer-jobs/',
        'priority': 70,
        'region': 'Asia',
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.job-title'},
        'value': 3500,
        'currency': 'SGD',
    },
    'europa_remotely': {
        'url': 'https://europeRemotely.com/',
        'priority': 65,
        'region': 'Europe',
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.title'},
        'value': 3500,
        'currency': 'EUR',
    },
    'latam_jobs': {
        'url': 'https://www.getonbrd.com/jobs',
        'priority': 65,
        'region': 'Latin America',
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.job-title'},
        'value': 2500,
        'currency': 'USD',
    },
}


class InternationalPack(PlatformPack):
    """Generic international job platform pack"""

    RATE_LIMIT = 0.3
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.SELECTORS

    INTL_NAME = "generic"

    def __init__(self):
        super().__init__()
        config = INTERNATIONAL_CONFIGS.get(self.INTL_NAME, {})
        self.base_url = config.get('url', '')
        self.selectors = config.get('selectors', {})
        self.value_estimate = config.get('value', 3000)
        self.region = config.get('region', 'Global')
        self.currency = config.get('currency', 'USD')

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        self.stats['extractions'] += 1

        opportunities = await self.extract_via_selectors(context)

        if opportunities:
            self.stats['selector_successes'] += 1
        else:
            self.stats['failures'] += 1

        return opportunities

    async def extract_via_selectors(self, context: ExtractionContext) -> List[Dict]:
        """Extract jobs using CSS selectors"""
        opportunities = []

        if not context.html:
            return opportunities

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context.html, 'html.parser')

            item_selector = self.selectors.get('item', '.job-item')
            items = soup.select(item_selector)[:50]

            for item in items:
                opp = self._extract_job(item, context.url)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"[{self.PLATFORM}] Extraction failed: {e}")

        return opportunities

    def _extract_job(self, element, base_url: str) -> Optional[Dict]:
        """Extract job from HTML element"""
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
                'type': 'job',
                'value': self.value_estimate,
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'region': self.region,
                    'currency': self.currency,
                },
                'pricing': {
                    'currency': self.currency,
                }
            }

        except Exception as e:
            logger.debug(f"[{self.PLATFORM}] Extraction failed: {e}")
            return None


# Generate pack classes
def _create_intl_class(name: str):
    class_name = ''.join(word.title() for word in name.split('_')) + 'Pack'

    class NewPack(InternationalPack):
        PLATFORM = name
        INTL_NAME = name

    NewPack.__name__ = class_name
    return NewPack


INTERNATIONAL_PACK_CLASSES = {
    name: _create_intl_class(name)
    for name in INTERNATIONAL_CONFIGS.keys()
}

INTERNATIONAL_PACKS = [
    cls() for cls in INTERNATIONAL_PACK_CLASSES.values()
]
