"""
UPWORK PACK: Freelance Marketplace Integration

Features:
- API support (with OAuth)
- Selector-based extraction fallback
- Budget/rate parsing
- Skill extraction
"""

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime, timezone

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext

logger = logging.getLogger(__name__)


class UpworkPack(PlatformPack):
    """Platform pack for Upwork"""

    PLATFORM = "upwork"
    BASE_URL = "https://www.upwork.com"
    RATE_LIMIT = 0.2  # Be respectful
    REQUIRES_AUTH = True
    AUTH_TYPE = "oauth"
    PRIORITY = PackPriority.API

    SELECTORS = {
        'listing': 'article.job-tile, [data-test="job-tile"], .up-card-section',
        'title': 'a.job-title, h3 a, [data-test="job-title"]',
        'url': 'a.job-title, h3 a',
        'description': '.job-description, [data-test="job-description"]',
        'budget': '.budget, [data-test="budget"], .job-type',
        'skills': '.skills, [data-test="skill"], .air3-badge',
        'posted': '.posted-on, [data-test="posted-on"], time',
    }

    # API endpoints (requires OAuth)
    API_ENDPOINTS = {
        'jobs': '/api/profiles/v2/search/jobs',
        'job_detail': '/api/profiles/v2/jobs/{job_key}',
    }

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        """Main discovery - try API first, then selectors"""
        self.stats['extractions'] += 1

        # Try API if credentials available
        if self._credentials:
            opportunities = await self.extract_via_api(context)
            if opportunities:
                self.stats['api_successes'] += 1
                return opportunities

        # Fallback to selectors
        opportunities = await self.extract_via_selectors(context)

        if opportunities:
            self.stats['selector_successes'] += 1
        else:
            self.stats['failures'] += 1

        return opportunities

    async def extract_via_api(self, context: ExtractionContext) -> Optional[List[Dict]]:
        """Extract via Upwork API (requires OAuth)"""
        if not self._credentials:
            return None

        # API implementation would go here
        # This requires OAuth flow setup
        logger.debug("[upwork] API extraction not implemented - need OAuth")
        return None

    async def extract_via_selectors(self, context: ExtractionContext) -> List[Dict]:
        """Extract using CSS selectors"""
        opportunities = []

        if not context.html:
            return opportunities

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context.html, 'html.parser')

            # Find job tiles
            items = soup.select(self.SELECTORS['listing'])[:50]

            for item in items:
                opp = self._extract_upwork_job(item, context.url)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"[upwork] Selector extraction failed: {e}")

        return opportunities

    def _extract_upwork_job(self, element, base_url: str) -> Optional[Dict]:
        """Extract Upwork job from HTML element"""
        try:
            from urllib.parse import urljoin

            # Title and URL
            title_elem = element.select_one(self.SELECTORS['title'])
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')

            if not title or len(title) < 10:
                return None

            if url and not url.startswith('http'):
                url = urljoin(self.BASE_URL, url)

            # Description
            desc_elem = element.select_one(self.SELECTORS['description'])
            description = desc_elem.get_text(strip=True)[:1000] if desc_elem else ''

            # Budget
            budget_elem = element.select_one(self.SELECTORS['budget'])
            budget_text = budget_elem.get_text(strip=True) if budget_elem else ''
            budget = self._parse_upwork_budget(budget_text)

            # Skills
            skill_elems = element.select(self.SELECTORS['skills'])
            skills = [s.get_text(strip=True) for s in skill_elems[:10]]

            # Posted time
            posted_elem = element.select_one(self.SELECTORS['posted'])
            posted = posted_elem.get_text(strip=True) if posted_elem else ''

            return {
                'platform': self.PLATFORM,
                'title': title[:200],
                'url': url or base_url,
                'body': description,
                'value': budget,
                'skills': skills,
                'posted_at': posted,
                'type': 'gig',
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'budget_text': budget_text,
                    'job_type': 'hourly' if 'hourly' in budget_text.lower() else 'fixed',
                }
            }

        except Exception as e:
            logger.debug(f"[upwork] Job extraction failed: {e}")
            return None

    def _parse_upwork_budget(self, budget_text: str) -> Optional[float]:
        """Parse Upwork budget string"""
        if not budget_text:
            return None

        # Patterns: "$500 Fixed", "$25-$50 Hourly", "Hourly: $30.00-$45.00"
        patterns = [
            r'\$[\d,]+(?:\.\d+)?(?:\s*[-–]\s*\$?[\d,]+(?:\.\d+)?)?',
        ]

        for pattern in patterns:
            match = re.search(pattern, budget_text)
            if match:
                # Get first number
                nums = re.findall(r'[\d,]+(?:\.\d+)?', match.group())
                if nums:
                    try:
                        return float(nums[0].replace(',', ''))
                    except:
                        pass

        return None
