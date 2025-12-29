"""
AME/AMG ENDPOINTS
Monetization endpoints for third-party traffic

USAGE: Import these functions into main.py and create endpoints there
"""

from fastapi import Request, Response
from typing import Dict, Any
import json

from third_party_monetization import (
    parse_traffic_source,
    generate_monetization_strategy,
    generate_frontend_scripts,
    track_conversion,
    optimize_tactics
)


# ============================================================
# LANDING PAGE - Track & Monetize
# ============================================================

async def track_visit_handler(request: Request, utm_source: str = None, utm_campaign: str = None, utm_medium: str = None, creator: str = None, ref: str = None) -> Dict:
async def track_visit_handler(
    request: Request,
    utm_source: str = None,
    utm_campaign: str = None,
    utm_medium: str = None,
    creator: str = None,
    ref: str = None
):
    """
    Track visitor from social media
    Returns monetization strategy
    
    Usage in main.py:
    @app.get("/track-visit")
    async def track_visit(request: Request, utm_source: str = None, ...):
        return await track_visit_handler(request, utm_source, ...)
    """
    
    # Parse traffic source
    utm_params = {
        'utm_source': utm_source,
        'utm_campaign': utm_campaign,
        'utm_medium': utm_medium
    }
    
    traffic_data = parse_traffic_source(
        url=str(request.url),
        referrer=request.headers.get('referer', ''),
        utm_params=utm_params
    )
    
    # Add creator code
    if creator or ref:
        traffic_data['creator_code'] = creator or ref
    
    # Check if first visit (simplified - use cookies/session in production)
    traffic_data['is_first_visit'] = not request.cookies.get('returning_visitor')
    
    # Mock visitor and session data
    visitor_data = {
        **traffic_data,
        'visitor_id': request.cookies.get('visitor_id', 'new_visitor')
    }
    
    session_data = {
        'time_on_site': 0,
        'pages_viewed': 1,
        'cart_items': 0
    }
    
    # Mock product data (in production, get from product ID)
    product_data = {
        'id': 'default',
        'price': 497,
        'inventory': 47,
        'recent_purchases': 23,
        'category': 'template'
    }
    
    # Generate strategy
    strategy = generate_monetization_strategy(
        visitor_data,
        product_data,
        session_data
    )
    
    # Generate frontend scripts
    scripts = generate_frontend_scripts(strategy)
    
    # Set returning visitor cookie
    response = Response(content=json.dumps({
        'ok': True,
        'strategy': strategy,
        'scripts': scripts,
        'visitor_id': visitor_data['visitor_id']
    }))
    
    response.set_cookie(
        'returning_visitor',
        'true',
        max_age=30*24*60*60  # 30 days
    )
    
    return response


# ============================================================
# CONVERSION TRACKING
# ============================================================

async def track_conversion_handler(request: Request):
    """
    Track when visitor converts to customer
    
    Body: {
        "visitor_id": "...",
        "purchase_amount": 497,
        "tactics_shown": ["aigx_bonus", "first_discount"],
        "product_id": "template_123"
    }
    """
    
    body = await request.json()
    
    # Get visitor data from cookies/session
    visitor_data = {
        'visitor_id': body.get('visitor_id'),
        'source': request.cookies.get('traffic_source', 'direct'),
        'creator_code': request.cookies.get('creator_code'),
        'campaign': request.cookies.get('campaign')
    }
    
    purchase_data = {
        'total': body.get('purchase_amount'),
        'product_id': body.get('product_id')
    }
    
    tactics_shown = body.get('tactics_shown', [])
    
    # Track conversion
    conversion = track_conversion(visitor_data, purchase_data, tactics_shown)
    
    # TODO: Store conversion in database
    # await store_conversion(conversion)
    
    # Award AIGx if applicable
    aigx_earned = 0
    if 'aigx_bonus' in tactics_shown:
        aigx_earned = int(purchase_data['total'] * 1.5)  # 150% of purchase
        # TODO: Credit AIGx to user account
    
    return {
        'ok': True,
        'conversion_tracked': True,
        'aigx_earned': aigx_earned,
        'conversion_id': conversion.get('visitor_id')
    }


# ============================================================
# AMG OPTIMIZATION
# ============================================================

async def amg_optimize_handler():
    """
    AMG analyzes conversion data and returns optimizations
    
    Returns which tactics work best per platform
    """
    
    # TODO: Load conversion history from database
    # For now, return mock optimization data
    
    mock_conversions = [
        {
            'source': 'instagram',
            'primary_tactic': 'aigx_bonus',
            'purchase_amount': 497
        },
        {
            'source': 'tiktok',
            'primary_tactic': 'time_sensitive',
            'purchase_amount': 997
        },
        {
            'source': 'instagram',
            'primary_tactic': 'first_discount',
            'purchase_amount': 497
        }
    ]
    
    optimizations = optimize_tactics(mock_conversions)
    
    return {
        'ok': True,
        'optimizations': optimizations,
        'recommendations': {
            'instagram': {
                'best_tactic': 'aigx_bonus',
                'recommended_discount': 15,
                'recommended_aigx_multiplier': 1.5
            },
            'tiktok': {
                'best_tactic': 'time_sensitive',
                'recommended_discount': 20,
                'recommended_aigx_multiplier': 2.0
            }
        }
    }


# ============================================================
# CREATOR CODES
# ============================================================

async def register_creator_handler(body: Dict):
    """
    Register a creator code for affiliate tracking
    
    Body: {
        "creator_name": "wade",
        "platform": "instagram",
        "commission_pct": 10
    }
    """
    
    creator_name = body.get('creator_name')
    platform = body.get('platform')
    commission_pct = body.get('commission_pct', 10)
    
    creator_code = f"{creator_name}_{platform[:3]}".lower()
    
    # TODO: Store in database
    
    creator_link = f"https://aigentsy.com/start?creator={creator_code}"
    
    return {
        'ok': True,
        'creator_code': creator_code,
        'creator_link': creator_link,
        'commission_pct': commission_pct,
        'tracking_enabled': True
    }


async def get_creator_stats_handler(creator_code: str):
    """
    Get creator performance stats
    """
    
    # TODO: Load from database
    
    mock_stats = {
        'creator_code': creator_code,
        'total_clicks': 1247,
        'total_conversions': 47,
        'conversion_rate': 3.77,
        'total_revenue': 23379,
        'commission_earned': 2337.90,
        'top_platform': 'instagram',
        'best_performing_tactic': 'aigx_bonus'
    }
    
    return {
        'ok': True,
        **mock_stats
    }


# ============================================================
# SOCIAL MEDIA WIDGETS
# ============================================================

async def instagram_bio_link_widget_handler():
    """
    Generate Instagram bio link landing page
    Shows multiple links/products in mobile-optimized layout
    """
    
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>AiGentsy - Wade's Links</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-purple-500 to-pink-500 min-h-screen">
    <div class="max-w-md mx-auto p-6">
        <div class="text-center mb-8">
            <div class="w-24 h-24 rounded-full bg-white mx-auto mb-4 flex items-center justify-center">
                <span class="text-4xl">🤖</span>
            </div>
            <h1 class="text-white text-2xl font-bold mb-2">@AiGentsy</h1>
            <p class="text-white/80">Build your AI business in 1 click</p>
        </div>
        
        <div class="space-y-4">
            <a href="/start?creator=wade_ig" 
               class="block bg-white rounded-lg p-4 shadow-lg hover:scale-105 transition">
                <div class="font-bold text-lg">🚀 Launch Your AI Business</div>
                <div class="text-gray-600 text-sm">Free + earn AIGx</div>
            </a>
            
            <a href="/templates?creator=wade_ig" 
               class="block bg-white rounded-lg p-4 shadow-lg hover:scale-105 transition">
                <div class="font-bold text-lg">📦 160+ Business Templates</div>
                <div class="text-gray-600 text-sm">Copy & launch instantly</div>
            </a>
            
            <a href="/services?creator=wade_ig" 
               class="block bg-white rounded-lg p-4 shadow-lg hover:scale-105 transition">
                <div class="font-bold text-lg">⚡ AI Services</div>
                <div class="text-gray-600 text-sm">Get it done with AI</div>
            </a>
        </div>
        
        <div class="mt-8 text-center text-white text-sm">
            <p>✨ Special: Get 50% bonus AIGx on first purchase</p>
        </div>
    </div>
    
    <script>
        // Track visit
        fetch('/track-visit?utm_source=instagram&creator=wade_ig')
            .then(r => r.json())
            .then(data => console.log('Tracking:', data));
    </script>
</body>
</html>
    """
    
    return Response(content=html, media_type="text/html")
