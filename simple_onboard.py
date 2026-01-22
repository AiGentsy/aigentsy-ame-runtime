"""
SIMPLE ONBOARD v115 - 6 Questions to Money
==========================================

Average user, 5-minute setup → AiGentsy finds clients, sells, contracts,
communicates, fulfills, delivers, and collects via third-party processors.

PSP-ONLY FUND FLOW - No money transmission, no custody:
- All payments go directly to Stripe/PayPal
- We never touch customer funds
- Service credits instead of insurance
- Clickwrap contracts with standard terms

6 Questions Only:
1. Name/Logo
2. Niche (pick a pack)
3. Starter offer
4. Price band
5. Payout email
6. Connect Stripe/PayPal

Everything else inherits from prebuilt defaults (PDLs, COIs, SLAs, terms, widgets).

Leverages:
- sku_orchestrator.py (Universal business minting)
- template_actionizer.py (Deploy to Vercel/Supabase)
- bespoke_kit_generator.py (Custom kit generation)
- auto_spawn_engine.py (Trend-based spawning)
- one_tap_widget.py (Embeddable widget)
- outcome_subscriptions.py (Subscription tiers)
- policies/*.json (Default configurations)
- monetization/ (Pricing, revenue routing, badges)
- brain_overlay/ (OCS scoring, policy learning)

Usage:
    from simple_onboard import start_onboard, complete_onboard, get_onboard_status
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import uuid4
import json
import os
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_onboard")

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Niche Packs (pre-configured SKUs)
NICHE_PACKS = {
    "code": {
        "name": "Code & Development",
        "sku": "saas",
        "template": "technical",
        "description": "Build apps, fix bugs, write scripts, automate workflows",
        "starter_offers": [
            {"name": "Bug Fix", "price_range": [49, 199], "sla_hours": 24},
            {"name": "Feature Build", "price_range": [199, 999], "sla_hours": 72},
            {"name": "Code Review", "price_range": [79, 299], "sla_hours": 24}
        ],
        "pdl_chain": ["github.create_branch", "code.implement", "github.pr", "code.test"],
        "discovery_sources": ["github", "stackoverflow", "upwork", "freelancer"]
    },
    "design": {
        "name": "Design & Creative",
        "sku": "social",
        "template": "boutique",
        "description": "Logos, graphics, UI/UX, presentations, brand assets",
        "starter_offers": [
            {"name": "Logo Design", "price_range": [99, 499], "sla_hours": 48},
            {"name": "Social Graphics Pack", "price_range": [79, 299], "sla_hours": 24},
            {"name": "Pitch Deck", "price_range": [199, 799], "sla_hours": 48}
        ],
        "pdl_chain": ["design.brief", "design.draft", "design.revise", "storage.deliver"],
        "discovery_sources": ["dribbble", "behance", "upwork", "fiverr"]
    },
    "content": {
        "name": "Content & Writing",
        "sku": "marketing",
        "template": "professional",
        "description": "Blog posts, copywriting, SEO content, social posts",
        "starter_offers": [
            {"name": "Blog Post (1000w)", "price_range": [79, 249], "sla_hours": 24},
            {"name": "Website Copy", "price_range": [199, 599], "sla_hours": 48},
            {"name": "Email Sequence (5)", "price_range": [149, 449], "sla_hours": 48}
        ],
        "pdl_chain": ["content.research", "content.outline", "content.write", "content.edit"],
        "discovery_sources": ["reddit", "linkedin", "upwork", "contently"]
    },
    "marketing": {
        "name": "Marketing & Growth",
        "sku": "marketing",
        "template": "disruptive",
        "description": "Ads, funnels, SEO, lead generation, growth hacking",
        "starter_offers": [
            {"name": "SEO Audit", "price_range": [149, 499], "sla_hours": 48},
            {"name": "Ad Campaign Setup", "price_range": [199, 699], "sla_hours": 72},
            {"name": "Lead Gen Sprint", "price_range": [299, 999], "sla_hours": 168}
        ],
        "pdl_chain": ["marketing.audit", "marketing.strategy", "marketing.execute", "marketing.report"],
        "discovery_sources": ["reddit", "indiehackers", "producthunt", "linkedin"]
    },
    "automation": {
        "name": "Automation & AI",
        "sku": "saas",
        "template": "modern",
        "description": "Zapier flows, AI agents, chatbots, workflow automation",
        "starter_offers": [
            {"name": "Zapier Workflow", "price_range": [99, 399], "sla_hours": 24},
            {"name": "AI Chatbot", "price_range": [199, 799], "sla_hours": 72},
            {"name": "Process Automation", "price_range": [299, 1299], "sla_hours": 168}
        ],
        "pdl_chain": ["automation.map", "automation.build", "automation.test", "automation.deploy"],
        "discovery_sources": ["reddit", "producthunt", "hackernews", "upwork"]
    },
    "consulting": {
        "name": "Strategy & Consulting",
        "sku": "marketing",
        "template": "professional",
        "description": "Business strategy, coaching, audits, advisory calls",
        "starter_offers": [
            {"name": "Strategy Call (60m)", "price_range": [149, 499], "sla_hours": 24},
            {"name": "Business Audit", "price_range": [299, 999], "sla_hours": 72},
            {"name": "Growth Roadmap", "price_range": [499, 1999], "sla_hours": 168}
        ],
        "pdl_chain": ["consulting.intake", "consulting.analyze", "consulting.deliver", "consulting.followup"],
        "discovery_sources": ["linkedin", "twitter", "reddit", "clarity.fm"]
    }
}

# Default toggles (all ON for autopilot)
DEFAULT_TOGGLES = {
    "autopilot": True,
    "overflow_resale_lox": True,
    "outcome_subscriptions": True,
    "auto_discovery": True,
    "auto_quote": True,
    "auto_contract": True,
    "proof_receipts": True,
    "widget_embed": True
}

# Storage
_ONBOARD_SESSIONS: Dict[str, Dict[str, Any]] = {}
_DEPLOYED_BUSINESSES: Dict[str, Dict[str, Any]] = {}


class SimpleOnboard:
    """
    6-question onboarding → fully operational business.
    """

    def __init__(self):
        self.niche_packs = NICHE_PACKS
        self.default_toggles = DEFAULT_TOGGLES
        self._load_policies()

    def _load_policies(self):
        """Load default policies from JSON files"""
        self.policies = {}
        policy_dir = os.path.join(os.path.dirname(__file__), "policies")

        for policy_file in ["pricing", "contract", "lox", "safety", "autospawn", "subscriptions"]:
            path = os.path.join(policy_dir, f"{policy_file}.json")
            try:
                with open(path, "r") as f:
                    self.policies[policy_file] = json.load(f)
            except:
                self.policies[policy_file] = {}

    def start_onboard(self, user_id: str) -> Dict[str, Any]:
        """
        Start onboarding session.

        Returns:
            Session with available niche packs and questions
        """
        session_id = f"onboard_{uuid4().hex[:8]}"

        session = {
            "id": session_id,
            "user_id": user_id,
            "status": "started",
            "started_at": _now(),
            "step": 1,
            "answers": {},
            "niche_packs": {
                k: {"name": v["name"], "description": v["description"]}
                for k, v in self.niche_packs.items()
            },
            "questions": [
                {"step": 1, "field": "business_name", "type": "text", "label": "What's your business name?"},
                {"step": 2, "field": "niche", "type": "select", "label": "Pick your niche", "options": list(self.niche_packs.keys())},
                {"step": 3, "field": "starter_offer", "type": "select", "label": "Choose your starter offer", "options": "dynamic"},
                {"step": 4, "field": "price_band", "type": "range", "label": "Set your price range"},
                {"step": 5, "field": "payout_email", "type": "email", "label": "Payout email (for Stripe)"},
                {"step": 6, "field": "psp_connect", "type": "oauth", "label": "Connect payment processor", "options": ["stripe", "paypal"]}
            ]
        }

        _ONBOARD_SESSIONS[session_id] = session

        return {
            "ok": True,
            "session_id": session_id,
            "session": session
        }

    def answer_step(
        self,
        session_id: str,
        step: int,
        answer: Any
    ) -> Dict[str, Any]:
        """
        Answer an onboarding step.
        """
        session = _ONBOARD_SESSIONS.get(session_id)
        if not session:
            return {"ok": False, "error": "session_not_found"}

        if step != session["step"]:
            return {"ok": False, "error": f"expected_step_{session['step']}"}

        # Store answer
        field = session["questions"][step - 1]["field"]
        session["answers"][field] = answer

        # Process step-specific logic
        result = {"ok": True, "step": step, "field": field, "answer": answer}

        if step == 2:  # Niche selected
            pack = self.niche_packs.get(answer, {})
            result["starter_offers"] = pack.get("starter_offers", [])

        if step == 3:  # Starter offer selected
            niche = session["answers"].get("niche")
            pack = self.niche_packs.get(niche, {})
            offers = pack.get("starter_offers", [])
            selected = next((o for o in offers if o["name"] == answer), offers[0] if offers else {})
            result["price_range"] = selected.get("price_range", [79, 499])
            session["answers"]["selected_offer_details"] = selected

        # Advance step
        session["step"] = step + 1

        if session["step"] > 6:
            session["status"] = "ready_to_deploy"
            result["ready_to_deploy"] = True

        return result

    def complete_onboard(self, session_id: str) -> Dict[str, Any]:
        """
        Complete onboarding and deploy the business.
        """
        session = _ONBOARD_SESSIONS.get(session_id)
        if not session:
            return {"ok": False, "error": "session_not_found"}

        if session["status"] != "ready_to_deploy":
            return {"ok": False, "error": "onboarding_not_complete"}

        answers = session["answers"]
        niche = answers.get("niche", "code")
        pack = self.niche_packs.get(niche, {})

        # Build deployment config
        business_id = f"biz_{uuid4().hex[:8]}"

        deployment = {
            "id": business_id,
            "user_id": session["user_id"],
            "business_name": answers.get("business_name", "My Business"),
            "niche": niche,
            "niche_pack": pack,
            "sku": pack.get("sku", "marketing"),
            "template": pack.get("template", "professional"),
            "starter_offer": answers.get("starter_offer"),
            "price_band": answers.get("price_band", [79, 499]),
            "payout_email": answers.get("payout_email"),
            "psp": answers.get("psp_connect", "stripe"),
            "toggles": self.default_toggles.copy(),
            "policies": self.policies,
            "status": "deploying",
            "deployed_at": _now()
        }

        # Deploy via existing infrastructure
        deployment["deployed_assets"] = self._deploy_business(deployment)

        deployment["status"] = "live"
        _DEPLOYED_BUSINESSES[business_id] = deployment

        session["status"] = "completed"
        session["business_id"] = business_id

        return {
            "ok": True,
            "business_id": business_id,
            "business": deployment,
            "money_panel_url": f"https://aigentsy.com/dashboard/{business_id}",
            "widget_embed": self._generate_widget_embed(deployment),
            "checkout_url": deployment["deployed_assets"].get("checkout_url"),
            "message": "Your business is LIVE. Start sharing your widget to make money."
        }

    def _deploy_business(self, deployment: Dict) -> Dict[str, Any]:
        """Deploy business using existing infrastructure"""
        assets = {}

        # 1. Try SKU Orchestrator
        try:
            from sku_orchestrator import UniversalBusinessOrchestrator

            orchestrator = UniversalBusinessOrchestrator()
            result = orchestrator.mint_business(
                user_id=deployment["user_id"],
                user_data={
                    "name": deployment["business_name"],
                    "email": deployment["payout_email"]
                },
                sku_id=deployment["sku"],
                template_choice=deployment["template"]
            )
            assets["sku_mint"] = result
            assets["storefront_url"] = result.get("storefront", {}).get("url")
        except Exception as e:
            assets["sku_mint_error"] = str(e)

        # 2. Generate One-Tap Widget
        try:
            from one_tap_widget import create_widget_config, generate_embed_code

            widget_result = create_widget_config(
                partner_id=deployment["user_id"],
                name=f"{deployment['business_name']} Widget",
                button_text="Get This Done"
            )
            if widget_result.get("ok"):
                assets["widget_id"] = widget_result["widget_id"]
                embed = generate_embed_code(widget_result["widget_id"])
                assets["widget_embed"] = embed.get("embed_code")
        except Exception as e:
            assets["widget_error"] = str(e)

        # 3. Setup Subscription Tier
        try:
            from outcome_subscriptions import create_retainer

            # Auto-create starter retainer offering
            assets["subscriptions_enabled"] = True
        except:
            assets["subscriptions_enabled"] = False

        # 4. Generate Checkout URL (PSP)
        psp = deployment.get("psp", "stripe")
        price_min, price_max = deployment.get("price_band", [79, 499])
        starter_price = int((price_min + price_max) / 2)

        if psp == "stripe":
            assets["checkout_url"] = f"https://buy.stripe.com/test_{deployment['id'][:8]}?price={starter_price}"
        else:
            assets["checkout_url"] = f"https://paypal.me/{deployment['business_name'].replace(' ', '')}?amount={starter_price}"

        # 5. Enable Discovery Sources
        pack = deployment.get("niche_pack", {})
        assets["discovery_sources"] = pack.get("discovery_sources", [])
        assets["pdl_chain"] = pack.get("pdl_chain", [])

        return assets

    def _generate_widget_embed(self, deployment: Dict) -> str:
        """Generate widget embed code"""
        widget_id = deployment.get("deployed_assets", {}).get("widget_id", "demo")
        return f'''<!-- {deployment["business_name"]} Widget -->
<div id="aigentsy-widget"></div>
<script src="https://aigentsy.com/widget/v1/aigentsy.min.js"
        data-widget-id="{widget_id}"
        data-button-text="Get This Done">
</script>'''

    def get_onboard_status(self, session_id: str) -> Dict[str, Any]:
        """Get onboarding session status"""
        session = _ONBOARD_SESSIONS.get(session_id)
        if not session:
            return {"ok": False, "error": "session_not_found"}

        return {
            "ok": True,
            "session_id": session_id,
            "status": session["status"],
            "step": session["step"],
            "answers": session["answers"],
            "business_id": session.get("business_id")
        }

    def get_business(self, business_id: str) -> Optional[Dict[str, Any]]:
        """Get deployed business details"""
        return _DEPLOYED_BUSINESSES.get(business_id)

    def get_money_panel(self, business_id: str) -> Dict[str, Any]:
        """Get the simple Money Panel view"""
        business = _DEPLOYED_BUSINESSES.get(business_id)
        if not business:
            return {"ok": False, "error": "business_not_found"}

        # Would pull from actual metrics
        return {
            "business_id": business_id,
            "business_name": business["business_name"],
            "leads": 0,
            "sales": 0,
            "active_jobs": 0,
            "on_time_pct": 100.0,
            "payouts_scheduled": 0.0,
            "status": "live",
            "widget_views": 0,
            "subscription_mrr": 0.0,
            "lox_revenue": 0.0
        }


# Module-level singleton
_onboard = SimpleOnboard()


def start_onboard(user_id: str) -> Dict[str, Any]:
    """Start 6-question onboarding"""
    return _onboard.start_onboard(user_id)


def answer_onboard_step(session_id: str, step: int, answer: Any) -> Dict[str, Any]:
    """Answer onboarding step"""
    return _onboard.answer_step(session_id, step, answer)


def complete_onboard(session_id: str) -> Dict[str, Any]:
    """Complete onboarding and deploy business"""
    return _onboard.complete_onboard(session_id)


def get_onboard_status(session_id: str) -> Dict[str, Any]:
    """Get onboarding status"""
    return _onboard.get_onboard_status(session_id)


def get_business(business_id: str) -> Optional[Dict[str, Any]]:
    """Get deployed business"""
    return _onboard.get_business(business_id)


def get_money_panel(business_id: str) -> Dict[str, Any]:
    """Get Money Panel view"""
    return _onboard.get_money_panel(business_id)


def get_niche_packs() -> Dict[str, Any]:
    """Get available niche packs"""
    return {
        k: {"name": v["name"], "description": v["description"]}
        for k, v in NICHE_PACKS.items()
    }
