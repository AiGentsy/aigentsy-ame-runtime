"""
GITHUB PACK: GitHub Jobs & Bounties Integration

Features:
- GitHub API support
- Issue/bounty detection
- Sponsor/funding detection
"""

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime, timezone

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext

logger = logging.getLogger(__name__)


class GithubPack(PlatformPack):
    """Platform pack for GitHub"""

    PLATFORM = "github"
    BASE_URL = "https://github.com"
    API_BASE = "https://api.github.com"
    RATE_LIMIT = 0.5
    REQUIRES_AUTH = False  # Can work without auth but rate-limited
    AUTH_TYPE = "api_key"
    PRIORITY = PackPriority.API

    SELECTORS = {
        'listing': '.Box-row, .js-navigation-item',
        'title': 'a.Link--primary, .markdown-title',
        'url': 'a.Link--primary',
        'labels': '.labels .IssueLabel, .Label',
        'comments': '.opened-by',
    }

    # Labels indicating bounties/paid work
    BOUNTY_LABELS = [
        'bounty', 'paid', 'help wanted', 'good first issue',
        'hacktoberfest', 'funded', 'sponsor', 'grant',
    ]

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        """Main discovery"""
        self.stats['extractions'] += 1

        # Check for API response
        if context.api_response:
            opportunities = self._parse_api_response(context.api_response)
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
        """Extract via GitHub API"""
        try:
            import aiohttp

            headers = {'Accept': 'application/vnd.github.v3+json'}
            if self._credentials and self._credentials.get('token'):
                headers['Authorization'] = f"token {self._credentials['token']}"

            opportunities = []

            async with aiohttp.ClientSession() as session:
                # Search for bounty/paid issues
                query = 'label:bounty+label:paid+state:open'
                async with session.get(
                    f"{self.API_BASE}/search/issues?q={query}&per_page=50",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data.get('items', []):
                            opp = self._parse_issue(item)
                            if opp:
                                opportunities.append(opp)

            return opportunities if opportunities else None

        except Exception as e:
            logger.error(f"[github] API extraction failed: {e}")
            return None

    def _parse_api_response(self, data: Dict) -> List[Dict]:
        """Parse GitHub API response"""
        opportunities = []

        items = data.get('items', []) if isinstance(data, dict) else data

        for item in items:
            opp = self._parse_issue(item)
            if opp:
                opportunities.append(opp)

        return opportunities

    def _parse_issue(self, issue: Dict) -> Optional[Dict]:
        """Parse GitHub issue"""
        title = issue.get('title', '')
        if not title:
            return None

        url = issue.get('html_url', '')

        # Get labels
        labels = [l.get('name', '') for l in issue.get('labels', [])]

        # Check if it's a bounty
        is_bounty = any(
            bl.lower() in label.lower()
            for label in labels
            for bl in self.BOUNTY_LABELS
        )

        # Extract bounty amount from title/body
        bounty_amount = self._extract_bounty_amount(
            f"{title} {issue.get('body', '')}"
        )

        return {
            'platform': self.PLATFORM,
            'title': title[:200],
            'url': url,
            'body': (issue.get('body', '') or '')[:1000],
            'type': 'bounty' if is_bounty else 'opportunity',
            'value': bounty_amount,
            'discovered_at': datetime.now(timezone.utc).isoformat(),
            'source_data': {
                'github_id': issue.get('id'),
                'number': issue.get('number'),
                'state': issue.get('state'),
                'labels': labels,
                'user': issue.get('user', {}).get('login'),
                'comments': issue.get('comments', 0),
                'created_at': issue.get('created_at'),
                'repo': self._extract_repo(url),
            }
        }

    def _extract_bounty_amount(self, text: str) -> Optional[float]:
        """Extract bounty amount from text"""
        if not text:
            return None

        # Common bounty patterns
        patterns = [
            r'bounty[:\s]+\$?([\d,]+)',
            r'\$([\d,]+)\s*bounty',
            r'reward[:\s]+\$?([\d,]+)',
            r'\$([\d,]+)\s*reward',
            r'pay[:\s]+\$?([\d,]+)',
        ]

        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except:
                    pass

        return None

    def _extract_repo(self, url: str) -> str:
        """Extract repo name from URL"""
        match = re.search(r'github\.com/([^/]+/[^/]+)', url)
        return match.group(1) if match else ''

    async def extract_via_selectors(self, context: ExtractionContext) -> List[Dict]:
        """Extract using CSS selectors"""
        opportunities = []

        if not context.html:
            return opportunities

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context.html, 'html.parser')

            # Find issue rows
            items = soup.select(self.SELECTORS['listing'])[:50]

            for item in items:
                opp = self._extract_issue_element(item, context.url)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"[github] Selector extraction failed: {e}")

        return opportunities

    def _extract_issue_element(self, element, base_url: str) -> Optional[Dict]:
        """Extract issue from HTML element"""
        try:
            from urllib.parse import urljoin

            # Get title and URL
            title_elem = element.select_one(self.SELECTORS['title'])
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')

            if not title:
                return None

            if url and not url.startswith('http'):
                url = urljoin(self.BASE_URL, url)

            # Get labels
            label_elems = element.select(self.SELECTORS['labels'])
            labels = [l.get_text(strip=True) for l in label_elems]

            # Check if bounty
            is_bounty = any(
                bl.lower() in label.lower()
                for label in labels
                for bl in self.BOUNTY_LABELS
            )

            return {
                'platform': self.PLATFORM,
                'title': title[:200],
                'url': url or base_url,
                'body': '',
                'type': 'bounty' if is_bounty else 'opportunity',
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'source_data': {
                    'labels': labels,
                }
            }

        except Exception as e:
            logger.debug(f"[github] Issue extraction failed: {e}")
            return None

    def get_bounty_search_url(self) -> str:
        """Get URL for bounty search"""
        return f"{self.BASE_URL}/search?q=label%3Abounty+state%3Aopen&type=Issues"
