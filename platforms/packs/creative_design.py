"""
CREATIVE/DESIGN: 10 Design and Creative Platforms

Platforms:
- dribbble
- behance
- 99designs
- coroflot
- designcrowd
- folyo_design
- smashing_jobs
- krop
- authentic_jobs_design
- design_jobs_board
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext


# Creative platform configurations
CREATIVE_CONFIGS = {
    'dribbble': {
        'url': 'https://dribbble.com/jobs',
        'priority': 75,
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.job-title'},
        'value': 3000,
    },
    'behance': {
        'url': 'https://www.behance.net/joblist',
        'priority': 75,
        'selectors': {'item': '.JobCard-root', 'link': 'a', 'title': '.JobCard-jobTitle'},
        'value': 2500,
    },
    '99designs': {
        'url': 'https://99designs.com/designers/jobs',
        'priority': 80,
        'selectors': {'item': '.contest-card', 'link': 'a', 'title': '.contest-title'},
        'value': 500,
    },
    'coroflot': {
        'url': 'https://www.coroflot.com/design-jobs',
        'priority': 70,
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.title'},
        'value': 2500,
    },
    'designcrowd': {
        'url': 'https://www.designcrowd.com/design-jobs',
        'priority': 70,
        'selectors': {'item': '.project-item', 'link': 'a', 'title': '.project-title'},
        'value': 400,
    },
    'folyo_design': {
        'url': 'https://folyo.me/jobs/design',
        'priority': 70,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.title'},
        'value': 2000,
    },
    'smashing_jobs': {
        'url': 'https://jobs.smashingmagazine.com/',
        'priority': 75,
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.job-title'},
        'value': 3000,
    },
    'krop': {
        'url': 'https://www.krop.com/creative-jobs/',
        'priority': 70,
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.title'},
        'value': 2500,
    },
    'authentic_jobs_design': {
        'url': 'https://authenticjobs.com/#category=Design',
        'priority': 70,
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.title'},
        'value': 2500,
    },
    'design_jobs_board': {
        'url': 'https://designjobsboard.com/',
        'priority': 70,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.title'},
        'value': 2000,
    },
}


class CreativeDesignPack(PlatformPack):
    """Generic creative/design platform pack"""

    RATE_LIMIT = 0.3
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.SELECTORS

    CREATIVE_NAME = "generic"

    def __init__(self):
        super().__init__()
        config = CREATIVE_CONFIGS.get(self.CREATIVE_NAME, {})
        self.base_url = config.get('url', '')
        self.selectors = config.get('selectors', {})
        self.value_estimate = config.get('value', 2000)

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        self.stats['extractions'] += 1

        opportunities = await self.extract_via_selectors(context)

        if opportunities:
            self.stats['selector_successes'] += 1
        else:
            self.stats['failures'] += 1

        return opportunities

    async def extract_via_selectors(self, context: ExtractionContext) -> List[Dict]:
        """Extract design jobs using CSS selectors"""
        opportunities = []

        if not context.html:
            return opportunities

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context.html, 'html.parser')

            item_selector = self.selectors.get('item', '.job-item')
            items = soup.select(item_selector)[:50]

            for item in items:
                opp = self._extract_design_job(item, context.url)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"[{self.PLATFORM}] Extraction failed: {e}")

        return opportunities

    def _extract_design_job(self, element, base_url: str) -> Optional[Dict]:
        """Extract design job from HTML element"""
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

            # Get company if available
            company_elem = element.select_one('.company, .company-name')
            company = company_elem.get_text(strip=True) if company_elem else ''

            return {
                'id': f"{self.PLATFORM}_{hash(url) % 10**8}",
                'platform': self.PLATFORM,
                'url': url or base_url,
                'canonical_url': url or base_url,
                'title': title[:200],
                'body': '',
                'company': company,
                'type': 'job',
                'value': self.value_estimate,
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'category': 'design',
                }
            }

        except Exception as e:
            logger.debug(f"[{self.PLATFORM}] Extraction failed: {e}")
            return None


# Generate pack classes
def _create_creative_class(name: str):
    class_name = ''.join(word.title() for word in name.split('_')) + 'Pack'

    class NewPack(CreativeDesignPack):
        PLATFORM = name
        CREATIVE_NAME = name

    NewPack.__name__ = class_name
    return NewPack


CREATIVE_PACK_CLASSES = {
    name: _create_creative_class(name)
    for name in CREATIVE_CONFIGS.keys()
}

CREATIVE_DESIGN_PACKS = [
    cls() for cls in CREATIVE_PACK_CLASSES.values()
]
