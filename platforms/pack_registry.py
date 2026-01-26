"""
PACK REGISTRY: Central Registry for Platform Packs

Features:
- Auto-discovery of packs
- Lazy loading
- Platform matching
- Stats aggregation
- Auto-registration of 106+ platform packs
"""

import logging
import importlib
import pkgutil
from typing import Dict, List, Optional, Type
from urllib.parse import urlparse

from .pack_interface import PlatformPack, GenericPack, PackConfig

logger = logging.getLogger(__name__)


# Extended URL patterns for all 106+ platforms
EXTENDED_URL_PATTERNS = {
    # Core platforms
    'upwork.com': 'upwork',
    'freelancer.com': 'freelancer',
    'fiverr.com': 'fiverr',
    'toptal.com': 'toptal',
    'linkedin.com': 'linkedin',
    'indeed.com': 'indeed',
    'glassdoor.com': 'glassdoor',
    'angellist.com': 'angellist',
    'angel.co': 'angellist',
    'weworkremotely.com': 'weworkremotely',
    'remoteok.com': 'remoteok',
    'remoteok.io': 'remoteok',
    'github.com': 'github',
    'producthunt.com': 'producthunt',
    'news.ycombinator.com': 'hackernews',
    'reddit.com': 'reddit',
    'twitter.com': 'twitter',
    'x.com': 'twitter',
    'crunchbase.com': 'crunchbase',

    # Job boards
    'remote.co': 'remote_co',
    'flexjobs.com': 'flexjobs',
    'justremote.co': 'justremote',
    'remoteleaf.com': 'remoteleaf',
    'workingnomads.com': 'workingnomads',
    'nodesk.co': 'nodesk',
    'remotehub.io': 'remotehub',
    'jobspresso.co': 'jobspresso',
    'authenticjobs.com': 'authenticjobs',
    'dribbble.com/jobs': 'dribbble_jobs',
    'behance.net/joblist': 'behance_jobs',
    'smashingmagazine.com/jobs': 'smashing_jobs',
    'stackoverflow.com/jobs': 'stackoverflow_jobs',
    'dice.com': 'dice',
    'hired.com': 'hired',
    'turing.com': 'turing',
    'gun.io': 'gun_io',
    'triplebyte.com': 'triplebyte',
    'a.]team': 'ateam',
    'braintrust.com': 'braintrust',
    'codementor.io': 'codementor',
    'arc.dev': 'arc',
    'crossover.com': 'crossover',
    'x-team.com': 'xteam',
    'lemon.io': 'lemon_io',

    # Freelance marketplaces
    'guru.com': 'guru',
    'peopleperhour.com': 'peopleperhour',
    'freelancermap.com': 'freelancermap',
    'servicescape.com': 'servicescape',
    'workmarket.com': 'workmarket',
    'kolabtree.com': 'kolabtree',
    'contently.com': 'contently',
    'clearvoice.com': 'clearvoice',
    'skyword.com': 'skyword',
    'scripted.com': 'scripted',
    'textbroker.com': 'textbroker',
    'constant-content.com': 'constantcontent',
    'crowdcontent.com': 'crowdcontent',
    'cactus.com': 'cactus',
    'wordsrus.com.au': 'wordsrus',

    # Creative/Design
    'dribbble.com': 'dribbble',
    'behance.net': 'behance',
    '99designs.com': '99designs',
    'designcrowd.com': 'designcrowd',
    'crowdspring.com': 'crowdspring',
    'designhill.com': 'designhill',
    'designcontest.com': 'designcontest',
    'designbro.com': 'designbro',
    'hatchwise.com': 'hatchwise',
    'looka.com': 'looka',

    # Tech communities
    'stackoverflow.com': 'stackoverflow_jobs',
    'hashnode.com': 'hashnode',
    'indiehackers.com': 'indiehackers',
    'betalist.com': 'betalist',
    'launchingnext.com': 'launching_next',
    'hackernoon.com': 'hacker_noon',
    'freecodecamp.org': 'freecodecamp_jobs',
    'daily.dev': 'daily_dev',
    'dev.to': 'dev_community',
    'lobste.rs': 'lobsters',
    'slashdot.org': 'slashdot_jobs',
    'techcrunch.com': 'techcrunch_jobs',
    'arstechnica.com': 'ars_technica_jobs',

    # International
    'seek.com.au': 'seek_au',
    'totaljobs.com': 'totaljobs_uk',
    'xing.com': 'xing_jobs',
    'jobberman.com': 'jobberman_africa',
    'naukri.com': 'naukri_india',
    'workopolis.com': 'workopolis_canada',
    'seek.co.nz': 'seek_nz',
    'jobstreet.com': 'jobstreet_asia',
    'europeremotely.com': 'europa_remotely',
    'getonbrd.com': 'latam_jobs',

    # Craigslist
    'sfbay.craigslist.org': 'craigslist_sf',
    'newyork.craigslist.org': 'craigslist_nyc',
    'losangeles.craigslist.org': 'craigslist_la',
    'chicago.craigslist.org': 'craigslist_chicago',
    'boston.craigslist.org': 'craigslist_boston',

    # Niche/Specialized
    'crypto.jobs': 'crypto_jobs',
    'web3.career': 'web3_jobs',
    'ai-jobs.net': 'ai_jobs',
    'mljobs.com': 'ml_jobs',
    'golangprojects.com': 'golang_jobs',
    'pythonjobs.com': 'python_jobs',
    'reactjobs.com': 'react_jobs',
    'vuejobs.com': 'vue_jobs',
    'rubyonrails.jobs': 'rails_jobs',
    'flutterjobs.info': 'flutter_jobs',

    # Government
    'regulations.gov': 'regulations_gov',
    'grants.gov': 'grants_gov',
    'sam.gov': 'sam_gov',
}


class PackRegistry:
    """
    Central registry for all platform packs.

    Responsibilities:
    - Register packs by platform name
    - Match URLs to appropriate packs
    - Lazy-load pack modules
    - Track pack statistics
    """

    def __init__(self):
        self._packs: Dict[str, PlatformPack] = {}
        self._pack_classes: Dict[str, Type[PlatformPack]] = {}
        self._url_patterns: Dict[str, str] = {}  # pattern -> platform
        self._generic_pack = GenericPack()

        # Auto-register built-in packs
        self._register_builtins()

    def _register_builtins(self):
        """Register built-in platform packs"""
        # Use extended URL patterns for all 106+ platforms
        self._url_patterns = EXTENDED_URL_PATTERNS.copy()

        # Auto-register all packs from the packs module
        self._auto_register_packs()

    def _auto_register_packs(self):
        """Auto-register all packs from the packs module"""
        try:
            from .packs import ALL_PACKS, get_pack_count

            registered_count = 0
            for pack in ALL_PACKS:
                try:
                    platform = pack.PLATFORM.lower()
                    self._packs[platform] = pack
                    registered_count += 1
                except Exception as e:
                    logger.warning(f"[registry] Failed to register pack: {e}")

            logger.info(f"[registry] Auto-registered {registered_count}/{get_pack_count()} packs")

        except ImportError as e:
            logger.warning(f"[registry] Could not import packs module: {e}")
        except Exception as e:
            logger.error(f"[registry] Auto-registration failed: {e}")

    def register(self, pack: PlatformPack):
        """Register a platform pack instance"""
        platform = pack.PLATFORM.lower()
        self._packs[platform] = pack
        logger.debug(f"[registry] Registered pack: {platform}")

    def register_class(self, pack_class: Type[PlatformPack]):
        """Register a platform pack class (lazy instantiation)"""
        platform = pack_class.PLATFORM.lower()
        self._pack_classes[platform] = pack_class
        logger.debug(f"[registry] Registered pack class: {platform}")

    def get_pack(self, platform: str) -> PlatformPack:
        """Get pack for platform (lazy instantiation)"""
        platform = platform.lower()

        # Check for instantiated pack
        if platform in self._packs:
            return self._packs[platform]

        # Check for registered class
        if platform in self._pack_classes:
            pack = self._pack_classes[platform]()
            self._packs[platform] = pack
            return pack

        # Try to import pack module
        pack = self._try_import_pack(platform)
        if pack:
            return pack

        # Return generic pack
        return self._generic_pack

    def get_pack_for_url(self, url: str) -> PlatformPack:
        """Get appropriate pack for URL"""
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower().replace('www.', '')

            # Check direct match
            for pattern, platform in self._url_patterns.items():
                if pattern in host:
                    return self.get_pack(platform)

        except Exception as e:
            logger.debug(f"[registry] URL parsing error: {e}")

        return self._generic_pack

    def identify_platform(self, url: str) -> str:
        """Identify platform from URL"""
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower().replace('www.', '')

            for pattern, platform in self._url_patterns.items():
                if pattern in host:
                    return platform

            # Return host as platform name
            return host.split('.')[0]

        except:
            return 'unknown'

    def _try_import_pack(self, platform: str) -> Optional[PlatformPack]:
        """Try to dynamically import pack module"""
        try:
            module_name = f"platforms.packs.{platform}_pack"
            module = importlib.import_module(module_name)

            # Find PlatformPack subclass in module
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    isinstance(obj, type) and
                    issubclass(obj, PlatformPack) and
                    obj is not PlatformPack
                ):
                    pack = obj()
                    self._packs[platform] = pack
                    return pack

        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"[registry] Failed to import {platform} pack: {e}")

        return None

    def list_packs(self) -> List[PackConfig]:
        """List all registered packs"""
        configs = []

        # Get configs from instantiated packs
        for pack in self._packs.values():
            configs.append(pack.get_config())

        # Get configs from registered classes
        for platform, pack_class in self._pack_classes.items():
            if platform not in self._packs:
                configs.append(PackConfig(
                    platform=platform,
                    base_url=pack_class.BASE_URL,
                    rate_limit=pack_class.RATE_LIMIT,
                    requires_auth=pack_class.REQUIRES_AUTH,
                ))

        return configs

    def get_all_platforms(self) -> List[str]:
        """Get list of all known platforms"""
        platforms = set()
        platforms.update(self._packs.keys())
        platforms.update(self._pack_classes.keys())
        platforms.update(self._url_patterns.values())
        return sorted(platforms)

    def get_stats(self) -> Dict:
        """Get aggregated stats from all packs"""
        total_stats = {
            'packs_registered': len(self._packs) + len(self._pack_classes),
            'platforms_known': len(self.get_all_platforms()),
            'extractions': 0,
            'successes': 0,
            'failures': 0,
        }

        pack_stats = {}
        for platform, pack in self._packs.items():
            stats = pack.get_stats()
            pack_stats[platform] = stats
            total_stats['extractions'] += stats.get('extractions', 0)
            total_stats['successes'] += (
                stats.get('api_successes', 0) +
                stats.get('flow_successes', 0) +
                stats.get('selector_successes', 0)
            )
            total_stats['failures'] += stats.get('failures', 0)

        return {
            **total_stats,
            'packs': pack_stats,
        }


# Singleton
_pack_registry: Optional[PackRegistry] = None


def get_pack_registry() -> PackRegistry:
    """Get or create pack registry instance"""
    global _pack_registry
    if _pack_registry is None:
        _pack_registry = PackRegistry()
    return _pack_registry
