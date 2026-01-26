"""
ULTIMATE DISCOVERY SYSTEM
Internet-wide real-time discovery + instant fulfillment

50+ platforms, 100% fresh, legal-safe, multilingual, production-grade
"""

from .real_time_sources import REAL_TIME_SOURCES, get_platform_freshness_hours
from .collector_runtime import CollectorRuntime
from .i18n_normalizer import I18nNormalizer
from .intent_signals import IntentScorer
from .safety_filter import SafetyFilter
from .entity_resolution import EntityResolver
from .internet_wide_scraper import InternetWideScraper
from .streams import StreamIngestor
from .continuous_discovery import ContinuousDiscovery

__all__ = [
    'REAL_TIME_SOURCES',
    'get_platform_freshness_hours',
    'CollectorRuntime',
    'I18nNormalizer',
    'IntentScorer',
    'SafetyFilter',
    'EntityResolver',
    'InternetWideScraper',
    'StreamIngestor',
    'ContinuousDiscovery'
]
