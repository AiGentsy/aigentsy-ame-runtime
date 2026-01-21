"""
AUTO-BIDDING ORCHESTRATOR
Combines Options A, B, C into unified system:
- Option A: Auto-apply where APIs available (GitHub, Upwork, Reddit)
- Option B: Generate proposals for manual submission (shown in dashboard)
- Option C: Email-based outreach for opportunities without APIs

Integration: Called after Wade approves an opportunity
"""

import asyncio
import httpx
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum

# Integration hooks for monetization + brain
try:
    from integration_hooks import IntegrationHooks
    from monetization.fee_schedule import get_fee
    _hooks = IntegrationHooks("auto_bidding")
except ImportError:
    _hooks = None


class BiddingChannel(str, Enum):
    API_AUTO = "api_auto"           # Full automation (GitHub, Upwork API)
    EMAIL_AUTO = "email_auto"       # Email-based (jobs with email contacts)
    MANUAL_ASSISTED = "manual"      # Generate proposal, Wade copies/pastes
    DM_AUTO = "dm_auto"            # Direct message (Reddit, LinkedIn)


class PlatformConfig:
    """Configuration for each platform's bidding approach"""
    
    CONFIGS = {
        "github": {
            "channel": BiddingChannel.API_AUTO,
            "api_available": True,
            "requires_token": "GITHUB_TOKEN",
            "submit_function": "submit_github_bid",
            "check_approval": "check_github_approval"
        },
        "upwork": {
            "channel": BiddingChannel.API_AUTO,
            "api_available": True,
            "requires_token": "UPWORK_API_KEY",
            "submit_function": "submit_upwork_proposal",
            "oauth_required": True
        },
        "freelancer": {
            "channel": BiddingChannel.API_AUTO,
            "api_available": True,
            "requires_token": "FREELANCER_API_KEY"
        },
        "reddit": {
            "channel": BiddingChannel.DM_AUTO,
            "api_available": True,
            "requires_token": "REDDIT_CLIENT_ID",
            "submit_function": "submit_reddit_dm"
        },
        "linkedin_jobs": {
            "channel": BiddingChannel.EMAIL_AUTO,
            "api_available": False,
            "fallback": BiddingChannel.MANUAL_ASSISTED,
            "extract_email": True
        },
        "hackernews": {
            "channel": BiddingChannel.EMAIL_AUTO,
            "extract_email": True
        },
        "indiehackers": {
            "channel": BiddingChannel.EMAIL_AUTO,
            "extract_email": True
        },
        "stackoverflow": {
            "channel": BiddingChannel.MANUAL_ASSISTED,
            "api_available": False
        }
    }
    
    @classmethod
    def get_channel(cls, platform: str) -> BiddingChannel:
        """Determine best bidding channel for platform"""
        config = cls.CONFIGS.get(platform, {})
        
        # Check if API token available
        if config.get("api_available"):
            token_var = config.get("requires_token")
            if token_var and os.getenv(token_var):
                return config.get("channel", BiddingChannel.API_AUTO)
        
        # Fall back to email or manual
        if config.get("extract_email"):
            return BiddingChannel.EMAIL_AUTO
        
        return config.get("fallback", BiddingChannel.MANUAL_ASSISTED)


# ============================================================
# PROPOSAL GENERATOR - Universal for All Channels
# ============================================================

async def generate_proposal(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate AI-powered proposal using Claude
    Works for all channels - API, email, manual
    """
    
    title = opportunity.get('title', 'Opportunity')
    description = opportunity.get('description', '')
    value = opportunity.get('estimated_value', 5000)
    opp_type = opportunity.get('type', 'job')
    
    # Get fulfillability data
    fulfillability = opportunity.get('fulfillability', {})
    delivery_days = fulfillability.get('delivery_days', 7)
    confidence = fulfillability.get('confidence', 0.8)
    
    # Template selection based on type
    if opp_type in ['code', 'development', 'programming', 'job']:
        template_type = "technical"
    elif opp_type in ['design', 'creative']:
        template_type = "creative"
    elif opp_type in ['writing', 'content']:
        template_type = "content"
    else:
        template_type = "general"
    
    proposals = {
        "technical": f"""Hi there!

I can help with "{title}".

**My Approach:**
• Claude Sonnet 4 (best-in-class AI for coding)
• Clean, production-ready code with documentation
• Full testing & error handling
• {delivery_days}-day delivery

**Deliverables:**
✓ Complete solution with source code
✓ Documentation & deployment guide
✓ Post-delivery support

**Timeline:** {delivery_days} days
**Investment:** ${value:,}

I'm ready to start immediately. Let's build something great!

Best regards,
Wade (AiGentsy)
""",
        
        "creative": f"""Hi!

I'd love to work on "{title}".

**What I Offer:**
• AI-powered design tools (best-in-class)
• Professional, modern aesthetics
• Multiple concepts & revisions
• {delivery_days}-day delivery

**Deliverables:**
✓ High-quality designs in all formats
✓ Source files included
✓ Unlimited revisions until satisfied

**Timeline:** {delivery_days} days
**Investment:** ${value:,}

Let's create something amazing!

Wade (AiGentsy)
""",
        
        "content": f"""Hello!

I can deliver excellent content for "{title}".

**My Process:**
• AI-powered content generation (Claude)
• SEO-optimized writing
• Professional tone & style
• {delivery_days}-day delivery

**What You Get:**
✓ Original, engaging content
✓ SEO optimization
✓ Revisions included
✓ Fast turnaround

**Timeline:** {delivery_days} days
**Investment:** ${value:,}

Ready to start writing!

Wade (AiGentsy)
""",
        
        "general": f"""Hi!

I'm interested in "{title}".

**What I Bring:**
• Professional service delivery
• Fast turnaround ({delivery_days} days)
• High-quality results
• Post-project support

**Timeline:** {delivery_days} days
**Investment:** ${value:,}

I'm ready to discuss the details and get started.

Best,
Wade (AiGentsy)
"""
    }
    
    proposal_text = proposals.get(template_type, proposals["general"])
    
    return {
        "proposal_text": proposal_text.strip(),
        "template_type": template_type,
        "word_count": len(proposal_text.split()),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


# ============================================================
# CHANNEL A: API AUTO-BIDDING
# ============================================================

async def submit_via_api(
    opportunity: Dict[str, Any],
    proposal: Dict[str, Any],
    platform: str
) -> Dict[str, Any]:
    """
    Submit bid via platform API
    Currently supports: GitHub, Reddit
    """
    
    if platform == "github":
        return await submit_github_bid(opportunity, proposal)
    elif platform == "reddit":
        return await submit_reddit_dm(opportunity, proposal)
    elif platform == "upwork":
        return await submit_upwork_proposal(opportunity, proposal)
    else:
        return {
            "success": False,
            "error": f"API submission not implemented for {platform}",
            "fallback": "manual"
        }


async def submit_github_bid(opportunity: Dict[str, Any], proposal: Dict[str, Any]) -> Dict[str, Any]:
    """Submit to GitHub by commenting on issue"""
    
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return {"success": False, "error": "GITHUB_TOKEN not set", "fallback": "manual"}
    
    try:
        # Parse GitHub URL
        url = opportunity['url']
        parts = url.split('/')
        owner, repo, issue_num = parts[-4], parts[-3], parts[-1]
        
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}/comments"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                headers={
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={"body": proposal['proposal_text']},
                timeout=15
            )
            
            if response.status_code == 201:
                return {
                    "success": True,
                    "method": "github_api",
                    "comment_url": response.json()['html_url'],
                    "submitted_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"GitHub API: {response.status_code}",
                    "fallback": "manual"
                }
    
    except Exception as e:
        return {"success": False, "error": str(e), "fallback": "manual"}


async def submit_reddit_dm(opportunity: Dict[str, Any], proposal: Dict[str, Any]) -> Dict[str, Any]:
    """Submit Reddit DM or comment"""
    
    # TODO: Implement Reddit OAuth + message sending
    return {
        "success": False,
        "error": "Reddit API not yet implemented",
        "fallback": "manual"
    }


async def submit_upwork_proposal(opportunity: Dict[str, Any], proposal: Dict[str, Any]) -> Dict[str, Any]:
    """Submit Upwork proposal via API"""
    
    # TODO: Implement Upwork OAuth + proposal submission
    return {
        "success": False,
        "error": "Upwork API requires OAuth setup",
        "fallback": "manual"
    }


# ============================================================
# CHANNEL B: EMAIL AUTO-BIDDING
# ============================================================

async def submit_via_email(
    opportunity: Dict[str, Any],
    proposal: Dict[str, Any],
    email_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send proposal via email
    Requires: SENDGRID_API_KEY or RESEND_API_KEY
    """
    
    if not email_address:
        email_address = opportunity.get('contact_email')
    
    if not email_address:
        return {
            "success": False,
            "error": "No email address found",
            "fallback": "manual"
        }
    
    # Check for email service
    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    resend_key = os.getenv("RESEND_API_KEY")
    
    if resend_key:
        return await send_via_resend(email_address, opportunity, proposal)
    elif sendgrid_key:
        return await send_via_sendgrid(email_address, opportunity, proposal)
    else:
        return {
            "success": False,
            "error": "No email service configured",
            "email_draft": {
                "to": email_address,
                "subject": f"Re: {opportunity.get('title')}",
                "body": proposal['proposal_text']
            },
            "fallback": "manual"
        }


async def send_via_resend(email: str, opportunity: Dict, proposal: Dict) -> Dict:
    """Send email via Resend API"""
    
    resend_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("AIGENTSY_FROM_EMAIL", "hello@aigentsy.com")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": from_email,
                    "to": email,
                    "subject": f"Proposal: {opportunity.get('title')}",
                    "text": proposal['proposal_text']
                },
                timeout=15
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "method": "resend_email",
                    "email_id": response.json().get('id'),
                    "submitted_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Resend API: {response.status_code}",
                    "fallback": "manual"
                }
    
    except Exception as e:
        return {"success": False, "error": str(e), "fallback": "manual"}


async def send_via_sendgrid(email: str, opportunity: Dict, proposal: Dict) -> Dict:
    """Send email via SendGrid"""
    
    # TODO: Implement SendGrid
    return {"success": False, "error": "SendGrid not implemented", "fallback": "manual"}


# ============================================================
# CHANNEL C: MANUAL-ASSISTED (Dashboard Display)
# ============================================================

def prepare_manual_submission(
    opportunity: Dict[str, Any],
    proposal: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Prepare everything Wade needs to manually apply
    Shows in approval dashboard
    """
    
    return {
        "method": "manual",
        "opportunity_url": opportunity['url'],
        "proposal_text": proposal['proposal_text'],
        "instructions": f"""
📋 MANUAL APPLICATION REQUIRED

1. Visit: {opportunity['url']}
2. Click "Apply" or "Submit Proposal"
3. Copy this proposal:

--- START PROPOSAL ---
{proposal['proposal_text']}
--- END PROPOSAL ---

4. Paste and submit
5. Mark as submitted in dashboard
        """.strip(),
        "ready_to_copy": True,
        "platform": opportunity.get('source', 'unknown')
    }


# ============================================================
# MASTER ORCHESTRATOR
# ============================================================

async def auto_bid_on_opportunity(
    opportunity: Dict[str, Any],
    force_manual: bool = False
) -> Dict[str, Any]:
    """
    Master function: Routes to appropriate bidding channel
    Called after Wade approves an opportunity
    
    Returns:
        {
            "success": bool,
            "method": "api_auto" | "email_auto" | "manual",
            "submitted": bool,
            "proposal": {...},
            "submission_result": {...},
            "dashboard_display": {...}  # For manual review
        }
    """
    
    platform = opportunity.get('source', 'unknown')
    
    # Generate proposal first (used by all channels)
    proposal = await generate_proposal(opportunity)
    
    # Determine channel
    if force_manual:
        channel = BiddingChannel.MANUAL_ASSISTED
    else:
        channel = PlatformConfig.get_channel(platform)
    
    result = {
        "opportunity_id": opportunity['id'],
        "platform": platform,
        "channel": channel,
        "proposal": proposal,
        "submitted": False,
        "submitted_at": None
    }
    
    # Route to appropriate handler
    if channel == BiddingChannel.API_AUTO:
        submission = await submit_via_api(opportunity, proposal, platform)
        result["submission_result"] = submission
        result["submitted"] = submission.get("success", False)
        
        if not result["submitted"]:
            # Fallback to manual
            result["dashboard_display"] = prepare_manual_submission(opportunity, proposal)
    
    elif channel == BiddingChannel.EMAIL_AUTO:
        submission = await submit_via_email(opportunity, proposal)
        result["submission_result"] = submission
        result["submitted"] = submission.get("success", False)
        
        if not result["submitted"]:
            # Fallback to manual
            result["dashboard_display"] = prepare_manual_submission(opportunity, proposal)
    
    else:  # MANUAL_ASSISTED
        result["dashboard_display"] = prepare_manual_submission(opportunity, proposal)
        result["method"] = "manual"
    
    # Add submission timestamp
    if result["submitted"]:
        result["submitted_at"] = datetime.now(timezone.utc).isoformat()

        # Emit bid placed event to brain/monetization
        if _hooks:
            try:
                _hooks.on_bid_placed(
                    result,
                    opportunity_id=opportunity.get('id'),
                    bid_amount=opportunity.get('estimated_value', 0)
                )
            except Exception:
                pass  # Don't fail bidding on hook errors

    return result


# ============================================================
# BATCH BIDDING
# ============================================================

async def batch_auto_bid(opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Bid on multiple opportunities in parallel
    """
    
    tasks = [auto_bid_on_opportunity(opp) for opp in opportunities]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Categorize results
    submitted = []
    manual_required = []
    errors = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            errors.append({
                "opportunity_id": opportunities[i]['id'],
                "error": str(result)
            })
        elif result.get("submitted"):
            submitted.append(result)
        else:
            manual_required.append(result)
    
    return {
        "total": len(opportunities),
        "auto_submitted": len(submitted),
        "manual_required": len(manual_required),
        "errors": len(errors),
        "submitted_details": submitted,
        "manual_details": manual_required,
        "error_details": errors
    }
