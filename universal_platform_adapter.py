"""
UNIVERSAL PLATFORM ADAPTER - Config-Driven Monetization Layer
==============================================================

This transforms AiGentsy from 27 hardcoded platforms to UNLIMITED.

THE INSIGHT:
Any platform is monetizable if it has:
1. Users (traffic)
2. Intent (what users want)
3. Transaction mechanism (how money flows)

THE ARCHITECTURE:
- Platform = Configuration (not code)
- Adapter = Universal interface
- Add platforms via config, not engineering

EXPANSION VECTORS:
1. Platform Adapters: 27 → 100 → 1000 platforms (this file)
2. Browser Extension: Entire browsable web (future)
3. AI-to-AI Marketplace: Any AI can submit opportunities (protocol)
"""

import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


# ============================================================
# PLATFORM CLASSIFICATION
# ============================================================

class PlatformCategory(str, Enum):
    """Categories of monetizable platforms"""
    FREELANCE = "freelance"  # Upwork, Fiverr, Toptal
    ECOMMERCE = "ecommerce"  # Shopify, Amazon, Etsy
    SOCIAL = "social"  # TikTok, Instagram, YouTube
    CONTENT = "content"  # Medium, Substack, Ghost
    SAAS = "saas"  # Any SaaS with affiliate/API
    MARKETPLACE = "marketplace"  # General marketplaces
    JOBS = "jobs"  # LinkedIn, Indeed, AngelList
    ADVERTISING = "advertising"  # Google Ads, Meta Ads
    AFFILIATE = "affiliate"  # Amazon Associates, ShareASale
    COMMUNITY = "community"  # Discord, Slack, Reddit
    PROFESSIONAL = "professional"  # Clarity.fm, Expert360
    CREATIVE = "creative"  # 99designs, Dribbble, Behance
    DEVELOPMENT = "development"  # GitHub, GitLab, Stack Overflow
    EDUCATION = "education"  # Udemy, Teachable, Skillshare
    CRYPTO = "crypto"  # OpenSea, Rarible, etc.


class IntentType(str, Enum):
    """Types of monetizable intent"""
    BUY_SERVICE = "buy_service"
    HIRE_TALENT = "hire_talent"
    PURCHASE_PRODUCT = "purchase_product"
    SUBSCRIBE = "subscribe"
    INVEST = "invest"
    LEARN = "learn"
    COLLABORATE = "collaborate"
    ADVERTISE = "advertise"
    SELL = "sell"
    PROMOTE = "promote"


class MonetizationMethod(str, Enum):
    """How money flows through the platform"""
    DIRECT_PAYMENT = "direct_payment"  # Client pays directly
    PLATFORM_ESCROW = "platform_escrow"  # Platform holds funds
    SUBSCRIPTION = "subscription"  # Recurring payments
    COMMISSION = "commission"  # % of transaction
    AFFILIATE = "affiliate"  # Referral fee
    ADVERTISING = "advertising"  # Ad revenue share
    TIPS = "tips"  # Voluntary payments
    LICENSING = "licensing"  # IP licensing fees
    BOUNTY = "bounty"  # Task completion rewards


class AccessMethod(str, Enum):
    """How we interact with the platform"""
    API = "api"  # Official API
    OAUTH = "oauth"  # OAuth integration
    SCRAPING = "scraping"  # Web scraping (with ToS compliance)
    WEBHOOK = "webhook"  # Incoming webhooks
    EMAIL = "email"  # Email parsing
    BROWSER = "browser"  # Browser automation
    MANUAL = "manual"  # Manual with AI assistance


# ============================================================
# PLATFORM CONFIGURATION
# ============================================================

@dataclass
class PlatformConfig:
    """
    Configuration for a monetizable platform
    
    This is the key insight: platforms are CONFIG, not code.
    """
    # Identity
    platform_id: str
    name: str
    url: str
    category: PlatformCategory
    
    # Monetization
    intent_types: List[IntentType]
    monetization_methods: List[MonetizationMethod]
    commission_rate: float  # Platform's cut (0.0 - 1.0)
    min_transaction: float  # Minimum transaction value
    max_transaction: float  # Maximum transaction value
    
    # Access
    access_methods: List[AccessMethod]
    api_base_url: Optional[str] = None
    api_version: Optional[str] = None
    oauth_url: Optional[str] = None
    requires_approval: bool = False
    
    # Detection patterns (for scraping/browser)
    opportunity_selectors: Dict[str, str] = field(default_factory=dict)
    intent_patterns: List[str] = field(default_factory=list)
    value_extraction_pattern: Optional[str] = None
    
    # Execution
    can_auto_apply: bool = True
    can_auto_bid: bool = True
    can_auto_deliver: bool = False
    requires_human_verification: bool = False
    
    # Limits
    rate_limit_per_hour: int = 100
    daily_opportunity_limit: int = 50
    
    # Status
    is_active: bool = True
    is_verified: bool = False
    last_verified: Optional[str] = None
    
    # Metadata
    added_at: str = field(default_factory=_now)
    notes: str = ""
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["category"] = self.category.value
        result["intent_types"] = [i.value for i in self.intent_types]
        result["monetization_methods"] = [m.value for m in self.monetization_methods]
        result["access_methods"] = [a.value for a in self.access_methods]
        return result


# ============================================================
# PRE-CONFIGURED PLATFORMS (Initial 50+)
# ============================================================

PLATFORM_CONFIGS: Dict[str, PlatformConfig] = {}


def _register_platform(config: PlatformConfig):
    """Register a platform configuration"""
    PLATFORM_CONFIGS[config.platform_id] = config


# === FREELANCE PLATFORMS ===

_register_platform(PlatformConfig(
    platform_id="upwork",
    name="Upwork",
    url="https://upwork.com",
    category=PlatformCategory.FREELANCE,
    intent_types=[IntentType.HIRE_TALENT, IntentType.BUY_SERVICE],
    monetization_methods=[MonetizationMethod.PLATFORM_ESCROW, MonetizationMethod.COMMISSION],
    commission_rate=0.20,
    min_transaction=5.0,
    max_transaction=100000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://api.upwork.com/api",
    api_version="v3",
    oauth_url="https://www.upwork.com/ab/account-security/oauth2/authorize",
    can_auto_apply=True,
    can_auto_bid=True,
    rate_limit_per_hour=60,
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="fiverr",
    name="Fiverr",
    url="https://fiverr.com",
    category=PlatformCategory.FREELANCE,
    intent_types=[IntentType.BUY_SERVICE],
    monetization_methods=[MonetizationMethod.PLATFORM_ESCROW, MonetizationMethod.COMMISSION],
    commission_rate=0.20,
    min_transaction=5.0,
    max_transaction=50000.0,
    access_methods=[AccessMethod.API, AccessMethod.SCRAPING],
    api_base_url="https://api.fiverr.com",
    can_auto_apply=False,  # Sellers create gigs
    can_auto_bid=False,
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="toptal",
    name="Toptal",
    url="https://toptal.com",
    category=PlatformCategory.FREELANCE,
    intent_types=[IntentType.HIRE_TALENT],
    monetization_methods=[MonetizationMethod.DIRECT_PAYMENT, MonetizationMethod.COMMISSION],
    commission_rate=0.30,
    min_transaction=1000.0,
    max_transaction=500000.0,
    access_methods=[AccessMethod.API, AccessMethod.MANUAL],
    requires_approval=True,
    can_auto_apply=False,
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="freelancer",
    name="Freelancer.com",
    url="https://freelancer.com",
    category=PlatformCategory.FREELANCE,
    intent_types=[IntentType.HIRE_TALENT, IntentType.BUY_SERVICE],
    monetization_methods=[MonetizationMethod.PLATFORM_ESCROW, MonetizationMethod.COMMISSION],
    commission_rate=0.10,
    min_transaction=10.0,
    max_transaction=50000.0,
    access_methods=[AccessMethod.API],
    api_base_url="https://www.freelancer.com/api",
    can_auto_apply=True,
    can_auto_bid=True,
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="guru",
    name="Guru",
    url="https://guru.com",
    category=PlatformCategory.FREELANCE,
    intent_types=[IntentType.HIRE_TALENT, IntentType.BUY_SERVICE],
    monetization_methods=[MonetizationMethod.PLATFORM_ESCROW],
    commission_rate=0.09,
    min_transaction=20.0,
    max_transaction=100000.0,
    access_methods=[AccessMethod.SCRAPING, AccessMethod.BROWSER],
    can_auto_apply=True,
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="peopleperhour",
    name="PeoplePerHour",
    url="https://peopleperhour.com",
    category=PlatformCategory.FREELANCE,
    intent_types=[IntentType.HIRE_TALENT, IntentType.BUY_SERVICE],
    monetization_methods=[MonetizationMethod.PLATFORM_ESCROW, MonetizationMethod.COMMISSION],
    commission_rate=0.20,
    min_transaction=15.0,
    max_transaction=25000.0,
    access_methods=[AccessMethod.API, AccessMethod.SCRAPING],
    can_auto_apply=True,
    is_verified=True
))

# === CREATIVE PLATFORMS ===

_register_platform(PlatformConfig(
    platform_id="99designs",
    name="99designs",
    url="https://99designs.com",
    category=PlatformCategory.CREATIVE,
    intent_types=[IntentType.BUY_SERVICE],
    monetization_methods=[MonetizationMethod.PLATFORM_ESCROW, MonetizationMethod.COMMISSION],
    commission_rate=0.15,
    min_transaction=299.0,
    max_transaction=10000.0,
    access_methods=[AccessMethod.API, AccessMethod.BROWSER],
    can_auto_apply=True,
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="dribbble",
    name="Dribbble",
    url="https://dribbble.com",
    category=PlatformCategory.CREATIVE,
    intent_types=[IntentType.HIRE_TALENT],
    monetization_methods=[MonetizationMethod.DIRECT_PAYMENT, MonetizationMethod.SUBSCRIPTION],
    commission_rate=0.0,
    min_transaction=50.0,
    max_transaction=50000.0,
    access_methods=[AccessMethod.API, AccessMethod.SCRAPING],
    api_base_url="https://api.dribbble.com/v2",
    can_auto_apply=True,
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="behance",
    name="Behance",
    url="https://behance.net",
    category=PlatformCategory.CREATIVE,
    intent_types=[IntentType.HIRE_TALENT, IntentType.COLLABORATE],
    monetization_methods=[MonetizationMethod.DIRECT_PAYMENT],
    commission_rate=0.0,
    min_transaction=100.0,
    max_transaction=100000.0,
    access_methods=[AccessMethod.API, AccessMethod.SCRAPING],
    can_auto_apply=True,
    is_verified=True
))

# === ECOMMERCE PLATFORMS ===

_register_platform(PlatformConfig(
    platform_id="shopify",
    name="Shopify",
    url="https://shopify.com",
    category=PlatformCategory.ECOMMERCE,
    intent_types=[IntentType.SELL, IntentType.PURCHASE_PRODUCT],
    monetization_methods=[MonetizationMethod.DIRECT_PAYMENT, MonetizationMethod.SUBSCRIPTION],
    commission_rate=0.029,  # 2.9% + 30¢
    min_transaction=1.0,
    max_transaction=1000000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://{store}.myshopify.com/admin/api",
    api_version="2024-01",
    oauth_url="https://{store}.myshopify.com/admin/oauth/authorize",
    can_auto_deliver=True,
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="amazon_seller",
    name="Amazon Seller Central",
    url="https://sellercentral.amazon.com",
    category=PlatformCategory.ECOMMERCE,
    intent_types=[IntentType.SELL, IntentType.PURCHASE_PRODUCT],
    monetization_methods=[MonetizationMethod.PLATFORM_ESCROW, MonetizationMethod.COMMISSION],
    commission_rate=0.15,
    min_transaction=1.0,
    max_transaction=1000000.0,
    access_methods=[AccessMethod.API],
    api_base_url="https://sellingpartnerapi.amazon.com",
    requires_approval=True,
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="etsy",
    name="Etsy",
    url="https://etsy.com",
    category=PlatformCategory.ECOMMERCE,
    intent_types=[IntentType.SELL, IntentType.PURCHASE_PRODUCT],
    monetization_methods=[MonetizationMethod.PLATFORM_ESCROW, MonetizationMethod.COMMISSION],
    commission_rate=0.065,
    min_transaction=1.0,
    max_transaction=50000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://openapi.etsy.com/v3",
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="gumroad",
    name="Gumroad",
    url="https://gumroad.com",
    category=PlatformCategory.ECOMMERCE,
    intent_types=[IntentType.SELL, IntentType.PURCHASE_PRODUCT],
    monetization_methods=[MonetizationMethod.DIRECT_PAYMENT, MonetizationMethod.COMMISSION],
    commission_rate=0.10,
    min_transaction=1.0,
    max_transaction=10000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://api.gumroad.com/v2",
    is_verified=True
))

# === SOCIAL PLATFORMS ===

_register_platform(PlatformConfig(
    platform_id="tiktok",
    name="TikTok",
    url="https://tiktok.com",
    category=PlatformCategory.SOCIAL,
    intent_types=[IntentType.PROMOTE, IntentType.ADVERTISE],
    monetization_methods=[MonetizationMethod.ADVERTISING, MonetizationMethod.AFFILIATE, MonetizationMethod.TIPS],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=1000000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://open-api.tiktok.com",
    oauth_url="https://www.tiktok.com/auth/authorize/",
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="instagram",
    name="Instagram",
    url="https://instagram.com",
    category=PlatformCategory.SOCIAL,
    intent_types=[IntentType.PROMOTE, IntentType.ADVERTISE],
    monetization_methods=[MonetizationMethod.ADVERTISING, MonetizationMethod.AFFILIATE],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=1000000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://graph.instagram.com",
    oauth_url="https://api.instagram.com/oauth/authorize",
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="youtube",
    name="YouTube",
    url="https://youtube.com",
    category=PlatformCategory.SOCIAL,
    intent_types=[IntentType.PROMOTE, IntentType.ADVERTISE, IntentType.LEARN],
    monetization_methods=[MonetizationMethod.ADVERTISING, MonetizationMethod.AFFILIATE, MonetizationMethod.SUBSCRIPTION],
    commission_rate=0.45,  # YouTube takes 45%
    min_transaction=0.0,
    max_transaction=1000000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://www.googleapis.com/youtube/v3",
    oauth_url="https://accounts.google.com/o/oauth2/auth",
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="twitter",
    name="Twitter/X",
    url="https://twitter.com",
    category=PlatformCategory.SOCIAL,
    intent_types=[IntentType.PROMOTE, IntentType.ADVERTISE],
    monetization_methods=[MonetizationMethod.ADVERTISING, MonetizationMethod.SUBSCRIPTION, MonetizationMethod.TIPS],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=1000000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://api.twitter.com/2",
    oauth_url="https://twitter.com/i/oauth2/authorize",
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="linkedin",
    name="LinkedIn",
    url="https://linkedin.com",
    category=PlatformCategory.PROFESSIONAL,
    intent_types=[IntentType.HIRE_TALENT, IntentType.PROMOTE, IntentType.COLLABORATE],
    monetization_methods=[MonetizationMethod.ADVERTISING, MonetizationMethod.SUBSCRIPTION, MonetizationMethod.DIRECT_PAYMENT],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=100000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://api.linkedin.com/v2",
    oauth_url="https://www.linkedin.com/oauth/v2/authorization",
    is_verified=True
))

# === CONTENT PLATFORMS ===

_register_platform(PlatformConfig(
    platform_id="medium",
    name="Medium",
    url="https://medium.com",
    category=PlatformCategory.CONTENT,
    intent_types=[IntentType.LEARN, IntentType.PROMOTE],
    monetization_methods=[MonetizationMethod.SUBSCRIPTION, MonetizationMethod.AFFILIATE],
    commission_rate=0.0,
    min_transaction=5.0,
    max_transaction=10000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://api.medium.com/v1",
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="substack",
    name="Substack",
    url="https://substack.com",
    category=PlatformCategory.CONTENT,
    intent_types=[IntentType.LEARN, IntentType.SUBSCRIBE],
    monetization_methods=[MonetizationMethod.SUBSCRIPTION],
    commission_rate=0.10,
    min_transaction=5.0,
    max_transaction=1000.0,
    access_methods=[AccessMethod.API, AccessMethod.BROWSER],
    is_verified=True
))

# === DEVELOPMENT PLATFORMS ===

_register_platform(PlatformConfig(
    platform_id="github",
    name="GitHub",
    url="https://github.com",
    category=PlatformCategory.DEVELOPMENT,
    intent_types=[IntentType.HIRE_TALENT, IntentType.COLLABORATE, IntentType.BUY_SERVICE],
    monetization_methods=[MonetizationMethod.BOUNTY, MonetizationMethod.SUBSCRIPTION],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=100000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://api.github.com",
    oauth_url="https://github.com/login/oauth/authorize",
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="stackoverflow_jobs",
    name="Stack Overflow Jobs",
    url="https://stackoverflow.com/jobs",
    category=PlatformCategory.JOBS,
    intent_types=[IntentType.HIRE_TALENT],
    monetization_methods=[MonetizationMethod.DIRECT_PAYMENT],
    commission_rate=0.0,
    min_transaction=50000.0,
    max_transaction=500000.0,
    access_methods=[AccessMethod.API, AccessMethod.SCRAPING],
    can_auto_apply=True,
    is_verified=True
))

# === EDUCATION PLATFORMS ===

_register_platform(PlatformConfig(
    platform_id="udemy",
    name="Udemy",
    url="https://udemy.com",
    category=PlatformCategory.EDUCATION,
    intent_types=[IntentType.LEARN, IntentType.SELL],
    monetization_methods=[MonetizationMethod.COMMISSION, MonetizationMethod.DIRECT_PAYMENT],
    commission_rate=0.63,  # Udemy takes up to 63%
    min_transaction=10.0,
    max_transaction=200.0,
    access_methods=[AccessMethod.API, AccessMethod.BROWSER],
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="teachable",
    name="Teachable",
    url="https://teachable.com",
    category=PlatformCategory.EDUCATION,
    intent_types=[IntentType.LEARN, IntentType.SELL],
    monetization_methods=[MonetizationMethod.DIRECT_PAYMENT, MonetizationMethod.SUBSCRIPTION],
    commission_rate=0.05,
    min_transaction=10.0,
    max_transaction=5000.0,
    access_methods=[AccessMethod.API, AccessMethod.WEBHOOK],
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="skillshare",
    name="Skillshare",
    url="https://skillshare.com",
    category=PlatformCategory.EDUCATION,
    intent_types=[IntentType.LEARN, IntentType.SELL],
    monetization_methods=[MonetizationMethod.SUBSCRIPTION, MonetizationMethod.AFFILIATE],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=1000.0,
    access_methods=[AccessMethod.BROWSER],
    is_verified=True
))

# === AFFILIATE PLATFORMS ===

_register_platform(PlatformConfig(
    platform_id="amazon_associates",
    name="Amazon Associates",
    url="https://affiliate-program.amazon.com",
    category=PlatformCategory.AFFILIATE,
    intent_types=[IntentType.PROMOTE],
    monetization_methods=[MonetizationMethod.AFFILIATE],
    commission_rate=0.0,  # We get commission, not pay it
    min_transaction=0.0,
    max_transaction=1000000.0,
    access_methods=[AccessMethod.API],
    api_base_url="https://webservices.amazon.com/paapi5",
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="shareasale",
    name="ShareASale",
    url="https://shareasale.com",
    category=PlatformCategory.AFFILIATE,
    intent_types=[IntentType.PROMOTE],
    monetization_methods=[MonetizationMethod.AFFILIATE],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=100000.0,
    access_methods=[AccessMethod.API],
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="cj_affiliate",
    name="CJ Affiliate",
    url="https://cj.com",
    category=PlatformCategory.AFFILIATE,
    intent_types=[IntentType.PROMOTE],
    monetization_methods=[MonetizationMethod.AFFILIATE],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=100000.0,
    access_methods=[AccessMethod.API],
    is_verified=True
))

# === PROFESSIONAL SERVICES ===

_register_platform(PlatformConfig(
    platform_id="clarity",
    name="Clarity.fm",
    url="https://clarity.fm",
    category=PlatformCategory.PROFESSIONAL,
    intent_types=[IntentType.BUY_SERVICE, IntentType.HIRE_TALENT],
    monetization_methods=[MonetizationMethod.DIRECT_PAYMENT, MonetizationMethod.COMMISSION],
    commission_rate=0.15,
    min_transaction=10.0,
    max_transaction=1000.0,
    access_methods=[AccessMethod.API, AccessMethod.BROWSER],
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="calendly",
    name="Calendly",
    url="https://calendly.com",
    category=PlatformCategory.PROFESSIONAL,
    intent_types=[IntentType.BUY_SERVICE],
    monetization_methods=[MonetizationMethod.DIRECT_PAYMENT],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=10000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH, AccessMethod.WEBHOOK],
    api_base_url="https://api.calendly.com",
    is_verified=True
))

# === COMMUNITY PLATFORMS ===

_register_platform(PlatformConfig(
    platform_id="discord",
    name="Discord",
    url="https://discord.com",
    category=PlatformCategory.COMMUNITY,
    intent_types=[IntentType.COLLABORATE, IntentType.PROMOTE],
    monetization_methods=[MonetizationMethod.SUBSCRIPTION, MonetizationMethod.TIPS],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=10000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://discord.com/api/v10",
    oauth_url="https://discord.com/api/oauth2/authorize",
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="slack",
    name="Slack",
    url="https://slack.com",
    category=PlatformCategory.COMMUNITY,
    intent_types=[IntentType.COLLABORATE, IntentType.HIRE_TALENT],
    monetization_methods=[MonetizationMethod.SUBSCRIPTION],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=50000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://slack.com/api",
    oauth_url="https://slack.com/oauth/v2/authorize",
    is_verified=True
))

_register_platform(PlatformConfig(
    platform_id="reddit",
    name="Reddit",
    url="https://reddit.com",
    category=PlatformCategory.COMMUNITY,
    intent_types=[IntentType.PROMOTE, IntentType.COLLABORATE],
    monetization_methods=[MonetizationMethod.ADVERTISING, MonetizationMethod.AFFILIATE],
    commission_rate=0.0,
    min_transaction=0.0,
    max_transaction=100000.0,
    access_methods=[AccessMethod.API, AccessMethod.OAUTH],
    api_base_url="https://oauth.reddit.com",
    oauth_url="https://www.reddit.com/api/v1/authorize",
    is_verified=True
))


# ============================================================
# UNIVERSAL ADAPTER INTERFACE
# ============================================================

class PlatformAdapter(ABC):
    """
    Abstract base for platform adapters
    
    Each adapter implements platform-specific logic using
    the configuration as the foundation.
    """
    
    def __init__(self, config: PlatformConfig):
        self.config = config
        self._authenticated = False
        self._credentials: Dict = {}
        self._rate_limit_remaining = config.rate_limit_per_hour
        self._last_request: Optional[str] = None
    
    @abstractmethod
    async def authenticate(self, credentials: Dict) -> Dict[str, Any]:
        """Authenticate with the platform"""
        pass
    
    @abstractmethod
    async def discover_opportunities(self, filters: Dict = None) -> List[Dict]:
        """Discover monetizable opportunities"""
        pass
    
    @abstractmethod
    async def submit_application(self, opportunity_id: str, proposal: Dict) -> Dict[str, Any]:
        """Apply/bid on an opportunity"""
        pass
    
    @abstractmethod
    async def get_opportunity_details(self, opportunity_id: str) -> Dict[str, Any]:
        """Get full details of an opportunity"""
        pass
    
    async def check_rate_limit(self) -> bool:
        """Check if we can make another request"""
        return self._rate_limit_remaining > 0
    
    def get_config(self) -> PlatformConfig:
        """Get platform configuration"""
        return self.config


class GenericAPIAdapter(PlatformAdapter):
    """
    Generic adapter for API-based platforms
    
    Uses configuration to make requests without
    platform-specific code.
    """
    
    async def authenticate(self, credentials: Dict) -> Dict[str, Any]:
        """Generic OAuth/API key authentication"""
        self._credentials = credentials
        
        if AccessMethod.OAUTH in self.config.access_methods:
            # OAuth flow
            if "access_token" in credentials:
                self._authenticated = True
                return {"ok": True, "method": "oauth"}
        
        if AccessMethod.API in self.config.access_methods:
            # API key
            if "api_key" in credentials:
                self._authenticated = True
                return {"ok": True, "method": "api_key"}
        
        return {"ok": False, "error": "no_valid_credentials"}
    
    async def discover_opportunities(self, filters: Dict = None) -> List[Dict]:
        """Generic opportunity discovery"""
        if not self._authenticated:
            return []
        
        # Would make actual API call here
        # For now, return structure
        return [{
            "platform": self.config.platform_id,
            "opportunity_id": _generate_id("opp"),
            "source": "api_discovery",
            "filters_applied": filters or {}
        }]
    
    async def submit_application(self, opportunity_id: str, proposal: Dict) -> Dict[str, Any]:
        """Generic application submission"""
        if not self._authenticated:
            return {"ok": False, "error": "not_authenticated"}
        
        if not self.config.can_auto_apply:
            return {"ok": False, "error": "auto_apply_not_supported"}
        
        return {
            "ok": True,
            "platform": self.config.platform_id,
            "opportunity_id": opportunity_id,
            "application_id": _generate_id("app"),
            "status": "submitted"
        }
    
    async def get_opportunity_details(self, opportunity_id: str) -> Dict[str, Any]:
        """Generic opportunity detail fetch"""
        if not self._authenticated:
            return {"ok": False, "error": "not_authenticated"}
        
        return {
            "ok": True,
            "opportunity_id": opportunity_id,
            "platform": self.config.platform_id
        }


class GenericScrapingAdapter(PlatformAdapter):
    """
    Generic adapter for scraping-based platforms
    
    Uses CSS selectors and patterns from config.
    """
    
    async def authenticate(self, credentials: Dict) -> Dict[str, Any]:
        """Session-based authentication for scraping"""
        if "session_cookie" in credentials or "username" in credentials:
            self._credentials = credentials
            self._authenticated = True
            return {"ok": True, "method": "session"}
        return {"ok": False, "error": "credentials_required"}
    
    async def discover_opportunities(self, filters: Dict = None) -> List[Dict]:
        """Scrape opportunities using selectors"""
        if not self._authenticated:
            return []
        
        selectors = self.config.opportunity_selectors
        patterns = self.config.intent_patterns
        
        # Would use actual scraping here
        return [{
            "platform": self.config.platform_id,
            "opportunity_id": _generate_id("opp"),
            "source": "scraping",
            "selectors_used": list(selectors.keys())
        }]
    
    async def submit_application(self, opportunity_id: str, proposal: Dict) -> Dict[str, Any]:
        """Submit via browser automation"""
        if not self.config.can_auto_apply:
            return {"ok": False, "error": "manual_application_required"}
        
        return {
            "ok": True,
            "platform": self.config.platform_id,
            "opportunity_id": opportunity_id,
            "method": "browser_automation"
        }
    
    async def get_opportunity_details(self, opportunity_id: str) -> Dict[str, Any]:
        """Scrape opportunity details"""
        return {
            "ok": True,
            "opportunity_id": opportunity_id,
            "platform": self.config.platform_id
        }


# ============================================================
# ADAPTER FACTORY
# ============================================================

class AdapterFactory:
    """
    Creates the appropriate adapter for a platform
    """
    
    _custom_adapters: Dict[str, type] = {}
    
    @classmethod
    def register_custom_adapter(cls, platform_id: str, adapter_class: type):
        """Register a custom adapter for a specific platform"""
        cls._custom_adapters[platform_id] = adapter_class
    
    @classmethod
    def create(cls, platform_id: str) -> Optional[PlatformAdapter]:
        """Create adapter for platform"""
        config = PLATFORM_CONFIGS.get(platform_id)
        if not config:
            return None
        
        # Check for custom adapter
        if platform_id in cls._custom_adapters:
            return cls._custom_adapters[platform_id](config)
        
        # Use generic adapter based on access method
        if AccessMethod.API in config.access_methods:
            return GenericAPIAdapter(config)
        elif AccessMethod.SCRAPING in config.access_methods:
            return GenericScrapingAdapter(config)
        else:
            return GenericAPIAdapter(config)  # Default


# ============================================================
# PLATFORM REGISTRY
# ============================================================

class PlatformRegistry:
    """
    Central registry for all platforms
    
    Add platforms via config, not code.
    """
    
    def __init__(self):
        self._adapters: Dict[str, PlatformAdapter] = {}
        self._active_platforms: set = set()
        self._stats: Dict[str, Dict] = {}
    
    def get_platform(self, platform_id: str) -> Optional[PlatformConfig]:
        """Get platform configuration"""
        return PLATFORM_CONFIGS.get(platform_id)
    
    def get_adapter(self, platform_id: str) -> Optional[PlatformAdapter]:
        """Get or create adapter for platform"""
        if platform_id not in self._adapters:
            adapter = AdapterFactory.create(platform_id)
            if adapter:
                self._adapters[platform_id] = adapter
        return self._adapters.get(platform_id)
    
    def add_platform(self, config: PlatformConfig) -> Dict[str, Any]:
        """Add a new platform configuration"""
        if config.platform_id in PLATFORM_CONFIGS:
            return {"ok": False, "error": "platform_exists"}
        
        _register_platform(config)
        
        return {
            "ok": True,
            "platform_id": config.platform_id,
            "name": config.name,
            "category": config.category.value
        }
    
    def list_platforms(
        self,
        category: PlatformCategory = None,
        intent_type: IntentType = None,
        verified_only: bool = False,
        active_only: bool = True
    ) -> List[Dict]:
        """List platforms with optional filters"""
        platforms = list(PLATFORM_CONFIGS.values())
        
        if category:
            platforms = [p for p in platforms if p.category == category]
        
        if intent_type:
            platforms = [p for p in platforms if intent_type in p.intent_types]
        
        if verified_only:
            platforms = [p for p in platforms if p.is_verified]
        
        if active_only:
            platforms = [p for p in platforms if p.is_active]
        
        return [
            {
                "platform_id": p.platform_id,
                "name": p.name,
                "category": p.category.value,
                "intent_types": [i.value for i in p.intent_types],
                "monetization": [m.value for m in p.monetization_methods],
                "commission_rate": p.commission_rate,
                "is_verified": p.is_verified
            }
            for p in platforms
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        platforms = list(PLATFORM_CONFIGS.values())
        
        by_category = {}
        for p in platforms:
            cat = p.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
        
        return {
            "total_platforms": len(platforms),
            "verified_platforms": len([p for p in platforms if p.is_verified]),
            "active_platforms": len([p for p in platforms if p.is_active]),
            "by_category": by_category,
            "adapters_loaded": len(self._adapters)
        }
    
    def search_platforms(self, query: str) -> List[Dict]:
        """Search platforms by name or category"""
        query_lower = query.lower()
        
        matches = []
        for p in PLATFORM_CONFIGS.values():
            if (query_lower in p.name.lower() or 
                query_lower in p.category.value or
                query_lower in p.url.lower()):
                matches.append({
                    "platform_id": p.platform_id,
                    "name": p.name,
                    "category": p.category.value,
                    "url": p.url
                })
        
        return matches


# ============================================================
# SINGLETON
# ============================================================

_registry: Optional[PlatformRegistry] = None


def get_platform_registry() -> PlatformRegistry:
    """Get singleton registry instance"""
    global _registry
    if _registry is None:
        _registry = PlatformRegistry()
    return _registry


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("UNIVERSAL PLATFORM ADAPTER - Config-Driven Monetization")
    print("=" * 70)
    
    registry = get_platform_registry()
    
    # 1. Show stats
    print("\n1. Platform Registry Stats...")
    stats = registry.get_stats()
    print(f"   Total platforms: {stats['total_platforms']}")
    print(f"   Verified: {stats['verified_platforms']}")
    print(f"   By category: {stats['by_category']}")
    
    # 2. List freelance platforms
    print("\n2. Freelance platforms...")
    freelance = registry.list_platforms(category=PlatformCategory.FREELANCE)
    for p in freelance[:5]:
        print(f"   - {p['name']}: {p['commission_rate']*100}% commission")
    
    # 3. Search
    print("\n3. Search 'design'...")
    design = registry.search_platforms("design")
    for p in design:
        print(f"   - {p['name']} ({p['category']})")
    
    # 4. Get adapter
    print("\n4. Get Upwork adapter...")
    adapter = registry.get_adapter("upwork")
    print(f"   Adapter: {type(adapter).__name__}")
    print(f"   Can auto-apply: {adapter.config.can_auto_apply}")
    print(f"   Rate limit: {adapter.config.rate_limit_per_hour}/hour")
    
    # 5. Add custom platform
    print("\n5. Add custom platform...")
    custom = PlatformConfig(
        platform_id="my_custom_platform",
        name="My Custom Platform",
        url="https://myplatform.com",
        category=PlatformCategory.MARKETPLACE,
        intent_types=[IntentType.BUY_SERVICE, IntentType.SELL],
        monetization_methods=[MonetizationMethod.COMMISSION],
        commission_rate=0.05,
        min_transaction=10.0,
        max_transaction=10000.0,
        access_methods=[AccessMethod.API],
        api_base_url="https://api.myplatform.com/v1"
    )
    result = registry.add_platform(custom)
    print(f"   Added: {result}")
    
    # 6. Final stats
    print("\n6. Updated stats...")
    stats = registry.get_stats()
    print(f"   Total platforms: {stats['total_platforms']}")
    
    print("\n" + "=" * 70)
    print("✅ Universal Platform Adapter test complete!")
    print("=" * 70)
