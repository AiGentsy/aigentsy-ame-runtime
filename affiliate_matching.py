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
    signal: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Match a purchase intent signal to affiliate offer(s).

    Args:
        signal: Signal from U-ACR with product_intent, text, price_range, etc.

    Returns:
        {
            "matched": True/False,
            "affiliate_links": [...],
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

    # Generate affiliate links
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
    avg_price = sum(price_range) / 2 if price_range else category["avg_price"]
    commission_rate = category["commission_rate"]
    conversion_prob = signal.get("conversion_prob", signal.get("conversion_prob_override", 0.05))
    expected_commission = avg_price * commission_rate * conversion_prob

    # Generate outreach template
    outreach_template = _generate_outreach_template(
        product_intent=product_intent,
        text=text,
        affiliate_link=affiliate_links[0]["url"] if affiliate_links else None,
        source=source
    )

    return {
        "matched": len(affiliate_links) > 0,
        "signal_id": signal_id,
        "product_intent": product_intent,
        "affiliate_links": affiliate_links,
        "outreach_template": outreach_template,
        "expected_commission": round(expected_commission, 2),
        "avg_order_value": avg_price,
        "commission_rate": commission_rate,
        "conversion_prob": conversion_prob,
        "tracking_id": tracking_id,
        "matched_at": _now()
    }


def _generate_outreach_template(
    product_intent: str,
    text: str,
    affiliate_link: str,
    source: str
) -> Dict[str, str]:
    """Generate outreach templates for different channels"""

    # Extract what they're looking for
    looking_for = product_intent.replace("_", " ").title()
    if looking_for == "General":
        looking_for = "what you're looking for"

    # Twitter DM template (concise)
    twitter_dm = f"""Hey! Saw you're looking for {looking_for}.

Found some great deals that might help: {affiliate_link}

Let me know if you need help finding something specific!"""

    # Email template (more detailed)
    email_subject = f"Found deals on {looking_for} for you"
    email_body = f"""Hi there,

I noticed you were looking for {looking_for} and wanted to help out.

I found some great options that match what you're looking for:
{affiliate_link}

The link above has curated results based on your search. If you need something more specific, just reply and I'll help narrow it down.

Happy shopping!

- AiGentsy"""

    # SMS template (very short)
    sms = f"Hey! Found great deals on {looking_for}: {affiliate_link}"

    return {
        "twitter_dm": twitter_dm,
        "email_subject": email_subject,
        "email_body": email_body,
        "sms": sms,
        "affiliate_link": affiliate_link
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
        "networks": {
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
        "conversion_stats": get_conversion_stats(),
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
        print("AFFILIATE MATCHING ENGINE TEST")
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

        print(f"\nMatch Result:")
        print(f"  Matched: {result['matched']}")
        print(f"  Expected Commission: ${result['expected_commission']}")
        print(f"  Tracking ID: {result['tracking_id']}")
        print(f"\nAffiliate Link: {result['affiliate_links'][0]['url'][:80]}...")
        print(f"\nTwitter DM Template:")
        print(result['outreach_template']['twitter_dm'])

        print("\n" + "=" * 80)
        print("Status:")
        print(get_affiliate_status())

    asyncio.run(test())
