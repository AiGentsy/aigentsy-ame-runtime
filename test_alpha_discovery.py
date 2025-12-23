"""
ALPHA DISCOVERY ENGINE - TEST SUITE
Test all components of Phase 1
"""

import asyncio
from alpha_discovery_engine import AlphaDiscoveryEngine, CapabilityMatcher, AlphaDiscoveryRouter
from explicit_marketplace_scrapers import ExplicitMarketplaceScrapers
from wade_approval_dashboard import fulfillment_queue


async def test_capability_matcher():
    """Test capability matching logic"""
    
    print("\n" + "="*70)
    print("TEST 1: CAPABILITY MATCHER")
    print("="*70)
    
    matcher = CapabilityMatcher()
    
    # Test 1: AiGentsy CAN fulfill (software development)
    opp1 = {
        'type': 'software_development',
        'title': 'Build React App',
        'value': 5000
    }
    
    result1 = matcher.check_aigentsy_capability(opp1)
    print(f"\n✅ Software Development:")
    print(f"   Can fulfill: {result1['can_fulfill']}")
    print(f"   Confidence: {result1['confidence']}")
    print(f"   Estimated profit: ${result1.get('estimated_profit', 0):,.0f}")
    
    # Test 2: AiGentsy CANNOT fulfill (physical product)
    opp2 = {
        'type': 'physical_product_manufacturing',
        'title': 'Make flower pots',
        'value': 1000
    }
    
    result2 = matcher.check_aigentsy_capability(opp2)
    print(f"\n❌ Physical Product:")
    print(f"   Can fulfill: {result2['can_fulfill']}")
    print(f"   Reason: {result2.get('reason', 'N/A')}")
    
    # Test 3: Fuzzy matching (content in title)
    opp3 = {
        'type': 'consulting',
        'title': 'Need help with data analysis and visualization',
        'description': 'Looking for someone to analyze our sales data',
        'value': 3000
    }
    
    result3 = matcher.check_aigentsy_capability(opp3)
    print(f"\n✅ Fuzzy Match (data analysis):")
    print(f"   Can fulfill: {result3['can_fulfill']}")
    print(f"   Matched capability: {result3.get('matched_capability', 'N/A')}")
    print(f"   Confidence: {result3['confidence']}")


async def test_router():
    """Test routing logic"""
    
    print("\n" + "="*70)
    print("TEST 2: INTELLIGENT ROUTER")
    print("="*70)
    
    router = AlphaDiscoveryRouter()
    
    # Test 1: Route to AiGentsy (no users exist)
    opp1 = {
        'id': 'test_1',
        'platform': 'test',
        'type': 'content_creation',
        'title': 'Write blog posts',
        'description': 'Need 10 blog posts',
        'value': 1000
    }
    
    routing1 = await router.route_opportunity(opp1)
    print(f"\nRouting Decision 1:")
    print(f"   Method: {routing1['fulfillment_method'].value}")
    print(f"   Routed to: {routing1['routed_to']}")
    print(f"   Reasoning: {routing1['reasoning']}")
    
    # Test 2: Physical product (should be held)
    opp2 = {
        'id': 'test_2',
        'platform': 'test',
        'type': 'physical_product_manufacturing',
        'title': 'Make custom furniture',
        'description': 'Need carpenter',
        'value': 5000
    }
    
    routing2 = await router.route_opportunity(opp2)
    print(f"\nRouting Decision 2:")
    print(f"   Method: {routing2['fulfillment_method'].value}")
    print(f"   Reasoning: {routing2['reasoning']}")
    print(f"   Recommendation: {routing2.get('recommendation', 'N/A')}")


async def test_scrapers():
    """Test marketplace scrapers"""
    
    print("\n" + "="*70)
    print("TEST 3: EXPLICIT MARKETPLACE SCRAPERS")
    print("="*70)
    
    scrapers = ExplicitMarketplaceScrapers()
    
    # Test GitHub scraper
    print("\n🔍 Testing GitHub scraper...")
    github_opps = await scrapers.scrape_github()
    print(f"   Found {len(github_opps)} opportunities")
    if github_opps:
        print(f"   Sample: {github_opps[0]['title'][:50]}...")
    
    # Test Reddit scraper
    print("\n🔍 Testing Reddit scraper...")
    reddit_opps = await scrapers.scrape_reddit()
    print(f"   Found {len(reddit_opps)} opportunities")
    if reddit_opps:
        print(f"   Sample: {reddit_opps[0]['title'][:50]}...")
    
    # Test HackerNews scraper
    print("\n🔍 Testing HackerNews scraper...")
    hn_opps = await scrapers.scrape_hackernews()
    print(f"   Found {len(hn_opps)} opportunities")
    if hn_opps:
        print(f"   Sample: {hn_opps[0]['title'][:50]}...")
    
    # Test Upwork (simulated)
    print("\n🔍 Testing Upwork scraper...")
    upwork_opps = await scrapers.scrape_upwork()
    print(f"   Found {len(upwork_opps)} opportunities (simulated)")


async def test_full_discovery():
    """Test complete discovery pipeline"""
    
    print("\n" + "="*70)
    print("TEST 4: FULL ALPHA DISCOVERY PIPELINE")
    print("="*70)
    
    engine = AlphaDiscoveryEngine()
    
    # Run discovery
    results = await engine.discover_and_route()
    
    print(f"\n📊 RESULTS:")
    print(f"   Total opportunities: {results['total_opportunities']}")
    print(f"   Total value: ${results['total_value']:,.0f}")
    print(f"\n   → User routed: {results['routing']['user_routed']['count']}")
    print(f"      Revenue: ${results['routing']['user_routed']['aigentsy_revenue']:,.0f}")
    print(f"\n   → AiGentsy routed: {results['routing']['aigentsy_routed']['count']}")
    print(f"      Profit: ${results['routing']['aigentsy_routed']['estimated_profit']:,.0f}")
    print(f"\n   → Held: {results['routing']['held']['count']}")
    print(f"\n   💰 Total potential revenue: ${results['total_potential_revenue']:,.0f}")


async def test_wade_dashboard():
    """Test Wade's approval dashboard"""
    
    print("\n" + "="*70)
    print("TEST 5: WADE'S APPROVAL DASHBOARD")
    print("="*70)
    
    # Add test opportunities to queue
    test_opp = {
        'id': 'test_opp_1',
        'platform': 'github',
        'type': 'software_development',
        'title': 'Build authentication system',
        'value': 5000,
        'url': 'https://github.com/test'
    }
    
    test_routing = {
        'fulfillment_method': 'aigentsy_direct',
        'confidence': 0.90,
        'economics': {
            'estimated_cost': 1500,
            'estimated_profit': 3500,
            'estimated_days': 7
        },
        'capability': {
            'ai_models': ['claude', 'gpt4'],
            'tools': ['code_execution']
        }
    }
    
    # Add to queue
    fulfillment = fulfillment_queue.add_to_queue(test_opp, test_routing)
    
    print(f"\n✅ Added to queue:")
    print(f"   Fulfillment ID: {fulfillment['id']}")
    print(f"   Opportunity: {fulfillment['opportunity']['title']}")
    print(f"   Estimated profit: ${fulfillment['estimated_profit']:,.0f}")
    
    # Get queue
    pending = fulfillment_queue.get_pending_queue()
    print(f"\n📋 Pending queue: {len(pending)} items")
    
    # Get stats
    stats = fulfillment_queue.get_stats()
    print(f"\n📊 Queue stats:")
    print(f"   Pending: {stats['pending']['count']} (${stats['pending']['total_profit']:,.0f} profit)")
    
    # Approve fulfillment
    result = fulfillment_queue.approve_fulfillment(fulfillment['id'])
    print(f"\n✅ Approval result: {result['status']}")
    
    # Check stats after approval
    stats_after = fulfillment_queue.get_stats()
    print(f"\n📊 Stats after approval:")
    print(f"   Pending: {stats_after['pending']['count']}")
    print(f"   Approved: {stats_after['approved']['count']}")


async def run_all_tests():
    """Run all tests"""
    
    print("\n" + "="*70)
    print("🧪 ALPHA DISCOVERY ENGINE - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    await test_capability_matcher()
    await test_router()
    await test_scrapers()
    await test_full_discovery()
    await test_wade_dashboard()
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
