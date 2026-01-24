"""
Master Playbook - Ultimate Accretion Pack Integration
======================================================

Integrates all 12 profit-maximizing intelligence layers:

Tier 1 - Revenue Optimization:
  - LTV Oracle: Predict lifetime value, churn risk
  - PriceArm V2: Dynamic pricing with guardrails
  - Attention Router: Thompson Sampling budget allocation

Tier 2 - Learning:
  - Causal Uplift Trainer: Estimate causal effects
  - Hierarchical Bandits: Multi-level arm selection

Tier 3 - Capital Allocation:
  - R3 Allocator: Kelly-criterion risk-adjusted allocation

Tier 4 - Quality & Trust:
  - AIGx Incentives: Hot-streak bonuses, failure rebates
  - Adversarial Guard: Sybil/bot/fraud detection

Tier 5 - Accountability:
  - Policy Shapley: Fair attribution via Shapley values
  - Policy Lab: Always-on micro-experiments
  - KPI Board: Real-time business intelligence

Impact: Full autonomous profit maximization stack
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import logging
import asyncio

logger = logging.getLogger("master_playbook")


class MasterPlaybook:
    """
    Master orchestrator integrating all 12 profit-maximizing modules

    Provides a unified interface for:
    - Opportunity evaluation and pricing
    - Budget and capital allocation
    - Execution with quality controls
    - Learning and attribution
    - Experimentation and measurement
    """

    def __init__(self):
        """Initialize all intelligence layers"""
        # Tier 1: Revenue Optimization
        self._init_tier1_revenue()

        # Tier 2: Learning
        self._init_tier2_learning()

        # Tier 3: Capital Allocation
        self._init_tier3_capital()

        # Tier 4: Quality & Trust
        self._init_tier4_quality()

        # Tier 5: Accountability
        self._init_tier5_accountability()

        self._initialized = True
        logger.info("MasterPlaybook initialized with all 12 intelligence layers")

    def _init_tier1_revenue(self):
        """Initialize Tier 1: Revenue optimization modules"""
        # LTV Oracle
        try:
            from brain_economics.ltv_oracle import get_ltv_oracle
            self.ltv_oracle = get_ltv_oracle()
            logger.info("✓ LTV Oracle loaded")
        except ImportError as e:
            logger.warning(f"LTV Oracle not available: {e}")
            self.ltv_oracle = None

        # PriceArm V2
        try:
            from pricing.price_arm_v2 import get_price_arm
            self.price_arm_v2 = get_price_arm()
            logger.info("✓ PriceArm V2 loaded")
        except ImportError as e:
            logger.warning(f"PriceArm V2 not available: {e}")
            self.price_arm_v2 = None

        # Attention Router
        try:
            from growth.attention_router import get_attention_router
            self.attention_router = get_attention_router()
            logger.info("✓ Attention Router loaded")
        except ImportError as e:
            logger.warning(f"Attention Router not available: {e}")
            self.attention_router = None

    def _init_tier2_learning(self):
        """Initialize Tier 2: Learning modules"""
        # Causal Uplift Trainer
        try:
            from learning.causal_uplift_trainer import get_causal_uplift_trainer
            self.causal_uplift = get_causal_uplift_trainer()
            logger.info("✓ Causal Uplift Trainer loaded")
        except ImportError as e:
            logger.warning(f"Causal Uplift Trainer not available: {e}")
            self.causal_uplift = None

        # Hierarchical Bandits
        try:
            from learning.hier_bandits import get_hierarchical_bandits
            self.hier_bandits = get_hierarchical_bandits()
            logger.info("✓ Hierarchical Bandits loaded")
        except ImportError as e:
            logger.warning(f"Hierarchical Bandits not available: {e}")
            self.hier_bandits = None

    def _init_tier3_capital(self):
        """Initialize Tier 3: Capital allocation modules"""
        # R3 Allocator
        try:
            from allocation.r3_allocator import get_r3_allocator
            self.r3_allocator = get_r3_allocator()
            logger.info("✓ R3 Allocator loaded")
        except ImportError as e:
            logger.warning(f"R3 Allocator not available: {e}")
            self.r3_allocator = None

    def _init_tier4_quality(self):
        """Initialize Tier 4: Quality & trust modules"""
        # AIGx Incentives
        try:
            from assurance.aigx_incentives import get_aigx_incentives
            self.aigx_incentives = get_aigx_incentives()
            logger.info("✓ AIGx Incentives loaded")
        except ImportError as e:
            logger.warning(f"AIGx Incentives not available: {e}")
            self.aigx_incentives = None

        # Adversarial Guard
        try:
            from quality.adversarial_guard import get_adversarial_guard
            self.adversarial_guard = get_adversarial_guard()
            logger.info("✓ Adversarial Guard loaded")
        except ImportError as e:
            logger.warning(f"Adversarial Guard not available: {e}")
            self.adversarial_guard = None

    def _init_tier5_accountability(self):
        """Initialize Tier 5: Accountability modules"""
        # Policy Shapley
        try:
            from econometrics.policy_shapley import get_policy_shapley
            self.policy_shapley = get_policy_shapley()
            logger.info("✓ Policy Shapley loaded")
        except ImportError as e:
            logger.warning(f"Policy Shapley not available: {e}")
            self.policy_shapley = None

        # Policy Lab
        try:
            from experiments.policy_lab import get_policy_lab
            self.policy_lab = get_policy_lab()
            logger.info("✓ Policy Lab loaded")
        except ImportError as e:
            logger.warning(f"Policy Lab not available: {e}")
            self.policy_lab = None

        # KPI Board
        try:
            from reporting.kpi_board import get_kpi_board
            self.kpi_board = get_kpi_board()
            logger.info("✓ KPI Board loaded")
        except ImportError as e:
            logger.warning(f"KPI Board not available: {e}")
            self.kpi_board = None

    async def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full opportunity evaluation using all intelligence layers

        Returns:
            Comprehensive evaluation with pricing, risk, allocation recommendation
        """
        result = {
            "opp_id": opportunity.get("id", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tiers": {}
        }

        # Tier 1: Revenue analysis
        tier1 = {}

        if self.ltv_oracle:
            ltv_result = self.ltv_oracle.predict(opportunity)
            tier1["ltv"] = ltv_result

        if self.price_arm_v2:
            base_value = float(opportunity.get("value", 100))
            risk_data = {"adversarial_score": 0.1}

            if self.adversarial_guard:
                risk_data["adversarial_score"] = self.adversarial_guard.score(opportunity)

            price_result = self.price_arm_v2.quote(opportunity, base_value, risk_data)
            tier1["pricing"] = price_result

        result["tiers"]["tier1_revenue"] = tier1

        # Tier 2: Learning signals
        tier2 = {}

        if self.hier_bandits:
            context = {
                "segment": opportunity.get("segment", "smb"),
                "platform": opportunity.get("platform", "upwork"),
                "sku": opportunity.get("sku", "default")
            }
            available_arms = ["base", "premium", "enterprise"]
            arm, expected = self.hier_bandits.select_arm(context, available_arms)
            tier2["bandit_selection"] = {"arm": arm, "expected_value": expected}

        result["tiers"]["tier2_learning"] = tier2

        # Tier 3: Capital allocation
        tier3 = {}

        if self.r3_allocator:
            # Single opportunity allocation
            opps = [opportunity]
            budget = float(opportunity.get("budget", 1000))
            allocation = self.r3_allocator.allocate(opps, budget, {})
            tier3["allocation"] = allocation

        result["tiers"]["tier3_capital"] = tier3

        # Tier 4: Quality checks
        tier4 = {}

        if self.adversarial_guard:
            assessment = self.adversarial_guard.assess(opportunity)
            tier4["adversarial"] = {
                "risk_score": assessment.risk_score,
                "flags": assessment.flags,
                "require_escrow": assessment.require_escrow,
                "block": assessment.block
            }

        result["tiers"]["tier4_quality"] = tier4

        # Tier 5: Experiment assignment
        tier5 = {}

        if self.policy_lab:
            available_engines = opportunity.get("engines", ["default"])
            experiment_engine = self.policy_lab.assign(
                opportunity.get("id", ""),
                available_engines
            )
            if experiment_engine:
                tier5["experiment_assignment"] = experiment_engine

        result["tiers"]["tier5_accountability"] = tier5

        # Final recommendation
        result["recommendation"] = self._synthesize_recommendation(result)

        return result

    def _synthesize_recommendation(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize final recommendation from all tier evaluations"""
        recommendation = {
            "proceed": True,
            "confidence": 0.8,
            "actions": [],
            "warnings": []
        }

        tier4 = evaluation.get("tiers", {}).get("tier4_quality", {})
        adversarial = tier4.get("adversarial", {})

        # Check for blocks
        if adversarial.get("block", False):
            recommendation["proceed"] = False
            recommendation["confidence"] = 0.95
            recommendation["actions"].append("BLOCK: High adversarial risk")
            return recommendation

        # Check for escrow requirement
        if adversarial.get("require_escrow", False):
            recommendation["actions"].append("REQUIRE_ESCROW")
            recommendation["warnings"].append("Elevated risk - escrow recommended")

        # Get pricing
        tier1 = evaluation.get("tiers", {}).get("tier1_revenue", {})
        pricing = tier1.get("pricing", {})
        if pricing:
            recommendation["target_price"] = pricing.get("target_price", 0)
            recommendation["price_range"] = [
                pricing.get("min_price", 0),
                pricing.get("max_price", 0)
            ]

        # Get allocation
        tier3 = evaluation.get("tiers", {}).get("tier3_capital", {})
        allocation = tier3.get("allocation", {})
        if allocation.get("allocations"):
            alloc = allocation["allocations"][0]
            recommendation["allocated_amount"] = alloc.get("allocated", 0)
            recommendation["kelly_fraction"] = alloc.get("kelly_fraction", 0)

        return recommendation

    async def record_outcome(self, result: Dict[str, Any]):
        """
        Record execution outcome to all learning systems

        Args:
            result: Execution result with success, revenue, engine, etc.
        """
        # KPI Board
        if self.kpi_board:
            self.kpi_board.emit({
                "ts": datetime.now(timezone.utc).isoformat(),
                "opp_id": result.get("opp_id", ""),
                "revenue": result.get("revenue", 0),
                "spend": result.get("spend", 0),
                "tokens": result.get("tokens_used", 0),
                "engine": result.get("engine", "unknown"),
                "success": result.get("ok", False),
                "assured": result.get("assured", False),
                "refunded": result.get("refunded", False)
            })

        # Hierarchical Bandits update
        if self.hier_bandits:
            context = {
                "segment": result.get("segment", "smb"),
                "platform": result.get("platform", "upwork"),
                "sku": result.get("sku", "default")
            }
            self.hier_bandits.update(
                context=context,
                arm=result.get("engine", "default"),
                reward=result.get("revenue", 0)
            )

        # Policy Lab outcome
        if self.policy_lab:
            self.policy_lab.record_outcome(
                engine=result.get("engine", "unknown"),
                success=result.get("ok", False),
                revenue=result.get("revenue", 0)
            )

        # AIGx Incentives
        if self.aigx_incentives:
            incentives = self.aigx_incentives.incentives_for(result)
            result["incentives"] = incentives

        # Policy Shapley
        if self.policy_shapley:
            self.policy_shapley.record_outcome(
                engines_used=result.get("engines_used", [result.get("engine", "unknown")]),
                revenue=result.get("revenue", 0),
                baseline_revenue=result.get("baseline", 0)
            )

        logger.info(f"Outcome recorded for opp_id={result.get('opp_id', 'unknown')}")

    async def get_budget_weights(self, platform_kpis: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Get optimal budget allocation weights across platforms

        Args:
            platform_kpis: Dict of platform -> {ctr, conversion_rate, cac, ltv}

        Returns:
            Dict of platform -> weight (sums to 1.0)
        """
        if self.attention_router:
            return self.attention_router.weights(platform_kpis)
        return {}

    async def calculate_attribution(self, outcomes: List[Dict] = None) -> Dict[str, float]:
        """
        Calculate Shapley attribution for all engines

        Returns:
            Dict of engine -> Shapley value (contribution share)
        """
        if self.policy_shapley:
            return await self.policy_shapley.value(outcomes)
        return {}

    async def get_causal_uplift(self, outcomes: List[Dict]) -> Dict[str, float]:
        """
        Estimate causal uplift for each engine

        Returns:
            Dict of engine -> uplift score
        """
        if self.causal_uplift:
            return await self.causal_uplift.estimate(outcomes)
        return {}

    def get_kpis(self) -> Dict[str, Any]:
        """Get current KPIs from all systems"""
        kpis = {
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if self.kpi_board:
            kpis["board"] = self.kpi_board.get_kpis()

        if self.policy_lab:
            kpis["experiments"] = self.policy_lab.get_stats()

        if self.aigx_incentives:
            kpis["incentives"] = self.aigx_incentives.get_stats()

        if self.adversarial_guard:
            kpis["adversarial"] = self.adversarial_guard.get_stats()

        if self.policy_shapley:
            kpis["attribution"] = self.policy_shapley.get_stats()

        if self.r3_allocator:
            kpis["allocation"] = self.r3_allocator.get_stats()

        return kpis

    def get_stats(self) -> Dict[str, Any]:
        """Get playbook statistics"""
        modules_loaded = 0
        module_status = {}

        for name in ["ltv_oracle", "price_arm_v2", "attention_router",
                     "causal_uplift", "hier_bandits", "r3_allocator",
                     "aigx_incentives", "adversarial_guard",
                     "policy_shapley", "policy_lab", "kpi_board"]:
            loaded = getattr(self, name, None) is not None
            module_status[name] = loaded
            if loaded:
                modules_loaded += 1

        return {
            "modules_loaded": modules_loaded,
            "modules_total": 11,
            "module_status": module_status,
            "initialized": self._initialized
        }


# Singleton
_master_playbook: Optional[MasterPlaybook] = None


def get_master_playbook() -> MasterPlaybook:
    global _master_playbook
    if _master_playbook is None:
        _master_playbook = MasterPlaybook()
    return _master_playbook


async def evaluate_opportunity(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    return await get_master_playbook().evaluate_opportunity(opportunity)


async def record_outcome(result: Dict[str, Any]):
    await get_master_playbook().record_outcome(result)


def get_kpis() -> Dict[str, Any]:
    return get_master_playbook().get_kpis()
