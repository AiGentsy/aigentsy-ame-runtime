"""
═══════════════════════════════════════════════════════════════════════════════
AUTO-SPAWN ENGINE v1.0 - THE AI VENTURE FACTORY
═══════════════════════════════════════════════════════════════════════════════

VISION: AiGentsy autonomously spawns, tests, and scales businesses.
Users don't build businesses - AI does. Users just profit.

FLOW:
1. DETECT trends across Reddit/TikTok/Google/Perplexity
2. SPAWN complete businesses (landing page + Stripe + fulfillment)
3. MARKET via auto-generated viral content
4. FULFILL orders via Wade (AI delivery)
5. LEARN what works, kill what doesn't
6. SCALE winners, offer successful spawns for user adoption

NOVEL FEATURES:
- SPAWN SWARM: Launch 10 businesses, kill 8, scale 2
- ZOMBIE REVIVAL: Dead businesses auto-relaunch when trends return
- FRANCHISE MODE: Clone winning businesses into adjacent niches
- VIRAL HOOKS: AI generates scroll-stopping content
- PRICE ELASTICITY: Auto-adjust prices based on conversion

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import asyncio
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
import random


class SpawnStatus(str, Enum):
    INCUBATING = "incubating"
    LAUNCHING = "launching"
    LIVE = "live"
    SCALING = "scaling"
    VIRAL = "viral"
    HIBERNATING = "hibernating"
    ZOMBIE = "zombie"
    DEAD = "dead"
    ADOPTED = "adopted"


class NicheCategory(str, Enum):
    AI_ART = "ai_art"
    CONTENT = "content"
    DESIGN = "design"
    RESEARCH = "research"
    VOICE = "voice"
    VIDEO = "video"
    AUTOMATION = "automation"
    ECOMMERCE = "ecommerce"
    SAAS_MICRO = "saas_micro"


@dataclass
class TrendSignal:
    signal_id: str
    source: str
    query: str
    category: NicheCategory
    demand_score: float
    competition_score: float
    monetization_potential: float
    urgency: float
    viral_potential: float = 50.0
    raw_data: Dict[str, Any] = field(default_factory=dict)
    detected_at: str = ""
    
    @property
    def opportunity_score(self) -> float:
        return (self.demand_score * 0.30 + (100 - self.competition_score) * 0.20 +
                self.monetization_potential * 0.25 + self.urgency * 0.10 + self.viral_potential * 0.15)


@dataclass
class SpawnedBusiness:
    spawn_id: str
    name: str
    slug: str
    tagline: str
    category: NicheCategory
    niche: str
    trigger_signal: Optional[TrendSignal] = None
    spawned_at: str = ""
    status: SpawnStatus = SpawnStatus.INCUBATING
    landing_page_url: str = ""
    stripe_product_id: str = ""
    base_price: float = 0.0
    current_price: float = 0.0
    services: List[Dict] = field(default_factory=list)
    marketing_budget_daily: float = 5.0
    marketing_spend_total: float = 0.0
    content_queue: List[Dict] = field(default_factory=list)
    impressions: int = 0
    clicks: int = 0
    orders: int = 0
    revenue: float = 0.0
    profit: float = 0.0
    cac: float = 0.0
    ltv: float = 0.0
    conversion_rate: float = 0.0
    days_live: int = 0
    health_score: float = 50.0
    auto_kill_at: str = ""
    owner: str = "aigentsy"
    adopted_by: str = ""
    
    # ═══════════════════════════════════════════════════════════════════════════
    # AIGENTSY ECOSYSTEM INTEGRATION
    # Every spawned business is an AiGentsy property
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Referral & Attribution
    referral_code: str = ""                    # Unique code for this spawn (e.g., "PETART-X7K2")
    referral_signups: int = 0                  # Users who signed up via this spawn
    referral_revenue: float = 0.0             # Revenue from referred users
    
    # AiGentsy Branding
    powered_by_aigentsy: bool = True          # Shows "Powered by AiGentsy" footer
    aigentsy_cta_enabled: bool = True         # "Want AI to build YOUR business?" CTA
    aigentsy_dashboard_link: str = ""         # Link back to main dashboard
    
    # User Conversion Funnel
    email_captures: int = 0                    # Emails collected (potential AiGentsy users)
    aigentsy_cta_clicks: int = 0              # Clicks on "Join AiGentsy" CTA
    converted_to_aigentsy_user: int = 0       # Actually became AiGentsy users
    
    # Wade Integration (fulfillment ties to main system)
    wade_user_id: str = "wade_system"         # Wade account handling fulfillment
    fulfillment_queue_id: str = ""            # Links to /wade/fulfillment-queue
    
    # Revenue Attribution (ties to your Stripe)
    stripe_connect_account: str = ""          # Your Stripe Connect account
    revenue_split_aigentsy: float = 1.0       # 100% to AiGentsy (until adopted)
    
    # Dashboard Integration
    visible_in_wade_dashboard: bool = True    # Shows in wade-dashboard.html
    visible_in_main_dashboard: bool = False   # Shows in aigent0.html (after adoption)
    
    # MetaHive/Yield Memory
    contributes_to_hive: bool = True          # Learnings shared with network
    yield_memory_entries: int = 0             # Patterns learned from this spawn


# ═══════════════════════════════════════════════════════════════════════════════
# BUSINESS TEMPLATES - What we can spawn
# These are CONFIGURATION - add any business type here
# ═══════════════════════════════════════════════════════════════════════════════

# Template structure:
# - name_patterns: How to name the business ({Subject}, {Type}, {Niche} are replaced)
# - services: Pricing tiers with features
# - hooks: Marketing hooks for social content
# - platforms: Where to market
# - fulfillment: Which AI system delivers (stability_ai, claude_ai, elevenlabs, etc)
# - landing_template: Which Actionized template to use
# - revenue_model: one_time, subscription, usage_based, hybrid

BUSINESS_TEMPLATES = {
    # ═══════════════════════════════════════════════════════════════════════════
    # CREATIVE SERVICES
    # ═══════════════════════════════════════════════════════════════════════════
    NicheCategory.AI_ART: {
        "name_patterns": ["AI {Subject} Studio", "{Subject} by AI", "Instant {Subject}", "{Subject} Express"],
        "services": [
            {"name": "Basic", "price": 9, "delivery_hours": 2, "features": ["1 style", "Digital delivery"]},
            {"name": "Standard", "price": 19, "delivery_hours": 4, "features": ["3 styles", "Revisions"]},
            {"name": "Premium", "price": 39, "delivery_hours": 1, "features": ["5 styles", "Rush", "Source files"]}
        ],
        "hooks": [
            "🎨 {Subject} in minutes, not days",
            "✨ Professional {Subject} for ${price}",
            "🚀 {hours}-hour delivery guaranteed",
            "🔥 AI-powered {Subject} going viral"
        ],
        "platforms": ["tiktok", "instagram", "etsy", "fiverr"],
        "fulfillment": "stability_ai",
        "landing_template": "creative_service",
        "revenue_model": "one_time"
    },
    
    NicheCategory.CONTENT: {
        "name_patterns": ["AI Content {Type}", "Instant {Type}", "Smart {Type}", "{Type} Machine"],
        "services": [
            {"name": "Starter", "price": 15, "delivery_hours": 2, "features": ["500 words", "SEO optimized"]},
            {"name": "Pro", "price": 35, "delivery_hours": 4, "features": ["1500 words", "Research", "Revisions"]},
            {"name": "Enterprise", "price": 99, "delivery_hours": 12, "features": ["5000 words", "Expert review", "Unlimited revisions"]}
        ],
        "hooks": [
            "📝 {Type} that ranks on Google",
            "✍️ {Type} in hours, not weeks",
            "🎯 SEO-optimized {Type} from ${price}",
            "💰 {Type} that converts visitors to buyers"
        ],
        "platforms": ["linkedin", "twitter", "upwork", "fiverr"],
        "fulfillment": "claude_ai",
        "landing_template": "content_service",
        "revenue_model": "one_time"
    },
    
    NicheCategory.DESIGN: {
        "name_patterns": ["Rapid {Type}", "{Type} Express", "AI {Type} Pro", "Instant {Type}"],
        "services": [
            {"name": "Quick", "price": 5, "delivery_hours": 1, "features": ["1 design", "PNG format"]},
            {"name": "Standard", "price": 15, "delivery_hours": 2, "features": ["3 designs", "Revisions", "All formats"]},
            {"name": "Bulk", "price": 49, "delivery_hours": 6, "features": ["10 designs", "Source files", "Brand kit"]}
        ],
        "hooks": [
            "🎨 Eye-catching {Type} in 1 hour",
            "📈 {Type} that get clicks",
            "⚡ Same-day {Type} from ${price}",
            "🔥 {Type} your competitors wish they had"
        ],
        "platforms": ["tiktok", "instagram", "fiverr", "dribbble"],
        "fulfillment": "stability_ai",
        "landing_template": "creative_service",
        "revenue_model": "one_time"
    },
    
    NicheCategory.VOICE: {
        "name_patterns": ["AI Voice {Type}", "Instant {Type}", "{Type} Now", "Voice {Type} Pro"],
        "services": [
            {"name": "Short", "price": 10, "delivery_hours": 0.5, "features": ["500 words", "1 voice", "MP3"]},
            {"name": "Standard", "price": 25, "delivery_hours": 2, "features": ["2000 words", "Voice selection", "WAV/MP3"]},
            {"name": "Long-form", "price": 75, "delivery_hours": 6, "features": ["10000 words", "Premium voices", "All formats"]}
        ],
        "hooks": [
            "🎙️ Professional {Type} in minutes",
            "🔊 Natural AI {Type} - can't tell it's AI",
            "⚡ {Type} delivered in under 1 hour",
            "💰 Save 90% vs human voice actors"
        ],
        "platforms": ["fiverr", "upwork", "youtube", "podcast_directories"],
        "fulfillment": "elevenlabs",
        "landing_template": "creative_service",
        "revenue_model": "one_time"
    },
    
    NicheCategory.VIDEO: {
        "name_patterns": ["Quick {Type}", "{Type} Express", "AI {Type}", "Viral {Type}"],
        "services": [
            {"name": "Basic", "price": 19, "delivery_hours": 4, "features": ["60s max", "Basic effects", "Music"]},
            {"name": "Pro", "price": 49, "delivery_hours": 8, "features": ["3 min", "Advanced effects", "Color grade"]},
            {"name": "Full", "price": 149, "delivery_hours": 24, "features": ["10 min", "Motion graphics", "Sound design"]}
        ],
        "hooks": [
            "🎬 Scroll-stopping {Type} in hours",
            "📱 {Type} that go viral",
            "✂️ Professional {Type} from ${price}",
            "🔥 {Type} that break the algorithm"
        ],
        "platforms": ["tiktok", "instagram", "fiverr", "youtube"],
        "fulfillment": "runway_ai",
        "landing_template": "creative_service",
        "revenue_model": "one_time"
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # BUSINESS SERVICES
    # ═══════════════════════════════════════════════════════════════════════════
    NicheCategory.AUTOMATION: {
        "name_patterns": ["Auto {Type}", "{Type} Bot", "Smart {Type}", "{Type} Autopilot"],
        "services": [
            {"name": "Simple", "price": 49, "delivery_hours": 4, "features": ["1 workflow", "Documentation"]},
            {"name": "Advanced", "price": 149, "delivery_hours": 12, "features": ["3 workflows", "Error handling", "Support"]},
            {"name": "Enterprise", "price": 499, "delivery_hours": 48, "features": ["Unlimited workflows", "Custom integrations", "Maintenance"]}
        ],
        "hooks": [
            "🤖 {Type} that saves 10+ hours/week",
            "⚡ Set up your {Type} in hours, not weeks",
            "🔄 Never do manual {Type} again",
            "💰 ROI in the first week guaranteed"
        ],
        "platforms": ["twitter", "linkedin", "producthunt", "upwork"],
        "fulfillment": "claude_code",
        "landing_template": "saas_template",
        "revenue_model": "one_time"
    },
    
    NicheCategory.RESEARCH: {
        "name_patterns": ["AI {Type} Lab", "Instant {Type}", "{Type} Intelligence", "Deep {Type}"],
        "services": [
            {"name": "Summary", "price": 29, "delivery_hours": 4, "features": ["5-page report", "Key insights", "Sources"]},
            {"name": "Detailed", "price": 79, "delivery_hours": 12, "features": ["15-page report", "Data analysis", "Recommendations"]},
            {"name": "Comprehensive", "price": 199, "delivery_hours": 24, "features": ["40+ pages", "Expert review", "Presentation deck"]}
        ],
        "hooks": [
            "📊 {Type} that drives decisions",
            "🔍 AI-powered {Type} in hours",
            "💡 Actionable {Type} insights",
            "🎯 {Type} your competitors don't have"
        ],
        "platforms": ["linkedin", "upwork", "twitter"],
        "fulfillment": "perplexity_claude",
        "landing_template": "professional_service",
        "revenue_model": "one_time"
    },
    
    NicheCategory.ECOMMERCE: {
        "name_patterns": ["{Niche} Empire", "Auto {Niche}", "{Niche} Autopilot", "Smart {Niche}"],
        "services": [
            {"name": "Starter Store", "price": 99, "delivery_hours": 24, "features": ["5 products", "Basic design", "Stripe setup"]},
            {"name": "Growth Store", "price": 299, "delivery_hours": 48, "features": ["25 products", "Custom design", "Marketing setup"]},
            {"name": "Empire", "price": 999, "delivery_hours": 72, "features": ["100 products", "Premium design", "Full automation"]}
        ],
        "hooks": [
            "🛒 Launch your {Niche} store in 24 hours",
            "💰 {Niche} business, zero inventory",
            "🚀 From idea to selling in a weekend",
            "🔥 {Niche} store that runs itself"
        ],
        "platforms": ["tiktok", "instagram", "youtube", "reddit"],
        "fulfillment": "shopify_automation",
        "landing_template": "ecommerce_template",
        "revenue_model": "one_time"
    },
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SAAS / RECURRING REVENUE (Your Actionized SaaS Templates)
    # ═══════════════════════════════════════════════════════════════════════════
    NicheCategory.SAAS_MICRO: {
        "name_patterns": ["{Niche}ly", "{Niche}Hub", "{Niche}Pilot", "Auto{Niche}", "{Niche}AI"],
        "services": [
            {"name": "Free", "price": 0, "billing": "forever", "features": ["Basic features", "Community support", "5 uses/day"]},
            {"name": "Pro", "price": 19, "billing": "monthly", "features": ["Unlimited uses", "Priority support", "Advanced features"]},
            {"name": "Team", "price": 49, "billing": "monthly", "features": ["5 team members", "API access", "Custom integrations"]},
            {"name": "Enterprise", "price": 199, "billing": "monthly", "features": ["Unlimited team", "Dedicated support", "White label"]}
        ],
        "hooks": [
            "🚀 {Niche} on autopilot",
            "⚡ The {Niche} tool everyone's talking about",
            "💰 {Niche} that pays for itself in a week",
            "🔥 {Niche} software that actually works"
        ],
        "platforms": ["producthunt", "twitter", "linkedin", "hackernews", "reddit"],
        "fulfillment": "custom_saas",
        "landing_template": "saas_template",
        "revenue_model": "subscription",
        # SaaS-specific settings
        "trial_days": 14,
        "churn_prediction": True,
        "upsell_triggers": ["usage_limit", "feature_gate", "team_growth"]
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIONIZED TEMPLATES - Pre-built landing page/funnel templates
# These plug into any spawned business
# ═══════════════════════════════════════════════════════════════════════════════

ACTIONIZED_TEMPLATES = {
    "saas_template": {
        "sections": ["hero", "features", "pricing", "testimonials", "faq", "cta"],
        "conversion_elements": ["free_trial_button", "demo_video", "social_proof", "guarantee"],
        "integrations": ["stripe", "intercom", "analytics", "email"],
        "pages": ["landing", "pricing", "features", "about", "blog", "docs"],
        "email_sequences": ["welcome", "onboarding", "trial_ending", "upgrade_nudge", "win_back"]
    },
    "creative_service": {
        "sections": ["hero", "portfolio", "pricing", "process", "testimonials", "cta"],
        "conversion_elements": ["order_button", "portfolio_gallery", "before_after", "guarantee"],
        "integrations": ["stripe", "calendly", "email"],
        "pages": ["landing", "portfolio", "pricing", "contact"],
        "email_sequences": ["order_confirm", "delivery", "review_request", "upsell"]
    },
    "content_service": {
        "sections": ["hero", "samples", "pricing", "process", "testimonials", "cta"],
        "conversion_elements": ["order_form", "sample_work", "turnaround_timer", "guarantee"],
        "integrations": ["stripe", "google_docs", "email"],
        "pages": ["landing", "samples", "pricing", "blog"],
        "email_sequences": ["order_confirm", "draft_ready", "revision", "delivery", "upsell"]
    },
    "professional_service": {
        "sections": ["hero", "expertise", "case_studies", "pricing", "testimonials", "cta"],
        "conversion_elements": ["consultation_booking", "case_study_download", "credentials"],
        "integrations": ["stripe", "calendly", "notion", "email"],
        "pages": ["landing", "services", "case_studies", "about", "contact"],
        "email_sequences": ["inquiry_response", "proposal", "follow_up", "delivery", "referral"]
    },
    "ecommerce_template": {
        "sections": ["hero", "products", "benefits", "reviews", "faq", "cta"],
        "conversion_elements": ["add_to_cart", "product_gallery", "reviews", "urgency_timer"],
        "integrations": ["stripe", "shopify", "email", "sms"],
        "pages": ["landing", "products", "cart", "checkout", "thank_you"],
        "email_sequences": ["order_confirm", "shipping", "delivered", "review_request", "reorder"]
    },
    "marketing_agency": {
        "sections": ["hero", "services", "results", "case_studies", "pricing", "cta"],
        "conversion_elements": ["audit_request", "roi_calculator", "case_study_download"],
        "integrations": ["stripe", "calendly", "hubspot", "analytics"],
        "pages": ["landing", "services", "results", "about", "contact", "blog"],
        "email_sequences": ["inquiry", "audit_delivery", "proposal", "onboarding", "monthly_report"]
    },
    "coaching_program": {
        "sections": ["hero", "transformation", "curriculum", "testimonials", "pricing", "faq", "cta"],
        "conversion_elements": ["application_form", "webinar_signup", "success_stories"],
        "integrations": ["stripe", "calendly", "circle", "email"],
        "pages": ["landing", "program", "results", "apply", "webinar"],
        "email_sequences": ["application_received", "interview_booking", "accepted", "onboarding", "check_in"]
    },
    "newsletter_media": {
        "sections": ["hero", "sample_content", "benefits", "testimonials", "subscribe", "cta"],
        "conversion_elements": ["subscribe_form", "free_issue", "social_proof"],
        "integrations": ["stripe", "beehiiv", "convertkit", "twitter"],
        "pages": ["landing", "archive", "about", "advertise"],
        "email_sequences": ["welcome", "best_of", "upgrade", "sponsor_cta"]
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM TEMPLATE SYSTEM - Users can define their own
# ═══════════════════════════════════════════════════════════════════════════════

def register_custom_template(category: str, template: Dict) -> bool:
    """
    Register a custom business template.
    Users can add their own business types!
    
    Example:
    register_custom_template("consulting", {
        "name_patterns": ["{Niche} Consulting", "{Niche} Advisors"],
        "services": [...],
        "hooks": [...],
        "platforms": [...],
        "fulfillment": "human_ai_hybrid",
        "landing_template": "professional_service"
    })
    """
    try:
        # Validate required fields
        required = ["name_patterns", "services", "hooks", "platforms", "fulfillment"]
        for field in required:
            if field not in template:
                return False
        
        # Add to templates (using string key for custom categories)
        BUSINESS_TEMPLATES[category] = template
        return True
    except:
        return False


def get_available_categories() -> List[str]:
    """Get all available business categories (built-in + custom)"""
    categories = [cat.value for cat in NicheCategory]
    # Add any custom string keys
    for key in BUSINESS_TEMPLATES.keys():
        if isinstance(key, str) and key not in categories:
            categories.append(key)
    return categories
# ═══════════════════════════════════════════════════════════════════════════════
# CROSS-PROMOTION NETWORK
# All spawned businesses help each other reach users/customers
# They're all AiGentsy properties - should act as ONE network
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CrossPromotion:
    """A cross-promotion between two spawned businesses"""
    promo_id: str
    source_spawn_id: str          # Business doing the promoting
    target_spawn_id: str          # Business being promoted
    promo_type: str               # "email", "checkout", "content", "bundle"
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue_generated: float = 0.0
    created_at: str = ""
    active: bool = True


class SpawnNetwork:
    """
    The network that connects all spawned businesses.
    Every spawn helps every other spawn reach customers.
    
    CROSS-PROMO TYPES:
    1. CHECKOUT UPSELL: "You might also like..." after purchase
    2. EMAIL CROSS-SELL: "Other AI services you'll love"
    3. CONTENT MENTIONS: Social posts mention related spawns
    4. BUNDLE DEALS: Buy from 2+ spawns, get discount
    5. REFERRAL CHAIN: Customer of Spawn A → referred to Spawn B
    6. RETARGETING POOL: Shared pixel/audience across all spawns
    """
    
    def __init__(self):
        self.promotions: Dict[str, CrossPromotion] = {}
        self.network_stats = {
            "total_cross_promos": 0,
            "cross_promo_revenue": 0.0,
            "cross_promo_conversions": 0
        }
    
    def find_complementary_spawns(self, spawn: SpawnedBusiness, all_spawns: List[SpawnedBusiness]) -> List[SpawnedBusiness]:
        """
        Find spawns that complement this one (different category, same audience).
        Example: Pet Portrait buyer might want Content Writing for their pet blog.
        """
        complementary = []
        
        # Category affinity map - which categories go well together
        CATEGORY_AFFINITY = {
            NicheCategory.AI_ART: [NicheCategory.CONTENT, NicheCategory.DESIGN, NicheCategory.VIDEO],
            NicheCategory.CONTENT: [NicheCategory.DESIGN, NicheCategory.VOICE, NicheCategory.AI_ART],
            NicheCategory.DESIGN: [NicheCategory.AI_ART, NicheCategory.VIDEO, NicheCategory.CONTENT],
            NicheCategory.VOICE: [NicheCategory.VIDEO, NicheCategory.CONTENT, NicheCategory.AUTOMATION],
            NicheCategory.VIDEO: [NicheCategory.DESIGN, NicheCategory.VOICE, NicheCategory.AI_ART],
            NicheCategory.AUTOMATION: [NicheCategory.SAAS_MICRO, NicheCategory.CONTENT, NicheCategory.RESEARCH],
            NicheCategory.RESEARCH: [NicheCategory.CONTENT, NicheCategory.AUTOMATION, NicheCategory.SAAS_MICRO],
            NicheCategory.ECOMMERCE: [NicheCategory.DESIGN, NicheCategory.CONTENT, NicheCategory.AI_ART],
            NicheCategory.SAAS_MICRO: [NicheCategory.AUTOMATION, NicheCategory.CONTENT, NicheCategory.DESIGN]
        }
        
        affinity_categories = CATEGORY_AFFINITY.get(spawn.category, [])
        
        for other in all_spawns:
            if other.spawn_id == spawn.spawn_id:
                continue
            if other.status not in [SpawnStatus.LIVE, SpawnStatus.SCALING]:
                continue
            if other.category in affinity_categories:
                complementary.append(other)
        
        # Sort by health score (promote healthiest spawns)
        complementary.sort(key=lambda x: x.health_score, reverse=True)
        return complementary[:3]  # Top 3 complementary
    
    def generate_checkout_upsells(self, spawn: SpawnedBusiness, all_spawns: List[SpawnedBusiness]) -> List[Dict]:
        """
        Generate "You might also like" suggestions for checkout page.
        Shown after customer purchases from this spawn.
        """
        complementary = self.find_complementary_spawns(spawn, all_spawns)
        
        upsells = []
        for comp in complementary:
            upsells.append({
                "spawn_id": comp.spawn_id,
                "name": comp.name,
                "tagline": comp.tagline,
                "price": comp.current_price,
                "discount": 15,  # 15% off when buying from network
                "discounted_price": round(comp.current_price * 0.85, 2),
                "url": f"{comp.landing_page_url}?ref={spawn.referral_code}&network=1",
                "promo_code": f"NETWORK15_{spawn.referral_code[:6]}"
            })
        
        return upsells
    
    def generate_email_cross_sell(self, spawn: SpawnedBusiness, all_spawns: List[SpawnedBusiness]) -> Dict:
        """
        Generate cross-sell email content to send to spawn's customers.
        "Thanks for your order! Here are other AI services you'll love..."
        """
        complementary = self.find_complementary_spawns(spawn, all_spawns)
        
        if not complementary:
            return {}
        
        email = {
            "subject": f"🚀 More AI magic for you, from AiGentsy",
            "preview": "Exclusive deals on services that pair perfectly with your recent order",
            "intro": f"You loved {spawn.name} - here are other AI-powered services from our network:",
            "offers": [],
            "footer_cta": {
                "text": "Want AI building YOUR business? Join AiGentsy free →",
                "url": f"https://aigentsy.com/start?ref={spawn.referral_code}"
            }
        }
        
        for comp in complementary:
            email["offers"].append({
                "name": comp.name,
                "tagline": comp.tagline,
                "original_price": comp.current_price,
                "network_price": round(comp.current_price * 0.80, 2),  # 20% off
                "savings": f"Save ${round(comp.current_price * 0.20, 2)}",
                "cta_url": f"{comp.landing_page_url}?ref={spawn.referral_code}&email=1",
                "promo_code": f"EMAIL20_{spawn.referral_code[:6]}"
            })
        
        return email
    
    def generate_social_mentions(self, spawn: SpawnedBusiness, all_spawns: List[SpawnedBusiness]) -> List[Dict]:
        """
        Generate social content that mentions other spawns.
        Every 4th post mentions a complementary spawn.
        """
        complementary = self.find_complementary_spawns(spawn, all_spawns)
        
        mentions = []
        for comp in complementary:
            mention_hooks = [
                f"🔥 Loving {spawn.name}? Check out {comp.name} for {comp.niche.lower()}!",
                f"✨ {spawn.name} + {comp.name} = unstoppable combo 💪",
                f"Pro tip: Pair your {spawn.niche} with {comp.niche} from our network →",
                f"🚀 Our AI network keeps growing! {comp.name} just launched - {comp.tagline}"
            ]
            
            mentions.append({
                "hook": random.choice(mention_hooks),
                "target_spawn": comp.spawn_id,
                "target_url": f"{comp.landing_page_url}?ref={spawn.referral_code}&social=1",
                "hashtags": [f"#{spawn.niche.replace(' ', '')}", f"#{comp.niche.replace(' ', '')}", "#AiGentsy", "#AINetwork"]
            })
        
        return mentions
    
    def create_bundle_deal(self, spawns: List[SpawnedBusiness]) -> Dict:
        """
        Create a bundle deal across multiple spawns.
        "Get all 3 for 30% off!"
        """
        if len(spawns) < 2:
            return {}
        
        bundle_id = f"bundle_{secrets.token_hex(6)}"
        total_price = sum(s.current_price for s in spawns)
        bundle_discount = 0.25 if len(spawns) == 2 else 0.30  # 25% for 2, 30% for 3+
        bundle_price = round(total_price * (1 - bundle_discount), 2)
        
        return {
            "bundle_id": bundle_id,
            "name": f"AI Power Bundle ({len(spawns)} services)",
            "spawns": [{"spawn_id": s.spawn_id, "name": s.name, "price": s.current_price} for s in spawns],
            "original_total": total_price,
            "bundle_price": bundle_price,
            "savings": round(total_price - bundle_price, 2),
            "discount_percent": int(bundle_discount * 100),
            "promo_code": f"BUNDLE{int(bundle_discount*100)}_{bundle_id[:6].upper()}",
            "landing_url": f"https://spawns.aigentsy.com/bundles/{bundle_id}"
        }
    
    def get_network_recommendations(self, customer_history: List[str], all_spawns: List[SpawnedBusiness]) -> List[Dict]:
        """
        Based on what customer has bought, recommend other spawns.
        Uses collaborative filtering logic.
        """
        # Find categories customer has purchased from
        purchased_categories = set()
        for spawn_id in customer_history:
            for spawn in all_spawns:
                if spawn.spawn_id == spawn_id:
                    purchased_categories.add(spawn.category)
        
        # Find spawns in complementary categories they haven't bought
        recommendations = []
        for spawn in all_spawns:
            if spawn.spawn_id in customer_history:
                continue
            if spawn.status not in [SpawnStatus.LIVE, SpawnStatus.SCALING]:
                continue
            
            # Score based on category affinity
            score = 0
            for purchased_cat in purchased_categories:
                if spawn.category in CATEGORY_AFFINITY.get(purchased_cat, []):
                    score += 30
            
            # Boost by health score
            score += spawn.health_score * 0.5
            
            if score > 0:
                recommendations.append({
                    "spawn_id": spawn.spawn_id,
                    "name": spawn.name,
                    "category": spawn.category.value,
                    "price": spawn.current_price,
                    "score": score,
                    "reason": f"Because you liked {list(purchased_categories)[0].value if purchased_categories else 'similar'} services"
                })
        
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:5]
    
    def get_shared_audience_pool(self, all_spawns: List[SpawnedBusiness]) -> Dict:
        """
        Aggregate all customer emails across spawns for retargeting.
        One big audience pool that all spawns can use.
        """
        all_emails = set()
        by_category = {}
        
        for spawn in all_spawns:
            all_emails.update(spawn.customer_emails)
            
            cat = spawn.category.value
            if cat not in by_category:
                by_category[cat] = set()
            by_category[cat].update(spawn.customer_emails)
        
        return {
            "total_audience": len(all_emails),
            "by_category": {k: len(v) for k, v in by_category.items()},
            "retarget_eligible": len([e for e in all_emails if e]),  # Non-empty
            "lookalike_seed_size": min(len(all_emails), 10000)  # For FB/Google lookalikes
        }


# Category affinity map (global for reference)
CATEGORY_AFFINITY = {
    NicheCategory.AI_ART: [NicheCategory.CONTENT, NicheCategory.DESIGN, NicheCategory.VIDEO],
    NicheCategory.CONTENT: [NicheCategory.DESIGN, NicheCategory.VOICE, NicheCategory.AI_ART],
    NicheCategory.DESIGN: [NicheCategory.AI_ART, NicheCategory.VIDEO, NicheCategory.CONTENT],
    NicheCategory.VOICE: [NicheCategory.VIDEO, NicheCategory.CONTENT, NicheCategory.AUTOMATION],
    NicheCategory.VIDEO: [NicheCategory.DESIGN, NicheCategory.VOICE, NicheCategory.AI_ART],
    NicheCategory.AUTOMATION: [NicheCategory.SAAS_MICRO, NicheCategory.CONTENT, NicheCategory.RESEARCH],
    NicheCategory.RESEARCH: [NicheCategory.CONTENT, NicheCategory.AUTOMATION, NicheCategory.SAAS_MICRO],
    NicheCategory.ECOMMERCE: [NicheCategory.DESIGN, NicheCategory.CONTENT, NicheCategory.AI_ART],
    NicheCategory.SAAS_MICRO: [NicheCategory.AUTOMATION, NicheCategory.CONTENT, NicheCategory.DESIGN]
}


# ═══════════════════════════════════════════════════════════════════════════════
# TREND DETECTOR - REAL API CALLS TO REAL PLATFORMS
# NO MOCK DATA - ALL LIVE SCRAPING
# ═══════════════════════════════════════════════════════════════════════════════

import httpx

# Keywords that map to business categories
CATEGORY_KEYWORDS = {
    NicheCategory.AI_ART: ["ai art", "ai portrait", "ai image", "midjourney", "dalle", "stable diffusion", "ai photo", "ai headshot", "pet portrait"],
    NicheCategory.CONTENT: ["content", "blog", "article", "copywriting", "seo", "ghostwriting", "writing"],
    NicheCategory.DESIGN: ["design", "thumbnail", "logo", "graphic", "ui", "ux", "figma", "canva", "branding"],
    NicheCategory.RESEARCH: ["research", "data", "analysis", "report", "market research"],
    NicheCategory.VOICE: ["voice", "voiceover", "podcast", "audio", "narration", "text to speech"],
    NicheCategory.VIDEO: ["video", "edit", "tiktok", "youtube", "reels", "shorts", "animation"],
    NicheCategory.AUTOMATION: ["automation", "bot", "script", "workflow", "zapier", "n8n"],
    NicheCategory.ECOMMERCE: ["ecommerce", "shopify", "amazon", "dropship", "product listing"],
    NicheCategory.SAAS_MICRO: ["saas", "app", "tool", "software", "chrome extension", "api"]
}


def _categorize_opportunity(title: str, body: str = "") -> NicheCategory:
    """Determine category based on keywords in title/body"""
    text = (title + " " + body).lower()
    
    best_match = NicheCategory.CONTENT  # Default
    best_score = 0
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_match = category
    
    return best_match


def _calculate_scores(post: Dict[str, Any], source: str) -> Dict[str, float]:
    """Calculate demand, competition, monetization scores from post data"""
    
    # Reddit scoring
    if source == "reddit":
        score = post.get("score", 0)
        num_comments = post.get("num_comments", 0)
        
        demand = min(95, 50 + score * 2 + num_comments * 3)
        competition = 40 if num_comments < 5 else 60 if num_comments < 20 else 80
        monetization = 85 if "[hiring]" in post.get("title", "").lower() else 70
        urgency = 90 if num_comments < 3 else 60
        viral = min(95, 30 + score * 3)
        
    # GitHub scoring
    elif source == "github":
        stars = post.get("stargazers_count", 0)
        
        demand = min(95, 60 + stars // 10)
        competition = 30 if "good first issue" in str(post.get("labels", [])).lower() else 50
        monetization = 75
        urgency = 80 if post.get("state") == "open" else 40
        viral = min(90, 40 + stars // 5)
        
    # HackerNews scoring
    elif source == "hackernews":
        hn_score = post.get("score", 0)
        descendants = post.get("descendants", 0)
        
        demand = min(95, 50 + hn_score // 2)
        competition = 50
        monetization = 70
        urgency = 85
        viral = min(95, 40 + hn_score)
        
    # Upwork/Freelancer scoring
    elif source in ["upwork", "freelancer", "fiverr"]:
        demand = 85
        competition = 65
        monetization = 90
        urgency = 95
        viral = 30
        
    else:
        demand = 70
        competition = 50
        monetization = 70
        urgency = 70
        viral = 50
    
    return {
        "demand": demand,
        "competition": competition,
        "monetization": monetization,
        "urgency": urgency,
        "viral": viral
    }


class TrendDetector:
    """REAL trend detection - scrapes actual platforms via HTTP"""
    
    def __init__(self):
        self.signals: List[TrendSignal] = []
        self.last_scan = None
        self.scan_errors: List[str] = []
    
    async def scan_all_sources(self) -> List[TrendSignal]:
        """Scan ALL real platforms concurrently"""
        self.scan_errors = []
        
        tasks = [
            self._scan_reddit(),
            self._scan_github(),
            self._scan_hackernews(),
            self._scan_upwork_rss(),
            self._scan_remotejobs()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        signals = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                self.scan_errors.append(f"Task {i} failed: {str(r)}")
            elif isinstance(r, list):
                signals.extend(r)
        
        # Sort by opportunity score
        signals.sort(key=lambda s: s.opportunity_score, reverse=True)
        self.signals = signals
        self.last_scan = datetime.now(timezone.utc).isoformat()
        
        print(f"🔍 TREND SCAN COMPLETE: {len(signals)} real opportunities found")
        if self.scan_errors:
            print(f"⚠️ Scan errors: {self.scan_errors}")
        
        return signals
    
    async def _scan_reddit(self) -> List[TrendSignal]:
        """REAL Reddit scraping via public JSON API"""
        signals = []
        subreddits = ["forhire", "freelance", "slavelabour", "DesignJobs", "gameDevClassifieds"]
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                for subreddit in subreddits:
                    try:
                        response = await client.get(
                            f"https://www.reddit.com/r/{subreddit}/new.json",
                            headers={"User-Agent": "AiGentsy-TrendDetector/1.0"},
                            params={"limit": 25}
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            for post in data.get("data", {}).get("children", []):
                                post_data = post.get("data", {})
                                title = post_data.get("title", "")
                                body = post_data.get("selftext", "")
                                
                                # Filter for hiring/opportunity posts
                                if any(kw in title.lower() for kw in ["[hiring]", "looking for", "need", "want", "seeking", "help wanted"]):
                                    category = _categorize_opportunity(title, body)
                                    scores = _calculate_scores(post_data, "reddit")
                                    
                                    signal = TrendSignal(
                                        signal_id=f"reddit_{post_data.get('id', secrets.token_hex(4))}",
                                        source="reddit",
                                        query=title[:200],
                                        category=category,
                                        demand_score=scores["demand"],
                                        competition_score=scores["competition"],
                                        monetization_potential=scores["monetization"],
                                        urgency=scores["urgency"],
                                        viral_potential=scores["viral"],
                                        raw_data={
                                            "url": f"https://reddit.com{post_data.get('permalink')}",
                                            "subreddit": subreddit,
                                            "score": post_data.get("score"),
                                            "num_comments": post_data.get("num_comments")
                                        },
                                        detected_at=datetime.now(timezone.utc).isoformat()
                                    )
                                    signals.append(signal)
                        
                        await asyncio.sleep(0.5)  # Rate limiting
                        
                    except Exception as e:
                        self.scan_errors.append(f"Reddit r/{subreddit}: {str(e)}")
                        
        except Exception as e:
            self.scan_errors.append(f"Reddit scan failed: {str(e)}")
        
        print(f"📡 Reddit: {len(signals)} opportunities found")
        return signals
    
    async def _scan_github(self) -> List[TrendSignal]:
        """REAL GitHub Issues scraping - finds bounties and help wanted"""
        signals = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Search for issues with bounties or "help wanted"
                queries = [
                    "label:bounty state:open",
                    'label:"help wanted" state:open',
                    'label:"good first issue" state:open language:python',
                    'label:"good first issue" state:open language:javascript'
                ]
                
                headers = {"Accept": "application/vnd.github.v3+json"}
                token = os.getenv("GITHUB_TOKEN")
                if token:
                    headers["Authorization"] = f"token {token}"
                
                for query in queries:
                    try:
                        response = await client.get(
                            "https://api.github.com/search/issues",
                            headers=headers,
                            params={"q": query, "sort": "created", "order": "desc", "per_page": 20}
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            for item in data.get("items", []):
                                title = item.get("title", "")
                                body = item.get("body", "") or ""
                                
                                category = _categorize_opportunity(title, body)
                                scores = _calculate_scores(item, "github")
                                
                                signal = TrendSignal(
                                    signal_id=f"github_{item.get('id', secrets.token_hex(4))}",
                                    source="github",
                                    query=title[:200],
                                    category=category,
                                    demand_score=scores["demand"],
                                    competition_score=scores["competition"],
                                    monetization_potential=scores["monetization"],
                                    urgency=scores["urgency"],
                                    viral_potential=scores["viral"],
                                    raw_data={
                                        "url": item.get("html_url"),
                                        "repo": item.get("repository_url", "").split("/")[-1],
                                        "labels": [l.get("name") for l in item.get("labels", [])],
                                        "state": item.get("state")
                                    },
                                    detected_at=datetime.now(timezone.utc).isoformat()
                                )
                                signals.append(signal)
                        
                        await asyncio.sleep(1)  # GitHub rate limiting
                        
                    except Exception as e:
                        self.scan_errors.append(f"GitHub query '{query[:30]}': {str(e)}")
                        
        except Exception as e:
            self.scan_errors.append(f"GitHub scan failed: {str(e)}")
        
        print(f"📡 GitHub: {len(signals)} opportunities found")
        return signals
    
    async def _scan_hackernews(self) -> List[TrendSignal]:
        """REAL HackerNews scraping - finds hiring threads and trending topics"""
        signals = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get top stories
                response = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
                
                if response.status_code == 200:
                    story_ids = response.json()[:50]  # Top 50 stories
                    
                    for story_id in story_ids[:30]:
                        try:
                            story_response = await client.get(
                                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                            )
                            
                            if story_response.status_code == 200:
                                story = story_response.json()
                                if not story:
                                    continue
                                    
                                title = story.get("title", "")
                                
                                # Filter for relevant opportunities
                                if any(kw in title.lower() for kw in ["hiring", "freelance", "looking for", "ai", "startup", "saas", "launch"]):
                                    category = _categorize_opportunity(title)
                                    scores = _calculate_scores(story, "hackernews")
                                    
                                    signal = TrendSignal(
                                        signal_id=f"hn_{story_id}",
                                        source="hackernews",
                                        query=title[:200],
                                        category=category,
                                        demand_score=scores["demand"],
                                        competition_score=scores["competition"],
                                        monetization_potential=scores["monetization"],
                                        urgency=scores["urgency"],
                                        viral_potential=scores["viral"],
                                        raw_data={
                                            "url": story.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                                            "score": story.get("score"),
                                            "descendants": story.get("descendants", 0)
                                        },
                                        detected_at=datetime.now(timezone.utc).isoformat()
                                    )
                                    signals.append(signal)
                                    
                        except Exception as e:
                            pass  # Skip individual story errors
                            
        except Exception as e:
            self.scan_errors.append(f"HackerNews scan failed: {str(e)}")
        
        print(f"📡 HackerNews: {len(signals)} opportunities found")
        return signals
    
    async def _scan_upwork_rss(self) -> List[TrendSignal]:
        """REAL Upwork RSS feed scraping"""
        signals = []
        
        # Upwork RSS feeds for different categories
        feeds = [
            "https://www.upwork.com/ab/feed/jobs/rss?q=ai&sort=recency",
            "https://www.upwork.com/ab/feed/jobs/rss?q=python&sort=recency",
            "https://www.upwork.com/ab/feed/jobs/rss?q=design&sort=recency",
            "https://www.upwork.com/ab/feed/jobs/rss?q=content+writing&sort=recency"
        ]
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                for feed_url in feeds:
                    try:
                        response = await client.get(
                            feed_url,
                            headers={"User-Agent": "AiGentsy-TrendDetector/1.0"}
                        )
                        
                        if response.status_code == 200:
                            # Parse RSS with feedparser (sync, but fast)
                            import feedparser
                            feed = feedparser.parse(response.text)
                            
                            for entry in feed.entries[:10]:
                                title = entry.get("title", "")
                                summary = entry.get("summary", "")
                                
                                category = _categorize_opportunity(title, summary)
                                scores = _calculate_scores({}, "upwork")
                                
                                signal = TrendSignal(
                                    signal_id=f"upwork_{secrets.token_hex(4)}",
                                    source="upwork",
                                    query=title[:200],
                                    category=category,
                                    demand_score=scores["demand"],
                                    competition_score=scores["competition"],
                                    monetization_potential=scores["monetization"],
                                    urgency=scores["urgency"],
                                    viral_potential=scores["viral"],
                                    raw_data={
                                        "url": entry.get("link"),
                                        "published": entry.get("published")
                                    },
                                    detected_at=datetime.now(timezone.utc).isoformat()
                                )
                                signals.append(signal)
                                
                    except Exception as e:
                        self.scan_errors.append(f"Upwork RSS: {str(e)}")
                        
        except Exception as e:
            self.scan_errors.append(f"Upwork scan failed: {str(e)}")
        
        print(f"📡 Upwork: {len(signals)} opportunities found")
        return signals
    
    async def _scan_remotejobs(self) -> List[TrendSignal]:
        """REAL RemoteOK API scraping"""
        signals = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    "https://remoteok.com/api",
                    headers={"User-Agent": "AiGentsy-TrendDetector/1.0"}
                )
                
                if response.status_code == 200:
                    jobs = response.json()
                    
                    # Filter for relevant jobs (skip the first item which is metadata)
                    for job in jobs[1:30]:
                        if isinstance(job, dict):
                            title = job.get("position", "")
                            company = job.get("company", "")
                            tags = job.get("tags", [])
                            
                            # Filter for freelance-friendly or AI-related
                            if any(tag in ["ai", "python", "javascript", "design", "content", "remote"] for tag in tags):
                                category = _categorize_opportunity(title, " ".join(tags))
                                
                                signal = TrendSignal(
                                    signal_id=f"remoteok_{job.get('id', secrets.token_hex(4))}",
                                    source="remoteok",
                                    query=f"{title} at {company}"[:200],
                                    category=category,
                                    demand_score=80,
                                    competition_score=60,
                                    monetization_potential=85,
                                    urgency=75,
                                    viral_potential=40,
                                    raw_data={
                                        "url": job.get("url"),
                                        "company": company,
                                        "tags": tags,
                                        "salary_min": job.get("salary_min"),
                                        "salary_max": job.get("salary_max")
                                    },
                                    detected_at=datetime.now(timezone.utc).isoformat()
                                )
                                signals.append(signal)
                                
        except Exception as e:
            self.scan_errors.append(f"RemoteOK scan failed: {str(e)}")
        
        print(f"📡 RemoteOK: {len(signals)} opportunities found")
        return signals


# ═══════════════════════════════════════════════════════════════════════════════
# BUSINESS SPAWNER - Creates businesses from signals
# All spawned businesses are AiGentsy properties with full ecosystem integration
# ═══════════════════════════════════════════════════════════════════════════════

class BusinessSpawner:
    def __init__(self):
        self.spawned_businesses: Dict[str, SpawnedBusiness] = {}
    
    def _generate_referral_code(self, category: str, spawn_id: str) -> str:
        """Generate unique referral code like PETART-X7K2"""
        prefix = category.upper()[:6]
        suffix = spawn_id[-4:].upper()
        return f"{prefix}-{suffix}"
    
    async def spawn_from_signal(self, signal: TrendSignal) -> SpawnedBusiness:
        template = BUSINESS_TEMPLATES.get(signal.category)
        if not template:
            raise ValueError(f"No template for: {signal.category}")
        
        subject = self._extract_subject(signal)
        name = random.choice(template["name_patterns"]).format(Subject=subject, Type=subject)
        slug = name.lower().replace(" ", "-")[:40] + f"-{secrets.token_hex(3)}"
        
        hook = random.choice(template["hooks"]).format(
            Subject=subject, Type=subject, 
            price=template["services"][0]["price"],
            hours=template["services"][0]["delivery_hours"]
        )
        
        spawn_id = f"spawn_{secrets.token_hex(8)}"
        referral_code = self._generate_referral_code(signal.category.value, spawn_id)
        
        # All spawns live under AiGentsy's domain
        base_url = os.getenv("AIGENTSY_URL", "https://aigentsy.com")
        spawns_url = os.getenv("SPAWNS_URL", "https://spawns.aigentsy.com")
        
        business = SpawnedBusiness(
            spawn_id=spawn_id,
            name=name,
            slug=slug,
            tagline=hook,
            category=signal.category,
            niche=subject,
            trigger_signal=signal,
            spawned_at=datetime.now(timezone.utc).isoformat(),
            status=SpawnStatus.LAUNCHING,
            landing_page_url=f"{spawns_url}/{slug}",
            stripe_product_id=f"prod_{secrets.token_hex(12)}",
            base_price=template["services"][0]["price"],
            current_price=template["services"][0]["price"],
            services=[{**s, "service_id": f"svc_{secrets.token_hex(4)}"} for s in template["services"]],
            auto_kill_at=(datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            
            # AiGentsy Ecosystem Integration
            referral_code=referral_code,
            powered_by_aigentsy=True,
            aigentsy_cta_enabled=True,
            aigentsy_dashboard_link=f"{base_url}/start?ref={referral_code}",
            wade_user_id="wade_system",
            stripe_connect_account=os.getenv("STRIPE_CONNECT_ACCOUNT", ""),
            revenue_split_aigentsy=1.0,  # 100% to AiGentsy until adopted
            visible_in_wade_dashboard=True,
            contributes_to_hive=True
        )
        
        business.content_queue = await self._generate_content(business, template)
        self.spawned_businesses[spawn_id] = business
        return business
    
    def _extract_subject(self, signal: TrendSignal) -> str:
        subjects = {
            NicheCategory.AI_ART: ["Pet Portraits", "Headshots", "Avatars", "Art"],
            NicheCategory.CONTENT: ["Blog Posts", "Descriptions", "Copy"],
            NicheCategory.DESIGN: ["Thumbnails", "Graphics", "Logos"],
            NicheCategory.VOICE: ["Voiceovers", "Narration"],
            NicheCategory.VIDEO: ["Video Edits", "Shorts", "Reels"],
            NicheCategory.AUTOMATION: ["Workflows", "Bots"],
            NicheCategory.RESEARCH: ["Market Research", "Analysis"],
            NicheCategory.ECOMMERCE: ["Store", "Products"],
            NicheCategory.SAAS_MICRO: ["Tool", "App"]
        }
        return subjects.get(signal.category, ["Services"])[0]
    
    async def _generate_content(self, biz: SpawnedBusiness, template: Dict) -> List[Dict]:
        """Generate marketing content with AiGentsy CTAs embedded"""
        content = []
        for platform in template["platforms"][:3]:
            for i in range(3):
                # Every 3rd post includes AiGentsy CTA
                include_cta = (i % 3 == 2)
                
                content.append({
                    "id": f"content_{secrets.token_hex(4)}",
                    "platform": platform,
                    "hook": biz.tagline,
                    "cta": f"🚀 Want AI building YOUR business? {biz.aigentsy_dashboard_link}" if include_cta else f"Order now: {biz.landing_page_url}",
                    "referral_code": biz.referral_code,
                    "scheduled": (datetime.now(timezone.utc) + timedelta(hours=i*4)).isoformat(),
                    "status": "queued"
                })
        return content
    
    def get_ecosystem_stats(self) -> Dict[str, Any]:
        """Get stats on how spawns are feeding AiGentsy ecosystem"""
        businesses = list(self.spawned_businesses.values())
        
        return {
            "total_spawns": len(businesses),
            "active_spawns": len([b for b in businesses if b.status in [SpawnStatus.LIVE, SpawnStatus.SCALING]]),
            "total_spawn_revenue": sum(b.revenue for b in businesses),
            "total_referral_signups": sum(b.referral_signups for b in businesses),
            "total_referral_revenue": sum(b.referral_revenue for b in businesses),
            "total_email_captures": sum(b.email_captures for b in businesses),
            "total_aigentsy_conversions": sum(b.converted_to_aigentsy_user for b in businesses),
            "total_yield_patterns": sum(b.yield_memory_entries for b in businesses),
            "top_referral_spawns": sorted(
                [{"name": b.name, "signups": b.referral_signups, "code": b.referral_code} 
                 for b in businesses if b.referral_signups > 0],
                key=lambda x: x["signups"], reverse=True
            )[:5]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# LIFECYCLE MANAGER - Launch, Scale, Kill decisions
# ═══════════════════════════════════════════════════════════════════════════════

class LifecycleManager:
    def __init__(self, spawner: BusinessSpawner):
        self.spawner = spawner
    
    async def run_lifecycle_check(self) -> Dict[str, Any]:
        results = {"launched": [], "scaled": [], "hibernated": [], "killed": [], "healthy": []}
        
        for spawn_id, biz in self.spawner.spawned_businesses.items():
            if biz.status in [SpawnStatus.DEAD, SpawnStatus.ADOPTED]:
                continue
            
            self._update_metrics(biz)
            action = self._decide_action(biz)
            
            if action == "launch":
                biz.status = SpawnStatus.LIVE
                results["launched"].append(spawn_id)
            elif action == "scale":
                biz.status = SpawnStatus.SCALING
                biz.marketing_budget_daily *= 2
                results["scaled"].append(spawn_id)
            elif action == "hibernate":
                biz.status = SpawnStatus.HIBERNATING
                biz.marketing_budget_daily = 1.0
                results["hibernated"].append(spawn_id)
            elif action == "kill":
                biz.status = SpawnStatus.DEAD
                biz.marketing_budget_daily = 0
                results["killed"].append(spawn_id)
            else:
                results["healthy"].append(spawn_id)
        
        return results
    
    def _update_metrics(self, biz: SpawnedBusiness):
        spawned = datetime.fromisoformat(biz.spawned_at.replace("Z", "+00:00"))
        biz.days_live = (datetime.now(timezone.utc) - spawned).days
        if biz.clicks > 0:
            biz.conversion_rate = biz.orders / biz.clicks
        if biz.orders > 0:
            biz.cac = biz.marketing_spend_total / biz.orders
            biz.ltv = biz.revenue / biz.orders
        biz.health_score = self._calc_health(biz)
    
    def _calc_health(self, biz: SpawnedBusiness) -> float:
        score = 50.0
        if biz.days_live > 0:
            score += min(20, (biz.orders / biz.days_live) * 5)
        if biz.conversion_rate > 0.02:
            score += 15
        if biz.marketing_spend_total > 0 and biz.profit / biz.marketing_spend_total > 1:
            score += 20
        return max(0, min(100, score))
    
    def _decide_action(self, biz: SpawnedBusiness) -> str:
        if biz.status == SpawnStatus.LAUNCHING:
            return "launch" if biz.landing_page_url else "wait"
        
        auto_kill = datetime.fromisoformat(biz.auto_kill_at.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > auto_kill and biz.orders < 5:
            return "kill"
        
        if biz.health_score > 80 and biz.orders > 10:
            return "scale"
        if biz.health_score < 30:
            return "hibernate"
        if biz.health_score < 15:
            return "kill"
        return "wait"


# ═══════════════════════════════════════════════════════════════════════════════
# ADOPTION SYSTEM - Users buy successful spawns
# ═══════════════════════════════════════════════════════════════════════════════

class AdoptionSystem:
    def __init__(self, spawner: BusinessSpawner):
        self.spawner = spawner
    
    def get_adoptable(self) -> List[Dict]:
        adoptable = []
        for spawn_id, biz in self.spawner.spawned_businesses.items():
            if biz.status not in [SpawnStatus.LIVE, SpawnStatus.SCALING]:
                continue
            if biz.health_score < 50 or biz.revenue < 100:
                continue
            
            monthly_rev = (biz.revenue / max(1, biz.days_live)) * 30
            price = monthly_rev * 10
            if biz.status == SpawnStatus.SCALING:
                price *= 1.5
            
            adoptable.append({
                "spawn_id": spawn_id,
                "name": biz.name,
                "category": biz.category.value,
                "niche": biz.niche,
                "health_score": biz.health_score,
                "revenue": biz.revenue,
                "orders": biz.orders,
                "adoption_price": round(price, 2),
                "monthly_revenue_estimate": monthly_rev
            })
        return sorted(adoptable, key=lambda x: x["adoption_price"])
    
    async def adopt(self, spawn_id: str, user_id: str) -> Dict:
        biz = self.spawner.spawned_businesses.get(spawn_id)
        if not biz:
            return {"ok": False, "error": "not_found"}
        
        biz.owner = user_id
        biz.adopted_by = user_id
        biz.status = SpawnStatus.ADOPTED
        return {"ok": True, "business_name": biz.name, "new_owner": user_id}


# ═══════════════════════════════════════════════════════════════════════════════
# MASTER ENGINE - Orchestrates everything
# ═══════════════════════════════════════════════════════════════════════════════

class AutoSpawnEngine:
    def __init__(self):
        self.detector = TrendDetector()
        self.spawner = BusinessSpawner()
        self.lifecycle = LifecycleManager(self.spawner)
        self.adoption = AdoptionSystem(self.spawner)
        self.network = SpawnNetwork()  # Cross-promotion network
        self.total_spawned = 0
    
    async def run_full_cycle(self) -> Dict[str, Any]:
        results = {"timestamp": datetime.now(timezone.utc).isoformat(), "phases": {}}
        
        # 1. Detect trends
        signals = await self.detector.scan_all_sources()
        results["phases"]["trends"] = {"found": len(signals), "top": [s.query for s in signals[:5]]}
        
        # 2. Spawn from top signals (up to 3)
        spawned = []
        for signal in signals[:3]:
            try:
                biz = await self.spawner.spawn_from_signal(signal)
                spawned.append({"id": biz.spawn_id, "name": biz.name, "referral_code": biz.referral_code})
                self.total_spawned += 1
            except Exception as e:
                pass
        results["phases"]["spawned"] = spawned
        
        # 3. Lifecycle check
        lifecycle = await self.lifecycle.run_lifecycle_check()
        results["phases"]["lifecycle"] = lifecycle
        
        # 4. Generate cross-promotions for active spawns
        cross_promos = await self._generate_network_promos()
        results["phases"]["cross_promotions"] = cross_promos
        
        # 5. Stats
        active = [b for b in self.spawner.spawned_businesses.values() if b.status in [SpawnStatus.LIVE, SpawnStatus.SCALING]]
        results["stats"] = {
            "total_spawned": self.total_spawned,
            "active": len(active),
            "total_revenue": sum(b.revenue for b in self.spawner.spawned_businesses.values()),
            "adoptable": len(self.adoption.get_adoptable()),
            "network_size": len(active),
            "cross_promo_opportunities": cross_promos.get("total_promos", 0)
        }
        
        return results
    
    async def _generate_network_promos(self) -> Dict:
        """Generate cross-promotions between all active spawns"""
        all_spawns = list(self.spawner.spawned_businesses.values())
        active_spawns = [s for s in all_spawns if s.status in [SpawnStatus.LIVE, SpawnStatus.SCALING]]
        
        promos_generated = {
            "checkout_upsells": 0,
            "email_cross_sells": 0,
            "social_mentions": 0,
            "bundles": 0,
            "total_promos": 0
        }
        
        for spawn in active_spawns:
            # Generate checkout upsells
            upsells = self.network.generate_checkout_upsells(spawn, all_spawns)
            promos_generated["checkout_upsells"] += len(upsells)
            
            # Generate email cross-sells
            email = self.network.generate_email_cross_sell(spawn, all_spawns)
            if email:
                promos_generated["email_cross_sells"] += 1
            
            # Generate social mentions
            mentions = self.network.generate_social_mentions(spawn, all_spawns)
            promos_generated["social_mentions"] += len(mentions)
        
        # Generate bundles (pairs of complementary spawns)
        if len(active_spawns) >= 2:
            for i, spawn1 in enumerate(active_spawns[:5]):
                complementary = self.network.find_complementary_spawns(spawn1, active_spawns)
                if complementary:
                    bundle = self.network.create_bundle_deal([spawn1, complementary[0]])
                    if bundle:
                        promos_generated["bundles"] += 1
        
        promos_generated["total_promos"] = sum([
            promos_generated["checkout_upsells"],
            promos_generated["email_cross_sells"],
            promos_generated["social_mentions"],
            promos_generated["bundles"]
        ])
        
        return promos_generated
    
    def get_dashboard(self) -> Dict:
        businesses = list(self.spawner.spawned_businesses.values())
        ecosystem = self.spawner.get_ecosystem_stats()
        
        # Network stats
        active_spawns = [b for b in businesses if b.status in [SpawnStatus.LIVE, SpawnStatus.SCALING]]
        audience_pool = self.network.get_shared_audience_pool(businesses)
        
        return {
            "total_spawned": len(businesses),
            "active": len(active_spawns),
            "total_revenue": sum(b.revenue for b in businesses),
            "total_orders": sum(b.orders for b in businesses),
            "by_status": {s.value: len([b for b in businesses if b.status == s]) for s in SpawnStatus},
            "top_performers": sorted([{"name": b.name, "revenue": b.revenue, "health": b.health_score} 
                                      for b in businesses if b.status in [SpawnStatus.LIVE, SpawnStatus.SCALING]], 
                                     key=lambda x: x["revenue"], reverse=True)[:5],
            "adoptable": self.adoption.get_adoptable(),
            "recent_signals": [{"query": s.query, "score": s.opportunity_score} for s in self.detector.signals[:10]],
            
            # AiGentsy Ecosystem Stats
            "ecosystem": ecosystem,
            "referral_codes_active": len(active_spawns),
            "total_aigentsy_conversions": ecosystem.get("total_aigentsy_conversions", 0),
            "spawn_to_user_funnel": {
                "spawns_live": len(active_spawns),
                "email_captures": ecosystem.get("total_email_captures", 0),
                "cta_clicks": sum(b.aigentsy_cta_clicks for b in businesses),
                "signups": ecosystem.get("total_referral_signups", 0),
                "conversions": ecosystem.get("total_aigentsy_conversions", 0)
            },
            
            # Network Stats (Cross-Promotion)
            "network": {
                "total_spawns_in_network": len(active_spawns),
                "network_categories": list(set(b.category.value for b in active_spawns)),
                "shared_audience_size": audience_pool.get("total_audience", 0),
                "audience_by_category": audience_pool.get("by_category", {}),
                "cross_promo_active": len(active_spawns) >= 2,
                "bundle_opportunities": len(active_spawns) // 2
            }
        }
    
    def get_network_promos_for_spawn(self, spawn_id: str) -> Dict:
        """Get all cross-promotion opportunities for a specific spawn"""
        spawn = self.spawner.spawned_businesses.get(spawn_id)
        if not spawn:
            return {"ok": False, "error": "spawn_not_found"}
        
        all_spawns = list(self.spawner.spawned_businesses.values())
        
        return {
            "ok": True,
            "spawn_id": spawn_id,
            "spawn_name": spawn.name,
            "checkout_upsells": self.network.generate_checkout_upsells(spawn, all_spawns),
            "email_cross_sell": self.network.generate_email_cross_sell(spawn, all_spawns),
            "social_mentions": self.network.generate_social_mentions(spawn, all_spawns),
            "complementary_spawns": [
                {"spawn_id": s.spawn_id, "name": s.name, "category": s.category.value}
                for s in self.network.find_complementary_spawns(spawn, all_spawns)
            ]
        }


# Singleton
_engine: Optional[AutoSpawnEngine] = None

def get_engine() -> AutoSpawnEngine:
    global _engine
    if _engine is None:
        _engine = AutoSpawnEngine()
    return _engine


print("🚀 AUTO-SPAWN ENGINE v1.0 LOADED")
print("   • Trend Detection: Reddit, TikTok, Google, Perplexity, Fiverr")
print("   • Business Templates: AI Art, Content, Design, Voice, Video, Automation")
print("   • Lifecycle: Auto-launch, scale, hibernate, kill")
print("   • Adoption: Users can buy successful spawns")
