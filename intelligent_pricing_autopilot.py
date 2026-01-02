"""
INTELLIGENT PRICING AUTOPILOT
==============================

Real-time market learning that optimizes pricing based on:
1. Win/loss history - what prices actually won jobs
2. Competitor pricing - what others are charging NOW
3. Demand surge detection - when to charge more
4. Price elasticity - how price changes affect conversion

INTEGRATES WITH:
- pricing_oracle.py (existing dynamic pricing)
- yield_memory.py (pattern storage)
- execution_scorer.py (win probability)
- outcome_oracle_max.py (conversion tracking)
"""

import asyncio
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
from collections import defaultdict
import statistics

# Import existing systems
try:
    from pricing_oracle import calculate_dynamic_price, suggest_optimal_pricing
    PRICING_ORACLE_AVAILABLE = True
except ImportError:
    PRICING_ORACLE_AVAILABLE = False

try:
    from yield_memory import store_pattern, find_similar_patterns
    YIELD_MEMORY_AVAILABLE = True
except ImportError:
    YIELD_MEMORY_AVAILABLE = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


# ============================================================
# CONFIGURATION
# ============================================================

class ServiceCategory(str, Enum):
    CONTENT_WRITING = "content_writing"
    SOFTWARE_DEV = "software_dev"
    DESIGN = "design"
    MARKETING = "marketing"
    CONSULTING = "consulting"
    DATA_ANALYSIS = "data_analysis"
    VIDEO_PRODUCTION = "video_production"
    VIRTUAL_ASSISTANT = "virtual_assistant"
    OTHER = "other"


class BidOutcome(str, Enum):
    WON = "won"
    LOST = "lost"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"


class DemandLevel(str, Enum):
    SURGE = "surge"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


# Base market rates by category (hourly)
BASE_MARKET_RATES = {
    ServiceCategory.CONTENT_WRITING: {"low": 25, "mid": 50, "high": 100},
    ServiceCategory.SOFTWARE_DEV: {"low": 50, "mid": 100, "high": 200},
    ServiceCategory.DESIGN: {"low": 35, "mid": 75, "high": 150},
    ServiceCategory.MARKETING: {"low": 40, "mid": 80, "high": 150},
    ServiceCategory.CONSULTING: {"low": 75, "mid": 150, "high": 300},
    ServiceCategory.DATA_ANALYSIS: {"low": 50, "mid": 100, "high": 200},
    ServiceCategory.VIDEO_PRODUCTION: {"low": 50, "mid": 100, "high": 250},
    ServiceCategory.VIRTUAL_ASSISTANT: {"low": 15, "mid": 30, "high": 60},
    ServiceCategory.OTHER: {"low": 30, "mid": 60, "high": 120},
}

# Default price elasticity by category
DEFAULT_ELASTICITY = {
    ServiceCategory.CONTENT_WRITING: 0.08,
    ServiceCategory.SOFTWARE_DEV: 0.05,
    ServiceCategory.DESIGN: 0.07,
    ServiceCategory.MARKETING: 0.06,
    ServiceCategory.CONSULTING: 0.04,
    ServiceCategory.DATA_ANALYSIS: 0.05,
    ServiceCategory.VIDEO_PRODUCTION: 0.06,
    ServiceCategory.VIRTUAL_ASSISTANT: 0.10,
    ServiceCategory.OTHER: 0.07,
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class BidRecord:
    bid_id: str
    opportunity_id: str
    platform: str
    category: ServiceCategory
    bid_price: float
    estimated_hours: float
    effective_hourly: float
    outcome: BidOutcome
    winning_price: Optional[float] = None
    competitor_count: int = 0
    submitted_at: str = field(default_factory=_now)
    resolved_at: Optional[str] = None


@dataclass
class CompetitorPricing:
    observation_id: str
    platform: str
    category: ServiceCategory
    competitor_id: str
    price: float
    estimated_hours: float
    effective_hourly: float
    service_description: str
    reputation_score: Optional[float] = None
    observed_at: str = field(default_factory=_now)


@dataclass
class DemandSignal:
    signal_id: str
    category: ServiceCategory
    platform: str
    demand_level: DemandLevel
    opportunities_count: int
    avg_budget: float
    time_window_hours: int
    detected_at: str = field(default_factory=_now)


@dataclass
class PriceRecommendation:
    opportunity_id: str
    category: ServiceCategory
    recommended_price: float
    price_range: Tuple[float, float]
    confidence: float
    win_probability: float
    factors: Dict[str, Any]
    generated_at: str = field(default_factory=_now)
    
    def to_dict(self) -> Dict:
        return {
            "opportunity_id": self.opportunity_id,
            "category": self.category.value,
            "recommended_price": self.recommended_price,
            "price_range": {"min": self.price_range[0], "max": self.price_range[1]},
            "confidence": self.confidence,
            "win_probability": self.win_probability,
            "factors": self.factors,
            "generated_at": self.generated_at,
        }


# ============================================================
# PRICING AUTOPILOT ENGINE
# ============================================================

class IntelligentPricingAutopilot:
    """Self-learning pricing engine."""
    
    def __init__(self):
        self.bid_history: List[BidRecord] = []
        self.competitor_observations: List[CompetitorPricing] = []
        self.demand_signals: List[DemandSignal] = []
        
        self.learned_elasticity: Dict[ServiceCategory, float] = dict(DEFAULT_ELASTICITY)
        self.learned_win_rates: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.category_demand: Dict[ServiceCategory, DemandLevel] = {
            cat: DemandLevel.NORMAL for cat in ServiceCategory
        }
        
        self._price_cache: Dict[str, PriceRecommendation] = {}
        self._cache_ttl_minutes = 15
        
        print("\n" + "="*60)
        print("💰 INTELLIGENT PRICING AUTOPILOT INITIALIZED")
        print("="*60)
    
    
    def record_bid(
        self,
        opportunity_id: str,
        platform: str,
        category: ServiceCategory,
        bid_price: float,
        estimated_hours: float,
        competitor_count: int = 0
    ) -> BidRecord:
        """Record a bid submission."""
        effective_hourly = bid_price / estimated_hours if estimated_hours > 0 else bid_price
        
        record = BidRecord(
            bid_id=_generate_id("bid"),
            opportunity_id=opportunity_id,
            platform=platform,
            category=category,
            bid_price=bid_price,
            estimated_hours=estimated_hours,
            effective_hourly=effective_hourly,
            outcome=BidOutcome.PENDING,
            competitor_count=competitor_count,
        )
        
        self.bid_history.append(record)
        return record
    
    
    def record_bid_outcome(
        self,
        bid_id: str,
        outcome: BidOutcome,
        winning_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Record bid outcome and learn from it."""
        bid = None
        for b in self.bid_history:
            if b.bid_id == bid_id:
                bid = b
                break
        
        if not bid:
            return {"ok": False, "error": "bid_not_found"}
        
        bid.outcome = outcome
        bid.winning_price = winning_price
        bid.resolved_at = _now()
        
        self._learn_from_outcome(bid)
        
        return {"ok": True, "bid_id": bid_id, "outcome": outcome.value}
    
    
    def _learn_from_outcome(self, bid: BidRecord):
        """Learn from bid outcome."""
        bucket = str(int(bid.effective_hourly // 10) * 10)
        category = bid.category.value
        
        if bucket not in self.learned_win_rates[category]:
            self.learned_win_rates[category][bucket] = {"wins": 0, "total": 0}
        
        self.learned_win_rates[category][bucket]["total"] += 1
        if bid.outcome == BidOutcome.WON:
            self.learned_win_rates[category][bucket]["wins"] += 1
        
        # Update elasticity
        if bid.outcome == BidOutcome.LOST and bid.winning_price:
            price_diff_pct = (bid.bid_price - bid.winning_price) / bid.winning_price
            if price_diff_pct > 0.1:
                current = self.learned_elasticity[bid.category]
                self.learned_elasticity[bid.category] = min(0.15, current + 0.005)
        elif bid.outcome == BidOutcome.WON:
            current = self.learned_elasticity[bid.category]
            self.learned_elasticity[bid.category] = max(0.02, current - 0.002)
    
    
    def get_win_rate_for_price(self, category: ServiceCategory, effective_hourly: float) -> float:
        """Get historical win rate for a price point."""
        bucket = str(int(effective_hourly // 10) * 10)
        
        if bucket in self.learned_win_rates[category.value]:
            stats = self.learned_win_rates[category.value][bucket]
            if stats["total"] > 0:
                return stats["wins"] / stats["total"]
        return 0.3
    
    
    def record_competitor_pricing(
        self,
        platform: str,
        category: ServiceCategory,
        price: float,
        estimated_hours: float,
        service_description: str,
        reputation_score: Optional[float] = None
    ) -> CompetitorPricing:
        """Record competitor pricing observation."""
        effective_hourly = price / estimated_hours if estimated_hours > 0 else price
        competitor_hash = hashlib.md5(f"{platform}:{service_description[:20]}".encode()).hexdigest()[:8]
        
        observation = CompetitorPricing(
            observation_id=_generate_id("comp"),
            platform=platform,
            category=category,
            competitor_id=f"comp_{competitor_hash}",
            price=price,
            estimated_hours=estimated_hours,
            effective_hourly=effective_hourly,
            service_description=service_description,
            reputation_score=reputation_score,
        )
        
        self.competitor_observations.append(observation)
        return observation
    
    
    def get_competitor_pricing_stats(
        self,
        category: ServiceCategory,
        platform: Optional[str] = None,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """Get competitor pricing statistics."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        
        observations = [
            o for o in self.competitor_observations
            if o.category == category
            and datetime.fromisoformat(o.observed_at.replace("Z", "+00:00")) > cutoff
            and (platform is None or o.platform == platform)
        ]
        
        if not observations:
            rates = BASE_MARKET_RATES[category]
            return {
                "category": category.value,
                "observations": 0,
                "avg_hourly": rates["mid"],
                "min_hourly": rates["low"],
                "max_hourly": rates["high"],
                "median_hourly": rates["mid"],
                "source": "defaults",
            }
        
        hourlies = [o.effective_hourly for o in observations]
        
        return {
            "category": category.value,
            "observations": len(observations),
            "avg_hourly": round(statistics.mean(hourlies), 2),
            "min_hourly": round(min(hourlies), 2),
            "max_hourly": round(max(hourlies), 2),
            "median_hourly": round(statistics.median(hourlies), 2),
            "source": "observed",
        }
    
    
    def record_demand_signal(
        self,
        category: ServiceCategory,
        platform: str,
        opportunities_count: int,
        avg_budget: float,
        time_window_hours: int = 24
    ) -> DemandSignal:
        """Record demand signal and update demand level."""
        historical = self._get_historical_demand(category, platform)
        
        if opportunities_count > historical * 2:
            level = DemandLevel.SURGE
        elif opportunities_count > historical * 1.5:
            level = DemandLevel.HIGH
        elif opportunities_count < historical * 0.5:
            level = DemandLevel.LOW
        else:
            level = DemandLevel.NORMAL
        
        signal = DemandSignal(
            signal_id=_generate_id("demand"),
            category=category,
            platform=platform,
            demand_level=level,
            opportunities_count=opportunities_count,
            avg_budget=avg_budget,
            time_window_hours=time_window_hours,
        )
        
        self.demand_signals.append(signal)
        self.category_demand[category] = level
        
        return signal
    
    
    def _get_historical_demand(self, category: ServiceCategory, platform: str) -> float:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        signals = [
            s for s in self.demand_signals
            if s.category == category and s.platform == platform
            and datetime.fromisoformat(s.detected_at.replace("Z", "+00:00")) > cutoff
        ]
        if signals:
            return statistics.mean([s.opportunities_count for s in signals])
        return 10
    
    
    def get_current_demand(self, category: ServiceCategory) -> DemandLevel:
        return self.category_demand.get(category, DemandLevel.NORMAL)
    
    
    def get_demand_multiplier(self, category: ServiceCategory) -> float:
        demand = self.get_current_demand(category)
        multipliers = {
            DemandLevel.SURGE: 1.30,
            DemandLevel.HIGH: 1.15,
            DemandLevel.NORMAL: 1.00,
            DemandLevel.LOW: 0.90,
        }
        return multipliers[demand]
    
    
    async def recommend_price(
        self,
        opportunity_id: str,
        category: ServiceCategory,
        estimated_hours: float,
        platform: str,
        buyer_budget: Optional[float] = None,
        competitor_count: int = 0,
        agent_reputation: float = 0.5,
        urgency: str = "normal"
    ) -> PriceRecommendation:
        """Generate optimal price recommendation."""
        
        market_rates = BASE_MARKET_RATES[category]
        competitor_stats = self.get_competitor_pricing_stats(category, platform)
        base_hourly = competitor_stats.get("median_hourly", market_rates["mid"])
        
        factors = {}
        
        # 1. Demand adjustment
        demand_mult = self.get_demand_multiplier(category)
        factors["demand_multiplier"] = demand_mult
        
        # 2. Reputation adjustment
        rep_mult = 0.85 + (agent_reputation * 0.30)
        factors["reputation_multiplier"] = round(rep_mult, 2)
        
        # 3. Competition adjustment
        if competitor_count > 10:
            comp_mult = 0.90
        elif competitor_count > 5:
            comp_mult = 0.95
        elif competitor_count < 3:
            comp_mult = 1.05
        else:
            comp_mult = 1.0
        factors["competition_multiplier"] = comp_mult
        
        # 4. Urgency adjustment
        urgency_mults = {"critical": 1.25, "high": 1.15, "normal": 1.0, "low": 0.95}
        urgency_mult = urgency_mults.get(urgency, 1.0)
        factors["urgency_multiplier"] = urgency_mult
        
        # 5. Budget anchoring
        if buyer_budget and buyer_budget > 0:
            budget_hourly = buyer_budget / estimated_hours if estimated_hours > 0 else buyer_budget
            if budget_hourly > base_hourly * 1.5:
                budget_mult = 1.20
            elif budget_hourly > base_hourly:
                budget_mult = 1.0 + ((budget_hourly - base_hourly) / base_hourly) * 0.3
            else:
                budget_mult = max(0.8, budget_hourly / base_hourly)
            factors["budget_anchoring"] = round(budget_mult, 2)
        else:
            budget_mult = 1.0
        
        # 6. Learned win rate adjustment
        best_price_bucket = self._find_optimal_price_bucket(category)
        if best_price_bucket:
            learned_adjustment = best_price_bucket / base_hourly
            learned_adjustment = max(0.8, min(1.2, learned_adjustment))
            factors["learned_adjustment"] = round(learned_adjustment, 2)
        else:
            learned_adjustment = 1.0
        
        # Calculate final hourly rate
        final_hourly = (
            base_hourly * demand_mult * rep_mult * comp_mult * 
            urgency_mult * budget_mult * learned_adjustment
        )
        
        final_hourly = max(market_rates["low"], min(market_rates["high"] * 1.5, final_hourly))
        recommended_price = round(final_hourly * estimated_hours, 2)
        price_range = (round(recommended_price * 0.85, 2), round(recommended_price * 1.15, 2))
        
        win_prob = self._estimate_win_probability(category, final_hourly, competitor_count, agent_reputation)
        confidence = self._calculate_confidence(category, platform)
        
        return PriceRecommendation(
            opportunity_id=opportunity_id,
            category=category,
            recommended_price=recommended_price,
            price_range=price_range,
            confidence=confidence,
            win_probability=win_prob,
            factors=factors,
        )
    
    
    def _find_optimal_price_bucket(self, category: ServiceCategory) -> Optional[float]:
        cat_rates = self.learned_win_rates.get(category.value, {})
        if not cat_rates:
            return None
        
        best_bucket = None
        best_score = 0
        
        for bucket, stats in cat_rates.items():
            if stats["total"] < 3:
                continue
            win_rate = stats["wins"] / stats["total"]
            bucket_price = float(bucket)
            score = win_rate * bucket_price
            if score > best_score:
                best_score = score
                best_bucket = bucket_price + 5
        
        return best_bucket
    
    
    def _estimate_win_probability(
        self,
        category: ServiceCategory,
        effective_hourly: float,
        competitor_count: int,
        reputation: float
    ) -> float:
        base_prob = self.get_win_rate_for_price(category, effective_hourly)
        
        if competitor_count > 10:
            comp_adj = 0.7
        elif competitor_count > 5:
            comp_adj = 0.85
        elif competitor_count < 3:
            comp_adj = 1.1
        else:
            comp_adj = 1.0
        
        rep_adj = 0.8 + (reputation * 0.4)
        prob = base_prob * comp_adj * rep_adj
        
        return round(min(0.95, max(0.05, prob)), 2)
    
    
    def _calculate_confidence(self, category: ServiceCategory, platform: str) -> float:
        confidence = 0.5
        
        category_bids = [b for b in self.bid_history if b.category == category]
        if len(category_bids) > 50:
            confidence += 0.2
        elif len(category_bids) > 20:
            confidence += 0.1
        
        competitor_obs = [c for c in self.competitor_observations if c.category == category]
        if len(competitor_obs) > 20:
            confidence += 0.15
        elif len(competitor_obs) > 10:
            confidence += 0.08
        
        return round(min(0.95, confidence), 2)
    
    
    def get_elasticity(self, category: ServiceCategory) -> float:
        return self.learned_elasticity.get(category, DEFAULT_ELASTICITY.get(category, 0.07))
    
    
    def simulate_conversion_at_price(
        self,
        category: ServiceCategory,
        base_price: float,
        new_price: float,
        base_conversion_rate: float = 0.3
    ) -> float:
        elasticity = self.get_elasticity(category)
        price_change_pct = (new_price - base_price) / base_price
        conversion_change = -elasticity * (price_change_pct / 0.10)
        new_conversion = base_conversion_rate * (1 + conversion_change)
        return max(0.05, min(0.90, new_conversion))
    
    
    def find_revenue_maximizing_price(
        self,
        category: ServiceCategory,
        base_price: float,
        base_conversion: float = 0.3
    ) -> Dict[str, Any]:
        best_price = base_price
        best_revenue = base_price * base_conversion
        
        test_points = [base_price * (0.70 + i * 0.05) for i in range(17)]
        results = []
        
        for test_price in test_points:
            conversion = self.simulate_conversion_at_price(category, base_price, test_price, base_conversion)
            expected_revenue = test_price * conversion
            results.append({
                "price": round(test_price, 2),
                "conversion": round(conversion, 3),
                "expected_revenue": round(expected_revenue, 2),
            })
            if expected_revenue > best_revenue:
                best_revenue = expected_revenue
                best_price = test_price
        
        return {
            "optimal_price": round(best_price, 2),
            "expected_conversion": round(
                self.simulate_conversion_at_price(category, base_price, best_price, base_conversion), 3
            ),
            "expected_revenue": round(best_revenue, 2),
            "revenue_vs_base": round((best_revenue - base_price * base_conversion) / (base_price * base_conversion), 2),
        }
    
    
    def get_pricing_stats(self) -> Dict[str, Any]:
        if not self.bid_history:
            return {"total_bids": 0}
        
        total_bids = len(self.bid_history)
        resolved_bids = [b for b in self.bid_history if b.outcome != BidOutcome.PENDING]
        won_bids = [b for b in self.bid_history if b.outcome == BidOutcome.WON]
        win_rate = len(won_bids) / len(resolved_bids) if resolved_bids else 0
        
        return {
            "total_bids": total_bids,
            "resolved_bids": len(resolved_bids),
            "won_bids": len(won_bids),
            "overall_win_rate": round(win_rate, 2),
            "competitor_observations": len(self.competitor_observations),
            "demand_signals": len(self.demand_signals),
        }


# ============================================================
# INTEGRATION FUNCTIONS
# ============================================================

_PRICING_AUTOPILOT: Optional[IntelligentPricingAutopilot] = None


def get_pricing_autopilot() -> IntelligentPricingAutopilot:
    global _PRICING_AUTOPILOT
    if _PRICING_AUTOPILOT is None:
        _PRICING_AUTOPILOT = IntelligentPricingAutopilot()
    return _PRICING_AUTOPILOT


async def get_smart_bid_price(
    opportunity_id: str,
    category: str,
    estimated_hours: float,
    platform: str,
    buyer_budget: Optional[float] = None,
    competitor_count: int = 0,
    agent_reputation: float = 0.5,
    urgency: str = "normal"
) -> Dict[str, Any]:
    """Main integration function - get a smart bid price."""
    autopilot = get_pricing_autopilot()
    
    try:
        cat = ServiceCategory(category.lower().replace(" ", "_"))
    except ValueError:
        cat = ServiceCategory.OTHER
    
    recommendation = await autopilot.recommend_price(
        opportunity_id=opportunity_id,
        category=cat,
        estimated_hours=estimated_hours,
        platform=platform,
        buyer_budget=buyer_budget,
        competitor_count=competitor_count,
        agent_reputation=agent_reputation,
        urgency=urgency,
    )
    
    return {
        "ok": True,
        "recommended_price": recommendation.recommended_price,
        "price_range": {"min": recommendation.price_range[0], "max": recommendation.price_range[1]},
        "win_probability": recommendation.win_probability,
        "confidence": recommendation.confidence,
        "factors": recommendation.factors,
        "hourly_rate": round(recommendation.recommended_price / estimated_hours, 2) if estimated_hours > 0 else None,
    }


def record_bid_result(
    bid_id: str,
    won: bool,
    winning_price: Optional[float] = None
) -> Dict[str, Any]:
    """Record the result of a bid for learning."""
    autopilot = get_pricing_autopilot()
    outcome = BidOutcome.WON if won else BidOutcome.LOST
    return autopilot.record_bid_outcome(bid_id, outcome, winning_price)


# ============================================================
# TESTING
# ============================================================

async def _test_pricing_autopilot():
    print("\n" + "="*60)
    print("🧪 TESTING INTELLIGENT PRICING AUTOPILOT")
    print("="*60)
    
    autopilot = get_pricing_autopilot()
    
    # Seed bid history
    print("\n📝 Seeding bid history...")
    test_bids = [
        {"cat": ServiceCategory.CONTENT_WRITING, "price": 150, "hours": 3, "won": True},
        {"cat": ServiceCategory.CONTENT_WRITING, "price": 180, "hours": 4, "won": True},
        {"cat": ServiceCategory.SOFTWARE_DEV, "price": 500, "hours": 5, "won": True},
        {"cat": ServiceCategory.CONTENT_WRITING, "price": 250, "hours": 3, "won": False, "winning": 180},
        {"cat": ServiceCategory.SOFTWARE_DEV, "price": 800, "hours": 5, "won": False, "winning": 500},
    ]
    
    for tb in test_bids:
        bid = autopilot.record_bid("opp_" + _generate_id("t"), "upwork", tb["cat"], tb["price"], tb["hours"], 5)
        autopilot.record_bid_outcome(bid.bid_id, BidOutcome.WON if tb["won"] else BidOutcome.LOST, tb.get("winning"))
    print(f"   Seeded {len(test_bids)} bids")
    
    # Test recommendation
    print("\n💰 Testing price recommendation...")
    rec = await autopilot.recommend_price(
        opportunity_id="test_001",
        category=ServiceCategory.CONTENT_WRITING,
        estimated_hours=4,
        platform="upwork",
        buyer_budget=250,
        competitor_count=5,
        agent_reputation=0.7,
    )
    
    print(f"   Recommended: ${rec.recommended_price}")
    print(f"   Win Probability: {rec.win_probability:.0%}")
    print(f"   Factors: {rec.factors}")
    
    # Test demand surge
    print("\n📈 Testing demand surge...")
    autopilot.record_demand_signal(ServiceCategory.DESIGN, "upwork", 50, 500)
    demand = autopilot.get_current_demand(ServiceCategory.DESIGN)
    print(f"   Design demand: {demand.value}")
    print(f"   Multiplier: {autopilot.get_demand_multiplier(ServiceCategory.DESIGN)}")
    
    # Stats
    print("\n📊 Stats:", autopilot.get_pricing_stats())
    print("\n✅ Pricing autopilot tests completed!")


if __name__ == "__main__":
    asyncio.run(_test_pricing_autopilot())
