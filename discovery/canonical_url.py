"""
URL CANONICALIZATION: Normalize URLs for Deduplication

Features:
- Protocol normalization
- Domain normalization (www removal, case)
- Path normalization (trailing slash, encoding)
- Query parameter filtering (tracking removal)
- Platform-specific rules
"""

import re
import hashlib
from typing import Optional, Dict, Set
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, unquote
import logging

logger = logging.getLogger(__name__)


# Tracking parameters to remove
TRACKING_PARAMS: Set[str] = {
    # Google
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
    'gclid', 'gclsrc', 'dclid',
    # Facebook
    'fbclid', 'fb_action_ids', 'fb_action_types', 'fb_source',
    # Twitter
    'twclid',
    # LinkedIn
    'li_fat_id', 'li_gc',
    # Microsoft
    'msclkid',
    # Mailchimp
    'mc_cid', 'mc_eid',
    # General
    'ref', 'source', 'referrer', 'campaign',
    '_ga', '_gl', '_hsenc', '_hsmi',
    'mkt_tok', 'trk', 'trkCampaign',
}

# Platform-specific normalization rules
PLATFORM_RULES: Dict[str, Dict] = {
    'upwork': {
        'remove_params': {'nv', 'uid', 'sort', 'page'},
        'keep_path_segments': 3,  # /jobs/~xxx/yyy -> keep 3 segments
    },
    'freelancer': {
        'remove_params': {'source', 'funnel'},
    },
    'linkedin': {
        'remove_params': {'trk', 'trkInfo', 'originalSubdomain'},
        'remove_fragment': True,
    },
    'twitter': {
        'normalize_host': 'twitter.com',  # x.com -> twitter.com
        'remove_params': {'s', 't'},
    },
    'reddit': {
        'remove_params': {'utm_name', 'context'},
        'remove_fragment': True,
    },
    'hackernews': {
        'keep_params': {'id'},  # Only keep ID param
    },
    'github': {
        'remove_params': {'tab'},
    },
    'producthunt': {
        'remove_params': {'ref', 'utm_source'},
    },
    'crunchbase': {
        'remove_params': {'utm_source', 'utm_medium'},
    },
}


class URLCanonicalizer:
    """
    Normalize URLs for consistent deduplication.

    Handles:
    - Protocol normalization (http -> https)
    - Domain normalization (www removal, lowercase)
    - Path normalization (encoding, trailing slash)
    - Query parameter filtering
    - Platform-specific rules
    """

    def __init__(self, platform_rules: Optional[Dict] = None):
        self.platform_rules = platform_rules or PLATFORM_RULES
        self.stats = {
            'canonicalized': 0,
            'invalid': 0,
            'platform_rules_applied': 0,
        }

    def canonicalize(self, url: str, platform: Optional[str] = None) -> str:
        """
        Canonicalize URL for deduplication.

        Args:
            url: Raw URL to normalize
            platform: Optional platform hint for specific rules

        Returns:
            Canonical URL string
        """
        if not url:
            return ''

        try:
            self.stats['canonicalized'] += 1

            # Parse URL
            parsed = urlparse(url.strip())

            # Normalize protocol (prefer https)
            scheme = 'https' if parsed.scheme in ('http', 'https', '') else parsed.scheme

            # Normalize domain
            netloc = self._normalize_domain(parsed.netloc, platform)
            if not netloc:
                self.stats['invalid'] += 1
                return url.lower().strip()

            # Normalize path
            path = self._normalize_path(parsed.path)

            # Normalize query params
            query = self._normalize_query(parsed.query, platform)

            # Handle fragment (usually remove)
            fragment = ''
            if platform and self.platform_rules.get(platform, {}).get('remove_fragment'):
                fragment = ''
            elif parsed.fragment and not parsed.fragment.startswith('!'):
                # Keep hashbang URLs (#!) but remove regular fragments
                fragment = ''

            # Reconstruct
            canonical = urlunparse((scheme, netloc, path, '', query, fragment))

            return canonical

        except Exception as e:
            logger.debug(f"[canonical_url] Failed to canonicalize {url}: {e}")
            self.stats['invalid'] += 1
            return url.lower().strip()

    def _normalize_domain(self, netloc: str, platform: Optional[str] = None) -> str:
        """Normalize domain/netloc"""
        if not netloc:
            return ''

        # Lowercase
        netloc = netloc.lower()

        # Remove www prefix
        if netloc.startswith('www.'):
            netloc = netloc[4:]

        # Remove default ports
        if netloc.endswith(':80'):
            netloc = netloc[:-3]
        elif netloc.endswith(':443'):
            netloc = netloc[:-4]

        # Platform-specific domain normalization
        if platform:
            rules = self.platform_rules.get(platform, {})
            if rules.get('normalize_host'):
                # Handle domain aliases (e.g., x.com -> twitter.com)
                if 'x.com' in netloc:
                    netloc = netloc.replace('x.com', 'twitter.com')

        return netloc

    def _normalize_path(self, path: str) -> str:
        """Normalize URL path"""
        if not path:
            return '/'

        # Decode percent-encoded characters
        path = unquote(path)

        # Remove duplicate slashes
        path = re.sub(r'/+', '/', path)

        # Remove trailing slash (except for root)
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')

        # Resolve . and .. segments
        segments = []
        for segment in path.split('/'):
            if segment == '..':
                if segments:
                    segments.pop()
            elif segment != '.':
                segments.append(segment)
        path = '/'.join(segments) or '/'

        return path

    def _normalize_query(self, query: str, platform: Optional[str] = None) -> str:
        """Normalize query parameters"""
        if not query:
            return ''

        # Parse query
        params = parse_qs(query, keep_blank_values=False)

        # Get platform rules
        rules = self.platform_rules.get(platform, {}) if platform else {}
        remove_params = rules.get('remove_params', set())
        keep_params = rules.get('keep_params')

        # Filter parameters
        filtered = {}
        for key, values in params.items():
            key_lower = key.lower()

            # Skip tracking params
            if key_lower in TRACKING_PARAMS:
                continue

            # Skip platform-specific remove params
            if key_lower in remove_params:
                self.stats['platform_rules_applied'] += 1
                continue

            # If keep_params specified, only keep those
            if keep_params is not None and key_lower not in keep_params:
                continue

            # Keep param
            filtered[key] = values

        # Sort parameters for consistency
        sorted_params = sorted(filtered.items())

        # Encode
        return urlencode(sorted_params, doseq=True)

    def generate_dedup_key(self, url: str, platform: Optional[str] = None) -> str:
        """
        Generate deduplication key from URL.

        Returns a short hash suitable for index lookups.
        """
        canonical = self.canonicalize(url, platform)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def get_stats(self) -> Dict:
        """Get canonicalization stats"""
        return self.stats.copy()


# Singleton instance
_canonicalizer: Optional[URLCanonicalizer] = None


def get_canonicalizer() -> URLCanonicalizer:
    """Get or create canonicalizer instance"""
    global _canonicalizer
    if _canonicalizer is None:
        _canonicalizer = URLCanonicalizer()
    return _canonicalizer


def canonicalize_url(url: str, platform: Optional[str] = None) -> str:
    """Convenience function to canonicalize URL"""
    return get_canonicalizer().canonicalize(url, platform)


def generate_dedup_key(url: str, platform: Optional[str] = None) -> str:
    """Convenience function to generate dedup key"""
    return get_canonicalizer().generate_dedup_key(url, platform)
