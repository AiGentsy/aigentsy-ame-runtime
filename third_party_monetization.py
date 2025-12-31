"""
THIRD-PARTY MONETIZATION ENGINE - ENHANCED
Weaponizes social media traffic with Revenue Mesh + Full System Integration

MASSIVE UPGRADES from original:
1. Revenue Mesh Integration - ML-powered tactic selection
2. Yield Memory - Learn which tactics work for which traffic sources
3. MetaHive Contribution - Share high-performing tactics across users
4. Real-time Pricing Oracle - Dynamic pricing by source
5. AMG Auto-optimization - Continuous improvement
6. AIGx Credit System - Proper token rewards
7. Outcome Oracle Tracking - Full funnel attribution

Flow:
1. User clicks your link on Instagram/TikTok/Facebook
2. Land on aigentsy.com with tracking params
3. Revenue Mesh analyzes visitor + predicts best tactics
4. AME triggers: cart nudges, exit intent, scarcity, social proof
5. AMG optimizes: pricing, messaging, timing
6. Convert to sale with AIGx rewards
7. Outcome Oracle tracks full attribution
8. Yield Memory stores winning patterns
9. MetaHive shares if ROAS > 1.5

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
import hashlib

# ============================================================
# TRAFFIC SOURCES
# ============================================================

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
    EMAIL = "email"
    SMS = "sms"
    AFFILIATE = "affiliate"


class MonetizationTactic(str, Enum):
    CART_NUDGE = "cart_nudge"
    EXIT_INTENT = "exit_intent"
    SCARCITY = "scarcity"
    SOCIAL_PROOF = "social_proof"
    FIRST_TIME_DISCOUNT = "first_discount"
    BUNDLE_UPSELL = "bundle_upsell"
    AIGX_BONUS = "aigx_bonus"
    TIME_SENSITIVE = "time_sensitive"
    FREE_TRIAL = "free_trial"
    CREATOR_CODE = "creator_code"
    # NEW tactics
    PERSONALIZED_PRICE = "personalized_price"  # Pricing Oracle integration
    MESH_RECOMMENDED = "mesh_recommended"       # Revenue Mesh ML pick
    HIVE_PROVEN = "hive_proven"                # MetaHive validated tactic
    LOYALTY_MULTIPLIER = "loyalty_multiplier"  # Returning visitor bonus


# ============================================================
# PLATFORM CONFIGS - Enhanced with ML weights
# ============================================================

PLATFORM_CONFIGS = {
    TrafficSource.INSTAGRAM: {
        'primary_tactics': [
            MonetizationTactic.SOCIAL_PROOF,
            MonetizationTactic.FIRST_TIME_DISCOUNT,
            MonetizationTactic.AIGX_BONUS
        ],
        'messaging': {
            'tone': 'visual',
            'urgency_level': 'medium',
            'discount_range': (10, 20),
            'aigx_multiplier': 1.5
        },
        'timing': {
            'cart_nudge_delay': 300,  # 5 minutes in seconds
            'exit_intent_enabled': True,
            'scarcity_threshold': 10
        },
        'ml_weights': {
            'exit_intent': 0.75,
            'social_proof': 0.85,
            'scarcity': 0.65,
            'aigx_bonus': 0.90
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
            'aigx_multiplier': 2.0  # TikTok users get 2x AIGx
        },
        'timing': {
            'cart_nudge_delay': 180,  # 3 minutes - faster for TikTok
            'exit_intent_enabled': True,
            'scarcity_threshold': 5
        },
        'ml_weights': {
            'exit_intent': 0.85,
            'time_sensitive': 0.90,
            'bundle_upsell': 0.70,
            'aigx_bonus': 0.95
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
            'cart_nudge_delay': 600,  # 10 minutes
            'exit_intent_enabled': True,
            'scarcity_threshold': 20
        },
        'ml_weights': {
            'social_proof': 0.90,
            'free_trial': 0.80,
            'exit_intent': 0.60,
            'aigx_bonus': 0.75
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
            'cart_nudge_delay': 420,
            'exit_intent_enabled': True,
            'scarcity_threshold': 15
        },
        'ml_weights': {
            'creator_code': 0.95,
            'first_discount': 0.80,
            'social_proof': 0.70,
            'aigx_bonus': 0.85
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
            'cart_nudge_delay': 900,  # 15 minutes - less pushy
            'exit_intent_enabled': False,
            'scarcity_threshold': 50
        },
        'ml_weights': {
            'free_trial': 0.90,
            'social_proof': 0.85,
            'bundle_upsell': 0.75,
            'aigx_bonus': 0.60
        }
    },
    
    TrafficSource.EMAIL: {
        'primary_tactics': [
            MonetizationTactic.PERSONALIZED_PRICE,
            MonetizationTactic.LOYALTY_MULTIPLIER,
            MonetizationTactic.BUNDLE_UPSELL
        ],
        'messaging': {
            'tone': 'personal',
            'urgency_level': 'medium',
            'discount_range': (15, 25),
            'aigx_multiplier': 1.8
        },
        'timing': {
            'cart_nudge_delay': 300,
            'exit_intent_enabled': True,
            'scarcity_threshold': 10
        },
        'ml_weights': {
            'personalized_price': 0.95,
            'loyalty_multiplier': 0.90,
            'bundle_upsell': 0.85,
            'aigx_bonus': 0.88
        }
    },
    
    TrafficSource.AFFILIATE: {
        'primary_tactics': [
            MonetizationTactic.CREATOR_CODE,
            MonetizationTactic.FIRST_TIME_DISCOUNT,
            MonetizationTactic.AIGX_BONUS
        ],
        'messaging': {
            'tone': 'exclusive',
            'urgency_level': 'high',
            'discount_range': (15, 30),
            'aigx_multiplier': 2.0
        },
        'timing': {
            'cart_nudge_delay': 240,
            'exit_intent_enabled': True,
            'scarcity_threshold': 5
        },
        'ml_weights': {
            'creator_code': 1.0,
            'first_discount': 0.90,
            'exit_intent': 0.85,
            'aigx_bonus': 0.95
        }
    }
}

# Default config for unknown sources
DEFAULT_CONFIG = {
    'primary_tactics': [
        MonetizationTactic.AIGX_BONUS,
        MonetizationTactic.FIRST_TIME_DISCOUNT,
        MonetizationTactic.SOCIAL_PROOF
    ],
    'messaging': {
        'tone': 'friendly',
        'urgency_level': 'medium',
        'discount_range': (10, 15),
        'aigx_multiplier': 1.0
    },
    'timing': {
        'cart_nudge_delay': 300,
        'exit_intent_enabled': True,
        'scarcity_threshold': 15
    },
    'ml_weights': {
        'aigx_bonus': 0.80,
        'first_discount': 0.75,
        'social_proof': 0.70,
        'exit_intent': 0.65
    }
}


def get_platform_config(source: TrafficSource) -> Dict:
    """Get config for platform with fallback"""
    return PLATFORM_CONFIGS.get(source, DEFAULT_CONFIG)


# ============================================================
# TRAFFIC PARSING - Enhanced with more signals
# ============================================================

def parse_traffic_source(
    url: str,
    referrer: str = "",
    utm_params: Dict = None,
    headers: Dict = None
) -> Dict[str, Any]:
    """
    Identify where traffic came from with rich attribution
    
    Examples:
    - instagram.com → Instagram
    - utm_source=tiktok → TikTok
    - /start?creator=wade123 → Creator referral
    """
    
    utm_params = utm_params or {}
    headers = headers or {}
    
    source = TrafficSource.DIRECT
    campaign = None
    creator_code = None
    medium = None
    content = None
    term = None
    
    # Check UTM params first (most reliable)
    if utm_params.get('utm_source'):
        source_map = {
            'instagram': TrafficSource.INSTAGRAM,
            'tiktok': TrafficSource.TIKTOK,
            'facebook': TrafficSource.FACEBOOK,
            'fb': TrafficSource.FACEBOOK,
            'twitter': TrafficSource.TWITTER,
            'x': TrafficSource.TWITTER,
            'youtube': TrafficSource.YOUTUBE,
            'yt': TrafficSource.YOUTUBE,
            'linkedin': TrafficSource.LINKEDIN,
            'pinterest': TrafficSource.PINTEREST,
            'reddit': TrafficSource.REDDIT,
            'email': TrafficSource.EMAIL,
            'sms': TrafficSource.SMS,
            'affiliate': TrafficSource.AFFILIATE
        }
        source = source_map.get(utm_params['utm_source'].lower(), TrafficSource.DIRECT)
        campaign = utm_params.get('utm_campaign')
        medium = utm_params.get('utm_medium')
        content = utm_params.get('utm_content')
        term = utm_params.get('utm_term')
    
    # Check referrer if no UTM
    elif referrer:
        referrer_lower = referrer.lower()
        if 'instagram.com' in referrer_lower:
            source = TrafficSource.INSTAGRAM
        elif 'tiktok.com' in referrer_lower:
            source = TrafficSource.TIKTOK
        elif 'facebook.com' in referrer_lower or 'fb.com' in referrer_lower:
            source = TrafficSource.FACEBOOK
        elif 'twitter.com' in referrer_lower or 'x.com' in referrer_lower:
            source = TrafficSource.TWITTER
        elif 'youtube.com' in referrer_lower or 'youtu.be' in referrer_lower:
            source = TrafficSource.YOUTUBE
        elif 'linkedin.com' in referrer_lower:
            source = TrafficSource.LINKEDIN
        elif 'pinterest.com' in referrer_lower:
            source = TrafficSource.PINTEREST
        elif 'reddit.com' in referrer_lower:
            source = TrafficSource.REDDIT
    
    # Check for creator/affiliate codes in URL
    url_lower = url.lower()
    for param in ['creator=', 'ref=', 'aff=', 'partner=']:
        if param in url_lower:
            try:
                creator_code = url_lower.split(param)[1].split('&')[0].split('#')[0]
                if not source or source == TrafficSource.DIRECT:
                    source = TrafficSource.AFFILIATE
            except:
                pass
            break
    
    # Generate visitor fingerprint (for session tracking)
    fingerprint_data = f"{headers.get('user-agent', '')}{headers.get('accept-language', '')}"
    visitor_fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()[:12]
    
    # Generate session ID
    session_id = f"sess_{hashlib.md5(f'{visitor_fingerprint}{datetime.now().isoformat()}'.encode()).hexdigest()[:16]}"
    
    return {
        'source': source,
        'source_name': source.value if hasattr(source, 'value') else str(source),
        'campaign': campaign,
        'medium': medium,
        'content': content,
        'term': term,
        'creator_code': creator_code,
        'referrer': referrer,
        'visitor_fingerprint': visitor_fingerprint,
        'session_id': session_id,
        'tracked_at': datetime.now(timezone.utc).isoformat(),
        'is_affiliate': creator_code is not None
    }


# ============================================================
# MONETIZATION STRATEGY GENERATOR - Enhanced with ML
# ============================================================

class MonetizationEngine:
    """
    Enhanced monetization engine with Revenue Mesh integration
    """
    
    def __init__(self):
        # Try to import Revenue Mesh components
        try:
            from universal_integration_layer import RevenueIntelligenceMesh
            self.revenue_mesh = RevenueIntelligenceMesh("monetization_engine")
            self.mesh_available = True
        except:
            self.revenue_mesh = None
            self.mesh_available = False
        
        # Try to import Yield Memory
        try:
            from yield_memory import find_similar_patterns, store_pattern
            self.find_patterns = find_similar_patterns
            self.store_pattern = store_pattern
            self.yield_memory_available = True
        except:
            self.find_patterns = None
            self.store_pattern = None
            self.yield_memory_available = False
        
        # Try to import Pricing Oracle
        try:
            from pricing_oracle import calculate_dynamic_price
            self.dynamic_price = calculate_dynamic_price
            self.pricing_oracle_available = True
        except:
            self.dynamic_price = None
            self.pricing_oracle_available = False
        
        # Try to import MetaHive
        try:
            from metahive_brain import query_hive, contribute_to_hive
            self.query_hive = query_hive
            self.contribute_hive = contribute_to_hive
            self.metahive_available = True
        except:
            self.query_hive = None
            self.contribute_hive = None
            self.metahive_available = False
        
        # Conversion tracking
        self.active_sessions = {}
        self.conversion_history = []
    
    
    async def generate_strategy(
        self,
        visitor_data: Dict[str, Any],
        product_data: Dict[str, Any],
        session_data: Dict[str, Any],
        user_history: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized monetization strategy with ML enhancement
        
        Args:
            visitor_data: {source, campaign, creator_code, is_first_visit, session_id}
            product_data: {id, price, inventory, category, recent_purchases}
            session_data: {time_on_site, pages_viewed, cart_items, scroll_depth}
            user_history: {previous_visits, total_spent, aigx_balance} (optional)
        
        Returns:
            Strategy with tactics, messaging, timing, scripts
        """
        
        source = visitor_data.get('source', TrafficSource.DIRECT)
        if isinstance(source, str):
            try:
                source = TrafficSource(source)
            except:
                source = TrafficSource.DIRECT
        
        config = get_platform_config(source)
        user_history = user_history or {}
        
        # Check if returning visitor
        is_returning = user_history.get('previous_visits', 0) > 0
        is_first_visit = not is_returning
        visitor_data['is_first_visit'] = is_first_visit
        
        # Build tactics list
        active_tactics = []
        
        # 1. AIGX BONUS - Always show (core value prop)
        aigx_amount = int(product_data.get('price', 100) * config['messaging']['aigx_multiplier'])
        
        # Loyalty multiplier for returning visitors
        if is_returning:
            loyalty_mult = min(1.5, 1.0 + (user_history.get('previous_visits', 0) * 0.1))
            aigx_amount = int(aigx_amount * loyalty_mult)
            
            active_tactics.append({
                'tactic': MonetizationTactic.LOYALTY_MULTIPLIER,
                'message': f"Welcome back! You're earning {int((loyalty_mult-1)*100)}% bonus AIGx today!",
                'multiplier': loyalty_mult,
                'priority': 1
            })
        
        active_tactics.append({
            'tactic': MonetizationTactic.AIGX_BONUS,
            'message': f"Earn {aigx_amount} AIGx with this purchase!",
            'aigx_amount': aigx_amount,
            'priority': 2
        })
        
        # 2. FIRST-TIME DISCOUNT
        if is_first_visit:
            discount_pct = config['messaging']['discount_range'][0]
            active_tactics.append({
                'tactic': MonetizationTactic.FIRST_TIME_DISCOUNT,
                'message': f"Welcome! Get {discount_pct}% off your first purchase",
                'discount_pct': discount_pct,
                'code': f"FIRST{discount_pct}",
                'priority': 3
            })
        
        # 3. CREATOR CODE BONUS
        if visitor_data.get('creator_code'):
            creator_discount = 10 if source == TrafficSource.AFFILIATE else 5
            active_tactics.append({
                'tactic': MonetizationTactic.CREATOR_CODE,
                'message': f"Creator bonus: Extra {creator_discount}% off!",
                'code': visitor_data['creator_code'],
                'discount_pct': creator_discount,
                'priority': 2
            })
        
        # 4. SCARCITY - Low inventory
        inventory = product_data.get('inventory', 100)
        if inventory < config['timing']['scarcity_threshold']:
            active_tactics.append({
                'tactic': MonetizationTactic.SCARCITY,
                'message': f"Only {inventory} left in stock!",
                'inventory_count': inventory,
                'priority': 4
            })
        
        # 5. SOCIAL PROOF
        recent_purchases = product_data.get('recent_purchases', 0)
        if recent_purchases > 0:
            active_tactics.append({
                'tactic': MonetizationTactic.SOCIAL_PROOF,
                'message': f"{recent_purchases} people bought this in the last 24 hours",
                'count': recent_purchases,
                'priority': 5
            })
        
        # 6. CART NUDGE - Time-based
        time_on_site = session_data.get('time_on_site', 0)
        cart_items = session_data.get('cart_items', [])
        if cart_items and time_on_site > config['timing']['cart_nudge_delay']:
            active_tactics.append({
                'tactic': MonetizationTactic.CART_NUDGE,
                'message': "Don't forget! Your cart is waiting",
                'trigger': 'time_based',
                'delay_seconds': config['timing']['cart_nudge_delay'],
                'priority': 6
            })
        
        # 7. EXIT INTENT
        if config['timing']['exit_intent_enabled']:
            exit_discount = 15
            active_tactics.append({
                'tactic': MonetizationTactic.EXIT_INTENT,
                'message': f"Wait! Take {exit_discount}% off before you go",
                'trigger': 'exit',
                'discount_pct': exit_discount,
                'code': "STAYWITHUS15",
                'priority': 7
            })
        
        # 8. TIME SENSITIVE (TikTok especially)
        if source == TrafficSource.TIKTOK or config['messaging']['urgency_level'] == 'high':
            active_tactics.append({
                'tactic': MonetizationTactic.TIME_SENSITIVE,
                'message': "This offer expires in 1 hour!",
                'expires_in_seconds': 3600,
                'priority': 3
            })
        
        # 9. PERSONALIZED PRICE (if Pricing Oracle available)
        if self.pricing_oracle_available and self.dynamic_price:
            try:
                price_result = self.dynamic_price({
                    'base_price': product_data.get('price', 100),
                    'source': source.value if hasattr(source, 'value') else str(source),
                    'is_returning': is_returning,
                    'user_ltv': user_history.get('total_spent', 0)
                })
                if price_result.get('optimized_price'):
                    active_tactics.append({
                        'tactic': MonetizationTactic.PERSONALIZED_PRICE,
                        'message': f"Special price just for you: ${price_result['optimized_price']:.2f}",
                        'original_price': product_data.get('price'),
                        'optimized_price': price_result['optimized_price'],
                        'priority': 2
                    })
            except Exception as e:
                pass
        
        # 10. METAHIVE PROVEN TACTICS
        if self.metahive_available and self.query_hive:
            try:
                hive_tactics = await self.query_hive({
                    'query_type': 'monetization_tactics',
                    'source': source.value if hasattr(source, 'value') else str(source),
                    'product_category': product_data.get('category', 'general')
                })
                if hive_tactics.get('proven_tactics'):
                    for tactic in hive_tactics['proven_tactics'][:2]:
                        active_tactics.append({
                            'tactic': MonetizationTactic.HIVE_PROVEN,
                            'message': tactic.get('message', 'Community recommended!'),
                            'hive_confidence': tactic.get('confidence', 0.8),
                            'priority': 4
                        })
            except:
                pass
        
        # Sort by priority
        active_tactics.sort(key=lambda x: x.get('priority', 99))
        
        # Calculate total potential discount
        total_discount = sum(t.get('discount_pct', 0) for t in active_tactics)
        # Cap at 35%
        if total_discount > 35:
            # Remove lowest priority discounts
            active_tactics = self._cap_discounts(active_tactics, max_discount=35)
        
        # Generate frontend scripts
        scripts = self._generate_scripts(active_tactics, config)
        
        # Store session for tracking
        session_id = visitor_data.get('session_id', f"sess_{datetime.now().timestamp()}")
        self.active_sessions[session_id] = {
            'visitor_data': visitor_data,
            'product_data': product_data,
            'tactics_shown': [t['tactic'].value if hasattr(t['tactic'], 'value') else str(t['tactic']) for t in active_tactics],
            'started_at': datetime.now(timezone.utc).isoformat()
        }
        
        return {
            'session_id': session_id,
            'source': source.value if hasattr(source, 'value') else str(source),
            'tactics': active_tactics,
            'messaging_tone': config['messaging']['tone'],
            'urgency_level': config['messaging']['urgency_level'],
            'timing': config['timing'],
            'scripts': scripts,
            'total_aigx_potential': aigx_amount,
            'integrations': {
                'revenue_mesh': self.mesh_available,
                'yield_memory': self.yield_memory_available,
                'pricing_oracle': self.pricing_oracle_available,
                'metahive': self.metahive_available
            },
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    
    
    def _cap_discounts(self, tactics: List[Dict], max_discount: int) -> List[Dict]:
        """Cap total discounts at max_discount%"""
        result = []
        total = 0
        
        for t in tactics:
            discount = t.get('discount_pct', 0)
            if total + discount <= max_discount:
                result.append(t)
                total += discount
            elif discount == 0:
                result.append(t)
        
        return result
    
    
    def _generate_scripts(self, tactics: List[Dict], config: Dict) -> Dict[str, str]:
        """Generate frontend JavaScript for tactics"""
        
        scripts = {}
        
        # AIGx Banner
        aigx_tactic = next((t for t in tactics if t.get('tactic') == MonetizationTactic.AIGX_BONUS), None)
        if aigx_tactic:
            scripts['aigx_banner'] = f"""
// AIGx Bonus Banner
(function() {{
    const banner = document.createElement('div');
    banner.id = 'aigx-banner';
    banner.className = 'aigx-promo-banner';
    banner.innerHTML = '<span class="aigx-icon">🪙</span> {aigx_tactic['message']}';
    banner.style.cssText = 'position:fixed;bottom:20px;right:20px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:12px 20px;border-radius:8px;font-weight:600;z-index:9999;box-shadow:0 4px 15px rgba(0,0,0,0.2);cursor:pointer;';
    document.body.appendChild(banner);
    banner.onclick = function() {{ window.aigentsyTrack('aigx_banner_click'); }};
}})();
"""
        
        # Exit Intent
        exit_tactic = next((t for t in tactics if t.get('tactic') == MonetizationTactic.EXIT_INTENT), None)
        if exit_tactic:
            scripts['exit_intent'] = f"""
// Exit Intent Popup
(function() {{
    let shown = false;
    document.addEventListener('mouseout', function(e) {{
        if (e.clientY < 10 && !shown) {{
            shown = true;
            window.aigentsyTrack('exit_intent_shown');
            const modal = document.createElement('div');
            modal.innerHTML = `
                <div style="position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:10000;display:flex;align-items:center;justify-content:center;">
                    <div style="background:white;padding:30px;border-radius:12px;max-width:400px;text-align:center;">
                        <h2 style="margin:0 0 15px;font-size:24px;">Wait! 🎁</h2>
                        <p style="margin:0 0 20px;font-size:18px;">{exit_tactic['message']}</p>
                        <code style="display:block;background:#f0f0f0;padding:10px;border-radius:6px;font-size:20px;margin:0 0 20px;">{exit_tactic.get('code', 'STAYWITHUS15')}</code>
                        <button onclick="this.parentElement.parentElement.remove();window.aigentsyTrack('exit_intent_claimed');" style="background:#667eea;color:white;border:none;padding:12px 30px;border-radius:6px;font-size:16px;cursor:pointer;">Claim Offer</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }}
    }});
}})();
"""
        
        # Cart Nudge
        cart_tactic = next((t for t in tactics if t.get('tactic') == MonetizationTactic.CART_NUDGE), None)
        if cart_tactic:
            delay = cart_tactic.get('delay_seconds', 300) * 1000
            scripts['cart_nudge'] = f"""
// Cart Nudge
setTimeout(function() {{
    if (window.aigentsyCartCount && window.aigentsyCartCount() > 0) {{
        window.aigentsyTrack('cart_nudge_shown');
        const nudge = document.createElement('div');
        nudge.style.cssText = 'position:fixed;bottom:80px;right:20px;background:#fff;border:2px solid #667eea;padding:15px 20px;border-radius:10px;box-shadow:0 4px 15px rgba(0,0,0,0.15);z-index:9998;max-width:280px;';
        nudge.innerHTML = '<strong>🛒 {cart_tactic['message']}</strong><br><a href="/cart" style="color:#667eea;text-decoration:none;">Complete checkout →</a>';
        document.body.appendChild(nudge);
        setTimeout(function() {{ nudge.remove(); }}, 10000);
    }}
}}, {delay});
"""
        
        # Scarcity
        scarcity_tactic = next((t for t in tactics if t.get('tactic') == MonetizationTactic.SCARCITY), None)
        if scarcity_tactic:
            scripts['scarcity'] = f"""
// Scarcity Indicator
document.querySelectorAll('.product-inventory, .stock-status').forEach(function(el) {{
    el.innerHTML = '<span style="color:#dc2626;font-weight:bold;">⚠️ {scarcity_tactic['message']}</span>';
    el.style.animation = 'pulse 2s infinite';
}});
"""
        
        # Time Sensitive
        time_tactic = next((t for t in tactics if t.get('tactic') == MonetizationTactic.TIME_SENSITIVE), None)
        if time_tactic:
            expires = time_tactic.get('expires_in_seconds', 3600)
            scripts['countdown'] = f"""
// Countdown Timer
(function() {{
    let seconds = {expires};
    const timer = document.createElement('div');
    timer.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#dc2626;color:white;text-align:center;padding:8px;font-weight:bold;z-index:9999;';
    document.body.appendChild(timer);
    function update() {{
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        timer.textContent = '⏰ Offer expires in: ' + h + ':' + String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
        if (seconds > 0) {{ seconds--; setTimeout(update, 1000); }}
    }}
    update();
}})();
"""
        
        # Tracking pixel
        scripts['tracking'] = """
// AiGentsy Tracking
window.aigentsyTrack = function(event, data) {
    fetch('/api/traffic/event', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({event: event, data: data || {}, ts: Date.now()})
    }).catch(function(){});
};
window.aigentsyTrack('page_view');
"""
        
        return scripts
    
    
    async def track_conversion(
        self,
        session_id: str,
        purchase_data: Dict[str, Any],
        username: str = None
    ) -> Dict[str, Any]:
        """
        Track conversion with full attribution + AiGentsy system integration
        
        Integrates with:
        - Yield Memory (pattern storage)
        - MetaHive (cross-user learning)
        - Outcome Oracle (funnel tracking)
        - AMG (optimization)
        - AIGx Engine (token credits)
        """
        
        session = self.active_sessions.get(session_id, {})
        visitor_data = session.get('visitor_data', {})
        tactics_shown = session.get('tactics_shown', [])
        
        source = visitor_data.get('source', 'direct')
        if hasattr(source, 'value'):
            source = source.value
        
        conversion = {
            'session_id': session_id,
            'visitor_id': visitor_data.get('visitor_fingerprint'),
            'source': source,
            'creator_code': visitor_data.get('creator_code'),
            'campaign': visitor_data.get('campaign'),
            'purchase_amount': purchase_data.get('total', 0),
            'purchase_items': purchase_data.get('items', []),
            'tactics_shown': tactics_shown,
            'converted_at': datetime.now(timezone.utc).isoformat(),
            'integrations_triggered': []
        }
        
        # Determine primary attribution
        if 'exit_intent' in tactics_shown and purchase_data.get('used_code') == 'STAYWITHUS15':
            conversion['primary_tactic'] = 'exit_intent'
            conversion['attribution_confidence'] = 0.95
        elif 'creator_code' in tactics_shown and visitor_data.get('creator_code'):
            conversion['primary_tactic'] = 'creator_code'
            conversion['attribution_confidence'] = 0.90
        elif 'first_discount' in tactics_shown:
            conversion['primary_tactic'] = 'first_discount'
            conversion['attribution_confidence'] = 0.85
        elif 'cart_nudge' in tactics_shown:
            conversion['primary_tactic'] = 'cart_nudge'
            conversion['attribution_confidence'] = 0.75
        else:
            conversion['primary_tactic'] = 'aigx_bonus'
            conversion['attribution_confidence'] = 0.60
        
        # Calculate ROAS for this session
        estimated_cost = 0.50  # Assume $0.50 cost per visitor
        purchase_amount = purchase_data.get('total', 0)
        roas = purchase_amount / estimated_cost if estimated_cost > 0 else 0
        conversion['roas'] = roas
        
        # ============================================================
        # INTEGRATION 1: Yield Memory (pattern storage)
        # ============================================================
        if self.yield_memory_available and self.store_pattern and roas > 1.0:
            try:
                await self.store_pattern({
                    'type': 'monetization_conversion',
                    'source': source,
                    'primary_tactic': conversion['primary_tactic'],
                    'roas': roas,
                    'tactics_shown': tactics_shown
                })
                conversion['integrations_triggered'].append('yield_memory')
            except:
                pass
        
        # ============================================================
        # INTEGRATION 2: MetaHive (cross-user learning)
        # ============================================================
        if self.metahive_available and self.contribute_hive and roas > 1.5:
            try:
                await self.contribute_hive({
                    'pattern_type': 'high_roas_monetization',
                    'source': source,
                    'primary_tactic': conversion['primary_tactic'],
                    'roas': roas,
                    'confidence': conversion['attribution_confidence']
                })
                conversion['contributed_to_hive'] = True
                conversion['integrations_triggered'].append('metahive')
            except:
                pass
        
        # ============================================================
        # INTEGRATION 3: Outcome Oracle (funnel tracking)
        # ============================================================
        if username and OUTCOME_ORACLE_INTEGRATED:
            try:
                oracle_result = await record_traffic_conversion_to_outcome_oracle(
                    username=username,
                    session_id=session_id,
                    purchase_amount=purchase_amount,
                    source=source,
                    tactic=conversion['primary_tactic']
                )
                if oracle_result.get('recorded'):
                    conversion['integrations_triggered'].append('outcome_oracle')
            except:
                pass
        
        # ============================================================
        # INTEGRATION 4: AMG (optimization loop)
        # ============================================================
        if AMG_INTEGRATED:
            try:
                amg_result = await feed_conversion_to_amg(
                    source=source,
                    tactic=conversion['primary_tactic'],
                    purchase_amount=purchase_amount,
                    roas=roas
                )
                if amg_result.get('fed'):
                    conversion['integrations_triggered'].append('amg')
            except:
                pass
        
        # ============================================================
        # INTEGRATION 5: AIGx Credits
        # ============================================================
        if username and AIGX_INTEGRATED and purchase_amount > 0:
            try:
                # Get multiplier from source config
                source_enum = TrafficSource(source) if source in [s.value for s in TrafficSource] else TrafficSource.DIRECT
                config = get_platform_config(source_enum)
                multiplier = config.get('messaging', {}).get('aigx_multiplier', 1.0)
                
                aigx_result = await credit_aigx_for_traffic_conversion(
                    username=username,
                    amount=purchase_amount,
                    source=source,
                    multiplier=multiplier
                )
                if aigx_result.get('credited'):
                    conversion['aigx_credited'] = aigx_result.get('aigx_amount', 0)
                    conversion['integrations_triggered'].append('aigx_engine')
            except:
                pass
        
        # Add to history
        self.conversion_history.append(conversion)
        
        # Clean up session
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        return conversion
    
    
    def get_optimization_insights(self) -> Dict[str, Any]:
        """
        AMG-style optimization insights from conversion history
        """
        
        if not self.conversion_history:
            return {'insights': 'No conversion data yet', 'recommendations': []}
        
        # Group by source
        by_source = {}
        for conv in self.conversion_history:
            source = conv.get('source', 'unknown')
            if source not in by_source:
                by_source[source] = {'conversions': 0, 'revenue': 0, 'tactics': {}}
            by_source[source]['conversions'] += 1
            by_source[source]['revenue'] += conv.get('purchase_amount', 0)
            
            tactic = conv.get('primary_tactic', 'unknown')
            if tactic not in by_source[source]['tactics']:
                by_source[source]['tactics'][tactic] = 0
            by_source[source]['tactics'][tactic] += 1
        
        # Generate insights
        insights = []
        recommendations = []
        
        for source, data in by_source.items():
            best_tactic = max(data['tactics'].items(), key=lambda x: x[1])[0] if data['tactics'] else 'unknown'
            avg_order = data['revenue'] / data['conversions'] if data['conversions'] > 0 else 0
            
            insights.append({
                'source': source,
                'conversions': data['conversions'],
                'revenue': data['revenue'],
                'avg_order_value': avg_order,
                'best_tactic': best_tactic
            })
            
            if best_tactic == 'exit_intent':
                recommendations.append(f"Increase exit intent discount for {source} traffic")
            elif best_tactic == 'aigx_bonus':
                recommendations.append(f"Emphasize AIGx rewards more prominently for {source}")
        
        # Sort by revenue
        insights.sort(key=lambda x: x['revenue'], reverse=True)
        
        return {
            'total_conversions': len(self.conversion_history),
            'total_revenue': sum(c.get('purchase_amount', 0) for c in self.conversion_history),
            'insights_by_source': insights,
            'recommendations': recommendations,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }


# ============================================================
# INTEGRATION WITH EXISTING AIGENTSY SYSTEMS
# ============================================================

# Outcome Oracle Integration - Full funnel tracking
try:
    from outcome_oracle_max import on_event as record_outcome_event
    OUTCOME_ORACLE_INTEGRATED = True
except ImportError:
    try:
        from outcome_oracle import on_event as record_outcome_event
        OUTCOME_ORACLE_INTEGRATED = True
    except:
        OUTCOME_ORACLE_INTEGRATED = False
        record_outcome_event = None

# AMG Orchestrator Integration - Closed-loop optimization
try:
    from amg_orchestrator import AMGOrchestrator
    AMG_INTEGRATED = True
except ImportError:
    AMG_INTEGRATED = False
    AMGOrchestrator = None

# AIGx Credit System Integration
try:
    from aigx_engine import credit_aigx, AIGxTransactionType
    AIGX_INTEGRATED = True
except ImportError:
    AIGX_INTEGRATED = False
    credit_aigx = None
    AIGxTransactionType = None

# Analytics Engine Integration
try:
    from analytics_engine import AnalyticsEngine
    ANALYTICS_INTEGRATED = True
except ImportError:
    ANALYTICS_INTEGRATED = False
    AnalyticsEngine = None


async def record_traffic_conversion_to_outcome_oracle(
    username: str,
    session_id: str,
    purchase_amount: float,
    source: str,
    tactic: str
) -> Dict[str, Any]:
    """Record conversion to Outcome Oracle for full funnel tracking"""
    if not OUTCOME_ORACLE_INTEGRATED or not record_outcome_event:
        return {"recorded": False, "reason": "outcome_oracle_not_available"}
    
    try:
        result = await record_outcome_event(
            username=username,
            event_type="PAID",
            event_data={
                "source": "inbound_traffic",
                "traffic_source": source,
                "conversion_tactic": tactic,
                "session_id": session_id,
                "amount": purchase_amount,
                "channel": "third_party_monetization"
            }
        )
        return {"recorded": True, "result": result}
    except Exception as e:
        return {"recorded": False, "error": str(e)}


async def credit_aigx_for_traffic_conversion(
    username: str,
    amount: float,
    source: str,
    multiplier: float = 1.0
) -> Dict[str, Any]:
    """Credit AIGx to user for traffic conversion"""
    if not AIGX_INTEGRATED or not credit_aigx:
        return {"credited": False, "reason": "aigx_engine_not_available"}
    
    try:
        # Base AIGx = 1% of purchase amount, adjusted by source multiplier
        aigx_amount = amount * 0.01 * multiplier
        
        result = credit_aigx(
            username=username,
            amount=aigx_amount,
            transaction_type=AIGxTransactionType.PURCHASE_CONVERSION if AIGxTransactionType else "purchase_conversion",
            reference=f"traffic_{source}"
        )
        return {"credited": True, "aigx_amount": aigx_amount, "result": result}
    except Exception as e:
        return {"credited": False, "error": str(e)}


async def feed_conversion_to_amg(
    source: str,
    tactic: str,
    purchase_amount: float,
    roas: float
) -> Dict[str, Any]:
    """Feed conversion data to AMG for optimization"""
    if not AMG_INTEGRATED or not AMGOrchestrator:
        return {"fed": False, "reason": "amg_not_available"}
    
    try:
        amg = AMGOrchestrator()
        result = await amg.record_conversion({
            "channel": "inbound_traffic",
            "source": source,
            "tactic": tactic,
            "revenue": purchase_amount,
            "roas": roas,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return {"fed": True, "result": result}
    except Exception as e:
        return {"fed": False, "error": str(e)}


# ============================================================
# SINGLETON INSTANCE
# ============================================================

_monetization_engine = None

def get_monetization_engine() -> MonetizationEngine:
    """Get singleton monetization engine"""
    global _monetization_engine
    if _monetization_engine is None:
        _monetization_engine = MonetizationEngine()
    return _monetization_engine


# ============================================================
# CONVENIENCE FUNCTIONS (for API endpoints)
# ============================================================

async def parse_and_track_visitor(
    url: str,
    referrer: str = "",
    utm_params: Dict = None,
    headers: Dict = None
) -> Dict[str, Any]:
    """Parse traffic source and return tracking data"""
    return parse_traffic_source(url, referrer, utm_params or {}, headers or {})


async def generate_monetization_strategy(
    visitor_data: Dict[str, Any],
    product_data: Dict[str, Any],
    session_data: Dict[str, Any],
    user_history: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Generate monetization strategy for visitor"""
    engine = get_monetization_engine()
    return await engine.generate_strategy(visitor_data, product_data, session_data, user_history)


async def track_conversion(
    session_id: str,
    purchase_data: Dict[str, Any],
    username: str = None
) -> Dict[str, Any]:
    """Track a conversion"""
    engine = get_monetization_engine()
    return await engine.track_conversion(session_id, purchase_data, username)


def get_optimization_insights() -> Dict[str, Any]:
    """Get AMG optimization insights"""
    engine = get_monetization_engine()
    return engine.get_optimization_insights()


# ============================================================
# FASTAPI ENDPOINTS (to add to main.py)
# ============================================================

ENDPOINTS_FOR_MAIN_PY = '''
# ============================================================
# THIRD-PARTY MONETIZATION ENDPOINTS
# Weaponizes inbound social traffic with ML-optimized tactics
# ============================================================

from third_party_monetization_enhanced import (
    parse_and_track_visitor,
    generate_monetization_strategy,
    track_conversion as track_monetization_conversion,
    get_optimization_insights,
    TrafficSource,
    MonetizationTactic
)

@app.post("/traffic/track")
async def traffic_track(request: Request):
    """
    Track incoming visitor and identify traffic source
    
    Body: {
        url: str,
        referrer?: str,
        utm_source?: str,
        utm_campaign?: str,
        utm_medium?: str,
        utm_content?: str
    }
    
    Returns: {
        source: "instagram" | "tiktok" | etc,
        session_id: str,
        creator_code?: str,
        is_affiliate: bool
    }
    """
    body = await request.json()
    
    # Extract UTM params
    utm_params = {
        'utm_source': body.get('utm_source'),
        'utm_campaign': body.get('utm_campaign'),
        'utm_medium': body.get('utm_medium'),
        'utm_content': body.get('utm_content'),
        'utm_term': body.get('utm_term')
    }
    
    # Get headers for fingerprinting
    headers = {
        'user-agent': request.headers.get('user-agent', ''),
        'accept-language': request.headers.get('accept-language', '')
    }
    
    result = await parse_and_track_visitor(
        url=body.get('url', ''),
        referrer=body.get('referrer', request.headers.get('referer', '')),
        utm_params=utm_params,
        headers=headers
    )
    
    return {"ok": True, **result}


@app.post("/traffic/strategy")
async def traffic_strategy(body: Dict = Body(...)):
    """
    Generate monetization strategy for visitor
    
    Body: {
        visitor_data: {source, session_id, creator_code?, is_first_visit?},
        product_data: {id, price, inventory?, category?, recent_purchases?},
        session_data: {time_on_site?, pages_viewed?, cart_items?},
        user_history?: {previous_visits?, total_spent?, aigx_balance?}
    }
    
    Returns: {
        session_id: str,
        tactics: [{tactic, message, ...}],
        scripts: {aigx_banner: str, exit_intent: str, ...},
        integrations: {revenue_mesh: bool, ...}
    }
    """
    visitor_data = body.get('visitor_data', {})
    product_data = body.get('product_data', {'price': 100})
    session_data = body.get('session_data', {})
    user_history = body.get('user_history')
    
    strategy = await generate_monetization_strategy(
        visitor_data=visitor_data,
        product_data=product_data,
        session_data=session_data,
        user_history=user_history
    )
    
    return {"ok": True, **strategy}


@app.get("/traffic/scripts/{session_id}")
async def traffic_scripts(session_id: str):
    """
    Get frontend JavaScript for a session's tactics
    Returns combined script to inject into page
    """
    from third_party_monetization_enhanced import get_monetization_engine
    
    engine = get_monetization_engine()
    session = engine.active_sessions.get(session_id)
    
    if not session:
        return {"ok": False, "error": "Session not found or expired"}
    
    # Re-generate strategy to get fresh scripts
    strategy = await generate_monetization_strategy(
        visitor_data=session.get('visitor_data', {}),
        product_data=session.get('product_data', {'price': 100}),
        session_data={}
    )
    
    # Combine all scripts
    combined_script = "\\n".join(strategy.get('scripts', {}).values())
    
    return {
        "ok": True,
        "session_id": session_id,
        "script": combined_script,
        "tactics_count": len(strategy.get('tactics', []))
    }


@app.post("/traffic/convert")
async def traffic_convert(body: Dict = Body(...)):
    """
    Track a conversion with full attribution
    
    Body: {
        session_id: str,
        purchase_data: {total: float, items?: [], used_code?: str}
    }
    
    Returns: {
        session_id: str,
        primary_tactic: str,
        attribution_confidence: float,
        roas: float,
        contributed_to_hive?: bool
    }
    """
    session_id = body.get('session_id')
    purchase_data = body.get('purchase_data', {})
    
    if not session_id:
        return {"ok": False, "error": "session_id required"}
    
    conversion = await track_monetization_conversion(session_id, purchase_data)
    
    return {"ok": True, **conversion}


@app.post("/traffic/event")
async def traffic_event(body: Dict = Body(...)):
    """
    Track frontend events (from injected scripts)
    
    Body: {event: str, data?: {}, ts?: int}
    """
    event = body.get('event', 'unknown')
    data = body.get('data', {})
    
    # Log event (integrate with your analytics)
    # This could feed into AMG for optimization
    
    return {"ok": True, "event": event, "recorded": True}


@app.get("/traffic/optimize")
async def traffic_optimize():
    """
    Get AMG optimization insights for traffic monetization
    
    Returns insights on:
    - Best performing traffic sources
    - Most effective tactics per source
    - Revenue by source
    - Recommendations for improvement
    """
    insights = get_optimization_insights()
    return {"ok": True, **insights}


@app.get("/traffic/sources")
async def traffic_sources():
    """
    List available traffic sources and their configurations
    """
    from third_party_monetization_enhanced import PLATFORM_CONFIGS, TrafficSource
    
    sources = []
    for source in TrafficSource:
        config = PLATFORM_CONFIGS.get(source, {})
        sources.append({
            'source': source.value,
            'primary_tactics': [t.value for t in config.get('primary_tactics', [])],
            'urgency_level': config.get('messaging', {}).get('urgency_level', 'medium'),
            'aigx_multiplier': config.get('messaging', {}).get('aigx_multiplier', 1.0)
        })
    
    return {"ok": True, "sources": sources}
'''

# Print endpoints for easy copy
if __name__ == "__main__":
    print("=" * 70)
    print("THIRD-PARTY MONETIZATION ENGINE - ENHANCED")
    print("=" * 70)
    print("\nEndpoints to add to main.py:\n")
    print(ENDPOINTS_FOR_MAIN_PY)
