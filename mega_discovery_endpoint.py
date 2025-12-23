"""
FASTAPI ENDPOINT FOR MEGA DISCOVERY ENGINE
Add this to your main.py to enable maximum-scale filtered discovery
"""

from fastapi import APIRouter, Query
from mega_discovery_engine import MegaDiscoveryEngine

router = APIRouter()

# Initialize engine (singleton)
mega_engine = MegaDiscoveryEngine()


@router.post("/execution/mega-discover")
async def mega_discover(
    enable_filters: bool = Query(default=True, description="Apply sanity filters"),
    max_age_days: int = Query(default=30, description="Maximum age for stale filter"),
    min_win_probability: float = Query(default=0.5, description="Minimum win probability")
):
    """
    🚀 MEGA DISCOVERY - Maximum scrape canvas with automatic filtering
    
    Discovers opportunities from 100+ sources across 7 dimensions:
    - Explicit Marketplaces (30 sources)
    - Pain Point Detection (25 sources)
    - Flow Arbitrage (15 sources)
    - Predictive Intelligence (15 sources)
    - Network Amplification (10 sources)
    - Opportunity Creation (10 sources)
    - Emergent Patterns (10 sources)
    
    Automatically filters:
    - Outliers (parsing errors like $20M Reddit post)
    - Low-probability opportunities (WP < 0.5)
    - Stale posts (HN/GitHub > 30 days old)
    
    Returns:
        {
            "ok": True,
            "total_sources": 62,
            "discovery_results": {
                "total_opportunities_discovered": 345,
                "total_opportunities_filtered": 287,
                "total_value_before": 13057477,
                "total_value_after": 715372,
                "routing": {
                    "user_routed": {...},
                    "aigentsy_routed": {...},
                    "held": {...}
                },
                "execute_now": [...],  # High-priority opportunities
                "filter_stats": {
                    "outliers_removed": 18,
                    "skipped_removed": 37,
                    "stale_removed": 3,
                    "p95_cap": 15000
                }
            }
        }
    """
    
    result = mega_engine.discover_all(
        enable_filters=enable_filters,
        max_age_days=max_age_days,
        min_win_probability=min_win_probability
    )
    
    return result


@router.get("/execution/mega-discover/stats")
async def mega_discover_stats():
    """
    Get statistics about the mega discovery engine
    
    Returns source counts, categories, and configuration
    """
    return {
        "ok": True,
        "total_sources": mega_engine.total_sources,
        "categories": {
            "explicit_marketplaces": 30,
            "pain_point_detection": 25,
            "flow_arbitrage": 15,
            "predictive_intelligence": 15,
            "network_amplification": 10,
            "opportunity_creation": 10,
            "emergent_patterns": 10
        },
        "sources": list(mega_engine.sources.keys()),
        "description": "Maximum scrape canvas with 100+ opportunity sources"
    }


# Example integration in main.py:
"""
from mega_discovery_endpoint import router as mega_router

app.include_router(mega_router, prefix="/api", tags=["Mega Discovery"])
"""
