"""
REMOTE OK PACK: Remote Job Board Integration

Features:
- JSON API support
- Tag/skill parsing
- Salary extraction
"""

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime, timezone

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext

logger = logging.getLogger(__name__)


class RemoteOKPack(PlatformPack):
    """Platform pack for RemoteOK"""

    PLATFORM = "remoteok"
    BASE_URL = "https://remoteok.com"
    RATE_LIMIT = 0.5
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.API

    # RemoteOK has a public JSON API
    API_URL = "https://remoteok.com/api"

    SELECTORS = {
        'listing': 'tr.job, .job',
        'title': 'h2, .company_and_position h2',
        'company': '.company h3, .companyLink',
        'url': 'a.job, td.source a',
        'tags': '.tags .tag, .tag',
        'salary': '.salary, [data-salary]',
        'location': '.location',
    }

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        """Main discovery - prefer API"""
        self.stats['extractions'] += 1

        # Check for API response
        if context.api_response:
            opportunities = self._parse_api_response(context.api_response)
            if opportunities:
                self.stats['api_successes'] += 1
                return opportunities

        # Try to parse JSON from HTML/content
        if context.html:
            json_opps = self._try_parse_json(context.html)
            if json_opps:
                self.stats['api_successes'] += 1
                return json_opps

        # Fallback to selectors
        opportunities = await self.extract_via_selectors(context)

        if opportunities:
            self.stats['selector_successes'] += 1
        else:
            self.stats['failures'] += 1

        return opportunities

    async def extract_via_api(self, context: ExtractionContext) -> Optional[List[Dict]]:
        """Extract via RemoteOK JSON API"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.API_URL,
                    timeout=aiohttp.ClientTimeout(total=15),
                    headers={'User-Agent': 'AiGentsy/1.0'}
                ) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()
                    return self._parse_api_response(data)

        except Exception as e:
            logger.error(f"[remoteok] API extraction failed: {e}")
            return None

    def _try_parse_json(self, content: str) -> Optional[List[Dict]]:
        """Try to parse JSON from content"""
        import json

        content_stripped = content.strip()
        if content_stripped.startswith('['):
            try:
                data = json.loads(content_stripped)
                return self._parse_api_response(data)
            except:
                pass

        return None

    def _parse_api_response(self, data: List) -> List[Dict]:
        """Parse RemoteOK API response"""
        opportunities = []

        if not isinstance(data, list):
            return opportunities

        for item in data:
            # Skip legal/meta items
            if not isinstance(item, dict):
                continue
            if item.get('legal') or not item.get('position'):
                continue

            opp = self._parse_job(item)
            if opp:
                opportunities.append(opp)

        return opportunities

    def _parse_job(self, job: Dict) -> Optional[Dict]:
        """Parse single RemoteOK job"""
        position = job.get('position', '')
        if not position:
            return None

        company = job.get('company', 'Unknown')
        slug = job.get('slug', '')

        url = job.get('url', '')
        if not url and slug:
            url = f"{self.BASE_URL}/remote-jobs/{slug}"

        # Parse salary
        salary_min = job.get('salary_min')
        salary_max = job.get('salary_max')
        salary = None
        if salary_min:
            salary = float(salary_min)
        elif salary_max:
            salary = float(salary_max)

        # Get tags
        tags = job.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        return {
            'platform': self.PLATFORM,
            'title': f"{position} at {company}"[:200],
            'url': url,
            'body': job.get('description', '')[:1000],
            'company': company,
            'value': salary,
            'skills': tags[:10],
            'type': 'job',
            'discovered_at': datetime.now(timezone.utc).isoformat(),
            'source_data': {
                'remoteok_id': job.get('id'),
                'slug': slug,
                'date': job.get('date'),
                'logo': job.get('logo'),
                'location': job.get('location'),
                'salary_min': salary_min,
                'salary_max': salary_max,
            }
        }

    async def extract_via_selectors(self, context: ExtractionContext) -> List[Dict]:
        """Extract using CSS selectors"""
        opportunities = []

        if not context.html:
            return opportunities

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context.html, 'html.parser')

            # Find job rows
            items = soup.select(self.SELECTORS['listing'])[:50]

            for item in items:
                opp = self._extract_job_element(item)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"[remoteok] Selector extraction failed: {e}")

        return opportunities

    def _extract_job_element(self, element) -> Optional[Dict]:
        """Extract job from HTML element"""
        try:
            # Get title
            title_elem = element.select_one(self.SELECTORS['title'])
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            if not title:
                return None

            # Get company
            company_elem = element.select_one(self.SELECTORS['company'])
            company = company_elem.get_text(strip=True) if company_elem else ''

            # Get URL
            url_elem = element.select_one(self.SELECTORS['url'])
            url = url_elem.get('href', '') if url_elem else ''
            if url and not url.startswith('http'):
                url = f"{self.BASE_URL}{url}"

            # Get tags
            tag_elems = element.select(self.SELECTORS['tags'])
            tags = [t.get_text(strip=True) for t in tag_elems[:10]]

            # Get salary
            salary_elem = element.select_one(self.SELECTORS['salary'])
            salary = None
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
                match = re.search(r'[\d,]+', salary_text.replace(',', ''))
                if match:
                    try:
                        salary = float(match.group())
                    except:
                        pass

            return {
                'platform': self.PLATFORM,
                'title': f"{title} at {company}"[:200] if company else title[:200],
                'url': url or self.BASE_URL,
                'body': '',
                'company': company,
                'value': salary,
                'skills': tags,
                'type': 'job',
                'discovered_at': datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.debug(f"[remoteok] Job extraction failed: {e}")
            return None
