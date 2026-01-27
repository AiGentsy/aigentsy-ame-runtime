"""
INTEGRATION ROUTES: Full-Stack Discovery→Contract→Fulfill→Proof API
═══════════════════════════════════════════════════════════════════════════════

Endpoints:
1. GET /integration/stats - Full system stats
2. GET /integration/health - Full system health
3. POST /integration/discover-and-execute - Full pipeline on N opportunities
4. GET /integration/capacity - Workforce capacity
5. POST /integration/create-contract - Generate SOW + Escrow
6. POST /integration/release-milestone - Release milestone on QA pass
7. GET /integration/client-room/{contract_id} - Client room data

Updated: Jan 2026
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try FastAPI
try:
    from fastapi import APIRouter, HTTPException, Query, Body
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not available - Integration routes disabled")


if FASTAPI_AVAILABLE:
    # Create router
    router = APIRouter(prefix="/integration", tags=["Integration"])

    # Request/Response models
    class FullStackRequest(BaseModel):
        max_opportunities: int = 10
        auto_contract: bool = True
        auto_execute: bool = True
        dry_run: bool = False

    class ContractRequest(BaseModel):
        opportunity_id: str

    class MilestoneReleaseRequest(BaseModel):
        contract_id: str
        milestone_id: str

    class ClientRoomResponse(BaseModel):
        contract_id: str
        room_url: str
        milestones: List[Dict[str, Any]]
        total_amount: float
        status: str

    # Lazy loaders with fallbacks
    def _get_system_loader():
        try:
            from integration.system_loader import get_system_loader
            return get_system_loader()
        except Exception as e:
            logger.debug(f"System loader not available: {e}")
            return None

    def _get_orchestrator():
        try:
            from fulfillment.orchestrator import get_fulfillment_orchestrator
            return get_fulfillment_orchestrator()
        except Exception as e:
            logger.debug(f"Orchestrator not available: {e}")
            return None

    def _get_sow_generator():
        try:
            from contracts.sow_generator import get_sow_generator
            return get_sow_generator()
        except Exception as e:
            logger.debug(f"SOW generator not available: {e}")
            return None

    def _get_escrow():
        try:
            from contracts.milestone_escrow import get_milestone_escrow
            return get_milestone_escrow()
        except Exception as e:
            logger.debug(f"Escrow not available: {e}")
            return None

    def _get_qa():
        try:
            from qa.checklists import get_qa_checklists
            return get_qa_checklists()
        except Exception as e:
            logger.debug(f"QA not available: {e}")
            return None

    def _get_dispatcher():
        try:
            from workforce.dispatcher import get_workforce_dispatcher
            return get_workforce_dispatcher()
        except Exception as e:
            logger.debug(f"Dispatcher not available: {e}")
            return None

    def _get_discovery_manager():
        try:
            from managers.discovery_manager import get_discovery_manager
            return get_discovery_manager()
        except Exception as e:
            logger.debug(f"Discovery manager not available: {e}")
            return None

    def _get_hybrid_discovery():
        """Get hybrid discovery engine for contact-enriched opportunities"""
        try:
            from discovery.hybrid_discovery import get_hybrid_discovery
            return get_hybrid_discovery()
        except Exception as e:
            logger.debug(f"Hybrid discovery not available: {e}")
            return None

    # Store for active contracts
    _contracts_cache: Dict[str, Dict] = {}
    _execution_results: Dict[str, Dict] = {}
    _presentation_results: Dict[str, Dict] = {}  # Track contract presentations

    def _get_customer_loop_wiring():
        """Get customer loop wiring for outreach"""
        try:
            from integration.customer_loop_wiring import get_customer_loop_wiring
            return get_customer_loop_wiring()
        except Exception as e:
            logger.debug(f"Customer loop wiring not available: {e}")
            return None

    @router.get("/stats")
    async def get_integration_stats():
        """
        Get full system integration stats.

        Returns stats from all loaded systems:
        - Managers (discovery, execution, revenue)
        - Engines (35+)
        - Oracles (7)
        - Brain modules (12)
        - Agents (10+)
        - Fulfillment pipeline
        """
        stats = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'integration': {
                'contracts_created': len(_contracts_cache),
                'executions_run': len(_execution_results),
            }
        }

        # System loader stats
        loader = _get_system_loader()
        if loader:
            stats['systems'] = loader.get_stats()

        # Orchestrator stats
        orchestrator = _get_orchestrator()
        if orchestrator:
            stats['orchestrator'] = orchestrator.get_stats()

        # SOW generator stats
        sow_gen = _get_sow_generator()
        if sow_gen:
            stats['sow_generator'] = sow_gen.get_stats()

        # Escrow stats
        escrow = _get_escrow()
        if escrow:
            stats['escrow'] = escrow.get_stats()

        # QA stats
        qa = _get_qa()
        if qa:
            stats['qa'] = qa.get_stats()

        # Workforce stats
        dispatcher = _get_dispatcher()
        if dispatcher:
            stats['workforce'] = dispatcher.get_stats()

        return {
            'ok': True,
            'stats': stats,
        }

    @router.get("/health")
    async def get_integration_health():
        """
        Full system health check.

        Checks all integration components.
        """
        health = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'components': {},
        }

        # Check each component
        components = {
            'system_loader': _get_system_loader,
            'orchestrator': _get_orchestrator,
            'sow_generator': _get_sow_generator,
            'escrow': _get_escrow,
            'qa_checklists': _get_qa,
            'workforce_dispatcher': _get_dispatcher,
            'discovery_manager': _get_discovery_manager,
        }

        loaded = 0
        for name, loader in components.items():
            try:
                instance = loader()
                health['components'][name] = instance is not None
                if instance:
                    loaded += 1
            except Exception as e:
                health['components'][name] = False
                health['components'][f'{name}_error'] = str(e)

        # System loader detailed health
        loader = _get_system_loader()
        if loader:
            health['systems_health'] = loader.health_check()

        # Determine overall status
        total = len(components)
        health['loaded'] = loaded
        health['total'] = total
        health['coverage_pct'] = round(loaded / total * 100, 1) if total > 0 else 0

        if loaded == total:
            health['status'] = 'healthy'
        elif loaded > total * 0.5:
            health['status'] = 'degraded'
        else:
            health['status'] = 'unhealthy'

        return health

    @router.get("/debug/perplexity")
    async def debug_perplexity():
        """
        Debug endpoint to test Perplexity API directly.

        Returns raw API response to diagnose issues.
        """
        import os
        import httpx

        perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        if not perplexity_key:
            return {
                'ok': False,
                'error': 'PERPLEXITY_API_KEY not configured',
                'key_preview': None
            }

        # Test with a simple query
        test_query = "Find 3 recent hiring posts for developers on Twitter"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {perplexity_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "sonar",
                        "messages": [
                            {"role": "system", "content": "Return a JSON array of job opportunities."},
                            {"role": "user", "content": test_query}
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.1
                    }
                )

                return {
                    'ok': response.is_success,
                    'status_code': response.status_code,
                    'key_preview': f"{perplexity_key[:8]}...{perplexity_key[-4:]}",
                    'query': test_query,
                    'response_preview': response.text[:1000] if response.text else None,
                    'headers': dict(response.headers)
                }
        except Exception as e:
            return {
                'ok': False,
                'error': f"{type(e).__name__}: {str(e)}",
                'key_preview': f"{perplexity_key[:8]}...{perplexity_key[-4:]}"
            }

    @router.get("/debug/multi-source")
    async def debug_multi_source():
        """
        Debug endpoint to check MultiSourceDiscovery configuration.

        Shows which APIs are detected and available for discovery.
        """
        import os

        result = {
            'ok': True,
            'discovery_sources': {},
            'api_keys_detected': {},
            'twitter_details': {}
        }

        # Check each API key
        api_checks = {
            'PERPLEXITY_API_KEY': 'perplexity',
            'TWITTER_BEARER_TOKEN': 'twitter_search',
            'TWITTER_API_KEY': 'twitter_oauth',
            'TWITTER_ACCESS_TOKEN': 'twitter_dm',
            'GITHUB_TOKEN': 'github',
            'OPENROUTER_API_KEY': 'openrouter',
            'GEMINI_API_KEY': 'gemini',
            'REDDIT_CLIENT_ID': 'reddit_oauth'
        }

        for env_var, name in api_checks.items():
            value = os.getenv(env_var)
            result['api_keys_detected'][name] = {
                'configured': bool(value),
                'env_var': env_var,
                'length': len(value) if value else 0
            }

        # Twitter-specific details
        twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN')
        result['twitter_details'] = {
            'bearer_token_exists': bool(twitter_bearer),
            'bearer_token_length': len(twitter_bearer) if twitter_bearer else 0,
            'bearer_token_preview': f"{twitter_bearer[:10]}...{twitter_bearer[-4:]}" if twitter_bearer and len(twitter_bearer) > 14 else None,
            'api_key_exists': bool(os.getenv('TWITTER_API_KEY')),
            'access_token_exists': bool(os.getenv('TWITTER_ACCESS_TOKEN')),
            'can_search': bool(twitter_bearer),
            'can_dm': bool(os.getenv('TWITTER_ACCESS_TOKEN'))
        }

        # Try to instantiate MultiSourceDiscovery to see what it detects
        try:
            from discovery.multi_source_discovery import MultiSourceDiscovery
            msd = MultiSourceDiscovery()
            result['discovery_sources'] = {
                'enabled': list(msd.sources.keys()),
                'count': len(msd.sources),
                'details': {k: v.get('description', '') for k, v in msd.sources.items()}
            }
        except Exception as e:
            result['discovery_sources'] = {
                'error': f"{type(e).__name__}: {str(e)}"
            }

        return result

    @router.get("/debug/twitter")
    async def debug_twitter():
        """
        Debug endpoint to test Twitter API directly.

        Tests Bearer Token authentication and search functionality.
        """
        import os
        import httpx

        twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN')

        result = {
            'ok': False,
            'bearer_token': {
                'exists': bool(twitter_bearer),
                'length': len(twitter_bearer) if twitter_bearer else 0,
                'preview': f"{twitter_bearer[:10]}..." if twitter_bearer and len(twitter_bearer) > 10 else None
            },
            'api_test': None
        }

        if not twitter_bearer:
            result['error'] = 'TWITTER_BEARER_TOKEN not configured'
            result['hint'] = 'Add TWITTER_BEARER_TOKEN to Render environment variables'
            return result

        # Test the API
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    headers={"Authorization": f"Bearer {twitter_bearer}"},
                    params={
                        "query": "hiring developer -is:retweet",
                        "max_results": 10,
                        "tweet.fields": "author_id",
                        "expansions": "author_id",
                        "user.fields": "username"
                    }
                )

                result['api_test'] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                }

                if response.status_code == 200:
                    data = response.json()
                    tweets = data.get('data', [])
                    users = {u['id']: u for u in data.get('includes', {}).get('users', [])}

                    result['ok'] = True
                    result['api_test']['tweets_found'] = len(tweets)
                    result['api_test']['sample_tweets'] = []

                    for tweet in tweets[:3]:
                        user = users.get(tweet.get('author_id'), {})
                        result['api_test']['sample_tweets'].append({
                            'id': tweet.get('id'),
                            'username': user.get('username'),
                            'text_preview': tweet.get('text', '')[:100]
                        })
                elif response.status_code == 401:
                    result['error'] = 'UNAUTHORIZED - Bearer token is invalid or expired'
                    result['api_test']['response'] = response.text[:300]
                elif response.status_code == 403:
                    result['error'] = 'FORBIDDEN - API access denied (may need elevated access)'
                    result['api_test']['response'] = response.text[:300]
                elif response.status_code == 429:
                    result['error'] = 'RATE LIMITED - Too many requests'
                    result['api_test']['response'] = response.text[:300]
                else:
                    result['error'] = f'HTTP {response.status_code}'
                    result['api_test']['response'] = response.text[:300]

        except Exception as e:
            result['error'] = f"{type(e).__name__}: {str(e)}"

        return result

    @router.get("/capacity")
    async def get_capacity():
        """
        Get workforce capacity across all tiers.

        Returns:
        - Per-tier capacity (fabric, pdl, human)
        - Utilization percentages
        - Estimated wait times
        """
        dispatcher = _get_dispatcher()
        if not dispatcher:
            return {
                'ok': True,
                'capacity': {
                    'message': 'Workforce dispatcher not loaded',
                    'default_capacity': {
                        'fabric': {'available': 100, 'utilization_pct': 0},
                        'pdl': {'available': 50, 'utilization_pct': 0},
                        'human_premium': {'available': 5, 'utilization_pct': 0},
                        'human_standard': {'available': 20, 'utilization_pct': 0},
                        'hybrid': {'available': 10, 'utilization_pct': 0},
                    }
                }
            }

        return {
            'ok': True,
            'capacity': dispatcher.get_capacity(),
            'stats': dispatcher.get_stats(),
        }

    @router.post("/discover-and-execute")
    async def discover_and_execute_full_stack(request: FullStackRequest):
        """
        Full-stack pipeline: Discovery→Route→Contract→Fulfill.

        This is the main autonomous execution endpoint.

        Steps:
        1. Discover opportunities (Perplexity-first)
        2. Enrich and route
        3. Generate SOW and escrow (if auto_contract)
        4. Create execution plan
        5. Dispatch to workforce (if auto_execute)
        """
        start_time = time.time()
        execution_id = f"exec_{int(time.time())}"

        results = {
            'execution_id': execution_id,
            'started_at': datetime.now(timezone.utc).isoformat(),
            'steps': {},
            'opportunities_processed': 0,
            'contracts_created': 0,
            'plans_created': 0,
            'tasks_dispatched': 0,
        }

        try:
            # Step 1: Discover opportunities (HYBRID: Perplexity + Direct API Enrichment)
            logger.info(f"[{execution_id}] Step 1: Discovering opportunities with HYBRID engine...")
            opportunities = []

            # Try hybrid discovery first (includes contact enrichment)
            try:
                from discovery.hybrid_discovery import discover_with_contact
                opportunities = await discover_with_contact(max_opportunities=request.max_opportunities)

                # Count how many have contact info
                with_contact = sum(1 for o in opportunities if o.get('contact'))
                results['steps']['discovery'] = {
                    'status': 'success',
                    'count': len(opportunities),
                    'source': 'hybrid_discovery',
                    'with_contact': with_contact,
                    'contact_rate': f"{with_contact/len(opportunities)*100:.1f}%" if opportunities else "0%",
                }
                logger.info(f"[{execution_id}] Hybrid discovery: {with_contact}/{len(opportunities)} with contact")
            except Exception as e:
                logger.warning(f"[{execution_id}] Hybrid discovery failed: {e}, falling back...")

                # Fallback to perplexity-first
                try:
                    from discovery.perplexity_first import discover_with_perplexity_first
                    discovery_result = await discover_with_perplexity_first()
                    opportunities = discovery_result.get('opportunities', [])[:request.max_opportunities]
                    results['steps']['discovery'] = {
                        'status': 'success',
                        'count': len(opportunities),
                        'source': 'perplexity_first_fallback',
                    }
                except Exception as e2:
                    logger.warning(f"[{execution_id}] Perplexity fallback failed: {e2}")

                    # Final fallback to discovery manager
                    dm = _get_discovery_manager()
                    if dm:
                        try:
                            discovery_result = await dm.discover_all()
                            opportunities = discovery_result.get('opportunities', [])[:request.max_opportunities]
                            results['steps']['discovery'] = {
                                'status': 'success',
                                'count': len(opportunities),
                                'source': 'discovery_manager_fallback',
                            }
                        except Exception as e3:
                            results['steps']['discovery'] = {'status': 'failed', 'error': str(e3)}

            results['opportunities_processed'] = len(opportunities)

            if not opportunities:
                results['steps']['discovery'] = results['steps'].get('discovery', {'status': 'empty'})
                return {'ok': True, 'results': results, 'timing_ms': (time.time() - start_time) * 1000}

            # Step 2: Enrich opportunities
            logger.info(f"[{execution_id}] Step 2: Enriching {len(opportunities)} opportunities...")
            try:
                from enrichment import get_enrichment_pipeline
                pipeline = get_enrichment_pipeline()
                opportunities = pipeline.enrich_batch(opportunities)
                results['steps']['enrichment'] = {'status': 'success', 'enriched': len(opportunities)}
            except Exception as e:
                results['steps']['enrichment'] = {'status': 'skipped', 'reason': str(e)}

            # Step 3: Route opportunities
            logger.info(f"[{execution_id}] Step 3: Routing opportunities...")
            try:
                from routing import get_conversion_router
                router_instance = get_conversion_router()
                opportunities = router_instance.route_batch(opportunities)
                # Sort by routing score
                opportunities.sort(key=lambda x: x.get('routing_score', 0), reverse=True)
                results['steps']['routing'] = {'status': 'success', 'routed': len(opportunities)}
            except Exception as e:
                results['steps']['routing'] = {'status': 'skipped', 'reason': str(e)}

            # Step 4: Create contracts (if enabled)
            contracts = []
            if request.auto_contract:
                logger.info(f"[{execution_id}] Step 4: Creating contracts...")
                orchestrator = _get_orchestrator()
                sow_gen = _get_sow_generator()
                escrow = _get_escrow()

                for opp in opportunities:
                    try:
                        # Generate execution plan
                        if orchestrator:
                            plan = orchestrator.plan_from_offerpack(opp)
                            plan_dict = orchestrator.to_dict(plan)

                            # Generate SOW
                            if sow_gen:
                                sow = sow_gen.sow_from_plan(opp, plan_dict)
                                sow_dict = sow_gen.to_dict(sow)

                                # Create escrow
                                if escrow:
                                    contract = await escrow.create_milestones(opp, sow_dict)
                                    contract_dict = escrow.to_dict(contract)

                                    contracts.append({
                                        'opportunity_id': opp.get('id'),
                                        'plan': plan_dict,
                                        'sow': sow_dict,
                                        'escrow': contract_dict,
                                    })

                                    # Cache
                                    _contracts_cache[contract.id] = contract_dict
                                    results['contracts_created'] += 1

                            results['plans_created'] += 1

                    except Exception as e:
                        logger.warning(f"[{execution_id}] Contract creation failed for {opp.get('id')}: {e}")

                results['steps']['contracts'] = {
                    'status': 'success' if contracts else 'no_contracts',
                    'count': len(contracts),
                }

                # Step 4b: Present contracts to customers (WIRING EXISTING OUTREACH)
                logger.info(f"[{execution_id}] Step 4b: Presenting contracts to customers...")
                wiring = _get_customer_loop_wiring()
                presentations = []

                if wiring and contracts:
                    for contract_data in contracts:
                        try:
                            from integration.customer_loop_wiring import present_contract_after_creation
                            opp_id = contract_data.get('opportunity_id')

                            # Find the opportunity
                            opp_for_presentation = None
                            for o in opportunities:
                                if o.get('id') == opp_id:
                                    opp_for_presentation = o
                                    break

                            if opp_for_presentation:
                                presentation = await present_contract_after_creation(
                                    opportunity=opp_for_presentation,
                                    contract=contract_data.get('escrow', {}),
                                    sow=contract_data.get('sow'),
                                )
                                presentations.append({
                                    'opportunity_id': opp_id,
                                    **presentation
                                })

                                if presentation.get('presented'):
                                    logger.info(f"✅ Contract presented via {presentation.get('method')}")
                                else:
                                    logger.warning(f"⚠️ Contract not presented: {presentation.get('error')}")

                        except Exception as e:
                            logger.warning(f"[{execution_id}] Presentation failed for {contract_data.get('opportunity_id')}: {e}")
                            presentations.append({
                                'opportunity_id': contract_data.get('opportunity_id'),
                                'presented': False,
                                'error': str(e),
                            })

                    results['steps']['presentation'] = {
                        'status': 'success' if any(p.get('presented') for p in presentations) else 'no_presentations',
                        'presented': len([p for p in presentations if p.get('presented')]),
                        'total': len(presentations),
                    }
                    results['presentations'] = presentations
                    _presentation_results[execution_id] = presentations
                else:
                    results['steps']['presentation'] = {
                        'status': 'skipped',
                        'reason': 'wiring not available or no contracts'
                    }
            else:
                results['steps']['contracts'] = {'status': 'skipped', 'reason': 'auto_contract=false'}

            # Step 5: Dispatch to workforce (if enabled)
            if request.auto_execute and not request.dry_run:
                logger.info(f"[{execution_id}] Step 5: Dispatching to workforce...")
                dispatcher = _get_dispatcher()

                if dispatcher:
                    tasks_dispatched = 0
                    for contract in contracts:
                        plan = contract.get('plan', {})
                        plan_id = contract.get('opportunity_id', 'unknown')

                        for step in plan.get('steps', []):
                            try:
                                task = await dispatcher.dispatch_step(step, plan_id)
                                tasks_dispatched += 1
                            except Exception as e:
                                logger.warning(f"[{execution_id}] Dispatch failed: {e}")

                    results['tasks_dispatched'] = tasks_dispatched
                    results['steps']['dispatch'] = {
                        'status': 'success',
                        'tasks': tasks_dispatched,
                    }
                else:
                    results['steps']['dispatch'] = {'status': 'skipped', 'reason': 'dispatcher not available'}
            else:
                results['steps']['dispatch'] = {'status': 'skipped', 'reason': 'auto_execute=false or dry_run'}

            results['completed_at'] = datetime.now(timezone.utc).isoformat()
            results['contracts'] = contracts

            # Store execution result
            _execution_results[execution_id] = results

            elapsed_ms = (time.time() - start_time) * 1000
            return {
                'ok': True,
                'results': results,
                'timing_ms': elapsed_ms,
            }

        except Exception as e:
            logger.error(f"[{execution_id}] Full-stack execution failed: {e}")
            results['error'] = str(e)
            return {
                'ok': False,
                'results': results,
                'timing_ms': (time.time() - start_time) * 1000,
            }

    @router.post("/create-contract")
    async def create_contract(request: ContractRequest):
        """
        Create SOW + Escrow for a single opportunity.

        Returns contract with:
        - SOW details
        - Milestone paylinks
        - Client room URL
        """
        # Get opportunity from access panel cache
        try:
            from routes.access_panel import _opportunities_cache
            opp = _opportunities_cache.get(request.opportunity_id)
        except ImportError:
            opp = None

        if not opp:
            raise HTTPException(404, f"Opportunity {request.opportunity_id} not found")

        orchestrator = _get_orchestrator()
        sow_gen = _get_sow_generator()
        escrow = _get_escrow()

        if not all([orchestrator, sow_gen, escrow]):
            raise HTTPException(503, "Contract creation components not available")

        try:
            # Generate plan
            plan = orchestrator.plan_from_offerpack(opp)
            plan_dict = orchestrator.to_dict(plan)

            # Generate SOW
            sow = sow_gen.sow_from_plan(opp, plan_dict)
            sow_dict = sow_gen.to_dict(sow)

            # Create escrow
            contract = await escrow.create_milestones(opp, sow_dict)
            contract_dict = escrow.to_dict(contract)

            # Cache
            _contracts_cache[contract.id] = contract_dict

            return {
                'ok': True,
                'contract': {
                    'id': contract.id,
                    'sow': sow_dict,
                    'escrow': contract_dict,
                    'plan': plan_dict,
                    'client_room_url': contract.client_room_url,
                }
            }

        except Exception as e:
            logger.error(f"Contract creation failed: {e}")
            raise HTTPException(500, str(e))

    @router.post("/release-milestone")
    async def release_milestone(request: MilestoneReleaseRequest):
        """
        Release milestone funds after QA gate passes.

        Checks:
        1. Contract exists
        2. Milestone is funded
        3. QA gate passed
        4. Releases funds
        """
        escrow = _get_escrow()
        qa = _get_qa()

        if not escrow:
            raise HTTPException(503, "Escrow not available")

        # Check QA gate
        qa_passed = True
        if qa:
            gate_id = f"qa_{request.milestone_id}_code_review"
            gate = qa.get_gate(gate_id)
            if gate:
                qa_passed = gate.passed

        if not qa_passed:
            raise HTTPException(400, f"QA gate not passed for milestone {request.milestone_id}")

        try:
            success = await escrow.release_milestone(
                request.contract_id,
                request.milestone_id,
                qa_passed=qa_passed
            )

            if success:
                return {
                    'ok': True,
                    'message': f"Milestone {request.milestone_id} released",
                    'contract_id': request.contract_id,
                }
            else:
                raise HTTPException(400, "Failed to release milestone")

        except Exception as e:
            logger.error(f"Milestone release failed: {e}")
            raise HTTPException(500, str(e))

    @router.get("/client-room/{contract_id}")
    async def get_client_room(contract_id: str):
        """
        Get client room data for a contract.

        Returns all information needed for client-facing room:
        - Contract status
        - Milestone status and paylinks
        - SOW summary
        """
        contract_dict = _contracts_cache.get(contract_id)

        if not contract_dict:
            # Try to get from escrow
            escrow = _get_escrow()
            if escrow:
                contract = escrow.get_contract(contract_id)
                if contract:
                    contract_dict = escrow.to_dict(contract)

        if not contract_dict:
            raise HTTPException(404, f"Contract {contract_id} not found")

        return {
            'ok': True,
            'client_room': {
                'contract_id': contract_id,
                'room_url': contract_dict.get('client_room_url'),
                'status': contract_dict.get('status'),
                'total_amount_usd': contract_dict.get('total_amount_usd'),
                'funded_amount_usd': contract_dict.get('funded_amount_usd'),
                'released_amount_usd': contract_dict.get('released_amount_usd'),
                'milestones': contract_dict.get('milestones', []),
            }
        }

    @router.get("/execution/{execution_id}")
    async def get_execution_result(execution_id: str):
        """Get results of a full-stack execution"""
        result = _execution_results.get(execution_id)

        if not result:
            raise HTTPException(404, f"Execution {execution_id} not found")

        return {
            'ok': True,
            'execution': result,
        }


    @router.get("/customer-loop-status")
    async def get_customer_loop_status():
        """
        Get customer loop wiring status.

        Shows which outreach/presentation systems are configured
        and what's needed to close the customer loop.
        """
        wiring = _get_customer_loop_wiring()
        if not wiring:
            return {
                'ok': False,
                'error': 'Customer loop wiring not loaded',
                'recommendation': 'Check integration/customer_loop_wiring.py exists',
            }

        status = wiring.get_status()

        return {
            'ok': True,
            'customer_loop': status,
            'presentation_history': {
                'total_executions': len(_presentation_results),
                'recent': list(_presentation_results.values())[-5:] if _presentation_results else [],
            }
        }

    @router.get("/wall-of-wins")
    async def get_wall_of_wins():
        """
        Get Wall of Wins - completed contracts with real revenue.

        Only shows contracts where:
        - Customer signed SOW
        - At least one milestone funded
        - Work delivered and approved
        """
        escrow = _get_escrow()
        if not escrow:
            return {'ok': True, 'wall_of_wins': [], 'count': 0}

        # Get completed contracts (milestones released)
        wins = []
        stats = escrow.get_stats()

        # Build wall of wins from completed milestones
        for contract_id, contract_dict in _contracts_cache.items():
            released = contract_dict.get('released_amount_usd', 0)
            if released > 0:
                wins.append({
                    'contract_id': contract_id,
                    'title': contract_dict.get('title', 'Project'),
                    'revenue_usd': released,
                    'completed_at': contract_dict.get('completed_at'),
                })

        return {
            'ok': True,
            'wall_of_wins': wins,
            'count': len(wins),
            'total_revenue_usd': sum(w.get('revenue_usd', 0) for w in wins),
            'generated_at': datetime.now(timezone.utc).isoformat() + 'Z',
        }


def get_integration_router():
    """Get Integration router for app registration"""
    if FASTAPI_AVAILABLE:
        return router
    return None
