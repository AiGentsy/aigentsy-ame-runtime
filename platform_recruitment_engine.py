"""
PLATFORM RECRUITMENT ENGINE
============================
Converts inbound traffic into monetization clients.

The Pitch:
"We see you came from TikTok. Want to make money from it 24/7 while you sleep?"

How It Works:
1. Visitor arrives from TikTok/Instagram/YouTube/etc
2. We detect their source platform
3. After engagement (exit intent, time on site, etc.)
4. Show recruitment CTA with platform-specific monetization pitch
5. Fast signup → Connect platform → AME/AMG deployed
6. User earns passive income, AiGentsy takes 2.8% + 28¢

Monetization Methods by Platform:
- TikTok: Affiliate links, viral reposts, creator fund optimization
- Instagram: Story monetization, affiliate, sponsored content matching
- YouTube: Ad optimization, affiliate, sponsorship matching
- Twitter/X: Thread monetization, affiliate links, viral reposts
- LinkedIn: Lead gen, B2B affiliate, content monetization

This is the GROWTH ENGINE - every visitor is a potential client.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum
import json


class RecruitmentTrigger(str, Enum):
    """When to show recruitment CTA"""
    EXIT_INTENT = "exit_intent"          # About to leave
    TIME_ON_SITE = "time_on_site"        # Been here 60+ seconds
    SCROLL_DEPTH = "scroll_depth"        # Scrolled 50%+
    CART_ABANDON = "cart_abandon"        # Added to cart but leaving
    SECOND_PAGE = "second_page"          # Viewed 2+ pages
    RETURN_VISIT = "return_visit"        # Came back again
    POST_PURCHASE = "post_purchase"      # After they bought something


class PlatformMonetizationPitch:
    """
    Platform-specific monetization pitches
    Each platform has unique money-making opportunities
    """
    
    PITCHES = {
        "tiktok": {
            "headline": "Make Money From TikTok 24/7",
            "subheadline": "While you sleep, we're monetizing your audience",
            "opportunities": [
                {
                    "name": "Affiliate Marketing",
                    "description": "Auto-insert affiliate links in your bio & comments",
                    "avg_monthly": "$500-$5,000",
                    "effort": "Zero - fully automated"
                },
                {
                    "name": "Viral Reposting",
                    "description": "AI finds & reposts trending content in your niche",
                    "avg_monthly": "$200-$2,000",
                    "effort": "Zero - AI handles everything"
                },
                {
                    "name": "Creator Fund Optimizer",
                    "description": "AI optimizes posting times & hashtags for max fund payouts",
                    "avg_monthly": "+30-50% boost",
                    "effort": "Zero - runs in background"
                },
                {
                    "name": "Brand Deal Matching",
                    "description": "AI finds & negotiates sponsorships for you",
                    "avg_monthly": "$1,000-$10,000+",
                    "effort": "Just approve deals"
                }
            ],
            "social_proof": {
                "users": 2847,
                "avg_earnings": "$1,240/month",
                "top_earner": "$12,400/month"
            },
            "cta": "Start Earning From TikTok →",
            "urgency": "TikTok algorithm changes fast - early movers win"
        },
        
        "instagram": {
            "headline": "Turn Instagram Into Passive Income",
            "subheadline": "Your followers = your ATM. Let AI do the work.",
            "opportunities": [
                {
                    "name": "Story Monetization",
                    "description": "Auto-post affiliate stories that convert",
                    "avg_monthly": "$300-$3,000",
                    "effort": "Zero - AI creates & posts"
                },
                {
                    "name": "Link-in-Bio Optimizer",
                    "description": "AI rotates highest-converting affiliate links",
                    "avg_monthly": "$400-$4,000",
                    "effort": "Zero - set and forget"
                },
                {
                    "name": "Reel Repurposing",
                    "description": "AI repurposes viral TikToks to your Reels",
                    "avg_monthly": "$200-$1,500",
                    "effort": "Zero - fully automated"
                },
                {
                    "name": "Sponsored Post Matching",
                    "description": "AI finds brands that match your aesthetic",
                    "avg_monthly": "$500-$5,000+",
                    "effort": "Just approve posts"
                }
            ],
            "social_proof": {
                "users": 3201,
                "avg_earnings": "$980/month",
                "top_earner": "$8,700/month"
            },
            "cta": "Monetize My Instagram →",
            "urgency": "Your followers are already there - start earning today"
        },
        
        "youtube": {
            "headline": "Maximize Your YouTube Revenue",
            "subheadline": "Beyond AdSense - unlock 5 more income streams",
            "opportunities": [
                {
                    "name": "Affiliate Integration",
                    "description": "AI adds affiliate links to descriptions & pinned comments",
                    "avg_monthly": "$500-$10,000",
                    "effort": "Zero - retroactive on all videos"
                },
                {
                    "name": "Sponsorship Autopilot",
                    "description": "AI finds, negotiates & manages brand deals",
                    "avg_monthly": "$2,000-$20,000+",
                    "effort": "Just record the segment"
                },
                {
                    "name": "Shorts Monetization",
                    "description": "AI repurposes long-form into monetized Shorts",
                    "avg_monthly": "$300-$3,000",
                    "effort": "Zero - AI edits automatically"
                },
                {
                    "name": "Community Tab Sales",
                    "description": "AI posts high-converting offers to your community",
                    "avg_monthly": "$200-$2,000",
                    "effort": "Zero - fully automated"
                }
            ],
            "social_proof": {
                "users": 1892,
                "avg_earnings": "$2,100/month",
                "top_earner": "$34,000/month"
            },
            "cta": "Boost My YouTube Revenue →",
            "urgency": "Your back catalog is a goldmine - start monetizing it"
        },
        
        "twitter": {
            "headline": "Turn Tweets Into Cash",
            "subheadline": "Every thread, every reply - monetized automatically",
            "opportunities": [
                {
                    "name": "Thread Monetization",
                    "description": "AI adds affiliate links to viral threads",
                    "avg_monthly": "$200-$2,000",
                    "effort": "Zero - AI detects viral potential"
                },
                {
                    "name": "Viral Repost Engine",
                    "description": "AI finds & reposts trending content with your spin",
                    "avg_monthly": "$100-$1,000",
                    "effort": "Zero - runs 24/7"
                },
                {
                    "name": "Newsletter Funnel",
                    "description": "AI converts followers to email subscribers you own",
                    "avg_monthly": "$500-$5,000",
                    "effort": "Zero - automated DM sequences"
                },
                {
                    "name": "Paid Promotion Matching",
                    "description": "AI finds accounts that want you to promote them",
                    "avg_monthly": "$300-$3,000",
                    "effort": "Just approve tweets"
                }
            ],
            "social_proof": {
                "users": 1456,
                "avg_earnings": "$640/month",
                "top_earner": "$7,200/month"
            },
            "cta": "Monetize My Twitter →",
            "urgency": "X/Twitter monetization is exploding - get in now"
        },
        
        "linkedin": {
            "headline": "LinkedIn = B2B Money Machine",
            "subheadline": "Your network is worth $$$. Let AI extract it.",
            "opportunities": [
                {
                    "name": "Lead Generation",
                    "description": "AI identifies & warms up high-value prospects",
                    "avg_monthly": "$1,000-$10,000",
                    "effort": "Just close the deals"
                },
                {
                    "name": "B2B Affiliate",
                    "description": "Recommend SaaS tools, earn recurring commissions",
                    "avg_monthly": "$500-$5,000",
                    "effort": "Zero - AI posts recommendations"
                },
                {
                    "name": "Content Syndication",
                    "description": "AI repurposes your posts across platforms for reach",
                    "avg_monthly": "+50% engagement",
                    "effort": "Zero - automated"
                },
                {
                    "name": "Speaking/Consulting Leads",
                    "description": "AI positions you as expert, attracts paid gigs",
                    "avg_monthly": "$2,000-$20,000+",
                    "effort": "Just show up"
                }
            ],
            "social_proof": {
                "users": 987,
                "avg_earnings": "$2,800/month",
                "top_earner": "$45,000/month"
            },
            "cta": "Unlock LinkedIn Revenue →",
            "urgency": "B2B buyers are on LinkedIn daily - capture them"
        },
        
        "reddit": {
            "headline": "Reddit Karma = Real Money",
            "subheadline": "Turn upvotes into income streams",
            "opportunities": [
                {
                    "name": "Niche Authority",
                    "description": "AI builds your reputation in profitable subreddits",
                    "avg_monthly": "$300-$3,000",
                    "effort": "Zero - AI posts & engages"
                },
                {
                    "name": "Affiliate Drops",
                    "description": "AI naturally recommends affiliate products in comments",
                    "avg_monthly": "$200-$2,000",
                    "effort": "Zero - contextual & compliant"
                },
                {
                    "name": "AMA Monetization",
                    "description": "AI schedules & promotes AMAs that drive sales",
                    "avg_monthly": "$500-$5,000",
                    "effort": "Just answer questions"
                }
            ],
            "social_proof": {
                "users": 654,
                "avg_earnings": "$520/month",
                "top_earner": "$4,800/month"
            },
            "cta": "Monetize My Reddit →",
            "urgency": "Reddit traffic converts 3x better than social"
        },
        
        "pinterest": {
            "headline": "Pinterest Pins = Passive Profits",
            "subheadline": "Pins live forever. So does the income.",
            "opportunities": [
                {
                    "name": "Affiliate Pins",
                    "description": "AI creates & posts affiliate pins 24/7",
                    "avg_monthly": "$400-$4,000",
                    "effort": "Zero - fully automated"
                },
                {
                    "name": "Traffic Arbitrage",
                    "description": "AI drives Pinterest traffic to monetized pages",
                    "avg_monthly": "$300-$3,000",
                    "effort": "Zero - AI handles everything"
                },
                {
                    "name": "Product Tagging",
                    "description": "AI tags products in your pins for commission",
                    "avg_monthly": "$200-$2,000",
                    "effort": "Zero - retroactive tagging"
                }
            ],
            "social_proof": {
                "users": 432,
                "avg_earnings": "$680/month",
                "top_earner": "$6,200/month"
            },
            "cta": "Start Earning From Pinterest →",
            "urgency": "Pinterest pins rank for years - compound your income"
        }
    }
    
    # Default for unknown platforms
    DEFAULT_PITCH = {
        "headline": "Turn Your Social Media Into Income",
        "subheadline": "AI monetizes your audience 24/7 while you sleep",
        "opportunities": [
            {
                "name": "Affiliate Marketing",
                "description": "AI auto-inserts relevant affiliate links",
                "avg_monthly": "$500-$5,000",
                "effort": "Zero - fully automated"
            },
            {
                "name": "Content Monetization",
                "description": "AI repurposes viral content for profit",
                "avg_monthly": "$300-$3,000",
                "effort": "Zero - AI handles everything"
            },
            {
                "name": "Brand Partnerships",
                "description": "AI finds & negotiates sponsorships",
                "avg_monthly": "$1,000-$10,000+",
                "effort": "Just approve deals"
            }
        ],
        "social_proof": {
            "users": 12500,
            "avg_earnings": "$1,100/month",
            "top_earner": "$45,000/month"
        },
        "cta": "Start Earning Now →",
        "urgency": "Every day without monetization = money left on the table"
    }
    
    @classmethod
    def get_pitch(cls, platform: str) -> Dict[str, Any]:
        """Get platform-specific pitch"""
        return cls.PITCHES.get(platform.lower(), cls.DEFAULT_PITCH)


# ============================================================
# RECRUITMENT CTA GENERATOR
# ============================================================

class RecruitmentEngine:
    """
    Generates recruitment CTAs for converting visitors into clients
    """
    
    def __init__(self):
        self.recruitment_sessions = {}
        self.conversion_history = []
    
    
    def generate_recruitment_cta(
        self,
        source_platform: str,
        visitor_data: Dict[str, Any],
        trigger: RecruitmentTrigger,
        tactics_experienced: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a recruitment CTA based on visitor's source platform
        
        Args:
            source_platform: Where they came from (tiktok, instagram, etc)
            visitor_data: Session data from traffic tracking
            trigger: What triggered this CTA (exit_intent, time_on_site, etc)
            tactics_experienced: Which monetization tactics they saw/experienced
        
        Returns:
            CTA content + scripts to display
        """
        
        pitch = PlatformMonetizationPitch.get_pitch(source_platform)
        tactics_experienced = tactics_experienced or []
        
        # Personalize based on what they experienced
        experience_context = self._get_experience_context(tactics_experienced)
        
        # Build the CTA
        cta = {
            "platform": source_platform,
            "trigger": trigger.value if hasattr(trigger, 'value') else trigger,
            "pitch": pitch,
            "personalization": {
                "tactics_experienced": tactics_experienced,
                "experience_context": experience_context
            },
            "display": self._generate_display_content(pitch, source_platform, experience_context),
            "scripts": self._generate_recruitment_scripts(pitch, source_platform, trigger),
            "signup_url": f"/signup?source={source_platform}&ref=platform_recruit",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Track this recruitment attempt
        session_id = visitor_data.get('session_id', f"recruit_{datetime.now().timestamp()}")
        self.recruitment_sessions[session_id] = {
            "platform": source_platform,
            "trigger": trigger,
            "shown_at": datetime.now(timezone.utc).isoformat()
        }
        
        return cta
    
    
    def _get_experience_context(self, tactics: List[str]) -> str:
        """Generate context based on what tactics they experienced"""
        
        if not tactics:
            return "our AI-powered monetization tools"
        
        experiences = []
        if 'exit_intent' in tactics:
            experiences.append("that exit popup that almost got you to stay")
        if 'aigx_bonus' in tactics:
            experiences.append("the AIGx rewards you saw")
        if 'scarcity' in tactics:
            experiences.append("the urgency messaging")
        if 'social_proof' in tactics:
            experiences.append("the social proof indicators")
        if 'cart_nudge' in tactics:
            experiences.append("the cart reminder")
        if 'time_sensitive' in tactics:
            experiences.append("the countdown timer")
        if 'first_discount' in tactics:
            experiences.append("the welcome discount")
        
        if experiences:
            return f"You just experienced {', '.join(experiences[:2])}. "
        return ""
    
    
    def _generate_display_content(
        self,
        pitch: Dict[str, Any],
        platform: str,
        experience_context: str
    ) -> Dict[str, str]:
        """Generate display content for the CTA"""
        
        platform_display = platform.replace('_', ' ').title()
        
        # Main headline
        headline = pitch['headline']
        
        # Personalized subheadline
        if experience_context:
            subheadline = f"{experience_context}Now imagine this running on YOUR {platform_display} 24/7."
        else:
            subheadline = pitch['subheadline']
        
        # Top 3 opportunities
        top_opportunities = pitch['opportunities'][:3]
        opportunities_html = ""
        for opp in top_opportunities:
            opportunities_html += f"""
            <div class="opp-item">
                <strong>{opp['name']}</strong>
                <span class="earnings">{opp['avg_monthly']}/mo</span>
                <span class="effort">{opp['effort']}</span>
            </div>
            """
        
        # Social proof
        social = pitch['social_proof']
        social_proof = f"{social['users']:,} creators earning avg ${social['avg_earnings'].replace('$','').replace('/month','')}/mo"
        
        return {
            "headline": headline,
            "subheadline": subheadline,
            "opportunities_html": opportunities_html,
            "social_proof": social_proof,
            "cta_button": pitch['cta'],
            "urgency": pitch['urgency']
        }
    
    
    def _generate_recruitment_scripts(
        self,
        pitch: Dict[str, Any],
        platform: str,
        trigger: RecruitmentTrigger
    ) -> Dict[str, str]:
        """Generate JavaScript for recruitment CTAs"""
        
        scripts = {}
        
        platform_display = platform.replace('_', ' ').title()
        social = pitch['social_proof']
        
        # Modal script
        scripts['recruitment_modal'] = f"""
// AiGentsy Platform Recruitment Modal
(function() {{
    const modal = document.createElement('div');
    modal.id = 'aigentsy-recruit-modal';
    modal.innerHTML = `
        <div style="position:fixed;inset:0;background:rgba(0,0,0,0.8);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;">
            <div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);border-radius:16px;max-width:500px;width:100%;padding:30px;color:white;position:relative;box-shadow:0 25px 50px rgba(0,0,0,0.5);">
                <button onclick="this.parentElement.parentElement.remove();window.aigentsyTrack('recruit_dismissed');" style="position:absolute;top:15px;right:15px;background:none;border:none;color:#888;font-size:24px;cursor:pointer;">×</button>
                
                <div style="text-align:center;margin-bottom:20px;">
                    <span style="font-size:40px;">💰</span>
                </div>
                
                <h2 style="margin:0 0 10px;font-size:28px;text-align:center;background:linear-gradient(90deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                    {pitch['headline']}
                </h2>
                
                <p style="margin:0 0 25px;text-align:center;color:#aaa;font-size:16px;">
                    We noticed you came from {platform_display}.<br>
                    <strong style="color:#fff;">Want to make money from it 24/7?</strong>
                </p>
                
                <div style="background:rgba(255,255,255,0.05);border-radius:12px;padding:20px;margin-bottom:20px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;padding-bottom:15px;border-bottom:1px solid rgba(255,255,255,0.1);">
                        <span>🤖 Affiliate Marketing</span>
                        <span style="color:#4ade80;font-weight:bold;">$500-$5K/mo</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;padding-bottom:15px;border-bottom:1px solid rgba(255,255,255,0.1);">
                        <span>🔄 Viral Reposting</span>
                        <span style="color:#4ade80;font-weight:bold;">$200-$2K/mo</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span>📈 Brand Deals</span>
                        <span style="color:#4ade80;font-weight:bold;">$1K-$10K+/mo</span>
                    </div>
                </div>
                
                <div style="text-align:center;margin-bottom:20px;color:#888;font-size:14px;">
                    <span style="color:#4ade80;">●</span> {social['users']:,} creators already earning
                </div>
                
                <button onclick="window.location.href='/signup?source={platform}&ref=platform_recruit';window.aigentsyTrack('recruit_clicked');" style="width:100%;padding:16px;background:linear-gradient(90deg,#667eea,#764ba2);border:none;border-radius:10px;color:white;font-size:18px;font-weight:bold;cursor:pointer;transition:transform 0.2s;">
                    {pitch['cta']}
                </button>
                
                <p style="margin:15px 0 0;text-align:center;color:#666;font-size:12px;">
                    Free to start • No credit card • Takes 2 minutes
                </p>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    window.aigentsyTrack('recruit_shown', {{platform: '{platform}', trigger: '{trigger.value if hasattr(trigger, "value") else trigger}'}});
}})();
"""
        
        # Trigger script based on trigger type
        if trigger == RecruitmentTrigger.EXIT_INTENT:
            scripts['trigger'] = """
// Trigger on exit intent
(function() {
    let shown = false;
    document.addEventListener('mouseout', function(e) {
        if (e.clientY < 10 && !shown) {
            shown = true;
            window.showRecruitmentModal();
        }
    });
})();
"""
        elif trigger == RecruitmentTrigger.TIME_ON_SITE:
            scripts['trigger'] = """
// Trigger after 60 seconds
setTimeout(function() {
    window.showRecruitmentModal();
}, 60000);
"""
        elif trigger == RecruitmentTrigger.SCROLL_DEPTH:
            scripts['trigger'] = """
// Trigger at 50% scroll
(function() {
    let shown = false;
    window.addEventListener('scroll', function() {
        if (!shown && (window.scrollY / (document.body.scrollHeight - window.innerHeight)) > 0.5) {
            shown = true;
            window.showRecruitmentModal();
        }
    });
})();
"""
        
        # Floating banner (less intrusive option)
        scripts['floating_banner'] = f"""
// Floating recruitment banner
(function() {{
    const banner = document.createElement('div');
    banner.innerHTML = `
        <div style="position:fixed;bottom:20px;left:20px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:15px 20px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:9998;max-width:300px;cursor:pointer;" onclick="window.showRecruitmentModal();">
            <div style="font-weight:bold;margin-bottom:5px;">💰 Monetize Your {platform_display}</div>
            <div style="font-size:13px;opacity:0.9;">Make money 24/7 while you sleep →</div>
        </div>
    `;
    setTimeout(function() {{ document.body.appendChild(banner); }}, 5000);
}})();
"""
        
        return scripts
    
    
    def track_recruitment_conversion(
        self,
        session_id: str,
        signup_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track when a recruited visitor signs up"""
        
        session = self.recruitment_sessions.get(session_id, {})
        
        conversion = {
            "session_id": session_id,
            "platform": session.get('platform', 'unknown'),
            "trigger": session.get('trigger'),
            "shown_at": session.get('shown_at'),
            "converted_at": datetime.now(timezone.utc).isoformat(),
            "signup_data": signup_data
        }
        
        self.conversion_history.append(conversion)
        
        return conversion
    
    
    def get_recruitment_stats(self) -> Dict[str, Any]:
        """Get recruitment performance stats"""
        
        total_shown = len(self.recruitment_sessions)
        total_converted = len(self.conversion_history)
        
        # By platform
        by_platform = {}
        for conv in self.conversion_history:
            platform = conv.get('platform', 'unknown')
            if platform not in by_platform:
                by_platform[platform] = 0
            by_platform[platform] += 1
        
        return {
            "total_shown": total_shown,
            "total_converted": total_converted,
            "conversion_rate": total_converted / total_shown if total_shown > 0 else 0,
            "by_platform": by_platform
        }


# ============================================================
# SINGLETON
# ============================================================

_recruitment_engine = None

def get_recruitment_engine() -> RecruitmentEngine:
    """Get singleton recruitment engine"""
    global _recruitment_engine
    if _recruitment_engine is None:
        _recruitment_engine = RecruitmentEngine()
    return _recruitment_engine


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def generate_recruitment_cta(
    source_platform: str,
    visitor_data: Dict[str, Any],
    trigger: str = "exit_intent",
    tactics_experienced: List[str] = None
) -> Dict[str, Any]:
    """Generate recruitment CTA for a visitor"""
    engine = get_recruitment_engine()
    
    # Convert string trigger to enum
    trigger_enum = RecruitmentTrigger(trigger) if trigger in [t.value for t in RecruitmentTrigger] else RecruitmentTrigger.EXIT_INTENT
    
    return engine.generate_recruitment_cta(
        source_platform=source_platform,
        visitor_data=visitor_data,
        trigger=trigger_enum,
        tactics_experienced=tactics_experienced
    )


def get_platform_pitch(platform: str) -> Dict[str, Any]:
    """Get the monetization pitch for a platform"""
    return PlatformMonetizationPitch.get_pitch(platform)


def get_all_platform_pitches() -> Dict[str, Any]:
    """Get all platform pitches"""
    return PlatformMonetizationPitch.PITCHES


# ============================================================
# FASTAPI ENDPOINTS
# ============================================================

ENDPOINTS_FOR_MAIN_PY = '''
# ============================================================
# PLATFORM RECRUITMENT ENDPOINTS  
# Converts inbound visitors into monetization clients
# "We see you came from TikTok. Want to make money from it 24/7?"
# ============================================================

from platform_recruitment_engine import (
    generate_recruitment_cta,
    get_platform_pitch,
    get_all_platform_pitches,
    get_recruitment_engine,
    RecruitmentTrigger
)

@app.post("/recruit/cta")
async def recruit_cta(body: Dict = Body(...)):
    """
    Generate recruitment CTA for a visitor
    
    Call this when you want to show the "monetize your platform" pitch.
    Best triggered on exit intent or after 60 seconds on site.
    
    Body: {
        source_platform: "tiktok" | "instagram" | "youtube" | etc,
        visitor_data: {session_id, ...},
        trigger?: "exit_intent" | "time_on_site" | "scroll_depth",
        tactics_experienced?: ["exit_intent", "aigx_bonus", ...]
    }
    
    Returns: {
        ok: true,
        platform: str,
        pitch: {headline, opportunities, social_proof, ...},
        scripts: {recruitment_modal: str, trigger: str, floating_banner: str},
        signup_url: str
    }
    """
    source_platform = body.get('source_platform', 'direct')
    visitor_data = body.get('visitor_data', {})
    trigger = body.get('trigger', 'exit_intent')
    tactics_experienced = body.get('tactics_experienced', [])
    
    cta = generate_recruitment_cta(
        source_platform=source_platform,
        visitor_data=visitor_data,
        trigger=trigger,
        tactics_experienced=tactics_experienced
    )
    
    return {"ok": True, **cta}


@app.get("/recruit/pitch/{platform}")
async def recruit_pitch(platform: str):
    """
    Get the monetization pitch for a specific platform
    
    Returns opportunities, earnings potential, social proof.
    Use this to customize landing pages by traffic source.
    """
    pitch = get_platform_pitch(platform)
    return {"ok": True, "platform": platform, "pitch": pitch}


@app.get("/recruit/pitches")
async def recruit_all_pitches():
    """
    Get all platform monetization pitches
    
    Useful for building comparison pages or letting users
    see all monetization opportunities.
    """
    pitches = get_all_platform_pitches()
    return {"ok": True, "pitches": pitches}


@app.post("/recruit/convert")
async def recruit_convert(body: Dict = Body(...)):
    """
    Track when a recruited visitor signs up
    
    Body: {
        session_id: str,
        signup_data: {username, email, platform_connected, ...}
    }
    """
    session_id = body.get('session_id')
    signup_data = body.get('signup_data', {})
    
    engine = get_recruitment_engine()
    conversion = engine.track_recruitment_conversion(session_id, signup_data)
    
    return {"ok": True, **conversion}


@app.get("/recruit/stats")
async def recruit_stats():
    """
    Get recruitment performance stats
    
    Shows conversion rates, top platforms, etc.
    """
    engine = get_recruitment_engine()
    stats = engine.get_recruitment_stats()
    return {"ok": True, **stats}


@app.post("/recruit/simulate")
async def recruit_simulate(body: Dict = Body(...)):
    """
    Simulate a recruitment flow for testing
    
    Body: {
        platform: "tiktok" | "instagram" | etc
    }
    """
    platform = body.get('platform', 'tiktok')
    
    cta = generate_recruitment_cta(
        source_platform=platform,
        visitor_data={"session_id": f"sim_{platform}_{datetime.now().timestamp()}"},
        trigger="exit_intent",
        tactics_experienced=["exit_intent", "aigx_bonus", "scarcity"]
    )
    
    return {
        "ok": True,
        "simulated_platform": platform,
        "cta": cta
    }
'''

# ============================================================
# INTEGRATION: Connect to existing referral system
# ============================================================

async def process_recruitment_signup(
    username: str,
    source_platform: str,
    session_id: str
) -> Dict[str, Any]:
    """
    Process a signup that came from platform recruitment.
    Connects to existing referral system in main.py.
    
    This should be called after user signs up via /signup?source=tiktok&ref=platform_recruit
    """
    
    result = {
        "username": username,
        "source_platform": source_platform,
        "session_id": session_id,
        "recruitment_type": "platform_recruit",
        "processed_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Track the recruitment conversion
    engine = get_recruitment_engine()
    conversion = engine.track_recruitment_conversion(session_id, {
        "username": username,
        "platform": source_platform
    })
    result["conversion"] = conversion
    
    # Suggest immediate business deployment based on their source platform
    pitch = PlatformMonetizationPitch.get_pitch(source_platform)
    result["suggested_deployment"] = {
        "platform": source_platform,
        "opportunities": pitch['opportunities'][:2],  # Top 2 opportunities
        "next_step": f"Deploy {source_platform} monetization",
        "action_url": f"/deploy/quick?platform={source_platform}&username={username}"
    }
    
    return result


# ============================================================
# QUICK DEPLOY ENDPOINT
# Fast-tracks recruited users into monetization
# ============================================================

QUICK_DEPLOY_ENDPOINT = '''
@app.post("/deploy/quick")
async def deploy_quick(body: Dict = Body(...)):
    """
    Quick deploy monetization for a recruited user.
    
    Called after user signs up via platform recruitment.
    Immediately sets up their platform monetization.
    
    Body: {
        username: str,
        platform: "tiktok" | "instagram" | etc,
        connect_token?: str (OAuth token if they connected platform)
    }
    """
    username = body.get('username')
    platform = body.get('platform', 'tiktok')
    
    if not username:
        return {"ok": False, "error": "username required"}
    
    # Get platform-specific deployment config
    from platform_recruitment_engine import get_platform_pitch
    pitch = get_platform_pitch(platform)
    
    # Queue monetization setup
    deployment = {
        "username": username,
        "platform": platform,
        "opportunities": pitch['opportunities'],
        "status": "QUEUED",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # In production, this triggers:
    # 1. business_in_a_box_accelerator for platform setup
    # 2. AME/AMG configuration for the platform
    # 3. Template deployment if applicable
    
    return {
        "ok": True,
        "deployment": deployment,
        "next_steps": [
            f"Connect your {platform} account",
            "Choose your monetization methods",
            "AI deploys and starts earning"
        ],
        "estimated_first_earnings": "24-48 hours"
    }
'''


if __name__ == "__main__":
    print("=" * 70)
    print("PLATFORM RECRUITMENT ENGINE")
    print("Converts inbound visitors into monetization clients")
    print("=" * 70)
    
    # Test
    cta = generate_recruitment_cta(
        source_platform="tiktok",
        visitor_data={"session_id": "test123"},
        trigger="exit_intent",
        tactics_experienced=["exit_intent", "aigx_bonus"]
    )
    
    print(f"\nGenerated CTA for TikTok visitor:")
    print(f"  Headline: {cta['display']['headline']}")
    print(f"  CTA Button: {cta['display']['cta_button']}")
    print(f"  Signup URL: {cta['signup_url']}")
