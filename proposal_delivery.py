import os
import requests
from datetime import datetime

def proposal_delivery(proposal: str, delivery_config: dict):
    """
    Delivers a proposal via multiple channels:
    - webhook (e.g., Discord, Slack, Zapier)
    - email (stub for SMTP or API-based service)
    - dm (logs universal message format for later automation)
    """

    status = {"webhook": False, "email": False, "dm": False}

    # Webhook delivery
    webhook_url = delivery_config.get("webhook_url")
    if webhook_url:
        try:
            res = requests.post(webhook_url, json={"proposal": proposal}, timeout=10)
            if res.status_code in [200, 201, 204]:
                status["webhook"] = True
                print("📬 Proposal sent via webhook.")
        except Exception as e:
            print("⚠️ Webhook delivery failed:", str(e))

    # Email delivery (stub — insert SMTP or API logic here)
    email_address = delivery_config.get("email")
    if email_address:
        print(f"✉️ Email delivery queued for: {email_address}")
        status["email"] = True

    # DM delivery (universal format)
    dm_target = delivery_config.get("dm_target")
    dm_platform = delivery_config.get("platform", "universal")
    if dm_target:
        dm_msg = f'''
        💬 Direct Message Proposal
        Platform: {dm_platform}
        Recipient: {dm_target}
        ---
        {proposal}
        ---
        Timestamp: {datetime.utcnow().isoformat()}
        '''
        print(dm_msg)
        status["dm"] = True

    return status