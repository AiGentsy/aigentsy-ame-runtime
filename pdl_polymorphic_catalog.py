"""
PDL CATALOG - Protocol Descriptor Language Catalog
═══════════════════════════════════════════════════════════════════════════════

UNIFIED SOURCE OF TRUTH for all platform definitions.

This catalog defines:
- Platform capabilities and actions
- API requirements and availability
- Execution methods (api, browser, universal_fabric)
- Cost models and SLAs
- Input schemas

Every platform operation flows through a PDL, enabling:
- Polymorphic execution routing
- Universal Fabric fallback
- API availability checking
- Cost tracking and margin gating

Updated: Jan 2026
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import os


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class PlatformTier(Enum):
    """Platform API access tier"""
    FREE = "free"           # No API key needed (public endpoints)
    API = "api"             # Has API configured via env var
    OAUTH = "oauth"         # Requires OAuth flow
    PAID = "paid"           # Requires paid API access
    BROWSER = "browser"     # No API, use browser automation
    FUTURE = "future"       # Planned but not implemented


class ExecutionMethod(Enum):
    """How to execute the PDL action"""
    API = "api"                         # Direct API call
    BROWSER = "browser"                 # Playwright browser automation
    UNIVERSAL_FABRIC = "universal_fabric"  # AI-powered universal executor
    MANUAL = "manual"                   # Queue for human execution
    HYBRID = "hybrid"                   # Try API, fallback to browser


# ═══════════════════════════════════════════════════════════════════════════════
# PDL DATACLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PDL:
    """
    Protocol Descriptor Language - Defines a single platform action.

    Examples:
    - github.post_comment
    - reddit.post_reply
    - linkedin.send_connection
    - upwork.submit_proposal
    """
    name: str                           # "github.post_comment"
    platform: str                       # "github"
    action: str                         # "post_comment"
    description: str                    # Human-readable description
    tier: PlatformTier                  # Access tier
    execution_method: ExecutionMethod   # How to execute
    required_apis: List[str]            # ["GITHUB_TOKEN"]
    optional_apis: List[str] = field(default_factory=list)
    endpoint: Optional[str] = None      # API endpoint path
    fabric_endpoint: Optional[str] = None  # Universal Fabric endpoint
    browser_url_template: Optional[str] = None  # URL for browser automation
    inputs: Dict[str, Any] = field(default_factory=dict)  # Input schema
    outputs: Dict[str, Any] = field(default_factory=dict)  # Output schema
    cost_model: Dict[str, Any] = field(default_factory=lambda: {"type": "free", "estimate_usd": 0})
    sla: Dict[str, Any] = field(default_factory=lambda: {"timeout_sec": 60, "retry_count": 3})
    tags: List[str] = field(default_factory=list)
    auto_execute: bool = False          # Can execute without human approval
    max_ev_auto: float = 50.0           # Max EV for auto-execute
    rate_limit: Dict[str, int] = field(default_factory=lambda: {"per_hour": 100})

    def can_execute(self) -> bool:
        """Check if all required APIs are configured"""
        return all(os.getenv(api) for api in self.required_apis)

    def get_available_apis(self) -> List[str]:
        """Get list of configured APIs"""
        return [api for api in self.required_apis if os.getenv(api)]

    def get_missing_apis(self) -> List[str]:
        """Get list of missing APIs"""
        return [api for api in self.required_apis if not os.getenv(api)]

    def get_execution_method(self) -> ExecutionMethod:
        """
        Determine actual execution method based on API availability.
        Falls back to BROWSER or UNIVERSAL_FABRIC if APIs missing.
        """
        if self.can_execute():
            return self.execution_method
        elif self.browser_url_template:
            return ExecutionMethod.BROWSER
        else:
            return ExecutionMethod.UNIVERSAL_FABRIC

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "name": self.name,
            "platform": self.platform,
            "action": self.action,
            "description": self.description,
            "tier": self.tier.value,
            "execution_method": self.execution_method.value,
            "actual_execution_method": self.get_execution_method().value,
            "required_apis": self.required_apis,
            "optional_apis": self.optional_apis,
            "endpoint": self.endpoint,
            "fabric_endpoint": self.fabric_endpoint,
            "browser_url_template": self.browser_url_template,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "cost_model": self.cost_model,
            "sla": self.sla,
            "tags": self.tags,
            "auto_execute": self.auto_execute,
            "max_ev_auto": self.max_ev_auto,
            "rate_limit": self.rate_limit,
            "can_execute": self.can_execute(),
            "available_apis": self.get_available_apis(),
            "missing_apis": self.get_missing_apis()
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PDL CATALOG
# ═══════════════════════════════════════════════════════════════════════════════

class PDLCatalog:
    """
    Centralized catalog of all Platform Descriptor Languages.

    THE source of truth for platform capabilities.
    """

    def __init__(self):
        self.pdls: Dict[str, PDL] = {}
        self._register_all_platforms()

    def _register_all_platforms(self):
        """Register all platform PDLs"""
        self._register_github_pdls()
        self._register_reddit_pdls()
        self._register_linkedin_pdls()
        self._register_twitter_pdls()
        self._register_hackernews_pdls()
        self._register_upwork_pdls()
        self._register_fiverr_pdls()
        self._register_freelancer_pdls()
        self._register_email_pdls()
        self._register_stripe_pdls()
        self._register_shopify_pdls()
        self._register_instagram_pdls()
        self._register_sms_pdls()
        self._register_ai_pdls()

    def _register(self, pdl: PDL):
        """Register a single PDL"""
        self.pdls[pdl.name] = pdl

    # ═══════════════════════════════════════════════════════════════════════════
    # GITHUB PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_github_pdls(self):
        self._register(PDL(
            name="github.analyze_issue",
            platform="github",
            action="analyze_issue",
            description="Analyze a GitHub issue to understand requirements",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["GITHUB_TOKEN", "OPENROUTER_API_KEY"],
            endpoint="/github/analyze-issue",
            fabric_endpoint="/fabric/execute-pdl/github.analyze_issue",
            inputs={"issue_url": "str", "repo_owner": "str", "repo_name": "str", "issue_number": "int"},
            outputs={"analysis": "dict", "requirements": "list", "complexity": "str"},
            cost_model={"type": "per_call", "estimate_usd": 0.02},
            sla={"timeout_sec": 30, "retry_count": 3},
            tags=["github", "discovery", "analysis"],
            auto_execute=True,
            rate_limit={"per_hour": 100}
        ))

        self._register(PDL(
            name="github.post_comment",
            platform="github",
            action="post_comment",
            description="Post a comment on a GitHub issue",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["GITHUB_TOKEN"],
            endpoint="/github/post-comment",
            fabric_endpoint="/fabric/execute-pdl/github.post_comment",
            browser_url_template="https://github.com/{owner}/{repo}/issues/{issue_number}",
            inputs={"issue_url": "str", "comment": "str"},
            outputs={"comment_id": "str", "url": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 30, "retry_count": 3},
            tags=["github", "communication"],
            auto_execute=True,
            rate_limit={"per_hour": 50}
        ))

        self._register(PDL(
            name="github.create_branch",
            platform="github",
            action="create_branch",
            description="Create a new branch for PR submission",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["GITHUB_TOKEN"],
            endpoint="/github/create-branch",
            fabric_endpoint="/fabric/execute-pdl/github.create_branch",
            inputs={"repo_url": "str", "branch_name": "str", "base_branch": "str"},
            outputs={"branch_url": "str", "sha": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 60, "retry_count": 3},
            tags=["github", "development"],
            auto_execute=True,
            rate_limit={"per_hour": 30}
        ))

        self._register(PDL(
            name="github.submit_pr",
            platform="github",
            action="submit_pr",
            description="Submit a pull request with solution",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["GITHUB_TOKEN"],
            endpoint="/github/submit-pr",
            fabric_endpoint="/fabric/execute-pdl/github.submit_pr",
            browser_url_template="https://github.com/{owner}/{repo}/compare/{base}...{head}",
            inputs={"repo_url": "str", "title": "str", "body": "str", "head_branch": "str", "base_branch": "str"},
            outputs={"pr_number": "int", "pr_url": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 60, "retry_count": 3},
            tags=["github", "fulfillment"],
            auto_execute=True,
            max_ev_auto=500.0,  # Higher for bounties
            rate_limit={"per_hour": 20}
        ))

        self._register(PDL(
            name="github.check_pr_status",
            platform="github",
            action="check_pr_status",
            description="Check status of a submitted PR",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["GITHUB_TOKEN"],
            endpoint="/github/pr-status",
            fabric_endpoint="/fabric/execute-pdl/github.check_pr_status",
            inputs={"pr_url": "str"},
            outputs={"status": "str", "merged": "bool", "reviews": "list"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 30, "retry_count": 3},
            tags=["github", "tracking"],
            auto_execute=True,
            rate_limit={"per_hour": 200}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # REDDIT PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_reddit_pdls(self):
        self._register(PDL(
            name="reddit.post_reply",
            platform="reddit",
            action="post_reply",
            description="Post a helpful reply on a Reddit thread",
            tier=PlatformTier.BROWSER,
            execution_method=ExecutionMethod.HYBRID,
            required_apis=["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"],
            optional_apis=["OPENROUTER_API_KEY"],
            endpoint="/reddit/post-reply",
            fabric_endpoint="/fabric/execute-pdl/reddit.post_reply",
            browser_url_template="{post_url}",
            inputs={"post_url": "str", "reply_text": "str", "subreddit": "str"},
            outputs={"comment_id": "str", "url": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 60, "retry_count": 2},
            tags=["reddit", "communication", "conversational"],
            auto_execute=True,  # Helpful replies are low risk
            rate_limit={"per_hour": 10}  # Reddit rate limits
        ))

        self._register(PDL(
            name="reddit.send_dm",
            platform="reddit",
            action="send_dm",
            description="Send a direct message on Reddit",
            tier=PlatformTier.BROWSER,
            execution_method=ExecutionMethod.HYBRID,
            required_apis=["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"],
            endpoint="/reddit/send-dm",
            fabric_endpoint="/fabric/execute-pdl/reddit.send_dm",
            browser_url_template="https://www.reddit.com/message/compose/?to={username}",
            inputs={"username": "str", "subject": "str", "message": "str"},
            outputs={"sent": "bool", "message_id": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 60, "retry_count": 2},
            tags=["reddit", "communication"],
            auto_execute=False,  # DMs require approval
            rate_limit={"per_hour": 5}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # LINKEDIN PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_linkedin_pdls(self):
        self._register(PDL(
            name="linkedin.send_connection",
            platform="linkedin",
            action="send_connection",
            description="Send a LinkedIn connection request",
            tier=PlatformTier.OAUTH,
            execution_method=ExecutionMethod.HYBRID,
            required_apis=["LINKEDIN_ACCESS_TOKEN"],
            optional_apis=["LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET"],
            endpoint="/linkedin/connect",
            fabric_endpoint="/fabric/execute-pdl/linkedin.send_connection",
            browser_url_template="https://www.linkedin.com/in/{profile_id}",
            inputs={"profile_url": "str", "note": "str"},
            outputs={"sent": "bool", "connection_id": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 60, "retry_count": 2},
            tags=["linkedin", "communication", "conversational"],
            auto_execute=False,  # Requires approval
            rate_limit={"per_hour": 20}  # LinkedIn strict limits
        ))

        self._register(PDL(
            name="linkedin.send_message",
            platform="linkedin",
            action="send_message",
            description="Send a LinkedIn message to a connection",
            tier=PlatformTier.OAUTH,
            execution_method=ExecutionMethod.HYBRID,
            required_apis=["LINKEDIN_ACCESS_TOKEN"],
            endpoint="/linkedin/send-message",
            fabric_endpoint="/fabric/execute-pdl/linkedin.send_message",
            browser_url_template="https://www.linkedin.com/messaging/compose/?recipient={profile_id}",
            inputs={"profile_url": "str", "message": "str"},
            outputs={"sent": "bool", "message_id": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 60, "retry_count": 2},
            tags=["linkedin", "communication"],
            auto_execute=False,
            rate_limit={"per_hour": 30}
        ))

        self._register(PDL(
            name="linkedin.get_profile",
            platform="linkedin",
            action="get_profile",
            description="Get LinkedIn profile information",
            tier=PlatformTier.OAUTH,
            execution_method=ExecutionMethod.HYBRID,
            required_apis=["LINKEDIN_ACCESS_TOKEN"],
            endpoint="/linkedin/profile",
            fabric_endpoint="/fabric/execute-pdl/linkedin.get_profile",
            inputs={"profile_url": "str"},
            outputs={"name": "str", "title": "str", "company": "str", "skills": "list"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 30, "retry_count": 3},
            tags=["linkedin", "discovery"],
            auto_execute=True,
            rate_limit={"per_hour": 100}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # TWITTER PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_twitter_pdls(self):
        self._register(PDL(
            name="twitter.post_reply",
            platform="twitter",
            action="post_reply",
            description="Post a reply to a tweet",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.HYBRID,
            required_apis=["TWITTER_BEARER_TOKEN"],
            optional_apis=["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"],
            endpoint="/twitter/post-reply",
            fabric_endpoint="/fabric/execute-pdl/twitter.post_reply",
            browser_url_template="{tweet_url}",
            inputs={"tweet_url": "str", "reply_text": "str"},
            outputs={"tweet_id": "str", "url": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 30, "retry_count": 2},
            tags=["twitter", "communication"],
            auto_execute=True,
            rate_limit={"per_hour": 25}
        ))

        self._register(PDL(
            name="twitter.send_dm",
            platform="twitter",
            action="send_dm",
            description="Send a Twitter direct message",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.HYBRID,
            required_apis=["TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"],
            endpoint="/twitter/send-dm",
            fabric_endpoint="/fabric/execute-pdl/twitter.send_dm",
            browser_url_template="https://twitter.com/messages/compose?recipient_id={user_id}",
            inputs={"user_id": "str", "message": "str"},
            outputs={"dm_id": "str", "sent": "bool"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 30, "retry_count": 2},
            tags=["twitter", "communication"],
            auto_execute=False,
            rate_limit={"per_hour": 15}
        ))

        self._register(PDL(
            name="twitter.post_tweet",
            platform="twitter",
            action="post_tweet",
            description="Post a new tweet",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.HYBRID,
            required_apis=["TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"],
            endpoint="/twitter/post",
            fabric_endpoint="/fabric/execute-pdl/twitter.post_tweet",
            browser_url_template="https://twitter.com/compose/tweet",
            inputs={"text": "str", "media_ids": "list"},
            outputs={"tweet_id": "str", "url": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 30, "retry_count": 2},
            tags=["twitter", "content_posting"],
            auto_execute=True,
            rate_limit={"per_hour": 25}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # HACKERNEWS PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_hackernews_pdls(self):
        self._register(PDL(
            name="hackernews.post_comment",
            platform="hackernews",
            action="post_comment",
            description="Post a comment on HackerNews",
            tier=PlatformTier.BROWSER,
            execution_method=ExecutionMethod.BROWSER,
            required_apis=["HN_USERNAME", "HN_PASSWORD"],
            optional_apis=["OPENROUTER_API_KEY"],
            endpoint="/hackernews/post-comment",
            fabric_endpoint="/fabric/execute-pdl/hackernews.post_comment",
            browser_url_template="https://news.ycombinator.com/item?id={item_id}",
            inputs={"item_id": "str", "comment_text": "str"},
            outputs={"comment_id": "str", "url": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 60, "retry_count": 2},
            tags=["hackernews", "communication", "conversational"],
            auto_execute=False,  # HN requires careful moderation
            rate_limit={"per_hour": 5}  # Very conservative
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # UPWORK PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_upwork_pdls(self):
        self._register(PDL(
            name="upwork.submit_proposal",
            platform="upwork",
            action="submit_proposal",
            description="Submit a proposal on Upwork",
            tier=PlatformTier.BROWSER,
            execution_method=ExecutionMethod.UNIVERSAL_FABRIC,
            required_apis=["UPWORK_USERNAME", "UPWORK_PASSWORD"],
            optional_apis=["OPENROUTER_API_KEY"],
            endpoint="/upwork/submit-proposal",
            fabric_endpoint="/fabric/execute-pdl/upwork.submit_proposal",
            browser_url_template="{job_url}",
            inputs={"job_url": "str", "cover_letter": "str", "bid_amount": "float", "duration": "str"},
            outputs={"proposal_id": "str", "submitted": "bool"},
            cost_model={"type": "per_connect", "estimate_usd": 0.30},  # Upwork connects cost
            sla={"timeout_sec": 120, "retry_count": 2},
            tags=["upwork", "proposal", "marketplace"],
            auto_execute=False,  # Requires human review
            max_ev_auto=0,  # Never auto-execute
            rate_limit={"per_hour": 5}
        ))

        self._register(PDL(
            name="upwork.send_message",
            platform="upwork",
            action="send_message",
            description="Send a message to an Upwork client",
            tier=PlatformTier.BROWSER,
            execution_method=ExecutionMethod.UNIVERSAL_FABRIC,
            required_apis=["UPWORK_USERNAME", "UPWORK_PASSWORD"],
            endpoint="/upwork/send-message",
            fabric_endpoint="/fabric/execute-pdl/upwork.send_message",
            browser_url_template="https://www.upwork.com/messages/rooms/{room_id}",
            inputs={"room_id": "str", "message": "str"},
            outputs={"sent": "bool", "message_id": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 60, "retry_count": 2},
            tags=["upwork", "communication"],
            auto_execute=False,
            rate_limit={"per_hour": 20}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # FIVERR PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_fiverr_pdls(self):
        self._register(PDL(
            name="fiverr.submit_offer",
            platform="fiverr",
            action="submit_offer",
            description="Submit a custom offer on Fiverr",
            tier=PlatformTier.BROWSER,
            execution_method=ExecutionMethod.UNIVERSAL_FABRIC,
            required_apis=["FIVERR_USERNAME", "FIVERR_PASSWORD"],
            optional_apis=["OPENROUTER_API_KEY"],
            endpoint="/fiverr/submit-offer",
            fabric_endpoint="/fabric/execute-pdl/fiverr.submit_offer",
            browser_url_template="{request_url}",
            inputs={"request_url": "str", "offer_description": "str", "price": "float", "delivery_days": "int"},
            outputs={"offer_id": "str", "submitted": "bool"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 120, "retry_count": 2},
            tags=["fiverr", "proposal", "marketplace"],
            auto_execute=False,
            rate_limit={"per_hour": 10}
        ))

        self._register(PDL(
            name="fiverr.send_message",
            platform="fiverr",
            action="send_message",
            description="Send a message to a Fiverr buyer",
            tier=PlatformTier.BROWSER,
            execution_method=ExecutionMethod.UNIVERSAL_FABRIC,
            required_apis=["FIVERR_USERNAME", "FIVERR_PASSWORD"],
            endpoint="/fiverr/send-message",
            fabric_endpoint="/fabric/execute-pdl/fiverr.send_message",
            browser_url_template="https://www.fiverr.com/inbox/{conversation_id}",
            inputs={"conversation_id": "str", "message": "str"},
            outputs={"sent": "bool"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 60, "retry_count": 2},
            tags=["fiverr", "communication"],
            auto_execute=False,
            rate_limit={"per_hour": 20}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # FREELANCER PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_freelancer_pdls(self):
        self._register(PDL(
            name="freelancer.submit_bid",
            platform="freelancer",
            action="submit_bid",
            description="Submit a bid on Freelancer.com",
            tier=PlatformTier.BROWSER,
            execution_method=ExecutionMethod.UNIVERSAL_FABRIC,
            required_apis=["FREELANCER_USERNAME", "FREELANCER_PASSWORD"],
            optional_apis=["OPENROUTER_API_KEY"],
            endpoint="/freelancer/submit-bid",
            fabric_endpoint="/fabric/execute-pdl/freelancer.submit_bid",
            browser_url_template="{project_url}",
            inputs={"project_url": "str", "description": "str", "bid_amount": "float", "period": "int"},
            outputs={"bid_id": "str", "submitted": "bool"},
            cost_model={"type": "per_bid", "estimate_usd": 0.50},
            sla={"timeout_sec": 120, "retry_count": 2},
            tags=["freelancer", "proposal", "marketplace"],
            auto_execute=False,
            rate_limit={"per_hour": 5}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # EMAIL PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_email_pdls(self):
        self._register(PDL(
            name="email.send",
            platform="email",
            action="send",
            description="Send an email via Resend",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["RESEND_API_KEY"],
            endpoint="/email/send",
            fabric_endpoint="/fabric/execute-pdl/email.send",
            inputs={"to": "str", "subject": "str", "body": "str", "html": "str"},
            outputs={"email_id": "str", "sent": "bool"},
            cost_model={"type": "per_email", "estimate_usd": 0.001},
            sla={"timeout_sec": 30, "retry_count": 3},
            tags=["email", "communication"],
            auto_execute=False,  # Email requires consent
            rate_limit={"per_hour": 100}
        ))

        self._register(PDL(
            name="email.send_outreach",
            platform="email",
            action="send_outreach",
            description="Send a personalized outreach email",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["RESEND_API_KEY", "OPENROUTER_API_KEY"],
            endpoint="/email/send-outreach",
            fabric_endpoint="/fabric/execute-pdl/email.send_outreach",
            inputs={"to": "str", "opportunity": "dict", "pitch_style": "str"},
            outputs={"email_id": "str", "sent": "bool", "pitch_generated": "str"},
            cost_model={"type": "per_email", "estimate_usd": 0.02},
            sla={"timeout_sec": 60, "retry_count": 3},
            tags=["email", "communication", "ai_enhanced"],
            auto_execute=False,
            rate_limit={"per_hour": 50}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # STRIPE PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_stripe_pdls(self):
        self._register(PDL(
            name="stripe.create_payment_link",
            platform="stripe",
            action="create_payment_link",
            description="Create a Stripe payment link",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["STRIPE_SECRET_KEY"],
            endpoint="/wade/payment-link",
            fabric_endpoint="/fabric/execute-pdl/stripe.create_payment_link",
            inputs={"amount": "float", "currency": "str", "description": "str", "customer_email": "str"},
            outputs={"payment_link": "str", "payment_id": "str"},
            cost_model={"type": "percentage", "estimate_pct": 2.9},
            sla={"timeout_sec": 30, "retry_count": 3},
            tags=["stripe", "payment"],
            auto_execute=True,
            rate_limit={"per_hour": 100}
        ))

        self._register(PDL(
            name="stripe.send_invoice",
            platform="stripe",
            action="send_invoice",
            description="Send a Stripe invoice",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["STRIPE_SECRET_KEY"],
            endpoint="/stripe/send-invoice",
            fabric_endpoint="/fabric/execute-pdl/stripe.send_invoice",
            inputs={"customer_email": "str", "items": "list", "due_days": "int"},
            outputs={"invoice_id": "str", "invoice_url": "str"},
            cost_model={"type": "percentage", "estimate_pct": 2.9},
            sla={"timeout_sec": 30, "retry_count": 3},
            tags=["stripe", "payment", "invoicing"],
            auto_execute=False,
            rate_limit={"per_hour": 50}
        ))

        self._register(PDL(
            name="stripe.check_payment_status",
            platform="stripe",
            action="check_payment_status",
            description="Check Stripe payment status",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["STRIPE_SECRET_KEY"],
            endpoint="/stripe/payment-status",
            fabric_endpoint="/fabric/execute-pdl/stripe.check_payment_status",
            inputs={"payment_id": "str"},
            outputs={"status": "str", "paid": "bool", "amount": "float"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 15, "retry_count": 3},
            tags=["stripe", "payment", "tracking"],
            auto_execute=True,
            rate_limit={"per_hour": 500}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # SHOPIFY PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_shopify_pdls(self):
        self._register(PDL(
            name="shopify.create_product",
            platform="shopify",
            action="create_product",
            description="Create a Shopify product listing",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["SHOPIFY_ACCESS_TOKEN", "SHOPIFY_SHOP_DOMAIN"],
            endpoint="/shopify/create-product",
            fabric_endpoint="/fabric/execute-pdl/shopify.create_product",
            inputs={"title": "str", "description": "str", "price": "float", "images": "list"},
            outputs={"product_id": "str", "handle": "str", "url": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 60, "retry_count": 3},
            tags=["shopify", "ecommerce", "arbitrage"],
            auto_execute=False,  # Product creation requires approval
            rate_limit={"per_hour": 50}
        ))

        self._register(PDL(
            name="shopify.fulfill_order",
            platform="shopify",
            action="fulfill_order",
            description="Fulfill a Shopify order",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["SHOPIFY_ACCESS_TOKEN", "SHOPIFY_SHOP_DOMAIN"],
            endpoint="/shopify/fulfill",
            fabric_endpoint="/fabric/execute-pdl/shopify.fulfill_order",
            inputs={"order_id": "str", "tracking_number": "str", "carrier": "str"},
            outputs={"fulfillment_id": "str", "status": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 30, "retry_count": 3},
            tags=["shopify", "ecommerce", "fulfillment"],
            auto_execute=True,
            rate_limit={"per_hour": 100}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # INSTAGRAM PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_instagram_pdls(self):
        self._register(PDL(
            name="instagram.post_content",
            platform="instagram",
            action="post_content",
            description="Post content to Instagram",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.HYBRID,
            required_apis=["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ID"],
            endpoint="/instagram/post",
            fabric_endpoint="/fabric/execute-pdl/instagram.post_content",
            browser_url_template="https://www.instagram.com/",
            inputs={"image_url": "str", "caption": "str", "hashtags": "list"},
            outputs={"post_id": "str", "url": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 60, "retry_count": 2},
            tags=["instagram", "content_posting", "social"],
            auto_execute=True,
            rate_limit={"per_hour": 10}
        ))

        self._register(PDL(
            name="instagram.reply_comment",
            platform="instagram",
            action="reply_comment",
            description="Reply to an Instagram comment",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.HYBRID,
            required_apis=["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ID"],
            endpoint="/instagram/reply",
            fabric_endpoint="/fabric/execute-pdl/instagram.reply_comment",
            inputs={"comment_id": "str", "reply_text": "str"},
            outputs={"reply_id": "str"},
            cost_model={"type": "free", "estimate_usd": 0},
            sla={"timeout_sec": 30, "retry_count": 2},
            tags=["instagram", "communication"],
            auto_execute=True,
            rate_limit={"per_hour": 30}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # SMS PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_sms_pdls(self):
        self._register(PDL(
            name="sms.send",
            platform="sms",
            action="send",
            description="Send SMS via Twilio",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
            endpoint="/sms/send",
            fabric_endpoint="/fabric/execute-pdl/sms.send",
            inputs={"to": "str", "message": "str"},
            outputs={"message_id": "str", "status": "str"},
            cost_model={"type": "per_sms", "estimate_usd": 0.01},
            sla={"timeout_sec": 30, "retry_count": 3},
            tags=["sms", "communication"],
            auto_execute=False,  # SMS requires consent
            rate_limit={"per_hour": 50}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # AI PDLs
    # ═══════════════════════════════════════════════════════════════════════════

    def _register_ai_pdls(self):
        self._register(PDL(
            name="ai.generate_code",
            platform="ai",
            action="generate_code",
            description="Generate code using AI",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["OPENROUTER_API_KEY"],
            optional_apis=["GEMINI_API_KEY", "ANTHROPIC_API_KEY"],
            endpoint="/fulfillment/code-generation",
            fabric_endpoint="/fabric/execute-pdl/ai.generate_code",
            inputs={"prompt": "str", "language": "str", "context": "dict"},
            outputs={"code": "str", "explanation": "str"},
            cost_model={"type": "per_token", "estimate_usd": 0.03},
            sla={"timeout_sec": 120, "retry_count": 2},
            tags=["ai", "fulfillment", "code"],
            auto_execute=True,
            rate_limit={"per_hour": 100}
        ))

        self._register(PDL(
            name="ai.generate_pitch",
            platform="ai",
            action="generate_pitch",
            description="Generate a sales pitch using AI",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["OPENROUTER_API_KEY"],
            optional_apis=["GEMINI_API_KEY"],
            endpoint="/ame/generate-pitch",
            fabric_endpoint="/fabric/execute-pdl/ai.generate_pitch",
            inputs={"opportunity": "dict", "style": "str", "max_length": "int"},
            outputs={"pitch": "str", "key_points": "list"},
            cost_model={"type": "per_token", "estimate_usd": 0.02},
            sla={"timeout_sec": 60, "retry_count": 2},
            tags=["ai", "communication", "sales"],
            auto_execute=True,
            rate_limit={"per_hour": 200}
        ))

        self._register(PDL(
            name="ai.analyze_opportunity",
            platform="ai",
            action="analyze_opportunity",
            description="Analyze an opportunity using AI",
            tier=PlatformTier.API,
            execution_method=ExecutionMethod.API,
            required_apis=["OPENROUTER_API_KEY"],
            optional_apis=["PERPLEXITY_API_KEY"],
            endpoint="/ame/analyze-opportunity",
            fabric_endpoint="/fabric/execute-pdl/ai.analyze_opportunity",
            inputs={"opportunity": "dict"},
            outputs={"analysis": "dict", "ev_estimate": "float", "recommended_action": "str"},
            cost_model={"type": "per_call", "estimate_usd": 0.02},
            sla={"timeout_sec": 45, "retry_count": 2},
            tags=["ai", "analysis", "discovery"],
            auto_execute=True,
            rate_limit={"per_hour": 300}
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # CATALOG QUERY METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def get(self, name: str) -> Optional[PDL]:
        """Get PDL by name"""
        return self.pdls.get(name)

    def all(self) -> List[PDL]:
        """Get all PDLs"""
        return list(self.pdls.values())

    def by_platform(self, platform: str) -> List[PDL]:
        """Get all PDLs for a platform"""
        return [pdl for pdl in self.pdls.values() if pdl.platform == platform]

    def by_tag(self, tag: str) -> List[PDL]:
        """Get all PDLs with a tag"""
        return [pdl for pdl in self.pdls.values() if tag in pdl.tags]

    def executable(self) -> List[PDL]:
        """Get all PDLs that can currently execute (APIs configured)"""
        return [pdl for pdl in self.pdls.values() if pdl.can_execute()]

    def auto_executable(self) -> List[PDL]:
        """Get all PDLs that can auto-execute"""
        return [pdl for pdl in self.pdls.values() if pdl.auto_execute and pdl.can_execute()]

    def by_execution_method(self, method: ExecutionMethod) -> List[PDL]:
        """Get all PDLs by execution method"""
        return [pdl for pdl in self.pdls.values() if pdl.get_execution_method() == method]

    def summary(self) -> Dict[str, Any]:
        """Get catalog summary"""
        all_pdls = self.all()
        executable = self.executable()
        auto_exec = self.auto_executable()

        by_platform = {}
        for pdl in all_pdls:
            if pdl.platform not in by_platform:
                by_platform[pdl.platform] = {"total": 0, "executable": 0, "auto": 0}
            by_platform[pdl.platform]["total"] += 1
            if pdl.can_execute():
                by_platform[pdl.platform]["executable"] += 1
            if pdl.auto_execute and pdl.can_execute():
                by_platform[pdl.platform]["auto"] += 1

        by_method = {}
        for pdl in all_pdls:
            method = pdl.get_execution_method().value
            by_method[method] = by_method.get(method, 0) + 1

        return {
            "total_pdls": len(all_pdls),
            "executable_pdls": len(executable),
            "auto_executable_pdls": len(auto_exec),
            "by_platform": by_platform,
            "by_execution_method": by_method,
            "platforms": list(by_platform.keys())
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_catalog: Optional[PDLCatalog] = None

def get_pdl_catalog() -> PDLCatalog:
    """Get the singleton PDL catalog instance"""
    global _catalog
    if _catalog is None:
        _catalog = PDLCatalog()
    return _catalog


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_pdl(name: str) -> Optional[PDL]:
    """Get a PDL by name"""
    return get_pdl_catalog().get(name)

def can_execute_pdl(name: str) -> bool:
    """Check if a PDL can execute"""
    pdl = get_pdl(name)
    return pdl.can_execute() if pdl else False

def get_pdl_for_action(platform: str, action: str) -> Optional[PDL]:
    """Get PDL for a platform action"""
    return get_pdl(f"{platform}.{action}")


print("📋 PDL CATALOG LOADED")
print(f"   • Total PDLs: {len(get_pdl_catalog().all())}")
print(f"   • Executable: {len(get_pdl_catalog().executable())}")
print(f"   • Auto-executable: {len(get_pdl_catalog().auto_executable())}")
