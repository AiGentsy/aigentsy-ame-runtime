"""
JOB BOARDS: 25+ Remote and Tech Job Platforms

Platforms:
- weworkremotely
- ycombinator_jobs (workatastartup)
- angellist (wellfound)
- otta
- remoteco
- flexjobs
- powertofly
- landing_jobs
- authentic_jobs
- startup_jobs
- builtin
- key_values
- arc_dev
- terminal
- nodesk
- remotive
- remoters
- working_nomads
- jobspresso
- indeed
- glassdoor
- monster
- ziprecruiter
- linkedin_jobs
- dice
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext


# Job board configurations
JOB_BOARD_CONFIGS = {
    'weworkremotely': {
        'url': 'https://weworkremotely.com/categories/remote-programming-jobs',
        'priority': 80,
        'selectors': {'item': 'li.feature', 'link': 'a', 'title': '.title'},
        'value': 3000,
    },
    'ycombinator_jobs': {
        'url': 'https://www.workatastartup.com/jobs',
        'priority': 85,
        'selectors': {'item': '.job-card', 'link': 'a', 'title': 'h3'},
        'value': 5000,
    },
    'angellist': {
        'url': 'https://wellfound.com/jobs',
        'priority': 80,
        'selectors': {'item': '[data-test="JobSearchResult"]', 'link': 'a', 'title': 'h2'},
        'value': 4000,
    },
    'otta': {
        'url': 'https://otta.com/jobs',
        'priority': 75,
        'selectors': {'item': '[data-testid="job-card"]', 'link': 'a', 'title': 'h3'},
        'value': 4000,
    },
    'remoteco': {
        'url': 'https://remote.co/remote-jobs/developer/',
        'priority': 75,
        'selectors': {'item': '.job_listing', 'link': 'a', 'title': '.title'},
        'value': 3000,
    },
    'flexjobs': {
        'url': 'https://www.flexjobs.com/remote-jobs/computer-it',
        'priority': 75,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.job-title'},
        'value': 3500,
        'requires_auth': True,
    },
    'powertofly': {
        'url': 'https://powertofly.com/jobs',
        'priority': 70,
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.job-title'},
        'value': 3000,
    },
    'landing_jobs': {
        'url': 'https://landing.jobs/jobs',
        'priority': 70,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': 'h3'},
        'value': 3500,
    },
    'authentic_jobs': {
        'url': 'https://authenticjobs.com/',
        'priority': 70,
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.title'},
        'value': 2500,
    },
    'startup_jobs': {
        'url': 'https://startup.jobs/',
        'priority': 75,
        'selectors': {'item': '.job-card', 'link': 'a', 'title': 'h3'},
        'value': 3000,
    },
    'builtin': {
        'url': 'https://builtin.com/jobs/remote',
        'priority': 70,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.title'},
        'value': 4000,
    },
    'key_values': {
        'url': 'https://www.keyvalues.com/',
        'priority': 75,
        'selectors': {'item': '.company-card', 'link': 'a', 'title': '.company-name'},
        'value': 4000,
    },
    'arc_dev': {
        'url': 'https://arc.dev/remote-jobs',
        'priority': 80,
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.job-title'},
        'value': 5000,
    },
    'terminal': {
        'url': 'https://terminal.io/jobs',
        'priority': 75,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.title'},
        'value': 5000,
    },
    'nodesk': {
        'url': 'https://nodesk.co/remote-jobs/',
        'priority': 70,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.title'},
        'value': 3000,
    },
    'remotive': {
        'url': 'https://remotive.com/remote-jobs/software-dev',
        'priority': 80,
        'selectors': {'item': '.job-tile', 'link': 'a', 'title': '.job-title'},
        'value': 3500,
    },
    'remoters': {
        'url': 'https://remoters.net/jobs/',
        'priority': 70,
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.title'},
        'value': 2500,
    },
    'working_nomads': {
        'url': 'https://www.workingnomads.com/jobs',
        'priority': 70,
        'selectors': {'item': '.job-item', 'link': 'a', 'title': '.title'},
        'value': 3000,
    },
    'jobspresso': {
        'url': 'https://jobspresso.co/remote-work/',
        'priority': 70,
        'selectors': {'item': '.job_listing', 'link': 'a', 'title': '.title'},
        'value': 3000,
    },
    'indeed': {
        'url': 'https://www.indeed.com/jobs?q=remote+developer',
        'priority': 80,
        'selectors': {'item': '.job_seen_beacon', 'link': 'a.jcs-JobTitle', 'title': 'h2'},
        'value': 4000,
    },
    'glassdoor': {
        'url': 'https://www.glassdoor.com/Job/remote-developer-jobs-SRCH_IL.0,6_IS11047_KO7,16.htm',
        'priority': 75,
        'selectors': {'item': '.job-listing', 'link': 'a', 'title': '.job-title'},
        'value': 4000,
    },
    'monster': {
        'url': 'https://www.monster.com/jobs/search?q=remote+developer',
        'priority': 70,
        'selectors': {'item': '.job-card', 'link': 'a', 'title': '.title'},
        'value': 3500,
    },
    'ziprecruiter': {
        'url': 'https://www.ziprecruiter.com/jobs-search?search=remote+developer',
        'priority': 75,
        'selectors': {'item': '.job_content', 'link': 'a', 'title': '.job_title'},
        'value': 3500,
    },
    'linkedin_jobs': {
        'url': 'https://www.linkedin.com/jobs/search/?keywords=remote%20developer',
        'priority': 85,
        'selectors': {'item': '.job-card-container', 'link': 'a', 'title': '.job-card-list__title'},
        'value': 5000,
        'requires_auth': True,
    },
    'dice': {
        'url': 'https://www.dice.com/jobs?q=remote&countryCode=US',
        'priority': 75,
        'selectors': {'item': '.card-job', 'link': 'a', 'title': '.card-title'},
        'value': 4000,
    },
}


class JobBoardPack(PlatformPack):
    """Generic job board pack using CSS selectors"""

    RATE_LIMIT = 0.3
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.SELECTORS

    # Override in subclass
    BOARD_NAME = "generic"

    def __init__(self):
        super().__init__()
        config = JOB_BOARD_CONFIGS.get(self.BOARD_NAME, {})
        self.base_url = config.get('url', '')
        self.selectors = config.get('selectors', {})
        self.value_estimate = config.get('value', 3000)
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
            logger.error(f"[{self.PLATFORM}] Selector extraction failed: {e}")

        return opportunities

    def _extract_job(self, element, base_url: str) -> Optional[Dict]:
        """Extract job from HTML element"""
        try:
            # Get title and URL
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

            # Get description if available
            desc_elem = element.select_one('.description, .excerpt, p')
            description = desc_elem.get_text(strip=True)[:500] if desc_elem else ''

            # Get company if available
            company_elem = element.select_one('.company, .company-name, .employer')
            company = company_elem.get_text(strip=True) if company_elem else ''

            return {
                'id': f"{self.PLATFORM}_{hash(url) % 10**8}",
                'platform': self.PLATFORM,
                'url': url or base_url,
                'canonical_url': url or base_url,
                'title': title[:200],
                'body': description,
                'company': company,
                'type': 'job',
                'value': self.value_estimate,
                'discovered_at': datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.debug(f"[{self.PLATFORM}] Job extraction failed: {e}")
            return None


# Generate pack classes for each job board
def _create_job_board_class(board_name: str):
    """Factory to create job board pack classes"""
    class_name = ''.join(word.title() for word in board_name.split('_')) + 'Pack'

    class NewPack(JobBoardPack):
        PLATFORM = board_name
        BOARD_NAME = board_name

    NewPack.__name__ = class_name
    return NewPack


# Create all job board pack classes
JOB_BOARD_PACK_CLASSES = {
    name: _create_job_board_class(name)
    for name in JOB_BOARD_CONFIGS.keys()
}

# Instantiate all packs
JOB_BOARD_PACKS = [
    cls() for cls in JOB_BOARD_PACK_CLASSES.values()
]
