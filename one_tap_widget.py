"""
ONE-TAP OUTCOME WIDGET
======================

Embeddable JavaScript widget that any site can use to offer
one-click outcome purchases.

Flow:
1. Partner embeds <script src="aigentsy.js?partner=xyz">
2. User clicks "Buy This Outcome"
3. Widget opens modal with price + trust signals
4. Stripe Checkout → COI created → execution starts
5. Partner gets rev share

Revenue:
- 1.5% widget origination fee (on top of standard fees)
- Partner affiliate share (configurable, default 5%)

Usage:
    from one_tap_widget import create_widget_config, generate_embed_code, process_widget_purchase
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import uuid4
import json
import hashlib

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Fee structure
WIDGET_ORIGINATION_FEE_PCT = 0.015  # 1.5%
DEFAULT_AFFILIATE_SHARE_PCT = 0.05  # 5% to partner

# Widget storage
_WIDGET_CONFIGS: Dict[str, Dict[str, Any]] = {}
_WIDGET_SESSIONS: Dict[str, Dict[str, Any]] = {}
_WIDGET_PURCHASES: Dict[str, Dict[str, Any]] = {}


class OneTapWidget:
    """
    Manages embeddable outcome purchase widgets.
    """

    def __init__(self):
        self.origination_fee_pct = WIDGET_ORIGINATION_FEE_PCT
        self.default_affiliate_share = DEFAULT_AFFILIATE_SHARE_PCT

    def create_widget_config(
        self,
        partner_id: str,
        *,
        name: str = "Outcome Widget",
        allowed_domains: list = None,
        affiliate_share_pct: float = None,
        theme: str = "light",
        button_text: str = "Get This Done",
        show_trust_signals: bool = True,
        show_ocs: bool = True,
        show_insurance_option: bool = True,
        max_price: float = 10000,
        outcome_categories: list = None
    ) -> Dict[str, Any]:
        """
        Create widget configuration for a partner.

        Args:
            partner_id: Partner identifier
            name: Widget name
            allowed_domains: Domains allowed to embed (empty = all)
            affiliate_share_pct: Partner's revenue share
            theme: light or dark
            button_text: CTA button text
            show_trust_signals: Show OCS, completion rate
            show_ocs: Show provider OCS score
            show_insurance_option: Allow outcome insurance upsell
            max_price: Maximum outcome price
            outcome_categories: Allowed categories

        Returns:
            Widget config with API key
        """
        widget_id = f"widget_{partner_id}_{uuid4().hex[:8]}"
        api_key = f"wk_{hashlib.sha256(f'{widget_id}{_now()}'.encode()).hexdigest()[:32]}"

        config = {
            "id": widget_id,
            "partner_id": partner_id,
            "api_key": api_key,
            "name": name,
            "status": "ACTIVE",
            "allowed_domains": allowed_domains or [],
            "affiliate_share_pct": affiliate_share_pct or self.default_affiliate_share,
            "origination_fee_pct": self.origination_fee_pct,
            "theme": theme,
            "button_text": button_text,
            "show_trust_signals": show_trust_signals,
            "show_ocs": show_ocs,
            "show_insurance_option": show_insurance_option,
            "max_price": max_price,
            "outcome_categories": outcome_categories or ["all"],
            "created_at": _now(),
            "stats": {
                "impressions": 0,
                "clicks": 0,
                "purchases": 0,
                "total_revenue": 0.0,
                "affiliate_earnings": 0.0
            }
        }

        _WIDGET_CONFIGS[widget_id] = config
        return {"ok": True, "widget_id": widget_id, "api_key": api_key, "config": config}

    def generate_embed_code(
        self,
        widget_id: str,
        *,
        outcome_type: str = None,
        default_description: str = None,
        container_id: str = "aigentsy-widget"
    ) -> Dict[str, Any]:
        """
        Generate embeddable JavaScript snippet.

        Args:
            widget_id: Widget ID
            outcome_type: Pre-selected outcome type
            default_description: Pre-filled description
            container_id: DOM container ID

        Returns:
            Embed code and instructions
        """
        config = _WIDGET_CONFIGS.get(widget_id)
        if not config:
            return {"ok": False, "error": "widget_not_found"}

        # Generate embed snippet
        script_url = "https://aigentsy.com/widget/v1/aigentsy.min.js"

        embed_code = f'''<!-- AiGentsy One-Tap Widget -->
<div id="{container_id}"></div>
<script src="{script_url}"
        data-widget-id="{widget_id}"
        data-api-key="{config['api_key']}"
        data-theme="{config['theme']}"
        data-button-text="{config['button_text']}"
        {f'data-outcome-type="{outcome_type}"' if outcome_type else ''}
        {f'data-description="{default_description}"' if default_description else ''}
        data-container="{container_id}">
</script>'''

        # Also generate programmatic init
        programmatic_code = f'''// Programmatic initialization
window.AiGentsyWidget.init({{
    widgetId: "{widget_id}",
    apiKey: "{config['api_key']}",
    container: "#{container_id}",
    theme: "{config['theme']}",
    buttonText: "{config['button_text']}",
    {f'outcomeType: "{outcome_type}",' if outcome_type else ''}
    {f'description: "{default_description}",' if default_description else ''}
    onPurchase: function(result) {{
        console.log("Outcome purchased:", result);
    }},
    onError: function(error) {{
        console.error("Widget error:", error);
    }}
}});'''

        return {
            "ok": True,
            "embed_code": embed_code,
            "programmatic_code": programmatic_code,
            "script_url": script_url,
            "docs_url": "https://docs.aigentsy.com/widget"
        }

    def create_widget_session(
        self,
        widget_id: str,
        *,
        outcome_description: str,
        outcome_type: str = "general",
        user_email: str = None,
        metadata: dict = None,
        referrer_url: str = None
    ) -> Dict[str, Any]:
        """
        Create a widget session when user initiates purchase.
        """
        config = _WIDGET_CONFIGS.get(widget_id)
        if not config:
            return {"ok": False, "error": "widget_not_found"}

        if config["status"] != "ACTIVE":
            return {"ok": False, "error": "widget_inactive"}

        session_id = f"wsess_{uuid4().hex[:12]}"

        # Get price quote
        try:
            from monetization import MonetizationFabric
            fabric = MonetizationFabric()
            base_price = 100  # Default, would come from pricing
            suggested_price = fabric.price_outcome(base_price, load_pct=0.5, wave_score=0.3)
        except:
            suggested_price = 100.0

        # Add widget origination fee
        widget_fee = round(suggested_price * config["origination_fee_pct"], 2)
        total_price = round(suggested_price + widget_fee, 2)

        session = {
            "id": session_id,
            "widget_id": widget_id,
            "partner_id": config["partner_id"],
            "outcome_description": outcome_description,
            "outcome_type": outcome_type,
            "user_email": user_email,
            "metadata": metadata or {},
            "referrer_url": referrer_url,
            "pricing": {
                "base_price": suggested_price,
                "widget_fee": widget_fee,
                "total_price": total_price,
                "affiliate_share": round(total_price * config["affiliate_share_pct"], 2)
            },
            "status": "PENDING",
            "created_at": _now(),
            "expires_at": None,  # Set when checkout starts
            "checkout_url": None,
            "coi_id": None
        }

        _WIDGET_SESSIONS[session_id] = session

        # Update widget stats
        config["stats"]["clicks"] += 1

        return {
            "ok": True,
            "session_id": session_id,
            "pricing": session["pricing"],
            "trust_signals": self._get_trust_signals(outcome_type) if config["show_trust_signals"] else None
        }

    def _get_trust_signals(self, outcome_type: str) -> Dict[str, Any]:
        """Get trust signals for outcome type"""
        # Would integrate with OCS and analytics
        return {
            "completion_rate": 0.94,
            "avg_delivery_time": "2.4 hours",
            "satisfaction_score": 4.7,
            "outcomes_delivered": 12847,
            "insurance_available": True
        }

    def process_widget_purchase(
        self,
        session_id: str,
        *,
        payment_intent_id: str = None,
        buyer_email: str = None,
        add_insurance: bool = False
    ) -> Dict[str, Any]:
        """
        Process a widget purchase after payment.

        Args:
            session_id: Widget session ID
            payment_intent_id: Stripe payment intent
            buyer_email: Buyer's email
            add_insurance: Whether insurance was added

        Returns:
            Purchase result with COI details
        """
        session = _WIDGET_SESSIONS.get(session_id)
        if not session:
            return {"ok": False, "error": "session_not_found"}

        if session["status"] != "PENDING":
            return {"ok": False, "error": f"session_is_{session['status'].lower()}"}

        config = _WIDGET_CONFIGS.get(session["widget_id"])
        if not config:
            return {"ok": False, "error": "widget_config_not_found"}

        # Create COI
        coi_id = f"coi_widget_{uuid4().hex[:8]}"

        purchase = {
            "id": f"wpurch_{uuid4().hex[:8]}",
            "session_id": session_id,
            "widget_id": session["widget_id"],
            "partner_id": session["partner_id"],
            "coi_id": coi_id,
            "buyer_email": buyer_email or session["user_email"],
            "outcome_description": session["outcome_description"],
            "outcome_type": session["outcome_type"],
            "pricing": session["pricing"],
            "insurance_added": add_insurance,
            "payment_intent_id": payment_intent_id,
            "status": "PURCHASED",
            "purchased_at": _now(),
            "metadata": session["metadata"]
        }

        _WIDGET_PURCHASES[purchase["id"]] = purchase

        # Update session
        session["status"] = "PURCHASED"
        session["coi_id"] = coi_id

        # Update widget stats
        config["stats"]["purchases"] += 1
        config["stats"]["total_revenue"] += session["pricing"]["total_price"]
        config["stats"]["affiliate_earnings"] += session["pricing"]["affiliate_share"]

        # Post affiliate payment to ledger
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="widget_affiliate",
                ref=f"widget:{purchase['id']}",
                debit=0,
                credit=session["pricing"]["affiliate_share"],
                meta={
                    "partner_id": session["partner_id"],
                    "widget_id": session["widget_id"],
                    "coi_id": coi_id
                }
            )
        except ImportError:
            pass

        return {
            "ok": True,
            "purchase": purchase,
            "coi_id": coi_id,
            "affiliate_earnings": session["pricing"]["affiliate_share"],
            "message": "Outcome purchased successfully"
        }

    def get_widget_config(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get widget configuration"""
        return _WIDGET_CONFIGS.get(widget_id)

    def get_widget_stats(self, widget_id: str) -> Dict[str, Any]:
        """Get widget performance stats"""
        config = _WIDGET_CONFIGS.get(widget_id)
        if not config:
            return {"ok": False, "error": "widget_not_found"}

        stats = config["stats"]
        conversion_rate = stats["purchases"] / stats["clicks"] if stats["clicks"] > 0 else 0

        return {
            "widget_id": widget_id,
            "impressions": stats["impressions"],
            "clicks": stats["clicks"],
            "purchases": stats["purchases"],
            "conversion_rate": round(conversion_rate, 4),
            "total_revenue": round(stats["total_revenue"], 2),
            "affiliate_earnings": round(stats["affiliate_earnings"], 2),
            "avg_order_value": round(stats["total_revenue"] / stats["purchases"], 2) if stats["purchases"] > 0 else 0
        }

    def get_partner_widgets(self, partner_id: str) -> List[Dict[str, Any]]:
        """Get all widgets for a partner"""
        return [
            c for c in _WIDGET_CONFIGS.values()
            if c["partner_id"] == partner_id
        ]

    def get_all_stats(self) -> Dict[str, Any]:
        """Get aggregate widget statistics"""
        total_purchases = sum(c["stats"]["purchases"] for c in _WIDGET_CONFIGS.values())
        total_revenue = sum(c["stats"]["total_revenue"] for c in _WIDGET_CONFIGS.values())
        total_affiliate = sum(c["stats"]["affiliate_earnings"] for c in _WIDGET_CONFIGS.values())
        widget_fees = total_revenue * WIDGET_ORIGINATION_FEE_PCT

        return {
            "total_widgets": len(_WIDGET_CONFIGS),
            "active_widgets": len([c for c in _WIDGET_CONFIGS.values() if c["status"] == "ACTIVE"]),
            "total_purchases": total_purchases,
            "total_revenue": round(total_revenue, 2),
            "total_affiliate_payouts": round(total_affiliate, 2),
            "total_widget_fees": round(widget_fees, 2),
            "partners": len(set(c["partner_id"] for c in _WIDGET_CONFIGS.values()))
        }


# Module-level singleton
_widget = OneTapWidget()


def create_widget_config(partner_id: str, name: str = "Outcome Widget", **kwargs) -> Dict[str, Any]:
    """Create widget configuration for partner"""
    return _widget.create_widget_config(partner_id, name=name, **kwargs)


def generate_embed_code(widget_id: str, **kwargs) -> Dict[str, Any]:
    """Generate embeddable JavaScript"""
    return _widget.generate_embed_code(widget_id, **kwargs)


def create_widget_session(widget_id: str, **kwargs) -> Dict[str, Any]:
    """Create widget purchase session"""
    return _widget.create_widget_session(widget_id, **kwargs)


def process_widget_purchase(session_id: str, **kwargs) -> Dict[str, Any]:
    """Process widget purchase"""
    return _widget.process_widget_purchase(session_id, **kwargs)


def get_widget_config(widget_id: str) -> Optional[Dict[str, Any]]:
    """Get widget config"""
    return _widget.get_widget_config(widget_id)


def get_widget_stats(widget_id: str) -> Dict[str, Any]:
    """Get widget performance stats"""
    return _widget.get_widget_stats(widget_id)


def get_partner_widgets(partner_id: str) -> list:
    """Get partner's widgets"""
    return _widget.get_partner_widgets(partner_id)


def get_widget_platform_stats() -> Dict[str, Any]:
    """Get aggregate widget stats"""
    return _widget.get_all_stats()


def get_widget_stats(widget_id: str = None) -> Dict[str, Any]:
    """Get widget stats - if no widget_id, returns platform stats"""
    if widget_id:
        return _widget.get_stats(widget_id)
    return get_widget_platform_stats()
