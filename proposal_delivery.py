import os
import requests
from datetime import datetime

# ✅ Universal DM Bot Formatter
def format_universal_dm(recipient: str, platform: str, proposal: str):
    """
    Formats a universal DM for any platform (Fiverr, LinkedIn, etc.)
    """
    timestamp = datetime.utcnow().isoformat()
    return f"""
💬 Direct Message (via {platform})
To: {recipient}

Hi {recipient},

We found a strong match between your needs and one of our AiGentsy solutions:

{proposal}

To explore or collaborate, visit:
https://aigentsy.com/start?invite={recipient}

🕒 Sent: {timestamp}
""".strip()


def deliver_proposal(query: str, matches: list[dict], originator: str):
    """
    Multi-channel proposal dispatch:
    - Webhook (e.g. Zapier, Discord)
    - Email (stub)
    - DM (universal logging)
    """
    invite_link = f"https://aigentsy.com/start?invite={originator}"
    
    formatted_matches = [
        f"- {m['venture']} ({m['username']}): {m.get('match_reason', 'N/A')}"
        for m in matches
    ]
    match_block = "\n".join(formatted_matches)
    
    proposal_msg = f"""
🚀 AiGentsy Proposal Opportunity
Query: {query}
From: {originator}

Matching Agents:
{match_block}

🔗 Invite to fulfill: {invite_link}
Timestamp: {datetime.utcnow().isoformat()}
    """.strip()

    delivery_status = {"webhook": False, "email": False, "dm": False}

    # --- Webhook Delivery ---
    webhook_url = os.getenv("PROPOSAL_WEBHOOK_URL")
    if webhook_url:
        try:
            res = requests.post(
                webhook_url,
                json={"text": proposal_msg},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if res.status_code in [200, 204]:
                print("📬 Sent via Webhook")
                delivery_status["webhook"] = True
        except Exception as e:
            print("⚠️ Webhook failed:", str(e))

    # --- Email Delivery (Stub) ---
    email = os.getenv("PROPOSAL_EMAIL")
    if email:
        print(f"✉️ [Stub] Email would be sent to {email}")
        delivery_status["email"] = True

    # --- Universal DM Delivery ---
    dm_target = os.getenv("PROPOSAL_DM_TARGET")
    dm_platform = os.getenv("PROPOSAL_DM_PLATFORM", "universal")
    if dm_target:
        formatted_dm = format_universal_dm(dm_target, dm_platform, proposal_msg)
        print(formatted_dm)
        delivery_status["dm"] = True

    return delivery_status
