import os
import requests
from datetime import datetime

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

    # --- Webhook ---
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

    # --- Email Stub (to replace with SMTP/API) ---
    email = os.getenv("PROPOSAL_EMAIL")
    if email:
        print(f"✉️ [Stub] Email would be sent to {email}")
        delivery_status["email"] = True

    # --- Universal DM Stub ---
    dm_target = os.getenv("PROPOSAL_DM_TARGET")
    dm_platform = os.getenv("PROPOSAL_DM_PLATFORM", "universal")
    if dm_target:
        print(f"""
💬 DM Message
Platform: {dm_platform}
To: {dm_target}
---
{proposal_msg}
---
""")
        delivery_status["dm"] = True

    return delivery_status
