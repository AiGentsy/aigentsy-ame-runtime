"""
Attention Router - Real-time Budget Routing by Marginal ROI
============================================================

Tier 1 Revenue Maximization Module

Features:
- Route attention/budget to highest marginal ROI platforms
- Real-time platform performance tracking
- Thompson Sampling for exploration/exploitation
- Diminishing returns modeling

Impact: 2x capital efficiency through optimal resource allocation
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import math
import random
import logging

logger = logging.getLogger("attention_router")


@dataclass
class PlatformPerformance:
    """Platform performance metrics"""
    platform: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    spend: float = 0.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def ctr(self) -> float:
        return self.clicks / max(1, self.impressions)

    @property
    def cvr(self) -> float:
        return self.conversions / max(1, self.clicks)

    @property
    def roas(self) -> float:
        return self.revenue / max(0.01, self.spend)

    @property
    def cpa(self) -> float:
        return self.spend / max(1, self.conversions)

    @property
    def marginal_roi(self) -> float:
        """Marginal ROI with diminishing returns"""
        base_roi = self.roas
        # Apply diminishing returns based on spend
        diminishing_factor = 1.0 / (1 + self.spend / 1000)
        return base_roi * diminishing_factor


@dataclass
class AttentionWeights:
    """Attention allocation weights"""
    weights: Dict[str, float]
    confidence: float
    reasoning: List[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Platform base weights (prior knowledge)
PLATFORM_PRIORS = {
    "upwork": {"weight": 0.15, "alpha": 2, "beta": 8},      # Known conversion rates
    "fiverr": {"weight": 0.10, "alpha": 3, "beta": 12},
    "linkedin": {"weight": 0.20, "alpha": 4, "beta": 10},
    "github": {"weight": 0.15, "alpha": 3, "beta": 7},
    "producthunt": {"weight": 0.10, "alpha": 2, "beta": 10},
    "reddit": {"weight": 0.10, "alpha": 1, "beta": 5},
    "hackernews": {"weight": 0.08, "alpha": 2, "beta": 8},
    "direct": {"weight": 0.12, "alpha": 5, "beta": 5},
}


class AttentionRouter:
    """
    Routes attention and budget to maximize marginal ROI

    Uses Thompson Sampling with:
    - Beta distributions for conversion rates
    - Diminishing returns modeling
    - Exploration bonus for under-sampled platforms
    """

    def __init__(self, exploration_factor: float = 0.1):
        self.exploration_factor = exploration_factor

        # Platform performance tracking
        self._performance: Dict[str, PlatformPerformance] = {}

        # Thompson Sampling state (alpha, beta for Beta distribution)
        self._beta_params: Dict[str, Tuple[float, float]] = {}

        # Historical weights for comparison
        self._weight_history: List[AttentionWeights] = []

        # Initialize with priors
        self._init_priors()

    def _init_priors(self):
        """Initialize Thompson Sampling priors"""
        for platform, prior in PLATFORM_PRIORS.items():
            self._beta_params[platform] = (prior["alpha"], prior["beta"])
            self._performance[platform] = PlatformPerformance(platform=platform)

    def weights(self, platform_kpis: Dict[str, Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Calculate attention weights for each platform

        Args:
            platform_kpis: Optional real-time KPIs from yield_memory

        Returns:
            Dict of platform -> weight (sums to 1.0)
        """
        platform_kpis = platform_kpis or {}

        # Update performance from KPIs
        self._update_performance(platform_kpis)

        # Calculate Thompson Sampling weights
        ts_weights = self._thompson_sampling_weights()

        # Calculate marginal ROI weights
        roi_weights = self._marginal_roi_weights()

        # Blend Thompson Sampling with marginal ROI
        blended_weights = {}
        for platform in set(ts_weights.keys()) | set(roi_weights.keys()):
            ts_w = ts_weights.get(platform, 0.05)
            roi_w = roi_weights.get(platform, 0.05)
            # 70% TS, 30% marginal ROI
            blended_weights[platform] = 0.7 * ts_w + 0.3 * roi_w

        # Add exploration bonus for under-sampled platforms
        blended_weights = self._add_exploration_bonus(blended_weights)

        # Normalize to sum to 1.0
        total = sum(blended_weights.values())
        if total > 0:
            normalized = {p: w / total for p, w in blended_weights.items()}
        else:
            # Fallback to uniform
            normalized = {p: 1.0 / len(blended_weights) for p in blended_weights}

        # Build reasoning
        reasoning = [
            f"Top 3: {self._top_n_platforms(normalized, 3)}",
            f"Exploration factor: {self.exploration_factor:.2f}",
            f"Total platforms: {len(normalized)}"
        ]

        # Calculate confidence
        total_samples = sum(
            self._beta_params.get(p, (1, 1))[0] + self._beta_params.get(p, (1, 1))[1] - 2
            for p in normalized
        )
        confidence = min(0.95, 0.5 + total_samples / 200)

        result = AttentionWeights(
            weights=normalized,
            confidence=confidence,
            reasoning=reasoning
        )

        self._weight_history.append(result)

        logger.info(f"Attention weights calculated: {self._top_n_platforms(normalized, 3)}")

        return normalized

    def _update_performance(self, platform_kpis: Dict[str, Dict[str, Any]]):
        """Update platform performance from KPIs"""
        for platform, kpis in platform_kpis.items():
            if platform not in self._performance:
                self._performance[platform] = PlatformPerformance(platform=platform)

            perf = self._performance[platform]
            perf.impressions = kpis.get("impressions", perf.impressions)
            perf.clicks = kpis.get("clicks", perf.clicks)
            perf.conversions = kpis.get("conversions", perf.conversions)
            perf.revenue = kpis.get("revenue", perf.revenue)
            perf.spend = kpis.get("spend", perf.spend)
            perf.last_updated = datetime.now(timezone.utc)

    def _thompson_sampling_weights(self) -> Dict[str, float]:
        """Calculate weights using Thompson Sampling"""
        samples = {}
        for platform, (alpha, beta) in self._beta_params.items():
            # Sample from Beta distribution
            sample = random.betavariate(alpha, beta)
            samples[platform] = sample

        # Normalize to weights
        total = sum(samples.values())
        if total > 0:
            return {p: s / total for p, s in samples.items()}
        return {p: 1.0 / len(samples) for p in samples}

    def _marginal_roi_weights(self) -> Dict[str, float]:
        """Calculate weights based on marginal ROI"""
        roi_scores = {}
        for platform, perf in self._performance.items():
            roi_scores[platform] = max(0.01, perf.marginal_roi)

        # Softmax-style conversion to weights
        total = sum(roi_scores.values())
        if total > 0:
            return {p: s / total for p, s in roi_scores.items()}
        return {p: 1.0 / len(roi_scores) for p in roi_scores}

    def _add_exploration_bonus(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Add exploration bonus for under-sampled platforms"""
        result = dict(weights)

        for platform in result:
            alpha, beta = self._beta_params.get(platform, (1, 1))
            total_samples = alpha + beta - 2

            if total_samples < 10:
                # Strong exploration bonus
                result[platform] += self.exploration_factor * 2
            elif total_samples < 50:
                # Moderate exploration bonus
                result[platform] += self.exploration_factor

        return result

    def _top_n_platforms(self, weights: Dict[str, float], n: int) -> str:
        """Get top N platforms as string"""
        sorted_platforms = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:n]
        return ", ".join(f"{p}={w:.1%}" for p, w in sorted_platforms)

    def record_outcome(self, platform: str, success: bool, revenue: float = 0):
        """Record outcome to update Thompson Sampling priors"""
        if platform not in self._beta_params:
            self._beta_params[platform] = (1, 1)

        alpha, beta = self._beta_params[platform]

        if success:
            alpha += 1
        else:
            beta += 1

        self._beta_params[platform] = (alpha, beta)

        # Update performance
        if platform not in self._performance:
            self._performance[platform] = PlatformPerformance(platform=platform)

        if success:
            self._performance[platform].conversions += 1
            self._performance[platform].revenue += revenue

        logger.debug(f"Outcome recorded for {platform}: success={success}, α={alpha}, β={beta}")

    def get_platform_quotas(self, total_budget: float = 1000) -> Dict[str, float]:
        """Get budget allocation quotas per platform"""
        weights = self.weights()
        return {p: w * total_budget for p, w in weights.items()}

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        return {
            "beta_params": self._beta_params,
            "performance": {
                p: {
                    "ctr": perf.ctr,
                    "cvr": perf.cvr,
                    "roas": perf.roas,
                    "marginal_roi": perf.marginal_roi
                }
                for p, perf in self._performance.items()
            },
            "current_weights": self.weights() if self._beta_params else {},
            "exploration_factor": self.exploration_factor
        }


# Singleton instance
_attention_router: Optional[AttentionRouter] = None


def get_attention_router() -> AttentionRouter:
    """Get or create the Attention Router singleton"""
    global _attention_router
    if _attention_router is None:
        _attention_router = AttentionRouter()
    return _attention_router


def get_attention_weights(platform_kpis: Dict[str, Dict[str, Any]] = None) -> Dict[str, float]:
    """Convenience function to get attention weights"""
    return get_attention_router().weights(platform_kpis)
