"""Messaging adapters (stubs).
Replace with real Postmark/Twilio calls. Keep function signatures stable.
"""
from typing import Dict, Any

def send_email_postmark(to: str, subject: str, text: str, html: str = "") -> Dict[str, Any]:
    # TODO: implement Postmark API call
    return {"status": "ok", "id": "pm_mock_123", "to": to}

def send_sms_twilio(to: str, body: str) -> Dict[str, Any]:
    # TODO: implement Twilio API call
    return {"status": "ok", "sid": "tw_mock_123", "to": to}
