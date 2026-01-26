"""
PLATFORM PACKS: 106 Platform Implementations for Internet-Wide Discovery

Categories:
- Core packs (5): Upwork, HackerNews, Reddit, RemoteOK, GitHub
- HackerNews variants (4): new, show, ask, jobs
- Reddit subreddits (12): forhire, slavelabour, jobs, etc.
- Job boards (25): WeWorkRemotely, AngelList, Indeed, etc.
- Freelance marketplaces (15): Fiverr, Freelancer, Toptal, etc.
- Creative/Design (10): Dribbble, Behance, 99designs, etc.
- Tech communities (15): StackOverflow, IndieHackers, etc.
- International (10): Seek AU, TotalJobs UK, etc.
- Craigslist cities (5): SF, NYC, LA, Chicago, Boston
- Niche/Specialized (10): Crypto, Web3, AI, ML, etc.

Total: 106 platform packs
"""

import logging

logger = logging.getLogger(__name__)

# Core packs
from .upwork_pack import UpworkPack
from .hackernews_pack import HackerNewsPack
from .reddit_pack import RedditPack
from .remoteok_pack import RemoteOKPack
from .github_pack import GithubPack

CORE_PACKS = [
    UpworkPack(),
    HackerNewsPack(),
    RedditPack(),
    RemoteOKPack(),
    GithubPack(),
]

# HackerNews variants
try:
    from .hackernews_variants import HN_VARIANT_PACKS
    logger.info(f"Loaded {len(HN_VARIANT_PACKS)} HackerNews variant packs")
except ImportError as e:
    HN_VARIANT_PACKS = []
    logger.warning(f"Could not load HN variants: {e}")

# Reddit subreddits
try:
    from .reddit_subreddits import REDDIT_SUBREDDIT_PACKS
    logger.info(f"Loaded {len(REDDIT_SUBREDDIT_PACKS)} Reddit subreddit packs")
except ImportError as e:
    REDDIT_SUBREDDIT_PACKS = []
    logger.warning(f"Could not load Reddit subreddits: {e}")

# Job boards
try:
    from .job_boards import JOB_BOARD_PACKS
    logger.info(f"Loaded {len(JOB_BOARD_PACKS)} job board packs")
except ImportError as e:
    JOB_BOARD_PACKS = []
    logger.warning(f"Could not load job boards: {e}")

# Freelance marketplaces
try:
    from .freelance_marketplaces import FREELANCE_MARKETPLACE_PACKS
    logger.info(f"Loaded {len(FREELANCE_MARKETPLACE_PACKS)} freelance marketplace packs")
except ImportError as e:
    FREELANCE_MARKETPLACE_PACKS = []
    logger.warning(f"Could not load freelance marketplaces: {e}")

# Creative/Design
try:
    from .creative_design import CREATIVE_DESIGN_PACKS
    logger.info(f"Loaded {len(CREATIVE_DESIGN_PACKS)} creative/design packs")
except ImportError as e:
    CREATIVE_DESIGN_PACKS = []
    logger.warning(f"Could not load creative/design: {e}")

# Tech communities
try:
    from .tech_communities import TECH_COMMUNITY_PACKS
    logger.info(f"Loaded {len(TECH_COMMUNITY_PACKS)} tech community packs")
except ImportError as e:
    TECH_COMMUNITY_PACKS = []
    logger.warning(f"Could not load tech communities: {e}")

# International
try:
    from .international import INTERNATIONAL_PACKS
    logger.info(f"Loaded {len(INTERNATIONAL_PACKS)} international packs")
except ImportError as e:
    INTERNATIONAL_PACKS = []
    logger.warning(f"Could not load international: {e}")

# Craigslist cities
try:
    from .craigslist_cities import CRAIGSLIST_PACKS
    logger.info(f"Loaded {len(CRAIGSLIST_PACKS)} Craigslist city packs")
except ImportError as e:
    CRAIGSLIST_PACKS = []
    logger.warning(f"Could not load Craigslist cities: {e}")

# Niche/Specialized
try:
    from .niche_specialized import NICHE_SPECIALIZED_PACKS
    logger.info(f"Loaded {len(NICHE_SPECIALIZED_PACKS)} niche/specialized packs")
except ImportError as e:
    NICHE_SPECIALIZED_PACKS = []
    logger.warning(f"Could not load niche/specialized: {e}")


# Aggregate all packs
ALL_PACKS = (
    CORE_PACKS +
    HN_VARIANT_PACKS +
    REDDIT_SUBREDDIT_PACKS +
    JOB_BOARD_PACKS +
    FREELANCE_MARKETPLACE_PACKS +
    CREATIVE_DESIGN_PACKS +
    TECH_COMMUNITY_PACKS +
    INTERNATIONAL_PACKS +
    CRAIGSLIST_PACKS +
    NICHE_SPECIALIZED_PACKS
)

logger.info(f"Total platform packs loaded: {len(ALL_PACKS)}")


def get_all_packs():
    """Get list of all platform pack instances"""
    return ALL_PACKS


def get_pack_count():
    """Get total number of packs"""
    return len(ALL_PACKS)


def get_packs_by_category():
    """Get packs organized by category"""
    return {
        'core': CORE_PACKS,
        'hackernews_variants': HN_VARIANT_PACKS,
        'reddit_subreddits': REDDIT_SUBREDDIT_PACKS,
        'job_boards': JOB_BOARD_PACKS,
        'freelance_marketplaces': FREELANCE_MARKETPLACE_PACKS,
        'creative_design': CREATIVE_DESIGN_PACKS,
        'tech_communities': TECH_COMMUNITY_PACKS,
        'international': INTERNATIONAL_PACKS,
        'craigslist': CRAIGSLIST_PACKS,
        'niche_specialized': NICHE_SPECIALIZED_PACKS,
    }


__all__ = [
    # Core packs
    'UpworkPack',
    'HackerNewsPack',
    'RedditPack',
    'RemoteOKPack',
    'GithubPack',

    # Aggregated lists
    'ALL_PACKS',
    'CORE_PACKS',
    'HN_VARIANT_PACKS',
    'REDDIT_SUBREDDIT_PACKS',
    'JOB_BOARD_PACKS',
    'FREELANCE_MARKETPLACE_PACKS',
    'CREATIVE_DESIGN_PACKS',
    'TECH_COMMUNITY_PACKS',
    'INTERNATIONAL_PACKS',
    'CRAIGSLIST_PACKS',
    'NICHE_SPECIALIZED_PACKS',

    # Helper functions
    'get_all_packs',
    'get_pack_count',
    'get_packs_by_category',
]
