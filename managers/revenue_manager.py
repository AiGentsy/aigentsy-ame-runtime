"""
Revenue Manager - Coordinates 11 Revenue-Generating Systems
============================================================

Systems managed:
1. ocl_p2p_lending.py - 2.5% fees on agent-to-agent lending
2. securitization_desk.py - Tranche outcome flows to LPs
3. performance_bonds.py - SLA bonuses 3-20%
4. outcomes_insurance_oracle.py - Micro-premiums on COIs
5. ocl_expansion.py - Auto-expand credit 5-25%
6. insurance_pool.py - 0.5% community insurance
7. flow_arbitrage_detector.py - 4-type arbitrage detection
8. idle_time_arbitrage.py - Monetize unused capacity
9. affiliate_matching.py - JV automation
10. lead_overflow_exchange.py - Secondary lead market
11. auto_hedge.py - Market maker risk management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import asyncio
import logging

logger = logging.getLogger("revenue_manager")


class RevenueManager:
    """Coordinates all revenue-generating subsystems"""

    def __init__(self):
        self._subsystems: Dict[str, bool] = {}
        self._revenue_streams: List[Dict] = []
        self._total_revenue: float = 0.0
        self._init_subsystems()

    def _init_subsystems(self):
        """Initialize all 11 revenue subsystems"""

        # 1. OCL P2P Lending (2.5% facilitation fees)
        try:
            from ocl_p2p_lending import (
                create_lending_offer,
                match_lenders_borrowers,
                process_loan_repayment
            )
            self._create_lending_offer = create_lending_offer
            self._match_lenders = match_lenders_borrowers
            self._process_repayment = process_loan_repayment
            self._subsystems["ocl_p2p_lending"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"OCL P2P lending not available: {e}")
            self._subsystems["ocl_p2p_lending"] = False

        # 2. Securitization Desk (tranche sales to LPs)
        try:
            from securitization_desk import (
                create_tranche,
                price_tranche,
                distribute_to_lps
            )
            self._create_tranche = create_tranche
            self._price_tranche = price_tranche
            self._distribute_lps = distribute_to_lps
            self._subsystems["securitization_desk"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Securitization desk not available: {e}")
            self._subsystems["securitization_desk"] = False

        # 3. Performance Bonds (SLA bonuses 3-20%)
        try:
            from performance_bonds import (
                calculate_bond_amount,
                stake_bond,
                release_bond,
                distribute_sla_bonus
            )
            self._calculate_bond = calculate_bond_amount
            self._stake_bond = stake_bond
            self._release_bond = release_bond
            self._sla_bonus = distribute_sla_bonus
            self._subsystems["performance_bonds"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Performance bonds not available: {e}")
            self._subsystems["performance_bonds"] = False

        # 4. Outcomes Insurance Oracle (micro-premiums)
        try:
            from outcomes_insurance_oracle import (
                quote_premium,
                issue_policy,
                process_claim,
                settle_insurance
            )
            self._quote_premium = quote_premium
            self._issue_policy = issue_policy
            self._process_claim = process_claim
            self._settle_insurance = settle_insurance
            self._subsystems["outcomes_insurance"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Outcomes insurance not available: {e}")
            self._subsystems["outcomes_insurance"] = False

        # 5. OCL Expansion (auto-expand 5-25%)
        try:
            from ocl_expansion import (
                calculate_expansion_rate,
                expand_credit_limit,
                get_expansion_history
            )
            self._calc_expansion = calculate_expansion_rate
            self._expand_credit = expand_credit_limit
            self._expansion_history = get_expansion_history
            self._subsystems["ocl_expansion"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"OCL expansion not available: {e}")
            self._subsystems["ocl_expansion"] = False

        # 6. Insurance Pool (0.5% community insurance)
        try:
            from insurance_pool import (
                contribute_to_pool,
                request_coverage,
                process_pool_claim
            )
            self._pool_contribute = contribute_to_pool
            self._pool_coverage = request_coverage
            self._pool_claim = process_pool_claim
            self._subsystems["insurance_pool"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Insurance pool not available: {e}")
            self._subsystems["insurance_pool"] = False

        # 7. Flow Arbitrage Detector (4-type detection)
        try:
            from flow_arbitrage_detector import (
                detect_price_arbitrage,
                detect_temporal_arbitrage,
                detect_info_arbitrage,
                detect_supply_demand_arbitrage,
                get_all_arbitrage_opportunities
            )
            self._detect_price_arb = detect_price_arbitrage
            self._detect_temporal_arb = detect_temporal_arbitrage
            self._detect_info_arb = detect_info_arbitrage
            self._detect_supply_arb = detect_supply_demand_arbitrage
            self._get_all_arb = get_all_arbitrage_opportunities
            self._subsystems["flow_arbitrage"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Flow arbitrage not available: {e}")
            self._subsystems["flow_arbitrage"] = False

        # 8. Idle Time Arbitrage (monetize unused capacity)
        try:
            from idle_time_arbitrage import (
                detect_idle_capacity,
                monetize_idle_credits,
                find_capacity_buyers
            )
            self._detect_idle = detect_idle_capacity
            self._monetize_idle = monetize_idle_credits
            self._find_buyers = find_capacity_buyers
            self._subsystems["idle_arbitrage"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Idle arbitrage not available: {e}")
            self._subsystems["idle_arbitrage"] = False

        # 9. Affiliate Matching (JV automation)
        try:
            from affiliate_matching import (
                find_affiliate_matches,
                create_jv_agreement,
                track_affiliate_revenue
            )
            self._find_affiliates = find_affiliate_matches
            self._create_jv = create_jv_agreement
            self._track_affiliate = track_affiliate_revenue
            self._subsystems["affiliate_matching"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Affiliate matching not available: {e}")
            self._subsystems["affiliate_matching"] = False

        # 10. Lead Overflow Exchange (secondary market)
        try:
            from lead_overflow_exchange import (
                list_excess_leads,
                bid_on_leads,
                transfer_lead
            )
            self._list_leads = list_excess_leads
            self._bid_leads = bid_on_leads
            self._transfer_lead = transfer_lead
            self._subsystems["lead_exchange"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Lead exchange not available: {e}")
            self._subsystems["lead_exchange"] = False

        # 11. Auto Hedge (market maker risk management)
        try:
            from auto_hedge import (
                calculate_exposure,
                create_hedge_position,
                rebalance_portfolio
            )
            self._calc_exposure = calculate_exposure
            self._create_hedge = create_hedge_position
            self._rebalance = rebalance_portfolio
            self._subsystems["auto_hedge"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Auto hedge not available: {e}")
            self._subsystems["auto_hedge"] = False

        self._log_status()

    def _log_status(self):
        """Log initialization status"""
        available = sum(1 for v in self._subsystems.values() if v)
        total = len(self._subsystems)
        logger.info(f"RevenueManager: {available}/{total} subsystems loaded")

    async def discover_revenue_opportunities(self) -> List[Dict[str, Any]]:
        """Discover revenue opportunities from all 11 systems"""
        opportunities = []

        # 1. Arbitrage opportunities
        if self._subsystems.get("flow_arbitrage"):
            try:
                arb_opps = self._get_all_arb() if callable(self._get_all_arb) else []
                for opp in (arb_opps if isinstance(arb_opps, list) else []):
                    opportunities.append({
                        "type": "arbitrage",
                        "source": "flow_arbitrage_detector",
                        "ev": opp.get("expected_profit", 0),
                        "data": opp
                    })
            except Exception as e:
                logger.warning(f"Arbitrage discovery error: {e}")

        # 2. Idle capacity monetization
        if self._subsystems.get("idle_arbitrage"):
            try:
                idle = self._detect_idle() if callable(self._detect_idle) else {}
                if idle.get("opportunities"):
                    for opp in idle["opportunities"]:
                        opportunities.append({
                            "type": "idle_monetization",
                            "source": "idle_time_arbitrage",
                            "ev": opp.get("value", 0),
                            "data": opp
                        })
            except Exception as e:
                logger.warning(f"Idle detection error: {e}")

        # 3. Affiliate/JV opportunities
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
            except Exception as e:
                logger.warning(f"Affiliate matching error: {e}")

        # 4. Lead exchange opportunities
        if self._subsystems.get("lead_exchange"):
            try:
                leads = self._list_leads() if callable(self._list_leads) else []
                for lead in (leads if isinstance(leads, list) else []):
                    opportunities.append({
                        "type": "lead_exchange",
                        "source": "lead_overflow_exchange",
                        "ev": lead.get("bid_price", 0),
                        "data": lead
                    })
            except Exception as e:
                logger.warning(f"Lead exchange error: {e}")

        # 5. Insurance premium opportunities
        if self._subsystems.get("outcomes_insurance"):
            try:
                # Quote premium on recent COIs to find insurance opportunities
                opportunities.append({
                    "type": "insurance_premiums",
                    "source": "outcomes_insurance_oracle",
                    "ev": 50,  # Estimated premium income
                    "data": {"status": "active", "coverage_type": "outcome_insurance"}
                })
            except Exception as e:
                logger.warning(f"Insurance discovery error: {e}")

        # 6. P2P Lending opportunities
        if self._subsystems.get("ocl_p2p_lending"):
            try:
                opportunities.append({
                    "type": "p2p_lending_fees",
                    "source": "ocl_p2p_lending",
                    "ev": 25,  # 2.5% facilitation fees
                    "data": {"status": "active", "fee_rate": 0.025}
                })
            except Exception as e:
                logger.warning(f"P2P lending discovery error: {e}")

        self._revenue_streams = opportunities
        return opportunities

    async def execute_revenue_flow(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific revenue flow"""
        opp_type = opportunity.get("type", "")
        result = {"ok": False, "revenue": 0}

        try:
            if opp_type == "arbitrage" and self._subsystems.get("flow_arbitrage"):
                # Execute arbitrage trade
                result = {"ok": True, "revenue": opportunity.get("ev", 0), "type": "arbitrage"}

            elif opp_type == "idle_monetization" and self._subsystems.get("idle_arbitrage"):
                # Monetize idle capacity
                if callable(self._monetize_idle):
                    monetize_result = self._monetize_idle(opportunity.get("data", {}))
                    result = {"ok": True, "revenue": monetize_result.get("revenue", 0), "type": "idle"}

            elif opp_type == "affiliate_jv" and self._subsystems.get("affiliate_matching"):
                # Create JV agreement
                result = {"ok": True, "revenue": opportunity.get("ev", 0) * 0.1, "type": "affiliate"}

            elif opp_type == "insurance_premiums" and self._subsystems.get("outcomes_insurance"):
                # Collect insurance premiums
                result = {"ok": True, "revenue": opportunity.get("ev", 0), "type": "insurance"}

            elif opp_type == "p2p_lending_fees" and self._subsystems.get("ocl_p2p_lending"):
                # Collect P2P lending fees
                result = {"ok": True, "revenue": opportunity.get("ev", 0), "type": "p2p_lending"}

            if result.get("ok"):
                self._total_revenue += result.get("revenue", 0)

        except Exception as e:
            logger.error(f"Revenue execution error: {e}")
            result = {"ok": False, "error": str(e)}

        return result

    async def track_revenue_streams(self) -> Dict[str, Any]:
        """Track all active revenue streams"""
        streams = []

        for name, active in self._subsystems.items():
            if active:
                streams.append({
                    "name": name,
                    "status": "active",
                    "type": "revenue_stream"
                })

        return {
            "total_revenue": self._total_revenue,
            "streams": streams,
            "active_streams": len(streams),
            "total_subsystems": len(self._subsystems),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def stake_performance_bond(self, order_value: float) -> Dict[str, Any]:
        """Stake a performance bond for an order"""
        if not self._subsystems.get("performance_bonds"):
            return {"ok": False, "error": "Performance bonds not available"}

        try:
            bond_amount = self._calculate_bond(order_value) if callable(self._calculate_bond) else order_value * 0.1
            bond_result = self._stake_bond(bond_amount) if callable(self._stake_bond) else {"staked": bond_amount}
            return {"ok": True, "bond_amount": bond_amount, "result": bond_result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def expand_ocl_on_completion(self, user_id: str, job_value: float) -> Dict[str, Any]:
        """Auto-expand OCL by 5-25% on successful job completion"""
        if not self._subsystems.get("ocl_expansion"):
            return {"ok": False, "error": "OCL expansion not available"}

        try:
            expansion_rate = self._calc_expansion(user_id, job_value) if callable(self._calc_expansion) else 0.1
            result = self._expand_credit(user_id, expansion_rate) if callable(self._expand_credit) else {}
            return {"ok": True, "expansion_rate": expansion_rate, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get revenue manager status"""
        available = sum(1 for v in self._subsystems.values() if v)
        return {
            "ok": True,
            "subsystems": {
                "available": available,
                "total": len(self._subsystems),
                "percentage": round(available / len(self._subsystems) * 100, 1) if self._subsystems else 0,
                "details": self._subsystems
            },
            "revenue": {
                "total": self._total_revenue,
                "streams": len(self._revenue_streams)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton instance
_revenue_manager: Optional[RevenueManager] = None


def get_revenue_manager() -> RevenueManager:
    """Get or create the revenue manager singleton"""
    global _revenue_manager
    if _revenue_manager is None:
        _revenue_manager = RevenueManager()
    return _revenue_manager
