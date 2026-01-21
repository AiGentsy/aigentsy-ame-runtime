"""
BRAIN INTEGRATION OVERLAY v1.0
==============================

Self-sharpening monetization layer that wires every fabric event into the AI Brain/MetaHive.
Each agent learns the best-earning routes, pushes them network-wide, and compounds outcomes.

Components:
- events: Shared Outcomes Bus - emit normalized, model-ready records
- feature_store: Single source of truth for all learning features
- policy: Policy interfaces for pricing, placement, tranching, routing
- apex_routes: Cross-agent knowledge distribution (top-decile policies)
- ocs: Outcome Credit Score as first-class feature
- exploration: Safe exploration governor (3-7% volume for discovery)
- passport: Proof-of-Outcome portable credentials
- programmatic_guarantees: Outcome-Or-Refund with premium pricing
- placement: Sponsored intent marketplace
- spec_importer: Auto-generate PDLs from OpenAPI/HAR/Postman

Usage:
    from brain_overlay import Brain

    brain = Brain()

    # Emit events
    brain.emit("coi.executed", payload)

    # Get policy suggestions
    action = brain.policy("pricing.oaa", scope).suggest(state)

    # Learn from outcomes
    brain.learn("pricing.oaa", state, action, reward=profit)

    # Distribute apex routes
    brain.publish_apex_routes()
"""

from .events import BrainEvents, emit_event
from .feature_store import FeatureStore, get_feature_store
from .policy import PolicyEngine, get_policy
from .apex_routes import ApexRoutes, publish_apex, subscribe_apex
from .ocs import OCSEngine, score_entity, get_ocs
from .exploration import ExplorationGovernor, should_explore, record_exploration
from .passport import PassportEngine, issue_passport, verify_passport
from .programmatic_guarantees import PGEngine, quote_pg, attach_pg
from .placement import PlacementMarket, rank_with_sponsors, bid_on_placement
from .spec_importer import SpecImporter, import_openapi, import_har

__all__ = [
    "Brain",
    "BrainEvents", "emit_event",
    "FeatureStore", "get_feature_store",
    "PolicyEngine", "get_policy",
    "ApexRoutes", "publish_apex", "subscribe_apex",
    "OCSEngine", "score_entity", "get_ocs",
    "ExplorationGovernor", "should_explore", "record_exploration",
    "PassportEngine", "issue_passport", "verify_passport",
    "PGEngine", "quote_pg", "attach_pg",
    "PlacementMarket", "rank_with_sponsors", "bid_on_placement",
    "SpecImporter", "import_openapi", "import_har"
]

__version__ = "1.0.0"


class Brain:
    """
    Unified Brain interface that orchestrates all overlay components.

    The Brain is the collective intelligence layer that:
    1. Ingests events from all fabric operations
    2. Maintains feature store for model-ready data
    3. Provides policy suggestions via learned models
    4. Distributes apex routes network-wide
    5. Tracks OCS for trust-weighted operations
    6. Governs exploration for safe discovery
    """

    def __init__(self):
        self.events = BrainEvents()
        self.features = FeatureStore()
        self.policies = PolicyEngine()
        self.apex = ApexRoutes()
        self.ocs = OCSEngine()
        self.exploration = ExplorationGovernor()
        self.passports = PassportEngine()
        self.guarantees = PGEngine()
        self.placement = PlacementMarket()
        self.importer = SpecImporter()

        # Wire components together
        self._wire_components()

    def _wire_components(self):
        """Wire event handlers to update feature store and policies"""
        # COI events update OCS and features
        self.events.on("coi.executed", self._on_coi_executed)
        self.events.on("pricing.quoted", self._on_pricing_quoted)
        self.events.on("ifx.order_filled", self._on_order_filled)
        self.events.on("dealgraph.tranche_bound", self._on_tranche_bound)
        self.events.on("ocs.updated", self._on_ocs_updated)
        self.events.on("placement.auction", self._on_placement_auction)
        self.events.on("connector.health", self._on_connector_health)

    def emit(self, event_type: str, payload: dict):
        """Emit event to brain and feature store"""
        return self.events.emit(event_type, payload)

    def policy(self, policy_name: str, scope: dict = None):
        """Get policy interface for suggestions"""
        return self.policies.get(policy_name, scope)

    def learn(self, policy_name: str, state: dict, action: dict, reward: float, meta: dict = None):
        """Record learning example for policy"""
        return self.policies.learn(policy_name, state, action, reward, meta)

    def find_apex_routes(self, top_k: int = 20, min_lift: float = 0.08, min_conf: float = 0.9):
        """Find top-performing policies to distribute"""
        return self.apex.find_top(top_k, min_lift, min_conf)

    def publish_apex(self, routes: list = None):
        """Publish apex routes to MetaHive"""
        if routes is None:
            routes = self.find_apex_routes()
        return self.apex.publish(routes)

    def get_ocs(self, entity_id: str) -> float:
        """Get Outcome Credit Score for entity"""
        return self.ocs.score(entity_id)

    def should_explore(self, context: dict) -> bool:
        """Check if we should explore (vs exploit)"""
        return self.exploration.should_explore(context)

    def issue_passport(self, entity_id: str) -> dict:
        """Issue proof-of-outcome passport"""
        return self.passports.issue(entity_id)

    def quote_guarantee(self, ocs: float, variance: float, base_price: float) -> dict:
        """Quote programmatic guarantee premium"""
        return self.guarantees.quote(ocs, variance, base_price)

    def rank_results(self, results: list, sponsored_bids: dict = None) -> list:
        """Rank results with sponsored placement"""
        return self.placement.rank(results, sponsored_bids)

    def import_spec(self, spec: dict, spec_type: str = "openapi") -> dict:
        """Import API spec and generate PDLs"""
        return self.importer.import_spec(spec, spec_type)

    # Event handlers
    def _on_coi_executed(self, payload: dict):
        """Handle COI execution event"""
        actor_id = payload.get("actor_id")
        if actor_id:
            # Update OCS
            self.ocs.record_outcome(
                actor_id,
                success=payload.get("success", False),
                sla_met=payload.get("sla_met", False),
                proofs=payload.get("proof_count", 0)
            )
            # Update features
            self.features.update(
                keys={"actor_id": actor_id, "sku_id": payload.get("sku_id")},
                features={
                    "last_coi_success": payload.get("success"),
                    "last_coi_margin": payload.get("margin", 0),
                    "last_coi_latency": payload.get("latency_ms", 0)
                }
            )

    def _on_pricing_quoted(self, payload: dict):
        """Handle pricing quote event"""
        self.features.update(
            keys={"sku_id": payload.get("sku_id"), "segment": payload.get("segment")},
            features={
                "last_quote": payload.get("price"),
                "last_spread": payload.get("spread"),
                "pg_attached": payload.get("pg_attached", False)
            }
        )

    def _on_order_filled(self, payload: dict):
        """Handle IFX order fill event"""
        self.features.update(
            keys={"actor_id": payload.get("actor_id")},
            features={
                "last_fill_price": payload.get("fill_price"),
                "last_slippage": payload.get("slippage", 0),
                "kelly_fraction": payload.get("kelly_fraction", 0.1)
            }
        )

    def _on_tranche_bound(self, payload: dict):
        """Handle DealGraph tranche binding event"""
        self.features.update(
            keys={"tranche_id": payload.get("tranche_id")},
            features={
                "tranche_type": payload.get("tranche_type"),
                "expected_loss": payload.get("expected_loss", 0),
                "premium": payload.get("premium", 0)
            }
        )

    def _on_ocs_updated(self, payload: dict):
        """Handle OCS update event"""
        actor_id = payload.get("actor_id")
        if actor_id:
            self.features.update(
                keys={"actor_id": actor_id},
                features={"ocs": payload.get("ocs", 50)}
            )

    def _on_placement_auction(self, payload: dict):
        """Handle placement auction event"""
        self.features.update(
            keys={"placement_id": payload.get("placement_id")},
            features={
                "winning_bid": payload.get("winning_bid"),
                "ctr": payload.get("ctr", 0),
                "conversion": payload.get("conversion", 0)
            }
        )

    def _on_connector_health(self, payload: dict):
        """Handle connector health event"""
        connector_id = payload.get("connector_id")
        if connector_id:
            self.features.update(
                keys={"connector_id": connector_id},
                features={
                    "latency_p95": payload.get("latency_p95", 0),
                    "fail_rate": payload.get("fail_rate", 0),
                    "rate_limit_hits": payload.get("rate_limit_hits", 0)
                }
            )


# Module-level singleton
_brain = None

def get_brain() -> Brain:
    """Get or create brain singleton"""
    global _brain
    if _brain is None:
        _brain = Brain()
    return _brain
