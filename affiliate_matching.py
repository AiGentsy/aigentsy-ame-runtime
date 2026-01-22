"""
AFFILIATE MATCHING ENGINE FOR U-ACR
====================================

Captures $4.6T abandoned cart TAM via affiliate matching instead of Shopify.

FLOW:
1. Capture purchase intent signals from Twitter/Instagram (already working)
2. Match signals to affiliate products/offers
3. Generate trackable affiliate links
4. Send outreach via Twitter DM / Email / SMS
5. Track conversions and earn 3-15% commission

SUPPORTED AFFILIATE NETWORKS:
- Amazon Associates (AMAZON_AFFILIATE_TAG)
- ShareASale (SHAREASALE_AFFILIATE_ID)
- CJ Affiliate (CJ_AFFILIATE_ID)
- Impact (IMPACT_ACCOUNT_SID)
- Direct merchant programs

NO SHOPIFY REQUIRED - This is the matchmaker model.

Usage:
    from affiliate_matching import match_signal_to_affiliate, get_affiliate_status

    result = await match_signal_to_affiliate(signal)
    # Returns affiliate link + outreach template
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

# Auto-spawn storefront integration
SPAWNS_URL = os.getenv("SPAWNS_URL", "https://spawns.aigentsy.com")
AIGENTSY_URL = os.getenv("AIGENTSY_URL", "https://aigentsy.com")
AUTO_SPAWN_ENABLED = os.getenv("AUTO_SPAWN_STOREFRONTS", "true").lower() == "true"


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

    # Calculate expected commission
    # Storefront = higher margin (15-30% vs 3-8% affiliate)
    avg_price = sum(price_range) / 2 if price_range else category["avg_price"]
    conversion_prob = signal.get("conversion_prob", signal.get("conversion_prob_override", 0.05))

    if storefront:
        # AiGentsy storefront: higher margin (avg 20%)
        commission_rate = 0.20
        expected_commission = avg_price * commission_rate * conversion_prob
    else:
        # Affiliate: standard rates
        commission_rate = category["commission_rate"]
        expected_commission = avg_price * commission_rate * conversion_prob

    # Generate outreach template with storefront prioritized
    outreach_template = _generate_outreach_template(
        product_intent=product_intent,
        text=text,
        affiliate_link=affiliate_links[0]["url"] if affiliate_links else None,
        source=source,
        storefront_url=storefront_url
    )

    return {
        "matched": len(affiliate_links) > 0 or storefront is not None,
        "signal_id": signal_id,
        "product_intent": product_intent,
        "storefront": storefront,
        "affiliate_links": affiliate_links,
        "outreach_template": outreach_template,
        "expected_commission": round(expected_commission, 2),
        "avg_order_value": avg_price,
        "commission_rate": commission_rate,
        "conversion_prob": conversion_prob,
        "tracking_id": tracking_id,
        "channel": "storefront" if storefront else "affiliate",
        "matched_at": _now()
    }


def _generate_outreach_template(
    product_intent: str,
    text: str,
    affiliate_link: str,
    source: str,
    storefront_url: str = None
) -> Dict[str, str]:
    """
    Generate cool, smart, inviting outreach templates for different channels.

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

    # Twitter DM templates (rotate for variety) - casual, helpful vibe
    twitter_templates = [
        f"""yo - caught your post about {looking_for}

put together some options that might be exactly what you need: {main_link}

lmk if you want me to dig deeper on specs or deals""",

        f"""saw you're hunting for {hook}

curated a few solid picks here: {main_link}

hit me back if you need recs on specific features""",

        f"""quick heads up - noticed you're looking for {looking_for}

found some solid options worth checking: {main_link}

always down to help narrow it down if needed"""
    ]

    # Pick based on product intent hash for consistency
    import hashlib
    template_idx = int(hashlib.md5(product_intent.encode()).hexdigest(), 16) % len(twitter_templates)
    twitter_dm = twitter_templates[template_idx]

    # Email template - helpful but not pushy
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

- A"""

    # SMS template - super casual, value-first
    sms_templates = [
        f"found some solid {looking_for} options: {main_link} - lmk if you need help narrowing down",
        f"yo - {hook} options here: {main_link}",
        f"quick {looking_for} finds: {main_link} - hit me if you need more recs"
    ]
    sms = sms_templates[template_idx % len(sms_templates)]

    return {
        "twitter_dm": twitter_dm,
        "email_subject": email_subject,
        "email_body": email_body,
        "sms": sms,
        "affiliate_link": affiliate_link,
        "storefront_url": storefront_url,
        "main_link": main_link
    }


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH MATCHING
# ═══════════════════════════════════════════════════════════════════════════════

async def match_batch_signals(
    signals: List[Dict[str, Any]],
    min_expected_commission: float = 0.10
) -> Dict[str, Any]:
    """
    Match multiple signals to affiliate offers.
    Filters by minimum expected commission.
    """
    results = []
    total_expected = 0

    for signal in signals:
        match = await match_signal_to_affiliate(signal)

        if match["matched"] and match["expected_commission"] >= min_expected_commission:
            results.append(match)
            total_expected += match["expected_commission"]

    return {
        "ok": True,
        "signals_processed": len(signals),
        "signals_matched": len(results),
        "total_expected_commission": round(total_expected, 2),
        "matches": results,
        "processed_at": _now()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSION TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

# In-memory conversion tracking (would be persisted in production)
CONVERSION_TRACKING = {}


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
# STATUS & HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

def get_affiliate_status() -> Dict[str, Any]:
    """Get affiliate matching engine status"""
    return {
        "ok": True,
        "auto_spawn_storefronts": {
            "enabled": AUTO_SPAWN_ENABLED,
            "spawns_url": SPAWNS_URL,
            "commission_rate": "15-30% (owned channel)",
            "description": "Auto-spawns AiGentsy storefronts for purchase intent signals"
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
            "2. Auto-spawn AiGentsy storefront for niche (15-30% margin)",
            "3. Fallback to affiliate links (4-10% margin)",
            "4. Generate cool outreach templates",
            "5. Execute via Twitter DM / Email / SMS",
            "6. Track conversions and optimize"
        ],
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
        print("U-ACR AFFILIATE + STOREFRONT MATCHING ENGINE")
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

        print(f"\n{'='*40}")
        print("MATCH RESULT")
        print(f"{'='*40}")
        print(f"  Matched: {result['matched']}")
        print(f"  Channel: {result['channel']}")
        print(f"  Expected Commission: ${result['expected_commission']}")
        print(f"  Commission Rate: {result['commission_rate']*100:.0f}%")
        print(f"  Tracking ID: {result['tracking_id']}")

        if result.get('storefront'):
            print(f"\n{'='*40}")
            print("AUTO-SPAWNED STOREFRONT")
            print(f"{'='*40}")
            print(f"  Storefront URL: {result['storefront']['storefront_url']}")
            print(f"  Name: {result['storefront']['storefront_name']}")
            print(f"  Niche: {result['storefront']['niche']}")
            print(f"  Spawn ID: {result['storefront']['spawn_id']}")

        if result.get('affiliate_links'):
            print(f"\n{'='*40}")
            print("AFFILIATE FALLBACK")
            print(f"{'='*40}")
            print(f"  Amazon Link: {result['affiliate_links'][0]['url'][:60]}...")

        print(f"\n{'='*40}")
        print("OUTREACH TEMPLATES (cool, smart, inviting)")
        print(f"{'='*40}")
        print("\nTwitter DM:")
        print("-" * 40)
        print(result['outreach_template']['twitter_dm'])
        print("\nEmail Subject:", result['outreach_template']['email_subject'])
        print("\nSMS:")
        print("-" * 40)
        print(result['outreach_template']['sms'])

        print(f"\n{'='*80}")
        print("ENGINE STATUS")
        print(f"{'='*80}")
        status = get_affiliate_status()
        print(f"Auto-Spawn Storefronts: {'ENABLED' if status['auto_spawn_storefronts']['enabled'] else 'DISABLED'}")
        print(f"Spawns URL: {status['auto_spawn_storefronts']['spawns_url']}")
        print(f"Storefront Commission: {status['auto_spawn_storefronts']['commission_rate']}")
        print(f"\nMonetization Flow:")
        for step in status['monetization_flow']:
            print(f"  {step}")

    asyncio.run(test())
