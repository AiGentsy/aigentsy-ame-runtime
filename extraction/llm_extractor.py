"""
LLM EXTRACTOR: Zero-Shot Learning for New Platforms

Features:
- Extract structured data from unknown HTML
- Learn selectors from successful extractions
- Generate platform packs automatically
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class ExtractionResult:
    """Result from LLM extraction"""
    data: Dict[str, Any]
    confidence: float
    selectors_learned: Dict[str, str]
    raw_response: str


class LLMExtractor:
    """
    Zero-shot extraction using LLM.

    For platforms without dedicated packs, use LLM to:
    1. Understand the page structure
    2. Extract opportunity data
    3. Learn selectors for future use
    """

    EXTRACTION_PROMPT = """Analyze this HTML page and extract opportunity/job listing information.

URL: {url}
Platform: {platform}

HTML (truncated):
```html
{html}
```

Extract the following fields if present:
- title: The job/opportunity title
- company: Company or poster name
- description: Full description text
- budget/salary: Any price, budget, or salary information
- skills: Required skills (as array)
- location: Location if mentioned
- contact: Any contact information (email, etc.)
- posted_date: When posted if available
- deadline: Application deadline if available

Also identify the CSS selectors used to find each field.

Return as JSON:
{{
  "data": {{
    "title": "...",
    "company": "...",
    "description": "...",
    "budget": "...",
    "skills": ["..."],
    "location": "...",
    "contact": "...",
    "posted_date": "...",
    "deadline": "..."
  }},
  "selectors": {{
    "title": "CSS selector used",
    "company": "CSS selector used",
    ...
  }},
  "confidence": 0.0 to 1.0,
  "page_type": "job_listing|freelance_gig|rfp|grant|unknown"
}}

Only return the JSON, no explanation."""

    BATCH_EXTRACTION_PROMPT = """Extract all opportunities from this listing page.

URL: {url}
Platform: {platform}

HTML (truncated):
```html
{html}
```

Extract each opportunity with:
- title, url, description, budget (if visible)

Return as JSON array:
[
  {{"title": "...", "url": "...", "description": "...", "budget": "..."}},
  ...
]

Only return the JSON array."""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo-16k"
    ):
        self.model = model

        if openai_api_key and OPENAI_AVAILABLE:
            openai.api_key = openai_api_key
            self.enabled = True
        else:
            self.enabled = False

        # Cache learned selectors
        self.learned_selectors: Dict[str, Dict[str, str]] = {}

        # Stats
        self.stats = {
            'extractions': 0,
            'successes': 0,
            'failures': 0,
            'selectors_learned': 0,
        }

    async def extract_single(
        self,
        html: str,
        url: str,
        platform: str = "unknown"
    ) -> Optional[ExtractionResult]:
        """
        Extract data from a single opportunity page.

        Args:
            html: Page HTML content
            url: Page URL
            platform: Platform name hint

        Returns:
            ExtractionResult or None if failed
        """
        if not self.enabled:
            logger.warning("[llm_extractor] LLM not available")
            return None

        self.stats['extractions'] += 1

        # Truncate HTML to fit context
        html_truncated = self._truncate_html(html, max_chars=10000)

        prompt = self.EXTRACTION_PROMPT.format(
            url=url,
            platform=platform,
            html=html_truncated,
        )

        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1000,
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            result = self._parse_json_response(content)

            if result and result.get('data'):
                self.stats['successes'] += 1

                # Learn selectors
                selectors = result.get('selectors', {})
                if selectors:
                    self._learn_selectors(platform, selectors)

                return ExtractionResult(
                    data=result['data'],
                    confidence=result.get('confidence', 0.5),
                    selectors_learned=selectors,
                    raw_response=content,
                )

        except Exception as e:
            logger.error(f"[llm_extractor] Extraction failed: {e}")

        self.stats['failures'] += 1
        return None

    async def extract_listings(
        self,
        html: str,
        url: str,
        platform: str = "unknown"
    ) -> List[Dict]:
        """
        Extract multiple opportunities from a listing page.

        Args:
            html: Page HTML content
            url: Page URL
            platform: Platform name hint

        Returns:
            List of extracted opportunities
        """
        if not self.enabled:
            return []

        self.stats['extractions'] += 1

        html_truncated = self._truncate_html(html, max_chars=15000)

        prompt = self.BATCH_EXTRACTION_PROMPT.format(
            url=url,
            platform=platform,
            html=html_truncated,
        )

        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000,
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON array
            opportunities = self._parse_json_response(content)

            if isinstance(opportunities, list):
                self.stats['successes'] += 1

                # Normalize and add metadata
                normalized = []
                for opp in opportunities:
                    if isinstance(opp, dict) and opp.get('title'):
                        opp['platform'] = platform
                        opp['discovered_at'] = datetime.now(timezone.utc).isoformat()
                        opp['extraction_method'] = 'llm_zero_shot'
                        normalized.append(opp)

                return normalized

        except Exception as e:
            logger.error(f"[llm_extractor] Batch extraction failed: {e}")

        self.stats['failures'] += 1
        return []

    def _truncate_html(self, html: str, max_chars: int = 10000) -> str:
        """Truncate HTML while keeping structure"""
        if len(html) <= max_chars:
            return html

        # Try to keep meaningful content
        # Remove scripts and styles first
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

        # Remove excessive whitespace
        html = re.sub(r'\s+', ' ', html)

        if len(html) <= max_chars:
            return html

        # Still too long - truncate at tag boundary
        return html[:max_chars].rsplit('<', 1)[0]

    def _parse_json_response(self, content: str) -> Optional[Any]:
        """Parse JSON from LLM response"""
        # Try direct parse
        try:
            return json.loads(content)
        except:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Try to find JSON object or array
        for start, end in [('{', '}'), ('[', ']')]:
            start_idx = content.find(start)
            if start_idx != -1:
                # Find matching end
                depth = 0
                for i, char in enumerate(content[start_idx:], start_idx):
                    if char == start:
                        depth += 1
                    elif char == end:
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(content[start_idx:i+1])
                            except:
                                break

        return None

    def _learn_selectors(self, platform: str, selectors: Dict[str, str]):
        """Store learned selectors for platform"""
        if platform not in self.learned_selectors:
            self.learned_selectors[platform] = {}

        for field, selector in selectors.items():
            if selector and selector not in ['null', 'undefined', '']:
                self.learned_selectors[platform][field] = selector
                self.stats['selectors_learned'] += 1

        logger.info(
            f"[llm_extractor] Learned {len(selectors)} selectors for {platform}"
        )

    def get_learned_selectors(self, platform: str) -> Dict[str, str]:
        """Get learned selectors for platform"""
        return self.learned_selectors.get(platform, {})

    def generate_pack_template(self, platform: str) -> str:
        """Generate platform pack template from learned selectors"""
        selectors = self.learned_selectors.get(platform, {})

        template = f'''"""
Platform Pack: {platform.title()}
Auto-generated from LLM extraction
"""

from platforms.pack_interface import PlatformPack


class {platform.title().replace("_", "")}Pack(PlatformPack):
    PLATFORM = "{platform}"

    SELECTORS = {{
'''

        for field, selector in selectors.items():
            template += f'        "{field}": "{selector}",\n'

        template += '''    }

    async def extract_opportunities(self, html: str) -> list:
        # Implementation based on learned selectors
        pass
'''

        return template

    def get_stats(self) -> Dict:
        """Get extractor stats"""
        return {
            **self.stats,
            'enabled': self.enabled,
            'platforms_learned': len(self.learned_selectors),
        }


# Singleton
_llm_extractor: Optional[LLMExtractor] = None


def get_llm_extractor(
    openai_api_key: Optional[str] = None
) -> LLMExtractor:
    """Get or create LLM extractor instance"""
    global _llm_extractor
    if _llm_extractor is None:
        _llm_extractor = LLMExtractor(openai_api_key)
    return _llm_extractor
