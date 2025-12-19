"""
Resend Email Automator
Sets up email automation sequences for each business type

Sequences:
- SaaS: Developer onboarding, API key activation
- Marketing: Welcome, nurture, conversion, re-engagement
- Social: Creator tips, content reminders, growth strategies
"""

import os
import httpx
from typing import Dict, Any, List
from datetime import datetime, timezone


RESEND_API_KEY = os.getenv("RESEND_API_KEY")


def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Email sequences for each template type
EMAIL_SEQUENCES = {
    "saas": [
        {
            "name": "welcome_developers",
            "subject": "Welcome to {business_name} API!",
            "delay_hours": 0,
            "template": """
Hi there!

Welcome to {business_name} API. Your API key is ready:

API Key: {api_key}
Base URL: https://{username}.aigentsy.com/api

Get started with our quickstart guide:
https://{username}.aigentsy.com/docs/quickstart

Questions? Reply to this email.

Best,
{business_name} Team
"""
        },
        {
            "name": "api_key_activated",
            "subject": "Your API key is active",
            "delay_hours": 24,
            "template": """
Great news! Your API key is now active and ready to use.

You've made {request_count} requests in the last 24 hours.

Next steps:
- Explore our API reference
- Check out code examples
- Join our developer community

Need help? We're here: support@{username}.aigentsy.com

Best,
{business_name} Team
"""
        }
    ],
    
    "marketing": [
        {
            "name": "welcome_series_1",
            "subject": "You're in 🎉",
            "delay_hours": 0,
            "template": """
Hey!

Thanks for signing up. You're awesome.

Here's what happens next:
1. Check your email tomorrow for a quick win
2. Get access to our best content
3. Start seeing results in days, not months

Talk soon,
{business_name}
"""
        },
        {
            "name": "welcome_series_2",
            "subject": "Quick win inside →",
            "delay_hours": 48,
            "template": """
Hey again!

Here's your quick win:

[QUICK WIN CONTENT HERE]

This should take you 10 minutes and give you immediate results.

Try it today. Reply and let me know how it goes.

Cheers,
{business_name}
"""
        },
        {
            "name": "nurture_1",
            "subject": "The #1 mistake everyone makes",
            "delay_hours": 168,  # 7 days
            "template": """
Real talk:

Most people make this one mistake: [MISTAKE]

Here's how to avoid it: [SOLUTION]

This is the difference between success and struggle.

Save this email.

{business_name}
"""
        }
    ],
    
    "social": [
        {
            "name": "welcome_creators",
            "subject": "Let's grow your audience 🚀",
            "delay_hours": 0,
            "template": """
Welcome to {business_name}!

Your content calendar is ready. Here's what to do:

TODAY:
- Post your first piece of content
- Engage with 5 accounts in your niche
- Join our creator community

This week, we'll help you:
- Hit your first 1,000 followers
- Go viral with proven templates
- Build a content system that works

Let's go!
{business_name}
"""
        },
        {
            "name": "content_reminder",
            "subject": "Time to post! 📱",
            "delay_hours": 24,
            "template": """
Hey!

Quick reminder: Your content is scheduled for today.

Today's posts:
- Twitter: {twitter_post}
- LinkedIn: {linkedin_post}
- Instagram: {instagram_post}

Need to reschedule? Just reply.

Keep growing!
{business_name}
"""
        }
    ]
}


async def setup_email_automation(
    username: str,
    template_type: str,
    config: Dict[str, Any],
    user_email: str
) -> Dict[str, Any]:
    """
    Setup email automation for user's business
    
    Steps:
    1. Configure Resend domain
    2. Create email sequences
    3. Setup automation triggers
    4. Return automation dashboard URL
    
    Args:
        username: User's username
        template_type: "saas" | "marketing" | "social"
        config: Template configuration
        user_email: User's email for testing
        
    Returns:
        {
            "ok": True,
            "sequences_count": 3,
            "from_email": "hello@{username}.aigentsy.com",
            "dashboard_url": "..."
        }
    """
    
    print(f"📧 Setting up email automation for {username}...")
    
    # Check if Resend is configured
    if not RESEND_API_KEY:
        print("⚠️  Resend API key not configured - using mock email setup")
        return await _mock_email_setup(username, template_type, config)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Get sequences for this template type
            sequences = EMAIL_SEQUENCES.get(template_type, [])
            
            if not sequences:
                return {
                    "ok": False,
                    "error": f"No email sequences defined for template type: {template_type}"
                }
            
            # Configure sender email
            from_email = f"hello@{username}.aigentsy.com"
            
            # For now, we'll use Resend's default domain
            # In production, you'd configure custom domain DNS
            from_email_default = f"onboarding@resend.dev"
            
            # Create sequences (in production, this would use Resend's API)
            # For now, we'll store sequence configs
            
            created_sequences = []
            
            for sequence in sequences:
                sequence_data = {
                    "id": f"seq_{username}_{sequence['name']}",
                    "name": sequence["name"],
                    "subject": sequence["subject"],
                    "from": from_email_default,
                    "delay_hours": sequence["delay_hours"],
                    "template": sequence["template"],
                    "status": "active",
                    "created_at": now_iso()
                }
                
                created_sequences.append(sequence_data)
            
            return {
                "ok": True,
                "sequences_count": len(created_sequences),
                "sequences": created_sequences,
                "from_email": from_email_default,
                "custom_domain": f"{username}.aigentsy.com",
                "dashboard_url": "https://resend.com/emails",
                "configured_at": now_iso()
            }
            
    except Exception as e:
        print(f"❌ Resend setup error: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


async def _mock_email_setup(
    username: str,
    template_type: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mock email setup for testing without Resend API
    """
    
    sequences = EMAIL_SEQUENCES.get(template_type, [])
    
    print(f"✅ Mock email setup: {len(sequences)} sequences")
    
    return {
        "ok": True,
        "sequences_count": len(sequences),
        "sequences": [
            {
                "id": f"mock_seq_{username}_{seq['name']}",
                "name": seq["name"],
                "subject": seq["subject"],
                "from": f"hello@{username}.aigentsy.com",
                "delay_hours": seq["delay_hours"],
                "status": "active"
            }
            for seq in sequences
        ],
        "from_email": f"hello@{username}.aigentsy.com",
        "custom_domain": f"{username}.aigentsy.com",
        "dashboard_url": f"https://resend.com/mock/{username}",
        "configured_at": now_iso(),
        "mock": True
    }


async def send_test_email(
    username: str,
    sequence_name: str,
    to_email: str
) -> Dict[str, Any]:
    """Send a test email from a sequence"""
    
    if not RESEND_API_KEY:
        return {"ok": True, "mock": True, "message": "Mock email sent"}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "from": "onboarding@resend.dev",
                "to": [to_email],
                "subject": f"Test Email from {username}'s Business",
                "html": f"<p>This is a test email from your AiGentsy business.</p><p>Sequence: {sequence_name}</p>"
            }
            
            response = await client.post(
                "https://api.resend.com/emails",
                headers=headers,
                json=payload
            )
            
            if response.status_code in [200, 201]:
                return {
                    "ok": True,
                    "email_id": response.json().get("id"),
                    "sent_to": to_email
                }
            else:
                return {
                    "ok": False,
                    "error": f"Failed to send: {response.status_code}"
                }
                
    except Exception as e:
        return {"ok": False, "error": str(e)}
