"""
PLATFORM PACK INTERFACE: Base Class for All Platform Adapters

Priority hierarchy:
1. API - Official API if available (most reliable)
2. Flow - Browser automation flow
3. Selectors - CSS selectors with auto-healing
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PackPriority(Enum):
    """Extraction method priority"""
    API = 1       # Official API - highest priority
    FLOW = 2      # Browser automation flow
    SELECTORS = 3  # CSS selectors


@dataclass
class PackConfig:
    """Configuration for a platform pack"""
    platform: str
    base_url: str
    rate_limit: float = 0.5  # requests per second
    requires_auth: bool = False
    auth_type: str = "none"  # none, oauth, api_key, cookie
    priority: PackPriority = PackPriority.SELECTORS
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionContext:
    """Context passed to extraction methods"""
    html: Optional[str] = None
    url: str = ""
    api_response: Optional[Dict] = None
    cookies: Optional[Dict] = None
    headers: Optional[Dict] = None
    platform_config: Optional[PackConfig] = None


class PlatformPack(ABC):
    """
    Base class for all platform-specific extraction packs.

    Each pack implements:
    - Platform configuration
    - API extraction (if available)
    - Flow-based extraction
    - Selector-based extraction
    """

    # Override in subclass
    PLATFORM: str = "base"
    BASE_URL: str = ""
    RATE_LIMIT: float = 0.5
    REQUIRES_AUTH: bool = False
    AUTH_TYPE: str = "none"
    PRIORITY: PackPriority = PackPriority.SELECTORS

    # Selectors for extraction (override in subclass)
    SELECTORS: Dict[str, str] = {}

    # API endpoints (override in subclass)
    API_ENDPOINTS: Dict[str, str] = {}

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._credentials: Optional[Dict] = None
        self.stats = {
            'extractions': 0,
            'api_successes': 0,
            'flow_successes': 0,
            'selector_successes': 0,
            'failures': 0,
        }

    def get_config(self) -> PackConfig:
        """Get pack configuration"""
        return PackConfig(
            platform=self.PLATFORM,
            base_url=self.BASE_URL,
            rate_limit=self.RATE_LIMIT,
            requires_auth=self.REQUIRES_AUTH,
            auth_type=self.AUTH_TYPE,
            priority=self.PRIORITY,
            metadata=self.config,
        )

    def set_credentials(self, credentials: Dict):
        """Set authentication credentials"""
        self._credentials = credentials

    @abstractmethod
    async def discover(self, context: ExtractionContext) -> List[Dict]:
        """
        Main discovery method - orchestrates extraction strategy.

        Args:
            context: Extraction context with HTML/API data

        Returns:
            List of discovered opportunities
        """
        pass

    async def extract_via_api(self, context: ExtractionContext) -> Optional[List[Dict]]:
        """
        Extract using official API.

        Override in subclass if platform has API.
        Returns None if API not available/failed.
        """
        return None

    async def extract_via_flow(self, context: ExtractionContext) -> Optional[List[Dict]]:
        """
        Extract using browser automation flow.

        Override in subclass for complex interactions.
        Returns None if flow not implemented/failed.
        """
        return None

    async def extract_via_selectors(self, context: ExtractionContext) -> List[Dict]:
        """
        Extract using CSS selectors.

        Default implementation uses SELECTORS dict.
        Override for custom logic.
        """
        opportunities = []

        if not context.html:
            return opportunities

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(context.html, 'html.parser')

            # Find listing container
            listing_selector = self.SELECTORS.get('listing', 'article, .item, .job')
            items = soup.select(listing_selector)[:100]

            for item in items:
                opp = self._extract_item(item, context.url)
                if opp:
                    opportunities.append(opp)

        except Exception as e:
            logger.error(f"[{self.PLATFORM}] Selector extraction failed: {e}")

        return opportunities

    def _extract_item(self, element, base_url: str) -> Optional[Dict]:
        """Extract opportunity from HTML element"""
        try:
            from urllib.parse import urljoin

            # Extract fields using selectors
            title = self._select_text(element, self.SELECTORS.get('title', 'a, h1, h2, h3'))
            url = self._select_attr(element, self.SELECTORS.get('url', 'a'), 'href')
            description = self._select_text(element, self.SELECTORS.get('description', '.description, p'))
            budget = self._select_text(element, self.SELECTORS.get('budget', '.budget, .price, .salary'))
            company = self._select_text(element, self.SELECTORS.get('company', '.company, .author'))

            if not title or len(title) < 5:
                return None

            # Make URL absolute
            if url and not url.startswith('http'):
                url = urljoin(base_url, url)

            return {
                'platform': self.PLATFORM,
                'title': title[:200],
                'url': url or base_url,
                'body': description[:1000] if description else '',
                'value': self._parse_budget(budget),
                'company': company,
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'type': 'opportunity',
            }

        except Exception as e:
            logger.debug(f"[{self.PLATFORM}] Item extraction failed: {e}")
            return None

    def _select_text(self, element, selector: str) -> Optional[str]:
        """Select and extract text from element"""
        try:
            found = element.select_one(selector)
            if found:
                return found.get_text(strip=True)
        except:
            pass
        return None

    def _select_attr(self, element, selector: str, attr: str) -> Optional[str]:
        """Select and extract attribute from element"""
        try:
            found = element.select_one(selector)
            if found:
                return found.get(attr)
        except:
            pass
        return None

    def _parse_budget(self, budget_str: Optional[str]) -> Optional[float]:
        """Parse budget string to float"""
        if not budget_str:
            return None

        import re
        # Find first number in string
        match = re.search(r'[\d,]+(?:\.\d+)?', budget_str.replace(',', ''))
        if match:
            try:
                return float(match.group())
            except:
                pass
        return None

    def get_stats(self) -> Dict:
        """Get pack statistics"""
        return {
            'platform': self.PLATFORM,
            **self.stats,
        }


class GenericPack(PlatformPack):
    """
    Generic pack for unknown platforms.

    Uses common selectors and patterns.
    """

    PLATFORM = "generic"
    PRIORITY = PackPriority.SELECTORS

    SELECTORS = {
        'listing': 'article, .item, .job, .listing, .post, .story, tr',
        'title': 'a, h1, h2, h3, .title',
        'url': 'a[href]',
        'description': '.description, .body, p, .summary',
        'budget': '.price, .budget, .salary, .pay',
        'company': '.company, .author, .poster, .by',
    }

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        """Generic discovery - just use selectors"""
        self.stats['extractions'] += 1

        opportunities = await self.extract_via_selectors(context)

        if opportunities:
            self.stats['selector_successes'] += 1
        else:
            self.stats['failures'] += 1

        return opportunities
