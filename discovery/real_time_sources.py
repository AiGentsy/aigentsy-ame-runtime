"""
REAL-TIME SOURCES: 55+ Platforms for Internet-Wide Discovery

ZERO FAKE DATA - All URLs must be REAL, working endpoints
Platform-specific freshness windows enforce fresh discovery
"""

from typing import Dict

# =============================================================================
# 55+ REAL-TIME SOURCES
# =============================================================================

REAL_TIME_SOURCES: Dict[str, str] = {
    # =========================================================================
    # HACKERNEWS (High-quality tech opportunities)
    # =========================================================================
    'hackernews_new': 'https://news.ycombinator.com/newest',
    'hackernews_show': 'https://news.ycombinator.com/show',
    'hackernews_ask': 'https://news.ycombinator.com/ask',
    'hackernews_jobs': 'https://news.ycombinator.com/jobs',

    # =========================================================================
    # REDDIT (Job/gig subreddits - HIGH VOLUME)
    # =========================================================================
    'reddit_forhire': 'https://www.reddit.com/r/forhire/new/.json',
    'reddit_slavelabour': 'https://www.reddit.com/r/slavelabour/new/.json',
    'reddit_jobs': 'https://www.reddit.com/r/jobs/new/.json',
    'reddit_startup': 'https://www.reddit.com/r/startups/new/.json',
    'reddit_entrepreneur': 'https://www.reddit.com/r/Entrepreneur/new/.json',
    'reddit_sideproject': 'https://www.reddit.com/r/SideProject/new/.json',
    'reddit_programming': 'https://www.reddit.com/r/programming/new/.json',
    'reddit_webdev': 'https://www.reddit.com/r/webdev/new/.json',
    'reddit_freelance': 'https://www.reddit.com/r/freelance/new/.json',
    'reddit_remotejobs': 'https://www.reddit.com/r/remotejobs/new/.json',
    'reddit_hireawriter': 'https://www.reddit.com/r/HireaWriter/new/.json',
    'reddit_designjobs': 'https://www.reddit.com/r/DesignJobs/new/.json',

    # =========================================================================
    # TECH COMMUNITIES
    # =========================================================================
    'devto_listings': 'https://dev.to/listings',
    'hashnode_feed': 'https://hashnode.com/recent',
    'indiehackers_new': 'https://www.indiehackers.com/products?sorting=newest',
    'producthunt_today': 'https://www.producthunt.com',

    # =========================================================================
    # JOB BOARDS (Remote-focused)
    # =========================================================================
    'remoteok_latest': 'https://remoteok.com/api',
    'weworkremotely_new': 'https://weworkremotely.com/remote-jobs.rss',
    'ycombinator_jobs': 'https://www.workatastartup.com/jobs',
    'wellfound_latest': 'https://wellfound.com/jobs',
    'startup_jobs': 'https://startup.jobs',
    'himalayas': 'https://himalayas.app/jobs',
    'justremote': 'https://justremote.co/remote-jobs',
    'flexjobs_new': 'https://www.flexjobs.com/remote-jobs',
    'remotive': 'https://remotive.com/api/remote-jobs',
    'nodesk': 'https://nodesk.co/remote-jobs/',
    'jobspresso': 'https://jobspresso.co/remote-work/',

    # =========================================================================
    # FREELANCE MARKETPLACES
    # =========================================================================
    'upwork_latest': 'https://www.upwork.com/nx/search/jobs/',
    'fiverr_requests': 'https://www.fiverr.com/categories',
    'freelancer_latest': 'https://www.freelancer.com/jobs/',
    'guru_new': 'https://www.guru.com/d/jobs/',
    'peopleperhour_live': 'https://www.peopleperhour.com/freelance-jobs',
    'toptal_jobs': 'https://www.toptal.com/careers',

    # =========================================================================
    # CREATIVE PLATFORMS
    # =========================================================================
    'dribbble_jobs': 'https://dribbble.com/jobs',
    'behance_jobs': 'https://www.behance.net/joblist',
    'coroflot_jobs': 'https://www.coroflot.com/jobs',
    'krop': 'https://www.krop.com/creative-jobs/',
    'authentic_jobs': 'https://authenticjobs.com',

    # =========================================================================
    # TECH-SPECIFIC
    # =========================================================================
    'stackoverflow_jobs': 'https://stackoverflow.com/jobs',
    'dice': 'https://www.dice.com/jobs',
    'builtin': 'https://builtin.com/jobs',
    'landing_jobs': 'https://landing.jobs/jobs',

    # =========================================================================
    # CRAIGSLIST (Major cities - Computer Gigs)
    # =========================================================================
    'craigslist_gigs_sf': 'https://sfbay.craigslist.org/search/cpg',
    'craigslist_gigs_nyc': 'https://newyork.craigslist.org/search/cpg',
    'craigslist_gigs_la': 'https://losangeles.craigslist.org/search/cpg',
    'craigslist_gigs_chicago': 'https://chicago.craigslist.org/search/cpg',
    'craigslist_gigs_boston': 'https://boston.craigslist.org/search/cpg',
    'craigslist_gigs_seattle': 'https://seattle.craigslist.org/search/cpg',
    'craigslist_gigs_austin': 'https://austin.craigslist.org/search/cpg',
    'craigslist_gigs_denver': 'https://denver.craigslist.org/search/cpg',

    # =========================================================================
    # STARTUP/BETA PLATFORMS
    # =========================================================================
    'betalist': 'https://betalist.com/startups',
    'launching_next': 'https://www.launchingnext.com',
    'product_hunt_upcoming': 'https://www.producthunt.com/upcoming',

    # =========================================================================
    # INTERNATIONAL BOARDS
    # =========================================================================
    'indeed_remote': 'https://www.indeed.com/jobs?q=remote',
    'glassdoor': 'https://www.glassdoor.com/Job/remote-jobs-SRCH_IL.0,6_IS11047.htm',
    'monster': 'https://www.monster.com/jobs/search?q=remote',
    'ziprecruiter': 'https://www.ziprecruiter.com/jobs-search?search=remote',
    'seek_au': 'https://www.seek.com.au/remote-jobs',
    'reed_uk': 'https://www.reed.co.uk/jobs/remote-jobs',

    # =========================================================================
    # NICHE / SPECIALIZED
    # =========================================================================
    'powertofly': 'https://powertofly.com/jobs/',
    'women_who_code': 'https://www.womenwhocode.com/jobs',
    'diversify_tech': 'https://www.diversifytech.com/job-board',
    'arc_dev': 'https://arc.dev/remote-jobs',
    'gun_io': 'https://gun.io/find-work/',
    'working_nomads': 'https://www.workingnomads.com/jobs',
}

# =============================================================================
# PLATFORM-SPECIFIC FRESHNESS WINDOWS (in HOURS)
# =============================================================================

PLATFORM_FRESHNESS_HOURS: Dict[str, int] = {
    # Fast-moving platforms (12h)
    'twitter': 12,
    'twitter_hiring': 12,
    'twitter_freelance': 12,

    # Daily cycle platforms (24h)
    'hackernews_new': 24,
    'hackernews_show': 24,
    'hackernews_ask': 24,
    'hackernews_jobs': 24,
    'producthunt_today': 24,
    'devto_listings': 24,

    # 2-day platforms (48h)
    'reddit_forhire': 48,
    'reddit_slavelabour': 48,
    'reddit_jobs': 48,
    'reddit_startup': 48,
    'reddit_entrepreneur': 48,
    'reddit_sideproject': 48,
    'reddit_programming': 48,
    'reddit_webdev': 48,
    'reddit_freelance': 48,
    'reddit_remotejobs': 48,
    'reddit_hireawriter': 48,
    'reddit_designjobs': 48,
    'upwork_latest': 48,
    'fiverr_requests': 48,
    'freelancer_latest': 48,
    'craigslist_gigs_sf': 48,
    'craigslist_gigs_nyc': 48,
    'craigslist_gigs_la': 48,
    'craigslist_gigs_chicago': 48,
    'craigslist_gigs_boston': 48,
    'craigslist_gigs_seattle': 48,
    'craigslist_gigs_austin': 48,
    'craigslist_gigs_denver': 48,

    # 3-day platforms (72h)
    'linkedin_jobs_24h': 72,
    'indiehackers_new': 72,
    'remoteok_latest': 72,
    'weworkremotely_new': 72,
    'wellfound_latest': 72,
    'guru_new': 72,
    'peopleperhour_live': 72,

    # Default for unlisted platforms
    'default': 48
}


def get_platform_freshness_hours(platform: str) -> int:
    """Get freshness window in hours for a platform"""
    # Normalize platform name
    platform_lower = platform.lower().replace('-', '_').replace(' ', '_')

    # Direct match
    if platform_lower in PLATFORM_FRESHNESS_HOURS:
        return PLATFORM_FRESHNESS_HOURS[platform_lower]

    # Partial match (e.g., 'reddit' matches all reddit_*)
    for key, hours in PLATFORM_FRESHNESS_HOURS.items():
        if key in platform_lower or platform_lower in key:
            return hours

    return PLATFORM_FRESHNESS_HOURS['default']


# =============================================================================
# PLATFORM METADATA (for routing/execution)
# =============================================================================

PLATFORM_METADATA = {
    'hackernews': {
        'type': 'tech_community',
        'avg_value': 500,
        'win_rate': 0.15,
        'contactability': 0.3,  # Comments only
        'requires_auth': False,
    },
    'reddit': {
        'type': 'community',
        'avg_value': 200,
        'win_rate': 0.20,
        'contactability': 0.6,  # DM available
        'requires_auth': False,
    },
    'upwork': {
        'type': 'marketplace',
        'avg_value': 1000,
        'win_rate': 0.10,
        'contactability': 0.9,  # Direct proposals
        'requires_auth': True,
    },
    'fiverr': {
        'type': 'marketplace',
        'avg_value': 150,
        'win_rate': 0.25,
        'contactability': 0.8,
        'requires_auth': True,
    },
    'freelancer': {
        'type': 'marketplace',
        'avg_value': 500,
        'win_rate': 0.08,
        'contactability': 0.9,
        'requires_auth': True,
    },
    'craigslist': {
        'type': 'classifieds',
        'avg_value': 300,
        'win_rate': 0.30,
        'contactability': 0.95,  # Direct email
        'requires_auth': False,
    },
    'remoteok': {
        'type': 'job_board',
        'avg_value': 5000,
        'win_rate': 0.05,
        'contactability': 0.7,
        'requires_auth': False,
    },
    'producthunt': {
        'type': 'startup',
        'avg_value': 2000,
        'win_rate': 0.12,
        'contactability': 0.5,
        'requires_auth': False,
    },
    'dribbble': {
        'type': 'creative',
        'avg_value': 800,
        'win_rate': 0.15,
        'contactability': 0.7,
        'requires_auth': True,
    },
    'indiehackers': {
        'type': 'startup',
        'avg_value': 1500,
        'win_rate': 0.18,
        'contactability': 0.6,
        'requires_auth': False,
    },
}


def get_platform_metadata(platform: str) -> dict:
    """Get metadata for a platform"""
    platform_lower = platform.lower()

    # Direct match
    if platform_lower in PLATFORM_METADATA:
        return PLATFORM_METADATA[platform_lower]

    # Partial match
    for key, meta in PLATFORM_METADATA.items():
        if key in platform_lower:
            return meta

    # Default metadata
    return {
        'type': 'unknown',
        'avg_value': 500,
        'win_rate': 0.10,
        'contactability': 0.5,
        'requires_auth': False,
    }


# Total platform count
TOTAL_PLATFORMS = len(REAL_TIME_SOURCES)
print(f"[real_time_sources] Loaded {TOTAL_PLATFORMS} real-time sources")
