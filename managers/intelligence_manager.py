"""
Intelligence Manager - Scoring, Prediction, Learning
=====================================================

Systems managed:
1. metahive_brain.py - Cross-user learning
2. outcome_oracle_max.py - Funnel tracking
3. pricing_oracle.py - Dynamic pricing
4. yield_memory.py - Pattern storage
5. ltv_forecaster.py - LTV/churn prediction
6. fraud_detector.py - Fraud signals
7. intelligent_pricing_autopilot.py - Real-time price learning
8. client_success_predictor.py - Success prediction
9. adaptive_aggression.py - Aggression tuning
10. slo_policy.py - SLA/SLO policies
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import asyncio
import logging

logger = logging.getLogger("intelligence_manager")


class IntelligenceManager:
    """Coordinates all intelligence and learning systems"""

    def __init__(self):
        self._subsystems: Dict[str, bool] = {}
        self._patterns_learned: int = 0
        self._predictions_made: int = 0
        self._init_subsystems()

    def _init_subsystems(self):
        """Initialize all 10 intelligence subsystems"""

        # 1. MetaHive Brain (cross-user learning)
        try:
            from metahive_brain import contribute_to_hive, query_hive, get_hive_stats
            self._contribute_hive = contribute_to_hive
            self._query_hive = query_hive
            self._hive_stats = get_hive_stats
            self._subsystems["metahive"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"MetaHive not available: {e}")
            self._subsystems["metahive"] = False

        # 2. Outcome Oracle (funnel tracking)
        try:
            from outcome_oracle_max import on_event, get_user_funnel_stats, credit_aigx
            self._track_event = on_event
            self._get_funnel = get_user_funnel_stats
            self._credit_aigx = credit_aigx
            self._subsystems["outcome_oracle"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Outcome oracle not available: {e}")
            self._subsystems["outcome_oracle"] = False

        # 3. Pricing Oracle (dynamic pricing)
        try:
            from pricing_oracle import calculate_dynamic_price, suggest_optimal_pricing
            self._calc_price = calculate_dynamic_price
            self._suggest_price = suggest_optimal_pricing
            self._subsystems["pricing_oracle"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Pricing oracle not available: {e}")
            self._subsystems["pricing_oracle"] = False

        # 4. Yield Memory (pattern storage)
        try:
            from yield_memory import store_pattern, get_best_action, find_similar_patterns
            self._store_pattern = store_pattern
            self._get_best_action = get_best_action
            self._find_patterns = find_similar_patterns
            self._subsystems["yield_memory"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Yield memory not available: {e}")
            self._subsystems["yield_memory"] = False

        # 5. LTV Forecaster (churn prediction)
        try:
            from ltv_forecaster import calculate_ltv_with_churn, predict_churn_risk
            self._calc_ltv = calculate_ltv_with_churn
            self._predict_churn = predict_churn_risk
            self._subsystems["ltv_forecaster"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"LTV forecaster not available: {e}")
            self._subsystems["ltv_forecaster"] = False

        # 6. Fraud Detector
        try:
            from fraud_detector import check_fraud_signals, get_risk_score
            self._check_fraud = check_fraud_signals
            self._risk_score = get_risk_score
            self._subsystems["fraud_detector"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Fraud detector not available: {e}")
            self._subsystems["fraud_detector"] = False

        # 7. Intelligent Pricing Autopilot
        try:
            from intelligent_pricing_autopilot import (
                optimize_price_realtime,
                learn_from_outcome,
                get_pricing_insights
            )
            self._optimize_price = optimize_price_realtime
            self._learn_price = learn_from_outcome
            self._price_insights = get_pricing_insights
            self._subsystems["pricing_autopilot"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Pricing autopilot not available: {e}")
            self._subsystems["pricing_autopilot"] = False

        # 8. Client Success Predictor
        try:
            from client_success_predictor import (
                predict_success_probability,
                get_success_factors,
                recommend_actions
            )
            self._predict_success = predict_success_probability
            self._success_factors = get_success_factors
            self._recommend = recommend_actions
            self._subsystems["success_predictor"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Success predictor not available: {e}")
            self._subsystems["success_predictor"] = False

        # 9. Adaptive Aggression
        try:
            from adaptive_aggression import (
                calculate_aggression_level,
                adjust_strategy,
                get_aggression_metrics
            )
            self._calc_aggression = calculate_aggression_level
            self._adjust_strategy = adjust_strategy
            self._aggression_metrics = get_aggression_metrics
            self._subsystems["adaptive_aggression"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Adaptive aggression not available: {e}")
            self._subsystems["adaptive_aggression"] = False

        # 10. SLO Policy
        try:
            from slo_policy import (
                get_slo_requirements,
                check_slo_compliance,
                calculate_slo_bonus
            )
            self._slo_requirements = get_slo_requirements
            self._check_slo = check_slo_compliance
            self._slo_bonus = calculate_slo_bonus
            self._subsystems["slo_policy"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"SLO policy not available: {e}")
            self._subsystems["slo_policy"] = False

        self._log_status()

    def _log_status(self):
        """Log initialization status"""
        available = sum(1 for v in self._subsystems.values() if v)
        total = len(self._subsystems)
        logger.info(f"IntelligenceManager: {available}/{total} subsystems loaded")

    async def score_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score opportunities using all intelligence systems"""
        scored = []

        for opp in opportunities:
            score = opp.get("ev", opp.get("expected_value", 0))

            # 1. MetaHive pattern matching
            if self._subsystems.get("metahive"):
                try:
                    pattern = self._query_hive(opp.get("type", "unknown"), {})
                    if pattern and isinstance(pattern, dict):
                        success_rate = pattern.get("success_rate", 0.5)
                        score *= (1 + success_rate)
                except Exception as e:
                    logger.debug(f"MetaHive query error: {e}")

            # 2. Outcome Oracle conversion probability
            if self._subsystems.get("outcome_oracle"):
                try:
                    funnel = self._get_funnel(opp.get("user_id", "system"))
                    if funnel and isinstance(funnel, dict):
                        conversion_rate = funnel.get("conversion_rate", 0.5)
                        score *= (0.5 + conversion_rate)
                except Exception as e:
                    logger.debug(f"Funnel stats error: {e}")

            # 3. LTV multiplier
            if self._subsystems.get("ltv_forecaster"):
                try:
                    ltv_data = self._calc_ltv(opp.get("user_id", "system"), {})
                    if ltv_data and isinstance(ltv_data, dict):
                        ltv_multiplier = min(ltv_data.get("ltv", 100) / 100, 2.0)
                        score *= ltv_multiplier
                except Exception as e:
                    logger.debug(f"LTV calculation error: {e}")

            # 4. Fraud risk adjustment
            if self._subsystems.get("fraud_detector"):
                try:
                    fraud_signals = self._check_fraud({"opportunity": opp})
                    if fraud_signals and isinstance(fraud_signals, dict):
                        risk = fraud_signals.get("risk_level", 0)
                        score *= (1 - risk * 0.5)  # Reduce score based on fraud risk
                except Exception as e:
                    logger.debug(f"Fraud check error: {e}")

            # 5. Success prediction
            if self._subsystems.get("success_predictor"):
                try:
                    success_prob = self._predict_success(opp) if callable(self._predict_success) else 0.5
                    if isinstance(success_prob, (int, float)):
                        score *= (0.5 + success_prob * 0.5)
                except Exception as e:
                    logger.debug(f"Success prediction error: {e}")

            scored.append({
                **opp,
                "priority_score": max(0, score),
                "scored_at": datetime.now(timezone.utc).isoformat()
            })
            self._predictions_made += 1

        # Sort by priority score
        scored.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        return scored

    async def predict_outcomes(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Predict outcomes for a specific opportunity"""
        predictions = {
            "opportunity_id": opportunity.get("id", str(uuid4())[:8]),
            "success_probability": 0.5,
            "expected_revenue": 0,
            "expected_cost": 0,
            "ltv_impact": 0,
            "risk_factors": []
        }

        # Success probability
        if self._subsystems.get("success_predictor") and callable(self._predict_success):
            try:
                predictions["success_probability"] = self._predict_success(opportunity)
            except:
                pass

        # Expected revenue from pricing
        if self._subsystems.get("pricing_oracle") and callable(self._calc_price):
            try:
                price_data = self._calc_price(opportunity.get("base_price", 100), opportunity)
                if isinstance(price_data, dict):
                    predictions["expected_revenue"] = price_data.get("price", 100)
                elif isinstance(price_data, (int, float)):
                    predictions["expected_revenue"] = price_data
            except:
                pass

        # LTV impact
        if self._subsystems.get("ltv_forecaster") and callable(self._calc_ltv):
            try:
                ltv = self._calc_ltv(opportunity.get("user_id", "system"), {})
                if isinstance(ltv, dict):
                    predictions["ltv_impact"] = ltv.get("ltv", 0)
            except:
                pass

        # Risk factors
        if self._subsystems.get("fraud_detector") and callable(self._check_fraud):
            try:
                fraud = self._check_fraud(opportunity)
                if isinstance(fraud, dict):
                    predictions["risk_factors"] = fraud.get("signals", [])
            except:
                pass

        self._predictions_made += 1
        return predictions

    async def optimize_pricing(self, opportunity: Dict[str, Any]) -> float:
        """Get optimized price for an opportunity"""
        base_price = opportunity.get("base_price", opportunity.get("ev", 100))

        # Try pricing autopilot first (real-time learning)
        if self._subsystems.get("pricing_autopilot") and callable(self._optimize_price):
            try:
                optimized = self._optimize_price(opportunity)
                if isinstance(optimized, (int, float)):
                    return optimized
                elif isinstance(optimized, dict):
                    return optimized.get("price", base_price)
            except:
                pass

        # Fallback to pricing oracle
        if self._subsystems.get("pricing_oracle") and callable(self._calc_price):
            try:
                price_data = self._calc_price(base_price, opportunity)
                if isinstance(price_data, (int, float)):
                    return price_data
                elif isinstance(price_data, dict):
                    return price_data.get("price", base_price)
            except:
                pass

        return base_price

    async def learn_from_cycle(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Learn from execution cycle results"""
        learned = 0
        errors = []

        for result in results:
            if not isinstance(result, dict):
                continue

            # 1. Store pattern in Yield Memory
            if self._subsystems.get("yield_memory") and callable(self._store_pattern):
                try:
                    self._store_pattern(
                        username="system",
                        pattern_type="execution_result",
                        context={"cycle": result.get("cycle_id", "unknown")},
                        action={"type": result.get("type", "unknown")},
                        outcome={"success": result.get("ok", False), "revenue": result.get("revenue", 0)}
                    )
                    learned += 1
                except Exception as e:
                    errors.append(f"yield_memory: {e}")

            # 2. Contribute to MetaHive
            if self._subsystems.get("metahive") and callable(self._contribute_hive):
                try:
                    await self._contribute_hive(
                        username="system",
                        pattern_type="execution_learning",
                        context={"result_type": result.get("type", "unknown")},
                        action={"success": result.get("ok", False)},
                        outcome={"revenue": result.get("revenue", 0)}
                    )
                    learned += 1
                except Exception as e:
                    errors.append(f"metahive: {e}")

            # 3. Track in Outcome Oracle
            if self._subsystems.get("outcome_oracle") and callable(self._track_event):
                try:
                    event_type = "task_completed" if result.get("ok") else "task_failed"
                    self._track_event(event_type, "system", result)
                    learned += 1
                except Exception as e:
                    errors.append(f"outcome_oracle: {e}")

            # 4. Learn pricing from outcome
            if self._subsystems.get("pricing_autopilot") and callable(self._learn_price):
                try:
                    self._learn_price(result)
                    learned += 1
                except Exception as e:
                    errors.append(f"pricing_autopilot: {e}")

        self._patterns_learned += learned

        return {
            "ok": len(errors) == 0,
            "patterns_learned": learned,
            "errors": errors[:5] if errors else [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def get_best_action_for_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get best action recommendation for a given context"""
        recommendations = {
            "action": None,
            "confidence": 0,
            "reasoning": []
        }

        # Query yield memory for similar patterns
        if self._subsystems.get("yield_memory") and callable(self._get_best_action):
            try:
                best = self._get_best_action(context)
                if best:
                    recommendations["action"] = best.get("action")
                    recommendations["confidence"] = best.get("confidence", 0.5)
                    recommendations["reasoning"].append("yield_memory pattern match")
            except:
                pass

        # Query metahive for collective wisdom
        if self._subsystems.get("metahive") and callable(self._query_hive):
            try:
                hive_wisdom = self._query_hive(context.get("type", "general"), context)
                if hive_wisdom:
                    recommendations["hive_insights"] = hive_wisdom
                    recommendations["reasoning"].append("metahive collective learning")
            except:
                pass

        # Get aggression level
        if self._subsystems.get("adaptive_aggression") and callable(self._calc_aggression):
            try:
                aggression = self._calc_aggression(context)
                recommendations["aggression_level"] = aggression
                recommendations["reasoning"].append("adaptive aggression tuning")
            except:
                pass

        return recommendations

    def get_status(self) -> Dict[str, Any]:
        """Get intelligence manager status"""
        available = sum(1 for v in self._subsystems.values() if v)

        return {
            "ok": True,
            "subsystems": {
                "available": available,
                "total": len(self._subsystems),
                "percentage": round(available / len(self._subsystems) * 100, 1) if self._subsystems else 0,
                "details": self._subsystems
            },
            "intelligence": {
                "patterns_learned": self._patterns_learned,
                "predictions_made": self._predictions_made
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton instance
_intelligence_manager: Optional[IntelligenceManager] = None


def get_intelligence_manager() -> IntelligenceManager:
    """Get or create the intelligence manager singleton"""
    global _intelligence_manager
    if _intelligence_manager is None:
        _intelligence_manager = IntelligenceManager()
    return _intelligence_manager
