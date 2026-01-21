"""
UNIVERSAL CONNECTOR BUS (UCB) v1.0
==================================

Protocol-agnostic fulfillment fabric that turns any target site/app/API/UI
into an addressable "Outcome Function" with SLAs, pricing, risk and proofs.

Connector Types:
- HTTP/API Generic
- Webhook (outbound)
- SMTP/IMAP (email)
- SMS (Twilio-style)
- Slack/Discord
- Google Suite
- Airtable/Notion
- Shopify/WooCommerce
- Stripe/PayPal
- S3/GCS Storage
- Headless Browser (Playwright fallback)

Usage:
    from connectors import ConnectorRegistry, execute_outcome

    registry = ConnectorRegistry()
    registry.auto_register_all()

    result = await execute_outcome(registry, {
        "outcome_type": "send_email",
        "inputs": {"to": "user@example.com", "subject": "Hello"},
        "sla": {"deadline_sec": 30},
        "pricing": {"model": "fixed", "amount_usd": 0.01},
        "risk": {"bond_usd": 0},
        "proofs": ["message_id"],
        "idempotency_key": "email-123"
    })
"""

from .base import Connector, ConnectorResult, ConnectorHealth
from .registry import ConnectorRegistry, execute_outcome, score_connector
from .http_generic import HTTPGenericConnector
from .webhook import WebhookConnector
from .email_connector import EmailConnector
from .resend_connector import ResendConnector
from .sms_connector import SMSConnector
from .slack_connector import SlackConnector
from .shopify_connector import ShopifyConnector
from .stripe_connector import StripeConnector
from .storage_connector import StorageConnector
from .airtable_connector import AirtableConnector
from .headless_connector import HeadlessConnector

__all__ = [
    "Connector",
    "ConnectorResult",
    "ConnectorHealth",
    "ConnectorRegistry",
    "execute_outcome",
    "score_connector",
    "HTTPGenericConnector",
    "WebhookConnector",
    "EmailConnector",
    "ResendConnector",
    "SMSConnector",
    "SlackConnector",
    "ShopifyConnector",
    "StripeConnector",
    "StorageConnector",
    "AirtableConnector",
    "HeadlessConnector",
]

__version__ = "1.0.0"
