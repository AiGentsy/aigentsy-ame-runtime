"""
I18N NORMALIZER: Multilingual Support for Global Discovery

Features:
- Auto-detect language (40+ languages)
- Translate to English for scoring
- Keep original for outreach
- Translation caching
"""

import logging
from typing import Dict, Optional, Tuple
import hashlib

logger = logging.getLogger(__name__)

# Try to import language detection libraries
try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not installed - language detection disabled")

# Try to import translation library
try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    logger.warning("googletrans not installed - translation disabled")


class I18nNormalizer:
    """
    Multilingual support for opportunity discovery.

    - Detects language of opportunity text
    - Translates non-English to English for scoring
    - Preserves original text for outreach
    - Caches translations to reduce API calls
    """

    def __init__(self, cache_size: int = 10000):
        self.cache: Dict[str, Tuple[str, str]] = {}  # hash -> (title_en, body_en)
        self.cache_size = cache_size

        if GOOGLETRANS_AVAILABLE:
            self.translator = Translator()
        else:
            self.translator = None

        # Stats
        self.stats = {
            'processed': 0,
            'english': 0,
            'translated': 0,
            'cache_hits': 0,
            'detection_failed': 0,
            'translation_failed': 0,
        }

    def _cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.sha256(text[:500].encode('utf-8')).hexdigest()[:16]

    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        if not text or len(text) < 10:
            return 'en'  # Default to English for short text

        if not LANGDETECT_AVAILABLE:
            return 'unknown'

        try:
            return detect(text)
        except LangDetectException:
            return 'unknown'
        except Exception as e:
            logger.debug(f"Language detection failed: {e}")
            return 'unknown'

    def translate_to_english(self, text: str, source_lang: str = 'auto') -> Optional[str]:
        """Translate text to English"""
        if not text:
            return text

        if not GOOGLETRANS_AVAILABLE or self.translator is None:
            return text  # Return original if translation unavailable

        try:
            result = self.translator.translate(text[:2000], dest='en', src=source_lang)
            return result.text
        except Exception as e:
            logger.debug(f"Translation failed: {e}")
            return text  # Return original on failure

    def normalize_language(self, opp: Dict) -> Dict:
        """
        Add language detection and English translation to opportunity.

        Adds:
        - lang: detected language code
        - title_en: English title (translated if needed)
        - body_en: English body (translated if needed)
        """
        self.stats['processed'] += 1

        title = opp.get('title', '') or ''
        body = opp.get('body', '') or opp.get('description', '') or ''

        # Combine for detection
        text = f"{title} {body}".strip()

        if not text:
            opp['lang'] = 'en'
            opp['title_en'] = title
            opp['body_en'] = body
            return opp

        # Check cache first
        cache_key = self._cache_key(text)
        if cache_key in self.cache:
            self.stats['cache_hits'] += 1
            cached_title_en, cached_body_en = self.cache[cache_key]
            opp['title_en'] = cached_title_en
            opp['body_en'] = cached_body_en
            opp['lang'] = 'cached'
            return opp

        # Detect language
        lang = self.detect_language(text)
        opp['lang'] = lang

        if lang == 'unknown':
            self.stats['detection_failed'] += 1
            opp['title_en'] = title
            opp['body_en'] = body
            return opp

        # If English, no translation needed
        if lang == 'en':
            self.stats['english'] += 1
            opp['title_en'] = title
            opp['body_en'] = body
            return opp

        # Translate to English
        try:
            title_en = self.translate_to_english(title, lang) if title else ''
            body_en = self.translate_to_english(body[:1000], lang) if body else ''

            opp['title_en'] = title_en
            opp['body_en'] = body_en

            # Cache translation
            if len(self.cache) < self.cache_size:
                self.cache[cache_key] = (title_en, body_en)

            self.stats['translated'] += 1

        except Exception as e:
            logger.warning(f"Translation failed: {e}")
            self.stats['translation_failed'] += 1
            opp['title_en'] = title
            opp['body_en'] = body

        return opp

    def normalize_batch(self, opportunities: list) -> list:
        """Normalize language for batch of opportunities"""
        return [self.normalize_language(opp) for opp in opportunities]

    def get_stats(self) -> Dict:
        """Get normalization stats"""
        return {
            **self.stats,
            'cache_size': len(self.cache),
            'english_rate': self.stats['english'] / max(1, self.stats['processed']),
            'translation_rate': self.stats['translated'] / max(1, self.stats['processed']),
        }


# Singleton instance
_normalizer_instance: Optional[I18nNormalizer] = None


def get_i18n_normalizer() -> I18nNormalizer:
    """Get or create normalizer instance"""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = I18nNormalizer()
    return _normalizer_instance
