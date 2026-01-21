"""
EXPLORATION GOVERNOR
====================

Safe "try stuff" without burning margin.
Global budget (3-7% of volume) reserved for exploration:
- New PDLs from Spec Importer
- New connectors (headless fallbacks)
- New bundles (co-sell variants)

Auto-graduate to production when uplift > threshold with confidence.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import random


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class ExplorationGovernor:
    """
    Controls exploration budget and graduation.

    Ensures:
    - Exploration stays within budget (3-7% of volume)
    - New capabilities get tested safely
    - Winners graduate to production
    - Losers get killed quickly
    """

    def __init__(self):
        self.config = {
            "min_exploration_pct": 0.03,    # 3% min
            "max_exploration_pct": 0.07,    # 7% max
            "graduation_threshold": 0.08,   # 8% lift to graduate
            "graduation_confidence": 0.90,  # 90% confidence
            "min_samples": 50,              # Min samples before graduation
            "kill_threshold": -0.05,        # -5% to kill experiment
            "kill_samples": 20              # Min samples before kill decision
        }

        self._experiments: Dict[str, Dict[str, Any]] = {}
        self._exploration_budget_used = 0.0
        self._total_volume = 0
        self._exploration_volume = 0

    def should_explore(self, context: Dict[str, Any]) -> bool:
        """
        Decide if we should explore vs exploit.

        Args:
            context: Current context (can influence exploration rate)

        Returns:
            True if should explore
        """
        # Calculate current exploration rate
        if self._total_volume == 0:
            current_rate = 0
        else:
            current_rate = self._exploration_volume / self._total_volume

        # Dynamic exploration rate based on recent performance
        base_rate = (self.config["min_exploration_pct"] + self.config["max_exploration_pct"]) / 2

        # Increase exploration if we have few experiments
        active_experiments = len([e for e in self._experiments.values() if e.get("status") == "active"])
        if active_experiments < 3:
            base_rate = self.config["max_exploration_pct"]

        # Decrease if we're at budget limit
        if current_rate >= self.config["max_exploration_pct"]:
            return False

        # Random decision with adjusted rate
        return random.random() < base_rate

    def start_experiment(
        self,
        experiment_id: str,
        experiment_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Start a new experiment.

        Types:
        - pdl: New PDL from spec importer
        - connector: New connector path
        - bundle: New co-sell bundle
        - pricing: New pricing strategy
        """
        if experiment_id in self._experiments:
            return {"ok": False, "error": "experiment_exists"}

        self._experiments[experiment_id] = {
            "id": experiment_id,
            "type": experiment_type,
            "config": config,
            "status": "active",
            "started_at": _now_iso(),
            "samples": 0,
            "successes": 0,
            "total_reward": 0.0,
            "baseline_samples": 0,
            "baseline_reward": 0.0
        }

        return {
            "ok": True,
            "experiment_id": experiment_id,
            "status": "started"
        }

    def record_exploration(
        self,
        experiment_id: str,
        success: bool,
        reward: float,
        baseline_reward: float = None
    ) -> Dict[str, Any]:
        """
        Record exploration outcome.

        Args:
            experiment_id: Experiment identifier
            success: Whether outcome was successful
            reward: Reward received
            baseline_reward: Baseline reward for comparison
        """
        if experiment_id not in self._experiments:
            return {"ok": False, "error": "experiment_not_found"}

        exp = self._experiments[experiment_id]
        if exp["status"] != "active":
            return {"ok": False, "error": f"experiment_{exp['status']}"}

        # Update metrics
        exp["samples"] += 1
        if success:
            exp["successes"] += 1
        exp["total_reward"] += reward

        if baseline_reward is not None:
            exp["baseline_samples"] += 1
            exp["baseline_reward"] += baseline_reward

        # Update global counters
        self._total_volume += 1
        self._exploration_volume += 1

        # Check graduation/kill conditions
        result = self._check_graduation(experiment_id)

        return {
            "ok": True,
            "experiment_id": experiment_id,
            "samples": exp["samples"],
            "graduation_check": result
        }

    def _check_graduation(self, experiment_id: str) -> Dict[str, Any]:
        """Check if experiment should graduate or be killed"""
        exp = self._experiments[experiment_id]

        # Not enough samples yet
        if exp["samples"] < self.config["kill_samples"]:
            return {"status": "collecting", "samples": exp["samples"]}

        # Calculate lift
        if exp["baseline_samples"] == 0:
            # Use success rate as proxy
            lift = (exp["successes"] / exp["samples"]) - 0.5
        else:
            exp_avg = exp["total_reward"] / exp["samples"]
            baseline_avg = exp["baseline_reward"] / exp["baseline_samples"]
            lift = (exp_avg - baseline_avg) / baseline_avg if baseline_avg != 0 else 0

        # Check kill condition
        if exp["samples"] >= self.config["kill_samples"] and lift < self.config["kill_threshold"]:
            exp["status"] = "killed"
            exp["killed_at"] = _now_iso()
            exp["final_lift"] = lift
            return {"status": "killed", "lift": round(lift, 4)}

        # Check graduation condition
        if exp["samples"] >= self.config["min_samples"] and lift >= self.config["graduation_threshold"]:
            # Simple confidence check (would use proper stats in production)
            success_rate = exp["successes"] / exp["samples"]
            if success_rate >= self.config["graduation_confidence"]:
                exp["status"] = "graduated"
                exp["graduated_at"] = _now_iso()
                exp["final_lift"] = lift
                return {"status": "graduated", "lift": round(lift, 4)}

        return {
            "status": "active",
            "lift": round(lift, 4),
            "samples_to_graduation": self.config["min_samples"] - exp["samples"]
        }

    def graduate_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Manually graduate an experiment to production"""
        if experiment_id not in self._experiments:
            return {"ok": False, "error": "experiment_not_found"}

        exp = self._experiments[experiment_id]
        exp["status"] = "graduated"
        exp["graduated_at"] = _now_iso()

        return {
            "ok": True,
            "experiment_id": experiment_id,
            "config": exp["config"],
            "samples": exp["samples"],
            "success_rate": exp["successes"] / exp["samples"] if exp["samples"] > 0 else 0
        }

    def kill_experiment(self, experiment_id: str, reason: str = "manual") -> Dict[str, Any]:
        """Manually kill an experiment"""
        if experiment_id not in self._experiments:
            return {"ok": False, "error": "experiment_not_found"}

        exp = self._experiments[experiment_id]
        exp["status"] = "killed"
        exp["killed_at"] = _now_iso()
        exp["kill_reason"] = reason

        return {"ok": True, "experiment_id": experiment_id, "reason": reason}

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment details"""
        return self._experiments.get(experiment_id)

    def list_experiments(self, status: str = None) -> List[Dict[str, Any]]:
        """List experiments, optionally filtered by status"""
        experiments = list(self._experiments.values())
        if status:
            experiments = [e for e in experiments if e.get("status") == status]
        return experiments

    def get_stats(self) -> Dict[str, Any]:
        """Get exploration statistics"""
        active = [e for e in self._experiments.values() if e["status"] == "active"]
        graduated = [e for e in self._experiments.values() if e["status"] == "graduated"]
        killed = [e for e in self._experiments.values() if e["status"] == "killed"]

        exploration_rate = self._exploration_volume / self._total_volume if self._total_volume > 0 else 0

        return {
            "total_experiments": len(self._experiments),
            "active": len(active),
            "graduated": len(graduated),
            "killed": len(killed),
            "exploration_rate": round(exploration_rate, 4),
            "budget_min": self.config["min_exploration_pct"],
            "budget_max": self.config["max_exploration_pct"]
        }


# Module-level singleton
_exploration_governor = ExplorationGovernor()


def should_explore(context: Dict[str, Any] = None) -> bool:
    """Check if should explore"""
    return _exploration_governor.should_explore(context or {})


def start_experiment(experiment_id: str, experiment_type: str, config: Dict) -> Dict[str, Any]:
    """Start new experiment"""
    return _exploration_governor.start_experiment(experiment_id, experiment_type, config)


def record_exploration(experiment_id: str, success: bool, reward: float, **kwargs) -> Dict[str, Any]:
    """Record exploration outcome"""
    return _exploration_governor.record_exploration(experiment_id, success, reward, **kwargs)


def get_exploration_stats() -> Dict[str, Any]:
    """Get exploration statistics"""
    return _exploration_governor.get_stats()
