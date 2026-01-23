"""
Discovery Manager - Opportunity Discovery from 15+ Sources
==========================================================

Systems managed:
1. alpha_discovery_engine.py - 7 discovery dimensions
2. ultimate_discovery_engine.py - Combined discovery
3. auto_spawn_engine.py - AI venture factory
4. internet_domination_engine.py - Internet-wide scanning
5. flow_arbitrage_detector.py - Arbitrage opportunities
6. pain_point_detector.py - Pain point discovery
7. real_signal_ingestion.py - Signal processing
8. research_engine.py - Research capabilities
9. industry_knowledge.py - Domain expertise
10. advanced_discovery_dimensions.py - Extended dimensions
11. autonomous_deal_graph.py - Relationship opportunities
12. direct_outreach_engine.py - Lead discovery
13. affiliate_matching.py - JV opportunities
14. internet_discovery_expansion.py - Extended internet sources
15. discovery_to_queue_connector.py - Queue integration
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import asyncio
import logging

logger = logging.getLogger("discovery_manager")


class DiscoveryManager:
    """Coordinates all 15+ discovery sources"""

    def __init__(self):
        self._subsystems: Dict[str, bool] = {}
        self._opportunities: List[Dict] = []
        self._sources_used: List[str] = []
        self._init_subsystems()

    def _init_subsystems(self):
        """Initialize all 15 discovery subsystems"""

        # 1. Alpha Discovery Engine (7 dimensions)
        try:
            from alpha_discovery_engine import AlphaDiscoveryEngine
            self._alpha_discovery = AlphaDiscoveryEngine()
            self._subsystems["alpha_discovery"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Alpha discovery not available: {e}")
            self._subsystems["alpha_discovery"] = False

        # 2. Ultimate Discovery Engine
        try:
            from ultimate_discovery_engine import discover_all_opportunities
            self._ultimate_discover = discover_all_opportunities
            self._subsystems["ultimate_discovery"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Ultimate discovery not available: {e}")
            self._subsystems["ultimate_discovery"] = False

        # 3. Auto-Spawn Engine
        try:
            from auto_spawn_engine import get_spawn_engine
            self._spawn_engine = get_spawn_engine()
            self._subsystems["spawn_engine"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Spawn engine not available: {e}")
            self._subsystems["spawn_engine"] = False

        # 4. Internet Domination Engine
        try:
            from internet_domination_engine import get_domination_opportunities, domination_scan_all
            self._get_domination_opps = get_domination_opportunities
            self._domination_scan = domination_scan_all
            self._subsystems["internet_domination"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Internet domination not available: {e}")
            self._subsystems["internet_domination"] = False

        # 5. Flow Arbitrage Detector
        try:
            from flow_arbitrage_detector import (
                get_all_arbitrage_opportunities,
                detect_price_arbitrage,
                detect_temporal_arbitrage
            )
            self._get_arbitrage = get_all_arbitrage_opportunities
            self._price_arb = detect_price_arbitrage
            self._temporal_arb = detect_temporal_arbitrage
            self._subsystems["flow_arbitrage"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Flow arbitrage not available: {e}")
            self._subsystems["flow_arbitrage"] = False

        # 6. Pain Point Detector
        try:
            from pain_point_detector import PainPointDetector
            self._pain_detector = PainPointDetector()
            self._subsystems["pain_detector"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Pain detector not available: {e}")
            self._subsystems["pain_detector"] = False

        # 7. Real Signal Ingestion
        try:
            from real_signal_ingestion import get_signal_engine
            self._signal_engine = get_signal_engine()
            self._subsystems["signal_ingestion"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Signal ingestion not available: {e}")
            self._subsystems["signal_ingestion"] = False

        # 8. Research Engine
        try:
            from research_engine import ResearchEngine
            self._research_engine = ResearchEngine()
            self._subsystems["research_engine"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Research engine not available: {e}")
            self._subsystems["research_engine"] = False

        # 9. Industry Knowledge
        try:
            from industry_knowledge import get_industry_insights, analyze_industry_gaps
            self._industry_insights = get_industry_insights
            self._analyze_gaps = analyze_industry_gaps
            self._subsystems["industry_knowledge"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Industry knowledge not available: {e}")
            self._subsystems["industry_knowledge"] = False

        # 10. Advanced Discovery Dimensions
        try:
            from advanced_discovery_dimensions import (
                discover_advanced_opportunities,
                get_discovery_dimensions
            )
            self._advanced_discover = discover_advanced_opportunities
            self._get_dimensions = get_discovery_dimensions
            self._subsystems["advanced_dimensions"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Advanced dimensions not available: {e}")
            self._subsystems["advanced_dimensions"] = False

        # 11. Autonomous Deal Graph
        try:
            from autonomous_deal_graph import get_deal_graph
            self._deal_graph = get_deal_graph()
            self._subsystems["deal_graph"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Deal graph not available: {e}")
            self._subsystems["deal_graph"] = False

        # 12. Direct Outreach Engine (lead discovery)
        try:
            from direct_outreach_engine import find_prospects
            self._find_prospects = find_prospects
            self._subsystems["direct_outreach"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Direct outreach not available: {e}")
            self._subsystems["direct_outreach"] = False

        # 13. Affiliate Matching (JV opportunities)
        try:
            from affiliate_matching import find_affiliate_matches
            self._find_affiliates = find_affiliate_matches
            self._subsystems["affiliate_matching"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Affiliate matching not available: {e}")
            self._subsystems["affiliate_matching"] = False

        # 14. Internet Discovery Expansion
        try:
            from internet_search_setup import search_internet, internet_discovery_scan
            self._search_internet = search_internet
            self._internet_scan = internet_discovery_scan
            self._subsystems["internet_search"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Internet search not available: {e}")
            self._subsystems["internet_search"] = False

        # 15. Idle Time Arbitrage (capacity discovery)
        try:
            from idle_time_arbitrage import detect_idle_capacity
            self._detect_idle = detect_idle_capacity
            self._subsystems["idle_arbitrage"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Idle arbitrage not available: {e}")
            self._subsystems["idle_arbitrage"] = False

        self._log_status()

    def _log_status(self):
        """Log initialization status"""
        available = sum(1 for v in self._subsystems.values() if v)
        total = len(self._subsystems)
        logger.info(f"DiscoveryManager: {available}/{total} subsystems loaded")

    async def discover_all_sources(self) -> List[Dict[str, Any]]:
        """Discover opportunities from all 15+ sources"""
        opportunities = []
        self._sources_used = []

        # 1. Alpha Discovery (7 dimensions)
        if self._subsystems.get("alpha_discovery"):
            try:
                alpha_opps = await self._alpha_discovery.discover() if hasattr(self._alpha_discovery, 'discover') else {}
                for opp in alpha_opps.get("opportunities", []):
                    opportunities.append({**opp, "source": "alpha_discovery"})
                self._sources_used.append("alpha_discovery")
            except Exception as e:
                logger.warning(f"Alpha discovery error: {e}")

        # 2. Ultimate Discovery
        if self._subsystems.get("ultimate_discovery"):
            try:
                ultimate_opps = await self._ultimate_discover() if asyncio.iscoroutinefunction(self._ultimate_discover) else self._ultimate_discover()
                for opp in (ultimate_opps.get("opportunities", []) if isinstance(ultimate_opps, dict) else []):
                    opportunities.append({**opp, "source": "ultimate_discovery"})
                self._sources_used.append("ultimate_discovery")
            except Exception as e:
                logger.warning(f"Ultimate discovery error: {e}")

        # 3. Spawn Engine (AI Venture Factory)
        if self._subsystems.get("spawn_engine"):
            try:
                if hasattr(self._spawn_engine, 'detector'):
                    signals = await self._spawn_engine.detector.scan_all_sources()
                    for sig in (signals[:30] if isinstance(signals, list) else []):
                        opportunities.append({
                            "type": "spawn_opportunity",
                            "source": "spawn_engine",
                            "ev": getattr(sig, 'opportunity_score', 50),
                            "query": getattr(sig, 'query', '')[:100],
                            "platform": getattr(sig, 'source', 'unknown')
                        })
                    self._sources_used.append("spawn_engine")
            except Exception as e:
                logger.warning(f"Spawn engine error: {e}")

        # 4. Internet Domination
        if self._subsystems.get("internet_domination"):
            try:
                inet_opps = await self._get_domination_opps(limit=30)
                for opp in (inet_opps if isinstance(inet_opps, list) else []):
                    opportunities.append({**opp, "source": "internet_domination"})
                self._sources_used.append("internet_domination")
            except Exception as e:
                logger.warning(f"Internet domination error: {e}")

        # 5. Flow Arbitrage
        if self._subsystems.get("flow_arbitrage"):
            try:
                arb_opps = self._get_arbitrage() if callable(self._get_arbitrage) else []
                for opp in (arb_opps if isinstance(arb_opps, list) else []):
                    opportunities.append({
                        "type": "arbitrage",
                        "source": "flow_arbitrage",
                        "ev": opp.get("expected_profit", 0),
                        "data": opp
                    })
                self._sources_used.append("flow_arbitrage")
            except Exception as e:
                logger.warning(f"Flow arbitrage error: {e}")

        # 6. Pain Point Detection
        if self._subsystems.get("pain_detector"):
            try:
                if hasattr(self._pain_detector, 'detect'):
                    pains = await self._pain_detector.detect() if asyncio.iscoroutinefunction(self._pain_detector.detect) else self._pain_detector.detect()
                    for pain in (pains.get("pain_points", []) if isinstance(pains, dict) else []):
                        opportunities.append({
                            "type": "pain_point",
                            "source": "pain_detector",
                            "ev": pain.get("severity", 50),
                            "data": pain
                        })
                    self._sources_used.append("pain_detector")
            except Exception as e:
                logger.warning(f"Pain detector error: {e}")

        # 7. Signal Ingestion
        if self._subsystems.get("signal_ingestion"):
            try:
                if hasattr(self._signal_engine, 'get_latest_signals'):
                    signals = self._signal_engine.get_latest_signals(50)
                    for sig in (signals if isinstance(signals, list) else []):
                        opportunities.append({
                            "type": "signal",
                            "source": "signal_ingestion",
                            "ev": sig.get("strength", 30),
                            "data": sig
                        })
                    self._sources_used.append("signal_ingestion")
            except Exception as e:
                logger.warning(f"Signal ingestion error: {e}")

        # 8. Research Engine
        if self._subsystems.get("research_engine"):
            try:
                if hasattr(self._research_engine, 'discover_opportunities'):
                    research_opps = await self._research_engine.discover_opportunities() if asyncio.iscoroutinefunction(self._research_engine.discover_opportunities) else self._research_engine.discover_opportunities()
                    for opp in (research_opps if isinstance(research_opps, list) else []):
                        opportunities.append({**opp, "source": "research_engine"})
                    self._sources_used.append("research_engine")
            except Exception as e:
                logger.warning(f"Research engine error: {e}")

        # 9. Deal Graph (relationship opportunities)
        if self._subsystems.get("deal_graph"):
            try:
                if hasattr(self._deal_graph, 'get_intro_opportunities'):
                    intro_opps = self._deal_graph.get_intro_opportunities(limit=20)
                    for intro in (intro_opps if isinstance(intro_opps, list) else []):
                        opportunities.append({
                            "type": "relationship_intro",
                            "source": "deal_graph",
                            "ev": getattr(intro, 'expected_value', 50),
                            "data": intro.__dict__ if hasattr(intro, '__dict__') else intro
                        })
                    self._sources_used.append("deal_graph")
            except Exception as e:
                logger.warning(f"Deal graph error: {e}")

        # 10. Affiliate/JV Opportunities
        if self._subsystems.get("affiliate_matching"):
            try:
                affiliates = self._find_affiliates({}) if callable(self._find_affiliates) else []
                for aff in (affiliates if isinstance(affiliates, list) else []):
                    opportunities.append({
                        "type": "affiliate_jv",
                        "source": "affiliate_matching",
                        "ev": aff.get("potential_revenue", 0),
                        "data": aff
                    })
                self._sources_used.append("affiliate_matching")
            except Exception as e:
                logger.warning(f"Affiliate matching error: {e}")

        # 11. Industry Knowledge
        if self._subsystems.get("industry_knowledge"):
            try:
                if callable(self._analyze_gaps):
                    gaps = self._analyze_gaps()
                    for gap in (gaps if isinstance(gaps, list) else []):
                        opportunities.append({
                            "type": "industry_gap",
                            "source": "industry_knowledge",
                            "ev": gap.get("opportunity_size", 0),
                            "data": gap
                        })
                    self._sources_used.append("industry_knowledge")
            except Exception as e:
                logger.warning(f"Industry knowledge error: {e}")

        # 12. Advanced Dimensions
        if self._subsystems.get("advanced_dimensions"):
            try:
                if callable(self._advanced_discover):
                    adv_opps = await self._advanced_discover() if asyncio.iscoroutinefunction(self._advanced_discover) else self._advanced_discover()
                    for opp in (adv_opps if isinstance(adv_opps, list) else []):
                        opportunities.append({**opp, "source": "advanced_dimensions"})
                    self._sources_used.append("advanced_dimensions")
            except Exception as e:
                logger.warning(f"Advanced dimensions error: {e}")

        # 13. Idle Capacity
        if self._subsystems.get("idle_arbitrage"):
            try:
                idle = self._detect_idle() if callable(self._detect_idle) else {}
                for opp in idle.get("opportunities", []):
                    opportunities.append({
                        "type": "idle_capacity",
                        "source": "idle_arbitrage",
                        "ev": opp.get("value", 0),
                        "data": opp
                    })
                self._sources_used.append("idle_arbitrage")
            except Exception as e:
                logger.warning(f"Idle arbitrage error: {e}")

        self._opportunities = opportunities
        return opportunities

    async def enrich_with_network(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich opportunities with network/relationship data"""
        if not self._subsystems.get("deal_graph"):
            return opportunities

        try:
            enriched = []
            for opp in opportunities:
                enriched_opp = {**opp}

                # Try to get network multiplier
                if hasattr(self._deal_graph, 'get_network_multiplier'):
                    entity_id = opp.get("entity_id") or opp.get("user_id")
                    if entity_id:
                        multiplier = self._deal_graph.get_network_multiplier(entity_id)
                        enriched_opp["network_multiplier"] = multiplier
                        enriched_opp["ev"] = opp.get("ev", 0) * multiplier

                # Try to find related connections
                if hasattr(self._deal_graph, 'find_related'):
                    related = self._deal_graph.find_related(opp.get("type", ""))
                    enriched_opp["related_connections"] = len(related) if isinstance(related, list) else 0

                enriched.append(enriched_opp)

            return enriched

        except Exception as e:
            logger.warning(f"Network enrichment error: {e}")
            return opportunities

    async def detect_arbitrage(self) -> List[Dict[str, Any]]:
        """Detect arbitrage opportunities specifically"""
        arbitrage_opps = []

        if not self._subsystems.get("flow_arbitrage"):
            return arbitrage_opps

        try:
            # Price arbitrage
            if callable(self._price_arb):
                price_arbs = self._price_arb()
                for arb in (price_arbs if isinstance(price_arbs, list) else []):
                    arbitrage_opps.append({
                        "type": "price_arbitrage",
                        "source": "flow_arbitrage",
                        "ev": arb.get("spread", 0),
                        "data": arb
                    })

            # Temporal arbitrage
            if callable(self._temporal_arb):
                time_arbs = self._temporal_arb()
                for arb in (time_arbs if isinstance(time_arbs, list) else []):
                    arbitrage_opps.append({
                        "type": "temporal_arbitrage",
                        "source": "flow_arbitrage",
                        "ev": arb.get("expected_gain", 0),
                        "data": arb
                    })

        except Exception as e:
            logger.warning(f"Arbitrage detection error: {e}")

        return arbitrage_opps

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
                "opportunities_found": len(self._opportunities),
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
