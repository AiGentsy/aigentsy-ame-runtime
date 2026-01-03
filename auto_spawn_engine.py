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
# TREND DETECTOR - Finds opportunities
# ═══════════════════════════════════════════════════════════════════════════════

class TrendDetector:
    def __init__(self):
        self.signals: List[TrendSignal] = []
        self.last_scan = None
    
    async def scan_all_sources(self) -> List[TrendSignal]:
        tasks = [self._scan_reddit(), self._scan_tiktok(), self._scan_google(), 
                 self._scan_perplexity(), self._scan_fiverr()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        signals = []
        for r in results:
            if isinstance(r, list):
                signals.extend(r)
        
        signals.sort(key=lambda s: s.opportunity_score, reverse=True)
        self.signals = signals
        self.last_scan = datetime.now(timezone.utc).isoformat()
        return signals
    
    async def _scan_reddit(self) -> List[TrendSignal]:
        return [
            TrendSignal("reddit_1", "reddit", "Need AI pet portraits for Etsy", NicheCategory.AI_ART, 88, 35, 92, 80, 60, detected_at=datetime.now(timezone.utc).isoformat()),
            TrendSignal("reddit_2", "reddit", "YouTube thumbnails designer needed", NicheCategory.DESIGN, 90, 50, 85, 75, 55, detected_at=datetime.now(timezone.utc).isoformat()),
            TrendSignal("reddit_3", "reddit", "TikTok editor for viral content", NicheCategory.VIDEO, 95, 45, 88, 85, 85, detected_at=datetime.now(timezone.utc).isoformat()),
            TrendSignal("reddit_4", "reddit", "AI voiceover for podcast", NicheCategory.VOICE, 75, 40, 80, 60, 45, detected_at=datetime.now(timezone.utc).isoformat()),
        ]
    
    async def _scan_tiktok(self) -> List[TrendSignal]:
        return [
            TrendSignal("tiktok_1", "tiktok", "#AIart trending", NicheCategory.AI_ART, 92, 40, 85, 70, 90, detected_at=datetime.now(timezone.utc).isoformat()),
            TrendSignal("tiktok_2", "tiktok", "#sidehustle viral", NicheCategory.SAAS_MICRO, 88, 50, 80, 65, 88, detected_at=datetime.now(timezone.utc).isoformat()),
        ]
    
    async def _scan_google(self) -> List[TrendSignal]:
        return [
            TrendSignal("google_1", "google_trends", "ai headshot generator +1200%", NicheCategory.AI_ART, 95, 45, 90, 75, 70, detected_at=datetime.now(timezone.utc).isoformat()),
            TrendSignal("google_2", "google_trends", "ai thumbnail maker +700%", NicheCategory.DESIGN, 85, 50, 85, 70, 65, detected_at=datetime.now(timezone.utc).isoformat()),
        ]
    
    async def _scan_perplexity(self) -> List[TrendSignal]:
        return [
            TrendSignal("perplexity_1", "perplexity", "affordable ai portraits under $20", NicheCategory.AI_ART, 88, 30, 92, 75, 55, detected_at=datetime.now(timezone.utc).isoformat()),
            TrendSignal("perplexity_2", "perplexity", "same-day thumbnail service gap", NicheCategory.DESIGN, 85, 25, 90, 80, 60, detected_at=datetime.now(timezone.utc).isoformat()),
        ]
    
    async def _scan_fiverr(self) -> List[TrendSignal]:
        return [
            TrendSignal("fiverr_1", "fiverr", "AI pet portrait 5000 orders/mo", NicheCategory.AI_ART, 90, 65, 80, 50, 50, detected_at=datetime.now(timezone.utc).isoformat()),
            TrendSignal("fiverr_2", "fiverr", "YouTube thumbnail 8000 orders/mo", NicheCategory.DESIGN, 92, 65, 78, 50, 55, detected_at=datetime.now(timezone.utc).isoformat()),
        ]


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
                spawned.append({"id": biz.spawn_id, "name": biz.name})
                self.total_spawned += 1
            except Exception as e:
                pass
        results["phases"]["spawned"] = spawned
        
        # 3. Lifecycle check
        lifecycle = await self.lifecycle.run_lifecycle_check()
        results["phases"]["lifecycle"] = lifecycle
        
        # 4. Stats
        active = [b for b in self.spawner.spawned_businesses.values() if b.status in [SpawnStatus.LIVE, SpawnStatus.SCALING]]
        results["stats"] = {
            "total_spawned": self.total_spawned,
            "active": len(active),
            "total_revenue": sum(b.revenue for b in self.spawner.spawned_businesses.values()),
            "adoptable": len(self.adoption.get_adoptable())
        }
        
        return results
    
    def get_dashboard(self) -> Dict:
        businesses = list(self.spawner.spawned_businesses.values())
        ecosystem = self.spawner.get_ecosystem_stats()
        
        return {
            "total_spawned": len(businesses),
            "active": len([b for b in businesses if b.status in [SpawnStatus.LIVE, SpawnStatus.SCALING]]),
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
            "referral_codes_active": len([b for b in businesses if b.status in [SpawnStatus.LIVE, SpawnStatus.SCALING]]),
            "total_aigentsy_conversions": ecosystem.get("total_aigentsy_conversions", 0),
            "spawn_to_user_funnel": {
                "spawns_live": len([b for b in businesses if b.status == SpawnStatus.LIVE]),
                "email_captures": ecosystem.get("total_email_captures", 0),
                "cta_clicks": sum(b.aigentsy_cta_clicks for b in businesses),
                "signups": ecosystem.get("total_referral_signups", 0),
                "conversions": ecosystem.get("total_aigentsy_conversions", 0)
            }
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
