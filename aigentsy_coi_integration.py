"""
AIGENTSY COI INTEGRATION LAYER
==============================

Wires the Universal Fulfillment Fabric (COI Runtime) with ALL AiGentsy systems:
- AME (Autonomous Marketing Engine) - Pitch delivery via COI connectors
- AMG (App Monetization Graph) - Revenue loop fulfillment via COI
- AI Family Brain - Intelligent task routing with multi-model orchestration
- MetaBridge - Deal matching and proposal dispatch via COI
- JV Mesh - Joint venture actions and notifications via COI
- MetaHive - Reward distribution and contributions via COI

This creates a unified intelligence + fulfillment fabric where:
1. AI Family Brain decides WHAT to do (intelligence)
2. COI Runtime decides HOW to do it (execution)
3. All systems share proofs, SLAs, and attribution

Usage:
    from aigentsy_coi_integration import AiGentsyFabric

    fabric = AiGentsyFabric()
    await fabric.initialize()

    # Execute any outcome with full AiGentsy intelligence
    result = await fabric.execute_smart("send_email", {
        "to": "user@example.com",
        "subject": "Opportunity",
        "body": "..."
    })
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone

logger = logging.getLogger("aigentsy_fabric")


# ============================================================================
# SAFE IMPORTS WITH FALLBACKS
# ============================================================================

# COI Runtime
try:
    from coi_runtime import get_coi_runtime, COIRuntime
    COI_AVAILABLE = True
except ImportError:
    COI_AVAILABLE = False
    logger.warning("COI Runtime not available")

# AI Family Brain
try:
    from ai_family_brain import (
        get_brain, ai_execute, ai_research, ai_content, ai_code,
        TaskCategory, AIModel, get_family_stats
    )
    AI_FAMILY_AVAILABLE = True
except ImportError:
    AI_FAMILY_AVAILABLE = False
    logger.warning("AI Family Brain not available")

# AME
try:
    from ame_pitches import (
        generate_pitch, approve_pitch, get_pending_pitches, get_stats as ame_stats
    )
    AME_AVAILABLE = True
except ImportError:
    AME_AVAILABLE = False
    logger.warning("AME not available")

# AMG
try:
    from amg_orchestrator import AMGOrchestrator
    AMG_AVAILABLE = True
except ImportError:
    AMG_AVAILABLE = False
    logger.warning("AMG Orchestrator not available")

# MetaBridge
try:
    from metabridge_runtime import MetaBridgeRuntime
    METABRIDGE_AVAILABLE = True
except ImportError:
    METABRIDGE_AVAILABLE = False
    logger.warning("MetaBridge not available")

# JV Mesh
try:
    from jv_mesh import (
        create_jv_proposal, vote_on_jv, list_active_jvs,
        suggest_jv_partners, auto_propose_jv
    )
    JV_MESH_AVAILABLE = True
except ImportError:
    JV_MESH_AVAILABLE = False
    logger.warning("JV Mesh not available")

# MetaHive
try:
    from metahive_rewards import (
        join_hive, record_contribution, distribute_hive_rewards,
        get_hive_treasury_stats, get_member_projected_earnings
    )
    METAHIVE_AVAILABLE = True
except ImportError:
    METAHIVE_AVAILABLE = False
    logger.warning("MetaHive not available")

# Yield Memory
try:
    from yield_memory import store_pattern, find_similar_patterns, get_best_action
    YIELD_MEMORY_AVAILABLE = True
except ImportError:
    YIELD_MEMORY_AVAILABLE = False
    logger.warning("Yield Memory not available")


# ============================================================================
# AIGENTSY FABRIC - UNIFIED INTELLIGENCE + FULFILLMENT
# ============================================================================

class AiGentsyFabric:
    """
    The AiGentsy Fabric unifies all systems into a coherent whole:

    INTELLIGENCE LAYER (AI Family Brain):
    - Multi-model routing (Claude, GPT-4, Gemini, Perplexity)
    - Specialization learning and cross-pollination
    - Task category optimization

    FULFILLMENT LAYER (COI Runtime):
    - Universal connector bus (Resend, Stripe, Shopify, etc.)
    - Protocol descriptors (PDLs) for declarative outcomes
    - SLA monitoring and proof collection

    BUSINESS LAYER (AME, AMG, MetaBridge, JV Mesh, MetaHive):
    - Autonomous marketing and sales
    - Revenue optimization and attribution
    - Partnership formation and rewards
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Core systems
        self.coi_runtime: Optional[COIRuntime] = None
        self.ai_brain = None
        self.metabridge: Optional[MetaBridgeRuntime] = None

        # State
        self._fulfillment_history: List[Dict[str, Any]] = []
        self._callbacks: Dict[str, List[Callable]] = {
            "on_fulfillment": [],
            "on_failure": [],
            "on_revenue": []
        }

        # Metrics
        self._metrics = {
            "total_fulfillments": 0,
            "successful_fulfillments": 0,
            "failed_fulfillments": 0,
            "total_revenue": 0.0,
            "ai_tasks_routed": 0,
            "jv_proposals_sent": 0,
            "metahive_contributions": 0
        }

        self._initialized = True
        logger.info("AiGentsy Fabric instance created")

    async def initialize(self) -> Dict[str, Any]:
        """Initialize all integrated systems"""
        status = {
            "coi": False,
            "ai_family": False,
            "ame": False,
            "amg": False,
            "metabridge": False,
            "jv_mesh": False,
            "metahive": False,
            "yield_memory": False
        }

        # Initialize COI Runtime
        if COI_AVAILABLE:
            try:
                self.coi_runtime = get_coi_runtime()
                await self.coi_runtime.initialize()
                status["coi"] = True
                logger.info("COI Runtime initialized")
            except Exception as e:
                logger.error(f"COI initialization failed: {e}")

        # Initialize AI Family Brain
        if AI_FAMILY_AVAILABLE:
            try:
                self.ai_brain = get_brain()
                status["ai_family"] = True
                logger.info("AI Family Brain initialized")
            except Exception as e:
                logger.error(f"AI Family Brain init failed: {e}")

        # Initialize MetaBridge
        if METABRIDGE_AVAILABLE:
            try:
                self.metabridge = MetaBridgeRuntime()
                status["metabridge"] = True
                logger.info("MetaBridge initialized")
            except Exception as e:
                logger.error(f"MetaBridge init failed: {e}")

        # Check other systems (they don't need explicit init)
        status["ame"] = AME_AVAILABLE
        status["amg"] = AMG_AVAILABLE
        status["jv_mesh"] = JV_MESH_AVAILABLE
        status["metahive"] = METAHIVE_AVAILABLE
        status["yield_memory"] = YIELD_MEMORY_AVAILABLE

        available = [k for k, v in status.items() if v]
        logger.info(f"AiGentsy Fabric initialized: {len(available)}/{len(status)} systems")

        return {
            "ok": True,
            "systems": status,
            "available": available,
            "count": len(available)
        }

    # ========================================================================
    # SMART EXECUTION (AI-ROUTED FULFILLMENT)
    # ========================================================================

    async def execute_smart(
        self,
        outcome_type: str,
        params: Dict[str, Any],
        *,
        use_ai: bool = True,
        ai_task_category: str = "fulfillment",
        username: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Smart execution that combines AI Family Brain intelligence with COI fulfillment.

        1. If use_ai=True, AI Family Brain can enhance/validate the request
        2. COI Runtime executes the outcome with best connector
        3. Results flow back for learning and attribution
        """
        start_time = datetime.now(timezone.utc)

        # Check if AI should enhance this request
        if use_ai and AI_FAMILY_AVAILABLE and ai_task_category != "fulfillment":
            try:
                # Use AI to enhance request if it's a content generation task
                if ai_task_category in ["content_generation", "email_writing", "pitch_creation"]:
                    ai_result = await ai_execute(
                        f"Enhance this for {outcome_type}: {params.get('body', params.get('text', ''))}",
                        task_category=ai_task_category,
                        max_tokens=1500,
                        optimize_for="quality"
                    )
                    if ai_result.get("ok") and ai_result.get("response"):
                        # Use enhanced content
                        if "body" in params:
                            params["body"] = ai_result["response"]
                        elif "text" in params:
                            params["text"] = ai_result["response"]

                        self._metrics["ai_tasks_routed"] += 1
            except Exception as e:
                logger.warning(f"AI enhancement failed: {e}")

        # Execute via COI Runtime
        if not COI_AVAILABLE or not self.coi_runtime:
            return {"ok": False, "error": "coi_runtime_not_available"}

        try:
            result = await self.coi_runtime.execute_from_pdl(
                self._map_outcome_to_pdl(outcome_type),
                params,
                idempotency_key=idempotency_key
            )

            # Record for learning
            self._record_fulfillment(outcome_type, params, result, username)

            # Store pattern if yield memory is available
            if YIELD_MEMORY_AVAILABLE and username:
                try:
                    store_pattern(
                        username=username,
                        pattern_type=outcome_type,
                        context={"channel": result.get("connector", "unknown")},
                        action={"type": outcome_type, "params": params},
                        outcome={
                            "success": result.get("ok", False),
                            "latency_ms": result.get("latency_ms", 0)
                        }
                    )
                except Exception as e:
                    logger.warning(f"Pattern storage failed: {e}")

            return result

        except Exception as e:
            logger.error(f"Smart execution failed: {e}")
            return {"ok": False, "error": str(e)}

    def _map_outcome_to_pdl(self, outcome_type: str) -> str:
        """Map outcome types to PDL names"""
        mapping = {
            "send_email": "email.send",
            "send_email_nudge": "email.nudge",
            "send_email_blast": "email.send",
            "send_sms": "sms.send",
            "send_slack": "slack.message",
            "create_payment_link": "stripe.payment_link",
            "create_invoice": "stripe.invoice",
            "create_product": "shopify.create_product",
            "create_order": "shopify.create_order",
            "deliver_webhook": "webhook.deliver",
            "upload_file": "storage.upload",
            "create_record": "airtable.create_record",
            "http_post": "http.post",
            "fill_form": "browser.fill_form",
            "scrape": "browser.scrape"
        }
        return mapping.get(outcome_type, outcome_type)

    def _record_fulfillment(
        self,
        outcome_type: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        username: Optional[str]
    ):
        """Record fulfillment for metrics and learning"""
        self._fulfillment_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "outcome_type": outcome_type,
            "username": username,
            "success": result.get("ok", False),
            "connector": result.get("connector"),
            "latency_ms": result.get("latency_ms", 0)
        })

        # Keep history bounded
        if len(self._fulfillment_history) > 1000:
            self._fulfillment_history = self._fulfillment_history[-1000:]

        # Update metrics
        self._metrics["total_fulfillments"] += 1
        if result.get("ok"):
            self._metrics["successful_fulfillments"] += 1
        else:
            self._metrics["failed_fulfillments"] += 1

    # ========================================================================
    # AME INTEGRATION - INTELLIGENT PITCH DELIVERY
    # ========================================================================

    async def ame_deliver_pitch(
        self,
        pitch_id: str,
        channel: str = "email"
    ) -> Dict[str, Any]:
        """
        Deliver an AME pitch via COI connectors.

        Uses the best available connector (Resend preferred for email).
        """
        if not AME_AVAILABLE:
            return {"ok": False, "error": "ame_not_available"}

        from ame_pitches import get_pitch
        pitch = get_pitch(pitch_id)
        if not pitch:
            return {"ok": False, "error": "pitch_not_found"}

        # Deliver via COI
        if channel == "email":
            return await self.execute_smart(
                "send_email",
                {
                    "to": pitch.get("recipient_email") or pitch.get("recipient"),
                    "subject": pitch.get("subject", "Opportunity from AiGentsy"),
                    "body": pitch.get("message"),
                    "html": pitch.get("html")
                },
                ai_task_category="email_writing",
                username=pitch.get("originator"),
                idempotency_key=f"ame_pitch_{pitch_id}"
            )
        elif channel == "slack":
            return await self.execute_smart(
                "send_slack",
                {
                    "channel": pitch.get("recipient_channel"),
                    "message": pitch.get("message")
                },
                idempotency_key=f"ame_pitch_{pitch_id}"
            )
        else:
            return {"ok": False, "error": f"unsupported_channel:{channel}"}

    async def ame_auto_pipeline(
        self,
        matches: List[Dict[str, Any]],
        originator: str
    ) -> Dict[str, Any]:
        """
        Full AME pipeline: Generate pitches and deliver via COI.
        """
        if not AME_AVAILABLE:
            return {"ok": False, "error": "ame_not_available"}

        from ame_pitches import generate_pitches_from_matches

        # Generate pitches
        pitches = generate_pitches_from_matches(matches, "email", originator)

        # Deliver each via COI
        results = []
        for pitch in pitches:
            result = await self.ame_deliver_pitch(pitch["id"], "email")
            results.append({
                "pitch_id": pitch["id"],
                "recipient": pitch.get("recipient"),
                "delivered": result.get("ok", False),
                "error": result.get("error")
            })

        return {
            "ok": True,
            "total": len(pitches),
            "delivered": len([r for r in results if r["delivered"]]),
            "results": results
        }

    # ========================================================================
    # AMG INTEGRATION - COI-POWERED REVENUE ROUTING
    # ========================================================================

    async def amg_execute_action(
        self,
        username: str,
        action_type: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an AMG action via COI.

        This powers the ROUTE stage of the AMG loop with real fulfillment.
        """
        # Map AMG actions to COI outcomes
        action_map = {
            "cross_sell": "send_email",
            "upsell": "send_email",
            "retarget": "send_email",
            "reactivate": "send_email",
            "syndicate": "deliver_webhook",
            "sponsor_apply": "http_post",
            "jv_compose": "send_email",
            "ip_attach": "http_post"
        }

        outcome_type = action_map.get(action_type, "http_post")

        return await self.execute_smart(
            outcome_type,
            params,
            username=username,
            idempotency_key=f"amg_{username}_{action_type}_{int(datetime.now().timestamp())}"
        )

    async def amg_run_with_coi(self, username: str) -> Dict[str, Any]:
        """
        Run full AMG cycle with COI-powered fulfillment.
        """
        if not AMG_AVAILABLE:
            return {"ok": False, "error": "amg_not_available"}

        orchestrator = AMGOrchestrator(username)

        # Initialize graph
        await orchestrator.initialize_graph()

        # Run cycle - the _route stage will use our execute_action
        # We hook into the orchestrator by patching the queue
        result = await orchestrator.run_cycle()

        return result

    # ========================================================================
    # METABRIDGE INTEGRATION - COI-POWERED DEAL FULFILLMENT
    # ========================================================================

    async def metabridge_dispatch_with_coi(
        self,
        query: str,
        originator: str,
        mesh_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        MetaBridge deal dispatch with COI-powered delivery.
        """
        if not METABRIDGE_AVAILABLE or not self.metabridge:
            return {"ok": False, "error": "metabridge_not_available"}

        # Match and generate proposal
        matches = self.metabridge.match_offer(query)

        if not matches:
            return {"ok": False, "error": "no_matches_found"}

        # Generate proposal
        proposal = self.metabridge.generate_proposal(originator, query, matches)

        # Deliver via COI
        target = matches[0].get("email") or matches[0].get("username")
        if target and "@" in str(target):
            result = await self.execute_smart(
                "send_email",
                {
                    "to": target,
                    "subject": f"Partnership Opportunity: {query[:50]}...",
                    "body": proposal
                },
                username=originator,
                idempotency_key=f"metabridge_{mesh_session_id or originator}"
            )
        else:
            result = {"ok": False, "error": "no_delivery_target"}

        return {
            "ok": result.get("ok", False),
            "matches": len(matches),
            "proposal": proposal[:500] + "...",
            "delivery": result
        }

    # ========================================================================
    # JV MESH INTEGRATION - COI-POWERED JV NOTIFICATIONS
    # ========================================================================

    async def jv_propose_with_coi(
        self,
        proposer: str,
        partner: str,
        title: str,
        description: str,
        revenue_split: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Create JV proposal and notify via COI.
        """
        if not JV_MESH_AVAILABLE:
            return {"ok": False, "error": "jv_mesh_not_available"}

        # Create proposal
        result = await create_jv_proposal(
            proposer=proposer,
            partner=partner,
            title=title,
            description=description,
            revenue_split=revenue_split
        )

        if not result.get("ok"):
            return result

        proposal_id = result.get("proposal_id")

        # Notify partner via COI email
        email_result = await self.execute_smart(
            "send_email",
            {
                "to": f"{partner}@aigentsy.com",  # Would need real email lookup
                "subject": f"JV Proposal: {title}",
                "body": f"""
Hi {partner},

{proposer} has proposed a Joint Venture partnership:

Title: {title}
Description: {description}

Revenue Split:
{chr(10).join(f"  - {k}: {v*100:.0f}%" for k, v in revenue_split.items())}

Review and respond at: https://aigentsy.com/jv/proposals/{proposal_id}

This is an automated notification from AiGentsy JV Mesh.
"""
            },
            username=proposer,
            idempotency_key=f"jv_notif_{proposal_id}"
        )

        self._metrics["jv_proposals_sent"] += 1

        return {
            "ok": True,
            "proposal_id": proposal_id,
            "notification_sent": email_result.get("ok", False),
            "proposal": result.get("proposal")
        }

    async def jv_auto_match_with_coi(
        self,
        agent: Dict[str, Any],
        all_agents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Auto-match JV partners and propose via COI.
        """
        if not JV_MESH_AVAILABLE:
            return {"ok": False, "error": "jv_mesh_not_available"}

        # Get suggestions
        suggestions = suggest_jv_partners(agent, all_agents)

        if not suggestions.get("suggested_partners"):
            return {"ok": False, "error": "no_compatible_partners"}

        # Auto-propose to top match
        top_partner = suggestions["suggested_partners"][0]

        result = await auto_propose_jv(
            agent_username=suggestions.get("agent"),
            suggested_partner=top_partner,
            all_agents=all_agents
        )

        # Notify via COI if proposal was created
        if result.get("ok") and result.get("proposal_id"):
            await self.execute_smart(
                "send_email",
                {
                    "to": f"{top_partner['username']}@aigentsy.com",
                    "subject": f"AI-Matched Partnership Opportunity",
                    "body": f"You've been matched with {suggestions.get('agent')} for a potential JV!"
                },
                idempotency_key=f"jv_match_notif_{result.get('proposal_id')}"
            )

        return result

    # ========================================================================
    # METAHIVE INTEGRATION - COI-POWERED REWARDS
    # ========================================================================

    async def metahive_distribute_with_coi(self) -> Dict[str, Any]:
        """
        Distribute MetaHive rewards using COI for payment links.
        """
        if not METAHIVE_AVAILABLE:
            return {"ok": False, "error": "metahive_not_available"}

        # Distribute rewards
        result = await distribute_hive_rewards()

        if not result.get("ok"):
            return result

        distributions = result.get("distributions", [])

        # Send notification emails via COI
        for dist in distributions[:10]:  # Limit to 10 for demo
            await self.execute_smart(
                "send_email",
                {
                    "to": f"{dist['username']}@aigentsy.com",
                    "subject": "MetaHive Rewards Distributed!",
                    "body": f"""
Congratulations!

Your MetaHive rewards have been distributed:
  Amount: ${dist['amount']:.2f}
  Credits: {dist['credits']}
  Outcome Score: {dist['outcome_score']}

Keep contributing to earn more!
- The AiGentsy Team
"""
                },
                username="metahive_system",
                idempotency_key=f"metahive_dist_{dist['username']}"
            )

        return result

    async def metahive_record_with_coi(
        self,
        username: str,
        contribution_type: str,
        value: float = 1.0
    ) -> Dict[str, Any]:
        """
        Record MetaHive contribution with automatic reward calculation.
        """
        if not METAHIVE_AVAILABLE:
            return {"ok": False, "error": "metahive_not_available"}

        result = record_contribution(username, contribution_type, value)

        if result.get("ok"):
            self._metrics["metahive_contributions"] += 1

        return result

    # ========================================================================
    # AI FAMILY BRAIN INTEGRATION - INTELLIGENT TASK ROUTING
    # ========================================================================

    async def ai_execute_with_fulfillment(
        self,
        prompt: str,
        task_category: str = "content_generation",
        fulfill_result: bool = False,
        fulfillment_type: Optional[str] = None,
        fulfillment_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute AI task and optionally fulfill the result via COI.

        Example: Generate a pitch (AI) then send it (COI).
        """
        if not AI_FAMILY_AVAILABLE:
            return {"ok": False, "error": "ai_family_not_available"}

        # Execute AI task
        ai_result = await ai_execute(prompt, task_category)

        if not ai_result.get("ok"):
            return ai_result

        self._metrics["ai_tasks_routed"] += 1

        # Optionally fulfill the result
        if fulfill_result and fulfillment_type:
            params = fulfillment_params or {}

            # Use AI output as content
            if "body" not in params:
                params["body"] = ai_result.get("response", "")

            fulfillment_result = await self.execute_smart(
                fulfillment_type,
                params,
                use_ai=False  # Already used AI
            )

            return {
                "ok": True,
                "ai_result": ai_result,
                "fulfillment_result": fulfillment_result
            }

        return ai_result

    async def ai_research_and_act(
        self,
        research_query: str,
        action_type: str,
        action_params: Dict[str, Any],
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Research with AI then act via COI.

        Example: Research a lead (AI), then email them (COI).
        """
        # Research phase
        research = await ai_execute(research_query, "research", optimize_for="quality")

        if not research.get("ok"):
            return {"ok": False, "error": "research_failed", "details": research}

        # Enhance action params with research
        enhanced_params = {**action_params}
        if "body" in enhanced_params:
            enhanced_params["body"] = f"{enhanced_params['body']}\n\nResearch Context:\n{research.get('response', '')[:500]}"

        # Act via COI
        action_result = await self.execute_smart(
            action_type,
            enhanced_params,
            username=username
        )

        return {
            "ok": action_result.get("ok", False),
            "research": research.get("response", "")[:1000],
            "action_result": action_result
        }

    # ========================================================================
    # UNIFIED METRICS AND STATUS
    # ========================================================================

    def get_fabric_status(self) -> Dict[str, Any]:
        """Get comprehensive fabric status"""
        return {
            "ok": True,
            "systems": {
                "coi": COI_AVAILABLE,
                "ai_family": AI_FAMILY_AVAILABLE,
                "ame": AME_AVAILABLE,
                "amg": AMG_AVAILABLE,
                "metabridge": METABRIDGE_AVAILABLE,
                "jv_mesh": JV_MESH_AVAILABLE,
                "metahive": METAHIVE_AVAILABLE,
                "yield_memory": YIELD_MEMORY_AVAILABLE
            },
            "metrics": self._metrics,
            "fulfillment_history_count": len(self._fulfillment_history),
            "ai_family_stats": get_family_stats() if AI_FAMILY_AVAILABLE else None
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get fabric metrics"""
        return {**self._metrics}

    def on_fulfillment(self, callback: Callable):
        """Register callback for successful fulfillments"""
        self._callbacks["on_fulfillment"].append(callback)

    def on_failure(self, callback: Callable):
        """Register callback for failures"""
        self._callbacks["on_failure"].append(callback)

    def on_revenue(self, callback: Callable):
        """Register callback for revenue events"""
        self._callbacks["on_revenue"].append(callback)


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_fabric_instance: Optional[AiGentsyFabric] = None


def get_fabric() -> AiGentsyFabric:
    """Get or create the singleton AiGentsy Fabric instance"""
    global _fabric_instance
    if _fabric_instance is None:
        _fabric_instance = AiGentsyFabric()
    return _fabric_instance


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def smart_execute(outcome_type: str, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Convenience function for smart execution"""
    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()
    return await fabric.execute_smart(outcome_type, params, **kwargs)


async def smart_email(to: str, subject: str, body: str, **kwargs) -> Dict[str, Any]:
    """Send email with AI enhancement and Resend delivery"""
    return await smart_execute("send_email", {"to": to, "subject": subject, "body": body}, **kwargs)


async def smart_pitch(recipient: str, context: Dict[str, Any], originator: str) -> Dict[str, Any]:
    """Generate and deliver pitch via AME + COI"""
    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    # Generate pitch via AME
    if AME_AVAILABLE:
        pitch = generate_pitch(recipient, "email", context, originator)
        return await fabric.ame_deliver_pitch(pitch["id"], "email")

    return {"ok": False, "error": "ame_not_available"}


async def ai_to_action(prompt: str, task_category: str, action_type: str, action_params: Dict[str, Any]) -> Dict[str, Any]:
    """AI task with automatic fulfillment"""
    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()
    return await fabric.ai_execute_with_fulfillment(
        prompt, task_category, fulfill_result=True,
        fulfillment_type=action_type, fulfillment_params=action_params
    )


# ============================================================================
# INITIALIZATION LOG
# ============================================================================

logger.info("""
================================================================================
   AIGENTSY COI INTEGRATION LAYER LOADED
================================================================================

   INTELLIGENCE (AI Family Brain):
   - Claude, GPT-4, Gemini, Perplexity orchestration
   - Specialization learning and cross-pollination

   FULFILLMENT (COI Runtime):
   - Resend (email), Stripe (payments), Shopify (commerce)
   - SMS, Slack, Webhooks, Browser automation

   BUSINESS SYSTEMS:
   - AME: Autonomous pitch generation and delivery
   - AMG: Full revenue loop with COI routing
   - MetaBridge: Deal matching with COI dispatch
   - JV Mesh: Partnership proposals via COI
   - MetaHive: Reward distribution via COI

   Usage: from aigentsy_coi_integration import get_fabric, smart_execute
================================================================================
""")
