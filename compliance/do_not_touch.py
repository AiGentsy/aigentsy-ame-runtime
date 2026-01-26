"""
DO NOT TOUCH: Blocked Domains Registry

Features:
- Permanent blocklist for legal/ethical reasons
- Pattern-based blocking
- Reason tracking
- Runtime additions
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# Domains we must never touch
BLOCKED_DOMAINS: Dict[str, str] = {
    # Legal/Terms of Service
    'facebook.com': 'TOS violation risk',
    'www.facebook.com': 'TOS violation risk',
    'instagram.com': 'TOS violation risk',
    'www.instagram.com': 'TOS violation risk',

    # Government sensitive
    'cia.gov': 'Government sensitive',
    'fbi.gov': 'Government sensitive',
    'nsa.gov': 'Government sensitive',
    'dhs.gov': 'Government sensitive',

    # Financial regulatory
    'sec.gov': 'Regulatory - use official API',
    'finra.org': 'Regulatory',

    # Healthcare
    'hhs.gov': 'Healthcare sensitive',

    # Military
    'army.mil': 'Military',
    'navy.mil': 'Military',
    'af.mil': 'Military',

    # Known scam aggregators
    'scam-site.example': 'Known scam',
}

# Patterns to block
BLOCKED_PATTERNS: List[Tuple[str, str]] = [
    (r'\.mil$', 'Military domain'),
    (r'\.gov\.uk$', 'UK Government'),
    (r'darkweb|onion|tor\.', 'Dark web'),
    (r'pirate|warez|crack', 'Piracy'),
    (r'phishing|malware', 'Security threat'),
]


class DNTRegistry:
    """
    Do Not Touch Registry - domains we must never scrape.

    Reasons:
    - Terms of Service violations
    - Legal restrictions
    - Government sensitive
    - Security threats
    - Ethical concerns
    """

    def __init__(
        self,
        blocked_domains: Optional[Dict[str, str]] = None,
        blocked_patterns: Optional[List[Tuple[str, str]]] = None
    ):
        self.blocked_domains = blocked_domains or BLOCKED_DOMAINS.copy()
        self.blocked_patterns = blocked_patterns or BLOCKED_PATTERNS.copy()

        # Compile patterns
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), reason)
            for pattern, reason in self.blocked_patterns
        ]

        # Runtime additions
        self.runtime_blocks: Dict[str, str] = {}

        self.stats = {
            'checked': 0,
            'blocked': 0,
            'domain_blocks': 0,
            'pattern_blocks': 0,
        }

    def is_blocked(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Check if URL is blocked.

        Returns:
            Tuple of (is_blocked, reason)
        """
        self.stats['checked'] += 1

        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()

            if not host:
                return False, None

            # Check exact domain match
            if host in self.blocked_domains:
                self.stats['blocked'] += 1
                self.stats['domain_blocks'] += 1
                reason = self.blocked_domains[host]
                logger.info(f"[dnt] Blocked {host}: {reason}")
                return True, reason

            # Check runtime blocks
            if host in self.runtime_blocks:
                self.stats['blocked'] += 1
                self.stats['domain_blocks'] += 1
                reason = self.runtime_blocks[host]
                return True, reason

            # Check domain without www
            host_no_www = host.replace('www.', '')
            if host_no_www in self.blocked_domains:
                self.stats['blocked'] += 1
                self.stats['domain_blocks'] += 1
                reason = self.blocked_domains[host_no_www]
                return True, reason

            # Check patterns
            for pattern, reason in self.compiled_patterns:
                if pattern.search(url):
                    self.stats['blocked'] += 1
                    self.stats['pattern_blocks'] += 1
                    logger.info(f"[dnt] Pattern blocked {url}: {reason}")
                    return True, reason

            return False, None

        except Exception as e:
            logger.debug(f"[dnt] Error checking {url}: {e}")
            return False, None

    def add_block(self, domain: str, reason: str):
        """Add domain to runtime blocklist"""
        domain = domain.lower().replace('www.', '')
        self.runtime_blocks[domain] = reason
        logger.info(f"[dnt] Added block: {domain} ({reason})")

    def remove_block(self, domain: str):
        """Remove domain from runtime blocklist"""
        domain = domain.lower().replace('www.', '')
        if domain in self.runtime_blocks:
            del self.runtime_blocks[domain]
            logger.info(f"[dnt] Removed block: {domain}")

    def get_blocked_domains(self) -> List[Dict]:
        """Get all blocked domains with reasons"""
        domains = []

        for domain, reason in self.blocked_domains.items():
            domains.append({
                'domain': domain,
                'reason': reason,
                'type': 'permanent',
            })

        for domain, reason in self.runtime_blocks.items():
            domains.append({
                'domain': domain,
                'reason': reason,
                'type': 'runtime',
            })

        return domains

    def filter_urls(self, urls: List[str]) -> List[str]:
        """Filter list of URLs, removing blocked ones"""
        return [url for url in urls if not self.is_blocked(url)[0]]

    def filter_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Filter opportunities, removing those with blocked URLs"""
        filtered = []
        for opp in opportunities:
            url = opp.get('url', '')
            is_blocked, reason = self.is_blocked(url)
            if is_blocked:
                opp['blocked'] = True
                opp['blocked_reason'] = reason
            else:
                filtered.append(opp)
        return filtered

    def get_stats(self) -> Dict:
        """Get registry stats"""
        return {
            **self.stats,
            'permanent_blocks': len(self.blocked_domains),
            'runtime_blocks': len(self.runtime_blocks),
            'patterns': len(self.blocked_patterns),
        }


# Singleton
_dnt_registry: Optional[DNTRegistry] = None


def get_dnt_registry() -> DNTRegistry:
    """Get or create DNT registry instance"""
    global _dnt_registry
    if _dnt_registry is None:
        _dnt_registry = DNTRegistry()
    return _dnt_registry
