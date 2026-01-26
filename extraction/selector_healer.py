"""
SELECTOR HEALER: LLM-Powered Auto-Healing for CSS Selectors

Features:
- Detect broken selectors
- Generate alternative selectors using LLM
- Track selector health metrics
- Automatic fallback chain
"""

import logging
import time
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available for selector healing")


@dataclass
class SelectorHealth:
    """Track selector health metrics"""
    selector: str
    platform: str
    success_count: int = 0
    failure_count: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    alternatives: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / max(1, total)

    @property
    def is_healthy(self) -> bool:
        return self.success_rate >= 0.8

    def to_dict(self) -> Dict:
        return {
            'selector': self.selector,
            'platform': self.platform,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': self.success_rate,
            'is_healthy': self.is_healthy,
            'alternatives': self.alternatives,
        }


# Common extraction patterns
EXTRACTION_PATTERNS = {
    'job_listing': {
        'title': [
            'h1.job-title', 'h1[class*="title"]', '.job-title',
            '[data-testid="job-title"]', 'h1', '.posting-title',
        ],
        'company': [
            '.company-name', '[data-testid="company"]', '.employer',
            'a[href*="/company/"]', '.organization',
        ],
        'description': [
            '.job-description', '[data-testid="description"]',
            '.description', '#job-description', '.posting-description',
        ],
        'salary': [
            '.salary', '[data-testid="salary"]', '.compensation',
            '.pay-range', '[class*="salary"]',
        ],
    },
    'freelance_gig': {
        'title': [
            'h1', '.job-title', '.gig-title', '.project-title',
        ],
        'budget': [
            '.budget', '.price', '[data-testid="budget"]',
            '.project-budget', '[class*="budget"]',
        ],
        'description': [
            '.description', '.job-description', '.project-description',
        ],
        'skills': [
            '.skills', '.tags', '.job-skills', '[data-testid="skills"]',
        ],
    },
}


class SelectorHealer:
    """
    Auto-heal broken CSS selectors using LLM.

    Flow:
    1. Try primary selector
    2. If fails, try alternatives from history
    3. If all fail, use LLM to generate new selectors
    4. Track success/failure for learning
    """

    LLM_PROMPT = """Given this HTML snippet, generate CSS selectors to extract the following field.

HTML:
```
{html_snippet}
```

Field to extract: {field_name}
Field description: {field_description}

Previous selectors that failed:
{failed_selectors}

Return a JSON array of 3-5 CSS selectors that would likely work, ordered by confidence.
Example: ["h1.title", "[data-field='title']", "h1"]

Only return the JSON array, no explanation."""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo"
    ):
        self.model = model

        if openai_api_key and OPENAI_AVAILABLE:
            openai.api_key = openai_api_key
            self.llm_enabled = True
        else:
            self.llm_enabled = False

        # Selector health tracking
        self.health: Dict[str, SelectorHealth] = {}

        # Stats
        self.stats = {
            'attempts': 0,
            'primary_success': 0,
            'alternative_success': 0,
            'llm_heals': 0,
            'total_failures': 0,
        }

    def _health_key(self, platform: str, selector: str) -> str:
        """Generate key for health tracking"""
        return f"{platform}:{selector}"

    def get_health(self, platform: str, selector: str) -> SelectorHealth:
        """Get or create health record for selector"""
        key = self._health_key(platform, selector)
        if key not in self.health:
            self.health[key] = SelectorHealth(
                selector=selector,
                platform=platform,
            )
        return self.health[key]

    def record_success(self, platform: str, selector: str):
        """Record successful selector use"""
        health = self.get_health(platform, selector)
        health.success_count += 1
        health.last_success = datetime.now(timezone.utc)

    def record_failure(self, platform: str, selector: str):
        """Record failed selector use"""
        health = self.get_health(platform, selector)
        health.failure_count += 1
        health.last_failure = datetime.now(timezone.utc)

    async def try_selectors(
        self,
        html: str,
        selectors: List[str],
        platform: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Try list of selectors in order.

        Returns:
            Tuple of (result, working_selector) or (None, None) if all fail
        """
        # Import BeautifulSoup
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return None, None

        soup = BeautifulSoup(html, 'html.parser')

        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text:
                        self.record_success(platform, selector)
                        return text, selector
                self.record_failure(platform, selector)
            except Exception as e:
                logger.debug(f"[selector_healer] Selector error: {e}")
                self.record_failure(platform, selector)

        return None, None

    async def extract_field(
        self,
        html: str,
        platform: str,
        field_name: str,
        primary_selector: Optional[str] = None,
        field_description: str = "",
    ) -> Tuple[Optional[str], Dict]:
        """
        Extract field with auto-healing.

        Args:
            html: HTML content
            platform: Platform name
            field_name: Name of field to extract
            primary_selector: Primary CSS selector to try
            field_description: Description for LLM context

        Returns:
            Tuple of (extracted_value, metadata)
        """
        self.stats['attempts'] += 1
        metadata = {'attempts': [], 'healed': False}

        # Build selector chain
        selectors = []

        # 1. Primary selector first
        if primary_selector:
            selectors.append(primary_selector)

        # 2. Add known alternatives from health tracking
        health = self.get_health(platform, primary_selector or '')
        selectors.extend(health.alternatives)

        # 3. Add pattern-based fallbacks
        for pattern_type, patterns in EXTRACTION_PATTERNS.items():
            if field_name in patterns:
                selectors.extend(patterns[field_name])

        # Deduplicate while preserving order
        seen = set()
        unique_selectors = []
        for s in selectors:
            if s and s not in seen:
                seen.add(s)
                unique_selectors.append(s)

        # Try selectors
        result, working_selector = await self.try_selectors(
            html, unique_selectors, platform
        )

        if result:
            if working_selector == primary_selector:
                self.stats['primary_success'] += 1
            else:
                self.stats['alternative_success'] += 1
                metadata['healed'] = True
                # Add to alternatives if new
                if working_selector not in health.alternatives:
                    health.alternatives.append(working_selector)

            metadata['selector'] = working_selector
            return result, metadata

        # All selectors failed - try LLM healing
        if self.llm_enabled:
            new_selectors = await self._llm_generate_selectors(
                html[:5000],  # Limit HTML size
                field_name,
                field_description,
                unique_selectors[:5],  # Failed selectors for context
            )

            if new_selectors:
                self.stats['llm_heals'] += 1
                result, working_selector = await self.try_selectors(
                    html, new_selectors, platform
                )

                if result:
                    metadata['healed'] = True
                    metadata['llm_generated'] = True
                    metadata['selector'] = working_selector
                    # Add to alternatives
                    if working_selector not in health.alternatives:
                        health.alternatives.append(working_selector)
                    return result, metadata

        self.stats['total_failures'] += 1
        return None, metadata

    async def _llm_generate_selectors(
        self,
        html_snippet: str,
        field_name: str,
        field_description: str,
        failed_selectors: List[str],
    ) -> List[str]:
        """Use LLM to generate new selector candidates"""
        if not self.llm_enabled:
            return []

        prompt = self.LLM_PROMPT.format(
            html_snippet=html_snippet,
            field_name=field_name,
            field_description=field_description or f"The {field_name} field",
            failed_selectors=', '.join(failed_selectors) or 'none',
        )

        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            selectors = json.loads(content)
            if isinstance(selectors, list):
                return [s for s in selectors if isinstance(s, str)]

        except Exception as e:
            logger.warning(f"[selector_healer] LLM error: {e}")

        return []

    def get_unhealthy_selectors(self, min_attempts: int = 10) -> List[Dict]:
        """Get list of unhealthy selectors needing attention"""
        unhealthy = []
        for key, health in self.health.items():
            total = health.success_count + health.failure_count
            if total >= min_attempts and not health.is_healthy:
                unhealthy.append(health.to_dict())

        return sorted(unhealthy, key=lambda x: x['success_rate'])

    def get_stats(self) -> Dict:
        """Get healer stats"""
        return {
            **self.stats,
            'tracked_selectors': len(self.health),
            'llm_enabled': self.llm_enabled,
        }


# Singleton
_selector_healer: Optional[SelectorHealer] = None


def get_selector_healer(
    openai_api_key: Optional[str] = None
) -> SelectorHealer:
    """Get or create selector healer instance"""
    global _selector_healer
    if _selector_healer is None:
        _selector_healer = SelectorHealer(openai_api_key)
    return _selector_healer
