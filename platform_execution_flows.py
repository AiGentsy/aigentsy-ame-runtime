"""
PLATFORM EXECUTION FLOWS - Polymorphic Monetization
═══════════════════════════════════════════════════════════════════════════════

Each platform monetizes in its NATIVE way, not forced through one-size-fits-all.

EXECUTION MODES:
- immediate: Execute directly without communication (GitHub bounties)
- conversational: Build relationship first (LinkedIn leads)
- application_based: Submit application, await approval (Twitter sponsored)
- proposal_based: Submit proposal, await hire (Upwork/Fiverr)
- arbitrage: Source/list/fulfill product flow (Shopify)
- content_posting: Post content with monetization (Instagram affiliate)
- payment_collection: Direct payment flow (Stripe invoices)
- manual_review: Queue for human review (APIs not configured)

This module:
1. Checks which APIs are configured (from v115 fabric)
2. Returns the appropriate execution flow for each opportunity
3. Specifies what steps, approvals, and communication are needed
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class ExecutionMode(Enum):
    """Execution modes for different platform types"""
    IMMEDIATE = "immediate"           # Execute now (GitHub bounties)
    CONVERSATIONAL = "conversational" # Build relationship (LinkedIn)
    APPLICATION_BASED = "application_based"  # Apply → approval → execute
    PROPOSAL_BASED = "proposal_based"        # Submit proposal → hire → execute
    ARBITRAGE = "arbitrage"                  # Source → list → fulfill
    CONTENT_POSTING = "content_posting"      # Post content with monetization
    PAYMENT_COLLECTION = "payment_collection" # Direct payment flow
    MANUAL_REVIEW = "manual_review"          # Queue for human review


def flow_to_dict(flow: 'ExecutionFlow') -> Dict[str, Any]:
    """Convert ExecutionFlow dataclass to JSON-serializable dict"""
    if flow is None:
        return None
    return {
        "platform": flow.platform,
        "execution_mode": flow.execution_mode.value,
        "steps": flow.steps,
        "requires_communication": flow.requires_communication,
        "requires_approval": flow.requires_approval,
        "required_apis": flow.required_apis,
        "optional_apis": flow.optional_apis,
        "endpoints": flow.endpoints,
        "estimated_time_minutes": flow.estimated_time_minutes,
        "auto_execute": flow.auto_execute
    }


@dataclass
class ExecutionFlow:
    """Configuration for a platform's execution flow"""
    platform: str
    execution_mode: ExecutionMode
    steps: List[str]
    requires_communication: bool
    requires_approval: bool
    required_apis: List[str]
    optional_apis: List[str]
    endpoints: Dict[str, str]  # step_name -> endpoint
    estimated_time_minutes: int
    auto_execute: bool  # Can run without human intervention


# ═══════════════════════════════════════════════════════════════════════════════
# API AVAILABILITY CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

def get_configured_apis() -> Dict[str, bool]:
    """
    Check which APIs are configured based on environment variables.
    Mirrors v115_api_fabric.py validation logic.
    """
    return {
        # Payment
        "stripe": bool(os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET")),
        "stripe_webhook": bool(os.getenv("STRIPE_WEBHOOK_SECRET")),

        # E-Commerce
        "shopify": bool(os.getenv("SHOPIFY_ADMIN_TOKEN") or os.getenv("SHOPIFY_ACCESS_TOKEN")),

        # Affiliate
        "amazon_affiliate": True,  # Always configured with default tag

        # Social - Twitter
        "twitter": bool(os.getenv("TWITTER_BEARER_TOKEN")) or all([
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET"),
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_SECRET")
        ]),
        "twitter_dm": bool(os.getenv("TWITTER_ACCESS_TOKEN")),

        # Social - Instagram
        "instagram": all([os.getenv("INSTAGRAM_ACCESS_TOKEN"), os.getenv("INSTAGRAM_BUSINESS_ID")]),

        # Social - LinkedIn
        "linkedin": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
        "linkedin_oauth": all([
            os.getenv("LINKEDIN_ACCESS_TOKEN"),
            os.getenv("LINKEDIN_CLIENT_ID"),
            os.getenv("LINKEDIN_CLIENT_SECRET")
        ]),

        # Communication
        "twilio": all([
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN"),
            os.getenv("TWILIO_PHONE_NUMBER")
        ]),
        "resend": bool(os.getenv("RESEND_API_KEY")),

        # AI
        "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "perplexity": bool(os.getenv("PERPLEXITY_API_KEY")),

        # Content Generation
        "stability": bool(os.getenv("STABILITY_API_KEY")),
        "runway": bool(os.getenv("RUNWAV_API_KEY")),

        # Development
        "github": bool(os.getenv("GITHUB_TOKEN")),

        # Storage
        "jsonbin": bool(os.getenv("JSONBIN_SECRET")),

        # Marketplaces (manual - no API)
        "upwork": False,  # No direct API access
        "fiverr": False,  # No direct API access
        "freelancer": False,  # No direct API access
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PLATFORM EXECUTION FLOWS
# ═══════════════════════════════════════════════════════════════════════════════

PLATFORM_FLOWS: Dict[str, ExecutionFlow] = {
    # ─────────────────────────────────────────────────────────────────────────
    # IMMEDIATE EXECUTION - No communication needed
    # ─────────────────────────────────────────────────────────────────────────

    "github_bounty": ExecutionFlow(
        platform="github",
        execution_mode=ExecutionMode.IMMEDIATE,
        steps=[
            "analyze_issue",      # Parse issue requirements
            "generate_solution",  # AI generates code
            "create_branch",      # Fork and create branch
            "submit_pr",          # Submit pull request
            "await_review",       # Track PR status
            "claim_bounty"        # Claim payment after merge
        ],
        requires_communication=False,  # PRs are the communication
        requires_approval=False,       # Auto-execute for bounties
        required_apis=["github", "openrouter"],
        optional_apis=["gemini"],
        endpoints={
            "analyze_issue": "/github/analyze-issue",
            "generate_solution": "/fulfillment/code-generation",
            "create_branch": "/github/create-branch",
            "submit_pr": "/github/submit-pr",
            "await_review": "/github/pr-status",
            "claim_bounty": "/bounties/claim"
        },
        estimated_time_minutes=30,
        auto_execute=True
    ),

    "github_issue": ExecutionFlow(
        platform="github",
        execution_mode=ExecutionMode.IMMEDIATE,
        steps=[
            "analyze_issue",
            "post_interest_comment",  # Express interest on issue
            "generate_solution",
            "submit_pr"
        ],
        requires_communication=False,  # Comment on issue IS the communication
        requires_approval=False,
        required_apis=["github", "openrouter"],
        optional_apis=["gemini"],
        endpoints={
            "analyze_issue": "/github/analyze-issue",
            "post_interest_comment": "/github/post-comment",
            "generate_solution": "/fulfillment/code-generation",
            "submit_pr": "/github/submit-pr"
        },
        estimated_time_minutes=45,
        auto_execute=True
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # CONVERSATIONAL - Build relationship first
    # ─────────────────────────────────────────────────────────────────────────

    "linkedin_lead": ExecutionFlow(
        platform="linkedin",
        execution_mode=ExecutionMode.CONVERSATIONAL,
        steps=[
            "enrich_profile",       # Get profile data
            "send_connection",      # Send connection request
            "await_connection",     # Wait for accept
            "qualify_lead",         # Assess fit via message
            "send_proposal",        # Send service proposal
            "negotiate",            # Handle objections
            "close_deal",           # Generate contract
            "collect_payment"       # Stripe payment link
        ],
        requires_communication=True,
        requires_approval=True,  # Human approves connection strategy
        required_apis=["linkedin", "openrouter", "stripe"],
        optional_apis=["resend", "perplexity"],
        endpoints={
            "enrich_profile": "/linkedin/profile",
            "send_connection": "/linkedin/connect",
            "qualify_lead": "/linkedin/send-message",
            "send_proposal": "/linkedin/send-message",
            "close_deal": "/contract/generate",
            "collect_payment": "/wade/payment-link"
        },
        estimated_time_minutes=1440,  # 24 hours (relationship building)
        auto_execute=False
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # APPLICATION BASED - Submit application, await approval
    # ─────────────────────────────────────────────────────────────────────────

    "twitter_sponsored": ExecutionFlow(
        platform="twitter",
        execution_mode=ExecutionMode.APPLICATION_BASED,
        steps=[
            "identify_opportunity",  # Find sponsored post opportunity
            "apply_to_campaign",     # Apply via DM or form
            "await_approval",        # Wait for brand approval
            "create_content",        # Generate sponsored content
            "post_content",          # Tweet with disclosure
            "track_engagement",      # Monitor metrics
            "collect_payment"        # Invoice sponsor
        ],
        requires_communication=True,  # DM to brand
        requires_approval=True,
        required_apis=["twitter", "twitter_dm", "openrouter"],
        optional_apis=["stability", "stripe"],
        endpoints={
            "apply_to_campaign": "/twitter/send-dm",
            "create_content": "/ame/generate-pitch",
            "post_content": "/twitter/post",
            "track_engagement": "/twitter/analytics",
            "collect_payment": "/stripe/send-invoice"
        },
        estimated_time_minutes=2880,  # 48 hours
        auto_execute=False
    ),

    "twitter_affiliate": ExecutionFlow(
        platform="twitter",
        execution_mode=ExecutionMode.CONTENT_POSTING,
        steps=[
            "identify_product",      # Find product to promote
            "generate_affiliate_link", # Create affiliate URL
            "create_thread",         # Generate tweet thread
            "post_thread",           # Post with affiliate link
            "track_conversions"      # Monitor clicks/purchases
        ],
        requires_communication=False,
        requires_approval=False,
        required_apis=["twitter", "amazon_affiliate", "openrouter"],
        optional_apis=["perplexity", "stability"],
        endpoints={
            "generate_affiliate_link": "/affiliate/generate-link",
            "create_thread": "/ame/generate-pitch",
            "post_thread": "/twitter/post",
            "track_conversions": "/affiliate/analytics"
        },
        estimated_time_minutes=15,
        auto_execute=True
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # PROPOSAL BASED - Submit proposal, await hire
    # ─────────────────────────────────────────────────────────────────────────

    "upwork_gig": ExecutionFlow(
        platform="upwork",
        execution_mode=ExecutionMode.PROPOSAL_BASED,
        steps=[
            "analyze_job",           # Parse job requirements
            "generate_proposal",     # AI-generated proposal
            "calculate_bid",         # COGS-aware pricing
            "submit_proposal",       # Submit via platform
            "await_hire",            # Wait for client decision
            "sign_contract",         # Accept terms
            "execute_work",          # Fulfill the job
            "deliver_work",          # Submit deliverables
            "collect_payment"        # Escrow release
        ],
        requires_communication=True,  # Messages through platform
        requires_approval=True,       # Human reviews proposals
        required_apis=["openrouter"],  # Upwork has no API
        optional_apis=["gemini", "stability"],
        endpoints={
            "analyze_job": "/ame/analyze-opportunity",
            "generate_proposal": "/ame/generate-pitch",
            "calculate_bid": "/execution/margin-gate",
            "submit_proposal": "/upwork/submit-proposal",  # Manual
            "execute_work": "/fulfillment/code-generation",
            "deliver_work": "/delivery/upwork"
        },
        estimated_time_minutes=4320,  # 3 days
        auto_execute=False  # Manual submission required
    ),

    "fiverr_gig": ExecutionFlow(
        platform="fiverr",
        execution_mode=ExecutionMode.PROPOSAL_BASED,
        steps=[
            "analyze_request",
            "generate_offer",
            "submit_offer",
            "await_acceptance",
            "execute_work",
            "deliver_work",
            "collect_payment"
        ],
        requires_communication=True,
        requires_approval=True,
        required_apis=["openrouter"],
        optional_apis=["gemini", "stability"],
        endpoints={
            "analyze_request": "/ame/analyze-opportunity",
            "generate_offer": "/ame/generate-pitch",
            "execute_work": "/fulfillment/code-generation",
            "deliver_work": "/delivery/fiverr"
        },
        estimated_time_minutes=2880,
        auto_execute=False
    ),

    "freelancer_gig": ExecutionFlow(
        platform="freelancer",
        execution_mode=ExecutionMode.PROPOSAL_BASED,
        steps=[
            "analyze_project",
            "generate_bid",
            "submit_bid",
            "await_award",
            "accept_milestone",
            "execute_work",
            "deliver_work",
            "request_payment"
        ],
        requires_communication=True,
        requires_approval=True,
        required_apis=["openrouter"],
        optional_apis=["gemini"],
        endpoints={
            "analyze_project": "/ame/analyze-opportunity",
            "generate_bid": "/ame/generate-pitch",
            "execute_work": "/fulfillment/code-generation",
            "deliver_work": "/delivery/freelancer"
        },
        estimated_time_minutes=4320,
        auto_execute=False
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # CONTENT POSTING - Post content with monetization
    # ─────────────────────────────────────────────────────────────────────────

    "instagram_creator": ExecutionFlow(
        platform="instagram",
        execution_mode=ExecutionMode.CONTENT_POSTING,
        steps=[
            "identify_trend",        # Find trending topic
            "generate_content",      # AI creates image/caption
            "generate_affiliate_link", # Create product link
            "post_content",          # Post to Instagram
            "engage_comments",       # Respond to engagement
            "track_conversions"      # Monitor affiliate clicks
        ],
        requires_communication=False,
        requires_approval=False,
        required_apis=["instagram", "openrouter", "amazon_affiliate"],
        optional_apis=["stability", "perplexity"],
        endpoints={
            "identify_trend": "/discovery/instagram/trends",
            "generate_content": "/fulfillment/graphics-generation",
            "generate_affiliate_link": "/affiliate/generate-link",
            "post_content": "/instagram/post",
            "engage_comments": "/instagram/reply",
            "track_conversions": "/affiliate/analytics"
        },
        estimated_time_minutes=30,
        auto_execute=True
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # ARBITRAGE - Source, list, fulfill
    # ─────────────────────────────────────────────────────────────────────────

    "shopify_arbitrage": ExecutionFlow(
        platform="shopify",
        execution_mode=ExecutionMode.ARBITRAGE,
        steps=[
            "identify_product",      # Find arbitrage opportunity
            "source_supplier",       # Find wholesale source
            "calculate_margin",      # Verify profit margin
            "create_listing",        # List on Shopify store
            "setup_automation",      # Configure auto-fulfill
            "monitor_sales",         # Track orders
            "fulfill_orders"         # Process and ship
        ],
        requires_communication=False,
        requires_approval=True,  # Review before listing
        required_apis=["shopify", "stripe"],
        optional_apis=["openrouter", "perplexity"],
        endpoints={
            "identify_product": "/discovery/arbitrage/detect",
            "calculate_margin": "/execution/margin-gate",
            "create_listing": "/shopify/create-product",
            "monitor_sales": "/shopify/orders",
            "fulfill_orders": "/shopify/fulfill"
        },
        estimated_time_minutes=60,
        auto_execute=False
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # PAYMENT COLLECTION - Direct payment flow
    # ─────────────────────────────────────────────────────────────────────────

    "stripe_invoice": ExecutionFlow(
        platform="stripe",
        execution_mode=ExecutionMode.PAYMENT_COLLECTION,
        steps=[
            "identify_receivable",   # Find unpaid invoice
            "send_reminder",         # Email payment reminder
            "generate_payment_link", # Create Stripe link
            "track_payment",         # Monitor payment status
            "reconcile"              # Update books
        ],
        requires_communication=True,  # Email reminder
        requires_approval=False,
        required_apis=["stripe", "resend"],
        optional_apis=["twilio"],
        endpoints={
            "identify_receivable": "/payments/status",
            "send_reminder": "/email/send",
            "generate_payment_link": "/wade/payment-link",
            "track_payment": "/stripe/payment-status",
            "reconcile": "/books/reconcile"
        },
        estimated_time_minutes=5,
        auto_execute=True
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # REDDIT PAIN POINTS - Respond with solution
    # ─────────────────────────────────────────────────────────────────────────

    "reddit_pain_point": ExecutionFlow(
        platform="reddit",
        execution_mode=ExecutionMode.CONVERSATIONAL,
        steps=[
            "analyze_post",          # Understand the pain point
            "generate_helpful_reply", # Create value-first response
            "post_reply",            # Comment on post
            "await_engagement",      # Wait for OP response
            "offer_service",         # If interested, offer paid help
            "close_deal"             # Move to contract
        ],
        requires_communication=True,
        requires_approval=True,  # Review replies before posting
        required_apis=["openrouter"],  # Reddit API is rate-limited
        optional_apis=["perplexity"],
        endpoints={
            "analyze_post": "/ame/analyze-opportunity",
            "generate_helpful_reply": "/ame/generate-pitch",
            "post_reply": "/reddit/post-reply",
            "offer_service": "/reddit/post-reply",
            "close_deal": "/contract/generate"
        },
        estimated_time_minutes=1440,
        auto_execute=False
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # HACKERNEWS - Technical community engagement
    # ─────────────────────────────────────────────────────────────────────────

    "hackernews_opportunity": ExecutionFlow(
        platform="hackernews",
        execution_mode=ExecutionMode.CONVERSATIONAL,
        steps=[
            "analyze_thread",
            "generate_technical_reply",
            "post_comment",
            "await_engagement",
            "offer_consulting"
        ],
        requires_communication=True,
        requires_approval=True,
        required_apis=["openrouter"],
        optional_apis=["perplexity"],
        endpoints={
            "analyze_thread": "/ame/analyze-opportunity",
            "generate_technical_reply": "/ame/generate-pitch",
            "post_comment": "/hackernews/post-comment"
        },
        estimated_time_minutes=1440,
        auto_execute=False
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # EMAIL OUTREACH - Direct email communication
    # ─────────────────────────────────────────────────────────────────────────

    "email_outreach": ExecutionFlow(
        platform="email",
        execution_mode=ExecutionMode.CONVERSATIONAL,
        steps=[
            "enrich_contact",        # Research the lead
            "generate_email",        # Create personalized pitch
            "send_email",            # Send via Resend
            "await_reply",           # Monitor for response
            "qualify_response",      # Assess interest level
            "send_followup",         # Follow up if needed
            "close_deal"             # Generate contract
        ],
        requires_communication=True,
        requires_approval=True,
        required_apis=["resend", "openrouter"],
        optional_apis=["perplexity", "stripe"],
        endpoints={
            "enrich_contact": "/contacts/enrich",
            "generate_email": "/ame/generate-pitch",
            "send_email": "/email/send",
            "qualify_response": "/ame/analyze-response",
            "close_deal": "/contract/generate"
        },
        estimated_time_minutes=2880,
        auto_execute=False
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# FLOW DETERMINATION
# ═══════════════════════════════════════════════════════════════════════════════

def determine_execution_flow(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine the appropriate execution flow for an opportunity.

    Args:
        opportunity: Opportunity dict with platform, source, labels, etc.

    Returns:
        Dict with:
        - flow: ExecutionFlow or None
        - flow_key: str identifier
        - can_execute: bool
        - missing_apis: List[str]
        - reason: str explanation
    """
    platform = opportunity.get("platform", "").lower()
    source = opportunity.get("source", "").lower()
    labels = [str(l).lower() for l in opportunity.get("labels", [])]
    label_str = " ".join(labels)
    title = opportunity.get("title", "").lower()

    # Get current API configuration
    apis = get_configured_apis()

    result = {
        "flow": None,  # Will be set to flow dict (not object) for JSON serialization
        "flow_key": None,
        "can_execute": False,
        "missing_apis": [],
        "available_apis": [],
        "reason": "",
        "execution_mode": None,
        "requires_communication": True,
        "requires_approval": True,
        "auto_execute": False,
        "steps": [],
        "endpoints": {}
    }

    # ─────────────────────────────────────────────────────────────────────────
    # GITHUB - Check for bounty vs regular issue
    # ─────────────────────────────────────────────────────────────────────────
    if platform in ["github", "github_bounties"]:
        # Check if it's a bounty
        is_bounty = (
            "bounty" in source or
            "bounty" in label_str or
            "$" in label_str or
            "bounty" in title or
            "awaiting payment" in label_str
        )

        if is_bounty:
            flow_key = "github_bounty"
        else:
            flow_key = "github_issue"

        flow = PLATFORM_FLOWS.get(flow_key)
        if flow:
            missing = [api for api in flow.required_apis if not apis.get(api)]
            available = [api for api in flow.required_apis if apis.get(api)]

            result["flow"] = flow_to_dict(flow)
            result["flow_key"] = flow_key
            result["missing_apis"] = missing
            result["available_apis"] = available
            result["can_execute"] = len(missing) == 0
            result["execution_mode"] = flow.execution_mode.value
            result["requires_communication"] = flow.requires_communication
            result["requires_approval"] = flow.requires_approval
            result["auto_execute"] = flow.auto_execute and len(missing) == 0
            result["steps"] = flow.steps
            result["endpoints"] = flow.endpoints

            if result["can_execute"]:
                result["reason"] = f"GitHub {'bounty' if is_bounty else 'issue'} - IMMEDIATE execution (PR submission)"
            else:
                result["reason"] = f"Missing APIs: {', '.join(missing)}"

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # LINKEDIN - Conversational flow
    # ─────────────────────────────────────────────────────────────────────────
    if platform == "linkedin":
        flow_key = "linkedin_lead"
        flow = PLATFORM_FLOWS.get(flow_key)
        if flow:
            missing = [api for api in flow.required_apis if not apis.get(api)]
            available = [api for api in flow.required_apis if apis.get(api)]

            result["flow"] = flow_to_dict(flow)
            result["flow_key"] = flow_key
            result["missing_apis"] = missing
            result["available_apis"] = available
            result["can_execute"] = len(missing) == 0
            result["execution_mode"] = flow.execution_mode.value
            result["requires_communication"] = flow.requires_communication
            result["requires_approval"] = flow.requires_approval
            result["auto_execute"] = flow.auto_execute
            result["steps"] = flow.steps
            result["endpoints"] = flow.endpoints

            if result["can_execute"]:
                result["reason"] = "LinkedIn lead - CONVERSATIONAL flow (connection → qualify → close)"
            else:
                result["reason"] = f"Missing APIs: {', '.join(missing)}"

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # TWITTER - Check for sponsored vs affiliate
    # ─────────────────────────────────────────────────────────────────────────
    if platform == "twitter":
        # Check if it's sponsored content opportunity
        is_sponsored = any(kw in title for kw in ["sponsor", "paid", "collaboration", "brand"])

        flow_key = "twitter_sponsored" if is_sponsored else "twitter_affiliate"
        flow = PLATFORM_FLOWS.get(flow_key)
        if flow:
            missing = [api for api in flow.required_apis if not apis.get(api)]
            available = [api for api in flow.required_apis if apis.get(api)]

            result["flow"] = flow_to_dict(flow)
            result["flow_key"] = flow_key
            result["missing_apis"] = missing
            result["available_apis"] = available
            result["can_execute"] = len(missing) == 0
            result["execution_mode"] = flow.execution_mode.value
            result["requires_communication"] = flow.requires_communication
            result["requires_approval"] = flow.requires_approval
            result["auto_execute"] = flow.auto_execute and len(missing) == 0

            if result["can_execute"]:
                if is_sponsored:
                    result["reason"] = "Twitter sponsored - APPLICATION flow (apply → approval → post)"
                else:
                    result["reason"] = "Twitter affiliate - CONTENT POSTING flow (post with affiliate link)"
            else:
                result["reason"] = f"Missing APIs: {', '.join(missing)}"

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # UPWORK/FIVERR/FREELANCER - Proposal based
    # ─────────────────────────────────────────────────────────────────────────
    if platform in ["upwork", "freelancer", "fiverr"]:
        flow_key = f"{platform}_gig"
        flow = PLATFORM_FLOWS.get(flow_key)
        if flow:
            missing = [api for api in flow.required_apis if not apis.get(api)]
            available = [api for api in flow.required_apis if apis.get(api)]

            result["flow"] = flow_to_dict(flow)
            result["flow_key"] = flow_key
            result["missing_apis"] = missing
            result["available_apis"] = available
            result["can_execute"] = len(missing) == 0
            result["execution_mode"] = flow.execution_mode.value
            result["requires_communication"] = flow.requires_communication
            result["requires_approval"] = flow.requires_approval
            result["auto_execute"] = False  # Always manual for marketplaces
            result["steps"] = flow.steps
            result["endpoints"] = flow.endpoints

            if result["can_execute"]:
                result["reason"] = f"{platform.title()} - PROPOSAL flow (submit → hire → execute)"
            else:
                result["reason"] = f"Missing APIs: {', '.join(missing)}"

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # INSTAGRAM - Content posting with affiliate
    # ─────────────────────────────────────────────────────────────────────────
    if platform == "instagram":
        flow_key = "instagram_creator"
        flow = PLATFORM_FLOWS.get(flow_key)
        if flow:
            missing = [api for api in flow.required_apis if not apis.get(api)]
            available = [api for api in flow.required_apis if apis.get(api)]

            result["flow"] = flow_to_dict(flow)
            result["flow_key"] = flow_key
            result["missing_apis"] = missing
            result["available_apis"] = available
            result["can_execute"] = len(missing) == 0
            result["execution_mode"] = flow.execution_mode.value
            result["requires_communication"] = flow.requires_communication
            result["requires_approval"] = flow.requires_approval
            result["auto_execute"] = flow.auto_execute and len(missing) == 0
            result["steps"] = flow.steps
            result["endpoints"] = flow.endpoints

            if result["can_execute"]:
                result["reason"] = "Instagram - CONTENT POSTING flow (generate → post → track)"
            else:
                result["reason"] = f"Missing APIs: {', '.join(missing)}"

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # SHOPIFY - Arbitrage flow
    # ─────────────────────────────────────────────────────────────────────────
    if platform == "shopify" or source == "arbitrage":
        flow_key = "shopify_arbitrage"
        flow = PLATFORM_FLOWS.get(flow_key)
        if flow:
            missing = [api for api in flow.required_apis if not apis.get(api)]
            available = [api for api in flow.required_apis if apis.get(api)]

            result["flow"] = flow_to_dict(flow)
            result["flow_key"] = flow_key
            result["missing_apis"] = missing
            result["available_apis"] = available
            result["can_execute"] = len(missing) == 0
            result["execution_mode"] = flow.execution_mode.value
            result["requires_communication"] = flow.requires_communication
            result["requires_approval"] = flow.requires_approval
            result["auto_execute"] = flow.auto_execute
            result["steps"] = flow.steps
            result["endpoints"] = flow.endpoints

            if result["can_execute"]:
                result["reason"] = "Shopify - ARBITRAGE flow (source → list → fulfill)"
            else:
                result["reason"] = f"Missing APIs: {', '.join(missing)}"

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # STRIPE - Payment collection
    # ─────────────────────────────────────────────────────────────────────────
    if platform == "stripe" or source in ["invoice", "payment", "receivable"]:
        flow_key = "stripe_invoice"
        flow = PLATFORM_FLOWS.get(flow_key)
        if flow:
            missing = [api for api in flow.required_apis if not apis.get(api)]
            available = [api for api in flow.required_apis if apis.get(api)]

            result["flow"] = flow_to_dict(flow)
            result["flow_key"] = flow_key
            result["missing_apis"] = missing
            result["available_apis"] = available
            result["can_execute"] = len(missing) == 0
            result["execution_mode"] = flow.execution_mode.value
            result["requires_communication"] = flow.requires_communication
            result["requires_approval"] = flow.requires_approval
            result["auto_execute"] = flow.auto_execute and len(missing) == 0
            result["steps"] = flow.steps
            result["endpoints"] = flow.endpoints

            if result["can_execute"]:
                result["reason"] = "Stripe - PAYMENT COLLECTION flow (reminder → link → collect)"
            else:
                result["reason"] = f"Missing APIs: {', '.join(missing)}"

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # REDDIT - Pain point response
    # ─────────────────────────────────────────────────────────────────────────
    if platform == "reddit":
        flow_key = "reddit_pain_point"
        flow = PLATFORM_FLOWS.get(flow_key)
        if flow:
            missing = [api for api in flow.required_apis if not apis.get(api)]
            available = [api for api in flow.required_apis if apis.get(api)]

            result["flow"] = flow_to_dict(flow)
            result["flow_key"] = flow_key
            result["missing_apis"] = missing
            result["available_apis"] = available
            result["can_execute"] = len(missing) == 0
            result["execution_mode"] = flow.execution_mode.value
            result["requires_communication"] = flow.requires_communication
            result["requires_approval"] = flow.requires_approval
            result["auto_execute"] = flow.auto_execute
            result["steps"] = flow.steps
            result["endpoints"] = flow.endpoints

            if result["can_execute"]:
                result["reason"] = "Reddit - CONVERSATIONAL flow (helpful reply → engagement → offer)"
            else:
                result["reason"] = f"Missing APIs: {', '.join(missing)}"

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # HACKERNEWS - Technical engagement
    # ─────────────────────────────────────────────────────────────────────────
    if platform == "hackernews":
        flow_key = "hackernews_opportunity"
        flow = PLATFORM_FLOWS.get(flow_key)
        if flow:
            missing = [api for api in flow.required_apis if not apis.get(api)]
            available = [api for api in flow.required_apis if apis.get(api)]

            result["flow"] = flow_to_dict(flow)
            result["flow_key"] = flow_key
            result["missing_apis"] = missing
            result["available_apis"] = available
            result["can_execute"] = len(missing) == 0
            result["execution_mode"] = flow.execution_mode.value
            result["requires_communication"] = flow.requires_communication
            result["requires_approval"] = flow.requires_approval
            result["auto_execute"] = flow.auto_execute
            result["steps"] = flow.steps
            result["endpoints"] = flow.endpoints

            if result["can_execute"]:
                result["reason"] = "HackerNews - CONVERSATIONAL flow (technical reply → engagement)"
            else:
                result["reason"] = f"Missing APIs: {', '.join(missing)}"

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # EMAIL - Direct outreach
    # ─────────────────────────────────────────────────────────────────────────
    if platform == "email" or opportunity.get("contact", {}).get("email"):
        flow_key = "email_outreach"
        flow = PLATFORM_FLOWS.get(flow_key)
        if flow:
            missing = [api for api in flow.required_apis if not apis.get(api)]
            available = [api for api in flow.required_apis if apis.get(api)]

            result["flow"] = flow_to_dict(flow)
            result["flow_key"] = flow_key
            result["missing_apis"] = missing
            result["available_apis"] = available
            result["can_execute"] = len(missing) == 0
            result["execution_mode"] = flow.execution_mode.value
            result["requires_communication"] = flow.requires_communication
            result["requires_approval"] = flow.requires_approval
            result["auto_execute"] = flow.auto_execute
            result["steps"] = flow.steps
            result["endpoints"] = flow.endpoints

            if result["can_execute"]:
                result["reason"] = "Email - CONVERSATIONAL flow (outreach → qualify → close)"
            else:
                result["reason"] = f"Missing APIs: {', '.join(missing)}"

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # DEFAULT - Unknown platform, queue for manual review
    # ─────────────────────────────────────────────────────────────────────────
    result["flow_key"] = "manual_review"
    result["execution_mode"] = ExecutionMode.MANUAL_REVIEW.value
    result["can_execute"] = False
    result["reason"] = f"Unknown platform '{platform}' - queued for manual review"
    result["requires_approval"] = True
    result["auto_execute"] = False

    return result


def route_opportunities_by_flow(
    opportunities: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Route opportunities into buckets based on their execution flow.

    Returns:
        Dict with keys:
        - immediate: Can execute right now (GitHub bounties)
        - conversational: Need relationship building (LinkedIn, Reddit)
        - proposal_based: Need proposal submission (Upwork, Fiverr)
        - content_posting: Can post content (Twitter, Instagram)
        - payment_collection: Can collect payment (Stripe)
        - manual_review: Need human review (missing APIs or unknown platform)
    """
    routed = {
        "immediate": [],
        "conversational": [],
        "application_based": [],
        "proposal_based": [],
        "arbitrage": [],
        "content_posting": [],
        "payment_collection": [],
        "manual_review": []
    }

    stats = {
        "total": len(opportunities),
        "by_mode": {},
        "can_auto_execute": 0,
        "needs_approval": 0,
        "missing_apis": 0
    }

    for opp in opportunities:
        flow_result = determine_execution_flow(opp)

        # Enrich opportunity with flow info
        opp["_flow"] = flow_result

        mode = flow_result.get("execution_mode", "manual_review")

        # Route to appropriate bucket
        if mode in routed:
            routed[mode].append(opp)
        else:
            routed["manual_review"].append(opp)

        # Update stats
        stats["by_mode"][mode] = stats["by_mode"].get(mode, 0) + 1

        if flow_result.get("auto_execute"):
            stats["can_auto_execute"] += 1
        if flow_result.get("requires_approval"):
            stats["needs_approval"] += 1
        if flow_result.get("missing_apis"):
            stats["missing_apis"] += 1

    return {
        "routed": routed,
        "stats": stats
    }


def get_flow_summary() -> Dict[str, Any]:
    """Get summary of all configured flows and API status"""
    apis = get_configured_apis()

    flows_summary = {}
    for flow_key, flow in PLATFORM_FLOWS.items():
        missing = [api for api in flow.required_apis if not apis.get(api)]
        flows_summary[flow_key] = {
            "platform": flow.platform,
            "mode": flow.execution_mode.value,
            "ready": len(missing) == 0,
            "missing_apis": missing,
            "steps": flow.steps,
            "auto_execute": flow.auto_execute,
            "requires_approval": flow.requires_approval,
            "estimated_minutes": flow.estimated_time_minutes
        }

    configured_apis = [k for k, v in apis.items() if v]
    missing_apis = [k for k, v in apis.items() if not v]

    return {
        "flows": flows_summary,
        "apis": {
            "configured": configured_apis,
            "missing": missing_apis,
            "total_configured": len(configured_apis),
            "total_missing": len(missing_apis)
        },
        "ready_flows": [k for k, v in flows_summary.items() if v["ready"]],
        "blocked_flows": [k for k, v in flows_summary.items() if not v["ready"]]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "ExecutionMode",
    "ExecutionFlow",
    "PLATFORM_FLOWS",
    "get_configured_apis",
    "determine_execution_flow",
    "route_opportunities_by_flow",
    "get_flow_summary"
]


if __name__ == "__main__":
    # Test the flow determination
    print("=" * 80)
    print("PLATFORM EXECUTION FLOWS - TEST")
    print("=" * 80)

    summary = get_flow_summary()

    print(f"\nConfigured APIs ({summary['apis']['total_configured']}):")
    for api in summary['apis']['configured']:
        print(f"  ✓ {api}")

    print(f"\nMissing APIs ({summary['apis']['total_missing']}):")
    for api in summary['apis']['missing']:
        print(f"  ✗ {api}")

    print(f"\nReady Flows ({len(summary['ready_flows'])}):")
    for flow in summary['ready_flows']:
        info = summary['flows'][flow]
        print(f"  ✓ {flow}: {info['mode']} ({'auto' if info['auto_execute'] else 'manual'})")

    print(f"\nBlocked Flows ({len(summary['blocked_flows'])}):")
    for flow in summary['blocked_flows']:
        info = summary['flows'][flow]
        print(f"  ✗ {flow}: missing {info['missing_apis']}")

    # Test with sample opportunities
    print("\n" + "=" * 80)
    print("SAMPLE OPPORTUNITY ROUTING")
    print("=" * 80)

    test_opps = [
        {"platform": "github", "source": "bounty", "title": "[$100] Fix bug", "labels": ["bounty"]},
        {"platform": "linkedin", "title": "CTO looking for automation"},
        {"platform": "twitter", "title": "Need developer for project"},
        {"platform": "upwork", "title": "Full-stack developer needed"},
        {"platform": "instagram", "title": "Product promotion"},
        {"platform": "reddit", "title": "[Hiring] Need help with code"},
        {"platform": "unknown", "title": "Some opportunity"},
    ]

    for opp in test_opps:
        result = determine_execution_flow(opp)
        status = "✓" if result["can_execute"] else "✗"
        print(f"\n{status} {opp['platform']}: {result['execution_mode']}")
        print(f"    Flow: {result['flow_key']}")
        print(f"    Reason: {result['reason']}")
        print(f"    Auto-execute: {result['auto_execute']}")
