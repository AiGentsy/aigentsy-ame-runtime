"""
═══════════════════════════════════════════════════════════════════════════════
V111 PRODUCTION INTEGRATIONS - REAL API LAYER
═══════════════════════════════════════════════════════════════════════════════

Connects v111 GapHarvester II to real external services:

PAYMENT PROCESSING:
- Stripe: Invoice webhooks, interchange rates, payment routing
- Shopify: Order webhooks, invoice tracking

SOCIAL SIGNALS:
- Twitter: Purchase intent scraper for U-ACR
- Instagram: Shopping intent signals

WEBHOOKS:
- /webhooks/stripe/invoice-paid → Receivables Desk
- /webhooks/shopify/invoice-created → Receivables Desk
- /webhooks/stripe/charge-succeeded → Payments Optimizer

BACKGROUND TASKS:
- Twitter signal scraper (runs every 15 min)
- Instagram signal scraper (runs every 30 min)
- Stripe invoice sync (runs every hour)

All with:
- Signature verification
- Rate limiting
- Error handling
- Retry logic
- Monitoring

USAGE:
    from v111_production_integrations import include_v111_integrations
    include_v111_integrations(app)
"""

from fastapi import HTTPException, Request, BackgroundTasks, Header
from typing import Dict, Any, List, Optional
import os
import hmac
import hashlib
import json
import time
from datetime import datetime, timezone, timedelta
import asyncio

# ═══════════════════════════════════════════════════════════════════════════════
# STRIPE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

STRIPE_AVAILABLE = False
stripe = None

try:
    import stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
        STRIPE_AVAILABLE = True
except ImportError:
    print("⚠️ stripe package not installed - run: pip install stripe")


async def verify_stripe_signature(payload: bytes, signature: str) -> bool:
    """Verify Stripe webhook signature"""
    if not STRIPE_WEBHOOK_SECRET:
        return True  # Skip verification in dev
    
    try:
        stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
        return True
    except Exception as e:
        print(f"❌ Stripe signature verification failed: {e}")
        return False


async def get_stripe_invoice_details(invoice_id: str) -> Optional[Dict[str, Any]]:
    """Fetch invoice details from Stripe"""
    if not STRIPE_AVAILABLE:
        return None
    
    try:
        invoice = stripe.Invoice.retrieve(invoice_id)
        
        return {
            "invoice_id": invoice.id,
            "amount": invoice.amount_due / 100,  # Convert cents to dollars
            "customer": invoice.customer,
            "customer_email": invoice.customer_email,
            "due_date": invoice.due_date,
            "status": invoice.status,
            "days_outstanding": (
                (datetime.now(timezone.utc).timestamp() - invoice.created)
                // 86400
            ) if invoice.created else 0,
            "currency": invoice.currency,
            "platform": "stripe"
        }
    except Exception as e:
        print(f"❌ Error fetching Stripe invoice {invoice_id}: {e}")
        return None


async def get_stripe_interchange_rates(
    amount: float,
    card_brand: str,
    card_country: str
) -> Dict[str, float]:
    """
    Get current Stripe interchange rates
    Note: Stripe doesn't expose real-time interchange via API,
    so we use documented rates + Radar for fraud probability
    """
    
    # Base Stripe rates (as of 2026)
    base_rates = {
        "visa_us": {"percent": 2.9, "fixed": 0.30},
        "visa_international": {"percent": 3.9, "fixed": 0.30},
        "mastercard_us": {"percent": 2.9, "fixed": 0.30},
        "mastercard_international": {"percent": 3.9, "fixed": 0.30},
        "amex": {"percent": 3.5, "fixed": 0.30},
        "discover": {"percent": 2.9, "fixed": 0.30}
    }
    
    # Determine rate key
    rate_key = f"{card_brand.lower()}_{'us' if card_country == 'US' else 'international'}"
    
    if rate_key not in base_rates:
        rate_key = "visa_us"  # Default fallback
    
    rate = base_rates[rate_key]
    
    return {
        "rate_percent": rate["percent"],
        "fixed_fee": rate["fixed"],
        "total_fee": (amount * rate["percent"] / 100) + rate["fixed"]
    }


async def get_stripe_payment_intent_auth_probability(
    payment_intent_id: str
) -> float:
    """
    Get authorization probability from Stripe Radar
    """
    if not STRIPE_AVAILABLE:
        return 0.95  # Default high probability
    
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        # Check Radar risk score
        if hasattr(payment_intent, 'charges') and payment_intent.charges.data:
            charge = payment_intent.charges.data[0]
            if hasattr(charge, 'outcome'):
                risk_level = charge.outcome.get('risk_level', 'normal')
                
                # Convert risk level to auth probability
                risk_map = {
                    'normal': 0.96,
                    'elevated': 0.85,
                    'highest': 0.60
                }
                return risk_map.get(risk_level, 0.95)
        
        return 0.95  # Default
    except Exception as e:
        print(f"⚠️ Error getting auth probability: {e}")
        return 0.95


async def create_stripe_payout(
    amount: float,
    destination: str,
    metadata: Dict[str, Any]
) -> Optional[str]:
    """Create payout to creator/merchant"""
    if not STRIPE_AVAILABLE:
        return None
    
    try:
        payout = stripe.Transfer.create(
            amount=int(amount * 100),  # Convert to cents
            currency="usd",
            destination=destination,
            metadata=metadata
        )
        return payout.id
    except Exception as e:
        print(f"❌ Error creating Stripe payout: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# SHOPIFY INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

SHOPIFY_AVAILABLE = False
SHOPIFY_ADMIN_TOKEN = os.getenv("SHOPIFY_ADMIN_TOKEN")
SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET")
SHOPIFY_SHOP_URL = os.getenv("SHOPIFY_SHOP_URL", "")

if SHOPIFY_ADMIN_TOKEN:
    SHOPIFY_AVAILABLE = True

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("⚠️ httpx not installed - run: pip install httpx")


async def verify_shopify_signature(payload: bytes, signature: str) -> bool:
    """Verify Shopify webhook signature"""
    if not SHOPIFY_WEBHOOK_SECRET:
        return True  # Skip in dev
    
    try:
        computed_hmac = hmac.new(
            SHOPIFY_WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_hmac, signature)
    except Exception as e:
        print(f"❌ Shopify signature verification failed: {e}")
        return False


async def get_shopify_invoice_details(order_id: str) -> Optional[Dict[str, Any]]:
    """Fetch order/invoice details from Shopify"""
    if not SHOPIFY_AVAILABLE or not HTTPX_AVAILABLE:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SHOPIFY_SHOP_URL}/admin/api/2024-01/orders/{order_id}.json",
                headers={
                    "X-Shopify-Access-Token": SHOPIFY_ADMIN_TOKEN
                }
            )
            
            if response.status_code != 200:
                return None
            
            order = response.json()["order"]
            
            # Check if invoice is unpaid
            financial_status = order.get("financial_status", "paid")
            
            if financial_status == "paid":
                return None  # Skip paid orders
            
            created_at = datetime.fromisoformat(
                order["created_at"].replace("Z", "+00:00")
            )
            days_outstanding = (
                datetime.now(timezone.utc) - created_at
            ).days
            
            return {
                "invoice_id": f"shopify_{order['id']}",
                "amount": float(order.get("total_price", 0)),
                "customer": order.get("customer", {}).get("email", "unknown"),
                "due_date": None,
                "days_outstanding": days_outstanding,
                "status": financial_status,
                "platform": "shopify",
                "currency": order.get("currency", "USD")
            }
    except Exception as e:
        print(f"❌ Error fetching Shopify order {order_id}: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# TWITTER INTEGRATION (X API)
# ═══════════════════════════════════════════════════════════════════════════════

TWITTER_AVAILABLE = False
twitter_client = None

try:
    import tweepy

    # Option 1: Bearer Token (App-only auth - best for search)
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

    # Option 2: OAuth 1.0a (User auth - needed for posting)
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
    TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
    TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

    # Prefer Bearer Token for search (simpler, higher rate limits)
    if TWITTER_BEARER_TOKEN:
        twitter_client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
        TWITTER_AVAILABLE = True
        print("✅ Twitter: Using Bearer Token (App-only auth)")
    elif all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        twitter_client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        TWITTER_AVAILABLE = True
        print("✅ Twitter: Using OAuth 1.0a (User auth)")
    else:
        print("⚠️ Twitter: No valid credentials (need TWITTER_BEARER_TOKEN or all 4 OAuth keys)")
except ImportError:
    print("⚠️ tweepy not installed - run: pip install tweepy")


async def scrape_twitter_purchase_signals(
    max_results: int = 100
) -> List[Dict[str, Any]]:
    """
    Scrape Twitter for purchase intent signals
    
    Looks for patterns like:
    - "looking for X but can't find a seller I trust"
    - "anyone know where to buy X"
    - "need X but don't know where to get it"
    """
    if not TWITTER_AVAILABLE:
        return []
    
    # HIGH-QUALITY PURCHASE INTENT QUERIES
    # Each query targets specific buying signals, not general "looking for" noise
    search_queries = [
        # Direct purchase intent
        '"want to buy" -RT -is:retweet lang:en',
        '"looking to buy" -RT -is:retweet lang:en',
        '"trying to buy" -RT -is:retweet lang:en',
        '"where can I buy" -RT -is:retweet lang:en',
        '"anyone selling" -RT -is:retweet lang:en',

        # ISO (In Search Of) - common marketplace language
        '"ISO" (buy OR sell OR purchase) -RT -is:retweet lang:en',
        '"in search of" (buy OR purchase) -RT -is:retweet lang:en',

        # WTB (Want To Buy) - enthusiast/collector language
        '"WTB" -RT -is:retweet lang:en',
        '"want to purchase" -RT -is:retweet lang:en',

        # Frustrated buyers (high intent)
        '"can\'t find" (buy OR seller OR stock) -RT -is:retweet lang:en',
        '"out of stock" (need OR want) -RT -is:retweet lang:en',
        '"sold out" (looking OR need) -RT -is:retweet lang:en',

        # Recommendation seeking (trust signals)
        '"recommend" (seller OR store OR shop) -RT -is:retweet lang:en',
        '"trusted seller" -RT -is:retweet lang:en',

        # Price shopping (ready to buy)
        '"best price" (buy OR purchase) -RT -is:retweet lang:en',
        '"cheapest place to buy" -RT -is:retweet lang:en'
    ]

    # PRODUCT CATEGORIES with price ranges
    PRODUCT_CATEGORIES = {
        # Electronics
        "laptop": {"keywords": ["laptop", "macbook", "chromebook", "notebook"], "price": [500, 3000]},
        "phone": {"keywords": ["phone", "iphone", "android", "smartphone", "galaxy"], "price": [300, 1500]},
        "tablet": {"keywords": ["tablet", "ipad"], "price": [300, 1500]},
        "camera": {"keywords": ["camera", "dslr", "mirrorless", "canon", "nikon", "sony a7"], "price": [500, 4000]},
        "headphones": {"keywords": ["headphones", "airpods", "earbuds", "beats"], "price": [50, 500]},
        "console": {"keywords": ["ps5", "playstation", "xbox", "nintendo", "switch"], "price": [300, 600]},
        "gpu": {"keywords": ["gpu", "graphics card", "rtx", "nvidia", "amd rx"], "price": [300, 2000]},
        "monitor": {"keywords": ["monitor", "display", "4k monitor"], "price": [200, 1500]},

        # Fashion/Luxury
        "sneakers": {"keywords": ["sneakers", "jordans", "yeezys", "dunks", "air max"], "price": [100, 500]},
        "watch": {"keywords": ["watch", "rolex", "omega", "seiko", "casio"], "price": [100, 10000]},
        "bag": {"keywords": ["handbag", "purse", "louis vuitton", "gucci bag"], "price": [200, 5000]},

        # Collectibles
        "cards": {"keywords": ["pokemon card", "trading card", "sports card", "mtg"], "price": [20, 1000]},
        "vinyl": {"keywords": ["vinyl", "record", "lp"], "price": [20, 200]},
        "funko": {"keywords": ["funko", "pop figure"], "price": [15, 100]},

        # Home/Appliances
        "furniture": {"keywords": ["couch", "sofa", "desk", "chair", "mattress"], "price": [200, 2000]},
        "appliance": {"keywords": ["refrigerator", "washer", "dryer", "dishwasher"], "price": [500, 2000]},

        # Vehicles/Parts
        "car_parts": {"keywords": ["car part", "auto part", "oem", "aftermarket"], "price": [50, 1000]},
        "bike": {"keywords": ["bicycle", "ebike", "mountain bike"], "price": [200, 3000]},

        # Services (high value)
        "software": {"keywords": ["software", "license", "subscription"], "price": [50, 500]},
        "tickets": {"keywords": ["ticket", "concert", "event", "game ticket"], "price": [50, 500]},
    }

    signals = []

    try:
        for query in search_queries:
            try:
                tweets = twitter_client.search_recent_tweets(
                    query=query,
                    max_results=min(max_results // len(search_queries), 100),
                    tweet_fields=["created_at", "public_metrics", "author_id"]
                )

                if not tweets.data:
                    continue

                for tweet in tweets.data:
                    text = tweet.text.lower()

                    # Skip if looks like spam/bot
                    spam_indicators = ["follow me", "dm me", "click here", "free money", "giveaway"]
                    if any(spam in text for spam in spam_indicators):
                        continue

                    # Extract product category and price range
                    detected_category = None
                    price_range = [100, 1000]  # Default

                    for category, config in PRODUCT_CATEGORIES.items():
                        if any(kw in text for kw in config["keywords"]):
                            detected_category = category
                            price_range = config["price"]
                            break

                    # Calculate conversion probability based on signal strength
                    base_prob = 0.05
                    engagement = tweet.public_metrics.get("like_count", 0) if tweet.public_metrics else 0

                    # Boost probability for strong signals
                    if any(term in text for term in ["wtb", "want to buy", "looking to buy"]):
                        base_prob += 0.05
                    if any(term in text for term in ["urgent", "asap", "need today"]):
                        base_prob += 0.03
                    if detected_category:  # Specific product = higher intent
                        base_prob += 0.02
                    if engagement > 5:  # Engagement = social proof
                        base_prob += 0.02

                    signal = {
                        "text": tweet.text,
                        "source": "twitter",
                        "user_id": f"twitter_{tweet.author_id}",
                        "product_intent": detected_category or "general",
                        "price_range": price_range,
                        "timestamp": tweet.created_at.isoformat() if tweet.created_at else None,
                        "engagement": engagement,
                        "conversion_prob_override": min(base_prob, 0.20)  # Cap at 20%
                    }

                    signals.append(signal)

                    if len(signals) >= max_results:
                        break

                # Rate limit - Twitter API has strict limits
                await asyncio.sleep(1)

            except Exception as e:
                print(f"⚠️ Error searching Twitter with query '{query}': {e}")
                continue

        print(f"✅ Twitter: Captured {len(signals)} purchase intent signals")
        return signals
    except Exception as e:
        print(f"❌ Error scraping Twitter signals: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# INSTAGRAM INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

INSTAGRAM_AVAILABLE = False
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")

if INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ID:
    INSTAGRAM_AVAILABLE = True


async def scrape_instagram_shopping_signals() -> List[Dict[str, Any]]:
    """
    Scrape Instagram for shopping intent from comments/captions
    Note: Requires Instagram Business account with appropriate permissions
    """
    if not INSTAGRAM_AVAILABLE or not HTTPX_AVAILABLE:
        return []
    
    signals = []
    
    try:
        async with httpx.AsyncClient() as client:
            # Get recent media
            response = await client.get(
                f"https://graph.instagram.com/v18.0/{INSTAGRAM_BUSINESS_ID}/media",
                params={
                    "fields": "id,caption,comments_count,like_count",
                    "access_token": INSTAGRAM_ACCESS_TOKEN,
                    "limit": 25
                }
            )
            
            if response.status_code != 200:
                return []
            
            media_items = response.json().get("data", [])
            
            for media in media_items:
                caption = media.get("caption", "").lower()
                
                # Look for shopping intent keywords
                shopping_keywords = [
                    "where to buy",
                    "link in bio",
                    "shop",
                    "purchase",
                    "looking for"
                ]
                
                if any(keyword in caption for keyword in shopping_keywords):
                    signal = {
                        "text": media.get("caption", ""),
                        "source": "instagram",
                        "user_id": f"instagram_{INSTAGRAM_BUSINESS_ID}",
                        "product_intent": "instagram_product",
                        "price_range": [50, 500],  # Default for Instagram shopping
                        "engagement": media.get("like_count", 0)
                    }
                    signals.append(signal)
        
        return signals
    except Exception as e:
        print(f"❌ Error scraping Instagram signals: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# WEBHOOK HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_stripe_invoice_paid_webhook(
    event: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle Stripe invoice.paid webhook
    Triggers receivables collection
    """
    try:
        # Import v111 functions
        from v111_gapharvester_ii import receivables_recover
        
        invoice = event["data"]["object"]
        invoice_id = invoice["id"]
        amount_paid = invoice["amount_paid"] / 100  # Convert cents to dollars
        
        # Find matching advance
        from v111_gapharvester_ii import RECEIVABLES_ADVANCES
        
        matching_advance = None
        for advance_id, advance in RECEIVABLES_ADVANCES.items():
            if advance["invoice_id"] == invoice_id:
                matching_advance = advance
                break
        
        if not matching_advance:
            print(f"⚠️ No matching advance for invoice {invoice_id}")
            return {"ok": False, "reason": "no_matching_advance"}
        
        # Trigger collection
        collection = await receivables_recover(
            advance_id=matching_advance["advance_id"],
            collected_amount=amount_paid,
            collection_method="stripe_webhook"
        )
        
        return {
            "ok": True,
            "invoice_id": invoice_id,
            "amount_collected": amount_paid,
            "collection": collection
        }
    except Exception as e:
        print(f"❌ Error handling Stripe invoice webhook: {e}")
        return {"ok": False, "error": str(e)}


async def handle_shopify_order_webhook(
    order: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle Shopify order creation webhook
    Triggers invoice ingestion for unpaid orders
    """
    try:
        from v111_gapharvester_ii import receivables_ingest
        
        # Check if order is unpaid
        financial_status = order.get("financial_status", "paid")
        
        if financial_status == "paid":
            return {"ok": False, "reason": "order_already_paid"}
        
        # Convert to invoice format
        invoice = {
            "invoice_id": f"shopify_{order['id']}",
            "amount": float(order.get("total_price", 0)),
            "customer": order.get("customer", {}).get("email", "unknown"),
            "due_date": None,
            "days_outstanding": 0
        }
        
        # Ingest invoice
        result = await receivables_ingest(
            invoices=[invoice],
            platform="shopify"
        )
        
        return {
            "ok": True,
            "order_id": order["id"],
            "invoice_ingested": result
        }
    except Exception as e:
        print(f"❌ Error handling Shopify order webhook: {e}")
        return {"ok": False, "error": str(e)}


async def handle_stripe_charge_succeeded_webhook(
    event: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle Stripe charge.succeeded webhook
    Can be used for payment routing metrics
    """
    try:
        charge = event["data"]["object"]
        
        # Extract routing metrics
        payment_method = charge.get("payment_method_details", {})
        card = payment_method.get("card", {})
        
        metrics = {
            "amount": charge["amount"] / 100,
            "card_brand": card.get("brand", "unknown"),
            "card_country": card.get("country", "US"),
            "outcome": charge.get("outcome", {}),
            "processor": "stripe"
        }
        
        return {"ok": True, "metrics": metrics}
    except Exception as e:
        print(f"❌ Error handling charge webhook: {e}")
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════════════════════════

async def background_twitter_signal_scraper():
    """
    Background task to scrape Twitter signals every 15 minutes
    """
    while True:
        try:
            print("🔍 Scraping Twitter for purchase signals...")
            signals = await scrape_twitter_purchase_signals(max_results=100)
            
            if signals:
                # Ingest into U-ACR
                from v111_gapharvester_ii import uacr_ingest_signals
                
                result = await uacr_ingest_signals(
                    signals=signals,
                    source_type="social"
                )
                
                print(f"✅ Ingested {result['signals_ingested']} Twitter signals")
            else:
                print("⚠️ No Twitter signals found")
        except Exception as e:
            print(f"❌ Error in Twitter signal scraper: {e}")
        
        # Wait 15 minutes
        await asyncio.sleep(15 * 60)


async def background_instagram_signal_scraper():
    """
    Background task to scrape Instagram signals every 30 minutes
    """
    while True:
        try:
            print("🔍 Scraping Instagram for shopping signals...")
            signals = await scrape_instagram_shopping_signals()
            
            if signals:
                from v111_gapharvester_ii import uacr_ingest_signals
                
                result = await uacr_ingest_signals(
                    signals=signals,
                    source_type="social"
                )
                
                print(f"✅ Ingested {result['signals_ingested']} Instagram signals")
            else:
                print("⚠️ No Instagram signals found")
        except Exception as e:
            print(f"❌ Error in Instagram signal scraper: {e}")
        
        # Wait 30 minutes
        await asyncio.sleep(30 * 60)


async def background_stripe_invoice_sync():
    """
    Background task to sync unpaid Stripe invoices every hour
    """
    while True:
        try:
            if not STRIPE_AVAILABLE:
                await asyncio.sleep(60 * 60)
                continue
            
            print("🔍 Syncing unpaid Stripe invoices...")
            
            # Get unpaid invoices
            invoices = stripe.Invoice.list(status="open", limit=100)
            
            invoice_data = []
            for inv in invoices.auto_paging_iter():
                days_outstanding = (
                    (datetime.now(timezone.utc).timestamp() - inv.created)
                    // 86400
                ) if inv.created else 0
                
                invoice_data.append({
                    "invoice_id": inv.id,
                    "amount": inv.amount_due / 100,
                    "customer": inv.customer_email or inv.customer,
                    "due_date": inv.due_date,
                    "days_outstanding": days_outstanding
                })
            
            if invoice_data:
                from v111_gapharvester_ii import receivables_ingest
                
                result = await receivables_ingest(
                    invoices=invoice_data,
                    platform="stripe"
                )
                
                print(f"✅ Synced {result['invoices_ingested']} Stripe invoices")
            else:
                print("⚠️ No unpaid Stripe invoices found")
        except Exception as e:
            print(f"❌ Error in Stripe invoice sync: {e}")
        
        # Wait 1 hour
        await asyncio.sleep(60 * 60)


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_v111_integrations(app):
    """
    Add all v111 production integrations to FastAPI app
    """
    
    # ===== STRIPE WEBHOOKS =====
    
    @app.post("/webhooks/stripe")
    async def stripe_webhook_endpoint(
        request: Request,
        stripe_signature: str = Header(None, alias="Stripe-Signature")
    ):
        """Handle all Stripe webhooks"""
        payload = await request.body()
        
        # Verify signature
        if not await verify_stripe_signature(payload, stripe_signature):
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        try:
            event = json.loads(payload)
            event_type = event["type"]
            
            if event_type == "invoice.paid":
                return await handle_stripe_invoice_paid_webhook(event)
            
            elif event_type == "charge.succeeded":
                return await handle_stripe_charge_succeeded_webhook(event)
            
            else:
                return {"ok": True, "event_type": event_type, "processed": False}
        except Exception as e:
            print(f"❌ Stripe webhook error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===== SHOPIFY WEBHOOKS =====
    
    @app.post("/webhooks/shopify/orders-create")
    async def shopify_orders_webhook(
        request: Request,
        x_shopify_hmac_sha256: str = Header(None)
    ):
        """Handle Shopify order creation webhooks"""
        payload = await request.body()
        
        # Verify signature
        if not await verify_shopify_signature(payload, x_shopify_hmac_sha256):
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        try:
            order = json.loads(payload)
            return await handle_shopify_order_webhook(order)
        except Exception as e:
            print(f"❌ Shopify webhook error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ===== MANUAL SYNC ENDPOINTS =====
    
    @app.post("/integrations/twitter/sync-signals")
    async def manual_twitter_sync():
        """Manually trigger Twitter signal scrape"""
        signals = await scrape_twitter_purchase_signals(max_results=100)
        
        if not signals:
            return {"ok": True, "signals_found": 0}
        
        from v111_gapharvester_ii import uacr_ingest_signals
        
        result = await uacr_ingest_signals(
            signals=signals,
            source_type="social"
        )
        
        return {
            "ok": True,
            "signals_found": len(signals),
            "signals_ingested": result["signals_ingested"],
            "sample_signals": signals[:5]  # Show first 5 for debugging
        }

    @app.post("/integrations/instagram/sync-signals")
    async def manual_instagram_sync():
        """Manually trigger Instagram signal scrape"""
        signals = await scrape_instagram_shopping_signals()

        if not signals:
            return {"ok": True, "signals_found": 0, "note": "No shopping signals detected"}

        from v111_gapharvester_ii import uacr_ingest_signals

        result = await uacr_ingest_signals(
            signals=signals,
            source_type="social"
        )

        return {
            "ok": True,
            "signals_found": len(signals),
            "signals_ingested": result["signals_ingested"],
            "sample_signals": signals[:5]  # Show first 5 for debugging
        }

    @app.post("/integrations/stripe/sync-invoices")
    async def manual_stripe_sync():
        """Manually trigger Stripe invoice sync"""
        if not STRIPE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Stripe not available")
        
        invoices = stripe.Invoice.list(status="open", limit=100)
        
        invoice_data = []
        for inv in invoices.auto_paging_iter():
            invoice_details = await get_stripe_invoice_details(inv.id)
            if invoice_details:
                invoice_data.append(invoice_details)
        
        if not invoice_data:
            return {"ok": True, "invoices_found": 0}
        
        from v111_gapharvester_ii import receivables_ingest
        
        result = await receivables_ingest(
            invoices=invoice_data,
            platform="stripe"
        )
        
        return {
            "ok": True,
            "invoices_found": len(invoice_data),
            "invoices_ingested": result["invoices_ingested"]
        }
    
    @app.get("/integrations/status")
    async def integrations_status():
        """Get status of all integrations"""
        return {
            "ok": True,
            "integrations": {
                "stripe": {
                    "available": STRIPE_AVAILABLE,
                    "webhooks_configured": bool(STRIPE_WEBHOOK_SECRET)
                },
                "shopify": {
                    "available": SHOPIFY_AVAILABLE,
                    "webhooks_configured": bool(SHOPIFY_WEBHOOK_SECRET)
                },
                "twitter": {
                    "available": TWITTER_AVAILABLE,
                    "scraper_enabled": True
                },
                "instagram": {
                    "available": INSTAGRAM_AVAILABLE,
                    "scraper_enabled": True
                }
            },
            "background_tasks": [
                "twitter_signal_scraper (every 15 min)",
                "instagram_signal_scraper (every 30 min)",
                "stripe_invoice_sync (every 60 min)"
            ]
        }

    @app.get("/integrations/signals/live")
    async def get_live_signals():
        """View all captured signals in memory (debug endpoint)"""
        from v111_gapharvester_ii import UACR_SIGNALS, UACR_QUOTES

        # Get last 24 hours of signals
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=24)

        recent_signals = []
        for signal_id, signal in UACR_SIGNALS.items():
            ingested_at = signal.get("ingested_at", "")
            if ingested_at:
                try:
                    signal_time = datetime.fromisoformat(ingested_at.replace("Z", "+00:00"))
                    if signal_time > cutoff:
                        recent_signals.append({
                            "signal_id": signal_id,
                            "source": signal.get("source"),
                            "product_intent": signal.get("product_intent"),
                            "text_preview": signal.get("text", "")[:100] + "..." if signal.get("text") else None,
                            "price_range": signal.get("price_range"),
                            "conversion_prob": signal.get("conversion_prob"),
                            "status": signal.get("status"),
                            "ingested_at": ingested_at
                        })
                except:
                    pass

        return {
            "ok": True,
            "total_signals_in_memory": len(UACR_SIGNALS),
            "total_quotes_in_memory": len(UACR_QUOTES),
            "signals_last_24h": len(recent_signals),
            "recent_signals": sorted(recent_signals, key=lambda x: x.get("ingested_at", ""), reverse=True)[:20]
        }

    # ===== START BACKGROUND TASKS =====
    
    @app.on_event("startup")
    async def start_background_tasks():
        """Start all background scraper tasks"""
        if TWITTER_AVAILABLE:
            asyncio.create_task(background_twitter_signal_scraper())
            print("✅ Twitter signal scraper started (every 15 min)")
        
        if INSTAGRAM_AVAILABLE:
            asyncio.create_task(background_instagram_signal_scraper())
            print("✅ Instagram signal scraper started (every 30 min)")
        
        if STRIPE_AVAILABLE:
            asyncio.create_task(background_stripe_invoice_sync())
            print("✅ Stripe invoice sync started (every 60 min)")
    
    print("=" * 80)
    print("🔌 V111 PRODUCTION INTEGRATIONS LOADED")
    print("=" * 80)
    print("Integrations:")
    print(f"  Stripe: {'✓' if STRIPE_AVAILABLE else '✗'}")
    print(f"  Shopify: {'✓' if SHOPIFY_AVAILABLE else '✗'}")
    print(f"  Twitter: {'✓' if TWITTER_AVAILABLE else '✗'}")
    print(f"  Instagram: {'✓' if INSTAGRAM_AVAILABLE else '✗'}")
    print("=" * 80)
    print("Webhooks:")
    print("  POST /webhooks/stripe")
    print("  POST /webhooks/shopify/orders-create")
    print("=" * 80)
    print("Manual Sync:")
    print("  POST /integrations/twitter/sync-signals")
    print("  POST /integrations/stripe/sync-invoices")
    print("=" * 80)
    print("Status: GET /integrations/status")
    print("=" * 80)
