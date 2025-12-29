"""
THIRD-PARTY MONETIZATION ENGINE (AME/AMG)
Weaponizes social media traffic from Instagram, TikTok, Facebook, etc.

Flow:
1. User clicks your link on Instagram/TikTok/Facebook
2. Land on aigentsy.com with tracking params
3. AME triggers: cart nudges, exit intent, scarcity, social proof
4. AMG optimizes: pricing, messaging, timing
5. Convert to sale with AIGx rewards

Revenue Streams:
- Direct sales (templates, services)
- Affiliate commissions
- Lead generation
- Subscription signups
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum
import json


class TrafficSource(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"
    PINTEREST = "pinterest"
    REDDIT = "reddit"
    ORGANIC = "organic"
    DIRECT = "direct"


class MonetizationTactic(str, Enum):
    CART_NUDGE = "cart_nudge"              # Abandoned cart reminder
    EXIT_INTENT = "exit_intent"            # Popup when leaving
    SCARCITY = "scarcity"                  # Limited time/quantity
    SOCIAL_PROOF = "social_proof"          # "X people bought this"
    FIRST_TIME_DISCOUNT = "first_discount" # 10% off first purchase
    BUNDLE_UPSELL = "bundle_upsell"        # "Buy 2 get 10% off"
    AIGX_BONUS = "aigx_bonus"              # Earn AIGx with purchase
    TIME_SENSITIVE = "time_sensitive"      # "Offer expires in 1 hour"
    FREE_TRIAL = "free_trial"              # "Try free for 7 days"
    CREATOR_CODE = "creator_code"          # Affiliate/creator codes


# ============================================================
# TRAFFIC TRACKING & ATTRIBUTION
# ============================================================

def parse_traffic_source(url: str, referrer: str, utm_params: Dict) -> Dict[str, Any]:
    """
    Identify where traffic came from
    
    Examples:
    - instagram.com → Instagram
    - utm_source=tiktok → TikTok
    - /start?creator=wade123 → Creator referral
    """
    
    source = TrafficSource.DIRECT
    campaign = None
    creator_code = None
    
    # Check UTM params
    if utm_params.get('utm_source'):
        source_map = {
            'instagram': TrafficSource.INSTAGRAM,
            'tiktok': TrafficSource.TIKTOK,
            'facebook': TrafficSource.FACEBOOK,
            'twitter': TrafficSource.TWITTER,
            'youtube': TrafficSource.YOUTUBE,
            'linkedin': TrafficSource.LINKEDIN,
            'pinterest': TrafficSource.PINTEREST,
            'reddit': TrafficSource.REDDIT
        }
        source = source_map.get(utm_params['utm_source'].lower(), TrafficSource.DIRECT)
        campaign = utm_params.get('utm_campaign')
    
    # Check referrer
    elif referrer:
        if 'instagram.com' in referrer:
            source = TrafficSource.INSTAGRAM
        elif 'tiktok.com' in referrer:
            source = TrafficSource.TIKTOK
        elif 'facebook.com' in referrer or 'fb.com' in referrer:
            source = TrafficSource.FACEBOOK
        elif 'twitter.com' in referrer or 'x.com' in referrer:
            source = TrafficSource.TWITTER
        elif 'youtube.com' in referrer:
            source = TrafficSource.YOUTUBE
        elif 'linkedin.com' in referrer:
            source = TrafficSource.LINKEDIN
    
    # Check for creator codes
    if 'creator=' in url or 'ref=' in url:
        # Extract from URL
        if 'creator=' in url:
            creator_code = url.split('creator=')[1].split('&')[0]
        elif 'ref=' in url:
            creator_code = url.split('ref=')[1].split('&')[0]
    
    return {
        'source': source,
        'campaign': campaign,
        'creator_code': creator_code,
        'tracked_at': datetime.now(timezone.utc).isoformat()
    }


# ============================================================
# MONETIZATION TACTICS BY PLATFORM
# ============================================================

class PlatformMonetizationConfig:
    """
    Different tactics work better on different platforms
    """
    
    CONFIGS = {
        TrafficSource.INSTAGRAM: {
            'primary_tactics': [
                MonetizationTactic.SOCIAL_PROOF,
                MonetizationTactic.FIRST_TIME_DISCOUNT,
                MonetizationTactic.AIGX_BONUS
            ],
            'messaging': {
                'tone': 'visual',
                'urgency_level': 'medium',
                'discount_range': (10, 20),  # 10-20% off
                'aigx_multiplier': 1.5  # 50% bonus AIGx
            },
            'timing': {
                'cart_nudge_delay': 5,  # 5 minutes
                'exit_intent_enabled': True,
                'scarcity_threshold': 10  # Show when <10 left
            }
        },
        
        TrafficSource.TIKTOK: {
            'primary_tactics': [
                MonetizationTactic.TIME_SENSITIVE,
                MonetizationTactic.BUNDLE_UPSELL,
                MonetizationTactic.AIGX_BONUS
            ],
            'messaging': {
                'tone': 'urgent',
                'urgency_level': 'high',
                'discount_range': (15, 25),
                'aigx_multiplier': 2.0  # 100% bonus AIGx
            },
            'timing': {
                'cart_nudge_delay': 3,  # Faster for TikTok
                'exit_intent_enabled': True,
                'scarcity_threshold': 5
            }
        },
        
        TrafficSource.FACEBOOK: {
            'primary_tactics': [
                MonetizationTactic.SOCIAL_PROOF,
                MonetizationTactic.FREE_TRIAL,
                MonetizationTactic.BUNDLE_UPSELL
            ],
            'messaging': {
                'tone': 'trustworthy',
                'urgency_level': 'low',
                'discount_range': (10, 15),
                'aigx_multiplier': 1.2
            },
            'timing': {
                'cart_nudge_delay': 10,
                'exit_intent_enabled': True,
                'scarcity_threshold': 20
            }
        },
        
        TrafficSource.LINKEDIN: {
            'primary_tactics': [
                MonetizationTactic.FREE_TRIAL,
                MonetizationTactic.SOCIAL_PROOF,
                MonetizationTactic.BUNDLE_UPSELL
            ],
            'messaging': {
                'tone': 'professional',
                'urgency_level': 'low',
                'discount_range': (5, 10),
                'aigx_multiplier': 1.0
            },
            'timing': {
                'cart_nudge_delay': 15,
                'exit_intent_enabled': False,  # Less pushy
                'scarcity_threshold': 50
            }
        },
        
        TrafficSource.YOUTUBE: {
            'primary_tactics': [
                MonetizationTactic.CREATOR_CODE,
                MonetizationTactic.FIRST_TIME_DISCOUNT,
                MonetizationTactic.AIGX_BONUS
            ],
            'messaging': {
                'tone': 'educational',
                'urgency_level': 'medium',
                'discount_range': (10, 20),
                'aigx_multiplier': 1.5
            },
            'timing': {
                'cart_nudge_delay': 7,
                'exit_intent_enabled': True,
                'scarcity_threshold': 15
            }
        }
    }
    
    @classmethod
    def get_config(cls, source: TrafficSource) -> Dict:
        return cls.CONFIGS.get(source, cls.CONFIGS[TrafficSource.INSTAGRAM])


# ============================================================
# DYNAMIC MONETIZATION ENGINE
# ============================================================

def generate_monetization_strategy(
    visitor_data: Dict[str, Any],
    product_data: Dict[str, Any],
    session_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate personalized monetization strategy
    
    Args:
        visitor_data: {source, campaign, creator_code, is_first_visit}
        product_data: {id, price, inventory, category}
        session_data: {time_on_site, pages_viewed, cart_items}
    
    Returns:
        Strategy with tactics, messaging, timing
    """
    
    source = visitor_data.get('source', TrafficSource.DIRECT)
    config = PlatformMonetizationConfig.get_config(source)
    
    # Select tactics based on session behavior
    active_tactics = []
    
    # Always show AIGx bonus
    active_tactics.append({
        'tactic': MonetizationTactic.AIGX_BONUS,
        'message': f"Earn {int(product_data['price'] * config['messaging']['aigx_multiplier'])} AIGx with this purchase!",
        'aigx_amount': int(product_data['price'] * config['messaging']['aigx_multiplier'])
    })
    
    # First-time visitor discount
    if visitor_data.get('is_first_visit'):
        discount_pct = config['messaging']['discount_range'][0]
        active_tactics.append({
            'tactic': MonetizationTactic.FIRST_TIME_DISCOUNT,
            'message': f"Welcome! Get {discount_pct}% off your first purchase",
            'discount_pct': discount_pct,
            'code': f"FIRST{discount_pct}"
        })
    
    # Cart abandonment
    if session_data.get('cart_items') and session_data.get('time_on_site') > config['timing']['cart_nudge_delay'] * 60:
        active_tactics.append({
            'tactic': MonetizationTactic.CART_NUDGE,
            'message': "Don't forget! Your cart is waiting",
            'trigger': 'time_based'
        })
    
    # Low inventory scarcity
    if product_data.get('inventory', 100) < config['timing']['scarcity_threshold']:
        active_tactics.append({
            'tactic': MonetizationTactic.SCARCITY,
            'message': f"Only {product_data['inventory']} left in stock!",
            'inventory_count': product_data['inventory']
        })
    
    # Social proof (if available)
    if product_data.get('recent_purchases', 0) > 0:
        active_tactics.append({
            'tactic': MonetizationTactic.SOCIAL_PROOF,
            'message': f"{product_data['recent_purchases']} people bought this in the last 24 hours",
            'count': product_data['recent_purchases']
        })
    
    # Exit intent (if enabled)
    if config['timing']['exit_intent_enabled']:
        active_tactics.append({
            'tactic': MonetizationTactic.EXIT_INTENT,
            'message': "Wait! Take 15% off before you go",
            'trigger': 'exit',
            'discount_pct': 15,
            'code': "STAYWITHUS15"
        })
    
    # Creator code bonus
    if visitor_data.get('creator_code'):
        active_tactics.append({
            'tactic': MonetizationTactic.CREATOR_CODE,
            'message': f"Creator bonus: Extra 10% off with code {visitor_data['creator_code']}",
            'code': visitor_data['creator_code'],
            'discount_pct': 10
        })
    
    return {
        'source': source,
        'tactics': active_tactics,
        'messaging_tone': config['messaging']['tone'],
        'urgency_level': config['messaging']['urgency_level'],
        'timing': config['timing'],
        'generated_at': datetime.now(timezone.utc).isoformat()
    }


# ============================================================
# FRONTEND INTEGRATION (JavaScript Snippets)
# ============================================================

def generate_frontend_scripts(strategy: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate JavaScript to inject into frontend
    """
    
    scripts = {}
    
    # Cart nudge script
    if any(t['tactic'] == MonetizationTactic.CART_NUDGE for t in strategy['tactics']):
        cart_nudge = next(t for t in strategy['tactics'] if t['tactic'] == MonetizationTactic.CART_NUDGE)
        scripts['cart_nudge'] = f"""
// Cart Abandonment Nudge
setTimeout(() => {{
    if (document.getElementById('cart-count').innerText > 0) {{
        showNotification('{cart_nudge['message']}', 'info');
    }}
}}, {strategy['timing']['cart_nudge_delay'] * 60 * 1000});
"""
    
    # Exit intent script
    if any(t['tactic'] == MonetizationTactic.EXIT_INTENT for t in strategy['tactics']):
        exit_tactic = next(t for t in strategy['tactics'] if t['tactic'] == MonetizationTactic.EXIT_INTENT)
        scripts['exit_intent'] = f"""
// Exit Intent Popup
document.addEventListener('mouseout', (e) => {{
    if (e.clientY < 10) {{
        showModal({{
            title: '{exit_tactic['message']}',
            code: '{exit_tactic['code']}',
            discount: {exit_tactic['discount_pct']}
        }});
    }}
}}, {{ once: true }});
"""
    
    # AIGx bonus banner
    if any(t['tactic'] == MonetizationTactic.AIGX_BONUS for t in strategy['tactics']):
        aigx_tactic = next(t for t in strategy['tactics'] if t['tactic'] == MonetizationTactic.AIGX_BONUS)
        scripts['aigx_banner'] = f"""
// AIGx Bonus Banner
showBanner({{
    message: '{aigx_tactic['message']}',
    type: 'success',
    persistent: true,
    aigx_amount: {aigx_tactic['aigx_amount']}
}});
"""
    
    # Scarcity indicator
    if any(t['tactic'] == MonetizationTactic.SCARCITY for t in strategy['tactics']):
        scarcity = next(t for t in strategy['tactics'] if t['tactic'] == MonetizationTactic.SCARCITY)
        scripts['scarcity'] = f"""
// Scarcity Indicator
document.querySelectorAll('.product-inventory').forEach(el => {{
    el.innerHTML = '<span class="text-red-600 font-bold">{scarcity['message']}</span>';
    el.classList.add('pulse');
}});
"""
    
    return scripts


# ============================================================
# CONVERSION TRACKING
# ============================================================

def track_conversion(
    visitor_data: Dict[str, Any],
    purchase_data: Dict[str, Any],
    tactics_shown: List[str]
) -> Dict[str, Any]:
    """
    Track which tactics led to conversion
    Used by AMG to optimize
    """
    
    conversion = {
        'visitor_id': visitor_data.get('visitor_id'),
        'source': visitor_data.get('source'),
        'creator_code': visitor_data.get('creator_code'),
        'campaign': visitor_data.get('campaign'),
        'purchase_amount': purchase_data.get('total'),
        'tactics_shown': tactics_shown,
        'converted_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Calculate attribution
    # Which tactic gets credit?
    if 'exit_intent' in tactics_shown:
        conversion['primary_tactic'] = 'exit_intent'
        conversion['attribution_confidence'] = 0.9
    elif 'cart_nudge' in tactics_shown:
        conversion['primary_tactic'] = 'cart_nudge'
        conversion['attribution_confidence'] = 0.7
    elif 'first_discount' in tactics_shown:
        conversion['primary_tactic'] = 'first_discount'
        conversion['attribution_confidence'] = 0.8
    else:
        conversion['primary_tactic'] = 'aigx_bonus'
        conversion['attribution_confidence'] = 0.5
    
    return conversion


# ============================================================
# AMG OPTIMIZATION ENGINE
# ============================================================

def optimize_tactics(conversion_history: List[Dict]) -> Dict[str, Any]:
    """
    AMG analyzes conversions and optimizes tactics
    
    Returns updated configuration with:
    - Best performing tactics per source
    - Optimal discount percentages
    - Best timing for nudges
    """
    
    # Group by source
    by_source = {}
    for conv in conversion_history:
        source = conv['source']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(conv)
    
    optimizations = {}
    
    for source, conversions in by_source.items():
        # Calculate conversion rate by tactic
        tactic_performance = {}
        
        for conv in conversions:
            tactic = conv.get('primary_tactic')
            if tactic:
                if tactic not in tactic_performance:
                    tactic_performance[tactic] = {'conversions': 0, 'revenue': 0}
                tactic_performance[tactic]['conversions'] += 1
                tactic_performance[tactic]['revenue'] += conv.get('purchase_amount', 0)
        
        # Rank tactics
        ranked_tactics = sorted(
            tactic_performance.items(),
            key=lambda x: x[1]['conversions'],
            reverse=True
        )
        
        optimizations[source] = {
            'best_tactics': [t[0] for t in ranked_tactics[:3]],
            'performance': tactic_performance,
            'total_conversions': len(conversions),
            'total_revenue': sum(c.get('purchase_amount', 0) for c in conversions)
        }
    
    return optimizations
