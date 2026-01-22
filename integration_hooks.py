"""
UNIFIED INTEGRATION HOOKS
=========================

Drop-in integration module for wiring monetization and brain_overlay
into all systems across the platform.

Usage:
    from integration_hooks import IntegrationHooks
    hooks = IntegrationHooks()

    # In discovery systems:
    hooks.on_discovery(opportunity_data)

    # In bidding systems:
    hooks.on_bid(bid_data)

    # In execution systems:
    hooks.on_execution_start(coi_data)
    hooks.on_execution_complete(coi_data, success, proofs)

    # In reputation updates:
    hooks.on_reputation_change(entity_id, delta, reason)
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular dependencies
_monetization = None
_brain = None
_ocs_engine = None
_feature_store = None
_policy_engine = None


def _get_monetization():
    """Lazy load monetization fabric"""
    global _monetization
    if _monetization is None:
        try:
            from monetization import MonetizationFabric
            _monetization = MonetizationFabric()
        except ImportError:
            logger.warning("Monetization fabric not available")
            _monetization = False
    return _monetization if _monetization else None


def _get_brain():
    """Lazy load brain overlay"""
    global _brain
    if _brain is None:
        try:
            from brain_overlay import Brain
            _brain = Brain()
        except ImportError:
            logger.warning("Brain overlay not available")
            _brain = False
    return _brain if _brain else None


def _get_ocs():
    """Lazy load OCS engine"""
    global _ocs_engine
    if _ocs_engine is None:
        try:
            from brain_overlay.ocs import OCSEngine
            _ocs_engine = OCSEngine()
        except ImportError:
            logger.warning("OCS engine not available")
            _ocs_engine = False
    return _ocs_engine if _ocs_engine else None


def _get_features():
    """Lazy load feature store"""
    global _feature_store
    if _feature_store is None:
        try:
            from brain_overlay.feature_store import FeatureStore
            _feature_store = FeatureStore()
        except ImportError:
            logger.warning("Feature store not available")
            _feature_store = False
    return _feature_store if _feature_store else None


def _get_policy():
    """Lazy load policy engine"""
    global _policy_engine
    if _policy_engine is None:
        try:
            from brain_overlay.policy import PolicyEngine
            _policy_engine = PolicyEngine()
        except ImportError:
            logger.warning("Policy engine not available")
            _policy_engine = False
    return _policy_engine if _policy_engine else None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class IntegrationHooks:
    """
    Unified hooks for integrating monetization and brain across all systems.

    Provides standardized entry points for:
    - Discovery events (opportunities found)
    - Bidding events (bids placed/won)
    - Execution events (start/progress/complete)
    - Reputation events (score changes)
    - Revenue events (payments/splits)
    """

    def __init__(self, system_name: str = "unknown"):
        self.system_name = system_name
        self._callbacks: Dict[str, List[Callable]] = {}

    # =========================================================================
    # DISCOVERY HOOKS
    # =========================================================================

    def on_discovery(
        self,
        opportunity: Dict[str, Any],
        *,
        source: str = None,
        confidence: float = 0.5,
        estimated_value: float = 0.0
    ) -> Dict[str, Any]:
        """
        Hook for when an opportunity is discovered.

        Triggers:
        - Brain event emission
        - Feature store update
        - OCS lookup for ranking
        - Price suggestion
        """
        result = {
            "hooked": True,
            "timestamp": _now_iso(),
            "system": self.system_name
        }

        # Emit to brain
        brain = _get_brain()
        if brain:
            try:
                brain.emit("discovery", {
                    "opportunity": opportunity,
                    "source": source or self.system_name,
                    "confidence": confidence,
                    "estimated_value": estimated_value
                })
                result["brain_event"] = True
            except Exception as e:
                logger.error(f"Brain emit failed: {e}")
                result["brain_event"] = False

        # Update feature store
        features = _get_features()
        if features:
            try:
                entity_id = opportunity.get("entity_id") or opportunity.get("user_id") or "unknown"
                features.update(
                    keys={"actor_id": entity_id, "sku_id": opportunity.get("sku_id", "discovery")},
                    features={
                        "last_discovery": _now_iso(),
                        "discovery_confidence": confidence,
                        "estimated_value": estimated_value
                    }
                )
                result["feature_update"] = True
            except Exception as e:
                logger.error(f"Feature store update failed: {e}")
                result["feature_update"] = False

        # Get price suggestion
        monetization = _get_monetization()
        if monetization and estimated_value > 0:
            try:
                suggested_price = monetization.price_outcome(
                    base_price=estimated_value,
                    load_pct=0.3,
                    wave_score=confidence
                )
                result["suggested_price"] = suggested_price
            except Exception as e:
                logger.error(f"Price suggestion failed: {e}")

        # Get OCS for entity
        ocs = _get_ocs()
        if ocs:
            try:
                entity_id = opportunity.get("entity_id") or opportunity.get("provider_id")
                if entity_id:
                    ocs_data = ocs.get_entity_details(entity_id)
                    result["provider_ocs"] = ocs_data.get("ocs", 50)
            except Exception as e:
                logger.error(f"OCS lookup failed: {e}")

        return result

    def on_opportunity_ranked(
        self,
        opportunities: List[Dict[str, Any]],
        *,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """
        Hook for ranking opportunities with OCS and sponsored placement.

        Returns ranked opportunities with OCS scores and sponsored boosts.
        """
        ocs = _get_ocs()
        monetization = _get_monetization()

        ranked = []
        for opp in opportunities:
            entity_id = opp.get("entity_id") or opp.get("provider_id")

            # Get OCS score
            ocs_score = 50
            if ocs and entity_id:
                try:
                    ocs_data = ocs.get_entity_details(entity_id)
                    ocs_score = ocs_data.get("ocs", 50)
                except:
                    pass

            # Calculate ranking score
            base_score = opp.get("score", opp.get("confidence", 0.5))
            ocs_boost = (ocs_score - 50) / 100  # -0.5 to +0.5

            ranked.append({
                **opp,
                "ocs": ocs_score,
                "base_score": base_score,
                "ocs_boost": round(ocs_boost, 3),
                "final_score": round(base_score * (1 + ocs_boost * 0.3), 4)
            })

        # Sort by final score
        ranked.sort(key=lambda x: x["final_score"], reverse=True)

        # Add rank positions
        for i, r in enumerate(ranked):
            r["rank"] = i + 1

        return ranked

    # =========================================================================
    # BIDDING HOOKS
    # =========================================================================

    def on_bid_placed(
        self,
        bid: Dict[str, Any],
        *,
        opportunity_id: str = None,
        bid_amount: float = 0.0
    ) -> Dict[str, Any]:
        """
        Hook for when a bid is placed.

        Triggers:
        - Brain event emission
        - Policy learning
        - Fee calculation
        """
        result = {
            "hooked": True,
            "timestamp": _now_iso(),
            "system": self.system_name
        }

        # Emit to brain
        brain = _get_brain()
        if brain:
            try:
                brain.emit("bid_placed", {
                    "bid": bid,
                    "opportunity_id": opportunity_id,
                    "amount": bid_amount
                })
                result["brain_event"] = True
            except Exception as e:
                logger.error(f"Brain emit failed: {e}")

        # Calculate fees
        monetization = _get_monetization()
        if monetization and bid_amount > 0:
            try:
                from monetization.fee_schedule import calculate_platform_fee
                fees = calculate_platform_fee(bid_amount)
                result["fees"] = fees
                result["net_to_provider"] = round(bid_amount - fees.get("total_fee", 0), 2)
            except Exception as e:
                logger.error(f"Fee calculation failed: {e}")

        return result

    def on_bid_won(
        self,
        bid: Dict[str, Any],
        *,
        opportunity_id: str = None,
        winning_amount: float = 0.0,
        runner_up_amount: float = None
    ) -> Dict[str, Any]:
        """
        Hook for when a bid is won.

        Triggers:
        - Brain learning (positive reward)
        - Revenue routing setup
        - OCS consideration
        """
        result = {
            "hooked": True,
            "timestamp": _now_iso(),
            "system": self.system_name
        }

        # Emit to brain
        brain = _get_brain()
        if brain:
            try:
                brain.emit("bid_won", {
                    "bid": bid,
                    "opportunity_id": opportunity_id,
                    "amount": winning_amount,
                    "spread": winning_amount - runner_up_amount if runner_up_amount else 0
                })

                # Learn from winning bid
                entity_id = bid.get("entity_id") or bid.get("bidder_id")
                if entity_id:
                    brain.learn(
                        "bidding",
                        state={"opportunity_id": opportunity_id},
                        action={"bid_amount": winning_amount},
                        reward=1.0  # Won the bid
                    )

                result["brain_event"] = True
            except Exception as e:
                logger.error(f"Brain emit failed: {e}")

        # Calculate revenue split
        monetization = _get_monetization()
        if monetization and winning_amount > 0:
            try:
                splits = monetization.split_revenue(winning_amount)
                result["revenue_split"] = splits
            except Exception as e:
                logger.error(f"Revenue split failed: {e}")

        return result

    def on_bid_lost(
        self,
        bid: Dict[str, Any],
        *,
        opportunity_id: str = None,
        bid_amount: float = 0.0,
        winning_amount: float = None
    ) -> Dict[str, Any]:
        """
        Hook for when a bid is lost.

        Triggers:
        - Brain learning (negative reward to calibrate)
        """
        result = {
            "hooked": True,
            "timestamp": _now_iso(),
            "system": self.system_name
        }

        brain = _get_brain()
        if brain:
            try:
                brain.emit("bid_lost", {
                    "bid": bid,
                    "opportunity_id": opportunity_id,
                    "amount": bid_amount,
                    "winning_amount": winning_amount
                })

                # Learn from lost bid
                entity_id = bid.get("entity_id") or bid.get("bidder_id")
                if entity_id:
                    # Small negative reward if we bid too low
                    reward = -0.2 if winning_amount and bid_amount < winning_amount else -0.1
                    brain.learn(
                        "bidding",
                        state={"opportunity_id": opportunity_id},
                        action={"bid_amount": bid_amount},
                        reward=reward
                    )

                result["brain_event"] = True
            except Exception as e:
                logger.error(f"Brain emit failed: {e}")

        return result

    # =========================================================================
    # EXECUTION HOOKS
    # =========================================================================

    def on_execution_start(
        self,
        coi: Dict[str, Any],
        *,
        connector: str = None,
        pdl_id: str = None
    ) -> Dict[str, Any]:
        """
        Hook for when execution starts.

        Triggers:
        - Brain event emission
        - Connector policy lookup
        - Exploration check
        """
        result = {
            "hooked": True,
            "timestamp": _now_iso(),
            "system": self.system_name
        }

        brain = _get_brain()
        if brain:
            try:
                brain.emit("execution_started", {
                    "coi": coi,
                    "connector": connector,
                    "pdl_id": pdl_id
                })
                result["brain_event"] = True

                # Check exploration
                if brain.exploration.should_explore({}):
                    result["explore"] = True
                    result["exploration_connector"] = connector
            except Exception as e:
                logger.error(f"Brain emit failed: {e}")

        # Get connector policy recommendation
        policy = _get_policy()
        if policy and connector:
            try:
                rec = policy.suggest("connector.ucb", {"connector_id": connector})
                if rec:
                    result["connector_recommendation"] = rec
            except Exception as e:
                logger.error(f"Policy lookup failed: {e}")

        return result

    def on_execution_progress(
        self,
        coi_id: str,
        *,
        progress_pct: float = 0.0,
        stage: str = None
    ) -> Dict[str, Any]:
        """
        Hook for execution progress updates.
        """
        result = {
            "hooked": True,
            "timestamp": _now_iso(),
            "system": self.system_name
        }

        brain = _get_brain()
        if brain:
            try:
                brain.emit("execution_progress", {
                    "coi_id": coi_id,
                    "progress": progress_pct,
                    "stage": stage
                })
                result["brain_event"] = True
            except Exception as e:
                logger.error(f"Brain emit failed: {e}")

        return result

    def on_execution_complete(
        self,
        coi: Dict[str, Any],
        *,
        success: bool = True,
        proofs: List[Dict[str, Any]] = None,
        revenue: float = 0.0,
        connector: str = None
    ) -> Dict[str, Any]:
        """
        Hook for when execution completes.

        Triggers:
        - Brain learning (outcome reward)
        - OCS update (proofs)
        - Revenue recording
        - Ledger posting
        - Badge minting consideration
        """
        result = {
            "hooked": True,
            "timestamp": _now_iso(),
            "system": self.system_name
        }

        coi_id = coi.get("coi_id") or coi.get("id")
        entity_id = coi.get("entity_id") or coi.get("provider_id")

        # Emit to brain and learn
        brain = _get_brain()
        if brain:
            try:
                brain.emit("execution_completed", {
                    "coi": coi,
                    "success": success,
                    "proofs": proofs or [],
                    "revenue": revenue
                })

                # Learn from execution
                if connector:
                    reward = 1.0 if success else -0.5
                    brain.learn(
                        "connector",
                        state={"connector_id": connector},
                        action={"selected": True},
                        reward=reward
                    )

                result["brain_event"] = True
            except Exception as e:
                logger.error(f"Brain emit failed: {e}")

        # Update OCS
        ocs = _get_ocs()
        if ocs and entity_id:
            try:
                ocs_result = ocs.record_outcome(
                    entity_id=entity_id,
                    success=success,
                    sla_met=success,
                    proofs=len(proofs) if proofs else 0,
                    dispute=not success
                )
                result["ocs_updated"] = True
                result["new_ocs"] = ocs_result.get("ocs")
            except Exception as e:
                logger.error(f"OCS update failed: {e}")

        # Record revenue
        monetization = _get_monetization()
        if monetization and revenue > 0:
            try:
                # Post to ledger
                from monetization.ledger import post_entry
                post_entry(
                    entry_type="revenue",
                    ref=f"coi:{coi_id}",
                    debit=revenue,
                    credit=0,
                    meta={"success": success, "connector": connector, "entity_id": entity_id}
                )
                result["ledger_posted"] = True

                # Calculate splits
                splits = monetization.split_revenue(revenue)
                result["revenue_split"] = splits

                # Consider badge minting
                if success and proofs:
                    try:
                        from monetization.proof_badges import consider_badge
                        badge_result = consider_badge(entity_id, coi_id, proofs)
                        if badge_result.get("badge_minted"):
                            result["badge"] = badge_result.get("badge")
                    except ImportError:
                        pass

            except Exception as e:
                logger.error(f"Revenue recording failed: {e}")

        return result

    # =========================================================================
    # REPUTATION HOOKS
    # =========================================================================

    def on_reputation_change(
        self,
        entity_id: str,
        *,
        delta: float = 0.0,
        reason: str = None,
        source_system: str = None
    ) -> Dict[str, Any]:
        """
        Hook for reputation changes.

        Wires external reputation systems to OCS.
        """
        result = {
            "hooked": True,
            "timestamp": _now_iso(),
            "system": self.system_name
        }

        ocs = _get_ocs()
        if ocs:
            try:
                # Map external reputation delta to OCS impact
                ocs_result = ocs.record_outcome(
                    entity_id=entity_id,
                    success=delta > 0,
                    sla_met=delta > 0,
                    proofs=max(0, int(delta * 0.1)) if delta > 0 else 0,
                    dispute=delta < 0
                )
                result["ocs_updated"] = True
                result["new_ocs"] = ocs_result.get("ocs")
            except Exception as e:
                logger.error(f"OCS update failed: {e}")

        # Emit to brain
        brain = _get_brain()
        if brain:
            try:
                brain.emit("reputation_change", {
                    "entity_id": entity_id,
                    "delta": delta,
                    "reason": reason,
                    "source": source_system or self.system_name
                })
                result["brain_event"] = True
            except Exception as e:
                logger.error(f"Brain emit failed: {e}")

        return result

    # =========================================================================
    # REVENUE HOOKS
    # =========================================================================

    def on_payment_received(
        self,
        amount: float,
        *,
        currency: str = "USD",
        payer_id: str = None,
        ref_type: str = None,
        ref_id: str = None
    ) -> Dict[str, Any]:
        """
        Hook for when payment is received.

        Triggers:
        - Ledger posting
        - Revenue split calculation
        - Settlement queuing
        """
        result = {
            "hooked": True,
            "timestamp": _now_iso(),
            "system": self.system_name
        }

        monetization = _get_monetization()
        if monetization:
            try:
                # Post to ledger
                from monetization.ledger import post_entry
                post_entry(
                    entry_type="payment",
                    ref=f"{ref_type or 'payment'}:{ref_id or 'unknown'}",
                    debit=amount,
                    credit=0,
                    meta={"payer_id": payer_id, "currency": currency}
                )
                result["ledger_posted"] = True

                # Calculate splits
                splits = monetization.split_revenue(amount)
                result["revenue_split"] = splits

                # Queue settlement for provider share
                try:
                    from monetization.settlements import queue_settlement
                    if payer_id:
                        queue_settlement(
                            entity_id=payer_id,
                            amount=splits.get("user", 0),
                            currency=currency
                        )
                        result["settlement_queued"] = True
                except ImportError:
                    pass

            except Exception as e:
                logger.error(f"Payment processing failed: {e}")

        # Emit to brain
        brain = _get_brain()
        if brain:
            try:
                brain.emit("payment_received", {
                    "amount": amount,
                    "currency": currency,
                    "payer_id": payer_id,
                    "ref_type": ref_type,
                    "ref_id": ref_id
                })
                result["brain_event"] = True
            except Exception as e:
                logger.error(f"Brain emit failed: {e}")

        return result

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_entity_ocs(self, entity_id: str) -> Dict[str, Any]:
        """Get OCS data for an entity"""
        ocs = _get_ocs()
        if ocs:
            return ocs.get_entity_details(entity_id)
        return {"ocs": 50, "tier": "standard"}

    def get_price_suggestion(
        self,
        base_price: float,
        *,
        load_pct: float = 0.3,
        wave_score: float = 0.2,
        entity_id: str = None
    ) -> float:
        """Get dynamic price suggestion"""
        monetization = _get_monetization()
        if monetization:
            # Adjust for OCS if entity provided
            ocs_multiplier = 1.0
            if entity_id:
                ocs = _get_ocs()
                if ocs:
                    ocs_data = ocs.get_entity_details(entity_id)
                    tier = ocs_data.get("tier", "standard")
                    # Higher OCS = slight premium pricing
                    ocs_multiplier = {
                        "premium": 1.15,
                        "standard": 1.0,
                        "watched": 0.95,
                        "probation": 0.90
                    }.get(tier, 1.0)

            suggested = monetization.price_outcome(
                base_price=base_price,
                load_pct=load_pct,
                wave_score=wave_score
            )
            return round(suggested * ocs_multiplier, 2)
        return base_price

    def get_policy(self, policy_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get policy recommendation"""
        policy = _get_policy()
        if policy:
            return policy.suggest(policy_name, context or {})
        return {}

    def register_callback(self, event_type: str, callback: Callable):
        """Register callback for specific event type"""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Trigger registered callbacks"""
        for callback in self._callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Callback failed for {event_type}: {e}")


# =============================================================================
# MODULE-LEVEL SINGLETON AND CONVENIENCE FUNCTIONS
# =============================================================================

_default_hooks = None


def get_hooks(system_name: str = None) -> IntegrationHooks:
    """Get or create integration hooks instance"""
    global _default_hooks
    if system_name:
        return IntegrationHooks(system_name)
    if _default_hooks is None:
        _default_hooks = IntegrationHooks("default")
    return _default_hooks


# Convenience functions for quick integration
def hook_discovery(opportunity: Dict, **kwargs) -> Dict:
    """Quick hook for discovery events"""
    return get_hooks().on_discovery(opportunity, **kwargs)


def hook_bid_placed(bid: Dict, **kwargs) -> Dict:
    """Quick hook for bid placement"""
    return get_hooks().on_bid_placed(bid, **kwargs)


def hook_bid_won(bid: Dict, **kwargs) -> Dict:
    """Quick hook for won bids"""
    return get_hooks().on_bid_won(bid, **kwargs)


def hook_execution_start(coi: Dict, **kwargs) -> Dict:
    """Quick hook for execution start"""
    return get_hooks().on_execution_start(coi, **kwargs)


def hook_execution_complete(coi: Dict, **kwargs) -> Dict:
    """Quick hook for execution completion"""
    return get_hooks().on_execution_complete(coi, **kwargs)


def hook_payment(amount: float, **kwargs) -> Dict:
    """Quick hook for payments"""
    return get_hooks().on_payment_received(amount, **kwargs)


def get_ocs(entity_id: str) -> Dict:
    """Quick OCS lookup"""
    return get_hooks().get_entity_ocs(entity_id)


def suggest_price(base_price: float, **kwargs) -> float:
    """Quick price suggestion"""
    return get_hooks().get_price_suggestion(base_price, **kwargs)
