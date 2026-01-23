"""
Discovery Manager - Coordinates 17 Discovery Source Systems
============================================================

Systems managed (with ACTUAL function imports):
1. alpha_discovery_engine.py - AlphaDiscoveryEngine, CapabilityMatcher
2. ultimate_discovery_engine.py - scrape_* functions for 20+ platforms
3. auto_spawn_engine.py - AutoSpawnEngine, TrendDetector, BusinessSpawner
4. internet_domination_engine.py - RealScrapers, include_domination_engine
5. v110_gap_harvesters.py - scan_all_harvesters (20+ gap types)
6. flow_arbitrage_detector.py - FlowArbitrageDetector
7. idle_time_arbitrage.py - IdleTimeArbitrage, detect_idle_capacity
8. affiliate_matching.py - match_signal_to_affiliate
9. research_engine.py - ResearchEngine, PerplexityResearcher
10. pain_point_detector.py - PainPointDetector
11. dealgraph.py - create_deal, get_deal_summary
12. real_signal_ingestion.py - RealSignalIngestionEngine, get_signal_engine
13. platform_recruitment_engine.py - RecruitmentEngine, get_recruitment_engine
14. advanced_discovery_dimensions.py - PredictiveIntelligenceEngine
15. mega_discovery_engine.py - MegaDiscoveryEngine
16. autonomous_deal_graph.py - DealGraph, RelationshipGraph (network effects)
17. internet_discovery_expansion.py - SearchEngineScanner, ContactExtractor
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import asyncio
import logging

logger = logging.getLogger("discovery_manager")


class DiscoveryManager:
    """Coordinates all discovery source subsystems"""

    def __init__(self):
        self._subsystems: Dict[str, bool] = {}
        self._opportunities_found: int = 0
        self._sources_used: List[str] = []
        self._init_subsystems()

    def _init_subsystems(self):
        """Initialize all 15 discovery subsystems with CORRECT imports"""

        # 1. Alpha Discovery Engine
        try:
            from alpha_discovery_engine import (
                AlphaDiscoveryEngine,
                CapabilityMatcher,
                AlphaDiscoveryRouter,
                MultiAIOrchestrator
            )
            self._alpha_engine = AlphaDiscoveryEngine()
            self._capability_matcher = CapabilityMatcher
            self._alpha_router = AlphaDiscoveryRouter
            self._ai_orchestrator = MultiAIOrchestrator
            self._subsystems["alpha_discovery"] = True
            logger.info("Alpha Discovery Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Alpha discovery not available: {e}")
            self._subsystems["alpha_discovery"] = False

        # 2. Ultimate Discovery Engine (20+ platform scrapers)
        try:
            from ultimate_discovery_engine import (
                scrape_github,
                scrape_github_bounties,
                scrape_reddit,
                scrape_hackernews,
                scrape_upwork,
                scrape_remoteok,
                scrape_weworkremotely,
                scrape_indiehackers,
                scrape_fiverr,
                scrape_producthunt,
                scrape_devpost,
                scrape_linkedin_jobs,
                scrape_indeed,
                calculate_fulfillability
            )
            self._scrape_github = scrape_github
            self._scrape_bounties = scrape_github_bounties
            self._scrape_reddit = scrape_reddit
            self._scrape_hackernews = scrape_hackernews
            self._scrape_upwork = scrape_upwork
            self._scrape_remoteok = scrape_remoteok
            self._scrape_weworkremotely = scrape_weworkremotely
            self._scrape_indiehackers = scrape_indiehackers
            self._scrape_fiverr = scrape_fiverr
            self._scrape_producthunt = scrape_producthunt
            self._scrape_devpost = scrape_devpost
            self._scrape_linkedin = scrape_linkedin_jobs
            self._scrape_indeed = scrape_indeed
            self._calc_fulfillability = calculate_fulfillability
            self._subsystems["ultimate_discovery"] = True
            logger.info("Ultimate Discovery Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Ultimate discovery not available: {e}")
            self._subsystems["ultimate_discovery"] = False

        # 3. Auto Spawn Engine
        try:
            from auto_spawn_engine import (
                AutoSpawnEngine,
                get_spawn_engine,
                TrendDetector,
                BusinessSpawner,
                LifecycleManager,
                AdoptionSystem,
                SpawnNetwork,
                UniversalAI,
                get_universal_ai
            )
            self._spawn_engine = get_spawn_engine()
            self._trend_detector = TrendDetector
            self._business_spawner = BusinessSpawner
            self._lifecycle_mgr = LifecycleManager
            self._adoption_sys = AdoptionSystem
            self._spawn_network = SpawnNetwork
            self._universal_ai = get_universal_ai()
            self._subsystems["spawn_engine"] = True
            logger.info("Auto Spawn Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Spawn engine not available: {e}")
            self._subsystems["spawn_engine"] = False

        # 4. Internet Domination Engine
        try:
            from internet_domination_engine import (
                RealScrapers,
                include_domination_engine
            )
            self._real_scrapers = RealScrapers()
            self._include_domination = include_domination_engine
            self._subsystems["internet_domination"] = True
            logger.info("Internet Domination Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Internet domination not available: {e}")
            self._subsystems["internet_domination"] = False

        # 5. V110 Gap Harvesters (20+ gap types)
        try:
            from v110_gap_harvesters import (
                scan_all_harvesters,
                apcr_scan_credits,
                affiliate_scan_broken_links,
                saas_optimize_rightsizing,
                seo_scan_404s,
                market_scan_orphans,
                grants_scan,
                domains_scan_expiries,
                i18n_scan,
                car_scout_risks
            )
            self._scan_harvesters = scan_all_harvesters
            self._apcr_scan = apcr_scan_credits
            self._affiliate_scan = affiliate_scan_broken_links
            self._saas_scan = saas_optimize_rightsizing
            self._seo_scan = seo_scan_404s
            self._market_scan = market_scan_orphans
            self._grants_scan = grants_scan
            self._domains_scan = domains_scan_expiries
            self._i18n_scan = i18n_scan
            self._car_scan = car_scout_risks
            self._subsystems["gap_harvesters"] = True
            logger.info("V110 Gap Harvesters loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Gap harvesters not available: {e}")
            self._subsystems["gap_harvesters"] = False

        # 6. Flow Arbitrage Detector
        try:
            from flow_arbitrage_detector import FlowArbitrageDetector
            self._flow_detector = FlowArbitrageDetector()
            self._subsystems["flow_arbitrage"] = True
            logger.info("Flow Arbitrage Detector loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Flow arbitrage not available: {e}")
            self._subsystems["flow_arbitrage"] = False

        # 7. Idle Time Arbitrage
        try:
            from idle_time_arbitrage import (
                IdleTimeArbitrage,
                detect_idle_capacity,
                find_idle_slots,
                get_idle_arbitrage_stats
            )
            self._idle_arb = IdleTimeArbitrage()
            self._detect_idle = detect_idle_capacity
            self._find_slots = find_idle_slots
            self._idle_stats = get_idle_arbitrage_stats
            self._subsystems["idle_arbitrage"] = True
            logger.info("Idle Time Arbitrage loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Idle arbitrage not available: {e}")
            self._subsystems["idle_arbitrage"] = False

        # 8. Affiliate Matching
        try:
            from affiliate_matching import (
                match_signal_to_affiliate,
                match_batch_signals,
                get_affiliate_status,
                get_conversion_stats
            )
            self._match_affiliate = match_signal_to_affiliate
            self._batch_match = match_batch_signals
            self._affiliate_status = get_affiliate_status
            self._conversion_stats = get_conversion_stats
            self._subsystems["affiliate_matching"] = True
            logger.info("Affiliate Matching loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Affiliate matching not available: {e}")
            self._subsystems["affiliate_matching"] = False

        # 9. Research Engine
        try:
            from research_engine import (
                ResearchEngine,
                PerplexityResearcher,
                ClaudeOpusResearcher,
                GeminiResearcher,
                ResearchAnalyzer,
                PredictiveMarketEngine
            )
            self._research_engine = ResearchEngine()
            self._perplexity = PerplexityResearcher
            self._claude_researcher = ClaudeOpusResearcher
            self._gemini_researcher = GeminiResearcher
            self._research_analyzer = ResearchAnalyzer
            self._market_predictor = PredictiveMarketEngine
            self._subsystems["research_engine"] = True
            logger.info("Research Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Research engine not available: {e}")
            self._subsystems["research_engine"] = False

        # 10. Pain Point Detector
        try:
            from pain_point_detector import PainPointDetector
            self._pain_detector = PainPointDetector()
            self._subsystems["pain_detector"] = True
            logger.info("Pain Point Detector loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Pain detector not available: {e}")
            self._subsystems["pain_detector"] = False

        # 11. Deal Graph
        try:
            from dealgraph import (
                create_deal,
                get_deal_summary,
                transition_state,
                calculate_revenue_split
            )
            self._create_deal = create_deal
            self._deal_summary = get_deal_summary
            self._transition_state = transition_state
            self._revenue_split = calculate_revenue_split
            self._subsystems["deal_graph"] = True
            logger.info("Deal Graph loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Deal graph not available: {e}")
            self._subsystems["deal_graph"] = False

        # 12. Signal Ingestion
        try:
            from real_signal_ingestion import (
                RealSignalIngestionEngine,
                get_signal_engine
            )
            self._signal_engine = get_signal_engine()
            self._subsystems["signal_ingestion"] = True
            logger.info("Signal Ingestion loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Signal ingestion not available: {e}")
            self._subsystems["signal_ingestion"] = False

        # 13. Platform Recruitment Engine
        try:
            from platform_recruitment_engine import (
                RecruitmentEngine,
                get_recruitment_engine,
                get_all_platform_pitches
            )
            self._recruitment_engine = get_recruitment_engine()
            self._platform_pitches = get_all_platform_pitches
            self._subsystems["platform_recruitment"] = True
            logger.info("Platform Recruitment Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Platform recruitment not available: {e}")
            self._subsystems["platform_recruitment"] = False

        # 14. Advanced Discovery Dimensions
        try:
            from advanced_discovery_dimensions import (
                PredictiveIntelligenceEngine,
                NetworkAmplificationEngine,
                OpportunityCreationEngine,
                EmergentPatternDetector
            )
            self._predictive_intel = PredictiveIntelligenceEngine()
            self._network_amp = NetworkAmplificationEngine()
            self._opportunity_creator = OpportunityCreationEngine()
            self._pattern_detector = EmergentPatternDetector()
            self._subsystems["advanced_dimensions"] = True
            logger.info("Advanced Discovery Dimensions loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Advanced dimensions not available: {e}")
            self._subsystems["advanced_dimensions"] = False

        # 15. Mega Discovery Engine
        try:
            from mega_discovery_engine import MegaDiscoveryEngine
            self._mega_engine = MegaDiscoveryEngine()
            self._subsystems["mega_discovery"] = True
            logger.info("Mega Discovery Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Mega discovery not available: {e}")
            self._subsystems["mega_discovery"] = False

        # 16. Autonomous Deal Graph (network effects)
        try:
            from autonomous_deal_graph import (
                DealGraph,
                get_deal_graph,
                RelationshipGraph,
                IntroOpportunity
            )
            self._auto_deal_graph = get_deal_graph()
            self._relationship_graph = RelationshipGraph
            self._intro_opportunity = IntroOpportunity
            self._subsystems["autonomous_deal_graph"] = True
            logger.info("Autonomous Deal Graph loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Autonomous Deal Graph not available: {e}")
            self._subsystems["autonomous_deal_graph"] = False

        # 17. Internet Discovery Expansion
        try:
            from internet_discovery_expansion import (
                InternetDiscoveryExpansion,
                SearchEngineScanner,
                ContactExtractor,
                NewsScanner,
                FreelancePlatformScanner,
                expand_discovery_dimensions
            )
            self._internet_expansion = InternetDiscoveryExpansion()
            self._search_scanner = SearchEngineScanner
            self._contact_extractor = ContactExtractor
            self._news_scanner = NewsScanner
            self._freelance_scanner = FreelancePlatformScanner
            self._expand_discovery = expand_discovery_dimensions
            self._subsystems["internet_expansion"] = True
            logger.info("Internet Discovery Expansion loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Internet Discovery Expansion not available: {e}")
            self._subsystems["internet_expansion"] = False

        self._log_status()

    def _log_status(self):
        """Log initialization status"""
        available = sum(1 for v in self._subsystems.values() if v)
        total = len(self._subsystems)
        logger.info(f"DiscoveryManager: {available}/{total} subsystems loaded")

    async def discover_all_sources(self, user_profile: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Discover opportunities from all 15 sources"""
        if user_profile is None:
            user_profile = {"skills": ["python", "automation"], "budget_min": 50}

        all_opportunities = []
        sources_used = []

        # 1. Alpha Discovery
        if self._subsystems.get("alpha_discovery"):
            try:
                if hasattr(self._alpha_engine, 'discover'):
                    opps = await self._alpha_engine.discover(user_profile)
                    for opp in (opps if isinstance(opps, list) else []):
                        opp["source"] = "alpha_discovery"
                        all_opportunities.append(opp)
                    sources_used.append("alpha_discovery")
            except Exception as e:
                logger.warning(f"Alpha discovery error: {e}")

        # 2. Ultimate Discovery (multi-platform)
        if self._subsystems.get("ultimate_discovery"):
            try:
                scrapers = [
                    ("github", self._scrape_github),
                    ("reddit", self._scrape_reddit),
                    ("hackernews", self._scrape_hackernews),
                    ("upwork", self._scrape_upwork),
                ]
                for name, scraper in scrapers:
                    try:
                        if callable(scraper):
                            opps = await scraper(user_profile)
                            for opp in (opps if isinstance(opps, list) else []):
                                opp["source"] = f"ultimate/{name}"
                                all_opportunities.append(opp)
                    except:
                        pass
                sources_used.append("ultimate_discovery")
            except Exception as e:
                logger.warning(f"Ultimate discovery error: {e}")

        # 3. Auto Spawn Engine
        if self._subsystems.get("spawn_engine"):
            try:
                if hasattr(self._spawn_engine, 'discover_trends'):
                    trends = await self._spawn_engine.discover_trends()
                    for trend in (trends if isinstance(trends, list) else []):
                        all_opportunities.append({
                            "type": "spawn_trend",
                            "source": "spawn_engine",
                            "ev": trend.get("potential_value", 100),
                            "data": trend
                        })
                    sources_used.append("spawn_engine")
            except Exception as e:
                logger.warning(f"Spawn engine error: {e}")

        # 4. Internet Domination
        if self._subsystems.get("internet_domination"):
            try:
                if callable(self._discover_internet):
                    opps = await self._discover_internet(user_profile)
                    for opp in (opps if isinstance(opps, list) else []):
                        opp["source"] = "internet_domination"
                        all_opportunities.append(opp)
                    sources_used.append("internet_domination")
            except Exception as e:
                logger.warning(f"Internet domination error: {e}")

        # 5. Gap Harvesters
        if self._subsystems.get("gap_harvesters"):
            try:
                if callable(self._scan_harvesters):
                    gaps = await self._scan_harvesters()
                    if isinstance(gaps, dict) and gaps.get("ok"):
                        for name, data in gaps.get("harvesters", {}).items():
                            all_opportunities.append({
                                "type": "gap_harvester",
                                "source": f"gap/{name}",
                                "ev": data.get("potential_ev", 50) if isinstance(data, dict) else 50,
                                "data": data
                            })
                    sources_used.append("gap_harvesters")
            except Exception as e:
                logger.warning(f"Gap harvesters error: {e}")

        # 6. Flow Arbitrage
        if self._subsystems.get("flow_arbitrage"):
            try:
                if hasattr(self._flow_detector, 'scan_all_arbitrage'):
                    arbs = self._flow_detector.scan_all_arbitrage()
                    for arb in (arbs if isinstance(arbs, list) else []):
                        all_opportunities.append({
                            "type": "arbitrage",
                            "source": "flow_arbitrage",
                            "ev": arb.get("expected_profit", 0),
                            "data": arb
                        })
                    sources_used.append("flow_arbitrage")
            except Exception as e:
                logger.warning(f"Flow arbitrage error: {e}")

        # 7. Idle Arbitrage
        if self._subsystems.get("idle_arbitrage"):
            try:
                if callable(self._detect_idle):
                    idle = self._detect_idle()
                    if isinstance(idle, dict):
                        for slot in idle.get("idle_slots", []):
                            all_opportunities.append({
                                "type": "idle_capacity",
                                "source": "idle_arbitrage",
                                "ev": slot.get("value", 25),
                                "data": slot
                            })
                    sources_used.append("idle_arbitrage")
            except Exception as e:
                logger.warning(f"Idle arbitrage error: {e}")

        # 8. Research Engine
        if self._subsystems.get("research_engine"):
            try:
                if hasattr(self._research_engine, 'discover_opportunities'):
                    research = await self._research_engine.discover_opportunities(user_profile)
                    for opp in (research if isinstance(research, list) else []):
                        opp["source"] = "research_engine"
                        all_opportunities.append(opp)
                    sources_used.append("research_engine")
            except Exception as e:
                logger.warning(f"Research engine error: {e}")

        # 9. Pain Point Detection
        if self._subsystems.get("pain_detector"):
            try:
                if callable(self._detect_pain):
                    pains = await self._detect_pain(user_profile)
                    for pain in (pains if isinstance(pains, list) else []):
                        all_opportunities.append({
                            "type": "pain_point",
                            "source": "pain_detector",
                            "ev": pain.get("solution_value", 75),
                            "data": pain
                        })
                    sources_used.append("pain_detector")
            except Exception as e:
                logger.warning(f"Pain detector error: {e}")

        # 10. Deal Graph relationships
        if self._subsystems.get("deal_graph"):
            try:
                if hasattr(self._deal_graph, 'find_opportunities'):
                    deals = self._deal_graph.find_opportunities()
                    for deal in (deals if isinstance(deals, list) else []):
                        all_opportunities.append({
                            "type": "deal_relationship",
                            "source": "deal_graph",
                            "ev": deal.get("value", 50),
                            "data": deal
                        })
                    sources_used.append("deal_graph")
            except Exception as e:
                logger.warning(f"Deal graph error: {e}")

        self._opportunities_found += len(all_opportunities)
        self._sources_used = sources_used

        return all_opportunities

    async def enrich_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich opportunities with additional data"""
        enriched = []

        for opp in opportunities:
            enriched_opp = {**opp}

            # Add fulfillability score if available
            if self._subsystems.get("ultimate_discovery") and callable(self._calc_fulfillability):
                try:
                    fulfillability = self._calc_fulfillability(opp)
                    enriched_opp["fulfillability"] = fulfillability
                except:
                    pass

            enriched_opp["enriched_at"] = datetime.now(timezone.utc).isoformat()
            enriched.append(enriched_opp)

        return enriched

    def get_status(self) -> Dict[str, Any]:
        """Get discovery manager status"""
        available = sum(1 for v in self._subsystems.values() if v)
        return {
            "ok": True,
            "subsystems": {
                "available": available,
                "total": len(self._subsystems),
                "percentage": round(available / len(self._subsystems) * 100, 1) if self._subsystems else 0,
                "details": self._subsystems
            },
            "discovery": {
                "opportunities_found": self._opportunities_found,
                "sources_used": self._sources_used
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton instance
_discovery_manager: Optional[DiscoveryManager] = None


def get_discovery_manager() -> DiscoveryManager:
    """Get or create the discovery manager singleton"""
    global _discovery_manager
    if _discovery_manager is None:
        _discovery_manager = DiscoveryManager()
    return _discovery_manager
