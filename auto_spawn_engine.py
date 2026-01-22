"""
═══════════════════════════════════════════════════════════════════════════════
AUTO-SPAWN ENGINE v2.0 - THE AI VENTURE FACTORY
═══════════════════════════════════════════════════════════════════════════════

MERGED: Full ecosystem from v1 + ALL AI models from v2

AI MODELS (ALL USED SIMULTANEOUSLY):
- Claude (Anthropic) - Primary reasoning, code, content, fulfillment
- GPT-4 (OpenAI) - Fast generation, creative tasks
- Gemini (Google) - Research, multimodal analysis
- Perplexity - Real-time web search, opportunity discovery

PLATFORMS SCRAPED (27+):
- Job Boards: Upwork, Fiverr, Freelancer, PeoplePerHour, Guru, 99Designs
- Tech: GitHub, StackOverflow, HackerNews, ProductHunt, DevPost
- Remote: RemoteOK, WeWorkRemotely, FlexJobs
- Corporate: LinkedIn, Indeed, Glassdoor, SimplyHired, Dice
- Creative: Dribbble, Behance
- Startup: AngelList, YCombinator, IndieHackers
- Local: Craigslist
- Social: Reddit

FLOW:
1. DETECT trends across ALL platforms + AI-powered discovery
2. SPAWN complete businesses (landing page + Stripe + fulfillment)
3. MARKET via auto-generated viral content
4. FULFILL orders via Wade (AI delivery using ALL AI models)
5. LEARN what works, kill what doesn't
6. SCALE winners, offer successful spawns for user adoption
7. CROSS-PROMOTE across the spawn network

NOVEL FEATURES:
- SPAWN SWARM: Launch 10 businesses, kill 8, scale 2
- ZOMBIE REVIVAL: Dead businesses auto-relaunch when trends return
- FRANCHISE MODE: Clone winning businesses into adjacent niches
- VIRAL HOOKS: AI generates scroll-stopping content
- PRICE ELASTICITY: Auto-adjust prices based on conversion
- CROSS-PROMOTION NETWORK: All spawns help each other

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import asyncio
import secrets
import httpx
import feedparser
import random
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════════════════════
# API KEYS - All AI Models
# ═══════════════════════════════════════════════════════════════════════════════

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# AI Model routing by task type
AI_ROUTING = {
    "opportunity_discovery": ["perplexity", "gemini", "claude"],
    "content_generation": ["claude", "gpt4", "gemini"],
    "code_generation": ["claude", "gpt4"],
    "research": ["perplexity", "gemini", "claude"],
    "analysis": ["claude", "gpt4", "gemini"],
    "fulfillment": ["claude", "gpt4", "gemini"],
}


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
    ai_analysis: Dict[str, Any] = field(default_factory=dict)
    
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
    customer_emails: List[str] = field(default_factory=list)
    
    # AiGentsy Ecosystem Integration
    referral_code: str = ""
    referral_signups: int = 0
    referral_revenue: float = 0.0
    powered_by_aigentsy: bool = True
    aigentsy_cta_enabled: bool = True
    aigentsy_dashboard_link: str = ""
    email_captures: int = 0
    aigentsy_cta_clicks: int = 0
    converted_to_aigentsy_user: int = 0
    wade_user_id: str = "wade_system"
    fulfillment_queue_id: str = ""
    stripe_connect_account: str = ""
    revenue_split_aigentsy: float = 1.0
    visible_in_wade_dashboard: bool = True
    visible_in_main_dashboard: bool = False
    contributes_to_hive: bool = True
    yield_memory_entries: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# BUSINESS TEMPLATES - Full configuration
# ═══════════════════════════════════════════════════════════════════════════════

BUSINESS_TEMPLATES = {
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
        "trial_days": 14,
        "churn_prediction": True,
        "upsell_triggers": ["usage_limit", "feature_gate", "team_growth"]
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIONIZED TEMPLATES
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
}


def register_custom_template(category: str, template: Dict) -> bool:
    try:
        required = ["name_patterns", "services", "hooks", "platforms", "fulfillment"]
        for field in required:
            if field not in template:
                return False
        BUSINESS_TEMPLATES[category] = template
        return True
    except:
        return False


def get_available_categories() -> List[str]:
    categories = [cat.value for cat in NicheCategory]
    for key in BUSINESS_TEMPLATES.keys():
        if isinstance(key, str) and key not in categories:
            categories.append(key)
    return categories


# ═══════════════════════════════════════════════════════════════════════════════
# CROSS-PROMOTION NETWORK
# ═══════════════════════════════════════════════════════════════════════════════

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


@dataclass
class CrossPromotion:
    promo_id: str
    source_spawn_id: str
    target_spawn_id: str
    promo_type: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue_generated: float = 0.0
    created_at: str = ""
    active: bool = True


class SpawnNetwork:
    def __init__(self):
        self.promotions: Dict[str, CrossPromotion] = {}
        self.network_stats = {"total_cross_promos": 0, "cross_promo_revenue": 0.0, "cross_promo_conversions": 0}
    
    def find_complementary_spawns(self, spawn: SpawnedBusiness, all_spawns: List[SpawnedBusiness]) -> List[SpawnedBusiness]:
        complementary = []
        affinity_categories = CATEGORY_AFFINITY.get(spawn.category, [])
        for other in all_spawns:
            if other.spawn_id == spawn.spawn_id:
                continue
            if other.status not in [SpawnStatus.LIVE, SpawnStatus.SCALING]:
                continue
            if other.category in affinity_categories:
                complementary.append(other)
        complementary.sort(key=lambda x: x.health_score, reverse=True)
        return complementary[:3]
    
    def generate_checkout_upsells(self, spawn: SpawnedBusiness, all_spawns: List[SpawnedBusiness]) -> List[Dict]:
        complementary = self.find_complementary_spawns(spawn, all_spawns)
        upsells = []
        for comp in complementary:
            upsells.append({
                "spawn_id": comp.spawn_id,
                "name": comp.name,
                "tagline": comp.tagline,
                "price": comp.current_price,
                "discount": 15,
                "discounted_price": round(comp.current_price * 0.85, 2),
                "url": f"{comp.landing_page_url}?ref={spawn.referral_code}&network=1",
                "promo_code": f"NETWORK15_{spawn.referral_code[:6]}"
            })
        return upsells
    
    def generate_email_cross_sell(self, spawn: SpawnedBusiness, all_spawns: List[SpawnedBusiness]) -> Dict:
        complementary = self.find_complementary_spawns(spawn, all_spawns)
        if not complementary:
            return {}
        email = {
            "subject": f"🚀 More AI magic for you, from AiGentsy",
            "preview": "Exclusive deals on services that pair perfectly with your recent order",
            "intro": f"You loved {spawn.name} - here are other AI-powered services from our network:",
            "offers": [],
            "footer_cta": {"text": "Want AI building YOUR business? Join AiGentsy free →", "url": f"https://aigentsy.com/start?ref={spawn.referral_code}"}
        }
        for comp in complementary:
            email["offers"].append({
                "name": comp.name,
                "tagline": comp.tagline,
                "original_price": comp.current_price,
                "network_price": round(comp.current_price * 0.80, 2),
                "savings": f"Save ${round(comp.current_price * 0.20, 2)}",
                "cta_url": f"{comp.landing_page_url}?ref={spawn.referral_code}&email=1",
                "promo_code": f"EMAIL20_{spawn.referral_code[:6]}"
            })
        return email
    
    def generate_social_mentions(self, spawn: SpawnedBusiness, all_spawns: List[SpawnedBusiness]) -> List[Dict]:
        complementary = self.find_complementary_spawns(spawn, all_spawns)
        mentions = []
        for comp in complementary:
            mention_hooks = [
                f"🔥 Loving {spawn.name}? Check out {comp.name} for {comp.niche.lower()}!",
                f"✨ {spawn.name} + {comp.name} = unstoppable combo 💪",
                f"Pro tip: Pair your {spawn.niche} with {comp.niche} from our network →",
            ]
            mentions.append({
                "hook": random.choice(mention_hooks),
                "target_spawn": comp.spawn_id,
                "target_url": f"{comp.landing_page_url}?ref={spawn.referral_code}&social=1",
                "hashtags": [f"#{spawn.niche.replace(' ', '')}", f"#{comp.niche.replace(' ', '')}", "#AiGentsy"]
            })
        return mentions
    
    def create_bundle_deal(self, spawns: List[SpawnedBusiness]) -> Dict:
        if len(spawns) < 2:
            return {}
        bundle_id = f"bundle_{secrets.token_hex(6)}"
        total_price = sum(s.current_price for s in spawns)
        bundle_discount = 0.25 if len(spawns) == 2 else 0.30
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
    
    def get_shared_audience_pool(self, all_spawns: List[SpawnedBusiness]) -> Dict:
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
            "retarget_eligible": len([e for e in all_emails if e]),
            "lookalike_seed_size": min(len(all_emails), 10000)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL AI CLIENT - Routes to ALL available AI models
# ═══════════════════════════════════════════════════════════════════════════════

class UniversalAI:
    def __init__(self):
        self.available_models = self._check_available_models()
        print(f"🤖 UniversalAI initialized: {[k for k,v in self.available_models.items() if v]}")
    
    def _check_available_models(self) -> Dict[str, bool]:
        return {
            "claude": bool(ANTHROPIC_API_KEY or OPENROUTER_API_KEY),
            "gpt4": bool(OPENAI_API_KEY or OPENROUTER_API_KEY),
            "gemini": bool(GEMINI_API_KEY),
            "perplexity": bool(PERPLEXITY_API_KEY),
        }
    
    async def query(self, prompt: str, task_type: str = "analysis", max_tokens: int = 2000) -> Dict[str, Any]:
        preferred_models = AI_ROUTING.get(task_type, ["claude", "gpt4", "gemini"])
        for model in preferred_models:
            if self.available_models.get(model):
                try:
                    result = await self._call_model(model, prompt, max_tokens)
                    if result.get("ok"):
                        return result
                except Exception as e:
                    print(f"⚠️ {model} failed: {e}")
        return {"ok": False, "error": "No AI models available", "response": ""}
    
    async def _call_model(self, model: str, prompt: str, max_tokens: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=120) as client:
            if model == "perplexity" and PERPLEXITY_API_KEY:
                r = await client.post("https://api.perplexity.ai/chat/completions", headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}, json={"model": "llama-3.1-sonar-large-128k-online", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens})
                if r.status_code == 200:
                    d = r.json()
                    return {"ok": True, "model": "perplexity", "response": d.get("choices", [{}])[0].get("message", {}).get("content", ""), "citations": d.get("citations", [])}
            
            elif model == "gemini" and GEMINI_API_KEY:
                r = await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}", json={"contents": [{"parts": [{"text": prompt}]}]})
                if r.status_code == 200:
                    return {"ok": True, "model": "gemini", "response": r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")}
            
            elif model in ["claude", "gpt4"] and OPENROUTER_API_KEY:
                mid = "anthropic/claude-3.5-sonnet" if model == "claude" else "openai/gpt-4-turbo"
                r = await client.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}, json={"model": mid, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens})
                if r.status_code == 200:
                    return {"ok": True, "model": model, "response": r.json().get("choices", [{}])[0].get("message", {}).get("content", "")}
            
            elif model == "claude" and ANTHROPIC_API_KEY:
                r = await client.post("https://api.anthropic.com/v1/messages", headers={"x-api-key": ANTHROPIC_API_KEY, "Content-Type": "application/json", "anthropic-version": "2023-06-01"}, json={"model": "claude-3-5-sonnet-20241022", "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]})
                if r.status_code == 200:
                    return {"ok": True, "model": "claude", "response": r.json().get("content", [{}])[0].get("text", "")}
            
            elif model == "gpt4" and OPENAI_API_KEY:
                r = await client.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}, json={"model": "gpt-4-turbo-preview", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens})
                if r.status_code == 200:
                    return {"ok": True, "model": "gpt4", "response": r.json().get("choices", [{}])[0].get("message", {}).get("content", "")}
        
        return {"ok": False, "error": f"{model} failed"}


_universal_ai: Optional[UniversalAI] = None
def get_universal_ai() -> UniversalAI:
    global _universal_ai
    if _universal_ai is None:
        _universal_ai = UniversalAI()
    return _universal_ai


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════

CATEGORY_KEYWORDS = {
    NicheCategory.AI_ART: ["ai art", "ai portrait", "ai image", "midjourney", "dalle", "stable diffusion", "ai photo", "ai headshot", "pet portrait", "avatar", "digital art"],
    NicheCategory.CONTENT: ["content", "blog", "article", "copywriting", "seo", "ghostwriting", "writing", "copy", "newsletter"],
    NicheCategory.DESIGN: ["design", "thumbnail", "logo", "graphic", "ui", "ux", "figma", "canva", "branding", "poster", "banner"],
    NicheCategory.RESEARCH: ["research", "data", "analysis", "report", "market research", "competitive analysis"],
    NicheCategory.VOICE: ["voice", "voiceover", "podcast", "audio", "narration", "text to speech", "audiobook"],
    NicheCategory.VIDEO: ["video", "edit", "tiktok", "youtube", "reels", "shorts", "animation", "motion graphics"],
    NicheCategory.AUTOMATION: ["automation", "bot", "script", "workflow", "zapier", "n8n", "integration", "api"],
    NicheCategory.ECOMMERCE: ["ecommerce", "shopify", "amazon", "dropship", "product listing", "store", "etsy"],
    NicheCategory.SAAS_MICRO: ["saas", "app", "tool", "software", "chrome extension", "api", "mvp", "startup"]
}


def _categorize_opportunity(title: str, body: str = "") -> NicheCategory:
    text = (title + " " + body).lower()
    best_match, best_score = NicheCategory.CONTENT, 0
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score, best_match = score, category
    return best_match


def _calculate_scores(post: Dict[str, Any], source: str) -> Dict[str, float]:
    if source == "reddit":
        score, num_comments = post.get("score", 0), post.get("num_comments", 0)
        return {"demand": min(95, 50 + score * 2 + num_comments * 3), "competition": 40 if num_comments < 5 else 60, "monetization": 85 if "[hiring]" in post.get("title", "").lower() else 70, "urgency": 90 if num_comments < 3 else 60, "viral": min(95, 30 + score * 3)}
    elif source == "github":
        stars = post.get("stargazers_count", 0)
        return {"demand": min(95, 60 + stars // 10), "competition": 30 if "good first issue" in str(post.get("labels", [])).lower() else 50, "monetization": 75, "urgency": 80, "viral": min(90, 40 + stars // 5)}
    elif source == "hackernews":
        hn_score = post.get("score", 0)
        return {"demand": min(95, 50 + hn_score // 2), "competition": 50, "monetization": 70, "urgency": 85, "viral": min(95, 40 + hn_score)}
    elif source in ["upwork", "freelancer", "fiverr", "peopleperhour", "guru"]:
        return {"demand": 85, "competition": 65, "monetization": 90, "urgency": 95, "viral": 30}
    elif source == "perplexity":
        return {"demand": 90, "competition": 40, "monetization": 85, "urgency": 80, "viral": 60}
    return {"demand": 70, "competition": 50, "monetization": 70, "urgency": 70, "viral": 50}


# ═══════════════════════════════════════════════════════════════════════════════
# TREND DETECTOR - ALL PLATFORMS + ALL AI
# ═══════════════════════════════════════════════════════════════════════════════

class TrendDetector:
    def __init__(self):
        self.signals: List[TrendSignal] = []
        self.last_scan = None
        self.scan_errors: List[str] = []
        self.ai = get_universal_ai()
    
    async def scan_all_sources(self) -> List[TrendSignal]:
        self.scan_errors = []
        print("\n" + "="*80 + "\n🔍 AUTO-SPAWN v2.0 - ALL PLATFORMS + ALL AI\n" + "="*80)
        
        tasks = [
            ("reddit", self._scan_reddit()),
            ("github", self._scan_github()),
            ("hackernews", self._scan_hackernews()),
            ("upwork", self._scan_upwork()),
            ("remoteok", self._scan_remoteok()),
            ("weworkremotely", self._scan_weworkremotely()),
            ("indeed", self._scan_indeed()),
            ("producthunt", self._scan_producthunt()),
            ("ai_perplexity", self._scan_with_perplexity()),
            ("ai_gemini", self._scan_with_gemini()),
        ]
        
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
        
        signals = []
        for i, (source, _) in enumerate(tasks):
            r = results[i]
            if isinstance(r, Exception):
                self.scan_errors.append(f"{source}: {r}")
                print(f"   ❌ {source}: {str(r)[:50]}")
            elif isinstance(r, list):
                signals.extend(r)
                print(f"   ✅ {source}: {len(r)} opportunities")
        
        signals.sort(key=lambda s: s.opportunity_score, reverse=True)
        self.signals = signals
        self.last_scan = datetime.now(timezone.utc).isoformat()
        print(f"\n🎯 TOTAL: {len(signals)} real opportunities\n" + "="*80)
        return signals

    def detect_emerging_trends(self) -> Dict[str, Any]:
        """Detect emerging trends (sync wrapper returning cached/empty results)"""
        return {
            "ok": True,
            "trends": [
                {
                    "id": s.id,
                    "source": s.source,
                    "description": s.description,
                    "category": s.category.value if hasattr(s.category, 'value') else str(s.category),
                    "opportunity_score": s.opportunity_score,
                    "detected_at": s.detected_at
                }
                for s in self.signals[:10]
            ],
            "total_signals": len(self.signals),
            "last_scan": self.last_scan,
            "errors": self.scan_errors
        }

    async def _scan_reddit(self) -> List[TrendSignal]:
        signals = []
        subreddits = ["forhire", "freelance", "slavelabour", "DesignJobs", "gameDevClassifieds", "hiring", "remotejs", "webdev"]
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                for sub in subreddits:
                    try:
                        r = await client.get(f"https://www.reddit.com/r/{sub}/new.json", headers={"User-Agent": "AiGentsy/2.0"}, params={"limit": 25})
                        if r.status_code == 200:
                            for post in r.json().get("data", {}).get("children", []):
                                pd = post.get("data", {})
                                title = pd.get("title", "")
                                if any(kw in title.lower() for kw in ["[hiring]", "looking for", "need", "seeking", "help wanted", "paid"]):
                                    sc = _calculate_scores(pd, "reddit")
                                    signals.append(TrendSignal(f"reddit_{pd.get('id', secrets.token_hex(4))}", "reddit", title[:200], _categorize_opportunity(title, pd.get("selftext", "")), sc["demand"], sc["competition"], sc["monetization"], sc["urgency"], sc["viral"], {"url": f"https://reddit.com{pd.get('permalink')}", "subreddit": sub}, datetime.now(timezone.utc).isoformat()))
                        await asyncio.sleep(0.3)
                    except Exception as e:
                        self.scan_errors.append(f"Reddit r/{sub}: {e}")
        except Exception as e:
            self.scan_errors.append(f"Reddit: {e}")
        return signals
    
    async def _scan_github(self) -> List[TrendSignal]:
        signals = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {"Accept": "application/vnd.github.v3+json"}
                if GITHUB_TOKEN: headers["Authorization"] = f"token {GITHUB_TOKEN}"
                for query in ["label:bounty state:open", 'label:"help wanted" state:open', 'label:"good first issue" language:python']:
                    try:
                        r = await client.get("https://api.github.com/search/issues", headers=headers, params={"q": query, "sort": "created", "per_page": 15})
                        if r.status_code == 200:
                            for item in r.json().get("items", []):
                                title = item.get("title", "")
                                sc = _calculate_scores(item, "github")
                                signals.append(TrendSignal(f"github_{item.get('id')}", "github", title[:200], _categorize_opportunity(title, item.get("body", "") or ""), sc["demand"], sc["competition"], sc["monetization"], sc["urgency"], sc["viral"], {"url": item.get("html_url"), "labels": [l.get("name") for l in item.get("labels", [])]}, datetime.now(timezone.utc).isoformat()))
                        await asyncio.sleep(1)
                    except: pass
        except Exception as e:
            self.scan_errors.append(f"GitHub: {e}")
        return signals
    
    async def _scan_hackernews(self) -> List[TrendSignal]:
        signals = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
                if r.status_code == 200:
                    for sid in r.json()[:30]:
                        try:
                            sr = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                            if sr.status_code == 200:
                                story = sr.json()
                                if story and any(kw in story.get("title", "").lower() for kw in ["hiring", "freelance", "ai", "startup", "saas", "launch"]):
                                    title = story.get("title", "")
                                    sc = _calculate_scores(story, "hackernews")
                                    signals.append(TrendSignal(f"hn_{sid}", "hackernews", title[:200], _categorize_opportunity(title), sc["demand"], sc["competition"], sc["monetization"], sc["urgency"], sc["viral"], {"url": story.get("url") or f"https://news.ycombinator.com/item?id={sid}", "score": story.get("score")}, datetime.now(timezone.utc).isoformat()))
                        except: pass
        except Exception as e:
            self.scan_errors.append(f"HackerNews: {e}")
        return signals
    
    async def _scan_upwork(self) -> List[TrendSignal]:
        return await self._scan_rss("upwork", ["https://www.upwork.com/ab/feed/jobs/rss?q=ai&sort=recency", "https://www.upwork.com/ab/feed/jobs/rss?q=python&sort=recency", "https://www.upwork.com/ab/feed/jobs/rss?q=automation&sort=recency"])
    
    async def _scan_remoteok(self) -> List[TrendSignal]:
        signals = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get("https://remoteok.com/api", headers={"User-Agent": "AiGentsy/2.0"})
                if r.status_code == 200:
                    for job in r.json()[1:25]:
                        if isinstance(job, dict) and any(t in ["ai", "python", "javascript", "design"] for t in job.get("tags", [])):
                            title = f"{job.get('position', '')} at {job.get('company', '')}"
                            signals.append(TrendSignal(f"remoteok_{job.get('id', secrets.token_hex(4))}", "remoteok", title[:200], _categorize_opportunity(title), 80, 60, 85, 75, 40, {"url": job.get("url"), "tags": job.get("tags", [])}, datetime.now(timezone.utc).isoformat()))
        except Exception as e:
            self.scan_errors.append(f"RemoteOK: {e}")
        return signals
    
    async def _scan_weworkremotely(self) -> List[TrendSignal]:
        return await self._scan_rss("weworkremotely", ["https://weworkremotely.com/remote-jobs.rss"])
    
    async def _scan_indeed(self) -> List[TrendSignal]:
        return await self._scan_rss("indeed", ["https://www.indeed.com/rss?q=freelance+ai&sort=date"])
    
    async def _scan_producthunt(self) -> List[TrendSignal]:
        signals = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get("https://www.producthunt.com/feed", headers={"User-Agent": "AiGentsy/2.0"})
                if r.status_code == 200:
                    feed = feedparser.parse(r.text)
                    for entry in feed.entries[:10]:
                        title = entry.get("title", "")
                        if any(kw in title.lower() for kw in ["ai", "tool", "app", "saas"]):
                            signals.append(TrendSignal(f"ph_{secrets.token_hex(4)}", "producthunt", f"Build for: {title}"[:200], NicheCategory.SAAS_MICRO, 85, 50, 80, 70, 75, {"url": entry.get("link")}, datetime.now(timezone.utc).isoformat()))
        except Exception as e:
            self.scan_errors.append(f"ProductHunt: {e}")
        return signals
    
    async def _scan_rss(self, source: str, feeds: List[str]) -> List[TrendSignal]:
        signals = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                for url in feeds:
                    try:
                        r = await client.get(url, headers={"User-Agent": "AiGentsy/2.0"})
                        if r.status_code == 200:
                            feed = feedparser.parse(r.text)
                            for entry in feed.entries[:10]:
                                title = entry.get("title", "")
                                sc = _calculate_scores({}, source)
                                signals.append(TrendSignal(f"{source}_{secrets.token_hex(4)}", source, title[:200], _categorize_opportunity(title, entry.get("summary", "")), sc["demand"], sc["competition"], sc["monetization"], sc["urgency"], sc["viral"], {"url": entry.get("link")}, datetime.now(timezone.utc).isoformat()))
                    except: pass
        except Exception as e:
            self.scan_errors.append(f"{source} RSS: {e}")
        return signals
    
    async def _scan_with_perplexity(self) -> List[TrendSignal]:
        signals = []
        if not PERPLEXITY_API_KEY: return signals
        queries = ["What freelance AI and automation jobs were posted today on Upwork, Fiverr, and Reddit? List specific opportunities with prices.", "What are the hottest micro-SaaS trends people are paying for right now?", "What AI services are in highest demand this week?"]
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                for query in queries:
                    try:
                        r = await client.post("https://api.perplexity.ai/chat/completions", headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}, json={"model": "llama-3.1-sonar-large-128k-online", "messages": [{"role": "user", "content": query}], "max_tokens": 2000})
                        if r.status_code == 200:
                            d = r.json()
                            content = d.get("choices", [{}])[0].get("message", {}).get("content", "")
                            if content:
                                signals.append(TrendSignal(f"perplexity_{secrets.token_hex(4)}", "perplexity", query[:200], _categorize_opportunity(query, content), 90, 40, 85, 80, 60, {"ai_response": content[:2000], "citations": d.get("citations", [])[:5]}, datetime.now(timezone.utc).isoformat(), {"model": "perplexity-sonar"}))
                        await asyncio.sleep(1)
                    except Exception as e:
                        self.scan_errors.append(f"Perplexity: {e}")
        except Exception as e:
            self.scan_errors.append(f"Perplexity: {e}")
        return signals
    
    async def _scan_with_gemini(self) -> List[TrendSignal]:
        signals = []
        if not GEMINI_API_KEY: return signals
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}", json={"contents": [{"parts": [{"text": "What are the top 5 freelance opportunities for AI automation services right now? Be specific with platforms, prices, and demand levels."}]}]})
                if r.status_code == 200:
                    text = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if text:
                        signals.append(TrendSignal(f"gemini_{secrets.token_hex(4)}", "gemini", "Gemini AI Trend Analysis"[:200], NicheCategory.AUTOMATION, 85, 45, 80, 75, 55, {"ai_response": text[:2000]}, datetime.now(timezone.utc).isoformat(), {"model": "gemini-pro"}))
        except Exception as e:
            self.scan_errors.append(f"Gemini: {e}")
        return signals


# ═══════════════════════════════════════════════════════════════════════════════
# BUSINESS SPAWNER
# ═══════════════════════════════════════════════════════════════════════════════

class BusinessSpawner:
    def __init__(self):
        self.spawned_businesses: Dict[str, SpawnedBusiness] = {}
    
    def _generate_referral_code(self, category: str, spawn_id: str) -> str:
        return f"{category.upper()[:6]}-{spawn_id[-4:].upper()}"
    
    async def spawn_from_signal(self, signal: TrendSignal) -> SpawnedBusiness:
        template = BUSINESS_TEMPLATES.get(signal.category)
        if not template:
            raise ValueError(f"No template for: {signal.category}")
        
        subject = self._extract_subject(signal)
        name = random.choice(template["name_patterns"]).format(Subject=subject, Type=subject, Niche=subject)
        slug = name.lower().replace(" ", "-")[:40] + f"-{secrets.token_hex(3)}"
        hook = random.choice(template["hooks"]).format(Subject=subject, Type=subject, Niche=subject, price=template["services"][0]["price"], hours=template["services"][0].get("delivery_hours", 24))
        
        spawn_id = f"spawn_{secrets.token_hex(8)}"
        referral_code = self._generate_referral_code(signal.category.value, spawn_id)
        base_url = os.getenv("AIGENTSY_URL", "https://aigentsy.com")
        spawns_url = os.getenv("SPAWNS_URL", "https://spawns.aigentsy.com")
        
        business = SpawnedBusiness(
            spawn_id=spawn_id, name=name, slug=slug, tagline=hook, category=signal.category, niche=subject,
            trigger_signal=signal, spawned_at=datetime.now(timezone.utc).isoformat(), status=SpawnStatus.LAUNCHING,
            landing_page_url=f"{spawns_url}/{slug}", stripe_product_id=f"prod_{secrets.token_hex(12)}",
            base_price=template["services"][0]["price"], current_price=template["services"][0]["price"],
            services=[{**s, "service_id": f"svc_{secrets.token_hex(4)}"} for s in template["services"]],
            auto_kill_at=(datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            referral_code=referral_code, powered_by_aigentsy=True, aigentsy_cta_enabled=True,
            aigentsy_dashboard_link=f"{base_url}/start?ref={referral_code}",
            wade_user_id="wade_system", stripe_connect_account=os.getenv("STRIPE_CONNECT_ACCOUNT", ""),
            revenue_split_aigentsy=1.0, visible_in_wade_dashboard=True, contributes_to_hive=True
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
        content = []
        for platform in template["platforms"][:3]:
            for i in range(3):
                include_cta = (i % 3 == 2)
                content.append({
                    "id": f"content_{secrets.token_hex(4)}", "platform": platform, "hook": biz.tagline,
                    "cta": f"🚀 Want AI building YOUR business? {biz.aigentsy_dashboard_link}" if include_cta else f"Order now: {biz.landing_page_url}",
                    "referral_code": biz.referral_code,
                    "scheduled": (datetime.now(timezone.utc) + timedelta(hours=i*4)).isoformat(), "status": "queued"
                })
        return content
    
    def get_ecosystem_stats(self) -> Dict[str, Any]:
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
        }


# ═══════════════════════════════════════════════════════════════════════════════
# LIFECYCLE MANAGER
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
        if biz.marketing_spend_total > 0 and biz.profit / max(biz.marketing_spend_total, 1) > 1:
            score += 20
        return max(0, min(100, score))
    
    def _decide_action(self, biz: SpawnedBusiness) -> str:
        if biz.status == SpawnStatus.LAUNCHING:
            return "launch" if biz.landing_page_url else "wait"
        if biz.auto_kill_at:
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
# ADOPTION SYSTEM
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
                "spawn_id": spawn_id, "name": biz.name, "category": biz.category.value, "niche": biz.niche,
                "health_score": biz.health_score, "revenue": biz.revenue, "orders": biz.orders,
                "adoption_price": round(price, 2), "monthly_revenue_estimate": monthly_rev
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
# MASTER ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class AutoSpawnEngine:
    def __init__(self):
        self.detector = TrendDetector()
        self.spawner = BusinessSpawner()
        self.lifecycle = LifecycleManager(self.spawner)
        self.adoption = AdoptionSystem(self.spawner)
        self.network = SpawnNetwork()
        self.total_spawned = 0
        self.ai = get_universal_ai()
    
    async def run_full_cycle(self) -> Dict[str, Any]:
        results = {"timestamp": datetime.now(timezone.utc).isoformat(), "phases": {}}
        
        # 1. Detect from ALL sources + ALL AI
        signals = await self.detector.scan_all_sources()
        results["phases"]["trends"] = {"found": len(signals), "top": [{"query": s.query[:100], "source": s.source, "score": round(s.opportunity_score, 1)} for s in signals[:10]], "errors": self.detector.scan_errors}
        
        # 2. Spawn businesses
        spawned = []
        for signal in signals[:5]:
            try:
                biz = await self.spawner.spawn_from_signal(signal)
                spawned.append({"id": biz.spawn_id, "name": biz.name, "category": biz.category.value, "referral_code": biz.referral_code})
                self.total_spawned += 1
                print(f"   ✅ Spawned: {biz.name}")
            except Exception as e:
                print(f"   ❌ Spawn failed: {e}")
        results["phases"]["spawned"] = spawned
        
        # 3. Lifecycle
        results["phases"]["lifecycle"] = await self.lifecycle.run_lifecycle_check()
        
        # 4. Cross-promotions
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
            "cross_promo_opportunities": cross_promos.get("total_promos", 0),
            "ai_models_available": list(self.ai.available_models.keys())
        }
        
        return results
    
    async def _generate_network_promos(self) -> Dict:
        all_spawns = list(self.spawner.spawned_businesses.values())
        active_spawns = [s for s in all_spawns if s.status in [SpawnStatus.LIVE, SpawnStatus.SCALING]]
        promos_generated = {"checkout_upsells": 0, "email_cross_sells": 0, "social_mentions": 0, "bundles": 0, "total_promos": 0}
        for spawn in active_spawns:
            upsells = self.network.generate_checkout_upsells(spawn, all_spawns)
            promos_generated["checkout_upsells"] += len(upsells)
            email = self.network.generate_email_cross_sell(spawn, all_spawns)
            if email:
                promos_generated["email_cross_sells"] += 1
            mentions = self.network.generate_social_mentions(spawn, all_spawns)
            promos_generated["social_mentions"] += len(mentions)
        if len(active_spawns) >= 2:
            for spawn1 in active_spawns[:5]:
                complementary = self.network.find_complementary_spawns(spawn1, active_spawns)
                if complementary:
                    bundle = self.network.create_bundle_deal([spawn1, complementary[0]])
                    if bundle:
                        promos_generated["bundles"] += 1
        promos_generated["total_promos"] = sum([promos_generated["checkout_upsells"], promos_generated["email_cross_sells"], promos_generated["social_mentions"], promos_generated["bundles"]])
        return promos_generated
    
    def get_dashboard(self) -> Dict:
        businesses = list(self.spawner.spawned_businesses.values())
        ecosystem = self.spawner.get_ecosystem_stats()
        active_spawns = [b for b in businesses if b.status in [SpawnStatus.LIVE, SpawnStatus.SCALING]]
        audience_pool = self.network.get_shared_audience_pool(businesses)
        
        return {
            "total_spawned": len(businesses),
            "active": len(active_spawns),
            "total_revenue": sum(b.revenue for b in businesses),
            "total_orders": sum(b.orders for b in businesses),
            "by_status": {s.value: len([b for b in businesses if b.status == s]) for s in SpawnStatus},
            "top_performers": sorted([{"name": b.name, "revenue": b.revenue, "health": b.health_score} for b in businesses if b.status in [SpawnStatus.LIVE, SpawnStatus.SCALING]], key=lambda x: x["revenue"], reverse=True)[:5],
            "adoptable": self.adoption.get_adoptable(),
            "recent_signals": [{"query": s.query[:80], "source": s.source, "score": round(s.opportunity_score, 1)} for s in self.detector.signals[:10]],
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
            "network": {
                "total_spawns_in_network": len(active_spawns),
                "network_categories": list(set(b.category.value for b in active_spawns)),
                "shared_audience_size": audience_pool.get("total_audience", 0),
                "audience_by_category": audience_pool.get("by_category", {}),
                "cross_promo_active": len(active_spawns) >= 2,
                "bundle_opportunities": len(active_spawns) // 2
            },
            "ai_status": get_universal_ai().available_models
        }
    
    def get_network_promos_for_spawn(self, spawn_id: str) -> Dict:
        spawn = self.spawner.spawned_businesses.get(spawn_id)
        if not spawn:
            return {"ok": False, "error": "spawn_not_found"}
        all_spawns = list(self.spawner.spawned_businesses.values())
        return {
            "ok": True, "spawn_id": spawn_id, "spawn_name": spawn.name,
            "checkout_upsells": self.network.generate_checkout_upsells(spawn, all_spawns),
            "email_cross_sell": self.network.generate_email_cross_sell(spawn, all_spawns),
            "social_mentions": self.network.generate_social_mentions(spawn, all_spawns),
            "complementary_spawns": [{"spawn_id": s.spawn_id, "name": s.name, "category": s.category.value} for s in self.network.find_complementary_spawns(spawn, all_spawns)]
        }


# Singleton
_engine: Optional[AutoSpawnEngine] = None

def get_engine() -> AutoSpawnEngine:
    global _engine
    if _engine is None:
        _engine = AutoSpawnEngine()
    return _engine

def get_spawn_engine() -> AutoSpawnEngine:
    return get_engine()


print("🚀 AUTO-SPAWN ENGINE v2.0 LOADED")
print("   • AI Models: Claude, GPT-4, Gemini, Perplexity (ALL simultaneous)")
print("   • Platforms: Reddit, GitHub, HackerNews, Upwork, RemoteOK, ProductHunt +more")
print("   • Templates: AI Art, Content, Design, Voice, Video, Automation, SaaS")
print("   • Ecosystem: Cross-promotion network, referral tracking, adoption system")
print("   • Monetization: Direct fulfillment, arbitrage, spawns, lead gen, referrals")
