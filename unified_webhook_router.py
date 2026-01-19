"""
═══════════════════════════════════════════════════════════════════════════════
UNIFIED WEBHOOK ROUTER
Routes Stripe webhooks to Path A (user business) or Path B (Wade direct)
═══════════════════════════════════════════════════════════════════════════════

ROUTING LOGIC:
- metadata.user_business = true → Path A (stripe_webhook_handler.py)
- metadata.wade_harvesting = true → Path B (wade_webhook_handler.py)
- No metadata or unknown → Default to Path B

USAGE:
    from unified_webhook_router import setup_unified_webhook
    setup_unified_webhook(app)
    
WEBHOOK URL:
    POST /webhooks/stripe-unified
"""

import os
import stripe
from fastapi import Request, HTTPException, Header
from typing import Optional
import json

# Load Stripe secrets
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# Import handlers
try:
    from stripe_webhook_handler import handle_stripe_webhook as path_a_handler
    PATH_A_AVAILABLE = True
    print("✅ Path A handler (stripe_webhook_handler) loaded")
except ImportError as e:
    PATH_A_AVAILABLE = False
    print(f"⚠️ Path A handler not available: {e}")

try:
    from wade_webhook_handler import handle_wade_webhook as path_b_handler
    PATH_B_AVAILABLE = True
    print("✅ Path B handler (wade_webhook_handler) loaded")
except ImportError as e:
    PATH_B_AVAILABLE = False
    print(f"⚠️ Path B handler not available: {e}")


async def route_webhook(request: Request) -> dict:
    """
    Main routing logic for Stripe webhooks
    
    Routes based on metadata in the payment object:
    - user_business: true → Path A (user revenue, awards AIGx)
    - wade_harvesting: true → Path B (Wade direct, no AIGx)
    - Default → Path B
    """
    
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Stripe not configured - STRIPE_SECRET_KEY missing"
        )
    
    # Get payload and signature
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    # Verify webhook signature
    if not STRIPE_WEBHOOK_SECRET:
        print("⚠️ Webhook signature verification skipped (no STRIPE_WEBHOOK_SECRET)")
        event = json.loads(payload)
    else:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError as e:
            print(f"❌ Webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        except Exception as e:
            print(f"❌ Error verifying webhook: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})
    metadata = event_data.get("metadata", {})
    
    print(f"📨 Webhook received: {event_type}")
    print(f"🏷️  Metadata: {metadata}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # ROUTING DECISION
    # ═══════════════════════════════════════════════════════════════════════
    
    # Path A: User business (awards AIGx)
    if metadata.get("user_business") or metadata.get("username"):
        print(f"→ Routing to Path A (user business)")
        
        if not PATH_A_AVAILABLE:
            return {
                "ok": False,
                "error": "Path A handler not available",
                "event_type": event_type
            }
        
        try:
            result = await path_a_handler(request)
            return {
                "ok": True,
                "path": "A",
                "handler": "stripe_webhook_handler",
                "result": result
            }
        except Exception as e:
            print(f"❌ Path A handler error: {e}")
            return {
                "ok": False,
                "error": str(e),
                "path": "A"
            }
    
    # Path B: Wade direct harvesting (no AIGx)
    elif metadata.get("wade_harvesting") or metadata.get("revenue_path") == "path_b_wade":
        print(f"→ Routing to Path B (Wade direct)")
        
        if not PATH_B_AVAILABLE:
            return {
                "ok": False,
                "error": "Path B handler not available",
                "event_type": event_type
            }
        
        try:
            result = await path_b_handler(request)
            return {
                "ok": True,
                "path": "B",
                "handler": "wade_webhook_handler",
                "result": result
            }
        except Exception as e:
            print(f"❌ Path B handler error: {e}")
            return {
                "ok": False,
                "error": str(e),
                "path": "B"
            }
    
    # Default: Path B (Wade direct)
    else:
        print(f"→ No path metadata - defaulting to Path B (Wade direct)")
        
        if not PATH_B_AVAILABLE:
            return {
                "ok": False,
                "error": "Path B handler not available (default)",
                "event_type": event_type
            }
        
        try:
            result = await path_b_handler(request)
            return {
                "ok": True,
                "path": "B_default",
                "handler": "wade_webhook_handler",
                "result": result
            }
        except Exception as e:
            print(f"❌ Path B handler error: {e}")
            return {
                "ok": False,
                "error": str(e),
                "path": "B_default"
            }


def setup_unified_webhook(app):
    """
    Add unified webhook endpoint to FastAPI app
    
    Usage:
        from unified_webhook_router import setup_unified_webhook
        setup_unified_webhook(app)
    """
    
    @app.post("/webhooks/stripe-unified")
    async def unified_stripe_webhook(request: Request):
        """
        Unified Stripe webhook endpoint
        Routes to Path A (user business) or Path B (Wade direct)
        """
        return await route_webhook(request)
    
    @app.get("/webhooks/test-routing")
    async def test_routing():
        """
        Test endpoint to check which handlers are available
        """
        return {
            "ok": True,
            "path_a_available": PATH_A_AVAILABLE,
            "path_b_available": PATH_B_AVAILABLE,
            "routing_logic": {
                "path_a": "metadata.user_business = true OR metadata.username exists",
                "path_b": "metadata.wade_harvesting = true OR metadata.revenue_path = 'path_b_wade'",
                "default": "Path B (Wade direct)"
            }
        }
    
    print("=" * 80)
    print("🔀 UNIFIED WEBHOOK ROUTER LOADED")
    print("=" * 80)
    print("Endpoint: POST /webhooks/stripe-unified")
    print(f"Path A (user business): {'✅ Available' if PATH_A_AVAILABLE else '❌ Not available'}")
    print(f"Path B (Wade direct): {'✅ Available' if PATH_B_AVAILABLE else '❌ Not available'}")
    print("=" * 80)
    print("Routing Logic:")
    print("  • metadata.user_business = true → Path A")
    print("  • metadata.wade_harvesting = true → Path B")
    print("  • No metadata → Default to Path B")
    print("=" * 80)
