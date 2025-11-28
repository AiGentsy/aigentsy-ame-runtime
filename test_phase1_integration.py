"""
AiGentsy Phase 1 Integration Test Suite
Tests all 9 tasks end-to-end to validate the complete system

Run with: python test_phase1_integration.py
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuration
BASE_URL = "https://aigentsy.com"
TEST_USERNAME = "wade9877"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_section(msg):
    print(f"\n{Colors.YELLOW}{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}{Colors.END}\n")


async def test_revenue_ingestion_with_platform_attribution():
    """TEST 1: Revenue ingestion → Platform attribution → Outcome tracking → Unlocks"""
    print_section("TEST 1: Revenue Flow with Platform Attribution")
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # Test 1A: AME conversion on Instagram
        print_info("1A: Ingesting AME conversion on Instagram ($5,000)")
        try:
            r = await client.post(f"{BASE_URL}/revenue/ingest_ame", json={
                "username": TEST_USERNAME,
                "pitch_id": "test-pitch-instagram-001",
                "amount_usd": 5000.0,
                "recipient": "InstagramBrandCo",
                "platform": "instagram"
            })
            result = r.json()
            
            if result.get("ok"):
                print_success(f"AME conversion ingested: ${result.get('revenue')} on {result.get('platform')}")
                print_info(f"  User net: ${result.get('user_net')}")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")
        
        # Test 1B: TikTok affiliate commission
        print_info("1B: Ingesting TikTok affiliate commission ($250)")
        try:
            r = await client.post(f"{BASE_URL}/revenue/ingest_affiliate", json={
                "username": TEST_USERNAME,
                "source": "tiktok",
                "revenue_usd": 250.0,
                "product_id": "tiktok-widget-123"
            })
            result = r.json()
            
            if result.get("ok"):
                print_success(f"Affiliate commission ingested: ${result.get('revenue')} on {result.get('platform', 'tiktok')}")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")
        
        # Test 1C: LinkedIn AME conversion
        print_info("1C: Ingesting AME conversion on LinkedIn ($3,000)")
        try:
            r = await client.post(f"{BASE_URL}/revenue/ingest_ame", json={
                "username": TEST_USERNAME,
                "pitch_id": "test-pitch-linkedin-002",
                "amount_usd": 3000.0,
                "recipient": "LinkedInConsultingCo",
                "platform": "linkedin"
            })
            result = r.json()
            
            if result.get("ok"):
                print_success(f"AME conversion ingested: ${result.get('revenue')} on {result.get('platform')}")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")
        
        # Test 1D: YouTube CPM
        print_info("1D: Ingesting YouTube CPM revenue (50k views @ $5 CPM)")
        try:
            r = await client.post(f"{BASE_URL}/revenue/ingest_cpm", json={
                "username": TEST_USERNAME,
                "platform": "YouTube",
                "views": 50000,
                "cpm_rate": 5.0
            })
            result = r.json()
            
            if result.get("ok"):
                print_success(f"CPM revenue ingested: ${result.get('revenue')} from {result.get('views')} views")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")
        
        await asyncio.sleep(1)  # Let backend process
        
        # Verify: Check revenue summary
        print_info("Verifying: Revenue summary")
        try:
            r = await client.get(f"{BASE_URL}/revenue/summary", params={"username": TEST_USERNAME})
            result = r.json()
            
            if result.get("ok"):
                print_success(f"Total revenue: ${result.get('total_earned')}")
                print_info(f"  Breakdown: {json.dumps(result.get('breakdown'), indent=2)}")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")
        
        # Verify: Check platform attribution
        print_info("Verifying: Platform attribution")
        try:
            r = await client.get(f"{BASE_URL}/revenue/by_platform", params={"username": TEST_USERNAME})
            result = r.json()
            
            if result.get("ok"):
                print_success(f"Revenue by platform:")
                for platform, amount in result.get("byPlatform", {}).items():
                    print_info(f"  {platform}: ${amount}")
                print_info(f"Top platform: {result.get('topPlatform')}")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")


async def test_outcome_oracle_and_unlocks():
    """TEST 2: Outcome tracking → Feature unlocks → Notifications"""
    print_section("TEST 2: Outcome Oracle & Smart Unlocks")
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # Check unlock status
        print_info("Checking unlock status after revenue events")
        try:
            r = await client.get(f"{BASE_URL}/unlocks/status", params={"username": TEST_USERNAME})
            result = r.json()
            
            if result.get("ok"):
                summary = result.get("summary", {})
                print_success(f"Unlocks: {summary.get('totalUnlocked')} / {summary.get('totalAvailable')}")
                print_info(f"  PAID outcomes: {summary.get('paidOutcomes')}")
                print_info(f"  DELIVERED outcomes: {summary.get('deliveredOutcomes')}")
                
                features = result.get("unlocks", {})
                
                # Check outcome-based unlocks
                print_info("\nOutcome-based features:")
                ocl = features.get("ocl", {})
                if ocl.get("enabled"):
                    print_success(f"  OCL: Phase {ocl.get('phase')} - ${ocl.get('creditLine')} credit line")
                else:
                    print_info(f"  OCL: Locked - {ocl.get('nextMilestone')}")
                
                factoring = features.get("factoring", {})
                if factoring.get("enabled"):
                    print_success(f"  Factoring: Phase {factoring.get('phase')}")
                else:
                    print_info(f"  Factoring: Locked - {factoring.get('nextMilestone')}")
                
                ipvault = features.get("ipVault", {})
                if ipvault.get("enabled"):
                    print_success(f"  IPVault: {ipvault.get('royaltyRate')*100}% royalty rate")
                else:
                    print_info(f"  IPVault: Locked - {ipvault.get('progress')}")
                
                # Check revenue-based unlocks
                print_info("\nRevenue-based features:")
                if features.get("r3Autopilot", {}).get("enabled"):
                    print_success("  R³ Autopilot: Unlocked")
                else:
                    print_info(f"  R³ Autopilot: {features.get('r3Autopilot', {}).get('progress')}")
                
                if features.get("advancedAnalytics", {}).get("enabled"):
                    print_success("  Advanced Analytics: Unlocked")
                else:
                    print_info(f"  Advanced Analytics: {features.get('advancedAnalytics', {}).get('progress')}")
                
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")
        
        # Check notifications
        print_info("\nChecking notifications")
        try:
            r = await client.get(f"{BASE_URL}/notifications/list", params={
                "username": TEST_USERNAME,
                "unread_only": True
            })
            result = r.json()
            
            if result.get("ok"):
                notifications = result.get("notifications", [])
                unread_count = result.get("unreadCount", 0)
                
                if unread_count > 0:
                    print_success(f"Found {unread_count} unread notifications:")
                    for notif in notifications[:5]:  # Show first 5
                        print_info(f"  [{notif.get('type')}] {notif.get('title')}")
                        print_info(f"    {notif.get('message')}")
                else:
                    print_info("No unread notifications")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")


async def test_revenue_attribution_analytics():
    """TEST 3: Revenue attribution & analytics endpoints"""
    print_section("TEST 3: Revenue Attribution Analytics")
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # Test attribution history
        print_info("Fetching attribution history")
        try:
            r = await client.get(f"{BASE_URL}/revenue/attribution", params={
                "username": TEST_USERNAME,
                "limit": 10
            })
            result = r.json()
            
            if result.get("ok"):
                print_success(f"Retrieved {result.get('returnedRecords')} records (total: {result.get('totalRecords')})")
                for attr in result.get("attribution", [])[:3]:
                    print_info(f"  {attr.get('source')} on {attr.get('platform')}: ${attr.get('amount')}")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")
        
        # Test filtered attribution (Instagram only)
        print_info("\nFetching Instagram attribution only")
        try:
            r = await client.get(f"{BASE_URL}/revenue/attribution", params={
                "username": TEST_USERNAME,
                "platform": "instagram",
                "limit": 10
            })
            result = r.json()
            
            if result.get("ok"):
                print_success(f"Instagram deals: {result.get('filteredRecords')}")
                for attr in result.get("attribution", []):
                    print_info(f"  {attr.get('source')}: ${attr.get('amount')} - {attr.get('client', attr.get('product'))}")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")
        
        # Test top performers
        print_info("\nFetching top performers")
        try:
            r = await client.get(f"{BASE_URL}/revenue/top_performers", params={"username": TEST_USERNAME})
            result = r.json()
            
            if result.get("ok"):
                print_success("Top Sources:")
                for src in result.get("topSources", [])[:3]:
                    print_info(f"  {src.get('source')}: ${src.get('revenue')}")
                
                print_success("\nTop Platforms:")
                for plat in result.get("topPlatforms", [])[:3]:
                    print_info(f"  {plat.get('platform')}: ${plat.get('revenue')}")
                
                print_success("\nTop Combinations:")
                for combo in result.get("topCombinations", [])[:3]:
                    print_info(f"  {combo.get('source')} on {combo.get('platform')}: ${combo.get('revenue')}")
                
                print_info(f"\nTotal deals: {result.get('totalDeals')}")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")
        
        # Test platform breakdown
        print_info("\nFetching Instagram platform breakdown")
        try:
            r = await client.get(f"{BASE_URL}/revenue/platform_breakdown", params={
                "username": TEST_USERNAME,
                "platform": "instagram"
            })
            result = r.json()
            
            if result.get("ok"):
                print_success(f"Instagram revenue: ${result.get('totalRevenue')}")
                print_info(f"  Deals: {result.get('dealCount')}")
                print_info(f"  Avg deal size: ${result.get('avgDealSize')}")
                print_info("  By source:")
                for src, amt in result.get("bySource", {}).items():
                    print_info(f"    {src}: ${amt}")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")


async def test_intent_exchange_flow():
    """TEST 4: Intent Exchange end-to-end"""
    print_section("TEST 4: Intent Exchange Flow")
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        print_info("Testing Intent Exchange settlement")
        try:
            r = await client.post(f"{BASE_URL}/revenue/ingest_intent_settlement", json={
                "username": TEST_USERNAME,
                "intent_id": "test-intent-001",
                "amount_usd": 2500.0,
                "buyer": "TestBuyer",
                "platform": "intent_exchange"
            })
            result = r.json()
            
            if result.get("ok"):
                print_success(f"Intent settlement: ${result.get('revenue')}")
                print_info(f"  User net: ${result.get('user_net')}")
                print_info(f"  Total revenue: ${result.get('total_revenue')}")
            else:
                print_error(f"Failed: {result.get('error')}")
        except Exception as e:
            print_error(f"Exception: {e}")


async def test_cross_platform_consistency():
    """TEST 5: Cross-platform data consistency"""
    print_section("TEST 5: Data Consistency Check")
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        print_info("Fetching data from multiple endpoints")
        
        # Fetch from different endpoints
        summary = attribution = by_platform = None
        
        try:
            r = await client.get(f"{BASE_URL}/revenue/summary", params={"username": TEST_USERNAME})
            summary = r.json()
        except Exception as e:
            print_error(f"Summary fetch failed: {e}")
        
        try:
            r = await client.get(f"{BASE_URL}/revenue/attribution", params={"username": TEST_USERNAME, "limit": 100})
            attribution = r.json()
        except Exception as e:
            print_error(f"Attribution fetch failed: {e}")
        
        try:
            r = await client.get(f"{BASE_URL}/revenue/by_platform", params={"username": TEST_USERNAME})
            by_platform = r.json()
        except Exception as e:
            print_error(f"By platform fetch failed: {e}")
        
        # Check consistency
        if summary and attribution and by_platform:
            summary_total = summary.get("total_earned", 0)
            platform_total = by_platform.get("totalRevenue", 0)
            
            print_info(f"Summary total: ${summary_total}")
            print_info(f"Platform total: ${platform_total}")
            
            if abs(summary_total - platform_total) < 0.01:  # Allow for rounding
                print_success("✅ Revenue totals are consistent across endpoints")
            else:
                print_error(f"❌ Revenue mismatch: ${summary_total} vs ${platform_total}")
            
            # Check record counts
            attr_count = attribution.get("totalRecords", 0)
            print_info(f"Attribution records: {attr_count}")
            
            if attr_count > 0:
                print_success(f"✅ Attribution tracking is working ({attr_count} records)")
            else:
                print_error("❌ No attribution records found")


async def run_all_tests():
    """Run all integration tests"""
    print(f"\n{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print("║     AiGentsy Phase 1 Integration Test Suite              ║")
    print("║                                                           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(Colors.END)
    
    print_info(f"Testing against: {BASE_URL}")
    print_info(f"Test user: {TEST_USERNAME}")
    print_info(f"Timestamp: {datetime.now().isoformat()}\n")
    
    try:
        await test_revenue_ingestion_with_platform_attribution()
        await test_outcome_oracle_and_unlocks()
        await test_revenue_attribution_analytics()
        await test_intent_exchange_flow()
        await test_cross_platform_consistency()
        
        print_section("TEST SUITE COMPLETE")
        print_success("All tests finished! Review results above.")
        print_info("Check your backend logs for additional details.")
        
    except Exception as e:
        print_error(f"Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Configuration check
    print_info("Configuration:")
    print_info(f"  BASE_URL: {BASE_URL}")
    print_info(f"  TEST_USERNAME: {TEST_USERNAME}")
    
    proceed = input(f"\n{Colors.YELLOW}Proceed with tests? (y/n): {Colors.END}")
    if proceed.lower() == 'y':
        asyncio.run(run_all_tests())
    else:
        print_info("Tests cancelled")
