"""
ENTITY RESOLUTION: Deduplication at Internet Scale

Deduplicate opportunities across platforms using:
- URL canonicalization
- MinHash for near-duplicate text detection
- LSH index for fast lookups
"""

import hashlib
import logging
from typing import Dict, Optional, Set, List
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try to import MinHash libraries
try:
    from datasketch import MinHash, MinHashLSH
    MINHASH_AVAILABLE = True
except ImportError:
    MINHASH_AVAILABLE = False
    logger.warning("datasketch not installed - using simple deduplication")


class SimpleDeduplicator:
    """Simple deduplication without MinHash (fallback)"""

    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.seen_titles: Set[str] = set()

    def is_duplicate(self, opp: Dict) -> bool:
        """Check if opportunity is duplicate"""
        url = self.canonicalize_url(opp.get('url', ''))
        title = (opp.get('title', '') or '').lower().strip()[:100]

        if url and url in self.seen_urls:
            return True

        if title and title in self.seen_titles:
            return True

        # Not a duplicate - add to seen
        if url:
            self.seen_urls.add(url)
        if title:
            self.seen_titles.add(title)

        return False

    def canonicalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        if not url:
            return ''

        try:
            parsed = urlparse(url.lower().strip())

            # Remove www prefix
            netloc = parsed.netloc.replace('www.', '')

            # Remove trailing slash
            path = parsed.path.rstrip('/')

            # Remove tracking parameters
            query = parse_qs(parsed.query)
            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'source']
            query = {k: v for k, v in query.items() if k not in tracking_params}
            query_str = urlencode(query, doseq=True) if query else ''

            return urlunparse((parsed.scheme, netloc, path, '', query_str, ''))

        except Exception:
            return url.lower().strip()


class EntityResolver:
    """
    Deduplicate opportunities across platforms using:
    - URL canonicalization
    - MinHash for near-duplicate text detection (if available)
    - LSH index for fast lookups
    """

    def __init__(self, threshold: float = 0.8, num_perm: int = 128):
        self.threshold = threshold
        self.num_perm = num_perm

        self.seen_urls: Set[str] = set()
        self.seen_ids: Set[str] = set()

        # MinHash LSH index
        if MINHASH_AVAILABLE:
            self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
            self.use_minhash = True
        else:
            self.lsh = None
            self.use_minhash = False

        # Stats
        self.stats = {
            'processed': 0,
            'duplicates_url': 0,
            'duplicates_text': 0,
            'unique': 0,
        }

    def canonicalize_url(self, url: str) -> str:
        """Normalize URL for deduplication"""
        if not url:
            return ''

        try:
            parsed = urlparse(url.lower().strip())

            # Remove www prefix
            netloc = parsed.netloc.replace('www.', '')

            # Remove trailing slash
            path = parsed.path.rstrip('/')

            # Remove common tracking parameters
            query = parse_qs(parsed.query)
            tracking_params = [
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_content',
                'ref', 'source', 'fbclid', 'gclid', 'mc_cid', 'mc_eid'
            ]
            query = {k: v for k, v in query.items() if k not in tracking_params}
            query_str = urlencode(query, doseq=True) if query else ''

            return urlunparse((parsed.scheme, netloc, path, '', query_str, ''))

        except Exception:
            return url.lower().strip()

    def _text_signature(self, text: str) -> str:
        """Generate text signature for deduplication"""
        # Simple hash of normalized text
        normalized = ' '.join(text.lower().split())[:500]
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]

    def _minhash_signature(self, text: str) -> Optional['MinHash']:
        """Generate MinHash signature for text"""
        if not MINHASH_AVAILABLE or not text:
            return None

        m = MinHash(num_perm=self.num_perm)

        # Create 3-gram shingles
        words = text.lower().split()
        for i in range(max(1, len(words) - 2)):
            shingle = ' '.join(words[i:i+3])
            m.update(shingle.encode('utf8'))

        return m

    def near_dup_key(self, opp: Dict) -> str:
        """Generate deduplication key"""
        platform = opp.get('platform', 'unknown')
        url = self.canonicalize_url(opp.get('url', ''))

        # Get title for text-based dedup
        title = opp.get('title_en') or opp.get('title', '') or ''
        text_sig = self._text_signature(title)

        return f"{platform}|{url}|{text_sig}"

    def is_duplicate(self, opp: Dict) -> bool:
        """
        Check if opportunity is a duplicate.

        Uses multiple strategies:
        1. Exact URL match
        2. MinHash text similarity (if available)
        3. Title signature match
        """
        self.stats['processed'] += 1

        # Get canonical URL
        url = self.canonicalize_url(opp.get('url', ''))

        # Check exact URL match
        if url and url in self.seen_urls:
            self.stats['duplicates_url'] += 1
            return True

        # Check ID match
        opp_id = opp.get('id', '')
        if opp_id and opp_id in self.seen_ids:
            self.stats['duplicates_url'] += 1
            return True

        # MinHash text similarity check
        if self.use_minhash and self.lsh:
            title = opp.get('title_en') or opp.get('title', '') or ''
            if title and len(title) > 20:
                minhash = self._minhash_signature(title)
                if minhash:
                    # Query for similar items
                    results = self.lsh.query(minhash)
                    if results:
                        self.stats['duplicates_text'] += 1
                        return True

                    # Add to index
                    key = self.near_dup_key(opp)
                    try:
                        self.lsh.insert(key, minhash)
                    except Exception:
                        pass  # Key might already exist

        # Not a duplicate - add to seen sets
        if url:
            self.seen_urls.add(url)
        if opp_id:
            self.seen_ids.add(opp_id)

        self.stats['unique'] += 1
        return False

    def deduplicate_batch(self, opportunities: list) -> list:
        """Deduplicate batch of opportunities"""
        unique = []
        for opp in opportunities:
            if not self.is_duplicate(opp):
                unique.append(opp)

        logger.info(f"[entity_resolution] Deduped {len(opportunities)} -> {len(unique)}")
        return unique

    def get_stats(self) -> Dict:
        """Get deduplication stats"""
        return {
            **self.stats,
            'seen_urls': len(self.seen_urls),
            'seen_ids': len(self.seen_ids),
            'dedup_rate': (
                (self.stats['duplicates_url'] + self.stats['duplicates_text']) /
                max(1, self.stats['processed'])
            )
        }

    def reset(self):
        """Reset deduplication state"""
        self.seen_urls.clear()
        self.seen_ids.clear()
        if self.use_minhash:
            self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        self.stats = {k: 0 for k in self.stats}


# Singleton instance
_entity_resolver: Optional[EntityResolver] = None


def get_entity_resolver() -> EntityResolver:
    """Get or create entity resolver instance"""
    global _entity_resolver
    if _entity_resolver is None:
        _entity_resolver = EntityResolver()
    return _entity_resolver
