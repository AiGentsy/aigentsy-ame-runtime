"""
PARTNER MESH AUTO-OEM - AiGentsy v115
=====================================

Export signed, one-file widget configs that partners can drop in.
Attribution auto-splits via RevSplit optimizer.

FEATURES:
- One-file widget config export (JSON + signature)
- Partners embed AiGentsy capabilities in their products
- Automatic revenue attribution and splitting
- White-label options with "Powered by AiGentsy" badge
- Real-time performance tracking per partner

WIDGET TYPES:
- outcome_widget: Embedded outcome purchase button
- discovery_widget: AI opportunity finder
- fulfillment_widget: Order fulfillment integration
- payment_widget: Multi-rail payment pack

Powered by AiGentsy
"""

import os
import json
import hashlib
import hmac
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


# Secret for signing configs
SIGNING_SECRET = os.getenv("AIGENTSY_SIGNING_SECRET", "aigentsy_default_signing_key_change_in_prod")
AIGENTSY_URL = os.getenv("AIGENTSY_URL", "https://aigentsy.com")


class WidgetType(str, Enum):
    OUTCOME = "outcome_widget"
    DISCOVERY = "discovery_widget"
    FULFILLMENT = "fulfillment_widget"
    PAYMENT = "payment_widget"
    FULL_STACK = "full_stack_widget"


class PartnerTier(str, Enum):
    STARTER = "starter"        # 80/20 split (partner/aigentsy)
    GROWTH = "growth"          # 85/15 split
    SCALE = "scale"            # 90/10 split
    ENTERPRISE = "enterprise"  # 95/5 split (negotiated)


# Revenue split by tier
REVENUE_SPLITS = {
    PartnerTier.STARTER: {"partner": 0.80, "aigentsy": 0.20},
    PartnerTier.GROWTH: {"partner": 0.85, "aigentsy": 0.15},
    PartnerTier.SCALE: {"partner": 0.90, "aigentsy": 0.10},
    PartnerTier.ENTERPRISE: {"partner": 0.95, "aigentsy": 0.05},
}


@dataclass
class PartnerConfig:
    """Partner configuration"""
    partner_id: str
    partner_name: str
    tier: PartnerTier
    api_key: str
    allowed_widgets: List[WidgetType]
    allowed_domains: List[str]
    revenue_split: Dict[str, float]
    white_label: bool = False
    custom_branding: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    active: bool = True


@dataclass
class WidgetConfig:
    """Exportable widget configuration"""
    config_id: str
    partner_id: str
    widget_type: WidgetType
    config_data: Dict[str, Any]
    signature: str
    expires_at: str
    version: str = "1.0.0"


# In-memory partner registry (would be database in production)
PARTNER_REGISTRY: Dict[str, PartnerConfig] = {}
WIDGET_CONFIGS: Dict[str, WidgetConfig] = {}


def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


def _generate_partner_id() -> str:
    return f"partner_{secrets.token_hex(8)}"


def _generate_api_key() -> str:
    return f"ak_{secrets.token_urlsafe(32)}"


def _generate_config_id() -> str:
    return f"wconf_{secrets.token_hex(8)}"


def _sign_config(config_data: Dict[str, Any], partner_id: str) -> str:
    """Generate HMAC signature for config"""
    payload = json.dumps(config_data, sort_keys=True)
    message = f"{partner_id}:{payload}"
    signature = hmac.new(
        SIGNING_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def _verify_signature(config_data: Dict[str, Any], partner_id: str, signature: str) -> bool:
    """Verify config signature"""
    expected = _sign_config(config_data, partner_id)
    return hmac.compare_digest(expected, signature)


def register_partner(
    partner_name: str,
    tier: PartnerTier = PartnerTier.STARTER,
    allowed_widgets: List[WidgetType] = None,
    allowed_domains: List[str] = None,
    white_label: bool = False
) -> PartnerConfig:
    """Register a new partner"""

    partner_id = _generate_partner_id()
    api_key = _generate_api_key()

    if allowed_widgets is None:
        allowed_widgets = [WidgetType.OUTCOME, WidgetType.PAYMENT]

    if allowed_domains is None:
        allowed_domains = ["*"]

    partner = PartnerConfig(
        partner_id=partner_id,
        partner_name=partner_name,
        tier=tier,
        api_key=api_key,
        allowed_widgets=allowed_widgets,
        allowed_domains=allowed_domains,
        revenue_split=REVENUE_SPLITS[tier],
        white_label=white_label,
        created_at=_now(),
        active=True
    )

    PARTNER_REGISTRY[partner_id] = partner

    return partner


def generate_widget_config(
    partner_id: str,
    widget_type: WidgetType,
    custom_config: Dict[str, Any] = None,
    ttl_days: int = 365
) -> Optional[WidgetConfig]:
    """
    Generate a signed, exportable widget config.

    Partners can embed this config in their products.
    """

    if partner_id not in PARTNER_REGISTRY:
        return None

    partner = PARTNER_REGISTRY[partner_id]

    if not partner.active:
        return None

    if widget_type not in partner.allowed_widgets:
        return None

    config_id = _generate_config_id()

    # Base config
    config_data = {
        "widget_type": widget_type.value,
        "partner_id": partner_id,
        "partner_name": partner.partner_name,
        "api_endpoint": f"{AIGENTSY_URL}/api/v1/widget",
        "allowed_domains": partner.allowed_domains,
        "revenue_split": partner.revenue_split,
        "white_label": partner.white_label,
        "branding": {
            "powered_by": "AiGentsy" if not partner.white_label else partner.custom_branding.get("powered_by", ""),
            "logo_url": f"{AIGENTSY_URL}/assets/logo.svg" if not partner.white_label else partner.custom_branding.get("logo_url", ""),
            "primary_color": partner.custom_branding.get("primary_color", "#6366f1"),
            "badge_text": "Powered by AiGentsy" if not partner.white_label else ""
        },
        "version": "1.0.0",
        "issued_at": _now()
    }

    # Widget-specific config
    if widget_type == WidgetType.OUTCOME:
        config_data["widget_config"] = {
            "button_text": "Get Outcome",
            "success_redirect": custom_config.get("success_redirect", ""),
            "cancel_redirect": custom_config.get("cancel_redirect", ""),
            "outcome_types": custom_config.get("outcome_types", ["service", "product", "task"]),
            "min_price": custom_config.get("min_price", 5),
            "max_price": custom_config.get("max_price", 10000),
        }

    elif widget_type == WidgetType.DISCOVERY:
        config_data["widget_config"] = {
            "discovery_mode": custom_config.get("discovery_mode", "opportunities"),
            "categories": custom_config.get("categories", ["all"]),
            "auto_refresh": custom_config.get("auto_refresh", True),
            "refresh_interval_seconds": custom_config.get("refresh_interval", 300),
        }

    elif widget_type == WidgetType.FULFILLMENT:
        config_data["widget_config"] = {
            "fulfillment_types": custom_config.get("fulfillment_types", ["ai", "human", "hybrid"]),
            "sla_hours": custom_config.get("sla_hours", 24),
            "quality_guarantee": custom_config.get("quality_guarantee", True),
        }

    elif widget_type == WidgetType.PAYMENT:
        config_data["widget_config"] = {
            "payment_rails": custom_config.get("payment_rails", ["stripe_card", "paypal"]),
            "currencies": custom_config.get("currencies", ["USD"]),
            "optimize_for": custom_config.get("optimize_for", "conversion"),
        }

    elif widget_type == WidgetType.FULL_STACK:
        config_data["widget_config"] = {
            "enabled_modules": ["discovery", "outcome", "fulfillment", "payment"],
            "autonomy_level": custom_config.get("autonomy_level", 3),
            "auto_execute": custom_config.get("auto_execute", False),
        }

    # Merge custom config
    if custom_config:
        for key, value in custom_config.items():
            if key not in config_data["widget_config"]:
                config_data["widget_config"][key] = value

    # Sign the config
    signature = _sign_config(config_data, partner_id)

    expires_at = (datetime.now(timezone.utc) + timedelta(days=ttl_days)).isoformat() + "Z"

    widget_config = WidgetConfig(
        config_id=config_id,
        partner_id=partner_id,
        widget_type=widget_type,
        config_data=config_data,
        signature=signature,
        expires_at=expires_at
    )

    WIDGET_CONFIGS[config_id] = widget_config

    return widget_config


def export_widget_config(config_id: str) -> Optional[str]:
    """
    Export widget config as a single JSON file that partners can embed.

    Returns JSON string ready to be saved as aigentsy-widget-config.json
    """

    if config_id not in WIDGET_CONFIGS:
        return None

    widget_config = WIDGET_CONFIGS[config_id]

    export_data = {
        "aigentsy_widget_config": {
            "config_id": widget_config.config_id,
            "version": widget_config.version,
            "widget_type": widget_config.widget_type.value,
            "config": widget_config.config_data,
            "signature": widget_config.signature,
            "expires_at": widget_config.expires_at,
            "powered_by": "AiGentsy"
        },
        "embed_instructions": {
            "step_1": "Save this file as aigentsy-widget-config.json",
            "step_2": "Include AiGentsy SDK: <script src='https://aigentsy.com/sdk/widget.js'></script>",
            "step_3": "Initialize: AiGentsy.init({ configPath: './aigentsy-widget-config.json' })",
            "step_4": "Add widget: <div data-aigentsy-widget='outcome'></div>",
            "docs": "https://aigentsy.com/docs/partner-widgets"
        }
    }

    return json.dumps(export_data, indent=2)


def verify_widget_request(config_id: str, signature: str, domain: str) -> Dict[str, Any]:
    """Verify an incoming widget request"""

    if config_id not in WIDGET_CONFIGS:
        return {"valid": False, "error": "Config not found"}

    widget_config = WIDGET_CONFIGS[config_id]

    # Verify signature
    if not _verify_signature(widget_config.config_data, widget_config.partner_id, signature):
        return {"valid": False, "error": "Invalid signature"}

    # Check expiration
    expires = datetime.fromisoformat(widget_config.expires_at.replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires:
        return {"valid": False, "error": "Config expired"}

    # Check domain
    partner = PARTNER_REGISTRY.get(widget_config.partner_id)
    if partner and partner.allowed_domains != ["*"]:
        if domain not in partner.allowed_domains:
            return {"valid": False, "error": "Domain not allowed"}

    return {
        "valid": True,
        "partner_id": widget_config.partner_id,
        "widget_type": widget_config.widget_type.value,
        "revenue_split": widget_config.config_data.get("revenue_split", {}),
        "powered_by": "AiGentsy"
    }


# Revenue tracking per partner
PARTNER_REVENUE: Dict[str, Dict[str, float]] = {}


def track_partner_transaction(partner_id: str, amount: float, transaction_type: str) -> Dict[str, Any]:
    """Track a transaction and calculate revenue split"""

    if partner_id not in PARTNER_REGISTRY:
        return {"ok": False, "error": "Partner not found"}

    partner = PARTNER_REGISTRY[partner_id]
    split = partner.revenue_split

    partner_share = round(amount * split["partner"], 2)
    aigentsy_share = round(amount * split["aigentsy"], 2)

    if partner_id not in PARTNER_REVENUE:
        PARTNER_REVENUE[partner_id] = {
            "total_volume": 0,
            "partner_revenue": 0,
            "aigentsy_revenue": 0,
            "transactions": 0
        }

    PARTNER_REVENUE[partner_id]["total_volume"] += amount
    PARTNER_REVENUE[partner_id]["partner_revenue"] += partner_share
    PARTNER_REVENUE[partner_id]["aigentsy_revenue"] += aigentsy_share
    PARTNER_REVENUE[partner_id]["transactions"] += 1

    return {
        "ok": True,
        "amount": amount,
        "partner_share": partner_share,
        "aigentsy_share": aigentsy_share,
        "split": split,
        "powered_by": "AiGentsy"
    }


def get_partner_stats(partner_id: str) -> Dict[str, Any]:
    """Get partner performance stats"""

    if partner_id not in PARTNER_REGISTRY:
        return {"ok": False, "error": "Partner not found"}

    partner = PARTNER_REGISTRY[partner_id]
    revenue = PARTNER_REVENUE.get(partner_id, {
        "total_volume": 0,
        "partner_revenue": 0,
        "aigentsy_revenue": 0,
        "transactions": 0
    })

    return {
        "ok": True,
        "partner_id": partner_id,
        "partner_name": partner.partner_name,
        "tier": partner.tier.value,
        "revenue_split": partner.revenue_split,
        "stats": revenue,
        "widgets_issued": len([w for w in WIDGET_CONFIGS.values() if w.partner_id == partner_id]),
        "powered_by": "AiGentsy"
    }


def get_partner_mesh_status() -> Dict[str, Any]:
    """Get partner mesh status"""

    total_partners = len(PARTNER_REGISTRY)
    active_partners = len([p for p in PARTNER_REGISTRY.values() if p.active])
    total_widgets = len(WIDGET_CONFIGS)
    total_volume = sum(r.get("total_volume", 0) for r in PARTNER_REVENUE.values())
    total_aigentsy_rev = sum(r.get("aigentsy_revenue", 0) for r in PARTNER_REVENUE.values())

    return {
        "ok": True,
        "total_partners": total_partners,
        "active_partners": active_partners,
        "total_widgets_issued": total_widgets,
        "total_volume": round(total_volume, 2),
        "total_aigentsy_revenue": round(total_aigentsy_rev, 2),
        "tiers": {t.value: REVENUE_SPLITS[t] for t in PartnerTier},
        "widget_types": [w.value for w in WidgetType],
        "powered_by": "AiGentsy"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_partner_mesh(app):
    """Add partner mesh endpoints to FastAPI app"""

    from fastapi import Body, Header
    from fastapi.responses import PlainTextResponse

    @app.get("/partner-mesh/status")
    async def partner_mesh_status():
        """Get partner mesh status"""
        return get_partner_mesh_status()

    @app.post("/partner-mesh/register")
    async def register_new_partner(body: Dict = Body(...)):
        """Register a new partner"""
        partner = register_partner(
            partner_name=body.get("partner_name", "New Partner"),
            tier=PartnerTier(body.get("tier", "starter")),
            allowed_widgets=[WidgetType(w) for w in body.get("allowed_widgets", ["outcome_widget"])],
            allowed_domains=body.get("allowed_domains", ["*"]),
            white_label=body.get("white_label", False)
        )

        return {
            "ok": True,
            "partner_id": partner.partner_id,
            "api_key": partner.api_key,
            "tier": partner.tier.value,
            "revenue_split": partner.revenue_split,
            "powered_by": "AiGentsy"
        }

    @app.post("/partner-mesh/generate-widget")
    async def generate_widget(body: Dict = Body(...)):
        """Generate a widget config for a partner"""
        widget_config = generate_widget_config(
            partner_id=body.get("partner_id"),
            widget_type=WidgetType(body.get("widget_type", "outcome_widget")),
            custom_config=body.get("custom_config", {}),
            ttl_days=body.get("ttl_days", 365)
        )

        if not widget_config:
            return {"ok": False, "error": "Failed to generate widget config"}

        return {
            "ok": True,
            "config_id": widget_config.config_id,
            "widget_type": widget_config.widget_type.value,
            "expires_at": widget_config.expires_at,
            "download_url": f"/partner-mesh/export/{widget_config.config_id}",
            "powered_by": "AiGentsy"
        }

    @app.get("/partner-mesh/export/{config_id}")
    async def export_config(config_id: str):
        """Export widget config as JSON file"""
        config_json = export_widget_config(config_id)

        if not config_json:
            return {"ok": False, "error": "Config not found"}

        return PlainTextResponse(
            content=config_json,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=aigentsy-widget-{config_id}.json"}
        )

    @app.get("/partner-mesh/partner/{partner_id}/stats")
    async def partner_stats(partner_id: str):
        """Get partner stats"""
        return get_partner_stats(partner_id)

    @app.post("/partner-mesh/verify")
    async def verify_request(body: Dict = Body(...)):
        """Verify a widget request"""
        return verify_widget_request(
            config_id=body.get("config_id"),
            signature=body.get("signature"),
            domain=body.get("domain", "")
        )

    print("=" * 80)
    print("🤝 PARTNER MESH AUTO-OEM LOADED - Powered by AiGentsy")
    print("=" * 80)
    print("Endpoints:")
    print("  GET  /partner-mesh/status")
    print("  POST /partner-mesh/register")
    print("  POST /partner-mesh/generate-widget")
    print("  GET  /partner-mesh/export/{config_id}")
    print("  GET  /partner-mesh/partner/{partner_id}/stats")
    print("  POST /partner-mesh/verify")
    print("=" * 80)


if __name__ == "__main__":
    # Test
    print("=" * 60)
    print("PARTNER MESH AUTO-OEM TEST - Powered by AiGentsy")
    print("=" * 60)

    # Register partner
    partner = register_partner(
        partner_name="Acme Corp",
        tier=PartnerTier.GROWTH,
        allowed_widgets=[WidgetType.OUTCOME, WidgetType.PAYMENT, WidgetType.DISCOVERY]
    )

    print(f"\nPartner Registered:")
    print(f"  ID: {partner.partner_id}")
    print(f"  Name: {partner.partner_name}")
    print(f"  Tier: {partner.tier.value}")
    print(f"  Split: {partner.revenue_split}")
    print(f"  API Key: {partner.api_key[:20]}...")

    # Generate widget
    widget = generate_widget_config(
        partner_id=partner.partner_id,
        widget_type=WidgetType.OUTCOME,
        custom_config={"success_redirect": "https://acme.com/success"}
    )

    print(f"\nWidget Config Generated:")
    print(f"  Config ID: {widget.config_id}")
    print(f"  Type: {widget.widget_type.value}")
    print(f"  Signature: {widget.signature[:30]}...")

    # Export
    export = export_widget_config(widget.config_id)
    print(f"\nExported Config (first 200 chars):")
    print(export[:200] + "...")
