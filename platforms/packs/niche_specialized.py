"""
NICHE/SPECIALIZED: 10 Specialized Tech Platforms

Niches:
- crypto_jobs (Blockchain/Crypto)
- web3_jobs (Web3/DeFi)
- ai_jobs (AI/ML)
- ml_jobs (Machine Learning)
- golang_jobs (Go)
- python_jobs (Python)
- react_jobs (React)
- vue_jobs (Vue.js)
- rails_jobs (Ruby on Rails)
- flutter_jobs (Flutter/Mobile)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext


# Niche platform configurations
NICHE_CONFIGS = {
    'crypto_jobs': {
        'url': 'https://crypto.jobs/',
        'priority': 75,
        'niche': 'Blockchain/Crypto',
        'selectors': {'item': '.job-tile', 'link': 'a', 'title': '.job-title'},
        'value': 5000,
    },
    'web3_jobs': {
        'url': 'https://web3.career/',
        'priority': 75,
        'niche': 'Web3/DeFi',
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.title'},
        'value': 5000,
    },
    'ai_jobs': {
        'url': 'https://ai-jobs.net/',
        'priority': 80,
        'niche': 'AI',
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.title'},
        'value': 6000,
    },
    'ml_jobs': {
        'url': 'https://www.mljobs.com/',
        'priority': 80,
        'niche': 'Machine Learning',
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.job-title'},
        'value': 6000,
    },
    'golang_jobs': {
        'url': 'https://www.golangprojects.com/',
        'priority': 75,
        'niche': 'Golang',
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.title'},
        'value': 4500,
    },
    'python_jobs': {
        'url': 'https://www.pythonjobs.com/',
        'priority': 75,
        'niche': 'Python',
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.title'},
        'value': 4000,
    },
    'react_jobs': {
        'url': 'https://www.reactjobs.com/',
        'priority': 75,
        'niche': 'React',
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.title'},
        'value': 4000,
    },
    'vue_jobs': {
        'url': 'https://vuejobs.com/',
        'priority': 70,
        'niche': 'Vue.js',
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.job-title'},
        'value': 3500,
    },
    'rails_jobs': {
        'url': 'https://www.rubyonrails.jobs/',
        'priority': 70,
        'niche': 'Ruby on Rails',
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.title'},
        'value': 4000,
    },
    'flutter_jobs': {
        'url': 'https://flutterjobs.info/',
        'priority': 70,
        'niche': 'Flutter/Mobile',
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.job-title'},
        'value': 4000,
    },
}


class NicheSpecializedPack(PlatformPack):
    """Generic niche/specialized platform pack"""

    RATE_LIMIT = 0.5
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.SELECTORS

    NICHE_NAME = "generic"

    def __init__(self):
        super().__init__()
        config = NICHE_CONFIGS.get(self.NICHE_NAME, {})
        self.base_url = config.get('url', '')
        self.selectors = config.get('selectors', {})
        self.value_estimate = config.get('value', 4000)
        self.niche = config.get('niche', 'Tech')

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
                    'niche': self.niche,
                },
                'skills': [self.niche.lower()],
            }

        except Exception as e:
            logger.debug(f"[{self.PLATFORM}] Extraction failed: {e}")
            return None


# Generate pack classes
def _create_niche_class(name: str):
    class_name = ''.join(word.title() for word in name.split('_')) + 'Pack'

    class NewPack(NicheSpecializedPack):
        PLATFORM = name
        NICHE_NAME = name

    NewPack.__name__ = class_name
    return NewPack


NICHE_PACK_CLASSES = {
    name: _create_niche_class(name)
    for name in NICHE_CONFIGS.keys()
}

NICHE_SPECIALIZED_PACKS = [
    cls() for cls in NICHE_PACK_CLASSES.values()
]
