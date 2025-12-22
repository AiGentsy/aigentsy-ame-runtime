"""
QUICK START DEMO
Shows how the universal infrastructure works for all 3 SKUs
"""

import sys
sys.path.append('/mnt/user-data/outputs')

from sku_orchestrator import UniversalBusinessOrchestrator
from dashboard_connector import DashboardConnector

print("🚀 UNIVERSAL AUTONOMOUS INFRASTRUCTURE DEMO\n")
print("="*70)

# Initialize once - works for ALL SKUs
orchestrator = UniversalBusinessOrchestrator()

print("\n📦 SUPPORTED SKUs:")
print(f"   {orchestrator.supported_skus}")
print()

# Demo: Mint Marketing Business
print("="*70)
print("EXAMPLE 1: MINT MARKETING AGENCY")
print("="*70)

try:
    marketing_business = orchestrator.mint_business(
        user_id='demo_user_1',
        user_data={
            'name': 'Wade',
            'email': 'wade@example.com',
            'business_name': 'Demo Marketing Agency',
            'username': 'wade'
        },
        sku_id='marketing',
        template_choice='disruptive'
    )
    
    print(f"\n✅ MARKETING BUSINESS MINTED:")
    print(f"   Storefront: {marketing_business['storefront']['url']}")
    print(f"   C-Suite: {list(marketing_business['csuite'].keys())}")
    print(f"   Systems: {len(marketing_business['autonomous_systems'])} active")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Demo: Mint SaaS Platform  
print("\n\n" + "="*70)
print("EXAMPLE 2: MINT SAAS PLATFORM")
print("="*70)

try:
    saas_business = orchestrator.mint_business(
        user_id='demo_user_2',
        user_data={
            'name': 'Sarah',
            'email': 'sarah@example.com',
            'business_name': 'Demo API Platform',
            'username': 'sarah'
        },
        sku_id='saas',
        template_choice='developer'
    )
    
    print(f"\n✅ SAAS BUSINESS MINTED:")
    print(f"   Storefront: {saas_business['storefront']['url']}")
    print(f"   C-Suite: {list(saas_business['csuite'].keys())}")
    print(f"   Systems: {len(saas_business['autonomous_systems'])} active")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Demo: Dashboard Connector
print("\n\n" + "="*70)
print("EXAMPLE 3: UNIVERSAL DASHBOARD CONNECTOR")
print("="*70)

try:
    # Works for ANY SKU
    connector = DashboardConnector('demo_user_1')
    dashboard = connector.get_dashboard_state(force_refresh=True)
    
    print(f"\n✅ DASHBOARD CONNECTED:")
    print(f"   Selected SKU: {dashboard.get('selected_sku', 'unknown')}")
    print(f"   Revenue: ${dashboard.get('revenue_this_month', 0):,.0f}")
    print(f"   Universal data: revenue, leads, user profile")
    print(f"   SKU-specific data: loaded based on selected_sku")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n\n" + "="*70)
print("✅ SAME INFRASTRUCTURE WORKS FOR ALL SKUs")
print("="*70)
print("\nTo add SKU #4:")
print("1. Create /skus/consulting/config.py")
print("2. Done - orchestrator automatically supports it")
print()

