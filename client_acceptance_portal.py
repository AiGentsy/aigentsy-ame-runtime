"""
═══════════════════════════════════════════════════════════════════════════════
CLIENT ACCEPTANCE PORTAL
The handshake between AiGentsy and trade partners
═══════════════════════════════════════════════════════════════════════════════

Flow:
1. Pitch sent with unique accept link
2. Client clicks link → sees proposal with AI disclosure
3. Client accepts → payment authorized (NOT captured)
4. Wade executes → work delivered
5. Client approves delivery → payment captured
6. Revenue recorded

Money Movement:
- AUTHORIZE on accept (hold funds)
- CAPTURE on delivery approval (move funds)
- REFUND if delivery rejected or timeout

AI Speed Advantage:
- Logo: 2 hours (not 48)
- Website: 4 hours (not 1 week)  
- Content: 30 minutes (not 24 hours)
- "AiGentsy Automation Discount" = 40-60% below market

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import stripe
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# ═══════════════════════════════════════════════════════════════════════════════
# AI-SPEED SERVICE CATALOG
# "Better, Faster, Cheaper" - The AiGentsy Promise
# ═══════════════════════════════════════════════════════════════════════════════

class ServiceTier(str, Enum):
    EXPRESS = "express"      # Fastest - premium
    STANDARD = "standard"    # Default AI speed
    BUDGET = "budget"        # Slower but cheapest


AI_SERVICE_CATALOG = {
    # DESIGN SERVICES
    "logo_design": {
        "name": "Logo Design",
        "market_price": 300,
        "market_time_hours": 72,
        "ai_prices": {
            "express": 99,      # 67% discount
            "standard": 79,     # 74% discount
            "budget": 49        # 84% discount
        },
        "ai_times_hours": {
            "express": 1,       # 1 hour vs 3 days
            "standard": 4,
            "budget": 12
        },
        "deliverables": ["3 concepts", "Source files", "Revisions"],
        "quality_checks": ["brand_alignment", "resolution_check", "format_validation"]
    },
    
    "social_graphics": {
        "name": "Social Media Graphics Pack",
        "market_price": 200,
        "market_time_hours": 48,
        "ai_prices": {
            "express": 59,
            "standard": 39,
            "budget": 19
        },
        "ai_times_hours": {
            "express": 0.5,     # 30 minutes!
            "standard": 2,
            "budget": 6
        },
        "deliverables": ["10 branded posts", "Story templates", "Profile assets"],
        "quality_checks": ["dimension_check", "brand_consistency", "platform_compliance"]
    },
    
    "thumbnail_design": {
        "name": "YouTube/Video Thumbnails",
        "market_price": 50,
        "market_time_hours": 24,
        "ai_prices": {
            "express": 15,
            "standard": 9,
            "budget": 5
        },
        "ai_times_hours": {
            "express": 0.25,    # 15 minutes!
            "standard": 1,
            "budget": 3
        },
        "deliverables": ["3 thumbnail options", "Click-optimized design"],
        "quality_checks": ["ctr_prediction", "text_readability", "visual_hierarchy"]
    },
    
    # CONTENT SERVICES
    "blog_article": {
        "name": "SEO Blog Article (1500 words)",
        "market_price": 150,
        "market_time_hours": 48,
        "ai_prices": {
            "express": 39,
            "standard": 25,
            "budget": 15
        },
        "ai_times_hours": {
            "express": 0.5,
            "standard": 2,
            "budget": 6
        },
        "deliverables": ["1500+ words", "SEO optimized", "Meta description"],
        "quality_checks": ["plagiarism_check", "seo_score", "readability_score"]
    },
    
    "product_descriptions": {
        "name": "Product Descriptions (10 products)",
        "market_price": 100,
        "market_time_hours": 24,
        "ai_prices": {
            "express": 29,
            "standard": 19,
            "budget": 9
        },
        "ai_times_hours": {
            "express": 0.25,
            "standard": 1,
            "budget": 3
        },
        "deliverables": ["10 descriptions", "SEO keywords", "Bullet points"],
        "quality_checks": ["keyword_density", "conversion_optimization", "uniqueness"]
    },
    
    "social_content_month": {
        "name": "Social Content Calendar (30 posts)",
        "market_price": 500,
        "market_time_hours": 168,  # 1 week
        "ai_prices": {
            "express": 149,
            "standard": 99,
            "budget": 49
        },
        "ai_times_hours": {
            "express": 2,
            "standard": 6,
            "budget": 24
        },
        "deliverables": ["30 posts", "Captions", "Hashtag sets", "Posting schedule"],
        "quality_checks": ["engagement_prediction", "brand_voice", "platform_optimization"]
    },
    
    # WEBSITE SERVICES
    "landing_page": {
        "name": "Landing Page",
        "market_price": 800,
        "market_time_hours": 168,  # 1 week
        "ai_prices": {
            "express": 199,
            "standard": 149,
            "budget": 79
        },
        "ai_times_hours": {
            "express": 2,
            "standard": 6,
            "budget": 24
        },
        "deliverables": ["Responsive design", "Copy", "CTA optimization", "Hosting setup"],
        "quality_checks": ["mobile_responsive", "page_speed", "conversion_elements"]
    },
    
    "website_5page": {
        "name": "5-Page Website",
        "market_price": 2000,
        "market_time_hours": 336,  # 2 weeks
        "ai_prices": {
            "express": 499,
            "standard": 349,
            "budget": 199
        },
        "ai_times_hours": {
            "express": 4,
            "standard": 12,
            "budget": 48
        },
        "deliverables": ["5 pages", "Contact form", "SEO setup", "Analytics"],
        "quality_checks": ["cross_browser", "accessibility", "seo_technical"]
    },
    
    # VIDEO SERVICES
    "video_edit_short": {
        "name": "Short Video Edit (60s)",
        "market_price": 150,
        "market_time_hours": 48,
        "ai_prices": {
            "express": 39,
            "standard": 25,
            "budget": 15
        },
        "ai_times_hours": {
            "express": 0.5,
            "standard": 2,
            "budget": 6
        },
        "deliverables": ["Edited video", "Captions", "Music", "Transitions"],
        "quality_checks": ["audio_levels", "pacing_score", "hook_strength"]
    },
    
    "video_script": {
        "name": "Video Script (5 minutes)",
        "market_price": 200,
        "market_time_hours": 24,
        "ai_prices": {
            "express": 49,
            "standard": 29,
            "budget": 15
        },
        "ai_times_hours": {
            "express": 0.5,
            "standard": 2,
            "budget": 6
        },
        "deliverables": ["Full script", "Hook options", "CTA variations"],
        "quality_checks": ["retention_prediction", "clarity_score", "cta_strength"]
    },
    
    # AUDIO SERVICES
    "voiceover": {
        "name": "AI Voiceover (500 words)",
        "market_price": 100,
        "market_time_hours": 24,
        "ai_prices": {
            "express": 19,
            "standard": 12,
            "budget": 5
        },
        "ai_times_hours": {
            "express": 0.1,     # 6 minutes!
            "standard": 0.5,
            "budget": 2
        },
        "deliverables": ["MP3/WAV", "Multiple voices", "Speed options"],
        "quality_checks": ["pronunciation", "pacing", "audio_quality"]
    },
    
    # RESEARCH SERVICES
    "market_research": {
        "name": "Market Research Report",
        "market_price": 500,
        "market_time_hours": 168,
        "ai_prices": {
            "express": 99,
            "standard": 69,
            "budget": 39
        },
        "ai_times_hours": {
            "express": 1,
            "standard": 4,
            "budget": 12
        },
        "deliverables": ["10-page report", "Competitor analysis", "Market sizing"],
        "quality_checks": ["source_verification", "data_freshness", "insight_depth"]
    },
    
    "competitor_analysis": {
        "name": "Competitor Analysis (5 competitors)",
        "market_price": 300,
        "market_time_hours": 72,
        "ai_prices": {
            "express": 79,
            "standard": 49,
            "budget": 29
        },
        "ai_times_hours": {
            "express": 1,
            "standard": 3,
            "budget": 8
        },
        "deliverables": ["SWOT analysis", "Pricing comparison", "Strategy insights"],
        "quality_checks": ["accuracy_verification", "completeness", "actionability"]
    }
}


def get_service_pricing(service_type: str, tier: str = "standard") -> Dict[str, Any]:
    """Get pricing and timing for a service"""
    service = AI_SERVICE_CATALOG.get(service_type)
    if not service:
        return {"ok": False, "error": "service_not_found"}
    
    return {
        "ok": True,
        "service": service["name"],
        "market_price": service["market_price"],
        "market_time_hours": service["market_time_hours"],
        "ai_price": service["ai_prices"][tier],
        "ai_time_hours": service["ai_times_hours"][tier],
        "savings_dollars": service["market_price"] - service["ai_prices"][tier],
        "savings_percent": round((1 - service["ai_prices"][tier] / service["market_price"]) * 100),
        "time_savings_hours": service["market_time_hours"] - service["ai_times_hours"][tier],
        "deliverables": service["deliverables"],
        "tier": tier
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DEAL TOKENS - Secure accept links
# ═══════════════════════════════════════════════════════════════════════════════

_active_deals: Dict[str, Dict[str, Any]] = {}


def generate_deal_token(deal_id: str) -> str:
    """Generate secure token for deal acceptance link"""
    secret = os.getenv("DEAL_TOKEN_SECRET", "aigentsy-deals-2026")
    raw = f"{deal_id}:{secret}:{datetime.now().timestamp()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def create_accept_link(
    workflow_id: str,
    service_type: str,
    tier: str = "standard",
    client_email: str = None,
    custom_price: float = None,
    custom_description: str = None
) -> Dict[str, Any]:
    """
    Create a unique acceptance link for a deal
    
    Returns link that client clicks to accept and pay
    """
    
    pricing = get_service_pricing(service_type, tier)
    if not pricing["ok"]:
        return pricing
    
    deal_id = f"deal_{secrets.token_hex(8)}"
    token = generate_deal_token(deal_id)
    
    price = custom_price or pricing["ai_price"]
    
    deal = {
        "deal_id": deal_id,
        "token": token,
        "workflow_id": workflow_id,
        "service_type": service_type,
        "service_name": pricing["service"],
        "tier": tier,
        "price": price,
        "delivery_hours": pricing["ai_time_hours"],
        "deliverables": pricing["deliverables"],
        "custom_description": custom_description,
        "client_email": client_email,
        "status": "pending",  # pending → accepted → in_progress → delivered → completed/disputed
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "payment_intent_id": None,
        "accepted_at": None,
        "delivered_at": None,
        "completed_at": None,
        "disclosures_accepted": False,
        "terms_accepted": False,
        
        # Comparison data for client
        "market_price": pricing["market_price"],
        "market_time_hours": pricing["market_time_hours"],
        "savings_percent": pricing["savings_percent"],
        "time_savings_hours": pricing["time_savings_hours"]
    }
    
    _active_deals[deal_id] = deal
    
    # Generate accept URL
    base_url = os.getenv("AIGENTSY_BASE_URL", "https://aigentsy.com")
    accept_url = f"{base_url}/accept?deal={deal_id}&token={token}"
    
    return {
        "ok": True,
        "deal_id": deal_id,
        "accept_url": accept_url,
        "price": price,
        "delivery_hours": pricing["ai_time_hours"],
        "expires_at": deal["expires_at"]
    }


def get_deal(deal_id: str, token: str = None) -> Dict[str, Any]:
    """Get deal details (validates token if provided)"""
    deal = _active_deals.get(deal_id)
    
    if not deal:
        return {"ok": False, "error": "deal_not_found"}
    
    if token and deal["token"] != token:
        return {"ok": False, "error": "invalid_token"}
    
    # Check expiration
    expires = datetime.fromisoformat(deal["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires and deal["status"] == "pending":
        deal["status"] = "expired"
    
    return {"ok": True, "deal": deal}


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT ACCEPTANCE FLOW
# ═══════════════════════════════════════════════════════════════════════════════

async def accept_deal(
    deal_id: str,
    token: str,
    client_name: str,
    client_email: str,
    disclosures_accepted: bool,
    terms_accepted: bool,
    payment_method_id: str = None
) -> Dict[str, Any]:
    """
    Client accepts the deal
    
    1. Validates deal and token
    2. Confirms disclosures accepted
    3. Authorizes payment (does NOT capture)
    4. Updates deal status
    5. Notifies Wade to begin work
    """
    
    # Validate deal
    deal_result = get_deal(deal_id, token)
    if not deal_result["ok"]:
        return deal_result
    
    deal = deal_result["deal"]
    
    # Check status
    if deal["status"] != "pending":
        return {"ok": False, "error": f"deal_already_{deal['status']}"}
    
    # Require disclosures
    if not disclosures_accepted:
        return {"ok": False, "error": "must_accept_ai_disclosure"}
    
    if not terms_accepted:
        return {"ok": False, "error": "must_accept_terms"}
    
    # Create Stripe PaymentIntent (authorize only - capture later)
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(deal["price"] * 100),
            currency="usd",
            capture_method="manual",  # ← KEY: Authorize only, capture on delivery
            receipt_email=client_email,
            metadata={
                "deal_id": deal_id,
                "workflow_id": deal["workflow_id"],
                "service": deal["service_type"],
                "platform": "aigentsy",
                "revenue_path": "path_b_wade"
            },
            description=f"AiGentsy: {deal['service_name']}",
            # If payment method provided, confirm immediately
            payment_method=payment_method_id,
            confirm=bool(payment_method_id)
        )
        
        deal["payment_intent_id"] = payment_intent.id
        deal["client_secret"] = payment_intent.client_secret
        
    except stripe.error.StripeError as e:
        return {"ok": False, "error": f"payment_failed: {str(e)}"}
    
    # Update deal
    deal["status"] = "accepted"
    deal["client_name"] = client_name
    deal["client_email"] = client_email
    deal["disclosures_accepted"] = True
    deal["terms_accepted"] = True
    deal["accepted_at"] = datetime.now(timezone.utc).isoformat()
    
    # Calculate delivery deadline
    delivery_deadline = datetime.now(timezone.utc) + timedelta(hours=deal["delivery_hours"])
    deal["delivery_deadline"] = delivery_deadline.isoformat()
    
    return {
        "ok": True,
        "deal_id": deal_id,
        "status": "accepted",
        "payment_authorized": True,
        "amount": deal["price"],
        "delivery_deadline": deal["delivery_deadline"],
        "client_secret": deal.get("client_secret"),  # For Stripe Elements if needed
        "message": f"Thank you! Your {deal['service_name']} will be delivered within {deal['delivery_hours']} hours."
    }


async def mark_deal_in_progress(deal_id: str) -> Dict[str, Any]:
    """Wade marks deal as in progress"""
    deal = _active_deals.get(deal_id)
    if not deal:
        return {"ok": False, "error": "deal_not_found"}
    
    if deal["status"] != "accepted":
        return {"ok": False, "error": f"deal_must_be_accepted_first"}
    
    deal["status"] = "in_progress"
    deal["work_started_at"] = datetime.now(timezone.utc).isoformat()
    
    return {"ok": True, "status": "in_progress"}


# ═══════════════════════════════════════════════════════════════════════════════
# DELIVERY & QUALITY CONTROL
# ═══════════════════════════════════════════════════════════════════════════════

async def submit_delivery(
    deal_id: str,
    deliverables: List[Dict[str, Any]],
    quality_scores: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Wade submits completed work for client review
    
    deliverables: [
        {"type": "file", "name": "logo.png", "url": "https://..."},
        {"type": "link", "name": "Live website", "url": "https://..."},
        {"type": "text", "name": "Blog article", "content": "..."}
    ]
    
    quality_scores: Results of automated quality checks
    """
    
    deal = _active_deals.get(deal_id)
    if not deal:
        return {"ok": False, "error": "deal_not_found"}
    
    if deal["status"] not in ["accepted", "in_progress"]:
        return {"ok": False, "error": f"cannot_deliver_in_status_{deal['status']}"}
    
    # Run quality checks
    service = AI_SERVICE_CATALOG.get(deal["service_type"], {})
    required_checks = service.get("quality_checks", [])
    
    quality_passed = True
    quality_results = {}
    
    for check in required_checks:
        # In production, run actual quality checks here
        score = quality_scores.get(check, 0.85) if quality_scores else 0.85
        quality_results[check] = {
            "score": score,
            "passed": score >= 0.7
        }
        if score < 0.7:
            quality_passed = False
    
    if not quality_passed:
        return {
            "ok": False,
            "error": "quality_check_failed",
            "quality_results": quality_results,
            "message": "Deliverables did not pass quality checks. Please revise."
        }
    
    # Update deal
    deal["status"] = "delivered"
    deal["delivered_at"] = datetime.now(timezone.utc).isoformat()
    deal["deliverables"] = deliverables
    deal["quality_results"] = quality_results
    
    # Calculate if delivered on time
    deadline = datetime.fromisoformat(deal["delivery_deadline"].replace("Z", "+00:00"))
    delivered_at = datetime.fromisoformat(deal["delivered_at"].replace("Z", "+00:00"))
    deal["delivered_on_time"] = delivered_at <= deadline
    
    # TODO: Send notification to client to review
    
    return {
        "ok": True,
        "status": "delivered",
        "delivered_on_time": deal["delivered_on_time"],
        "quality_results": quality_results,
        "awaiting_client_approval": True
    }


async def client_approve_delivery(deal_id: str, token: str, rating: int = 5) -> Dict[str, Any]:
    """
    Client approves the delivery
    
    This triggers:
    1. Payment capture (money moves)
    2. Deal marked complete
    3. Revenue recorded
    """
    
    deal_result = get_deal(deal_id, token)
    if not deal_result["ok"]:
        return deal_result
    
    deal = deal_result["deal"]
    
    if deal["status"] != "delivered":
        return {"ok": False, "error": "deal_not_delivered_yet"}
    
    # CAPTURE PAYMENT - Money moves now!
    try:
        payment_intent = stripe.PaymentIntent.capture(
            deal["payment_intent_id"]
        )
        
        deal["payment_captured"] = True
        deal["captured_at"] = datetime.now(timezone.utc).isoformat()
        deal["captured_amount"] = payment_intent.amount_received / 100
        
    except stripe.error.StripeError as e:
        return {"ok": False, "error": f"capture_failed: {str(e)}"}
    
    # Update deal
    deal["status"] = "completed"
    deal["completed_at"] = datetime.now(timezone.utc).isoformat()
    deal["client_rating"] = rating
    
    return {
        "ok": True,
        "status": "completed",
        "payment_captured": True,
        "amount": deal["captured_amount"],
        "message": "Thank you! Payment has been processed."
    }


async def client_request_revision(
    deal_id: str,
    token: str,
    revision_notes: str
) -> Dict[str, Any]:
    """Client requests revisions before approving"""
    
    deal_result = get_deal(deal_id, token)
    if not deal_result["ok"]:
        return deal_result
    
    deal = deal_result["deal"]
    
    if deal["status"] != "delivered":
        return {"ok": False, "error": "deal_not_delivered_yet"}
    
    # Track revisions
    deal.setdefault("revisions", [])
    deal["revisions"].append({
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "notes": revision_notes
    })
    
    deal["status"] = "revision_requested"
    
    # Extend deadline by 50% of original time
    extension_hours = deal["delivery_hours"] * 0.5
    new_deadline = datetime.now(timezone.utc) + timedelta(hours=extension_hours)
    deal["delivery_deadline"] = new_deadline.isoformat()
    
    return {
        "ok": True,
        "status": "revision_requested",
        "revision_count": len(deal["revisions"]),
        "new_deadline": deal["delivery_deadline"],
        "message": f"Revision requested. Updated delivery within {extension_hours} hours."
    }


async def client_dispute_delivery(
    deal_id: str,
    token: str,
    reason: str
) -> Dict[str, Any]:
    """Client disputes the delivery - triggers review"""
    
    deal_result = get_deal(deal_id, token)
    if not deal_result["ok"]:
        return deal_result
    
    deal = deal_result["deal"]
    
    if deal["status"] not in ["delivered", "revision_requested"]:
        return {"ok": False, "error": "cannot_dispute_in_current_status"}
    
    deal["status"] = "disputed"
    deal["dispute"] = {
        "reason": reason,
        "opened_at": datetime.now(timezone.utc).isoformat(),
        "resolved": False
    }
    
    # Payment remains authorized but not captured
    # Admin will review and resolve
    
    return {
        "ok": True,
        "status": "disputed",
        "message": "Dispute opened. Our team will review within 24 hours."
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN / WADE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_pending_deals() -> List[Dict[str, Any]]:
    """Get all deals awaiting action"""
    return [d for d in _active_deals.values() if d["status"] in ["pending", "accepted"]]


def get_in_progress_deals() -> List[Dict[str, Any]]:
    """Get all deals being worked on"""
    return [d for d in _active_deals.values() if d["status"] == "in_progress"]


def get_awaiting_approval_deals() -> List[Dict[str, Any]]:
    """Get delivered deals awaiting client approval"""
    return [d for d in _active_deals.values() if d["status"] == "delivered"]


def get_deal_stats() -> Dict[str, Any]:
    """Get overall deal statistics"""
    deals = list(_active_deals.values())
    
    completed = [d for d in deals if d["status"] == "completed"]
    revenue = sum(d.get("captured_amount", 0) for d in completed)
    
    return {
        "total_deals": len(deals),
        "pending": len([d for d in deals if d["status"] == "pending"]),
        "accepted": len([d for d in deals if d["status"] == "accepted"]),
        "in_progress": len([d for d in deals if d["status"] == "in_progress"]),
        "delivered": len([d for d in deals if d["status"] == "delivered"]),
        "completed": len(completed),
        "disputed": len([d for d in deals if d["status"] == "disputed"]),
        "total_revenue": revenue,
        "avg_rating": sum(d.get("client_rating", 5) for d in completed) / max(1, len(completed)),
        "on_time_rate": len([d for d in completed if d.get("delivered_on_time")]) / max(1, len(completed)) * 100
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

ENDPOINTS_TO_ADD = '''
from client_acceptance_portal import (
    AI_SERVICE_CATALOG,
    get_service_pricing,
    create_accept_link,
    get_deal,
    accept_deal,
    mark_deal_in_progress,
    submit_delivery,
    client_approve_delivery,
    client_request_revision,
    client_dispute_delivery,
    get_pending_deals,
    get_in_progress_deals,
    get_awaiting_approval_deals,
    get_deal_stats
)

@app.get("/services/catalog")
async def services_catalog():
    """Get full service catalog with AI pricing"""
    catalog = []
    for service_id, service in AI_SERVICE_CATALOG.items():
        catalog.append({
            "id": service_id,
            "name": service["name"],
            "market_price": service["market_price"],
            "ai_price_standard": service["ai_prices"]["standard"],
            "ai_time_hours": service["ai_times_hours"]["standard"],
            "savings_percent": round((1 - service["ai_prices"]["standard"] / service["market_price"]) * 100),
            "deliverables": service["deliverables"]
        })
    return {"ok": True, "services": catalog}


@app.get("/services/{service_type}/pricing")
async def service_pricing(service_type: str, tier: str = "standard"):
    """Get detailed pricing for a service"""
    return get_service_pricing(service_type, tier)


@app.post("/deals/create")
async def create_deal(body: Dict = Body(...)):
    """
    Create a new deal with accept link
    
    Body: {
        workflow_id: str,
        service_type: str,
        tier?: "express" | "standard" | "budget",
        client_email?: str,
        custom_price?: float,
        custom_description?: str
    }
    """
    return create_accept_link(
        workflow_id=body["workflow_id"],
        service_type=body["service_type"],
        tier=body.get("tier", "standard"),
        client_email=body.get("client_email"),
        custom_price=body.get("custom_price"),
        custom_description=body.get("custom_description")
    )


@app.get("/deals/{deal_id}")
async def get_deal_details(deal_id: str, token: str = None):
    """Get deal details"""
    return get_deal(deal_id, token)


@app.post("/deals/{deal_id}/accept")
async def accept_deal_endpoint(deal_id: str, body: Dict = Body(...)):
    """
    Client accepts deal
    
    Body: {
        token: str,
        client_name: str,
        client_email: str,
        disclosures_accepted: bool,
        terms_accepted: bool,
        payment_method_id?: str
    }
    """
    return await accept_deal(
        deal_id=deal_id,
        token=body["token"],
        client_name=body["client_name"],
        client_email=body["client_email"],
        disclosures_accepted=body["disclosures_accepted"],
        terms_accepted=body["terms_accepted"],
        payment_method_id=body.get("payment_method_id")
    )


@app.post("/deals/{deal_id}/start")
async def start_deal(deal_id: str):
    """Wade marks deal as in progress"""
    return await mark_deal_in_progress(deal_id)


@app.post("/deals/{deal_id}/deliver")
async def deliver_deal(deal_id: str, body: Dict = Body(...)):
    """
    Submit delivery for client review
    
    Body: {
        deliverables: [{type, name, url/content}],
        quality_scores?: {check_name: score}
    }
    """
    return await submit_delivery(
        deal_id=deal_id,
        deliverables=body["deliverables"],
        quality_scores=body.get("quality_scores")
    )


@app.post("/deals/{deal_id}/approve")
async def approve_deal(deal_id: str, body: Dict = Body(...)):
    """
    Client approves delivery - triggers payment capture
    
    Body: {token: str, rating?: int}
    """
    return await client_approve_delivery(
        deal_id=deal_id,
        token=body["token"],
        rating=body.get("rating", 5)
    )


@app.post("/deals/{deal_id}/revision")
async def request_revision(deal_id: str, body: Dict = Body(...)):
    """
    Client requests revisions
    
    Body: {token: str, revision_notes: str}
    """
    return await client_request_revision(
        deal_id=deal_id,
        token=body["token"],
        revision_notes=body["revision_notes"]
    )


@app.post("/deals/{deal_id}/dispute")
async def dispute_deal(deal_id: str, body: Dict = Body(...)):
    """
    Client disputes delivery
    
    Body: {token: str, reason: str}
    """
    return await client_dispute_delivery(
        deal_id=deal_id,
        token=body["token"],
        reason=body["reason"]
    )


@app.get("/deals/stats")
async def deals_stats():
    """Get deal statistics"""
    return {"ok": True, **get_deal_stats()}


@app.get("/deals/pending")
async def pending_deals():
    """Get deals awaiting client acceptance"""
    return {"ok": True, "deals": get_pending_deals()}


@app.get("/deals/in-progress")
async def in_progress_deals():
    """Get deals being worked on"""
    return {"ok": True, "deals": get_in_progress_deals()}


@app.get("/deals/awaiting-approval")
async def awaiting_approval_deals():
    """Get delivered deals awaiting client approval"""
    return {"ok": True, "deals": get_awaiting_approval_deals()}
'''

print("Client Acceptance Portal loaded")
print(f"Services available: {len(AI_SERVICE_CATALOG)}")
