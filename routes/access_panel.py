"""
ACCESS PANEL API: REST Endpoints for Opportunity Management

Endpoints:
1. POST /access-panel/discover - Trigger discovery
2. GET /access-panel/opportunities - List opportunities
3. GET /access-panel/opportunities/{id} - Get opportunity details
4. POST /access-panel/opportunities/{id}/route - Route opportunity
5. POST /access-panel/opportunities/{id}/execute - Execute opportunity
6. GET /access-panel/stats - Get system stats
7. GET /access-panel/health - Health check
8. POST /access-panel/enrich - Enrich opportunities
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)

# Try FastAPI
try:
    from fastapi import APIRouter, HTTPException, Query, Body
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not available - Access Panel routes disabled")

# Import Access Panel components
try:
    from enrichment import get_enrichment_pipeline
    from routing import get_conversion_router, get_inventory_scorer
    from risk import get_anti_abuse, get_reputation_scorer
    from platforms import get_pack_registry
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False
    logger.warning("Access Panel components not available")

# Try to import existing systems
try:
    from managers.discovery_manager import get_discovery_manager
    DISCOVERY_AVAILABLE = True
except ImportError:
    DISCOVERY_AVAILABLE = False

try:
    from managers.execution_manager import get_execution_manager
    EXECUTION_AVAILABLE = True
except ImportError:
    EXECUTION_AVAILABLE = False


if FASTAPI_AVAILABLE:
    # Create router
    router = APIRouter(prefix="/access-panel", tags=["Access Panel"])

    # Request/Response models
    class DiscoverRequest(BaseModel):
        platforms: Optional[List[str]] = None
        max_results: int = 100
        enrich: bool = True
        route: bool = True
        strategy: str = "perplexity_first"  # perplexity_first, standard, scraping_only

    class DiscoverResponse(BaseModel):
        ok: bool
        opportunities: List[Dict[str, Any]]
        stats: Dict[str, Any]
        timing_ms: float

    class EnrichRequest(BaseModel):
        opportunities: List[Dict[str, Any]]

    class RouteRequest(BaseModel):
        opportunity_id: str

    class ExecuteRequest(BaseModel):
        opportunity_id: str
        dry_run: bool = False

    # In-memory store (would be database in production)
    _opportunities_cache: Dict[str, Dict] = {}

    @router.post("/discover", response_model=DiscoverResponse)
    async def discover_opportunities(request: DiscoverRequest):
        """
        Trigger opportunity discovery.

        Strategies:
        - perplexity_first: Use Perplexity AI as primary (recommended)
        - standard: Use all packs in parallel
        - scraping_only: Only use scraping packs

        - Enriches opportunities with scores
        - Routes for prioritization
        """
        start_time = time.time()
        strategy_used = request.strategy

        try:
            opportunities = []

            # Strategy: Perplexity-First (recommended)
            if request.strategy == "perplexity_first":
                try:
                    from discovery.perplexity_first import discover_with_perplexity_first
                    results = await discover_with_perplexity_first()
                    opportunities = results.get('opportunities', [])
                    logger.info(f"Perplexity-first: {len(opportunities)} opportunities")
                except Exception as e:
                    logger.warning(f"Perplexity-first failed: {e}, falling back to standard")
                    strategy_used = "standard_fallback"

            # Fallback or explicit standard strategy
            if not opportunities and DISCOVERY_AVAILABLE:
                discovery_manager = get_discovery_manager()
                results = await discovery_manager.discover_all()
                opportunities = results.get('opportunities', [])

            # Limit results
            opportunities = opportunities[:request.max_results]

            # Enrich if requested
            if request.enrich and COMPONENTS_AVAILABLE:
                pipeline = get_enrichment_pipeline()
                opportunities = pipeline.enrich_batch(opportunities)

            # Route if requested
            if request.route and COMPONENTS_AVAILABLE:
                router_instance = get_conversion_router()
                opportunities = router_instance.route_batch(opportunities)

            # Cache opportunities
            for opp in opportunities:
                opp_id = opp.get('id', '')
                if opp_id:
                    _opportunities_cache[opp_id] = opp

            elapsed_ms = (time.time() - start_time) * 1000

            return DiscoverResponse(
                ok=True,
                opportunities=opportunities,
                stats={
                    'total_discovered': len(opportunities),
                    'platforms': list(set(o.get('platform', '') for o in opportunities)),
                    'strategy': strategy_used,
                },
                timing_ms=elapsed_ms,
            )

        except Exception as e:
            logger.error(f"[access_panel] Discovery error: {e}")
            raise HTTPException(500, str(e))

    @router.get("/opportunities")
    async def list_opportunities(
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
        platform: Optional[str] = None,
        tier: Optional[str] = None,
        min_score: Optional[float] = None,
    ):
        """
        List discovered opportunities.

        Supports filtering by:
        - platform
        - routing tier
        - minimum routing score
        """
        opportunities = list(_opportunities_cache.values())

        # Filter by platform
        if platform:
            opportunities = [o for o in opportunities if o.get('platform') == platform]

        # Filter by tier
        if tier:
            opportunities = [o for o in opportunities if o.get('routing_tier') == tier]

        # Filter by score
        if min_score is not None:
            opportunities = [o for o in opportunities if o.get('routing_score', 0) >= min_score]

        # Sort by routing score
        opportunities.sort(key=lambda x: x.get('routing_score', 0), reverse=True)

        # Paginate
        total = len(opportunities)
        opportunities = opportunities[offset:offset + limit]

        return {
            'ok': True,
            'opportunities': opportunities,
            'total': total,
            'limit': limit,
            'offset': offset,
        }

    @router.get("/opportunities/{opportunity_id}")
    async def get_opportunity(opportunity_id: str):
        """Get single opportunity by ID"""
        opp = _opportunities_cache.get(opportunity_id)

        if not opp:
            raise HTTPException(404, f"Opportunity {opportunity_id} not found")

        return {
            'ok': True,
            'opportunity': opp,
        }

    @router.post("/opportunities/{opportunity_id}/route")
    async def route_opportunity(opportunity_id: str):
        """Route/re-route single opportunity"""
        opp = _opportunities_cache.get(opportunity_id)

        if not opp:
            raise HTTPException(404, f"Opportunity {opportunity_id} not found")

        if not COMPONENTS_AVAILABLE:
            raise HTTPException(503, "Routing components not available")

        try:
            router_instance = get_conversion_router()
            routed = router_instance.route(opp)

            # Update cache
            _opportunities_cache[opportunity_id] = routed

            return {
                'ok': True,
                'opportunity': routed,
                'routing_score': routed.get('routing_score'),
                'routing_tier': routed.get('routing_tier'),
            }

        except Exception as e:
            logger.error(f"[access_panel] Routing error: {e}")
            raise HTTPException(500, str(e))

    @router.post("/opportunities/{opportunity_id}/execute")
    async def execute_opportunity(opportunity_id: str, request: ExecuteRequest):
        """Execute/act on opportunity"""
        opp = _opportunities_cache.get(opportunity_id)

        if not opp:
            raise HTTPException(404, f"Opportunity {opportunity_id} not found")

        if not EXECUTION_AVAILABLE:
            raise HTTPException(503, "Execution manager not available")

        try:
            execution_manager = get_execution_manager()

            result = await execution_manager.execute(
                opportunity=opp,
                dry_run=request.dry_run,
            )

            # Update opportunity status
            if result.get('success'):
                opp['status'] = 'executing'
                opp['execution_id'] = result.get('execution_id')
                _opportunities_cache[opportunity_id] = opp

            return {
                'ok': True,
                'execution_result': result,
                'opportunity': opp,
            }

        except Exception as e:
            logger.error(f"[access_panel] Execution error: {e}")
            raise HTTPException(500, str(e))

    @router.post("/enrich")
    async def enrich_opportunities(request: EnrichRequest):
        """Enrich batch of opportunities"""
        if not COMPONENTS_AVAILABLE:
            raise HTTPException(503, "Enrichment components not available")

        try:
            pipeline = get_enrichment_pipeline()
            enriched = pipeline.enrich_batch(request.opportunities)

            return {
                'ok': True,
                'opportunities': enriched,
                'stats': pipeline.get_stats(),
            }

        except Exception as e:
            logger.error(f"[access_panel] Enrichment error: {e}")
            raise HTTPException(500, str(e))

    @router.get("/stats")
    async def get_stats():
        """Get Access Panel system stats"""
        stats = {
            'cached_opportunities': len(_opportunities_cache),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        if COMPONENTS_AVAILABLE:
            try:
                stats['enrichment'] = get_enrichment_pipeline().get_stats()
                stats['routing'] = get_conversion_router().get_stats()
                stats['inventory'] = get_inventory_scorer().get_stats()
                stats['anti_abuse'] = get_anti_abuse().get_stats()
                stats['reputation'] = get_reputation_scorer().get_stats()
                stats['platforms'] = get_pack_registry().get_stats()
            except Exception as e:
                stats['component_error'] = str(e)

        if DISCOVERY_AVAILABLE:
            try:
                stats['discovery'] = get_discovery_manager().get_stats()
            except:
                pass

        return {
            'ok': True,
            'stats': stats,
        }

    @router.get("/health")
    async def health_check():
        """Access Panel health check"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'components': {
                'fastapi': True,
                'discovery': DISCOVERY_AVAILABLE,
                'execution': EXECUTION_AVAILABLE,
                'access_panel_components': COMPONENTS_AVAILABLE,
            }
        }

        # Check component health
        if COMPONENTS_AVAILABLE:
            try:
                get_enrichment_pipeline()
                health['components']['enrichment'] = True
            except:
                health['components']['enrichment'] = False

            try:
                get_conversion_router()
                health['components']['routing'] = True
            except:
                health['components']['routing'] = False

        all_healthy = all(health['components'].values())
        health['status'] = 'healthy' if all_healthy else 'degraded'

        return health

    @router.get("/debug/perplexity")
    async def debug_perplexity():
        """Debug endpoint for Perplexity discovery issues"""
        debug_info = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'perplexity_first': None,
            'perplexity_pack': None,
        }

        # Check Perplexity-first discovery
        try:
            from discovery.perplexity_first import get_perplexity_first_discovery
            discovery = get_perplexity_first_discovery()
            debug_info['perplexity_first'] = discovery.get_debug_info()
        except Exception as e:
            debug_info['perplexity_first'] = {'error': str(e)}

        # Check Perplexity pack
        try:
            from platforms.packs.perplexity_discovery import PERPLEXITY_PACK
            import os
            debug_info['perplexity_pack'] = {
                'name': PERPLEXITY_PACK.get('name'),
                'priority': PERPLEXITY_PACK.get('priority'),
                'api_key_configured': bool(os.getenv('PERPLEXITY_API_KEY')),
                'api_key_prefix': os.getenv('PERPLEXITY_API_KEY', '')[:8] + '...' if os.getenv('PERPLEXITY_API_KEY') else None
            }
        except Exception as e:
            debug_info['perplexity_pack'] = {'error': str(e)}

        return debug_info


def get_access_panel_router():
    """Get Access Panel router for app registration"""
    if FASTAPI_AVAILABLE:
        return router
    return None
