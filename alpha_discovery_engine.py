"""
ALPHA DISCOVERY ENGINE - CORE ORCHESTRATOR
The monetization railway for the AI/AGI economy

7 Discovery Dimensions:
1. Explicit Marketplaces (GitHub, Upwork, Reddit, HN) - BUILD NOW
2. Pain Point Detection (Twitter, App Store reviews) - Week 2
3. Flow Arbitrage (cross-platform, temporal) - Week 2
4. Predictive Intelligence (funding→hiring, launches→needs) - Week 3
5. Network Amplification (internal opportunities) - Week 3
6. Opportunity Creation (proactive outreach) - Week 4
7. Emergent Patterns (AI meta-analysis) - Week 4

Phase 1: Build Dimension 1 + Core Routing
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import hashlib
from enum import Enum


# ============================================================
# FULFILLMENT CAPABILITIES
# ============================================================

class FulfillmentMethod(Enum):
    """Who fulfills the opportunity"""
    USER = "user"  # Route to existing user
    AIGENTSY = "aigentsy_direct"  # AiGentsy fulfills
    HOLD = "hold_for_recruitment"  # Need to recruit user
    REJECT = "reject"  # Cannot fulfill


# AiGentsy's digital fulfillment capabilities
AIGENTSY_CAPABILITIES = {
    # Software & Development
    'software_development': {
        'confidence': 0.95,
        'ai_models': ['claude', 'gpt4'],
        'tools': ['code_execution', 'github'],
        'avg_delivery_days': 7,
        'cost_multiplier': 0.30,  # 30% cost, 70% profit
        'can_fulfill': True
    },
    'api_integration': {
        'confidence': 0.90,
        'ai_models': ['claude', 'gpt4'],
        'tools': ['code_execution'],
        'avg_delivery_days': 5,
        'cost_multiplier': 0.30,
        'can_fulfill': True
    },
    'web_development': {
        'confidence': 0.85,
        'ai_models': ['claude', 'gpt4'],
        'tools': ['code_execution', 'vercel'],
        'avg_delivery_days': 10,
        'cost_multiplier': 0.35,
        'can_fulfill': True
    },
    'mobile_development': {
        'confidence': 0.75,
        'ai_models': ['claude', 'gpt4'],
        'tools': ['code_execution'],
        'avg_delivery_days': 14,
        'cost_multiplier': 0.40,
        'can_fulfill': True
    },
    
    # Content & Creative
    'content_creation': {
        'confidence': 0.95,
        'ai_models': ['claude', 'gpt4'],
        'tools': [],
        'avg_delivery_days': 2,
        'cost_multiplier': 0.20,
        'can_fulfill': True
    },
    'copywriting': {
        'confidence': 0.95,
        'ai_models': ['claude', 'gpt4'],
        'tools': [],
        'avg_delivery_days': 1,
        'cost_multiplier': 0.20,
        'can_fulfill': True
    },
    'technical_writing': {
        'confidence': 0.90,
        'ai_models': ['claude'],
        'tools': [],
        'avg_delivery_days': 3,
        'cost_multiplier': 0.25,
        'can_fulfill': True
    },
    'blog_writing': {
        'confidence': 0.95,
        'ai_models': ['claude', 'gpt4'],
        'tools': [],
        'avg_delivery_days': 1,
        'cost_multiplier': 0.15,
        'can_fulfill': True
    },
    
    # Data & Analysis
    'data_analysis': {
        'confidence': 0.95,
        'ai_models': ['claude', 'gpt4'],
        'tools': ['code_execution', 'python'],
        'avg_delivery_days': 3,
        'cost_multiplier': 0.30,
        'can_fulfill': True
    },
    'data_visualization': {
        'confidence': 0.85,
        'ai_models': ['claude', 'gpt4'],
        'tools': ['code_execution', 'python'],
        'avg_delivery_days': 2,
        'cost_multiplier': 0.30,
        'can_fulfill': True
    },
    'spreadsheet_automation': {
        'confidence': 0.90,
        'ai_models': ['claude', 'gpt4'],
        'tools': ['code_execution', 'python'],
        'avg_delivery_days': 2,
        'cost_multiplier': 0.25,
        'can_fulfill': True
    },
    
    # Business & Strategy
    'business_consulting': {
        'confidence': 0.85,
        'ai_models': ['claude'],
        'tools': [],
        'avg_delivery_days': 5,
        'cost_multiplier': 0.20,
        'can_fulfill': True
    },
    'market_research': {
        'confidence': 0.90,
        'ai_models': ['claude', 'perplexity'],
        'tools': ['web_search'],
        'avg_delivery_days': 3,
        'cost_multiplier': 0.25,
        'can_fulfill': True
    },
    'seo_optimization': {
        'confidence': 0.80,
        'ai_models': ['claude', 'gpt4'],
        'tools': ['web_search'],
        'avg_delivery_days': 7,
        'cost_multiplier': 0.30,
        'can_fulfill': True
    },
    
    # Automation
    'workflow_automation': {
        'confidence': 0.85,
        'ai_models': ['claude', 'gpt4'],
        'tools': ['code_execution', 'zapier'],
        'avg_delivery_days': 5,
        'cost_multiplier': 0.30,
        'can_fulfill': True
    },
    'email_automation': {
        'confidence': 0.90,
        'ai_models': ['claude'],
        'tools': ['resend', 'sendgrid'],
        'avg_delivery_days': 3,
        'cost_multiplier': 0.25,
        'can_fulfill': True
    },
    
    # CANNOT FULFILL (Physical/Manual)
    'physical_product_manufacturing': {
        'confidence': 0.0,
        'reason': 'physical_product',
        'can_fulfill': False
    },
    'in_person_services': {
        'confidence': 0.0,
        'reason': 'requires_physical_presence',
        'can_fulfill': False
    },
    'manual_labor': {
        'confidence': 0.0,
        'reason': 'physical_labor',
        'can_fulfill': False
    },
    'licensed_professional_services': {
        'confidence': 0.0,
        'reason': 'requires_human_license',
        'can_fulfill': False
    }
}


# ============================================================
# CAPABILITY MATCHER
# ============================================================

class CapabilityMatcher:
    """
    Determines: Can user fulfill? Can AiGentsy fulfill?
    """
    
    def __init__(self):
        self.aigentsy_capabilities = AIGENTSY_CAPABILITIES
    
    def check_aigentsy_capability(self, opportunity: Dict) -> Dict:
        """
        Can AiGentsy fulfill this opportunity?
        
        Returns:
            {
                'can_fulfill': bool,
                'confidence': float,
                'method': 'aigentsy_direct',
                'estimated_cost': float,
                'estimated_days': int,
                'ai_models': List[str],
                'reason': str (if cannot fulfill)
            }
        """
        
        opp_type = opportunity.get('type', '').lower()
        opp_title = opportunity.get('title', '').lower()
        opp_description = opportunity.get('description', '').lower()
        
        # Direct match on opportunity type
        if opp_type in self.aigentsy_capabilities:
            cap = self.aigentsy_capabilities[opp_type]
            
            if not cap.get('can_fulfill', False):
                return {
                    'can_fulfill': False,
                    'reason': cap.get('reason', 'not_in_capability_set'),
                    'confidence': 0.0
                }
            
            # Estimate cost
            value = opportunity.get('value', 0)
            estimated_cost = value * cap['cost_multiplier']
            
            return {
                'can_fulfill': True,
                'confidence': cap['confidence'],
                'method': 'aigentsy_direct',
                'estimated_cost': estimated_cost,
                'estimated_profit': value - estimated_cost,
                'estimated_days': cap['avg_delivery_days'],
                'ai_models': cap['ai_models'],
                'tools': cap.get('tools', [])
            }
        
        # Fuzzy matching on title/description
        capability_matches = []
        
        for cap_name, cap_config in self.aigentsy_capabilities.items():
            if not cap_config.get('can_fulfill', False):
                continue
            
            # Check if capability keywords in title/description
            if cap_name.replace('_', ' ') in opp_title or cap_name.replace('_', ' ') in opp_description:
                capability_matches.append((cap_name, cap_config))
        
        if capability_matches:
            # Use first match (could be improved with scoring)
            best_match = capability_matches[0]
            cap_name, cap_config = best_match
            
            value = opportunity.get('value', 0)
            estimated_cost = value * cap_config['cost_multiplier']
            
            return {
                'can_fulfill': True,
                'confidence': cap_config['confidence'] * 0.8,  # Lower confidence for fuzzy match
                'method': 'aigentsy_direct',
                'matched_capability': cap_name,
                'estimated_cost': estimated_cost,
                'estimated_profit': value - estimated_cost,
                'estimated_days': cap_config['avg_delivery_days'],
                'ai_models': cap_config['ai_models']
            }
        
        # Cannot fulfill
        return {
            'can_fulfill': False,
            'reason': 'no_matching_capability',
            'confidence': 0.0,
            'recommendation': 'route_to_user_or_recruit'
        }
    
    async def find_matching_users(self, opportunity: Dict) -> List[Dict]:
        """
        Find users whose businesses can fulfill this opportunity
        
        Returns list of matching users with scores
        """
        
        # Import here to avoid circular dependency
        from log_to_jsonbin import list_users
        
        try:
            all_users = list_users()
        except:
            return []
        
        matches = []
        
        for user in all_users:
            # Check if user has deployed business
            if not user.get('storefront_url'):
                continue
            
            # Check business type match
            company_type = user.get('companyType', '').lower()
            opp_type = opportunity.get('type', '').lower()
            
            # Simple matching logic (can be enhanced)
            score = 0.0
            
            # Marketing business matches marketing opportunities
            if company_type == 'marketing' and any(kw in opp_type for kw in ['marketing', 'seo', 'content', 'social']):
                score = 0.85
            
            # SaaS business matches dev opportunities
            elif company_type == 'saas' and any(kw in opp_type for kw in ['software', 'development', 'api', 'web', 'app']):
                score = 0.85
            
            # Social business matches content opportunities
            elif company_type == 'social' and any(kw in opp_type for kw in ['content', 'social', 'video', 'creative']):
                score = 0.85
            
            if score > 0:
                matches.append({
                    'username': user['username'],
                    'company_type': company_type,
                    'storefront_url': user['storefront_url'],
                    'score': score,
                    'user_data': user
                })
        
        # Sort by score
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches


# ============================================================
# INTELLIGENT ROUTER
# ============================================================

class AlphaDiscoveryRouter:
    """
    Smart routing: User first, AiGentsy backstop, Hold if neither
    
    PRIORITY:
    1. USER (always default - infinite scale)
    2. AIGENTSY (only if we can fulfill - high margins)
    3. HOLD (recruit user with this capability)
    4. REJECT (cannot fulfill at all)
    """
    
    def __init__(self):
        self.capability_matcher = CapabilityMatcher()
    
    async def route_opportunity(self, opportunity: Dict) -> Dict:
        """
        Intelligent routing decision
        
        Returns:
            {
                'fulfillment_method': FulfillmentMethod,
                'routed_to': username (if user) or 'aigentsy' or None,
                'confidence': float,
                'reasoning': str,
                'economics': {...}
            }
        """
        
        print(f"\n🎯 ROUTING: {opportunity['title'][:50]}...")
        
        # STEP 1: Try to match to existing user
        matching_users = await self.capability_matcher.find_matching_users(opportunity)
        
        if matching_users and matching_users[0]['score'] > 0.70:
            # HIGH CONFIDENCE USER MATCH - Route to user
            user = matching_users[0]
            
            value = opportunity.get('value', 0)
            user_revenue = value * 0.972  # User gets 97.2%
            aigentsy_fee = value * 0.028  # AiGentsy gets 2.8%
            
            print(f"   ✅ ROUTE TO USER: {user['username']} (confidence: {user['score']})")
            print(f"   💰 Economics: User gets ${user_revenue:,.0f}, AiGentsy gets ${aigentsy_fee:,.0f}")
            
            return {
                'fulfillment_method': FulfillmentMethod.USER,
                'routed_to': user['username'],
                'confidence': user['score'],
                'reasoning': f"User {user['username']} has matching {user['company_type']} business",
                'economics': {
                    'opportunity_value': value,
                    'user_revenue': user_revenue,
                    'aigentsy_fee': aigentsy_fee,
                    'aigentsy_margin': 0.028
                },
                'user_data': user
            }
        
        # STEP 2: Check if AiGentsy can fulfill
        aigentsy_capability = self.capability_matcher.check_aigentsy_capability(opportunity)
        
        if aigentsy_capability['can_fulfill'] and aigentsy_capability['confidence'] > 0.70:
            # AIGENTSY CAN FULFILL - Backstop mode
            
            value = opportunity.get('value', 0)
            cost = aigentsy_capability['estimated_cost']
            profit = aigentsy_capability['estimated_profit']
            margin = profit / value if value > 0 else 0
            
            print(f"   ✅ ROUTE TO AIGENTSY: {aigentsy_capability.get('matched_capability', opportunity['type'])}")
            print(f"   💰 Economics: Value ${value:,.0f}, Cost ${cost:,.0f}, Profit ${profit:,.0f} ({margin*100:.0f}% margin)")
            
            return {
                'fulfillment_method': FulfillmentMethod.AIGENTSY,
                'routed_to': 'aigentsy',
                'confidence': aigentsy_capability['confidence'],
                'reasoning': f"AiGentsy can fulfill via {', '.join(aigentsy_capability['ai_models'])}",
                'economics': {
                    'opportunity_value': value,
                    'estimated_cost': cost,
                    'estimated_profit': profit,
                    'margin': margin,
                    'estimated_days': aigentsy_capability['estimated_days']
                },
                'capability': aigentsy_capability,
                'requires_wade_approval': True
            }
        
        # STEP 3: Check if low-confidence user match exists
        if matching_users and matching_users[0]['score'] > 0.40:
            # LOW CONFIDENCE USER MATCH - Still route to user but flag
            user = matching_users[0]
            
            value = opportunity.get('value', 0)
            user_revenue = value * 0.972
            aigentsy_fee = value * 0.028
            
            print(f"   ⚠️  ROUTE TO USER (low confidence): {user['username']} (confidence: {user['score']})")
            
            return {
                'fulfillment_method': FulfillmentMethod.USER,
                'routed_to': user['username'],
                'confidence': user['score'],
                'reasoning': f"Low confidence match - review recommended",
                'low_confidence': True,
                'economics': {
                    'opportunity_value': value,
                    'user_revenue': user_revenue,
                    'aigentsy_fee': aigentsy_fee
                },
                'user_data': user
            }
        
        # STEP 4: Hold for future user recruitment
        print(f"   ⏸️  HOLD: Need to recruit user for {opportunity['type']}")
        
        return {
            'fulfillment_method': FulfillmentMethod.HOLD,
            'routed_to': None,
            'confidence': 0.0,
            'reasoning': f"No existing capability - recruit user for {opportunity['type']}",
            'recommendation': 'recruit_user',
            'opportunity_type_needed': opportunity['type'],
            'economics': {
                'opportunity_value': opportunity.get('value', 0),
                'potential_aigentsy_fee': opportunity.get('value', 0) * 0.028
            }
        }


# ============================================================
# MULTI-AI FULFILLMENT ORCHESTRATOR
# ============================================================

class MultiAIOrchestrator:
    """
    Coordinates multiple AI models for optimal fulfillment
    Claude + GPT-4 + Gemini + Perplexity working in tandem
    """
    
    def __init__(self):
        self.claude_available = True  # Always available in this environment
        self.gpt4_available = False  # Would need OpenAI API key
        self.gemini_available = False  # Would need Google API key
        self.perplexity_available = False  # Would need Perplexity API key
    
    async def orchestrate_fulfillment(self, opportunity: Dict, routing: Dict) -> Dict:
        """
        Decompose work and route to optimal AI for each subtask
        
        Phase 1: Use Claude for everything
        Future: Add GPT-4, Gemini, Perplexity when API keys available
        """
        
        # For now, Claude handles all work
        # Future enhancement: Route different subtasks to different AIs
        
        return {
            'primary_ai': 'claude',
            'orchestration_plan': {
                'analysis': 'claude',  # Claude best at reasoning
                'code': 'claude',  # Would use GPT-4 if available
                'research': 'claude',  # Would use Perplexity if available
                'synthesis': 'claude'
            },
            'estimated_quality': routing['confidence'],
            'ready_to_execute': True
        }


# ============================================================
# ALPHA DISCOVERY ENGINE - MAIN CLASS
# ============================================================

class AlphaDiscoveryEngine:
    """
    The ultimate opportunity detection and routing system
    
    Phase 1: Explicit Marketplaces + Intelligent Routing
    Future: 7 dimensions of discovery
    """
    
    def __init__(self):
        self.router = AlphaDiscoveryRouter()
        self.ai_orchestrator = MultiAIOrchestrator()
        
        # Phase 1: Explicit marketplace scrapers
        from explicit_marketplace_scrapers import ExplicitMarketplaceScrapers
        self.scrapers = ExplicitMarketplaceScrapers()
    
    async def discover_and_route(self, platforms: Optional[List[str]] = None) -> Dict:
        """
        Main discovery pipeline:
        1. Discover opportunities from all sources
        2. Route each opportunity intelligently
        3. Return categorized results
        """
        
        print("\n" + "="*70)
        print("🚀 ALPHA DISCOVERY ENGINE - DISCOVERY & ROUTING")
        print("="*70)
        
        # STEP 1: Discover opportunities
        print("\n📡 DISCOVERING OPPORTUNITIES...")
        
        opportunities = await self.scrapers.scrape_all(platforms=platforms)
        
        total_found = len(opportunities)
        total_value = sum(o.get('value', 0) for o in opportunities)
        
        print(f"\n✅ DISCOVERED: {total_found} opportunities (${total_value:,.0f} total value)")
        
        # STEP 2: Route each opportunity
        print(f"\n🎯 ROUTING {total_found} OPPORTUNITIES...")
        
        routed_results = []
        
        for opp in opportunities:
            routing = await self.router.route_opportunity(opp)
            
            routed_results.append({
                'opportunity': opp,
                'routing': routing
            })
        
        # STEP 3: Categorize results
        user_routed = [r for r in routed_results if r['routing']['fulfillment_method'] == FulfillmentMethod.USER]
        aigentsy_routed = [r for r in routed_results if r['routing']['fulfillment_method'] == FulfillmentMethod.AIGENTSY]
        held = [r for r in routed_results if r['routing']['fulfillment_method'] == FulfillmentMethod.HOLD]
        
        # Calculate economics
        user_value = sum(r['opportunity'].get('value', 0) for r in user_routed)
        aigentsy_value = sum(r['opportunity'].get('value', 0) for r in aigentsy_routed)
        held_value = sum(r['opportunity'].get('value', 0) for r in held)
        
        user_revenue = sum(r['routing']['economics'].get('aigentsy_fee', 0) for r in user_routed)
        aigentsy_profit = sum(r['routing']['economics'].get('estimated_profit', 0) for r in aigentsy_routed)
        
        print("\n" + "="*70)
        print("📊 ROUTING SUMMARY")
        print("="*70)
        print(f"\n✅ TO USERS: {len(user_routed)} opportunities (${user_value:,.0f})")
        print(f"   AiGentsy fee revenue: ${user_revenue:,.0f}")
        print(f"\n✅ TO AIGENTSY: {len(aigentsy_routed)} opportunities (${aigentsy_value:,.0f})")
        print(f"   Estimated profit: ${aigentsy_profit:,.0f}")
        print(f"\n⏸️  HELD: {len(held)} opportunities (${held_value:,.0f})")
        print(f"\n💰 TOTAL POTENTIAL REVENUE: ${user_revenue + aigentsy_profit:,.0f}")
        print("="*70)
        
        return {
            'ok': True,
            'total_opportunities': total_found,
            'total_value': total_value,
            'routing': {
                'user_routed': {
                    'count': len(user_routed),
                    'value': user_value,
                    'aigentsy_revenue': user_revenue,
                    'opportunities': user_routed
                },
                'aigentsy_routed': {
                    'count': len(aigentsy_routed),
                    'value': aigentsy_value,
                    'estimated_profit': aigentsy_profit,
                    'opportunities': aigentsy_routed,
                    'requires_approval': True
                },
                'held': {
                    'count': len(held),
                    'value': held_value,
                    'opportunities': held
                }
            },
            'total_potential_revenue': user_revenue + aigentsy_profit
        }


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    
    async def test_discovery():
        engine = AlphaDiscoveryEngine()
        
        # Discover and route all opportunities
        results = await engine.discover_and_route()
        
        print("\n✅ ALPHA DISCOVERY ENGINE TEST COMPLETE")
        print(f"   Total opportunities: {results['total_opportunities']}")
        print(f"   Potential revenue: ${results['total_potential_revenue']:,.0f}")
    
    # Run test
    asyncio.run(test_discovery())
