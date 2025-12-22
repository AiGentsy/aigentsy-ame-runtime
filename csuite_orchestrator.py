"""
C-Suite Intelligence Orchestrator
Coordinates all AiGentsy systems to provide strategic business intelligence
"""

from typing import Dict, List, Optional
from datetime import datetime
import httpx
import os


class CSuiteOrchestrator:
    """
    Master AI coordinator that runs autonomous business intelligence
    """
    
    def __init__(self, sku_config: Dict = None):
        self.backend_base = os.getenv("BACKEND_BASE", "https://aigentsy-ame-runtime.onrender.com")
        self.sku_config = sku_config  # NEW: Store SKU configuration
    
    async def analyze_business_state(self, username: str) -> Dict:
        """
        Aggregate intelligence from all AiGentsy systems
        
        Returns comprehensive business state including:
        - User capabilities (kit, tier, multiplier)
        - Revenue performance
        - System readiness (APEX)
        - Reputation status
        - Market position
        """
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                # Fetch dashboard data (primary intelligence source)
                dashboard_resp = await client.get(f"{self.backend_base}/dashboard/{username}")
                dashboard = dashboard_resp.json()
                
                if not dashboard.get("ok"):
                    return {"ok": False, "error": "Dashboard data unavailable"}
                
                # Extract key intelligence
                intelligence = {
                    "ok": True,
                    "username": username,
                    
                    # User Capabilities
                    "capabilities": {
                        "kit_type": dashboard["user"].get("company_type", "general"),
                        "user_number": dashboard["user"].get("user_number"),
                        "tier": dashboard["tier_progression"]["current_tier"],
                        "tier_multiplier": dashboard["tier_progression"]["tier_multiplier"],
                        "early_adopter_multiplier": dashboard["early_adopter"]["multiplier"],
                        "total_multiplier": (
                            dashboard["tier_progression"]["tier_multiplier"] * 
                            dashboard["early_adopter"]["multiplier"]
                        ),
                        "early_adopter_badge": dashboard["early_adopter"].get("badge")
                    },
                    
                    # Financial State
                    "financials": {
                        "aigx_balance": dashboard["aigx_equity"]["aigx_balance"],
                        "lifetime_revenue": dashboard["tier_progression"]["lifetime_revenue"],
                        "revenue_needed_for_next_tier": dashboard["tier_progression"].get("revenue_needed", 0),
                        "next_tier": dashboard["tier_progression"].get("next_tier")
                    },
                    
                    # System Readiness
                    "systems": {
                        "apex_ultra_active": dashboard["apex_ultra"]["activated"],
                        "systems_operational": dashboard["apex_ultra"]["systems_operational"],
                        "total_systems": dashboard["apex_ultra"]["total_systems"],
                        "success_rate": dashboard["apex_ultra"]["success_rate"]
                    },
                    
                    # Activity & Engagement
                    "activity": {
                        "current_streak": dashboard["activity_streaks"]["current_streak"],
                        "total_active_days": dashboard["activity_streaks"]["total_active_days"],
                        "total_referrals": dashboard["referrals"]["total_referrals"]
                    },
                    
                    # Reputation (calculate from ledger if no direct endpoint)
                    "reputation": self._calculate_reputation(dashboard)
                }
                
                # Try to get AME stats (optional - may not be available)
                try:
                    ame_resp = await client.get(f"{self.backend_base}/ame/stats")
                    ame_data = ame_resp.json()
                    intelligence["ame_stats"] = ame_data.get("stats", {})
                except:
                    intelligence["ame_stats"] = None
                
                return intelligence
                
            except Exception as e:
                return {"ok": False, "error": str(e)}
    
    def _calculate_reputation(self, dashboard: Dict) -> int:
        """
        Calculate reputation score from available data
        Formula: Base 10 + (deals * 5) + (reviews * 3) + (revenue / 100) + (months * 2)
        """
        reputation = 10  # Base score
        
        # From revenue stats (proxy for deals)
        lifetime_revenue = dashboard["tier_progression"].get("lifetime_revenue", 0)
        estimated_deals = min(lifetime_revenue / 200, 50)  # Assume $200 avg deal, cap at 50
        reputation += int(estimated_deals * 5)
        
        # From revenue contribution
        reputation += int(lifetime_revenue / 100)
        
        # From activity (proxy for time)
        active_days = dashboard["activity_streaks"].get("total_active_days", 0)
        estimated_months = active_days / 30
        reputation += int(estimated_months * 2)
        
        # Cap at 200
        return min(reputation, 200)
    
    async def generate_opportunities(
        self, 
        username: str, 
        intelligence: Dict
    ) -> List[Dict]:
        """
        Generate and score revenue opportunities based on business intelligence
        
        Returns ranked list of opportunities with:
        - Revenue potential
        - Time to first dollar
        - Confidence score
        - Required actions
        - Readiness status
        """
        
        kit_type = intelligence["capabilities"]["kit_type"]
        reputation = intelligence["reputation"]
        tier = intelligence["capabilities"]["tier"]
        apex_ready = intelligence["systems"]["apex_ultra_active"]
        
        # Get kit-specific opportunities
        opportunities = self._get_kit_opportunities(
            kit_type=kit_type,
            reputation=reputation,
            tier=tier,
            apex_ready=apex_ready
        )
        
        # Score and rank opportunities
        scored_opportunities = []
        for opp in opportunities:
            score = self._score_opportunity(opp, intelligence)
            opp["score"] = score
            opp["expected_value"] = (
                opp["revenue_potential"] * 
                opp["confidence"] / 
                max(opp["time_to_first_dollar"], 1)
            )
            scored_opportunities.append(opp)
        
        # Sort by expected value
        scored_opportunities.sort(key=lambda x: x["expected_value"], reverse=True)
        
        return scored_opportunities[:5]  # Return top 5
    
    def _get_kit_opportunities(
        self, 
        kit_type: str, 
        reputation: int,
        tier: str,
        apex_ready: bool
    ) -> List[Dict]:
        """
        Get predefined opportunities for each kit type
        """
        
        opportunities_map = {
            "legal": [
                {
                    "opportunity_id": "legal_safe_agreements",
                    "title": "SAFE Agreements",
                    "description": "Sell Y Combinator standard SAFE agreements at $500 each",
                    "revenue_potential": 4000,  # $500 x 8 per month
                    "time_to_first_dollar": 2,
                    "confidence": 0.90,
                    "pricing": "$500 per SAFE",
                    "target_customers": "Startups raising seed rounds, angel investors",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "activate_ame"],
                    "unlock_requirements": None
                },
                {
                    "opportunity_id": "legal_nda_templates",
                    "title": "NDA Templates",
                    "description": "Generate and sell customized NDAs at $200 each",
                    "revenue_potential": 2800,  # $200 x 14 per week
                    "time_to_first_dollar": 2,  # hours
                    "confidence": 0.85,
                    "pricing": "$200 per NDA",
                    "target_customers": "Startups, small businesses, entrepreneurs",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "activate_ame"],
                    "unlock_requirements": None
                },
                {
                    "opportunity_id": "legal_ip_licensing",
                    "title": "IP Assignment Frameworks",
                    "description": "License IP assignment templates at $500-2k each",
                    "revenue_potential": 6000,  # $500-2k x 3-6 per month
                    "time_to_first_dollar": 4,
                    "confidence": 0.75,
                    "pricing": "$500-2,000 per agreement",
                    "target_customers": "Tech companies, creative agencies, consultants",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "activate_ame", "partner_outreach"],
                    "unlock_requirements": None
                },
                {
                    "opportunity_id": "legal_compliance_audits",
                    "title": "Compliance Audits",
                    "description": "Offer comprehensive compliance audits at $1,500 each",
                    "revenue_potential": 12000,  # $1,500 x 8 per month
                    "time_to_first_dollar": 8,
                    "confidence": 0.70,
                    "pricing": "$1,500 per audit",
                    "target_customers": "Mid-size businesses, regulated industries",
                    "readiness_status": "unlock_needed" if reputation < 25 else "ready_now",
                    "required_actions": ["generate_documents", "activate_ame"],
                    "unlock_requirements": {"reputation": 25} if reputation < 25 else None
                }
            ],
            
            "saas": [
                {
                    "opportunity_id": "saas_micro_tools",
                    "title": "Micro-SaaS Tools",
                    "description": "Build and sell specialized micro-tools at $50-500",
                    "revenue_potential": 4000,  # $200 avg x 20 per month
                    "time_to_first_dollar": 6,
                    "confidence": 0.80,
                    "pricing": "$50-500 per tool",
                    "target_customers": "Developers, agencies, small businesses",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "activate_ame"],
                    "unlock_requirements": None
                },
                {
                    "opportunity_id": "saas_api_licensing",
                    "title": "White-Label APIs",
                    "description": "License APIs to agencies at $5k+ each",
                    "revenue_potential": 15000,  # $5k x 3 per month
                    "time_to_first_dollar": 12,
                    "confidence": 0.65,
                    "pricing": "$5,000+ per license",
                    "target_customers": "Marketing agencies, dev shops, enterprises",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "partner_outreach"],
                    "unlock_requirements": None
                },
                {
                    "opportunity_id": "saas_custom_integrations",
                    "title": "Custom Integrations",
                    "description": "Build custom integrations at $2k-10k per project",
                    "revenue_potential": 20000,  # $5k avg x 4 per month
                    "time_to_first_dollar": 16,
                    "confidence": 0.70,
                    "pricing": "$2,000-10,000 per project",
                    "target_customers": "Enterprises, SaaS companies",
                    "readiness_status": "unlock_needed" if reputation < 50 else "ready_now",
                    "required_actions": ["generate_documents", "activate_ame"],
                    "unlock_requirements": {"reputation": 50} if reputation < 50 else None
                }
            ],
            
            "marketing": [
                {
                    "opportunity_id": "marketing_seo_audits",
                    "title": "SEO Audits",
                    "description": "Deliver comprehensive SEO audits at $500 each",
                    "revenue_potential": 4000,  # $500 x 8 per month
                    "time_to_first_dollar": 3,
                    "confidence": 0.85,
                    "pricing": "$500 per audit",
                    "target_customers": "Local businesses, e-commerce, content sites",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "activate_ame"],
                    "unlock_requirements": None
                },
                {
                    "opportunity_id": "marketing_ad_management",
                    "title": "Ad Campaign Management",
                    "description": "Manage ad campaigns at 15% of ad spend",
                    "revenue_potential": 7500,  # 15% of $50k spend per month
                    "time_to_first_dollar": 8,
                    "confidence": 0.75,
                    "pricing": "15% of ad spend",
                    "target_customers": "E-commerce, lead gen businesses, agencies",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "activate_ame"],
                    "unlock_requirements": None
                },
                {
                    "opportunity_id": "marketing_growth_retainers",
                    "title": "Growth Consulting Retainers",
                    "description": "Monthly growth consulting at $1,500/month",
                    "revenue_potential": 9000,  # $1,500 x 6 clients
                    "time_to_first_dollar": 10,
                    "confidence": 0.70,
                    "pricing": "$1,500 per month",
                    "target_customers": "Startups, SaaS companies, B2B businesses",
                    "readiness_status": "unlock_needed" if reputation < 50 else "ready_now",
                    "required_actions": ["generate_documents", "partner_outreach"],
                    "unlock_requirements": {"reputation": 50} if reputation < 50 else None
                }
            ],
            
            "social": [
                {
                    "opportunity_id": "social_sponsored_content",
                    "title": "Sponsored Content",
                    "description": "Get matched with brands paying $500-5k per post",
                    "revenue_potential": 10000,  # $2k avg x 5 per month
                    "time_to_first_dollar": 4,
                    "confidence": 0.80,
                    "pricing": "$500-5,000 per post",
                    "target_customers": "Brands, marketing agencies, direct advertisers",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "partner_outreach"],
                    "unlock_requirements": None
                },
                {
                    "opportunity_id": "social_creator_kits",
                    "title": "Creator Kits & Templates",
                    "description": "Sell creator kits and templates at $50-200",
                    "revenue_potential": 3000,  # $100 avg x 30 per month
                    "time_to_first_dollar": 2,
                    "confidence": 0.85,
                    "pricing": "$50-200 per kit",
                    "target_customers": "Content creators, influencers, agencies",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "activate_ame"],
                    "unlock_requirements": None
                },
                {
                    "opportunity_id": "social_management_services",
                    "title": "Social Media Management",
                    "description": "Manage social accounts at $1,500/month per client",
                    "revenue_potential": 9000,  # $1,500 x 6 clients
                    "time_to_first_dollar": 8,
                    "confidence": 0.75,
                    "pricing": "$1,500 per month",
                    "target_customers": "Small businesses, personal brands, startups",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "activate_ame"],
                    "unlock_requirements": None
                }
            ],
            
            "general": [
                {
                    "opportunity_id": "general_service_packages",
                    "title": "Service Packages",
                    "description": "Package your core service offering",
                    "revenue_potential": 3000,  # Generic estimate
                    "time_to_first_dollar": 4,
                    "confidence": 0.70,
                    "pricing": "Custom pricing based on service",
                    "target_customers": "Varies by service type",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "activate_ame"],
                    "unlock_requirements": None
                },
                {
                    "opportunity_id": "general_consulting",
                    "title": "Consulting Services",
                    "description": "Offer hourly or project-based consulting",
                    "revenue_potential": 4000,  # $200/hr x 20 hrs/month
                    "time_to_first_dollar": 3,
                    "confidence": 0.75,
                    "pricing": "$150-300 per hour",
                    "target_customers": "Businesses needing expertise",
                    "readiness_status": "ready_now",
                    "required_actions": ["generate_documents", "activate_ame"],
                    "unlock_requirements": None
                }
            ]
        }
        
        return opportunities_map.get(kit_type, opportunities_map["general"])
    
    def _score_opportunity(self, opportunity: Dict, intelligence: Dict) -> float:
        """
        Score an opportunity based on user's current state
        Returns score 0-100
        """
        score = 50  # Base score
        
        # Boost if APEX ready
        if intelligence["systems"]["apex_ultra_active"]:
            score += 10
        
        # Boost based on tier
        tier_boost = {"free": 0, "pro": 10, "ultra": 20}
        score += tier_boost.get(intelligence["capabilities"]["tier"], 0)
        
        # Boost based on early adopter status
        if intelligence["capabilities"]["early_adopter_badge"]:
            score += 10
        
        # Penalty if unlock needed
        if opportunity["readiness_status"] == "unlock_needed":
            score -= 20
        
        # Confidence adjustment
        score *= opportunity["confidence"]
        
        return min(max(score, 0), 100)  # Clamp 0-100
    
    async def format_opportunities_for_chat(
        self, 
        opportunities: List[Dict],
        intelligence: Dict
    ) -> str:
        """
        Format opportunities as readable text for chat response
        """
        
        if not opportunities:
            return "No opportunities found for your business type."
        
        formatted = []
        
        for i, opp in enumerate(opportunities[:3], 1):
            status_emoji = "🚀" if opp["readiness_status"] == "ready_now" else "🔒"
            
            opp_text = f"""
{i}. {status_emoji} **{opp['title']}** ({opp['pricing']})
   • {opp['description']}
   • Target: {opp['target_customers']}
   • Est. Revenue: ${opp['revenue_potential']:,}/month
   • Time to $: {opp['time_to_first_dollar']} hours
   • Confidence: {int(opp['confidence'] * 100)}%
"""
            
            if opp["readiness_status"] == "unlock_needed" and opp.get("unlock_requirements"):
                req = opp["unlock_requirements"]
                if "reputation" in req:
                    current_rep = intelligence["reputation"]
                    needed = req["reputation"] - current_rep
                    opp_text += f"   • 🔒 Unlock at Rep {req['reputation']} ({needed} points to go)\n"
            else:
                opp_text += f"   • ✅ READY NOW\n"
            
            formatted.append(opp_text)
        
        return "\n".join(formatted)


# Singleton instance
_orchestrator = None

def get_orchestrator() -> CSuiteOrchestrator:
    """Get or create orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CSuiteOrchestrator()
    return _orchestrator
