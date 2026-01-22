"""
AFFILIATE MATCHING ENGINE FOR U-ACR
====================================

Captures $4.6T abandoned cart TAM via affiliate marketing storefronts.

AiGentsy storefronts are MARKETING FRONTS for affiliates - we don't hold inventory.
Revenue comes from affiliate commissions + user acquisition.

REVENUE STREAMS:
1. Affiliate Commissions (4-10% per sale)
   - Amazon Associates, ShareASale, CJ Affiliate, Impact
   - Curated storefronts drive traffic to affiliate links

2. AiGentsy Business-in-a-Box Acquisition (lifetime value)
   - Upsell signal sources to build their OWN AI-powered business
   - "This AI found you, matched products, sent outreach. Build your own business with it."
   - Convert deal-seekers into business owners using AiGentsy platform
   - User gets: discovery + marketing + fulfillment + execution (all automated)
   - AiGentsy gets: 2.8% + $0.28 per transaction + premiums

3. Referral Bonuses ($10-100 per signup)
   - Every outreach includes soft Business-in-a-Box CTA
   - Referral codes track attribution
   - Tiered bonuses: $10 Starter, $25 Pro, $50 Business, $100 Enterprise

4. Email Capture & Retargeting
   - Build audience for future campaigns
   - Cross-sell across niches

FLOW:
1. Capture purchase intent signals from Twitter/Instagram
2. Auto-spawn curated storefront (marketing landing page)
3. Generate affiliate links + AiGentsy upsell
4. Send cool outreach via Twitter DM / Email / SMS
5. Track: affiliate conversions + AiGentsy signups + referrals

NO INVENTORY. NO FULFILLMENT. Pure marketing arbitrage.

Usage:
    from affiliate_matching import match_signal_to_affiliate, get_affiliate_status

    result = await match_signal_to_affiliate(signal)
    # Returns affiliate link + outreach template + upsell CTA
"""

import os
import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode, quote_plus

# Affiliate network credentials
AMAZON_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "aigentsy-20")
SHAREASALE_AFFILIATE_ID = os.getenv("SHAREASALE_AFFILIATE_ID")
CJ_AFFILIATE_ID = os.getenv("CJ_AFFILIATE_ID")
IMPACT_ACCOUNT_SID = os.getenv("IMPACT_ACCOUNT_SID")

# Check availability
AMAZON_AVAILABLE = bool(AMAZON_AFFILIATE_TAG)
SHAREASALE_AVAILABLE = bool(SHAREASALE_AFFILIATE_ID)

# Auto-spawn storefront integration (marketing fronts, not inventory)
SPAWNS_URL = os.getenv("SPAWNS_URL", "https://spawns.aigentsy.com")
AIGENTSY_URL = os.getenv("AIGENTSY_URL", "https://aigentsy.com")
AUTO_SPAWN_ENABLED = os.getenv("AUTO_SPAWN_STOREFRONTS", "true").lower() == "true"

# ═══════════════════════════════════════════════════════════════════════════════
# AIGENTSY UPSELL & REFERRAL CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

# Referral bonus tiers (paid to referrer when referee signs up)
REFERRAL_BONUSES = {
    "free_signup": 0,        # Free tier signup - no bonus yet
    "starter": 10,           # $10 when referee upgrades to Starter
    "pro": 25,               # $25 when referee upgrades to Pro
    "business": 50,          # $50 when referee upgrades to Business
    "enterprise": 100,       # $100 for enterprise deals
}

# Revenue per converted AiGentsy user (lifetime value estimates)
AIGENTSY_USER_LTV = {
    "free": 0,
    "starter": 147,          # $49/mo * 3 months avg
    "pro": 594,              # $99/mo * 6 months avg
    "business": 2388,        # $199/mo * 12 months avg
}

# Upsell conversion rates (based on funnel stage)
UPSELL_CONVERSION_RATES = {
    "outreach_to_click": 0.08,       # 8% click the AiGentsy link
    "click_to_signup": 0.15,         # 15% of clickers sign up free
    "signup_to_paid": 0.12,          # 12% convert to paid
}

# Calculate expected value per outreach with AiGentsy upsell
def _calculate_upsell_ev() -> float:
    """Expected value of AiGentsy upsell per outreach"""
    click_rate = UPSELL_CONVERSION_RATES["outreach_to_click"]
    signup_rate = UPSELL_CONVERSION_RATES["click_to_signup"]
    paid_rate = UPSELL_CONVERSION_RATES["signup_to_paid"]
    avg_ltv = (AIGENTSY_USER_LTV["starter"] + AIGENTSY_USER_LTV["pro"]) / 2

    # EV = click_rate * signup_rate * paid_rate * avg_LTV
    return click_rate * signup_rate * paid_rate * avg_ltv

UPSELL_EV_PER_OUTREACH = _calculate_upsell_ev()  # ~$0.53 per outreach


def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


def _generate_tracking_id(signal_id: str, network: str) -> str:
    """Generate unique tracking ID for attribution"""
    raw = f"{signal_id}:{network}:{_now()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT CATEGORY MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

# Map detected product intents to affiliate search terms and categories
CATEGORY_MAPPING = {
    # Electronics
    "laptop": {
        "search_terms": ["laptop", "notebook computer", "macbook"],
        "amazon_category": "Computers",
        "commission_rate": 0.04,  # 4%
        "avg_price": 800
    },
    "phone": {
        "search_terms": ["smartphone", "iphone", "android phone"],
        "amazon_category": "Cell Phones",
        "commission_rate": 0.04,
        "avg_price": 600
    },
    "tablet": {
        "search_terms": ["tablet", "ipad"],
        "amazon_category": "Computers",
        "commission_rate": 0.04,
        "avg_price": 400
    },
    "camera": {
        "search_terms": ["camera", "dslr", "mirrorless camera"],
        "amazon_category": "Camera & Photo",
        "commission_rate": 0.04,
        "avg_price": 1200
    },
    "headphones": {
        "search_terms": ["headphones", "earbuds", "airpods"],
        "amazon_category": "Electronics",
        "commission_rate": 0.06,
        "avg_price": 150
    },
    "console": {
        "search_terms": ["gaming console", "playstation", "xbox", "nintendo switch"],
        "amazon_category": "Video Games",
        "commission_rate": 0.04,
        "avg_price": 450
    },
    "gpu": {
        "search_terms": ["graphics card", "nvidia rtx", "amd gpu"],
        "amazon_category": "Computers",
        "commission_rate": 0.04,
        "avg_price": 600
    },
    "monitor": {
        "search_terms": ["computer monitor", "gaming monitor", "4k display"],
        "amazon_category": "Computers",
        "commission_rate": 0.04,
        "avg_price": 350
    },

    # Fashion
    "sneakers": {
        "search_terms": ["sneakers", "running shoes", "athletic shoes"],
        "amazon_category": "Clothing, Shoes & Jewelry",
        "commission_rate": 0.07,
        "avg_price": 120
    },
    "watch": {
        "search_terms": ["watch", "smartwatch", "wristwatch"],
        "amazon_category": "Clothing, Shoes & Jewelry",
        "commission_rate": 0.07,
        "avg_price": 250
    },
    "bag": {
        "search_terms": ["handbag", "backpack", "messenger bag"],
        "amazon_category": "Clothing, Shoes & Jewelry",
        "commission_rate": 0.07,
        "avg_price": 150
    },

    # Collectibles
    "cards": {
        "search_terms": ["trading cards", "pokemon cards", "sports cards"],
        "amazon_category": "Toys & Games",
        "commission_rate": 0.08,
        "avg_price": 50
    },
    "vinyl": {
        "search_terms": ["vinyl records", "lp records"],
        "amazon_category": "Music",
        "commission_rate": 0.05,
        "avg_price": 30
    },
    "funko": {
        "search_terms": ["funko pop", "collectible figures"],
        "amazon_category": "Toys & Games",
        "commission_rate": 0.08,
        "avg_price": 15
    },

    # Home
    "furniture": {
        "search_terms": ["furniture", "desk", "chair", "sofa"],
        "amazon_category": "Home & Kitchen",
        "commission_rate": 0.08,
        "avg_price": 400
    },
    "appliance": {
        "search_terms": ["home appliance", "kitchen appliance"],
        "amazon_category": "Home & Kitchen",
        "commission_rate": 0.06,
        "avg_price": 300
    },

    # Services/Digital
    "software": {
        "search_terms": ["software", "subscription"],
        "amazon_category": "Software",
        "commission_rate": 0.10,
        "avg_price": 100
    },
    "tickets": {
        "search_terms": ["event tickets", "concert tickets"],
        "amazon_category": None,  # Not on Amazon - use StubHub affiliate
        "commission_rate": 0.08,
        "avg_price": 150
    },

    # General fallback
    "general": {
        "search_terms": [""],
        "amazon_category": None,
        "commission_rate": 0.05,
        "avg_price": 100
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-SPAWN STOREFRONT INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

# Category to auto-spawn niche mapping
CATEGORY_TO_NICHE = {
    "laptop": "tech_gear",
    "phone": "mobile_tech",
    "tablet": "mobile_tech",
    "camera": "photo_video",
    "headphones": "audio_gear",
    "console": "gaming",
    "gpu": "pc_builds",
    "monitor": "workspace",
    "sneakers": "streetwear",
    "watch": "accessories",
    "bag": "accessories",
    "cards": "collectibles",
    "vinyl": "collectibles",
    "funko": "collectibles",
    "furniture": "home_office",
    "appliance": "home_tech",
    "software": "digital_tools",
    "tickets": "experiences",
    "general": "curated_finds"
}


async def spawn_storefront_for_signal(
    signal: Dict[str, Any],
    product_intent: str
) -> Optional[Dict[str, Any]]:
    """
    Auto-spawn an AiGentsy storefront for a purchase intent signal.

    Creates a dedicated micro-storefront with curated products for the niche,
    instead of just sending to Amazon.

    Returns storefront details or None if spawning disabled/failed.
    """
    if not AUTO_SPAWN_ENABLED:
        return None

    try:
        # Import auto-spawn engine
        from auto_spawn_engine import BusinessSpawner, TrendSignal, NicheCategory

        signal_id = signal.get("signal_id", signal.get("id", "unknown"))
        niche = CATEGORY_TO_NICHE.get(product_intent, "curated_finds")

        # Map to auto-spawn category
        niche_to_category = {
            "tech_gear": NicheCategory.ECOMMERCE,
            "mobile_tech": NicheCategory.ECOMMERCE,
            "photo_video": NicheCategory.ECOMMERCE,
            "audio_gear": NicheCategory.ECOMMERCE,
            "gaming": NicheCategory.ECOMMERCE,
            "pc_builds": NicheCategory.ECOMMERCE,
            "workspace": NicheCategory.ECOMMERCE,
            "streetwear": NicheCategory.ECOMMERCE,
            "accessories": NicheCategory.ECOMMERCE,
            "collectibles": NicheCategory.ECOMMERCE,
            "home_office": NicheCategory.ECOMMERCE,
            "home_tech": NicheCategory.ECOMMERCE,
            "digital_tools": NicheCategory.SAAS_MICRO,
            "experiences": NicheCategory.CONTENT,
            "curated_finds": NicheCategory.ECOMMERCE
        }

        category = niche_to_category.get(niche, NicheCategory.ECOMMERCE)

        # Create trend signal from purchase intent
        trend_signal = TrendSignal(
            signal_id=f"uacr_{signal_id}",
            source="u-acr",
            query=signal.get("text", product_intent)[:200],
            category=category,
            demand_score=85.0,
            competition_score=40.0,
            monetization_potential=90.0,
            urgency=80.0,
            viral_potential=60.0,
            raw_data=signal,
            detected_at=_now()
        )

        # Spawn the storefront
        spawner = BusinessSpawner()
        business = await spawner.spawn_from_signal(trend_signal)

        return {
            "spawned": True,
            "storefront_url": business.landing_page_url,
            "storefront_name": business.name,
            "spawn_id": business.spawn_id,
            "referral_code": business.referral_code,
            "niche": niche,
            "category": category.value,
            "spawned_at": business.spawned_at
        }

    except ImportError:
        # Auto-spawn engine not available
        return None
    except Exception as e:
        print(f"Storefront spawn failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# AFFILIATE LINK GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_amazon_search_link(
    search_term: str,
    tracking_id: str
) -> str:
    """Generate Amazon affiliate search link"""
    params = {
        "k": search_term,
        "tag": AMAZON_AFFILIATE_TAG,
        "ref": f"aigentsy_{tracking_id}"
    }
    return f"https://www.amazon.com/s?{urlencode(params)}"


def generate_amazon_product_link(
    asin: str,
    tracking_id: str
) -> str:
    """Generate Amazon affiliate product link"""
    return f"https://www.amazon.com/dp/{asin}?tag={AMAZON_AFFILIATE_TAG}&ref=aigentsy_{tracking_id}"


def generate_shareasale_link(
    merchant_id: str,
    product_url: str,
    tracking_id: str
) -> str:
    """Generate ShareASale affiliate link"""
    if not SHAREASALE_AFFILIATE_ID:
        return product_url

    encoded_url = quote_plus(product_url)
    return f"https://www.shareasale.com/r.cfm?b={merchant_id}&u={SHAREASALE_AFFILIATE_ID}&m={merchant_id}&urllink={encoded_url}&afftrack={tracking_id}"


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNAL MATCHING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

async def match_signal_to_affiliate(
    signal: Dict[str, Any],
    spawn_storefront: bool = True
) -> Dict[str, Any]:
    """
    Match a purchase intent signal to affiliate offer(s) and optionally spawn an AiGentsy storefront.

    Args:
        signal: Signal from U-ACR with product_intent, text, price_range, etc.
        spawn_storefront: If True, auto-spawn an AiGentsy storefront for this signal

    Returns:
        {
            "matched": True/False,
            "affiliate_links": [...],
            "storefront": {...} or None,
            "outreach_template": "...",
            "expected_commission": float,
            "tracking_id": str
        }
    """
    signal_id = signal.get("signal_id", signal.get("id", "unknown"))
    product_intent = signal.get("product_intent", "general")
    text = signal.get("text", "")
    price_range = signal.get("price_range", [100, 1000])
    source = signal.get("source", "unknown")
    user_id = signal.get("user_id", "")

    # Get category mapping
    category = CATEGORY_MAPPING.get(product_intent, CATEGORY_MAPPING["general"])

    # Generate tracking ID
    tracking_id = _generate_tracking_id(signal_id, "amazon")

    # Try to spawn AiGentsy storefront first (higher margin, owned channel)
    storefront = None
    storefront_url = None
    if spawn_storefront and AUTO_SPAWN_ENABLED:
        storefront = await spawn_storefront_for_signal(signal, product_intent)
        if storefront and storefront.get("spawned"):
            storefront_url = storefront.get("storefront_url")

    # Generate affiliate links as backup/complement
    affiliate_links = []

    # Primary: Amazon search link
    if category["search_terms"] and category["search_terms"][0]:
        search_term = category["search_terms"][0]

        # Try to extract specific product from signal text
        if text:
            # Use first 50 chars of signal as search refinement
            text_snippet = text[:50].replace("\n", " ").strip()
            if len(text_snippet) > 10:
                search_term = text_snippet

        amazon_link = generate_amazon_search_link(search_term, tracking_id)
        affiliate_links.append({
            "network": "amazon",
            "url": amazon_link,
            "type": "search",
            "commission_rate": category["commission_rate"]
        })

    # Calculate expected revenue (affiliate commission is always 4-10%, storefronts are marketing fronts)
    avg_price = sum(price_range) / 2 if price_range else category["avg_price"]
    conversion_prob = signal.get("conversion_prob", signal.get("conversion_prob_override", 0.05))

    # Affiliate commission (storefront just provides better UX, same affiliate backend)
    commission_rate = category["commission_rate"]
    affiliate_commission = avg_price * commission_rate * conversion_prob

    # AiGentsy upsell expected value (user acquisition)
    upsell_ev = UPSELL_EV_PER_OUTREACH  # ~$0.53 per outreach

    # Total expected value = affiliate commission + upsell EV
    total_expected_value = affiliate_commission + upsell_ev

    # Generate referral code for this outreach
    referral_code = f"UACR-{tracking_id[:8].upper()}"
    aigentsy_signup_link = f"{AIGENTSY_URL}/start?ref={referral_code}"

    # Generate outreach template with storefront + upsell
    outreach_template = _generate_outreach_template(
        product_intent=product_intent,
        text=text,
        affiliate_link=affiliate_links[0]["url"] if affiliate_links else None,
        source=source,
        storefront_url=storefront_url,
        aigentsy_link=aigentsy_signup_link,
        referral_code=referral_code
    )

    return {
        "matched": len(affiliate_links) > 0 or storefront is not None,
        "signal_id": signal_id,
        "product_intent": product_intent,
        "storefront": storefront,
        "affiliate_links": affiliate_links,
        "outreach_template": outreach_template,
        "revenue_breakdown": {
            "affiliate_commission": round(affiliate_commission, 2),
            "upsell_ev": round(upsell_ev, 2),
            "total_expected": round(total_expected_value, 2)
        },
        "avg_order_value": avg_price,
        "commission_rate": commission_rate,
        "conversion_prob": conversion_prob,
        "tracking_id": tracking_id,
        "referral_code": referral_code,
        "aigentsy_signup_link": aigentsy_signup_link,
        "channel": "storefront" if storefront else "affiliate",
        "matched_at": _now()
    }


def _generate_outreach_template(
    product_intent: str,
    text: str,
    affiliate_link: str,
    source: str,
    storefront_url: str = None,
    aigentsy_link: str = None,
    referral_code: str = None
) -> Dict[str, str]:
    """
    Generate cool, smart, inviting outreach templates for different channels.

    Includes:
    - Product recommendation (affiliate link)
    - Soft AiGentsy upsell (become a user, start your own storefront)
    - Referral tracking

    The vibe: helpful friend who found exactly what you need, not a salesperson.
    """

    # Extract what they're looking for with style
    looking_for = product_intent.replace("_", " ").title()
    if looking_for == "General":
        looking_for = "what you mentioned"

    # Use storefront if available, otherwise affiliate link
    main_link = storefront_url or affiliate_link

    # Cool category-specific hooks
    category_hooks = {
        "laptop": "the perfect setup",
        "phone": "that upgrade",
        "camera": "gear that actually slaps",
        "headphones": "audio that hits different",
        "console": "the gaming setup",
        "sneakers": "heat for the collection",
        "watch": "that piece",
        "cards": "some fire pulls",
        "gpu": "the build upgrade",
        "monitor": "screen real estate",
        "furniture": "the space upgrade",
        "software": "tools that actually work",
        "general": "what you're after"
    }

    hook = category_hooks.get(product_intent, "exactly what you need")

    # AiGentsy Business-in-a-Box upsell CTAs (soft, value-focused)
    # Goal: Convert deal-seekers into business owners using AiGentsy platform
    upsell_ctas = [
        f"ps - this runs on AI that finds opportunities + handles fulfillment automatically. you can build your own business with it: {aigentsy_link}",
        f"btw an AI did all this - discovery, curation, outreach. you can spin up your own biz using the same system: {aigentsy_link}",
        f"fun fact: AI found you, matched products, and sent this. want to run your own? takes 10 min to set up: {aigentsy_link}",
    ]

    # Pick based on product intent hash for consistency
    template_idx = int(hashlib.md5(product_intent.encode()).hexdigest(), 16) % 3

    # Twitter DM templates - casual, helpful vibe + soft upsell
    twitter_templates = [
        f"""yo - caught your post about {looking_for}

put together some options that might be exactly what you need: {main_link}

lmk if you want me to dig deeper on specs or deals

{upsell_ctas[0]}""",

        f"""saw you're hunting for {hook}

curated a few solid picks here: {main_link}

hit me back if you need recs on specific features

{upsell_ctas[1]}""",

        f"""quick heads up - noticed you're looking for {looking_for}

found some solid options worth checking: {main_link}

always down to help narrow it down if needed

{upsell_ctas[2]}"""
    ]

    twitter_dm = twitter_templates[template_idx]

    # Email template - helpful with clear upsell section
    email_subject_options = [
        f"Found {hook} for you",
        f"Re: {looking_for} - options inside",
        f"Quick find: {looking_for}"
    ]
    email_subject = email_subject_options[template_idx % len(email_subject_options)]

    email_body = f"""Hey,

Saw your post about {looking_for} and wanted to pass along some options I found.

Here's what I put together: {main_link}

The picks are curated based on what you mentioned - mix of value and quality. If any of those hit, let me know and I can dig into reviews, compare specs, or find better deals.

No pressure either way - just figured I'd share since I was already looking.

---

Quick backstory: an AI found your post, matched products, wrote this email, and will handle any follow-up. I just set it up once.

Some people use this same system to run their own business - AI handles discovery, marketing, fulfillment, everything. You just pick a niche and collect margin.

If that sounds interesting: {aigentsy_link}

Takes about 10 minutes to set up. No inventory, no employees, runs 24/7.

Referral code if you try it: {referral_code}

- A"""

    # SMS template - super casual, value-first (no upsell in SMS, too long)
    sms_templates = [
        f"found some solid {looking_for} options: {main_link} - lmk if you need help narrowing down",
        f"yo - {hook} options here: {main_link}",
        f"quick {looking_for} finds: {main_link} - hit me if you need more recs"
    ]
    sms = sms_templates[template_idx % len(sms_templates)]

    # Follow-up upsell message (for second touch) - Business in a Box pitch
    followup_upsell = f"""hey - hope those {looking_for} options worked out

random thought: you know how i found you + sent curated options automatically?

that's all AI - discovery, matching, outreach, even fulfillment. runs 24/7.

some people use the same system to run their own business:
- picks a niche you care about
- finds customers automatically
- handles marketing + delivery
- you just collect the margin

takes like 10 min to set up. no inventory, no employees.

if you're curious: {aigentsy_link}

not for everyone but figured i'd mention since you were already shopping"""

    return {
        "twitter_dm": twitter_dm,
        "email_subject": email_subject,
        "email_body": email_body,
        "sms": sms,
        "followup_upsell": followup_upsell,
        "affiliate_link": affiliate_link,
        "storefront_url": storefront_url,
        "main_link": main_link,
        "aigentsy_link": aigentsy_link,
        "referral_code": referral_code
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH MATCHING
# ═══════════════════════════════════════════════════════════════════════════════

async def match_batch_signals(
    signals: List[Dict[str, Any]],
    min_expected_value: float = 0.10
) -> Dict[str, Any]:
    """
    Match multiple signals to affiliate offers + upsells.
    Filters by minimum expected value (affiliate + upsell EV).
    """
    results = []
    total_affiliate = 0
    total_upsell_ev = 0

    for signal in signals:
        match = await match_signal_to_affiliate(signal)

        if match["matched"]:
            rev = match.get("revenue_breakdown", {})
            total_ev = rev.get("total_expected", 0)

            if total_ev >= min_expected_value:
                results.append(match)
                total_affiliate += rev.get("affiliate_commission", 0)
                total_upsell_ev += rev.get("upsell_ev", 0)

    return {
        "ok": True,
        "signals_processed": len(signals),
        "signals_matched": len(results),
        "revenue_projection": {
            "affiliate_commissions": round(total_affiliate, 2),
            "upsell_ev": round(total_upsell_ev, 2),
            "total_expected": round(total_affiliate + total_upsell_ev, 2)
        },
        "matches": results,
        "processed_at": _now()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSION & REFERRAL TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

# In-memory tracking (would be persisted in production)
CONVERSION_TRACKING = {}
REFERRAL_TRACKING = {}
AIGENTSY_SIGNUPS = {}


def track_click(tracking_id: str, signal_id: str, network: str) -> None:
    """Track affiliate link click"""
    if tracking_id not in CONVERSION_TRACKING:
        CONVERSION_TRACKING[tracking_id] = {
            "signal_id": signal_id,
            "network": network,
            "clicked_at": _now(),
            "converted": False,
            "commission": 0
        }
    CONVERSION_TRACKING[tracking_id]["clicks"] = CONVERSION_TRACKING[tracking_id].get("clicks", 0) + 1


def track_conversion(tracking_id: str, commission: float) -> None:
    """Track affiliate conversion"""
    if tracking_id in CONVERSION_TRACKING:
        CONVERSION_TRACKING[tracking_id]["converted"] = True
        CONVERSION_TRACKING[tracking_id]["commission"] = commission
        CONVERSION_TRACKING[tracking_id]["converted_at"] = _now()


def get_conversion_stats() -> Dict[str, Any]:
    """Get conversion statistics"""
    total_clicks = sum(t.get("clicks", 0) for t in CONVERSION_TRACKING.values())
    total_conversions = sum(1 for t in CONVERSION_TRACKING.values() if t.get("converted"))
    total_commission = sum(t.get("commission", 0) for t in CONVERSION_TRACKING.values())

    return {
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "total_commission": total_commission,
        "conversion_rate": total_conversions / total_clicks if total_clicks > 0 else 0,
        "tracking_ids": len(CONVERSION_TRACKING)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# REFERRAL & UPSELL TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

def track_aigentsy_click(referral_code: str, signal_id: str) -> None:
    """Track click on AiGentsy signup link"""
    if referral_code not in REFERRAL_TRACKING:
        REFERRAL_TRACKING[referral_code] = {
            "signal_id": signal_id,
            "clicks": 0,
            "signups": 0,
            "upgrades": 0,
            "bonus_earned": 0,
            "first_click": _now()
        }
    REFERRAL_TRACKING[referral_code]["clicks"] += 1
    REFERRAL_TRACKING[referral_code]["last_click"] = _now()


def track_aigentsy_signup(referral_code: str, user_email: str, plan: str = "free") -> Dict[str, Any]:
    """Track AiGentsy signup from referral"""
    if referral_code not in REFERRAL_TRACKING:
        REFERRAL_TRACKING[referral_code] = {
            "clicks": 0,
            "signups": 0,
            "upgrades": 0,
            "bonus_earned": 0
        }

    REFERRAL_TRACKING[referral_code]["signups"] += 1

    signup_id = f"signup_{hashlib.md5(user_email.encode()).hexdigest()[:8]}"
    AIGENTSY_SIGNUPS[signup_id] = {
        "referral_code": referral_code,
        "email": user_email,
        "plan": plan,
        "signed_up_at": _now(),
        "upgraded": False
    }

    # Calculate bonus if paid plan
    bonus = REFERRAL_BONUSES.get(plan, 0)
    if bonus > 0:
        REFERRAL_TRACKING[referral_code]["upgrades"] += 1
        REFERRAL_TRACKING[referral_code]["bonus_earned"] += bonus

    return {
        "signup_id": signup_id,
        "referral_code": referral_code,
        "plan": plan,
        "bonus_earned": bonus
    }


def track_aigentsy_upgrade(signup_id: str, new_plan: str) -> Dict[str, Any]:
    """Track when a referred user upgrades their plan"""
    if signup_id not in AIGENTSY_SIGNUPS:
        return {"ok": False, "error": "Signup not found"}

    signup = AIGENTSY_SIGNUPS[signup_id]
    old_plan = signup["plan"]
    referral_code = signup["referral_code"]

    # Calculate bonus difference
    old_bonus = REFERRAL_BONUSES.get(old_plan, 0)
    new_bonus = REFERRAL_BONUSES.get(new_plan, 0)
    bonus_delta = max(0, new_bonus - old_bonus)

    # Update tracking
    signup["plan"] = new_plan
    signup["upgraded"] = True
    signup["upgraded_at"] = _now()

    if referral_code in REFERRAL_TRACKING and bonus_delta > 0:
        REFERRAL_TRACKING[referral_code]["upgrades"] += 1
        REFERRAL_TRACKING[referral_code]["bonus_earned"] += bonus_delta

    return {
        "ok": True,
        "signup_id": signup_id,
        "old_plan": old_plan,
        "new_plan": new_plan,
        "bonus_earned": bonus_delta,
        "referral_code": referral_code
    }


def get_referral_stats() -> Dict[str, Any]:
    """Get referral program statistics"""
    total_clicks = sum(r.get("clicks", 0) for r in REFERRAL_TRACKING.values())
    total_signups = sum(r.get("signups", 0) for r in REFERRAL_TRACKING.values())
    total_upgrades = sum(r.get("upgrades", 0) for r in REFERRAL_TRACKING.values())
    total_bonus = sum(r.get("bonus_earned", 0) for r in REFERRAL_TRACKING.values())

    return {
        "total_referral_clicks": total_clicks,
        "total_signups": total_signups,
        "total_paid_upgrades": total_upgrades,
        "total_bonus_earned": total_bonus,
        "click_to_signup_rate": total_signups / total_clicks if total_clicks > 0 else 0,
        "signup_to_paid_rate": total_upgrades / total_signups if total_signups > 0 else 0,
        "active_referral_codes": len(REFERRAL_TRACKING),
        "total_aigentsy_users": len(AIGENTSY_SIGNUPS)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS & HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

def get_affiliate_status() -> Dict[str, Any]:
    """Get affiliate matching engine status"""
    return {
        "ok": True,
        "business_model": "MARKETING FRONTS - No inventory, pure affiliate arbitrage + user acquisition",
        "revenue_streams": {
            "affiliate_commissions": {
                "rate": "4-10% per sale",
                "networks": ["Amazon Associates", "ShareASale", "CJ Affiliate"],
                "description": "Curated storefronts drive traffic to affiliate links"
            },
            "business_in_a_box_acquisition": {
                "upsell_ev_per_outreach": f"${UPSELL_EV_PER_OUTREACH:.2f}",
                "conversion_funnel": UPSELL_CONVERSION_RATES,
                "user_ltv": AIGENTSY_USER_LTV,
                "description": "Convert deal-seekers into Business-in-a-Box owners",
                "user_gets": "AI-powered discovery + marketing + fulfillment + execution",
                "aigentsy_gets": "2.8% + $0.28 per transaction + premiums"
            },
            "referral_bonuses": {
                "tiers": REFERRAL_BONUSES,
                "description": "Bonus paid when referred user upgrades to paid plan"
            }
        },
        "auto_spawn_storefronts": {
            "enabled": AUTO_SPAWN_ENABLED,
            "spawns_url": SPAWNS_URL,
            "purpose": "Marketing landing pages (not inventory)",
            "benefit": "Better UX, email capture, brand control, upsell opportunity"
        },
        "affiliate_networks": {
            "amazon": {
                "available": AMAZON_AVAILABLE,
                "tag": AMAZON_AFFILIATE_TAG if AMAZON_AVAILABLE else None,
                "commission_rates": "4-10% depending on category"
            },
            "shareasale": {
                "available": SHAREASALE_AVAILABLE,
                "affiliate_id": SHAREASALE_AFFILIATE_ID if SHAREASALE_AVAILABLE else None
            },
            "cj": {
                "available": bool(CJ_AFFILIATE_ID),
                "affiliate_id": CJ_AFFILIATE_ID if CJ_AFFILIATE_ID else None
            }
        },
        "categories_supported": list(CATEGORY_MAPPING.keys()),
        "niche_mapping": CATEGORY_TO_NICHE,
        "conversion_stats": get_conversion_stats(),
        "monetization_flow": [
            "1. Capture purchase intent signal from Twitter/Instagram",
            "2. Auto-spawn marketing storefront (curated landing page)",
            "3. Generate affiliate links (4-10% commission)",
            "4. Add soft AiGentsy upsell to outreach",
            "5. Execute via Twitter DM / Email / SMS",
            "6. Track: affiliate conversions + AiGentsy signups + referrals",
            "7. Follow-up with upsell for non-converters"
        ],
        "expected_value_per_outreach": {
            "affiliate_commission": "~$2-5 (varies by product)",
            "upsell_ev": f"~${UPSELL_EV_PER_OUTREACH:.2f}",
            "total": "~$2.50-5.50 per outreach"
        },
        "status": "operational"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_affiliate_matching(app):
    """Add affiliate matching endpoints to FastAPI app"""

    from fastapi import Body

    @app.get("/affiliate/status")
    async def affiliate_status():
        """Get affiliate matching engine status"""
        return get_affiliate_status()

    @app.post("/affiliate/match-signal")
    async def match_single_signal(signal: Dict = Body(...)):
        """Match a single signal to affiliate offers"""
        return await match_signal_to_affiliate(signal)

    @app.post("/affiliate/match-batch")
    async def match_batch(body: Dict = Body(...)):
        """
        Match batch of signals to affiliate offers.

        Body:
            signals: List of signals
            min_commission: Minimum expected commission (default 0.10)
        """
        signals = body.get("signals", [])
        min_commission = body.get("min_commission", 0.10)
        return await match_batch_signals(signals, min_commission)

    @app.post("/affiliate/process-live-signals")
    async def process_live_signals(body: Dict = Body(default={})):
        """
        Process all live U-ACR signals through affiliate matching.
        Returns matched signals with affiliate links ready for outreach.
        """
        try:
            from v111_gapharvester_ii import UACR_SIGNALS

            # Get all unprocessed signals
            signals = list(UACR_SIGNALS.values())

            if not signals:
                return {"ok": True, "message": "No signals to process", "matched": 0}

            # Match to affiliates
            min_commission = body.get("min_commission", 0.05)
            result = await match_batch_signals(signals, min_commission)

            return result

        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/affiliate/conversions")
    async def get_conversions():
        """Get conversion tracking stats"""
        return get_conversion_stats()

    print("=" * 80)
    print("🔗 AFFILIATE MATCHING ENGINE LOADED")
    print("=" * 80)
    print(f"Amazon Associates: {'✅' if AMAZON_AVAILABLE else '❌'} (tag: {AMAZON_AFFILIATE_TAG})")
    print(f"ShareASale: {'✅' if SHAREASALE_AVAILABLE else '❌'}")
    print(f"Categories: {len(CATEGORY_MAPPING)} product types supported")
    print("=" * 80)
    print("Endpoints:")
    print("  GET  /affiliate/status")
    print("  POST /affiliate/match-signal")
    print("  POST /affiliate/match-batch")
    print("  POST /affiliate/process-live-signals")
    print("  GET  /affiliate/conversions")
    print("=" * 80)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio

    async def test():
        print("=" * 80)
        print("U-ACR AFFILIATE MARKETING ENGINE")
        print("Marketing Fronts + Affiliate Arbitrage + User Acquisition")
        print("=" * 80)

        # Test signal
        test_signal = {
            "signal_id": "uacr_test123",
            "product_intent": "camera",
            "text": "Looking to buy a Sony A7IV mirrorless camera",
            "price_range": [2000, 3000],
            "source": "twitter",
            "conversion_prob": 0.10
        }

        print(f"\nTest Signal: {test_signal['text']}")
        print(f"Product Intent: {test_signal['product_intent']}")

        result = await match_signal_to_affiliate(test_signal)

        print(f"\n{'='*60}")
        print("REVENUE BREAKDOWN (per outreach)")
        print(f"{'='*60}")
        rev = result.get('revenue_breakdown', {})
        print(f"  Affiliate Commission (4-10%):  ${rev.get('affiliate_commission', 0):.2f}")
        print(f"  AiGentsy Upsell EV:            ${rev.get('upsell_ev', 0):.2f}")
        print(f"  ─────────────────────────────────────")
        print(f"  TOTAL EXPECTED VALUE:          ${rev.get('total_expected', 0):.2f}")

        print(f"\n{'='*60}")
        print("TRACKING & REFERRAL")
        print(f"{'='*60}")
        print(f"  Tracking ID:       {result['tracking_id']}")
        print(f"  Referral Code:     {result['referral_code']}")
        print(f"  AiGentsy Signup:   {result['aigentsy_signup_link']}")

        if result.get('storefront'):
            print(f"\n{'='*60}")
            print("AUTO-SPAWNED STOREFRONT (Marketing Front)")
            print(f"{'='*60}")
            print(f"  URL:    {result['storefront']['storefront_url']}")
            print(f"  Name:   {result['storefront']['storefront_name']}")
            print(f"  Niche:  {result['storefront']['niche']}")
            print(f"  NOTE:   No inventory - links to affiliate products")

        print(f"\n{'='*60}")
        print("OUTREACH TEMPLATES")
        print(f"{'='*60}")
        print("\n[Twitter DM - with soft upsell]")
        print("-" * 50)
        print(result['outreach_template']['twitter_dm'])

        print("\n[Follow-up Upsell Message]")
        print("-" * 50)
        print(result['outreach_template']['followup_upsell'])

        print(f"\n{'='*60}")
        print("REVENUE MODEL")
        print(f"{'='*60}")
        status = get_affiliate_status()
        print("\nRevenue Streams:")
        for stream, details in status['revenue_streams'].items():
            print(f"\n  {stream.upper()}:")
            if isinstance(details, dict):
                for k, v in details.items():
                    if k != 'description':
                        print(f"    {k}: {v}")

        print(f"\n{'='*60}")
        print("REFERRAL BONUS TIERS")
        print(f"{'='*60}")
        for plan, bonus in REFERRAL_BONUSES.items():
            if bonus > 0:
                print(f"  {plan.title()}: ${bonus} when referee upgrades")

        print(f"\nUpsell EV per outreach: ${UPSELL_EV_PER_OUTREACH:.2f}")
        print(f"(Based on {UPSELL_CONVERSION_RATES['outreach_to_click']*100:.0f}% click -> "
              f"{UPSELL_CONVERSION_RATES['click_to_signup']*100:.0f}% signup -> "
              f"{UPSELL_CONVERSION_RATES['signup_to_paid']*100:.0f}% paid)")

    asyncio.run(test())
