"""
Brain Policy Trainer - Autonomous Learning System
==================================================

Continuous policy improvement through:
- Causal uplift estimation
- Policy Shapley attribution
- Hierarchical bandit learning
- Experiment graduation
- Model updates

Impact: Self-improving autonomous agent
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import logging
import asyncio

logger = logging.getLogger("brain_policy_trainer")


@dataclass
class TrainingResult:
    """Result of a training cycle"""
    timestamp: datetime
    outcomes_processed: int
    uplift_scores: Dict[str, float]
    shapley_values: Dict[str, float]
    experiments_graduated: List[str]
    policy_updates: List[str]
    metrics: Dict[str, float]


class BrainPolicyTrainer:
    """
    Autonomous policy learning and improvement

    Training cycle:
    1. Collect outcomes from execution
    2. Estimate causal uplift for each engine
    3. Calculate Shapley attribution
    4. Update bandit priors
    5. Graduate successful experiments
    6. Publish updated policy
    """

    def __init__(self):
        self._init_modules()
        self._training_history: List[TrainingResult] = []
        self._outcomes_buffer: List[Dict] = []
        self._last_training: Optional[datetime] = None
        self._training_interval_minutes: int = 60

    def _init_modules(self):
        """Initialize learning modules"""
        # Causal Uplift Trainer
        try:
            from learning.causal_uplift_trainer import get_causal_trainer
            self.causal_uplift = get_causal_trainer()
            logger.info("✓ Causal Uplift Trainer loaded")
        except ImportError as e:
            logger.warning(f"Causal Uplift not available: {e}")
            self.causal_uplift = None

        # Policy Shapley
        try:
            from econometrics.policy_shapley import get_policy_shapley
            self.policy_shapley = get_policy_shapley()
            logger.info("✓ Policy Shapley loaded")
        except ImportError as e:
            logger.warning(f"Policy Shapley not available: {e}")
            self.policy_shapley = None

        # Hierarchical Bandits
        try:
            from learning.hier_bandits import get_hier_bandits
            self.hier_bandits = get_hier_bandits()
            logger.info("✓ Hierarchical Bandits loaded")
        except ImportError as e:
            logger.warning(f"Hierarchical Bandits not available: {e}")
            self.hier_bandits = None

        # Policy Lab (for experiments)
        try:
            from experiments.policy_lab import get_policy_lab
            self.policy_lab = get_policy_lab()
            logger.info("✓ Policy Lab loaded")
        except ImportError as e:
            logger.warning(f"Policy Lab not available: {e}")
            self.policy_lab = None

        # KPI Board (for metrics)
        try:
            from reporting.kpi_board import get_kpi_board
            self.kpi_board = get_kpi_board()
            logger.info("✓ KPI Board loaded")
        except ImportError as e:
            logger.warning(f"KPI Board not available: {e}")
            self.kpi_board = None

        # R3 Allocator (for rebalancing)
        try:
            from allocation.r3_allocator import get_r3_allocator
            self.r3_allocator = get_r3_allocator()
            logger.info("✓ R3 Allocator loaded")
        except ImportError as e:
            logger.warning(f"R3 Allocator not available: {e}")
            self.r3_allocator = None

    def buffer_outcome(self, outcome: Dict[str, Any]):
        """Buffer outcome for next training cycle"""
        self._outcomes_buffer.append({
            **outcome,
            "buffered_at": datetime.now(timezone.utc).isoformat()
        })

    async def train_and_publish_policy(self, outcomes: List[Dict[str, Any]] = None) -> TrainingResult:
        """
        Full training cycle with policy publication

        Args:
            outcomes: Optional list of outcomes (uses buffer if not provided)

        Returns:
            TrainingResult with all updates
        """
        # Use provided outcomes or buffer
        training_outcomes = outcomes or self._outcomes_buffer.copy()

        if not training_outcomes:
            logger.info("No outcomes to train on")
            return TrainingResult(
                timestamp=datetime.now(timezone.utc),
                outcomes_processed=0,
                uplift_scores={},
                shapley_values={},
                experiments_graduated=[],
                policy_updates=[],
                metrics={}
            )

        logger.info(f"Training on {len(training_outcomes)} outcomes")

        policy_updates = []
        experiments_graduated = []

        # 1. Causal uplift estimation
        uplift_scores = {}
        if self.causal_uplift:
            try:
                uplift_scores = await self.causal_uplift.estimate(training_outcomes)
                logger.info(f"Uplift scores: {uplift_scores}")
                policy_updates.append("uplift_scores_updated")
            except Exception as e:
                logger.error(f"Uplift estimation failed: {e}")

        # 2. Policy Shapley values
        shapley_values = {}
        if self.policy_shapley:
            try:
                # Format outcomes for Shapley
                shapley_outcomes = [
                    {
                        "engines_used": o.get("engines_used", [o.get("engine", "unknown")]),
                        "revenue": o.get("revenue", 0),
                        "baseline": o.get("baseline", 0)
                    }
                    for o in training_outcomes
                ]
                shapley_values = await self.policy_shapley.value(shapley_outcomes)
                logger.info(f"Shapley values: {shapley_values}")
                policy_updates.append("shapley_attribution_updated")
            except Exception as e:
                logger.error(f"Shapley calculation failed: {e}")

        # 3. Update hierarchical bandits
        if self.hier_bandits:
            try:
                for outcome in training_outcomes:
                    context = {
                        "segment": outcome.get("segment", "smb"),
                        "platform": outcome.get("platform", "upwork"),
                        "sku": outcome.get("sku", "default")
                    }
                    self.hier_bandits.update(
                        context=context,
                        arm=outcome.get("engine", "default"),
                        reward=outcome.get("revenue", 0)
                    )
                policy_updates.append("bandits_updated")
            except Exception as e:
                logger.error(f"Bandit update failed: {e}")

        # 4. Check experiment significance and graduate
        if self.policy_lab:
            try:
                active_experiments = self.policy_lab.get_active_experiments()
                for exp in active_experiments:
                    sig_result = self.policy_lab.check_significance(exp["id"])
                    if sig_result.get("significant", False):
                        lift = sig_result.get("lift", 0)
                        if lift > 0.05:  # 5% lift threshold for graduation
                            self.policy_lab.graduate_experiment(exp["id"])
                            experiments_graduated.append(exp["id"])
                            logger.info(f"Graduated experiment {exp['id']} with {lift:.1%} lift")

                if experiments_graduated:
                    policy_updates.append("experiments_graduated")
            except Exception as e:
                logger.error(f"Experiment graduation failed: {e}")

        # 5. Collect metrics
        metrics = {}
        if self.kpi_board:
            try:
                kpis = self.kpi_board.get_kpis()
                metrics = {
                    "cash_per_token": kpis.get("cash_per_token", 0),
                    "win_rate": kpis.get("win_rate", 0),
                    "total_revenue": kpis.get("total_revenue", 0)
                }
            except Exception as e:
                logger.error(f"Metrics collection failed: {e}")

        # 6. Update engine weights based on Shapley + uplift
        if shapley_values and uplift_scores:
            try:
                combined_scores = self._combine_scores(shapley_values, uplift_scores)
                policy_updates.append("engine_weights_updated")
                logger.info(f"Combined engine scores: {combined_scores}")
            except Exception as e:
                logger.error(f"Score combination failed: {e}")

        # Clear buffer
        self._outcomes_buffer.clear()
        self._last_training = datetime.now(timezone.utc)

        result = TrainingResult(
            timestamp=datetime.now(timezone.utc),
            outcomes_processed=len(training_outcomes),
            uplift_scores=uplift_scores,
            shapley_values=shapley_values,
            experiments_graduated=experiments_graduated,
            policy_updates=policy_updates,
            metrics=metrics
        )

        self._training_history.append(result)
        logger.info(f"Training complete: {len(policy_updates)} updates")

        return result

    def _combine_scores(self, shapley: Dict[str, float],
                        uplift: Dict[str, float]) -> Dict[str, float]:
        """
        Combine Shapley attribution with causal uplift

        Uses weighted average:
        - 60% Shapley (historical contribution)
        - 40% Uplift (causal effect)
        """
        all_engines = set(shapley.keys()) | set(uplift.keys())
        combined = {}

        for engine in all_engines:
            shapley_score = shapley.get(engine, 0)
            uplift_score = uplift.get(engine, 0)
            combined[engine] = 0.6 * shapley_score + 0.4 * uplift_score

        # Normalize to sum to 1
        total = sum(abs(v) for v in combined.values())
        if total > 0:
            combined = {k: v / total for k, v in combined.items()}

        return combined

    async def should_train(self) -> bool:
        """Check if training should run"""
        if not self._last_training:
            return len(self._outcomes_buffer) >= 10

        elapsed = datetime.now(timezone.utc) - self._last_training
        if elapsed > timedelta(minutes=self._training_interval_minutes):
            return len(self._outcomes_buffer) >= 5

        return len(self._outcomes_buffer) >= 50

    async def maybe_train(self) -> Optional[TrainingResult]:
        """Train if conditions are met"""
        if await self.should_train():
            return await self.train_and_publish_policy()
        return None

    def get_engine_rankings(self) -> List[Tuple[str, float]]:
        """Get current engine rankings based on training"""
        if not self._training_history:
            return []

        latest = self._training_history[-1]
        combined = self._combine_scores(
            latest.shapley_values,
            latest.uplift_scores
        )

        return sorted(combined.items(), key=lambda x: x[1], reverse=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get trainer statistics"""
        stats = {
            "training_cycles": len(self._training_history),
            "buffered_outcomes": len(self._outcomes_buffer),
            "last_training": self._last_training.isoformat() if self._last_training else None,
            "training_interval_minutes": self._training_interval_minutes,
            "modules": {
                "causal_uplift": self.causal_uplift is not None,
                "policy_shapley": self.policy_shapley is not None,
                "hier_bandits": self.hier_bandits is not None,
                "policy_lab": self.policy_lab is not None,
                "kpi_board": self.kpi_board is not None,
                "r3_allocator": self.r3_allocator is not None
            }
        }

        if self._training_history:
            latest = self._training_history[-1]
            stats["latest_training"] = {
                "timestamp": latest.timestamp.isoformat(),
                "outcomes_processed": latest.outcomes_processed,
                "policy_updates": latest.policy_updates,
                "experiments_graduated": latest.experiments_graduated
            }

        return stats


# Singleton
_brain_trainer: Optional[BrainPolicyTrainer] = None


def get_brain_trainer() -> BrainPolicyTrainer:
    global _brain_trainer
    if _brain_trainer is None:
        _brain_trainer = BrainPolicyTrainer()
    return _brain_trainer


async def train_policy(outcomes: List[Dict] = None) -> TrainingResult:
    return await get_brain_trainer().train_and_publish_policy(outcomes)


def buffer_outcome(outcome: Dict[str, Any]):
    get_brain_trainer().buffer_outcome(outcome)


async def maybe_train() -> Optional[TrainingResult]:
    return await get_brain_trainer().maybe_train()
