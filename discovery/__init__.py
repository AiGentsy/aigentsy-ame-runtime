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
from .hybrid_discovery import HybridDiscoveryEngine, get_hybrid_discovery, discover_with_contact
from .multi_source_discovery import MultiSourceDiscovery, get_multi_source_discovery, discover_all

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
    'ContinuousDiscovery',
    # Hybrid discovery (Perplexity + Direct API enrichment)
    'HybridDiscoveryEngine',
    'get_hybrid_discovery',
    'discover_with_contact',
    # Multi-source discovery (ALL configured APIs in parallel)
    'MultiSourceDiscovery',
    'get_multi_source_discovery',
    'discover_all',
]
