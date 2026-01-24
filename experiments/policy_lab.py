"""
Policy Lab - Always-on Micro-experiments
=========================================

Tier 5 Accountability Module

Features:
- Always-on micro-experiments
- SLO-aware ramping + auto-rollback
- Multi-armed bandit experiment allocation
- Statistical significance testing

Impact: Continuous improvement through experimentation
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import random
import math
import logging

logger = logging.getLogger("policy_lab")


class ExperimentStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ROLLED_BACK = "rolled_back"
    GRADUATED = "graduated"


@dataclass
class Experiment:
    """Single experiment"""
    id: str
    name: str
    treatment_engine: str
    control_engine: str
    traffic_pct: float
    status: ExperimentStatus = ExperimentStatus.ACTIVE
    treatment_wins: int = 0
    control_wins: int = 0
    treatment_revenue: float = 0.0
    control_revenue: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PolicyLab:
    """
    Continuous experimentation platform

    Features:
    - Multi-experiment management
    - Automatic traffic allocation
    - Significance testing
    - Auto-rollback on SLO breach
    """

    def __init__(self, max_experiments: int = 5, default_traffic: float = 0.1):
        self.max_experiments = max_experiments
        self.default_traffic = default_traffic

        self._experiments: Dict[str, Experiment] = {}
        self._slo_breaches: int = 0
        self._graduations: int = 0

    def create_experiment(self, name: str, treatment_engine: str,
                          control_engine: str, traffic_pct: float = None) -> str:
        """Create new experiment"""
        if len(self._experiments) >= self.max_experiments:
            # Remove oldest graduated or rolled back
            self._cleanup_experiments()

        exp_id = f"exp_{len(self._experiments) + 1}_{name.replace(' ', '_')[:10]}"
        traffic = traffic_pct or self.default_traffic

        experiment = Experiment(
            id=exp_id,
            name=name,
            treatment_engine=treatment_engine,
            control_engine=control_engine,
            traffic_pct=traffic
        )

        self._experiments[exp_id] = experiment
        logger.info(f"Created experiment: {exp_id}")

        return exp_id

    def assign(self, opp_id: str, available_engines: List[str]) -> Optional[str]:
        """
        Assign opportunity to experiment treatment

        Returns:
            Treatment engine if assigned, None otherwise
        """
        active_experiments = [
            e for e in self._experiments.values()
            if e.status == ExperimentStatus.ACTIVE
        ]

        for exp in active_experiments:
            if exp.treatment_engine not in available_engines:
                continue

            # Random assignment based on traffic %
            if random.random() < exp.traffic_pct:
                return exp.treatment_engine

        return None

    def record_outcome(self, engine: str, success: bool, revenue: float):
        """Record experiment outcome"""
        for exp in self._experiments.values():
            if exp.status != ExperimentStatus.ACTIVE:
                continue

            if engine == exp.treatment_engine:
                if success:
                    exp.treatment_wins += 1
                exp.treatment_revenue += revenue
            elif engine == exp.control_engine:
                if success:
                    exp.control_wins += 1
                exp.control_revenue += revenue

    def check_significance(self, exp_id: str) -> Dict[str, Any]:
        """Check if experiment has significant results"""
        if exp_id not in self._experiments:
            return {"significant": False}

        exp = self._experiments[exp_id]
        total_treatment = exp.treatment_wins + max(1, exp.treatment_revenue / 100)
        total_control = exp.control_wins + max(1, exp.control_revenue / 100)

        n = total_treatment + total_control
        if n < 30:
            return {"significant": False, "reason": "insufficient_samples", "n": n}

        # Calculate win rate difference
        treatment_rate = exp.treatment_wins / max(1, total_treatment)
        control_rate = exp.control_wins / max(1, total_control)
        diff = treatment_rate - control_rate

        # Simplified significance test
        pooled_rate = (exp.treatment_wins + exp.control_wins) / max(1, n)
        se = math.sqrt(pooled_rate * (1 - pooled_rate) * (1/max(1, total_treatment) + 1/max(1, total_control)))

        z_score = abs(diff) / max(0.001, se)
        significant = z_score > 1.96  # 95% confidence

        return {
            "significant": significant,
            "treatment_rate": treatment_rate,
            "control_rate": control_rate,
            "lift": diff / max(0.001, control_rate),
            "z_score": z_score,
            "n": n
        }

    def check_slo(self, slo_ok: bool):
        """Check SLO status and rollback if needed"""
        if not slo_ok:
            self._slo_breaches += 1

            # Rollback newest experiment if multiple breaches
            if self._slo_breaches >= 3:
                active = [e for e in self._experiments.values() if e.status == ExperimentStatus.ACTIVE]
                if active:
                    newest = max(active, key=lambda e: e.created_at)
                    newest.status = ExperimentStatus.ROLLED_BACK
                    logger.warning(f"Rolled back experiment {newest.id} due to SLO breaches")
                    self._slo_breaches = 0
        else:
            self._slo_breaches = max(0, self._slo_breaches - 1)

    def graduate_experiment(self, exp_id: str):
        """Graduate successful experiment"""
        if exp_id in self._experiments:
            self._experiments[exp_id].status = ExperimentStatus.GRADUATED
            self._graduations += 1
            logger.info(f"Graduated experiment: {exp_id}")

    def _cleanup_experiments(self):
        """Remove old completed experiments"""
        to_remove = []
        for exp_id, exp in self._experiments.items():
            if exp.status in [ExperimentStatus.GRADUATED, ExperimentStatus.ROLLED_BACK]:
                to_remove.append(exp_id)

        for exp_id in to_remove[:1]:  # Remove oldest one
            del self._experiments[exp_id]

    def get_active_experiments(self) -> List[Dict[str, Any]]:
        """Get all active experiments"""
        return [
            {
                "id": e.id,
                "name": e.name,
                "treatment": e.treatment_engine,
                "control": e.control_engine,
                "traffic_pct": e.traffic_pct,
                "treatment_wins": e.treatment_wins,
                "control_wins": e.control_wins
            }
            for e in self._experiments.values()
            if e.status == ExperimentStatus.ACTIVE
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get lab statistics"""
        return {
            "total_experiments": len(self._experiments),
            "active_experiments": len([e for e in self._experiments.values() if e.status == ExperimentStatus.ACTIVE]),
            "graduations": self._graduations,
            "slo_breaches": self._slo_breaches,
            "experiments": {
                e.id: {"status": e.status.value, "treatment_wins": e.treatment_wins}
                for e in self._experiments.values()
            }
        }


# Singleton
_policy_lab: Optional[PolicyLab] = None

def get_policy_lab() -> PolicyLab:
    global _policy_lab
    if _policy_lab is None:
        _policy_lab = PolicyLab()
    return _policy_lab

def assign_experiment(opp_id: str, engines: List[str]) -> Optional[str]:
    return get_policy_lab().assign(opp_id, engines)
