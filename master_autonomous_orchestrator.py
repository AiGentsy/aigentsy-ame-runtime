"""
MASTER AUTONOMOUS ORCHESTRATOR
═══════════════════════════════════════════════════════════════════════════════

COMPLETE END-TO-END AUTONOMOUS REVENUE SYSTEM

Orchestrates ALL 1000+ endpoints across the entire pipeline:

1. DISCOVERY (7 Dimensions)
   - Explicit Marketplaces: GitHub, Upwork, Fiverr, Freelancer, etc.
   - Pain Point Detection: Reddit, HackerNews, Twitter, ProductHunt
   - Flow Arbitrage: Pricing inefficiencies, arbitrage opportunities
   - Predictive Intelligence: Trend analysis, demand forecasting
   - Network Amplification: Referrals, viral loops, word-of-mouth
   - Opportunity Creation: Proactive outreach, cold pitching
   - Emergent Patterns: New market detection, trend surfing

2. COMMUNICATION (Multi-Channel)
   - Email: Postmark, SendGrid
   - DM: Twitter, LinkedIn, Platform messages
   - SMS: Twilio
   - Platform: GitHub comments, Reddit replies, HN

3. CONTRACT & AGREEMENT
   - Contract generation
   - Digital signatures (DocuSign/HelloSign)
   - Deposit collection
   - Milestone tracking

4. FULFILLMENT
   - Code generation (Claude, GPT-4)
   - Content creation
   - Graphics generation (Stable Diffusion, DALL-E)
   - Audio/Video generation
   - Deployment automation

5. PAYMENT COLLECTION
   - Stripe invoices & payment links
   - Escrow release requests
   - Platform payout tracking
   - Subscription management

Updated: Jan 2026
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import asyncio
import os

# ═══════════════════════════════════════════════════════════════════════════════
# HTTP CLIENT FOR INTERNAL API CALLS
# ═══════════════════════════════════════════════════════════════════════════════

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class MasterAutonomousOrchestrator:
    """
    The brain that orchestrates ALL autonomous operations.

    Runs the complete pipeline from discovery to payment collection
    with zero human intervention.
    """

    def __init__(self, backend_url: str = None):
        self.backend_url = backend_url or BACKEND_URL
        self.client = httpx.AsyncClient(timeout=300) if HTTPX_AVAILABLE else None

        # Track execution state
        self.current_run = {
            "started_at": None,
            "phase": None,
            "results": {},
            "errors": []
        }

    async def _call(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make internal API call"""
        if not self.client:
            return {"ok": False, "error": "httpx not available"}

        url = f"{self.backend_url}{endpoint}"
        try:
            if method == "GET":
                response = await self.client.get(url, params=data)
            else:
                response = await self.client.post(url, json=data or {})

            if response.status_code == 200:
                return response.json()
            else:
                return {"ok": False, "error": f"HTTP {response.status_code}", "body": response.text[:500]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 1: DISCOVERY - ALL 7 DIMENSIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_discovery_all_dimensions(self) -> Dict[str, Any]:
        """
        Run discovery across ALL 7 dimensions simultaneously.

        Returns opportunities from 27+ platforms.
        """
        self.current_run["phase"] = "discovery"

        results = {
            "dimension_1_explicit_marketplaces": [],
            "dimension_2_pain_point_detection": [],
            "dimension_3_flow_arbitrage": [],
            "dimension_4_predictive_intelligence": [],
            "dimension_5_network_amplification": [],
            "dimension_6_opportunity_creation": [],
            "dimension_7_emergent_patterns": [],
            "total_opportunities": 0,
            "total_value": 0
        }

        # Run all dimension discoveries in parallel
        discovery_tasks = [
            self._discover_dimension_1_explicit_marketplaces(),
            self._discover_dimension_2_pain_points(),
            self._discover_dimension_3_flow_arbitrage(),
            self._discover_dimension_4_predictive(),
            self._discover_dimension_5_network(),
            self._discover_dimension_6_opportunity_creation(),
            self._discover_dimension_7_emergent()
        ]

        dimension_results = await asyncio.gather(*discovery_tasks, return_exceptions=True)

        dimension_names = [
            "dimension_1_explicit_marketplaces",
            "dimension_2_pain_point_detection",
            "dimension_3_flow_arbitrage",
            "dimension_4_predictive_intelligence",
            "dimension_5_network_amplification",
            "dimension_6_opportunity_creation",
            "dimension_7_emergent_patterns"
        ]

        for i, (name, result) in enumerate(zip(dimension_names, dimension_results)):
            if isinstance(result, Exception):
                self.current_run["errors"].append({"dimension": name, "error": str(result)})
            else:
                results[name] = result.get("opportunities", [])
                results["total_opportunities"] += len(results[name])
                results["total_value"] += sum(o.get("value", 0) for o in results[name])

        self.current_run["results"]["discovery"] = results
        return results

    async def _discover_dimension_1_explicit_marketplaces(self) -> Dict[str, Any]:
        """Dimension 1: Explicit Marketplaces (GitHub, Upwork, Fiverr, etc.)"""
        opportunities = []

        # GitHub bounties
        github = await self._call("POST", "/discovery/github/bounties", {"limit": 50})
        if github.get("ok"):
            opportunities.extend(github.get("opportunities", []))

        # Upwork jobs
        upwork = await self._call("POST", "/discovery/upwork/search", {"limit": 30})
        if upwork.get("ok"):
            opportunities.extend(upwork.get("opportunities", []))

        # Fiverr requests
        fiverr = await self._call("POST", "/discovery/fiverr/buyer-requests", {"limit": 20})
        if fiverr.get("ok"):
            opportunities.extend(fiverr.get("opportunities", []))

        # Freelancer projects
        freelancer = await self._call("POST", "/discovery/freelancer/search", {"limit": 30})
        if freelancer.get("ok"):
            opportunities.extend(freelancer.get("opportunities", []))

        # TopTal
        toptal = await self._call("POST", "/discovery/toptal/jobs", {"limit": 20})
        if toptal.get("ok"):
            opportunities.extend(toptal.get("opportunities", []))

        # RemoteOK
        remoteok = await self._call("GET", "/discovery/remoteok/jobs")
        if remoteok.get("ok"):
            opportunities.extend(remoteok.get("opportunities", []))

        # WeWorkRemotely
        wwr = await self._call("GET", "/discovery/weworkremotely/jobs")
        if wwr.get("ok"):
            opportunities.extend(wwr.get("opportunities", []))

        # AngelList/Wellfound
        angellist = await self._call("GET", "/discovery/angellist/jobs")
        if angellist.get("ok"):
            opportunities.extend(angellist.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "explicit_marketplaces"}

    async def _discover_dimension_2_pain_points(self) -> Dict[str, Any]:
        """Dimension 2: Pain Point Detection (Reddit, HN, Twitter)"""
        opportunities = []

        # Reddit pain points
        reddit = await self._call("POST", "/discovery/reddit/pain-points", {
            "subreddits": ["webdev", "startups", "entrepreneur", "SaaS", "freelance"],
            "limit": 50
        })
        if reddit.get("ok"):
            opportunities.extend(reddit.get("opportunities", []))

        # HackerNews hiring/seeking
        hn = await self._call("GET", "/discovery/hackernews/who-is-hiring")
        if hn.get("ok"):
            opportunities.extend(hn.get("opportunities", []))

        # Twitter pain signals
        twitter = await self._call("POST", "/discovery/twitter/pain-signals", {
            "keywords": ["need developer", "looking for", "anyone know", "help with"],
            "limit": 30
        })
        if twitter.get("ok"):
            opportunities.extend(twitter.get("opportunities", []))

        # ProductHunt launches needing help
        ph = await self._call("GET", "/discovery/producthunt/launches")
        if ph.get("ok"):
            opportunities.extend(ph.get("opportunities", []))

        # IndieHackers requests
        ih = await self._call("GET", "/discovery/indiehackers/requests")
        if ih.get("ok"):
            opportunities.extend(ih.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "pain_point_detection"}

    async def _discover_dimension_3_flow_arbitrage(self) -> Dict[str, Any]:
        """Dimension 3: Flow Arbitrage (pricing inefficiencies)"""
        opportunities = []

        # Price arbitrage detection
        arb = await self._call("GET", "/discovery/arbitrage/detect")
        if arb.get("ok"):
            opportunities.extend(arb.get("opportunities", []))

        # Cross-platform price differences
        cross = await self._call("GET", "/discovery/arbitrage/cross-platform")
        if cross.get("ok"):
            opportunities.extend(cross.get("opportunities", []))

        # Underpriced gigs
        underpriced = await self._call("GET", "/discovery/arbitrage/underpriced")
        if underpriced.get("ok"):
            opportunities.extend(underpriced.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "flow_arbitrage"}

    async def _discover_dimension_4_predictive(self) -> Dict[str, Any]:
        """Dimension 4: Predictive Intelligence (trend forecasting)"""
        opportunities = []

        # Trend analysis
        trends = await self._call("GET", "/discovery/predictive/trends")
        if trends.get("ok"):
            opportunities.extend(trends.get("opportunities", []))

        # Demand forecasting
        demand = await self._call("GET", "/discovery/predictive/demand-forecast")
        if demand.get("ok"):
            opportunities.extend(demand.get("opportunities", []))

        # Seasonal patterns
        seasonal = await self._call("GET", "/discovery/predictive/seasonal")
        if seasonal.get("ok"):
            opportunities.extend(seasonal.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "predictive_intelligence"}

    async def _discover_dimension_5_network(self) -> Dict[str, Any]:
        """Dimension 5: Network Amplification (referrals, viral)"""
        opportunities = []

        # Referral opportunities
        referrals = await self._call("GET", "/discovery/network/referrals")
        if referrals.get("ok"):
            opportunities.extend(referrals.get("opportunities", []))

        # Viral loop detection
        viral = await self._call("GET", "/discovery/network/viral-loops")
        if viral.get("ok"):
            opportunities.extend(viral.get("opportunities", []))

        # Partnership opportunities
        partners = await self._call("GET", "/discovery/network/partnerships")
        if partners.get("ok"):
            opportunities.extend(partners.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "network_amplification"}

    async def _discover_dimension_6_opportunity_creation(self) -> Dict[str, Any]:
        """Dimension 6: Opportunity Creation (proactive outreach)"""
        opportunities = []

        # Cold outreach targets
        cold = await self._call("POST", "/discovery/outreach/targets", {"limit": 50})
        if cold.get("ok"):
            opportunities.extend(cold.get("opportunities", []))

        # LinkedIn prospects
        linkedin = await self._call("POST", "/discovery/linkedin/prospects", {"limit": 30})
        if linkedin.get("ok"):
            opportunities.extend(linkedin.get("opportunities", []))

        # Email list opportunities
        email_opps = await self._call("GET", "/discovery/email/opportunities")
        if email_opps.get("ok"):
            opportunities.extend(email_opps.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "opportunity_creation"}

    async def _discover_dimension_7_emergent(self) -> Dict[str, Any]:
        """Dimension 7: Emergent Patterns (new markets, trends)"""
        opportunities = []

        # New market detection
        new_markets = await self._call("GET", "/discovery/emergent/new-markets")
        if new_markets.get("ok"):
            opportunities.extend(new_markets.get("opportunities", []))

        # Trend surfing
        trend_surf = await self._call("GET", "/discovery/emergent/trend-surf")
        if trend_surf.get("ok"):
            opportunities.extend(trend_surf.get("opportunities", []))

        # Technology shifts
        tech_shifts = await self._call("GET", "/discovery/emergent/tech-shifts")
        if tech_shifts.get("ok"):
            opportunities.extend(tech_shifts.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "emergent_patterns"}

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 2: MULTI-CHANNEL COMMUNICATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_communication_all_channels(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """
        Initiate communication across ALL channels for discovered opportunities.

        Channels:
        - Email (Postmark/SendGrid)
        - DM (Twitter, LinkedIn, Platform)
        - SMS (Twilio)
        - Platform comments (GitHub, Reddit, HN)
        """
        self.current_run["phase"] = "communication"

        results = {
            "emails_sent": 0,
            "dms_sent": 0,
            "sms_sent": 0,
            "platform_messages": 0,
            "conversations_started": [],
            "errors": []
        }

        for opp in opportunities:
            platform = opp.get("platform", "unknown")
            contact = opp.get("contact", {})

            try:
                # Determine best communication channel
                if contact.get("email"):
                    # Send email
                    email_result = await self._send_email_outreach(opp)
                    if email_result.get("ok"):
                        results["emails_sent"] += 1
                        results["conversations_started"].append({
                            "opportunity_id": opp.get("id"),
                            "channel": "email",
                            "status": "sent"
                        })

                if contact.get("twitter"):
                    # Send Twitter DM
                    dm_result = await self._send_twitter_dm(opp)
                    if dm_result.get("ok"):
                        results["dms_sent"] += 1

                if contact.get("linkedin"):
                    # Send LinkedIn message
                    li_result = await self._send_linkedin_message(opp)
                    if li_result.get("ok"):
                        results["dms_sent"] += 1

                if contact.get("phone"):
                    # Send SMS
                    sms_result = await self._send_sms(opp)
                    if sms_result.get("ok"):
                        results["sms_sent"] += 1

                # Platform-specific messaging
                if platform in ["github", "github_bounties"]:
                    msg_result = await self._post_github_comment(opp)
                    if msg_result.get("ok"):
                        results["platform_messages"] += 1

                elif platform == "reddit":
                    msg_result = await self._post_reddit_reply(opp)
                    if msg_result.get("ok"):
                        results["platform_messages"] += 1

                elif platform in ["upwork", "freelancer", "fiverr"]:
                    msg_result = await self._send_platform_proposal(opp)
                    if msg_result.get("ok"):
                        results["platform_messages"] += 1

            except Exception as e:
                results["errors"].append({
                    "opportunity_id": opp.get("id"),
                    "error": str(e)
                })

        self.current_run["results"]["communication"] = results
        return results

    async def _send_email_outreach(self, opportunity: Dict) -> Dict[str, Any]:
        """Send outreach email via Postmark/SendGrid"""
        contact = opportunity.get("contact", {})
        email = contact.get("email")

        if not email:
            return {"ok": False, "error": "No email"}

        # Generate personalized pitch
        pitch = await self._call("POST", "/ame/generate-pitch", {
            "opportunity": opportunity,
            "channel": "email"
        })

        # Send via email service
        return await self._call("POST", "/email/send", {
            "to": email,
            "subject": pitch.get("subject", f"Re: {opportunity.get('title', 'Your Project')}"),
            "body": pitch.get("body", ""),
            "opportunity_id": opportunity.get("id")
        })

    async def _send_twitter_dm(self, opportunity: Dict) -> Dict[str, Any]:
        """Send Twitter DM"""
        contact = opportunity.get("contact", {})
        twitter = contact.get("twitter")

        if not twitter:
            return {"ok": False, "error": "No Twitter handle"}

        pitch = await self._call("POST", "/ame/generate-pitch", {
            "opportunity": opportunity,
            "channel": "twitter_dm",
            "max_length": 280
        })

        return await self._call("POST", "/twitter/send-dm", {
            "username": twitter,
            "message": pitch.get("body", ""),
            "opportunity_id": opportunity.get("id")
        })

    async def _send_linkedin_message(self, opportunity: Dict) -> Dict[str, Any]:
        """Send LinkedIn message"""
        contact = opportunity.get("contact", {})
        linkedin = contact.get("linkedin")

        if not linkedin:
            return {"ok": False, "error": "No LinkedIn profile"}

        pitch = await self._call("POST", "/ame/generate-pitch", {
            "opportunity": opportunity,
            "channel": "linkedin"
        })

        return await self._call("POST", "/linkedin/send-message", {
            "profile_url": linkedin,
            "message": pitch.get("body", ""),
            "opportunity_id": opportunity.get("id")
        })

    async def _send_sms(self, opportunity: Dict) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        contact = opportunity.get("contact", {})
        phone = contact.get("phone")

        if not phone:
            return {"ok": False, "error": "No phone number"}

        pitch = await self._call("POST", "/ame/generate-pitch", {
            "opportunity": opportunity,
            "channel": "sms",
            "max_length": 160
        })

        return await self._call("POST", "/sms/send", {
            "to": phone,
            "message": pitch.get("body", ""),
            "opportunity_id": opportunity.get("id")
        })

    async def _post_github_comment(self, opportunity: Dict) -> Dict[str, Any]:
        """Post GitHub comment expressing interest"""
        return await self._call("POST", "/github/post-comment", {
            "url": opportunity.get("url"),
            "type": "interest",
            "opportunity_id": opportunity.get("id")
        })

    async def _post_reddit_reply(self, opportunity: Dict) -> Dict[str, Any]:
        """Post Reddit reply"""
        return await self._call("POST", "/reddit/post-reply", {
            "url": opportunity.get("url"),
            "type": "offer_help",
            "opportunity_id": opportunity.get("id")
        })

    async def _send_platform_proposal(self, opportunity: Dict) -> Dict[str, Any]:
        """Send proposal on freelance platform"""
        platform = opportunity.get("platform")

        pitch = await self._call("POST", "/ame/generate-pitch", {
            "opportunity": opportunity,
            "channel": platform
        })

        return await self._call("POST", f"/{platform}/submit-proposal", {
            "job_id": opportunity.get("job_id") or opportunity.get("id"),
            "proposal": pitch.get("body", ""),
            "bid_amount": opportunity.get("suggested_bid", opportunity.get("value", 0) * 0.8)
        })

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 3: CONTRACT & AGREEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_contract_flow(self, conversations: List[Dict]) -> Dict[str, Any]:
        """
        Handle contract and agreement flow for interested clients.

        - Generate contracts
        - Send for signature
        - Collect deposits
        - Track milestones
        """
        self.current_run["phase"] = "contract"

        results = {
            "contracts_generated": 0,
            "contracts_sent": 0,
            "deposits_requested": 0,
            "deposits_collected": 0,
            "total_contract_value": 0,
            "contracts": [],
            "errors": []
        }

        for conv in conversations:
            if conv.get("status") != "client_interested":
                continue

            try:
                opportunity = conv.get("opportunity", {})

                # Generate contract
                contract = await self._call("POST", "/contract/generate", {
                    "opportunity": opportunity,
                    "client_email": conv.get("client_email"),
                    "amount": opportunity.get("value", 0),
                    "milestones": self._generate_milestones(opportunity)
                })

                if contract.get("ok"):
                    results["contracts_generated"] += 1
                    contract_id = contract.get("contract_id")

                    # Create Stripe payment link for deposit
                    deposit_amount = opportunity.get("value", 0) * 0.5  # 50% deposit
                    payment_link = await self._call("POST", "/contract/create-payment-link", {
                        "contract_id": contract_id,
                        "amount": deposit_amount
                    })

                    if payment_link.get("ok"):
                        results["deposits_requested"] += 1

                    # Send contract with payment link
                    send_result = await self._call("POST", "/contract/send", {
                        "contract_id": contract_id,
                        "include_payment_link": True
                    })

                    if send_result.get("ok"):
                        results["contracts_sent"] += 1
                        results["total_contract_value"] += opportunity.get("value", 0)

                        results["contracts"].append({
                            "contract_id": contract_id,
                            "opportunity_id": opportunity.get("id"),
                            "value": opportunity.get("value", 0),
                            "deposit": deposit_amount,
                            "payment_link": payment_link.get("payment_link")
                        })

            except Exception as e:
                results["errors"].append({
                    "conversation_id": conv.get("id"),
                    "error": str(e)
                })

        self.current_run["results"]["contract"] = results
        return results

    def _generate_milestones(self, opportunity: Dict) -> List[Dict]:
        """Generate milestone structure based on opportunity type"""
        value = opportunity.get("value", 0)
        opp_type = opportunity.get("type", "general")

        if opp_type in ["code_generation", "software_development"]:
            return [
                {"name": "Initial Setup & Architecture", "percentage": 20},
                {"name": "Core Development", "percentage": 40},
                {"name": "Testing & Refinement", "percentage": 25},
                {"name": "Deployment & Handoff", "percentage": 15}
            ]
        elif opp_type in ["content_generation", "writing"]:
            return [
                {"name": "Research & Outline", "percentage": 25},
                {"name": "First Draft", "percentage": 50},
                {"name": "Revisions & Final", "percentage": 25}
            ]
        else:
            return [
                {"name": "Deposit", "percentage": 50},
                {"name": "Final Delivery", "percentage": 50}
            ]

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 4: FULFILLMENT & DELIVERY
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_fulfillment(self, contracts: List[Dict]) -> Dict[str, Any]:
        """
        Execute fulfillment for signed contracts.

        - Code generation
        - Content creation
        - Graphics generation
        - Deployment
        """
        self.current_run["phase"] = "fulfillment"

        results = {
            "fulfilled": 0,
            "delivered": 0,
            "total_delivered_value": 0,
            "fulfillments": [],
            "errors": []
        }

        for contract in contracts:
            if contract.get("status") not in ["signed", "deposit_paid"]:
                continue

            try:
                opportunity = contract.get("opportunity", {})
                contract_id = contract.get("contract_id")

                # Determine fulfillment type and execute
                fulfillment_result = await self._execute_fulfillment(opportunity)

                if fulfillment_result.get("success"):
                    results["fulfilled"] += 1

                    # Deliver work
                    delivery_result = await self._deliver_work(opportunity, fulfillment_result)

                    if delivery_result.get("success"):
                        results["delivered"] += 1
                        results["total_delivered_value"] += opportunity.get("value", 0)

                        # Create payment request for remaining balance
                        remaining = opportunity.get("value", 0) * 0.5  # 50% on delivery
                        payment_result = await self._call("POST", "/wade/payment-link", {
                            "amount": remaining,
                            "description": f"Final payment: {opportunity.get('title', 'Work')}",
                            "workflow_id": contract_id
                        })

                        results["fulfillments"].append({
                            "contract_id": contract_id,
                            "opportunity_id": opportunity.get("id"),
                            "delivery_url": delivery_result.get("delivery_url"),
                            "payment_link": payment_result.get("payment_link"),
                            "value": opportunity.get("value", 0)
                        })

            except Exception as e:
                results["errors"].append({
                    "contract_id": contract.get("contract_id"),
                    "error": str(e)
                })

        self.current_run["results"]["fulfillment"] = results
        return results

    async def _execute_fulfillment(self, opportunity: Dict) -> Dict[str, Any]:
        """Execute the actual work based on opportunity type"""
        opp_type = opportunity.get("type", "general")

        if opp_type in ["code_generation", "software_development"]:
            return await self._call("POST", "/fulfillment/code-generation", {
                "opportunity": opportunity
            })

        elif opp_type in ["content_generation", "writing", "copywriting"]:
            return await self._call("POST", "/fulfillment/content-generation", {
                "opportunity": opportunity
            })

        elif opp_type in ["graphics", "design", "logo"]:
            return await self._call("POST", "/fulfillment/graphics-generation", {
                "opportunity": opportunity
            })

        elif opp_type in ["video", "animation"]:
            return await self._call("POST", "/fulfillment/video-generation", {
                "opportunity": opportunity
            })

        elif opp_type in ["audio", "music", "voiceover"]:
            return await self._call("POST", "/fulfillment/audio-generation", {
                "opportunity": opportunity
            })

        else:
            # Generic Claude-based fulfillment
            return await self._call("POST", "/fulfillment/claude-generic", {
                "opportunity": opportunity
            })

    async def _deliver_work(self, opportunity: Dict, fulfillment: Dict) -> Dict[str, Any]:
        """Deliver completed work to client/platform"""
        platform = opportunity.get("platform", "unknown")

        # Platform-specific delivery
        if platform in ["github", "github_bounties"]:
            return await self._call("POST", "/delivery/github", {
                "opportunity": opportunity,
                "fulfillment": fulfillment
            })

        elif platform in ["upwork", "freelancer", "fiverr"]:
            return await self._call("POST", f"/delivery/{platform}", {
                "opportunity": opportunity,
                "fulfillment": fulfillment
            })

        else:
            # Email delivery
            return await self._call("POST", "/delivery/email", {
                "opportunity": opportunity,
                "fulfillment": fulfillment
            })

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 5: PAYMENT COLLECTION
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_payment_collection(self) -> Dict[str, Any]:
        """
        Collect all pending payments across platforms.

        - Send Stripe invoices
        - Request escrow releases
        - Track bounty payouts
        - Process subscriptions
        """
        self.current_run["phase"] = "payment_collection"

        results = {
            "invoices_sent": 0,
            "payment_links_created": 0,
            "escrow_releases_requested": 0,
            "bounties_claimed": 0,
            "total_collected": 0,
            "total_pending": 0,
            "collections": [],
            "errors": []
        }

        # Send all pending invoices
        invoices = await self._call("POST", "/stripe/send-invoices", {})
        if invoices.get("ok"):
            results["invoices_sent"] = len(invoices.get("invoiced", []))

        # Request escrow releases
        escrow = await self._call("POST", "/escrow/auto-release", {})
        if escrow.get("ok"):
            results["escrow_releases_requested"] = escrow.get("requested", 0)

        # Claim bounties
        bounties = await self._call("POST", "/bounties/claim-all", {})
        if bounties.get("ok"):
            results["bounties_claimed"] = bounties.get("claimed", 0)

        # Process subscription renewals
        subs = await self._call("POST", "/subscriptions/process-renewals", {})
        if subs.get("ok"):
            results["total_collected"] += subs.get("collected", 0)

        # Get current payment status
        status = await self._call("GET", "/payments/status")
        if status.get("ok"):
            results["total_pending"] = status.get("summary", {}).get("total_pending", 0)

        # Batch payouts
        payouts = await self._call("POST", "/stripe/batch-payouts", {})
        if payouts.get("ok"):
            results["total_collected"] += payouts.get("paid_out", 0)

        self.current_run["results"]["payment_collection"] = results
        return results

    # ═══════════════════════════════════════════════════════════════════════════
    # MASTER ORCHESTRATION - RUN COMPLETE AUTONOMOUS LOOP
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_full_autonomous_cycle(self, config: Dict = None) -> Dict[str, Any]:
        """
        RUN THE COMPLETE AUTONOMOUS CYCLE

        Discovery → Communication → Contract → Fulfillment → Payment

        Zero human intervention required.
        """
        config = config or {}

        self.current_run = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "phase": "initializing",
            "results": {},
            "errors": []
        }

        final_results = {
            "ok": True,
            "started_at": self.current_run["started_at"],
            "phases_completed": [],
            "summary": {}
        }

        try:
            # PHASE 1: DISCOVERY
            print("🔍 Phase 1: Discovery across all 7 dimensions...")
            discovery = await self.run_discovery_all_dimensions()
            final_results["phases_completed"].append("discovery")
            final_results["discovery"] = {
                "total_opportunities": discovery["total_opportunities"],
                "total_value": discovery["total_value"],
                "by_dimension": {
                    k: len(v) for k, v in discovery.items()
                    if k.startswith("dimension_")
                }
            }

            # Collect all opportunities
            all_opportunities = []
            for k, v in discovery.items():
                if k.startswith("dimension_") and isinstance(v, list):
                    all_opportunities.extend(v)

            # PHASE 2: COMMUNICATION
            if all_opportunities:
                print(f"💬 Phase 2: Initiating communication for {len(all_opportunities)} opportunities...")
                communication = await self.run_communication_all_channels(all_opportunities)
                final_results["phases_completed"].append("communication")
                final_results["communication"] = {
                    "emails_sent": communication["emails_sent"],
                    "dms_sent": communication["dms_sent"],
                    "sms_sent": communication["sms_sent"],
                    "platform_messages": communication["platform_messages"],
                    "conversations_started": len(communication["conversations_started"])
                }

                # PHASE 3: CONTRACT
                interested = [c for c in communication["conversations_started"] if c.get("status") == "client_interested"]
                if interested:
                    print(f"📝 Phase 3: Generating contracts for {len(interested)} interested clients...")
                    contracts = await self.run_contract_flow(interested)
                    final_results["phases_completed"].append("contract")
                    final_results["contract"] = {
                        "contracts_generated": contracts["contracts_generated"],
                        "contracts_sent": contracts["contracts_sent"],
                        "deposits_requested": contracts["deposits_requested"],
                        "total_contract_value": contracts["total_contract_value"]
                    }

                    # PHASE 4: FULFILLMENT
                    signed = [c for c in contracts["contracts"] if c.get("status") in ["signed", "deposit_paid"]]
                    if signed:
                        print(f"🔨 Phase 4: Executing fulfillment for {len(signed)} signed contracts...")
                        fulfillment = await self.run_fulfillment(signed)
                        final_results["phases_completed"].append("fulfillment")
                        final_results["fulfillment"] = {
                            "fulfilled": fulfillment["fulfilled"],
                            "delivered": fulfillment["delivered"],
                            "total_delivered_value": fulfillment["total_delivered_value"]
                        }

            # PHASE 5: PAYMENT COLLECTION (always run)
            print("💰 Phase 5: Collecting all pending payments...")
            payment = await self.run_payment_collection()
            final_results["phases_completed"].append("payment_collection")
            final_results["payment_collection"] = {
                "invoices_sent": payment["invoices_sent"],
                "escrow_releases_requested": payment["escrow_releases_requested"],
                "bounties_claimed": payment["bounties_claimed"],
                "total_collected": payment["total_collected"],
                "total_pending": payment["total_pending"]
            }

            # SUMMARY
            final_results["summary"] = {
                "opportunities_found": discovery["total_opportunities"],
                "communications_sent": (
                    final_results.get("communication", {}).get("emails_sent", 0) +
                    final_results.get("communication", {}).get("dms_sent", 0) +
                    final_results.get("communication", {}).get("sms_sent", 0) +
                    final_results.get("communication", {}).get("platform_messages", 0)
                ),
                "contracts_value": final_results.get("contract", {}).get("total_contract_value", 0),
                "delivered_value": final_results.get("fulfillment", {}).get("total_delivered_value", 0),
                "collected": payment["total_collected"],
                "pending": payment["total_pending"]
            }

            final_results["completed_at"] = datetime.now(timezone.utc).isoformat()
            final_results["errors"] = self.current_run["errors"]

        except Exception as e:
            final_results["ok"] = False
            final_results["error"] = str(e)
            final_results["errors"] = self.current_run["errors"]

        return final_results


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_orchestrator_instance = None

def get_master_orchestrator() -> MasterAutonomousOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MasterAutonomousOrchestrator()
    return _orchestrator_instance
